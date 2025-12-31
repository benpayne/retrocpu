#!/usr/bin/env python3
"""
Test LCD via RetroCPU BASIC
Writes "HELLO" to the LCD display
"""

import serial
import time
import sys

def send_command(ser, cmd):
    """Send a command and wait for response"""
    print(f"Sending: {cmd}")
    ser.write(f"{cmd}\r".encode())
    time.sleep(0.2)  # Wait for command to execute

    # Read any response
    while ser.in_waiting:
        char = ser.read().decode('ascii', errors='ignore')
        sys.stdout.write(char)
        sys.stdout.flush()

def main():
    port = '/dev/ttyACM0'
    baud = 115200

    print(f"Opening {port} at {baud} baud...")
    ser = serial.Serial(port, baud, timeout=1)
    time.sleep(0.5)

    # Clear any initial output
    time.sleep(1)
    while ser.in_waiting:
        data = ser.read().decode('ascii', errors='ignore')
        sys.stdout.write(data)
        sys.stdout.flush()

    print("\n=== Starting BASIC ===\n")

    # Start BASIC with 'G' command
    ser.write(b"G\r")
    time.sleep(0.5)

    # Read BASIC startup message
    output = ""
    while ser.in_waiting:
        data = ser.read().decode('ascii', errors='ignore')
        output += data
        sys.stdout.write(data)
        sys.stdout.flush()

    # Answer memory size question
    if "MEMORY SIZE?" in output:
        print("\nAnswering MEMORY SIZE with 32000")
        ser.write(b"32000\r")
        time.sleep(0.5)

        # Read response
        output = ""
        while ser.in_waiting:
            data = ser.read().decode('ascii', errors='ignore')
            output += data
            sys.stdout.write(data)
            sys.stdout.flush()

        # Answer terminal width question
        if "TERMINAL WIDTH?" in output:
            print("\nAnswering TERMINAL WIDTH with 80")
            ser.write(b"80\r")
            time.sleep(0.5)

            # Read response (should be READY prompt)
            while ser.in_waiting:
                data = ser.read().decode('ascii', errors='ignore')
                sys.stdout.write(data)
                sys.stdout.flush()

    print("\n=== Testing LCD via BASIC ===\n")

    # Send clear display command (0x01)
    send_command(ser, "POKE 49409,0")  # Command register = $C101
    send_command(ser, "POKE 49409,1")  # Clear display
    time.sleep(0.5)

    # Write "HELLO"
    chars = "HELLO"
    for ch in chars:
        ascii_val = ord(ch)
        print(f"Writing '{ch}' (ASCII {ascii_val})")
        send_command(ser, f"POKE 49408,{ascii_val}")  # Data register = $C100
        time.sleep(0.1)

    print("\n=== Test complete! ===")
    print("You should see 'HELLO' on the LCD display")

    ser.close()

if __name__ == "__main__":
    main()
