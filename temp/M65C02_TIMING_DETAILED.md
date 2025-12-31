# M65C02 Detailed Timing Analysis

## MC State Machine (Complete)

The M65C02 uses a **6-state microcycle controller** with two operating modes:

### Normal Operation (No Wait States)
```
Sequence: 4 → 6 → 7 → 5 → 4 → 6 → 7 → 5 → ...
```

| MC Value | Binary  | Cycle Name | Phase | Description |
|----------|---------|------------|-------|-------------|
| **6**    | 3'b110  | C1         | Phi1O | Address setup |
| **7**    | 3'b111  | C2         | Phi2O | Control asserted, memory access begins |
| **5**    | 3'b101  | C3         | Phi2O | Memory operation completes, **check Wait** |
| **4**    | 3'b100  | C4         | Phi1O | Data capture window (for next instruction) |

### Wait State Operation
If `Wait` is asserted during MC=5 (C3), enters wait state loop:
```
5 (Wait=1) → 0 → 2 → 3 → 1 → check Wait → repeat or exit
```

| MC Value | Binary  | Cycle Name | Phase | Description |
|----------|---------|------------|-------|-------------|
| **0**    | 3'b000  | Wait-C4    | Phi1O | Wait state cycle 4 |
| **2**    | 3'b010  | Wait-C1    | Phi1O | Wait state cycle 1 |
| **3**    | 3'b011  | Wait-C2    | Phi2O | Wait state cycle 2 |
| **1**    | 3'b001  | Wait-C3    | Phi2O | Wait state cycle 3, **check Wait again** |

## Mapping to Real 6502 Timing

The M65C02 **does implement PHI1/PHI2 internally** but doesn't expose them as outputs:

```
Real 6502:                  M65C02 Internal:
┌─────────────────┐        ┌─────────────────┐
│ PHI1: Address   │   ≈    │ MC=6,4 (Phi1O)  │
│       Setup     │        │ Address stable  │
├─────────────────┤        ├─────────────────┤
│ PHI2: Data      │   ≈    │ MC=7,5 (Phi2O)  │
│       Valid     │        │ Data transfer   │
└─────────────────┘        └─────────────────┘
```

### Timeline for One Memory Read:

```
Clock:  ___/‾‾‾\___/‾‾‾\___/‾‾‾\___/‾‾‾\___

MC:     6         7         5         4
        C1        C2        C3        C4

Phase:  Phi1O     Phi2O     Phi2O     Phi1O

Addr:   [Setup ]  [Stable →→→→→→→→→] [Next]

IO_Op:  [FETCH/READ announced      ]

Data:             [Valid ←←←←←←←←←]  [Latch?]

CPU
reads:                      ^         ^
                            |         |
                         MC=5      MC=4
                       (Attempt)  (Works?)
```

## When Does CPU Read Data?

According to M65C02 documentation:
- **Address valid**: MC=6 (C1) through MC=5 (C3)
- **Data must be valid**: During MC=7 and MC=5 (Phi2O high)
- **CPU samples data**: End of MC=5 (C3) or start of MC=4 (C4)

**This matches our findings**:
- MC=5: Works for ROM, RAM, firmware UART reads
- MC=4: Works for PS/2 external controller reads

## When Does CPU Write Data?

Looking at our implementation in soc_top.v:
```verilog
wire mem_we = (cpu_io_op == 2'b01) && (cpu_mc == 3'b111);
//                                                   MC=7
```

So **writes happen at MC=7 (C2)** when IO_Op indicates WRITE.

## IO_Op Signal Encoding

From M65C02_Core.v:
```verilog
output [1:0] IO_Op,   // Operation type
```

| IO_Op | Binary | Operation | When Used |
|-------|--------|-----------|-----------|
| **0** | 2'b00  | NO_OP     | No memory operation |
| **1** | 2'b01  | WRITE     | Memory write |
| **2** | 2'b10  | READ      | Data read |
| **3** | 2'b11  | FETCH     | Instruction fetch |

## Current Peripheral Interface

Let's check what we're actually providing to peripherals:

### UART Interface
```verilog
uart_inst (
    .clk(clk_25mhz),              // Continuous 25 MHz
    .rst(system_rst),
    .cs(uart_cs),                  // Chip select from decoder
    .we(uart_cs && mem_we),        // Write enable (cs AND MC=7 AND WRITE)
    .addr(cpu_addr[7:0]),          // Address bottom 8 bits
    .data_in(cpu_data_out),        // Data from CPU
    .data_out(uart_data_out),      // Data to CPU
    ...
)
```

### Address Decoder
```verilog
address_decoder addr_dec (
    .addr(cpu_addr),               // Combinational decode
    .ram_cs(ram_cs),               // Active when addr in range
    .uart_cs(uart_cs),
    .lcd_cs(lcd_cs),
    .ps2_cs(ps2_cs),
    ...
)
```

## Key Insights

### 1. No PHI2 Output for Peripherals
The M65C02 has internal Phi1O/Phi2O timing but **doesn't expose these signals**. Peripherals only see:
- `MC[2:0]` - Internal state (not standard 6502 signal)
- `IO_Op[1:0]` - Operation type
- Continuous 25 MHz clock

### 2. Address Stability
Address bus (`AO[15:0]`) is stable from:
- **MC=6 (C1)** when new address appears
- Through **MC=7 (C2)** and **MC=5 (C3)**
- Changes at **MC=4 (C4)** to next address

### 3. Chip Select Timing
Our `uart_cs`, `lcd_cs`, `ps2_cs` are **purely combinational** from address decoder:
```verilog
assign uart_cs = io_cs && (addr[11:8] == 4'h0);
```

This means chip select **follows address changes immediately** - no PHI2 gating!

### 4. Write Enable Signal
```verilog
wire mem_we = (cpu_io_op == 2'b01) && (cpu_mc == 3'b111);
```

Write enable is active **only during MC=7 (C2)**, which is during Phi2O phase.

### 5. Data Capture Problem
We're trying to capture data at specific MC states, but:
- **MC=5**: Address still valid, but some peripherals not ready
- **MC=4**: Address changed! Reading wrong location

## Why Real 6502 Peripherals Won't Work

A **real 6502 peripheral** expects:

1. **PHI2 signal**: Tells peripheral when to drive data bus
   - **M65C02 doesn't provide this!**

2. **R/W signal**: Simple high/low
   - **M65C02 provides IO_Op[1:0] with 4 states**

3. **Chip Select gated by PHI2**: `CS = (address_match && PHI2)`
   - **Our CS is purely combinational, no PHI2 gating**

4. **Single bidirectional data bus**
   - **M65C02 has separate DI/DO**

## Impact on Our Decoder Logic

### Current Decoder (Combinational)
```verilog
// address_decoder.v - NO timing signals!
assign uart_cs = (addr[15:13] == 3'b110) && (addr[11:8] == 4'h0);
```

**Problem**: This activates **immediately** when address changes, not just during valid cycles.

### What We Need for Real 6502 Compatibility

To build peripherals compatible with real 6502:

#### Option A: Add PHI2 Equivalent Signal
```verilog
// Create PHI2 from MC states
wire phi2 = (cpu_mc == 3'b111) || (cpu_mc == 3'b101);  // MC=7 or MC=5

// Gate chip selects with PHI2
assign uart_cs_gated = uart_cs && phi2;
```

#### Option B: Use IO_Op as Enable
```verilog
// Activate CS only during actual memory operations
wire mem_access = (cpu_io_op != 2'b00);  // Not NO_OP
assign uart_cs_active = uart_cs && mem_access && phi2;
```

#### Option C: Add Enable Signal to Each Peripheral
```verilog
// Peripheral interface
module uart (
    input cs,           // Chip select (combinational from decoder)
    input enable,       // PHI2 equivalent (when CS is valid)
    input we,           // Write enable
    ...
);
```

## Recommendations

### For Real 6502 Peripheral Compatibility:

1. **Expose PHI2 equivalent**: Create signal from MC states
2. **Gate all chip selects**: CS_active = CS && PHI2
3. **Use standard R/W**: Convert IO_Op to simple R/W signal
4. **Add bus interface module**: Translate M65C02 signals to standard 6502

### For Our Current Issue (Monitor I/O Reads):

The problem is **NOT the decoder** - it's working fine. The issue is:
- **Data capture timing** (MC=5 vs MC=4)
- **Peripheral design** (some need different timing)
- **No wait state mechanism** being used

The decoder provides correct chip selects. The problem is when we **sample the data** from peripherals.

## Next Steps

Would you like me to:
1. **Add PHI2 output** to soc_top for real 6502 compatibility?
2. **Create a 6502 bus adapter** module?
3. **Investigate why specific peripherals need MC=4**?
4. **Design new peripherals** with proper timing interfaces?
