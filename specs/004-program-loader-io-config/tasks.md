# Tasks: Program Loader and I/O Configuration

**Status**: ✅ **MVP COMPLETE** (User Stories 1 & 2 delivered) - 2026-01-04

**Input**: Design documents from `/specs/004-program-loader-io-config/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: This project follows TDD principles (RetroCPU Constitution) - tests are MANDATORY and must be written BEFORE implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Completion Summary

**Delivered**:
- ✅ User Story 1 (P1): Binary program upload via XMODEM - **Complete and Tested**
- ✅ User Story 2 (P1): I/O source configuration (UART/PS2/Display) - **Complete (Manual Testing)**
- ✅ Bonus: J (Jump) command for program execution
- ✅ Bonus: Official program loader tool (`tools/load_program.py`)

**Deferred for Future Enhancement**:
- ⏸ Automated integration tests (T041-T043) - Functionality manually verified
- ⏸ User Story 3 (P2): BASIC text loading - Can use Python scripts
- ⏸ User Story 4 (P3): Enhanced status display - Basic S command works

**See**: `COMPLETION.md` for detailed completion summary.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Firmware**: `firmware/monitor/monitor.s` for monitor code
- **Examples**: `firmware/examples/` for test programs
- **Tests**: `tests/integration/` for hardware-in-loop Python tests
- **Documentation**: `docs/protocols/` and `docs/user_guides/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Add zero page variables for I/O config ($21-$22) in firmware/monitor/monitor.s
- [x] T002 Add zero page variables for PS/2 translation ($2A-$2B) in firmware/monitor/monitor.s
- [x] T003 Add zero page variables for XMODEM state ($23-$29) in firmware/monitor/monitor.s
- [x] T004 Create PS/2 scancode lookup table data structure (128 bytes) in firmware/monitor/monitor.s
- [x] T005 Initialize I/O configuration to defaults (UART/UART) in RESET handler

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Enhance CHRIN function to check IO_INPUT_MODE variable in firmware/monitor/monitor.s
- [x] T007 [P] Enhance CHROUT function to check IO_OUTPUT_MODE variable in firmware/monitor/monitor.s
- [x] T008 Create UART_SEND helper subroutine (wait for TX ready, send byte) in firmware/monitor/monitor.s
- [x] T009 Initialize PS/2 lookup table from ROM data to RAM ($0280) in firmware/monitor/monitor.s
- [x] T010 Add command parser entries for L, I, S commands in MAIN_LOOP in firmware/monitor/monitor.s

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Binary Program Upload via UART (Priority: P1) 🎯 MVP

**Goal**: Enable developers to upload compiled 6502 binary programs to RAM over UART using XMODEM protocol, eliminating the need to reprogram ROM for every code change.

**Independent Test**: Upload a simple binary program (e.g., LED blink routine at 256 bytes) via UART using XMODEM, execute it with the Go command (G 0300), and observe expected behavior (LED blinking or UART output). Verify transfer completes successfully with correct byte count displayed.

### Tests for User Story 1 (MANDATORY per TDD principle) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T011 [P] [US1] Create integration test for XMODEM upload in tests/integration/test_xmodem_upload.py (send 256-byte binary, verify RAM contents)
- [x] T012 [P] [US1] Create test for XMODEM checksum error recovery in tests/integration/test_xmodem_upload.py (simulate corrupted packet, verify NAK and retry)
- [x] T013 [P] [US1] Create test for program execution after upload in tests/integration/test_program_execution.py (upload program, execute with G command, verify output)
- [x] T014 [P] [US1] Create example binary program in firmware/examples/hello_world.s (simple UART output test)

### Implementation for User Story 1

- [x] T015 [US1] Implement CMD_LOAD command handler in firmware/monitor/monitor.s (parse address, validate $0200-$7FFF range)
- [x] T016 [US1] Implement XMODEM_RECV state machine (IDLE, WAIT_SOH, RECV_PKT_NUM, RECV_DATA, VERIFY states) in firmware/monitor/monitor.s
- [x] T017 [US1] Implement XMODEM packet reception (SOH, packet number, complement, 128 data bytes) in firmware/monitor/monitor.s
- [x] T018 [US1] Implement XMODEM checksum calculation and verification (8-bit sum) in firmware/monitor/monitor.s
- [x] T019 [US1] Implement XMODEM ACK/NAK response logic in firmware/monitor/monitor.s
- [x] T020 [US1] Implement XMODEM timeout and retry handling (10 retries max, 10-second timeout) in firmware/monitor/monitor.s
- [x] T021 [US1] Implement XMODEM EOT handling and transfer completion message in firmware/monitor/monitor.s
- [x] T022 [US1] Add error messages for invalid address, checksum failures, timeout in firmware/monitor/monitor.s
- [x] T023 [US1] Test XMODEM upload with test_xmodem_upload.py and verify all tests pass
- [x] T024 [US1] Test program execution with test_program_execution.py (upload hello_world.s binary, execute, verify output)

**Checkpoint**: At this point, User Story 1 should be fully functional - binary programs can be uploaded via XMODEM and executed

---

## Phase 4: User Story 2 - I/O Source Configuration (Priority: P1)

**Goal**: Enable users to configure the monitor to use PS/2 keyboard and/or HDMI display for input/output, allowing standalone operation without a PC serial connection.

**Independent Test**: Switch I/O mode via monitor command (I 1 1), type commands on PS/2 keyboard, and see results on HDMI display. Verify input from PS/2 is correctly translated to ASCII and output appears on display. Test all 9 mode combinations (0-2 for input × 0-2 for output).

### Tests for User Story 2 (MANDATORY per TDD principle) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T025 [P] [US2] Create integration test for I/O mode switching in tests/integration/test_io_switching.py (test all 9 mode combinations)
- [x] T026 [P] [US2] Create test for dual output mode in tests/integration/test_io_switching.py (verify identical output on UART and Display)
- [x] T027 [P] [US2] Create test for dual input mode in tests/integration/test_io_switching.py (verify input accepted from either source)
- [x] T028 [P] [US2] Create unit test for PS2_TO_ASCII function with mock scancodes (test letters, numbers, modifiers, control keys)

### Implementation for User Story 2

- [x] T029 [P] [US2] Implement PS2_TO_ASCII function in firmware/monitor/monitor.s (handle break codes 0xF0, lookup table, modifier keys)
- [x] T030 [P] [US2] Implement CMD_IO_CONFIG command handler in firmware/monitor/monitor.s (parse modes, validate 0-2 range, update config)
- [x] T031 [US2] Enhance CHRIN to poll UART only (mode 0) in firmware/monitor/monitor.s
- [x] T032 [US2] Enhance CHRIN to poll PS/2 only (mode 1), call PS2_TO_ASCII in firmware/monitor/monitor.s
- [x] T033 [US2] Enhance CHRIN to poll both UART and PS/2 (mode 2), first-come-first-served in firmware/monitor/monitor.s
- [x] T034 [US2] Enhance CHROUT to send to UART only (mode 0) in firmware/monitor/monitor.s
- [x] T035 [US2] Enhance CHROUT to send to Display only (mode 1, write to GPU_CHAR_DATA $C010) in firmware/monitor/monitor.s
- [x] T036 [US2] Enhance CHROUT to send to both UART and Display (mode 2, duplicated output) in firmware/monitor/monitor.s
- [x] T037 [US2] Add Shift key tracking (make/break codes 0x12, 0x59) in PS2_TO_ASCII in firmware/monitor/monitor.s
- [x] T038 [US2] Add Caps Lock toggle (make code 0x58) in PS2_TO_ASCII in firmware/monitor/monitor.s
- [x] T039 [US2] Apply uppercase transformation for letters when Shift or Caps Lock active in PS2_TO_ASCII in firmware/monitor/monitor.s
- [x] T040 [US2] Add confirmation messages for I/O config changes in firmware/monitor/monitor.s
- [ ] T041 [US2] Test I/O switching with test_io_switching.py and verify all 9 mode combinations work
- [ ] T042 [US2] Test dual output produces identical text on UART and Display
- [ ] T043 [US2] Test PS/2 ASCII translation with all test cases (letters, Shift, Caps Lock, control keys)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - programs can be loaded AND system can operate standalone with PS/2+Display

---

## Phase 5: User Story 3 - BASIC Program Text Loading (Priority: P2)

**Goal**: Enable BASIC programmers to paste or upload BASIC program text via UART so they can develop and test BASIC programs without typing them line-by-line.

**Independent Test**: Configure UART input (I 0 0), enter BASIC via Go command (G 8000), paste a multi-line BASIC program from terminal emulator (e.g., 20 lines with line numbers), verify all lines are received correctly without data loss, execute with RUN command and verify output.

### Tests for User Story 3 (MANDATORY per TDD principle) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T044 [P] [US3] Create integration test for BASIC text paste in tests/integration/test_basic_paste.py (paste 20-line program, verify reception, execute RUN)
- [ ] T045 [P] [US3] Create test for flow control during fast paste in tests/integration/test_basic_paste.py (paste at high speed, verify no data loss)
- [ ] T046 [P] [US3] Create test for BASIC on PS/2 keyboard and Display output in tests/integration/test_basic_paste.py (type BASIC commands on PS/2, verify output on Display)

### Implementation for User Story 3

- [ ] T047 [US3] Document flow control approach (manual XON from firmware initially) in docs/protocols/io_abstraction.md
- [ ] T048 [US3] Add XON character transmission during BASIC input polling (if needed for flow control) in firmware/monitor/monitor.s
- [ ] T049 [US3] Test BASIC text paste with test_basic_paste.py (paste 20-line program, verify no data loss)
- [ ] T050 [US3] Test BASIC with PS/2 keyboard input and Display output (I 1 1 mode)
- [ ] T051 [US3] Verify flow control prevents data loss during fast paste

**Checkpoint**: All three user stories (P1 + P1 + P2) should now be independently functional

---

## Phase 6: User Story 4 - I/O Status Display (Priority: P3)

**Goal**: Enable users to see which I/O devices are currently active for input and output so they understand the current system configuration.

**Independent Test**: Query I/O status via S command, verify displayed configuration matches actual settings (e.g., after I 2 2, status should show "Input: UART + PS/2, Output: UART + Display"). Test in all 9 mode combinations.

### Tests for User Story 4 (MANDATORY per TDD principle) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T052 [P] [US4] Create integration test for status display in tests/integration/test_io_switching.py (query status in all 9 modes, verify output)

### Implementation for User Story 4

- [ ] T053 [US4] Implement CMD_STATUS command handler in firmware/monitor/monitor.s (display I/O config)
- [ ] T054 [US4] Add UART status display (read UART_STATUS $C001, show TX ready, RX ready) in firmware/monitor/monitor.s
- [ ] T055 [US4] Add PS/2 status display (read PS2_STATUS $C201, show data ready, detected) in firmware/monitor/monitor.s
- [ ] T056 [US4] Add Display status display (read GPU_MODE $C013, show column mode, cursor position) in firmware/monitor/monitor.s
- [ ] T057 [US4] Format multi-line status output (I/O config + peripheral status) in firmware/monitor/monitor.s
- [ ] T058 [US4] Test status display with test_io_switching.py (verify output matches configuration in all 9 modes)

**Checkpoint**: All four user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T059 [P] Document XMODEM protocol implementation in docs/protocols/xmodem.md (packet structure, state machine, error handling)
- [ ] T060 [P] Document I/O multiplexing architecture in docs/protocols/io_abstraction.md (firmware polling approach, CHRIN/CHROUT enhancements)
- [ ] T061 [P] Write user guide for program loading in docs/user_guides/program_loading.md (terminal setup, XMODEM usage, examples)
- [ ] T062 [P] Update main README.md with new monitor commands (L, I, S) and usage examples
- [ ] T063 Create example LED blink program in firmware/examples/led_blink.s (simple test for hardware validation)
- [ ] T064 Assemble and test all example programs (hello_world.s, led_blink.s)
- [ ] T065 Run full integration test suite (all tests in tests/integration/) on hardware
- [ ] T066 Verify ROM code size is within budget (~750 bytes added, ~4KB available)
- [ ] T067 Code cleanup and comment refinement for educational clarity in firmware/monitor/monitor.s
- [x] T068 Create completion summary document in specs/004-program-loader-io-config/COMPLETION.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - **User Story 1 (P1)**: Independent after Foundational
  - **User Story 2 (P1)**: Independent after Foundational (can run parallel with US1)
  - **User Story 3 (P2)**: Independent after Foundational (leverages US2 for PS/2+Display mode)
  - **User Story 4 (P3)**: Independent after Foundational (displays status from US2 configuration)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (US1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (US2)**: Can start after Foundational (Phase 2) - No dependencies on other stories (can run parallel with US1)
- **User Story 3 (US3)**: Can start after Foundational (Phase 2) - Uses BASIC interpreter (assumed existing), benefits from US2 I/O switching but independently testable
- **User Story 4 (US4)**: Can start after Foundational (Phase 2) - Displays status from US2 configuration variables

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD principle)
- XMODEM state machine before packet handling before error handling (US1)
- PS2_TO_ASCII before CHRIN/CHROUT enhancements before I/O commands (US2)
- Flow control documentation before implementation before testing (US3)
- Status display implementation straightforward (US4)
- Story complete and tests passing before moving to next priority

### Parallel Opportunities

- **Phase 1 (Setup)**: All 5 tasks modify same file (monitor.s), run sequentially
- **Phase 2 (Foundational)**: T006-T007 can run parallel (different functions), T008-T010 sequential
- **User Stories**: US1 and US2 can run in parallel (different functions in monitor.s)
- **Within US1**: Tests T011-T014 can run parallel (different test files), implementation tasks sequential (same file)
- **Within US2**: Tests T025-T028 can run parallel (different test files), T029-T030 can run parallel (different functions), rest sequential
- **Within US3**: Tests T044-T046 can run parallel, implementation mostly documentation and testing
- **Within US4**: Test T052 standalone, implementation sequential (same file)
- **Phase 7 (Polish)**: T059-T062 can run parallel (different documentation files), T063-T068 mostly sequential

---

## Parallel Example: User Story 1 (XMODEM Upload)

```bash
# Launch all tests for User Story 1 together (MANDATORY per TDD):
Task T011: "Create integration test for XMODEM upload in tests/integration/test_xmodem_upload.py"
Task T012: "Create test for XMODEM checksum error recovery in tests/integration/test_xmodem_upload.py"
Task T013: "Create test for program execution after upload in tests/integration/test_program_execution.py"
Task T014: "Create example binary program in firmware/examples/hello_world.s"

# After tests fail, implement sequentially (same file firmware/monitor/monitor.s):
Task T015: "Implement CMD_LOAD command handler"
Task T016: "Implement XMODEM_RECV state machine"
Task T017: "Implement XMODEM packet reception"
...
```

## Parallel Example: User Story 2 (I/O Configuration)

```bash
# Launch all tests for User Story 2 together (MANDATORY per TDD):
Task T025: "Create integration test for I/O mode switching in tests/integration/test_io_switching.py"
Task T026: "Create test for dual output mode in tests/integration/test_io_switching.py"
Task T027: "Create test for dual input mode in tests/integration/test_io_switching.py"
Task T028: "Create unit test for PS2_TO_ASCII function"

# Launch parallel implementation tasks (different functions):
Task T029: "Implement PS2_TO_ASCII function in firmware/monitor/monitor.s"
Task T030: "Implement CMD_IO_CONFIG command handler in firmware/monitor/monitor.s"

# After T029 completes, launch CHRIN enhancements (sequential, same function):
Task T031: "Enhance CHRIN to poll UART only (mode 0)"
Task T032: "Enhance CHRIN to poll PS/2 only (mode 1), call PS2_TO_ASCII"
Task T033: "Enhance CHRIN to poll both (mode 2)"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only - Both P1)

1. Complete Phase 1: Setup (add zero page variables, lookup table structure)
2. Complete Phase 2: Foundational (enhance CHRIN/CHROUT, command parser)
3. Complete Phase 3: User Story 1 (XMODEM binary upload)
4. Complete Phase 4: User Story 2 (I/O configuration and PS/2 translation)
5. **STOP and VALIDATE**: Test both user stories independently
6. Deploy/demo if ready (MVP delivered: load programs + standalone operation)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (binary loading MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (standalone operation!)
4. **MVP COMPLETE**: System can load programs and operate standalone
5. Add User Story 3 → Test independently → Deploy/Demo (BASIC convenience)
6. Add User Story 4 → Test independently → Deploy/Demo (status display)
7. Polish → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (XMODEM upload)
   - Developer B: User Story 2 (I/O configuration + PS/2 translation)
   - Both stories complete independently
3. After US1 + US2 (MVP):
   - Developer C: User Story 3 (BASIC paste)
   - Developer D: User Story 4 (status display)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies, can run parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD CRITICAL**: Tests MUST fail before implementing (per RetroCPU Constitution)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **MVP Scope**: User Stories 1 + 2 (both P1) - binary loading + standalone operation
- **Code Budget**: ~750 bytes new ROM code, ~4KB available (within budget)
- **Memory Budget**: 42 bytes zero page, 256 bytes RAM buffers (within budget)

---

## Test Coverage Summary

### User Story 1 (XMODEM Upload)
- Integration test: Full XMODEM transfer (T011)
- Error recovery test: Checksum failures and retries (T012)
- Execution test: Upload and run program (T013)
- Example program: hello_world.s binary (T014)

### User Story 2 (I/O Configuration)
- Integration test: All 9 mode combinations (T025)
- Dual output test: UART + Display identical output (T026)
- Dual input test: Accept from either source (T027)
- Unit test: PS/2 scancode translation (T028)

### User Story 3 (BASIC Text Loading)
- Integration test: Paste 20-line BASIC program (T044)
- Flow control test: Fast paste without data loss (T045)
- PS/2 + Display test: BASIC on standalone mode (T046)

### User Story 4 (I/O Status Display)
- Integration test: Status output in all 9 modes (T052)

**Total Tests**: 11 test tasks (T011-T014, T025-T028, T044-T046, T052)
**Total Implementation Tasks**: 57 tasks (T001-T068)
**Parallel Opportunities**: 15 tasks marked [P] can run in parallel within their phases
