"""
Test suite for uart_tx.v module
Tests UART transmitter with 9600 baud, 8N1 format

UART Format: 8 data bits, No parity, 1 stop bit (8N1)
Baud Rate: 9600 (divider = 163 from 25 MHz clock)
Bit Time: 104.17 μs (9600 baud)

Per TDD: This test is written BEFORE the RTL implementation
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer


# UART timing constants
BAUD_RATE = 9600
BIT_PERIOD_US = 1000000 / BAUD_RATE  # ~104.17 μs
BIT_PERIOD_NS = int(BIT_PERIOD_US * 1000)  # ~104167 ns


async def sample_uart_bit(dut):
    """Wait for one bit period and sample TX line"""
    await Timer(BIT_PERIOD_NS, units="ns")
    return int(dut.tx.value)


async def receive_uart_byte(dut):
    """Receive a complete UART byte from TX line"""
    # Wait for start bit (falling edge)
    while dut.tx.value == 1:
        await Timer(1, units="us")

    # Verify start bit (should be 0)
    start_bit = int(dut.tx.value)
    assert start_bit == 0, "Start bit should be 0"

    # Wait half bit period to sample in middle of bit
    await Timer(BIT_PERIOD_NS // 2, units="ns")

    # Sample 8 data bits (LSB first)
    data = 0
    for i in range(8):
        await Timer(BIT_PERIOD_NS, units="ns")
        bit = int(dut.tx.value)
        data |= (bit << i)

    # Sample stop bit
    await Timer(BIT_PERIOD_NS, units="ns")
    stop_bit = int(dut.tx.value)
    assert stop_bit == 1, "Stop bit should be 1"

    return data


@cocotb.test()
async def test_uart_tx_idle_state(dut):
    """Test that TX line idles high"""

    # Create 25 MHz clock
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.tx_start.value = 0
    dut.tx_data.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # TX should idle high
    assert dut.tx.value == 1, "TX line should idle high"
    assert dut.tx_busy.value == 0, "TX should not be busy"

    # Wait and verify it stays high
    await Timer(1, units="us")
    assert dut.tx.value == 1, "TX line should remain high when idle"


@cocotb.test()
async def test_uart_tx_single_byte(dut):
    """Test transmitting a single byte"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.tx_start.value = 0
    dut.tx_data.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Start transmission of 0x55 (01010101 pattern, good test pattern)
    dut.tx_data.value = 0x55
    dut.tx_start.value = 1
    await RisingEdge(dut.clk)
    dut.tx_start.value = 0

    # TX should become busy
    await RisingEdge(dut.clk)
    assert dut.tx_busy.value == 1, "TX should be busy after start"

    # Receive the byte
    received = await receive_uart_byte(dut)
    assert received == 0x55, f"Expected 0x55, received 0x{received:02x}"

    # Wait for transmission to complete
    for _ in range(100):
        await RisingEdge(dut.clk)
        if dut.tx_busy.value == 0:
            break

    assert dut.tx_busy.value == 0, "TX should not be busy after transmission"


@cocotb.test()
async def test_uart_tx_all_zeros(dut):
    """Test transmitting 0x00 (all zeros)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.tx_start.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Transmit 0x00
    dut.tx_data.value = 0x00
    dut.tx_start.value = 1
    await RisingEdge(dut.clk)
    dut.tx_start.value = 0

    received = await receive_uart_byte(dut)
    assert received == 0x00, f"Expected 0x00, received 0x{received:02x}"


@cocotb.test()
async def test_uart_tx_all_ones(dut):
    """Test transmitting 0xFF (all ones)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.tx_start.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Transmit 0xFF
    dut.tx_data.value = 0xFF
    dut.tx_start.value = 1
    await RisingEdge(dut.clk)
    dut.tx_start.value = 0

    received = await receive_uart_byte(dut)
    assert received == 0xFF, f"Expected 0xFF, received 0x{received:02x}"


@cocotb.test()
async def test_uart_tx_ascii_characters(dut):
    """Test transmitting ASCII characters"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.tx_start.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Test ASCII characters 'A', 'B', 'C'
    test_chars = [0x41, 0x42, 0x43]  # 'A', 'B', 'C'

    for char in test_chars:
        # Wait for TX to be ready
        while dut.tx_busy.value == 1:
            await RisingEdge(dut.clk)

        # Transmit character
        dut.tx_data.value = char
        dut.tx_start.value = 1
        await RisingEdge(dut.clk)
        dut.tx_start.value = 0

        # Receive and verify
        received = await receive_uart_byte(dut)
        assert received == char, f"Expected 0x{char:02x}, received 0x{received:02x}"


@cocotb.test()
async def test_uart_tx_back_to_back(dut):
    """Test transmitting multiple bytes back-to-back"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.tx_start.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    test_data = [0x48, 0x45, 0x4C, 0x4C, 0x4F]  # "HELLO"

    for expected in test_data:
        # Wait for TX to be ready
        timeout = 0
        while dut.tx_busy.value == 1:
            await RisingEdge(dut.clk)
            timeout += 1
            assert timeout < 50000, "Timeout waiting for TX ready"

        # Start transmission
        dut.tx_data.value = expected
        dut.tx_start.value = 1
        await RisingEdge(dut.clk)
        dut.tx_start.value = 0

        # Receive and verify
        received = await receive_uart_byte(dut)
        assert received == expected, \
            f"Expected 0x{expected:02x} ('{chr(expected)}'), received 0x{received:02x}"


@cocotb.test()
async def test_uart_tx_busy_flag(dut):
    """Test that busy flag is set during transmission"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.tx_start.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Initially not busy
    assert dut.tx_busy.value == 0, "TX should not be busy initially"

    # Start transmission
    dut.tx_data.value = 0xAA
    dut.tx_start.value = 1
    await RisingEdge(dut.clk)
    dut.tx_start.value = 0
    await RisingEdge(dut.clk)

    # Should be busy now
    assert dut.tx_busy.value == 1, "TX should be busy during transmission"

    # Wait for start bit and first few data bits
    await Timer(BIT_PERIOD_NS * 3, units="ns")

    # Should still be busy
    assert dut.tx_busy.value == 1, "TX should remain busy during transmission"

    # Wait for completion
    await Timer(BIT_PERIOD_NS * 10, units="ns")

    # Should be idle again
    for _ in range(100):
        await RisingEdge(dut.clk)
        if dut.tx_busy.value == 0:
            break

    assert dut.tx_busy.value == 0, "TX should not be busy after transmission"


@cocotb.test()
async def test_uart_tx_start_pulse(dut):
    """Test that single-cycle start pulse triggers transmission"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.tx_start.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Single-cycle start pulse
    dut.tx_data.value = 0x42
    dut.tx_start.value = 1
    await RisingEdge(dut.clk)
    dut.tx_start.value = 0  # Deassert after 1 cycle

    # Should still transmit
    received = await receive_uart_byte(dut)
    assert received == 0x42, "Single-cycle start pulse should trigger transmission"


@cocotb.test()
async def test_uart_tx_baud_rate(dut):
    """Test that baud rate timing is correct"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.tx_start.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Start transmission
    dut.tx_data.value = 0xA5
    dut.tx_start.value = 1
    await RisingEdge(dut.clk)
    dut.tx_start.value = 0

    # Wait for start bit falling edge
    while dut.tx.value == 1:
        await Timer(100, units="ns")

    start_time = cocotb.utils.get_sim_time(units="ns")

    # Wait for stop bit
    await Timer(BIT_PERIOD_NS * 9.5, units="ns")  # Start + 8 data + stop

    # Verify we're in stop bit
    assert dut.tx.value == 1, "Should be in stop bit"

    # Measure approximate timing
    end_time = cocotb.utils.get_sim_time(units="ns")
    measured_frame_time = end_time - start_time

    # Frame should be about 10 bits * bit_period (start + 8 data + stop)
    expected_frame_time = BIT_PERIOD_NS * 10
    tolerance = BIT_PERIOD_NS * 0.5  # Allow 0.5 bit period tolerance

    assert abs(measured_frame_time - expected_frame_time) < tolerance, \
        f"Baud rate timing error: expected ~{expected_frame_time}ns, got {measured_frame_time}ns"


@cocotb.test()
async def test_uart_tx_reset(dut):
    """Test that reset aborts transmission and returns to idle"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.tx_start.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Start transmission
    dut.tx_data.value = 0x55
    dut.tx_start.value = 1
    await RisingEdge(dut.clk)
    dut.tx_start.value = 0

    # Wait partway through transmission
    await Timer(BIT_PERIOD_NS * 3, units="ns")

    # Assert reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Should return to idle
    assert dut.tx.value == 1, "TX should be high after reset"
    assert dut.tx_busy.value == 0, "TX should not be busy after reset"

    # Release reset
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Should remain idle
    assert dut.tx.value == 1, "TX should remain high"


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
        rtl_dir / "peripherals" / "uart" / "uart_tx.v"
    ]

    # Parameters
    parameters = {
        "CLK_FREQ": 25000000,  # 25 MHz
        "BAUD_RATE": 9600
    }

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="uart_tx",
        module="test_uart_tx",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
    )


if __name__ == "__main__":
    test_runner()
