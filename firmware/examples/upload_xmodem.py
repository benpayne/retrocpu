#!/usr/bin/env python3
"""Upload binary file to RetroCPU via XMODEM protocol."""

import serial
import time
import sys

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600

def xmodem_checksum(data):
    """Calculate XMODEM checksum (simple sum mod 256)."""
    return sum(data) & 0xFF

def send_xmodem_packet(ser, packet_num, data):
    """Send a single 128-byte XMODEM packet."""
    # Ensure data is exactly 128 bytes (pad with 0x00 if needed)
    if len(data) < 128:
        data = data + bytes([0x00] * (128 - len(data)))

    # Build packet: SOH + PKT# + ~PKT# + 128 data bytes + checksum
    packet = bytes([
        0x01,                    # SOH
        packet_num & 0xFF,       # Packet number
        (~packet_num) & 0xFF,    # Complement of packet number
    ])
    packet += data
    packet += bytes([xmodem_checksum(data)])

    # Send packet
    ser.write(packet)

    # Wait for ACK (0x06) or NAK (0x15)
    response = ser.read(1)
    if len(response) == 0:
        return False  # Timeout

    return response[0] == 0x06  # ACK

def upload_file(filename):
    """Upload binary file via XMODEM."""
    print(f"Opening {filename}...")
    with open(filename, 'rb') as f:
        data = f.read()

    print(f"File size: {len(data)} bytes")
    print(f"Packets needed: {(len(data) + 127) // 128}")
    print()

    # Open serial port
    print(f"Opening serial port {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(0.5)

    # Send 'L' command to start XMODEM receiver
    print("Sending 'L' command to monitor...")
    ser.write(b'L\r')
    time.sleep(0.5)

    # Wait for initial NAK from receiver
    print("Waiting for initial NAK...")
    start_time = time.time()
    while time.time() - start_time < 5:
        if ser.in_waiting:
            response = ser.read(1)
            if response[0] == 0x15:  # NAK
                print("  ✓ Receiver ready (NAK received)")
                break
    else:
        print("ERROR: No NAK received from receiver")
        ser.close()
        return False

    # Send data in 128-byte packets
    packet_num = 1
    offset = 0

    while offset < len(data):
        chunk = data[offset:offset+128]

        retry_count = 0
        while retry_count < 10:
            if send_xmodem_packet(ser, packet_num, chunk):
                print(f"  Packet {packet_num}: ACK ({offset + len(chunk)} / {len(data)} bytes)")
                break
            else:
                retry_count += 1
                print(f"  Packet {packet_num}: NAK (retry {retry_count}/10)")

        if retry_count >= 10:
            print("ERROR: Too many retries, upload failed")
            ser.close()
            return False

        offset += 128
        packet_num += 1

    # Send EOT (End of Transmission)
    print("Sending EOT...")
    ser.write(bytes([0x04]))  # EOT
    time.sleep(0.2)

    # Wait for final ACK
    response = ser.read(1)
    if len(response) > 0 and response[0] == 0x06:
        print("  ✓ Upload complete (ACK received)")
    else:
        print("  Warning: No final ACK received")

    ser.close()
    print()
    print("Upload successful!")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: upload_xmodem.py <binary_file>")
        sys.exit(1)

    if upload_file(sys.argv[1]):
        sys.exit(0)
    else:
        sys.exit(1)
