#!/usr/bin/env python3
"""
Minimal scroll test - just fills screen and writes one more char to scroll
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
    print("Minimal Scroll Test")
    print("=" * 60)

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(0.5)
        ser.reset_input_buffer()

        # Set 80-column mode (automatically triggers clear + cursor reset)
        print("1. Setting 80-column mode and clearing screen...")
        send_cmd(ser, "D C013 06")  # bit[1]=MODE (80-col), bit[2]=CURSOR_EN
        time.sleep(0.2)  # Mode change triggers clear

        # Write marker at row 0
        print("2. Writing 'ROW-00-START' at row 0...")
        send_cmd(ser, "D C011 00")
        send_cmd(ser, "D C012 00")
        for char in "ROW-00-START":
            send_cmd(ser, f"D C010 {ord(char):02X}")

        # Write single character at each of rows 1-29
        print("3. Writing single chars at rows 1-29...")
        for row in range(1, 30):
            send_cmd(ser, f"D C011 {row:02X}")
            send_cmd(ser, "D C012 00")
            send_cmd(ser, f"D C010 {ord('A') + row:02X}")

        # Now cursor is at (29, 1). Fill rest of row 29
        print("4. Filling rest of row 29 with 'X's...")
        for col in range(1, 80):
            send_cmd(ser, "D C010 58")  # 'X'

        # Cursor is now at (29, 80) which auto-wraps to (29, 0) and triggers scroll!
        time.sleep(0.3)  # Wait for scroll/clear

        # Write "AFTER" at start of what should now be a cleared bottom line
        print("5. Writing 'AFTER' at bottom line...")
        for char in "AFTER":
            send_cmd(ser, f"D C010 {ord(char):02X}")

        print("\n" + "=" * 60)
        print("Expected results (in 80-column mode):")
        print("  Line 1 (top): Should start with 'B' (row 1 after row 0 scrolled off)")
        print("  Line 29 (bottom): Should show 'AFTER' + 75 spaces")
        print("  Line 29 should NOT show 'ROW-00-START' or any X's before 'AFTER'!")
        print("\nWhat do you see on:")
        print("  - Top line (first 20 chars)?")
        print("  - Bottom line (first 20 chars)?")
        print("=" * 60)

        ser.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
