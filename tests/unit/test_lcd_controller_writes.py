#!/usr/bin/env python3
"""
Test LCD Controller Write Operations
Simulates the hardware test scenario to see what's different from working diagnostic
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, Timer

@cocotb.test()
async def test_lcd_controller_write_sequence(dut):
    """Test writing to LCD controller like the hardware test does"""

    # Start clock
    clock = Clock(dut.clk, 40, units="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.cs.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.data_in.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 5)

    dut._log.info("=== Test: LCD Controller Write Sequence ===")

    # Wait for init to complete (15ms = 375000 cycles, but we'll just wait a bit)
    dut._log.info("Waiting for LCD init...")
    await ClockCycles(dut.clk, 500000)  # Wait for init (takes ~482k cycles)

    dut._log.info(f"After init: init_done={dut.init_fsm_inst.init_done.value}")

    # Now try to write clear command (0x01) to command register (addr=0x01)
    dut._log.info("Writing clear command (0x01) to command register (0x01)...")
    dut.cs.value = 1
    dut.we.value = 1
    dut.addr.value = 0x01  # Command register
    dut.data_in.value = 0x01  # Clear display

    # Hold for 10 cycles like hardware test
    for i in range(10):
        await RisingEdge(dut.clk)
        dut._log.info(f"Cycle {i}: cs={dut.cs.value} we={dut.we.value} "
                     f"controller_busy={dut.controller_busy.value} "
                     f"state={dut.state.value} "
                     f"start_pulse={dut.start_pulse.value} "
                     f"timing_busy={dut.timing_busy.value}")

    # Release
    dut.cs.value = 0
    dut.we.value = 0

    dut._log.info("Write released, monitoring timing module...")

    # Monitor what happens in lcd_timing
    for i in range(50):
        await RisingEdge(dut.clk)
        if i % 5 == 0:
            dut._log.info(f"Cycle {i}: timing_state={dut.timing_inst.state.value} "
                         f"timing_busy={dut.timing_busy.value} "
                         f"timing_done={dut.timing_done.value} "
                         f"lcd_e={dut.lcd_e.value} "
                         f"lcd_data={dut.lcd_data.value}")

    # Now try writing 'H' (0x48) to data register (addr=0x00)
    dut._log.info("Writing 'H' (0x48) to data register (0x00)...")
    await ClockCycles(dut.clk, 100)  # Wait a bit

    dut.cs.value = 1
    dut.we.value = 1
    dut.addr.value = 0x00  # Data register
    dut.data_in.value = 0x48  # 'H'

    for i in range(10):
        await RisingEdge(dut.clk)
        dut._log.info(f"Write H cycle {i}: start_pulse={dut.start_pulse.value}")

    dut.cs.value = 0
    dut.we.value = 0

    # Monitor timing again
    for i in range(50):
        await RisingEdge(dut.clk)
        if i % 5 == 0:
            dut._log.info(f"After H: timing_state={dut.timing_inst.state.value} "
                         f"lcd_e={dut.lcd_e.value}")

    dut._log.info("=== Test Complete ===")


@cocotb.test()
async def test_lcd_controller_busy_flag(dut):
    """Check if controller_busy is preventing writes"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.cs.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.data_in.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst.value = 0

    dut._log.info("=== Test: Controller Busy Flag ===")

    # Check busy flag over time
    for i in range(500000):
        if i % 50000 == 0:
            init_active = dut.lcd_inst.init_active.value
            timing_busy = dut.lcd_inst.timing_busy.value
            cpu_write_pending = dut.lcd_inst.cpu_write_pending.value
            controller_busy = dut.lcd_inst.controller_busy.value
            dut._log.info(f"Cycle {i}: controller_busy={controller_busy} "
                         f"(init={init_active}, timing={timing_busy}, "
                         f"pending={cpu_write_pending})")
        await RisingEdge(dut.clk)

    dut._log.info(f"Final: controller_busy={dut.lcd_inst.controller_busy.value}")
