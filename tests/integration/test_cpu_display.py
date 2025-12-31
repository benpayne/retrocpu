"""
Integration test for CPU + Display Port (simplified system test)

Tests that the CPU can:
1. Boot from ROM
2. Execute instructions
3. Write to a memory-mapped display port
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


@cocotb.test()
async def test_cpu_writes_to_display(dut):
    """Test CPU executes ROM code and writes to display port"""

    # Start clock
    clock = Clock(dut.clk_25mhz, 40, unit="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    # Assert reset
    dut.reset_button_n.value = 0
    await ClockCycles(dut.clk_25mhz, 10)

    # Release reset
    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 200)  # Wait for power-on reset

    # Monitor display value for changes
    dut._log.info("=== Starting CPU Display Test ===")
    dut._log.info(f"Initial display_value: {dut.display_value.value}")

    # Wait for CPU to initialize (needs ~50 CPU clock cycles)
    await ClockCycles(dut.clk_25mhz, 10000)
    dut._log.info(f"After initialization: display_value={dut.display_value.value}")

    # Now monitor for display changes
    # The test program writes 1, 2, 3, 4 with delays
    max_cycles = 1_000_000  # 40ms at 25MHz should be plenty
    seen_values = set()

    for i in range(max_cycles):
        await RisingEdge(dut.clk_25mhz)

        # Check if display value changed
        current_val = int(dut.display_value.value)
        if current_val not in seen_values:
            seen_values.add(current_val)
            dut._log.info(f"Cycle {i}: Display changed to {current_val}")

            # If we've seen values 1, 2, 3, 4 then CPU is working!
            if {1, 2, 3, 4}.issubset(seen_values):
                dut._log.info("✓ SUCCESS: CPU executed and wrote 1,2,3,4 to display!")
                return

        # Early failure detection
        if i > 100_000 and len(seen_values) == 1:
            dut._log.error(f"✗ FAIL: Display stuck at {current_val} after 100k cycles")
            dut._log.error("CPU may not be executing or not writing to display port")
            assert False, "Display value never changed from initial value"

    # If we got here, CPU isn't working properly
    dut._log.error(f"✗ FAIL: Only saw values {seen_values} after {max_cycles} cycles")
    dut._log.error("Expected to see {1, 2, 3, 4}")
    assert False, f"CPU did not write expected sequence, only saw {seen_values}"


@cocotb.test()
async def test_reset_releases_properly(dut):
    """Test that system comes out of reset"""

    clock = Clock(dut.clk_25mhz, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Assert reset
    dut.reset_button_n.value = 0
    await ClockCycles(dut.clk_25mhz, 10)

    # Release reset
    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 200)

    # Check that we're out of reset by observing counter activity
    # If clock enable is working, we should see CPU activity
    initial_addr = int(dut.cpu_addr.value)
    await ClockCycles(dut.clk_25mhz, 1000)
    final_addr = int(dut.cpu_addr.value)

    assert initial_addr != final_addr, \
        f"CPU address never changed (stuck at {initial_addr:#06x}), CPU may not be running"
