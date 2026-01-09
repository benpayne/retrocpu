#!/usr/bin/env python3
"""
Simple test to verify serial communication with monitor
"""

import serial
import time

port = '/dev/ttyACM0'

print(f"Opening {port}...")
ser = serial.Serial(port, 9600, timeout=1)
time.sleep(1)

print("Sending carriage return to get prompt...")
ser.write(b'\r')
time.sleep(0.5)

print("Reading response...")
if ser.in_waiting:
    data = ser.read(ser.in_waiting)
    print(f"Received: {data}")
    print(f"ASCII: {data.decode('ascii', errors='replace')}")
else:
    print("No response received")

print("\nSending 'H' for help...")
ser.write(b'H\r')
time.sleep(1)

if ser.in_waiting:
    data = ser.read(ser.in_waiting)
    print(f"Received {len(data)} bytes:")
    print(data.decode('ascii', errors='replace'))
else:
    print("No response received")

ser.close()
