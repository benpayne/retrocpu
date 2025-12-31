"""
Test suite for gpu_registers.v module
Tests the GPU register interface for the DVI Character Display

Register Map (0xC010-0xC016):
- 0xC010 (0x0): CHAR_DATA (WO) - Write character at cursor, auto-advance
- 0xC011 (0x1): CURSOR_ROW (RW) - Cursor row (0-29)
- 0xC012 (0x2): CURSOR_COL (RW) - Cursor column (0-39 or 0-79)
- 0xC013 (0x3): CONTROL (WO) - bit[0]=CLEAR, bit[1]=MODE, bit[2]=CURSOR_EN
- 0xC014 (0x4): FG_COLOR (RW) - Foreground color (3-bit RGB, 0-7)
- 0xC015 (0x5): BG_COLOR (RW) - Background color (3-bit RGB, 0-7)
- 0xC016 (0x6): STATUS (RO) - bit[0]=READY, bit[1]=VSYNC

Per TDD: This test is written BEFORE the RTL implementation
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# Register addresses (offsets from base 0xC010)
REG_CHAR_DATA = 0x0
REG_CURSOR_ROW = 0x1
REG_CURSOR_COL = 0x2
REG_CONTROL = 0x3
REG_FG_COLOR = 0x4
REG_BG_COLOR = 0x5
REG_STATUS = 0x6

# Control register bits
CTRL_CLEAR = 0x01
CTRL_MODE_80COL = 0x02
CTRL_CURSOR_EN = 0x04

# Screen dimensions
ROWS = 30
COLS_40 = 40
COLS_80 = 80


async def reset_dut(dut):
    """Reset the DUT and wait for it to stabilize"""
    dut.rst_n.value = 0
    dut.we.value = 0
    dut.re.value = 0
    dut.addr.value = 0
    dut.data_in.value = 0
    dut.gpu_ready.value = 1
    dut.vsync.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def write_register(dut, addr, data):
    """Write to a register"""
    dut.addr.value = addr
    dut.data_in.value = data
    dut.we.value = 1
    dut.re.value = 0
    await RisingEdge(dut.clk)
    dut.we.value = 0
    await RisingEdge(dut.clk)


async def read_register(dut, addr):
    """Read from a register"""
    dut.addr.value = addr
    dut.we.value = 0
    dut.re.value = 1
    await RisingEdge(dut.clk)
    value = int(dut.data_out.value)
    dut.re.value = 0
    await RisingEdge(dut.clk)
    return value


@cocotb.test()
async def test_reset_values(dut):
    """Test that all registers have correct reset values"""

    clock = Clock(dut.clk, 40, units="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    # Check reset values
    assert dut.cursor_row.value == 0, "Cursor row should reset to 0"
    assert dut.cursor_col.value == 0, "Cursor column should reset to 0"
    assert dut.mode_80col.value == 0, "Should reset to 40-column mode"
    assert dut.cursor_enable.value == 1, "Cursor should be enabled by default"
    assert dut.fg_color.value == 0x7, "Foreground should reset to white (0x7)"
    assert dut.bg_color.value == 0x0, "Background should reset to black (0x0)"
    assert dut.clear_screen.value == 0, "Clear screen should not be active"


@cocotb.test()
async def test_cursor_row_read_write(dut):
    """Test CURSOR_ROW register read/write functionality"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write various row values
    test_rows = [0, 10, 20, 29]

    for row in test_rows:
        await write_register(dut, REG_CURSOR_ROW, row)
        assert dut.cursor_row.value == row, f"Cursor row should be {row}"

        # Read back
        read_value = await read_register(dut, REG_CURSOR_ROW)
        assert read_value == row, f"Read value should match written value {row}"


@cocotb.test()
async def test_cursor_row_clamping(dut):
    """Test that cursor row values > 29 are clamped to 29"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write values above maximum
    test_values = [30, 31, 50, 0x1F]  # Max 5-bit value = 31

    for value in test_values:
        await write_register(dut, REG_CURSOR_ROW, value)
        assert dut.cursor_row.value <= 29, f"Row should be clamped to max 29 for input {value}"


@cocotb.test()
async def test_cursor_col_read_write(dut):
    """Test CURSOR_COL register read/write functionality"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Test in 40-column mode
    test_cols = [0, 10, 20, 39]

    for col in test_cols:
        await write_register(dut, REG_CURSOR_COL, col)
        assert dut.cursor_col.value == col, f"Cursor col should be {col}"

        # Read back
        read_value = await read_register(dut, REG_CURSOR_COL)
        assert read_value == col, f"Read value should match written value {col}"


@cocotb.test()
async def test_cursor_col_clamping_40col(dut):
    """Test cursor column clamping in 40-column mode"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Ensure 40-column mode (default)
    await write_register(dut, REG_CONTROL, CTRL_CURSOR_EN)

    # Write values above 40-column maximum
    test_values = [40, 50, 79, 0x7F]

    for value in test_values:
        await write_register(dut, REG_CURSOR_COL, value)
        assert dut.cursor_col.value <= 39, \
            f"Column should be clamped to max 39 in 40-col mode for input {value}"


@cocotb.test()
async def test_cursor_col_clamping_80col(dut):
    """Test cursor column clamping in 80-column mode"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Switch to 80-column mode
    await write_register(dut, REG_CONTROL, CTRL_MODE_80COL | CTRL_CURSOR_EN)

    # Write valid 80-column values
    await write_register(dut, REG_CURSOR_COL, 79)
    assert dut.cursor_col.value == 79, "Should accept column 79 in 80-col mode"

    # Write values above 80-column maximum
    await write_register(dut, REG_CURSOR_COL, 80)
    assert dut.cursor_col.value <= 79, "Column should be clamped to max 79 in 80-col mode"


@cocotb.test()
async def test_fg_color_read_write(dut):
    """Test FG_COLOR register read/write with 3-bit masking"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Test all 8 valid colors
    for color in range(8):
        await write_register(dut, REG_FG_COLOR, color)
        assert dut.fg_color.value == color, f"FG color should be {color}"

        read_value = await read_register(dut, REG_FG_COLOR)
        assert read_value == color, f"Read FG color should be {color}"


@cocotb.test()
async def test_fg_color_masking(dut):
    """Test that FG_COLOR masks upper 5 bits"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write value with upper bits set
    await write_register(dut, REG_FG_COLOR, 0xFF)
    assert dut.fg_color.value == 0x07, "Upper bits should be masked, result should be 0x07"

    # Write 0xA5 (upper bits set)
    await write_register(dut, REG_FG_COLOR, 0xA5)
    assert dut.fg_color.value == 0x05, "Should mask to lower 3 bits (0x05)"


@cocotb.test()
async def test_bg_color_read_write(dut):
    """Test BG_COLOR register read/write with 3-bit masking"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Test all 8 valid colors
    for color in range(8):
        await write_register(dut, REG_BG_COLOR, color)
        assert dut.bg_color.value == color, f"BG color should be {color}"

        read_value = await read_register(dut, REG_BG_COLOR)
        assert read_value == color, f"Read BG color should be {color}"


@cocotb.test()
async def test_bg_color_masking(dut):
    """Test that BG_COLOR masks upper 5 bits"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write value with upper bits set
    await write_register(dut, REG_BG_COLOR, 0xF8)
    assert dut.bg_color.value == 0x00, "Upper bits should be masked, result should be 0x00"


@cocotb.test()
async def test_control_clear_screen(dut):
    """Test CONTROL register clear screen bit"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write clear bit
    await write_register(dut, REG_CONTROL, CTRL_CLEAR | CTRL_CURSOR_EN)

    # Clear screen should pulse for one cycle
    assert dut.clear_screen.value == 1, "Clear screen should be asserted"

    # Wait a cycle, should be self-clearing
    await RisingEdge(dut.clk)
    assert dut.clear_screen.value == 0, "Clear screen should be self-clearing"


@cocotb.test()
async def test_control_mode_switch(dut):
    """Test CONTROL register mode bit (40-col vs 80-col)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Default should be 40-column mode
    assert dut.mode_80col.value == 0, "Should start in 40-column mode"

    # Switch to 80-column mode
    await write_register(dut, REG_CONTROL, CTRL_MODE_80COL | CTRL_CURSOR_EN)
    assert dut.mode_80col.value == 1, "Should switch to 80-column mode"

    # Mode switch should trigger screen clear
    assert dut.clear_screen.value == 1, "Mode switch should trigger clear"
    await RisingEdge(dut.clk)

    # Should also reset cursor to 0,0
    assert dut.cursor_row.value == 0, "Mode switch should reset cursor row"
    assert dut.cursor_col.value == 0, "Mode switch should reset cursor col"

    # Switch back to 40-column mode
    await write_register(dut, REG_CONTROL, CTRL_CURSOR_EN)
    assert dut.mode_80col.value == 0, "Should switch back to 40-column mode"


@cocotb.test()
async def test_control_cursor_enable(dut):
    """Test CONTROL register cursor enable bit"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Default should be cursor enabled
    assert dut.cursor_enable.value == 1, "Cursor should be enabled by default"

    # Disable cursor
    await write_register(dut, REG_CONTROL, 0x00)
    assert dut.cursor_enable.value == 0, "Cursor should be disabled"

    # Enable cursor
    await write_register(dut, REG_CONTROL, CTRL_CURSOR_EN)
    assert dut.cursor_enable.value == 1, "Cursor should be enabled"


@cocotb.test()
async def test_status_register_read_only(dut):
    """Test that STATUS register is read-only"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Set status inputs
    dut.gpu_ready.value = 1
    dut.vsync.value = 0
    await RisingEdge(dut.clk)

    # Read status
    status = await read_register(dut, REG_STATUS)
    assert (status & 0x01) == 1, "READY bit should be set"
    assert (status & 0x02) == 0, "VSYNC bit should be clear"

    # Try to write (should have no effect)
    await write_register(dut, REG_STATUS, 0xFF)

    # Read again, should be unchanged
    status = await read_register(dut, REG_STATUS)
    assert (status & 0x01) == 1, "READY bit should still be set"
    assert (status & 0x02) == 0, "VSYNC bit should still be clear"


@cocotb.test()
async def test_status_register_vsync(dut):
    """Test that STATUS register reflects VSYNC input"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Test VSYNC low
    dut.vsync.value = 0
    await RisingEdge(dut.clk)
    status = await read_register(dut, REG_STATUS)
    assert (status & 0x02) == 0, "VSYNC bit should be clear"

    # Test VSYNC high
    dut.vsync.value = 1
    await RisingEdge(dut.clk)
    status = await read_register(dut, REG_STATUS)
    assert (status & 0x02) == 0x02, "VSYNC bit should be set"


@cocotb.test()
async def test_status_register_ready(dut):
    """Test that STATUS register reflects READY input"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Test READY high
    dut.gpu_ready.value = 1
    await RisingEdge(dut.clk)
    status = await read_register(dut, REG_STATUS)
    assert (status & 0x01) == 1, "READY bit should be set"

    # Test READY low
    dut.gpu_ready.value = 0
    await RisingEdge(dut.clk)
    status = await read_register(dut, REG_STATUS)
    assert (status & 0x01) == 0, "READY bit should be clear"


@cocotb.test()
async def test_char_data_write(dut):
    """Test writing to CHAR_DATA register"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write a character
    await write_register(dut, REG_CHAR_DATA, 0x41)  # 'A'

    # Check character buffer interface
    assert dut.char_we.value == 1, "Character write enable should be asserted"
    assert dut.char_data.value == 0x41, "Character data should be 0x41"
    assert dut.char_addr.value == 0, "Character address should be 0 (row 0, col 0)"

    await RisingEdge(dut.clk)
    assert dut.char_we.value == 0, "Character write enable should be deasserted"


@cocotb.test()
async def test_char_data_cursor_advance(dut):
    """Test that writing CHAR_DATA auto-advances cursor"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Initial position should be 0,0
    assert dut.cursor_row.value == 0
    assert dut.cursor_col.value == 0

    # Write a character
    await write_register(dut, REG_CHAR_DATA, 0x48)  # 'H'

    # Cursor should advance to column 1
    assert dut.cursor_row.value == 0, "Row should remain 0"
    assert dut.cursor_col.value == 1, "Column should advance to 1"

    # Write another character
    await write_register(dut, REG_CHAR_DATA, 0x49)  # 'I'

    # Cursor should advance to column 2
    assert dut.cursor_row.value == 0, "Row should remain 0"
    assert dut.cursor_col.value == 2, "Column should advance to 2"


@cocotb.test()
async def test_char_data_line_wrap_40col(dut):
    """Test cursor line wrap at column 39 in 40-column mode"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Position cursor at end of first line (col 39)
    await write_register(dut, REG_CURSOR_COL, 39)
    assert dut.cursor_row.value == 0
    assert dut.cursor_col.value == 39

    # Write a character (should wrap to next line)
    await write_register(dut, REG_CHAR_DATA, 0x58)  # 'X'

    # Cursor should wrap to row 1, column 0
    assert dut.cursor_row.value == 1, "Row should advance to 1"
    assert dut.cursor_col.value == 0, "Column should wrap to 0"


@cocotb.test()
async def test_char_data_line_wrap_80col(dut):
    """Test cursor line wrap at column 79 in 80-column mode"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Switch to 80-column mode
    await write_register(dut, REG_CONTROL, CTRL_MODE_80COL | CTRL_CURSOR_EN)
    await RisingEdge(dut.clk)

    # Position cursor at end of first line (col 79)
    await write_register(dut, REG_CURSOR_COL, 79)
    assert dut.cursor_col.value == 79

    # Write a character (should wrap to next line)
    await write_register(dut, REG_CHAR_DATA, 0x59)  # 'Y'

    # Cursor should wrap to row 1, column 0
    assert dut.cursor_row.value == 1, "Row should advance to 1"
    assert dut.cursor_col.value == 0, "Column should wrap to 0"


@cocotb.test()
async def test_char_data_scroll_trigger(dut):
    """Test scroll trigger when writing at last row"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Position cursor at last row, last column
    await write_register(dut, REG_CURSOR_ROW, 29)
    await write_register(dut, REG_CURSOR_COL, 39)

    assert dut.cursor_row.value == 29
    assert dut.cursor_col.value == 39

    # Write a character (should trigger scroll)
    await write_register(dut, REG_CHAR_DATA, 0x5A)  # 'Z'

    # Cursor should stay at row 29, wrap to column 0
    # (scroll operation moves content up)
    assert dut.cursor_row.value == 29, "Cursor should stay at last row after scroll"
    assert dut.cursor_col.value == 0, "Column should wrap to 0"


@cocotb.test()
async def test_char_data_address_calculation_40col(dut):
    """Test character buffer address calculation in 40-column mode"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Test various positions
    test_cases = [
        (0, 0, 0),           # Row 0, Col 0 -> Addr 0
        (0, 1, 1),           # Row 0, Col 1 -> Addr 1
        (1, 0, 40),          # Row 1, Col 0 -> Addr 40
        (1, 5, 45),          # Row 1, Col 5 -> Addr 45
        (10, 20, 420),       # Row 10, Col 20 -> Addr 420
        (29, 39, 1199),      # Row 29, Col 39 -> Addr 1199 (last position)
    ]

    for row, col, expected_addr in test_cases:
        await write_register(dut, REG_CURSOR_ROW, row)
        await write_register(dut, REG_CURSOR_COL, col)
        await write_register(dut, REG_CHAR_DATA, 0x2A)  # '*'

        actual_addr = int(dut.char_addr.value)
        assert actual_addr == expected_addr, \
            f"Address for ({row},{col}) should be {expected_addr}, got {actual_addr}"


@cocotb.test()
async def test_char_data_address_calculation_80col(dut):
    """Test character buffer address calculation in 80-column mode"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Switch to 80-column mode
    await write_register(dut, REG_CONTROL, CTRL_MODE_80COL | CTRL_CURSOR_EN)
    await RisingEdge(dut.clk)

    # Test various positions (addr = row * 80 + col)
    test_cases = [
        (0, 0, 0),           # Row 0, Col 0 -> Addr 0
        (0, 1, 1),           # Row 0, Col 1 -> Addr 1
        (1, 0, 80),          # Row 1, Col 0 -> Addr 80
        (1, 5, 85),          # Row 1, Col 5 -> Addr 85
        (10, 40, 840),       # Row 10, Col 40 -> Addr 840
        (29, 79, 2399),      # Row 29, Col 79 -> Addr 2399 (last position)
    ]

    for row, col, expected_addr in test_cases:
        await write_register(dut, REG_CURSOR_ROW, row)
        await write_register(dut, REG_CURSOR_COL, col)
        await write_register(dut, REG_CHAR_DATA, 0x2B)  # '+'

        actual_addr = int(dut.char_addr.value)
        assert actual_addr == expected_addr, \
            f"Address for ({row},{col}) should be {expected_addr}, got {actual_addr}"


@cocotb.test()
async def test_multiple_character_writes(dut):
    """Test writing multiple characters sequentially"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write "HELLO"
    test_string = [0x48, 0x45, 0x4C, 0x4C, 0x4F]  # "HELLO"

    for i, char in enumerate(test_string):
        await write_register(dut, REG_CHAR_DATA, char)

        # Verify cursor position
        assert dut.cursor_col.value == (i + 1), \
            f"After writing char {i}, cursor should be at column {i + 1}"


@cocotb.test()
async def test_positioned_character_write(dut):
    """Test writing character at specific position"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Position cursor at row 10, column 20
    await write_register(dut, REG_CURSOR_ROW, 10)
    await write_register(dut, REG_CURSOR_COL, 20)

    # Write a character
    await write_register(dut, REG_CHAR_DATA, 0x40)  # '@'

    # Verify it was written to correct address (10 * 40 + 20 = 420)
    assert dut.char_addr.value == 420, "Character should be written to address 420"

    # Cursor should have advanced
    assert dut.cursor_row.value == 10, "Row should remain 10"
    assert dut.cursor_col.value == 21, "Column should advance to 21"


@cocotb.test()
async def test_control_write_only(dut):
    """Test that CONTROL register is write-only (reads return undefined)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write to control register
    await write_register(dut, REG_CONTROL, CTRL_MODE_80COL | CTRL_CURSOR_EN)

    # The actual control outputs should reflect the write
    assert dut.mode_80col.value == 1, "Mode should be 80-column"
    assert dut.cursor_enable.value == 1, "Cursor should be enabled"

    # Reading CONTROL register is undefined (implementation-dependent)
    # Just verify read doesn't crash
    await read_register(dut, REG_CONTROL)


@cocotb.test()
async def test_char_data_write_only(dut):
    """Test that CHAR_DATA register is write-only"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write character
    await write_register(dut, REG_CHAR_DATA, 0x41)

    # Reading CHAR_DATA is undefined (implementation-dependent)
    # Just verify read doesn't crash
    await read_register(dut, REG_CHAR_DATA)


@cocotb.test()
async def test_reserved_registers(dut):
    """Test that reserved register addresses don't cause issues"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Try accessing reserved addresses (0x7-0xF)
    for addr in range(0x7, 0x10):
        # Write should not crash
        await write_register(dut, addr, 0x55)

        # Read should not crash
        await read_register(dut, addr)

        # Core functionality should still work
        assert dut.cursor_row.value == 0, "Reserved access shouldn't affect cursor_row"
        assert dut.cursor_col.value == 0, "Reserved access shouldn't affect cursor_col"


@cocotb.test()
async def test_simultaneous_read_write_protection(dut):
    """Test that simultaneous read/write is handled correctly"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Try to assert both we and re simultaneously (should not happen in normal operation)
    dut.addr.value = REG_FG_COLOR
    dut.data_in.value = 0x05
    dut.we.value = 1
    dut.re.value = 1
    await RisingEdge(dut.clk)

    # Implementation should prioritize one or ignore the operation
    # (Either behavior is acceptable as this is an invalid state)
    # Just verify it doesn't crash
    dut.we.value = 0
    dut.re.value = 0
    await RisingEdge(dut.clk)


# cocotb test configuration
def test_runner():
    """pytest entry point for running cocotb tests"""
    import os
    from pathlib import Path

    # Get project root
    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    # RTL source
    verilog_sources = [
        rtl_dir / "peripherals" / "video" / "gpu_registers.v"
    ]

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="gpu_registers",
        module="test_gpu_registers",
        simulator=simulator,
        waves=True if os.getenv("WAVES") == "1" else False,
    )


if __name__ == "__main__":
    test_runner()
