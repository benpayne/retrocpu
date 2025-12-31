#!/usr/bin/env python3
"""
Simple interactive test for E and D commands.
"""

import serial
import time
import sys

PORT = '/dev/ttyACM0'
BAUD = 9600

def send_slow(ser, text, delay=0.05):
    """Send text slowly, character by character"""
    for char in text:
        ser.write(char.encode('utf-8'))
        time.sleep(delay)
        # Echo back what we sent
        if ser.in_waiting:
            echo = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print(echo, end='', flush=True)

def read_all(ser, timeout=1):
    """Read all available data"""
    time.sleep(timeout)
    if ser.in_waiting:
        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        print(data, end='', flush=True)
        return data
    return ""

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print("Connected to RetroCPU")
    print("="*60)

    # Wait and read boot messages
    time.sleep(2)
    print("Boot messages:")
    read_all(ser, timeout=1)

    # Test 1: Examine ROM at $E000
    print("\n\n[TEST 1] Examine $E000 (Monitor ROM)")
    print("Sending: E")
    send_slow(ser, 'E')
    read_all(ser, timeout=0.5)
    print("\nSending address: E000")
    send_slow(ser, 'E000')
    result = read_all(ser, timeout=1)
    print("\n")

    # Test 2: Deposit $AA to $0200
    print("\n[TEST 2] Deposit $AA to $0200")
    print("Sending: D")
    send_slow(ser, 'D')
    read_all(ser, timeout=0.5)
    print("\nSending address: 0200")
    send_slow(ser, '0200')
    read_all(ser, timeout=0.5)
    print("\nSending value: AA")
    send_slow(ser, 'AA')
    result = read_all(ser, timeout=1)
    print("\n")

    # Test 3: Examine $0200 to verify
    print("\n[TEST 3] Examine $0200 (should show AA)")
    print("Sending: E")
    send_slow(ser, 'E')
    read_all(ser, timeout=0.5)
    print("\nSending address: 0200")
    send_slow(ser, '0200')
    result = read_all(ser, timeout=1)

    if 'AA' in result:
        print("\n✓ SUCCESS: Verified $0200 contains $AA")
    else:
        print("\n✗ FAILED: Could not verify value")

    print("\n" + "="*60)
    print("Test complete. Close connection.")

    ser.close()

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
