# RetroCPU Remediation Task List
**Date**: 2025-12-29
**Purpose**: Close gaps identified in validation - restore all claimed functionality

---

## Summary of Issues Found

After comprehensive validation, the following gaps were identified:

1. ❌ **Monitor E/D/G commands print "not implemented"** - Only H command works
2. ❌ **LCD controller not connected in soc_top.v** - Code exists but not integrated
3. ❌ **PS/2 keyboard not connected in soc_top.v** - Code exists but not integrated
4. ❌ **No requirements.txt** - Cannot recreate venv
5. ⚠️ **Cocotb tests exist but some can't run** - Need verification
6. ⚠️ **Missing formal integration tests** - test_cpu_memory.py, test_system_boot.py

---

## Priority Levels

- **P0 - CRITICAL**: Blocks basic system usage (User Story 1 MVP)
- **P1 - HIGH**: Needed for User Story 2 (BASIC)
- **P2 - MEDIUM**: Needed for User Stories 3-4 (LCD/PS2)
- **P3 - LOW**: Nice to have, testing infrastructure

---

# PHASE 1: Core Monitor Functionality (User Story 1 - MVP)

## P0-1: Implement Monitor E Command (Examine Memory)
**Blocks**: User Story 1, T035
**Estimated Time**: 1-2 hours
**Status**: NOT IMPLEMENTED (currently prints "not implemented")

### Requirements
- Read hex address from UART input (4 hex digits)
- Read memory at that address
- Display address:value in hex format
- Example: User types "E 0200" → Display "0200: 42"

### Files to Modify
- `/opt/wip/retrocpu/firmware/monitor/monitor.s`
  - Implement `CMD_EXAMINE` (currently at line 104)
  - Add hex input parsing routine
  - Add address display routine

### Implementation Steps
1. Create `READ_HEX_BYTE` subroutine (reads 2 hex chars → byte)
2. Create `READ_HEX_WORD` subroutine (reads 4 hex chars → 16-bit address)
3. Implement `CMD_EXAMINE`:
   - Skip whitespace
   - Call READ_HEX_WORD to get address
   - Load byte from (ADDR_HI:ADDR_LO)
   - Print address in hex (4 digits)
   - Print ": "
   - Print value in hex (2 digits)
   - Print newline

### Testing
- Build monitor.hex
- Program FPGA
- Test: `E 0000` (should show zero page)
- Test: `E E000` (should show monitor ROM start)
- Test: `E C000` (should show UART data register)

---

## P0-2: Implement Monitor D Command (Deposit Memory)
**Blocks**: User Story 1, T035
**Estimated Time**: 1-2 hours
**Status**: NOT IMPLEMENTED (currently prints "not implemented")

### Requirements
- Read hex address from UART input (4 hex digits)
- Read hex value from UART input (2 hex digits)
- Write value to that address (if writable)
- Display confirmation
- Example: User types "D 0200 42" → Write $42 to $0200, display "OK"

### Files to Modify
- `/opt/wip/retrocpu/firmware/monitor/monitor.s`
  - Implement `CMD_DEPOSIT` (currently at line 116)
  - Reuse hex parsing from P0-1

### Implementation Steps
1. Reuse `READ_HEX_WORD` from P0-1
2. Reuse `READ_HEX_BYTE` from P0-1
3. Implement `CMD_DEPOSIT`:
   - Skip whitespace
   - Call READ_HEX_WORD to get address
   - Skip whitespace
   - Call READ_HEX_BYTE to get value
   - Store value to (ADDR_HI:ADDR_LO)
   - Print "OK\r\n" or "ADDR: VAL\r\n"

### Testing
- Test: `D 0200 42` → then `E 0200` (should show 42)
- Test: `D 0000 11` → then `E 0000` (should show 11, zero page write)
- Test: `D E000 AA` → No change (ROM is read-only)

---

## P1-1: Implement Monitor G Command (Go to BASIC)
**Blocks**: User Story 2, T046, T047, T053
**Estimated Time**: 30 minutes
**Status**: NOT IN PARSER (welcome message claims it exists)

### Requirements
- Parse 'G' or 'g' command
- Jump to BASIC entry point at $9D11 (COLD_START)
- Never returns (BASIC takes over)

### Files to Modify
- `/opt/wip/retrocpu/firmware/monitor/monitor.s`
  - Add G command to parser (after line 90)
  - Implement `CMD_GO`

### Implementation Steps
1. Add to command parser (around line 90):
   ```assembly
   CMP #'G'           ; Go to BASIC
   BEQ CMD_GO
   CMP #'g'
   BEQ CMD_GO
   ```

2. Implement CMD_GO (before UNKNOWN_MSG):
   ```assembly
   CMD_GO:
       JMP $9D11      ; Jump to OSI BASIC COLD_START
   ```

### Testing
- Build monitor.hex
- Program FPGA
- Test: Type `G` → Should see "BASIC READY" or similar BASIC prompt
- Test: `PRINT 2+2` → Should see `4`

### Critical Notes
- **DO NOT jump to $8000** - That's data tables, not executable code
- **MUST jump to $9D11** - That's the COLD_START routine
- This is a ONE-WAY operation - BASIC doesn't return to monitor

---

## P0-3: Create requirements.txt for Python Environment
**Blocks**: Reproducible development environment
**Estimated Time**: 15 minutes
**Status**: MISSING

### Requirements
- Document all Python dependencies
- Allow `pip install -r requirements.txt` to recreate venv
- Include cocotb, pytest, and all testing dependencies

### Files to Create
- `/opt/wip/retrocpu/requirements.txt`

### Implementation Steps
1. Activate venv: `source venv/bin/activate`
2. Generate requirements: `pip freeze > requirements.txt`
3. Review and clean up (remove unnecessary packages)
4. Add comments for major sections

### Minimum Required Packages
```
# HDL Testing
cocotb>=2.0.0
cocotb-test>=0.2.0

# Python Testing
pytest>=9.0.0
pytest-timeout>=2.4.0

# Serial Communication (for firmware tests)
pyserial>=3.5

# Optional: Waveform viewing
# gtkwave (system package)
```

### Testing
- Delete venv: `rm -rf venv`
- Create new venv: `python3 -m venv venv`
- Activate: `source venv/bin/activate`
- Install: `pip install -r requirements.txt`
- Test: `python -c "import cocotb; print(cocotb.__version__)"`

---

# PHASE 2: LCD Integration (User Story 3)

## P2-1: Connect LCD Controller in soc_top.v
**Blocks**: User Story 3
**Estimated Time**: 2-3 hours
**Status**: RTL exists but not instantiated in soc_top.v

### Current Status
- ✅ `rtl/peripherals/lcd/lcd_controller.v` exists
- ✅ `rtl/peripherals/lcd/lcd_timing.v` exists
- ✅ `rtl/peripherals/lcd/lcd_init_fsm.v` exists
- ✅ Address decoder includes `lcd_cs` signal
- ❌ NO LCD module instantiation in soc_top.v
- ❌ NO LCD pins in top-level port list

### Files to Modify
1. `/opt/wip/retrocpu/rtl/system/soc_top.v`
   - Add LCD pins to module port list
   - Instantiate lcd_controller
   - Connect to data bus

2. `/opt/wip/retrocpu/colorlight_i5_debug.lpf` (or main .lpf)
   - Add LCD pin constraints (7 pins for 4-bit mode)

### Implementation Steps

#### Step 1: Add LCD pins to soc_top.v (after line 29)
```verilog
module soc_top (
    // Clock and reset
    input  wire clk_25mhz,
    input  wire reset_button_n,

    // UART
    output wire uart_tx,
    input  wire uart_rx,

    // LCD (HD44780 4-bit mode)
    output wire lcd_rs,          // Register select (0=cmd, 1=data)
    output wire lcd_e,           // Enable pulse
    output wire [3:0] lcd_db,    // Data bus (4-bit mode)

    // Debug LEDs
    output wire [3:0] led
);
```

#### Step 2: Instantiate LCD controller (after UART section, ~line 175)
```verilog
// ========================================================================
// LCD Controller (HD44780 4-bit mode)
// ========================================================================

wire [7:0] lcd_data_out;

lcd_controller #(
    .CLK_FREQ(25000000)        // 25 MHz system clock
) lcd_inst (
    .clk(clk_25mhz),
    .rst(system_rst),
    .cs(lcd_cs),
    .we(lcd_cs && mem_we),     // Write when LCD selected and CPU writes
    .addr(cpu_addr[1:0]),      // 4 registers: $C100-$C103
    .data_in(cpu_data_out),
    .data_out(lcd_data_out),

    // Physical LCD interface
    .lcd_rs(lcd_rs),
    .lcd_e(lcd_e),
    .lcd_db(lcd_db)
);
```

#### Step 3: Update data bus multiplexer (around line 191)
```verilog
always @(*) begin
    case (1'b1)
        ram_cs:         cpu_data_in_mux = ram_data_out;
        rom_basic_cs:   cpu_data_in_mux = rom_basic_data_out;
        rom_monitor_cs: cpu_data_in_mux = rom_monitor_data_out;
        uart_cs:        cpu_data_in_mux = uart_data_out;
        lcd_cs:         cpu_data_in_mux = lcd_data_out;    // ADD THIS
        default:        cpu_data_in_mux = 8'hFF;
    endcase
end
```

#### Step 4: Add LCD pin constraints
Choose 7 available pins on PMOD connector. Example:
```lpf
# LCD (HD44780 4-bit mode) - PMOD pins
LOCATE COMP "lcd_rs" SITE "XX";
LOCATE COMP "lcd_e" SITE "XX";
LOCATE COMP "lcd_db[0]" SITE "XX";
LOCATE COMP "lcd_db[1]" SITE "XX";
LOCATE COMP "lcd_db[2]" SITE "XX";
LOCATE COMP "lcd_db[3]" SITE "XX";

IOBUF PORT "lcd_rs" IO_TYPE=LVCMOS33;
IOBUF PORT "lcd_e" IO_TYPE=LVCMOS33;
IOBUF PORT "lcd_db[0]" IO_TYPE=LVCMOS33;
IOBUF PORT "lcd_db[1]" IO_TYPE=LVCMOS33;
IOBUF PORT "lcd_db[2]" IO_TYPE=LVCMOS33;
IOBUF PORT "lcd_db[3]" IO_TYPE=LVCMOS33;
```

**NOTE**: User needs to provide actual pin assignments based on their board

### Testing
1. Synthesis: `cd build && make synth` (should pass)
2. PnR: `make pnr` (should pass)
3. Generate bitstream: `make bitstream`
4. Program FPGA: `make program`
5. Test write to $C100 (data) and $C101 (command)
6. Connect LCD and verify characters appear

---

## P2-2: Add LCD Boot Message to Monitor
**Blocks**: User Story 3 enhancement
**Estimated Time**: 1 hour
**Status**: OPTIONAL (LCD hardware integration more important)

### Requirements
- After LCD initialization, display welcome message
- "RetroCPU v1.0" on line 1
- "6502 System" on line 2

### Files to Modify
- `/opt/wip/retrocpu/firmware/monitor/monitor.s`
  - Add LCD output routines
  - Send init sequence to LCD
  - Display boot message

### Implementation Steps
1. Create `LCD_OUT` subroutine (write character to $C100)
2. Create `LCD_CMD` subroutine (write command to $C101)
3. Create `LCD_INIT` subroutine (initialization sequence)
4. Create `LCD_PRINT_STRING` subroutine
5. In RESET, after UART welcome, call LCD_INIT and print message

### Testing
- Power on system with LCD connected
- Should see "RetroCPU v1.0" and "6502 System" on LCD

---

# PHASE 3: PS/2 Keyboard Integration (User Story 4)

## P2-3: Connect PS/2 Controller in soc_top.v
**Blocks**: User Story 4
**Estimated Time**: 2-3 hours
**Status**: RTL exists but not instantiated in soc_top.v

### Current Status
- ✅ `rtl/peripherals/ps2/ps2_wrapper.v` exists
- ✅ PS/2 library in `rtl/peripherals/ps2/ps2-controller-lib/`
- ✅ Address decoder includes `ps2_cs` signal
- ✅ Pins K5 (clock) and B3 (data) defined in .lpf
- ❌ NO PS/2 module instantiation in soc_top.v
- ❌ NO PS/2 pins in top-level port list

### Files to Modify
1. `/opt/wip/retrocpu/rtl/system/soc_top.v`
   - Add PS/2 pins to module port list
   - Instantiate ps2_wrapper
   - Connect to data bus

### Implementation Steps

#### Step 1: Add PS/2 pins to soc_top.v
```verilog
module soc_top (
    // Clock and reset
    input  wire clk_25mhz,
    input  wire reset_button_n,

    // UART
    output wire uart_tx,
    input  wire uart_rx,

    // LCD (HD44780 4-bit mode)
    output wire lcd_rs,
    output wire lcd_e,
    output wire [3:0] lcd_db,

    // PS/2 Keyboard
    input  wire ps2_clk,         // K5
    input  wire ps2_data,        // B3

    // Debug LEDs
    output wire [3:0] led
);
```

#### Step 2: Instantiate PS/2 wrapper (after LCD section)
```verilog
// ========================================================================
// PS/2 Keyboard Controller
// ========================================================================

wire [7:0] ps2_data_out;

ps2_wrapper #(
    .CLK_FREQ(25000000)        // 25 MHz system clock
) ps2_inst (
    .clk(clk_25mhz),
    .rst(system_rst),
    .cs(ps2_cs),
    .we(ps2_cs && mem_we),     // Write enable (for future commands)
    .addr(cpu_addr[1:0]),      // Registers: $C200-$C203
    .data_in(cpu_data_out),
    .data_out(ps2_data_out),

    // Physical PS/2 interface
    .ps2_clk(ps2_clk),
    .ps2_data(ps2_data)
);
```

#### Step 3: Update data bus multiplexer
```verilog
always @(*) begin
    case (1'b1)
        ram_cs:         cpu_data_in_mux = ram_data_out;
        rom_basic_cs:   cpu_data_in_mux = rom_basic_data_out;
        rom_monitor_cs: cpu_data_in_mux = rom_monitor_data_out;
        uart_cs:        cpu_data_in_mux = uart_data_out;
        lcd_cs:         cpu_data_in_mux = lcd_data_out;
        ps2_cs:         cpu_data_in_mux = ps2_data_out;    // ADD THIS
        default:        cpu_data_in_mux = 8'hFF;
    endcase
end
```

#### Step 4: Verify pin constraints exist
```lpf
# PS/2 Keyboard (should already be in .lpf)
LOCATE COMP "ps2_clk" SITE "K5";
LOCATE COMP "ps2_data" SITE "B3";
IOBUF PORT "ps2_clk" IO_TYPE=LVCMOS33;
IOBUF PORT "ps2_data" IO_TYPE=LVCMOS33;
```

### Testing
1. Synthesis: `cd build && make synth`
2. PnR: `make pnr`
3. Bitstream: `make bitstream`
4. Program: `make program`
5. Connect PS/2 keyboard
6. Read from $C200 (scan code) and $C201 (status)
7. Press keys, verify scan codes appear

---

## P2-4: Add PS/2 Keyboard Support to Monitor
**Blocks**: User Story 4 completion
**Estimated Time**: 3-4 hours
**Status**: NOT IMPLEMENTED

### Requirements
- Monitor can read input from PS/2 keyboard OR UART
- Scan codes decoded to ASCII
- Keyboard input appears in command prompt

### Files to Modify
- `/opt/wip/retrocpu/firmware/monitor/monitor.s`
  - Create `PS2_READ` subroutine
  - Create `PS2_TO_ASCII` lookup table
  - Modify `CHRIN` to check both UART and PS/2

### Implementation Steps
1. Create scan code to ASCII translation table (100+ bytes)
2. Implement `PS2_READ_SCANCODE` (poll $C200/$C201)
3. Implement `PS2_DECODE_ASCII` (handle make/break codes, shift state)
4. Modify `CHRIN`:
   - Check UART status first
   - If no UART data, check PS/2 status
   - Return first available character
5. Track shift/control state for proper ASCII conversion

### Testing
- Boot monitor
- Press keys on PS/2 keyboard
- Verify characters appear in prompt
- Test: Type `H` on keyboard → should show help

---

# PHASE 4: Testing Infrastructure (All User Stories)

## P3-1: Run and Fix Cocotb Unit Tests
**Blocks**: Test infrastructure validation
**Estimated Time**: 2-3 hours
**Status**: Tests exist, imports fixed, need to verify they pass

### Files to Test
All in `/opt/wip/retrocpu/tests/unit/`:
- test_clock_divider.py
- test_reset_controller.py
- test_ram.py
- test_address_decoder.py
- test_uart_tx.py
- test_uart_rx.py
- test_lcd_timing.py
- test_lcd_init_fsm.py
- test_lcd_controller.py

### Implementation Steps
1. Activate venv: `source venv/bin/activate`
2. Run each test: `cd tests/unit && pytest test_clock_divider.py -v`
3. For each failing test:
   - Review error message
   - Check if module path is correct
   - Check if test expectations match implementation
   - Fix test or implementation as needed
4. Document results

### Success Criteria
- All unit tests pass OR
- Failing tests have documented issues with plan to fix

---

## P3-2: Create Missing Integration Tests
**Blocks**: Test coverage completeness
**Estimated Time**: 2-3 hours
**Status**: 2 tests missing (per spec)

### Tests to Create

#### Test 1: test_cpu_memory.py (T015)
**File**: `/opt/wip/retrocpu/tests/integration/test_cpu_memory.py`

**Purpose**: Verify CPU can read/write RAM correctly

**Test cases**:
1. CPU writes to zero page, reads back
2. CPU writes to stack, reads back
3. CPU writes to general RAM, reads back
4. CPU reads from ROM (monitor/BASIC)
5. ROM writes are ignored

#### Test 2: test_system_boot.py (T016)
**File**: `/opt/wip/retrocpu/tests/integration/test_system_boot.py`

**Purpose**: Verify system boots and monitor starts

**Test cases**:
1. System comes out of reset
2. CPU fetches from reset vector
3. Monitor initialization runs
4. UART outputs welcome message
5. Monitor prompt appears

### Implementation Steps
1. Study existing integration tests as templates
2. Create test files with cocotb framework
3. Write test cases
4. Run tests: `pytest test_cpu_memory.py -v`
5. Debug and fix issues

---

# PHASE 5: Documentation & Validation

## P3-3: Update STATUS.md with Accurate Status
**Blocks**: Honest project status
**Estimated Time**: 30 minutes
**Status**: Current STATUS.md overstates completion

### Updates Needed
1. Change Phase 3 from "100%" to "76%" (realistic)
2. Change Phase 4 from "100%" to "50%" (G command missing, E/D not working)
3. Document what's actually working vs claimed
4. Update "Current System Capabilities" section
5. Add "Known Issues" section

### Known Issues to Document
- Monitor E/D commands print "not implemented"
- Monitor G command doesn't exist
- LCD controller not connected
- PS/2 keyboard not connected
- Some cocotb tests not verified

---

## P3-4: Create Comprehensive Test Suite Runner
**Blocks**: Regression testing
**Estimated Time**: 1 hour
**Status**: OPTIONAL

### Files to Create
- `/opt/wip/retrocpu/tests/run_all_tests.sh`

### Purpose
- Single command to run all tests (unit + integration + firmware)
- Generate test report
- Exit with proper status code

### Implementation
```bash
#!/bin/bash
set -e

echo "Running RetroCPU Test Suite..."
echo "================================"

# Unit tests
echo "Running unit tests..."
cd tests/unit
pytest -v --tb=short

# Integration tests
echo "Running integration tests..."
cd ../integration
pytest -v --tb=short

# Firmware tests (if hardware connected)
if [ "$RUN_HARDWARE_TESTS" = "1" ]; then
    echo "Running firmware tests..."
    cd ../firmware
    pytest -v --tb=short
fi

echo "All tests passed!"
```

---

# Task Summary & Timeline

## Critical Path (MVP Working)
**Total: 5-7 hours**
1. P0-1: Implement E command (1-2 hrs)
2. P0-2: Implement D command (1-2 hrs)
3. P1-1: Implement G command (30 min)
4. P0-3: Create requirements.txt (15 min)
5. Test monitor commands (1 hr)
6. Validate User Story 1 & 2 (1 hr)

## Full Restoration (All User Stories 1-2 Working)
**Total: 7-9 hours**
- Critical Path (above) + testing/validation

## Complete Feature Set (User Stories 3-4)
**Total: 15-20 hours**
- Critical Path
- P2-1: LCD integration (2-3 hrs)
- P2-2: LCD boot message (1 hr)
- P2-3: PS/2 integration (2-3 hrs)
- P2-4: PS/2 monitor support (3-4 hrs)
- Testing (2-3 hrs)

## Full Test Infrastructure
**Total: 20-25 hours**
- Complete Feature Set (above)
- P3-1: Fix cocotb tests (2-3 hrs)
- P3-2: Create missing tests (2-3 hrs)
- P3-3: Update documentation (30 min)
- P3-4: Test runner (1 hr)

---

# Execution Strategy

## Option A: Minimum Viable Restoration (Recommended First)
**Goal**: Get User Stories 1 & 2 working correctly
**Time**: 1 day (5-7 hours)
**Tasks**: P0-1, P0-2, P1-1, P0-3

After this, you'll have:
- ✅ Working monitor with E/D commands
- ✅ G command that starts BASIC
- ✅ Reproducible dev environment

## Option B: Full Feature Restoration
**Goal**: All hardware features working (LCD + PS/2)
**Time**: 2-3 days (15-20 hours)
**Tasks**: All P0-P2 tasks

After this, you'll have:
- ✅ Everything from Option A
- ✅ LCD display working
- ✅ PS/2 keyboard working
- ✅ Standalone computer (no PC needed)

## Option C: Complete Professional Quality
**Goal**: Production-ready with full test coverage
**Time**: 3-4 days (20-25 hours)
**Tasks**: All P0-P3 tasks

After this, you'll have:
- ✅ Everything from Option B
- ✅ Complete test suite passing
- ✅ CI/CD ready
- ✅ Accurate documentation

---

# Parallel Execution Opportunities

Multiple developers can work simultaneously:

## Team of 2
- **Dev A**: Monitor commands (P0-1, P0-2, P1-1) - 3-4 hrs
- **Dev B**: LCD integration (P2-1, P2-2) - 3-4 hrs
- Then merge and test together

## Team of 3
- **Dev A**: Monitor commands - 3-4 hrs
- **Dev B**: LCD integration - 3-4 hrs
- **Dev C**: PS/2 integration (P2-3) - 2-3 hrs
- Then merge and integrate

---

# Next Steps

**Recommend starting with P0-1 (Implement E command) because:**
1. It's the foundation for D command (reuse hex parsing)
2. It's user-visible functionality
3. It validates the monitor framework works
4. Quick win to build momentum

After P0-1 works, P0-2 and P1-1 will be trivial.

**Ready to begin? Choose:**
- Start with P0-1 (E command)?
- Execute full critical path (P0-1 → P0-2 → P1-1)?
- Different prioritization?
