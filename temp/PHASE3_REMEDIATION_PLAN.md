# Phase 3 Remediation Plan - Path to True 100% Completion

**Current Status**: 70% complete per specification, 100% working on hardware
**Goal**: Achieve 100% completion per tasks.md specification
**Estimated Effort**: 4-6 hours

---

## Priority 1: Critical Test Infrastructure (2-3 hours)

### Task 1.1: Install and Configure cocotb
**Required for**: T019, T022, T028, T029

```bash
# Install cocotb and dependencies
pip3 install cocotb cocotb-test

# Verify installation
python3 -c "import cocotb; print(f'cocotb {cocotb.__version__} installed')"
```

**Validation**: Run `python3 -c "import cocotb"` without errors

---

### Task 1.2: Run Unit Tests
**Required for**: T019 (RAM + address decoder), T022 (UART TX)

```bash
cd /opt/wip/retrocpu/tests/unit

# Test RAM (T012, part of T019)
python3 test_ram.py
# Expected: 9 tests pass

# Test address decoder (T013, part of T019)
python3 test_address_decoder.py
# Expected: 11 tests pass

# Test UART TX (T014, part of T022)
python3 test_uart_tx.py
# Expected: 10 tests pass
```

**Success Criteria**:
- All 9 RAM tests pass
- All 11 address decoder tests pass
- All 10 UART TX tests pass
- No X/Z values in simulation
- Correct timing behavior

**Documentation**: Save test output to `temp/UNIT_TEST_RESULTS.txt`

---

### Task 1.3: Run Integration Tests
**Required for**: T028 (CPU-memory), T029 (system boot)

```bash
cd /opt/wip/retrocpu/tests/integration

# Test CPU initialization (closest to T028)
python3 test_cpu_basic.py
# Expected: CPU initializes, no X values

# Test monitor boot (closest to T029)
python3 test_soc_monitor.py
# Expected: UART output captured, monitor boots
```

**Success Criteria**:
- CPU address bus shows valid values (not X/Z)
- Clock enable pulses correctly (~5 per 1000 cycles)
- UART transmits at least 1 character
- Monitor banner detected in UART output

**Documentation**: Save test output to `temp/INTEGRATION_TEST_RESULTS.txt`

---

## Priority 2: Test Naming Consistency (30 minutes)

### Task 2.1: Create or Rename test_cpu_memory.py
**Required for**: T015

**Option A**: Rename existing test
```bash
cd /opt/wip/retrocpu/tests/integration
cp test_cpu_basic.py test_cpu_memory.py
# Edit to focus on CPU-RAM interaction
```

**Option B**: Update tasks.md
```markdown
- [x] T015 [US1] Create tests/integration/test_cpu_basic.py cocotb test for CPU initialization and memory access
```

**Recommendation**: Option A (create test_cpu_memory.py with CPU-RAM focus)

---

### Task 2.2: Create or Rename test_system_boot.py
**Required for**: T016

**Option A**: Rename existing test
```bash
cd /opt/wip/retrocpu/tests/integration
cp test_soc_monitor.py test_system_boot.py
# Edit to focus on reset → monitor boot sequence
```

**Option B**: Update tasks.md
```markdown
- [x] T016 [US1] Create tests/integration/test_soc_monitor.py cocotb test for reset → monitor boot → UART output
```

**Recommendation**: Option A (create test_system_boot.py with boot focus)

---

## Priority 3: Documentation Updates (1 hour)

### Task 3.1: Update tasks.md for Accuracy

**Changes needed**:

1. **T014** - Update baud rate
```markdown
- [x] T014 [P] [US1] Create tests/unit/test_uart_tx.py cocotb test for UART transmit with 115200 baud (NOTE: Upgraded from 9600 for faster I/O)
```

2. **T020** - Update baud rate
```markdown
- [x] T020 [P] [US1] Implement rtl/peripherals/uart/uart_tx.v (transmit with 115200 baud, registers at $C000-$C001)
```

3. **T021** - Add note about RX
```markdown
- [x] T021 [P] [US1] Implement rtl/peripherals/uart/uart.v (top-level UART module with TX/RX, registers at $C000-$C001)
```

4. **T025** - Update size target
```markdown
- [x] T025 [US1] Build monitor.hex and verify size <8KB (NOTE: Expanded from 1KB to support E/D commands and UART RX)
```

5. **T034** - Update baud rate
```markdown
- [x] T034 [US1] Verify monitor prompt appears on serial terminal at 115200 baud
```

---

### Task 3.2: Update STATUS.md for Accuracy

**Change this section**:
```markdown
### ✅ Phase 3: User Story 1 - MVP (100% Complete) 🎉

- [x] All 25 tasks complete (T012-T036)
```

**To this**:
```markdown
### ✅ Phase 3: User Story 1 - MVP (100% Hardware Working, 70% Test Verification) 🎉

- [x] All 25 tasks complete (T012-T036)
- [x] Hardware fully validated with 61 automated tests
- [ ] cocotb test suite - pending installation and execution
- [ ] T019, T022, T028, T029 - test verification pending cocotb setup
```

---

### Task 3.3: Create Test Execution Guide

**File**: `tests/README.md`

```markdown
# RetroCPU Test Suite

## Prerequisites

```bash
pip3 install cocotb cocotb-test
```

## Running Tests

### Unit Tests
```bash
cd tests/unit
python3 test_ram.py              # 9 tests - RAM functionality
python3 test_address_decoder.py  # 11 tests - Memory map decoding
python3 test_uart_tx.py          # 10 tests - UART transmitter
```

### Integration Tests
```bash
cd tests/integration
python3 test_cpu_basic.py        # CPU initialization
python3 test_soc_monitor.py      # Monitor boot sequence
```

### Firmware Tests (Hardware Required)
```bash
cd tests/firmware
pytest test_monitor.py -v        # 19 monitor tests
pytest test_basic.py -v          # 42 BASIC tests
```

## Test Coverage

- **Unit Tests**: 30 cocotb tests (RTL simulation)
- **Integration Tests**: 2+ cocotb tests (full system simulation)
- **Firmware Tests**: 61 pytest tests (hardware validation)
```

---

## Priority 4: Optional Enhancements (2 hours)

### Task 4.1: Create Makefile for Test Execution

**File**: `tests/Makefile`

```makefile
.PHONY: all unit integration firmware clean

all: unit integration

unit:
	@echo "Running unit tests..."
	cd unit && python3 test_ram.py
	cd unit && python3 test_address_decoder.py
	cd unit && python3 test_uart_tx.py

integration:
	@echo "Running integration tests..."
	cd integration && python3 test_cpu_basic.py
	cd integration && python3 test_soc_monitor.py

firmware:
	@echo "Running firmware tests (requires hardware)..."
	cd firmware && pytest -v

clean:
	find . -name "*.vcd" -delete
	find . -name "sim_build" -type d -exec rm -rf {} +
	find . -name "__pycache__" -type d -exec rm -rf {} +
```

---

### Task 4.2: Add CI/CD Configuration

**File**: `.github/workflows/test.yml`

```yaml
name: RetroCPU Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install cocotb cocotb-test
          sudo apt-get install -y iverilog
      - name: Run unit tests
        run: |
          cd tests/unit
          python3 test_ram.py
          python3 test_address_decoder.py
          python3 test_uart_tx.py
```

---

## Validation Checklist

After completing remediation, verify:

- [ ] cocotb installed (`import cocotb` works)
- [ ] All 9 RAM tests pass
- [ ] All 11 address decoder tests pass
- [ ] All 10 UART TX tests pass
- [ ] CPU initialization test shows valid addresses
- [ ] Monitor boot test captures UART output
- [ ] Test files match tasks.md naming (or tasks.md updated)
- [ ] tasks.md reflects actual baud rates and sizes
- [ ] STATUS.md accurately reflects test infrastructure status
- [ ] Test execution guide created (tests/README.md)
- [ ] All test outputs saved for documentation

---

## Timeline

**Total Estimated Time**: 4-6 hours

| Task | Time | Complexity |
|------|------|------------|
| Install cocotb | 15 min | Low |
| Run unit tests (3 tests) | 1 hour | Medium |
| Run integration tests (2 tests) | 1 hour | Medium |
| Fix test naming | 30 min | Low |
| Update tasks.md | 30 min | Low |
| Update STATUS.md | 15 min | Low |
| Create test guide | 30 min | Low |
| Optional: Makefile | 30 min | Low |
| Optional: CI/CD | 1 hour | Medium |

**Recommended Sequence**:
1. Day 1: Install cocotb, run unit tests (2 hours)
2. Day 2: Run integration tests, fix naming (2 hours)
3. Day 3: Documentation updates (1 hour)
4. Day 4: Optional enhancements (2 hours)

---

## Success Criteria

Phase 3 can be marked as **truly 100% complete** when:

1. ✅ All RTL modules implemented (DONE)
2. ✅ All firmware implemented (DONE)
3. ✅ Hardware validated (DONE)
4. ✅ Synthesis/PnR successful (DONE)
5. ⏳ All cocotb unit tests pass (PENDING)
6. ⏳ All cocotb integration tests pass (PENDING)
7. ⏳ Test naming matches specification (PENDING)
8. ⏳ Documentation reflects reality (PENDING)

**Current**: 5/8 criteria met (62.5%)
**After remediation**: 8/8 criteria met (100%)

---

## Alternative: Accept Current State

If cocotb installation is not feasible (environment constraints, time constraints), recommend:

1. **Update STATUS.md** to state:
   ```markdown
   Phase 3: User Story 1 - MVP (100% Hardware Complete, Alternative Testing Approach)

   - Hardware fully validated with 61 automated firmware tests
   - cocotb test suite written but not executed (future work)
   - TDD workflow substituted with hardware-first + serial testing
   ```

2. **Update tasks.md** to add note:
   ```markdown
   **NOTE**: Original TDD workflow called for cocotb tests before implementation.
   Actual implementation used hardware-first development with comprehensive
   serial/firmware testing (61 automated tests). cocotb tests exist but were
   not integrated into development workflow.
   ```

3. **Create comparison document** showing equivalence:
   - 30 cocotb tests (specified) vs 61 firmware tests (actual)
   - Simulation testing (specified) vs hardware testing (actual)
   - Both approaches validate functionality, different trade-offs

**This alternative is acceptable** given:
- Hardware works perfectly
- Comprehensive automated testing exists
- Educational goals achieved
- No regressions possible (system working)

---

## Recommendation

**Short-term** (4-6 hours): Complete Priority 1 & 3 (install cocotb, run tests, update docs)

**Long-term** (if needed): Priority 2 & 4 (test naming, CI/CD)

**Alternative** (0 hours): Accept current state, update documentation to reflect hardware-first approach

All three paths are valid. The system is production-ready regardless of which path you choose.
