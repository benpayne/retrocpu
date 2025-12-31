#!/usr/bin/env python3
"""
Debug deposit command to see what's actually being received.
"""

import serial
import time

PORT = '/dev/ttyACM0'
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)
print("Connected")
time.sleep(1.5)

# Clear buffer
if ser.in_waiting:
    junk = ser.read(ser.in_waiting)
    print(f"Cleared: {repr(junk.decode('utf-8', errors='ignore'))}")

# Get to prompt
ser.write(b'\r\n')
time.sleep(0.5)
if ser.in_waiting:
    ser.read(ser.in_waiting)

print("\n=== Test Deposit $A5 to $0010 ===")

# Send D
print("Sending 'D'...")
ser.write(b'D')
time.sleep(0.3)

if ser.in_waiting:
    response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    print(f"After D: {repr(response)}")

# Send address 0010
print("Sending '0010'...")
for char in '0010':
    ser.write(char.encode('utf-8'))
    time.sleep(0.1)

time.sleep(0.3)
if ser.in_waiting:
    response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    print(f"After address: {repr(response)}")

# Send value A5
print("Sending 'A5'...")
for char in 'A5':
    ser.write(char.encode('utf-8'))
    time.sleep(0.1)

time.sleep(0.5)
if ser.in_waiting:
    response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    print(f"After value: {repr(response)}")

# Now examine to verify
print("\n=== Verify with Examine ===")
time.sleep(0.5)
ser.write(b'E')
time.sleep(0.3)
if ser.in_waiting:
    ser.read(ser.in_waiting)

for char in '0010':
    ser.write(char.encode('utf-8'))
    time.sleep(0.1)

time.sleep(1.0)
if ser.in_waiting:
    response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    print(f"Examine result: {repr(response)}")
    print(f"Visible: {response}")

ser.close()
