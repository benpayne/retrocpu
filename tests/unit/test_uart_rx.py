"""
Test suite for uart_rx.v module
Tests UART receiver with 115200 baud, 8N1 format

UART Format: 8 data bits, No parity, 1 stop bit (8N1)
Baud Rate: 115200 (divider = 217 from 25 MHz clock)
Bit Time: 8.68 μs (115200 baud)
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer


# UART timing constants
BAUD_RATE = 115200
BIT_PERIOD_US = 1000000 / BAUD_RATE  # ~8.68 μs
BIT_PERIOD_NS = int(BIT_PERIOD_US * 1000)  # ~8680 ns


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


@cocotb.test()
async def test_uart_rx_idle_state(dut):
    """Test that RX line idles high and no data ready"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.rx.value = 1  # Idle high
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # RX ready should be low (no data)
    assert dut.rx_ready.value == 0, "RX ready should be low when idle"

    # Wait and verify it stays low
    await Timer(10, unit="us")
    assert dut.rx_ready.value == 0, "RX ready should remain low when idle"


@cocotb.test()
async def test_uart_rx_single_byte(dut):
    """Test receiving a single byte"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.rx.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Send byte 0x55 (01010101 pattern, good test pattern)
    await send_uart_byte(dut, 0x55)

    # Wait for rx_ready pulse
    timeout = 0
    while dut.rx_ready.value == 0:
        await RisingEdge(dut.clk)
        timeout += 1
        assert timeout < 10000, "Timeout waiting for rx_ready"

    # Check received data
    received = int(dut.rx_data.value)
    assert received == 0x55, f"Expected 0x55, received 0x{received:02x}"

    # rx_ready should stay high (sticky flag until next reception)
    await RisingEdge(dut.clk)
    assert dut.rx_ready.value == 1, "rx_ready should stay high until next reception"


@cocotb.test()
async def test_uart_rx_all_zeros(dut):
    """Test receiving 0x00 (all zeros)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.rx.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Send 0x00
    await send_uart_byte(dut, 0x00)

    # Wait for rx_ready
    timeout = 0
    while dut.rx_ready.value == 0:
        await RisingEdge(dut.clk)
        timeout += 1
        assert timeout < 10000, "Timeout waiting for rx_ready"

    received = int(dut.rx_data.value)
    assert received == 0x00, f"Expected 0x00, received 0x{received:02x}"


@cocotb.test()
async def test_uart_rx_all_ones(dut):
    """Test receiving 0xFF (all ones)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.rx.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Send 0xFF
    await send_uart_byte(dut, 0xFF)

    # Wait for rx_ready
    timeout = 0
    while dut.rx_ready.value == 0:
        await RisingEdge(dut.clk)
        timeout += 1
        assert timeout < 10000, "Timeout waiting for rx_ready"

    received = int(dut.rx_data.value)
    assert received == 0xFF, f"Expected 0xFF, received 0x{received:02x}"


@cocotb.test()
async def test_uart_rx_ascii_characters(dut):
    """Test receiving ASCII characters"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.rx.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Test ASCII characters 'A', 'B', 'C'
    test_chars = [0x41, 0x42, 0x43]  # 'A', 'B', 'C'

    for expected in test_chars:
        # Send character
        await send_uart_byte(dut, expected)

        # Wait for rx_ready
        timeout = 0
        while dut.rx_ready.value == 0:
            await RisingEdge(dut.clk)
            timeout += 1
            assert timeout < 10000, "Timeout waiting for rx_ready"

        # Verify data
        received = int(dut.rx_data.value)
        assert received == expected, \
            f"Expected 0x{expected:02x} ('{chr(expected)}'), received 0x{received:02x}"

        # Wait a bit before next character
        await Timer(BIT_PERIOD_NS * 2, unit="ns")


@cocotb.test()
async def test_uart_rx_back_to_back(dut):
    """Test receiving multiple bytes back-to-back"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.rx.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    test_data = [0x48, 0x45, 0x4C, 0x4C, 0x4F]  # "HELLO"

    for expected in test_data:
        # Send byte
        await send_uart_byte(dut, expected)

        # Wait for rx_ready
        timeout = 0
        while dut.rx_ready.value == 0:
            await RisingEdge(dut.clk)
            timeout += 1
            assert timeout < 10000, f"Timeout waiting for rx_ready (char 0x{expected:02x})"

        # Verify
        received = int(dut.rx_data.value)
        assert received == expected, \
            f"Expected 0x{expected:02x}, received 0x{received:02x}"

        # Let rx_ready pulse complete
        await RisingEdge(dut.clk)


@cocotb.test()
async def test_uart_rx_start_bit_validation(dut):
    """Test that false start bit (glitch) is rejected"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.rx.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Send false start bit (glitch - goes low then back high quickly)
    dut.rx.value = 0
    await Timer(BIT_PERIOD_NS // 4, unit="ns")  # Quarter bit time
    dut.rx.value = 1

    # Wait and verify no data was received
    await Timer(BIT_PERIOD_NS * 5, unit="ns")
    assert dut.rx_ready.value == 0, "Should not receive data from false start bit"


@cocotb.test()
async def test_uart_rx_stop_bit_check(dut):
    """Test that invalid stop bit (framing error) discards data"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.rx.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Send start bit
    dut.rx.value = 0
    await Timer(BIT_PERIOD_NS, unit="ns")

    # Send 8 data bits
    for i in range(8):
        dut.rx.value = (0x55 >> i) & 1
        await Timer(BIT_PERIOD_NS, unit="ns")

    # Send invalid stop bit (should be high, but send low)
    dut.rx.value = 0
    await Timer(BIT_PERIOD_NS, unit="ns")

    # Return to idle
    dut.rx.value = 1
    await Timer(BIT_PERIOD_NS * 2, unit="ns")

    # Should NOT have rx_ready (framing error)
    assert dut.rx_ready.value == 0, "Should not set rx_ready with framing error"


@cocotb.test()
async def test_uart_rx_baud_rate_tolerance(dut):
    """Test that RX works with slight baud rate variation"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.rx.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Send byte with 2% faster baud rate (simulates clock mismatch)
    bit_period_fast = int(BIT_PERIOD_NS * 0.98)

    # Start bit
    dut.rx.value = 0
    await Timer(bit_period_fast, unit="ns")

    # Data bits (0xAA = 10101010)
    for i in range(8):
        dut.rx.value = (0xAA >> i) & 1
        await Timer(bit_period_fast, unit="ns")

    # Stop bit
    dut.rx.value = 1
    await Timer(bit_period_fast, unit="ns")

    # Should still receive correctly
    timeout = 0
    while dut.rx_ready.value == 0:
        await RisingEdge(dut.clk)
        timeout += 1
        assert timeout < 10000, "Timeout waiting for rx_ready"

    received = int(dut.rx_data.value)
    assert received == 0xAA, f"Expected 0xAA with baud rate variation, got 0x{received:02x}"


@cocotb.test()
async def test_uart_rx_reset_during_reception(dut):
    """Test that reset during reception clears state"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.rx.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Start sending a byte
    dut.rx.value = 0  # Start bit
    await Timer(BIT_PERIOD_NS * 3, unit="ns")

    # Assert reset mid-reception
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Should not have data ready
    assert dut.rx_ready.value == 0, "rx_ready should be cleared by reset"

    # Release reset and return to idle
    dut.rst.value = 0
    dut.rx.value = 1
    await RisingEdge(dut.clk)

    # Should be ready to receive again
    await send_uart_byte(dut, 0x42)

    timeout = 0
    while dut.rx_ready.value == 0:
        await RisingEdge(dut.clk)
        timeout += 1
        assert timeout < 10000, "Should recover after reset"

    received = int(dut.rx_data.value)
    assert received == 0x42, "Should receive correctly after reset"


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
        rtl_dir / "peripherals" / "uart" / "uart_rx.v"
    ]

    # Parameters
    parameters = {
        "CLK_FREQ": 25000000,  # 25 MHz
        "BAUD_RATE": 115200
    }

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="uart_rx",
        module="test_uart_rx",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
        timescale="1ns/1ps",  # Set timescale for proper 40ns clock period
    )


if __name__ == "__main__":
    test_runner()
