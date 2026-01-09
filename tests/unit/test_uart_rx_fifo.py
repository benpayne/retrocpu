"""
Test suite for uart_rx_fifo.v module
Tests UART receiver with 16-byte FIFO buffer

UART Format: 8 data bits, No parity, 1 stop bit (8N1)
Baud Rate: 9600 (for more realistic back-to-back byte timing)
FIFO Depth: 16 bytes
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# UART timing constants for 9600 baud
BAUD_RATE = 9600
BIT_PERIOD_US = 1000000 / BAUD_RATE  # ~104.17 μs
BIT_PERIOD_NS = int(BIT_PERIOD_US * 1000)  # ~104167 ns


async def send_uart_byte(dut, data):
    """Send a complete UART byte on RX line"""
    # Start bit (drive low)
    dut.rx.value = 0
    await Timer(BIT_PERIOD_NS, unit="ns")

    # Send 8 data bits (LSB first)
    for i in range(8):
        bit = (data >> i) & 1
        dut.rx.value = bit
        await Timer(BIT_PERIOD_NS, unit="ns")

    # Stop bit (drive high)
    dut.rx.value = 1
    await Timer(BIT_PERIOD_NS, unit="ns")


async def read_from_fifo(dut):
    """Read one byte from FIFO by asserting rd_en"""
    # Assert rd_en for one cycle
    dut.rd_en.value = 1
    await RisingEdge(dut.clk)
    data = int(dut.rx_data.value)
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    return data


@cocotb.test()
async def test_fifo_idle_state(dut):
    """Test that FIFO is empty on startup"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.rx.value = 1  # Idle high
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # FIFO should be empty
    assert dut.fifo_empty.value == 1, "FIFO should be empty on startup"
    assert dut.rx_ready.value == 0, "rx_ready should be low when FIFO empty"
    assert dut.fifo_full.value == 0, "FIFO should not be full"


@cocotb.test()
async def test_fifo_single_byte(dut):
    """Test receiving and reading a single byte through FIFO"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.rx.value = 1
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Send byte 0xAA
    await send_uart_byte(dut, 0xAA)

    # Wait for FIFO to have data
    timeout = 0
    while dut.rx_ready.value == 0:
        await RisingEdge(dut.clk)
        timeout += 1
        assert timeout < 10000, "Timeout waiting for rx_ready"

    # FIFO should not be empty
    assert dut.fifo_empty.value == 0, "FIFO should have data"
    assert dut.rx_ready.value == 1, "rx_ready should be high"

    # Read from FIFO
    received = await read_from_fifo(dut)
    assert received == 0xAA, f"Expected 0xAA, received 0x{received:02x}"

    # FIFO should now be empty
    await RisingEdge(dut.clk)
    assert dut.fifo_empty.value == 1, "FIFO should be empty after read"
    assert dut.rx_ready.value == 0, "rx_ready should be low when FIFO empty"


@cocotb.test()
async def test_fifo_back_to_back_bytes(dut):
    """Test receiving multiple bytes back-to-back without CPU reading"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.rx.value = 1
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Send 5 bytes back-to-back (A-E)
    test_bytes = [0x41, 0x42, 0x43, 0x44, 0x45]  # 'A', 'B', 'C', 'D', 'E'

    for byte in test_bytes:
        await send_uart_byte(dut, byte)

    # Wait a bit for all bytes to be received
    await Timer(1, unit="ms")

    # FIFO should have 5 bytes
    assert dut.rx_ready.value == 1, "rx_ready should be high"
    assert dut.fifo_empty.value == 0, "FIFO should not be empty"

    # Read all 5 bytes and verify order
    for expected_byte in test_bytes:
        received = await read_from_fifo(dut)
        assert received == expected_byte, f"Expected 0x{expected_byte:02x}, received 0x{received:02x}"

    # FIFO should now be empty
    await RisingEdge(dut.clk)
    assert dut.fifo_empty.value == 1, "FIFO should be empty after reading all bytes"
    assert dut.rx_ready.value == 0, "rx_ready should be low when FIFO empty"


@cocotb.test()
async def test_fifo_full_condition(dut):
    """Test filling the FIFO to capacity (16 bytes)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.rx.value = 1
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Send 16 bytes to fill the FIFO
    test_bytes = list(range(0x30, 0x40))  # '0' to '?'

    for byte in test_bytes:
        await send_uart_byte(dut, byte)

    # Wait for all bytes to be received
    await Timer(2, unit="ms")

    # FIFO should be full
    assert dut.fifo_full.value == 1, "FIFO should be full after 16 bytes"
    assert dut.rx_ready.value == 1, "rx_ready should be high"

    # Read all 16 bytes and verify
    for expected_byte in test_bytes:
        received = await read_from_fifo(dut)
        assert received == expected_byte, f"Expected 0x{expected_byte:02x}, received 0x{received:02x}"

    # FIFO should now be empty
    await RisingEdge(dut.clk)
    assert dut.fifo_empty.value == 1, "FIFO should be empty"
    assert dut.fifo_full.value == 0, "FIFO should not be full"


@cocotb.test()
async def test_fifo_interleaved_read_write(dut):
    """Test reading and writing to FIFO simultaneously"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.rx.value = 1
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Send 3 bytes
    await send_uart_byte(dut, 0x10)
    await send_uart_byte(dut, 0x20)
    await send_uart_byte(dut, 0x30)

    # Wait for bytes to arrive
    await Timer(500, unit="us")

    # Read first byte
    received = await read_from_fifo(dut)
    assert received == 0x10, f"Expected 0x10, got 0x{received:02x}"

    # Send another byte while FIFO still has data
    await send_uart_byte(dut, 0x40)
    await Timer(500, unit="us")

    # Read remaining bytes
    assert await read_from_fifo(dut) == 0x20
    assert await read_from_fifo(dut) == 0x30
    assert await read_from_fifo(dut) == 0x40

    # FIFO should be empty
    await RisingEdge(dut.clk)
    assert dut.fifo_empty.value == 1, "FIFO should be empty"


@cocotb.test()
async def test_fifo_no_duplicates(dut):
    """
    Critical test: Verify that each received byte is stored exactly once in FIFO
    This tests that the single-cycle rx_ready pulse works correctly
    """

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.rx.value = 1
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Send unique sequence A-Z (26 bytes - will overflow FIFO if duplicates occur)
    test_bytes = list(range(0x41, 0x5B))  # 'A' to 'Z'

    for byte in test_bytes[:10]:  # Send first 10 bytes
        await send_uart_byte(dut, byte)

    # Wait for all to be received
    await Timer(2, unit="ms")

    # Read and verify - should get exactly 10 unique bytes, no duplicates
    received_bytes = []
    for _ in range(10):
        if dut.fifo_empty.value == 0:
            byte = await read_from_fifo(dut)
            received_bytes.append(byte)
        else:
            break

    assert len(received_bytes) == 10, f"Expected 10 bytes, got {len(received_bytes)}"
    assert received_bytes == test_bytes[:10], f"Bytes mismatch: {[hex(b) for b in received_bytes]}"

    # FIFO should be empty
    assert dut.fifo_empty.value == 1, "FIFO should be empty after reading all bytes"


@cocotb.test()
async def test_fifo_concurrent_read_write_realistic(dut):
    """
    Test realistic scenario: Send 16 bytes back-to-back while CPU polls and reads
    Simulates CPU behavior:
    1. Poll rx_ready flag (FIFO not empty)
    2. Small random delay (simulating instruction cycles)
    3. Read data register (rd_en pulse)
    4. Repeat

    This tests for race conditions between FIFO write and read operations
    """
    import random

    clock = Clock(dut.clk, 40, unit="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.rx.value = 1
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Test data - 16 bytes (will fill FIFO exactly)
    test_bytes = list(range(0x41, 0x51))  # 'A' to 'P' (16 bytes)
    received_bytes = []

    # Async task: Send all bytes back-to-back
    async def send_bytes():
        """Send all test bytes continuously"""
        for byte in test_bytes:
            await send_uart_byte(dut, byte)
            dut._log.info(f"Sent byte 0x{byte:02x}")

    # Async task: Read bytes as they arrive (simulating CPU polling)
    async def read_bytes():
        """Poll for data and read with realistic delays"""
        bytes_read = 0
        # At 9600 baud, each byte takes ~1.04ms to transmit
        # For 16 bytes: 16 * 1.04ms = 16.6ms = 16,600,000ns
        # At 25MHz clock (40ns period): 16,600,000ns / 40ns = 415,000 clocks
        # Add margin for CPU delays and safety
        max_iterations = 500000
        iterations = 0

        while bytes_read < len(test_bytes) and iterations < max_iterations:
            iterations += 1

            # Poll rx_ready (check if FIFO not empty)
            if dut.rx_ready.value == 1:
                # Simulate CPU instruction delay between seeing flag and reading
                # Random delay: 2-20 clock cycles (simulates instruction overhead)
                delay_cycles = random.randint(2, 20)
                for _ in range(delay_cycles):
                    await RisingEdge(dut.clk)

                # Read from FIFO
                dut.rd_en.value = 1
                await RisingEdge(dut.clk)
                data = int(dut.rx_data.value)
                dut.rd_en.value = 0

                received_bytes.append(data)
                bytes_read += 1
                dut._log.info(f"Read byte #{bytes_read}: 0x{data:02x} after {delay_cycles} cycle delay")

                # Small delay before next poll (simulating other CPU work)
                for _ in range(random.randint(1, 5)):
                    await RisingEdge(dut.clk)
            else:
                # FIFO empty, wait one cycle before polling again
                await RisingEdge(dut.clk)

        if iterations >= max_iterations:
            dut._log.error(f"Timeout: only read {bytes_read}/{len(test_bytes)} bytes")

    # Run sender and reader concurrently
    send_task = cocotb.start_soon(send_bytes())
    read_task = cocotb.start_soon(read_bytes())

    # Wait for both to complete
    await send_task
    dut._log.info("All bytes sent")

    await read_task
    dut._log.info("All bytes read")

    # Verify all bytes received correctly in order
    assert len(received_bytes) == len(test_bytes), \
        f"Expected {len(test_bytes)} bytes, got {len(received_bytes)}"

    for i, (expected, received) in enumerate(zip(test_bytes, received_bytes)):
        assert received == expected, \
            f"Byte {i}: expected 0x{expected:02x}, got 0x{received:02x}"

    dut._log.info(f"SUCCESS: All {len(test_bytes)} bytes received correctly in order")

    # FIFO should be empty
    await RisingEdge(dut.clk)
    assert dut.fifo_empty.value == 1, "FIFO should be empty after reading all bytes"


# cocotb test configuration
def test_runner():
    """pytest entry point for running cocotb tests"""
    import os
    from pathlib import Path

    # Get project root
    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    # RTL sources - FIFO depends on uart_rx
    verilog_sources = [
        rtl_dir / "peripherals" / "uart" / "uart_rx.v",
        rtl_dir / "peripherals" / "uart" / "uart_rx_fifo.v"
    ]

    # Parameters
    parameters = {
        "CLK_FREQ": 25000000,  # 25 MHz
        "BAUD_RATE": 9600,      # 9600 baud for realistic back-to-back timing
        "FIFO_DEPTH": 16        # 16-byte FIFO
    }

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="uart_rx_fifo",
        module="test_uart_rx_fifo",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
        timescale="1ns/1ps",
    )


if __name__ == "__main__":
    test_runner()
