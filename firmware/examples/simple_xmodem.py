#!/usr/bin/env python3
"""
Simple custom XMODEM sender - bypasses the library
"""

import serial
import time

SOH = 0x01
ACK = 0x06
NAK = 0x15
EOT = 0x04
CAN = 0x18

def send_packet(ser, packet_num, data):
    """Send a single XMODEM packet"""
    # Pad data to 128 bytes
    if len(data) < 128:
        data += b'\x00' * (128 - len(data))

    # Calculate checksum
    checksum = sum(data) & 0xFF

    # Build packet
    complement = (255 - packet_num) & 0xFF
    packet = bytes([SOH, packet_num, complement]) + data + bytes([checksum])

    print(f"Sending packet {packet_num}:")
    print(f"  SOH={SOH:02X}, PKT={packet_num:02X}, CMPL={complement:02X}, CHKSUM={checksum:02X}")

    # Send packet byte-by-byte with delays to avoid buffer overflow
    for i, byte in enumerate(packet):
        ser.write(bytes([byte]))
        if i < len(packet) - 1:  # Don't delay after last byte
            time.sleep(0.002)  # 2ms between bytes
    print(f"  Sent packet byte-by-byte ({len(packet)} bytes with 2ms delays)")

    # Wait for ACK or NAK
    start = time.time()
    responses = []
    while (time.time() - start) < 3.0:
        if ser.in_waiting:
            response = ser.read(1)[0]
            responses.append(response)
            if response == ACK:
                print(f"  Responses: {[f'{b:02X}' for b in responses]}")
                print(f"  Got ACK!")
                return True
            elif response == NAK:
                print(f"  Responses: {[f'{b:02X}' for b in responses]}")
                print(f"  Got NAK!")
                return False
            elif response == CAN:
                print(f"  Responses: {[f'{b:02X}' for b in responses]}")
                print(f"  Got CAN - transfer cancelled!")
                return False
            else:
                # Keep collecting
                pass
        time.sleep(0.01)

    print(f"  Timeout waiting for response!")
    return False

def upload_file(port, filename):
    """Upload file using custom XMODEM"""
    print(f"Opening {port}...")
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)

    # Clear buffers
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # Get prompt
    print("Getting prompt...")
    ser.write(b'\r')
    time.sleep(0.5)
    if ser.in_waiting:
        resp = ser.read(ser.in_waiting)
        print(f"Initial response: {resp[:50]}")

    # Send L command
    print("\nSending 'L' command...")
    ser.write(b'L\r')
    time.sleep(1.0)

    # Read until we get NAK
    print("Waiting for initial NAK...")
    got_nak = False
    for _ in range(200):
        if ser.in_waiting:
            byte = ser.read(1)[0]
            if byte == NAK:
                print(f"Got initial NAK - monitor ready!")
                got_nak = True
                break
            elif 32 <= byte < 127:
                print(f"  Text: {chr(byte)}", end='')
            else:
                print(f"  Byte: {byte:02X}")
        time.sleep(0.01)

    if not got_nak:
        print("ERROR: No NAK received!")
        ser.close()
        return False

    # Read file
    print(f"\nReading {filename}...")
    with open(filename, 'rb') as f:
        data = f.read()
    print(f"File size: {len(data)} bytes")

    # Send packets
    packet_num = 1
    offset = 0

    while offset < len(data):
        chunk = data[offset:offset+128]

        # Try sending packet (with retries)
        for attempt in range(10):
            print(f"\nPacket {packet_num}, attempt {attempt+1}:")
            if send_packet(ser, packet_num, chunk):
                # Success!
                packet_num += 1
                offset += 128
                break
        else:
            print(f"Failed to send packet {packet_num} after 10 attempts!")
            ser.close()
            return False

    # Send EOT
    print("\nSending EOT...")
    ser.write(bytes([EOT]))
    time.sleep(0.5)

    # Check for ACK
    if ser.in_waiting:
        resp = ser.read(1)[0]
        if resp == ACK:
            print("Transfer complete!")
        else:
            print(f"Unexpected response to EOT: {resp:02X}")

    # Read any final messages
    time.sleep(0.5)
    if ser.in_waiting:
        msg = ser.read(ser.in_waiting)
        print(f"\nFinal message: {msg.decode('ascii', errors='replace')}")

    ser.close()
    return True

if __name__ == '__main__':
    import sys
    filename = sys.argv[1] if len(sys.argv) > 1 else 'hello.bin'
    upload_file('/dev/ttyACM0', filename)
