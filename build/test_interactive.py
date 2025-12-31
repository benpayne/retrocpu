#!/usr/bin/env python3
"""
Interactive test - works with already-booted system
"""

import serial
import time
import sys

def main():
    # Open serial port
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    time.sleep(0.1)

    print("Connected to /dev/ttyACM0 @ 115200 baud")
    print("Press Ctrl+C to exit")
    print("="*60)

    # Clear any pending input
    ser.reset_input_buffer()

    # Send a newline to see what prompt we get
    print("\nSending newline to check current state...")
    ser.write(b'\r\n')
    time.sleep(0.5)

    # Read response
    if ser.in_waiting > 0:
        response = ser.read(ser.in_waiting).decode('ascii', errors='replace')
        print(f"Response: {repr(response)}")

    print("\nEntering interactive mode...")
    print("Try typing: G (to start BASIC)")
    print("Or in BASIC: PRINT 2+2")
    print("-"*60)

    try:
        while True:
            # Check for input from serial
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                text = data.decode('ascii', errors='replace')
                print(text, end='', flush=True)

            # Check for keyboard input
            import select
            if select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                ser.write(char.encode('ascii'))

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n\nExiting...")
        ser.close()

if __name__ == '__main__':
    main()
