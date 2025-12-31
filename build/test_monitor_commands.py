#!/usr/bin/env python3
"""
Test the E (examine) and D (deposit) commands of the RetroCPU monitor.
"""

import serial
import time
import sys

# Configure serial port
PORT = '/dev/ttyACM0'
BAUD = 9600

def wait_for_prompt(ser, timeout=5):
    """Wait for the monitor prompt '> '"""
    start_time = time.time()
    buffer = ""
    while time.time() - start_time < timeout:
        if ser.in_waiting:
            char = ser.read(1).decode('utf-8', errors='ignore')
            buffer += char
            print(char, end='', flush=True)
            if buffer.endswith('> '):
                return True
    return False

def send_command(ser, command):
    """Send a command and wait for response"""
    print(f"\nSending: {command}")
    # Send command one character at a time with delay
    for char in command:
        ser.write(char.encode('utf-8'))
        time.sleep(0.05)  # 50ms between characters
    ser.write(b'\r')  # Send carriage return
    time.sleep(0.1)

def read_response(ser, timeout=2):
    """Read response from serial port"""
    start_time = time.time()
    buffer = ""
    while time.time() - start_time < timeout:
        if ser.in_waiting:
            char = ser.read(1).decode('utf-8', errors='ignore')
            buffer += char
            print(char, end='', flush=True)
    return buffer

def test_examine_command(ser):
    """Test the E (examine) command"""
    print("\n" + "="*60)
    print("Testing E (Examine) Command")
    print("="*60)

    # Test examining monitor ROM (should have known values)
    test_addresses = ['E000', 'E100', 'FFFC']

    for addr in test_addresses:
        if not wait_for_prompt(ser):
            print("ERROR: No prompt received")
            return False

        send_command(ser, f'E')
        time.sleep(0.1)

        # Send address
        for char in addr:
            ser.write(char.encode('utf-8'))
            time.sleep(0.05)

        response = read_response(ser, timeout=2)

        if addr in response:
            print(f"✓ Successfully examined address {addr}")
        else:
            print(f"✗ Failed to examine address {addr}")
            return False

    return True

def test_deposit_command(ser):
    """Test the D (deposit) command"""
    print("\n" + "="*60)
    print("Testing D (Deposit) Command")
    print("="*60)

    # Test writing to RAM
    test_cases = [
        ('0200', 'AA'),  # Write AA to $0200
        ('0201', '55'),  # Write 55 to $0201
        ('0300', 'FF'),  # Write FF to $0300
    ]

    for addr, value in test_cases:
        if not wait_for_prompt(ser):
            print("ERROR: No prompt received")
            return False

        send_command(ser, 'D')
        time.sleep(0.1)

        # Send address
        for char in addr:
            ser.write(char.encode('utf-8'))
            time.sleep(0.05)

        time.sleep(0.1)

        # Send value
        for char in value:
            ser.write(char.encode('utf-8'))
            time.sleep(0.05)

        response = read_response(ser, timeout=2)

        if addr in response and value in response:
            print(f"✓ Successfully deposited {value} to {addr}")
        else:
            print(f"✗ Failed to deposit to address {addr}")
            return False

    return True

def verify_deposit_with_examine(ser):
    """Verify deposited values by examining them"""
    print("\n" + "="*60)
    print("Verifying Deposits with Examine")
    print("="*60)

    test_cases = [
        ('0200', 'AA'),
        ('0201', '55'),
        ('0300', 'FF'),
    ]

    for addr, expected_value in test_cases:
        if not wait_for_prompt(ser):
            print("ERROR: No prompt received")
            return False

        send_command(ser, 'E')
        time.sleep(0.1)

        # Send address
        for char in addr:
            ser.write(char.encode('utf-8'))
            time.sleep(0.05)

        response = read_response(ser, timeout=2)

        if expected_value in response:
            print(f"✓ Verified {addr} contains {expected_value}")
        else:
            print(f"✗ Failed to verify {addr} - expected {expected_value}")
            return False

    return True

def main():
    print("RetroCPU Monitor Command Test")
    print("="*60)

    try:
        # Open serial port
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print(f"Connected to {PORT} at {BAUD} baud")

        # Wait for boot messages
        print("\nWaiting for boot messages...")
        time.sleep(2)

        # Read and display any initial output
        while ser.in_waiting:
            char = ser.read(1).decode('utf-8', errors='ignore')
            print(char, end='', flush=True)

        # Run tests
        if not test_examine_command(ser):
            print("\n✗ Examine command test FAILED")
            return 1

        if not test_deposit_command(ser):
            print("\n✗ Deposit command test FAILED")
            return 1

        if not verify_deposit_with_examine(ser):
            print("\n✗ Verification test FAILED")
            return 1

        print("\n" + "="*60)
        print("✓ All tests PASSED!")
        print("="*60)

        ser.close()
        return 0

    except serial.SerialException as e:
        print(f"Serial port error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1

if __name__ == '__main__':
    sys.exit(main())
