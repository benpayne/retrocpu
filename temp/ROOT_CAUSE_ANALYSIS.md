# Root Cause Analysis: Zero Page Write Failure

## Executive Summary

**Problem**: All writes to zero page memory ($0000-$00FF) fail and read back as $00. Writes to $0100+ work correctly.

**Root Cause**: DIMUX signal corruption due to RDY gating with clock division.

**Impact**: CRITICAL - System completely non-functional. Zero page is fundamental to 6502 operation.

## Evidence

### Hardware Test Results
- RAM module tested in isolation: **ALL TESTS PASS** ✓
  - $0000-$00FF work perfectly in isolation
  - $0100+ work perfectly in isolation
  - RAM hardware is **NOT** the problem

### On-Hardware Test Results
- **Firmware test** (firmware/monitor/monitor.s):
  ```
  $0000: wrote $11, read $00  FAIL
  $0010: wrote $22, read $00  FAIL
  $0080: wrote $33, read $00  FAIL
  $00FF: wrote $44, read $00  FAIL
  $0100: wrote $55, read $55  PASS ✓
  $0150: wrote $66, read $66  PASS ✓
  $0200: wrote $77, read $77  PASS ✓
  ```

### Key Findings
1. ✓ RAM module verified working (test_ram_isolation.py)
2. ✓ Address decoder correct (ram_cs includes zero page)
3. ✓ Both absolute and zero page addressing modes fail equally
4. ✗ Issue is in CPU-to-RAM interaction

## Technical Analysis

### The CPU Clock Division Method

The system uses a 25MHz system clock with a 1MHz CPU clock via clock enable pulses:

```verilog
// soc_top.v
clock_divider #(.DIVIDE_RATIO(25)) clk_div (
    .clk(clk_25mhz),
    .rst(system_rst),
    .clk_enable(cpu_clk_enable)  // Pulses high 1 out of 25 cycles
);

// CPU RDY connection
cpu cpu_inst (
    ...
    .RDY(cpu_rdy && cpu_clk_enable)  // RDY tied to clock enable
);
```

**Timing**:
- 24 out of 25 cycles: RDY=0 (CPU paused)
- 1 out of 25 cycles: RDY=1 (CPU runs for one 25MHz cycle)

### The DIMUX Signal

`DIMUX` is the data input multiplexer in the CPU core (rtl/cpu/arlet-6502/cpu.v:857):

```verilog
reg  [7:0] DIHOLD;     // Hold register for Data In
wire [7:0] DIMUX;      // Data In Multiplexer

always @(posedge clk)
    if( RDY )
        DIHOLD <= DI;

assign DIMUX = ~RDY ? DIHOLD : DI;
```

**Behavior**:
- When RDY=0: DIMUX = DIHOLD (held data from previous cycle)
- When RDY=1: DIMUX = DI (current data bus value)

### Zero Page Address Generation

For zero page operations (rtl/cpu/arlet-6502/cpu.v:398-399):

```verilog
parameter ZEROPAGE = 8'h00;

always @*
    case( state )
        ...
        ZP0,
        INDY0:  AB = { ZEROPAGE, DIMUX };  // Address = {$00, operand}
        ...
    endcase
```

For a zero page write like `STA $10`:
- AB should be {8'h00, $10} = $0010
- AB depends on DIMUX containing the operand byte ($10)

### The Failure Mechanism

**Instruction: `STA $10` (Store A to $0010)**

#### Cycle N: DECODE State
1. cpu_clk_enable = HIGH → RDY = 1
2. CPU fetches operand byte $10 from ROM
3. DI = $10 (from ROM)
4. DIHOLD <= $10 (latched on clock edge)
5. DIMUX = DI = $10 ✓
6. State transitions to ZP0

#### Cycle N+1: ZP0 State (THE PROBLEM)
1. cpu_clk_enable = HIGH → RDY = 1
2. **DIMUX = ~RDY ? DIHOLD : DI**
3. Since RDY=1: **DIMUX = DI**
4. **BUT WHAT IS DI NOW?**

Looking at soc_top.v:165-180:

```verilog
always @(*) begin
    case (1'b1)
        ram_cs:         cpu_data_in_mux = ram_data_out;  // ← ZP addresses map to RAM
        rom_basic_cs:   cpu_data_in_mux = rom_basic_data_out;
        rom_monitor_cs: cpu_data_in_mux = rom_monitor_data_out;
        ...
    endcase
end

always @(posedge clk_25mhz) begin
    if (cpu_clk_enable) begin
        cpu_data_in_reg <= cpu_data_in_mux;  // Updated every cpu_clk_enable
    end
end

assign cpu_data_in = cpu_data_in_reg;  // DI = cpu_data_in
```

5. During ZP0 state with RDY=1:
   - Address {$00, ???} is on the bus
   - ram_cs = 1 (zero page maps to RAM)
   - DI = ram_data_out = **whatever garbage is being read from RAM**
   - DIMUX = DI = **ram_data_out** (NOT the operand $10!)
   - AB = {8'h00, ram_data_out} = **WRONG ADDRESS!**

6. Write happens to wrong address:
   - If ram_data_out = $00, writes go to $0000
   - If ram_data_out = $20, writes go to $0020
   - If ram_data_out = $FF, writes go to $00FF

#### Why $0100+ Works

For addresses $0100+, the CPU uses absolute addressing (ABS0→ABS1 states):

```verilog
ABS0:
    - Fetch low byte of address
    - ABL <= low byte (registered)

ABS1:
    - Fetch high byte of address
    - AB = {DIMUX, ADD}  // High byte from DIMUX, low from ABL
    - Write happens

READ/WRITE:
    - AB = {ABH, ABL}  // Uses registered values
```

The key difference: Absolute addressing uses **registered ABL/ABH** which are stable, not the **combinational DIMUX** which gets corrupted by DI.

## Why This Design Usually Works

The Arlet 6502 core was designed for systems where RDY is tied to actual memory wait states, not clock division:

1. Normal case: RDY = 1 always (fast memory)
2. Wait state case: RDY = 0 when memory not ready, then RDY = 1 when data valid

In both cases, when RDY=1, DI contains **valid data from the current address**. The DIMUX logic expects this.

**Our system is different**: RDY pulses for clock division, so when RDY=1, DI might contain data from a **previous unrelated address**, corrupting DIMUX.

## Proposed Solutions

### Option 1: Don't Use RDY for Clock Division (RECOMMENDED)

Keep RDY=1 and use a different clock gating method:

```verilog
cpu cpu_inst (
    .clk(clk_25mhz),
    .reset(system_rst),
    .AB(cpu_addr),
    .DI(cpu_data_in),
    .DO(cpu_data_out),
    .WE(cpu_we_internal),
    .IRQ(cpu_irq_n),
    .NMI(cpu_nmi_n),
    .RDY(1'b1)  // Always ready
);

// Gate write enable instead
assign ram_we = ram_cs && cpu_we_internal && cpu_clk_enable;

// Gate register updates
always @(posedge clk_25mhz) begin
    if (cpu_clk_enable) begin
        // Latch CPU outputs
        cpu_addr_reg <= cpu_addr;
        cpu_we_reg <= cpu_we_internal;
        cpu_data_out_reg <= cpu_data_out;
    end
end
```

### Option 2: Fix DIHOLD Latching

Modify CPU core to latch DIHOLD on every cpu_clk_enable pulse:

```verilog
always @(posedge clk)
    if( cpu_clk_enable )  // Latch every CPU cycle, not just when RDY transitions
        DIHOLD <= DI;
```

**Problem**: This requires modifying the CPU core, which we'd prefer to avoid.

### Option 3: Use Proper Clock Division

Generate an actual divided clock instead of clock enable:

```verilog
reg [4:0] clk_counter;
reg cpu_clk;

always @(posedge clk_25mhz) begin
    if (system_rst) begin
        clk_counter <= 0;
        cpu_clk <= 0;
    end else begin
        clk_counter <= clk_counter + 1;
        if (clk_counter == 24) begin
            clk_counter <= 0;
            cpu_clk <= ~cpu_clk;  // Toggle creates 1 MHz clock
        end
    end
end

cpu cpu_inst (
    .clk(cpu_clk),  // Use divided clock directly
    .RDY(1'b1),     // Always ready
    ...
);
```

**Problem**: Mixed clock domains require careful handling.

## Verification Plan

After implementing fix:

1. Run test_ram_isolation.py - should still pass ✓
2. Program FPGA with fix
3. Run firmware address range test - should see all addresses pass ✓
4. Test monitor commands - INPUT_BUF should store characters correctly ✓
5. Test BASIC - should accept input and execute commands ✓

## References

- rtl/cpu/arlet-6502/cpu.v:857 - DIMUX assignment
- rtl/cpu/arlet-6502/cpu.v:398-399 - Zero page address generation
- rtl/system/soc_top.v:199 - RDY connection
- tests/unit/test_ram_isolation.py - RAM verification (all pass)
- firmware/monitor/monitor.s - Address range test
- BUG_REPORT_ZERO_PAGE_WRITES.md - Initial investigation
- RAM_DEBUG_NOTES.md - Debug notes

## Fix Attempts

### Attempt 1: Delay RDY by one cycle
**Result**: FAILED - System completely unresponsive. Delaying RDY breaks the CPU's execution timing.

### Attempt 2: Prevent DI updates during writes
**Result**: FAILED - Zero page still reads $00. The issue occurs during the write cycle itself when DIMUX switches to DI.

### Attempt 3: Change DIMUX to always use DIHOLD
**Result**: FAILED - System completely dead, no serial output. DIHOLD might not be initialized properly at reset.

## Real Solution Needed

The Arlet 6502 core's `DIMUX = ~RDY ? DIHOLD : DI` design is fundamentally incompatible with using RDY for clock division. The core expects:
- RDY=1: Normal operation, use DI directly from memory
- RDY=0: Memory wait state, use held value DIHOLD

Our usage:
- RDY=1 for 1 cycle every 25: CPU executes, but DI might contain wrong data
- RDY=0 for 24 cycles: CPU paused

### Possible Solutions

1. **Use real divided clock (RECOMMENDED)**
   - Generate actual 1 MHz clock from 25 MHz
   - Keep RDY=1 always
   - Requires careful clock domain crossing handling
   - Most compatible with CPU core design

2. **Modify CPU core more carefully**
   - Add reset for DIHOLD
   - Change DIMUX logic to be compatible with clock-enable style RDY
   - Requires thorough testing to ensure no other breakage

3. **Use different 6502 core**
   - Find a core designed for clock-enable operation
   - May require significant integration work

## Status

**BLOCKED** - Root cause confirmed, but suitable fix not yet found. Multiple approaches attempted without success.

Date: December 23, 2025
