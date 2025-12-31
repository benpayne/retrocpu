"""
Test for LCD Timing Generator (HD44780 4-bit mode)

Verifies that the timing generator produces correct enable pulses
and meets HD44780 timing requirements for 4-bit parallel interface.

HD44780 Timing Requirements:
- Enable pulse width (high): minimum 450ns
- Data setup time: minimum 80ns
- Data hold time: minimum 10ns
- Enable cycle time: minimum 1000ns

At 25 MHz clock (40ns period):
- Enable high: minimum 12 clocks (480ns) ✓
- Data setup: minimum 3 clocks (120ns) ✓
- Data hold: minimum 1 clock (40ns) ✓
- Full cycle: ~25 clocks (1000ns) ✓
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles


@cocotb.test()
async def test_timing_reset(dut):
    """Test that timing generator resets correctly"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_nibble.value = 0
    dut.rs.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # Verify idle state
    assert dut.lcd_e.value == 0, "Enable should be low after reset"
    assert dut.busy.value == 0, "Should not be busy after reset"
    assert dut.done.value == 0, "Done should be low after reset"


@cocotb.test()
async def test_timing_enable_pulse_width(dut):
    """Test that enable pulse meets minimum width requirement (450ns = 12 clocks)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_nibble.value = 0xA
    dut.rs.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # Start write cycle
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    # Wait for enable to go high
    while dut.lcd_e.value == 0:
        await RisingEdge(dut.clk)

    # Count enable high time
    enable_high_start = cocotb.utils.get_sim_time(units='ns')

    # Wait for enable to go low
    while dut.lcd_e.value == 1:
        await RisingEdge(dut.clk)

    enable_high_end = cocotb.utils.get_sim_time(units='ns')
    enable_high_time = enable_high_end - enable_high_start

    dut._log.info(f"Enable high time: {enable_high_time}ns")

    # Verify minimum width (450ns)
    assert enable_high_time >= 450, f"Enable pulse too short: {enable_high_time}ns < 450ns"


@cocotb.test()
async def test_timing_data_setup(dut):
    """Test that data is stable before enable rises (setup time ≥ 80ns = 3 clocks)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_nibble.value = 0x5
    dut.rs.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # Start write cycle
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    # Wait for busy to assert
    while dut.busy.value == 0:
        await RisingEdge(dut.clk)

    # Data should be on outputs immediately
    data_stable_start = cocotb.utils.get_sim_time(units='ns')

    # Wait for enable to rise
    while dut.lcd_e.value == 0:
        await RisingEdge(dut.clk)

    enable_rise = cocotb.utils.get_sim_time(units='ns')
    setup_time = enable_rise - data_stable_start

    dut._log.info(f"Data setup time: {setup_time}ns")

    # Verify minimum setup time (80ns)
    assert setup_time >= 80, f"Setup time too short: {setup_time}ns < 80ns"


@cocotb.test()
async def test_timing_data_hold(dut):
    """Test that data remains stable after enable falls (hold time ≥ 10ns = 1 clock)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_nibble.value = 0xF
    dut.rs.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # Start write cycle
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    # Wait for enable to go high then fall
    while dut.lcd_e.value == 0:
        await RisingEdge(dut.clk)

    while dut.lcd_e.value == 1:
        await RisingEdge(dut.clk)

    enable_fall = cocotb.utils.get_sim_time(units='ns')

    # Capture data value at enable fall
    data_at_fall = int(dut.lcd_data.value)

    # Wait one clock cycle
    await ClockCycles(dut.clk, 1)

    data_after_hold = int(dut.lcd_data.value)
    hold_end = cocotb.utils.get_sim_time(units='ns')
    hold_time = hold_end - enable_fall

    dut._log.info(f"Data hold time: {hold_time}ns")
    dut._log.info(f"Data at fall: 0x{data_at_fall:X}, after hold: 0x{data_after_hold:X}")

    # Verify data didn't change during hold period
    assert data_at_fall == data_after_hold, "Data changed during hold period"
    assert hold_time >= 10, f"Hold time too short: {hold_time}ns < 10ns"


@cocotb.test()
async def test_timing_full_cycle(dut):
    """Test complete write cycle with busy/done signaling"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    dut.data_nibble.value = 0x3
    dut.rs.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # Verify idle state
    assert dut.busy.value == 0, "Should not be busy initially"
    assert dut.done.value == 0, "Done should be low initially"

    # Start write cycle
    cycle_start = cocotb.utils.get_sim_time(units='ns')
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    # Should go busy immediately
    await RisingEdge(dut.clk)
    assert dut.busy.value == 1, "Should be busy after start"

    # Wait for done signal
    while dut.done.value == 0:
        await RisingEdge(dut.clk)

    cycle_end = cocotb.utils.get_sim_time(units='ns')
    cycle_time = cycle_end - cycle_start

    dut._log.info(f"Full cycle time: {cycle_time}ns")

    # Verify cycle meets minimum time (1000ns)
    assert cycle_time >= 1000, f"Cycle too fast: {cycle_time}ns < 1000ns"

    # Done should pulse for one clock
    await RisingEdge(dut.clk)
    assert dut.done.value == 0, "Done should be cleared after one clock"
    assert dut.busy.value == 0, "Should not be busy after done"


@cocotb.test()
async def test_timing_back_to_back(dut):
    """Test two consecutive write cycles"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.start.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # First write
    dut.data_nibble.value = 0x5
    dut.rs.value = 1
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    # Wait for first cycle to complete
    while dut.done.value == 0:
        await RisingEdge(dut.clk)

    await RisingEdge(dut.clk)

    # Verify ready for second write
    assert dut.busy.value == 0, "Should be ready for second write"

    # Second write
    dut.data_nibble.value = 0xA
    dut.rs.value = 0
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    # Wait for second cycle to complete
    while dut.done.value == 0:
        await RisingEdge(dut.clk)

    dut._log.info("Back-to-back writes completed successfully")


@cocotb.test()
async def test_timing_rs_propagation(dut):
    """Test that RS signal propagates correctly to LCD"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # Test RS=0 (command)
    dut.start.value = 0
    dut.data_nibble.value = 0x1
    dut.rs.value = 0
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    # Wait for busy
    while dut.busy.value == 0:
        await RisingEdge(dut.clk)

    assert dut.lcd_rs.value == 0, "LCD RS should be 0 for command"

    # Wait for completion
    while dut.done.value == 0:
        await RisingEdge(dut.clk)

    await ClockCycles(dut.clk, 2)

    # Test RS=1 (data)
    dut.data_nibble.value = 0x2
    dut.rs.value = 1
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    # Wait for busy
    while dut.busy.value == 0:
        await RisingEdge(dut.clk)

    assert dut.lcd_rs.value == 1, "LCD RS should be 1 for data"

    # Wait for completion
    while dut.done.value == 0:
        await RisingEdge(dut.clk)

    dut._log.info("RS signal propagation verified")
