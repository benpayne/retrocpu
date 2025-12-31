#!/usr/bin/env python3
"""
Integration test for BASIC system via serial port
Tests character input, buffer storage, and command execution
"""

import serial
import time
import sys

def test_basic_system(port='/dev/ttyACM0', baudrate=115200):
    """Test BASIC system via serial port"""

    print(f"Opening serial port {port} at {baudrate} baud...")
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        time.sleep(0.5)  # Let port stabilize

        # Flush any stale data
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.1)

        # Read any initial output (monitor banner)
        time.sleep(0.5)
        initial = ser.read(ser.in_waiting or 1000)
        print("=== Initial Output ===")
        print(initial.decode('ascii', errors='replace'))

        # Send 'G' command to start BASIC (single character, no CR)
        print("\n=== Sending 'G' command ===")
        ser.write(b'G')
        time.sleep(1.0)  # Wait for BASIC to boot

        # Read BASIC banner
        banner = ser.read(ser.in_waiting or 1000)
        print(banner.decode('ascii', errors='replace'))

        # Test 1: PRINT 2+2
        print("\n=== Test 1: Sending 'PRINT 2+2' ===")
        for char in b'PRINT 2+2\r':
            ser.write(bytes([char]))
            time.sleep(0.01)  # 10ms between characters
        time.sleep(1.0)  # Give it time to process

        # Read response
        response = ser.read(ser.in_waiting or 2000)
        response_text = response.decode('ascii', errors='replace')
        print(response_text)

        # Check for expected output
        success = False
        if 'X reg (length): 09' in response_text:
            print("✓ X register shows correct length (9)")
            success = True
        else:
            print("✗ X register length incorrect")

        if 'INPUT_LEN mem: 09' in response_text:
            print("✓ INPUT_LEN stored correctly")
        else:
            print("✗ INPUT_LEN not stored correctly")

        # Check buffer hex - should be "50 52 49 4E 54 20 32 2B 32" for "PRINT 2+2"
        if '50 52 49 4E 54' in response_text:
            print("✓ Buffer contains correct hex values (PRINT...)")
            success = True
        else:
            print("✗ Buffer does not contain correct characters")
            if '20 ' in response_text:
                print("  (Still seeing 0x20 space character issue)")

        if ' 4' in response_text:
            print("✓ BASIC output ' 4' detected")
            success = True
        else:
            print("✗ Expected output ' 4' not found")

        # Test 2: Simple command
        print("\n=== Test 2: Sending 'NEW' ===")
        for char in b'NEW\r':
            ser.write(bytes([char]))
            time.sleep(0.01)  # 10ms between characters
        time.sleep(0.5)

        response = ser.read(ser.in_waiting or 1000)
        response_text = response.decode('ascii', errors='replace')
        print(response_text)

        if 'Ready' in response_text:
            print("✓ NEW command works")
        else:
            print("✗ NEW command failed")

        ser.close()

        if success:
            print("\n=== TEST PASSED ===")
            return 0
        else:
            print("\n=== TEST FAILED ===")
            return 1

    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(test_basic_system())
