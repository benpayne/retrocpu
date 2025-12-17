"""
Test suite for address_decoder.v module
Tests memory map decoding for 6502 system

Memory Map:
  $0000-$7FFF : RAM (32 KB)
  $8000-$BFFF : BASIC ROM (16 KB)
  $C000-$C0FF : UART (256 bytes)
  $C100-$C1FF : LCD (256 bytes)
  $C200-$C2FF : PS/2 Keyboard (256 bytes)
  $C300-$DFFF : Reserved I/O
  $E000-$FFFF : Monitor ROM (8 KB)

Per TDD: This test is written BEFORE the RTL implementation
"""

import cocotb
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue


@cocotb.test()
async def test_decoder_ram_range(dut):
    """Test RAM address range (0x0000-0x7FFF)"""

    # Test addresses in RAM range
    test_addresses = [
        0x0000,  # First RAM address
        0x0001,  # Second address
        0x00FF,  # End of zero page
        0x0100,  # Start of stack
        0x01FF,  # End of stack
        0x0200,  # Start of general RAM
        0x1000,  # Middle of RAM
        0x4000,  # Middle of RAM
        0x7FFE,  # Second-to-last RAM
        0x7FFF,  # Last RAM address
    ]

    for addr in test_addresses:
        dut.addr.value = addr
        await Timer(1, units="ns")

        assert dut.ram_cs.value == 1, f"RAM not selected at 0x{addr:04x}"
        assert dut.rom_basic_cs.value == 0, f"BASIC ROM incorrectly selected at 0x{addr:04x}"
        assert dut.rom_monitor_cs.value == 0, f"Monitor ROM incorrectly selected at 0x{addr:04x}"
        assert dut.io_cs.value == 0, f"I/O incorrectly selected at 0x{addr:04x}"


@cocotb.test()
async def test_decoder_basic_rom_range(dut):
    """Test BASIC ROM address range (0x8000-0xBFFF)"""

    test_addresses = [
        0x8000,  # First BASIC ROM address
        0x8001,  # Second address
        0x9000,  # Middle
        0xA000,  # Middle
        0xB000,  # Near end
        0xBFFE,  # Second-to-last
        0xBFFF,  # Last BASIC ROM address
    ]

    for addr in test_addresses:
        dut.addr.value = addr
        await Timer(1, units="ns")

        assert dut.rom_basic_cs.value == 1, f"BASIC ROM not selected at 0x{addr:04x}"
        assert dut.ram_cs.value == 0, f"RAM incorrectly selected at 0x{addr:04x}"
        assert dut.rom_monitor_cs.value == 0, f"Monitor ROM incorrectly selected at 0x{addr:04x}"
        assert dut.io_cs.value == 0, f"I/O incorrectly selected at 0x{addr:04x}"


@cocotb.test()
async def test_decoder_uart_range(dut):
    """Test UART I/O address range (0xC000-0xC0FF)"""

    test_addresses = [
        0xC000,  # UART_DATA
        0xC001,  # UART_STATUS
        0xC002,  # UART_CONTROL
        0xC010,  # Mid-range
        0xC0FF,  # Last UART address
    ]

    for addr in test_addresses:
        dut.addr.value = addr
        await Timer(1, units="ns")

        assert dut.io_cs.value == 1, f"I/O not selected at 0x{addr:04x}"
        assert dut.uart_cs.value == 1, f"UART not selected at 0x{addr:04x}"
        assert dut.lcd_cs.value == 0, f"LCD incorrectly selected at 0x{addr:04x}"
        assert dut.ps2_cs.value == 0, f"PS/2 incorrectly selected at 0x{addr:04x}"
        assert dut.ram_cs.value == 0, f"RAM incorrectly selected at 0x{addr:04x}"


@cocotb.test()
async def test_decoder_lcd_range(dut):
    """Test LCD I/O address range (0xC100-0xC1FF)"""

    test_addresses = [
        0xC100,  # LCD_DATA
        0xC101,  # LCD_COMMAND
        0xC102,  # LCD_STATUS
        0xC110,  # Mid-range
        0xC1FF,  # Last LCD address
    ]

    for addr in test_addresses:
        dut.addr.value = addr
        await Timer(1, units="ns")

        assert dut.io_cs.value == 1, f"I/O not selected at 0x{addr:04x}"
        assert dut.lcd_cs.value == 1, f"LCD not selected at 0x{addr:04x}"
        assert dut.uart_cs.value == 0, f"UART incorrectly selected at 0x{addr:04x}"
        assert dut.ps2_cs.value == 0, f"PS/2 incorrectly selected at 0x{addr:04x}"
        assert dut.ram_cs.value == 0, f"RAM incorrectly selected at 0x{addr:04x}"


@cocotb.test()
async def test_decoder_ps2_range(dut):
    """Test PS/2 keyboard I/O address range (0xC200-0xC2FF)"""

    test_addresses = [
        0xC200,  # PS2_DATA
        0xC201,  # PS2_STATUS
        0xC210,  # Mid-range
        0xC2FF,  # Last PS/2 address
    ]

    for addr in test_addresses:
        dut.addr.value = addr
        await Timer(1, units="ns")

        assert dut.io_cs.value == 1, f"I/O not selected at 0x{addr:04x}"
        assert dut.ps2_cs.value == 1, f"PS/2 not selected at 0x{addr:04x}"
        assert dut.uart_cs.value == 0, f"UART incorrectly selected at 0x{addr:04x}"
        assert dut.lcd_cs.value == 0, f"LCD incorrectly selected at 0x{addr:04x}"
        assert dut.ram_cs.value == 0, f"RAM incorrectly selected at 0x{addr:04x}"


@cocotb.test()
async def test_decoder_reserved_io_range(dut):
    """Test reserved I/O address range (0xC300-0xDFFF)"""

    test_addresses = [
        0xC300,  # First reserved
        0xC400,  # Page boundary
        0xD000,  # Middle
        0xDFFF,  # Last reserved
    ]

    for addr in test_addresses:
        dut.addr.value = addr
        await Timer(1, units="ns")

        # Reserved I/O: io_cs should be 1, but no specific device selected
        assert dut.io_cs.value == 1, f"I/O not selected at 0x{addr:04x}"
        assert dut.uart_cs.value == 0, f"UART incorrectly selected at 0x{addr:04x}"
        assert dut.lcd_cs.value == 0, f"LCD incorrectly selected at 0x{addr:04x}"
        assert dut.ps2_cs.value == 0, f"PS/2 incorrectly selected at 0x{addr:04x}"
        assert dut.ram_cs.value == 0, f"RAM incorrectly selected at 0x{addr:04x}"


@cocotb.test()
async def test_decoder_monitor_rom_range(dut):
    """Test Monitor ROM address range (0xE000-0xFFFF)"""

    test_addresses = [
        0xE000,  # First monitor ROM address
        0xE001,  # Second address
        0xF000,  # Middle
        0xFFFA,  # NMI vector
        0xFFFC,  # RESET vector
        0xFFFE,  # IRQ/BRK vector
        0xFFFF,  # Last address
    ]

    for addr in test_addresses:
        dut.addr.value = addr
        await Timer(1, units="ns")

        assert dut.rom_monitor_cs.value == 1, f"Monitor ROM not selected at 0x{addr:04x}"
        assert dut.ram_cs.value == 0, f"RAM incorrectly selected at 0x{addr:04x}"
        assert dut.rom_basic_cs.value == 0, f"BASIC ROM incorrectly selected at 0x{addr:04x}"
        assert dut.io_cs.value == 0, f"I/O incorrectly selected at 0x{addr:04x}"


@cocotb.test()
async def test_decoder_boundaries(dut):
    """Test boundary addresses between regions"""

    boundaries = [
        # (addr, expected_cs)
        (0x7FFF, "ram"),      # Last RAM
        (0x8000, "basic"),    # First BASIC ROM
        (0xBFFF, "basic"),    # Last BASIC ROM
        (0xC000, "uart"),     # First UART
        (0xC0FF, "uart"),     # Last UART
        (0xC100, "lcd"),      # First LCD
        (0xC1FF, "lcd"),      # Last LCD
        (0xC200, "ps2"),      # First PS/2
        (0xC2FF, "ps2"),      # Last PS/2
        (0xC300, "reserved"), # First reserved I/O
        (0xDFFF, "reserved"), # Last reserved I/O
        (0xE000, "monitor"),  # First monitor ROM
        (0xFFFF, "monitor"),  # Last monitor ROM
    ]

    for addr, expected in boundaries:
        dut.addr.value = addr
        await Timer(1, units="ns")

        if expected == "ram":
            assert dut.ram_cs.value == 1, f"Boundary error at 0x{addr:04x}: RAM not selected"
        elif expected == "basic":
            assert dut.rom_basic_cs.value == 1, f"Boundary error at 0x{addr:04x}: BASIC ROM not selected"
        elif expected == "uart":
            assert dut.uart_cs.value == 1, f"Boundary error at 0x{addr:04x}: UART not selected"
        elif expected == "lcd":
            assert dut.lcd_cs.value == 1, f"Boundary error at 0x{addr:04x}: LCD not selected"
        elif expected == "ps2":
            assert dut.ps2_cs.value == 1, f"Boundary error at 0x{addr:04x}: PS/2 not selected"
        elif expected == "reserved":
            assert dut.io_cs.value == 1, f"Boundary error at 0x{addr:04x}: I/O not selected"
        elif expected == "monitor":
            assert dut.rom_monitor_cs.value == 1, f"Boundary error at 0x{addr:04x}: Monitor ROM not selected"


@cocotb.test()
async def test_decoder_mutual_exclusion(dut):
    """Test that only one chip select is active at a time"""

    # Test every 256th address across entire range
    for addr in range(0x0000, 0x10000, 0x100):
        dut.addr.value = addr
        await Timer(1, units="ns")

        # Count active chip selects
        active_count = 0
        if dut.ram_cs.value == 1:
            active_count += 1
        if dut.rom_basic_cs.value == 1:
            active_count += 1
        if dut.rom_monitor_cs.value == 1:
            active_count += 1

        # Note: I/O devices can have io_cs + device_cs both active
        # So we check main memory regions are mutually exclusive

        assert active_count <= 1, \
            f"Multiple chip selects active at 0x{addr:04x}: " \
            f"ram={dut.ram_cs.value} basic={dut.rom_basic_cs.value} monitor={dut.rom_monitor_cs.value}"


@cocotb.test()
async def test_decoder_combinational(dut):
    """Test that decoder is purely combinational (no clock dependency)"""

    # Change address and check immediate response (no clock needed)
    test_sequence = [
        (0x0000, 1, 0, 0),  # addr, ram_cs, rom_basic_cs, rom_monitor_cs
        (0x8000, 0, 1, 0),
        (0xE000, 0, 0, 1),
        (0x0100, 1, 0, 0),
        (0xC000, 0, 0, 0),  # I/O region
    ]

    for addr, exp_ram, exp_basic, exp_monitor in test_sequence:
        dut.addr.value = addr
        await Timer(1, units="ns")  # Propagation delay only

        assert dut.ram_cs.value == exp_ram, f"0x{addr:04x}: ram_cs"
        assert dut.rom_basic_cs.value == exp_basic, f"0x{addr:04x}: rom_basic_cs"
        assert dut.rom_monitor_cs.value == exp_monitor, f"0x{addr:04x}: rom_monitor_cs"


@cocotb.test()
async def test_decoder_page_aligned_io(dut):
    """Test that I/O devices are page-aligned (256-byte blocks)"""

    # UART should respond to C0xx
    for offset in range(256):
        dut.addr.value = 0xC000 + offset
        await Timer(1, units="ns")
        assert dut.uart_cs.value == 1, f"UART not selected at 0xC0{offset:02x}"

    # LCD should respond to C1xx
    for offset in range(256):
        dut.addr.value = 0xC100 + offset
        await Timer(1, units="ns")
        assert dut.lcd_cs.value == 1, f"LCD not selected at 0xC1{offset:02x}"

    # PS/2 should respond to C2xx
    for offset in range(256):
        dut.addr.value = 0xC200 + offset
        await Timer(1, units="ns")
        assert dut.ps2_cs.value == 1, f"PS/2 not selected at 0xC2{offset:02x}"


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
        rtl_dir / "memory" / "address_decoder.v"
    ]

    # Parameters
    parameters = {}

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="address_decoder",
        module="test_address_decoder",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
    )


if __name__ == "__main__":
    test_runner()
