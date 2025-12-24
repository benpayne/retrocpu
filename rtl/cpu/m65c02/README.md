# M65C02 CPU Core

**Source**: [MAM65C02-Processor-Core](https://github.com/MorrisMA/MAM65C02-Processor-Core)
**License**: LGPL v3
**Version**: V3a (microprogram version)
**Date Added**: 2025-12-23

## Overview

The M65C02 is a microprogrammed 65C02-compatible processor core designed for FPGA implementation. This core was selected to replace the Arlet 6502 core due to a critical zero page memory write bug in the Arlet implementation.

## Key Features

- **Full 65C02 compatibility**: Supports all documented 65C02 instructions and addressing modes
- **Microprogrammed architecture**: Flexible instruction execution via microcode ROM
- **Built-in microcycle controller**: Fixed 4-cycle microcycle designed for FPGA memory timing
- **Pipelined execution**: Many instructions complete in fewer than 4 microcycles
- **Debug signals**: Comprehensive internal state visibility (Mode, Done, SC, RMW, IO_Op)
- **Wait state support**: Configurable wait states for slow external memory

## Files

### Verilog RTL Modules
- `M65C02_Core.v` - Top-level CPU core module
- `M65C02_MPCv4.v` - Microprogram controller (version 4, fixed 4-cycle)
- `M65C02_AddrGen.v` - Address generation unit
- `M65C02_ALU.v` - Arithmetic logic unit
- `M65C02_BIN.v` - Binary arithmetic operations
- `M65C02_BCD.v` - Binary-coded decimal operations

### Microprogram ROM Files
- `M65C02_Decoder_ROM.txt` - Instruction decoder ROM ($readmemh format)
- `M65C02_uPgm_V3a.txt` - Microprogram ROM V3a ($readmemh format)

## Module Parameters

### M65C02_Core Parameters

```verilog
parameter pStkPtr_Rst = 8'hFF        // Stack pointer reset value
parameter pInt_Hndlr = 0             // Interrupt handler microcode address
parameter pM65C02_uPgm = "M65C02_uPgm_V3a.txt"      // Microprogram ROM file
parameter pM65C02_IDec = "M65C02_Decoder_ROM.txt"   // Decoder ROM file
```

### Integration Settings for RetroCPU

```verilog
M65C02_Core #(
    .pStkPtr_Rst(8'hFF),                        // Standard 6502 stack init
    .pInt_Hndlr(0),                             // Default interrupt handler
    .pM65C02_uPgm("M65C02_uPgm_V3a.txt"),       // V3a microprogram
    .pM65C02_IDec("M65C02_Decoder_ROM.txt")     // Decoder ROM
) cpu (
    .Clk(clk_25mhz),                            // 25 MHz system clock
    .Rst(system_rst),                           // Active high reset
    .AO(cpu_addr),                              // Address output [15:0]
    .DI(cpu_data_in),                           // Data input [7:0]
    .DO(cpu_data_out),                          // Data output [7:0]
    .IO_Op(cpu_io_op),                          // I/O operation [1:0]
    .MC(cpu_mc),                                // Microcycle state [2:0]
    .Wait(1'b0),                                // No wait states for internal RAM
    .Int(1'b0),                                 // Interrupts disabled in MVP
    .Vector(16'hFFFC),                          // Default reset vector
    .xIRQ(1'b1),                                // IRQ inactive (active low)
    // Unconnected outputs (for future use/debugging):
    .MemTyp(),                                  // Memory type classification
    .Done(), .SC(), .Mode(), .RMW(),            // Instruction status
    .Rdy(), .IntSvc(), .ISR(),                  // Ready and interrupt status
    .A(), .X(), .Y(), .S(), .P(), .PC(),        // Register values
    .IR(), .OP1(), .OP2(),                      // Internal working registers
    .IRQ_Msk()                                  // Interrupt mask bit
);
```

## Signal Interface

### Required Signals

| Signal | Direction | Width | Purpose |
|--------|-----------|-------|---------|
| Clk | Input | 1 | System clock (25 MHz) |
| Rst | Input | 1 | Active high reset |
| AO | Output | 16 | Address bus |
| DI | Input | 8 | Data input (reads) |
| DO | Output | 8 | Data output (writes) |
| IO_Op | Output | 2 | I/O operation type |
| MC | Output | 3 | Microcycle state counter |
| Wait | Input | 1 | Wait state request (active high) |

### IO_Op Encoding

- `2'b00` - NO_OP (no memory operation)
- `2'b01` - WRITE (memory write operation)
- `2'b10` - READ (memory read operation)
- `2'b11` - FETCH (instruction fetch operation)

### MC State Sequence

The microcycle controller cycles through 4 states in this order:

```
MC = 2 → 3 → 1 → 0 → 2 → 3 → 1 → 0 → ...
     ↑       ↑       ↑       ↑
  ADDR   MEM     DATA   CYCLE
  SETUP  ACCESS  VALID  END
```

- **MC=2 (ADDR_SETUP)**: CPU presents address on AO
- **MC=3 (MEM_ACCESS)**: Memory operation begins, address stable
- **MC=1 (DATA_VALID)**: Data must be valid and stable
- **MC=0 (CYCLE_END)**: Data captured by CPU on rising edge

## Timing Characteristics

### System Configuration
- **System Clock**: 25 MHz (40ns period)
- **Microcycle Length**: 4 clocks (160ns)
- **Microcycle Frequency**: 6.25 MHz
- **Effective Performance**: ~4-5 MIPS (pipelined execution)

### Memory Timing
- **Read Cycle**: 4 clocks (address setup → RAM latency → data valid → capture)
- **Write Cycle**: 4 clocks (address setup → write enable → data hold → complete)
- **Wait States**: Optional, in 4-clock increments (currently unused)

## Resource Usage

Estimated resource usage on Lattice ECP5 FPGA:
- **LUTs**: ~750 (3% of 25K available)
- **Registers**: ~200
- **Block RAM**: 2 blocks (for microprogram ROMs)

## Integration Notes

### Key Differences from Arlet 6502

1. **Signal Interface**:
   - M65C02 uses `IO_Op[1:0]` instead of single `WE` signal
   - M65C02 exposes `MC[2:0]` microcycle state (no separate clock enable)
   - M65C02 uses `Wait` for wait states (vs Arlet's `RDY`)

2. **Clock Division**:
   - M65C02 has built-in microcycle controller (no external clock_divider needed)
   - Runs at full 25 MHz with internal 4-cycle pipelining

3. **Memory Write Enable**:
   - Arlet: `mem_we = ram_cs && cpu_we`
   - M65C02: `mem_we = (cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && ram_cs`

4. **Data Capture**:
   - Arlet: Captures when `cpu_clk_enable == 1`
   - M65C02: Captures when `cpu_mc == 3'b000` (MC=0)

### Zero Page Bug Fix

The Arlet core had a DIMUX signal incompatibility with RDY-based clock division:
```verilog
assign DIMUX = ~RDY ? DIHOLD : DI;  // Problematic in Arlet
```

This caused zero page writes ($0000-$00FF) to fail. The M65C02 core eliminates this issue by:
- Not using RDY for clock division
- Built-in microcycle controller handles timing
- Proper data capture at MC=0 transition

## Testing

The M65C02 core has been validated via:
- Hardware testing on Colorlight i5 board (ECP5 FPGA)
- Monitor firmware boot and command execution
- Zero page memory write/read tests (all addresses $0000-$00FF)
- BASIC interpreter execution
- 30+ minute stability testing

## Documentation

For detailed integration information, see:
- `/specs/002-m65c02-port/spec.md` - Feature specification
- `/specs/002-m65c02-port/plan.md` - Implementation plan
- `/specs/002-m65c02-port/data-model.md` - Signal timing and data model
- `/specs/002-m65c02-port/contracts/m65c02-signals.md` - Complete signal reference
- `/specs/002-m65c02-port/contracts/memory-timing.md` - Timing diagrams
- `/specs/002-m65c02-port/contracts/signal-adaptation.md` - Arlet to M65C02 conversion

## License

The M65C02 core is licensed under the LGPL v3 license. See the original repository for complete license terms.

## References

- **Original Repository**: https://github.com/MorrisMA/MAM65C02-Processor-Core
- **65C02 Specification**: WDC W65C02S datasheet
- **Microprogram Documentation**: See original repository Docs/ directory
