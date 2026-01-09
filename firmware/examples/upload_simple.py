#!/usr/bin/env python3
"""Upload binary file to RetroCPU using monitor P (poke) command."""

import serial
import time
import sys

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
LOAD_ADDRESS = 0x0300  # Load address for program

def poke(ser, addr, data):
    """Write a byte to memory using monitor P command."""
    cmd = f"P {addr >> 8:02X} {addr & 0xFF:02X} {data:02X}\r"
    ser.write(cmd.encode())
    time.sleep(0.005)  # Small delay for processing

def upload_file(filename):
    """Upload binary file using poke commands."""
    print(f"Opening {filename}...")
    with open(filename, 'rb') as f:
        data = f.read()

    print(f"File size: {len(data)} bytes")
    print(f"Load address: ${LOAD_ADDRESS:04X}")
    print()

    # Open serial port
    print(f"Opening serial port {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(0.5)

    # Clear any pending data
    ser.write(b'\r')
    time.sleep(0.2)
    ser.reset_input_buffer()

    # Upload byte by byte
    print("Uploading...")
    addr = LOAD_ADDRESS

    for i, byte in enumerate(data):
        poke(ser, addr, byte)
        addr += 1

        if (i + 1) % 32 == 0:
            print(f"  {i + 1} / {len(data)} bytes ({(i + 1) * 100 // len(data)}%)")

    print(f"  {len(data)} / {len(data)} bytes (100%)")
    print()
    print("Upload complete!")
    print()

    ser.close()
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: upload_simple.py <binary_file>")
        sys.exit(1)

    if upload_file(sys.argv[1]):
        print("=" * 60)
        print("To run the program:")
        print(f"  1. Connect to serial: screen {SERIAL_PORT} 9600")
        print("  2. Press ENTER to get prompt")
        print(f"  3. Type: G 0300")
        print("  4. Press ENTER to execute")
        print()
        print("The program will draw 16 color bars on the display!")
        print("=" * 60)
        sys.exit(0)
    else:
        sys.exit(1)
