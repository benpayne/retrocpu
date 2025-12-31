---

description: "Task list for DVI Character Display GPU implementation"
---

# Tasks: DVI Character Display GPU

**Input**: Design documents from `/specs/003-hdmi-character-display/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/register_map.md, quickstart.md

**Tests**: This feature follows Test-Driven Development (TDD) - cocotb tests are written FIRST for each module before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US4)
- Include exact file paths in descriptions

## Path Conventions

- **FPGA/HDL project**: `rtl/` for Verilog modules, `tests/` for cocotb tests, `firmware/` for assembly programs
- **Module organization**: `rtl/peripherals/video/`, `rtl/system/`, `rtl/test/`
- **Test organization**: `tests/unit/` for module tests, `tests/integration/` for system tests, `tests/hardware/` for board tests
- **Documentation**: `docs/modules/`, `docs/timing/`, `docs/learning/`

---

## Phase 0: Hardware Validation (CRITICAL FIRST STEP)

**Purpose**: Validate hardware capabilities and DVI signal generation using reference implementation BEFORE building character display

**⚠️ USER REQUIREMENT**: This phase MUST be completed first to prove out hardware and learn from working code

- [ ] T001 Clone reference DVI implementation from https://github.com/splinedrive/my_hdmi_device to /tmp/my_hdmi_device
- [ ] T002 Study reference code structure and identify key modules (TMDS encoder, video timing, PLL configuration)
- [ ] T003 Document pinout mapping from reference code to Colorlight i5 carrier board in docs/hardware/pinout_mapping.md
- [ ] T004 Build reference implementation using yosys/nextpnr-ecp5 toolchain (follow reference repo build instructions)
- [ ] T005 Program Colorlight i5 board with reference bitstream using openFPGALoader
- [ ] T006 Validate DVI signal detection on test monitor (verify monitor displays reference pattern/image)
- [ ] T007 Document working PLL configuration and synthesis settings in docs/hardware/reference_config.md
- [ ] T008 Extract and document TMDS/LVDS primitive usage patterns from reference code in docs/learning/how_dvi_works.md

**Checkpoint**: Hardware validated - Monitor displays DVI signal from board. Ready to adapt for character display.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and development environment setup

- [ ] T009 Create directory structure per plan.md (rtl/peripherals/video/, tests/unit/, tests/integration/, firmware/gpu/, docs/)
- [ ] T010 [P] Create VGA timing reference documentation in docs/timing/vga_640x480_60hz.md (horizontal/vertical timing tables)
- [ ] T011 [P] Create font data file with 8x16 font for ASCII 0x20-0x7F in rtl/peripherals/video/font_data.hex
- [ ] T012 [P] Define placeholder glyph (solid block) for non-printable characters in font_data.hex
- [ ] T013 Configure cocotb test environment with Icarus Verilog in tests/Makefile.common
- [ ] T014 [P] Document memory map allocation (0xC010-0xC016 GPU registers) in docs/modules/register_interface.md

**Checkpoint**: Project structure ready, font data available, test framework configured

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core DVI infrastructure and clock generation that BLOCKS all user story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T015 Adapt PLL configuration from reference code for 25.175 MHz pixel clock and 251.75 MHz TMDS clock in rtl/system/clock_pll.v
- [ ] T016 Create clock domain crossing synchronizer module for CPU-to-pixel domain in rtl/peripherals/video/cdc_synchronizer.v
- [ ] T017 Adapt TMDS encoder module from reference code in rtl/peripherals/video/tmds_encoder.v
- [ ] T018 Adapt DVI transmitter with LVDS primitives from reference code in rtl/peripherals/video/dvi_transmitter.v (using ECP5 ODDRX2F)
- [ ] T019 Document clock domain crossing strategy and timing constraints in docs/timing/clock_domains.md

**Checkpoint**: Foundation ready - Clock generation and DVI signal output infrastructure complete. User story implementation can now begin.

---

## Phase 3: User Story 4 - DVI Signal Generation (Priority: P1) 🎯 MVP Part 1

**Goal**: Generate valid DVI video signals at 640x480 @ 60Hz that monitors can detect and display

**Independent Test**: Connect monitor to HDMI output and verify sync/detection occurs with stable blank screen or test pattern

### Tests for User Story 4 (Write FIRST, ensure they FAIL)

- [ ] T020 [P] [US4] Write cocotb unit test for video_timing.v in tests/unit/test_video_timing.py (verify hsync/vsync/DE timing, pixel counters)
- [ ] T021 [P] [US4] Write hardware validation test plan in tests/hardware/test_dvi_output.md (monitor detection checklist, visual inspection criteria)

### Implementation for User Story 4

- [ ] T022 [US4] Create video_timing.v module generating 640x480 @ 60Hz timing signals in rtl/peripherals/video/video_timing.v
- [ ] T023 [US4] Create simple test pattern generator (color bars or checkerboard) in rtl/test/dvi_test.v
- [ ] T024 [US4] Integrate dvi_test.v with video_timing, TMDS encoder, and DVI transmitter in rtl/test/dvi_test_top.v
- [ ] T025 [US4] Run cocotb test_video_timing.py and verify timing parameters match VGA spec (800x525 total, correct blanking intervals)
- [ ] T026 [US4] Synthesize dvi_test_top.v for Colorlight i5 using yosys/nextpnr-ecp5 (adapt build from Phase 0 reference)
- [ ] T027 [US4] Program board and validate monitor detection and stable test pattern display (SUCCESS CRITERIA: Monitor shows stable image)
- [ ] T028 [US4] Document DVI signal generation architecture and timing in docs/modules/dvi_timing.md

**Checkpoint**: Monitor displays stable DVI test pattern from Colorlight i5 board. Video infrastructure proven working.

---

## Phase 4: User Story 1 - Basic Character Output (Priority: P1) 🎯 MVP Part 2

**Goal**: Write ASCII characters to video memory and see them displayed on monitor (completes MVP with US4)

**Independent Test**: Write single character 'A' (0x41) to CHAR_DATA register and verify it appears at screen position

### Tests for User Story 1 (Write FIRST, ensure they FAIL)

- [ ] T029 [P] [US1] Write cocotb unit test for character_buffer.v in tests/unit/test_character_buffer.py (dual-port RAM write/read, addressing)
- [ ] T030 [P] [US1] Write cocotb unit test for font_rom.v in tests/unit/test_font_rom.py (font data integrity, character indexing)
- [ ] T031 [P] [US1] Write cocotb unit test for character_renderer.v in tests/unit/test_character_renderer.py (char-to-pixel conversion, scanline rendering)
- [ ] T032 [P] [US1] Write cocotb unit test for gpu_registers.v in tests/unit/test_gpu_registers.py (register writes, auto-increment, wrap behavior)
- [ ] T033 [US1] Write cocotb integration test for character display in tests/integration/test_gpu_character_output.py (write char, verify pixel data)

### Implementation for User Story 1

- [ ] T034 [P] [US1] Create character_buffer.v dual-port RAM module in rtl/peripherals/video/character_buffer.v (40x30 = 1200 bytes, mode-switchable)
- [ ] T035 [P] [US1] Create font_rom.v module loading font_data.hex in rtl/peripherals/video/font_rom.v (96 chars x 16 bytes = 1536 bytes)
- [ ] T036 [P] [US1] Create character_renderer.v scanline pixel generator in rtl/peripherals/video/character_renderer.v (fetch char, lookup font, output pixels)
- [ ] T037 [US1] Create gpu_registers.v memory-mapped register interface in rtl/peripherals/video/gpu_registers.v (CHAR_DATA at 0xC010, CURSOR_X/Y, auto-advance)
- [ ] T038 [US1] Integrate character_buffer, font_rom, character_renderer, gpu_registers with video_timing in rtl/peripherals/video/gpu_core.v
- [ ] T039 [US1] Create gpu_top.v integrating gpu_core with DVI transmitter and clock domains in rtl/peripherals/video/gpu_top.v
- [ ] T040 [US1] Run all Unit tests (T029-T032) and verify they pass (RED → GREEN verification)
- [ ] T041 [US1] Run integration test test_gpu_character_output.py and verify character rendering works in simulation
- [ ] T042 [US1] Integrate gpu_top into soc_top.v with CPU memory bus in rtl/system/soc_top.v
- [ ] T043 [US1] Write firmware test program in firmware/gpu/gpu_test.s (write "Hello World" string via CHAR_DATA register)
- [ ] T044 [US1] Synthesize full system, program board, and verify "Hello World" appears on monitor (VISUAL VALIDATION)
- [ ] T045 [US1] Test line wrap behavior (write 41 chars in 40-col mode) and verify cursor wraps to next line
- [ ] T046 [US1] Document character rendering pipeline in docs/modules/character_rendering.md (fetch, decode, render stages)

**Checkpoint**: 🎉 MVP COMPLETE - Can write text to screen via register writes. Monitor displays readable characters.

---

## Phase 5: User Story 3 - Screen Control Operations (Priority: P2)

**Goal**: Clear screen, move cursor to specific positions, control text placement

**Independent Test**: Write characters, issue clear screen command, verify all positions blank. Set cursor position, verify next char appears there.

### Tests for User Story 3 (Write FIRST, ensure they FAIL)

- [ ] T047 [P] [US3] Extend test_gpu_registers.py to test CONTROL register clear screen command (write 0x01, verify buffer cleared)
- [ ] T048 [P] [US3] Extend test_gpu_registers.py to test CURSOR_X/Y position setting (set position, verify next write goes there)
- [ ] T049 [US3] Write cocotb test for screen scrolling in tests/unit/test_gpu_scrolling.py (fill screen, write one more line, verify top line gone)

### Implementation for User Story 3

- [ ] T050 [US3] Add CONTROL register (0xC012) with clear screen command bit (bit 0) to gpu_registers.v
- [ ] T051 [US3] Add CURSOR_X (0xC013) and CURSOR_Y (0xC014) position registers to gpu_registers.v
- [ ] T052 [US3] Implement clear screen logic in gpu_registers.v (set all char_buffer positions to 0x20 space character)
- [ ] T053 [US3] Implement position bounds checking and clamping in gpu_registers.v (40-col: X<40, Y<30; 80-col: X<80, Y<30)
- [ ] T054 [US3] Implement automatic scrolling when cursor advances past last row in gpu_registers.v (move buffer up, clear bottom line)
- [ ] T055 [US3] Run unit tests (T047-T049) and verify clear, positioning, and scrolling work correctly
- [ ] T056 [US3] Write firmware demo program in firmware/gpu/gpu_demo.s (clear screen, position cursor, write formatted text)
- [ ] T057 [US3] Synthesize, program board, and verify clear/position/scroll operations work on hardware
- [ ] T058 [US3] Document control operations and timing in docs/modules/register_interface.md

**Checkpoint**: Screen control fully functional - clear, position, scroll work on hardware

---

## Phase 6: User Story 2 - Display Mode Configuration (Priority: P2)

**Goal**: Switch between 40-column and 80-column display modes

**Independent Test**: Set 80-col mode via control register, write 80 chars, verify no wrap until char 81

### Tests for User Story 2 (Write FIRST, ensure they FAIL)

- [ ] T059 [P] [US2] Write cocotb test for mode switching in tests/integration/test_gpu_mode_switching.py (set mode bit, verify column count, verify clear on switch)
- [ ] T060 [P] [US2] Extend test_character_buffer.py to test 80-column addressing (verify 80x30 buffer access)

### Implementation for User Story 2

- [ ] T061 [US2] Add mode select bit (bit 1) to CONTROL register in gpu_registers.v (0=40col, 1=80col)
- [ ] T062 [US2] Modify character_buffer.v to support both 40x30 (1200 bytes) and 80x30 (2400 bytes) addressing modes
- [ ] T063 [US2] Modify character_renderer.v to adjust character fetch timing for 40-col vs 80-col modes
- [ ] T064 [US2] Implement mode switch behavior in gpu_registers.v (clear screen, reset cursor to 0,0 on mode change per FR-022)
- [ ] T065 [US2] Set default mode to 40-column on reset/power-up in gpu_registers.v (per FR-021)
- [ ] T066 [US2] Run unit and integration tests (T059-T060) and verify mode switching works correctly
- [ ] T067 [US2] Write firmware test in firmware/gpu/gpu_test.s to test mode switching (write text, switch mode, verify clear, write more text)
- [ ] T068 [US2] Synthesize, program board, and verify both 40-col and 80-col modes display correctly on monitor
- [ ] T069 [US2] Document mode switching behavior and timing in docs/modules/register_interface.md

**Checkpoint**: Display mode switching works - Both 40-col and 80-col modes functional on hardware

---

## Phase 7: User Story 6 - Color Configuration (Priority: P2)

**Goal**: Configure foreground and background colors for text display

**Independent Test**: Write color values to color registers, write characters, verify colors on screen

### Tests for User Story 6 (Write FIRST, ensure they FAIL)

- [ ] T070 [P] [US6] Write cocotb unit test for color_palette.v in tests/unit/test_color_palette.py (3-bit to 24-bit RGB expansion)
- [ ] T071 [P] [US6] Write cocotb integration test for color application in tests/integration/test_gpu_color_modes.py (set colors, verify pixel RGB values)
- [ ] T072 [P] [US6] Extend test_gpu_registers.py to test color register writes and bit masking (verify upper bits ignored)

### Implementation for User Story 6

- [ ] T073 [P] [US6] Create color_palette.v module for 3-bit RGB to 24-bit expansion in rtl/peripherals/video/color_palette.v (8 colors: Black, Blue, Green, Cyan, Red, Magenta, Yellow, White)
- [ ] T074 [US6] Add FG_COLOR (0xC015) and BG_COLOR (0xC016) registers to gpu_registers.v (3-bit values, mask upper bits per FR-016/FR-017)
- [ ] T075 [US6] Integrate color_palette.v into character_renderer.v (apply FG color to character pixels, BG color to background)
- [ ] T076 [US6] Set default colors to white foreground (0x07), black background (0x00) on reset in gpu_registers.v (per FR-018)
- [ ] T077 [US6] Run unit and integration tests (T070-T072) and verify color application works correctly
- [ ] T078 [US6] Write firmware demo in firmware/gpu/gpu_demo.s showcasing all 8 colors (write text in each color)
- [ ] T079 [US6] Synthesize, program board, and verify colors display correctly on monitor (all 8 FG/BG combinations)
- [ ] T080 [US6] Document color palette and register usage in docs/modules/register_interface.md

**Checkpoint**: Color configuration works - All 8 colors render correctly on hardware

---

## Phase 8: User Story 5 - Visual Cursor Display (Priority: P2)

**Goal**: Display flashing cursor at current input position

**Independent Test**: Observe cursor flashing at ~1Hz at cursor position, verify it moves when cursor position changes

### Tests for User Story 5 (Write FIRST, ensure they FAIL)

- [ ] T081 [P] [US5] Write cocotb unit test for cursor_controller.v in tests/unit/test_cursor_controller.py (flash timing, position tracking, enable/disable)
- [ ] T082 [P] [US5] Write cocotb integration test for cursor rendering in tests/integration/test_gpu_character_output.py (verify cursor pixels override char pixels)

### Implementation for User Story 5

- [ ] T083 [US5] Create cursor_controller.v module with flash timer and position tracking in rtl/peripherals/video/cursor_controller.v (~1Hz flash from pixel clock or frame counter)
- [ ] T084 [US5] Add cursor enable bit (bit 2) to CONTROL register in gpu_registers.v (1=enabled, 0=disabled)
- [ ] T085 [US5] Integrate cursor_controller.v into character_renderer.v (override pixels at cursor position when flash state is visible)
- [ ] T086 [US5] Implement cursor rendering as solid block with inverted colors in character_renderer.v (per FR-020)
- [ ] T087 [US5] Enable cursor by default on reset in gpu_registers.v
- [ ] T088 [US5] Run unit and integration tests (T081-T082) and verify cursor display and flash timing
- [ ] T089 [US5] Write firmware demo in firmware/gpu/gpu_demo.s demonstrating cursor movement and enable/disable
- [ ] T090 [US5] Synthesize, program board, and verify cursor flashes at correct rate and position on monitor
- [ ] T091 [US5] Document cursor behavior and control in docs/modules/register_interface.md

**Checkpoint**: Cursor display complete - Flashing cursor visible and controllable on hardware

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, optimization, and validation across all user stories

- [ ] T092 [P] Create comprehensive quickstart tutorial in docs/quickstart_tutorial.md (hardware setup, firmware examples, troubleshooting)
- [ ] T093 [P] Write educational document explaining DVI/TMDS basics in docs/learning/how_dvi_works.md (expand from Phase 0 notes)
- [ ] T094 [P] Write educational document on character display architecture in docs/learning/character_display_basics.md
- [ ] T095 [P] Create timing diagrams for character rendering pipeline in docs/timing/rendering_pipeline.md
- [ ] T096 [P] Document all edge cases and their handling in docs/edge_cases.md (fast writes, extended ASCII, cable disconnect, etc.)
- [ ] T097 Code review and refactoring for clarity per Simplicity principle (review all modules, simplify state machines if needed)
- [ ] T098 Run full synthesis and verify timing constraints met (check setup/hold timing, clock domain crossings)
- [ ] T099 Measure FPGA resource utilization (LUTs, EBR blocks, verify within budget: <24K LUTs, <56 EBR)
- [ ] T100 [P] Test edge case: Write characters at >1000 chars/sec and verify no dropped characters (per SC-009)
- [ ] T101 [P] Test edge case: Extended ASCII (0x80-0xFF) displays as placeholder glyph
- [ ] T102 [P] Test edge case: Same FG/BG color (text becomes invisible but system doesn't crash)
- [ ] T103 Long-duration stability test (run for 1 hour with continuous display, verify no signal loss per SC-003)
- [ ] T104 Multi-monitor compatibility test (test with 3+ different monitors/brands)
- [ ] T105 Create demo video showing all features (character write, colors, modes, cursor, scrolling)
- [ ] T106 Update CLAUDE.md with DVI/GPU technologies and patterns learned

**Checkpoint**: Feature complete, documented, validated, and ready for production use

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Hardware Validation)**: MUST complete first - proves hardware works
- **Phase 1 (Setup)**: Can start after Phase 0 - no dependencies on Phase 0, but learn from it
- **Phase 2 (Foundational)**: Depends on Phase 0 and Phase 1 - BLOCKS all user stories
- **Phase 3 (US4 - DVI)**: Depends on Phase 2 completion - part of MVP
- **Phase 4 (US1 - Characters)**: Depends on Phase 3 completion - completes MVP with US4
- **Phase 5-8 (US3, US2, US6, US5)**: All depend on Phase 4 completion
  - These user stories can proceed in parallel (if team capacity allows)
  - Or sequentially in recommended order: US3 → US2 → US6 → US5
- **Phase 9 (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US4 (DVI Signal, P1)**: No dependencies on other stories - foundational
- **US1 (Character Output, P1)**: Depends on US4 (needs working DVI) - completes MVP
- **US3 (Screen Control, P2)**: Depends on US1 (needs character display working)
- **US2 (Mode Switch, P2)**: Depends on US1 (needs character display working) - can run parallel with US3
- **US6 (Color Config, P2)**: Depends on US1 (needs character display working) - can run parallel with US2/US3
- **US5 (Cursor Display, P2)**: Depends on US1 (needs character display working) - can run parallel with US2/US3/US6

### Within Each User Story

- Tests MUST be written FIRST and FAIL before implementation (TDD)
- Core modules before integration modules
- Unit tests pass before integration tests
- Simulation validation before hardware synthesis
- Hardware validation completes story

### Parallel Opportunities

**Phase 0**: Sequential (hardware validation must be done in order to learn)

**Phase 1 (Setup)**: All tasks marked [P] can run in parallel:
- T010 (VGA timing docs), T011 (font data), T012 (placeholder glyph), T014 (memory map docs)

**Phase 2 (Foundational)**: Sequential (each task depends on previous understanding)

**Phase 3 (US4)**:
- Tests T020, T021 can run in parallel

**Phase 4 (US1)**:
- Tests T029, T030, T031, T032 can run in parallel
- Implementation: T034, T035, T036 can run in parallel (different modules)

**Phase 5 (US3)**:
- Tests T047, T048, T049 can run in parallel

**Phase 6 (US2)**:
- Tests T059, T060 can run in parallel

**Phase 7 (US6)**:
- Tests T070, T071, T072 can run in parallel
- Implementation: T073 can run in parallel with T074

**Phase 8 (US5)**:
- Tests T081, T082 can run in parallel

**Phase 9 (Polish)**:
- Documentation tasks T092, T093, T094, T095, T096 can run in parallel
- Test tasks T100, T101, T102 can run in parallel

**Cross-Phase Parallelism**: After Phase 4 (MVP) complete, US3, US2, US6, US5 can all be worked on in parallel by different team members.

---

## Parallel Example: MVP (US4 + US1)

```bash
# Phase 3 (US4) - Tests first:
Task: "Write cocotb unit test for video_timing.v"
Task: "Write hardware validation test plan"

# Phase 4 (US1) - All unit tests together:
Task: "Write test for character_buffer.v in tests/unit/test_character_buffer.py"
Task: "Write test for font_rom.v in tests/unit/test_font_rom.py"
Task: "Write test for character_renderer.v in tests/unit/test_character_renderer.py"
Task: "Write test for gpu_registers.v in tests/unit/test_gpu_registers.py"

# Phase 4 (US1) - Independent modules together:
Task: "Create character_buffer.v in rtl/peripherals/video/character_buffer.v"
Task: "Create font_rom.v in rtl/peripherals/video/font_rom.v"
Task: "Create character_renderer.v in rtl/peripherals/video/character_renderer.v"
```

---

## Implementation Strategy

### MVP First (US4 + US1 Only)

1. ✅ Complete Phase 0: Hardware Validation (CRITICAL)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (BLOCKS all stories)
4. Complete Phase 3: User Story 4 (DVI signals working)
5. Complete Phase 4: User Story 1 (Character display working)
6. **STOP and VALIDATE**: Monitor displays "Hello World"
7. 🎉 **MVP COMPLETE** - Demo-able retro computer with text output!

### Incremental Delivery

1. Phase 0 → Hardware proven working with reference code
2. Phases 1-2 → Foundation ready for GPU development
3. Phases 3-4 → MVP: Display text on monitor via memory-mapped registers
4. Phase 5 → Add screen control (clear, position, scroll) → Demo again
5. Phase 6 → Add 80-column mode → Demo again
6. Phase 7 → Add colors → Demo again
7. Phase 8 → Add cursor → Demo again
8. Phase 9 → Polish and document → Production ready

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0-2 together (foundation)
2. Team completes Phase 3-4 together (MVP focus)
3. Once MVP done (Phase 4 complete):
   - Developer A: User Story 3 (Screen Control)
   - Developer B: User Story 2 (Mode Switching)
   - Developer C: User Story 6 (Colors)
   - Developer D: User Story 5 (Cursor)
4. Stories complete and integrate independently
5. Team does Phase 9 (Polish) together

---

## Success Criteria Mapping

- **SC-001, SC-002, SC-004**: Phase 3 (US4) - DVI signal generation and stability
- **SC-003, SC-005**: Phase 4 (US1) - Character display and rendering
- **SC-006, SC-007**: Phase 5 (US3) - Screen control operations
- **SC-008**: Phase 6 (US2) - Mode switching timing
- **SC-009**: Phase 9 (Polish) - Performance edge case test (T100)
- **SC-010, SC-011**: Phase 8 (US5) - Cursor display and control
- **SC-012, SC-013, SC-014**: Phase 7 (US6) - Color configuration
- **SC-015**: Phase 6 (US2) - Default mode verification
- **SC-016**: Phase 1 (Setup) + Phase 4 (US1) - Placeholder glyph

---

## Notes

- **[P]** tasks = different files, no dependencies, can run in parallel
- **[Story]** label (e.g., [US1], [US4]) maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD**: Verify tests FAIL before implementing (RED → GREEN → REFACTOR)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Hardware-first approach**: Phase 0 is critical - learn from working reference code
- **Simplicity**: Keep modules clean, well-commented, and educationally clear
- **Educational value**: Document learnings and patterns for future developers

---

**Total Tasks**: 106
**MVP Tasks**: 46 (Phase 0-4: T001-T046)
**Parallel Opportunities**: 25+ tasks can run in parallel within their phases
**Test Tasks**: 21 (following TDD principle)
**Independent Stories**: 5 (US4, US1, US3, US2, US6, US5 all independently testable)

**Suggested MVP Scope**: Phase 0 + Phase 1 + Phase 2 + Phase 3 (US4) + Phase 4 (US1) = 46 tasks
**MVP Deliverable**: Retro computer with DVI text output - write characters via memory-mapped registers, see them on monitor
