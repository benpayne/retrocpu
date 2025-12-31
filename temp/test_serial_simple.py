#!/usr/bin/env python3
"""Simple serial connection test."""

import serial
import time

PORT = '/dev/ttyACM0'
BAUD = 9600

print(f"Opening {PORT} at {BAUD} baud...")
ser = serial.Serial(PORT, BAUD, timeout=1)
print("Connected!")

time.sleep(2)

# Read any boot messages
if ser.in_waiting:
    data = ser.read(ser.in_waiting)
    print(f"Boot messages ({len(data)} bytes):")
    print(data.decode('utf-8', errors='replace'))

# Send newline
print("\nSending newline...")
ser.write(b'\r\n')
time.sleep(1)

# Read response
if ser.in_waiting:
    data = ser.read(ser.in_waiting)
    print(f"Response ({len(data)} bytes):")
    print(data.decode('utf-8', errors='replace'))
else:
    print("No response!")

# Send 'E FFF0' command
print("\nSending 'E FFF0' command...")
for char in 'E FFF0\r':
    ser.write(char.encode())
    time.sleep(0.1)
time.sleep(0.5)

# Read response
if ser.in_waiting:
    data = ser.read(ser.in_waiting)
    print(f"Response ({len(data)} bytes):")
    print(data.decode('utf-8', errors='replace'))
    print("Hex:", data.hex())
else:
    print("No response!")

ser.close()
