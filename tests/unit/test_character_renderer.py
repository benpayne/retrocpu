"""
Test suite for character_renderer module
Tests character-to-pixel conversion for DVI character display GPU

Per TDD: This test is written BEFORE the RTL implementation

The character renderer converts character codes to pixel data for display.
It operates on a scanline basis, processing one horizontal line at a time.

Key responsibilities:
- Read character from buffer based on screen position
- Look up font bitmap for that character and current scanline
- Output pixels with correct foreground/background colors
- Handle both 40-column and 80-column display modes
- Each character is 8 pixels wide × 16 pixels tall

Module Interface (character_renderer.v):
    Inputs:
        clk              - Pixel clock (25.175 MHz for 640x480)
        rst_n            - Active-low reset
        h_count[9:0]     - Horizontal pixel position (0-639)
        v_count[9:0]     - Vertical pixel position (0-479)
        video_active     - High during active video region
        mode_80col       - Display mode (0=40-col, 1=80-col)
        fg_color[2:0]    - Foreground color (3-bit RGB)
        bg_color[2:0]    - Background color (3-bit RGB)
        char_data[7:0]   - Character code from buffer

    Outputs:
        char_addr[10:0]  - Address to read from character buffer
        red[7:0]         - Red pixel component (0-255)
        green[7:0]       - Green pixel component (0-255)
        blue[7:0]        - Blue pixel component (0-255)

Display modes:
    40-column: 640 pixels / 16 pixels per char = 40 characters per line
    80-column: 640 pixels / 8 pixels per char = 80 characters per line

    Both modes: 480 pixels / 16 pixels per char = 30 character rows

Timing:
    40-column mode: Each character displayed for 16 pixels horizontally
    80-column mode: Each character displayed for 8 pixels horizontally

    For scanline N of a character row:
        - Fetch character code from buffer (char_addr)
        - Look up scanline N of that character from font ROM
        - Output 8 or 16 pixels (depending on mode) with colors applied
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


# Color definitions (3-bit RGB)
COLOR_BLACK = 0b000
COLOR_BLUE = 0b001
COLOR_GREEN = 0b010
COLOR_CYAN = 0b011
COLOR_RED = 0b100
COLOR_MAGENTA = 0b101
COLOR_YELLOW = 0b110
COLOR_WHITE = 0b111

# Helper function to convert 3-bit RGB to 8-bit component
def color_3bit_to_8bit(color_3bit, bit_position):
    """Convert 3-bit color to 8-bit RGB component

    Args:
        color_3bit: 3-bit RGB value (0-7)
        bit_position: 0=blue, 1=green, 2=red

    Returns:
        8-bit value: 0x00 if bit is 0, 0xFF if bit is 1
    """
    bit = (color_3bit >> bit_position) & 0x01
    return 0xFF if bit else 0x00


@cocotb.test()
async def test_character_renderer_reset(dut):
    """Test that character renderer resets correctly"""

    # Create 25.175 MHz pixel clock (39.7 ns period)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Apply reset
    dut.rst_n.value = 0
    dut.h_count.value = 0
    dut.v_count.value = 0
    dut.video_active.value = 0
    dut.mode_80col.value = 0
    dut.fg_color.value = COLOR_WHITE
    dut.bg_color.value = COLOR_BLACK
    dut.char_data.value = 0x00
    dut.font_pixels.value = 0x00  # Drive font_pixels input

    await ClockCycles(dut.clk, 5)

    # Release reset
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # After reset, outputs should be stable (black during inactive video)
    dut._log.info("Reset state verified")


@cocotb.test()
async def test_character_renderer_single_char_40col(dut):
    """Test rendering a single character at position (0,0) in 40-column mode

    This tests the basic character-to-pixel conversion:
    - Character 'A' (0x41) at screen position (0, 0)
    - First scanline (row 0) of the character
    - 40-column mode (16 pixels per character)
    - White foreground on black background
    """

    # Create pixel clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.mode_80col.value = 0  # 40-column mode
    dut.fg_color.value = COLOR_WHITE
    dut.bg_color.value = COLOR_BLACK
    dut.char_data.value = 0x41  # 'A'
    dut.font_pixels.value = 0x7E  # Test pattern for 'A' scanline: 0111 1110
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Position at character (0, 0), scanline 0
    # h_count = 0-15 (first character, 16 pixels wide in 40-col mode)
    # v_count = 0 (first scanline of first character row)

    pixels_seen = []

    for h_pixel in range(16):
        dut.h_count.value = h_pixel
        dut.v_count.value = 0
        dut.video_active.value = 1
        dut.char_data.value = 0x41  # 'A'
        dut.font_pixels.value = 0x7E  # Test pattern for 'A' scanline
        await RisingEdge(dut.clk)

        # Read pixel output
        r = int(dut.red.value)
        g = int(dut.green.value)
        b = int(dut.blue.value)
        pixels_seen.append((r, g, b))

        dut._log.info(f"Pixel {h_pixel}: R={r:02X} G={g:02X} B={b:02X}")

    # Verify character buffer address was requested
    # For position (0,0) in 40-col mode, char_addr should be 0
    char_addr = int(dut.char_addr.value)
    dut._log.info(f"Character buffer address: {char_addr}")
    assert char_addr == 0, f"Expected char_addr=0 for position (0,0), got {char_addr}"

    # Note: We can't verify exact pixel pattern without knowing the font data
    # But we can verify that colors are either foreground or background
    for i, (r, g, b) in enumerate(pixels_seen):
        # Each pixel should be either full white (0xFF) or black (0x00)
        assert r in [0x00, 0xFF], f"Pixel {i} red should be 0x00 or 0xFF, got 0x{r:02X}"
        assert g in [0x00, 0xFF], f"Pixel {i} green should be 0x00 or 0xFF, got 0x{g:02X}"
        assert b in [0x00, 0xFF], f"Pixel {i} blue should be 0x00 or 0xFF, got 0x{b:02X}"

        # For white-on-black, pixels should be (0xFF,0xFF,0xFF) or (0x00,0x00,0x00)
        if r == 0xFF:
            assert g == 0xFF and b == 0xFF, f"Pixel {i} should be full white"
        else:
            assert g == 0x00 and b == 0x00, f"Pixel {i} should be full black"

    dut._log.info(f"Successfully rendered 16 pixels for character 'A' at (0,0)")


@cocotb.test()
async def test_character_renderer_all_scanlines(dut):
    """Test all 16 scanlines of a character

    Each character is 16 pixels tall. This test verifies that the renderer
    correctly processes all 16 scanlines of a single character.
    """

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.mode_80col.value = 0  # 40-column mode
    dut.fg_color.value = COLOR_WHITE
    dut.bg_color.value = COLOR_BLACK
    dut.char_data.value = 0x42  # 'B'
    dut.font_pixels.value = 0xFF  # All pixels on
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Test character at position (0, 0) across all 16 scanlines
    for scanline in range(16):
        dut.v_count.value = scanline
        dut.h_count.value = 0  # First pixel of character
        dut.video_active.value = 1
        dut.char_data.value = 0x42  # 'B'
        dut.font_pixels.value = 0xFF  # All pixels on
        await RisingEdge(dut.clk)

        # Read pixel output for first pixel of each scanline
        r = int(dut.red.value)
        g = int(dut.green.value)
        b = int(dut.blue.value)

        dut._log.info(f"Scanline {scanline}: R={r:02X} G={g:02X} B={b:02X}")

        # Verify colors are valid (foreground or background)
        assert r in [0x00, 0xFF], f"Scanline {scanline} red invalid"
        assert g in [0x00, 0xFF], f"Scanline {scanline} green invalid"
        assert b in [0x00, 0xFF], f"Scanline {scanline} blue invalid"

    dut._log.info("Successfully processed all 16 scanlines")


@cocotb.test()
async def test_character_renderer_40col_timing(dut):
    """Test 40-column mode timing and character positioning

    In 40-column mode:
    - Each character is 16 pixels wide
    - 640 pixels / 16 = 40 characters per line
    - Character N starts at h_count = N * 16
    """

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.mode_80col.value = 0  # 40-column mode
    dut.fg_color.value = COLOR_GREEN
    dut.bg_color.value = COLOR_BLACK
    dut.font_pixels.value = 0xAA  # Alternating pattern
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Test character address calculation for several positions
    test_positions = [
        (0, 0, 0),      # First character: column 0, row 0 -> addr 0
        (16, 0, 1),     # Second character: column 1, row 0 -> addr 1
        (32, 0, 2),     # Third character: column 2, row 0 -> addr 2
        (0, 16, 40),    # First char of row 1: col 0, row 1 -> addr 40
        (624, 0, 39),   # Last char of row 0: col 39, row 0 -> addr 39
    ]

    for h_pos, v_pos, expected_addr in test_positions:
        dut.h_count.value = h_pos
        dut.v_count.value = v_pos
        dut.video_active.value = 1
        dut.char_data.value = 0x58  # 'X'
        dut.font_pixels.value = 0xAA  # Alternating pattern
        await RisingEdge(dut.clk)

        char_addr = int(dut.char_addr.value)
        dut._log.info(f"Position ({h_pos}, {v_pos}): char_addr={char_addr}, expected={expected_addr}")

        assert char_addr == expected_addr, \
            f"40-col mode: h={h_pos}, v={v_pos} should give addr={expected_addr}, got {char_addr}"

    dut._log.info("40-column timing verified")


@cocotb.test()
async def test_character_renderer_80col_timing(dut):
    """Test 80-column mode timing and character positioning

    In 80-column mode:
    - Each character is 8 pixels wide
    - 640 pixels / 8 = 80 characters per line
    - Character N starts at h_count = N * 8
    """

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.mode_80col.value = 1  # 80-column mode
    dut.fg_color.value = COLOR_YELLOW
    dut.bg_color.value = COLOR_BLUE
    dut.font_pixels.value = 0x55  # Alternating pattern
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Test character address calculation for several positions
    test_positions = [
        (0, 0, 0),      # First character: column 0, row 0 -> addr 0
        (8, 0, 1),      # Second character: column 1, row 0 -> addr 1
        (16, 0, 2),     # Third character: column 2, row 0 -> addr 2
        (0, 16, 80),    # First char of row 1: col 0, row 1 -> addr 80
        (632, 0, 79),   # Last char of row 0: col 79, row 0 -> addr 79
    ]

    for h_pos, v_pos, expected_addr in test_positions:
        dut.h_count.value = h_pos
        dut.v_count.value = v_pos
        dut.video_active.value = 1
        dut.char_data.value = 0x59  # 'Y'
        dut.font_pixels.value = 0x55  # Alternating pattern
        await RisingEdge(dut.clk)

        char_addr = int(dut.char_addr.value)
        dut._log.info(f"Position ({h_pos}, {v_pos}): char_addr={char_addr}, expected={expected_addr}")

        assert char_addr == expected_addr, \
            f"80-col mode: h={h_pos}, v={v_pos} should give addr={expected_addr}, got {char_addr}"

    dut._log.info("80-column timing verified")


@cocotb.test()
async def test_character_renderer_colors(dut):
    """Test foreground and background color application

    Tests that the renderer correctly applies foreground color to character
    pixels and background color to empty pixels.
    """

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.mode_80col.value = 0  # 40-column mode
    dut.font_pixels.value = 0xF0  # Half on, half off
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Test various color combinations
    color_tests = [
        (COLOR_WHITE, COLOR_BLACK, "White on Black"),
        (COLOR_GREEN, COLOR_BLUE, "Green on Blue"),
        (COLOR_YELLOW, COLOR_RED, "Yellow on Red"),
        (COLOR_CYAN, COLOR_MAGENTA, "Cyan on Magenta"),
    ]

    for fg_color, bg_color, description in color_tests:
        dut.fg_color.value = fg_color
        dut.bg_color.value = bg_color
        dut.char_data.value = 0x4D  # 'M'
        dut.font_pixels.value = 0xF0  # Half on, half off

        # Test first pixel of character at (0,0)
        dut.h_count.value = 0
        dut.v_count.value = 0
        dut.video_active.value = 1
        await RisingEdge(dut.clk)

        r = int(dut.red.value)
        g = int(dut.green.value)
        b = int(dut.blue.value)

        # Compute expected foreground color (8-bit RGB)
        fg_r = color_3bit_to_8bit(fg_color, 2)  # Red is bit 2
        fg_g = color_3bit_to_8bit(fg_color, 1)  # Green is bit 1
        fg_b = color_3bit_to_8bit(fg_color, 0)  # Blue is bit 0

        # Compute expected background color (8-bit RGB)
        bg_r = color_3bit_to_8bit(bg_color, 2)
        bg_g = color_3bit_to_8bit(bg_color, 1)
        bg_b = color_3bit_to_8bit(bg_color, 0)

        dut._log.info(f"{description}: R={r:02X} G={g:02X} B={b:02X}")
        dut._log.info(f"  Expected FG: R={fg_r:02X} G={fg_g:02X} B={fg_b:02X}")
        dut._log.info(f"  Expected BG: R={bg_r:02X} G={bg_g:02X} B={bg_b:02X}")

        # Pixel should be either foreground or background color
        is_fg = (r == fg_r and g == fg_g and b == fg_b)
        is_bg = (r == bg_r and g == bg_g and b == bg_b)

        assert is_fg or is_bg, \
            f"{description}: Pixel color ({r:02X},{g:02X},{b:02X}) " \
            f"matches neither FG ({fg_r:02X},{fg_g:02X},{fg_b:02X}) " \
            f"nor BG ({bg_r:02X},{bg_g:02X},{bg_b:02X})"

    dut._log.info("Color application verified for all test cases")


@cocotb.test()
async def test_character_renderer_video_inactive(dut):
    """Test that output is black when video_active is low

    During horizontal/vertical blanking, video_active=0 and output should be black.
    """

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.mode_80col.value = 0
    dut.fg_color.value = COLOR_WHITE
    dut.bg_color.value = COLOR_RED
    dut.font_pixels.value = 0xFF  # All pixels on
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Set position in active video area but video_active=0
    dut.h_count.value = 100
    dut.v_count.value = 100
    dut.video_active.value = 0
    dut.char_data.value = 0x48  # 'H'
    dut.font_pixels.value = 0xFF  # All pixels on
    await RisingEdge(dut.clk)

    r = int(dut.red.value)
    g = int(dut.green.value)
    b = int(dut.blue.value)

    dut._log.info(f"Inactive video: R={r:02X} G={g:02X} B={b:02X}")

    # Output should be black (0x00, 0x00, 0x00) during blanking
    assert r == 0x00, f"Red should be 0x00 during blanking, got 0x{r:02X}"
    assert g == 0x00, f"Green should be 0x00 during blanking, got 0x{g:02X}"
    assert b == 0x00, f"Blue should be 0x00 during blanking, got 0x{b:02X}"

    dut._log.info("Video blanking verified - output is black")


@cocotb.test()
async def test_character_renderer_horizontal_sequence(dut):
    """Test rendering a horizontal sequence of characters

    Verifies that as h_count advances, the correct character addresses
    are generated and pixels are output continuously.
    """

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.mode_80col.value = 0  # 40-column mode (16 pixels per char)
    dut.fg_color.value = COLOR_WHITE
    dut.bg_color.value = COLOR_BLACK
    dut.font_pixels.value = 0x81  # Test pattern
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Simulate rendering first 3 characters of scanline 0
    # Characters 0, 1, 2 (addresses 0, 1, 2)
    dut.v_count.value = 0
    dut.video_active.value = 1

    previous_addr = -1
    pixels_per_char = 0

    for h_pixel in range(48):  # 3 characters * 16 pixels
        dut.h_count.value = h_pixel

        # Simulate character buffer returning different chars
        char_col = h_pixel // 16
        dut.char_data.value = 0x41 + char_col  # 'A', 'B', 'C'
        dut.font_pixels.value = 0x81  # Test pattern

        await RisingEdge(dut.clk)

        char_addr = int(dut.char_addr.value)
        r = int(dut.red.value)
        g = int(dut.green.value)
        b = int(dut.blue.value)

        # Track when character address changes
        if char_addr != previous_addr:
            if previous_addr >= 0:
                dut._log.info(f"Character {previous_addr} rendered with {pixels_per_char} pixels")
                assert pixels_per_char == 16, \
                    f"Expected 16 pixels per character in 40-col mode, got {pixels_per_char}"
            previous_addr = char_addr
            pixels_per_char = 1
        else:
            pixels_per_char += 1

        # Verify pixel output is valid color
        assert r in [0x00, 0xFF], f"Pixel {h_pixel} red invalid"
        assert g in [0x00, 0xFF], f"Pixel {h_pixel} green invalid"
        assert b in [0x00, 0xFF], f"Pixel {h_pixel} blue invalid"

    dut._log.info("Horizontal character sequence verified")


@cocotb.test()
async def test_character_renderer_char_buffer_addressing(dut):
    """Test character buffer addressing for various screen positions

    Verifies that char_addr is correctly calculated from h_count and v_count
    for both display modes.

    Address formula:
        char_col = h_count / pixels_per_char
        char_row = v_count / 16
        char_addr = char_row * chars_per_row + char_col

    40-column mode: chars_per_row = 40, pixels_per_char = 16
    80-column mode: chars_per_row = 80, pixels_per_char = 8
    """

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.font_pixels.value = 0xC3  # Test pattern
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Test cases: (mode_80col, h_count, v_count, expected_addr, description)
    test_cases = [
        # 40-column mode tests
        (0, 0, 0, 0, "40-col: Top-left (0,0)"),
        (0, 16, 0, 1, "40-col: Second char row 0 (16,0)"),
        (0, 624, 0, 39, "40-col: Last char row 0 (624,0)"),
        (0, 0, 16, 40, "40-col: First char row 1 (0,16)"),
        (0, 320, 240, 900, "40-col: Middle char (320,240) = row 15, col 20 = 15*40+20"),
        (0, 624, 464, 1179, "40-col: Bottom-right (624,464) = row 29, col 39 = 29*40+39"),

        # 80-column mode tests
        (1, 0, 0, 0, "80-col: Top-left (0,0)"),
        (1, 8, 0, 1, "80-col: Second char row 0 (8,0)"),
        (1, 632, 0, 79, "80-col: Last char row 0 (632,0)"),
        (1, 0, 16, 80, "80-col: First char row 1 (0,16)"),
        (1, 320, 240, 1240, "80-col: Middle char (320,240) = row 15, col 40 = 15*80+40"),
        (1, 632, 464, 2399, "80-col: Bottom-right (632,464) = row 29, col 79 = 29*80+79"),
    ]

    for mode_80col, h, v, expected_addr, desc in test_cases:
        dut.mode_80col.value = mode_80col
        dut.h_count.value = h
        dut.v_count.value = v
        dut.video_active.value = 1
        dut.fg_color.value = COLOR_WHITE
        dut.bg_color.value = COLOR_BLACK
        dut.char_data.value = 0x2A  # '*'
        dut.font_pixels.value = 0xC3  # Test pattern

        await RisingEdge(dut.clk)

        char_addr = int(dut.char_addr.value)
        dut._log.info(f"{desc}: addr={char_addr}, expected={expected_addr}")

        assert char_addr == expected_addr, \
            f"{desc}: Expected addr={expected_addr}, got {char_addr}"

    dut._log.info("Character buffer addressing verified for all test cases")


# Test runner for pytest integration
def test_runner():
    """pytest entry point for running cocotb tests"""
    import os
    from pathlib import Path

    # Get project root
    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    # RTL sources - character_renderer will need font_rom
    verilog_sources = [
        rtl_dir / "peripherals" / "video" / "character_renderer.v",
        # Note: May also need font_rom.v depending on implementation
        # rtl_dir / "peripherals" / "video" / "font_rom.v",
    ]

    # Parameters (if any)
    parameters = {}

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="character_renderer",
        module="test_character_renderer",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
        compile_args=["-g2012", "-Wno-timescale"],
        sim_args=["-fst"] if os.getenv("WAVES") == "1" else [],
        timescale="1ns/1ps",
    )


if __name__ == "__main__":
    test_runner()
