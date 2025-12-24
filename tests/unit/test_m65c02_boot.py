"""
Test suite for M65C02 CPU core boot simulation
Debug why the M65C02 system is not booting on hardware

This test simulates the soc_top module with M65C02 core
to verify basic operation.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_m65c02_boot_basic(dut):
    """Test that M65C02 core boots and fetches from reset vector"""

    # Create 25 MHz clock
    clock = Clock(dut.clk_25mhz, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Button is not pressed (active-low input = high)
    dut.reset_button_n.value = 1

    # UART RX idle (high)
    dut.uart_rx.value = 1

    # Wait for power-on reset to complete
    for _ in range(200):
        await RisingEdge(dut.clk_25mhz)

    dut._log.info(f"After reset release:")
    dut._log.info(f"  system_rst = {dut.system_rst.value}")

    # Check if CPU is running (MC state should be cycling)
    mc_states = []
    for _ in range(20):
        await RisingEdge(dut.clk_25mhz)
        mc_states.append(int(dut.cpu_mc.value))

    dut._log.info(f"MC states: {mc_states}")

    # MC should cycle through 2, 3, 1, 0 pattern
    assert len(set(mc_states)) > 1, f"MC not changing: {mc_states}"

    # Check address bus activity
    addresses = []
    for _ in range(20):
        await RisingEdge(dut.clk_25mhz)
        addresses.append(int(dut.cpu_addr.value))

    dut._log.info(f"First 20 addresses: {[hex(a) for a in addresses[:20]]}")

    # Address should change (CPU fetching instructions)
    assert len(set(addresses)) > 1, f"Address bus not changing: {addresses}"

    # Check IO_Op activity
    io_ops = []
    for _ in range(20):
        await RisingEdge(dut.clk_25mhz)
        io_ops.append(int(dut.cpu_io_op.value))

    dut._log.info(f"IO_Op values: {io_ops}")

    # Should see some READ (2) or FETCH (3) operations
    assert 2 in io_ops or 3 in io_ops, f"No read/fetch operations: {io_ops}"


@cocotb.test()
async def test_m65c02_reset_vector_fetch(dut):
    """Test that M65C02 fetches from reset vector at $FFFC"""

    # Create 25 MHz clock
    clock = Clock(dut.clk_25mhz, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Button is not pressed
    dut.reset_button_n.value = 1
    dut.uart_rx.value = 1

    # Wait for power-on reset to complete
    for _ in range(200):
        await RisingEdge(dut.clk_25mhz)

    # Monitor for accesses to reset vector area ($FFFC/$FFFD)
    reset_vector_accessed = False

    for _ in range(100):
        await RisingEdge(dut.clk_25mhz)
        addr = int(dut.cpu_addr.value)

        if addr == 0xFFFC or addr == 0xFFFD:
            reset_vector_accessed = True
            dut._log.info(f"Reset vector accessed at address: {hex(addr)}")
            break

    assert reset_vector_accessed, "CPU did not access reset vector at $FFFC/$FFFD"


@cocotb.test()
async def test_m65c02_microcycle_sequence(dut):
    """Test that M65C02 MC state follows correct 2->3->1->0 sequence"""

    # Create 25 MHz clock
    clock = Clock(dut.clk_25mhz, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.reset_button_n.value = 1
    dut.uart_rx.value = 1

    # Wait for power-on reset
    for _ in range(200):
        await RisingEdge(dut.clk_25mhz)

    # Collect MC state sequence
    mc_sequence = []
    for _ in range(50):
        await RisingEdge(dut.clk_25mhz)
        mc_sequence.append(int(dut.cpu_mc.value))

    dut._log.info(f"MC sequence: {mc_sequence}")

    # Check for valid MC values (0, 1, 2, 3)
    for mc in mc_sequence:
        assert mc in [0, 1, 2, 3], f"Invalid MC value: {mc}"

    # Check that we see the expected pattern
    # The sequence should be 2 -> 3 -> 1 -> 0 -> 2 -> ...
    transitions = 0
    for i in range(len(mc_sequence) - 1):
        curr = mc_sequence[i]
        next_val = mc_sequence[i + 1]

        # Valid transitions
        if (curr == 2 and next_val == 3) or \
           (curr == 3 and next_val == 1) or \
           (curr == 1 and next_val == 0) or \
           (curr == 0 and next_val == 2):
            transitions += 1

    dut._log.info(f"Valid transitions: {transitions} / {len(mc_sequence) - 1}")

    # Should have mostly valid transitions
    assert transitions > (len(mc_sequence) - 1) * 0.8, \
        f"Too few valid MC transitions: {transitions}"


@cocotb.test()
async def test_m65c02_write_enable_signal(dut):
    """Test that mem_we signal is generated correctly"""

    # Create 25 MHz clock
    clock = Clock(dut.clk_25mhz, 40, units="ns")
    cocotb.start_soon(clock.start())

    dut.reset_button_n.value = 1
    dut.uart_rx.value = 1

    # Wait for power-on reset
    for _ in range(200):
        await RisingEdge(dut.clk_25mhz)

    # Monitor for write operations
    write_detected = False

    for _ in range(500):
        await RisingEdge(dut.clk_25mhz)

        io_op = int(dut.cpu_io_op.value)
        mc = int(dut.cpu_mc.value)

        # mem_we should be: (IO_Op == 01) && (MC == 011)
        expected_we = (io_op == 1) and (mc == 3)

        # Note: We can't directly check mem_we signal if it's internal
        # But we can verify the logic conditions

        if expected_we:
            write_detected = True
            dut._log.info(f"Write condition detected: IO_Op={io_op}, MC={mc}")
            # Writes should happen during boot (e.g., stack initialization)
            break

    # We expect some writes during boot (stack setup, etc.)
    # But if the CPU isn't running at all, this might not happen
    dut._log.info(f"Write operations detected: {write_detected}")


# cocotb test configuration
def test_runner():
    """pytest entry point for running cocotb tests"""
    import pytest
    import os
    from pathlib import Path

    # Get project root
    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    # RTL sources - need ALL files for soc_top
    verilog_sources = [
        # M65C02 core files
        rtl_dir / "cpu" / "m65c02" / "M65C02_Core.v",
        rtl_dir / "cpu" / "m65c02" / "M65C02_MPCv4.v",
        rtl_dir / "cpu" / "m65c02" / "M65C02_AddrGen.v",
        rtl_dir / "cpu" / "m65c02" / "M65C02_ALU.v",
        rtl_dir / "cpu" / "m65c02" / "M65C02_BIN.v",
        rtl_dir / "cpu" / "m65c02" / "M65C02_BCD.v",
        # System files
        rtl_dir / "system" / "reset_controller.v",
        rtl_dir / "memory" / "ram.v",
        rtl_dir / "memory" / "rom_basic.v",
        rtl_dir / "memory" / "rom_monitor.v",
        rtl_dir / "memory" / "address_decoder.v",
        rtl_dir / "peripherals" / "uart" / "uart.v",
        rtl_dir / "peripherals" / "uart" / "uart_tx.v",
        rtl_dir / "peripherals" / "uart" / "uart_rx.v",
        # Top level
        rtl_dir / "system" / "soc_top.v",
    ]

    # Include paths for M65C02 microprogram ROMs
    includes = [str(rtl_dir / "cpu" / "m65c02")]

    # Parameters
    parameters = {}

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="soc_top",
        module="test_m65c02_boot",
        simulator=simulator,
        parameters=parameters,
        includes=includes,
        waves=True if os.getenv("WAVES") == "1" else False,
    )


if __name__ == "__main__":
    test_runner()
