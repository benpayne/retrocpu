#!/usr/bin/env python3
"""
Debug XMODEM upload to see packet structure
"""

import serial
import time

def debug_upload():
    # Create a test packet manually
    import sys
    filename = sys.argv[1] if len(sys.argv) > 1 else 'hello.bin'
    with open(filename, 'rb') as f:
        data = f.read(128)  # Read first 128 bytes

    # Pad to 128 bytes if needed
    if len(data) < 128:
        data += b'\x00' * (128 - len(data))

    # Calculate checksum
    checksum = sum(data) & 0xFF

    # Build packet: SOH + packet_num + packet_num_complement + data + checksum
    packet_num = 1
    packet_num_complement = 255 - packet_num
    packet = bytes([0x01, packet_num, packet_num_complement]) + data + bytes([checksum])

    print(f"Packet structure:")
    print(f"  SOH: {packet[0]:02X}")
    print(f"  Packet number: {packet[1]:02X}")
    print(f"  Packet complement: {packet[2]:02X}")
    print(f"  Data (first 16 bytes): {packet[3:19].hex()}")
    print(f"  Checksum: {packet[131]:02X}")
    print(f"  Total packet length: {len(packet)}")

    # Send it
    print(f"\nOpening serial port...")
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    time.sleep(1)

    # Clear and get prompt
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.write(b'\r')
    time.sleep(0.5)
    if ser.in_waiting:
        ser.read(ser.in_waiting)

    # Send L command
    print("Sending L command...")
    ser.write(b'L\r')

    # Wait for NAK
    print("Waiting for NAK...")
    for _ in range(100):
        if ser.in_waiting:
            byte = ser.read(1)
            if byte == b'\x15':
                print(f"NAK received!")
                break
        time.sleep(0.01)

    # Send the packet
    print(f"Sending packet...")
    ser.write(packet)

    # Wait for response
    time.sleep(0.5)
    if ser.in_waiting:
        resp = ser.read(ser.in_waiting)
        print(f"Response ({len(resp)} bytes): {resp.hex()}")
        for b in resp:
            if b == 0x06:
                print("  ACK received!")
            elif b == 0x15:
                print("  NAK received!")
            elif b == 0x18:
                print("  CAN received!")
            elif 32 <= b < 127:
                print(f"  ASCII: {chr(b)}")
            else:
                print(f"  Byte: {b:02X}")
    else:
        print("No response")

    ser.close()

if __name__ == '__main__':
    debug_upload()
