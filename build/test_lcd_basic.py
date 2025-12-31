#!/usr/bin/env python3
"""
Test LCD via BASIC POKE commands
"""

import serial
import time

def send_slow(ser, text, delay=0.06):
    """Send text with delay between characters for UART RX timing"""
    for char in text:
        ser.write(char.encode())
        time.sleep(delay)

def wait_for_prompt(ser, prompt, timeout=5):
    """Wait for a specific prompt"""
    start = time.time()
    buffer = ""
    while time.time() - start < timeout:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting).decode('ascii', errors='ignore')
            buffer += data
            print(data, end='', flush=True)
            if prompt in buffer:
                return True
        time.sleep(0.05)
    return False

def main():
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=3)
    time.sleep(0.5)

    print("=" * 70)
    print("LCD Controller Test via BASIC")
    print("=" * 70)

    # Read any existing data
    existing = ser.read(2000).decode('ascii', errors='ignore')
    print(existing)

    # Start BASIC
    print("\n[Starting BASIC...]")
    send_slow(ser, 'G\r')
    time.sleep(0.2)

    # Wait for MEMORY SIZE prompt
    print("\n[Waiting for BASIC prompts...]")
    buffer = ""
    for i in range(50):  # 5 seconds
        if ser.in_waiting:
            data = ser.read(ser.in_waiting).decode('ascii', errors='ignore')
            buffer += data
            print(data, end='', flush=True)
        time.sleep(0.1)

    # Send memory size
    print("\n\n[Sending memory size: 32000]")
    send_slow(ser, '32000\r', delay=0.07)
    time.sleep(0.3)

    # Read response
    data = ser.read(1000).decode('ascii', errors='ignore')
    print(data)

    # Send terminal width
    print("\n[Sending terminal width: 72]")
    send_slow(ser, '72\r', delay=0.07)
    time.sleep(0.5)

    # Read BASIC banner
    data = ser.read(2000).decode('ascii', errors='ignore')
    print(data)

    # Now send POKE commands to write to LCD
    print("\n" + "=" * 70)
    print("Writing 'HELLO' to LCD at $C100 (49408 decimal)...")
    print("=" * 70)

    commands = [
        ('H', 'POKE 49408,72\r'),   # 'H' = 0x48 = 72
        ('E', 'POKE 49408,69\r'),   # 'E' = 0x45 = 69
        ('L', 'POKE 49408,76\r'),   # 'L' = 0x4C = 76
        ('L', 'POKE 49408,76\r'),   # 'L' = 0x4C = 76
        ('O', 'POKE 49408,79\r'),   # 'O' = 0x4F = 79
    ]

    for char, cmd in commands:
        print(f"\n[Writing '{char}' to LCD...]")
        send_slow(ser, cmd, delay=0.07)
        time.sleep(0.3)
        response = ser.read(500).decode('ascii', errors='ignore')
        print(response, end='')

    print("\n\n" + "=" * 70)
    print("Test complete! Check your LCD display - you should see 'HELLO'")
    print("=" * 70)

    ser.close()

if __name__ == '__main__':
    main()
