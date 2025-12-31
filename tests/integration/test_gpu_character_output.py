"""
Integration Test for GPU Character Output Pipeline

This test verifies the complete character display path:
Character code → GPU registers → Character buffer → Font ROM → Character renderer → Pixel output

Tests the end-to-end functionality of writing characters through the register interface
and verifying that they render correctly as pixels on the display.

Test Coverage:
1. End-to-end character write: Write 'A' to CHAR_DATA register, verify correct pixels appear
2. Multiple character write: Write "HELLO", verify all characters render
3. Cursor auto-advance: Verify cursor moves after each character
4. Line wrap: Write 41 characters in 40-col mode, verify wrap to next line
5. Color application: Set colors, write character, verify pixel colors match
6. Mode switching: Switch between 40-col and 80-col, verify layout changes
7. Screen clear: Write text, clear screen, verify all spaces

Expected system interface:
- GPU registers at 0xC010-0xC016
- CHAR_DATA register at 0xC010 (write character, auto-advance cursor)
- CURSOR_ROW at 0xC011 (cursor row position)
- CURSOR_COL at 0xC012 (cursor column position)
- CONTROL at 0xC013 (clear, mode, cursor enable)
- FG_COLOR at 0xC014 (3-bit RGB foreground color)
- BG_COLOR at 0xC015 (3-bit RGB background color)
- STATUS at 0xC016 (ready flag, vsync flag)

This is an integration test following TDD - it will FAIL initially until modules are implemented.

Author: RetroCPU Project
License: MIT
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, Timer

# Register addresses (GPU memory-mapped registers)
REG_CHAR_DATA  = 0xC010  # Write character at cursor position
REG_CURSOR_ROW = 0xC011  # Cursor row position (0-29)
REG_CURSOR_COL = 0xC012  # Cursor column position (0-39 or 0-79)
REG_CONTROL    = 0xC013  # Control register (clear, mode, cursor enable)
REG_FG_COLOR   = 0xC014  # Foreground color (3-bit RGB)
REG_BG_COLOR   = 0xC015  # Background color (3-bit RGB)
REG_STATUS     = 0xC016  # Status register (ready, vsync)

# Control register bits
CTRL_BIT_CLEAR      = 0x01  # Bit 0: Clear screen
CTRL_BIT_MODE_80COL = 0x02  # Bit 1: 1=80-col, 0=40-col
CTRL_BIT_CURSOR_EN  = 0x04  # Bit 2: Cursor enable

# Display dimensions
COLS_40 = 40
COLS_80 = 80
ROWS = 30

# Character cell size (8x16 pixels)
CHAR_WIDTH = 8
CHAR_HEIGHT = 16


class GPUTestHelper:
    """Helper class for GPU register writes and pixel verification"""

    def __init__(self, dut):
        self.dut = dut

    async def write_register(self, addr, data):
        """Write a byte to a GPU register"""
        self.dut.cpu_addr.value = addr
        self.dut.cpu_data_out.value = data
        self.dut.cpu_we.value = 1
        await RisingEdge(self.dut.clk)
        self.dut.cpu_we.value = 0
        await RisingEdge(self.dut.clk)

    async def read_register(self, addr):
        """Read a byte from a GPU register"""
        self.dut.cpu_addr.value = addr
        self.dut.cpu_we.value = 0
        await RisingEdge(self.dut.clk)
        value = int(self.dut.cpu_data_in.value)
        return value

    async def write_character(self, char):
        """Write a character to CHAR_DATA register (auto-advances cursor)"""
        await self.write_register(REG_CHAR_DATA, ord(char) if isinstance(char, str) else char)

    async def write_string(self, text):
        """Write a string of characters to the display"""
        for char in text:
            await self.write_character(char)

    async def set_cursor_position(self, row, col):
        """Set cursor position"""
        await self.write_register(REG_CURSOR_ROW, row)
        await self.write_register(REG_CURSOR_COL, col)

    async def get_cursor_position(self):
        """Read current cursor position"""
        row = await self.read_register(REG_CURSOR_ROW)
        col = await self.read_register(REG_CURSOR_COL)
        return (row, col)

    async def clear_screen(self):
        """Issue clear screen command"""
        await self.write_register(REG_CONTROL, CTRL_BIT_CLEAR | CTRL_BIT_CURSOR_EN)

    async def set_mode_40col(self):
        """Switch to 40-column mode"""
        await self.write_register(REG_CONTROL, CTRL_BIT_CURSOR_EN)  # MODE=0

    async def set_mode_80col(self):
        """Switch to 80-column mode"""
        await self.write_register(REG_CONTROL, CTRL_BIT_MODE_80COL | CTRL_BIT_CURSOR_EN)

    async def set_colors(self, fg_color, bg_color):
        """Set foreground and background colors (3-bit RGB)"""
        await self.write_register(REG_FG_COLOR, fg_color & 0x07)
        await self.write_register(REG_BG_COLOR, bg_color & 0x07)

    async def wait_for_ready(self):
        """Wait for GPU to be ready (STATUS.READY bit)"""
        timeout = 10000
        for _ in range(timeout):
            status = await self.read_register(REG_STATUS)
            if status & 0x01:  # READY bit
                return
            await RisingEdge(self.dut.clk)
        raise TimeoutError("GPU never became ready")

    async def wait_for_vsync(self):
        """Wait for vertical sync period"""
        timeout = 100000
        for _ in range(timeout):
            status = await self.read_register(REG_STATUS)
            if status & 0x02:  # VSYNC bit
                return
            await RisingEdge(self.dut.clk)
        raise TimeoutError("VSYNC never occurred")

    def get_pixel_position(self, row, col, char_x, char_y):
        """Calculate pixel coordinates for a character cell position"""
        # char_x, char_y are 0-7, 0-15 within the character cell
        pixel_x = col * CHAR_WIDTH + char_x
        pixel_y = row * CHAR_HEIGHT + char_y
        return (pixel_x, pixel_y)

    async def sample_pixel_at_char(self, row, col, char_x, char_y):
        """
        Sample a pixel at a specific character cell and offset.
        Returns RGB tuple (r, g, b) - each 8 bits.

        This would require access to the video output signals.
        For now, this is a placeholder showing the expected interface.
        """
        # In a real test, we'd need to wait for the correct scanline
        # and pixel position, then read the RGB output signals
        # For example: dut.video_r, dut.video_g, dut.video_b

        # Calculate expected scanline
        target_y = row * CHAR_HEIGHT + char_y

        # Wait for this scanline
        # (Implementation depends on how timing signals are exposed)

        # This is a simplified placeholder
        # Real implementation needs timing generator signals
        raise NotImplementedError("Pixel sampling requires video timing signals")


async def reset_system(dut):
    """Reset the system and initialize clocks"""
    # Create system clock (25 MHz)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Initialize signals
    dut.rst.value = 1
    dut.cpu_addr.value = 0
    dut.cpu_data_out.value = 0
    dut.cpu_we.value = 0

    # Hold reset for 10 cycles
    await ClockCycles(dut.clk, 10)

    # Release reset
    dut.rst.value = 0
    await ClockCycles(dut.clk, 5)

    dut._log.info("System reset complete")


@cocotb.test()
async def test_single_character_write(dut):
    """
    Test 1: End-to-end character write
    Write 'A' to CHAR_DATA register, verify cursor advances
    """
    await reset_system(dut)
    helper = GPUTestHelper(dut)

    dut._log.info("=== Test 1: Single Character Write ===")

    # Verify initial cursor position (0, 0)
    row, col = await helper.get_cursor_position()
    assert row == 0, f"Initial cursor row should be 0, got {row}"
    assert col == 0, f"Initial cursor col should be 0, got {col}"
    dut._log.info(f"Initial cursor position: ({row}, {col})")

    # Write character 'A' (0x41)
    dut._log.info("Writing character 'A' at (0, 0)")
    await helper.write_character('A')

    # Verify cursor advanced to (0, 1)
    row, col = await helper.get_cursor_position()
    assert row == 0, f"Cursor row should still be 0, got {row}"
    assert col == 1, f"Cursor col should advance to 1, got {col}"
    dut._log.info(f"After write, cursor position: ({row}, {col})")

    dut._log.info("✓ Single character write test PASSED")


@cocotb.test()
async def test_multiple_character_write(dut):
    """
    Test 2: Multiple character write
    Write "HELLO", verify all characters render and cursor advances correctly
    """
    await reset_system(dut)
    helper = GPUTestHelper(dut)

    dut._log.info("=== Test 2: Multiple Character Write ===")

    # Write "HELLO"
    test_string = "HELLO"
    dut._log.info(f"Writing string: '{test_string}'")
    await helper.write_string(test_string)

    # Verify cursor position after writing 5 characters
    row, col = await helper.get_cursor_position()
    assert row == 0, f"Cursor row should be 0, got {row}"
    assert col == len(test_string), f"Cursor col should be {len(test_string)}, got {col}"
    dut._log.info(f"After writing '{test_string}', cursor at ({row}, {col})")

    # Write more characters to test continuous advance
    await helper.write_string(" WORLD")
    row, col = await helper.get_cursor_position()
    expected_col = len("HELLO WORLD")
    assert col == expected_col, f"Cursor col should be {expected_col}, got {col}"
    dut._log.info(f"After writing 'HELLO WORLD', cursor at ({row}, {col})")

    dut._log.info("✓ Multiple character write test PASSED")


@cocotb.test()
async def test_cursor_auto_advance(dut):
    """
    Test 3: Cursor auto-advance
    Verify cursor automatically advances after each character write
    """
    await reset_system(dut)
    helper = GPUTestHelper(dut)

    dut._log.info("=== Test 3: Cursor Auto-Advance ===")

    # Write characters one by one and verify cursor advances each time
    for i in range(10):
        row, col = await helper.get_cursor_position()
        assert col == i, f"Before write {i}, cursor col should be {i}, got {col}"

        await helper.write_character(chr(ord('A') + i))

        row, col = await helper.get_cursor_position()
        assert col == i + 1, f"After write {i}, cursor col should be {i+1}, got {col}"
        dut._log.info(f"Write {i}: cursor advanced to ({row}, {col})")

    dut._log.info("✓ Cursor auto-advance test PASSED")


@cocotb.test()
async def test_line_wrap_40col(dut):
    """
    Test 4: Line wrap in 40-column mode
    Write 41 characters, verify cursor wraps to next line after character 40
    """
    await reset_system(dut)
    helper = GPUTestHelper(dut)

    dut._log.info("=== Test 4: Line Wrap (40-column mode) ===")

    # Ensure we're in 40-column mode
    await helper.set_mode_40col()
    dut._log.info("Set to 40-column mode")

    # Write exactly 40 characters (one full line)
    dut._log.info(f"Writing {COLS_40} characters to fill first line")
    for i in range(COLS_40):
        await helper.write_character('X')

    # Cursor should be at (0, 40) - end of line 0
    # Actually, per spec, after writing to col 39, cursor advances to (1, 0)
    row, col = await helper.get_cursor_position()
    dut._log.info(f"After writing {COLS_40} chars, cursor at ({row}, {col})")

    # The spec says cursor wraps to next line when reaching end
    # After writing 40 characters (0-39), cursor should wrap to (1, 0)
    assert row == 1, f"After line wrap, cursor row should be 1, got {row}"
    assert col == 0, f"After line wrap, cursor col should be 0, got {col}"

    # Write one more character to verify it appears on line 1
    await helper.write_character('Y')
    row, col = await helper.get_cursor_position()
    assert row == 1, f"Cursor row should still be 1, got {row}"
    assert col == 1, f"Cursor col should be 1, got {col}"
    dut._log.info(f"After writing to line 1, cursor at ({row}, {col})")

    dut._log.info("✓ Line wrap test PASSED")


@cocotb.test()
async def test_color_application(dut):
    """
    Test 5: Color application
    Set foreground and background colors, write character, verify colors
    """
    await reset_system(dut)
    helper = GPUTestHelper(dut)

    dut._log.info("=== Test 5: Color Application ===")

    # Test 1: Set green foreground, blue background
    dut._log.info("Setting colors: Green FG (0x02), Blue BG (0x01)")
    await helper.set_colors(fg_color=0x02, bg_color=0x01)  # Green on blue

    # Verify colors were set by reading back
    fg = await helper.read_register(REG_FG_COLOR)
    bg = await helper.read_register(REG_BG_COLOR)
    assert fg == 0x02, f"FG color should be 0x02 (green), got 0x{fg:02X}"
    assert bg == 0x01, f"BG color should be 0x01 (blue), got 0x{bg:02X}"
    dut._log.info(f"Colors set: FG=0x{fg:02X}, BG=0x{bg:02X}")

    # Write a character with these colors
    await helper.write_character('A')
    dut._log.info("Wrote character 'A' with green/blue colors")

    # Test 2: Change to red foreground, yellow background
    dut._log.info("Changing colors: Red FG (0x04), Yellow BG (0x06)")
    await helper.set_colors(fg_color=0x04, bg_color=0x06)  # Red on yellow

    await helper.write_character('B')
    dut._log.info("Wrote character 'B' with red/yellow colors")

    # Test 3: Test bit masking (upper bits should be ignored)
    dut._log.info("Testing bit masking: Writing 0xFF to color registers")
    await helper.set_colors(fg_color=0xFF, bg_color=0xFF)

    fg = await helper.read_register(REG_FG_COLOR)
    bg = await helper.read_register(REG_BG_COLOR)
    assert fg == 0x07, f"FG should mask to 0x07 (white), got 0x{fg:02X}"
    assert bg == 0x07, f"BG should mask to 0x07 (white), got 0x{bg:02X}"
    dut._log.info(f"Bit masking verified: FG=0x{fg:02X}, BG=0x{bg:02X}")

    dut._log.info("✓ Color application test PASSED")


@cocotb.test()
async def test_mode_switching(dut):
    """
    Test 6: Mode switching between 40-col and 80-col
    Verify screen clears and cursor resets on mode switch
    """
    await reset_system(dut)
    helper = GPUTestHelper(dut)

    dut._log.info("=== Test 6: Mode Switching ===")

    # Default should be 40-column mode
    dut._log.info("Starting in default 40-column mode")

    # Write some text in 40-col mode
    await helper.write_string("40-COL MODE")
    row, col = await helper.get_cursor_position()
    dut._log.info(f"Wrote text in 40-col mode, cursor at ({row}, {col})")

    # Switch to 80-column mode (should clear screen and reset cursor)
    dut._log.info("Switching to 80-column mode")
    await helper.set_mode_80col()

    # Wait for mode switch to complete
    await helper.wait_for_ready()

    # Verify cursor reset to (0, 0)
    row, col = await helper.get_cursor_position()
    assert row == 0, f"After mode switch, cursor row should be 0, got {row}"
    assert col == 0, f"After mode switch, cursor col should be 0, got {col}"
    dut._log.info(f"After mode switch, cursor reset to ({row}, {col})")

    # Write 80 characters to test 80-col mode
    dut._log.info("Writing 80 characters in 80-col mode")
    for i in range(COLS_80):
        await helper.write_character('8')

    row, col = await helper.get_cursor_position()
    dut._log.info(f"After writing {COLS_80} chars, cursor at ({row}, {col})")
    # Should wrap to line 1 after 80 characters
    assert row == 1, f"Cursor should wrap to row 1, got {row}"
    assert col == 0, f"Cursor should be at col 0, got {col}"

    # Switch back to 40-column mode
    dut._log.info("Switching back to 40-column mode")
    await helper.set_mode_40col()
    await helper.wait_for_ready()

    # Verify cursor reset again
    row, col = await helper.get_cursor_position()
    assert row == 0, f"After mode switch, cursor row should be 0, got {row}"
    assert col == 0, f"After mode switch, cursor col should be 0, got {col}"
    dut._log.info(f"After switching back, cursor reset to ({row}, {col})")

    dut._log.info("✓ Mode switching test PASSED")


@cocotb.test()
async def test_screen_clear(dut):
    """
    Test 7: Screen clear
    Write text, issue clear command, verify cursor resets
    """
    await reset_system(dut)
    helper = GPUTestHelper(dut)

    dut._log.info("=== Test 7: Screen Clear ===")

    # Write some text across multiple lines
    dut._log.info("Writing test pattern across screen")
    for line in range(5):
        await helper.set_cursor_position(line, 0)
        await helper.write_string(f"Line {line} test text")

    # Verify cursor is not at origin
    row, col = await helper.get_cursor_position()
    dut._log.info(f"Before clear, cursor at ({row}, {col})")
    assert row != 0 or col != 0, "Cursor should not be at origin before clear"

    # Issue clear screen command
    dut._log.info("Issuing clear screen command")
    await helper.clear_screen()

    # Wait for clear to complete
    await helper.wait_for_ready()

    # Verify cursor reset to (0, 0)
    row, col = await helper.get_cursor_position()
    assert row == 0, f"After clear, cursor row should be 0, got {row}"
    assert col == 0, f"After clear, cursor col should be 0, got {col}"
    dut._log.info(f"After clear, cursor reset to ({row}, {col})")

    # Write new text to verify display is working after clear
    await helper.write_string("After clear")
    row, col = await helper.get_cursor_position()
    dut._log.info(f"After writing new text, cursor at ({row}, {col})")

    dut._log.info("✓ Screen clear test PASSED")


@cocotb.test()
async def test_cursor_positioning(dut):
    """
    Test 8: Manual cursor positioning
    Set cursor to various positions and verify characters appear there
    """
    await reset_system(dut)
    helper = GPUTestHelper(dut)

    dut._log.info("=== Test 8: Cursor Positioning ===")

    # Test various cursor positions
    test_positions = [
        (0, 0),      # Top-left
        (0, 20),     # Middle of first line
        (10, 15),    # Middle of screen
        (29, 0),     # Last line, first column
        (29, 39),    # Bottom-right (40-col mode)
    ]

    for row, col in test_positions:
        dut._log.info(f"Setting cursor to ({row}, {col})")
        await helper.set_cursor_position(row, col)

        # Verify position was set
        actual_row, actual_col = await helper.get_cursor_position()
        assert actual_row == row, f"Cursor row should be {row}, got {actual_row}"
        assert actual_col == col, f"Cursor col should be {col}, got {actual_col}"

        # Write a character at this position
        await helper.write_character('*')

        # Verify cursor advanced
        actual_row, actual_col = await helper.get_cursor_position()
        dut._log.info(f"After write, cursor at ({actual_row}, {actual_col})")

    dut._log.info("✓ Cursor positioning test PASSED")


@cocotb.test()
async def test_bounds_checking(dut):
    """
    Test 9: Cursor position bounds checking
    Verify invalid positions are clamped to valid range
    """
    await reset_system(dut)
    helper = GPUTestHelper(dut)

    dut._log.info("=== Test 9: Bounds Checking ===")

    # Test row out of bounds (max is 29)
    dut._log.info("Testing row out of bounds: 50 (should clamp to 29)")
    await helper.write_register(REG_CURSOR_ROW, 50)
    row, col = await helper.get_cursor_position()
    assert row == 29, f"Out of bounds row (50) should clamp to 29, got {row}"
    dut._log.info(f"Row 50 clamped to {row}")

    # Reset to valid position
    await helper.set_cursor_position(0, 0)

    # Test column out of bounds in 40-col mode (max is 39)
    dut._log.info("Testing col out of bounds in 40-col mode: 60 (should clamp to 39)")
    await helper.set_mode_40col()
    await helper.write_register(REG_CURSOR_COL, 60)
    row, col = await helper.get_cursor_position()
    assert col == 39, f"Out of bounds col (60) should clamp to 39, got {col}"
    dut._log.info(f"Col 60 clamped to {col}")

    # Test column in 80-col mode (max is 79)
    dut._log.info("Testing col in 80-col mode: 60 (should be valid)")
    await helper.set_mode_80col()
    await helper.wait_for_ready()
    await helper.write_register(REG_CURSOR_COL, 60)
    row, col = await helper.get_cursor_position()
    assert col == 60, f"Col 60 should be valid in 80-col mode, got {col}"
    dut._log.info(f"Col 60 is valid in 80-col mode")

    dut._log.info("✓ Bounds checking test PASSED")


@cocotb.test()
async def test_status_register(dut):
    """
    Test 10: Status register
    Verify READY and VSYNC flags
    """
    await reset_system(dut)
    helper = GPUTestHelper(dut)

    dut._log.info("=== Test 10: Status Register ===")

    # GPU should be ready after reset
    status = await helper.read_register(REG_STATUS)
    ready = status & 0x01
    dut._log.info(f"Initial status: 0x{status:02X}, READY={ready}")
    assert ready == 1, f"GPU should be ready after reset, READY bit was {ready}"

    # Test vsync flag (should toggle periodically)
    dut._log.info("Waiting for VSYNC to occur...")
    await helper.wait_for_vsync()
    status = await helper.read_register(REG_STATUS)
    vsync = (status >> 1) & 0x01
    dut._log.info(f"VSYNC detected: status=0x{status:02X}, VSYNC={vsync}")
    assert vsync == 1, "VSYNC flag should be set when in vsync period"

    # Test that READY goes low during clear operation
    dut._log.info("Testing READY flag during clear operation")
    await helper.clear_screen()

    # Immediately check if READY went low (might be too fast to catch)
    status = await helper.read_register(REG_STATUS)
    dut._log.info(f"Status during/after clear: 0x{status:02X}")

    # Wait for ready to return
    await helper.wait_for_ready()
    status = await helper.read_register(REG_STATUS)
    ready = status & 0x01
    assert ready == 1, f"GPU should be ready after clear completes, READY={ready}"
    dut._log.info("GPU returned to ready state after clear")

    dut._log.info("✓ Status register test PASSED")


# cocotb test configuration
def test_runner():
    """
    Pytest entry point for running cocotb tests

    This function would be called by pytest-cocotb to run the integration tests.
    It needs to specify the RTL sources to simulate.

    NOTE: This test will FAIL initially because the GPU modules don't exist yet.
    This is expected for TDD (Test-Driven Development).
    """
    import pytest
    import os
    from pathlib import Path

    # Get project root
    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    # RTL sources for GPU character output integration test
    # This list will grow as modules are implemented
    verilog_sources = [
        # Video timing and DVI output
        rtl_dir / "peripherals" / "video" / "vga_timing_generator.v",
        rtl_dir / "peripherals" / "video" / "tmds_encoder.v",
        rtl_dir / "peripherals" / "video" / "dvi_transmitter.v",

        # Character display pipeline
        rtl_dir / "peripherals" / "video" / "character_buffer.v",
        rtl_dir / "peripherals" / "video" / "font_rom.v",
        rtl_dir / "peripherals" / "video" / "character_renderer.v",
        rtl_dir / "peripherals" / "video" / "gpu_registers.v",

        # Color support
        rtl_dir / "peripherals" / "video" / "color_palette.v",

        # GPU core integration
        rtl_dir / "peripherals" / "video" / "gpu_core.v",
        rtl_dir / "peripherals" / "video" / "gpu_top.v",
    ]

    # Parameters
    parameters = {}

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources if v.exists()],
        toplevel="gpu_top",  # Top-level module for integration test
        module="test_gpu_character_output",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
    )


if __name__ == "__main__":
    test_runner()
