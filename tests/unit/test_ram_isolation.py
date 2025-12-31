"""
Test RAM module in complete isolation
Tests zero page addresses specifically to verify RAM hardware works
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import os


@cocotb.test()
async def test_ram_zero_page_isolation(dut):
    """
    Direct test of RAM module with zero page addresses
    This bypasses all CPU and system logic
    """

    # Start clock with proper period
    clock = Clock(dut.clk, 40, unit="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.we.value = 0
    dut.addr.value = 0
    dut.data_in.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Test addresses from zero page boundary investigation
    test_cases = [
        (0x0000, 0x11, "$0000"),
        (0x0010, 0x22, "$0010"),
        (0x0080, 0x33, "$0080"),
        (0x00FF, 0x44, "$00FF"),
        (0x0100, 0x55, "$0100"),
        (0x0150, 0x66, "$0150"),
        (0x0200, 0x77, "$0200"),
    ]

    dut._log.info("=" * 60)
    dut._log.info("RAM ISOLATION TEST - Zero Page Boundary Investigation")
    dut._log.info("=" * 60)

    for addr, data, label in test_cases:
        # Write cycle
        dut.we.value = 1
        dut.addr.value = addr
        dut.data_in.value = data
        await RisingEdge(dut.clk)

        # Read cycle - address must be stable before we=0
        dut.we.value = 0
        dut.addr.value = addr
        await RisingEdge(dut.clk)

        # Check result (synchronous read, data available now)
        await RisingEdge(dut.clk)
        read_value = int(dut.data_out.value)

        status = "PASS ✓" if read_value == data else "FAIL ✗"
        dut._log.info(f"{label}: wrote 0x{data:02X}, read 0x{read_value:02X} - {status}")

        assert read_value == data, f"Address {label}: Expected 0x{data:02X}, got 0x{read_value:02X}"

    dut._log.info("=" * 60)
    dut._log.info("All RAM isolation tests PASSED")
    dut._log.info("=" * 60)


@cocotb.test()
async def test_ram_write_then_read_same_cycle(dut):
    """
    Test write followed immediately by read on next cycle
    This mimics 6502 zero page write timing
    """

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.we.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    dut._log.info("Testing rapid write-then-read at $0010...")

    # Write $AA to $0010
    dut.we.value = 1
    dut.addr.value = 0x0010
    dut.data_in.value = 0xAA
    await RisingEdge(dut.clk)

    # Immediately read from $0010 (same as CPU would do)
    dut.we.value = 0
    dut.addr.value = 0x0010
    await RisingEdge(dut.clk)

    # Check result
    await RisingEdge(dut.clk)
    read_value = int(dut.data_out.value)

    dut._log.info(f"Rapid write-read test: wrote 0xAA, read 0x{read_value:02X}")
    assert read_value == 0xAA, f"Expected 0xAA, got 0x{read_value:02X}"


@cocotb.test()
async def test_ram_address_bit_patterns(dut):
    """
    Test specific address bit patterns around bit 8
    This tests the exact boundary where failure occurs ($0100)
    """

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.we.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    dut._log.info("Testing address bit 8 boundary...")

    # Test addresses around the bit 8 boundary
    boundary_tests = [
        (0x00FE, 0xFE, "$00FE - bit 8 = 0"),
        (0x00FF, 0xFF, "$00FF - bit 8 = 0"),
        (0x0100, 0x01, "$0100 - bit 8 = 1"),
        (0x0101, 0x02, "$0101 - bit 8 = 1"),
    ]

    for addr, data, label in boundary_tests:
        # Write
        dut.we.value = 1
        dut.addr.value = addr
        dut.data_in.value = data
        await RisingEdge(dut.clk)

        # Read
        dut.we.value = 0
        dut.addr.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        read_value = int(dut.data_out.value)
        status = "PASS ✓" if read_value == data else "FAIL ✗"
        dut._log.info(f"{label}: wrote 0x{data:02X}, read 0x{read_value:02X} - {status}")

        assert read_value == data, f"{label}: Expected 0x{data:02X}, got 0x{read_value:02X}"


if __name__ == "__main__":
    # pytest entry point
    import sys
    from pathlib import Path

    # Get project root
    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    # RTL source
    verilog_sources = [
        rtl_dir / "memory" / "ram.v"
    ]

    # Parameters
    parameters = {
        "ADDR_WIDTH": 15,  # 32KB = 2^15 bytes
        "DATA_WIDTH": 8
    }

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="ram",
        module="test_ram_isolation",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
        timescale="1ns/1ps",
        compile_args=["-g2012"],
    )
