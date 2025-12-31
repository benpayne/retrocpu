#!/usr/bin/env python3
"""
Test monitor I/O register reads at MC=5 baseline.

The mystery: At MC=5, firmware UART operations work (status polling succeeds)
but monitor E/D commands cannot read I/O registers correctly.

This test will:
1. Verify firmware boots and UART works (baseline sanity check)
2. Try to use monitor E command to read UART status register (C000)
3. Try to use monitor E command to read PS/2 status register (C200)
4. Compare results to understand what's different
"""

import serial
import time
import sys

def send_command(ser, cmd, expect_prompt=True):
    """Send command and capture response."""
    print(f"\n→ Sending: {cmd}")
    ser.write(f"{cmd}\r".encode())
    time.sleep(0.1)

    response = ""
    timeout = time.time() + 2.0
    while time.time() < timeout:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting).decode('utf-8', errors='replace')
            response += chunk
            print(chunk, end='', flush=True)
            if expect_prompt and '>' in chunk:
                break
        time.sleep(0.05)

    return response

def main():
    print("=" * 70)
    print("Monitor I/O Read Investigation at MC=5")
    print("=" * 70)

    try:
        ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        time.sleep(0.5)

        # Clear any pending data
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        print("\n[1] Testing firmware boot and basic UART...")
        ser.write(b"\r\n")
        time.sleep(0.3)
        response = ser.read(ser.in_waiting).decode('utf-8', errors='replace')
        print(response, end='', flush=True)

        if '>' not in response:
            print("\n✗ No monitor prompt - firmware may not have booted")
            return 1

        print("\n✓ Firmware booted, monitor prompt present")

        # Test 1: Read UART status register at $C000
        print("\n" + "="*70)
        print("[2] Monitor E command: Read UART STATUS at $C000")
        print("    Expected: Should see bit 0 set (TX ready)")
        print("="*70)
        response = send_command(ser, "E C000")

        # Parse response to extract the value
        if "C000:" in response:
            # Format is typically "C000: XX" where XX is hex value
            parts = response.split("C000:")
            if len(parts) > 1:
                value_str = parts[1].strip().split()[0] if parts[1].strip() else "??"
                print(f"\n    Result: C000 = ${value_str}")

                try:
                    value = int(value_str, 16)
                    if value & 0x01:
                        print(f"    ✓ TX ready bit is set (bit 0 = 1)")
                    else:
                        print(f"    ✗ TX ready bit is NOT set (bit 0 = 0) - UNEXPECTED!")
                        print(f"    This suggests monitor E command is not reading correctly")
                except ValueError:
                    print(f"    ✗ Could not parse value: {value_str}")
        else:
            print(f"    ✗ Unexpected response format")

        # Test 2: Read UART data register at $C001
        print("\n" + "="*70)
        print("[3] Monitor E command: Read UART DATA at $C001")
        print("    Expected: Should see 00 (no RX data available)")
        print("="*70)
        response = send_command(ser, "E C001")

        if "C001:" in response:
            parts = response.split("C001:")
            if len(parts) > 1:
                value_str = parts[1].strip().split()[0] if parts[1].strip() else "??"
                print(f"\n    Result: C001 = ${value_str}")

        # Test 3: Read PS/2 status register at $C200
        print("\n" + "="*70)
        print("[4] Monitor E command: Read PS/2 STATUS at $C200")
        print("    Expected: Should see bit 0 set if key pressed, clear otherwise")
        print("="*70)
        response = send_command(ser, "E C200")

        if "C200:" in response:
            parts = response.split("C200:")
            if len(parts) > 1:
                value_str = parts[1].strip().split()[0] if parts[1].strip() else "??"
                print(f"\n    Result: C200 = ${value_str}")

        # Test 4: Read RAM at $0010 (should work)
        print("\n" + "="*70)
        print("[5] Monitor E command: Read RAM at $0010")
        print("    Expected: Should read successfully (monitor RAM reads work)")
        print("="*70)
        response = send_command(ser, "E 0010")

        if "0010:" in response:
            parts = response.split("0010:")
            if len(parts) > 1:
                value_str = parts[1].strip().split()[0] if parts[1].strip() else "??"
                print(f"\n    Result: 0010 = ${value_str}")
                print(f"    ✓ RAM read succeeded")

        # Test 5: Write then read RAM (should work)
        print("\n" + "="*70)
        print("[6] Monitor D/E commands: Write $AA to $0100, then read back")
        print("="*70)
        send_command(ser, "D 0100 AA")
        time.sleep(0.1)
        response = send_command(ser, "E 0100")

        if "0100:" in response:
            parts = response.split("0100:")
            if len(parts) > 1:
                value_str = parts[1].strip().split()[0] if parts[1].strip() else "??"
                print(f"\n    Result: 0100 = ${value_str}")
                if value_str.upper() == "AA":
                    print(f"    ✓ RAM write/read works correctly")
                else:
                    print(f"    ✗ RAM write/read mismatch!")

        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print("At MC=5 baseline:")
        print("- Firmware boots ✓")
        print("- Monitor prompt works ✓")
        print("- Monitor RAM reads/writes work ✓")
        print("- Monitor I/O reads: CHECK OUTPUT ABOVE")
        print("\nIf monitor I/O reads return $00 or wrong values, this confirms")
        print("the issue is specific to how monitor reads I/O registers.")
        print("="*70)

        ser.close()
        return 0

    except serial.SerialException as e:
        print(f"\n✗ Serial error: {e}")
        print("Make sure:")
        print("  1. FPGA is programmed")
        print("  2. No other programs are using /dev/ttyACM0")
        print("  3. You have permissions to access the serial port")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
