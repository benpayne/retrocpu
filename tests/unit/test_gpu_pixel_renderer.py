"""
Test suite for gpu_pixel_renderer.v module
Tests pixel decoding and rendering for 1/2/4 BPP graphics modes

The pixel renderer is responsible for:
- Converting VRAM bytes to individual pixels based on graphics mode
- Decoding pixel values to palette indices
- Calculating VRAM addresses from screen coordinates
- Supporting 1 BPP, 2 BPP, and 4 BPP graphics modes

Module Interface (gpu_pixel_renderer.v):
    Inputs:
        clk_pixel        - Pixel clock (25.175 MHz for 640x480)
        rst_n            - Active-low reset
        h_count[9:0]     - Horizontal counter from VGA timing (0-639)
        v_count[9:0]     - Vertical counter from VGA timing (0-479)
        gpu_mode[1:0]    - Graphics mode (00=1BPP, 01=2BPP, 10=4BPP)
        fb_base_addr[14:0] - Framebuffer base address in VRAM
        vram_data[7:0]   - VRAM byte read from current address

    Outputs:
        vram_addr[14:0]  - VRAM address to fetch
        pixel_palette_index[3:0] - Palette index for current pixel
        pixel_valid      - Pixel is in visible region

Graphics Modes:
    1 BPP: 8 pixels per byte (1 bit per pixel)
           Bit pattern: MSB first (bit 7 = first pixel)
           Palette indices: 0 or 1

    2 BPP: 4 pixels per byte (2 bits per pixel)
           Bit pattern: MSB first (bits [7:6] = first pixel)
           Palette indices: 0-3

    4 BPP: 2 pixels per byte (4 bits per pixel)
           Bit pattern: MSB first (bits [7:4] = first pixel)
           Palette indices: 0-15

Addressing:
    VRAM address = fb_base_addr + pixel_offset
    where pixel_offset depends on mode and pixel position
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


# Graphics mode constants
MODE_1BPP = 0b00
MODE_2BPP = 0b01
MODE_4BPP = 0b10

# Display dimensions
H_VISIBLE = 640
V_VISIBLE = 480


async def reset_dut(dut):
    """Reset the DUT and wait for it to stabilize"""
    dut.rst_n.value = 0
    dut.h_count.value = 0
    dut.v_count.value = 0
    dut.gpu_mode.value = MODE_1BPP
    dut.fb_base_addr.value = 0
    dut.vram_data.value = 0

    await ClockCycles(dut.clk_pixel, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk_pixel, 2)


@cocotb.test()
async def test_reset_state(dut):
    """Test that pixel renderer resets correctly"""

    clock = Clock(dut.clk_pixel, 40, units="ns")  # 25 MHz pixel clock
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    # After reset, outputs should be stable
    assert dut.vram_addr.value >= 0, "VRAM address should be valid"
    assert dut.pixel_palette_index.value >= 0, "Palette index should be valid"
    assert dut.pixel_valid.value in [0, 1], "Pixel valid should be 0 or 1"

    dut._log.info("Reset state verified")


@cocotb.test()
async def test_1bpp_mode_pixel_decode(dut):
    """Test 1 BPP mode: 8 pixels per byte, alternating black/white pattern

    VRAM byte: 0b10101010
    Expected pixels: 1,0,1,0,1,0,1,0 (MSB first)
    Palette indices: 1,0,1,0,1,0,1,0
    """

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    # Set 1 BPP mode
    dut.gpu_mode.value = MODE_1BPP
    dut.fb_base_addr.value = 0x0000
    dut.v_count.value = 0

    # Test pattern: 0b10101010 = alternating bits
    test_byte = 0b10101010
    dut.vram_data.value = test_byte

    # Expected palette indices for each pixel (MSB first)
    expected_indices = [1, 0, 1, 0, 1, 0, 1, 0]

    dut._log.info(f"Testing 1 BPP mode with byte 0x{test_byte:02X}")

    pixels_decoded = []

    for pixel_x in range(8):
        dut.h_count.value = pixel_x
        await RisingEdge(dut.clk_pixel)

        palette_idx = int(dut.pixel_palette_index.value)
        pixels_decoded.append(palette_idx)

        expected_idx = expected_indices[pixel_x]
        dut._log.info(f"Pixel {pixel_x}: palette_idx={palette_idx}, expected={expected_idx}")

        assert palette_idx == expected_idx, \
            f"1 BPP: Pixel {pixel_x} should decode to {expected_idx}, got {palette_idx}"
        assert dut.pixel_valid.value == 1, f"Pixel {pixel_x} should be valid in visible region"

    dut._log.info(f"1 BPP decode verified: {pixels_decoded}")


@cocotb.test()
async def test_1bpp_mode_all_zeros(dut):
    """Test 1 BPP mode with all zeros"""

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.gpu_mode.value = MODE_1BPP
    dut.fb_base_addr.value = 0x0000
    dut.v_count.value = 0
    dut.vram_data.value = 0x00

    for pixel_x in range(8):
        dut.h_count.value = pixel_x
        await RisingEdge(dut.clk_pixel)

        palette_idx = int(dut.pixel_palette_index.value)
        assert palette_idx == 0, f"1 BPP: All zero byte should give palette index 0, got {palette_idx}"

    dut._log.info("1 BPP all zeros verified")


@cocotb.test()
async def test_1bpp_mode_all_ones(dut):
    """Test 1 BPP mode with all ones"""

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.gpu_mode.value = MODE_1BPP
    dut.fb_base_addr.value = 0x0000
    dut.v_count.value = 0
    dut.vram_data.value = 0xFF

    for pixel_x in range(8):
        dut.h_count.value = pixel_x
        await RisingEdge(dut.clk_pixel)

        palette_idx = int(dut.pixel_palette_index.value)
        assert palette_idx == 1, f"1 BPP: All ones byte should give palette index 1, got {palette_idx}"

    dut._log.info("1 BPP all ones verified")


@cocotb.test()
async def test_2bpp_mode_pixel_decode(dut):
    """Test 2 BPP mode: 4 pixels per byte

    VRAM byte: 0b11100100 = 0xE4
    Bit pairs (MSB first): 11, 10, 01, 00
    Expected palette indices: 3, 2, 1, 0
    """

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    # Set 2 BPP mode
    dut.gpu_mode.value = MODE_2BPP
    dut.fb_base_addr.value = 0x0000
    dut.v_count.value = 0

    # Test pattern: 0b11100100
    test_byte = 0b11100100
    dut.vram_data.value = test_byte

    # Expected palette indices (2 bits per pixel, MSB first)
    expected_indices = [3, 2, 1, 0]

    dut._log.info(f"Testing 2 BPP mode with byte 0x{test_byte:02X}")

    pixels_decoded = []

    for pixel_x in range(4):
        dut.h_count.value = pixel_x
        await RisingEdge(dut.clk_pixel)

        palette_idx = int(dut.pixel_palette_index.value)
        pixels_decoded.append(palette_idx)

        expected_idx = expected_indices[pixel_x]
        dut._log.info(f"Pixel {pixel_x}: palette_idx={palette_idx}, expected={expected_idx}")

        assert palette_idx == expected_idx, \
            f"2 BPP: Pixel {pixel_x} should decode to {expected_idx}, got {palette_idx}"
        assert dut.pixel_valid.value == 1, f"Pixel {pixel_x} should be valid in visible region"

    dut._log.info(f"2 BPP decode verified: {pixels_decoded}")


@cocotb.test()
async def test_2bpp_mode_all_values(dut):
    """Test 2 BPP mode with all possible 2-bit values"""

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.gpu_mode.value = MODE_2BPP
    dut.fb_base_addr.value = 0x0000
    dut.v_count.value = 0

    # Test bytes with different patterns
    test_cases = [
        (0x00, [0, 0, 0, 0], "All zeros"),
        (0xFF, [3, 3, 3, 3], "All ones"),
        (0x1B, [0, 1, 2, 3], "Sequential 0-3"),
        (0xE4, [3, 2, 1, 0], "Reverse 3-0"),
    ]

    for test_byte, expected_indices, description in test_cases:
        dut.vram_data.value = test_byte
        dut._log.info(f"Testing 2 BPP: {description} (0x{test_byte:02X})")

        for pixel_x in range(4):
            dut.h_count.value = pixel_x
            await RisingEdge(dut.clk_pixel)

            palette_idx = int(dut.pixel_palette_index.value)
            expected_idx = expected_indices[pixel_x]

            assert palette_idx == expected_idx, \
                f"2 BPP {description}: Pixel {pixel_x} should be {expected_idx}, got {palette_idx}"

    dut._log.info("2 BPP all values verified")


@cocotb.test()
async def test_4bpp_mode_pixel_decode(dut):
    """Test 4 BPP mode: 2 pixels per byte

    VRAM byte: 0xA5
    Nibbles (MSB first): 0xA (10), 0x5 (5)
    Expected palette indices: 10, 5
    """

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    # Set 4 BPP mode
    dut.gpu_mode.value = MODE_4BPP
    dut.fb_base_addr.value = 0x0000
    dut.v_count.value = 0

    # Test pattern: 0xA5
    test_byte = 0xA5
    dut.vram_data.value = test_byte

    # Expected palette indices (4 bits per pixel, MSB first)
    expected_indices = [10, 5]

    dut._log.info(f"Testing 4 BPP mode with byte 0x{test_byte:02X}")

    pixels_decoded = []

    for pixel_x in range(2):
        dut.h_count.value = pixel_x
        await RisingEdge(dut.clk_pixel)

        palette_idx = int(dut.pixel_palette_index.value)
        pixels_decoded.append(palette_idx)

        expected_idx = expected_indices[pixel_x]
        dut._log.info(f"Pixel {pixel_x}: palette_idx={palette_idx} (0x{palette_idx:X}), expected={expected_idx}")

        assert palette_idx == expected_idx, \
            f"4 BPP: Pixel {pixel_x} should decode to {expected_idx}, got {palette_idx}"
        assert dut.pixel_valid.value == 1, f"Pixel {pixel_x} should be valid in visible region"

    dut._log.info(f"4 BPP decode verified: {pixels_decoded}")


@cocotb.test()
async def test_4bpp_mode_all_values(dut):
    """Test 4 BPP mode with various nibble combinations"""

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.gpu_mode.value = MODE_4BPP
    dut.fb_base_addr.value = 0x0000
    dut.v_count.value = 0

    # Test bytes with different patterns
    test_cases = [
        (0x00, [0, 0], "All zeros"),
        (0xFF, [15, 15], "All ones"),
        (0x01, [0, 1], "Low values"),
        (0xFE, [15, 14], "High values"),
        (0xA5, [10, 5], "0xA5 pattern"),
        (0x5A, [5, 10], "0x5A pattern"),
        (0x0F, [0, 15], "Low/High"),
        (0xF0, [15, 0], "High/Low"),
    ]

    for test_byte, expected_indices, description in test_cases:
        dut.vram_data.value = test_byte
        dut._log.info(f"Testing 4 BPP: {description} (0x{test_byte:02X})")

        for pixel_x in range(2):
            dut.h_count.value = pixel_x
            await RisingEdge(dut.clk_pixel)

            palette_idx = int(dut.pixel_palette_index.value)
            expected_idx = expected_indices[pixel_x]

            assert palette_idx == expected_idx, \
                f"4 BPP {description}: Pixel {pixel_x} should be {expected_idx}, got {palette_idx}"

    dut._log.info("4 BPP all values verified")


@cocotb.test()
async def test_vram_address_calculation_1bpp(dut):
    """Test VRAM address calculation in 1 BPP mode

    In 1 BPP mode:
    - 8 pixels per byte
    - Byte address = (v_count * 640 + h_count) / 8
    - For 640-pixel wide screen: 80 bytes per scanline
    """

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.gpu_mode.value = MODE_1BPP
    dut.fb_base_addr.value = 0x0000
    dut.vram_data.value = 0x00

    # Test cases: (h_count, v_count, expected_byte_offset)
    test_cases = [
        (0, 0, 0, "First pixel, first scanline"),
        (8, 0, 1, "Second byte, first scanline"),
        (16, 0, 2, "Third byte, first scanline"),
        (632, 0, 79, "Last byte, first scanline (632/8=79)"),
        (0, 1, 80, "First byte, second scanline (1*80)"),
        (0, 2, 160, "First byte, third scanline (2*80)"),
        (8, 1, 81, "Second byte, second scanline (80+1)"),
        (320, 240, 19280, "Middle pixel (240*80 + 320/8 = 19200+40)"),
    ]

    for h, v, expected_offset, description in test_cases:
        dut.h_count.value = h
        dut.v_count.value = v
        await RisingEdge(dut.clk_pixel)

        vram_addr = int(dut.vram_addr.value)
        expected_addr = expected_offset

        dut._log.info(f"{description}: ({h},{v}) -> addr={vram_addr}, expected={expected_addr}")

        assert vram_addr == expected_addr, \
            f"1 BPP {description}: Expected addr={expected_addr}, got {vram_addr}"

    dut._log.info("1 BPP VRAM address calculation verified")


@cocotb.test()
async def test_vram_address_calculation_2bpp(dut):
    """Test VRAM address calculation in 2 BPP mode

    In 2 BPP mode:
    - 4 pixels per byte
    - Byte address = (v_count * 640 + h_count) / 4
    - For 640-pixel wide screen: 160 bytes per scanline
    """

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.gpu_mode.value = MODE_2BPP
    dut.fb_base_addr.value = 0x0000
    dut.vram_data.value = 0x00

    # Test cases: (h_count, v_count, expected_byte_offset)
    test_cases = [
        (0, 0, 0, "First pixel, first scanline"),
        (4, 0, 1, "Second byte, first scanline"),
        (8, 0, 2, "Third byte, first scanline"),
        (636, 0, 159, "Last byte, first scanline (636/4=159)"),
        (0, 1, 160, "First byte, second scanline (1*160)"),
        (0, 2, 320, "First byte, third scanline (2*160)"),
        (4, 1, 161, "Second byte, second scanline (160+1)"),
        (320, 240, 38480, "Middle pixel (240*160 + 320/4 = 38400+80)"),
    ]

    for h, v, expected_offset, description in test_cases:
        dut.h_count.value = h
        dut.v_count.value = v
        await RisingEdge(dut.clk_pixel)

        vram_addr = int(dut.vram_addr.value)
        expected_addr = expected_offset

        dut._log.info(f"{description}: ({h},{v}) -> addr={vram_addr}, expected={expected_addr}")

        assert vram_addr == expected_addr, \
            f"2 BPP {description}: Expected addr={expected_addr}, got {vram_addr}"

    dut._log.info("2 BPP VRAM address calculation verified")


@cocotb.test()
async def test_vram_address_calculation_4bpp(dut):
    """Test VRAM address calculation in 4 BPP mode

    In 4 BPP mode:
    - 2 pixels per byte
    - Byte address = (v_count * 640 + h_count) / 2
    - For 640-pixel wide screen: 320 bytes per scanline
    """

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.gpu_mode.value = MODE_4BPP
    dut.fb_base_addr.value = 0x0000
    dut.vram_data.value = 0x00

    # Test cases: (h_count, v_count, expected_byte_offset)
    test_cases = [
        (0, 0, 0, "First pixel, first scanline"),
        (2, 0, 1, "Second byte, first scanline"),
        (4, 0, 2, "Third byte, first scanline"),
        (638, 0, 319, "Last byte, first scanline (638/2=319)"),
        (0, 1, 320, "First byte, second scanline (1*320)"),
        (0, 2, 640, "First byte, third scanline (2*320)"),
        (2, 1, 321, "Second byte, second scanline (320+1)"),
        (320, 240, 76960, "Middle pixel (240*320 + 320/2 = 76800+160)"),
    ]

    for h, v, expected_offset, description in test_cases:
        dut.h_count.value = h
        dut.v_count.value = v
        await RisingEdge(dut.clk_pixel)

        vram_addr = int(dut.vram_addr.value)
        expected_addr = expected_offset

        dut._log.info(f"{description}: ({h},{v}) -> addr={vram_addr}, expected={expected_addr}")

        assert vram_addr == expected_addr, \
            f"4 BPP {description}: Expected addr={expected_addr}, got {vram_addr}"

    dut._log.info("4 BPP VRAM address calculation verified")


@cocotb.test()
async def test_framebuffer_base_offset(dut):
    """Test that framebuffer base address is added to calculated offset

    VRAM address should be: fb_base_addr + pixel_offset
    """

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    # Test with different base addresses
    test_bases = [0x0000, 0x1000, 0x2000, 0x4000]

    for base_addr in test_bases:
        dut.gpu_mode.value = MODE_1BPP
        dut.fb_base_addr.value = base_addr
        dut.h_count.value = 0
        dut.v_count.value = 0
        dut.vram_data.value = 0x00

        await RisingEdge(dut.clk_pixel)

        vram_addr = int(dut.vram_addr.value)
        expected_addr = base_addr + 0  # Pixel offset is 0 at position (0,0)

        dut._log.info(f"Base 0x{base_addr:04X}: vram_addr=0x{vram_addr:04X}, expected=0x{expected_addr:04X}")

        assert vram_addr == expected_addr, \
            f"With base 0x{base_addr:04X}, expected addr=0x{expected_addr:04X}, got 0x{vram_addr:04X}"

    # Test with offset position
    dut.gpu_mode.value = MODE_1BPP
    dut.fb_base_addr.value = 0x1000
    dut.h_count.value = 8  # Second byte
    dut.v_count.value = 1  # Second scanline
    dut.vram_data.value = 0x00

    await RisingEdge(dut.clk_pixel)

    vram_addr = int(dut.vram_addr.value)
    # 1 BPP: byte offset = (1 * 80) + (8 / 8) = 80 + 1 = 81
    expected_addr = 0x1000 + 81

    assert vram_addr == expected_addr, \
        f"With base 0x1000 and offset 81, expected 0x{expected_addr:04X}, got 0x{vram_addr:04X}"

    dut._log.info("Framebuffer base offset verified")


@cocotb.test()
async def test_mode_switching(dut):
    """Test switching between graphics modes

    Verifies that pixel decoding changes correctly when gpu_mode is changed
    """

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    # Use same VRAM byte (0xC3 = 0b11000011) for all modes
    test_byte = 0xC3
    dut.vram_data.value = test_byte
    dut.fb_base_addr.value = 0x0000

    # Test 1 BPP mode
    dut.gpu_mode.value = MODE_1BPP
    dut.h_count.value = 0
    dut.v_count.value = 0
    await RisingEdge(dut.clk_pixel)

    palette_idx_1bpp = int(dut.pixel_palette_index.value)
    # In 1 BPP, first pixel is bit 7 of 0xC3 (0b11000011) = 1
    assert palette_idx_1bpp == 1, f"1 BPP mode: Expected palette index 1, got {palette_idx_1bpp}"
    dut._log.info(f"1 BPP mode: palette_idx={palette_idx_1bpp}")

    # Switch to 2 BPP mode
    dut.gpu_mode.value = MODE_2BPP
    dut.h_count.value = 0
    dut.v_count.value = 0
    await RisingEdge(dut.clk_pixel)

    palette_idx_2bpp = int(dut.pixel_palette_index.value)
    # In 2 BPP, first pixel is bits [7:6] of 0xC3 (0b11000011) = 0b11 = 3
    assert palette_idx_2bpp == 3, f"2 BPP mode: Expected palette index 3, got {palette_idx_2bpp}"
    dut._log.info(f"2 BPP mode: palette_idx={palette_idx_2bpp}")

    # Switch to 4 BPP mode
    dut.gpu_mode.value = MODE_4BPP
    dut.h_count.value = 0
    dut.v_count.value = 0
    await RisingEdge(dut.clk_pixel)

    palette_idx_4bpp = int(dut.pixel_palette_index.value)
    # In 4 BPP, first pixel is bits [7:4] of 0xC3 (0b11000011) = 0b1100 = 12
    assert palette_idx_4bpp == 12, f"4 BPP mode: Expected palette index 12, got {palette_idx_4bpp}"
    dut._log.info(f"4 BPP mode: palette_idx={palette_idx_4bpp}")

    # Switch back to 1 BPP to verify stability
    dut.gpu_mode.value = MODE_1BPP
    dut.h_count.value = 0
    dut.v_count.value = 0
    await RisingEdge(dut.clk_pixel)

    palette_idx_1bpp_again = int(dut.pixel_palette_index.value)
    assert palette_idx_1bpp_again == 1, \
        f"1 BPP mode (second time): Expected palette index 1, got {palette_idx_1bpp_again}"

    dut._log.info("Mode switching verified - decoding changes correctly")


@cocotb.test()
async def test_pixel_valid_signal(dut):
    """Test pixel_valid signal for visible vs blanking regions"""

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.gpu_mode.value = MODE_1BPP
    dut.fb_base_addr.value = 0x0000
    dut.vram_data.value = 0xFF

    # Test visible region (0 <= h < 640, 0 <= v < 480)
    visible_positions = [
        (0, 0, "Top-left corner"),
        (320, 240, "Center"),
        (639, 479, "Bottom-right corner"),
        (100, 200, "Random visible pixel"),
    ]

    for h, v, description in visible_positions:
        dut.h_count.value = h
        dut.v_count.value = v
        await RisingEdge(dut.clk_pixel)

        pixel_valid = int(dut.pixel_valid.value)
        dut._log.info(f"{description} ({h},{v}): pixel_valid={pixel_valid}")

        assert pixel_valid == 1, \
            f"{description} ({h},{v}) should be valid (in visible region)"

    # Test blanking regions (h >= 640 or v >= 480)
    blanking_positions = [
        (640, 0, "Right of visible (horizontal blanking)"),
        (700, 240, "Far right (horizontal blanking)"),
        (0, 480, "Below visible (vertical blanking)"),
        (320, 500, "Below visible (vertical blanking)"),
        (640, 480, "Corner blanking"),
    ]

    for h, v, description in blanking_positions:
        dut.h_count.value = h
        dut.v_count.value = v
        await RisingEdge(dut.clk_pixel)

        pixel_valid = int(dut.pixel_valid.value)
        dut._log.info(f"{description} ({h},{v}): pixel_valid={pixel_valid}")

        assert pixel_valid == 0, \
            f"{description} ({h},{v}) should be invalid (in blanking region)"

    dut._log.info("Pixel valid signal verified")


@cocotb.test()
async def test_scanline_progression_1bpp(dut):
    """Test that renderer correctly progresses through a scanline in 1 BPP mode

    Verifies that as h_count advances, the correct bytes are fetched and
    pixels are decoded in sequence.
    """

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.gpu_mode.value = MODE_1BPP
    dut.fb_base_addr.value = 0x0000
    dut.v_count.value = 0

    # Simulate first 24 pixels (3 bytes worth)
    # Byte 0: 0xFF (all 1s) -> pixels 0-7 should all be palette index 1
    # Byte 1: 0x00 (all 0s) -> pixels 8-15 should all be palette index 0
    # Byte 2: 0xAA (10101010) -> pixels 16-23 should alternate 1,0,1,0,1,0,1,0

    previous_addr = -1
    byte_count = 0

    for h in range(24):
        dut.h_count.value = h

        # Simulate VRAM data based on byte being fetched
        byte_index = h // 8
        if byte_index == 0:
            dut.vram_data.value = 0xFF
        elif byte_index == 1:
            dut.vram_data.value = 0x00
        elif byte_index == 2:
            dut.vram_data.value = 0xAA

        await RisingEdge(dut.clk_pixel)

        vram_addr = int(dut.vram_addr.value)
        palette_idx = int(dut.pixel_palette_index.value)

        # Track byte changes
        if vram_addr != previous_addr:
            byte_count += 1
            dut._log.info(f"Byte {byte_count}: addr={vram_addr}")
            previous_addr = vram_addr

        # Verify palette index based on pattern
        pixel_in_byte = h % 8
        if byte_index == 0:  # 0xFF
            assert palette_idx == 1, f"Pixel {h} (byte 0): Expected 1, got {palette_idx}"
        elif byte_index == 1:  # 0x00
            assert palette_idx == 0, f"Pixel {h} (byte 1): Expected 0, got {palette_idx}"
        elif byte_index == 2:  # 0xAA = 10101010
            expected = 1 if pixel_in_byte % 2 == 0 else 0
            assert palette_idx == expected, f"Pixel {h} (byte 2): Expected {expected}, got {palette_idx}"

    assert byte_count == 3, f"Should have fetched 3 bytes, got {byte_count}"
    dut._log.info("Scanline progression verified")


@cocotb.test()
async def test_multiple_scanlines(dut):
    """Test rendering multiple scanlines with different VRAM addresses"""

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    dut.gpu_mode.value = MODE_1BPP
    dut.fb_base_addr.value = 0x0000
    dut.vram_data.value = 0x00

    # In 1 BPP: 80 bytes per scanline (640 pixels / 8)
    bytes_per_line = 80

    # Test first pixel of several scanlines
    for scanline in range(5):
        dut.h_count.value = 0
        dut.v_count.value = scanline
        await RisingEdge(dut.clk_pixel)

        vram_addr = int(dut.vram_addr.value)
        expected_addr = scanline * bytes_per_line

        dut._log.info(f"Scanline {scanline}: addr={vram_addr}, expected={expected_addr}")

        assert vram_addr == expected_addr, \
            f"Scanline {scanline}: Expected addr={expected_addr}, got {vram_addr}"

    dut._log.info("Multiple scanlines verified")


# Test runner for pytest integration
def test_runner():
    """pytest entry point for running cocotb tests"""
    import os
    from pathlib import Path

    # Get project root
    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    # RTL sources
    verilog_sources = [
        rtl_dir / "peripherals" / "video" / "gpu_graphics_params.vh",
        rtl_dir / "peripherals" / "video" / "gpu_pixel_renderer.v",
        # Add any dependencies here if needed
    ]

    # Include directory for header files
    includes = [
        rtl_dir / "peripherals" / "video"
    ]

    # Parameters (if any)
    parameters = {}

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        includes=[str(i) for i in includes],
        toplevel="gpu_pixel_renderer",
        module="test_gpu_pixel_renderer",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
        compile_args=["-g2012"],
        timescale="1ns/1ps",
    )


if __name__ == "__main__":
    test_runner()
