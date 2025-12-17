---

description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **FPGA/HDL project**: `rtl/` for Verilog modules, `tests/` for cocotb tests
- **Module organization**: `rtl/core/`, `rtl/memory/`, `rtl/peripherals/`, `rtl/top/`
- **Test organization**: `tests/unit/` for module tests, `tests/integration/` for system tests
- Paths shown below assume FPGA structure - adjust based on plan.md structure

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /speckit.tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (rtl/, tests/, docs/)
- [ ] T002 Initialize cocotb test framework with sample test
- [ ] T003 [P] Configure Verilog linting and simulation tools (iverilog/verilator)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Define bus protocol and timing specifications
- [ ] T005 [P] Create common parameter definitions (data widths, addresses)
- [ ] T006 [P] Implement clock and reset infrastructure
- [ ] T007 Create base module templates with standard interfaces
- [ ] T008 Setup waveform viewing and debugging workflow
- [ ] T009 Configure synthesis constraints and timing requirements

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1 (MANDATORY per TDD principle) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for [module] in tests/unit/test_[module].py (cocotb)
- [ ] T011 [P] [US1] Integration test for [module interaction] in tests/integration/test_[system].py

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create [Module1] Verilog module in rtl/[category]/[module1].v
- [ ] T013 [P] [US1] Create [Module2] Verilog module in rtl/[category]/[module2].v
- [ ] T014 [US1] Integrate modules in rtl/[category]/[integration].v (depends on T012, T013)
- [ ] T015 [US1] Add timing constraints for module in docs/timing/[module].md
- [ ] T016 [US1] Verify simulation passes all test cases
- [ ] T017 [US1] Document module interface and usage in docs/modules/[module].md

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2 (MANDATORY per TDD principle) ⚠️

- [ ] T018 [P] [US2] Unit test for [module] in tests/unit/test_[module].py (cocotb)
- [ ] T019 [P] [US2] Integration test for [module interaction] in tests/integration/test_[system].py

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create [Module] Verilog module in rtl/[category]/[module].v
- [ ] T021 [US2] Integrate with existing bus/protocol in rtl/[category]/[integration].v
- [ ] T022 [US2] Add timing constraints and verify in simulation
- [ ] T023 [US2] Document module and integrate with User Story 1 (if needed)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3 (MANDATORY per TDD principle) ⚠️

- [ ] T024 [P] [US3] Unit test for [module] in tests/unit/test_[module].py (cocotb)
- [ ] T025 [P] [US3] Integration test for [module interaction] in tests/integration/test_[system].py

### Implementation for User Story 3

- [ ] T026 [P] [US3] Create [Module] Verilog module in rtl/[category]/[module].v
- [ ] T027 [US3] Integrate module with system in rtl/[category]/[integration].v
- [ ] T028 [US3] Verify timing and document module behavior

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/ (module guides, tutorials)
- [ ] TXXX Code cleanup and refactoring for clarity (per Simplicity principle)
- [ ] TXXX Timing optimization if needed (measure first, then optimize)
- [ ] TXXX [P] Additional edge case tests in tests/unit/
- [ ] TXXX Resource utilization review (LUT/BRAM usage)
- [ ] TXXX Run synthesis and verify timing constraints met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (MANDATORY per TDD):
Task: "Unit test for [module] in tests/unit/test_[module].py (cocotb)"
Task: "Integration test for [system] in tests/integration/test_[system].py"

# Launch all independent modules for User Story 1 together:
Task: "Create [Module1] Verilog module in rtl/core/[module1].v"
Task: "Create [Module2] Verilog module in rtl/core/[module2].v"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
