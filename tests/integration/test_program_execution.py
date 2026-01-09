"""
Integration test for program execution after XMODEM upload

Tests that programs uploaded via XMODEM can be successfully executed
using the G (Go) command.

This verifies the complete workflow:
1. Upload binary program via XMODEM
2. Execute program with G <address> command
3. Verify program runs correctly and produces expected output
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer
from cocotb.utils import get_sim_time


class UARTMonitor:
    """Monitor UART TX line and decode characters"""

    def __init__(self, tx_signal, baud_rate=9600):
        self.tx = tx_signal
        self.baud_rate = baud_rate
        self.bit_time_ns = (1.0 / baud_rate) * 1e9
        self.characters = []
        self.running = False

    async def start(self):
        """Start monitoring UART TX line"""
        self.running = True

        while self.running:
            try:
                # Wait for start bit
                await FallingEdge(self.tx)

                # Wait half a bit time
                await Timer(self.bit_time_ns / 2, units='ns')

                # Verify start bit
                if self.tx.value != 0:
                    continue

                # Wait to first data bit
                await Timer(self.bit_time_ns, units='ns')

                # Read 8 data bits (LSB first)
                byte_val = 0
                for i in range(8):
                    bit = int(self.tx.value)
                    byte_val |= (bit << i)
                    await Timer(self.bit_time_ns, units='ns')

                # Read stop bit
                stop_bit = int(self.tx.value)

                timestamp = get_sim_time(units='us')
                char = chr(byte_val) if 32 <= byte_val <= 126 else f'<{byte_val:02X}>'

                self.characters.append((timestamp, byte_val, char))
                cocotb.log.info(f"[{timestamp:8.1f}us] UART RX: 0x{byte_val:02X} {char}")

            except Exception as e:
                if self.running:
                    cocotb.log.error(f"UART monitor error: {e}")
                break

    def stop(self):
        """Stop monitoring"""
        self.running = False

    def get_string(self):
        """Get received characters as string"""
        result = ""
        for _, byte_val, char in self.characters:
            if 32 <= byte_val <= 126:
                result += chr(byte_val)
            elif byte_val == 0x0D:
                result += '\r'
            elif byte_val == 0x0A:
                result += '\n'
            else:
                result += f'[{byte_val:02X}]'
        return result

    def clear(self):
        """Clear received characters"""
        self.characters = []


@cocotb.test()
async def test_execute_uploaded_program(dut):
    """
    Test executing a program after XMODEM upload

    Expected flow:
    1. Upload simple test program to $0300 via XMODEM
    2. Execute program with "G 0300" command
    3. Program outputs "HELLO" to UART
    4. Verify output received
    """

    # Start clock
    clock = Clock(dut.clk_25mhz, 40, unit="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    # Start UART monitor
    uart_mon = UARTMonitor(dut.uart_tx, baud_rate=9600)
    monitor_task = cocotb.start_soon(uart_mon.start())

    dut._log.info("=== Test Program Execution After Upload ===")

    # Reset
    dut.reset_button_n.value = 0
    await ClockCycles(dut.clk_25mhz, 100)
    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 100)

    # Wait for monitor boot
    dut._log.info("Waiting for monitor boot...")
    await ClockCycles(dut.clk_25mhz, int(10e-3 * 25e6))  # 10ms

    # TODO: This test requires UART RX and full XMODEM implementation
    # Test workflow:

    # Step 1: Upload hello_world.bin via XMODEM
    # - Send "L 0300\r"
    # - Wait for NAK
    # - Send XMODEM packets with program code
    # - Wait for ACK
    # - Send EOT
    # - Wait for "Transfer complete" message

    # Step 2: Clear received buffer
    # uart_mon.clear()

    # Step 3: Execute program
    # - Send "G 0300\r"
    # - Wait for program to run

    # Step 4: Verify output
    # - Wait for "HELLO" string in UART output
    # - Verify program completed successfully

    # Example test program (hello_world.s assembled):
    # Should output "HELLO\r\n" and then return to monitor or loop

    dut._log.info("\n" + "="*60)
    dut._log.info("TEST STATUS: PLACEHOLDER - UART RX NOT YET IMPLEMENTED")
    dut._log.info("="*60)
    dut._log.info("This test will verify program execution after upload:")
    dut._log.info("  - Upload test program via XMODEM to $0300")
    dut._log.info("  - Execute with G 0300 command")
    dut._log.info("  - Verify program outputs 'HELLO' via UART")
    dut._log.info("  - Verify program returns or loops as expected")

    uart_mon.stop()
    await monitor_task

    assert len(uart_mon.characters) > 0, "No UART output - system not running"
    dut._log.info(f"✓ System is running - received {len(uart_mon.characters)} chars")


@cocotb.test()
async def test_execute_led_blink_program(dut):
    """
    Test executing LED blink program after upload

    Expected flow:
    1. Upload LED blink program to $0400
    2. Execute with G 0400
    3. Verify GPIO/LED outputs toggle at expected rate
    """

    # Start clock
    clock = Clock(dut.clk_25mhz, 40, unit="ns")
    cocotb.start_soon(clock.start())

    uart_mon = UARTMonitor(dut.uart_tx, baud_rate=9600)
    monitor_task = cocotb.start_soon(uart_mon.start())

    dut._log.info("=== Test LED Blink Program Execution ===")

    # Reset
    dut.reset_button_n.value = 0
    await ClockCycles(dut.clk_25mhz, 100)
    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 100)

    # TODO: This test requires UART RX and GPIO monitoring
    # Test workflow:

    # Step 1: Upload led_blink.bin via XMODEM to $0400

    # Step 2: Execute program
    # - Send "G 0400\r"

    # Step 3: Monitor GPIO outputs
    # - Check that LED outputs toggle
    # - Measure toggle frequency
    # - Verify matches expected blink rate

    # Step 4: (Optional) Send break to return to monitor
    # - Send Ctrl-C (0x03)
    # - Verify monitor prompt returns

    dut._log.info("\n" + "="*60)
    dut._log.info("TEST STATUS: PLACEHOLDER - UART RX NOT YET IMPLEMENTED")
    dut._log.info("="*60)
    dut._log.info("This test will verify LED blink program:")
    dut._log.info("  - Upload led_blink.bin to $0400")
    dut._log.info("  - Execute with G 0400")
    dut._log.info("  - Monitor GPIO for LED toggle")
    dut._log.info("  - Verify blink rate matches program")

    uart_mon.stop()
    await monitor_task

    assert len(uart_mon.characters) > 0, "No UART output - system not running"
    dut._log.info(f"✓ System is running")


@cocotb.test()
async def test_program_with_uart_output(dut):
    """
    Test program that uses UART via monitor vectors

    Programs should be able to call monitor CHROUT function
    to output characters via UART.
    """

    # Start clock
    clock = Clock(dut.clk_25mhz, 40, unit="ns")
    cocotb.start_soon(clock.start())

    uart_mon = UARTMonitor(dut.uart_tx, baud_rate=9600)
    monitor_task = cocotb.start_soon(uart_mon.start())

    dut._log.info("=== Test Program with UART Output ===")

    # Reset
    dut.reset_button_n.value = 0
    await ClockCycles(dut.clk_25mhz, 100)
    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 100)

    # TODO: This test requires full implementation
    # Test workflow:

    # Step 1: Upload test program that calls CHROUT vector
    # Program example:
    #   LDA #'H'
    #   JSR $FFF3  ; CHROUT vector
    #   LDA #'I'
    #   JSR $FFF3
    #   RTS

    # Step 2: Execute program
    # - Send "G 0300\r"

    # Step 3: Verify output
    # - Wait for "HI" in UART output
    # - Verify monitor prompt returns after RTS

    dut._log.info("\n" + "="*60)
    dut._log.info("TEST STATUS: PLACEHOLDER - UART RX NOT YET IMPLEMENTED")
    dut._log.info("="*60)
    dut._log.info("This test will verify programs can use monitor I/O:")
    dut._log.info("  - Upload program that calls CHROUT vector")
    dut._log.info("  - Execute program")
    dut._log.info("  - Verify output appears on UART")
    dut._log.info("  - Verify return to monitor after RTS")

    uart_mon.stop()
    await monitor_task

    assert len(uart_mon.characters) > 0, "No UART output - system not running"
    dut._log.info(f"✓ System is running")


@cocotb.test()
async def test_upload_to_multiple_addresses(dut):
    """
    Test uploading programs to different RAM addresses

    Verifies:
    1. Can upload to $0200 (lowest valid address)
    2. Can upload to $4000 (mid-range)
    3. Can upload to $7F00 (near upper limit)
    4. Programs at different addresses don't interfere
    """

    # Start clock
    clock = Clock(dut.clk_25mhz, 40, unit="ns")
    cocotb.start_soon(clock.start())

    uart_mon = UARTMonitor(dut.uart_tx, baud_rate=9600)
    monitor_task = cocotb.start_soon(uart_mon.start())

    dut._log.info("=== Test Upload to Multiple Addresses ===")

    # Reset
    dut.reset_button_n.value = 0
    await ClockCycles(dut.clk_25mhz, 100)
    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 100)

    # TODO: This test requires full implementation
    # Test workflow:

    # Upload program 1 to $0200 (outputs "A")
    # Upload program 2 to $4000 (outputs "B")
    # Upload program 3 to $7F00 (outputs "C")

    # Execute program 1: G 0200 -> verify "A"
    # Execute program 2: G 4000 -> verify "B"
    # Execute program 3: G 7F00 -> verify "C"

    # Verify all three still work after multiple executions

    dut._log.info("\n" + "="*60)
    dut._log.info("TEST STATUS: PLACEHOLDER - UART RX NOT YET IMPLEMENTED")
    dut._log.info("="*60)
    dut._log.info("This test will verify multiple program uploads:")
    dut._log.info("  - Upload to $0200, $4000, $7F00")
    dut._log.info("  - Execute each program independently")
    dut._log.info("  - Verify no interference between programs")

    uart_mon.stop()
    await monitor_task

    assert len(uart_mon.characters) > 0, "No UART output - system not running"
    dut._log.info(f"✓ System is running")
