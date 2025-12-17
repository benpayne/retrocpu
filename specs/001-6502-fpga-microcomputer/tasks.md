# Tasks: 6502 FPGA Microcomputer

**Input**: Design documents from `/specs/001-6502-fpga-microcomputer/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Tests**: MANDATORY per Test-Driven Design principle in constitution. All modules MUST have cocotb tests written BEFORE implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **FPGA/HDL project**: `rtl/` for Verilog modules, `tests/` for cocotb tests
- **Module organization**: `rtl/cpu/`, `rtl/memory/`, `rtl/peripherals/`, `rtl/system/`
- **Test organization**: `tests/unit/` for module tests, `tests/integration/` for system tests
- **Firmware**: `firmware/monitor/` and `firmware/basic/` for 6502 ROM code

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure (rtl/, tests/, firmware/, docs/, build/)
- [ ] T002 Add Arlet 6502 core as git submodule in rtl/cpu/ from https://github.com/Arlet/verilog-6502
- [ ] T003 [P] Create build/Makefile with synthesis, place-and-route, and programming targets
- [ ] T004 [P] Verify colorlight_i5.lpf pin constraints file exists and is correct
- [ ] T005 [P] Create .gitignore for sim/, synth/, and build artifacts
- [ ] T006 [P] Install and verify toolchain (yosys, nextpnr-ecp5, iverilog, cocotb, ca65)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create tests/unit/test_clock_divider.py cocotb test for clock generation
- [ ] T008 Implement rtl/system/clock_divider.v (25 MHz → 1 MHz clock enable)
- [ ] T009 [P] Create tests/unit/test_reset_controller.py cocotb test for reset behavior
- [ ] T010 [P] Implement rtl/system/reset_controller.v (power-on reset + button debounce)
- [ ] T011 Verify clock divider and reset tests pass via simulation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic System Boot and Monitor (Priority: P1) 🎯 MVP

**Goal**: Minimum viable system - CPU boots, runs monitor, UART output works

**Independent Test**: Program FPGA, observe monitor prompt on serial terminal, execute memory examine command

### Tests for User Story 1 (MANDATORY per TDD principle) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Create tests/unit/test_ram.py cocotb test for 32KB RAM read/write
- [ ] T013 [P] [US1] Create tests/unit/test_address_decoder.py cocotb test for memory map decode
- [ ] T014 [P] [US1] Create tests/unit/test_uart_tx.py cocotb test for UART transmit with baud rate
- [ ] T015 [P] [US1] Create tests/integration/test_cpu_memory.py cocotb test for CPU-RAM integration
- [ ] T016 [P] [US1] Create tests/integration/test_system_boot.py cocotb test for reset → monitor boot sequence

### Implementation for User Story 1

- [ ] T017 [P] [US1] Implement rtl/memory/ram.v (32KB block RAM with $readmemh support)
- [ ] T018 [P] [US1] Implement rtl/memory/address_decoder.v (decode $0000-$7FFF RAM, $C000-$C0FF UART, $E000-$FFFF ROM)
- [ ] T019 [US1] Verify RAM and address decoder tests pass
- [ ] T020 [P] [US1] Implement rtl/peripherals/uart/uart_tx.v (transmit with 9600 baud generator)
- [ ] T021 [P] [US1] Implement rtl/peripherals/uart/uart.v (top-level UART module, registers at $C000-$C001)
- [ ] T022 [US1] Verify UART TX tests pass
- [ ] T023 [US1] Write firmware/monitor/monitor.s (minimal monitor: welcome message, E/D/J/G commands)
- [ ] T024 [US1] Create firmware/monitor/Makefile (assemble with ca65, generate monitor.hex)
- [ ] T025 [US1] Build monitor.hex and verify size <1KB
- [ ] T026 [US1] Implement rtl/memory/rom_monitor.v (8KB ROM $E000-$FFFF, load monitor.hex)
- [ ] T027 [US1] Create rtl/system/soc_top.v integrating CPU, RAM, ROM, address decoder, UART, clock, reset
- [ ] T028 [US1] Verify CPU-memory integration test passes
- [ ] T029 [US1] Verify system boot integration test passes
- [ ] T030 [US1] Synthesize with yosys, verify no errors, check resource usage <15K LUTs
- [ ] T031 [US1] Place-and-route with nextpnr-ecp5, verify timing closure
- [ ] T032 [US1] Generate bitstream with ecppack
- [ ] T033 [US1] Program FPGA with openFPGALoader, test on hardware
- [ ] T034 [US1] Verify monitor prompt appears on serial terminal at 9600 baud
- [ ] T035 [US1] Test monitor E command (examine memory), verify correct hex output
- [ ] T036 [US1] Test reset button, verify system restarts to monitor prompt

**Checkpoint**: At this point, User Story 1 (MVP) should be fully functional and testable independently. System boots, monitor runs, UART works.

---

## Phase 4: User Story 2 - Run BASIC from ROM (Priority: P2)

**Goal**: BASIC interpreter runs from ROM, user can execute BASIC programs

**Independent Test**: From monitor, execute G command, BASIC starts, type "PRINT 2+2", verify output "4"

### Tests for User Story 2 (MANDATORY per TDD principle) ⚠️

- [ ] T037 [P] [US2] Create tests/unit/test_rom_basic.py cocotb test for BASIC ROM read access
- [ ] T038 [P] [US2] Create tests/integration/test_basic_boot.py cocotb test for monitor → BASIC handoff

### Implementation for User Story 2

- [ ] T039 [US2] Obtain EhBASIC source code (download or vendor into firmware/basic/)
- [ ] T040 [US2] Create firmware/basic/io_vectors.s (patch BASIC I/O vectors to point to monitor UART routines at $FFF0-$FFF9)
- [ ] T041 [US2] Create firmware/basic/Makefile (assemble EhBASIC, generate basic_rom.hex ~12KB)
- [ ] T042 [US2] Build basic_rom.hex and verify size fits in 16KB
- [ ] T043 [US2] Implement rtl/memory/rom_basic.v (16KB ROM $8000-$BFFF, load basic_rom.hex)
- [ ] T044 [US2] Update rtl/memory/address_decoder.v to include BASIC ROM decode ($8000-$BFFF)
- [ ] T045 [US2] Update rtl/system/soc_top.v to instantiate BASIC ROM
- [ ] T046 [US2] Update firmware/monitor/monitor.s G command to jump to BASIC entry point ($8000)
- [ ] T047 [US2] Rebuild monitor.hex with G command implementation
- [ ] T048 [US2] Verify BASIC ROM test passes
- [ ] T049 [US2] Verify BASIC boot integration test passes
- [ ] T050 [US2] Synthesize updated design, verify resource usage still <19K LUTs
- [ ] T051 [US2] Place-and-route and generate bitstream
- [ ] T052 [US2] Program FPGA and test on hardware
- [ ] T053 [US2] From monitor, execute G command, verify BASIC prompt appears
- [ ] T054 [US2] Type "PRINT 2+2" in BASIC, verify output "4"
- [ ] T055 [US2] Enter and run simple FOR loop program, verify repeated output
- [ ] T056 [US2] Test BASIC variables, LIST command, NEW command

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Full BASIC computer is functional via UART.

---

## Phase 5: User Story 3 - Character LCD Display (Priority: P3)

**Goal**: HD44780 LCD controller works, BASIC output can go to LCD

**Independent Test**: Connect LCD, write character to $C100, verify character appears on LCD display

### Tests for User Story 3 (MANDATORY per TDD principle) ⚠️

- [ ] T057 [P] [US3] Create tests/unit/test_lcd_timing.py cocotb test for HD44780 4-bit mode timing
- [ ] T058 [P] [US3] Create tests/unit/test_lcd_init_fsm.py cocotb test for LCD initialization sequence
- [ ] T059 [P] [US3] Create tests/unit/test_lcd_controller.py cocotb test for character write and command execution
- [ ] T060 [P] [US3] Create tests/integration/test_lcd_io.py cocotb test for CPU-LCD register access

### Implementation for User Story 3

- [ ] T061 [P] [US3] Implement rtl/peripherals/lcd/lcd_timing.v (4-bit mode timing generator: setup, enable pulse, hold)
- [ ] T062 [P] [US3] Implement rtl/peripherals/lcd/lcd_init_fsm.v (power-on initialization: 15ms wait, function set, display on)
- [ ] T063 [US3] Verify LCD timing and init FSM tests pass
- [ ] T064 [US3] Implement rtl/peripherals/lcd/lcd_controller.v (top-level: registers $C100-$C102, busy flag, nibble sequencing)
- [ ] T065 [US3] Verify LCD controller test passes
- [ ] T066 [US3] Update rtl/memory/address_decoder.v to include LCD decode ($C100-$C1FF)
- [ ] T067 [US3] Add LCD pin assignments to colorlight_i5.lpf (7 pins for 4-bit mode on PMOD connector)
- [ ] T068 [US3] Update rtl/system/soc_top.v to instantiate LCD controller and connect pins
- [ ] T069 [US3] Verify LCD I/O integration test passes
- [ ] T070 [US3] Synthesize updated design, verify resource usage and pin constraints
- [ ] T071 [US3] Place-and-route and generate bitstream
- [ ] T072 [US3] Program FPGA and test with LCD hardware connected
- [ ] T073 [US3] Write test character to $C100, verify appears on LCD
- [ ] T074 [US3] Send LCD clear command ($01 to $C101), verify display clears
- [ ] T075 [US3] Write multiple characters, verify line wrap to second line
- [ ] T076 [US3] Update firmware/monitor/monitor.s to add LCD output option (optional)
- [ ] T077 [US3] Patch BASIC I/O vectors to optionally output to LCD in addition to UART
- [ ] T078 [US3] Test BASIC PRINT command with LCD output, verify text appears on LCD

**Checkpoint**: All three user stories (Monitor, BASIC, LCD) should now be independently functional

---

## Phase 6: User Story 4 - PS/2 Keyboard Input (Priority: P4)

**Goal**: PS/2 keyboard interface provides raw scan codes, software can decode to ASCII

**Independent Test**: Connect PS/2 keyboard, press key, read scan code from $C200, verify correct scan code received

### Tests for User Story 4 (MANDATORY per TDD principle) ⚠️

- [ ] T079 [P] [US4] Create tests/unit/test_ps2_keyboard.py cocotb test for PS/2 protocol and scan code capture
- [ ] T080 [P] [US4] Create tests/integration/test_ps2_io.py cocotb test for CPU-keyboard register access

### Implementation for User Story 4

- [ ] T081 [US4] Verify existing rtl/peripherals/ps2/ps2_keyboard.v module is present and functional
- [ ] T082 [US4] Create rtl/peripherals/ps2/ps2_wrapper.v to adapt existing PS/2 module to memory-mapped registers ($C200-$C201)
- [ ] T083 [US4] Verify PS/2 keyboard test passes
- [ ] T084 [US4] Update rtl/memory/address_decoder.v to include PS/2 decode ($C200-$C2FF)
- [ ] T085 [US4] Update rtl/system/soc_top.v to instantiate PS/2 wrapper and connect pins (K5, B3 per .lpf)
- [ ] T086 [US4] Verify PS/2 I/O integration test passes
- [ ] T087 [US4] Synthesize updated design, verify resource usage
- [ ] T088 [US4] Place-and-route and generate bitstream
- [ ] T089 [US4] Program FPGA and test with PS/2 keyboard connected
- [ ] T090 [US4] Press keys on PS/2 keyboard, read $C200, verify correct scan codes
- [ ] T091 [US4] Verify status register $C201 data ready flag toggles correctly
- [ ] T092 [US4] Write firmware/monitor/ps2_decode.s (scan code to ASCII translation table ~100 bytes)
- [ ] T093 [US4] Update firmware/monitor/monitor.s CHRIN routine to read from PS/2 and decode to ASCII
- [ ] T094 [US4] Rebuild monitor.hex with PS/2 keyboard support
- [ ] T095 [US4] Test monitor command input via PS/2 keyboard instead of UART
- [ ] T096 [US4] Patch BASIC I/O vectors to read from PS/2 keyboard
- [ ] T097 [US4] Test BASIC INPUT statement with PS/2 keyboard

**Checkpoint**: Monitor and BASIC can now use PS/2 keyboard for input

---

## Phase 7: User Story 5 - Combined LCD and Keyboard Operation (Priority: P5)

**Goal**: Fully standalone operation - keyboard input, LCD output, no UART/PC required

**Independent Test**: Disconnect serial terminal, use only keyboard and LCD, run BASIC program, verify complete cycle

### Tests for User Story 5 (MANDATORY per TDD principle) ⚠️

- [ ] T098 [US5] Create tests/integration/test_standalone.py cocotb test simulating keyboard input → CPU → LCD output loop

### Implementation for User Story 5

- [ ] T099 [US5] Update firmware/monitor/monitor.s to detect I/O configuration (UART vs LCD+keyboard) at boot
- [ ] T100 [US5] Implement firmware/monitor/io_mux.s to route CHRIN/CHROUT to appropriate device
- [ ] T101 [US5] Update BASIC I/O vector patches to support both UART and LCD/keyboard configurations
- [ ] T102 [US5] Rebuild monitor.hex and basic_rom.hex with multi-device I/O support
- [ ] T103 [US5] Verify standalone integration test passes
- [ ] T104 [US5] Synthesize final design with all features
- [ ] T105 [US5] Place-and-route and generate final bitstream
- [ ] T106 [US5] Program FPGA with all peripherals connected (UART, LCD, PS/2)
- [ ] T107 [US5] Test standalone: disconnect PC, power on, verify monitor on LCD
- [ ] T108 [US5] Type monitor commands via keyboard, verify responses on LCD
- [ ] T109 [US5] Start BASIC via keyboard G command, verify BASIC prompt on LCD
- [ ] T110 [US5] Enter and run BASIC program using only keyboard and LCD
- [ ] T111 [US5] Verify all acceptance scenarios for US5 pass

**Checkpoint**: All five user stories should now be independently functional. System is a complete standalone 6502 computer.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T112 [P] Create docs/modules/cpu.md documenting Arlet 6502 integration
- [ ] T113 [P] Create docs/modules/memory.md documenting memory map and address decoder
- [ ] T114 [P] Create docs/modules/uart.md documenting UART registers and usage
- [ ] T115 [P] Create docs/modules/lcd.md documenting LCD controller and HD44780 commands
- [ ] T116 [P] Create docs/modules/ps2.md documenting PS/2 interface and scan code decoding
- [ ] T117 [P] Create docs/timing/bus_timing.md with CPU bus timing diagrams
- [ ] T118 [P] Create docs/timing/io_timing.md with UART/LCD/PS/2 timing specifications
- [ ] T119 [P] Create docs/learning/6502_basics.md tutorial for learners
- [ ] T120 [P] Create docs/learning/memory_map.md explaining address space
- [ ] T121 [P] Create docs/learning/hdl_patterns.md showing Verilog patterns used
- [ ] T122 Review synthesized design, generate resource utilization report
- [ ] T123 Verify all success criteria SC-001 through SC-016 are met
- [ ] T124 [P] Add debug LEDs to show system state (CPU running, UART TX, keyboard ready, LCD busy)
- [ ] T125 Run full regression test suite (all unit + integration tests)
- [ ] T126 Create build/README.md with build instructions and tool versions
- [ ] T127 Update top-level README.md with project overview and quick start link

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion - MVP
- **User Story 2 (Phase 4)**: Depends on User Story 1 (uses monitor UART routines)
- **User Story 3 (Phase 5)**: Depends on Foundational (independent of US1/US2 for hardware, but typically follows for I/O vector integration)
- **User Story 4 (Phase 6)**: Depends on Foundational (independent of US1/US2/US3 for hardware, but typically follows for I/O integration)
- **User Story 5 (Phase 7)**: Depends on User Stories 3 AND 4 being complete
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Requires US1 complete (uses monitor UART I/O routines)
- **User Story 3 (P3)**: Can start after Foundational, integrates with US1/US2 for I/O vectors
- **User Story 4 (P4)**: Can start after Foundational, integrates with US1/US2 for I/O vectors
- **User Story 5 (P5)**: Requires US3 (LCD) AND US4 (keyboard) complete

### Within Each User Story

- Tests (cocotb) MUST be written and FAIL before implementation (TDD mandate)
- Hardware modules before firmware
- Individual module tests before integration tests
- Synthesis and hardware test after simulation passes
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003-T006)
- Within Foundational phase: clock divider (T007-T008) parallel with reset (T009-T010)
- Within User Story 1 tests: All test creation tasks T012-T016 can run in parallel
- Within User Story 1 implementation: RAM (T017), UART (T020-T021), monitor firmware (T023-T025) can develop in parallel
- Within User Story 3: LCD timing (T061), init FSM (T062) can develop in parallel
- All documentation tasks in Phase 8 (T112-T121) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (MANDATORY per TDD):
Task: "Create tests/unit/test_ram.py cocotb test"
Task: "Create tests/unit/test_address_decoder.py cocotb test"
Task: "Create tests/unit/test_uart_tx.py cocotb test"
Task: "Create tests/integration/test_cpu_memory.py cocotb test"
Task: "Create tests/integration/test_system_boot.py cocotb test"

# After tests written and failing, launch independent modules together:
Task: "Implement rtl/memory/ram.v"
Task: "Implement rtl/memory/address_decoder.v"
# (Wait for T019 pass)

Task: "Implement rtl/peripherals/uart/uart_tx.v"
Task: "Implement rtl/peripherals/uart/uart.v"
# (In parallel)

Task: "Write firmware/monitor/monitor.s"
Task: "Create firmware/monitor/Makefile"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T011) - CRITICAL blocking phase
3. Complete Phase 3: User Story 1 (T012-T036)
4. **STOP and VALIDATE**: Test User Story 1 independently on hardware
5. Deploy/demo MVP: Working 6502 system with monitor

**MVP Deliverable**: Bootable 6502 system with monitor, UART I/O, memory examine/deposit commands. ~2-3 weeks effort.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (T012-T036) → Test independently → Deploy (MVP! 🎯)
3. Add User Story 2 (T037-T056) → Test independently → Deploy (BASIC computer)
4. Add User Story 3 (T057-T078) → Test independently → Deploy (with LCD)
5. Add User Story 4 (T079-T097) → Test independently → Deploy (with keyboard)
6. Add User Story 5 (T098-T111) → Test independently → Deploy (standalone)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T011)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (T012-T036) - MVP critical path
   - **Developer B**: Start User Story 3 hardware (T057-T075) in parallel
   - **Developer C**: Start User Story 4 hardware (T079-T091) in parallel
3. After US1 complete:
   - Developer A → User Story 2 (T037-T056)
   - Developer B → Complete US3 firmware integration (T076-T078)
   - Developer C → Complete US4 firmware integration (T092-T097)
4. Final integration: US5 (T098-T111) after US3+US4 complete
5. Polish phase (T112-T127) parallelizable across team

---

## Notes

- **TDD Workflow**: Every Verilog module has cocotb test written FIRST (red), then implementation (green), then verify test passes
- **Test Execution**: Run `make test-unit` for unit tests, `make test-integration` for integration tests
- **Simulation**: All tests run in iverilog simulation before hardware synthesis
- **Hardware Validation**: After each user story, program FPGA and verify on actual hardware
- **Commit Discipline**: Commit after each completed task or logical group (tests → implementation → verification)
- **Stop at Checkpoints**: Each checkpoint is an opportunity to validate story independently and deploy
- **Resource Monitoring**: Track LUT usage after each synthesis (target <19K, budget 24K)
- **Educational Focus**: Maintain code clarity and documentation throughout (per constitution)
- **Avoid**: Vague tasks, same-file conflicts, cross-story dependencies that break independence

---

## Task Summary

**Total Tasks**: 127 tasks
- Setup: 6 tasks (T001-T006)
- Foundational: 5 tasks (T007-T011)
- User Story 1 (MVP): 25 tasks (T012-T036)
- User Story 2: 20 tasks (T037-T056)
- User Story 3: 22 tasks (T057-T078)
- User Story 4: 19 tasks (T079-T097)
- User Story 5: 14 tasks (T098-T111)
- Polish: 16 tasks (T112-T127)

**Parallel Opportunities**: 45+ tasks marked [P] can run in parallel when prerequisites met

**Independent Test Criteria Per Story**:
- US1: Serial terminal shows monitor prompt, E command works
- US2: G command starts BASIC, "PRINT 2+2" outputs "4"
- US3: Character written to $C100 appears on LCD
- US4: Key press on PS/2 keyboard generates scan code at $C200
- US5: System operates with only keyboard+LCD, no PC required

**Suggested MVP Scope**: Complete through User Story 1 (Tasks T001-T036) for initial deployment. This delivers a working 6502 microcomputer with monitor and UART I/O.

**Estimated Effort**:
- MVP (US1): 2-3 weeks
- +BASIC (US2): +1 week
- +LCD (US3): +1 week
- +Keyboard (US4): +1 week
- +Standalone (US5): +0.5 weeks
- +Polish: +1 week
- **Total**: 6-8 weeks for complete system
