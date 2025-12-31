"""
Basic CPU integration test - diagnose why CPU has X values
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


@cocotb.test()
async def test_cpu_initialization(dut):
    """Test that CPU initializes and starts executing"""

    # Start clock
    clock = Clock(dut.clk_25mhz, 40, unit="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    # Assert reset
    dut.reset_button_n.value = 1  # Active-low, so 1 = not pressed
    await ClockCycles(dut.clk_25mhz, 10)

    dut._log.info("=== After 10 cycles ===")
    dut._log.info(f"system_rst: {dut.system_rst.value}")
    dut._log.info(f"cpu_clk_enable: {dut.cpu_clk_enable.value}")
    dut._log.info(f"cpu_addr: {dut.cpu_addr.value}")
    dut._log.info(f"cpu_rw: {dut.cpu_rw.value}")

    # Wait for reset to complete
    await ClockCycles(dut.clk_25mhz, 200)

    dut._log.info("=== After reset (210 cycles total) ===")
    dut._log.info(f"system_rst: {dut.system_rst.value}")
    dut._log.info(f"cpu_clk_enable: {dut.cpu_clk_enable.value}")

    # Wait for CPU clock enable
    max_wait = 1000
    for i in range(max_wait):
        await RisingEdge(dut.clk_25mhz)
        if dut.cpu_clk_enable.value == 1:
            dut._log.info(f"✓ CPU clock enabled after {i} cycles")
            break
    else:
        dut._log.error(f"✗ CPU clock never enabled after {max_wait} cycles")
        assert False, "CPU clock enable never asserted"

    # Now wait for multiple CPU clock enables so CPU can execute instructions
    cpu_cycle_count = 0
    for i in range(10000):
        await RisingEdge(dut.clk_25mhz)
        if dut.cpu_clk_enable.value == 1:
            cpu_cycle_count += 1
            if cpu_cycle_count >= 50:  # Wait for 50 CPU cycles
                break

    dut._log.info(f"Waited for {cpu_cycle_count} CPU cycles")
    dut._log.info(f"cpu_addr after {cpu_cycle_count} CPU cycles: {dut.cpu_addr.value}")

    # Check if address has valid values (not X/Z)
    addr_str = str(dut.cpu_addr.value)
    if 'x' in addr_str.lower() or 'z' in addr_str.lower():
        dut._log.error(f"✗ CPU address contains X/Z values: {addr_str}")
        dut._log.error("CPU is not initializing properly!")
        assert False, f"CPU address has invalid values: {addr_str}"
    else:
        dut._log.info(f"✓ CPU address is valid: {addr_str}")


@cocotb.test()
async def test_clock_enable_timing(dut):
    """Test that clock enable pulses correctly"""

    clock = Clock(dut.clk_25mhz, 40, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 300)  # Wait past reset

    # Count clock enables
    enable_count = 0
    for i in range(1000):
        await RisingEdge(dut.clk_25mhz)
        if dut.cpu_clk_enable.value == 1:
            enable_count += 1

    dut._log.info(f"Clock enables in 1000 cycles: {enable_count}")
    # With divider=200, we expect ~5 enables in 1000 cycles
    assert enable_count >= 3, f"Too few clock enables: {enable_count}, expected ~5"
    assert enable_count <= 8, f"Too many clock enables: {enable_count}, expected ~5"
