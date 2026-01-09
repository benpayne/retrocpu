#!/usr/bin/env python3
"""
Upload a binary file via XMODEM to RetroCPU
"""

import serial
import time
from xmodem import XMODEM

def upload_file(port, binary_file):
    """Upload a binary via XMODEM"""

    print(f"Opening serial port {port}...")
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(1)

    # Clear buffer and get prompt
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.write(b'\r')
    time.sleep(0.5)
    if ser.in_waiting:
        ser.read(ser.in_waiting)  # Discard

    # Send L command
    print("Sending L command...")
    ser.write(b'L\r')

    # Consume all text until we see a NAK (0x15)
    print("Waiting for XMODEM NAK...")
    consumed = b''
    for _ in range(100):  # Max iterations
        if ser.in_waiting:
            byte = ser.read(1)
            consumed += byte
            if byte == b'\x15':
                print(f"NAK received! Monitor ready.")
                break
        time.sleep(0.01)
    else:
        print(f"ERROR: No NAK. Received: {consumed}")
        ser.close()
        return False

    # Setup XMODEM with NAK injection
    first_nak = [True]

    def getc(size, timeout=1):
        if first_nak[0] and size == 1:
            first_nak[0] = False
            return b'\x15'
        return ser.read(size) or None

    def putc(data, timeout=1):
        return ser.write(data)

    # Upload
    print(f"Uploading {binary_file}...")
    modem = XMODEM(getc, putc, mode='xmodem')

    with open(binary_file, 'rb') as f:
        success = modem.send(f)

    if success:
        print("Upload successful!")
        time.sleep(1)

        # Read response
        if ser.in_waiting:
            resp = ser.read(ser.in_waiting)
            print(f"Monitor: {resp.decode('ascii', errors='replace')}")
    else:
        print("Upload failed!")

    ser.close()
    return success

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: xmodem_upload.py <binary_file> [port]")
        sys.exit(1)

    binary = sys.argv[1]
    port = sys.argv[2] if len(sys.argv) > 2 else '/dev/ttyACM0'

    upload_file(port, binary)
