#!/usr/bin/env python3
"""Test what commands the monitor actually supports"""

import serial
import time

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(1)

# Clear buffers
ser.reset_input_buffer()

# Get prompt
print("Getting prompt...")
ser.write(b'\r')
time.sleep(0.5)
response = ser.read(ser.in_waiting)
print(response.decode('ascii', errors='replace'))

# Try 'H' for help
print("\nSending 'H' for help...")
ser.write(b'H\r')
time.sleep(1)
response = ser.read(ser.in_waiting)
print(response.decode('ascii', errors='replace'))

ser.close()
