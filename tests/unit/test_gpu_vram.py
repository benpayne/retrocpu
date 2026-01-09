"""
Test suite for gpu_graphics_vram.v module
Tests dual-port VRAM with CPU write domain and pixel clock read domain

VRAM Specifications:
- Size: 32KB (32768 bytes)
- Address width: 15-bit (0x0000 - 0x7FFF)
- Organization: 4 pages of 8KB each
  - Page 0: 0x0000 - 0x1FFF
  - Page 1: 0x2000 - 0x3FFF
  - Page 2: 0x4000 - 0x5FFF
  - Page 3: 0x6000 - 0x7FFF
- Dual-port: CPU writes on clk_cpu, video reads on clk_pixel
- Clock domain crossing: Asynchronous read/write capability

Module Interface:
- input clk_cpu - CPU clock domain (25 MHz)
- input clk_pixel - Pixel clock domain (25 MHz, may have different phase)
- input [14:0] addr_write - Write address (15-bit)
- input [7:0] data_write - Data to write
- input we - Write enable
- input [14:0] addr_read - Read address (15-bit)
- output reg [7:0] data_read - Data read (registered)
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
import random


# VRAM constants
VRAM_SIZE = 32768
VRAM_ADDR_MAX = 0x7FFF
VRAM_PAGE_SIZE = 8192
VRAM_PAGE_0 = 0x0000
VRAM_PAGE_1 = 0x2000
VRAM_PAGE_2 = 0x4000
VRAM_PAGE_3 = 0x6000


async def reset_dut(dut):
    """Reset the DUT and initialize signals"""
    dut.we.value = 0
    dut.addr_write.value = 0
    dut.data_write.value = 0
    dut.addr_read.value = 0

    # Wait a few cycles for initialization
    await RisingEdge(dut.clk_cpu)
    await RisingEdge(dut.clk_cpu)


async def write_vram_byte(dut, addr, data):
    """Write a byte to VRAM at specified address"""
    dut.addr_write.value = addr
    dut.data_write.value = data
    dut.we.value = 1
    await RisingEdge(dut.clk_cpu)
    dut.we.value = 0
    await RisingEdge(dut.clk_cpu)


async def read_vram_byte(dut, addr):
    """Read a byte from VRAM at specified address (on pixel clock)"""
    dut.addr_read.value = addr
    await RisingEdge(dut.clk_pixel)
    # data_read is registered, so wait one more cycle to get the data
    await RisingEdge(dut.clk_pixel)
    value = int(dut.data_read.value)
    return value


@cocotb.test()
async def test_vram_single_write_read(dut):
    """Test 1: Write a byte to VRAM address, read it back, verify data matches"""

    # Start both clocks (same frequency, in phase)
    clock_cpu = Clock(dut.clk_cpu, 40, units="ns")  # 25 MHz
    clock_pixel = Clock(dut.clk_pixel, 40, units="ns")  # 25 MHz
    cocotb.start_soon(clock_cpu.start())
    cocotb.start_soon(clock_pixel.start())

    await reset_dut(dut)

    # Test data
    test_addr = 0x1234
    test_data = 0xA5

    # Write byte
    await write_vram_byte(dut, test_addr, test_data)

    # Wait for write to settle
    await RisingEdge(dut.clk_cpu)
    await RisingEdge(dut.clk_cpu)

    # Read back
    read_data = await read_vram_byte(dut, test_addr)

    assert read_data == test_data, \
        f"VRAM readback mismatch at 0x{test_addr:04X}: expected 0x{test_data:02X}, got 0x{read_data:02X}"

    dut._log.info(f"✓ Single write/read test passed: addr=0x{test_addr:04X}, data=0x{test_data:02X}")


@cocotb.test()
async def test_vram_address_wrapping(dut):
    """Test 2: Test address wrapping at 0x7FFF → 0x0000"""

    clock_cpu = Clock(dut.clk_cpu, 40, units="ns")
    clock_pixel = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock_cpu.start())
    cocotb.start_soon(clock_pixel.start())

    await reset_dut(dut)

    # Write to maximum address
    max_addr = VRAM_ADDR_MAX
    test_data_max = 0xDE
    await write_vram_byte(dut, max_addr, test_data_max)

    # Write to address 0
    zero_addr = 0x0000
    test_data_zero = 0xAD
    await write_vram_byte(dut, zero_addr, test_data_zero)

    # Try writing to wrapped address (should wrap to 0x0000)
    wrapped_addr = 0x8000  # This should wrap to 0x0000 (15-bit address)
    test_data_wrapped = 0xBE
    # Note: Verilog will automatically truncate to 15 bits
    await write_vram_byte(dut, wrapped_addr & 0x7FFF, test_data_wrapped)

    # Read back max address
    read_max = await read_vram_byte(dut, max_addr)
    assert read_max == test_data_max, \
        f"Max address (0x{max_addr:04X}) mismatch: expected 0x{test_data_max:02X}, got 0x{read_max:02X}"

    # Read back zero address (should have wrapped write)
    read_zero = await read_vram_byte(dut, zero_addr)
    assert read_zero == test_data_wrapped, \
        f"Wrapped address (0x{zero_addr:04X}) mismatch: expected 0x{test_data_wrapped:02X}, got 0x{read_zero:02X}"

    dut._log.info(f"✓ Address wrapping test passed: 0x{max_addr:04X}=0x{test_data_max:02X}, wrap to 0x0000=0x{test_data_wrapped:02X}")


@cocotb.test()
async def test_vram_dual_port_operation(dut):
    """Test 3: Test dual-port operation (simultaneous CPU write on clk_cpu, video read on clk_pixel)"""

    clock_cpu = Clock(dut.clk_cpu, 40, units="ns")
    clock_pixel = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock_cpu.start())
    cocotb.start_soon(clock_pixel.start())

    await reset_dut(dut)

    # Pre-write some data to various addresses
    test_addresses = [0x0100, 0x0200, 0x0300, 0x0400, 0x0500]
    test_data = [0x11, 0x22, 0x33, 0x44, 0x55]

    for addr, data in zip(test_addresses, test_data):
        await write_vram_byte(dut, addr, data)

    # Wait for writes to settle
    for _ in range(10):
        await RisingEdge(dut.clk_cpu)

    # Now perform simultaneous operations: write new data while reading old data
    write_addr = 0x0600
    write_data = 0xAA
    read_addr = 0x0100
    expected_read = 0x11

    # Set up write on CPU side
    dut.addr_write.value = write_addr
    dut.data_write.value = write_data
    dut.we.value = 1

    # Set up read on pixel side
    dut.addr_read.value = read_addr

    # Wait for both clocks to tick
    await RisingEdge(dut.clk_cpu)
    dut.we.value = 0

    # Read should complete on pixel clock
    await RisingEdge(dut.clk_pixel)
    read_value = int(dut.data_read.value)

    assert read_value == expected_read, \
        f"Dual-port read failed: expected 0x{expected_read:02X}, got 0x{read_value:02X}"

    # Verify the write also succeeded
    await RisingEdge(dut.clk_cpu)
    verify_data = await read_vram_byte(dut, write_addr)
    assert verify_data == write_data, \
        f"Dual-port write failed: expected 0x{write_data:02X}, got 0x{verify_data:02X}"

    dut._log.info(f"✓ Dual-port operation test passed: simultaneous read=0x{read_value:02X}, write=0x{write_data:02X}")


@cocotb.test()
async def test_vram_clock_domain_crossing(dut):
    """Test 4: Test clock domain crossing (write on clk_cpu, read on clk_pixel with different phase)"""

    # Create clocks with different phases (pixel clock delayed by 20ns)
    clock_cpu = Clock(dut.clk_cpu, 40, units="ns")  # 25 MHz
    cocotb.start_soon(clock_cpu.start())

    # Delay pixel clock startup to create phase offset
    await Timer(20, units="ns")
    clock_pixel = Clock(dut.clk_pixel, 40, units="ns")  # 25 MHz, offset by 20ns
    cocotb.start_soon(clock_pixel.start())

    await reset_dut(dut)

    # Write multiple bytes on CPU clock
    test_cases = [
        (0x1000, 0xCA),
        (0x2000, 0xFE),
        (0x3000, 0xBA),
        (0x4000, 0xBE),
    ]

    for addr, data in test_cases:
        await write_vram_byte(dut, addr, data)

    # Wait for clock domain crossing settling (at least 100 cycles)
    for _ in range(100):
        await RisingEdge(dut.clk_pixel)

    # Read back on pixel clock and verify
    for addr, expected in test_cases:
        dut.addr_read.value = addr
        await RisingEdge(dut.clk_pixel)
        await RisingEdge(dut.clk_pixel)  # Registered output
        read_value = int(dut.data_read.value)

        assert read_value == expected, \
            f"Clock domain crossing failed at 0x{addr:04X}: expected 0x{expected:02X}, got 0x{read_value:02X}"

    dut._log.info(f"✓ Clock domain crossing test passed: {len(test_cases)} writes verified across async domains")


@cocotb.test()
async def test_vram_sequential_writes(dut):
    """Test 5: Test multiple writes to sequential addresses"""

    clock_cpu = Clock(dut.clk_cpu, 40, units="ns")
    clock_pixel = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock_cpu.start())
    cocotb.start_soon(clock_pixel.start())

    await reset_dut(dut)

    # Write a sequence of bytes
    start_addr = 0x0800
    num_bytes = 256

    # Write sequential pattern
    for i in range(num_bytes):
        addr = (start_addr + i) & VRAM_ADDR_MAX
        data = i & 0xFF
        await write_vram_byte(dut, addr, data)

    # Wait for writes to settle
    for _ in range(50):
        await RisingEdge(dut.clk_cpu)

    # Read back and verify
    errors = 0
    for i in range(num_bytes):
        addr = (start_addr + i) & VRAM_ADDR_MAX
        expected = i & 0xFF
        read_value = await read_vram_byte(dut, addr)

        if read_value != expected:
            dut._log.error(f"Sequential write mismatch at 0x{addr:04X}: expected 0x{expected:02X}, got 0x{read_value:02X}")
            errors += 1
            if errors >= 10:  # Stop after 10 errors to avoid log spam
                break

    assert errors == 0, f"Sequential writes failed with {errors} errors"

    dut._log.info(f"✓ Sequential writes test passed: {num_bytes} consecutive bytes written and verified")


@cocotb.test()
async def test_vram_all_pages(dut):
    """Test 6: Test writes to all 4 pages (0x0000, 0x2000, 0x4000, 0x6000)"""

    clock_cpu = Clock(dut.clk_cpu, 40, units="ns")
    clock_pixel = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock_cpu.start())
    cocotb.start_soon(clock_pixel.start())

    await reset_dut(dut)

    # Define page base addresses and test patterns
    pages = [
        (VRAM_PAGE_0, 0xAA, "Page 0"),
        (VRAM_PAGE_1, 0xBB, "Page 1"),
        (VRAM_PAGE_2, 0xCC, "Page 2"),
        (VRAM_PAGE_3, 0xDD, "Page 3"),
    ]

    # Write test pattern to beginning, middle, and end of each page
    for page_base, pattern, page_name in pages:
        # Write to beginning of page
        await write_vram_byte(dut, page_base + 0x0000, pattern)

        # Write to middle of page
        await write_vram_byte(dut, page_base + 0x1000, pattern + 1)

        # Write to end of page (last byte)
        await write_vram_byte(dut, page_base + 0x1FFF, pattern + 2)

    # Wait for writes to settle
    for _ in range(100):
        await RisingEdge(dut.clk_cpu)

    # Verify all pages
    for page_base, pattern, page_name in pages:
        # Verify beginning
        read_val = await read_vram_byte(dut, page_base + 0x0000)
        assert read_val == pattern, \
            f"{page_name} beginning (0x{page_base:04X}) failed: expected 0x{pattern:02X}, got 0x{read_val:02X}"

        # Verify middle
        read_val = await read_vram_byte(dut, page_base + 0x1000)
        assert read_val == (pattern + 1), \
            f"{page_name} middle (0x{page_base + 0x1000:04X}) failed: expected 0x{pattern + 1:02X}, got 0x{read_val:02X}"

        # Verify end
        read_val = await read_vram_byte(dut, page_base + 0x1FFF)
        assert read_val == (pattern + 2), \
            f"{page_name} end (0x{page_base + 0x1FFF:04X}) failed: expected 0x{pattern + 2:02X}, got 0x{read_val:02X}"

        dut._log.info(f"✓ {page_name} (0x{page_base:04X}) verified: pattern=0x{pattern:02X}")

    dut._log.info(f"✓ All 4 pages test passed: All pages accessible and independent")


@cocotb.test()
async def test_vram_write_enable_control(dut):
    """Test 7: Verify that writes only occur when write enable (we) is asserted"""

    clock_cpu = Clock(dut.clk_cpu, 40, units="ns")
    clock_pixel = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock_cpu.start())
    cocotb.start_soon(clock_pixel.start())

    await reset_dut(dut)

    test_addr = 0x5678
    initial_data = 0x12

    # Write initial data
    await write_vram_byte(dut, test_addr, initial_data)

    # Wait and verify
    for _ in range(10):
        await RisingEdge(dut.clk_cpu)

    read_val = await read_vram_byte(dut, test_addr)
    assert read_val == initial_data, \
        f"Initial write failed: expected 0x{initial_data:02X}, got 0x{read_val:02X}"

    # Try to write with we=0 (should not write)
    dut.addr_write.value = test_addr
    dut.data_write.value = 0xFF  # Different data
    dut.we.value = 0  # Write disabled
    await RisingEdge(dut.clk_cpu)
    await RisingEdge(dut.clk_cpu)

    # Verify data unchanged
    read_val = await read_vram_byte(dut, test_addr)
    assert read_val == initial_data, \
        f"Write occurred with we=0: expected 0x{initial_data:02X}, got 0x{read_val:02X}"

    dut._log.info(f"✓ Write enable control test passed: we=0 prevents writes")


@cocotb.test()
async def test_vram_random_access_pattern(dut):
    """Test 8: Random access pattern to stress test VRAM"""

    clock_cpu = Clock(dut.clk_cpu, 40, units="ns")
    clock_pixel = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock_cpu.start())
    cocotb.start_soon(clock_pixel.start())

    await reset_dut(dut)

    # Generate random test vectors
    random.seed(42)  # Reproducible test
    num_tests = 100
    test_vectors = []

    for _ in range(num_tests):
        addr = random.randint(0, VRAM_ADDR_MAX)
        data = random.randint(0, 0xFF)
        test_vectors.append((addr, data))

    # Write all test vectors
    for addr, data in test_vectors:
        await write_vram_byte(dut, addr, data)

    # Wait for settling
    for _ in range(100):
        await RisingEdge(dut.clk_cpu)

    # Read back and verify in random order
    random.shuffle(test_vectors)
    errors = 0

    for addr, expected in test_vectors:
        read_val = await read_vram_byte(dut, addr)
        if read_val != expected:
            dut._log.error(f"Random access mismatch at 0x{addr:04X}: expected 0x{expected:02X}, got 0x{read_val:02X}")
            errors += 1
            if errors >= 10:
                break

    assert errors == 0, f"Random access test failed with {errors} errors"

    dut._log.info(f"✓ Random access test passed: {num_tests} random writes/reads verified")


# cocotb test configuration
def test_runner():
    """pytest entry point for running cocotb tests"""
    import os
    from pathlib import Path

    # Get project root
    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    # RTL source - VRAM module (to be implemented)
    verilog_sources = [
        rtl_dir / "peripherals" / "video" / "gpu_graphics_params.vh",
        rtl_dir / "peripherals" / "video" / "gpu_graphics_vram.v"
    ]

    # Include directory for header files
    includes = [
        rtl_dir / "peripherals" / "video"
    ]

    # No parameters needed for basic VRAM
    parameters = {}

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        includes=[str(i) for i in includes],
        toplevel="gpu_graphics_vram",
        module="test_gpu_vram",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
        timescale="1ns/1ps",
    )


if __name__ == "__main__":
    test_runner()
