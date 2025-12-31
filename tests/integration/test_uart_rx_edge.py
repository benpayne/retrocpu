"""
Test UART RX edge detection - verify sticky rx_ready converts to single-shot capture
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, Timer


async def send_uart_byte(dut, data, baud_rate=9600):
    """Send a complete UART byte on RX line"""
    bit_period_ns = int((1000000000 / baud_rate))
    
    # Start bit
    dut.rx.value = 0
    await Timer(bit_period_ns, unit="ns")
    
    # Data bits (LSB first)
    for i in range(8):
        bit = (data >> i) & 1
        dut.rx.value = bit
        await Timer(bit_period_ns, unit="ns")
    
    # Stop bit
    dut.rx.value = 1
    await Timer(bit_period_ns, unit="ns")


@cocotb.test()
async def test_uart_rx_edge_detection(dut):
    """Test that RX edge detection prevents reading stale data"""
    
    clock = Clock(dut.clk, 40, unit="ns")  # 25 MHz
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    dut.rx.value = 1  # Idle HIGH
    await ClockCycles(dut.clk, 10)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 10)
    
    dut._log.info("=== Test RX Edge Detection ===")
    
    # Send first byte: 0x55
    dut._log.info("Sending 0x55...")
    await send_uart_byte(dut, 0x55)
    await ClockCycles(dut.clk, 100)
    
    # Read status - should show RX ready
    dut.cs.value = 1
    dut.we.value = 0
    dut.addr.value = 0x01  # STATUS register
    await RisingEdge(dut.clk)
    status1 = int(dut.data_out.value)
    rx_ready1 = (status1 >> 1) & 1
    dut._log.info(f"Status after byte 1: 0x{status1:02X}, RX ready: {rx_ready1}")
    assert rx_ready1 == 1, "RX ready should be set after reception"
    
    # Read data register
    dut.addr.value = 0x00  # DATA register
    await RisingEdge(dut.clk)
    data1 = int(dut.data_out.value)
    dut._log.info(f"Read data: 0x{data1:02X}")
    assert data1 == 0x55, f"Expected 0x55, got 0x{data1:02X}"
    
    # Deselect
    dut.cs.value = 0
    await ClockCycles(dut.clk, 10)
    
    # Read status again - should be cleared after reading DATA
    dut.cs.value = 1
    dut.addr.value = 0x01  # STATUS register
    await RisingEdge(dut.clk)
    status2 = int(dut.data_out.value)
    rx_ready2 = (status2 >> 1) & 1
    dut._log.info(f"Status after read: 0x{status2:02X}, RX ready: {rx_ready2}")
    assert rx_ready2 == 0, "RX ready should be cleared after reading DATA"
    
    # Try reading data again - should get same stale value (0x55)
    # but reading it shouldn't set rx_ready again (that's the key test!)
    dut.addr.value = 0x00  # DATA register
    await RisingEdge(dut.clk)
    data2 = int(dut.data_out.value)
    dut._log.info(f"Read data again (stale): 0x{data2:02X}")
    
    dut.cs.value = 0
    await ClockCycles(dut.clk, 10)
    
    # Check status - should STILL be 0 (no spurious ready)
    dut.cs.value = 1
    dut.addr.value = 0x01
    await RisingEdge(dut.clk)
    status3 = int(dut.data_out.value)
    rx_ready3 = (status3 >> 1) & 1
    dut._log.info(f"Status after stale read: 0x{status3:02X}, RX ready: {rx_ready3}")
    assert rx_ready3 == 0, "RX ready should NOT reappear after reading stale data"
    
    dut.cs.value = 0
    await ClockCycles(dut.clk, 10)
    
    # Send second byte: 0xAA
    dut._log.info("Sending 0xAA...")
    await send_uart_byte(dut, 0xAA)
    await ClockCycles(dut.clk, 100)
    
    # Check status - should show RX ready again (new data)
    dut.cs.value = 1
    dut.addr.value = 0x01
    await RisingEdge(dut.clk)
    status4 = int(dut.data_out.value)
    rx_ready4 = (status4 >> 1) & 1
    dut._log.info(f"Status after byte 2: 0x{status4:02X}, RX ready: {rx_ready4}")
    assert rx_ready4 == 1, "RX ready should be set for new byte"
    
    # Read new data
    dut.addr.value = 0x00
    await RisingEdge(dut.clk)
    data3 = int(dut.data_out.value)
    dut._log.info(f"Read new data: 0x{data3:02X}")
    assert data3 == 0xAA, f"Expected 0xAA, got 0x{data3:02X}"
    
    dut._log.info("✓ Edge detection test passed!")


@cocotb.test()
async def test_uart_rx_no_spurious_ready(dut):
    """Test that rx_ready doesn't spuriously appear after idle"""
    
    clock = Clock(dut.clk, 40, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    dut.rx.value = 1
    await ClockCycles(dut.clk, 10)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 10)
    
    dut._log.info("=== Test No Spurious RX Ready ===")
    
    # Check status after reset - should be 0
    dut.cs.value = 1
    dut.we.value = 0
    dut.addr.value = 0x01
    
    for i in range(100):
        await RisingEdge(dut.clk)
        status = int(dut.data_out.value)
        rx_ready = (status >> 1) & 1
        
        if i % 20 == 0:
            dut._log.info(f"Poll {i}: status=0x{status:02X}, rx_ready={rx_ready}")
        
        assert rx_ready == 0, f"RX ready should be 0 when idle (poll {i})"
    
    dut._log.info("✓ No spurious ready after 100 polls")
