# Peripheral Interface Comparison: Real 6502 vs Our M65C02

## What Real 6502 Peripherals Expect

### Standard 6502 Peripheral Interface (e.g., 6522 VIA, 6551 ACIA)

```
           ┌──────────────┐
  PHI2 ────┤ Clock input  │ ← Tells peripheral when bus is valid
           │              │
  A[n:0] ──┤ Address      │ ← Stable during PHI2 high
           │              │
  D[7:0] ←→│ Data         │ ← Bidirectional, driven during PHI2
           │              │
  R/W ─────┤ Read/Write   │ ← 1=Read, 0=Write
           │              │
  CS ──────┤ Chip Select  │ ← Usually = address_match AND PHI2
           └──────────────┘
```

**Timing Requirements**:
1. **PHI2 high**: Data bus valid window (~500ns @ 1MHz)
2. **Address setup**: Before PHI2 rises (during PHI1)
3. **Data setup time**: Valid before PHI2 falls (tDSR)
4. **Data hold time**: After PHI2 falls (tHR)
5. **CS must be stable**: During entire PHI2 high period

### Typical 6502 Bus Cycle (1 MHz)

```
PHI1:  ‾‾‾\___________/‾‾‾
PHI2:  ___/‾‾‾‾‾‾‾‾‾‾‾\___

Addr:  ════[Valid────────]

R/W:   ════[Stable───────]

CS:    ____/‾‾‾‾‾‾‾‾‾‾‾\___  (gated by PHI2)

Data:       [Setup─Valid]     (for READ)
       ────────[Drive]────    (for WRITE)
```

## What Our M65C02 Peripherals Actually Get

### Our Current Peripheral Interface

```
           ┌──────────────┐
  CLK ─────┤ 25MHz clock  │ ← Continuous, NOT gated
           │              │
  A[n:0] ──┤ Address      │ ← Direct from CPU, changes mid-cycle
           │              │
  DI[7:0] ←│ Data In      │ ← Separate input (not bidirectional)
  DO[7:0] →│ Data Out     │ ← Separate output
           │              │
  WE ──────┤ Write Enable │ ← Only high during MC=7 AND IO_Op=WRITE
  RD ──────┤ Read Enable  │ ← Only high during MC=7 AND IO_Op=READ (PS/2 only)
           │              │
  CS ──────┤ Chip Select  │ ← Combinational from address, NO PHI2 gate!
           └──────────────┘
```

### Our Actual UART Interface
```verilog
uart_inst (
    .clk(clk_25mhz),              // NOT PHI2! Always running
    .cs(uart_cs),                 // NOT gated by PHI2!
    .we(uart_cs && mem_we),       // Only during MC=7 writes
    .addr(cpu_addr[7:0]),         // Changes every MC state
    .data_in(cpu_data_out),       // Always connected
    .data_out(uart_data_out),     // Always driven
    ...
)
```

### Our M65C02 Bus Cycle (25 MHz = 40ns per clock)

```
CLK:   __/‾\__/‾\__/‾\__/‾\__

MC:    6    7    5    4        (4 clocks = 160ns total)
       C1   C2   C3   C4

Addr:  [Setup ][Stable  ][Next]  ← Changes at MC=4!

CS:    [████████████████]  ← Active whenever address matches (combinational)

WE:         [██]              ← Only MC=7 for writes
RD:         [██]              ← Only MC=7 for reads (PS/2)

Data:            [?? ]        ← When is this valid?
```

## The Critical Differences

| Aspect | Real 6502 | Our M65C02 | Impact |
|--------|-----------|------------|--------|
| **Clock Signal** | PHI2 output for peripherals | 25 MHz continuous | ❌ Peripheral can't sync to bus |
| **Chip Select** | CS = addr_match AND PHI2 | CS = addr_match | ❌ CS active even when address invalid |
| **Data Valid Window** | Clear: PHI2 high (~500ns) | Unclear: MC states? | ❌ Peripheral doesn't know when to provide data |
| **R/W Timing** | Stable during PHI2 | WE/RD pulses at MC=7 | ⚠️ Different but workable |
| **Address Stability** | Entire PHI2 cycle | MC=6 through MC=5 only | ⚠️ Changes at MC=4 |
| **Data Bus** | Bidirectional D[7:0] | Separate DI/DO | ⚠️ Different but workable |

## Why Monitor I/O Reads Fail

Let's trace a monitor `E C001` command (read UART status):

### What Should Happen (Real 6502)
```
1. CPU puts $C001 on address bus during PHI1
2. PHI2 goes high → UART sees CS=1
3. UART drives status ($02 = TX ready) onto data bus
4. CPU samples data before PHI2 falls
5. PHI2 falls → UART stops driving bus
```

### What Actually Happens (Our M65C02)

**Attempt 1: Capture at MC=5 (C3)**
```
MC=6 (C1): Address $C001 appears → CS goes high
MC=7 (C2): Control asserted
MC=5 (C3): We capture data here ← But peripheral may not be ready!
MC=4 (C4): Address changes to next → CS goes low
```
**Result**: Some peripherals (UART) may need more time. We capture too early.

**Attempt 2: Capture at MC=4 (C4)**
```
MC=6 (C1): Address $C001 appears → CS goes high
MC=7 (C2): Control asserted
MC=5 (C3): Data becomes valid (maybe)
MC=4 (C4): We capture data BUT address already changed!
           Address now = next address
           CS now = wrong peripheral!
```
**Result**: We're reading from the NEXT address, not $C001!

## Why PS/2 LEDs Work at MC=4

The PS/2 controller has a `rd` signal:
```verilog
.rd(ps2_cs && mem_rd),  // Read when CPU executes read operation
```

Where `mem_rd = (cpu_io_op == 2'b10) && (cpu_mc == 3'b111);`

So PS/2 gets a read strobe at MC=7, and by MC=4, the data has propagated through its external hardware. **But by MC=4, the address has changed!**

The LEDs work because the PS/2 controller's **internal state** was updated at MC=7, and the LEDs are driven from internal registers, not directly from the bus transaction.

## Solutions for Real 6502 Compatibility

### Option 1: Create PHI2 Equivalent Signal
```verilog
// In soc_top.v
// PHI2 = high during MC=7 and MC=5 (Phi2O phase)
wire phi2_equivalent = (cpu_mc == 3'b111) || (cpu_mc == 3'b101);

// Gate all chip selects
wire uart_cs_phi2 = uart_cs && phi2_equivalent;
wire lcd_cs_phi2 = lcd_cs && phi2_equivalent;
wire ps2_cs_phi2 = ps2_cs && phi2_equivalent;

// Pass to peripherals
uart_inst (
    .clk(clk_25mhz),
    .phi2(phi2_equivalent),    // NEW: PHI2 equivalent
    .cs(uart_cs_phi2),         // Gated chip select
    ...
)
```

### Option 2: Create Standard 6502 Bus Adapter Module
```verilog
module m65c02_to_6502_bus (
    // M65C02 side
    input [15:0] cpu_addr,
    input [7:0] cpu_data_out,
    output reg [7:0] cpu_data_in,
    input [2:0] cpu_mc,
    input [1:0] cpu_io_op,

    // Standard 6502 bus side
    output reg [15:0] addr_6502,
    inout [7:0] data_6502,
    output phi2_6502,
    output r_w_6502
);
    // Generate PHI2
    assign phi2_6502 = (cpu_mc == 3'b111) || (cpu_mc == 3'b101);

    // Generate R/W (standard: 1=read, 0=write)
    assign r_w_6502 = (cpu_io_op != 2'b01);  // Not WRITE

    // Hold address stable during valid period
    always @(posedge clk) begin
        if (cpu_mc == 3'b110)  // MC=6, address setup
            addr_6502 <= cpu_addr;
    end

    // Bidirectional data bus
    assign data_6502 = (r_w_6502) ? 8'hZZ : cpu_data_out;
    always @(posedge clk) begin
        if (cpu_mc == 3'b101)  // MC=5, capture data
            cpu_data_in <= data_6502;
    end
endmodule
```

### Option 3: Redesign Peripherals with Clock-Enable Interface
```verilog
module uart_6502_compatible (
    input clk,              // System clock (25 MHz)
    input clk_enable,       // Clock enable (acts like PHI2)
    input cs,               // Chip select (from decoder)
    input we,               // Write enable
    input [7:0] addr,
    input [7:0] data_in,
    output reg [7:0] data_out,
    ...
);
    // Only respond when clk_enable is high (PHI2 equivalent)
    always @(posedge clk) begin
        if (clk_enable && cs && we) begin
            // Write logic
        end
    end

    // Combinational read (data valid when CS and clk_enable high)
    always @(*) begin
        if (clk_enable && cs)
            data_out = status_register;
        else
            data_out = 8'h00;
    end
endmodule
```

## Recommendations

For **real 6502 peripheral compatibility**, we need:

1. **Add PHI2 output**: Create from MC states (MC=7 or MC=5)
2. **Gate all chip selects**: CS_active = CS && PHI2
3. **Add R/W output**: Convert IO_Op[1:0] to standard R/W
4. **Hold address stable**: Don't let peripherals see MC=4 address change
5. **Provide clock enable**: Let peripherals sync to "PHI2" instead of raw clock

**The current interface is NOT compatible with real 6502 peripherals** because:
- ❌ No PHI2 signal
- ❌ Chip selects not gated by PHI2
- ❌ Address changes mid-cycle (at MC=4)
- ❌ No clear data valid window

Would you like me to implement one of these solutions?
