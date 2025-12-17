# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**HDL Language**: Verilog (SystemVerilog for testbenches if needed)
**Target Architecture**: 6502-compatible retro computer system
**Testing Framework**: cocotb (Python-based HDL verification)
**Simulation**: Icarus Verilog (iverilog) or Verilator
**Synthesis**: Yosys or other open source synthesis tools
**Target FPGA**: [e.g., Lattice iCE40, Xilinx Artix-7 or NEEDS CLARIFICATION]
**Project Type**: FPGA/HDL - determines rtl/ and test/ structure
**Timing Goals**: [e.g., 25 MHz clock, 1 cycle ALU operations or NEEDS CLARIFICATION]
**Resource Constraints**: [e.g., <1000 LUTs, <10 BRAMs, specific dev board or NEEDS CLARIFICATION]
**Module Scope**: [e.g., ALU only, full CPU core, system-on-chip or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with RetroCPU Constitution (.specify/memory/constitution.md):

- [ ] **Test-Driven Design**: Confirm cocotb test framework is ready for module tests
- [ ] **Simplicity Over Performance**: Design favors clarity and educational value
- [ ] **Module Reusability**: Modules have clear interfaces and single responsibilities
- [ ] **Educational Clarity**: Documentation includes learning objectives and rationale
- [ ] **Open Source Tooling**: All tools (iverilog, cocotb, yosys) are open source
- [ ] **Quality Gates**: Plan includes test, simulation, lint, documentation, and review gates
- [ ] **Technology Stack**: Using Verilog, cocotb, and open source synthesis toolchain

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
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# FPGA/HDL Project Structure (DEFAULT for RetroCPU)
rtl/
├── core/          # Core 6502 modules (ALU, registers, control)
├── memory/        # RAM, ROM, memory controllers
├── peripherals/   # I/O, timers, serial interfaces
└── top/           # Top-level integration modules

tests/
├── unit/          # cocotb unit tests for individual modules
├── integration/   # cocotb tests for module interactions
└── formal/        # Optional: formal verification (if used)

docs/
├── modules/       # Per-module documentation
├── timing/        # Timing diagrams and constraints
└── learning/      # Educational materials and tutorials

sim/               # Simulation artifacts (not committed)
└── waveforms/     # Generated waveforms for debugging

synth/             # Synthesis outputs (not committed)
└── reports/       # Resource utilization, timing reports
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
