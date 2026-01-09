#!/bin/bash
# Build and upload graphics GPU test program

set -e  # Exit on error

PROGRAM="test_gpu_graphics"
SERIAL_PORT="/dev/ttyACM0"
LOAD_ADDR="0300"  # Load address for the program

echo "===================================================================="
echo "Graphics GPU Test - Build and Upload"
echo "===================================================================="
echo ""

# Step 1: Assemble the program
echo "Step 1: Assembling ${PROGRAM}.s..."
ca65 -o ${PROGRAM}.o ${PROGRAM}.s
if [ $? -ne 0 ]; then
    echo "ERROR: Assembly failed!"
    exit 1
fi
echo "  ✓ Assembly successful: ${PROGRAM}.o"
echo ""

# Step 2: Link the program
echo "Step 2: Linking..."
ld65 -t none -o ${PROGRAM}.bin ${PROGRAM}.o
if [ $? -ne 0 ]; then
    echo "ERROR: Linking failed!"
    exit 1
fi
echo "  ✓ Linking successful: ${PROGRAM}.bin"
echo ""

# Step 3: Show binary info
SIZE=$(wc -c < ${PROGRAM}.bin)
echo "Step 3: Binary information"
echo "  Size: ${SIZE} bytes"
echo "  Load address: \$${LOAD_ADDR}"
echo ""

# Step 4: Upload using Python XMODEM script
echo "Step 4: Uploading to FPGA via XMODEM..."
echo "  Serial port: ${SERIAL_PORT}"
echo "  Protocol: XMODEM"
echo ""

# Create Python upload script
cat > upload_xmodem.py << 'PYTHON_SCRIPT'
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
PYTHON_SCRIPT

chmod +x upload_xmodem.py

# Run the upload
python3 upload_xmodem.py ${PROGRAM}.bin

if [ $? -eq 0 ]; then
    echo ""
    echo "===================================================================="
    echo "Upload Complete!"
    echo "===================================================================="
    echo ""
    echo "To run the program:"
    echo "  1. Connect to the monitor: screen ${SERIAL_PORT} 9600"
    echo "  2. Press ENTER to get the prompt"
    echo "  3. Type: G 0300"
    echo "  4. Press ENTER to execute"
    echo ""
    echo "The program will:"
    echo "  - Set up a 16-color palette"
    echo "  - Switch to 4 BPP graphics mode (160x100)"
    echo "  - Draw 16 vertical color bars"
    echo "  - Switch display to graphics mode"
    echo ""
    echo "You should see 16 colorful vertical bars on your display!"
    echo "===================================================================="
else
    echo ""
    echo "ERROR: Upload failed!"
    exit 1
fi
