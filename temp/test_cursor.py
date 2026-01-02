#!/usr/bin/env python3
"""
Test GPU cursor display - blinking cursor at various positions
"""

import serial
import time

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600

def send_cmd(ser, cmd):
    """Send monitor command"""
    for char in cmd:
        ser.write(char.encode())
        time.sleep(0.005)
    ser.write(b'\r')
    ser.flush()
    time.sleep(0.01)

def main():
    print("GPU Cursor Test")
    print("=" * 60)

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(0.5)
        ser.reset_input_buffer()

        # Set 80-column mode and clear
        print("1. Setting 80-column mode and clearing screen...")
        send_cmd(ser, "D C013 06")  # MODE + CURSOR_EN
        time.sleep(0.2)

        # Set colors
        print("2. Setting white on blue...")
        send_cmd(ser, "D C014 07")  # FG = White
        send_cmd(ser, "D C015 01")  # BG = Blue

        # Write some text
        print("3. Writing text...")
        for char in "Hello, World! The cursor should be blinking at the end of this line.":
            send_cmd(ser, f"D C010 {ord(char):02X}")

        # Cursor should be at end of text, blinking
        print("\nWaiting 5 seconds to observe cursor blink...")
        time.sleep(5)

        # Move cursor to specific position
        print("4. Moving cursor to row 5, column 20...")
        send_cmd(ser, "D C011 05")  # Row 5
        send_cmd(ser, "D C012 14")  # Col 20 (0x14)

        print("\nWaiting 5 seconds - cursor should blink at row 5, col 20...")
        time.sleep(5)

        # Write more text (cursor moves as we write)
        print("5. Writing text at new position...")
        for char in "CURSOR MOVES HERE":
            send_cmd(ser, f"D C010 {ord(char):02X}")

        print("\nWaiting 5 seconds - cursor should blink after 'HERE'...")
        time.sleep(5)

        # Test cursor at various colors
        print("6. Testing cursor with different colors...")
        send_cmd(ser, "D C011 0A")  # Row 10
        send_cmd(ser, "D C012 00")  # Col 0

        colors = [
            (0x07, 0x00, "White on Black"),
            (0x00, 0x07, "Black on White"),
            (0x04, 0x03, "Red on Cyan"),
            (0x06, 0x01, "Yellow on Blue"),
        ]

        for fg, bg, desc in colors:
            send_cmd(ser, f"D C014 {fg:02X}")  # Set FG
            send_cmd(ser, f"D C015 {bg:02X}")  # Set BG
            for char in f"{desc:20s}":
                send_cmd(ser, f"D C010 {ord(char):02X}")
            print(f"   {desc}")
            time.sleep(2)

        print("\n" + "=" * 60)
        print("Cursor test complete! Observe:")
        print("  - Cursor should be blinking (2 Hz = 2 blinks per second)")
        print("  - Cursor appears as inverted character cell")
        print("  - Cursor follows text as you write")
        print("  - Cursor works with all color combinations")
        print("=" * 60)

        ser.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
