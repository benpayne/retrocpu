<!--
SYNC IMPACT REPORT
==================
Version Change: [NEW] → 1.0.0 (Initial ratification)
Modified Principles: N/A (initial creation)
Added Sections:
  - Core Principles: 5 principles tailored for FPGA/HDL development
    1. Test-Driven Design (NON-NEGOTIABLE)
    2. Simplicity Over Performance
    3. Module Reusability
    4. Educational Clarity
    5. Open Source Tooling
  - Technology Stack: FPGA/Verilog-specific requirements
  - Development Workflow: HDL-specific testing and validation gates
  - Governance: Amendment procedures and compliance
Removed Sections: N/A (initial creation)
Templates Status:
  - ✅ plan-template.md: Constitution Check section will align with principles
  - ✅ spec-template.md: User scenarios compatible with HDL test scenarios
  - ✅ tasks-template.md: Task structure supports HDL module development
Follow-up TODOs: None
-->

# RetroCPU FPGA Constitution

## Core Principles

### I. Test-Driven Design (NON-NEGOTIABLE)

Test-Driven Development (TDD) is MANDATORY for all HDL modules:

- Tests MUST be written in cocotb BEFORE implementing any Verilog module
- Tests MUST fail initially (red phase) before implementation begins
- Implementation proceeds only to make tests pass (green phase)
- Refactoring follows only after tests pass
- Every module MUST have corresponding cocotb test coverage
- Integration tests MUST verify module interactions and bus protocols

**Rationale**: Hardware bugs are exponentially more expensive than software bugs. TDD
ensures correctness before synthesis, reduces debugging time, and provides living
documentation of module behavior.

### II. Simplicity Over Performance

When design choices arise, prioritize simplicity and clarity over performance optimization:

- Choose straightforward logic over clever optimizations
- Favor readable Verilog over dense, compact implementations
- Use clear signal names and consistent naming conventions
- Document non-obvious design decisions inline
- YAGNI principle: Implement only what is currently needed
- Avoid premature optimization; measure before optimizing

**Rationale**: This is a teaching project. Code must be understandable by learners.
Simple designs are easier to debug, verify, and extend. Performance can be optimized
later when bottlenecks are identified through measurement.

### III. Module Reusability

Every component MUST be designed as a reusable, self-contained module:

- Modules MUST have clear, well-defined interfaces
- Avoid tight coupling between modules; use standard bus protocols
- Modules MUST be independently testable in isolation
- Document module purpose, parameters, signals, and timing requirements
- Each module should have a single, clear responsibility
- Prefer composition over monolithic designs

**Rationale**: Reusable modules accelerate development, improve reliability through
reuse, and serve as building blocks for learning. Well-isolated modules simplify
testing and debugging.

### IV. Educational Clarity

All code and documentation MUST support the teaching mission:

- Code comments MUST explain "why" not just "what"
- Complex logic MUST include timing diagrams or state machine documentation
- Non-obvious design patterns MUST reference learning resources
- Variable and signal names MUST be descriptive and self-documenting
- Avoid abbreviations unless they are standard in the domain (e.g., CLK, RST)
- README files MUST include learning objectives and prerequisite knowledge

**Rationale**: Learners need context and explanation. Clear documentation reduces
barriers to entry and enables independent learning. Code should teach as it
implements.

### V. Open Source Tooling

All development MUST use open source tools exclusively:

- Synthesis and simulation: open source toolchains (e.g., yosys, iverilog, verilator)
- Testing framework: cocotb for all verification
- Version control: git for all source and documentation
- Documentation: Markdown and standard formats (no proprietary tools)
- Avoid vendor lock-in; ensure portability across FPGA families when feasible
- Contribute improvements back to open source tools when possible

**Rationale**: Open source tools ensure accessibility for all learners regardless of
financial resources. They promote transparency, community collaboration, and long-term
project sustainability.

## Technology Stack

**HDL Language**: Verilog (SystemVerilog allowed for testbenches only if needed)
**Target Architecture**: 6502-compatible retro computer system
**Testing Framework**: cocotb (Python-based HDL verification)
**Simulation**: Icarus Verilog (iverilog) or Verilator
**Synthesis**: Yosys or other open source synthesis tools
**Target FPGA**: To be determined (prefer widely available dev boards)
**Version Control**: Git with clear commit messages and feature branches
**Documentation**: Markdown for all documentation, inline comments in Verilog
**Coding Standard**: Consistent naming (lowercase_with_underscores for signals,
UPPERCASE for parameters, descriptive module names)

## Development Workflow

### Quality Gates

All contributions MUST pass these gates before merging:

1. **Test Gate**: All cocotb tests pass; new features include new tests
2. **Simulation Gate**: Module simulates correctly in iverilog/verilator
3. **Lint Gate**: Code passes Verilog linting (basic syntax/style checks)
4. **Documentation Gate**: Module has README with interface, timing, and examples
5. **Review Gate**: Code reviewed for clarity, simplicity, and teaching value

### Testing Requirements

- **Unit Tests**: Every module MUST have cocotb unit tests covering normal and edge cases
- **Integration Tests**: Bus interfaces and module interactions MUST be integration tested
- **Regression Tests**: Existing tests MUST continue passing after changes
- **Test Documentation**: Complex test scenarios MUST include comments explaining setup

### Commit Discipline

- Commits MUST be atomic (one logical change per commit)
- Commit messages MUST follow format: `type: brief description`
  - Types: feat, fix, test, docs, refactor, style
- Tests MUST be committed before implementation (TDD workflow visible in history)
- Do not commit synthesized outputs or simulation artifacts (use .gitignore)

## Governance

This constitution defines the non-negotiable principles and practices for the RetroCPU
FPGA project. It supersedes informal practices and provides the framework for all
development decisions.

### Amendment Process

- Amendments require documented justification and team consensus
- Version increments follow semantic versioning (MAJOR.MINOR.PATCH)
- All amendments MUST update this document and propagate changes to templates

### Compliance

- All code reviews MUST verify compliance with constitution principles
- Deviations from simplicity or reusability MUST be justified and documented
- Complexity that violates principles requires explicit approval with rationale
- Teaching value is a primary acceptance criterion for all contributions

### Living Document

- This constitution evolves with the project's needs
- Proposals for improvement are welcome and encouraged
- Changes are tracked through version control with clear rationale

**Version**: 1.0.0 | **Ratified**: 2025-12-16 | **Last Amended**: 2025-12-16
