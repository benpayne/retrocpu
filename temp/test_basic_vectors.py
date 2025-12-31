#!/usr/bin/env python3
"""Test script to check I/O vectors and BASIC startup."""

import serial
import time

def main():
    # Open serial port
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    time.sleep(0.5)

    # Flush any existing data
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.5)

    print("=== Testing I/O Vectors in ROM ===")

    # Test E command to check vectors at FFF0, FFF3, FFF6
    for addr in ['FFF0', 'FFF3', 'FFF6']:
        print(f"\nChecking {addr}:")

        # Wait for prompt
        ser.write(b'\n')
        time.sleep(0.2)
        ser.read_all()  # Clear

        # Send E command
        cmd = f'E {addr}\n'
        print(f"  Sending: {cmd.strip()}")
        ser.write(cmd.encode())
        time.sleep(0.3)

        # Read response
        response = ser.read_all().decode('utf-8', errors='ignore')
        print(f"  Response: {response.strip()}")

        # Check if it's 4C (JMP opcode)
        if '4C' in response:
            print(f"  ✓ {addr} contains JMP instruction (4C)")
        elif 'EA' in response:
            print(f"  ✗ {addr} contains NOP (EA) - vector not placed correctly!")
        else:
            print(f"  ? Unexpected response")

    print("\n=== Testing G Command ===")

    # Wait for prompt
    ser.write(b'\n')
    time.sleep(0.2)
    ser.read_all()  # Clear

    print("Sending G command...")
    ser.write(b'G\n')
    time.sleep(1.0)

    # Read response
    response = ''
    for _ in range(50):  # Try for 5 seconds
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            response += chunk
            print(chunk, end='', flush=True)
        time.sleep(0.1)

    print(f"\n\nTotal response length: {len(response)} bytes")

    if not response:
        print("✗ No response from BASIC - system likely crashed/reset")
    elif 'MEMORY SIZE' in response.upper() or 'OK' in response:
        print("✓ BASIC started successfully!")
    else:
        print("? Got some response but not BASIC startup")

    ser.close()

if __name__ == '__main__':
    main()
