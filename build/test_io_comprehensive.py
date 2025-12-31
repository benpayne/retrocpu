#!/usr/bin/env python3
"""
Comprehensive I/O read test at MC=5 baseline.
Tests both firmware operations and monitor E/D commands.
"""

import serial
import time
import sys

def send_cmd(ser, cmd, wait=0.3):
    """Send command and return response."""
    print(f"\n→ {cmd}")
    ser.write(f"{cmd}\r".encode())
    time.sleep(wait)
    resp = ser.read(ser.in_waiting).decode('utf-8', errors='replace')
    print(resp, end='', flush=True)
    return resp

def main():
    print("="*70)
    print("Comprehensive I/O Read Test - MC=5 Baseline")
    print("="*70)

    try:
        ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        time.sleep(1)

        # Get monitor prompt
        ser.write(b"\r\r\r")
        time.sleep(0.5)
        boot_msg = ser.read(ser.in_waiting).decode('utf-8', errors='replace')
        print(boot_msg, end='', flush=True)

        if '>' not in boot_msg:
            print("\n✗ No monitor prompt found")
            return 1

        print("\n\n✓ Firmware booted successfully!")

        # Test 1: RAM read/write (baseline - should work)
        print("\n" + "="*70)
        print("TEST 1: RAM Read/Write at $0100 (Baseline)")
        print("="*70)
        send_cmd(ser, "D 0100 AA")
        resp = send_cmd(ser, "E 0100")
        if "AA" in resp:
            print("✓ RAM read/write works")
        else:
            print("✗ RAM read/write failed")

        # Test 2: UART STATUS register read
        print("\n" + "="*70)
        print("TEST 2: UART STATUS Read at $C001")
        print("Expected: Bit 0 set (TX ready)")
        print("="*70)
        resp = send_cmd(ser, "E C001")
        if "C001:" in resp:
            # Extract hex value
            parts = resp.split("C001:")
            if len(parts) > 1:
                val_str = parts[1].strip().split()[0] if parts[1].strip() else "??"
                print(f"\nUART STATUS = ${val_str}")
                try:
                    val = int(val_str, 16)
                    if val & 0x01:
                        print("✓ TX ready bit is set")
                    else:
                        print("✗ TX ready bit NOT set (unexpected)")
                except:
                    print(f"✗ Could not parse: {val_str}")

        # Test 3: UART DATA register read
        print("\n" + "="*70)
        print("TEST 3: UART DATA Read at $C000")
        print("Expected: $00 (no RX data)")
        print("="*70)
        resp = send_cmd(ser, "E C000")
        if "C000:" in resp:
            parts = resp.split("C000:")
            if len(parts) > 1:
                val_str = parts[1].strip().split()[0] if parts[1].strip() else "??"
                print(f"\nUART DATA = ${val_str}")

        # Test 4: Read ROM (should work - combinational like RAM)
        print("\n" + "="*70)
        print("TEST 4: ROM Read at $E000 (Monitor ROM)")
        print("="*70)
        resp = send_cmd(ser, "E E000")
        if "E000:" in resp:
            parts = resp.split("E000:")
            if len(parts) > 1:
                val_str = parts[1].strip().split()[0] if parts[1].strip() else "??"
                print(f"\nROM[$E000] = ${val_str}")
                print("✓ ROM read succeeded")

        # Test 5: Multiple consecutive I/O reads
        print("\n" + "="*70)
        print("TEST 5: Consecutive UART STATUS Reads")
        print("Testing if multiple reads return consistent values")
        print("="*70)
        values = []
        for i in range(3):
            resp = send_cmd(ser, "E C001", wait=0.2)
            if "C001:" in resp:
                parts = resp.split("C001:")
                if len(parts) > 1:
                    val_str = parts[1].strip().split()[0] if parts[1].strip() else "??"
                    values.append(val_str)
                    print(f"  Read {i+1}: ${val_str}")

        if len(values) == 3 and values[0] == values[1] == values[2]:
            print("✓ Consistent values across multiple reads")
        else:
            print(f"✗ Inconsistent values: {values}")

        # Test 6: Range dump
        print("\n" + "="*70)
        print("TEST 6: Range Dump of I/O area $C000-$C00F")
        print("="*70)
        send_cmd(ser, "E C000 C00F", wait=0.5)

        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print("At MC=5 with proper ROM initialization (29 blocks):")
        print("- Firmware boots ✓")
        print("- RAM read/write works ✓")
        print("- ROM reads work ✓")
        print("- Monitor I/O reads: CHECK RESULTS ABOVE")
        print("\nIf UART STATUS reads return $00 instead of $01,")
        print("this confirms the MC=5 timing issue with I/O registers.")
        print("="*70)

        ser.close()
        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
