"""
Cocotb unit tests for character_buffer.v

The character buffer is a dual-port RAM used for storing ASCII character codes
for the DVI character display. It supports both 40-column (1200 bytes) and
80-column (2400 bytes) display modes.

Tests verify:
- Dual-port RAM behavior (simultaneous read/write)
- Write and read operations
- 40-column mode addressing (0-1199)
- 80-column mode addressing (0-2399)
- Address boundary behavior
- Independent clock domain operation
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.types import Logic
import random


# Test configuration
CLK_CPU_PERIOD_NS = 20      # 50 MHz CPU clock
CLK_VIDEO_PERIOD_NS = 13    # ~74.25 MHz video clock (720p pixel clock)

# Address ranges
ADDR_40COL_MAX = 1199  # 40 chars × 30 rows
ADDR_80COL_MAX = 2399  # 80 chars × 30 rows


@cocotb.test()
async def test_basic_write_read(dut):
    """Test basic write and read operations"""

    # Start both clocks
    cocotb.start_soon(Clock(dut.clk_cpu, CLK_CPU_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.clk_video, CLK_VIDEO_PERIOD_NS, units="ns").start())

    # Initialize inputs
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    # Wait for a few cycles
    await RisingEdge(dut.clk_cpu)
    await RisingEdge(dut.clk_cpu)

    # Write ASCII 'A' (0x41) to address 0
    dut.addr_write.value = 0
    dut.data_write.value = 0x41
    dut.we.value = 1
    await RisingEdge(dut.clk_cpu)
    dut.we.value = 0

    # Wait for write to complete
    await RisingEdge(dut.clk_cpu)

    # Read back from address 0
    dut.addr_read.value = 0
    await RisingEdge(dut.clk_video)
    await RisingEdge(dut.clk_video)

    # Verify the data
    assert dut.data_read.value == 0x41, \
        f"Expected 0x41 ('A'), got 0x{dut.data_read.value.integer:02x}"

    dut._log.info("Basic write/read test passed")


@cocotb.test()
async def test_multiple_writes_reads(dut):
    """Test multiple write and read operations at different addresses"""

    # Start both clocks
    cocotb.start_soon(Clock(dut.clk_cpu, CLK_CPU_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.clk_video, CLK_VIDEO_PERIOD_NS, units="ns").start())

    # Initialize inputs
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    await RisingEdge(dut.clk_cpu)

    # Write test pattern: ASCII characters at various addresses
    test_data = {
        0: 0x41,      # 'A' at start
        100: 0x42,    # 'B' at middle
        500: 0x43,    # 'C'
        1000: 0x44,   # 'D'
        1199: 0x45,   # 'E' at 40-col boundary
    }

    # Write all test data
    for addr, data in test_data.items():
        dut.addr_write.value = addr
        dut.data_write.value = data
        dut.we.value = 1
        await RisingEdge(dut.clk_cpu)
        dut.we.value = 0
        await RisingEdge(dut.clk_cpu)

    # Read back and verify all test data
    for addr, expected_data in test_data.items():
        dut.addr_read.value = addr
        await RisingEdge(dut.clk_video)
        await RisingEdge(dut.clk_video)

        actual = dut.data_read.value.integer
        assert actual == expected_data, \
            f"Address {addr}: Expected 0x{expected_data:02x}, got 0x{actual:02x}"

        dut._log.info(f"Address {addr}: Verified 0x{expected_data:02x}")

    dut._log.info("Multiple write/read test passed")


@cocotb.test()
async def test_40col_addressing(dut):
    """Test full 40-column mode address range (0-1199)"""

    # Start both clocks
    cocotb.start_soon(Clock(dut.clk_cpu, CLK_CPU_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.clk_video, CLK_VIDEO_PERIOD_NS, units="ns").start())

    # Initialize inputs
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    await RisingEdge(dut.clk_cpu)

    # Test boundary addresses for 40-column mode
    test_addresses = [
        0,          # First address
        1,          # Second address
        39,         # End of first row
        40,         # Start of second row
        1198,       # Second to last
        1199,       # Last valid address for 40-col
    ]

    # Write test pattern
    for addr in test_addresses:
        test_value = (addr & 0xFF)  # Use address as test data (lower 8 bits)
        dut.addr_write.value = addr
        dut.data_write.value = test_value
        dut.we.value = 1
        await RisingEdge(dut.clk_cpu)
        dut.we.value = 0
        await RisingEdge(dut.clk_cpu)

    # Read back and verify
    for addr in test_addresses:
        expected_value = (addr & 0xFF)
        dut.addr_read.value = addr
        await RisingEdge(dut.clk_video)
        await RisingEdge(dut.clk_video)

        actual = dut.data_read.value.integer
        assert actual == expected_value, \
            f"40-col addr {addr}: Expected 0x{expected_value:02x}, got 0x{actual:02x}"

    dut._log.info("40-column addressing test passed")


@cocotb.test()
async def test_80col_addressing(dut):
    """Test 80-column mode address range (0-2399)"""

    # Start both clocks
    cocotb.start_soon(Clock(dut.clk_cpu, CLK_CPU_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.clk_video, CLK_VIDEO_PERIOD_NS, units="ns").start())

    # Initialize inputs
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    await RisingEdge(dut.clk_cpu)

    # Test boundary addresses for 80-column mode
    test_addresses = [
        0,          # First address
        79,         # End of first row
        80,         # Start of second row
        1200,       # Just beyond 40-col range
        1500,       # Middle of 80-col range
        2398,       # Second to last
        2399,       # Last valid address for 80-col
    ]

    # Write test pattern
    for addr in test_addresses:
        test_value = ((addr * 17) & 0xFF)  # Use formula to generate test data
        dut.addr_write.value = addr
        dut.data_write.value = test_value
        dut.we.value = 1
        await RisingEdge(dut.clk_cpu)
        dut.we.value = 0
        await RisingEdge(dut.clk_cpu)

    # Read back and verify
    for addr in test_addresses:
        expected_value = ((addr * 17) & 0xFF)
        dut.addr_read.value = addr
        await RisingEdge(dut.clk_video)
        await RisingEdge(dut.clk_video)

        actual = dut.data_read.value.integer
        assert actual == expected_value, \
            f"80-col addr {addr}: Expected 0x{expected_value:02x}, got 0x{actual:02x}"

    dut._log.info("80-column addressing test passed")


@cocotb.test()
async def test_simultaneous_read_write(dut):
    """Test simultaneous read and write operations on different ports"""

    # Start both clocks
    cocotb.start_soon(Clock(dut.clk_cpu, CLK_CPU_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.clk_video, CLK_VIDEO_PERIOD_NS, units="ns").start())

    # Initialize inputs
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    await RisingEdge(dut.clk_cpu)

    # Pre-populate some addresses with known data
    initial_data = {
        10: 0x48,   # 'H'
        20: 0x45,   # 'E'
        30: 0x4C,   # 'L'
        40: 0x4C,   # 'L'
        50: 0x4F,   # 'O'
    }

    for addr, data in initial_data.items():
        dut.addr_write.value = addr
        dut.data_write.value = data
        dut.we.value = 1
        await RisingEdge(dut.clk_cpu)
        dut.we.value = 0
        await RisingEdge(dut.clk_cpu)

    # Now test simultaneous operations:
    # Write to address 100 while reading from address 10
    dut.addr_write.value = 100
    dut.data_write.value = 0x57  # 'W'
    dut.addr_read.value = 10
    dut.we.value = 1

    # Trigger both operations
    await RisingEdge(dut.clk_cpu)
    await RisingEdge(dut.clk_video)

    # Verify read was not affected by write to different address
    await RisingEdge(dut.clk_video)
    assert dut.data_read.value == 0x48, \
        f"Read from addr 10 during write to 100: Expected 0x48, got 0x{dut.data_read.value.integer:02x}"

    dut.we.value = 0
    await RisingEdge(dut.clk_cpu)

    # Verify the write completed successfully
    dut.addr_read.value = 100
    await RisingEdge(dut.clk_video)
    await RisingEdge(dut.clk_video)
    assert dut.data_read.value == 0x57, \
        f"Read from addr 100 after write: Expected 0x57, got 0x{dut.data_read.value.integer:02x}"

    dut._log.info("Simultaneous read/write test passed")


@cocotb.test()
async def test_read_write_same_address(dut):
    """Test reading from the same address that's being written to"""

    # Start both clocks
    cocotb.start_soon(Clock(dut.clk_cpu, CLK_CPU_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.clk_video, CLK_VIDEO_PERIOD_NS, units="ns").start())

    # Initialize inputs
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    await RisingEdge(dut.clk_cpu)

    # Write initial value
    test_addr = 555
    dut.addr_write.value = test_addr
    dut.data_write.value = 0x41  # 'A'
    dut.we.value = 1
    await RisingEdge(dut.clk_cpu)
    dut.we.value = 0
    await RisingEdge(dut.clk_cpu)

    # Verify initial value
    dut.addr_read.value = test_addr
    await RisingEdge(dut.clk_video)
    await RisingEdge(dut.clk_video)
    assert dut.data_read.value == 0x41

    # Now write a new value to the same address
    dut.addr_write.value = test_addr
    dut.data_write.value = 0x42  # 'B'
    dut.we.value = 1
    await RisingEdge(dut.clk_cpu)
    dut.we.value = 0
    await RisingEdge(dut.clk_cpu)

    # Read the updated value
    dut.addr_read.value = test_addr
    await RisingEdge(dut.clk_video)
    await RisingEdge(dut.clk_video)

    # Should see the new value
    assert dut.data_read.value == 0x42, \
        f"Expected updated value 0x42, got 0x{dut.data_read.value.integer:02x}"

    dut._log.info("Read/write same address test passed")


@cocotb.test()
async def test_write_enable_control(dut):
    """Test that writes only occur when write enable is asserted"""

    # Start both clocks
    cocotb.start_soon(Clock(dut.clk_cpu, CLK_CPU_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.clk_video, CLK_VIDEO_PERIOD_NS, units="ns").start())

    # Initialize inputs
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    await RisingEdge(dut.clk_cpu)

    # Write initial value with WE enabled
    test_addr = 777
    dut.addr_write.value = test_addr
    dut.data_write.value = 0x99
    dut.we.value = 1
    await RisingEdge(dut.clk_cpu)
    dut.we.value = 0
    await RisingEdge(dut.clk_cpu)

    # Verify write succeeded
    dut.addr_read.value = test_addr
    await RisingEdge(dut.clk_video)
    await RisingEdge(dut.clk_video)
    assert dut.data_read.value == 0x99

    # Now try to write with WE disabled
    dut.addr_write.value = test_addr
    dut.data_write.value = 0xAA
    dut.we.value = 0  # Keep WE disabled
    await RisingEdge(dut.clk_cpu)
    await RisingEdge(dut.clk_cpu)

    # Read back - should still see old value
    dut.addr_read.value = test_addr
    await RisingEdge(dut.clk_video)
    await RisingEdge(dut.clk_video)

    assert dut.data_read.value == 0x99, \
        f"Write occurred without WE! Expected 0x99, got 0x{dut.data_read.value.integer:02x}"

    dut._log.info("Write enable control test passed")


@cocotb.test()
async def test_random_access_pattern(dut):
    """Test random access patterns across the buffer"""

    # Start both clocks
    cocotb.start_soon(Clock(dut.clk_cpu, CLK_CPU_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.clk_video, CLK_VIDEO_PERIOD_NS, units="ns").start())

    # Initialize inputs
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    await RisingEdge(dut.clk_cpu)

    # Generate random test data
    random.seed(12345)  # Fixed seed for reproducibility
    num_tests = 50
    test_data = {}

    # Write random data to random addresses
    for _ in range(num_tests):
        addr = random.randint(0, ADDR_80COL_MAX)
        data = random.randint(0x20, 0x7E)  # Printable ASCII range
        test_data[addr] = data

        dut.addr_write.value = addr
        dut.data_write.value = data
        dut.we.value = 1
        await RisingEdge(dut.clk_cpu)
        dut.we.value = 0
        await RisingEdge(dut.clk_cpu)

    # Verify all random writes
    errors = 0
    for addr, expected_data in test_data.items():
        dut.addr_read.value = addr
        await RisingEdge(dut.clk_video)
        await RisingEdge(dut.clk_video)

        actual = dut.data_read.value.integer
        if actual != expected_data:
            dut._log.error(f"Address {addr}: Expected 0x{expected_data:02x}, got 0x{actual:02x}")
            errors += 1

    assert errors == 0, f"Random access test had {errors} errors"
    dut._log.info(f"Random access pattern test passed ({num_tests} operations)")


@cocotb.test()
async def test_full_screen_write(dut):
    """Test writing a full screen pattern in 40-column mode"""

    # Start both clocks
    cocotb.start_soon(Clock(dut.clk_cpu, CLK_CPU_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.clk_video, CLK_VIDEO_PERIOD_NS, units="ns").start())

    # Initialize inputs
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    await RisingEdge(dut.clk_cpu)

    # Write a full screen: 40 columns × 30 rows
    cols = 40
    rows = 30

    dut._log.info(f"Writing full screen pattern ({cols}x{rows})...")

    # Write pattern: alternating 'A' and 'B'
    for row in range(rows):
        for col in range(cols):
            addr = row * cols + col
            data = 0x41 if (row + col) % 2 == 0 else 0x42  # 'A' or 'B'

            dut.addr_write.value = addr
            dut.data_write.value = data
            dut.we.value = 1
            await RisingEdge(dut.clk_cpu)
            dut.we.value = 0

    dut._log.info("Full screen written, verifying...")

    # Verify the pattern by spot-checking various locations
    test_positions = [
        (0, 0),      # Top-left
        (0, 39),     # Top-right
        (15, 20),    # Middle
        (29, 0),     # Bottom-left
        (29, 39),    # Bottom-right
    ]

    for row, col in test_positions:
        addr = row * cols + col
        expected = 0x41 if (row + col) % 2 == 0 else 0x42

        dut.addr_read.value = addr
        await RisingEdge(dut.clk_video)
        await RisingEdge(dut.clk_video)

        actual = dut.data_read.value.integer
        assert actual == expected, \
            f"Position ({row},{col}): Expected 0x{expected:02x}, got 0x{actual:02x}"

    dut._log.info("Full screen write test passed")


@cocotb.test()
async def test_clock_domain_crossing(dut):
    """Test that the dual-port RAM works correctly with different clock domains"""

    # Start both clocks at different frequencies
    cocotb.start_soon(Clock(dut.clk_cpu, CLK_CPU_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.clk_video, CLK_VIDEO_PERIOD_NS, units="ns").start())

    # Initialize inputs
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    # Wait for both clocks to stabilize
    for _ in range(5):
        await RisingEdge(dut.clk_cpu)
    for _ in range(5):
        await RisingEdge(dut.clk_video)

    # Perform interleaved writes and reads using both clocks
    test_cycles = 20

    for i in range(test_cycles):
        # Write on CPU clock
        addr = i * 10
        data = 0x30 + i  # ASCII '0', '1', '2', etc.

        dut.addr_write.value = addr
        dut.data_write.value = data
        dut.we.value = 1
        await RisingEdge(dut.clk_cpu)
        dut.we.value = 0

        # Read on video clock (different address)
        if i > 0:
            prev_addr = (i - 1) * 10
            dut.addr_read.value = prev_addr
            await RisingEdge(dut.clk_video)
            await RisingEdge(dut.clk_video)

            expected = 0x30 + (i - 1)
            actual = dut.data_read.value.integer
            assert actual == expected, \
                f"Clock domain test cycle {i}: Expected 0x{expected:02x}, got 0x{actual:02x}"

    dut._log.info("Clock domain crossing test passed")


@cocotb.test()
async def test_address_boundaries(dut):
    """Test behavior at address boundaries"""

    # Start both clocks
    cocotb.start_soon(Clock(dut.clk_cpu, CLK_CPU_PERIOD_NS, units="ns").start())
    cocotb.start_soon(Clock(dut.clk_video, CLK_VIDEO_PERIOD_NS, units="ns").start())

    # Initialize inputs
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    await RisingEdge(dut.clk_cpu)

    # Test at power-of-2 boundaries and mode boundaries
    boundary_addresses = [
        (0, 0x50),          # Start
        (255, 0x51),        # 8-bit boundary
        (256, 0x52),        # 9-bit boundary
        (511, 0x53),        #
        (512, 0x54),        # 10-bit boundary
        (1023, 0x55),       #
        (1024, 0x56),       # 11-bit boundary
        (1199, 0x57),       # 40-col end
        (1200, 0x58),       # 80-col start
        (2047, 0x59),       #
        (2048, 0x5A),       # 12-bit boundary
        (2399, 0x5B),       # 80-col end
    ]

    # Write to all boundary addresses
    for addr, data in boundary_addresses:
        dut.addr_write.value = addr
        dut.data_write.value = data
        dut.we.value = 1
        await RisingEdge(dut.clk_cpu)
        dut.we.value = 0
        await RisingEdge(dut.clk_cpu)

    # Verify all boundary addresses
    for addr, expected_data in boundary_addresses:
        dut.addr_read.value = addr
        await RisingEdge(dut.clk_video)
        await RisingEdge(dut.clk_video)

        actual = dut.data_read.value.integer
        assert actual == expected_data, \
            f"Boundary addr {addr}: Expected 0x{expected_data:02x}, got 0x{actual:02x}"

        dut._log.info(f"Boundary address {addr}: Verified 0x{expected_data:02x}")

    dut._log.info("Address boundary test passed")


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
        rtl_dir / "peripherals" / "video" / "character_buffer.v"
    ]

    # Check if source files exist
    for src in verilog_sources:
        if not src.exists():
            print(f"WARNING: Source file not found: {src}")
            print("This is expected for TDD - test will fail until module is implemented.")

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="character_buffer",
        module="test_character_buffer",
        simulator=simulator,
        waves=True if os.getenv("WAVES") == "1" else False,
        timescale="1ns/1ps",
    )


if __name__ == "__main__":
    test_runner()
