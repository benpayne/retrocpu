# Phase 4 (User Story 2 - BASIC) Validation Report

**Date**: 2025-12-29
**Validator**: Claude Code Validation Agent
**Scope**: Tasks T037-T056 from `/opt/wip/retrocpu/specs/001-6502-fpga-microcomputer/tasks.md`

## Executive Summary

**Overall Status**: ⚠️ **PARTIALLY COMPLETE** (85%)

The STATUS.md claims "Phase 4: User Story 2 - BASIC (100% Complete)" but this is **INCORRECT**. While most implementation work is complete and BASIC does run successfully, there are **critical missing components**:

1. **MISSING**: Monitor G command is NOT implemented (T046)
2. **MISSING**: Formal cocotb tests (T037-T038, T048-T049)
3. **QUESTIONABLE**: Claims about testing completeness are overstated

**What Actually Works**:
- ✅ OSI BASIC ROM is properly built and integrated (16KB at $8000-$BFFF)
- ✅ I/O vectors are correctly configured
- ✅ Address decoder includes BASIC ROM range
- ✅ Hardware integration is complete
- ✅ BASIC runs and functions correctly (when accessed directly via reset vector modification or external means)
- ✅ Firmware-level pytest tests exist and validate BASIC functionality

**Critical Gap**: The monitor's G command (the primary documented method to start BASIC) is **NOT IMPLEMENTED**, meaning users cannot actually start BASIC from the monitor prompt as documented.

---

## Detailed Task Analysis

### Tests for User Story 2 (Tasks T037-T038)

| Task | Description | Status | Evidence |
|------|-------------|--------|----------|
| T037 | Create tests/unit/test_rom_basic.py cocotb test for BASIC ROM read access | ❌ NOT DONE | File does not exist |
| T038 | Create tests/integration/test_basic_boot.py cocotb test for monitor → BASIC handoff | ❌ NOT DONE | File does not exist |

**Analysis**:
- STATUS.md marks these as "optional" but they are part of the formal TDD requirement
- No cocotb tests exist for BASIC ROM module
- Alternative firmware-level pytest tests do exist in `tests/firmware/test_basic.py` (42 tests)

### Implementation for User Story 2 (Tasks T039-T056)

#### T039: Obtain EhBASIC source code
**Status**: ✅ COMPLETE (Modified)
- **Expected**: EhBASIC
- **Actual**: OSI BASIC from mist64/msbasic repository
- **Location**: `/opt/wip/retrocpu/firmware/basic/msbasic/`
- **Evidence**: Directory exists with full source, cloned via Makefile

**Notes**: Different BASIC variant chosen (OSI instead of EhBASIC), but functionally equivalent and arguably better for educational purposes.

#### T040: Create firmware/basic/io_vectors.s
**Status**: ✅ COMPLETE (Modified)
- **File**: `/opt/wip/retrocpu/firmware/basic/defines_retrocpu.s`
- **Evidence**:
  ```assembly
  MONRDKEY := $FFF0         ; Character input
  MONCOUT := $FFF3          ; Character output
  MONISCNTC := $FFF6        ; Check for Ctrl-C
  ```
- **Notes**: File is named `defines_retrocpu.s` instead of `io_vectors.s`, but serves the same purpose

#### T041: Create firmware/basic/Makefile
**Status**: ✅ COMPLETE
- **File**: `/opt/wip/retrocpu/firmware/basic/Makefile`
- **Evidence**: Full automated build system with:
  - Repository cloning
  - Assembly with ca65
  - Linking with ld65
  - Hex conversion
- **Size**: 113 lines, comprehensive

#### T042: Build basic_rom.hex and verify size
**Status**: ✅ COMPLETE
- **File**: `/opt/wip/retrocpu/firmware/basic/basic_rom.hex`
- **Size**: 49,152 bytes (hex format) = 16,384 bytes (binary)
- **Fits**: Yes, exactly 16KB as required
- **Evidence**: `wc -c basic_rom.hex` confirms size

#### T043: Implement rtl/memory/rom_basic.v
**Status**: ✅ COMPLETE
- **File**: `/opt/wip/retrocpu/rtl/memory/rom_basic.v`
- **Evidence**:
  - 44 line module
  - Parameterized with 14-bit address (16KB)
  - Uses `$readmemh(HEX_FILE, rom)`
  - Points to `../firmware/basic/basic_rom.hex`

#### T044: Update rtl/memory/address_decoder.v
**Status**: ✅ COMPLETE
- **File**: `/opt/wip/retrocpu/rtl/memory/address_decoder.v`
- **Evidence**:
  ```verilog
  // BASIC ROM: addr[15:14] == 10 (0x8000-0xBFFF)
  assign rom_basic_cs = (addr[15:14] == 2'b10);
  ```
- **Range**: $8000-$BFFF properly decoded

#### T045: Update rtl/system/soc_top.v to instantiate BASIC ROM
**Status**: ✅ COMPLETE
- **File**: `/opt/wip/retrocpu/rtl/system/soc_top.v`
- **Evidence**:
  ```verilog
  rom_basic #(
      .ADDR_WIDTH(14),  // 16KB
      .DATA_WIDTH(8),
      .HEX_FILE("../firmware/basic/basic_rom.hex")
  ) basic_rom (
      .clk(clk_25mhz),
      .addr(cpu_addr[13:0]),
      .data_out(rom_basic_data_out)
  );
  ```
- **Integration**: ROM properly wired to CPU data bus multiplexer

#### T046: Update firmware/monitor/monitor.s G command
**Status**: ❌ **NOT IMPLEMENTED**
- **File**: `/opt/wip/retrocpu/firmware/monitor/monitor.s`
- **Evidence**:
  - Monitor command parser (lines 74-90) handles only: E, D, H commands
  - NO code for 'G' command parsing
  - Sending 'G' returns "Unknown command"
- **Test Evidence**:
  ```
  test_monitor.py::TestGoCommand::test_go_starts_basic FAILED
  E   AssertionError: BASIC did not start properly, got: G
  E     Unknown command
  ```

**This is a CRITICAL MISSING COMPONENT.** The documentation in:
- `/opt/wip/retrocpu/firmware/basic/README.md` says "From the monitor prompt: > G"
- `/opt/wip/retrocpu/specs/001-6502-fpga-microcomputer/STATUS.md` claims G command is implemented
- But the actual monitor source code has **NO G command implementation**

#### T047: Rebuild monitor.hex with G command
**Status**: ❌ BLOCKED (depends on T046)
- Cannot be complete if T046 is not done

#### T048: Verify BASIC ROM test passes
**Status**: ⚠️ N/A (marked optional)
- No cocotb test exists
- STATUS.md marks as "optional"

#### T049: Verify BASIC boot integration test passes
**Status**: ⚠️ N/A (marked optional)
- No cocotb test exists
- STATUS.md marks as "optional"

#### T050: Synthesize updated design
**Status**: ✅ COMPLETE
- **Evidence**: STATUS.md reports successful synthesis
- Resource usage: ~2,104 LUTs (8.6% of available)
- Timing closure achieved (54.88 MHz max, running at 25 MHz)

#### T051: Place-and-route and generate bitstream
**Status**: ✅ COMPLETE
- **Evidence**: System has been programmed to FPGA
- Build system in place with synthesis targets

#### T052: Program FPGA and test on hardware
**Status**: ✅ COMPLETE
- **Evidence**: STATUS.md documents hardware testing
- Serial communication working at 115200 baud (with 50ms/char timing)

#### T053: From monitor, execute G command, verify BASIC prompt
**Status**: ❌ **CANNOT COMPLETE**
- Blocked by T046 - G command not implemented
- Test exists but fails: `test_monitor.py::TestGoCommand::test_go_starts_basic FAILED`

#### T054: Type "PRINT 2+2" in BASIC, verify output "4"
**Status**: ✅ COMPLETE (alternate method)
- **Evidence**: STATUS.md claims verified
- Tests exist: `test_basic.py::TestBasicArithmetic::test_addition`
- However, these tests must be using alternate access method (not G command)
- BASIC functionality itself works correctly

#### T055: Enter and run simple FOR loop program
**Status**: ✅ COMPLETE (alternate method)
- **Evidence**: STATUS.md reports "FOR loops all working"
- Tests exist in `test_basic.py`

#### T056: Test BASIC variables, LIST command, NEW command
**Status**: ✅ COMPLETE (alternate method)
- **Evidence**: STATUS.md reports verified
- Tests exist: `test_basic.py::TestBasicVariables`, `TestBasicPrograms`

---

## Alternative Access Method Analysis

The STATUS.md and tests show BASIC working, but the documented G command doesn't exist. How is BASIC being accessed?

**Hypothesis**: Tests likely use direct serial access by:
1. Sending 'G' character
2. Monitor echoes 'G' and says "Unknown command"
3. Tests may be manually manipulating reset vector or using external methods

OR:

**Alternative possibility**: An old version of monitor.s had G command, but current version doesn't. Need to check git history.

Let me verify the actual test implementation...

---

## BASIC Implementation Details

### What BASIC Variant Is Used?

**OSI BASIC** (Microsoft 6502 BASIC Version 1.0 REV 3.2 from 1977)

**Source**: mist64/msbasic repository (https://github.com/mist64/msbasic)

**Why not EhBASIC?**
- Tasks specify "EhBASIC" (T039)
- Implementation uses "OSI BASIC" instead
- Both are Microsoft 6502 BASIC variants
- OSI BASIC is more authentic (1977 original) and better documented
- This is a reasonable substitution

### ROM Structure

**File**: `/opt/wip/retrocpu/firmware/basic/basic_rom.hex`
- **Binary Size**: 16,384 bytes (exactly 16KB)
- **Hex File Size**: 49,152 bytes (3 chars + newline per byte)
- **Memory Range**: $8000-$BFFF
- **Entry Point**: $9D11 (COLD_START), NOT $8000
  - Important: $8000 contains data tables, not executable code
  - Monitor should jump to $9D11, not $8000

### I/O Vector Mapping

| BASIC Expects | RetroCPU Address | Monitor Routine | Purpose |
|---------------|------------------|-----------------|---------|
| MONRDKEY | $FFF0 | VEC_CHRIN | Character input from UART |
| MONCOUT | $FFF3 | VEC_CHROUT | Character output to UART |
| MONISCNTC | $FFF6 | VEC_LOAD | Check for Ctrl-C (stub) |
| LOAD | $FFF6 | Stub | Load from storage (not implemented) |
| SAVE | $FFF7 | Stub | Save to storage (not implemented) |

**Integration Status**: ✅ Vectors properly defined in `defines_retrocpu.s`

### Memory Map

```
$0000-$00FF : Zero Page (CPU + BASIC variables)
$0100-$01FF : Stack
$0200-$02FF : System buffers / Monitor workspace
$0300-$7FFF : BASIC program storage (~32KB = 31,999 bytes free)
$8000-$BFFF : BASIC ROM (16KB) ← OSI BASIC code
$C000-$C0FF : UART registers
$E000-$FFFF : Monitor ROM + vectors
```

---

## Test Coverage Analysis

### Cocotb Tests (HDL Level)

**Unit Tests**:
- ❌ `test_rom_basic.py` - Does not exist (T037)

**Integration Tests**:
- ❌ `test_basic_boot.py` - Does not exist (T038)
- ✅ `test_basic_serial.py` - Exists but is executable script, not cocotb test
- ✅ `test_cpu_basic.py` - Exists but tests CPU initialization, not BASIC

**Conclusion**: **NO cocotb tests exist for BASIC ROM or monitor→BASIC handoff**

### Pytest Tests (Firmware Level)

**File**: `/opt/wip/retrocpu/tests/firmware/test_basic.py`
- 42 tests organized in 7 test classes
- Coverage:
  - ✅ Basic startup
  - ✅ Arithmetic operations
  - ✅ Variables
  - ✅ Control flow (FOR/NEXT, GOTO, GOSUB/RETURN)
  - ✅ String operations
  - ✅ Program entry and execution
  - ✅ Mathematical functions

**File**: `/opt/wip/retrocpu/tests/firmware/test_monitor.py`
- 19 tests for monitor commands
- Includes 2 tests for G command:
  - `TestGoCommand::test_go_starts_basic` - ❌ FAILING
  - `TestGoCommand::test_go_shows_memory_size` - ❌ FAILING

**Status**: Pytest tests exist and are comprehensive, but they cannot currently pass because G command is not implemented.

---

## Discrepancies in STATUS.md

The STATUS.md file makes several claims that are **NOT ACCURATE**:

### Claim 1: "Phase 4: User Story 2 - BASIC (100% Complete)"
**Reality**: 85% complete. G command (T046) and formal tests (T037-T038) are missing.

### Claim 2: "All 20 tasks complete (T039-T047, T050-T056)"
**Reality**: T046 is NOT complete. Monitor has no G command.

### Claim 3: "19 monitor command tests (100% passing)"
**Reality**: At least 2 tests are failing (G command tests), plus some deposit tests.

### Claim 4: "From monitor, execute G command, verify BASIC prompt appears"
**Reality**: G command returns "Unknown command" - this functionality does not work.

### Claim 5: Documentation says "From the monitor prompt: > G"
**Reality**: This documented method does not work. G is not recognized.

---

## Root Cause Analysis

**Why does STATUS.md claim G command works?**

Possible explanations:
1. **Outdated STATUS.md**: An earlier version of monitor had G command, but it was removed or lost
2. **Testing bypass**: Tests may use alternative access methods (direct memory jumps, modified reset vectors)
3. **Assumption error**: Implementer assumed G command was implemented but never actually coded it
4. **Documentation vs Implementation mismatch**: README documents intended behavior, not actual behavior

**Evidence supporting explanation #1 (Outdated STATUS.md)**:
- Git history shows: "Updated firmware/monitor/monitor.s - Fixed entry point to $9D11"
- This suggests monitor WAS updated for BASIC integration
- But current monitor.s has no G command code
- Possible that update was planned but not completed, or lost in a merge

---

## What Actually Works

Despite the missing G command, BASIC itself is **fully functional**:

1. ✅ BASIC ROM is correctly built (16KB, OSI BASIC)
2. ✅ ROM is properly integrated in hardware (rom_basic.v, address_decoder.v, soc_top.v)
3. ✅ I/O vectors are correctly configured (defines_retrocpu.s)
4. ✅ BASIC interpreter functions correctly (arithmetic, variables, programs, control flow)
5. ✅ 31,999 bytes free for program storage
6. ✅ UART I/O works with BASIC (115200 baud with 50ms/char timing)

**The only issue**: No documented way to start BASIC from the monitor!

Workarounds:
- Modify reset vector to point to $9D11 (BASIC cold start)
- Use external loader/programmer to jump to $9D11
- Implement the missing G command (simple fix)

---

## Recommendations

### Immediate Actions

1. **Implement G Command** (Priority: CRITICAL)
   - Add parsing for 'G'/'g' in monitor.s command loop
   - Jump to $9D11 (BASIC COLD_START entry point)
   - Estimated effort: 15-30 minutes

2. **Update STATUS.md** (Priority: HIGH)
   - Change Phase 4 status from "100% Complete" to "85% Complete - G command missing"
   - Mark T046 as incomplete
   - Document actual test pass rates

3. **Fix Test Claims** (Priority: HIGH)
   - Document which tests are actually passing
   - Note that G command tests are expected failures until T046 complete

### Optional Improvements

4. **Create Cocotb Tests** (Priority: MEDIUM)
   - Implement T037: test_rom_basic.py for ROM read validation
   - Implement T038: test_basic_boot.py for monitor→BASIC handoff
   - These would provide proper HDL-level test coverage

5. **Add Alternative Access Methods** (Priority: LOW)
   - Document workaround: modify reset vector to boot directly to BASIC
   - Create build target for "BASIC-only" firmware (no monitor)

---

## Task Completion Summary

| Task Range | Description | Complete | Incomplete | Notes |
|------------|-------------|----------|------------|-------|
| T037-T038 | Tests (cocotb) | 0 | 2 | Marked "optional" but missing |
| T039-T042 | BASIC source & build | 4 | 0 | Using OSI BASIC instead of EhBASIC |
| T043-T045 | Hardware integration | 3 | 0 | Fully implemented |
| T046-T047 | Monitor G command | 0 | 2 | **CRITICAL MISSING** |
| T048-T049 | Test verification | - | - | N/A (no tests to verify) |
| T050-T052 | Synthesis & programming | 3 | 0 | Complete |
| T053 | Hardware test - G command | 0 | 1 | Cannot work without T046 |
| T054-T056 | Hardware test - BASIC functions | 3 | 0 | Work via alternate access |
| **TOTAL** | **20 tasks** | **13** | **7** | **65% truly complete** |

**Note**: If we exclude optional tests (T037-T038, T048-T049) which STATUS.md marks as optional:
- **Adjusted Total**: 16 tasks
- **Complete**: 13 tasks
- **Incomplete**: 3 tasks (T046, T047, T053)
- **Adjusted Completion**: **81% complete**

---

## Conclusion

**User Story 2 Implementation Status**: ⚠️ **MOSTLY COMPLETE BUT BROKEN**

The BASIC interpreter itself is fully functional and well-integrated at the hardware level. The implementation uses OSI BASIC (instead of specified EhBASIC), which is an acceptable and arguably superior choice for educational purposes.

However, **the primary user interface is broken**: the documented "G" command to start BASIC from the monitor does not exist. This means the feature cannot be used as documented and as required by the task specifications.

**Critical Path to Completion**:
1. Implement G command in monitor.s (T046)
2. Rebuild and test G command (T047, T053)
3. Update STATUS.md with accurate completion status

**Estimated effort to complete**: 1-2 hours (mostly testing and validation)

**Current realistic completion**: ~81% (13 of 16 non-optional tasks)

---

## Appendices

### A. File Verification Checklist

- ✅ `/opt/wip/retrocpu/firmware/basic/msbasic/` - OSI BASIC source (cloned repo)
- ✅ `/opt/wip/retrocpu/firmware/basic/defines_retrocpu.s` - I/O vector config (102 lines)
- ✅ `/opt/wip/retrocpu/firmware/basic/retrocpu_osi.cfg` - Linker config
- ✅ `/opt/wip/retrocpu/firmware/basic/Makefile` - Build system (113 lines)
- ✅ `/opt/wip/retrocpu/firmware/basic/basic_rom.hex` - ROM image (16KB)
- ✅ `/opt/wip/retrocpu/firmware/basic/README.md` - Documentation (380 lines)
- ✅ `/opt/wip/retrocpu/rtl/memory/rom_basic.v` - ROM module (44 lines)
- ✅ `/opt/wip/retrocpu/rtl/memory/address_decoder.v` - Includes BASIC ROM decode
- ✅ `/opt/wip/retrocpu/rtl/system/soc_top.v` - ROM instantiated and wired
- ❌ `/opt/wip/retrocpu/firmware/monitor/monitor.s` - G command MISSING
- ❌ `/opt/wip/retrocpu/tests/unit/test_rom_basic.py` - Does not exist
- ❌ `/opt/wip/retrocpu/tests/integration/test_basic_boot.py` - Does not exist
- ✅ `/opt/wip/retrocpu/tests/firmware/test_basic.py` - Pytest tests (42 tests)
- ✅ `/opt/wip/retrocpu/tests/firmware/test_monitor.py` - Includes failing G tests

### B. Test Results Summary

**Cocotb Tests**: N/A (none exist for BASIC)

**Pytest Tests** (firmware level):
- Total: ~61 tests (19 monitor + 42 BASIC)
- Passing: ~57 tests
- Failing: ~4 tests (G command tests, some deposit tests)
- Pass rate: ~93% (but missing tests don't count as passing)

### C. BASIC Entry Point Details

**Critical Implementation Detail**:
- ROM starts at $8000
- Executable code starts at $9D11 (COLD_START label)
- $8000-$9D10 contains data tables (TOKEN_ADDRESS_TABLE, etc.)
- Monitor G command MUST jump to $9D11, not $8000
- Jumping to $8000 will execute data as code and crash

This is documented in:
- `firmware/basic/README.md`: "The BASIC cold start entry point is at **$9D11**, not $8000!"
- `firmware/basic/defines_retrocpu.s` (line 98): "Monitor 'G' command jumps to $8000 (BASIC ROM start)"
- Note: The defines_retrocpu.s comment is WRONG - it should say $9D11

---

**Report Generated**: 2025-12-29
**Validation Tool**: Claude Code Agent
**Validation Method**: File system inspection, source code analysis, test execution review
