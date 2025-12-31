#!/usr/bin/env python3
"""
Test suite for LCD display via monitor commands.

Tests the LCD controller at $C100-$C102:
- $C100: Data register (write ASCII character)
- $C101: Command register (write HD44780 command)
- $C102: Status register (read busy flag)
"""

import pytest
import time


class TestLCDDisplay:
    """Test LCD display functionality via monitor D commands."""

    def test_lcd_status_readable(self, monitor):
        """Test that LCD status register is readable."""
        # Read LCD status at $C102
        status = monitor.examine('C102')
        assert status is not None, "Should be able to read LCD status"
        assert len(status) == 2, "Status should be 2-digit hex"

        # Convert to int and check format
        status_val = int(status, 16)
        print(f"LCD Status: 0x{status_val:02X}")

        # Busy flag is in bit 0
        busy = status_val & 0x01
        print(f"  Busy flag: {busy}")

    def test_lcd_write_command(self, monitor):
        """Test writing command to LCD command register."""
        # Write clear display command (0x01) to $C101
        result = monitor.deposit('C101', '01')
        assert result, "Should be able to write to LCD command register"

        time.sleep(0.1)  # Give LCD time to process

    def test_lcd_write_data(self, monitor):
        """Test writing ASCII data to LCD data register."""
        # Write 'A' (0x41) to $C100
        result = monitor.deposit('C100', '41')
        assert result, "Should be able to write to LCD data register"

        time.sleep(0.05)

    def test_lcd_clear_display(self, monitor):
        """Test LCD clear display command."""
        # Clear display (0x01)
        result = monitor.deposit('C101', '01')
        assert result, "Clear display command should succeed"

        time.sleep(0.02)  # Clear needs extra time

        # Display on, cursor off (0x0C)
        result = monitor.deposit('C101', '0C')
        assert result, "Display on command should succeed"

        time.sleep(0.01)

    def test_lcd_write_hello(self, monitor):
        """Test writing 'HELLO' to LCD display."""
        # Initialize LCD
        # Clear display
        monitor.deposit('C101', '01')
        time.sleep(0.02)

        # Display on, cursor off
        monitor.deposit('C101', '0C')
        time.sleep(0.01)

        # Entry mode: increment, no shift
        monitor.deposit('C101', '06')
        time.sleep(0.01)

        # Set cursor to home (0x80)
        monitor.deposit('C101', '80')
        time.sleep(0.01)

        # Write "HELLO"
        for ch in "HELLO":
            result = monitor.deposit('C100', f'{ord(ch):02X}')
            assert result, f"Should write '{ch}' to LCD"
            time.sleep(0.01)

        print("Written 'HELLO' to LCD line 1")

    def test_lcd_two_lines(self, monitor):
        """Test writing to both lines of LCD display."""
        # Initialize LCD
        monitor.deposit('C101', '01')  # Clear
        time.sleep(0.02)

        monitor.deposit('C101', '0C')  # Display on
        time.sleep(0.01)

        monitor.deposit('C101', '06')  # Entry mode
        time.sleep(0.01)

        # Write "HELLO" to line 1
        monitor.deposit('C101', '80')  # Set cursor to line 1, column 0
        time.sleep(0.01)

        for ch in "HELLO":
            monitor.deposit('C100', f'{ord(ch):02X}')
            time.sleep(0.01)

        # Write "WORLD" to line 2
        monitor.deposit('C101', 'C0')  # Set cursor to line 2, column 0 (0x80 | 0x40)
        time.sleep(0.01)

        for ch in "WORLD":
            monitor.deposit('C100', f'{ord(ch):02X}')
            time.sleep(0.01)

        print("Written 'HELLO' to line 1, 'WORLD' to line 2")

    def test_lcd_numbers(self, monitor):
        """Test writing numbers to LCD."""
        # Initialize
        monitor.deposit('C101', '01')  # Clear
        time.sleep(0.02)

        monitor.deposit('C101', '0C')  # Display on
        time.sleep(0.01)

        monitor.deposit('C101', '80')  # Home position
        time.sleep(0.01)

        # Write "0123456789"
        for i in range(10):
            ch = str(i)
            monitor.deposit('C100', f'{ord(ch):02X}')
            time.sleep(0.01)

        print("Written '0123456789' to LCD")

    def test_lcd_cursor_position(self, monitor):
        """Test setting cursor position."""
        # Initialize
        monitor.deposit('C101', '01')  # Clear
        time.sleep(0.02)

        monitor.deposit('C101', '0C')  # Display on
        time.sleep(0.01)

        # Write at different positions on line 1
        positions = [
            (0x80, 'A'),  # Column 0
            (0x85, 'B'),  # Column 5
            (0x8A, 'C'),  # Column 10
            (0x8F, 'D'),  # Column 15
        ]

        for pos, char in positions:
            monitor.deposit('C101', f'{pos:02X}')  # Set position
            time.sleep(0.01)
            monitor.deposit('C100', f'{ord(char):02X}')  # Write character
            time.sleep(0.01)

        print("Written characters at different positions")

    def test_lcd_full_alphabet(self, monitor):
        """Test writing full alphabet."""
        # Initialize
        monitor.deposit('C101', '01')  # Clear
        time.sleep(0.02)

        monitor.deposit('C101', '0C')  # Display on
        time.sleep(0.01)

        # Line 1: A-P
        monitor.deposit('C101', '80')  # Line 1
        time.sleep(0.01)

        for i in range(16):
            ch = chr(ord('A') + i)
            monitor.deposit('C100', f'{ord(ch):02X}')
            time.sleep(0.01)

        # Line 2: Q-Z
        monitor.deposit('C101', 'C0')  # Line 2
        time.sleep(0.01)

        for i in range(16, 26):
            ch = chr(ord('A') + i)
            monitor.deposit('C100', f'{ord(ch):02X}')
            time.sleep(0.01)

        print("Written alphabet A-Z to LCD")


@pytest.mark.slow
class TestLCDStress:
    """Stress tests for LCD display."""

    def test_lcd_rapid_writes(self, monitor):
        """Test rapid character writes to LCD."""
        # Initialize
        monitor.deposit('C101', '01')
        time.sleep(0.02)

        monitor.deposit('C101', '0C')
        time.sleep(0.01)

        monitor.deposit('C101', '80')
        time.sleep(0.01)

        # Write 32 characters (fill both lines)
        message = "RETROCPU 6502 FPGA SYSTEM V1"
        for ch in message[:32]:  # Limit to 32 chars (16 per line)
            monitor.deposit('C100', f'{ord(ch):02X}')
            time.sleep(0.01)

        print(f"Written message: {message[:32]}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
