#!/usr/bin/env python3
"""
Manual test of zero page deposit and examine to see what's really happening.
"""

import serial
import time

PORT = '/dev/ttyACM0'
BAUD = 9600
CHAR_DELAY = 0.15

ser = serial.Serial(PORT, BAUD, timeout=1)
print("Connected")
time.sleep(1.5)

# Clear
if ser.in_waiting:
    junk = ser.read(ser.in_waiting)

# Get to prompt
ser.write(b'\r\n')
time.sleep(0.5)
if ser.in_waiting:
    ser.read(ser.in_waiting)

print("\n=== DEPOSIT $A5 to $0010 ===")
print("Sending D...")
ser.write(b'D')
time.sleep(0.3)
if ser.in_waiting:
    print(f"  {repr(ser.read(ser.in_waiting).decode('utf-8', errors='ignore'))}")

print("Sending address 0010...")
for c in '0010':
    ser.write(c.encode('utf-8'))
    time.sleep(CHAR_DELAY)
time.sleep(0.5)
if ser.in_waiting:
    print(f"  {repr(ser.read(ser.in_waiting).decode('utf-8', errors='ignore'))}")

time.sleep(0.2)
print("Sending value A5...")
for c in 'A5':
    ser.write(c.encode('utf-8'))
    time.sleep(CHAR_DELAY)
time.sleep(0.7)
if ser.in_waiting:
    resp = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    print(f"  Response: {repr(resp)}")
    print(f"  Visible: {resp}")

print("\n=== Wait 1 second ===")
time.sleep(1.0)

print("\n=== EXAMINE $0010 ===")
print("Sending E...")
ser.write(b'E')
time.sleep(0.3)
if ser.in_waiting:
    print(f"  {repr(ser.read(ser.in_waiting).decode('utf-8', errors='ignore'))}")

print("Sending address 0010...")
for c in '0010':
    ser.write(c.encode('utf-8'))
    time.sleep(CHAR_DELAY)
time.sleep(0.5)
if ser.in_waiting:
    resp = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    print(f"  Response: {repr(resp)}")
    print(f"  Visible: {resp}")

    # Parse value
    for line in resp.split('\n'):
        if ':' in line:
            parts = line.split(':')
            if len(parts) >= 2:
                value = parts[1].strip().split()[0]
                print(f"\n*** PARSED VALUE: {value} ***")

ser.close()
