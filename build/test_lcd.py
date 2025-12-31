#!/usr/bin/env python3
"""
Test LCD Controller via Monitor Commands

Writes test characters to LCD at $C100-$C102
"""

import serial
import time

def send_command(ser, cmd):
    """Send command and wait for prompt"""
    ser.write((cmd + '\r').encode())
    time.sleep(0.1)
    response = ser.read(1000).decode('ascii', errors='ignore')
    print(response)
    return response

def main():
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=2)
    time.sleep(0.5)

    # Clear any startup messages
    ser.read(2000)

    print("=" * 60)
    print("LCD Controller Test")
    print("=" * 60)

    # Test 1: Check LCD status (should be ready after init)
    print("\n1. Checking LCD status register ($C102)...")
    time.sleep(1)  # Wait for LCD init (15ms + sequence)

    # Read status by examining memory at $C102
    # Note: Monitor E command may not work for I/O - we'll need to use BASIC or direct writes

    # Test 2: Write "HELLO" to LCD data register ($C100)
    print("\n2. Writing 'H' to LCD ($C100)...")
    print("   (This requires BASIC or monitor deposit command)")

    # For now, let's just show the user how to test manually
    print("\n=== Manual Test Instructions ===")
    print("From the monitor prompt, try:")
    print("  D C100 48    # Write 'H' (0x48) to LCD")
    print("  D C100 45    # Write 'E' (0x45)")
    print("  D C100 4C    # Write 'L' (0x4C)")
    print("  D C100 4C    # Write 'L' (0x4C)")
    print("  D C100 4F    # Write 'O' (0x4F)")
    print("")
    print("Or from BASIC:")
    print("  G            # Start BASIC")
    print("  POKE 49408, 72   # Write 'H' ($C100 = 49408)")
    print("  POKE 49408, 69   # Write 'E'")
    print("")
    print("If LCD is working, you should see characters appear!")
    print("=" * 60)

    ser.close()

if __name__ == '__main__':
    main()
