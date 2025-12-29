#!/usr/bin/env python3
"""
Test Monitor Commands - Validation Script
==========================================

Tests the RetroCPU monitor command interface via UART.

Commands tested:
- H/h : Help command (displays available commands)
- E : Examine memory (currently shows "not yet implemented")
- D : Deposit to memory (currently shows "not yet implemented")
- Unknown : Error handling

Usage:
    python3 test_monitor_commands.py [--port /dev/ttyACM0] [--baud 9600]

Requirements:
    - pyserial: pip install pyserial
    - FPGA programmed with monitor firmware
    - Serial port available

Exit codes:
    0 - All tests passed
    1 - One or more tests failed
    2 - Cannot connect to serial port
"""

import serial
import time
import sys
import argparse
import re


class MonitorTest:
    def __init__(self, port='/dev/ttyACM0', baud=9600, timeout=2):
        """Initialize connection to monitor."""
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.ser = None
        self.test_results = []

    def connect(self):
        """Connect to serial port."""
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
            time.sleep(0.5)  # Let monitor settle
            self.ser.reset_input_buffer()
            print(f"✓ Connected to {self.port} at {self.baud} baud\n")
            return True
        except serial.SerialException as e:
            print(f"✗ Cannot connect to {self.port}: {e}", file=sys.stderr)
            return False

    def disconnect(self):
        """Close serial connection."""
        if self.ser:
            self.ser.close()

    def send_command(self, cmd, wait_time=0.5):
        """Send command and read response."""
        if not self.ser:
            return None

        # Send command
        self.ser.write(cmd.encode() + b'\r')
        time.sleep(wait_time)

        # Read all available response
        response = b''
        for _ in range(20):  # Read for up to 2 seconds
            if self.ser.in_waiting:
                response += self.ser.read(self.ser.in_waiting)
            time.sleep(0.1)
            if b'> ' in response:  # Wait for prompt
                break

        return response.decode('ascii', errors='replace')

    def test_help_command(self):
        """Test H command displays help."""
        print("Test: Help Command (H)")
        print("-" * 40)

        response = self.send_command('H')

        # Check for expected help text
        checks = [
            ('Available commands' in response, "Contains 'Available commands'"),
            ('E addr' in response, "Contains 'E addr' command"),
            ('D addr' in response, "Contains 'D addr' command"),
            ('H' in response or 'Help' in response, "Contains Help reference"),
        ]

        all_passed = all(check[0] for check in checks)

        for passed, desc in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {desc}")

        if all_passed:
            print("  ✓ Test PASSED\n")
        else:
            print("  ✗ Test FAILED\n")
            print(f"Response:\n{response}\n")

        self.test_results.append(('Help Command', all_passed))
        return all_passed

    def test_help_lowercase(self):
        """Test h command (lowercase) also works."""
        print("Test: Help Command (h - lowercase)")
        print("-" * 40)

        response = self.send_command('h')

        # Should get same help text
        checks = [
            ('Available commands' in response, "Contains 'Available commands'"),
            ('E addr' in response, "Contains 'E addr' command"),
        ]

        all_passed = all(check[0] for check in checks)

        for passed, desc in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {desc}")

        if all_passed:
            print("  ✓ Test PASSED (case-insensitive)\n")
        else:
            print("  ✗ Test FAILED\n")

        self.test_results.append(('Help Lowercase', all_passed))
        return all_passed

    def test_examine_command(self):
        """Test E command (currently stub)."""
        print("Test: Examine Command (E)")
        print("-" * 40)

        response = self.send_command('E')

        # For now, expect "not yet implemented" message
        checks = [
            ('not yet implemented' in response.lower(), "Shows 'not yet implemented'"),
            ('E\r\n' in response, "Echoes command"),
        ]

        all_passed = all(check[0] for check in checks)

        for passed, desc in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {desc}")

        if all_passed:
            print("  ✓ Test PASSED (stub acknowledged)\n")
        else:
            print("  ✗ Test FAILED\n")
            print(f"Response:\n{response}\n")

        self.test_results.append(('Examine Command', all_passed))
        return all_passed

    def test_deposit_command(self):
        """Test D command (currently stub)."""
        print("Test: Deposit Command (D)")
        print("-" * 40)

        response = self.send_command('D')

        # For now, expect "not yet implemented" message
        checks = [
            ('not yet implemented' in response.lower(), "Shows 'not yet implemented'"),
            ('D\r\n' in response, "Echoes command"),
        ]

        all_passed = all(check[0] for check in checks)

        for passed, desc in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {desc}")

        if all_passed:
            print("  ✓ Test PASSED (stub acknowledged)\n")
        else:
            print("  ✗ Test FAILED\n")
            print(f"Response:\n{response}\n")

        self.test_results.append(('Deposit Command', all_passed))
        return all_passed

    def test_unknown_command(self):
        """Test unknown command handling."""
        print("Test: Unknown Command (X)")
        print("-" * 40)

        response = self.send_command('X')

        checks = [
            ('Unknown command' in response, "Shows 'Unknown command'"),
            ('X\r\n' in response, "Echoes invalid command"),
        ]

        all_passed = all(check[0] for check in checks)

        for passed, desc in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {desc}")

        if all_passed:
            print("  ✓ Test PASSED\n")
        else:
            print("  ✗ Test FAILED\n")
            print(f"Response:\n{response}\n")

        self.test_results.append(('Unknown Command', all_passed))
        return all_passed

    def test_echo(self):
        """Test basic echo functionality."""
        print("Test: Echo Functionality")
        print("-" * 40)

        test_chars = ['A', 'B', '1', '2']
        all_passed = True

        for char in test_chars:
            response = self.send_command(char, wait_time=0.3)
            echoed = char in response
            status = "✓" if echoed else "✗"
            print(f"  {status} Echo '{char}': {echoed}")
            if not echoed:
                all_passed = False

        if all_passed:
            print("  ✓ Test PASSED\n")
        else:
            print("  ✗ Test FAILED\n")

        self.test_results.append(('Echo', all_passed))
        return all_passed

    def run_all_tests(self):
        """Run all tests and report results."""
        print("=" * 50)
        print("RetroCPU Monitor Command Validation")
        print("=" * 50)
        print()

        if not self.connect():
            return False

        try:
            # Run all tests
            self.test_echo()
            self.test_help_command()
            self.test_help_lowercase()
            self.test_examine_command()
            self.test_deposit_command()
            self.test_unknown_command()

            # Print summary
            print("=" * 50)
            print("Test Summary")
            print("=" * 50)

            passed = sum(1 for _, result in self.test_results if result)
            total = len(self.test_results)

            for name, result in self.test_results:
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"  {status}: {name}")

            print()
            print(f"Results: {passed}/{total} tests passed")

            if passed == total:
                print("✓ ALL TESTS PASSED")
                return True
            else:
                print("✗ SOME TESTS FAILED")
                return False

        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description='Test RetroCPU monitor commands via UART'
    )
    parser.add_argument(
        '--port',
        default='/dev/ttyACM0',
        help='Serial port (default: /dev/ttyACM0)'
    )
    parser.add_argument(
        '--baud',
        type=int,
        default=9600,
        help='Baud rate (default: 9600)'
    )

    args = parser.parse_args()

    tester = MonitorTest(port=args.port, baud=args.baud)

    if tester.run_all_tests():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
