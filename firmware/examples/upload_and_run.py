#!/usr/bin/env python3
"""
Upload and run a program via XMODEM
"""

import serial
import time
from xmodem import XMODEM

def upload_and_run(port, binary_file, load_address=0x0300):
    """Upload a binary via XMODEM and execute it"""

    print(f"Opening serial port {port}...")
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(1.0)

    # Clear any pending data and get to a clean prompt
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # Send carriage return to get a fresh prompt
    print("Getting monitor prompt...")
    ser.write(b'\r')
    time.sleep(1.0)

    # Clear the response (welcome message or error)
    if ser.in_waiting:
        data = ser.read(ser.in_waiting)
        print(f"Monitor response: {data.decode('ascii', errors='replace')[:100]}...")

    # Now send the L command and wait for XMODEM ready message
    print("\nSending 'L' command to start XMODEM receive...")
    ser.write(b'L\r')

    # Wait briefly for "Ready for XMODEM" message and consume it
    time.sleep(0.2)
    if ser.in_waiting:
        ready_msg = ser.read(ser.in_waiting)
        print(f"Monitor: {ready_msg.decode('ascii', errors='replace').strip()}")

    # Very brief wait for NAKs to start (monitor times out quickly)
    time.sleep(0.1)

    print(f"Starting XMODEM upload of {binary_file}...")

    def getc(size, timeout=3):
        data = ser.read(size)
        return data or None

    def putc(data, timeout=3):
        n = ser.write(data)
        print(f"XMODEM putc({len(data)}): {data[:16].hex()}...")
        return n

    modem = XMODEM(getc, putc, mode='xmodem')

    with open(binary_file, 'rb') as f:
        success = modem.send(f)

    if success:
        print("Upload successful!")
        time.sleep(1)

        # Read any response
        if ser.in_waiting:
            response = ser.read(ser.in_waiting)
            print(f"Response: {response.decode('ascii', errors='replace')}")

        # Verify upload by examining first few bytes
        print(f"\nVerifying upload at 0x{load_address:04X}...")
        ser.write(f'E {load_address:04X}\r'.encode())
        time.sleep(0.5)

        # Read verification output
        if ser.in_waiting:
            output = ser.read(ser.in_waiting)
            print(f"Memory at {load_address:04X}: {output.decode('ascii', errors='replace')}")

        print("\nUpload complete! Program is loaded in memory.")
        print("Note: Monitor does not have an execute command.")
        print("To run the program, you would need to manually jump to the address")
        print(f"or add a CPU reset with PC set to 0x{load_address:04X}.")
    else:
        print("Upload failed!")

    ser.close()
    return success

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: upload_and_run.py <binary_file> [serial_port]")
        sys.exit(1)

    binary_file = sys.argv[1]
    port = sys.argv[2] if len(sys.argv) > 2 else '/dev/ttyACM0'

    upload_and_run(port, binary_file)
