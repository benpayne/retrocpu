#!/usr/bin/env python3
"""
Test BASIC startup after adding I/O vectors.
This script verifies that the I/O vectors are correctly installed
and that BASIC can start without crashing.
"""

import serial
import time

PORT = '/dev/ttyACM0'
BAUD = 9600

def send_slow(ser, text, delay=0.1):
    """Send text slowly, character by character."""
    for char in text:
        ser.write(char.encode('utf-8'))
        time.sleep(delay)

def read_all(ser, timeout=2):
    """Read all available data with timeout."""
    start = time.time()
    buffer = ""
    while time.time() - start < timeout:
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        time.sleep(0.05)
    return buffer

def main():
    print("=== Testing BASIC Startup with I/O Vectors ===\n")

    # Open serial port
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(1)

    # Clear any boot messages
    if ser.in_waiting:
        junk = ser.read(ser.in_waiting)

    # Send newline to get prompt
    ser.write(b'\r\n')
    time.sleep(0.5)

    # Clear output
    if ser.in_waiting:
        ser.read(ser.in_waiting)

    print("Step 1: Verify I/O vectors are correct")
    print("Checking $FFF0 (CHRIN vector)...")
    send_slow(ser, 'E FFF0\r')
    time.sleep(0.5)
    result = read_all(ser, timeout=2)
    print(f"Result: {result}")

    if 'FFF0' in result and '4C' in result:
        print("✓ $FFF0 contains $4C (JMP opcode)\n")
    else:
        print("✗ $FFF0 does not contain JMP instruction\n")

    print("Checking $FFF3 (CHROUT vector)...")
    send_slow(ser, 'E FFF3\r')
    time.sleep(0.5)
    result = read_all(ser, timeout=2)
    print(f"Result: {result}")

    if 'FFF3' in result and '4C' in result:
        print("✓ $FFF3 contains $4C (JMP opcode)\n")
    else:
        print("✗ $FFF3 does not contain JMP instruction\n")

    print("Checking $FFF6 (LOAD/break vector)...")
    send_slow(ser, 'E FFF6\r')
    time.sleep(0.5)
    result = read_all(ser, timeout=2)
    print(f"Result: {result}")

    if 'FFF6' in result:
        print(f"✓ $FFF6 contains: {result.split(':')[1].strip() if ':' in result else 'unknown'}\n")

    print("\nStep 2: Start BASIC with G command")
    print("Sending 'G' command...")
    ser.write(b'G')
    time.sleep(2.0)

    # Read BASIC output
    output = read_all(ser, timeout=5)
    print("\n=== BASIC Output ===")
    print(output)
    print("=== End Output ===\n")

    # Check for success indicators
    if 'BASIC' in output.upper():
        print("✓ BASIC banner detected")

    if 'MEMORY SIZE' in output.upper() or 'BYTES FREE' in output.upper():
        print("✓ BASIC memory prompt detected")

    if 'OK' in output:
        print("✓ BASIC OK prompt detected")

    if 'RetroCPU Monitor' in output:
        print("✗ System reset back to monitor - BASIC crashed!")
        return False

    print("\n=== Testing BASIC Commands ===")

    # Wait for OK prompt or memory size prompt
    if 'MEMORY SIZE' in output.upper():
        print("BASIC is asking for MEMORY SIZE - sending default (press Enter)")
        ser.write(b'\r')
        time.sleep(1)
        output = read_all(ser, timeout=3)
        print(output)

    # Try a simple PRINT command
    print("\nTrying: PRINT 2+2")
    send_slow(ser, 'PRINT 2+2\r', delay=0.15)
    time.sleep(1)
    output = read_all(ser, timeout=2)
    print(f"Result: {output}")

    if '4' in output:
        print("✓ BASIC PRINT command works!")

    print("\n=== Test Complete ===")
    ser.close()
    return True

if __name__ == '__main__':
    main()
