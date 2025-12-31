#!/usr/bin/env python3
"""Debug script to test E command with prompts."""

import serial
import time

def main():
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    print("Serial port opened")
    time.sleep(1.5)

    # Flush buffers    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.5)

    print("\n=== Test 1: Check for boot message ===")
    time.sleep(1.0)
    if ser.in_waiting:
        boot_msg = ser.read_all().decode('utf-8', errors='ignore')
        print(f"Boot message ({len(boot_msg)} bytes):")
        print(boot_msg)
    else:
        print("No boot message")

    print("\n=== Test 2: Send newline and wait for prompt ===")
    ser.write(b'\n')
    time.sleep(0.5)
    if ser.in_waiting:
        response = ser.read_all().decode('utf-8', errors='ignore')
        print(f"Response: {repr(response)}")
    else:
        print("No response")

    print("\n=== Test 3: Send 'E' and wait for Address prompt ===")
    print("Sending 'E'...")
    ser.write(b'E')
    time.sleep(0.5)

    response = ''
    for i in range(20):  # Try for 2 seconds
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            response += chunk
            print(f"Got: {repr(chunk)}")
        time.sleep(0.1)

    print(f"\nTotal response: {repr(response)}")
    print(f"Length: {len(response)} bytes")

    if 'Address:' in response:
        print("✓ Found 'Address:' prompt")

        print("\n=== Test 4: Send address '0200' ===")
        print("Sending '0200'...")
        ser.write(b'0200')
        time.sleep(0.5)

        response2 = ''
        for i in range(20):
            if ser.in_waiting:
                chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                response2 += chunk
                print(f"Got: {repr(chunk)}")
            time.sleep(0.1)

        print(f"\nTotal response: {repr(response2)}")
        if ':' in response2:
            print("✓ Got result with ':' ")
        else:
            print("✗ No ':' in result")
    else:
        print("✗ 'Address:' prompt not found")

    ser.close()

if __name__ == '__main__':
    main()
