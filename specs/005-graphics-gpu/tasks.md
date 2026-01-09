# Tasks: Graphics Mode GPU with VRAM

**Input**: Design documents from `/specs/005-graphics-gpu/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test-Driven Design (TDD) is MANDATORY per RetroCPU Constitution. All tests must be written FIRST and FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **FPGA/HDL project**: `rtl/peripherals/video/` for GPU modules, `tests/` for cocotb tests
- **Test organization**: `tests/unit/` for module tests, `tests/integration/` for system tests
- **Documentation**: `docs/modules/` for module guides

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and test framework setup

- [ ] T001 Verify project structure exists (rtl/peripherals/video/, tests/unit/, tests/integration/)
- [ ] T002 Verify cocotb test framework is configured and working (run existing test_gpu_registers.py)
- [ ] T003 [P] Verify iverilog and Yosys are installed and accessible

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Review existing VGA timing generator (rtl/peripherals/video/vga_timing_generator.v) for integration points
- [ ] T005 [P] Review existing dual-port RAM pattern from rtl/peripherals/video/character_buffer.v for VRAM implementation
- [ ] T006 [P] Document register address space allocation (0xC100-0xC10F) and verify no conflicts with existing peripherals
- [ ] T007 Create common parameter definitions for GPU (modes, resolutions, palette size) in rtl/peripherals/video/gpu_graphics_params.vh

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Single-Page Graphics Display (Priority: P1) 🎯 MVP

**Goal**: Enable developer to write a bitmap image to VRAM and display it on screen in a single graphics mode (1 BPP, 2 BPP, or 4 BPP)

**Independent Test**: Write a known test pattern (checkerboard, color bars, etc.) to VRAM via registers and verify the display output matches the expected bitmap

### Tests for User Story 1 (MANDATORY per TDD principle) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Create unit test for VRAM module in tests/unit/test_gpu_vram.py (cocotb) - test write/read, address wrapping, dual-port operation
- [ ] T009 [P] [US1] Create unit test for palette module in tests/unit/test_gpu_palette.py (cocotb) - test RGB444 writes, RGB888 expansion, invalid index handling
- [ ] T010 [P] [US1] Create unit test for graphics registers in tests/unit/test_gpu_graphics_registers.py (cocotb) - test VRAM_ADDR, VRAM_DATA, GPU_MODE, CLUT registers
- [ ] T011 [P] [US1] Create unit test for pixel renderer in tests/unit/test_gpu_pixel_renderer.py (cocotb) - test 1/2/4 BPP decoding, palette lookup
- [ ] T012 [P] [US1] Create integration test for full framebuffer display in tests/integration/test_gpu_graphics_framebuffer.py - write test pattern, verify output

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement 32KB dual-port VRAM module in rtl/peripherals/video/gpu_graphics_vram.v with block RAM synthesis directive
- [ ] T014 [P] [US1] Implement 16-entry RGB444 palette module in rtl/peripherals/video/gpu_graphics_palette.v with RGB888 expansion
- [ ] T015 [US1] Implement graphics register file in rtl/peripherals/video/gpu_graphics_registers.v (VRAM_ADDR, VRAM_DATA, GPU_MODE, CLUT_INDEX, CLUT_DATA_R/G/B, DISPLAY_MODE)
- [ ] T016 [US1] Implement pixel renderer module in rtl/peripherals/video/gpu_pixel_renderer.v with 1/2/4 BPP decoding and palette lookup
- [ ] T017 [US1] Create graphics GPU top-level integration in rtl/peripherals/video/gpu_graphics_core.v (integrate VRAM + palette + registers + renderer)
- [ ] T018 [US1] Implement character/graphics output multiplexer in rtl/peripherals/video/gpu_mux.v controlled by DISPLAY_MODE register
- [ ] T019 [US1] Update top-level GPU module (rtl/peripherals/video/gpu_top.v) to instantiate gpu_graphics_core and gpu_mux
- [ ] T020 [US1] Run all US1 unit tests and verify they pass (tests/unit/test_gpu_*.py)
- [ ] T021 [US1] Run US1 integration test and verify framebuffer displays correctly (tests/integration/test_gpu_graphics_framebuffer.py)
- [ ] T022 [US1] Document VRAM module interface and clock domain crossing in docs/modules/gpu_graphics_vram.md
- [ ] T023 [US1] Document graphics GPU architecture and module integration in docs/modules/gpu_graphics_architecture.md

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - basic graphics display works in all three modes

---

## Phase 4: User Story 2 - Efficient Bulk Data Transfer (Priority: P2)

**Goal**: Enable developer to transfer a complete framebuffer from CPU memory to VRAM quickly using burst write mode (auto-increment address)

**Independent Test**: Measure the time to write an 8KB framebuffer and verify it completes within acceptable performance bounds (<100ms per SC-001)

**Dependencies**: Requires User Story 1 (VRAM and registers) to be complete

### Tests for User Story 2 (MANDATORY per TDD principle) ⚠️

- [ ] T024 [P] [US2] Create performance test for burst write mode in tests/integration/test_gpu_burst_write_performance.py - measure 8KB transfer time, verify <100ms

### Implementation for User Story 2

- [ ] T025 [US2] Add burst mode logic to graphics registers module in rtl/peripherals/video/gpu_graphics_registers.v (VRAM_CTRL bit 0, auto-increment on VRAM_DATA write)
- [ ] T026 [US2] Update unit test test_gpu_graphics_registers.py to test burst mode enable/disable and auto-increment behavior
- [ ] T027 [US2] Run burst write performance test and verify SC-001 criterion (<100ms for 8KB)
- [ ] T028 [US2] Update register map documentation in docs/gpu_register_map.md with burst mode usage examples

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - graphics display works AND bulk transfers are efficient

---

## Phase 5: User Story 4 - Palette Programming for Color Customization (Priority: P2)

**Goal**: Enable developer to program custom color palettes to achieve specific artistic styles or match period-accurate game colors

**Independent Test**: Program specific RGB444 values into palette entries and verify displayed colors match the specified values

**Dependencies**: Requires User Story 1 (palette module) to be complete

**Note**: This is User Story 4 but implemented as Phase 5 because palette programming is already implemented in US1. This phase adds validation and documentation.

### Tests for User Story 4 (MANDATORY per TDD principle) ⚠️

- [ ] T029 [P] [US4] Create palette update test in tests/integration/test_gpu_palette_update.py - program palette, display image, change palette, verify immediate color update

### Implementation for User Story 4

- [ ] T030 [US4] Verify palette write interface in gpu_graphics_palette.v correctly handles CLUT_INDEX and CLUT_DATA_R/G/B writes
- [ ] T031 [US4] Verify RGB444 to RGB888 bit expansion produces correct output (test with test_gpu_palette.py)
- [ ] T032 [US4] Run palette update integration test and verify immediate color changes (test_gpu_palette_update.py)
- [ ] T033 [US4] Add palette programming examples to docs/modules/gpu_graphics_architecture.md and quickstart guide

**Checkpoint**: At this point, User Stories 1, 2, AND 4 work independently - full palette customization is available

---

## Phase 6: User Story 3 - Page Flipping for Tear-Free Animation (Priority: P3)

**Goal**: Enable developer to render animation frames to off-screen VRAM page and flip to new page during VBlank to avoid tearing

**Independent Test**: Alternately render to two pages and flip between them while verifying no screen tearing occurs and VBlank interrupt timing is correct

**Dependencies**: Requires User Story 1 (VRAM and display) and User Story 2 (burst writes for fast rendering) to be complete

### Tests for User Story 3 (MANDATORY per TDD principle) ⚠️

- [ ] T034 [P] [US3] Create page flipping integration test in tests/integration/test_gpu_page_flipping.py - render to two pages, flip on VBlank, verify no tearing
- [ ] T035 [P] [US3] Create VBlank interrupt timing test in tests/integration/test_gpu_vblank_interrupt.py - verify interrupt fires at correct time (±1 scanline)

### Implementation for User Story 3

- [ ] T036 [US3] Add framebuffer base address registers (FB_BASE_LO, FB_BASE_HI) to rtl/peripherals/video/gpu_graphics_registers.v
- [ ] T037 [US3] Update pixel renderer (rtl/peripherals/video/gpu_pixel_renderer.v) to use FB_BASE_ADDR as offset for VRAM reads
- [ ] T038 [US3] Implement VBlank signal generation in graphics core (rtl/peripherals/video/gpu_graphics_core.v) using vsync from vga_timing_generator
- [ ] T039 [US3] Implement dual-flop synchronizer for VBlank clock domain crossing (pixel clock to CPU clock) in rtl/peripherals/video/gpu_graphics_core.v
- [ ] T040 [US3] Implement VBlank edge detection for interrupt pulse generation in rtl/peripherals/video/gpu_graphics_core.v
- [ ] T041 [US3] Add GPU_STATUS register (VBlank flag) to rtl/peripherals/video/gpu_graphics_registers.v
- [ ] T042 [US3] Add GPU_IRQ_CTRL register (VBlank interrupt enable) to rtl/peripherals/video/gpu_graphics_registers.v
- [ ] T043 [US3] Connect VBlank interrupt output from gpu_graphics_core to CPU interrupt controller (update gpu_top.v)
- [ ] T044 [US3] Update unit test test_gpu_graphics_registers.py to test FB_BASE_ADDR, GPU_STATUS, and GPU_IRQ_CTRL registers
- [ ] T045 [US3] Run page flipping integration test and verify tear-free display (tests/integration/test_gpu_page_flipping.py)
- [ ] T046 [US3] Run VBlank interrupt timing test and verify SC-006 criterion (±1 scanline accuracy)
- [ ] T047 [US3] Document page flipping and VBlank interrupt usage in docs/modules/gpu_graphics_architecture.md

**Checkpoint**: All user stories should now be independently functional - full graphics GPU with page flipping and VBlank interrupts works

---

## Phase 7: Mode Switching and Edge Cases

**Goal**: Verify all graphics modes (1/2/4 BPP) work correctly and edge cases are handled properly

**Purpose**: Cross-cutting validation that affects multiple user stories

### Tests for Mode Switching

- [ ] T048 [P] Create mode switching test in tests/integration/test_gpu_mode_switching.py - switch between 1/2/4 BPP modes, verify correct rendering
- [ ] T049 [P] Create edge case test in tests/unit/test_gpu_edge_cases.py - test VRAM address wrap, invalid palette index, mid-frame mode change

### Implementation

- [ ] T050 Verify 1 BPP mode (320x200) renders correctly in gpu_pixel_renderer.v
- [ ] T051 Verify 2 BPP mode (160x200) renders correctly with 4-color palette in gpu_pixel_renderer.v
- [ ] T052 Verify 4 BPP mode (160x100) renders correctly with 16-color palette in gpu_pixel_renderer.v
- [ ] T053 Verify VRAM address wrapping at $7FFF→$0000 in gpu_graphics_vram.v
- [ ] T054 Verify invalid CLUT_INDEX (>15) is masked in gpu_graphics_palette.v
- [ ] T055 Run mode switching integration test and verify all modes work (tests/integration/test_gpu_mode_switching.py)
- [ ] T056 Run edge case unit tests and verify proper handling (tests/unit/test_gpu_edge_cases.py)

**Checkpoint**: All modes and edge cases validated

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, synthesis validation, and final documentation

- [ ] T057 [P] Run full regression test suite (all unit and integration tests) and verify all pass
- [ ] T058 [P] Review Verilog code for clarity and simplicity (per Constitution: Simplicity Over Performance)
- [ ] T059 [P] Add inline comments explaining clock domain crossing in gpu_graphics_core.v
- [ ] T060 [P] Add inline comments explaining dual-port RAM usage in gpu_graphics_vram.v
- [ ] T061 Run Yosys synthesis on graphics GPU modules and verify block RAM inference (check synthesis report for EBR usage)
- [ ] T062 Verify VRAM uses <5% of block RAM resources per SC-005 (32KB = 3.6% of 896KB)
- [ ] T063 Run timing analysis and verify 25 MHz pixel clock timing is met
- [ ] T064 [P] Update main project README with graphics GPU feature overview
- [ ] T065 [P] Create GPU usage tutorial in docs/user_guides/graphics_gpu_quickstart.md (based on quickstart.md)
- [ ] T066 [P] Update register map documentation in docs/gpu_register_map.md with complete 0xC100-0xC10F register descriptions
- [ ] T067 Generate waveforms for key operations (burst write, page flip, VBlank interrupt) and save to docs/timing/
- [ ] T068 Final validation: Build complete system, test all user stories end-to-end, verify no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion (needs VRAM and registers)
- **User Story 4 (Phase 5)**: Depends on User Story 1 completion (palette already implemented)
- **User Story 3 (Phase 6)**: Depends on User Story 1 AND 2 completion (needs display and fast writes)
- **Mode Switching (Phase 7)**: Depends on all user stories being complete
- **Polish (Phase 8)**: Depends on all previous phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - **THIS IS THE MVP**
- **User Story 2 (P2)**: Depends on US1 (needs VRAM_ADDR and VRAM_DATA registers to extend with burst mode)
- **User Story 4 (P2)**: Depends on US1 (palette module already implemented, just needs validation)
- **User Story 3 (P3)**: Depends on US1 AND US2 (needs display working AND fast writes for rendering off-screen pages)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD principle)
- Unit tests before integration tests
- Module implementation before integration
- All tests for a story must pass before story is considered complete
- Story complete before moving to next priority

### Parallel Opportunities

#### Phase 1: Setup
- All 3 tasks can run in parallel (verification tasks)

#### Phase 2: Foundational
- T005, T006, T007 can run in parallel (review and documentation tasks)

#### Phase 3: User Story 1 - Tests
- T008, T009, T010, T011, T012 can all run in parallel (different test files)

#### Phase 3: User Story 1 - Implementation
- T013, T014 can run in parallel (VRAM and palette are independent modules)
- T015, T016 can run in parallel after T013/T014 (registers and renderer are independent)
- T022, T023 can run in parallel (documentation tasks)

#### Phase 4: User Story 2 - Tests
- T024 is single test (no parallelization)

#### Phase 5: User Story 4 - Tests
- T029 is single test (no parallelization)

#### Phase 6: User Story 3 - Tests
- T034, T035 can run in parallel (different test scenarios)

#### Phase 6: User Story 3 - Implementation
- T036, T037, T038-T040 should run sequentially (interdependent)
- T044, T047 can run in parallel (testing and documentation)

#### Phase 7: Mode Switching
- T048, T049 can run in parallel (different test files)
- T050, T051, T052, T053, T054 can run in parallel (different validation checks)

#### Phase 8: Polish
- T057, T058, T059, T060, T064, T065, T066 can all run in parallel (independent review/doc tasks)

### Full Dependency Graph

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
Phase 3 (User Story 1: Single-Page Graphics Display) ← MVP CHECKPOINT
    ↓
    ├─→ Phase 4 (User Story 2: Burst Write Mode)
    ├─→ Phase 5 (User Story 4: Palette Programming)
    └─→ Phase 6 (User Story 3: Page Flipping) ← requires US1 + US2
            ↓
        Phase 7 (Mode Switching & Edge Cases)
            ↓
        Phase 8 (Polish & Final Validation)
```

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (MANDATORY per TDD):
Task T008: "Create unit test for VRAM module in tests/unit/test_gpu_vram.py"
Task T009: "Create unit test for palette module in tests/unit/test_gpu_palette.py"
Task T010: "Create unit test for graphics registers in tests/unit/test_gpu_graphics_registers.py"
Task T011: "Create unit test for pixel renderer in tests/unit/test_gpu_pixel_renderer.py"
Task T012: "Create integration test for full framebuffer display in tests/integration/test_gpu_graphics_framebuffer.py"

# After tests written and failing, launch independent modules in parallel:
Task T013: "Implement 32KB dual-port VRAM module in rtl/peripherals/video/gpu_graphics_vram.v"
Task T014: "Implement 16-entry RGB444 palette module in rtl/peripherals/video/gpu_graphics_palette.v"

# After T013 and T014 complete, launch next layer in parallel:
Task T015: "Implement graphics register file in rtl/peripherals/video/gpu_graphics_registers.v"
Task T016: "Implement pixel renderer module in rtl/peripherals/video/gpu_pixel_renderer.v"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify tools and structure)
2. Complete Phase 2: Foundational (review existing code, document plan)
3. Complete Phase 3: User Story 1 (write tests, implement modules, verify)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. **MVP ACHIEVED**: Basic graphics display works in all three modes (1/2/4 BPP)
6. Demo/validate with stakeholders before proceeding

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP DEMO** (basic graphics)
3. Add User Story 2 → Test independently → **Demo v2** (fast bulk transfers)
4. Add User Story 4 → Test independently → **Demo v3** (custom palettes)
5. Add User Story 3 → Test independently → **Demo v4** (smooth animations)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - All developers work on User Story 1 together (MVP first)
3. After MVP complete:
   - Developer A: User Story 2 (burst mode)
   - Developer B: User Story 4 (palette validation)
   - Developer C: User Story 3 (page flipping) - starts after US2 done
4. Stories complete and integrate independently

---

## Task Summary

**Total Tasks**: 68

**Tasks by Phase**:
- Phase 1 (Setup): 3 tasks
- Phase 2 (Foundational): 4 tasks
- Phase 3 (User Story 1): 16 tasks
- Phase 4 (User Story 2): 5 tasks
- Phase 5 (User Story 4): 5 tasks
- Phase 6 (User Story 3): 14 tasks
- Phase 7 (Mode Switching): 9 tasks
- Phase 8 (Polish): 12 tasks

**Parallel Opportunities**: 30+ tasks can run in parallel within their phases

**Independent Test Criteria**:
- **US1**: Write test pattern to VRAM, verify display output matches (tests T008-T012, validation T020-T021)
- **US2**: Write 8KB framebuffer using burst mode, verify <100ms (test T024, validation T027)
- **US4**: Program palette colors, verify displayed colors match RGB444 values (test T029, validation T032)
- **US3**: Render to two pages, flip during VBlank, verify no tearing (tests T034-T035, validation T045-T046)

**Suggested MVP Scope**: User Story 1 only (Phase 1 + Phase 2 + Phase 3 = 23 tasks)

**TDD Compliance**: ✅ All user stories have mandatory tests written BEFORE implementation

---

## Notes

- [P] tasks = different files, no dependencies (can run in parallel)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD red-green-refactor cycle)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Follow RetroCPU Constitution: Test-Driven Design, Simplicity Over Performance, Module Reusability, Educational Clarity
- All Verilog code should include inline comments explaining "why" not just "what"
- Use `(* ram_style = "block" *)` synthesis directive for VRAM to ensure block RAM inference
- Document all clock domain crossings with dual-flop synchronizer pattern
