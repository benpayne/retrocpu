"""
Test suite for reset_controller module
Tests power-on reset and button reset with debouncing

Per TDD: This test is written BEFORE the RTL implementation
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_reset_controller_power_on(dut):
    """Test that power-on reset asserts for minimum duration"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Button is not pressed (active-low input = high)
    dut.reset_button_n.value = 1

    # Wait a few cycles
    for _ in range(5):
        await RisingEdge(dut.clk)

    # Reset should still be asserted for power-on period
    assert dut.rst.value == 1, "Reset should be asserted during power-on"

    # Wait for power-on reset to complete (should be ~100 cycles)
    reset_released = False
    for _ in range(200):
        await RisingEdge(dut.clk)
        if dut.rst.value == 0:
            reset_released = True
            break

    assert reset_released, "Reset should be released after power-on period"


@cocotb.test()
async def test_reset_controller_button_press(dut):
    """Test that button press generates reset pulse"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Button is not pressed
    dut.reset_button_n.value = 1

    # Wait for power-on reset to complete
    for _ in range(150):
        await RisingEdge(dut.clk)

    # Verify system is out of reset
    assert dut.rst.value == 0, "System should be out of reset"

    # Press button (active-low)
    dut.reset_button_n.value = 0
    await RisingEdge(dut.clk)

    # Reset should be asserted within a few cycles
    reset_asserted = False
    for _ in range(10):
        await RisingEdge(dut.clk)
        if dut.rst.value == 1:
            reset_asserted = True
            break

    assert reset_asserted, "Reset should be asserted after button press"

    # Release button
    dut.reset_button_n.value = 1

    # Wait for reset to be released
    reset_released = False
    for _ in range(200):
        await RisingEdge(dut.clk)
        if dut.rst.value == 0:
            reset_released = True
            break

    assert reset_released, "Reset should be released after button release"


@cocotb.test()
async def test_reset_controller_debounce(dut):
    """Test that button debouncing works correctly"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Button is not pressed
    dut.reset_button_n.value = 1

    # Wait for power-on reset to complete
    for _ in range(150):
        await RisingEdge(dut.clk)

    assert dut.rst.value == 0, "System should be out of reset"

    # Simulate button bouncing (rapid press/release)
    for _ in range(5):
        dut.reset_button_n.value = 0
        await RisingEdge(dut.clk)
        dut.reset_button_n.value = 1
        await RisingEdge(dut.clk)

    # Now hold button pressed
    dut.reset_button_n.value = 0

    # Wait for debounce period
    for _ in range(20):
        await RisingEdge(dut.clk)

    # Reset should now be asserted
    assert dut.rst.value == 1, "Reset should be asserted after debounce period"


@cocotb.test()
async def test_reset_controller_minimum_pulse(dut):
    """Test that reset pulse has minimum width"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Button is not pressed
    dut.reset_button_n.value = 1

    # Wait for power-on reset to complete
    for _ in range(150):
        await RisingEdge(dut.clk)

    assert dut.rst.value == 0, "System should be out of reset"

    # Press and quickly release button (1 cycle glitch)
    dut.reset_button_n.value = 0
    await RisingEdge(dut.clk)
    dut.reset_button_n.value = 1

    # Wait to see if reset is asserted
    await Timer(1, units="us")  # Wait 1 microsecond

    # Count how long reset stays asserted
    reset_cycles = 0
    if dut.rst.value == 1:
        while dut.rst.value == 1:
            await RisingEdge(dut.clk)
            reset_cycles += 1
            if reset_cycles > 200:  # Safety limit
                break

        # Reset should be asserted for at least 10 cycles
        assert reset_cycles >= 10, f"Reset pulse too short: {reset_cycles} cycles"


@cocotb.test()
async def test_reset_controller_synchronous(dut):
    """Test that reset output is synchronous to clock"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Button is not pressed
    dut.reset_button_n.value = 1

    # Wait for power-on reset
    for _ in range(150):
        await RisingEdge(dut.clk)

    # Sample reset signal at multiple points in clock cycle
    for _ in range(10):
        # Press button
        dut.reset_button_n.value = 0

        # Wait for reset assertion
        for _ in range(30):
            await RisingEdge(dut.clk)
            if dut.rst.value == 1:
                break

        # Check that reset only changes on clock edge
        rst_before = int(dut.rst.value)
        await Timer(10, units="ns")  # Wait 10 ns (mid-cycle)
        rst_mid = int(dut.rst.value)

        assert rst_before == rst_mid, "Reset should not change mid-cycle"

        # Release button
        dut.reset_button_n.value = 1

        # Wait for reset release
        for _ in range(150):
            await RisingEdge(dut.clk)
            if dut.rst.value == 0:
                break


@cocotb.test()
async def test_reset_controller_extended_press(dut):
    """Test reset behavior with extended button press"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Button is not pressed
    dut.reset_button_n.value = 1

    # Wait for power-on reset
    for _ in range(150):
        await RisingEdge(dut.clk)

    assert dut.rst.value == 0, "System should be out of reset"

    # Press button and hold for extended period
    dut.reset_button_n.value = 0

    # Wait for reset assertion
    for _ in range(30):
        await RisingEdge(dut.clk)

    assert dut.rst.value == 1, "Reset should be asserted"

    # Hold button for 100 more cycles
    for _ in range(100):
        await RisingEdge(dut.clk)
        assert dut.rst.value == 1, "Reset should stay asserted while button pressed"

    # Release button
    dut.reset_button_n.value = 1

    # Wait for reset to be released
    reset_released = False
    for _ in range(200):
        await RisingEdge(dut.clk)
        if dut.rst.value == 0:
            reset_released = True
            break

    assert reset_released, "Reset should be released after button release"


# cocotb test configuration
def test_runner():
    """pytest entry point for running cocotb tests"""
    import pytest
    import os
    from pathlib import Path

    # Get project root
    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    # RTL source
    verilog_sources = [
        rtl_dir / "system" / "reset_controller.v"
    ]

    # Parameters
    parameters = {}

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="reset_controller",
        module="test_reset_controller",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
    )


if __name__ == "__main__":
    test_runner()
