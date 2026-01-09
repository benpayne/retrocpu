#!/usr/bin/env python3
"""
Integration test for program loading via XMODEM and I/O configuration.

Tests the implemented features:
- User Story 1: XMODEM binary upload (L command)
- User Story 2: I/O configuration (I command)

Usage:
    python3 test_program_loader.py [--port /dev/ttyUSB0] [--baud 9600]
"""

import argparse
import serial
import time
import struct
import sys
from pathlib import Path


class XModemSender:
    """Simple XMODEM sender for testing binary uploads."""

    SOH = 0x01
    EOT = 0x04
    ACK = 0x06
    NAK = 0x15

    def __init__(self, ser):
        self.ser = ser
        self.packet_num = 1

    def calculate_checksum(self, data):
        """Calculate 8-bit checksum for XMODEM packet."""
        return sum(data) & 0xFF

    def send_packet(self, data):
        """Send a 128-byte XMODEM packet."""
        # Pad data to 128 bytes
        packet_data = data + b'\x00' * (128 - len(data))

        # Build packet: SOH + PKT# + ~PKT# + DATA[128] + CHECKSUM
        packet = bytes([
            self.SOH,
            self.packet_num & 0xFF,
            (~self.packet_num) & 0xFF
        ])
        packet += packet_data
        packet += bytes([self.calculate_checksum(packet_data)])

        # Send packet
        self.ser.write(packet)
        self.ser.flush()

        print(f"  Sent packet #{self.packet_num} ({len(packet)} bytes)")

        # Wait for ACK
        response = self.ser.read(1)
        if len(response) == 0:
            print("  ERROR: No response (timeout)")
            return False

        if response[0] == self.ACK:
            print(f"  Received ACK")
            self.packet_num += 1
            return True
        elif response[0] == self.NAK:
            print(f"  Received NAK (retry)")
            return False
        else:
            print(f"  ERROR: Unexpected response: 0x{response[0]:02X}")
            return False

    def send_file(self, data, max_retries=10):
        """Send complete file via XMODEM."""
        print(f"\nStarting XMODEM transfer ({len(data)} bytes)...")

        # Wait for initial NAK
        print("Waiting for receiver NAK...")
        start_time = time.time()
        while True:
            if self.ser.in_waiting > 0:
                ch = self.ser.read(1)
                if ch[0] == self.NAK:
                    print("Received initial NAK, starting transfer")
                    break
                else:
                    print(f"Ignoring byte: 0x{ch[0]:02X}")

            if time.time() - start_time > 10:
                print("ERROR: Timeout waiting for initial NAK")
                return False

            time.sleep(0.1)

        # Send data in 128-byte packets
        offset = 0
        while offset < len(data):
            chunk = data[offset:offset+128]

            retries = 0
            while retries < max_retries:
                if self.send_packet(chunk):
                    offset += len(chunk)
                    break
                retries += 1
                print(f"  Retry {retries}/{max_retries}")

            if retries >= max_retries:
                print("ERROR: Max retries exceeded")
                return False

        # Send EOT
        print("\nSending EOT...")
        self.ser.write(bytes([self.EOT]))
        self.ser.flush()

        response = self.ser.read(1)
        if len(response) > 0 and response[0] == self.ACK:
            print("Received final ACK - Transfer complete!")
            return True
        else:
            print("ERROR: No ACK for EOT")
            return False


class MonitorTester:
    """Test harness for RetroGPU monitor firmware."""

    def __init__(self, port='/dev/ttyUSB0', baud=9600, timeout=2.0):
        print(f"Opening serial port {port} at {baud} baud...")
        self.ser = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
            write_timeout=timeout
        )
        time.sleep(0.5)  # Let port stabilize
        print("Serial port open")

    def close(self):
        """Close serial port."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed")

    def read_until_prompt(self, timeout=5.0):
        """Read until we see the monitor prompt '> '."""
        output = b''
        start_time = time.time()

        while True:
            if self.ser.in_waiting > 0:
                ch = self.ser.read(1)
                output += ch
                sys.stdout.write(ch.decode('ascii', errors='replace'))
                sys.stdout.flush()

                # Check for prompt at end
                if output.endswith(b'> '):
                    return output.decode('ascii', errors='replace')

            if time.time() - start_time > timeout:
                print("\nTIMEOUT waiting for prompt")
                return output.decode('ascii', errors='replace')

            time.sleep(0.01)

    def send_command(self, cmd):
        """Send a command and wait for prompt."""
        print(f"\n>>> {cmd}")
        self.ser.write(cmd.encode('ascii') + b'\r')
        self.ser.flush()
        return self.read_until_prompt()

    def wait_for_boot(self):
        """Wait for monitor to boot and display initial prompt."""
        print("\nWaiting for monitor boot...")

        # First, try to read boot message (short timeout)
        output = self.read_until_prompt(timeout=2.0)

        if "M65C02" in output or "Monitor" in output or "RetroCPU" in output:
            print("\n✓ Monitor booted successfully")
            return True

        # If no boot message, monitor might already be running
        # Send CR to get a fresh prompt
        print("\nNo boot message - sending CR to check if monitor is running...")
        self.ser.write(b'\r')
        self.ser.flush()
        time.sleep(0.3)

        output = self.read_until_prompt(timeout=2.0)

        if '> ' in output:
            print("\n✓ Monitor is already running")
            return True
        else:
            print("\n✗ Monitor not responding")
            return False

    def test_io_config(self):
        """Test I/O configuration command."""
        print("\n" + "="*60)
        print("TEST: I/O Configuration (I command)")
        print("="*60)

        test_cases = [
            ("I 0 0", "IN=UART", "OUT=UART"),
            ("I 1 1", "IN=PS2", "OUT=Display"),
            ("I 2 2", "IN=Both", "OUT=Both"),
            ("I 0 2", "IN=UART", "OUT=Both"),
        ]

        passed = 0
        failed = 0

        for cmd, expect_in, expect_out in test_cases:
            output = self.send_command(cmd)

            if expect_in in output and expect_out in output:
                print(f"✓ PASS: {cmd} → {expect_in}, {expect_out}")
                passed += 1
            else:
                print(f"✗ FAIL: {cmd}")
                print(f"  Expected: {expect_in}, {expect_out}")
                print(f"  Got: {output}")
                failed += 1

        # Test invalid input
        output = self.send_command("I 5 0")
        if "Invalid" in output:
            print(f"✓ PASS: Invalid input rejected")
            passed += 1
        else:
            print(f"✗ FAIL: Invalid input not rejected")
            failed += 1

        print(f"\nI/O Config Tests: {passed} passed, {failed} failed")
        return failed == 0

    def test_xmodem_upload(self):
        """Test XMODEM binary upload."""
        print("\n" + "="*60)
        print("TEST: XMODEM Binary Upload (L command)")
        print("="*60)

        # Create simple test binary (hello world program)
        # This is the assembled version of hello_world.s
        test_binary = bytes([
            0xA2, 0x00,              # LDX #$00
            0xBD, 0x0E, 0x03,        # LDA MESSAGE,X
            0xF0, 0x06,              # BEQ DONE
            0x20, 0xF3, 0xFF,        # JSR CHROUT
            0xE8,                    # INX
            0xD0, 0xF5,              # BNE PRINT_LOOP
            0xA9, 0x0D,              # LDA #$0D
            0x20, 0xF3, 0xFF,        # JSR CHROUT
            0xA9, 0x0A,              # LDA #$0A
            0x20, 0xF3, 0xFF,        # JSR CHROUT
            0x60,                    # RTS
            # MESSAGE: "HELLO WORLD\0"
            0x48, 0x45, 0x4C, 0x4C, 0x4F, 0x20,
            0x57, 0x4F, 0x52, 0x4C, 0x44, 0x00
        ])

        print(f"\nTest binary size: {len(test_binary)} bytes")

        # Send load command
        print("\nSending L 0300 command...")
        self.ser.write(b'L 0300\r')
        self.ser.flush()

        # Read response
        time.sleep(0.5)
        response = b''
        while self.ser.in_waiting > 0:
            response += self.ser.read(self.ser.in_waiting)
            time.sleep(0.1)

        print(f"Response: {response.decode('ascii', errors='replace')}")

        # Create XMODEM sender and transfer file
        xmodem = XModemSender(self.ser)
        success = xmodem.send_file(test_binary)

        if success:
            print("\n✓ XMODEM transfer completed successfully")

            # Read any completion message
            time.sleep(0.5)
            while self.ser.in_waiting > 0:
                ch = self.ser.read(1)
                sys.stdout.write(ch.decode('ascii', errors='replace'))
                sys.stdout.flush()

            return True
        else:
            print("\n✗ XMODEM transfer failed")
            return False

    def test_program_execution(self):
        """Test executing the uploaded program."""
        print("\n" + "="*60)
        print("TEST: Program Execution (G command)")
        print("="*60)

        # Execute program at 0300
        output = self.send_command("G 0300")

        if "HELLO WORLD" in output:
            print("✓ PASS: Program executed and printed 'HELLO WORLD'")
            return True
        else:
            print("✗ FAIL: Program did not execute correctly")
            print(f"  Output: {output}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Test RetroGPU monitor program loading')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--baud', type=int, default=9600, help='Baud rate (default: 9600)')
    parser.add_argument('--skip-xmodem', action='store_true', help='Skip XMODEM test')
    args = parser.parse_args()

    tester = None
    try:
        tester = MonitorTester(port=args.port, baud=args.baud)

        # Wait for monitor to boot
        if not tester.wait_for_boot():
            print("\nERROR: Monitor did not boot properly")
            return 1

        # Run tests
        results = []

        # Test I/O configuration
        results.append(("I/O Config", tester.test_io_config()))

        # Reset to UART mode for XMODEM test
        tester.send_command("I 0 0")

        # Test XMODEM upload
        if not args.skip_xmodem:
            results.append(("XMODEM Upload", tester.test_xmodem_upload()))

            # Test program execution
            results.append(("Program Execution", tester.test_program_execution()))

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {test_name}")

        print(f"\nTotal: {passed}/{total} tests passed")

        return 0 if passed == total else 1

    except serial.SerialException as e:
        print(f"\nSerial port error: {e}")
        print("\nTroubleshooting:")
        print("1. Check that the board is connected")
        print("2. Verify the port name (try 'ls /dev/ttyUSB*' or 'ls /dev/ttyACM*')")
        print("3. Check permissions (you may need: sudo usermod -a -G dialout $USER)")
        print("4. Ensure no other program is using the serial port")
        return 1

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1

    finally:
        if tester:
            tester.close()


if __name__ == '__main__':
    sys.exit(main())
