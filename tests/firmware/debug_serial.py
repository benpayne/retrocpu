#!/usr/bin/env python3
"""
Debug serial communication to understand timing issues.
"""

import serial
import time
import sys

PORT = '/dev/ttyACM0'
BAUD = 9600

def send_char(ser, char, delay=0.05):
    """Send single character and show what comes back."""
    print(f">> Sending: '{char}' (0x{ord(char):02X})")
    ser.write(char.encode('utf-8'))
    time.sleep(delay)

    # Read immediate response
    if ser.in_waiting:
        response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        print(f"<< Immediate: {repr(response)}")
        return response
    else:
        print("<< No immediate response")
        return ""

def send_string_debug(ser, text, char_delay=0.05):
    """Send string character by character with debug output."""
    print(f"\n=== Sending string: '{text}' ===")
    all_response = ""
    for char in text:
        resp = send_char(ser, char, char_delay)
        all_response += resp
    return all_response

def test_examine_debug(ser):
    """Test E command with full debug output."""
    print("\n" + "="*60)
    print("TEST: Examine $E000")
    print("="*60)

    # Wait for clean state
    time.sleep(0.5)
    if ser.in_waiting:
        junk = ser.read(ser.in_waiting)
        print(f"Cleared buffer: {repr(junk.decode('utf-8', errors='ignore'))}")

    # Send 'E'
    print("\nStep 1: Send 'E' command")
    send_char(ser, 'E', 0.1)

    # Wait for "Address: " prompt
    print("\nStep 2: Wait for 'Address:' prompt")
    time.sleep(0.5)
    if ser.in_waiting:
        response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        print(f"Response: {repr(response)}")

    # Send address
    print("\nStep 3: Send address 'E000'")
    for char in 'E000':
        send_char(ser, char, 0.1)

    # Wait for result
    print("\nStep 4: Wait for result")
    time.sleep(1.0)  # Give plenty of time
    if ser.in_waiting:
        response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        print(f"Final response: {repr(response)}")
        print(f"Response (visible): {response}")
    else:
        print("ERROR: No response received!")

def test_timing_variations(ser):
    """Test different character delays."""
    print("\n" + "="*60)
    print("TEST: Different timing delays")
    print("="*60)

    for delay in [0.05, 0.075, 0.1, 0.15]:
        print(f"\n--- Testing with {delay*1000}ms delay ---")

        # Clear
        time.sleep(0.5)
        if ser.in_waiting:
            ser.read(ser.in_waiting)

        # Send E
        ser.write(b'E')
        time.sleep(0.3)
        ser.read(ser.in_waiting)  # Consume "Address:" prompt

        # Send address with this delay
        for char in 'E000':
            ser.write(char.encode('utf-8'))
            time.sleep(delay)

        # Wait and see result
        time.sleep(1.0)
        if ser.in_waiting:
            response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print(f"Result: {repr(response)}")
            if 'E000:' in response:
                print(f"✓ SUCCESS with {delay*1000}ms delay")
            else:
                print(f"✗ FAILED with {delay*1000}ms delay")

def main():
    try:
        print("Opening serial port...")
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print(f"Connected to {PORT} at {BAUD} baud\n")

        # Wait for system to stabilize
        time.sleep(1)

        # Clear any boot messages
        if ser.in_waiting:
            boot = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print(f"Boot messages:\n{boot}\n")

        # Get to clean prompt
        ser.write(b'\r')
        time.sleep(0.2)
        if ser.in_waiting:
            ser.read(ser.in_waiting)

        # Run tests
        test_examine_debug(ser)
        test_timing_variations(ser)

        ser.close()
        print("\n" + "="*60)
        print("Debug session complete")
        print("="*60)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
