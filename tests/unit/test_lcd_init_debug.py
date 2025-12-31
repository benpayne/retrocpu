#!/usr/bin/env python3
"""
Debug LCD Initialization - Monitor init FSM states
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

@cocotb.test()
async def test_lcd_init_sequence(dut):
    """Monitor the LCD initialization FSM step by step"""

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

    dut._log.info("=== Test: LCD Init FSM Debug ===")

    # Monitor init FSM for first 500k cycles
    prev_state = None
    prev_timing_state = None

    for cycle in range(500000):
        await RisingEdge(dut.clk)

        init_state = int(dut.init_fsm_inst.state.value)
        timing_state = int(dut.timing_inst.state.value)
        init_active = int(dut.init_active.value)
        init_done = int(dut.init_done.value)
        timing_start = int(dut.timing_start.value)
        timing_busy = int(dut.timing_busy.value)
        timing_done = int(dut.timing_done.value)
        init_start_timing = int(dut.init_start_timing.value)

        # Log state transitions
        if init_state != prev_state:
            dut._log.info(f"Cycle {cycle}: Init FSM state change: {prev_state} -> {init_state}")
            dut._log.info(f"  init_active={init_active}, init_done={init_done}")
            dut._log.info(f"  init_start_timing={init_start_timing}, timing_start={timing_start}")
            dut._log.info(f"  timing_busy={timing_busy}, timing_done={timing_done}")
            prev_state = init_state

        if timing_state != prev_timing_state:
            dut._log.info(f"Cycle {cycle}: Timing state change: {prev_timing_state} -> {timing_state}")
            prev_timing_state = timing_state

        # Log any timing_start pulses
        if timing_start == 1:
            nibble = int(dut.timing_nibble.value)
            dut._log.info(f"Cycle {cycle}: timing_start pulsed! nibble=0x{nibble:X}, rs={dut.timing_rs.value}")

        # Stop if init completes
        if init_done == 1:
            dut._log.info(f"Cycle {cycle}: INIT COMPLETE!")
            break

        # Check for stuck states
        if cycle == 400000 and init_state == 1:
            dut._log.error(f"Cycle {cycle}: Still in state 1 (WAIT_POWER) after 400k cycles!")
            break

    dut._log.info(f"Final state: init_state={dut.init_fsm_inst.state.value}, "
                  f"timing_state={dut.timing_inst.state.value}")
    dut._log.info(f"Init status: active={dut.init_active.value}, done={dut.init_done.value}")
    dut._log.info("=== Test Complete ===")
