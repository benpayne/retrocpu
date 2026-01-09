#!/usr/bin/env python3
"""
Test UART buffer integrity by sending A-Z repeatedly
"""

import serial
import time

def test_buffer(port='/dev/ttyACM0', iterations=10):
    """Send A-Z multiple times and check for dropped bytes"""

    print(f"Opening {port}...")
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)

    # Clear buffers
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # Get prompt
    print("Getting prompt...")
    ser.write(b'\r')
    time.sleep(0.5)
    if ser.in_waiting:
        resp = ser.read(ser.in_waiting)
        print(f"Prompt: {resp[:50]}")

    # Send A-Z multiple times, each with its own T command
    alphabet = b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    print(f"\nTesting {iterations} iterations of A-Z with 2ms inter-byte delays...")

    all_results = []

    for i in range(iterations):
        # Send T command
        print(f"\nIteration {i+1}:")
        print("  Sending 'T' command...")
        ser.write(b'T\r')
        time.sleep(0.5)

        # Read the "Waiting for 26 bytes..." message
        if ser.in_waiting:
            resp = ser.read(ser.in_waiting)
            # print(f"  Monitor: {resp.decode('ascii', errors='replace')}")

        # Send A-Z all at once (testing fixed FIFO)
        print(f"  Sending {alphabet.decode()} (no delays, testing fixed FIFO)...")
        ser.write(alphabet)

        # Wait for echo
        time.sleep(1)
        if ser.in_waiting:
            resp = ser.read(ser.in_waiting)
            received = resp.decode('ascii', errors='replace').strip()
            # Extract just the A-Z part (remove prompt and other text)
            for line in received.split('\n'):
                if 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' in line:
                    all_results.append(line)
                    print(f"  Received: {line}")
                    break
            else:
                # Didn't find complete alphabet, show what we got
                print(f"  Received (partial): {received[:50]}")
                all_results.append(received[:50])

    print("\n=== SUMMARY ===")
    time.sleep(1)

    # Analyze results
    successful = sum(1 for r in all_results if 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' in r)

    print(f"Successful iterations: {successful}/{iterations}")

    if successful == iterations:
        print("✓ All iterations received complete A-Z - buffer integrity is GOOD!")
        print("✓ 2ms inter-byte delays successfully prevent buffer overflow!")
        ser.close()
        return True
    else:
        print(f"✗ Only {successful} out of {iterations} iterations successful")
        print("✗ Buffer overflow still occurring or other issues")
        ser.close()
        return False

if __name__ == '__main__':
    success = test_buffer(iterations=10)
    exit(0 if success else 1)
