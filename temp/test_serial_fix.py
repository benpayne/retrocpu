#!/usr/bin/env python3
"""
Test the zero page fix by reading serial output
"""
import serial
import time
import sys

def main():
    port = '/dev/ttyACM0'
    baud = 115200

    print(f"Connecting to {port} at {baud} baud...")

    try:
        with serial.Serial(port, baud, timeout=5) as ser:
            print("Connected! Waiting for output...\n")
            print("=" * 70)

            # Read for 10 seconds or until we see the monitor prompt
            start_time = time.time()
            buffer = ""

            while time.time() - start_time < 10:
                if ser.in_waiting:
                    data = ser.read(ser.in_waiting).decode('ascii', errors='replace')
                    print(data, end='', flush=True)
                    buffer += data

                    # Check if we've seen the test results
                    if "Address Range Test" in buffer and "> " in buffer:
                        print("\n" + "=" * 70)
                        print("\nTest output received! Analyzing results...")

                        # Check for failures
                        lines = buffer.split('\n')
                        for line in lines:
                            if ':' in line and ('00:' in line or '10:' in line or '80:' in line or 'FF:' in line):
                                parts = line.split(':')
                                if len(parts) >= 2:
                                    addr = parts[0].strip()
                                    value = parts[1].strip().split()[0] if parts[1].strip() else "??"
                                    # Check if the value matches expected pattern
                                    if addr in ['00', '10', '80', 'FF'] and value == '00':
                                        print(f"FAIL: Address ${addr} still reads $00")
                                    elif addr in ['00', '10', '80', 'FF'] and value != '00':
                                        print(f"SUCCESS: Address ${addr} now reads ${value} (not $00)")
                                    elif addr in ['0100', '0150', '0200'] and value != '00':
                                        print(f"OK: Address ${addr} reads ${value} (as expected)")

                        return 0

                time.sleep(0.1)

            print("\n" + "=" * 70)
            print("\nTimeout waiting for complete output")
            return 1

    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1

if __name__ == "__main__":
    sys.exit(main())
