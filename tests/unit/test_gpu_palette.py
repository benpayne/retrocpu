"""
Test suite for gpu_graphics_palette.v module
Tests the GPU palette/CLUT (Color Look-Up Table) functionality

Palette Features:
- 16 entries (indices 0-15)
- RGB444 format (4 bits per color channel)
- RGB444 -> RGB888 expansion via bit duplication {R[3:0], R[3:0]}
- Default grayscale ramp on reset
- Write via CLUT_INDEX and CLUT_DATA_R/G/B registers
- Read via pixel_index for color lookup

Per TDD: This test is written BEFORE the RTL implementation
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# Palette constants
PALETTE_SIZE = 16
RGB444_MAX = 0xF
RGB888_MAX = 0xFF


def expand_rgb444_to_rgb888(rgb444_value):
    """
    Expand 4-bit RGB value to 8-bit by duplicating bits.
    Example: 0xF -> 0xFF, 0xA -> 0xAA, 0x0 -> 0x00
    """
    return (rgb444_value << 4) | rgb444_value


async def reset_dut(dut):
    """Reset the DUT and wait for it to stabilize"""
    dut.rst_n.value = 0
    dut.clut_index.value = 0
    dut.clut_data_r.value = 0
    dut.clut_data_g.value = 0
    dut.clut_data_b.value = 0
    dut.clut_we.value = 0
    dut.pixel_index.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def write_palette_entry(dut, index, r, g, b):
    """Write an RGB444 value to a palette entry"""
    dut.clut_index.value = index
    dut.clut_data_r.value = r
    dut.clut_data_g.value = g
    dut.clut_data_b.value = b
    dut.clut_we.value = 1
    await RisingEdge(dut.clk)
    dut.clut_we.value = 0
    await RisingEdge(dut.clk)


async def read_palette_entry(dut, pixel_index):
    """Read RGB888 values for a given pixel index"""
    dut.pixel_index.value = pixel_index
    await RisingEdge(dut.clk)
    r = int(dut.rgb_r_out.value)
    g = int(dut.rgb_g_out.value)
    b = int(dut.rgb_b_out.value)
    return (r, g, b)


@cocotb.test()
async def test_reset_grayscale_ramp(dut):
    """Test that palette initializes with grayscale ramp on reset"""

    clock = Clock(dut.clk, 40, units="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    # Verify grayscale ramp (0x0, 0x1, 0x2, ... 0xF)
    for i in range(PALETTE_SIZE):
        r, g, b = await read_palette_entry(dut, i)

        # Grayscale means R=G=B
        expected_value = expand_rgb444_to_rgb888(i)

        assert r == expected_value, \
            f"Index {i}: Red should be {expected_value:02X}, got {r:02X}"
        assert g == expected_value, \
            f"Index {i}: Green should be {expected_value:02X}, got {g:02X}"
        assert b == expected_value, \
            f"Index {i}: Blue should be {expected_value:02X}, got {b:02X}"


@cocotb.test()
async def test_write_single_palette_entry(dut):
    """Test writing a single palette entry"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write bright red (R=0xF, G=0x0, B=0x0) to index 5
    await write_palette_entry(dut, 5, 0xF, 0x0, 0x0)

    # Read back
    r, g, b = await read_palette_entry(dut, 5)

    assert r == 0xFF, f"Red should be 0xFF, got {r:02X}"
    assert g == 0x00, f"Green should be 0x00, got {g:02X}"
    assert b == 0x00, f"Blue should be 0x00, got {b:02X}"


@cocotb.test()
async def test_write_read_all_entries(dut):
    """Test writing and reading all 16 palette entries"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Define test colors for each index
    test_colors = [
        (0x0, 0x0, 0x0),  # 0: Black
        (0xF, 0x0, 0x0),  # 1: Red
        (0x0, 0xF, 0x0),  # 2: Green
        (0xF, 0xF, 0x0),  # 3: Yellow
        (0x0, 0x0, 0xF),  # 4: Blue
        (0xF, 0x0, 0xF),  # 5: Magenta
        (0x0, 0xF, 0xF),  # 6: Cyan
        (0xF, 0xF, 0xF),  # 7: White
        (0x8, 0x0, 0x0),  # 8: Dark red
        (0x0, 0x8, 0x0),  # 9: Dark green
        (0x0, 0x0, 0x8),  # 10: Dark blue
        (0x8, 0x8, 0x8),  # 11: Gray
        (0xA, 0x5, 0x0),  # 12: Orange-ish
        (0x5, 0xA, 0x5),  # 13: Light green-ish
        (0x3, 0x3, 0xE),  # 14: Light blue-ish
        (0xE, 0xE, 0x3),  # 15: Light yellow-ish
    ]

    # Write all entries
    for index, (r, g, b) in enumerate(test_colors):
        await write_palette_entry(dut, index, r, g, b)

    # Read all entries and verify
    for index, (expected_r, expected_g, expected_b) in enumerate(test_colors):
        r, g, b = await read_palette_entry(dut, index)

        expected_r_expanded = expand_rgb444_to_rgb888(expected_r)
        expected_g_expanded = expand_rgb444_to_rgb888(expected_g)
        expected_b_expanded = expand_rgb444_to_rgb888(expected_b)

        assert r == expected_r_expanded, \
            f"Index {index}: Red should be {expected_r_expanded:02X}, got {r:02X}"
        assert g == expected_g_expanded, \
            f"Index {index}: Green should be {expected_g_expanded:02X}, got {g:02X}"
        assert b == expected_b_expanded, \
            f"Index {index}: Blue should be {expected_b_expanded:02X}, got {b:02X}"


@cocotb.test()
async def test_rgb444_expansion(dut):
    """Test RGB444 to RGB888 bit duplication expansion"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Test all possible 4-bit values (0x0 to 0xF) for each channel
    test_values = list(range(16))

    # Test red channel
    for value in test_values:
        await write_palette_entry(dut, 0, value, 0x0, 0x0)
        r, g, b = await read_palette_entry(dut, 0)
        expected = expand_rgb444_to_rgb888(value)
        assert r == expected, \
            f"Red 0x{value:X} should expand to 0x{expected:02X}, got 0x{r:02X}"

    # Test green channel
    for value in test_values:
        await write_palette_entry(dut, 0, 0x0, value, 0x0)
        r, g, b = await read_palette_entry(dut, 0)
        expected = expand_rgb444_to_rgb888(value)
        assert g == expected, \
            f"Green 0x{value:X} should expand to 0x{expected:02X}, got 0x{g:02X}"

    # Test blue channel
    for value in test_values:
        await write_palette_entry(dut, 0, 0x0, 0x0, value)
        r, g, b = await read_palette_entry(dut, 0)
        expected = expand_rgb444_to_rgb888(value)
        assert b == expected, \
            f"Blue 0x{value:X} should expand to 0x{expected:02X}, got 0x{b:02X}"


@cocotb.test()
async def test_expansion_edge_cases(dut):
    """Test specific RGB444 expansion edge cases"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Test specific important values
    edge_cases = [
        (0x0, 0x00),  # Min value: 0x0 -> 0x00
        (0xF, 0xFF),  # Max value: 0xF -> 0xFF
        (0x8, 0x88),  # Middle value: 0x8 -> 0x88
        (0x1, 0x11),  # Low value: 0x1 -> 0x11
        (0xA, 0xAA),  # 0xA -> 0xAA
        (0x5, 0x55),  # 0x5 -> 0x55
    ]

    for rgb444, expected_rgb888 in edge_cases:
        # Write to all channels
        await write_palette_entry(dut, 0, rgb444, rgb444, rgb444)
        r, g, b = await read_palette_entry(dut, 0)

        assert r == expected_rgb888, \
            f"0x{rgb444:X} -> 0x{expected_rgb888:02X} (Red), got 0x{r:02X}"
        assert g == expected_rgb888, \
            f"0x{rgb444:X} -> 0x{expected_rgb888:02X} (Green), got 0x{g:02X}"
        assert b == expected_rgb888, \
            f"0x{rgb444:X} -> 0x{expected_rgb888:02X} (Blue), got 0x{b:02X}"


@cocotb.test()
async def test_invalid_index_masking(dut):
    """Test that index values > 15 are masked to 0-15"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write unique colors to indices 0-15
    for i in range(16):
        await write_palette_entry(dut, i, i, i, i)

    # Test invalid write indices (should wrap to 0-15)
    invalid_indices = [
        (16, 0),   # 0x10 & 0xF = 0x0
        (17, 1),   # 0x11 & 0xF = 0x1
        (31, 15),  # 0x1F & 0xF = 0xF
        (32, 0),   # 0x20 & 0xF = 0x0
        (255, 15), # 0xFF & 0xF = 0xF
    ]

    for invalid_index, masked_index in invalid_indices:
        # Write a distinctive color (0xF, 0xA, 0x5) using invalid index
        await write_palette_entry(dut, invalid_index, 0xF, 0xA, 0x5)

        # Read using the masked index - should get the color we just wrote
        r, g, b = await read_palette_entry(dut, masked_index)

        assert r == 0xFF, \
            f"Index {invalid_index} (masked to {masked_index}): Red should be 0xFF, got {r:02X}"
        assert g == 0xAA, \
            f"Index {invalid_index} (masked to {masked_index}): Green should be 0xAA, got {g:02X}"
        assert b == 0x55, \
            f"Index {invalid_index} (masked to {masked_index}): Blue should be 0x55, got {b:02X}"


@cocotb.test()
async def test_invalid_pixel_index_masking(dut):
    """Test that pixel_index values > 15 are masked during lookup"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write distinctive colors to some palette entries
    await write_palette_entry(dut, 0, 0x1, 0x2, 0x3)
    await write_palette_entry(dut, 5, 0x5, 0x6, 0x7)
    await write_palette_entry(dut, 15, 0xE, 0xD, 0xC)

    # Test invalid pixel indices during read
    invalid_pixel_reads = [
        (16, 0),   # Should read from index 0
        (21, 5),   # Should read from index 5
        (31, 15),  # Should read from index 15
        (255, 15), # Should read from index 15
    ]

    for invalid_pixel_index, masked_index in invalid_pixel_reads:
        # First read the expected value using valid index
        expected_r, expected_g, expected_b = await read_palette_entry(dut, masked_index)

        # Now read using invalid index
        r, g, b = await read_palette_entry(dut, invalid_pixel_index)

        assert r == expected_r, \
            f"Pixel index {invalid_pixel_index} (masked to {masked_index}): Red mismatch"
        assert g == expected_g, \
            f"Pixel index {invalid_pixel_index} (masked to {masked_index}): Green mismatch"
        assert b == expected_b, \
            f"Pixel index {invalid_pixel_index} (masked to {masked_index}): Blue mismatch"


@cocotb.test()
async def test_rapid_palette_updates(dut):
    """Test writing multiple palette entries in rapid succession"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Rapidly write all 16 entries back-to-back
    rapid_colors = []
    for i in range(16):
        r = (i * 3) & 0xF
        g = (i * 5) & 0xF
        b = (i * 7) & 0xF
        rapid_colors.append((r, g, b))
        await write_palette_entry(dut, i, r, g, b)

    # Verify all entries were written correctly
    for index, (expected_r, expected_g, expected_b) in enumerate(rapid_colors):
        r, g, b = await read_palette_entry(dut, index)

        expected_r_expanded = expand_rgb444_to_rgb888(expected_r)
        expected_g_expanded = expand_rgb444_to_rgb888(expected_g)
        expected_b_expanded = expand_rgb444_to_rgb888(expected_b)

        assert r == expected_r_expanded, \
            f"Rapid update index {index}: Red should be {expected_r_expanded:02X}, got {r:02X}"
        assert g == expected_g_expanded, \
            f"Rapid update index {index}: Green should be {expected_g_expanded:02X}, got {g:02X}"
        assert b == expected_b_expanded, \
            f"Rapid update index {index}: Blue should be {expected_b_expanded:02X}, got {b:02X}"


@cocotb.test()
async def test_interleaved_read_write(dut):
    """Test interleaving palette writes and reads"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write index 0
    await write_palette_entry(dut, 0, 0xA, 0xB, 0xC)

    # Read index 0
    r, g, b = await read_palette_entry(dut, 0)
    assert r == 0xAA and g == 0xBB and b == 0xCC

    # Write index 3
    await write_palette_entry(dut, 3, 0x1, 0x2, 0x3)

    # Read index 0 again (should be unchanged)
    r, g, b = await read_palette_entry(dut, 0)
    assert r == 0xAA and g == 0xBB and b == 0xCC

    # Read index 3
    r, g, b = await read_palette_entry(dut, 3)
    assert r == 0x11 and g == 0x22 and b == 0x33

    # Write index 0 again with new color
    await write_palette_entry(dut, 0, 0xD, 0xE, 0xF)

    # Read both
    r, g, b = await read_palette_entry(dut, 0)
    assert r == 0xDD and g == 0xEE and b == 0xFF

    r, g, b = await read_palette_entry(dut, 3)
    assert r == 0x11 and g == 0x22 and b == 0x33


@cocotb.test()
async def test_overwrite_palette_entry(dut):
    """Test overwriting the same palette entry multiple times"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write initial color to index 7
    await write_palette_entry(dut, 7, 0x1, 0x2, 0x3)
    r, g, b = await read_palette_entry(dut, 7)
    assert r == 0x11 and g == 0x22 and b == 0x33

    # Overwrite with second color
    await write_palette_entry(dut, 7, 0x4, 0x5, 0x6)
    r, g, b = await read_palette_entry(dut, 7)
    assert r == 0x44 and g == 0x55 and b == 0x66

    # Overwrite with third color
    await write_palette_entry(dut, 7, 0xE, 0xD, 0xC)
    r, g, b = await read_palette_entry(dut, 7)
    assert r == 0xEE and g == 0xDD and b == 0xCC


@cocotb.test()
async def test_write_enable_control(dut):
    """Test that writes only occur when clut_we is asserted"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write a known color to index 2
    await write_palette_entry(dut, 2, 0x7, 0x8, 0x9)
    r, g, b = await read_palette_entry(dut, 2)
    assert r == 0x77 and g == 0x88 and b == 0x99

    # Set up write data but don't assert clut_we
    dut.clut_index.value = 2
    dut.clut_data_r.value = 0xF
    dut.clut_data_g.value = 0xE
    dut.clut_data_b.value = 0xD
    dut.clut_we.value = 0  # Not asserted
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Read back - should be unchanged
    r, g, b = await read_palette_entry(dut, 2)
    assert r == 0x77, f"Write without WE should not change Red, got {r:02X}"
    assert g == 0x88, f"Write without WE should not change Green, got {g:02X}"
    assert b == 0x99, f"Write without WE should not change Blue, got {b:02X}"


@cocotb.test()
async def test_simultaneous_read_different_index(dut):
    """Test that reading one index doesn't affect reading another"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write different colors to different indices
    await write_palette_entry(dut, 0, 0x1, 0x2, 0x3)
    await write_palette_entry(dut, 8, 0xA, 0xB, 0xC)
    await write_palette_entry(dut, 15, 0xF, 0xE, 0xD)

    # Read them in different orders
    r, g, b = await read_palette_entry(dut, 8)
    assert r == 0xAA and g == 0xBB and b == 0xCC

    r, g, b = await read_palette_entry(dut, 0)
    assert r == 0x11 and g == 0x22 and b == 0x33

    r, g, b = await read_palette_entry(dut, 15)
    assert r == 0xFF and g == 0xEE and b == 0xDD

    r, g, b = await read_palette_entry(dut, 8)
    assert r == 0xAA and g == 0xBB and b == 0xCC


@cocotb.test()
async def test_partial_channel_update(dut):
    """Test updating individual color channels"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write initial color
    await write_palette_entry(dut, 5, 0x3, 0x6, 0x9)
    r, g, b = await read_palette_entry(dut, 5)
    assert r == 0x33 and g == 0x66 and b == 0x99

    # Update only red (but all channels are written)
    await write_palette_entry(dut, 5, 0xC, 0x6, 0x9)
    r, g, b = await read_palette_entry(dut, 5)
    assert r == 0xCC and g == 0x66 and b == 0x99

    # Update only green
    await write_palette_entry(dut, 5, 0xC, 0xA, 0x9)
    r, g, b = await read_palette_entry(dut, 5)
    assert r == 0xCC and g == 0xAA and b == 0x99

    # Update only blue
    await write_palette_entry(dut, 5, 0xC, 0xA, 0x2)
    r, g, b = await read_palette_entry(dut, 5)
    assert r == 0xCC and g == 0xAA and b == 0x22


@cocotb.test()
async def test_reset_clears_custom_palette(dut):
    """Test that reset restores default grayscale ramp"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write custom colors to all entries
    for i in range(16):
        await write_palette_entry(dut, i, 0xF, 0x0, 0x0)  # All red

    # Verify custom colors are set
    r, g, b = await read_palette_entry(dut, 5)
    assert r == 0xFF and g == 0x00 and b == 0x00

    # Reset
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Verify grayscale ramp is restored
    for i in range(PALETTE_SIZE):
        r, g, b = await read_palette_entry(dut, i)
        expected_value = expand_rgb444_to_rgb888(i)
        assert r == expected_value, f"After reset, index {i} red should be {expected_value:02X}"
        assert g == expected_value, f"After reset, index {i} green should be {expected_value:02X}"
        assert b == expected_value, f"After reset, index {i} blue should be {expected_value:02X}"


@cocotb.test()
async def test_zero_values(dut):
    """Test writing all-zero values (black)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write black to several indices
    for i in [0, 5, 10, 15]:
        await write_palette_entry(dut, i, 0x0, 0x0, 0x0)
        r, g, b = await read_palette_entry(dut, i)
        assert r == 0x00, f"Index {i} red should be 0x00"
        assert g == 0x00, f"Index {i} green should be 0x00"
        assert b == 0x00, f"Index {i} blue should be 0x00"


@cocotb.test()
async def test_max_values(dut):
    """Test writing all-max values (white)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write white to several indices
    for i in [1, 6, 11, 14]:
        await write_palette_entry(dut, i, 0xF, 0xF, 0xF)
        r, g, b = await read_palette_entry(dut, i)
        assert r == 0xFF, f"Index {i} red should be 0xFF"
        assert g == 0xFF, f"Index {i} green should be 0xFF"
        assert b == 0xFF, f"Index {i} blue should be 0xFF"


@cocotb.test()
async def test_independent_palette_entries(dut):
    """Test that palette entries are independent and don't interfere"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write unique patterns to each entry
    patterns = []
    for i in range(16):
        r = (i & 0x1) * 0xF
        g = ((i >> 1) & 0x1) * 0xF
        b = ((i >> 2) & 0x1) * 0xF
        patterns.append((r, g, b))
        await write_palette_entry(dut, i, r, g, b)

    # Read all entries and verify they're all independent
    for i in range(16):
        r, g, b = await read_palette_entry(dut, i)
        expected_r = expand_rgb444_to_rgb888(patterns[i][0])
        expected_g = expand_rgb444_to_rgb888(patterns[i][1])
        expected_b = expand_rgb444_to_rgb888(patterns[i][2])

        assert r == expected_r, f"Index {i} red independence test failed"
        assert g == expected_g, f"Index {i} green independence test failed"
        assert b == expected_b, f"Index {i} blue independence test failed"


@cocotb.test()
async def test_read_without_prior_write(dut):
    """Test reading an entry immediately after reset (default grayscale)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Read without any prior writes (should get grayscale ramp)
    for i in range(16):
        r, g, b = await read_palette_entry(dut, i)
        expected = expand_rgb444_to_rgb888(i)
        assert r == expected, f"Default index {i} red should be {expected:02X}"
        assert g == expected, f"Default index {i} green should be {expected:02X}"
        assert b == expected, f"Default index {i} blue should be {expected:02X}"


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
        rtl_dir / "peripherals" / "video" / "gpu_graphics_params.vh",
        rtl_dir / "peripherals" / "video" / "gpu_graphics_palette.v"
    ]

    # Include directory for header files
    includes = [
        rtl_dir / "peripherals" / "video"
    ]

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        includes=[str(i) for i in includes],
        toplevel="gpu_graphics_palette",
        module="test_gpu_palette",
        simulator=simulator,
        waves=True if os.getenv("WAVES") == "1" else False,
        timescale="1ns/1ps",
    )


if __name__ == "__main__":
    test_runner()
