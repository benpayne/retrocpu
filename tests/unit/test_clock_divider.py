"""
Test suite for clock_divider module
Tests the 25 MHz to 1 MHz clock divider with clock enable output

Per TDD: This test is written BEFORE the RTL implementation
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.binary import BinaryValue


@cocotb.test()
async def test_clock_divider_basic(dut):
    """Test basic clock divider functionality"""

    # Create 25 MHz clock (40 ns period)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Clock enable should be low initially
    assert dut.clk_enable.value == 0, "Clock enable should be low after reset"

    # Wait and check that clk_enable toggles
    enable_count = 0
    for _ in range(100):
        await RisingEdge(dut.clk)
        if dut.clk_enable.value == 1:
            enable_count += 1

    # Should see approximately 4 enable pulses in 100 cycles (25:1 ratio)
    assert 2 <= enable_count <= 6, f"Expected 3-5 enable pulses, got {enable_count}"


@cocotb.test()
async def test_clock_divider_ratio(dut):
    """Test that clock divider produces correct 25:1 ratio"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Count cycles between enable pulses
    enable_cycles = []
    cycle_count = 0

    for _ in range(200):
        await RisingEdge(dut.clk)
        cycle_count += 1

        if dut.clk_enable.value == 1:
            if len(enable_cycles) < 5:  # Collect 5 measurements
                enable_cycles.append(cycle_count)
                cycle_count = 0

    # Should be 25 cycles between each enable pulse
    for i, cycles in enumerate(enable_cycles):
        assert cycles == 25, f"Enable pulse {i}: expected 25 cycles, got {cycles}"


@cocotb.test()
async def test_clock_divider_pulse_width(dut):
    """Test that clock enable pulse is exactly 1 clock cycle wide"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Wait for first enable pulse
    while dut.clk_enable.value == 0:
        await RisingEdge(dut.clk)

    # Enable should be high for exactly 1 cycle
    assert dut.clk_enable.value == 1, "Enable should be high"
    await RisingEdge(dut.clk)
    assert dut.clk_enable.value == 0, "Enable should be low after 1 cycle"


@cocotb.test()
async def test_clock_divider_reset(dut):
    """Test that reset properly resets the divider counter"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    # Run for some cycles
    for _ in range(10):
        await RisingEdge(dut.clk)

    # Assert reset again
    dut.rst.value = 1
    await RisingEdge(dut.clk)

    # Clock enable should be low during reset
    assert dut.clk_enable.value == 0, "Clock enable should be low during reset"

    # Deassert reset
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Count cycles to next enable
    cycle_count = 0
    while dut.clk_enable.value == 0:
        await RisingEdge(dut.clk)
        cycle_count += 1
        assert cycle_count < 30, "Timeout waiting for enable after reset"

    # Should be close to 25 cycles (counter was reset)
    assert 23 <= cycle_count <= 26, f"Expected ~25 cycles after reset, got {cycle_count}"


@cocotb.test()
async def test_clock_divider_continuous(dut):
    """Test clock divider over extended period"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Run for 500 cycles (20 enable pulses expected)
    enable_count = 0
    for _ in range(500):
        await RisingEdge(dut.clk)
        if dut.clk_enable.value == 1:
            enable_count += 1

    # Should see 20 enable pulses (500 / 25 = 20)
    assert 18 <= enable_count <= 22, f"Expected ~20 enable pulses, got {enable_count}"


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
        rtl_dir / "system" / "clock_divider.v"
    ]

    # Parameters
    parameters = {}

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="clock_divider",
        module="test_clock_divider",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
    )


if __name__ == "__main__":
    test_runner()
