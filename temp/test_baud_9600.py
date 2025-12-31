#!/usr/bin/env python3
"""Test with 9600 baud like the tests use."""

import serial
import time

def main():
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    print("Serial port opened at 9600 baud")
    time.sleep(2.0)

    # Flush buffers
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    print("Buffers flushed")
    time.sleep(0.5)

    print("\n=== Checking for boot message ===")
    time.sleep(1.0)
    if ser.in_waiting:
        boot_msg = ser.read_all().decode('utf-8', errors='ignore')
        print(f"Got {len(boot_msg)} bytes:")
        print(boot_msg)
    else:
        print("No data waiting")

    print("\n=== Sending newline ===")
    ser.write(b'\r\n')
    time.sleep(1.0)

    if ser.in_waiting:
        response = ser.read_all().decode('utf-8', errors='ignore')
        print(f"Response ({len(response)} bytes):")
        print(response)
        if '>' in response:
            print("✓ Found prompt!")
        else:
            print("No prompt found")
    else:
        print("No response")

    ser.close()

if __name__ == '__main__':
    main()
