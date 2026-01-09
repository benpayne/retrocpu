"""
Integration test for XMODEM binary upload to RetroCPU monitor

Tests the XMODEM protocol implementation in the monitor firmware.
Simulates a terminal sending binary data via XMODEM and verifies:
- Protocol handshaking (NAK to start, ACK/NAK responses)
- Packet reception and validation
- Checksum verification
- Error recovery on corrupted packets
- Binary data correctly written to RAM
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer
from cocotb.utils import get_sim_time


# XMODEM protocol constants
SOH = 0x01  # Start of Header
EOT = 0x04  # End of Transmission
ACK = 0x06  # Acknowledge
NAK = 0x15  # Negative Acknowledge
CAN = 0x18  # Cancel


class UARTInterface:
    """Bidirectional UART interface for XMODEM communication"""

    def __init__(self, dut, baud_rate=9600, clk_freq=25e6):
        self.dut = dut
        self.baud_rate = baud_rate
        self.bit_time_ns = (1.0 / baud_rate) * 1e9
        self.tx_line = dut.uart_tx  # Monitor transmits on this line
        self.rx_chars = []  # Characters received from monitor
        self.running = False

    async def start_monitor(self):
        """Start monitoring UART TX line (monitor to terminal)"""
        self.running = True

        while self.running:
            try:
                # Wait for start bit (falling edge)
                await FallingEdge(self.tx_line)

                # Wait half a bit time to sample in middle
                await Timer(self.bit_time_ns / 2, units='ns')

                # Verify start bit is still low
                if self.tx_line.value != 0:
                    continue

                # Wait to first data bit
                await Timer(self.bit_time_ns, units='ns')

                # Read 8 data bits (LSB first)
                byte_val = 0
                for i in range(8):
                    bit = int(self.tx_line.value)
                    byte_val |= (bit << i)
                    await Timer(self.bit_time_ns, units='ns')

                # Read stop bit
                stop_bit = int(self.tx_line.value)

                timestamp = get_sim_time(units='us')
                char = chr(byte_val) if 32 <= byte_val <= 126 else f'<{byte_val:02X}>'

                self.rx_chars.append(byte_val)
                cocotb.log.info(f"[{timestamp:8.1f}us] Monitor TX: 0x{byte_val:02X} {char}")

            except Exception as e:
                if self.running:
                    cocotb.log.error(f"UART monitor error: {e}")
                break

    def stop_monitor(self):
        """Stop monitoring"""
        self.running = False

    async def send_byte(self, byte_val):
        """
        Send a byte to monitor via UART RX line
        This simulates terminal sending to monitor
        NOTE: This would require UART RX to be implemented in the SoC
        """
        # TODO: Implement UART RX transmission simulation
        # For now, this is a placeholder that would need:
        # 1. Access to uart_rx signal in DUT
        # 2. Bit-banging the UART protocol (start bit, 8 data bits, stop bit)
        cocotb.log.info(f"Sending byte to monitor: 0x{byte_val:02X}")
        pass

    async def wait_for_response(self, expected_bytes, timeout_ms=1000):
        """
        Wait for specific bytes from monitor
        Returns True if received, False on timeout
        """
        start_time = get_sim_time(units='ms')
        start_idx = len(self.rx_chars)

        while True:
            current_time = get_sim_time(units='ms')
            if current_time - start_time > timeout_ms:
                return False

            # Check if we've received the expected bytes
            if len(self.rx_chars) >= start_idx + len(expected_bytes):
                received = self.rx_chars[start_idx:start_idx + len(expected_bytes)]
                if received == list(expected_bytes):
                    return True

            await Timer(100, units='us')


def create_xmodem_packet(packet_num, data):
    """
    Create an XMODEM packet

    Args:
        packet_num: Packet number (1-255)
        data: 128 bytes of data

    Returns:
        132-byte packet: SOH + PKT# + ~PKT# + DATA[128] + CHECKSUM
    """
    assert len(data) == 128, "Data must be exactly 128 bytes"
    assert 1 <= packet_num <= 255, "Packet number must be 1-255"

    packet = bytearray()
    packet.append(SOH)
    packet.append(packet_num)
    packet.append(255 - packet_num)  # Packet number complement
    packet.extend(data)

    # Calculate checksum (simple 8-bit sum)
    checksum = sum(data) & 0xFF
    packet.append(checksum)

    return bytes(packet)


def corrupt_checksum(packet):
    """Corrupt the checksum of an XMODEM packet"""
    corrupt = bytearray(packet)
    corrupt[-1] = (corrupt[-1] + 1) & 0xFF  # Change last byte (checksum)
    return bytes(corrupt)


@cocotb.test()
async def test_xmodem_basic_upload(dut):
    """
    Test basic XMODEM upload of 256-byte binary

    This test verifies:
    1. Monitor accepts L command with address
    2. Monitor sends NAK to initiate XMODEM
    3. Monitor accepts packets and sends ACK
    4. Monitor handles EOT and completes transfer
    5. Binary data is correctly written to RAM
    """

    # Start clock
    clock = Clock(dut.clk_25mhz, 40, unit="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    # Start UART monitor
    uart = UARTInterface(dut, baud_rate=9600)
    monitor_task = cocotb.start_soon(uart.start_monitor())

    dut._log.info("=== Test XMODEM Basic Upload (256 bytes) ===")

    # Reset
    dut.reset_button_n.value = 0
    await ClockCycles(dut.clk_25mhz, 100)
    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 100)

    dut._log.info("System reset complete")

    # Wait for monitor to boot and print banner
    # Each char at 9600 baud takes ~1ms, banner is ~500 chars
    # So we need at least 500ms, but simulation is slow
    dut._log.info("Waiting for monitor boot banner...")
    await ClockCycles(dut.clk_25mhz, int(10e-3 * 25e6))  # 10ms

    # TODO: This test requires UART RX to be fully implemented
    # The following is the test structure that would run when UART RX is available:

    # Step 1: Send "L 0300" command
    # for char in "L 0300\r":
    #     await uart.send_byte(ord(char))

    # Step 2: Wait for monitor to send NAK (start XMODEM)
    # nak_received = await uart.wait_for_response([NAK], timeout_ms=2000)
    # assert nak_received, "Monitor did not send NAK to start XMODEM"

    # Step 3: Send packet 1 (first 128 bytes)
    # test_data_1 = bytes(range(0, 128))  # 0x00-0x7F
    # packet_1 = create_xmodem_packet(1, test_data_1)
    # for byte in packet_1:
    #     await uart.send_byte(byte)

    # Step 4: Wait for ACK
    # ack_received = await uart.wait_for_response([ACK], timeout_ms=2000)
    # assert ack_received, "Monitor did not ACK packet 1"

    # Step 5: Send packet 2 (next 128 bytes)
    # test_data_2 = bytes(range(128, 256))  # 0x80-0xFF
    # packet_2 = create_xmodem_packet(2, test_data_2)
    # for byte in packet_2:
    #     await uart.send_byte(byte)

    # Step 6: Wait for ACK
    # ack_received = await uart.wait_for_response([ACK], timeout_ms=2000)
    # assert ack_received, "Monitor did not ACK packet 2"

    # Step 7: Send EOT
    # await uart.send_byte(EOT)

    # Step 8: Wait for final ACK
    # ack_received = await uart.wait_for_response([ACK], timeout_ms=2000)
    # assert ack_received, "Monitor did not ACK EOT"

    # Step 9: Verify data in RAM at $0300
    # This would require reading RAM through CPU or memory interface

    dut._log.info("\n" + "="*60)
    dut._log.info("TEST STATUS: PLACEHOLDER - UART RX NOT YET IMPLEMENTED")
    dut._log.info("="*60)
    dut._log.info("This test structure is ready for when UART RX is available.")
    dut._log.info("It will test:")
    dut._log.info("  - L command parsing and address validation")
    dut._log.info("  - XMODEM handshaking (NAK to start)")
    dut._log.info("  - Packet reception and ACK/NAK responses")
    dut._log.info("  - EOT handling")
    dut._log.info("  - Data written to RAM at correct address")

    # For now, just verify the system boots
    uart.stop_monitor()
    await monitor_task

    assert len(uart.rx_chars) > 0, "No UART output - system not running"
    dut._log.info(f"✓ System is running - received {len(uart.rx_chars)} chars")


@cocotb.test()
async def test_xmodem_checksum_error_recovery(dut):
    """
    Test XMODEM checksum error recovery

    This test verifies:
    1. Monitor detects corrupted packet (bad checksum)
    2. Monitor sends NAK on checksum error
    3. Monitor accepts retransmitted packet
    4. Transfer completes successfully after recovery
    """

    # Start clock
    clock = Clock(dut.clk_25mhz, 40, unit="ns")
    cocotb.start_soon(clock.start())

    uart = UARTInterface(dut, baud_rate=9600)
    monitor_task = cocotb.start_soon(uart.start_monitor())

    dut._log.info("=== Test XMODEM Checksum Error Recovery ===")

    # Reset
    dut.reset_button_n.value = 0
    await ClockCycles(dut.clk_25mhz, 100)
    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 100)

    # TODO: This test requires UART RX implementation
    # Test structure:

    # Step 1: Start XMODEM transfer (L 0400)
    # Step 2: Send packet 1 with correct checksum - verify ACK
    # Step 3: Send packet 2 with WRONG checksum - verify NAK
    # Step 4: Resend packet 2 with correct checksum - verify ACK
    # Step 5: Send packet 3 with correct checksum - verify ACK
    # Step 6: Send EOT - verify ACK
    # Step 7: Verify all data in RAM

    dut._log.info("\n" + "="*60)
    dut._log.info("TEST STATUS: PLACEHOLDER - UART RX NOT YET IMPLEMENTED")
    dut._log.info("="*60)
    dut._log.info("This test will verify checksum error detection and recovery:")
    dut._log.info("  - Bad checksum triggers NAK")
    dut._log.info("  - Good retransmission triggers ACK")
    dut._log.info("  - Transfer continues after error recovery")

    uart.stop_monitor()
    await monitor_task

    assert len(uart.rx_chars) > 0, "No UART output - system not running"
    dut._log.info(f"✓ System is running - received {len(uart.rx_chars)} chars")


@cocotb.test()
async def test_xmodem_address_validation(dut):
    """
    Test XMODEM address validation

    This test verifies:
    1. L command rejects address < $0200 (too low)
    2. L command rejects address > $7FFF (ROM/IO space)
    3. L command accepts valid address range $0200-$7FFF
    """

    # Start clock
    clock = Clock(dut.clk_25mhz, 40, unit="ns")
    cocotb.start_soon(clock.start())

    uart = UARTInterface(dut, baud_rate=9600)
    monitor_task = cocotb.start_soon(uart.start_monitor())

    dut._log.info("=== Test XMODEM Address Validation ===")

    # Reset
    dut.reset_button_n.value = 0
    await ClockCycles(dut.clk_25mhz, 100)
    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 100)

    # TODO: This test requires UART RX implementation
    # Test structure:

    # Test Case 1: Address too low
    # Send: "L 0100\r"
    # Expect: Error message "Address too low (min: 0200)"
    # Verify: No NAK sent (XMODEM not started)

    # Test Case 2: Address in ROM space
    # Send: "L 8000\r"
    # Expect: Error message "Address in ROM/IO space (max: 7FFF)"
    # Verify: No NAK sent

    # Test Case 3: Valid address at boundary
    # Send: "L 0200\r"
    # Expect: "Ready to receive XMODEM..."
    # Verify: NAK sent

    # Test Case 4: Valid address at upper boundary
    # Send: "L 7FFF\r"
    # Expect: "Ready to receive XMODEM..."
    # Verify: NAK sent

    dut._log.info("\n" + "="*60)
    dut._log.info("TEST STATUS: PLACEHOLDER - UART RX NOT YET IMPLEMENTED")
    dut._log.info("="*60)
    dut._log.info("This test will verify address validation:")
    dut._log.info("  - Reject L 0100 (too low)")
    dut._log.info("  - Reject L 8000 (ROM space)")
    dut._log.info("  - Accept L 0200 (valid lower bound)")
    dut._log.info("  - Accept L 7FFF (valid upper bound)")

    uart.stop_monitor()
    await monitor_task

    assert len(uart.rx_chars) > 0, "No UART output - system not running"
    dut._log.info(f"✓ System is running - received {len(uart.rx_chars)} chars")


@cocotb.test()
async def test_xmodem_timeout_handling(dut):
    """
    Test XMODEM timeout handling

    This test verifies:
    1. Monitor times out if no data received after NAK
    2. Monitor sends error message on timeout
    3. Monitor returns to command prompt
    """

    # Start clock
    clock = Clock(dut.clk_25mhz, 40, unit="ns")
    cocotb.start_soon(clock.start())

    uart = UARTInterface(dut, baud_rate=9600)
    monitor_task = cocotb.start_soon(uart.start_monitor())

    dut._log.info("=== Test XMODEM Timeout Handling ===")

    # Reset
    dut.reset_button_n.value = 0
    await ClockCycles(dut.clk_25mhz, 100)
    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 100)

    # TODO: This test requires UART RX implementation
    # Test structure:

    # Step 1: Send L command
    # Send: "L 0300\r"
    # Expect: NAK

    # Step 2: Wait for timeout (10 seconds in real hardware, shorter in sim)
    # Do not send any data

    # Step 3: Verify timeout error message
    # Expect: "Transfer failed: timeout"
    # Expect: Prompt ">"

    dut._log.info("\n" + "="*60)
    dut._log.info("TEST STATUS: PLACEHOLDER - UART RX NOT YET IMPLEMENTED")
    dut._log.info("="*60)
    dut._log.info("This test will verify timeout handling:")
    dut._log.info("  - Monitor times out after 10 seconds of no data")
    dut._log.info("  - Error message displayed")
    dut._log.info("  - Returns to command prompt")

    uart.stop_monitor()
    await monitor_task

    assert len(uart.rx_chars) > 0, "No UART output - system not running"
    dut._log.info(f"✓ System is running - received {len(uart.rx_chars)} chars")
