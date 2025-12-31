"""
Test RAM module with zero page addresses
Verifies that writes to $0000-$00FF work correctly
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


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
        module="test_ram_zeropage",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
        compile_args=["-g2012", "-Wno-timescale"],
        sim_args=["-fst"] if os.getenv("WAVES") == "1" else [],
        timescale="1ns/1ps",
    )

@cocotb.test()
async def test_ram_zeropage_write_read(dut):
    """Test write and read to zero page addresses"""

    # Start clock - use 1 second period to match simulator precision
    clock = Clock(dut.clk, 2, unit="sec")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.we.value = 0
    dut.addr.value = 0
    dut.data_in.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Test 1: Write $AA to address $0000
    dut.we.value = 1
    dut.addr.value = 0x0000
    dut.data_in.value = 0xAA
    await RisingEdge(dut.clk)

    # Read back from $0000
    dut.we.value = 0
    dut.addr.value = 0x0000
    await RisingEdge(dut.clk)

    # Check data_out on next cycle (synchronous read)
    read_value = dut.data_out.value.integer
    assert read_value == 0xAA, f"Expected 0xAA at $0000, got 0x{read_value:02X}"
    print(f"✓ Address $0000: wrote 0xAA, read 0x{read_value:02X}")

    # Test 2: Write $55 to address $0010
    dut.we.value = 1
    dut.addr.value = 0x0010
    dut.data_in.value = 0x55
    await RisingEdge(dut.clk)

    # Read back from $0010
    dut.we.value = 0
    dut.addr.value = 0x0010
    await RisingEdge(dut.clk)

    read_value = dut.data_out.value.integer
    assert read_value == 0x55, f"Expected 0x55 at $0010, got 0x{read_value:02X}"
    print(f"✓ Address $0010: wrote 0x55, read 0x{read_value:02X}")

    # Test 3: Write $CC to address $0020
    dut.we.value = 1
    dut.addr.value = 0x0020
    dut.data_in.value = 0xCC
    await RisingEdge(dut.clk)

    # Read back from $0020
    dut.we.value = 0
    dut.addr.value = 0x0020
    await RisingEdge(dut.clk)

    read_value = dut.data_out.value.integer
    assert read_value == 0xCC, f"Expected 0xCC at $0020, got 0x{read_value:02X}"
    print(f"✓ Address $0020: wrote 0xCC, read 0x{read_value:02X}")

    # Test 4: Verify all three values are retained
    dut.we.value = 0

    # Read $0000
    dut.addr.value = 0x0000
    await RisingEdge(dut.clk)
    assert dut.data_out.value.integer == 0xAA, "Address $0000 lost its value"
    print(f"✓ Address $0000 retained: 0x{dut.data_out.value.integer:02X}")

    # Read $0010
    dut.addr.value = 0x0010
    await RisingEdge(dut.clk)
    assert dut.data_out.value.integer == 0x55, "Address $0010 lost its value"
    print(f"✓ Address $0010 retained: 0x{dut.data_out.value.integer:02X}")

    # Read $0020
    dut.addr.value = 0x0020
    await RisingEdge(dut.clk)
    assert dut.data_out.value.integer == 0xCC, "Address $0020 lost its value"
    print(f"✓ Address $0020 retained: 0x{dut.data_out.value.integer:02X}")

    print("\n✓ All zero page tests passed!")

@cocotb.test()
async def test_ram_write_read_timing(dut):
    """Test write/read timing - write on one cycle, read back on next"""

    # Start clock
    clock = Clock(dut.clk, 2, unit="sec")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 0
    dut.we.value = 0
    await RisingEdge(dut.clk)

    # Write $42 to $0005
    dut.we.value = 1
    dut.addr.value = 0x0005
    dut.data_in.value = 0x42
    await RisingEdge(dut.clk)

    # On same cycle as write completes, switch to read
    # The write should complete, and read should start
    dut.we.value = 0
    dut.addr.value = 0x0005

    # Wait for read to complete
    await RisingEdge(dut.clk)

    # Now data_out should have the value we just wrote
    read_value = dut.data_out.value.integer
    assert read_value == 0x42, f"Expected 0x42, got 0x{read_value:02X}"
    print(f"✓ Write-then-read timing test passed: 0x{read_value:02X}")
