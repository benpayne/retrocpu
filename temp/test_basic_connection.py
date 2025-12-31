#!/usr/bin/env python3
"""Basic test to check if monitor is responding."""

import serial
import time

def main():
    # Open serial port
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    print("Serial port opened")
    time.sleep(1.0)

    # Flush any existing data
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    print("Buffers flushed")
    time.sleep(0.5)

    # Read any startup messages
    time.sleep(1.0)
    startup = ser.read_all().decode('utf-8', errors='ignore')
    print(f"Startup message ({len(startup)} bytes):")
    print(startup)
    print("---")

    # Try sending H command (help)
    print("\nSending H command...")
    ser.write(b'H\n')
    time.sleep(0.5)

    response = ser.read_all().decode('utf-8', errors='ignore')
    print(f"Response ({len(response)} bytes):")
    print(response)

    if response:
        print("\n✓ Monitor is responding")
    else:
        print("\n✗ No response from monitor")

    ser.close()

if __name__ == '__main__':
    main()
