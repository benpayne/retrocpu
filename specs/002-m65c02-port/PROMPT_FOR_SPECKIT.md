# Prompt for Speckit: M65C02 CPU Core Port

## Context

We have a working 6502 FPGA microcomputer project (spec: `specs/001-6502-fpga-microcomputer/`) that is currently BLOCKED by a critical hardware bug in the CPU core.

## The Problem

The Arlet 6502 CPU core we're using has a fundamental incompatibility with our clock division method:
- The core uses RDY (ready) signal for memory wait states
- We're using RDY for clock division (clock enable pulses)
- This causes ALL zero page memory writes ($0000-$00FF) to fail
- Zero page is critical for 6502 operation - BASIC, monitor commands, and all complex programs depend on it

**Technical Details**: See `ROOT_CAUSE_ANALYSIS.md` and `6502_CORE_COMPARISON.md` in project root

## The Solution

Port the project to the **M65C02 CPU core**, which has a built-in microcycle controller specifically designed for flexible FPGA memory timing. This core solves our clock division problem properly.

## Current System (What We Have)

**Working Hardware** (from spec `001-6502-fpga-microcomputer`):
- 32KB RAM at $0000-$7FFF (verified working for $0100+)
- 16KB BASIC ROM at $8000-$BFFF (EhBASIC)
- 8KB Monitor ROM at $E000-$FFFF
- UART TX/RX at $C000-$C0FF (115200 baud)
- Address decoder for memory map
- Clock divider (25 MHz → 1 MHz clock enable)
- Reset controller with button debounce
- Target: Colorlight i5 board with ECP5 FPGA

**Current Status**: See `specs/001-6502-fpga-microcomputer/STATUS.md`

## What Needs to Happen

Create a specification for porting the existing system from Arlet 6502 to M65C02 CPU core.

## Key Requirements

### 1. Core Integration
- Download/integrate M65C02 core from: https://github.com/MorrisMA/MAM65C02-Processor-Core
- Replace Arlet 6502 CPU in `rtl/system/soc_top.v`
- Adapt signal interfaces (M65C02 has different signals)

### 2. Memory Timing Configuration
- Configure M65C02's microcycle controller for our memory:
  - System clock: 25 MHz
  - Target CPU speed: ~1 MHz
  - Synchronous block RAM (1-2 cycles)
- This replaces our current RDY-based clock enable approach

### 3. Signal Mapping
Map M65C02 signals to our existing system:
- Address bus, data bus
- Read/write strobes (M65C02 has separate nOE/nWR vs Arlet's WE)
- Status signals (Mode, Done, SC, RMW, IO_Op - use for debugging)
- Interrupt signals (IRQ, NMI)

### 4. Testing Strategy
- Reuse existing tests where possible (RAM, UART, address decoder)
- Add M65C02-specific tests
- Focus on zero page operations (this is what was broken)
- Integration testing with monitor and BASIC

### 5. Validation Criteria
- Zero page writes must work (addresses $0000-$00FF)
- Monitor boots and shows prompt
- Monitor E command works (examine memory)
- BASIC boots from monitor G command
- BASIC "PRINT 2+2" outputs "4"
- All existing hardware (UART, memory) continues to work

## M65C02 Core Features (from research)

**Advantages**:
- Built-in microcycle controller (1, 2, or 4 cycle memory access)
- Separate read/write strobes (nOE, nWR)
- Rich debug signals (Mode, Done, SC, RMW, IO_Op)
- 73+ MHz capable (much faster than we need)
- Rockwell instruction extensions
- Proven in FPGAs

**Differences from Standard 6502**:
- BRK/IRQ/NMI push address of last byte (not next instruction)
- Not all instructions interruptible (CLI, SEI, jumps, branches, calls, returns)
- External interrupt prioritization and vector provision
- Pipelined execution (faster than standard 6502)

## What to Preserve

From the existing system:
- All memory modules (RAM, ROMs)
- Address decoder (may need minor updates)
- UART peripheral
- Clock divider module (may need updates)
- Reset controller
- Monitor firmware (should work as-is)
- BASIC firmware (should work as-is)
- Build system (Makefile)

## Success Criteria

After the port:
1. System boots and monitor prompt appears via UART
2. Zero page memory works (addresses $0000-$00FF read/write correctly)
3. Monitor E command displays memory contents
4. Monitor G command starts BASIC
5. BASIC "PRINT 2+2" outputs "4"
6. All User Story 2 acceptance criteria pass
7. System ready to continue with User Story 3 (LCD) and beyond

## References

**In this repo**:
- `specs/001-6502-fpga-microcomputer/` - Original spec (use as template)
- `specs/001-6502-fpga-microcomputer/STATUS.md` - Current status
- `ROOT_CAUSE_ANALYSIS.md` - Why we need this port
- `6502_CORE_COMPARISON.md` - Core comparison research
- `rtl/system/soc_top.v` - Current system integration
- `rtl/cpu/arlet-6502/cpu.v` - Current CPU (to be replaced)

**External**:
- M65C02 Core: https://github.com/MorrisMA/MAM65C02-Processor-Core
- M65C02 OpenCores: https://opencores.org/projects/m65c02

## Estimated Effort

5-10 hours total for complete port and validation

## Output Request

Please create a complete specification in `specs/002-m65c02-port/` that includes:
- `spec.md` - Full feature specification
- `plan.md` - Implementation plan
- `tasks.md` - Detailed task breakdown
- Any other necessary planning documents

Follow the same structure and quality standards as `specs/001-6502-fpga-microcomputer/`.
