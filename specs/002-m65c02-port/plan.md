# Implementation Plan: M65C02 CPU Core Port

**Branch**: `002-m65c02-port` | **Date**: 2025-12-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-m65c02-port/spec.md`

## Summary

**Primary Requirement**: Replace the Arlet 6502 CPU core with the M65C02 CPU core to fix a critical zero page memory write failure that blocks all BASIC interpreter functionality, monitor commands, and complex 6502 programs.

**Root Cause**: The Arlet 6502 core's DIMUX signal logic is incompatible with RDY-based clock division. When RDY pulses high for CPU execution, DIMUX switches to the data bus containing incorrect data, corrupting zero page addresses ($0000-$00FF).

**Technical Approach**: The M65C02 core features a built-in microcycle controller specifically designed for flexible FPGA memory timing, which properly handles clock division without the RDY signal incompatibility. This port preserves all existing peripherals, memory, and firmware while swapping only the CPU core.

**Success Criteria**: Zero page memory ($0000-$00FF) read/write operations work correctly, BASIC interpreter executes "PRINT 2+2" and outputs "4", and all existing monitor commands function properly.

## Technical Context

**HDL Language**: Verilog-2001 (per existing codebase)
**Target Architecture**: 6502-compatible microcomputer system with M65C02 CPU core
**Testing Framework**: cocotb (Python-based HDL verification)
**Simulation**: Icarus Verilog (iverilog) - confirmed working in existing project
**Synthesis**: Yosys (open source) - confirmed working in existing project
**Place-and-Route**: nextpnr-ecp5 for Lattice ECP5 FPGA
**Target FPGA**: Colorlight i5 board with ECP5 FPGA (25K LUTs)
**Project Type**: FPGA/HDL system-on-chip integration
**System Clock**: 25 MHz input clock
**CPU Target Frequency**: ~1 MHz (achieved via M65C02 microcycle controller configuration)
**Memory Architecture**:
- 32KB synchronous block RAM ($0000-$7FFF)
- 16KB BASIC ROM ($8000-$BFFF)
- 8KB Monitor ROM ($E000-$FFFF)
- Memory-mapped UART ($C000-$C0FF)
**Resource Constraints**: Must remain under 12K LUTs (~50% of 25K available), existing design uses ~2K LUTs
**Module Scope**: CPU core replacement in `rtl/system/soc_top.v` with signal adaptation layer
**Integration Points**:
- M65C02 address bus → existing address decoder
- M65C02 data bus → existing memory/peripheral data buses
- M65C02 nOE/nWR strobes → existing memory write enable logic
- M65C02 microcycle controller → memory timing configuration

**Key Differences from Arlet Core**:
- M65C02 uses separate nOE (output enable) and nWR (write) strobes vs Arlet's single WE signal
- M65C02 provides debug signals: Mode, Done, SC, RMW, IO_Op (optional but useful)
- M65C02 has built-in microcycle controller for flexible memory cycle timing
- M65C02 is pipelined with faster execution than standard 6502

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with RetroCPU Constitution (.specify/memory/constitution.md):

- [x] **Test-Driven Design**: cocotb framework confirmed ready; existing tests will be adapted for M65C02; new integration tests will be written before core replacement
- [x] **Simplicity Over Performance**: Design focuses on fixing bug with minimal changes; preserves all existing modules; only swaps CPU core and adapts signals
- [x] **Module Reusability**: M65C02 core is self-contained module; existing memory, peripherals, and firmware are preserved; signal adaptation layer is clean interface
- [x] **Educational Clarity**: Plan documents WHY port is needed (bug fix), HOW M65C02 solves it (microcycle controller), and WHAT changes (CPU swap only)
- [x] **Open Source Tooling**: M65C02 core is open source (MAM65C02-Processor-Core); all existing tools (iverilog, cocotb, yosys, nextpnr) remain unchanged
- [x] **Quality Gates**: Plan includes test adaptation, M65C02 simulation, signal timing verification, zero page validation, and hardware testing gates
- [x] **Technology Stack**: Continues using Verilog, cocotb, yosys, nextpnr-ecp5, and Icarus Verilog per constitution

**Constitution Compliance**: ✅ PASSED - All principles satisfied. This is a surgical fix preserving constitution compliance throughout.

## Project Structure

### Documentation (this feature)

```text
specs/002-m65c02-port/
├── spec.md              # Feature specification (complete)
├── plan.md              # This implementation plan
├── research.md          # M65C02 core interface, microcycle config, signal mapping (Phase 0)
├── data-model.md        # M65C02 signal entities and timing contracts (Phase 1)
├── quickstart.md        # Quick integration guide for M65C02 port (Phase 1)
├── contracts/           # Signal timing diagrams and interface contracts (Phase 1)
│   ├── m65c02-signals.md       # M65C02 signal descriptions and timing
│   ├── memory-timing.md        # Microcycle controller configuration
│   └── signal-adaptation.md    # Arlet WE → M65C02 nOE/nWR mapping
├── checklists/
│   └── requirements.md  # Spec quality checklist (complete)
└── tasks.md             # Implementation tasks (Phase 2 - /speckit.tasks command)
```

### Source Code (repository root)

**Existing Structure** (preserved from specs/001-6502-fpga-microcomputer):

```text
rtl/
├── cpu/
│   ├── arlet-6502/           # Current CPU core (to be replaced)
│   │   ├── cpu.v             # Arlet 6502 CPU module
│   │   └── ALU.v             # Arlet ALU module
│   └── m65c02/               # NEW: M65C02 CPU core (from MAM65C02-Processor-Core)
│       ├── M65C02_Core.v     # Main CPU core module
│       ├── M65C02_ALU.v      # ALU module
│       ├── M65C02_MPCv5.v    # Microprogram controller
│       └── [other M65C02 source files as needed]
├── memory/
│   ├── ram.v                 # 32KB block RAM (preserved)
│   ├── rom_basic.v           # BASIC ROM (preserved)
│   ├── rom_monitor.v         # Monitor ROM (preserved)
│   └── address_decoder.v     # Memory map decoder (may need minor updates)
├── peripherals/
│   └── uart/
│       ├── uart.v            # UART top-level (preserved)
│       ├── uart_tx.v         # UART transmit (preserved)
│       └── uart_rx.v         # UART receive (preserved)
└── system/
    ├── soc_top.v             # System integration (MODIFIED for M65C02)
    ├── clock_divider.v       # Clock divider (may need updates for microcycle)
    └── reset_controller.v    # Reset controller (preserved)

tests/
├── unit/
│   ├── test_ram.py           # RAM tests (preserved, continue to pass)
│   ├── test_uart_tx.py       # UART TX tests (preserved)
│   ├── test_uart_rx.py       # UART RX tests (preserved)
│   ├── test_address_decoder.py  # Address decoder tests (preserved)
│   ├── test_clock_divider.py    # Clock divider tests (may need updates)
│   ├── test_reset_controller.py # Reset tests (preserved)
│   └── test_m65c02_core.py   # NEW: M65C02 core unit tests
├── integration/
│   ├── test_cpu_basic.py     # CPU-memory integration (UPDATE for M65C02)
│   ├── test_soc_monitor.py   # System boot test (UPDATE for M65C02)
│   └── test_m65c02_zeropage.py  # NEW: Zero page validation test
└── unit/test_ram_isolation.py   # RAM isolation test (preserved, already passing)

firmware/
├── monitor/
│   ├── monitor.s             # Monitor source (preserved, 65C02-compatible)
│   └── monitor.hex           # Monitor binary (preserved)
└── basic/
    └── basic_rom.hex         # BASIC binary (preserved, 65C02-compatible)

build/
└── Makefile                  # Build system (minor updates for M65C02 sources)

docs/
├── modules/
│   ├── cpu.md                # UPDATE: Document M65C02 core integration
│   ├── memory.md             # Preserved
│   └── uart.md               # Preserved
├── timing/
│   ├── bus_timing.md         # UPDATE: M65C02 bus timing diagrams
│   └── io_timing.md          # Preserved
└── learning/
    ├── 6502_basics.md        # Preserved
    └── memory_map.md         # Preserved
```

**Structure Rationale**:
- **Preserves existing project structure** from specs/001-6502-fpga-microcomputer
- **Isolates M65C02 core** in new rtl/cpu/m65c02/ directory for clean separation
- **Keeps Arlet core** temporarily for reference during development
- **Minimizes changes** to existing modules (memory, peripherals, firmware) per constitution simplicity principle
- **Adds targeted tests** for M65C02 integration and zero page validation
- **Updates only soc_top.v** for CPU swap, maintaining module reusability

## Complexity Tracking

> **No constitution violations** - This plan maintains full compliance.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

**Justification**: This is a straightforward module replacement (CPU core swap) following test-driven design, maintaining simplicity, preserving reusability, with clear educational value (demonstrates how to fix architectural incompatibility), and using only open source tools.

## Phase 0: Research & Unknowns

**Objective**: Resolve all technical unknowns about M65C02 integration before design.

### Research Tasks

1. **M65C02 Core Source Analysis**
   - Task: Download and review MAM65C02-Processor-Core repository
   - Questions to answer:
     - What Verilog files are required for core integration?
     - What are the exact signal names and bit widths?
     - How is the microcycle controller configured (parameters, inputs, signals)?
     - Are there any dependencies or sub-modules required?
   - Output: Document M65C02 file manifest and module hierarchy

2. **Microcycle Controller Configuration**
   - Task: Research M65C02 microcycle controller setup for synchronous block RAM
   - Questions to answer:
     - What parameters control memory cycle length (1, 2, or 4 cycles)?
     - How to achieve ~1 MHz CPU frequency from 25 MHz system clock?
     - What signals configure memory timing for different address ranges?
     - How does wait-state insertion work?
   - Output: Document microcycle configuration strategy with timing diagrams

3. **Signal Interface Mapping**
   - Task: Map M65C02 signals to Arlet 6502 signals and existing system
   - Questions to answer:
     - How to convert M65C02's nOE/nWR to memory write enable logic?
     - How do M65C02 read/write cycles differ in timing from Arlet?
     - What are M65C02 debug signals (Mode, Done, SC, RMW, IO_Op) and how to use them?
     - How do IRQ/NMI signals differ between cores?
   - Output: Signal mapping table with timing relationships

4. **Test Adaptation Strategy**
   - Task: Determine how to adapt existing cocotb tests for M65C02
   - Questions to answer:
     - What signal names change in test fixtures?
     - Does M65C02 require different reset sequences?
     - How to verify microcycle controller behavior in simulation?
     - What waveforms indicate correct zero page operation?
   - Output: Test adaptation checklist and new test requirements

5. **Firmware Compatibility Verification**
   - Task: Verify monitor and BASIC firmware are 65C02-compatible
   - Questions to answer:
     - Do monitor.hex and basic_rom.hex use any NMOS 6502-specific behaviors?
     - Are interrupt vectors compatible with M65C02's BRK/IRQ behavior changes?
     - Do any firmware timing loops depend on specific CPU speed?
   - Output: Firmware compatibility report with any necessary adjustments

**Research Output**: `research.md` documenting all findings and resolving all unknowns

## Phase 1: Design & Contracts

**Prerequisites**: research.md complete with all unknowns resolved

### Design Artifacts

1. **Data Model** (`data-model.md`)
   - M65C02 signal entities (address bus, data bus, control signals)
   - Signal timing relationships and state transitions
   - Microcycle controller configuration parameters
   - Memory cycle state machine

2. **Signal Contracts** (`contracts/`)
   - `m65c02-signals.md`: Complete M65C02 signal reference with timing diagrams
   - `memory-timing.md`: Microcycle controller configuration and memory cycle timing
   - `signal-adaptation.md`: Arlet-to-M65C02 signal conversion logic and timing

3. **Quickstart Guide** (`quickstart.md`)
   - Step-by-step M65C02 integration procedure
   - Simulation and testing workflow
   - Common issues and troubleshooting

### Agent Context Update

Run: `.specify/scripts/bash/update-agent-context.sh claude`

**Technology additions**:
- M65C02 CPU core (MAM65C02-Processor-Core)
- Microcycle controller configuration
- Signal adaptation layer (nOE/nWR strobes)

**Output**: Updated `.specify/memory/agent-specific/claude.md` with M65C02 context

## Phase 2: Task Breakdown

**Prerequisites**: Phase 1 complete (design, contracts, quickstart ready)

**Deliverable**: `tasks.md` with detailed implementation tasks

**Command**: Run `/speckit.tasks` after Phase 1 to generate task breakdown

**Task Categories Expected**:
1. M65C02 core integration and source preparation
2. Microcycle controller configuration
3. Signal adaptation layer implementation
4. Test adaptation and new test creation
5. System integration and soc_top.v modification
6. Synthesis, place-and-route, and FPGA programming
7. Zero page validation and BASIC testing
8. Documentation updates

## Quality Gates

### Before Synthesis:
- [ ] All existing unit tests pass with M65C02 core (RAM, UART, address decoder, reset)
- [ ] New M65C02 integration tests pass (CPU-memory, zero page, microcycle timing)
- [ ] Simulation waveforms show correct zero page write/read cycles
- [ ] Signal timing analysis confirms no setup/hold violations

### After Synthesis:
- [ ] Design synthesizes successfully with Yosys (no errors, acceptable LUT usage)
- [ ] Place-and-route completes with positive timing slack (target: >5ns margin at 25 MHz)
- [ ] Resource utilization under 50% of available LUTs (<12K of 25K)

### Hardware Validation:
- [ ] System boots and displays monitor welcome message within 1 second
- [ ] Zero page write/read test passes for all addresses $0000-$00FF
- [ ] Monitor E command displays memory correctly (including zero page)
- [ ] Monitor G command starts BASIC successfully
- [ ] BASIC "PRINT 2+2" executes and outputs "4"
- [ ] System remains stable for 30+ minutes continuous operation

### Documentation:
- [ ] M65C02 integration documented in docs/modules/cpu.md
- [ ] Bus timing diagrams updated in docs/timing/bus_timing.md
- [ ] Quickstart guide tested by following steps exactly as written

## Success Metrics

**Zero Page Fix Validation**:
- 100% of zero page addresses ($0000-$00FF) read/write correctly (vs 0% previously)
- Zero page addressing modes execute without errors in both monitor and BASIC

**System Stability**:
- System boots within 1 second (currently achieves this)
- Reset button success rate: 100% (currently achieves this)
- Continuous operation stability: 30+ minutes without crashes

**BASIC Functionality**:
- BASIC boots and displays "Ready" prompt within 2 seconds
- "PRINT 2+2" executes correctly (currently fails due to zero page bug)
- FOR loop programs execute without errors (currently fails)
- Variable assignment/retrieval works (currently fails)

**Resource Efficiency**:
- LUT usage remains under 50% of available resources (currently at 8%, target <50%)
- Timing closure with positive slack (currently achieving 52+ MHz vs 25 MHz target)

## Risk Mitigation

**Risk**: M65C02 core source incompatibility with Yosys
- **Mitigation**: Phase 0 research validates Verilog-2001 compatibility; synthesize M65C02 core standalone before integration

**Risk**: Microcycle controller configuration more complex than expected
- **Mitigation**: Start with simplest configuration (single-cycle); iterate based on simulation; document configuration process

**Risk**: Signal timing violations between M65C02 and existing peripherals
- **Mitigation**: Extensive simulation validation before synthesis; use M65C02 debug signals to monitor bus activity

**Risk**: Firmware incompatibility with M65C02
- **Mitigation**: Phase 0 research validates 65C02 compatibility; test with simple monitor commands before full BASIC

**Risk**: Regression in existing functionality
- **Mitigation**: All existing tests must pass; hardware validation confirms UART, memory, reset still work

## Next Steps After Planning

1. Review this plan for completeness and accuracy
2. Execute Phase 0: Research (generate research.md)
3. Execute Phase 1: Design (generate data-model.md, contracts/, quickstart.md)
4. Update agent context with M65C02 details
5. Run `/speckit.tasks` to generate detailed task breakdown
6. Begin implementation following TDD workflow (tests first, then code)

## References

**Specification**: [spec.md](spec.md) - Feature specification with user stories and requirements
**Quality Checklist**: [checklists/requirements.md](checklists/requirements.md) - Spec validation (PASSED)
**Constitution**: `.specify/memory/constitution.md` - RetroCPU project principles
**Original Spec**: `specs/001-6502-fpga-microcomputer/` - Existing system specification
**Root Cause Analysis**: `ROOT_CAUSE_ANALYSIS.md` - Why this port is necessary
**Core Comparison**: `6502_CORE_COMPARISON.md` - Why M65C02 was selected
**M65C02 Core**: https://github.com/MorrisMA/MAM65C02-Processor-Core - Source repository
