"""
Test full SoC with monitor firmware - see what CPU actually sends to UART
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer
from cocotb.utils import get_sim_time


class UARTMonitor:
    """Monitor UART TX line and decode characters"""

    def __init__(self, tx_signal, baud_rate=9600, clk_freq=25e6):
        self.tx = tx_signal
        self.baud_rate = baud_rate
        self.bit_time = 1.0 / baud_rate  # seconds
        self.bit_time_ns = self.bit_time * 1e9  # nanoseconds
        self.characters = []
        self.running = False

    async def start(self):
        """Start monitoring UART TX line"""
        self.running = True

        while self.running:
            # Wait for start bit (falling edge)
            await FallingEdge(self.tx)

            # Wait half a bit time to sample in the middle
            await Timer(self.bit_time_ns / 2, units='ns')

            # Verify start bit is still low
            if self.tx.value != 0:
                continue  # False start

            # Wait to first data bit
            await Timer(self.bit_time_ns, units='ns')

            # Read 8 data bits (LSB first)
            byte_val = 0
            for i in range(8):
                bit = int(self.tx.value)
                byte_val |= (bit << i)
                await Timer(self.bit_time_ns, units='ns')

            # Read stop bit (should be high)
            stop_bit = int(self.tx.value)

            char = chr(byte_val) if 32 <= byte_val <= 126 else f'\\x{byte_val:02x}'
            timestamp = get_sim_time(units='us')

            self.characters.append((timestamp, byte_val, char))
            cocotb.log.info(f"[{timestamp:8.1f}us] UART RX: 0x{byte_val:02X} '{char}' (stop={stop_bit})")

    def stop(self):
        """Stop monitoring"""
        self.running = False

    def get_string(self):
        """Get received characters as string"""
        result = ""
        for _, byte_val, char in self.characters:
            if 32 <= byte_val <= 126:
                result += chr(byte_val)
            else:
                result += f'[{byte_val:02X}]'
        return result


@cocotb.test()
async def test_monitor_boot(dut):
    """Test monitor firmware boot sequence"""

    # Start clock
    clock = Clock(dut.clk_25mhz, 40, unit="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    # Start UART monitor
    uart_mon = UARTMonitor(dut.uart_tx, baud_rate=9600, clk_freq=25e6)
    monitor_task = cocotb.start_soon(uart_mon.start())

    dut._log.info("=== Testing Monitor Firmware Boot ===")

    # Reset
    dut.reset_button_n.value = 0  # Active low reset
    await ClockCycles(dut.clk_25mhz, 100)
    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 100)

    dut._log.info("System out of reset, monitoring UART...")

    # Run for a short time to capture first character
    # At 9600 baud, each char takes ~1ms, so 5ms should give us ~5 chars
    # (with holdoff disabled in simulation, but simulation is VERY slow)
    run_time_ms = 5  # 5ms should give us a few chars
    cycles = int(run_time_ms * 1e-3 * 25e6)

    dut._log.info(f"Running for {run_time_ms}ms ({cycles} cycles)...")

    await ClockCycles(dut.clk_25mhz, cycles)

    uart_mon.stop()
    await monitor_task

    # Print results
    dut._log.info(f"\n{'='*60}")
    dut._log.info(f"UART Output Captured: {len(uart_mon.characters)} characters")
    dut._log.info(f"{'='*60}")

    output = uart_mon.get_string()
    dut._log.info(f"String: {output}")

    # Show first 20 characters in detail
    dut._log.info(f"\nFirst 20 characters:")
    for i, (ts, byte_val, char) in enumerate(uart_mon.characters[:20]):
        dut._log.info(f"  {i:2d}: [{ts:8.1f}us] 0x{byte_val:02X} '{char}'")

    # Check if we got expected monitor output
    if len(uart_mon.characters) == 0:
        dut._log.error("✗ NO UART OUTPUT - CPU may not be running")
        assert False, "No UART output received"

    # Check for 'X' debug character (first thing monitor sends)
    first_char = uart_mon.characters[0][1]
    if first_char == ord('X'):
        dut._log.info("✓ Got debug 'X' character")
    else:
        dut._log.warning(f"✗ First char was 0x{first_char:02X}, expected 0x58 'X'")

    # Look for monitor banner
    if 'RetroCPU' in output or 'Monitor' in output:
        dut._log.info("✓ Found monitor banner text")
    else:
        dut._log.warning("✗ Did not find expected monitor banner")

    dut._log.info(f"\n✓ Test complete - captured {len(uart_mon.characters)} chars")
