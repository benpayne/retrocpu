# Tasks: M65C02 CPU Core Port

**Input**: Design documents from `/specs/002-m65c02-port/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are NOT required for this feature per project constitution. Testing will be performed via hardware validation and existing test suite verification.

**Organization**: Tasks are grouped by user story to enable focused implementation and independent validation of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Implementation Strategy

**MVP Scope**: User Stories 1 + 2 + 5 (Core Integration + Zero Page Fix + Memory Timing)
- These three stories MUST work together to achieve the primary goal: fixing the zero page bug
- User Stories 3 + 4 (Monitor + BASIC) are validation stories that depend on 1+2+5

**Delivery Order**:
1. Phase 1-2: Setup and foundational work
2. Phase 3-5: US1 + US2 + US5 together (integrated MVP)
3. Phase 6: US3 (Monitor validation)
4. Phase 7: US4 (BASIC validation)
5. Phase 8: Polish and documentation

---

## Phase 1: Setup (M65C02 Source Acquisition)

**Purpose**: Obtain and prepare M65C02 core files for integration

- [ ] T001 Clone M65C02 repository from https://github.com/MorrisMA/MAM65C02-Processor-Core to temporary location
- [ ] T002 [P] Create directory rtl/cpu/m65c02/ for M65C02 core files
- [ ] T003 Copy required Verilog files (M65C02_Core.v, M65C02_MPCv4.v, M65C02_AddrGen.v, M65C02_ALU.v, M65C02_BIN.v, M65C02_BCD.v) to rtl/cpu/m65c02/
- [ ] T004 [P] Copy microprogram files (M65C02_Decoder_ROM.txt, M65C02_uPgm_V3a.txt) to rtl/cpu/m65c02/
- [ ] T005 [P] Create rtl/cpu/m65c02/README.md documenting core source, license (LGPL), and parameters
- [ ] T006 Backup current soc_top.v to rtl/system/soc_top.v.arlet_backup

---

## Phase 2: Foundational (Build System Updates)

**Purpose**: Update build system to include M65C02 sources before integration work begins

**⚠️ CRITICAL**: No integration work can begin until build system recognizes M65C02 files

- [ ] T007 Backup build/Makefile to build/Makefile.arlet_backup
- [ ] T008 Update build/Makefile to add M65C02 source files (M65C02_Core.v, M65C02_MPCv4.v, M65C02_AddrGen.v, M65C02_ALU.v, M65C02_BIN.v, M65C02_BCD.v)
- [ ] T009 [P] Add include path for M65C02 microprogram ROMs in build/Makefile (YOSYS_FLAGS += -I../rtl/cpu/m65c02)
- [ ] T010 [P] Comment out or remove Arlet 6502 source files from build/Makefile
- [ ] T011 Test build system recognizes M65C02 files with dry-run synthesis

**Checkpoint**: Foundation ready - M65C02 files available for integration

---

## Phase 3: User Story 1 - Core Integration and Boot Verification (Priority: P1) 🎯 MVP CRITICAL

**Goal**: Replace Arlet 6502 with M65C02 in soc_top.v and achieve successful system boot with monitor prompt

**Independent Test**: Power on FPGA after synthesis. Monitor displays welcome message and prompt via UART within 1 second.

### Implementation for User Story 1

**Signal Declarations (soc_top.v)**:

- [ ] T012 [US1] Remove signal declarations in rtl/system/soc_top.v: cpu_we, cpu_clk_enable, cpu_clk_enable_delayed
- [ ] T013 [US1] Add signal declarations in rtl/system/soc_top.v: cpu_io_op[1:0], cpu_mc[2:0]

**Clock Divider Removal**:

- [ ] T014 [US1] Comment out clock_divider instantiation in rtl/system/soc_top.v (M65C02 has built-in microcycle controller)

**Write Enable Logic Updates**:

- [ ] T015 [US1] Update RAM write enable in rtl/system/soc_top.v: Change from (ram_cs && cpu_we) to ((cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && ram_cs)
- [ ] T016 [P] [US1] Update UART write enable in rtl/system/soc_top.v: Change from (uart_cs && cpu_we) to ((cpu_io_op == 2'b01) && (cpu_mc == 3'b011) && uart_cs)

**Data Capture Logic Update**:

- [ ] T017 [US1] Update data bus register in rtl/system/soc_top.v: Change capture condition from (cpu_clk_enable) to (cpu_mc == 3'b000)

**CPU Instance Replacement**:

- [ ] T018 [US1] Remove Arlet CPU instantiation in rtl/system/soc_top.v
- [ ] T019 [US1] Add M65C02_Core instantiation in rtl/system/soc_top.v with parameters (pStkPtr_Rst=8'hFF, pInt_Hndlr=0, pM65C02_uPgm="M65C02_uPgm_V3a.txt", pM65C02_IDec="M65C02_Decoder_ROM.txt")
- [ ] T020 [US1] Connect M65C02 clock and reset signals (Clk ← clk_25mhz, Rst ← system_rst)
- [ ] T021 [US1] Connect M65C02 address and data buses (AO ← cpu_addr, DI ← cpu_data_in, DO ← cpu_data_out)
- [ ] T022 [US1] Connect M65C02 control signals (IO_Op ← cpu_io_op, MC ← cpu_mc)
- [ ] T023 [US1] Tie off M65C02 memory controller signals (Wait ← 1'b0, MemTyp ← leave unconnected)
- [ ] T024 [US1] Tie off M65C02 interrupt signals for MVP (Int ← 1'b0, Vector ← 16'hFFFC, xIRQ ← 1'b1, IRQ_Msk ← leave unconnected)
- [ ] T025 [US1] Leave M65C02 status/debug signals unconnected (Done, SC, Mode, RMW, Rdy, IntSvc, ISR)
- [ ] T026 [US1] Leave M65C02 register debug signals unconnected (A, X, Y, S, P, PC, IR, OP1, OP2)

**Synthesis and Initial Hardware Test**:

- [ ] T027 [US1] Run clean build and synthesize design with Yosys (make clean && make synth)
- [ ] T028 [US1] Verify synthesis completes without errors and check LUT usage (<12K target)
- [ ] T029 [US1] Run place-and-route with nextpnr-ecp5 (make pnr)
- [ ] T030 [US1] Verify timing closure with positive slack at 25 MHz
- [ ] T031 [US1] Generate bitstream (make bitstream)
- [ ] T032 [US1] Program FPGA (make program or openFPGALoader -b colorlight-i5 soc_top.bit)
- [ ] T033 [US1] Verify system boots and monitor welcome message appears on UART within 1 second
- [ ] T034 [US1] Verify monitor prompt ("> ") is displayed
- [ ] T035 [US1] Test reset button successfully reboots system

**Checkpoint**: US1 complete - System boots with M65C02, monitor prompt appears ✅

---

## Phase 4: User Story 2 - Zero Page Memory Access (Priority: P1) 🎯 MVP CRITICAL

**Goal**: Validate that zero page addresses ($0000-$00FF) support correct read and write operations (PRIMARY BUG FIX)

**Independent Test**: Use monitor D/E commands to write/read zero page. All values match what was written.

### Implementation for User Story 2

**Zero Page Validation Tests (Hardware)**:

- [ ] T036 [US2] Test write/read to $0000: Monitor command "D 0000 11" then "E 0000", verify reads $11 (not $00)
- [ ] T037 [US2] Test write/read to $0010: Monitor command "D 0010 22" then "E 0010", verify reads $22
- [ ] T038 [US2] Test write/read to $0080: Monitor command "D 0080 33" then "E 0080", verify reads $33
- [ ] T039 [US2] Test write/read to $00FF: Monitor command "D 00FF 44" then "E 00FF", verify reads $44
- [ ] T040 [US2] Test multiple zero page addresses retain values when read back in different order
- [ ] T041 [US2] Test zero page addressing modes execute without errors by running simple monitor commands
- [ ] T042 [US2] Document zero page test results in specs/002-m65c02-port/VALIDATION_LOG.md

**Checkpoint**: US2 complete - Zero page write/read operations work correctly, PRIMARY BUG FIXED ✅

---

## Phase 5: User Story 5 - Memory Timing Configuration (Priority: P1) 🎯 MVP CRITICAL

**Goal**: Verify M65C02 microcycle controller is correctly configured for memory subsystem timing

**Independent Test**: Run memory access tests to RAM, ROM, and UART. All operations complete without timing violations or data corruption.

### Implementation for User Story 5

**Memory Timing Validation**:

- [ ] T043 [US5] Verify ROM reads ($E000-$FFFF) fetch correct instruction data by observing successful monitor boot
- [ ] T044 [US5] Verify RAM writes ($0000-$7FFF) store data correctly by writing patterns to addresses $0100, $1000, $7FFF and reading back
- [ ] T045 [US5] Verify UART register access ($C000-$C001) completes correctly by sending/receiving characters
- [ ] T046 [US5] Verify rapid consecutive memory accesses don't cause bus contention by performing multiple sequential D/E commands
- [ ] T047 [US5] Run system stability test: Leave system running for 30+ minutes, monitor for errors, data corruption, or hangs
- [ ] T048 [US5] Verify microcycle state sequence (MC: 2→3→1→0) in simulation if available (optional, use GTKWave with test waveforms)
- [ ] T049 [US5] Document memory timing validation results in specs/002-m65c02-port/VALIDATION_LOG.md

**Checkpoint**: US5 complete - Memory timing configured correctly, system stable ✅

**🎯 MVP MILESTONE**: User Stories 1 + 2 + 5 complete - M65C02 integrated, zero page working, timing validated

---

## Phase 6: User Story 3 - Monitor Command Functionality (Priority: P2)

**Goal**: Validate monitor E (examine) and D (deposit) commands work correctly for all memory

**Independent Test**: Execute monitor "E 0200" and "D 0200 AA" commands. Both complete successfully with correct output.

### Implementation for User Story 3

**Monitor Command Validation**:

- [ ] T050 [US3] Test monitor E (examine) command displays memory at $0200 correctly
- [ ] T051 [US3] Test monitor D (deposit) command writes value $AA to $0200
- [ ] T052 [US3] Verify deposited value reads back correctly with E command
- [ ] T053 [US3] Test monitor E command on zero page ($0010) displays non-zero values (validates US2)
- [ ] T054 [US3] Test monitor commands on various memory ranges (RAM, ROM, I/O) all function correctly
- [ ] T055 [US3] Document monitor command test results in specs/002-m65c02-port/VALIDATION_LOG.md

**Checkpoint**: US3 complete - Monitor commands fully functional ✅

---

## Phase 7: User Story 4 - BASIC Interpreter Operation (Priority: P2)

**Goal**: Validate BASIC interpreter starts and executes programs correctly

**Independent Test**: Execute monitor "G" command, BASIC starts. Type "PRINT 2+2", output displays "4".

### Implementation for User Story 4

**BASIC Interpreter Validation**:

- [ ] T056 [US4] Test monitor G command starts BASIC and displays "Ready" prompt within 2 seconds
- [ ] T057 [US4] Test BASIC command "PRINT 2+2" outputs "4" correctly
- [ ] T058 [US4] Test BASIC FOR loop program: "FOR I=1 TO 5:PRINT I:NEXT" executes and displays 1,2,3,4,5
- [ ] T059 [US4] Test BASIC variable assignment: "A=10" then "PRINT A" outputs "10"
- [ ] T060 [US4] Test BASIC program entry and listing: Enter program lines, use LIST command, verify program displayed
- [ ] T061 [US4] Test BASIC NEW command clears program
- [ ] T062 [US4] Run extended BASIC tests: Multiple programs, nested loops, arrays (if supported), string operations
- [ ] T063 [US4] Document BASIC interpreter test results in specs/002-m65c02-port/VALIDATION_LOG.md

**Checkpoint**: US4 complete - BASIC interpreter fully functional ✅

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final validation

### Existing Test Suite Validation

- [ ] T064 [P] Run existing unit test: pytest tests/unit/test_ram.py -v (verify still passes with M65C02)
- [ ] T065 [P] Run existing unit test: pytest tests/unit/test_uart_tx.py -v (verify still passes)
- [ ] T066 [P] Run existing unit test: pytest tests/unit/test_uart_rx.py -v (verify still passes)
- [ ] T067 [P] Run existing unit test: pytest tests/unit/test_address_decoder.py -v (if exists, verify still passes)
- [ ] T068 [P] Run existing unit test: pytest tests/unit/test_reset_controller.py -v (if exists, verify still passes)

### Resource Usage and Performance Validation

- [ ] T069 Check final synthesis report: Verify LUT usage is within budget (<12K / 25K LUTs = <50%)
- [ ] T070 Check timing report: Verify positive slack at 25 MHz system clock
- [ ] T071 Measure CPU performance: Estimate effective MIPS based on microcycle rate (6.25 MHz microcycle = ~4-5 MIPS expected)

### Documentation Updates

- [ ] T072 [P] Update project README.md: Document M65C02 core as CPU, list specifications (25 MHz, 6.25 MHz microcycle, ~4-5 MIPS)
- [ ] T073 [P] Create specs/002-m65c02-port/INTEGRATION_LOG.md: Document integration steps taken, changes made, validation results
- [ ] T074 [P] Update docs/modules/cpu.md: Document M65C02 core integration, signal interface, microcycle controller configuration
- [ ] T075 [P] Update docs/timing/bus_timing.md: Document M65C02 bus timing (4-cycle microcycles, MC states, memory access timing)
- [ ] T076 [P] Create release notes summarizing M65C02 port: Zero page bug fixed, BASIC functional, ~6x performance improvement

### Git Commit and Branch Management

- [ ] T077 Review all changes in git diff, ensure no unintended modifications
- [ ] T078 Git add all M65C02 files: rtl/cpu/m65c02/, rtl/system/soc_top.v, build/Makefile, specs/002-m65c02-port/
- [ ] T079 Create git commit with comprehensive message documenting M65C02 integration and zero page bug fix
- [ ] T080 Tag commit with version number (e.g., v0.2.0-m65c02-port)

---

## Dependencies and Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Build System)
    ↓
Phase 3 (US1: Core Integration) ←──┐
    ↓                              │
Phase 4 (US2: Zero Page) ──────────┤  MVP Core
    ↓                              │  (Must complete
Phase 5 (US5: Memory Timing) ──────┘  together)
    ↓
Phase 6 (US3: Monitor Commands) ← Validation
    ↓
Phase 7 (US4: BASIC) ← Validation
    ↓
Phase 8 (Polish)
```

### User Story Dependencies

- **US1 (Core Integration)**: No dependencies, foundational
- **US2 (Zero Page)**: Depends on US1 (need working CPU to test zero page)
- **US5 (Memory Timing)**: Depends on US1 (need CPU integrated to validate timing)
- **US3 (Monitor)**: Depends on US1 + US2 + US5 (monitor commands use zero page)
- **US4 (BASIC)**: Depends on US1 + US2 + US5 (BASIC heavily uses zero page)

### Parallel Execution Opportunities

**Within Phase 1 (Setup)**:
- T002, T004, T005 can run in parallel (different directories/files)

**Within Phase 2 (Build)**:
- T009, T010 can run in parallel (independent Makefile edits)

**Within Phase 3 (US1)**:
- T012, T013 can run in parallel (independent signal edits)
- T016 can run parallel with T015 (different modules)
- After CPU replacement complete, T027-T035 must run sequentially (build → synth → pnr → program → test)

**Within Phase 8 (Polish)**:
- T064-T068 can run in parallel (independent test suites)
- T072-T076 can run in parallel (independent documentation files)

---

## Task Summary

- **Total Tasks**: 80
- **Phase 1 (Setup)**: 6 tasks
- **Phase 2 (Foundational)**: 5 tasks
- **Phase 3 (US1 - Core Integration)**: 24 tasks 🎯
- **Phase 4 (US2 - Zero Page)**: 7 tasks 🎯
- **Phase 5 (US5 - Memory Timing)**: 7 tasks 🎯
- **Phase 6 (US3 - Monitor)**: 6 tasks
- **Phase 7 (US4 - BASIC)**: 8 tasks
- **Phase 8 (Polish)**: 17 tasks

**MVP Tasks** (Phase 1-5): 49 tasks
**Validation Tasks** (Phase 6-7): 14 tasks
**Polish Tasks** (Phase 8): 17 tasks

**Parallel Opportunities**: 15 tasks marked [P] can run in parallel with others in same phase

**Critical Path**: Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) + Phase 5 (US5) → Phase 6 (US3) → Phase 7 (US4) → Phase 8

---

## Validation Checklist

### After MVP (Phase 5 Complete)

✅ System boots, monitor prompt appears
✅ Zero page addresses ($0000-$00FF) read/write correctly
✅ Memory timing stable, no data corruption
✅ System runs continuously without hangs

### After Full Implementation (Phase 7 Complete)

✅ Monitor E/D commands work
✅ BASIC interpreter starts and runs programs
✅ "PRINT 2+2" outputs "4"
✅ All existing tests pass

### Final Acceptance (Phase 8 Complete)

✅ Documentation updated
✅ Resource usage within budget
✅ Timing closure achieved
✅ Git commit tagged

---

## Success Criteria Mapping

| Success Criteria | Validated By | Phase |
|------------------|--------------|-------|
| SC-001: Boot in 1 second | T033 | Phase 3 (US1) |
| SC-002: 30 min stability | T047 | Phase 5 (US5) |
| SC-003: Reset works | T035 | Phase 3 (US1) |
| SC-004: Zero page 100% | T036-T041 | Phase 4 (US2) |
| SC-007: Monitor E works | T050, T053 | Phase 6 (US3) |
| SC-008: Monitor D works | T051, T052 | Phase 6 (US3) |
| SC-009: Monitor G works | T056 | Phase 7 (US4) |
| SC-012: PRINT 2+2 = 4 | T057 | Phase 7 (US4) |
| SC-013: FOR loops work | T058 | Phase 7 (US4) |
| SC-014: Variables work | T059 | Phase 7 (US4) |
| SC-019: Synthesis OK | T027 | Phase 3 (US1) |
| SC-020: PnR with slack | T029, T030 | Phase 3 (US1) |
| SC-021: Resource <50% | T028, T069 | Phase 3, 8 |
| SC-023: Existing tests pass | T064-T068 | Phase 8 |

---

## Notes

- **No new test creation required**: Per RetroCPU constitution and project context, hardware validation with monitor/BASIC firmware is the primary test method
- **Existing tests preserved**: All existing cocotb unit tests for RAM, UART, etc. must continue to pass
- **Hardware-first validation**: Tasks focus on FPGA synthesis, programming, and real hardware testing rather than extensive simulation
- **Incremental delivery**: MVP (Phases 1-5) delivers the core value (zero page fix), with Phases 6-7 validating the fix works for monitor and BASIC

**Status**: Task breakdown complete ✅ | Ready for implementation
