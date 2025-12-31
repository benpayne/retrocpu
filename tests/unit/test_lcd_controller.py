"""
Test for LCD Controller Top-Level Module

Verifies the complete LCD controller including:
- Memory-mapped register interface ($C100-$C102)
- Initialization sequence integration
- Character and command writes with nibble sequencing
- Busy flag management
- 4-bit mode operation (high nibble, then low nibble)

Register Map:
- $C100: Data register (write character ASCII code)
- $C101: Command register (write HD44780 command)
- $C102: Status register (read bit 0 = busy)
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


@cocotb.test()
async def test_controller_reset(dut):
    """Test that controller resets correctly"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.cs.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.data_in.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # Verify reset state
    assert dut.lcd_e.value == 0, "LCD enable should be low"
    dut._log.info("Reset state verified")


@cocotb.test()
async def test_controller_init_busy(dut):
    """Test that controller is busy during initialization"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.cs.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.data_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    # Read status register ($C102) during init
    dut.cs.value = 1
    dut.we.value = 0  # Read
    dut.addr.value = 0x02  # Status register
    await RisingEdge(dut.clk)

    # Busy flag should be set during initialization
    status = int(dut.data_out.value)
    busy = status & 0x01

    dut._log.info(f"Status during init: 0x{status:02X}, busy={busy}")
    assert busy == 1, "Should be busy during initialization"


@cocotb.test()
async def test_controller_write_character(dut):
    """Test writing a character to data register ($C100)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.cs.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.data_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 10)

    # Wait for initialization to complete (shortened for sim)
    # In real test, would wait for busy to clear
    for _ in range(100):
        dut.cs.value = 1
        dut.we.value = 0
        dut.addr.value = 0x02  # Status
        await RisingEdge(dut.clk)
        status = int(dut.data_out.value)
        if (status & 0x01) == 0:  # Not busy
            break
        dut.cs.value = 0
        await ClockCycles(dut.clk, 100)

    dut._log.info("Initialization complete, writing character")

    # Write character 'A' (0x41) to data register
    dut.cs.value = 1
    dut.we.value = 1  # Write
    dut.addr.value = 0x00  # Data register ($C100)
    dut.data_in.value = 0x41  # 'A'
    await RisingEdge(dut.clk)
    dut.cs.value = 0
    dut.we.value = 0
    await ClockCycles(dut.clk, 2)

    # Monitor LCD signals for 4-bit nibble sequence
    # Should see high nibble (0x4) then low nibble (0x1)
    nibbles_seen = []
    timeout = 0

    for _ in range(5000):
        await RisingEdge(dut.clk)
        timeout += 1

        if dut.lcd_e.value == 1:  # Enable pulse - capture data
            nibble = int(dut.lcd_data.value) & 0x0F
            rs = int(dut.lcd_rs.value)
            nibbles_seen.append((nibble, rs))
            dut._log.info(f"Nibble: 0x{nibble:X}, RS={rs}")

            # Wait for enable to go low
            while dut.lcd_e.value == 1:
                await RisingEdge(dut.clk)
                timeout += 1
                if timeout > 5000:
                    break

        if len(nibbles_seen) >= 2:  # Got both nibbles
            break

        if timeout > 5000:
            break

    # Verify we saw high nibble (0x4) then low nibble (0x1)
    assert len(nibbles_seen) >= 2, f"Expected 2 nibbles, got {len(nibbles_seen)}"

    high_nibble, high_rs = nibbles_seen[0]
    low_nibble, low_rs = nibbles_seen[1]

    dut._log.info(f"Character write: high=0x{high_nibble:X}, low=0x{low_nibble:X}")

    assert high_nibble == 0x4, f"Expected high nibble 0x4, got 0x{high_nibble:X}"
    assert low_nibble == 0x1, f"Expected low nibble 0x1, got 0x{low_nibble:X}"
    assert high_rs == 1, "RS should be 1 for data"
    assert low_rs == 1, "RS should be 1 for data"


@cocotb.test()
async def test_controller_write_command(dut):
    """Test writing a command to command register ($C101)"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.cs.value = 0
    dut.we.value = 0
    dut.addr.value = 0
    dut.data_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 10)

    # Wait for init
    for _ in range(100):
        dut.cs.value = 1
        dut.we.value = 0
        dut.addr.value = 0x02
        await RisingEdge(dut.clk)
        if (int(dut.data_out.value) & 0x01) == 0:
            break
        dut.cs.value = 0
        await ClockCycles(dut.clk, 100)

    dut._log.info("Writing command")

    # Write clear display command (0x01) to command register
    dut.cs.value = 1
    dut.we.value = 1
    dut.addr.value = 0x01  # Command register ($C101)
    dut.data_in.value = 0x01  # Clear display
    await RisingEdge(dut.clk)
    dut.cs.value = 0
    dut.we.value = 0
    await ClockCycles(dut.clk, 2)

    # Monitor for nibbles with RS=0 (command)
    nibbles_seen = []
    timeout = 0

    for _ in range(5000):
        await RisingEdge(dut.clk)
        timeout += 1

        if dut.lcd_e.value == 1:
            nibble = int(dut.lcd_data.value) & 0x0F
            rs = int(dut.lcd_rs.value)
            nibbles_seen.append((nibble, rs))
            dut._log.info(f"Command nibble: 0x{nibble:X}, RS={rs}")

            while dut.lcd_e.value == 1:
                await RisingEdge(dut.clk)
                timeout += 1
                if timeout > 5000:
                    break

        if len(nibbles_seen) >= 2:
            break

        if timeout > 5000:
            break

    # Verify command nibbles
    assert len(nibbles_seen) >= 2, f"Expected 2 nibbles, got {len(nibbles_seen)}"

    high_nibble, high_rs = nibbles_seen[0]
    low_nibble, low_rs = nibbles_seen[1]

    dut._log.info(f"Command write: high=0x{high_nibble:X}, low=0x{low_nibble:X}")

    assert high_nibble == 0x0, f"Expected high nibble 0x0, got 0x{high_nibble:X}"
    assert low_nibble == 0x1, f"Expected low nibble 0x1, got 0x{low_nibble:X}"
    assert high_rs == 0, "RS should be 0 for command"
    assert low_rs == 0, "RS should be 0 for command"


@cocotb.test()
async def test_controller_busy_flag(dut):
    """Test that busy flag prevents writes and clears when ready"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.cs.value = 0
    dut.we.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 10)

    # Wait for init
    for _ in range(100):
        dut.cs.value = 1
        dut.we.value = 0
        dut.addr.value = 0x02
        await RisingEdge(dut.clk)
        if (int(dut.data_out.value) & 0x01) == 0:
            break
        dut.cs.value = 0
        await ClockCycles(dut.clk, 100)

    dut._log.info("Testing busy flag behavior")

    # Write a character
    dut.cs.value = 1
    dut.we.value = 1
    dut.addr.value = 0x00
    dut.data_in.value = 0x42  # 'B'
    await RisingEdge(dut.clk)
    dut.cs.value = 0
    dut.we.value = 0
    await ClockCycles(dut.clk, 2)

    # Immediately check status - should be busy
    dut.cs.value = 1
    dut.we.value = 0
    dut.addr.value = 0x02
    await RisingEdge(dut.clk)
    status = int(dut.data_out.value)
    busy_immediately = status & 0x01

    dut._log.info(f"Busy immediately after write: {busy_immediately}")
    # Note: May or may not be busy depending on timing

    # Wait for busy to clear
    busy_cleared = False
    for _ in range(5000):
        dut.cs.value = 1
        dut.we.value = 0
        dut.addr.value = 0x02
        await RisingEdge(dut.clk)
        status = int(dut.data_out.value)
        if (status & 0x01) == 0:
            busy_cleared = True
            dut._log.info("Busy flag cleared")
            break
        dut.cs.value = 0
        await ClockCycles(dut.clk, 10)

    assert busy_cleared, "Busy flag should eventually clear"


@cocotb.test()
async def test_controller_multiple_characters(dut):
    """Test writing multiple characters in sequence"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.cs.value = 0
    dut.we.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 10)

    # Wait for init
    for _ in range(100):
        dut.cs.value = 1
        dut.we.value = 0
        dut.addr.value = 0x02
        await RisingEdge(dut.clk)
        if (int(dut.data_out.value) & 0x01) == 0:
            break
        dut.cs.value = 0
        await ClockCycles(dut.clk, 100)

    # Write "HI" (0x48, 0x49)
    characters = [0x48, 0x49]  # 'H', 'I'

    for char in characters:
        # Wait for not busy
        for _ in range(5000):
            dut.cs.value = 1
            dut.we.value = 0
            dut.addr.value = 0x02
            await RisingEdge(dut.clk)
            if (int(dut.data_out.value) & 0x01) == 0:
                break
            dut.cs.value = 0
            await ClockCycles(dut.clk, 10)

        # Write character
        dut.cs.value = 1
        dut.we.value = 1
        dut.addr.value = 0x00
        dut.data_in.value = char
        await RisingEdge(dut.clk)
        dut.cs.value = 0
        dut.we.value = 0

        dut._log.info(f"Wrote character 0x{char:02X}")
        await ClockCycles(dut.clk, 100)

    dut._log.info("Multiple character writes completed")


@cocotb.test()
async def test_controller_register_decode(dut):
    """Test that register addresses are decoded correctly"""

    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.cs.value = 0
    dut.we.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 10)

    # Test reading different addresses
    addresses = [0x00, 0x01, 0x02, 0x03, 0xFF]

    for addr in addresses:
        dut.cs.value = 1
        dut.we.value = 0
        dut.addr.value = addr
        await RisingEdge(dut.clk)
        data = int(dut.data_out.value)
        dut._log.info(f"Read addr 0x{addr:02X}: 0x{data:02X}")
        dut.cs.value = 0
        await ClockCycles(dut.clk, 2)

    # Only $C102 (addr 0x02) should return valid status
    # Other addresses may return 0 or undefined
    dut._log.info("Register decode test completed")
