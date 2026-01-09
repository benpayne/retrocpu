# Implementation Plan: Program Loader and I/O Configuration

**Branch**: `004-program-loader-io-config` | **Date**: 2026-01-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-program-loader-io-config/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature enables dynamic program loading via UART and flexible I/O configuration for standalone operation. Users can upload binary 6502 programs to RAM using XMODEM protocol, paste BASIC program text via flow-controlled serial, and switch between UART and PS/2/Display I/O sources. The primary technical approach involves extending the monitor firmware with XMODEM state machine implementation, adding I/O abstraction layer for source multiplexing, and integrating existing PS/2 and GPU peripherals for standalone keyboard/display operation.

## Technical Context

**HDL Language**: Verilog (SystemVerilog for testbenches if needed)
**Target Architecture**: 6502-compatible retro computer system (M65C02 CPU)
**Testing Framework**: cocotb (Python-based HDL verification)
**Simulation**: Icarus Verilog (iverilog) or Verilator
**Synthesis**: Yosys open source synthesis
**Target FPGA**: Lattice ECP5-25k (Colorlight i5 v7.0 board)
**Project Type**: Mixed FPGA/HDL and firmware development
**Timing Goals**: 25 MHz system clock, monitor firmware operations (non-critical timing)
**Resource Constraints**: Colorlight i5 board (ECP5-25k), existing peripherals (UART, PS/2, GPU)
**Module Scope**: Monitor firmware enhancement (6502 assembly) + I/O peripheral integration + minimal RTL changes for I/O multiplexing

**Implementation Layers**:
1. **Monitor Firmware (6502 Assembly)**: XMODEM protocol state machine, binary loader command, I/O configuration commands, flow control (XON/XOFF)
2. **RTL I/O Abstraction**: Input multiplexer (UART RX + PS/2 scancode → ASCII buffer), output router (character → UART TX + GPU CHAR_DATA)
3. **Peripheral Integration**: PS/2 keyboard ASCII mapping, GPU character output interface, UART existing functionality
4. **Testing**: Hardware-in-loop tests (Python scripts via UART), integration tests (monitor + peripherals), functional tests (upload/execute programs)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with RetroCPU Constitution (.specify/memory/constitution.md):

- [x] **Test-Driven Design**: Hardware-in-loop tests for XMODEM, I/O routing, and program execution; integration tests for monitor + peripherals; functional tests for binary upload and I/O switching
- [x] **Simplicity Over Performance**: XMODEM chosen over more complex protocols (YMODEM, Kermit); simple I/O multiplexing via polling existing status registers; straightforward firmware state machines
- [x] **Module Reusability**: I/O abstraction layer can be reused for future peripherals; XMODEM implementation can be ported to other 6502 projects; PS/2 and GPU interfaces remain generic
- [x] **Educational Clarity**: XMODEM protocol state machine will be documented with timing diagrams; I/O multiplexing architecture explained with data flow diagrams; monitor commands documented with examples
- [x] **Open Source Tooling**: Using ca65 assembler (cc65 toolchain), existing Yosys/nextpnr synthesis, Python for test scripts, standard terminal emulators for XMODEM
- [x] **Quality Gates**: Test plan includes unit tests (XMODEM state machine), integration tests (I/O routing), hardware validation (binary upload and execution), documentation (protocol specs and user guide)
- [x] **Technology Stack**: Monitor firmware in 6502 assembly, RTL in Verilog, tests in Python (hardware-in-loop), open source toolchain throughout

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# RetroCPU Project Structure - Feature 004 Focus

firmware/monitor/
├── monitor.s           # Main monitor firmware (ADD: I/O commands, XMODEM loader)
├── monitor.cfg         # Linker config
└── monitor.hex         # Compiled ROM image

rtl/
├── system/
│   └── io_controller.v # NEW: I/O source multiplexing and routing logic
├── peripherals/
│   ├── uart/
│   │   └── uart.v      # MODIFY: Add flow control signals (XON/XOFF)
│   ├── ps2/
│   │   └── ps2_*.v     # EXISTING: PS/2 keyboard interface (use as-is)
│   └── video/
│       └── gpu_*.v     # EXISTING: GPU character output (use as-is)
└── top/
    └── soc_top.v       # MODIFY: Wire io_controller to peripherals

tests/
├── integration/
│   ├── test_xmodem_upload.py      # NEW: XMODEM binary upload test
│   ├── test_io_switching.py       # NEW: I/O source switching test
│   ├── test_program_execution.py  # NEW: Load and execute binary program
│   └── test_basic_paste.py        # NEW: BASIC text loading test
└── unit/
    └── test_io_controller.v        # NEW: cocotb test for I/O multiplexer

docs/
├── protocols/
│   ├── xmodem.md                   # NEW: XMODEM implementation details
│   └── io_abstraction.md           # NEW: I/O multiplexing architecture
└── user_guides/
    └── program_loading.md          # NEW: User guide for loading programs

firmware/examples/
├── hello_world.s                   # NEW: Example binary program for testing
└── led_blink.s                     # NEW: Simple test program
```

**Structure Decision**: This feature is primarily firmware-focused (monitor.s enhancements for XMODEM and I/O commands) with minimal RTL changes (new io_controller.v for I/O multiplexing). Existing peripherals (UART, PS/2, GPU) are used as-is with interface wiring changes in soc_top.v. Testing is hardware-in-loop using Python scripts that communicate via UART.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations identified. All constitution principles are satisfied:
- Firmware polling approach favors simplicity over RTL complexity
- XMODEM chosen over more complex protocols
- Reusable I/O abstraction layer
- Comprehensive documentation and educational clarity
- Open source toolchain throughout

## Phase 0: Research - ✅ COMPLETE

**Date**: 2026-01-01
**Document**: [research.md](research.md)

**Research Areas Covered**:
1. ✅ XMODEM Protocol Implementation (packet structure, state machine, error handling)
2. ✅ PS/2 to ASCII Mapping (Scancode Set 2, lookup table strategy)
3. ✅ GPU Character Output (interface at $C010, auto-advance cursor)
4. ✅ I/O Multiplexing Architecture (firmware polling vs RTL, chose firmware)
5. ✅ Flow Control Implementation (XON/XOFF for BASIC text)
6. ✅ Monitor Firmware Extension (command parser integration points)

**Key Decisions**:
- XMODEM with 8-bit checksum (simple, widely supported)
- Firmware polling for I/O multiplexing (simplicity over performance)
- Lookup table for PS/2 scancode translation (educational clarity)
- Manual flow control initially (automatic XOFF if needed later)

**Clarifications Resolved**:
- ✅ PS/2 peripheral interface: Memory-mapped at $C200-$C201, FIFO-based
- ✅ UART status register: Bit 0=TX ready, Bit 1=RX ready (confirmed)
- ✅ GPU character output: Single register write to $C010, auto-advance
- ✅ Monitor code structure: Command parser with existing E/D/G/H commands

## Phase 1: Data Model & Contracts - ✅ COMPLETE

**Date**: 2026-01-01
**Documents**:
- [data-model.md](data-model.md)
- [contracts/monitor-xmodem-interface.md](contracts/monitor-xmodem-interface.md)
- [contracts/monitor-io-config-interface.md](contracts/monitor-io-config-interface.md)
- [contracts/ps2-ascii-translation.md](contracts/ps2-ascii-translation.md)
- [quickstart.md](quickstart.md)

**Data Model Defined**:
- Zero page layout ($00-$2B): I/O config, XMODEM state, PS/2 state
- RAM buffers ($0200-$02FF): XMODEM packet buffer, PS/2 lookup table
- Memory map: Existing peripherals (UART $C000, PS/2 $C200, GPU $C010)
- State machines: XMODEM (6 states), PS/2 translation (make/break codes)

**Contracts Established**:
1. **XMODEM Interface**: L command syntax, packet structure, error handling
2. **I/O Config Interface**: I and S command syntax, mode values, routing logic
3. **PS/2 Translation**: Scancode Set 2 mapping, modifier key handling, lookup table

**Quickstart Guide Created**:
- Implementation roadmap (6 phases)
- Code organization and structure
- Build and test workflow
- Common pitfalls and performance considerations

**Agent Context Updated**:
- ✅ Ran `update-agent-context.sh` to propagate design to CLAUDE.md

## Phase 1 Post-Design Constitution Re-Check

Re-verify compliance after completing Phase 1 design:

- [x] **Test-Driven Design**: Test plan includes unit tests (PS2_TO_ASCII, XMODEM state machine), integration tests (upload, I/O switching, program execution), and hardware-in-loop validation
- [x] **Simplicity Over Performance**: Firmware polling confirmed as simplest approach; XMODEM chosen over complex protocols; no premature optimization
- [x] **Module Reusability**: I/O abstraction (CHRIN/CHROUT enhancement) reusable for future peripherals; XMODEM implementation portable to other 6502 projects
- [x] **Educational Clarity**: Comprehensive documentation generated (protocols, contracts, quickstart); lookup table approach for PS/2 is pedagogically clear
- [x] **Open Source Tooling**: Using ca65 assembler, Python test scripts, standard terminal emulators; no proprietary tools
- [x] **Quality Gates**: Test strategy defined with unit, integration, and hardware-in-loop tests; documentation complete before implementation
- [x] **Technology Stack**: 6502 assembly for firmware, Verilog for minimal RTL (if needed), Python for tests; open source throughout

**Result**: ✅ PASS - Design complies with all constitution principles

## Implementation Phases (Post-Planning)

These phases will be executed after `/speckit.plan` completes and `/speckit.tasks` generates the task list:

### Phase 2: XMODEM Core Implementation
- Implement CMD_LOAD command handler
- Implement XMODEM_RECV state machine
- Add checksum verification and error handling
- **Test**: `test_xmodem_upload.py`

### Phase 3: I/O Configuration
- Implement CMD_IO_CONFIG and CMD_STATUS
- Enhance CHRIN for input multiplexing
- Enhance CHROUT for output routing
- **Test**: `test_io_switching.py`

### Phase 4: PS/2 Translation Layer
- Create PS2_XLAT_TABLE lookup table
- Implement PS2_TO_ASCII function
- Handle modifier keys (Shift, Caps Lock)
- **Test**: Unit tests for PS2 translation

### Phase 5: Integration & Hardware Validation
- Create example binary programs
- Full end-to-end testing (upload, switch I/O, execute)
- BASIC text paste testing
- Hardware-in-loop validation on FPGA

### Phase 6: Documentation & Completion
- Write protocol documentation (XMODEM, I/O abstraction)
- Write user guide for program loading
- Update main README with new commands
- Create completion summary

## Ready for Task Generation

**Status**: ✅ Ready for `/speckit.tasks` command

This plan is complete and provides all necessary design artifacts for task breakdown:
- Research findings documented with key decisions
- Data model defines memory layout and state machines
- Contracts specify all interfaces and test cases
- Quickstart provides implementation roadmap and code organization
- Constitution compliance verified (initial and post-design)
