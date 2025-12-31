"""
Simple debug test for uart_rx
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

BAUD_RATE = 115200
BIT_PERIOD_NS = int((1000000 / BAUD_RATE) * 1000)  # ~8680 ns

@cocotb.test()
async def test_uart_rx_debug(dut):
    """Debug test - send one byte and monitor signals"""

    # Create 25 MHz clock (40ns period)
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst.value = 1
    dut.rx.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    dut._log.info("Starting test - sending 0x55")

    # Send start bit
    dut.rx.value = 0
    dut._log.info(f"t={cocotb.utils.get_sim_time('ns')}ns: Start bit sent (rx=0)")
    await Timer(BIT_PERIOD_NS, unit="ns")

    # Send 8 data bits (0x55 = 0b01010101, LSB first)
    test_byte = 0x55
    for i in range(8):
        bit = (test_byte >> i) & 1
        dut.rx.value = bit
        dut._log.info(f"t={cocotb.utils.get_sim_time('ns')}ns: Data bit {i} = {bit}")
        await Timer(BIT_PERIOD_NS, unit="ns")

    # Send stop bit
    dut.rx.value = 1
    dut._log.info(f"t={cocotb.utils.get_sim_time('ns')}ns: Stop bit sent (rx=1)")
    await Timer(BIT_PERIOD_NS, unit="ns")

    dut._log.info(f"t={cocotb.utils.get_sim_time('ns')}ns: Byte transmission complete")

    # Wait and poll for rx_ready
    dut._log.info("Polling for rx_ready...")
    timeout = 0
    while dut.rx_ready.value == 0 and timeout < 1000:
        await RisingEdge(dut.clk)
        timeout += 1
        if timeout % 100 == 0:
            state = int(dut.state.value)
            baud_counter = int(dut.baud_counter.value)
            bit_index = int(dut.bit_index.value) if hasattr(dut, 'bit_index') else -1
            dut._log.info(f"  Cycle {timeout}: state={state}, baud_counter={baud_counter}, bit_index={bit_index}, rx_ready={dut.rx_ready.value}")

    if dut.rx_ready.value == 1:
        received = int(dut.rx_data.value)
        dut._log.info(f"SUCCESS! rx_ready=1, rx_data=0x{received:02x} after {timeout} cycles")
        assert received == 0x55, f"Expected 0x55, got 0x{received:02x}"
    else:
        state = int(dut.state.value)
        baud_counter = int(dut.baud_counter.value)
        dut._log.error(f"TIMEOUT after {timeout} cycles. Final state={state}, baud_counter={baud_counter}")
        assert False, "Timeout waiting for rx_ready"


if __name__ == "__main__":
    import os
    from pathlib import Path
    from cocotb_test.simulator import run

    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    verilog_sources = [
        rtl_dir / "peripherals" / "uart" / "uart_rx.v"
    ]

    parameters = {
        "CLK_FREQ": 25000000,
        "BAUD_RATE": 115200
    }

    simulator = os.getenv("SIM", "icarus")

    run(
        verilog_sources=[str(v) for v in verilog_sources],
        toplevel="uart_rx",
        module="test_uart_rx_debug",
        simulator=simulator,
        parameters=parameters,
        waves=True,
        timescale="1ns/1ps",
    )
