"""
Test UART status register reading - simulates monitor firmware behavior
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


@cocotb.test()
async def test_uart_status_checking(dut):
    """Test UART status checking like monitor firmware does"""

    clock = Clock(dut.clk, 40, unit="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 10)

    dut._log.info("=== Testing UART Status Register ===")

    # Test writing a string with status checking (like monitor CHROUT)
    test_string = "HELLO"

    for i, char in enumerate(test_string):
        dut._log.info(f"\n--- Character {i}: '{char}' (0x{ord(char):02X}) ---")

        # Simulate monitor's CHROUT: poll status until ready
        poll_count = 0
        max_polls = 100000

        while poll_count < max_polls:
            # Read UART status ($C001)
            dut.cs.value = 1
            dut.we.value = 0  # Read
            dut.addr.value = 0x01  # Status register
            await RisingEdge(dut.clk)

            status = int(dut.data_out.value)
            tx_ready = status & 0x01

            if poll_count < 5 or poll_count % 10000 == 0:
                dut._log.info(f"  Poll {poll_count}: status=0x{status:02X}, tx_ready={tx_ready}")

            if tx_ready:
                dut._log.info(f"  ✓ TX ready after {poll_count} polls")
                break

            poll_count += 1
            await RisingEdge(dut.clk)

        if poll_count >= max_polls:
            dut._log.error(f"✗ TX never became ready after {max_polls} polls!")
            assert False, "UART never became ready"

        # Write character to UART data register ($C000)
        dut.cs.value = 1
        dut.we.value = 1  # Write
        dut.addr.value = 0x00  # Data register
        dut.data_in.value = ord(char)
        await RisingEdge(dut.clk)

        # Deassert write
        dut.cs.value = 0
        dut.we.value = 0
        await RisingEdge(dut.clk)

        dut._log.info(f"  Wrote character '{char}'")

    # Wait for last character to transmit
    dut._log.info("\nWaiting for final transmission to complete...")
    await ClockCycles(dut.clk, 50000)

    dut._log.info("\n✓ Test completed successfully")


@cocotb.test()
async def test_uart_rapid_writes(dut):
    """Test what happens with rapid writes (no status checking)"""

    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 10)

    dut._log.info("=== Testing Rapid Writes (No Status Check) ===")

    test_string = "ABCD"

    for i, char in enumerate(test_string):
        dut._log.info(f"Writing '{char}' without checking status")

        # Write immediately
        dut.cs.value = 1
        dut.we.value = 1
        dut.addr.value = 0x00
        dut.data_in.value = ord(char)
        await RisingEdge(dut.clk)

        dut.cs.value = 0
        dut.we.value = 0
        await RisingEdge(dut.clk)

        # Very short delay
        await ClockCycles(dut.clk, 100)

    dut._log.info("All characters written rapidly")
    await ClockCycles(dut.clk, 100000)

    dut._log.info("✓ Test completed")
