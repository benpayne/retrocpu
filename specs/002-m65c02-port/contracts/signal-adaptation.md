# Signal Adaptation: Arlet 6502 → M65C02

**Date**: 2025-12-23
**Phase**: Phase 1 - Design (Contracts)
**Feature**: [spec.md](../spec.md) | [data-model.md](../data-model.md)

## Purpose

This document provides specific guidance for converting the existing Arlet 6502 CPU integration to use the M65C02 CPU core. It includes signal mappings, conversion logic, and Verilog code examples.

---

## Signal Mapping Table

### Direct Connections (Rename Only)

| Arlet Signal | M65C02 Signal | Notes |
|--------------|---------------|-------|
| `clk` | `Clk` | Direct connection, same 25 MHz clock |
| `reset` | `Rst` | Both active high, direct connection |
| `AB[15:0]` | `AO[15:0]` | Address bus, rename only |
| `DI[7:0]` | `DI[7:0]` | Data input, same signal |
| `DO[7:0]` | `DO[7:0]` | Data output, same signal |
| `IRQ` (active low) | `xIRQ` (active low) | External IRQ, tie to 1'b1 in MVP |
| `NMI` (active low) | (via Int/Vector) | Requires wrapper, tie to 1'b1 in MVP |

### Signals Requiring Conversion Logic

| Function | Arlet Signal | M65C02 Signals | Conversion Required |
|----------|--------------|----------------|---------------------|
| Write Enable | `WE` (1 bit) | `IO_Op[1:0]` (2 bits) | Decode IO_Op to generate mem_we |
| Read Enable | Implicit (~WE) | `IO_Op[1:0]` | Decode IO_Op to detect read |
| Clock Enable | External divider | Built-in microcycle | **Remove clock_divider** |
| Data Capture | `RDY` pulse | `MC` state | Change to MC=0 edge |
| Ready | `RDY` (active high) | `Wait` (active high) | **Inverted meaning**, tie to 0 |

### New Signals (M65C02 Only)

| Signal | Type | Connection (MVP) | Purpose |
|--------|------|------------------|---------|
| `MC[2:0]` | Output | Use for data capture | Microcycle state |
| `MemTyp[1:0]` | Output | Leave unconnected | Memory type (debug) |
| `Int` | Input | Tie to 1'b0 | Interrupt request |
| `Vector[15:0]` | Input | Tie to 16'hFFFC | Interrupt vector |
| `Rdy` | Output | Leave unconnected | Internal ready |
| `Done`, `SC`, `Mode`, `RMW` | Outputs | Leave unconnected | Status/debug |
| `A`, `X`, `Y`, `S`, `P`, `PC`, `IR`, `OP1`, `OP2` | Outputs | Leave unconnected | Debug registers |
| `IRQ_Msk`, `IntSvc`, `ISR` | Outputs | Leave unconnected | Interrupt status |

---

## Module Replacement

### Arlet 6502 Instantiation (Old)

```verilog
// Old Arlet 6502 CPU instantiation
cpu cpu_inst (
    .clk(clk_25mhz),
    .reset(system_rst),
    .AB(cpu_addr),
    .DI(cpu_data_in),
    .DO(cpu_data_out),
    .WE(cpu_we),          // ← Single write enable bit
    .IRQ(cpu_irq_n),
    .NMI(cpu_nmi_n),
    .RDY(cpu_rdy && cpu_clk_enable)  // ← BUG: This causes zero page failure!
);

// Clock divider (TO BE REMOVED)
clock_divider #(
    .DIVIDE_RATIO(25)  // 25 MHz → 1 MHz clock enable
) clk_div (
    .clk(clk_25mhz),
    .rst(system_rst),
    .clk_enable(cpu_clk_enable)  // ← Causes the bug when used with RDY
);
```

### M65C02 Instantiation (New)

```verilog
// New M65C02 CPU instantiation
M65C02_Core #(
    .pStkPtr_Rst(8'hFF),                        // Stack pointer reset value
    .pInt_Hndlr(0),                             // Interrupt handler microcode address
    .pM65C02_uPgm("M65C02_uPgm_V3a.txt"),       // Microprogram ROM file
    .pM65C02_IDec("M65C02_Decoder_ROM.txt")     // Decoder ROM file
) cpu (
    // Clock and Reset (direct connections)
    .Clk(clk_25mhz),                            // 25 MHz, no clock enable needed
    .Rst(system_rst),

    // Address and Data Buses (rename only)
    .AO(cpu_addr),                              // Was: AB
    .DI(cpu_data_in),                           // Same name
    .DO(cpu_data_out),                          // Same name

    // Control Signals (new)
    .IO_Op(cpu_io_op),                          // NEW: 2-bit operation type
    .MC(cpu_mc),                                // NEW: microcycle state

    // Memory Controller Interface (tie-offs for MVP)
    .Wait(1'b0),                                // NEW: No wait states
    .MemTyp(),                                  // NEW: Unused, leave unconnected

    // Interrupt Interface (tie-offs for MVP, no interrupts)
    .Int(1'b0),                                 // NEW: No interrupts
    .Vector(16'hFFFC),                          // NEW: Default reset vector
    .xIRQ(1'b1),                                // Was: IRQ (inverted polarity)
    .IRQ_Msk(),                                 // NEW: Unused

    // Status and Debug Signals (leave unconnected for MVP)
    .Done(),
    .SC(),
    .Mode(),
    .RMW(),
    .Rdy(),
    .IntSvc(),
    .ISR(),

    // Internal Registers (leave unconnected, for debug only)
    .A(),
    .X(),
    .Y(),
    .S(),
    .P(),
    .PC(),
    .IR(),
    .OP1(),
    .OP2()
);

// Clock divider REMOVED - No longer needed!
// M65C02 runs at full 25 MHz with built-in microcycle controller
```

---

## Write Enable Generation

### Old Method (Arlet)

```verilog
// Arlet: Direct WE signal
wire cpu_we;  // From CPU: 1=write, 0=read

// Use with RAM
ram main_ram (
    .clk(clk_25mhz),
    .we(ram_cs && cpu_we),  // Write when CPU says so
    ...
);
```

### New Method (M65C02)

```verilog
// M65C02: Decode IO_Op to generate write enable
wire [1:0] cpu_io_op;  // From CPU: 00/01=Write/10=Read/11=Fetch
wire [2:0] cpu_mc;     // Microcycle state

// Method 1: Write enable during MC=3 only (recommended for sync RAM)
wire mem_we;
assign mem_we = (cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && ram_cs;

// Method 2: Write enable during MC=3 and MC=1 (hold for 2 clocks)
wire mem_we_extended;
assign mem_we_extended = (cpu_io_op == 2'b01) &&
                         (cpu_mc == 3'b011 || cpu_mc == 3'b001) &&
                         ram_cs;

// Use with RAM
ram main_ram (
    .clk(clk_25mhz),
    .we(mem_we),  // Write only when IO_Op indicates write AND MC=3
    ...
);
```

**Explanation**:
- `IO_Op == 2'b01` → Write operation
- `MC == 3'b011` (MC=3) → Memory access cycle
- For synchronous RAM, write occurs at rising edge when we=1
- We assert we only during MC=3 for clean single-edge write

---

## Data Bus Timing Changes

### Old Method (Arlet with Clock Enable)

```verilog
// Old: Data captured when clock enable pulses
reg [7:0] cpu_data_in_reg;
always @(posedge clk_25mhz) begin
    if (system_rst)
        cpu_data_in_reg <= 8'hEA;  // NOP
    else if (cpu_clk_enable)  // ← Captures every 25 clocks
        cpu_data_in_reg <= cpu_data_in_mux;
end
```

### New Method (M65C02 with Microcycle State)

```verilog
// New: Data captured at end of microcycle (MC=0)
wire [2:0] cpu_mc;  // Microcycle state from M65C02
reg [7:0] cpu_data_in_reg;

always @(posedge clk_25mhz) begin
    if (system_rst)
        cpu_data_in_reg <= 8'hEA;  // NOP
    else if (cpu_mc == 3'b000)  // MC=0: end of microcycle
        cpu_data_in_reg <= cpu_data_in_mux;
end

assign cpu_data_in = cpu_data_in_reg;
```

**Explanation**:
- MC=0 marks end of 4-cycle microcycle
- Data is stable during MC=1 and captured at MC=0 edge
- Captures every 4 clocks (vs every 25 with Arlet)
- **This fixes the zero page bug** - no more RDY corruption!

---

## Address Decoder Changes

### Minimal Changes Required

The address decoder typically doesn't need changes, but timing may need verification:

```verilog
// Address decoder (mostly unchanged)
address_decoder addr_dec (
    .addr(cpu_addr),  // Connected to AO from M65C02
    .ram_cs(ram_cs),
    .rom_basic_cs(rom_basic_cs),
    .rom_monitor_cs(rom_monitor_cs),
    .uart_cs(uart_cs),
    .lcd_cs(lcd_cs),
    .ps2_cs(ps2_cs)
);

// Chip selects used with IO_Op to generate write enables
assign ram_we = (cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && ram_cs;
assign uart_we = (cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && uart_cs;
```

**Timing Consideration**:
- Address is stable for 3 clocks (MC=2,3,1) vs 1 clock in Arlet
- This gives more time for address decode → easier timing closure
- Chip selects should be stable by MC=3 when write occurs

---

## Data Multiplexer Changes

### Old Implementation

```verilog
// Combinational mux + register with clock enable
reg [7:0] cpu_data_in_mux;
reg [7:0] cpu_data_in_reg;

always @(*) begin
    case (1'b1)
        ram_cs:         cpu_data_in_mux = ram_data_out;
        rom_basic_cs:   cpu_data_in_mux = rom_basic_data_out;
        rom_monitor_cs: cpu_data_in_mux = rom_monitor_data_out;
        uart_cs:        cpu_data_in_mux = uart_data_out;
        default:        cpu_data_in_mux = 8'hFF;
    endcase
end

always @(posedge clk_25mhz) begin
    if (system_rst)
        cpu_data_in_reg <= 8'hEA;
    else if (cpu_clk_enable)  // ← OLD: Clock enable based
        cpu_data_in_reg <= cpu_data_in_mux;
end
```

### New Implementation

```verilog
// Combinational mux + register with MC-based capture
reg [7:0] cpu_data_in_mux;
reg [7:0] cpu_data_in_reg;

// Mux logic unchanged (combinational)
always @(*) begin
    case (1'b1)
        ram_cs:         cpu_data_in_mux = ram_data_out;
        rom_basic_cs:   cpu_data_in_mux = rom_basic_data_out;
        rom_monitor_cs: cpu_data_in_mux = rom_monitor_data_out;
        uart_cs:        cpu_data_in_mux = uart_data_out;
        default:        cpu_data_in_mux = 8'hFF;
    endcase
end

// Register logic changed to use MC instead of clock enable
always @(posedge clk_25mhz) begin
    if (system_rst)
        cpu_data_in_reg <= 8'hEA;
    else if (cpu_mc == 3'b000)  // ← NEW: MC=0 based
        cpu_data_in_reg <= cpu_data_in_mux;
end

assign cpu_data_in = cpu_data_in_reg;
```

**Key Change**: Replace `cpu_clk_enable` condition with `cpu_mc == 3'b000`

---

## Complete soc_top.v Changes

### Changes Required

1. **Remove/Bypass Clock Divider**:
   ```verilog
   // OLD: Clock divider instantiation
   clock_divider #(
       .DIVIDE_RATIO(25)
   ) clk_div (
       .clk(clk_25mhz),
       .rst(system_rst),
       .clk_enable(cpu_clk_enable)
   );

   // NEW: Remove entirely, or comment out
   // clock_divider module not needed with M65C02
   ```

2. **Update CPU Instance** (see earlier section)

3. **Change Write Enable Logic**:
   ```verilog
   // OLD:
   .we(ram_cs && cpu_we)

   // NEW:
   .we((cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && ram_cs)
   ```

4. **Change Data Capture Logic**:
   ```verilog
   // OLD:
   else if (cpu_clk_enable)

   // NEW:
   else if (cpu_mc == 3'b000)
   ```

5. **Update Signal Declarations**:
   ```verilog
   // Remove:
   wire cpu_clk_enable;
   reg cpu_clk_enable_delayed;
   wire cpu_we;

   // Add:
   wire [1:0] cpu_io_op;
   wire [2:0] cpu_mc;
   ```

### Diff-Style Summary

```diff
  // CPU Interface Signals
  wire [15:0] cpu_addr;
  wire [7:0] cpu_data_out;
  wire [7:0] cpu_data_in;
- wire cpu_we;
+ wire [1:0] cpu_io_op;  // NEW
+ wire [2:0] cpu_mc;      // NEW
- wire cpu_clk_enable;
- wire cpu_rdy = 1'b1;

  // Memory Write Enables
- assign ram_we = ram_cs && cpu_we;
+ assign ram_we = (cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && ram_cs;

  // Data Capture
  always @(posedge clk_25mhz) begin
      if (system_rst)
          cpu_data_in_reg <= 8'hEA;
-     else if (cpu_clk_enable)
+     else if (cpu_mc == 3'b000)  // MC=0
          cpu_data_in_reg <= cpu_data_in_mux;
  end

- // Clock Divider (REMOVE)
- clock_divider #(
-     .DIVIDE_RATIO(25)
- ) clk_div (
-     ...
- );

  // CPU Instance (REPLACE)
- cpu cpu_inst (
-     .clk(clk_25mhz),
-     .reset(system_rst),
-     .AB(cpu_addr),
-     .WE(cpu_we),
-     .RDY(cpu_rdy && cpu_clk_enable),
-     ...
- );

+ M65C02_Core #(
+     .pStkPtr_Rst(8'hFF),
+     .pM65C02_uPgm("M65C02_uPgm_V3a.txt"),
+     .pM65C02_IDec("M65C02_Decoder_ROM.txt")
+ ) cpu (
+     .Clk(clk_25mhz),
+     .Rst(system_rst),
+     .AO(cpu_addr),
+     .DI(cpu_data_in),
+     .DO(cpu_data_out),
+     .IO_Op(cpu_io_op),
+     .MC(cpu_mc),
+     .Wait(1'b0),
+     .Int(1'b0),
+     .Vector(16'hFFFC),
+     .xIRQ(1'b1),
+     ...
+ );
```

---

## Peripheral Adaptations

### UART Changes

```verilog
// UART write enable generation
// OLD:
.we(uart_cs && cpu_we)

// NEW:
.we((cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && uart_cs)

// UART data capture (if needed)
// OLD:
if (uart_cs && cpu_clk_enable && !cpu_we)

// NEW:
if (uart_cs && (cpu_mc == 3'b000) && (cpu_io_op == 2'b10 || cpu_io_op == 2'b11))
```

**Note**: UART timing should work identically, just with different triggers.

### Future Peripherals (LCD, PS/2)

```verilog
// Same pattern for all peripherals
assign lcd_we = (cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && lcd_cs;
assign ps2_we = (cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && ps2_cs;
```

---

## Interrupt Handling (Future Enhancement)

### MVP: No Interrupts

```verilog
// Tie-offs for MVP (no interrupt support)
.Int(1'b0),
.Vector(16'hFFFC),
.xIRQ(1'b1)
```

### Future: Interrupt Wrapper Module

When adding interrupts, create `m65c02_int_wrapper.v`:

```verilog
module m65c02_int_wrapper (
    input wire clk,
    input wire rst,

    // External interrupt sources
    input wire xIRQ_n,      // External IRQ (active low)
    input wire xNMI_n,      // External NMI (active low)

    // From CPU
    input wire IRQ_Msk,     // I flag from P register

    // To CPU
    output reg Int,         // Interrupt request to core
    output reg [15:0] Vector // ISR address

    // Memory interface (to read vectors)
    // ... (read $FFFA/C/E for vectors)
);

    // IRQ edge detection
    reg xIRQ_n_sync1, xIRQ_n_sync2;
    reg xNMI_n_sync1, xNMI_n_sync2, xNMI_n_prev;
    wire nmi_edge;

    // Synchronizers
    always @(posedge clk) begin
        xIRQ_n_sync1 <= xIRQ_n;
        xIRQ_n_sync2 <= xIRQ_n_sync1;

        xNMI_n_sync1 <= xNMI_n;
        xNMI_n_sync2 <= xNMI_n_sync1;
        xNMI_n_prev <= xNMI_n_sync2;
    end

    // NMI edge detector (negative edge)
    assign nmi_edge = xNMI_n_prev && !xNMI_n_sync2;

    // Interrupt prioritization
    always @(*) begin
        if (nmi_edge) begin
            Int = 1'b1;
            Vector = nmi_vector;  // From $FFFA/$FFFB
        end else if (!xIRQ_n_sync2 && !IRQ_Msk) begin
            Int = 1'b1;
            Vector = irq_vector;  // From $FFFE/$FFFF
        end else begin
            Int = 1'b0;
            Vector = 16'hFFFC;  // Default
        end
    end

    // Vector fetching logic
    // ... (reads from memory at $FFFA/C/E)

endmodule
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Forgetting to Update Write Enable Logic

**Problem**:
```verilog
// Wrong: Still using cpu_we (doesn't exist)
.we(ram_cs && cpu_we)
```

**Solution**:
```verilog
// Correct: Decode IO_Op
.we((cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && ram_cs)
```

### Pitfall 2: Wrong MC State for Data Capture

**Problem**:
```verilog
// Wrong: Capturing at MC=3 (too early)
else if (cpu_mc == 3'b011)
    cpu_data_in_reg <= cpu_data_in_mux;
```

**Solution**:
```verilog
// Correct: Capture at MC=0 (end of microcycle)
else if (cpu_mc == 3'b000)
    cpu_data_in_reg <= cpu_data_in_mux;
```

### Pitfall 3: Leaving Clock Divider Connected

**Problem**:
```verilog
// Wrong: Clock divider still generating cpu_clk_enable
clock_divider clk_div (...);  // Still instantiated
// But cpu_clk_enable not used anywhere
```

**Solution**:
```verilog
// Correct: Remove clock divider entirely
// (comment out or delete the instantiation)
```

### Pitfall 4: Inverted Wait Logic

**Problem**:
```verilog
// Wrong: Arlet RDY and M65C02 Wait are opposite!
.Wait(cpu_rdy)  // If RDY was 1 (ready), Wait should be 0!
```

**Solution**:
```verilog
// Correct: Tie Wait to 0 for MVP (no wait states)
.Wait(1'b0)

// Or if using external wait logic:
.Wait(~memory_ready)  // Invert meaning
```

### Pitfall 5: Not Connecting Required Signals

**Problem**:
```verilog
// Wrong: Leaving required inputs unconnected
M65C02_Core cpu (
    .Clk(clk_25mhz),
    .Rst(system_rst),
    // .Wait() - Missing! Will cause X's in simulation
    // .Int() - Missing!
    ...
);
```

**Solution**:
```verilog
// Correct: Connect all required inputs (even if tied off)
M65C02_Core cpu (
    .Clk(clk_25mhz),
    .Rst(system_rst),
    .Wait(1'b0),      // Tie to constant
    .Int(1'b0),       // Tie to constant
    .Vector(16'hFFFC), // Tie to constant
    .xIRQ(1'b1),      // Tie to constant
    ...
);
```

---

## Verification Approach

### Simulation Checklist

After making changes, verify in simulation:

1. **Basic Signals**:
   - [ ] cpu_addr driven correctly by M65C02
   - [ ] cpu_io_op changes appropriately (01 for writes, 10/11 for reads)
   - [ ] cpu_mc cycles through 2→3→1→0 repeatedly

2. **Write Operations**:
   - [ ] mem_we asserts only when IO_Op=01 and MC=3
   - [ ] mem_we pulse is ~40ns wide (1 clock at MC=3)
   - [ ] cpu_data_out stable when mem_we asserted

3. **Read Operations**:
   - [ ] Data multiplexer selects correct source
   - [ ] cpu_data_in_reg captures at MC=0 edge
   - [ ] Captured data stable for subsequent microcycles

4. **Zero Page Operations** (CRITICAL):
   - [ ] Write to $0000: Check RAM[$0000] contains written value
   - [ ] Read from $0000: Check CPU receives correct value
   - [ ] No corruption or unexpected changes

### Waveform Analysis

View in GTKWave:
```
clk_25mhz
system_rst
cpu_mc[2:0]
cpu_addr[15:0]
cpu_io_op[1:0]
cpu_data_out[7:0]
cpu_data_in[7:0]
cpu_data_in_reg[7:0]
ram_cs
mem_we
ram_data_out[7:0]
```

Look for:
- MC sequence 2→3→1→0 repeating
- Address stable 3 clocks per microcycle
- mem_we pulse only at MC=3 for writes
- Data captured at MC=0 edge for reads

---

## Integration Testing

### Test Sequence

1. **Compile and Simulate**:
   ```bash
   cd build
   make sim_soc
   ```

2. **Check Reset Behavior**:
   - System resets properly
   - First instruction fetch from $FFFC

3. **Test Zero Page Write/Read**:
   ```
   Write $55 to $0000
   Read from $0000
   Expect: $55 (not $00!)
   ```

4. **Test Monitor Boot**:
   - Monitor welcome message appears
   - UART TX outputs correct bytes

5. **Test BASIC**:
   - "G" command starts BASIC
   - "PRINT 2+2" outputs "4"

---

## Related Documents

- **[m65c02-signals.md](m65c02-signals.md)** - Complete signal reference
- **[memory-timing.md](memory-timing.md)** - Timing diagrams
- **[data-model.md](../data-model.md)** - Signal entities
- **[quickstart.md](../quickstart.md)** - Step-by-step integration guide

**Status**: Signal adaptation guide complete ✅
