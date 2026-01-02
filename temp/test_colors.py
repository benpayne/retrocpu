#!/usr/bin/env python3
"""
Test GPU color functionality - display all 8 colors
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
    print("GPU Color Test")
    print("=" * 60)

    colors = [
        (0x00, "Black"),
        (0x01, "Blue"),
        (0x02, "Green"),
        (0x03, "Cyan"),
        (0x04, "Red"),
        (0x05, "Magenta"),
        (0x06, "Yellow"),
        (0x07, "White"),
    ]

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(0.5)
        ser.reset_input_buffer()

        # Set 80-column mode and clear
        print("1. Setting 80-column mode...")
        send_cmd(ser, "D C013 06")  # MODE + CURSOR_EN
        time.sleep(0.2)

        print("2. Testing all 8 foreground colors on black background...")
        send_cmd(ser, "D C015 00")  # BG = Black

        for color_val, color_name in colors:
            print(f"   Writing '{color_name}' in {color_name} color...")
            send_cmd(ser, f"D C014 {color_val:02X}")  # Set FG color
            for char in f"{color_name:8s} ":  # 9 chars including space
                send_cmd(ser, f"D C010 {ord(char):02X}")

        # Move to next line
        send_cmd(ser, "D C011 01")  # Row 1
        send_cmd(ser, "D C012 00")  # Col 0

        print("3. Testing all 8 background colors with white text...")
        send_cmd(ser, "D C014 07")  # FG = White

        for color_val, color_name in colors:
            print(f"   Writing '{color_name}' on {color_name} background...")
            send_cmd(ser, f"D C015 {color_val:02X}")  # Set BG color
            for char in f"{color_name:8s} ":  # 9 chars including space
                send_cmd(ser, f"D C010 {ord(char):02X}")

        # Demo: Rainbow text
        print("4. Writing rainbow text...")
        send_cmd(ser, "D C011 03")  # Row 3
        send_cmd(ser, "D C012 00")  # Col 0
        send_cmd(ser, "D C015 00")  # BG = Black

        rainbow_text = "RAINBOW: Red Green Cyan Yellow Magenta Blue White"
        rainbow_colors = [0x04, 0x02, 0x03, 0x06, 0x05, 0x01, 0x07]

        for i, char in enumerate(rainbow_text):
            color_idx = i % len(rainbow_colors)
            send_cmd(ser, f"D C014 {rainbow_colors[color_idx]:02X}")
            send_cmd(ser, f"D C010 {ord(char):02X}")

        print("\n" + "=" * 60)
        print("Color test complete! Check the display:")
        print("  Row 0: All 8 foreground colors on black background")
        print("  Row 1: White text on all 8 background colors")
        print("  Row 3: Rainbow colored text")
        print("=" * 60)

        ser.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
