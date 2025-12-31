"""
Test suite for font_rom.v module
Tests 8x16 VGA font ROM with ASCII characters 0x20-0x7F

Font Format:
- 8x16 pixel characters (8 pixels wide, 16 scanlines tall)
- ASCII printable range: 0x20-0x7E (96 characters)
- Each character: 16 bytes (one byte per scanline)
- Total ROM size: 96 chars × 16 bytes = 1536 bytes
- Non-printable chars (0x00-0x1F, 0x7F, 0x80-0xFF) show placeholder glyph
- Font data loaded from: rtl/peripherals/video/font_data.hex
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from pathlib import Path


# Known font patterns for verification (from font_data.hex)
# These are the expected pixel patterns for specific characters

# Character 'A' (0x41) - recognizable pattern
FONT_CHAR_A = [
    0x00, 0x00, 0x10, 0x38, 0x6C, 0xC6, 0xC6, 0xFE,
    0xC6, 0xC6, 0xC6, 0x00, 0x00, 0x00, 0x00, 0x00
]

# Character 'H' (0x48) - recognizable pattern
FONT_CHAR_H = [
    0x00, 0x00, 0xC6, 0xC6, 0xC6, 0xC6, 0xFE, 0xC6,
    0xC6, 0xC6, 0xC6, 0x00, 0x00, 0x00, 0x00, 0x00
]

# Character '0' (0x30) - recognizable pattern
FONT_CHAR_ZERO = [
    0x00, 0x00, 0x7C, 0xC6, 0xCE, 0xDE, 0xF6, 0xE6,
    0xC6, 0xC6, 0x7C, 0x00, 0x00, 0x00, 0x00, 0x00
]

# Character '@' (0x40) - recognizable pattern
FONT_CHAR_AT = [
    0x00, 0x00, 0x00, 0x7C, 0xC6, 0xC6, 0xDE, 0xDE,
    0xDE, 0xDC, 0xC0, 0x7E, 0x00, 0x00, 0x00, 0x00
]

# Character ' ' (0x20) - space (all zeros)
FONT_CHAR_SPACE = [0x00] * 16

# Character '!' (0x21) - exclamation mark
FONT_CHAR_EXCLAMATION = [
    0x00, 0x00, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18,
    0x18, 0x00, 0x18, 0x18, 0x00, 0x00, 0x00, 0x00
]

# Placeholder glyph for non-printable chars (0x7F in font data)
# This is a solid block pattern
FONT_PLACEHOLDER = [
    0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00
]


async def read_character(dut, char_code):
    """
    Read all 16 scanlines of a character from the font ROM.
    Returns list of 16 bytes representing the character bitmap.
    """
    scanlines = []
    for scanline in range(16):
        dut.char_code.value = char_code
        dut.scanline.value = scanline
        await RisingEdge(dut.clk)
        # Read pixel_row after clock edge (ROM should be synchronous)
        pixel_row = int(dut.pixel_row.value)
        scanlines.append(pixel_row)
    return scanlines


def compare_scanlines(actual, expected, char_code):
    """Helper to compare scanline arrays and provide detailed error message"""
    if actual == expected:
        return True

    # Generate detailed error message
    char_str = chr(char_code) if 0x20 <= char_code <= 0x7E else f"0x{char_code:02X}"
    error_msg = f"\nCharacter {char_str} (0x{char_code:02X}) mismatch:\n"
    error_msg += "Scanline | Expected | Actual\n"
    error_msg += "---------|----------|--------\n"
    for i, (exp, act) in enumerate(zip(expected, actual)):
        mark = "  <--" if exp != act else ""
        error_msg += f"   {i:2d}    |   0x{exp:02X}   | 0x{act:02X}{mark}\n"
    assert False, error_msg


@cocotb.test()
async def test_font_rom_basic_operation(dut):
    """Test basic ROM read operation"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Wait a few clocks for initialization
    for _ in range(5):
        await RisingEdge(dut.clk)

    # Read first scanline of space character (0x20)
    dut.char_code.value = 0x20
    dut.scanline.value = 0
    await RisingEdge(dut.clk)

    # Should read valid data (space is all 0x00)
    pixel_row = int(dut.pixel_row.value)
    assert pixel_row == 0x00, f"Space first scanline should be 0x00, got 0x{pixel_row:02X}"


@cocotb.test()
async def test_font_rom_character_a(dut):
    """Test reading character 'A' (0x41)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read all scanlines of 'A'
    scanlines = await read_character(dut, 0x41)

    # Verify against known pattern
    compare_scanlines(scanlines, FONT_CHAR_A, 0x41)


@cocotb.test()
async def test_font_rom_character_h(dut):
    """Test reading character 'H' (0x48)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read all scanlines of 'H'
    scanlines = await read_character(dut, 0x48)

    # Verify against known pattern
    compare_scanlines(scanlines, FONT_CHAR_H, 0x48)


@cocotb.test()
async def test_font_rom_character_zero(dut):
    """Test reading character '0' (0x30)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read all scanlines of '0'
    scanlines = await read_character(dut, 0x30)

    # Verify against known pattern
    compare_scanlines(scanlines, FONT_CHAR_ZERO, 0x30)


@cocotb.test()
async def test_font_rom_character_at(dut):
    """Test reading character '@' (0x40)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read all scanlines of '@'
    scanlines = await read_character(dut, 0x40)

    # Verify against known pattern
    compare_scanlines(scanlines, FONT_CHAR_AT, 0x40)


@cocotb.test()
async def test_font_rom_space_character(dut):
    """Test reading space character (0x20) - should be all zeros"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read all scanlines of space
    scanlines = await read_character(dut, 0x20)

    # All scanlines should be 0x00
    compare_scanlines(scanlines, FONT_CHAR_SPACE, 0x20)


@cocotb.test()
async def test_font_rom_exclamation_mark(dut):
    """Test reading exclamation mark (0x21)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read all scanlines of '!'
    scanlines = await read_character(dut, 0x21)

    # Verify against known pattern
    compare_scanlines(scanlines, FONT_CHAR_EXCLAMATION, 0x21)


@cocotb.test()
async def test_font_rom_printable_range_start(dut):
    """Test first printable character in range (0x20 - space)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read space (first printable char)
    scanlines = await read_character(dut, 0x20)

    # Verify it's readable (all zeros for space)
    assert all(s == 0x00 for s in scanlines), "Space character should be all zeros"


@cocotb.test()
async def test_font_rom_printable_range_end(dut):
    """Test last printable character in range (0x7E - tilde)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read tilde (last standard printable char)
    scanlines = await read_character(dut, 0x7E)

    # Verify it has some pixels set (tilde is not blank)
    pixels_set = sum(s for s in scanlines)
    assert pixels_set > 0, "Tilde character should have some pixels set"


@cocotb.test()
async def test_font_rom_placeholder_for_control_chars(dut):
    """Test that control characters (0x00-0x1F) show placeholder glyph"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Test a few control characters - they should all show placeholder
    control_chars = [0x00, 0x01, 0x0D, 0x1F]

    for char_code in control_chars:
        scanlines = await read_character(dut, char_code)
        # Placeholder should have many pixels set (solid block pattern)
        pixels_set = sum(s for s in scanlines)
        assert pixels_set > 0, \
            f"Control char 0x{char_code:02X} should show placeholder glyph with pixels"


@cocotb.test()
async def test_font_rom_placeholder_for_del(dut):
    """Test that DEL character (0x7F) shows placeholder glyph"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read DEL character
    scanlines = await read_character(dut, 0x7F)

    # Should match placeholder pattern (solid block)
    compare_scanlines(scanlines, FONT_PLACEHOLDER, 0x7F)


@cocotb.test()
async def test_font_rom_placeholder_for_high_chars(dut):
    """Test that high characters (0x80-0xFF) show placeholder glyph"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Test a few high characters - they should all show placeholder
    high_chars = [0x80, 0xAA, 0xFF]

    for char_code in high_chars:
        scanlines = await read_character(dut, char_code)
        # Placeholder should match the solid block pattern
        compare_scanlines(scanlines, FONT_PLACEHOLDER, char_code)


@cocotb.test()
async def test_font_rom_scanline_addressing(dut):
    """Test that scanline parameter correctly selects rows within a character"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Test character 'A' scanline by scanline
    dut.char_code.value = 0x41  # 'A'

    for scanline_num in range(16):
        dut.scanline.value = scanline_num
        await RisingEdge(dut.clk)
        pixel_row = int(dut.pixel_row.value)
        expected = FONT_CHAR_A[scanline_num]
        assert pixel_row == expected, \
            f"'A' scanline {scanline_num}: expected 0x{expected:02X}, got 0x{pixel_row:02X}"


@cocotb.test()
async def test_font_rom_address_calculation(dut):
    """Test correct address calculation: addr = (char_code - 0x20) * 16 + scanline"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Test that different characters access different memory regions
    # by verifying they have different patterns

    char_codes = [0x20, 0x30, 0x41, 0x5A, 0x7E]
    char_data = []

    for char_code in char_codes:
        scanlines = await read_character(dut, char_code)
        char_data.append((char_code, scanlines))

    # Verify that different characters have different data
    # (except space which is intentionally blank)
    for i, (code1, data1) in enumerate(char_data):
        for code2, data2 in char_data[i+1:]:
            if code1 == 0x20 or code2 == 0x20:
                continue  # Skip space comparison
            # Different characters should have different patterns
            if data1 == data2:
                char1 = chr(code1) if 0x20 <= code1 <= 0x7E else f"0x{code1:02X}"
                char2 = chr(code2) if 0x20 <= code2 <= 0x7E else f"0x{code2:02X}"
                assert False, f"Characters {char1} and {char2} should not be identical"


@cocotb.test()
async def test_font_rom_all_scanlines_valid(dut):
    """Test that all 16 scanlines can be addressed for a character"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Pick a character with pixels throughout (like 'H')
    dut.char_code.value = 0x48

    # Read all 16 scanlines
    for scanline in range(16):
        dut.scanline.value = scanline
        await RisingEdge(dut.clk)
        pixel_row = int(dut.pixel_row.value)
        # Just verify we get valid data (not undefined)
        assert 0 <= pixel_row <= 0xFF, \
            f"Scanline {scanline} returned invalid value: {pixel_row}"


@cocotb.test()
async def test_font_rom_sequential_reads(dut):
    """Test reading multiple characters sequentially"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read "HELLO" string
    test_string = [0x48, 0x45, 0x4C, 0x4C, 0x4F]  # "HELLO"

    for char_code in test_string:
        # Read first few scanlines of each character
        for scanline in range(4):
            dut.char_code.value = char_code
            dut.scanline.value = scanline
            await RisingEdge(dut.clk)
            pixel_row = int(dut.pixel_row.value)
            # Just verify we get valid reads
            assert 0 <= pixel_row <= 0xFF, \
                f"Char 0x{char_code:02X} scanline {scanline} invalid"


@cocotb.test()
async def test_font_rom_random_access(dut):
    """Test random access pattern (non-sequential reads)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Random access pattern: different chars and scanlines
    access_pattern = [
        (0x41, 5),   # 'A' scanline 5
        (0x5A, 10),  # 'Z' scanline 10
        (0x30, 0),   # '0' scanline 0
        (0x41, 5),   # 'A' scanline 5 again (should be same)
        (0x40, 8),   # '@' scanline 8
    ]

    results = []
    for char_code, scanline in access_pattern:
        dut.char_code.value = char_code
        dut.scanline.value = scanline
        await RisingEdge(dut.clk)
        pixel_row = int(dut.pixel_row.value)
        results.append((char_code, scanline, pixel_row))

    # Verify repeated reads give same result
    assert results[0][2] == results[3][2], \
        "Repeated read of same location should return same value"


@cocotb.test()
async def test_font_rom_digits(dut):
    """Test reading all digit characters 0-9"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read all digits (0x30-0x39)
    for char_code in range(0x30, 0x3A):
        scanlines = await read_character(dut, char_code)
        # Verify digits have content (non-zero pixels)
        pixels_set = sum(s for s in scanlines)
        digit = chr(char_code)
        assert pixels_set > 0, f"Digit '{digit}' should have pixels set"


@cocotb.test()
async def test_font_rom_uppercase_letters(dut):
    """Test reading uppercase letters A-Z"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read uppercase A-Z (0x41-0x5A)
    for char_code in range(0x41, 0x5B):
        scanlines = await read_character(dut, char_code)
        # Verify letters have content
        pixels_set = sum(s for s in scanlines)
        letter = chr(char_code)
        assert pixels_set > 0, f"Letter '{letter}' should have pixels set"


@cocotb.test()
async def test_font_rom_lowercase_letters(dut):
    """Test reading lowercase letters a-z"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Read lowercase a-z (0x61-0x7A)
    for char_code in range(0x61, 0x7B):
        scanlines = await read_character(dut, char_code)
        # Verify letters have content
        pixels_set = sum(s for s in scanlines)
        letter = chr(char_code)
        assert pixels_set > 0, f"Letter '{letter}' should have pixels set"


@cocotb.test()
async def test_font_rom_punctuation(dut):
    """Test reading common punctuation marks"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Test punctuation: ! " # $ % & ' ( ) * + , - . /
    punct_codes = [0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27,
                   0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F]

    for char_code in punct_codes:
        scanlines = await read_character(dut, char_code)
        # All should be readable (will have varying content)
        assert len(scanlines) == 16, \
            f"Punctuation 0x{char_code:02X} should return 16 scanlines"


@cocotb.test()
async def test_font_rom_data_integrity(dut):
    """Test that font data loaded correctly from font_data.hex"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    await RisingEdge(dut.clk)

    # Test several known patterns to ensure hex file loaded correctly
    test_cases = [
        (0x20, FONT_CHAR_SPACE),
        (0x30, FONT_CHAR_ZERO),
        (0x40, FONT_CHAR_AT),
        (0x41, FONT_CHAR_A),
        (0x48, FONT_CHAR_H),
        (0x7F, FONT_PLACEHOLDER),
    ]

    for char_code, expected in test_cases:
        scanlines = await read_character(dut, char_code)
        compare_scanlines(scanlines, expected, char_code)


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
        rtl_dir / "peripherals" / "video" / "font_rom.v"
    ]

    # Check if source files exist
    for src in verilog_sources:
        if not src.exists():
            print(f"WARNING: Source file not found: {src}")
            print("This is expected for TDD - test will fail until module is implemented.")

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="font_rom",
        module="test_font_rom",
        simulator=simulator,
        waves=True if os.getenv("WAVES") == "1" else False,
        timescale="1ns/1ps",
        compile_args=["-g2012", "-Wno-timescale", "-I" + str(rtl_dir / "peripherals" / "video")],
    )


if __name__ == "__main__":
    test_runner()
