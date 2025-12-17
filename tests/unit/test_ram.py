"""
Test suite for ram.v module
Tests 32KB block RAM with read/write operations

Per TDD: This test is written BEFORE the RTL implementation
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.binary import BinaryValue
import random


@cocotb.test()
async def test_ram_basic_write_read(dut):
    """Test basic write and read operations"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.data_in.value = 0
    await RisingEdge(dut.clk)

    # Write data to address 0x0000
    dut.we.value = 1
    dut.addr.value = 0x0000
    dut.data_in.value = 0x42
    await RisingEdge(dut.clk)

    # Disable write
    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Read back from address 0x0000
    dut.addr.value = 0x0000
    await RisingEdge(dut.clk)

    # Data should be available
    assert dut.data_out.value == 0x42, f"Expected 0x42, got 0x{dut.data_out.value:02x}"


@cocotb.test()
async def test_ram_multiple_addresses(dut):
    """Test writing and reading from multiple addresses"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Write test pattern to multiple addresses
    test_data = {
        0x0000: 0x11,
        0x0001: 0x22,
        0x0010: 0x33,
        0x0100: 0x44,
        0x1000: 0x55,
        0x7FFF: 0x66,  # Last address in 32KB
    }

    # Write phase
    for addr, data in test_data.items():
        dut.we.value = 1
        dut.addr.value = addr
        dut.data_in.value = data
        await RisingEdge(dut.clk)

    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Read phase
    for addr, expected in test_data.items():
        dut.addr.value = addr
        await RisingEdge(dut.clk)
        actual = int(dut.data_out.value)
        assert actual == expected, f"Address 0x{addr:04x}: expected 0x{expected:02x}, got 0x{actual:02x}"


@cocotb.test()
async def test_ram_write_enable(dut):
    """Test that write enable properly gates writes"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Write initial value
    dut.we.value = 1
    dut.addr.value = 0x0100
    dut.data_in.value = 0xAA
    await RisingEdge(dut.clk)

    # Try to write with WE disabled (should not write)
    dut.we.value = 0
    dut.addr.value = 0x0100
    dut.data_in.value = 0x55
    await RisingEdge(dut.clk)

    # Read back - should still be 0xAA
    dut.addr.value = 0x0100
    await RisingEdge(dut.clk)
    assert dut.data_out.value == 0xAA, "Write occurred with WE=0"


@cocotb.test()
async def test_ram_address_independence(dut):
    """Test that different addresses hold independent data"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Write different values to adjacent addresses
    addresses = [0x0200, 0x0201, 0x0202, 0x0203]
    values = [0x10, 0x20, 0x30, 0x40]

    for addr, val in zip(addresses, values):
        dut.we.value = 1
        dut.addr.value = addr
        dut.data_in.value = val
        await RisingEdge(dut.clk)

    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Verify each address independently
    for addr, expected in zip(addresses, values):
        dut.addr.value = addr
        await RisingEdge(dut.clk)
        assert dut.data_out.value == expected, \
            f"Address 0x{addr:04x}: expected 0x{expected:02x}, got 0x{dut.data_out.value:02x}"


@cocotb.test()
async def test_ram_sequential_access(dut):
    """Test sequential read/write pattern (typical 6502 usage)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Write sequential pattern
    base_addr = 0x0300
    for i in range(16):
        dut.we.value = 1
        dut.addr.value = base_addr + i
        dut.data_in.value = i
        await RisingEdge(dut.clk)

    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Read back sequentially
    for i in range(16):
        dut.addr.value = base_addr + i
        await RisingEdge(dut.clk)
        assert dut.data_out.value == i, \
            f"Offset {i}: expected {i}, got {dut.data_out.value}"


@cocotb.test()
async def test_ram_zero_page(dut):
    """Test zero page access (important for 6502)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Write to zero page addresses
    for addr in range(0x00, 0x10):
        dut.we.value = 1
        dut.addr.value = addr
        dut.data_in.value = addr ^ 0xFF
        await RisingEdge(dut.clk)

    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Read back
    for addr in range(0x00, 0x10):
        dut.addr.value = addr
        await RisingEdge(dut.clk)
        expected = addr ^ 0xFF
        assert dut.data_out.value == expected, \
            f"Zero page 0x{addr:02x}: expected 0x{expected:02x}, got 0x{dut.data_out.value:02x}"


@cocotb.test()
async def test_ram_stack_area(dut):
    """Test stack area access (0x0100-0x01FF)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Simulate stack operations (write backwards like 6502 stack)
    stack_pointer = 0x01FF
    stack_data = [0xAA, 0xBB, 0xCC, 0xDD]

    for data in stack_data:
        dut.we.value = 1
        dut.addr.value = stack_pointer
        dut.data_in.value = data
        await RisingEdge(dut.clk)
        stack_pointer -= 1

    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Read back (simulate stack pop)
    stack_pointer = 0x01FC
    for expected in reversed(stack_data):
        stack_pointer += 1
        dut.addr.value = stack_pointer
        await RisingEdge(dut.clk)
        assert dut.data_out.value == expected, \
            f"Stack 0x{stack_pointer:04x}: expected 0x{expected:02x}, got 0x{dut.data_out.value:02x}"


@cocotb.test()
async def test_ram_boundary_addresses(dut):
    """Test first and last addresses of 32KB range"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Test first address (0x0000)
    dut.we.value = 1
    dut.addr.value = 0x0000
    dut.data_in.value = 0x12
    await RisingEdge(dut.clk)

    # Test last address (0x7FFF for 32KB)
    dut.addr.value = 0x7FFF
    dut.data_in.value = 0x34
    await RisingEdge(dut.clk)

    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Read first address
    dut.addr.value = 0x0000
    await RisingEdge(dut.clk)
    assert dut.data_out.value == 0x12, "First address failed"

    # Read last address
    dut.addr.value = 0x7FFF
    await RisingEdge(dut.clk)
    assert dut.data_out.value == 0x34, "Last address failed"


@cocotb.test()
async def test_ram_random_access(dut):
    """Test random access pattern with random data"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Generate random test data
    random.seed(42)  # Reproducible
    test_pairs = []
    for _ in range(50):
        addr = random.randint(0x0000, 0x7FFF)
        data = random.randint(0x00, 0xFF)
        test_pairs.append((addr, data))

    # Write phase
    for addr, data in test_pairs:
        dut.we.value = 1
        dut.addr.value = addr
        dut.data_in.value = data
        await RisingEdge(dut.clk)

    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Read and verify
    errors = 0
    for addr, expected in test_pairs:
        dut.addr.value = addr
        await RisingEdge(dut.clk)
        actual = int(dut.data_out.value)
        if actual != expected:
            errors += 1
            if errors <= 5:  # Only print first 5 errors
                dut._log.error(f"Address 0x{addr:04x}: expected 0x{expected:02x}, got 0x{actual:02x}")

    assert errors == 0, f"Found {errors} errors in random access test"


# cocotb test configuration
def test_runner():
    """pytest entry point for running cocotb tests"""
    import os
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
        module="test_ram",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
    )


if __name__ == "__main__":
    test_runner()
