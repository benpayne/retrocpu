#!/usr/bin/env python3
"""Check the full I/O vector JMP instructions."""

import serial
import time

PORT = '/dev/ttyACM0'
BAUD = 9600

def send_slow(ser, text, delay=0.1):
    for char in text:
        ser.write(char.encode())
        time.sleep(delay)

def examine(ser, addr):
    """Examine memory and return value."""
    send_slow(ser, f'E {addr}\r')
    time.sleep(0.5)
    response = ''
    while ser.in_waiting:
        response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        time.sleep(0.05)

    # Parse "ADDR: VAL"
    for line in response.split('\n'):
        if ':' in line:
            parts = line.split(':')
            if len(parts) >= 2:
                val = parts[1].strip().split()[0]
                if len(val) == 2:
                    return val
    return None

print("Checking I/O Vector Jump Instructions\n")

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

# Clear buffers
if ser.in_waiting:
    ser.read(ser.in_waiting)

# CHRIN vector at $FFF0-$FFF2
print("CHRIN vector at $FFF0:")
fff0 = examine(ser, 'FFF0')  # Should be $4C (JMP)
fff1 = examine(ser, 'FFF1')  # Low byte of address
fff2 = examine(ser, 'FFF2')  # High byte of address

if fff0 and fff1 and fff2:
    target = f"${fff2}{fff1}"
    print(f"  $FFF0: ${fff0} (JMP opcode)")
    print(f"  $FFF1: ${fff1}")
    print(f"  $FFF2: ${fff2}")
    print(f"  → JMP {target} (CHRIN routine)\n")

# CHROUT vector at $FFF3-$FFF5
print("CHROUT vector at $FFF3:")
fff3 = examine(ser, 'FFF3')  # Should be $4C (JMP)
fff4 = examine(ser, 'FFF4')  # Low byte of address
fff5 = examine(ser, 'FFF5')  # High byte of address

if fff3 and fff4 and fff5:
    target = f"${fff5}{fff4}"
    print(f"  $FFF3: ${fff3} (JMP opcode)")
    print(f"  $FFF4: ${fff4}")
    print(f"  $FFF5: ${fff5}")
    print(f"  → JMP {target} (CHROUT routine)\n")

# LOAD vector at $FFF6-$FFF8
print("LOAD/break vector at $FFF6:")
fff6 = examine(ser, 'FFF6')  # Should be $A9 (LDA #)
fff7 = examine(ser, 'FFF7')  # Immediate value
fff8 = examine(ser, 'FFF8')  # Should be $60 (RTS)

if fff6 and fff7 and fff8:
    print(f"  $FFF6: ${fff6} (LDA immediate)")
    print(f"  $FFF7: ${fff7} (value)")
    print(f"  $FFF8: ${fff8} (RTS)")

# Check BASIC ROM start
print("\nBASIC ROM at $8000:")
basic_start = examine(ser, '8000')
if basic_start:
    print(f"  $8000: ${basic_start}")

ser.close()
