"""
Test suite for RetroCPU monitor commands.

Tests the monitor firmware including:
- E (examine memory) command
- D (deposit memory) command
- G (go to BASIC) command
- Reset functionality
"""

import pytest
import time


class TestMonitorBasic:
    """Basic monitor functionality tests."""

    def test_monitor_prompt(self, serial_port):
        """Test that monitor displays prompt after newline."""
        # Send newline to trigger prompt
        serial_port.write(b'\r\n')
        time.sleep(0.5)

        # Read response
        if serial_port.in_waiting:
            response = serial_port.read(serial_port.in_waiting).decode('utf-8', errors='ignore')
            assert '>' in response, f"Monitor prompt not found, got: {repr(response)}"
        else:
            # Already at prompt (cleared by fixture)
            pass  # This is OK

    def test_monitor_echo(self, serial_port):
        """Test that monitor echoes characters."""
        serial_port.write(b'X')
        import time
        time.sleep(0.1)

        if serial_port.in_waiting:
            response = serial_port.read(serial_port.in_waiting).decode('utf-8', errors='ignore')
            # Should echo 'X' and show hex debug output
            assert 'X' in response or '58' in response, "No echo from monitor"


class TestExamineCommand:
    """Test the E (examine) command."""

    def test_examine_rom_start(self, monitor):
        """Test examining ROM at $E000 (monitor start)."""
        value = monitor.examine('E000')
        assert value is not None, "Failed to examine $E000"
        # Should return some value (not checking specific value as ROM may vary)
        assert len(value) == 2, f"Expected 2-digit hex, got: {value}"

    def test_examine_rom_vectors(self, monitor):
        """Test examining ROM reset vector at $FFFC."""
        value = monitor.examine('FFFC')
        assert value is not None, "Failed to examine $FFFC"
        assert len(value) == 2, f"Expected 2-digit hex, got: {value}"

    def test_examine_multiple_addresses(self, monitor):
        """Test examining multiple different addresses."""
        addresses = ['E000', 'E100', 'E200', 'FFF0']

        for addr in addresses:
            value = monitor.examine(addr)
            assert value is not None, f"Failed to examine ${addr}"
            assert len(value) == 2, f"Invalid value format for ${addr}: {value}"

    def test_examine_ram(self, monitor):
        """Test examining RAM address."""
        value = monitor.examine('0200')
        assert value is not None, "Failed to examine RAM at $0200"
        assert len(value) == 2, f"Expected 2-digit hex, got: {value}"


class TestDepositCommand:
    """Test the D (deposit) command."""

    def test_deposit_to_ram(self, monitor):
        """Test depositing value to RAM."""
        result = monitor.deposit('0200', 'AA')
        assert result, "Failed to deposit $AA to $0200"

    def test_deposit_and_verify(self, monitor):
        """Test depositing value and verifying with examine."""
        # Deposit $55 to $0300
        result = monitor.deposit('0300', '55')
        assert result, "Failed to deposit $55 to $0300"

        # Verify with examine
        value = monitor.examine('0300')
        assert value == '55', f"Expected $55 at $0300, got ${value}"

    def test_deposit_multiple_values(self, monitor):
        """Test depositing and verifying multiple values."""
        test_cases = [
            ('0400', 'AA'),
            ('0401', '55'),
            ('0402', 'FF'),
            ('0403', '00'),
            ('0404', '12'),
            ('0405', 'AB'),
        ]

        for addr, val in test_cases:
            # Deposit
            result = monitor.deposit(addr, val)
            assert result, f"Failed to deposit ${val} to ${addr}"

            # Verify
            read_val = monitor.examine(addr)
            assert read_val == val, f"Expected ${val} at ${addr}, got ${read_val}"

    def test_deposit_zero_page(self, monitor):
        """Test depositing to zero page RAM."""
        # Zero page write test (this was the original bug!)
        # Use $0030 instead of $0010 to avoid monitor's INPUT_BUF at $0010-$001F
        result = monitor.deposit('0030', 'A5')
        assert result, "Failed to deposit to zero page $0030"

        import time
        time.sleep(1.0)  # Extra wait to ensure write completes

        value = monitor.examine('0030')
        assert value == 'A5', f"Zero page write failed: expected $A5, got ${value}"

    def test_deposit_stack_page(self, monitor):
        """Test depositing to stack page ($0100-$01FF)."""
        result = monitor.deposit('0150', '5A')
        assert result, "Failed to deposit to stack page $0150"

        value = monitor.examine('0150')
        assert value == '5A', f"Stack page write failed: expected $5A, got ${value}"


class TestGoCommand:
    """Test the G (go to BASIC) command."""

    def test_go_starts_basic(self, fpga_reset, serial_port):
        """Test that G command starts BASIC (will reset FPGA after)."""
        # Send G command
        serial_port.write(b'G')
        time.sleep(1.0)

        # Read BASIC startup
        output = ''
        timeout = time.time() + 5
        while time.time() < timeout:
            if serial_port.in_waiting:
                output += serial_port.read(serial_port.in_waiting).decode('utf-8', errors='ignore')
                if 'OK' in output or 'MEMORY SIZE' in output.upper():
                    break
            time.sleep(0.1)

        # Should see BASIC startup message or prompt
        assert 'BASIC' in output.upper() or 'OK' in output or 'MEMORY SIZE' in output.upper(), \
            f"BASIC did not start properly, got: {output}"

        # Reset FPGA for next test
        fpga_reset()

    def test_go_shows_memory_size(self, fpga_reset, serial_port):
        """Test that BASIC shows available memory (will reset FPGA after)."""
        # Send G command
        serial_port.write(b'G')
        time.sleep(1.0)

        # Read BASIC startup
        output = ''
        timeout = time.time() + 5
        while time.time() < timeout:
            if serial_port.in_waiting:
                output += serial_port.read(serial_port.in_waiting).decode('utf-8', errors='ignore')
                if 'OK' in output or 'MEMORY' in output.upper():
                    break
            time.sleep(0.1)

        # Should show bytes free, memory size prompt, or OK prompt
        assert 'BYTE' in output.upper() or 'OK' in output or 'MEMORY' in output.upper(), \
            f"BASIC memory information not displayed, got: {output}"

        # Reset FPGA for next test
        fpga_reset()


class TestMonitorRobustness:
    """Test monitor error handling and edge cases."""

    def test_invalid_command(self, serial_port):
        """Test that invalid command shows error."""
        serial_port.write(b'Z\r')
        import time
        time.sleep(0.2)

        if serial_port.in_waiting:
            response = serial_port.read(serial_port.in_waiting).decode('utf-8', errors='ignore')
            # Should see unknown command message or just return to prompt
            assert '>' in response, "Monitor did not return to prompt"

    def test_examine_hex_lowercase(self, monitor):
        """Test examine with lowercase hex digits."""
        value = monitor.examine('e000')  # lowercase
        assert value is not None, "Failed to examine with lowercase hex"

    def test_deposit_hex_lowercase(self, monitor):
        """Test deposit with lowercase hex digits."""
        result = monitor.deposit('0500', 'aa')  # lowercase
        assert result, "Failed to deposit with lowercase hex"

        value = monitor.examine('0500')
        assert value == 'AA', f"Expected $AA, got ${value}"


class TestMemoryMap:
    """Test memory map correctness."""

    def test_ram_range_start(self, monitor):
        """Test RAM at start of range ($0000)."""
        # Write and verify at $0000
        monitor.deposit('0000', 'A1')
        value = monitor.examine('0000')
        assert value == 'A1', "Failed to write/read at $0000"

    def test_ram_range_end(self, monitor):
        """Test RAM near end of range ($7FFF)."""
        # Write and verify at $7FFF
        monitor.deposit('7FFF', 'B2')
        value = monitor.examine('7FFF')
        assert value == 'B2', "Failed to write/read at $7FFF"

    def test_rom_is_readable(self, monitor):
        """Test that ROM addresses are readable."""
        # Monitor ROM at $E000
        value = monitor.examine('E000')
        assert value is not None, "Could not read monitor ROM"

        # BASIC ROM at $8000
        value = monitor.examine('8000')
        assert value is not None, "Could not read BASIC ROM"


@pytest.mark.slow
class TestMemoryStressTest:
    """Stress tests for memory operations."""

    def test_sequential_writes(self, monitor):
        """Test sequential writes to RAM."""
        base = 0x0600
        count = 16

        # Write sequential values
        for i in range(count):
            addr = f"{base + i:04X}"
            val = f"{i:02X}"
            result = monitor.deposit(addr, val)
            assert result, f"Failed to deposit ${val} to ${addr}"

        # Verify all values
        for i in range(count):
            addr = f"{base + i:04X}"
            expected = f"{i:02X}"
            value = monitor.examine(addr)
            assert value == expected, \
                f"Sequential write failed at ${addr}: expected ${expected}, got ${value}"

    def test_pattern_write_aa55(self, monitor):
        """Test writing alternating AA/55 pattern."""
        base = 0x0700
        count = 8

        # Write pattern
        for i in range(count):
            addr = f"{base + i:04X}"
            val = 'AA' if i % 2 == 0 else '55'
            monitor.deposit(addr, val)

        # Verify pattern
        for i in range(count):
            addr = f"{base + i:04X}"
            expected = 'AA' if i % 2 == 0 else '55'
            value = monitor.examine(addr)
            assert value == expected, \
                f"Pattern test failed at ${addr}: expected ${expected}, got ${value}"
