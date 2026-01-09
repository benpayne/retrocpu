"""
Unit tests for VGA Timing Generator (640x400@70Hz mode)

Tests the vga_timing_generator module to verify:
- Correct horizontal timing (640 visible, 800 total)
- Correct vertical timing (400 visible, 449 total)
- Proper sync signal generation
- Video active signal correctness
- Frame start pulse
- 70 Hz refresh rate at 25 MHz pixel clock

Author: RetroCPU Project
License: MIT
Created: 2026-01-06
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.regression import TestFactory


# VGA 640x400@70Hz timing parameters
H_VISIBLE = 640
H_FRONT = 16
H_SYNC = 96
H_BACK = 48
H_TOTAL = 800  # H_VISIBLE + H_FRONT + H_SYNC + H_BACK

V_VISIBLE = 400
V_FRONT = 12
V_SYNC = 2
V_BACK = 35
V_TOTAL = 449  # V_VISIBLE + V_FRONT + V_SYNC + V_BACK

H_SYNC_START = H_VISIBLE + H_FRONT  # 656
H_SYNC_END = H_VISIBLE + H_FRONT + H_SYNC  # 752
V_SYNC_START = V_VISIBLE + V_FRONT  # 412
V_SYNC_END = V_VISIBLE + V_FRONT + V_SYNC  # 414


@cocotb.test()
async def test_horizontal_timing(dut):
    """Test horizontal counter and timing"""

    # Start clock (25 MHz = 40ns period)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Check horizontal counter counts 0-799
    for expected in range(H_TOTAL):
        assert dut.h_count.value == expected, \
            f"h_count mismatch: expected {expected}, got {dut.h_count.value}"
        await RisingEdge(dut.clk)

    # Should wrap back to 0
    assert dut.h_count.value == 0, "h_count did not wrap to 0"


@cocotb.test()
async def test_vertical_timing(dut):
    """Test vertical counter increments at end of horizontal line"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # v_count should be 0 initially
    assert dut.v_count.value == 0, "v_count not 0 at start"

    # Wait for one complete horizontal line
    for _ in range(H_TOTAL):
        await RisingEdge(dut.clk)

    # v_count should now be 1
    assert dut.v_count.value == 1, f"v_count not 1 after one line: {dut.v_count.value}"

    # Skip ahead to near end of frame (just before v_count wraps)
    # Current v_count = 1, need to get to V_TOTAL - 1 = 448
    remaining_lines = V_TOTAL - 2  # -2 because we're at line 1, want line 448
    for _ in range(remaining_lines):
        for _ in range(H_TOTAL):
            await RisingEdge(dut.clk)

    assert dut.v_count.value == V_TOTAL - 1, \
        f"v_count not at {V_TOTAL - 1}: {dut.v_count.value}"

    # One more line should wrap to 0
    for _ in range(H_TOTAL):
        await RisingEdge(dut.clk)

    assert dut.v_count.value == 0, "v_count did not wrap to 0"


@cocotb.test()
async def test_hsync_timing(dut):
    """Test horizontal sync pulse timing"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # HSYNC is active low, so should be high (1) during visible region
    for h in range(H_SYNC_START):
        assert dut.h_count.value == h
        assert dut.hsync.value == 1, \
            f"hsync should be HIGH at h_count={h}, got {dut.hsync.value}"
        await RisingEdge(dut.clk)

    # HSYNC should go low during sync pulse
    for h in range(H_SYNC_START, H_SYNC_END):
        assert dut.h_count.value == h
        assert dut.hsync.value == 0, \
            f"hsync should be LOW at h_count={h}, got {dut.hsync.value}"
        await RisingEdge(dut.clk)

    # HSYNC should go high after sync pulse
    for h in range(H_SYNC_END, H_TOTAL):
        assert dut.h_count.value == h
        assert dut.hsync.value == 1, \
            f"hsync should be HIGH at h_count={h}, got {dut.hsync.value}"
        await RisingEdge(dut.clk)


@cocotb.test()
async def test_vsync_timing(dut):
    """Test vertical sync pulse timing"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # VSYNC is active high, so should be low (0) before sync
    assert dut.vsync.value == 0, "vsync should be LOW initially"

    # Skip to just before vsync start
    for v in range(V_SYNC_START):
        for _ in range(H_TOTAL):
            await RisingEdge(dut.clk)

    assert dut.v_count.value == V_SYNC_START
    assert dut.vsync.value == 1, f"vsync should be HIGH at v_count={V_SYNC_START}"

    # VSYNC should stay high for V_SYNC lines
    for v in range(V_SYNC):
        for _ in range(H_TOTAL):
            await RisingEdge(dut.clk)
        assert dut.vsync.value == 1, f"vsync should be HIGH at v_count={V_SYNC_START + v + 1}"

    # VSYNC should go low after sync
    assert dut.v_count.value == V_SYNC_END
    assert dut.vsync.value == 0, f"vsync should be LOW after sync at v_count={V_SYNC_END}"


@cocotb.test()
async def test_video_active(dut):
    """Test video_active signal"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # video_active should be high only when h_count < 640 AND v_count < 400

    # Test at (0, 0) - should be active
    assert dut.h_count.value == 0
    assert dut.v_count.value == 0
    assert dut.video_active.value == 1, "video_active should be HIGH at (0,0)"

    # Test at (639, 0) - should be active (last visible pixel)
    for _ in range(639):
        await RisingEdge(dut.clk)
    assert dut.h_count.value == 639
    assert dut.video_active.value == 1, "video_active should be HIGH at (639,0)"

    # Test at (640, 0) - should be inactive (first non-visible pixel)
    await RisingEdge(dut.clk)
    assert dut.h_count.value == 640
    assert dut.video_active.value == 0, "video_active should be LOW at (640,0)"

    # Skip to last visible line
    for v in range(1, V_VISIBLE):
        for _ in range(H_TOTAL):
            await RisingEdge(dut.clk)

    # At (0, 399) - should be active
    assert dut.v_count.value == V_VISIBLE - 1
    assert dut.h_count.value == 0
    assert dut.video_active.value == 1, f"video_active should be HIGH at (0,{V_VISIBLE-1})"

    # Skip one more line to (0, 400)
    for _ in range(H_TOTAL):
        await RisingEdge(dut.clk)

    assert dut.v_count.value == V_VISIBLE
    assert dut.video_active.value == 0, f"video_active should be LOW at (0,{V_VISIBLE})"


@cocotb.test()
async def test_frame_start(dut):
    """Test frame_start pulse"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # frame_start should pulse at h=0, v=0
    assert dut.h_count.value == 0
    assert dut.v_count.value == 0
    assert dut.frame_start.value == 1, "frame_start should be HIGH at (0,0)"

    # Should go low immediately
    await RisingEdge(dut.clk)
    assert dut.frame_start.value == 0, "frame_start should be LOW after first pixel"

    # Skip to end of frame
    for v in range(V_TOTAL):
        for h in range(H_TOTAL):
            if v == 0 and h == 0:
                continue  # Already tested
            await RisingEdge(dut.clk)
            assert dut.frame_start.value == 0, \
                f"frame_start should be LOW at ({h},{v})"

    # Back at (0, 0) - should pulse again
    assert dut.h_count.value == 0
    assert dut.v_count.value == 0
    assert dut.frame_start.value == 1, "frame_start should pulse again at (0,0)"


@cocotb.test()
async def test_refresh_rate(dut):
    """Test that refresh rate is approximately 70 Hz"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # One frame = H_TOTAL × V_TOTAL pixels = 800 × 449 = 359,200 pixels
    # At 25 MHz pixel clock: 359,200 / 25,000,000 = 14.368 ms per frame
    # Refresh rate = 1 / 0.014368 = 69.6 Hz ≈ 70 Hz

    frame_pixels = H_TOTAL * V_TOTAL
    pixel_time_ns = 40  # 25 MHz = 40ns per pixel
    frame_time_ns = frame_pixels * pixel_time_ns

    # Expected: 359,200 * 40 = 14,368,000 ns = 14.368 ms
    expected_frame_time = 14368000  # nanoseconds

    # Measure actual frame time by counting clocks between frame_start pulses
    start_time = cocotb.utils.get_sim_time(units="ns")

    # Wait for first frame_start
    while dut.frame_start.value != 1:
        await RisingEdge(dut.clk)

    # Wait for next frame_start
    await RisingEdge(dut.clk)
    while dut.frame_start.value != 1:
        await RisingEdge(dut.clk)

    end_time = cocotb.utils.get_sim_time(units="ns")
    actual_frame_time = end_time - start_time

    # Allow 1% tolerance
    tolerance = expected_frame_time * 0.01
    assert abs(actual_frame_time - expected_frame_time) < tolerance, \
        f"Frame time mismatch: expected {expected_frame_time}ns, got {actual_frame_time}ns"

    # Calculate actual refresh rate
    actual_refresh_hz = 1e9 / actual_frame_time  # Convert ns to Hz
    expected_refresh_hz = 70.087

    dut._log.info(f"Measured refresh rate: {actual_refresh_hz:.2f} Hz (expected {expected_refresh_hz:.2f} Hz)")

    # Allow 1 Hz tolerance
    assert abs(actual_refresh_hz - expected_refresh_hz) < 1.0, \
        f"Refresh rate out of tolerance: {actual_refresh_hz:.2f} Hz"


# Create test factory for parameterized tests if needed
# tf = TestFactory(test_function)
# tf.generate_tests()
