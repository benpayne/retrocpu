# RetroCPU Remediation - Quick Checklist
**Date**: 2025-12-29

---

## CRITICAL PATH (5-7 hours) - User Stories 1 & 2

### Monitor Commands
- [ ] **P0-1**: Implement E (Examine) command (1-2 hrs)
  - [ ] Create READ_HEX_BYTE subroutine
  - [ ] Create READ_HEX_WORD subroutine
  - [ ] Implement CMD_EXAMINE logic
  - [ ] Test: `E 0000`, `E E000`, `E C000`

- [ ] **P0-2**: Implement D (Deposit) command (1-2 hrs)
  - [ ] Reuse hex parsing from P0-1
  - [ ] Implement CMD_DEPOSIT logic
  - [ ] Test: `D 0200 42` then `E 0200`

- [ ] **P1-1**: Implement G (Go to BASIC) command (30 min)
  - [ ] Add G/g to command parser
  - [ ] Add CMD_GO: JMP $9D11
  - [ ] Test: `G` → BASIC starts, `PRINT 2+2` → 4

### Infrastructure
- [ ] **P0-3**: Create requirements.txt (15 min)
  - [ ] Activate venv
  - [ ] Run `pip freeze > requirements.txt`
  - [ ] Clean up and add comments
  - [ ] Test: Delete venv, recreate, reinstall

### Validation
- [ ] Rebuild monitor.hex
- [ ] Program FPGA
- [ ] Test all monitor commands work
- [ ] Test BASIC starts with G command
- [ ] Update STATUS.md with accurate completion %

**CHECKPOINT**: User Stories 1 & 2 should be 100% working

---

## PHASE 2 (10-13 hours) - Add LCD & PS/2

### LCD Integration
- [ ] **P2-1**: Connect LCD in soc_top.v (2-3 hrs)
  - [ ] Add LCD pins to module port
  - [ ] Instantiate lcd_controller
  - [ ] Update data bus mux
  - [ ] Add pin constraints to .lpf
  - [ ] Synthesis, PnR, program
  - [ ] Test: Write to $C100/$C101

- [ ] **P2-2**: LCD boot message (1 hr) [OPTIONAL]
  - [ ] Add LCD_OUT, LCD_CMD, LCD_INIT to monitor
  - [ ] Display "RetroCPU v1.0" on boot
  - [ ] Test with LCD connected

### PS/2 Integration
- [ ] **P2-3**: Connect PS/2 in soc_top.v (2-3 hrs)
  - [ ] Add PS/2 pins to module port
  - [ ] Instantiate ps2_wrapper
  - [ ] Update data bus mux
  - [ ] Verify pin constraints
  - [ ] Synthesis, PnR, program
  - [ ] Test: Read $C200/$C201, press keys

- [ ] **P2-4**: PS/2 monitor support (3-4 hrs)
  - [ ] Create scan code → ASCII table
  - [ ] Implement PS2_READ_SCANCODE
  - [ ] Implement PS2_DECODE_ASCII
  - [ ] Modify CHRIN to check PS/2
  - [ ] Test: Type on PS/2 keyboard

**CHECKPOINT**: User Stories 3 & 4 should work

---

## PHASE 3 (5-7 hours) - Testing & Documentation

### Testing
- [ ] **P3-1**: Run cocotb unit tests (2-3 hrs)
  - [ ] test_clock_divider.py
  - [ ] test_reset_controller.py
  - [ ] test_ram.py
  - [ ] test_address_decoder.py
  - [ ] test_uart_tx.py
  - [ ] test_uart_rx.py
  - [ ] test_lcd_*.py
  - [ ] Document results

- [ ] **P3-2**: Create missing integration tests (2-3 hrs)
  - [ ] test_cpu_memory.py (T015)
  - [ ] test_system_boot.py (T016)
  - [ ] Run and verify pass

### Documentation
- [ ] **P3-3**: Update STATUS.md (30 min)
  - [ ] Correct completion percentages
  - [ ] Document what actually works
  - [ ] Add "Known Issues" section
  - [ ] Remove false claims

- [ ] **P3-4**: Test runner script (1 hr) [OPTIONAL]
  - [ ] Create run_all_tests.sh
  - [ ] Test on clean system

**CHECKPOINT**: Production quality, full test coverage

---

## Summary by Priority

### P0 - CRITICAL (Blocks MVP)
- [ ] P0-1: E command
- [ ] P0-2: D command
- [ ] P0-3: requirements.txt

### P1 - HIGH (Blocks BASIC)
- [ ] P1-1: G command

### P2 - MEDIUM (Blocks LCD/PS2)
- [ ] P2-1: LCD integration
- [ ] P2-2: LCD boot message (optional)
- [ ] P2-3: PS/2 integration
- [ ] P2-4: PS/2 monitor support

### P3 - LOW (Testing/Docs)
- [ ] P3-1: Cocotb tests
- [ ] P3-2: Integration tests
- [ ] P3-3: STATUS.md update
- [ ] P3-4: Test runner (optional)

---

## Quick Status Check

**Before starting, current reality:**
- ❌ Monitor E command: Prints "not implemented"
- ❌ Monitor D command: Prints "not implemented"
- ❌ Monitor G command: Doesn't exist
- ❌ LCD: Not connected (code exists)
- ❌ PS/2: Not connected (code exists)
- ❌ requirements.txt: Doesn't exist
- ✅ Build system: Works
- ✅ UART: Works
- ✅ BASIC ROM: Built and ready
- ✅ RAM/ROM/CPU: All working

**After Critical Path (P0-P1):**
- ✅ Monitor E command: Working
- ✅ Monitor D command: Working
- ✅ Monitor G command: Starts BASIC
- ✅ User Story 1: 100% complete
- ✅ User Story 2: 100% complete
- ❌ User Story 3: Still needs LCD
- ❌ User Story 4: Still needs PS/2

**After Phase 2 (P2):**
- ✅ User Story 3: LCD working
- ✅ User Story 4: PS/2 working
- ✅ Standalone computer (no PC needed)

**After Phase 3 (P3):**
- ✅ All tests passing
- ✅ Production ready
- ✅ CI/CD ready

---

## Time Estimates

| Scope | Tasks | Time | Result |
|-------|-------|------|--------|
| Critical Path | P0-1, P0-2, P1-1, P0-3 | 5-7 hrs | US1&2 complete |
| + LCD/PS2 | + P2-1, P2-2, P2-3, P2-4 | 15-20 hrs | US3&4 complete |
| + Testing | + P3-1, P3-2, P3-3, P3-4 | 20-25 hrs | Production ready |

---

## Recommended Start

**Next command to run:**
```bash
# Start with P0-1 (Implement E command)
cd /opt/wip/retrocpu/firmware/monitor
# Edit monitor.s
# Add hex parsing and E command implementation
```

**Or use agent to implement in parallel** - I can launch agents to work on multiple tasks simultaneously.
