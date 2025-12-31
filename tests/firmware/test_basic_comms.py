#!/usr/bin/env python3
"""
Basic communication test - just see if anything comes back.
"""

import serial
import time

PORT = '/dev/ttyACM0'
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)
print(f"Connected to {PORT} at {BAUD} baud")
print("Waiting for boot messages...")
time.sleep(2)

# Read any boot messages
if ser.in_waiting:
    data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    print(f"Boot data:\n{data}")
else:
    print("No boot data")

print("\n--- Testing basic echo ---")
print("Sending newline...")
ser.write(b'\r\n')
time.sleep(0.5)

if ser.in_waiting:
    data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    print(f"Response: {repr(data)}")
else:
    print("No response to newline")

print("\nSending 'E' and waiting...")
ser.write(b'E')
time.sleep(1)

if ser.in_waiting:
    data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    print(f"Response: {repr(data)}")
    print(f"Visible: {data}")
else:
    print("No response to 'E'")

print("\nChecking if data is available...")
for i in range(10):
    time.sleep(0.5)
    if ser.in_waiting:
        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        print(f"Delayed response: {repr(data)}")
        break
else:
    print("No delayed response either")

ser.close()
