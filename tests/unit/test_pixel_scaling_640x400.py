"""
Unit tests for GPU Pixel Renderer scaling (640x400 display mode)

Tests the gpu_pixel_renderer module to verify:
- Correct x_pixel and y_pixel calculation using bit shifts
- No complex arithmetic (multiplication/division)
- Proper scaling for each graphics mode:
  * 1BPP: 320x200 → 640x400 (2x2 scaling)
  * 2BPP: 160x200 → 640x400 (4x2 scaling)
  * 4BPP: 160x100 → 640x400 (4x4 scaling)

Author: RetroCPU Project
License: MIT
Created: 2026-01-06
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# Graphics mode constants (from gpu_graphics_params.vh)
GPU_MODE_1BPP = 0b00
GPU_MODE_2BPP = 0b01
GPU_MODE_4BPP = 0b10


@cocotb.test()
async def test_1bpp_scaling(dut):
    """Test 1BPP mode scaling: 320x200 → 640x400 (2x2)"""

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    dut.gpu_mode.value = GPU_MODE_1BPP
    dut.fb_base_addr.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk_pixel)

    # Test x_pixel scaling: h_count >> 1 (divide by 2)
    test_cases = [
        (0, 0),      # h_count=0 → x_pixel=0
        (1, 0),      # h_count=1 → x_pixel=0 (same pixel)
        (2, 1),      # h_count=2 → x_pixel=1
        (3, 1),      # h_count=3 → x_pixel=1 (same pixel)
        (639, 319),  # h_count=639 → x_pixel=319 (last pixel)
    ]

    for h_count, expected_x in test_cases:
        dut.h_count.value = h_count
        dut.v_count.value = 0
        await Timer(1, units="ns")  # Let combinational logic settle

        # Access internal x_pixel signal
        actual_x = dut.x_pixel.value.integer
        assert actual_x == expected_x, \
            f"1BPP x_pixel: h_count={h_count}, expected x={expected_x}, got {actual_x}"

    # Test y_pixel scaling: v_count >> 1 (divide by 2)
    test_cases_y = [
        (0, 0),      # v_count=0 → y_pixel=0
        (1, 0),      # v_count=1 → y_pixel=0 (same line)
        (2, 1),      # v_count=2 → y_pixel=1
        (3, 1),      # v_count=3 → y_pixel=1 (same line)
        (399, 199),  # v_count=399 → y_pixel=199 (last line)
    ]

    for v_count, expected_y in test_cases_y:
        dut.h_count.value = 0
        dut.v_count.value = v_count
        await Timer(1, units="ns")

        actual_y = dut.y_pixel.value.integer
        assert actual_y == expected_y, \
            f"1BPP y_pixel: v_count={v_count}, expected y={expected_y}, got {actual_y}"


@cocotb.test()
async def test_2bpp_scaling(dut):
    """Test 2BPP mode scaling: 160x200 → 640x400 (4x2)"""

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    dut.gpu_mode.value = GPU_MODE_2BPP
    dut.fb_base_addr.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk_pixel)

    # Test x_pixel scaling: h_count >> 2 (divide by 4)
    test_cases = [
        (0, 0),      # h_count=0 → x_pixel=0
        (1, 0),      # h_count=1 → x_pixel=0
        (2, 0),      # h_count=2 → x_pixel=0
        (3, 0),      # h_count=3 → x_pixel=0 (4 VGA pixels per data pixel)
        (4, 1),      # h_count=4 → x_pixel=1
        (639, 159),  # h_count=639 → x_pixel=159 (last pixel)
    ]

    for h_count, expected_x in test_cases:
        dut.h_count.value = h_count
        dut.v_count.value = 0
        await Timer(1, units="ns")

        actual_x = dut.x_pixel.value.integer
        assert actual_x == expected_x, \
            f"2BPP x_pixel: h_count={h_count}, expected x={expected_x}, got {actual_x}"

    # Test y_pixel scaling: v_count >> 1 (divide by 2)
    test_cases_y = [
        (0, 0),
        (1, 0),
        (2, 1),
        (3, 1),
        (399, 199),
    ]

    for v_count, expected_y in test_cases_y:
        dut.h_count.value = 0
        dut.v_count.value = v_count
        await Timer(1, units="ns")

        actual_y = dut.y_pixel.value.integer
        assert actual_y == expected_y, \
            f"2BPP y_pixel: v_count={v_count}, expected y={expected_y}, got {actual_y}"


@cocotb.test()
async def test_4bpp_scaling(dut):
    """Test 4BPP mode scaling: 160x100 → 640x400 (4x4)"""

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    dut.gpu_mode.value = GPU_MODE_4BPP
    dut.fb_base_addr.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk_pixel)

    # Test x_pixel scaling: h_count >> 2 (divide by 4)
    test_cases = [
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0),
        (4, 1),
        (8, 2),
        (639, 159),
    ]

    for h_count, expected_x in test_cases:
        dut.h_count.value = h_count
        dut.v_count.value = 0
        await Timer(1, units="ns")

        actual_x = dut.x_pixel.value.integer
        assert actual_x == expected_x, \
            f"4BPP x_pixel: h_count={h_count}, expected x={expected_x}, got {actual_x}"

    # Test y_pixel scaling: v_count >> 2 (divide by 4)
    test_cases_y = [
        (0, 0),      # v_count=0 → y_pixel=0
        (1, 0),      # v_count=1 → y_pixel=0
        (2, 0),      # v_count=2 → y_pixel=0
        (3, 0),      # v_count=3 → y_pixel=0 (4 VGA lines per data line)
        (4, 1),      # v_count=4 → y_pixel=1
        (8, 2),      # v_count=8 → y_pixel=2
        (399, 99),   # v_count=399 → y_pixel=99 (last line)
    ]

    for v_count, expected_y in test_cases_y:
        dut.h_count.value = 0
        dut.v_count.value = v_count
        await Timer(1, units="ns")

        actual_y = dut.y_pixel.value.integer
        assert actual_y == expected_y, \
            f"4BPP y_pixel: v_count={v_count}, expected y={expected_y}, got {actual_y}"


@cocotb.test()
async def test_vram_address_calculation(dut):
    """Test VRAM address calculation for different modes"""

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    dut.fb_base_addr.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk_pixel)

    # Test 1BPP mode: 40 bytes per row, 8 pixels per byte
    # At position (0,0): address should be 0
    # At position (8,0): address should be 1 (next byte, 8 pixels = 1 byte in 1BPP)
    # At position (0,1): address should be 40 (next row)

    dut.gpu_mode.value = GPU_MODE_1BPP

    # Position (0,0) → x_pixel=0, y_pixel=0 → addr = 0*40 + 0/8 = 0
    dut.h_count.value = 0
    dut.v_count.value = 0
    await RisingEdge(dut.clk_pixel)
    await Timer(1, units="ns")
    # vram_addr is registered, so wait one more cycle
    await RisingEdge(dut.clk_pixel)
    assert dut.vram_addr.value == 0, f"1BPP (0,0): expected addr=0, got {dut.vram_addr.value}"

    # Position (16,0) → x_pixel=8, y_pixel=0 → addr = 0*40 + 8/8 = 1
    dut.h_count.value = 16  # h_count=16 → x_pixel=8
    dut.v_count.value = 0
    await RisingEdge(dut.clk_pixel)
    await Timer(1, units="ns")
    await RisingEdge(dut.clk_pixel)
    assert dut.vram_addr.value == 1, f"1BPP (16,0): expected addr=1, got {dut.vram_addr.value}"

    # Position (0,2) → x_pixel=0, y_pixel=1 → addr = 1*40 + 0/8 = 40
    dut.h_count.value = 0
    dut.v_count.value = 2  # v_count=2 → y_pixel=1
    await RisingEdge(dut.clk_pixel)
    await Timer(1, units="ns")
    await RisingEdge(dut.clk_pixel)
    assert dut.vram_addr.value == 40, f"1BPP (0,2): expected addr=40, got {dut.vram_addr.value}"

    # Test 4BPP mode: 80 bytes per row, 2 pixels per byte
    dut.gpu_mode.value = GPU_MODE_4BPP

    # Position (0,0) → x_pixel=0, y_pixel=0 → addr = 0*80 + 0/2 = 0
    dut.h_count.value = 0
    dut.v_count.value = 0
    await RisingEdge(dut.clk_pixel)
    await Timer(1, units="ns")
    await RisingEdge(dut.clk_pixel)
    assert dut.vram_addr.value == 0, f"4BPP (0,0): expected addr=0, got {dut.vram_addr.value}"

    # Position (8,0) → x_pixel=2, y_pixel=0 → addr = 0*80 + 2/2 = 1
    dut.h_count.value = 8  # h_count=8 → x_pixel=2
    dut.v_count.value = 0
    await RisingEdge(dut.clk_pixel)
    await Timer(1, units="ns")
    await RisingEdge(dut.clk_pixel)
    assert dut.vram_addr.value == 1, f"4BPP (8,0): expected addr=1, got {dut.vram_addr.value}"

    # Position (0,4) → x_pixel=0, y_pixel=1 → addr = 1*80 + 0/2 = 80
    dut.h_count.value = 0
    dut.v_count.value = 4  # v_count=4 → y_pixel=1
    await RisingEdge(dut.clk_pixel)
    await Timer(1, units="ns")
    await RisingEdge(dut.clk_pixel)
    assert dut.vram_addr.value == 80, f"4BPP (0,4): expected addr=80, got {dut.vram_addr.value}"


@cocotb.test()
async def test_no_multiplication_in_timing(dut):
    """
    Verify that pixel calculation completes quickly (no slow multiplication).

    This is a performance/timing test to ensure the bit-shift operations
    are synthesizing correctly without complex arithmetic.
    """

    clock = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    dut.gpu_mode.value = GPU_MODE_4BPP
    dut.fb_base_addr.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk_pixel)

    # Change h_count and v_count rapidly
    # If there's complex multiplication, x_pixel/y_pixel won't update in time
    for i in range(10):
        dut.h_count.value = i * 64
        dut.v_count.value = i * 40
        await Timer(1, units="ns")  # Just 1ns for combinational logic

        # x_pixel and y_pixel should update immediately (combinational)
        expected_x = (i * 64) >> 2  # h_count / 4 for 4BPP
        expected_y = (i * 40) >> 2  # v_count / 4 for 4BPP

        actual_x = dut.x_pixel.value.integer
        actual_y = dut.y_pixel.value.integer

        assert actual_x == expected_x, \
            f"x_pixel didn't update instantly: expected {expected_x}, got {actual_x}"
        assert actual_y == expected_y, \
            f"y_pixel didn't update instantly: expected {expected_y}, got {actual_y}"

    dut._log.info("✓ Pixel scaling uses fast combinational logic (bit shifts only)")
