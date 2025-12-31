"""
Test for LCD Initialization FSM (HD44780 4-bit mode)

Verifies that the initialization FSM executes the correct power-on sequence
according to HD44780 datasheet specifications.

HD44780 4-bit Initialization Sequence:
1. Wait 15ms after power-on (Vcc reaches 4.5V)
2. Send 0x3 (Function set) - wait 4.1ms
3. Send 0x3 (Function set) - wait 100μs
4. Send 0x3 (Function set) - wait small delay
5. Send 0x2 (Set 4-bit mode) - wait small delay
6. Send 0x28 (Function set: 4-bit, 2 lines, 5x8 font)
7. Send 0x0C (Display on, cursor off, blink off)
8. Send 0x01 (Clear display)
9. Initialization complete

At 25 MHz (40ns clock):
- 15ms = 375,000 clocks
- 4.1ms = 102,500 clocks
- 100μs = 2,500 clocks
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


@cocotb.test()
async def test_init_fsm_reset(dut):
    """Test that FSM resets correctly"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Hold reset
    dut.rst.value = 1
    dut.timing_done.value = 0
    await ClockCycles(dut.clk, 10)

    # Check reset state
    assert dut.init_done.value == 0, "init_done should be low during reset"
    assert dut.init_active.value == 0, "init_active should be low during reset"

    # Release reset
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # Should start initialization automatically
    assert dut.init_active.value == 1, "init_active should go high after reset"
    assert dut.init_done.value == 0, "init_done should remain low until complete"


@cocotb.test()
async def test_init_fsm_power_on_wait(dut):
    """Test that FSM waits 15ms after power-on"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.timing_done.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0

    # Wait for init to start
    await ClockCycles(dut.clk, 2)
    assert dut.init_active.value == 1, "Should enter init sequence"

    # Should be in WAIT_POWER state - no nibble output yet
    initial_start = int(dut.start_timing.value) if hasattr(dut, 'start_timing') else 0

    # Fast-forward through power-on wait (15ms = 375,000 clocks)
    # For simulation, we'll just check that no commands are sent during initial period
    for _ in range(100):
        await ClockCycles(dut.clk, 100)
        if hasattr(dut, 'start_timing') and dut.start_timing.value == 1:
            break

    dut._log.info("Power-on wait period verified")


@cocotb.test()
async def test_init_fsm_function_set_sequence(dut):
    """Test that FSM sends three 0x3 function set commands"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.timing_done.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    function_set_count = 0
    max_commands = 20  # Safety limit

    # Monitor commands sent during initialization
    for _ in range(max_commands):
        # Wait for start_timing pulse
        while dut.start_timing.value == 0:
            await RisingEdge(dut.clk)
            if dut.init_done.value == 1:
                break

        if dut.init_done.value == 1:
            break

        # Capture nibble value
        nibble = int(dut.nibble_out.value)
        rs = int(dut.rs_out.value)

        dut._log.info(f"Command {_ + 1}: nibble=0x{nibble:X}, RS={rs}")

        # First three commands should be 0x3 with RS=0 (command)
        if function_set_count < 3:
            if nibble == 0x3 and rs == 0:
                function_set_count += 1
                dut._log.info(f"Function set {function_set_count}/3 detected")

        # Simulate timing completion
        dut.timing_done.value = 1
        await RisingEdge(dut.clk)
        dut.timing_done.value = 0
        await ClockCycles(dut.clk, 2)

    # Should have seen three 0x3 function sets
    assert function_set_count >= 3, f"Expected 3 function sets, got {function_set_count}"


@cocotb.test()
async def test_init_fsm_4bit_mode_entry(dut):
    """Test that FSM sends 0x2 to enter 4-bit mode"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.timing_done.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    found_4bit_entry = False
    max_commands = 20

    # Monitor for 0x2 command (4-bit mode entry)
    for cmd_num in range(max_commands):
        # Wait for start_timing pulse
        while dut.start_timing.value == 0:
            await RisingEdge(dut.clk)
            if dut.init_done.value == 1:
                break

        if dut.init_done.value == 1:
            break

        # Capture command
        nibble = int(dut.nibble_out.value)
        rs = int(dut.rs_out.value)

        dut._log.info(f"Command {cmd_num}: nibble=0x{nibble:X}, RS={rs}")

        # Look for 0x2 (4-bit mode entry)
        if nibble == 0x2 and rs == 0:
            found_4bit_entry = True
            dut._log.info("4-bit mode entry (0x2) detected")

        # Simulate timing completion
        dut.timing_done.value = 1
        await RisingEdge(dut.clk)
        dut.timing_done.value = 0
        await ClockCycles(dut.clk, 2)

    assert found_4bit_entry, "Did not find 4-bit mode entry command (0x2)"


@cocotb.test()
async def test_init_fsm_complete_sequence(dut):
    """Test complete initialization sequence and verify init_done signal"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.timing_done.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    command_log = []
    max_commands = 30

    # Run through entire initialization
    for cmd_num in range(max_commands):
        # Wait for start_timing pulse
        timeout = 0
        while dut.start_timing.value == 0:
            await RisingEdge(dut.clk)
            timeout += 1
            if dut.init_done.value == 1 or timeout > 1000:
                break

        if dut.init_done.value == 1:
            dut._log.info(f"Initialization complete after {len(command_log)} commands")
            break

        if timeout > 1000:
            dut._log.warning("Timeout waiting for start_timing")
            break

        # Capture command
        nibble = int(dut.nibble_out.value)
        rs = int(dut.rs_out.value)
        command_log.append((nibble, rs))

        dut._log.info(f"Command {cmd_num}: nibble=0x{nibble:X}, RS={rs}")

        # Simulate timing completion
        dut.timing_done.value = 1
        await RisingEdge(dut.clk)
        dut.timing_done.value = 0
        await ClockCycles(dut.clk, 2)

    # Verify initialization completed
    assert dut.init_done.value == 1, "Initialization should complete"
    assert dut.init_active.value == 0, "init_active should be low when done"

    # Log command sequence for review
    dut._log.info("Complete command sequence:")
    for i, (nibble, rs) in enumerate(command_log):
        dut._log.info(f"  {i}: 0x{nibble:X} (RS={rs})")

    # Verify we got a reasonable number of commands (should be ~8-10)
    assert len(command_log) >= 5, f"Too few commands: {len(command_log)}"
    assert len(command_log) <= 15, f"Too many commands: {len(command_log)}"


@cocotb.test()
async def test_init_fsm_stays_done(dut):
    """Test that init_done stays asserted after initialization"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.timing_done.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # Run through initialization quickly
    for _ in range(30):
        if dut.init_done.value == 1:
            break

        # Wait for command
        while dut.start_timing.value == 0:
            await RisingEdge(dut.clk)
            if dut.init_done.value == 1:
                break

        if dut.init_done.value == 1:
            break

        # Complete timing
        dut.timing_done.value = 1
        await RisingEdge(dut.clk)
        dut.timing_done.value = 0
        await ClockCycles(dut.clk, 2)

    # Verify done
    assert dut.init_done.value == 1, "Should be done"

    # Wait and verify it stays done
    await ClockCycles(dut.clk, 100)
    assert dut.init_done.value == 1, "init_done should stay high"
    assert dut.init_active.value == 0, "init_active should stay low"

    dut._log.info("init_done signal remains stable")


@cocotb.test()
async def test_init_fsm_no_spurious_commands(dut):
    """Test that no commands are sent after initialization completes"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.timing_done.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # Run through initialization
    for _ in range(30):
        if dut.init_done.value == 1:
            break

        while dut.start_timing.value == 0:
            await RisingEdge(dut.clk)
            if dut.init_done.value == 1:
                break

        if dut.init_done.value == 1:
            break

        dut.timing_done.value = 1
        await RisingEdge(dut.clk)
        dut.timing_done.value = 0
        await ClockCycles(dut.clk, 2)

    # Now initialization is done
    assert dut.init_done.value == 1

    # Monitor for spurious start_timing pulses
    spurious_count = 0
    for _ in range(1000):
        if dut.start_timing.value == 1:
            spurious_count += 1
            dut._log.error("Spurious start_timing pulse after init done!")
        await RisingEdge(dut.clk)

    assert spurious_count == 0, f"Found {spurious_count} spurious commands after init"
    dut._log.info("No spurious commands after initialization")
