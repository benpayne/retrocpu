#!/usr/bin/env python3
"""Execute uploaded program on RetroCPU."""

import serial
import time

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
RUN_ADDRESS = 0x0300

def main():
    print("=" * 60)
    print("Executing Graphics GPU Test Program")
    print("=" * 60)
    print()

    # Open serial port
    print(f"Opening serial port {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(0.5)

    # Clear input
    ser.reset_input_buffer()

    # Send GO command: G 0300
    print(f"Executing program at ${RUN_ADDRESS:04X}...")
    cmd = f"G {RUN_ADDRESS >> 8:02X}{RUN_ADDRESS & 0xFF:02X}\r"
    ser.write(cmd.encode())
    time.sleep(0.5)

    # Read any response
    if ser.in_waiting:
        response = ser.read(ser.in_waiting)
        print(f"Response: {response}")

    print()
    print("=" * 60)
    print("Program executed!")
    print()
    print("You should now see 16 vertical color bars on your display")
    print("showing all 16 palette colors in 4 BPP mode (160x100).")
    print("=" * 60)

    ser.close()

if __name__ == '__main__':
    main()
