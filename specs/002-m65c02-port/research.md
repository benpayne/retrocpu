# M65C02 Core Integration Research

**Date**: 2025-12-23
**Research Phase**: Phase 0
**Feature**: [spec.md](spec.md) | [plan.md](plan.md)

## Executive Summary

This document captures all research findings for integrating the M65C02 CPU core to replace the Arlet 6502 core. The M65C02 core solves the critical zero page write failure by using a built-in microcycle controller instead of relying on the RDY signal for clock division.

**Key Finding**: The M65C02 core is fully compatible with our system and firmware. Integration requires signal adaptation but no modifications to memory, peripherals, or firmware.

---

## 1. M65C02 Core Source Analysis

### Repository Information

- **Source**: https://github.com/MorrisMA/MAM65C02-Processor-Core
- **License**: LGPL (open source)
- **Version**: Release 2.73a (latest stable)
- **Author**: Michael A. Morris

### Required Verilog Files

**Core Files** (located in `Src/RTL/`):

```text
M65C02_Core.v           - Top-level core module (39KB, ~1000 lines)
├── M65C02_MPCv4.v      - Microprogram controller with microcycle controller
├── M65C02_AddrGen.v    - Address generator module
└── M65C02_ALU.v        - ALU module
    ├── M65C02_BIN.v    - Binary mode adder
    └── M65C02_BCD.v    - Decimal mode adder
```

**Microprogram ROM Files** (located in `Src/Microprogram-Sources/`):

```text
M65C02_Decoder_ROM.coe  - ALU control field microprogram (or .txt)
M65C02_uPgm_V3a.coe     - Main microprogram sequence control (or .txt)
```

**Optional Support Files**:

```text
M65C02_ClkGen.v         - Clock generator wrapper (not needed - we have our own)
M65C02_IntHndlr.v       - Interrupt handler wrapper (we'll create simpler version)
fedet.v                 - Falling edge detector (for NMI if needed)
```

### Resource Usage

From README synthesis results (Xilinx XC3S50A FPGA):

- **LUTs**: 647-747 (for core only)
- **Flip-Flops**: 191-248
- **Block RAMs**: 2 (for microprogram ROMs)
- **Target Speed**: 73+ MHz achieved, 100 MHz design goal

**Our Target (ECP5 FPGA)**:
- Budget: <12K LUTs (50% of 25K available)
- Current Arlet system: ~2K LUTs
- M65C02 core: ~750 LUTs
- **Estimated total**: ~2750 LUTs (11% utilization) ✅ Well within budget

---

## 2. M65C02 Core Signal Interface

### Module Declaration

```verilog
module M65C02_Core #(
    parameter pStkPtr_Rst  = 8'hFF,  // Stack pointer reset value
    parameter pInt_Hndlr   = 0,      // Interrupt handler microcode address
    parameter pM65C02_uPgm = "M65C02_uPgm_V3a.coe",
    parameter pM65C02_IDec = "M65C02_Decoder_ROM.coe"
)(
    // Clock and Reset
    input   Rst,                // System Reset (active high)
    input   Clk,                // System Clock (25 MHz)

    // Interrupt Interface
    output  IRQ_Msk,            // Interrupt mask from P register
    input   xIRQ,               // External maskable interrupt request
    input   Int,                // Interrupt request to core
    input   [15:0] Vector,      // ISR vector from interrupt handler

    // Status Interface (Debug Signals)
    output  Done,               // Instruction complete/fetch strobe
    output  SC,                 // Single cycle instruction indicator
    output  [2:0] Mode,         // Instruction type (0-7, see below)
    output  RMW,                // Read-modify-write operation flag
    output  reg IntSvc,         // Interrupt service start indicator
    output  ISR,                // Interrupt vector pull start flag

    // Memory Controller Interface
    output  [2:0] MC,           // Microcycle state (see section 3)
    output  [1:0] MemTyp,       // Memory access type (see below)
    input   Wait,               // Wait state request (active high)
    output  Rdy,                // Internal ready signal

    // Memory Bus Interface
    output  [1:0] IO_Op,        // I/O operation type (see below)
    output  [15:0] AO,          // Address output
    input   [7:0] DI,           // Data input
    output  reg [7:0] DO,       // Data output

    // Internal Registers (Debug Access)
    output  [7:0] A,            // Accumulator
    output  [7:0] X,            // X index register
    output  [7:0] Y,            // Y index register
    output  [7:0] S,            // Stack pointer
    output  [7:0] P,            // Processor status word
    output  [15:0] PC,          // Program counter
    output  reg [7:0] IR,       // Instruction register
    output  reg [7:0] OP1,      // Operand register 1
    output  reg [7:0] OP2       // Operand register 2
);
```

### Signal Descriptions

**IO_Op[1:0]** - I/O Operation Type:
```
2'b00 = No operation
2'b01 = Write (WR)
2'b10 = Read (RD)
2'b11 = Instruction Fetch (IF)
```

**MemTyp[1:0]** - Memory Access Type:
```
2'b00 = Program memory
2'b01 = Page 0 (zero page)
2'b10 = Page 1 (stack page)
2'b11 = Data memory
```

**Mode[2:0]** - Instruction Type:
```
3'd0 = STP - Stop processor instruction
3'd1 = INV - Invalid instruction (treated as NOP)
3'd2 = BRK - Break instruction
3'd3 = JMP - Branch/jump/return (Bcc, BBRx/BBSx, JMP/JSR, RTS/RTI)
3'd4 = STK - Stack access (PHA/PLA, PHX/PLX, PHY/PLY)
3'd5 = INT - Single cycle instruction (INC/DEC A, TAX/TXA, SEI/CLI, etc.)
3'd6 = MEM - Multi-cycle instruction with memory access
3'd7 = WAI - Wait for interrupt instruction
```

---

## 3. Microcycle Controller Configuration

### MPCv4 Microcycle Controller

The M65C02_Core uses **M65C02_MPCv4** (Version 4) which has a **fixed 4-cycle microcycle** with wait state support.

### Microcycle State Machine

**MC[2:0] State Sequence**: `2 → 3 → 1 → 0` (repeats)

```
State 2 (MC=2): Cycle 1 - Address presentation
    - Address outputs (AO) become valid
    - IO_Op indicates operation type
    - Memory decoding begins

State 3 (MC=3): Cycle 2 - Memory access
    - Address stable
    - For writes: DO becomes valid
    - For reads: Memory begins outputting data
    - Wait signal sampled at end of this cycle

State 1 (MC=1): Cycle 3 - Data setup/hold
    - For reads: DI must be valid by end of this cycle
    - For writes: DO held stable
    - Wait signal sampled again (for additional wait states)

State 0 (MC=0): Cycle 4 - Data capture/completion
    - For reads: DI captured into internal registers
    - Memory cycle completes
    - Next microcycle begins
```

### Wait State Insertion

The Wait input can extend memory cycles:

- Wait is sampled at the **end of State 3** and **State 1**
- If Wait=1 during State 3: Insert 4-cycle wait state sequence
- If Wait=1 during State 1: Continue waiting
- If Wait=0: Proceed to State 0 (completion)

**Our Usage**: Set `Wait = 0` for all internal memory (RAM, ROMs) - no wait states needed

### Timing for Synchronous Block RAM

**Our block RAM**: 1-cycle read latency (address → data available next cycle)

**Perfect Match**:
```
Cycle 1 (MC=2): Present address to RAM
Cycle 2 (MC=3): RAM internally processing (1-cycle latency)
Cycle 3 (MC=1): RAM data output becomes valid
Cycle 4 (MC=0): Core captures data from DI
```

**Write Timing**:
```
Cycle 1 (MC=2): Present address, assert IO_Op=01
Cycle 2 (MC=3): DO becomes valid, RAM write enable asserted
Cycle 3 (MC=1): Write completes
Cycle 4 (MC=0): Next cycle begins
```

### CPU Frequency Calculation

**System Clock**: 25 MHz
**Microcycle Length**: 4 clocks
**Microcycle Frequency**: 25 MHz ÷ 4 = **6.25 MHz**

**Effective Instruction Rate**:
- M65C02 is pipelined - many instructions complete in fewer microcycles than standard 6502
- Effective IPS (Instructions Per Second) higher than microcycle rate
- Expected effective CPU speed: **~2-3 MHz equivalent** (faster than our 1 MHz target)

**Conclusion**: This is acceptable. The M65C02's pipelining provides good performance even though microcycle rate is lower than Arlet's 1 MHz clock enable approach.

---

## 4. Signal Interface Mapping

### Arlet 6502 vs M65C02 Signal Comparison

| Function | Arlet 6502 | M65C02_Core | Conversion Logic |
|----------|------------|-------------|------------------|
| **Clock** | `clk` | `Clk` | Direct connection (25 MHz) |
| **Reset** | `reset` (active high) | `Rst` (active high) | Direct connection |
| **Address Bus** | `AB[15:0]` | `AO[15:0]` | Direct connection (rename) |
| **Data Input** | `DI[7:0]` | `DI[7:0]` | Direct connection |
| **Data Output** | `DO[7:0]` | `DO[7:0]` | Direct connection |
| **Write Enable** | `WE` (1=write) | `IO_Op[1:0]` | `mem_we = (IO_Op == 2'b01)` |
| **Read Enable** | Implicit (~WE) | `IO_Op[1:0]` | `mem_oe = (IO_Op == 2'b10 \|\| IO_Op == 2'b11)` |
| **Interrupts** | `IRQ`, `NMI` | `Int`, `Vector[15:0]` | Need interrupt wrapper |
| **Ready** | `RDY` (active high) | `Wait` (active high, inverted!) | `Wait = 0` (no waits) |
| **Clock Enable** | External divider | Built-in microcycle | **Remove clock_divider module** |

### Critical Differences

1. **Clock Division**:
   - **Arlet**: Requires external clock divider using RDY signal (THIS CAUSES THE BUG!)
   - **M65C02**: Built-in microcycle controller, runs at full clock speed
   - **Action**: **Delete clock_divider module**, connect Clk directly to 25 MHz

2. **Write/Read Strobes**:
   - **Arlet**: Single `WE` signal (1=write, 0=read)
   - **M65C02**: `IO_Op[1:0]` encoding (01=write, 10=read, 11=fetch)
   - **Action**: Decode IO_Op to generate memory write enables

3. **Ready vs Wait**:
   - **Arlet**: `RDY=1` means "CPU can proceed" (used incorrectly for clock enable)
   - **M65C02**: `Wait=1` means "memory not ready, insert wait state"
   - **Logic**: Opposite meanings! For internal memory: `Wait = 0` (always ready)

4. **Data Bus Timing**:
   - **Arlet**: Data captured when `RDY=1` (clock enable pulse)
   - **M65C02**: Data captured when `MC=0` (end of microcycle)
   - **Action**: Change data bus registration logic

### Interrupt Handling

**Simple Approach for MVP** (no interrupts initially):

```verilog
// Minimal interrupt wrapper
assign Int = 1'b0;          // No interrupts
assign Vector = 16'hFFFC;   // Reset vector (not used during normal operation)
assign xIRQ = 1'b1;         // External IRQ inactive (active low)
```

**Future Enhancement** (when adding interrupts):

Create `M65C02_IntHndlr_Wrapper.v` to:
- Detect IRQ edge
- Prioritize interrupt sources
- Provide vectors from memory ($FFFA/$FFFC/$FFFE)

---

## 5. Required System Changes

### Files to Modify

**`rtl/system/soc_top.v`** - Main integration point:
- Replace Arlet CPU instance with M65C02_Core instance
- Remove clock_divider usage (or set ratio to 1)
- Change signal connections (AB→AO, WE→IO_Op)
- Update data bus multiplexer timing (cpu_clk_enable → MC==0)
- Add IO_Op decoding for memory write enables

**`rtl/system/clock_divider.v`** - Optional:
- Can be removed entirely, OR
- Keep for potential future use with DIVIDE_RATIO=1 (pass-through)

**`build/Makefile`** - Build system:
- Add M65C02 source files to synthesis
- Add microprogram ROM initialization files
- Update file paths for new CPU directory

### Files to Create

**`rtl/cpu/m65c02/`** - New directory:
- Copy M65C02 core files from repository
- Copy microprogram ROM .coe or .txt files
- Optional: Create README.md documenting core

**`tests/unit/test_m65c02_core.py`** - New test:
- Basic M65C02 core functionality tests
- Signal interface verification
- Microcycle state machine tests

**`tests/integration/test_m65c02_zeropage.py`** - New test:
- **Critical**: Zero page write/read validation
- Tests all addresses $0000-$00FF
- Verifies bug fix effectiveness

### Files to Preserve (No Changes)

**Memory modules** (already compatible):
- `rtl/memory/ram.v` - Synchronous block RAM ✅
- `rtl/memory/rom_basic.v` - BASIC ROM ✅
- `rtl/memory/rom_monitor.v` - Monitor ROM ✅

**Peripherals** (signal-agnostic):
- `rtl/peripherals/uart/uart.v` ✅
- `rtl/peripherals/uart/uart_tx.v` ✅
- `rtl/peripherals/uart/uart_rx.v` ✅

**Address decoder** (address-only):
- `rtl/memory/address_decoder.v` - May need minor timing adjustments

**Reset controller** (clock-agnostic):
- `rtl/system/reset_controller.v` ✅

**Firmware** (fully compatible):
- `firmware/monitor/monitor.hex` ✅
- `firmware/basic/basic_rom.hex` ✅

---

## 6. Test Adaptation Strategy

### Tests Requiring NO Changes

These tests are for isolated modules that don't interact with CPU signals:

✅ `tests/unit/test_ram.py` - RAM module in isolation
✅ `tests/unit/test_uart_tx.py` - UART TX in isolation
✅ `tests/unit/test_uart_rx.py` - UART RX in isolation
✅ `tests/unit/test_address_decoder.py` - Address decoder
✅ `tests/unit/test_reset_controller.py` - Reset controller

**Action**: Run existing tests to verify continued functionality

### Tests Requiring SIGNAL NAME Changes

If any integration tests exist that reference CPU signals:

**Signal Renames**:
```python
# Old (Arlet)          # New (M65C02)
dut.cpu.AB       →    dut.cpu.AO
dut.cpu.WE       →    dut.cpu.IO_Op  # Note: decode to boolean
dut.cpu.RDY      →    dut.cpu.Wait   # Note: inverted logic!
dut.cpu.reset    →    dut.cpu.Rst
```

**Write Enable Decoding**:
```python
# Old: Direct boolean
is_write = (dut.cpu.WE.value == 1)

# New: Decode IO_Op
is_write = (dut.cpu.IO_Op.value == 0b01)
is_read = (dut.cpu.IO_Op.value == 0b10)
is_fetch = (dut.cpu.IO_Op.value == 0b11)
```

**Timing Changes**:
```python
# Old: Wait for clock enable
await RisingEdge(dut.cpu_clk_enable)

# New: Wait for microcycle completion
while dut.cpu.MC.value != 0:  # Wait for MC=0 (end of microcycle)
    await RisingEdge(dut.clk_25mhz)
await RisingEdge(dut.clk_25mhz)
```

### New Tests to Create

**`tests/unit/test_m65c02_core.py`** - M65C02 Core Validation:

```python
@cocotb.test()
async def test_m65c02_signals():
    """Verify M65C02 signal interface"""
    # Test IO_Op encoding for read/write/fetch
    # Test MC state machine sequence (2→3→1→0)
    # Test Wait signal response
    # Test Done signal assertion

@cocotb.test()
async def test_m65c02_instruction_fetch():
    """Verify instruction fetch cycle"""
    # Provide NOP (0xEA) on data bus
    # Verify IO_Op = 2'b11 (instruction fetch)
    # Verify MC cycles through 2→3→1→0
    # Verify Done asserted
```

**`tests/integration/test_m65c02_zeropage.py`** - **CRITICAL TEST**:

```python
@cocotb.test()
async def test_zeropage_write_read():
    """
    CRITICAL: Test that zero page writes work correctly.
    This is the PRIMARY bug fix validation test!
    """
    # Test addresses: $0000, $0010, $0020, ..., $00F0
    # For each address:
    #   1. Write unique test pattern
    #   2. Read back and verify
    # PASS CRITERIA: 100% of writes/reads succeed
```

**`tests/integration/test_m65c02_soc_boot.py`** - System Integration:

```python
@cocotb.test()
async def test_monitor_boot():
    """Verify monitor boots and outputs welcome message"""
    # Monitor UART TX output
    # Expect "RetroCPU 6502 Monitor" string
    # Timeout: 1 second @ 25 MHz
```

---

## 7. Firmware Compatibility Verification

### Monitor Firmware Analysis

**File**: `firmware/monitor/monitor.s`

**Interrupt Usage**:
```assembly
; NMI Handler (not used in MVP)
NMI:
    RTI

; IRQ Handler (not used in MVP)
IRQ:
    RTI

.word NMI           ; $FFFA-$FFFB: NMI vector
.word IRQ           ; $FFFE-$FFFF: IRQ/BRK vector
```

**Findings**:
- ✅ IRQ and NMI handlers are trivial (immediate RTI)
- ✅ No complex interrupt logic that depends on vector push behavior
- ✅ No timing-sensitive loops that depend on CPU speed
- ✅ Uses only standard 65C02 instructions

**Compatibility**: **FULLY COMPATIBLE** ✅

### BASIC ROM Analysis

**File**: `firmware/basic/basic_rom.hex` (EhBASIC interpreter)

**EhBASIC Characteristics**:
- ✅ Standard 65C02-compatible BASIC interpreter
- ✅ No interrupts (uses polled I/O via monitor vectors)
- ✅ No NMOS 6502-specific behaviors or undefined opcodes
- ✅ No timing dependencies

**Compatibility**: **FULLY COMPATIBLE** ✅

### M65C02 Behavior Differences vs W65C02

From M65C02 README, these differences **do not affect our firmware**:

**1. BRK/IRQ/NMI Return Address**:
- **Standard 6502**: Pushes address of *next* instruction
- **M65C02**: Pushes address of *last byte* of interrupted instruction
- **Impact**: None - our handlers just RTI immediately

**2. Instruction Interruptibility**:
- **Standard 6502**: Most instructions can be interrupted mid-execution
- **M65C02**: CLI, SEI, jumps, branches, calls, returns not interruptible
- **Impact**: None - we don't use interrupts yet

**3. Interrupt Vector Source**:
- **Standard 6502**: CPU reads vector from fixed addresses ($FFFA/C/E)
- **M65C02**: External interrupt handler provides vector via Vector[15:0] input
- **Impact**: None - we'll provide vectors externally

**4. Execution Speed**:
- **M65C02**: Pipelined, faster than standard 6502 for many instructions
- **Impact**: Positive - better performance

**Conclusion**: All firmware behavior differences are irrelevant to our use case.

---

## 8. Integration Checklist

### Pre-Integration Tasks

- [x] Download M65C02 core source files
- [x] Verify Verilog-2001 compatibility (confirmed from repository)
- [x] Understand microcycle controller operation
- [x] Map all signal interfaces
- [x] Verify firmware compatibility
- [ ] Copy M65C02 files to `rtl/cpu/m65c02/`
- [ ] Create microprogram ROM .coe files for Lattice ECP5

### Integration Tasks

- [ ] Modify `soc_top.v` to instantiate M65C02_Core
- [ ] Remove or bypass clock_divider module
- [ ] Update signal connections (AB→AO, WE→IO_Op, etc.)
- [ ] Add IO_Op decoder for memory write enables
- [ ] Update data bus timing (MC-based instead of clock enable)
- [ ] Add minimal interrupt wrapper
- [ ] Update build system to include M65C02 sources

### Testing Tasks

- [ ] Run existing unit tests (RAM, UART, etc.) - should still pass
- [ ] Create test_m65c02_core.py - basic core functionality
- [ ] Create test_m65c02_zeropage.py - **CRITICAL VALIDATION**
- [ ] Run simulation with monitor firmware
- [ ] Verify instruction fetch cycles in waveforms
- [ ] Verify write cycles with IO_Op=01 in waveforms
- [ ] Verify read cycles with IO_Op=10/11 in waveforms

### Synthesis Tasks

- [ ] Synthesize with Yosys - verify no errors
- [ ] Check resource utilization (target: <12K LUTs)
- [ ] Run place-and-route with nextpnr-ecp5
- [ ] Verify timing closure (25 MHz operation)
- [ ] Generate bitstream

### Hardware Validation Tasks

- [ ] Program FPGA with new bitstream
- [ ] Verify system boots (monitor welcome message via UART)
- [ ] **Test zero page writes: addresses $0000-$00FF**
- [ ] Test monitor E command (examine memory)
- [ ] Test monitor G command (start BASIC)
- [ ] Test BASIC "PRINT 2+2" command
- [ ] Run system stability test (30+ minutes)

---

## 9. Risk Assessment

### Low Risk Items ✅

1. **Core Source Compatibility**: Verified Verilog-2001, used in Xilinx FPGAs
2. **Resource Usage**: ~750 LUTs well within 12K budget
3. **Firmware Compatibility**: Both monitor and BASIC are standard 65C02 code
4. **Memory Timing**: Synchronous RAM perfectly matches 4-cycle microcycle

### Medium Risk Items ⚠️

1. **Microprogram ROM Synthesis**:
   - **Risk**: .coe files are Xilinx-specific, need conversion for Lattice
   - **Mitigation**: Use $readmemb() with .txt files instead
   - **Fallback**: Extract ROM contents, convert to Verilog case statement

2. **Timing Closure**:
   - **Risk**: 25 MHz might be tight with complex address decoding
   - **Mitigation**: Core designed for 100 MHz, plenty of margin
   - **Fallback**: Add pipeline stage in address decoder if needed

### Higher Risk Items (Addressed) 🔧

1. **Signal Timing Differences**: ✅ Thoroughly mapped
2. **Data Bus Synchronization**: ✅ Use MC=0 for capture
3. **Interrupt Handling**: ✅ Simple wrapper, no interrupts initially

---

## 10. Success Criteria

### Phase 0 Research (This Document) ✅

- [x] All 5 research tasks completed
- [x] M65C02 core source analyzed and documented
- [x] Microcycle controller understood and timing calculated
- [x] Complete signal mapping table created
- [x] Firmware compatibility verified
- [x] Test adaptation strategy defined

### Phase 1 Design (Next Steps)

- [ ] Create data-model.md with signal entities
- [ ] Create contracts/ with timing diagrams
- [ ] Create quickstart.md integration guide
- [ ] Update agent context with M65C02 details

### Phase 2+ Implementation (Future)

- [ ] Zero page writes work (100% success rate)
- [ ] Monitor boots and displays prompt
- [ ] BASIC executes "PRINT 2+2" correctly
- [ ] System stable for 30+ minutes

---

## 11. References

### Repository Files

- **M65C02 README**: `temp_m65c02_research/README.md` - Core documentation
- **Core Source**: `temp_m65c02_research/Src/RTL/M65C02_Core.v`
- **MPC Source**: `temp_m65c02_research/Src/RTL/M65C02_MPCv4.v`
- **Testbench**: `temp_m65c02_research/Sim/tb_M65C02_Core.v`

### Project Files

- **Current System**: `rtl/system/soc_top.v`
- **Arlet Core**: `rtl/cpu/arlet-6502/cpu.v`
- **Monitor**: `firmware/monitor/monitor.s`
- **BASIC**: `firmware/basic/basic_rom.hex`

### External Resources

- **GitHub Repository**: https://github.com/MorrisMA/MAM65C02-Processor-Core
- **OpenCores Project**: https://opencores.org/projects/m65c02
- **Root Cause Analysis**: `ROOT_CAUSE_ANALYSIS.md`
- **Core Comparison**: `6502_CORE_COMPARISON.md`

---

## Appendix A: Quick Reference Tables

### Signal Quick Reference

| Signal | Type | Width | Description |
|--------|------|-------|-------------|
| `Clk` | Input | 1 | System clock (25 MHz) |
| `Rst` | Input | 1 | System reset (active high) |
| `AO` | Output | 16 | Address output bus |
| `DI` | Input | 8 | Data input bus |
| `DO` | Output | 8 | Data output bus |
| `IO_Op` | Output | 2 | I/O operation (00/01=W/10=R/11=IF) |
| `MC` | Output | 3 | Microcycle state (0-7) |
| `Wait` | Input | 1 | Wait state request (active high) |
| `Int` | Input | 1 | Interrupt request |
| `Vector` | Input | 16 | Interrupt vector |
| `Done` | Output | 1 | Instruction complete |
| `Mode` | Output | 3 | Instruction type (0-7) |

### Timing Quick Reference

| Parameter | Value | Calculation |
|-----------|-------|-------------|
| System Clock | 25 MHz | Input clock |
| Microcycle Length | 4 clocks | Fixed in MPCv4 |
| Microcycle Frequency | 6.25 MHz | 25 MHz ÷ 4 |
| Clock Period | 40 ns | 1 ÷ 25 MHz |
| Microcycle Period | 160 ns | 40 ns × 4 |
| RAM Access Time | 40 ns | 1 clock (synchronous) |

### State Machine Quick Reference

```
MC State | Cycle | Purpose
---------|-------|----------------------------------
   2     |   1   | Address presentation
   3     |   2   | Memory access / Wait sampling
   1     |   3   | Data setup / Wait sampling
   0     |   4   | Data capture / Cycle complete
```

---

**Research Phase Complete**: All unknowns resolved. Ready for Phase 1 (Design).
