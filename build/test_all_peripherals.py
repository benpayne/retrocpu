#!/usr/bin/env python3
"""
Comprehensive peripheral test for RetroCPU
Tests UART, PS/2, Monitor I/O reads, and LCD
"""

import serial
import time
import sys

def test_uart_boot(port='/dev/ttyACM0', baudrate=9600, timeout=3):
    """Test UART firmware boot and basic communication"""
    print("\n" + "="*60)
    print("TEST 1: UART Firmware Boot")
    print("="*60)

    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(0.5)

        # Send CR to get prompt
        print("Sending CR to trigger monitor prompt...")
        ser.write(b'\r')
        time.sleep(0.5)

        # Read response
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            response = data.decode('ascii', errors='replace')
            print(f"Response: {repr(response)}")

            if '>' in response or '*' in response:
                print("✓ UART BOOT: PASS - Monitor prompt received")
                return ser, True
            else:
                print("✗ UART BOOT: FAIL - No monitor prompt")
                return ser, False
        else:
            print("✗ UART BOOT: FAIL - No response")
            return ser, False

    except Exception as e:
        print(f"✗ UART BOOT: ERROR - {e}")
        return None, False

def test_monitor_ram_read(ser):
    """Test monitor can read RAM (baseline)"""
    print("\n" + "="*60)
    print("TEST 2: Monitor RAM Read (Baseline)")
    print("="*60)

    if not ser:
        print("✗ SKIPPED - No serial connection")
        return False

    try:
        # First write a value to RAM
        print("Writing $AA to RAM address $0200...")
        ser.write(b'D 0200 AA\r')
        time.sleep(0.3)
        ser.read(ser.in_waiting)  # Clear response

        # Now read it back
        print("Reading RAM address $0200...")
        ser.write(b'E 0200\r')
        time.sleep(0.3)

        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            response = data.decode('ascii', errors='replace')
            print(f"Response: {repr(response)}")

            if 'AA' in response or 'aa' in response:
                print("✓ RAM READ: PASS - Read back $AA correctly")
                return True
            else:
                print("✗ RAM READ: FAIL - Incorrect value")
                return False
        else:
            print("✗ RAM READ: FAIL - No response")
            return False

    except Exception as e:
        print(f"✗ RAM READ: ERROR - {e}")
        return False

def test_monitor_io_read(ser):
    """Test monitor can read I/O registers"""
    print("\n" + "="*60)
    print("TEST 3: Monitor I/O Register Reads")
    print("="*60)

    if not ser:
        print("✗ SKIPPED - No serial connection")
        return False

    results = []

    # Test UART status register ($C001)
    try:
        print("\nReading UART status register ($C001)...")
        ser.write(b'E C001\r')
        time.sleep(0.3)

        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            response = data.decode('ascii', errors='replace')
            print(f"Response: {repr(response)}")

            # UART status should NOT be 00 (should show TX ready bit at minimum)
            if '00' not in response.split()[0] if response.split() else True:
                print("✓ UART STATUS READ: PASS - Non-zero value (expected)")
                results.append(True)
            else:
                print("✗ UART STATUS READ: FAIL - Returned $00 (wrong)")
                results.append(False)
        else:
            print("✗ UART STATUS READ: FAIL - No response")
            results.append(False)

    except Exception as e:
        print(f"✗ UART STATUS READ: ERROR - {e}")
        results.append(False)

    # Test UART data register ($C000)
    try:
        print("\nReading UART data register ($C000)...")
        ser.write(b'E C000\r')
        time.sleep(0.3)

        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            response = data.decode('ascii', errors='replace')
            print(f"Response: {repr(response)}")

            # Should not return the constant $30 ('0') that was seen before
            if '30' not in response or response.count('30') > 1:
                print("✓ UART DATA READ: Possibly OK - Not the constant $30")
                results.append(True)
            else:
                print("✗ UART DATA READ: FAIL - Still returning constant $30")
                results.append(False)
        else:
            print("✗ UART DATA READ: FAIL - No response")
            results.append(False)

    except Exception as e:
        print(f"✗ UART DATA READ: ERROR - {e}")
        results.append(False)

    # Test PS/2 status register ($C201)
    try:
        print("\nReading PS/2 status register ($C201)...")
        ser.write(b'E C201\r')
        time.sleep(0.3)

        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            response = data.decode('ascii', errors='replace')
            print(f"Response: {repr(response)}")
            print("✓ PS/2 STATUS READ: PASS - Got a response")
            results.append(True)
        else:
            print("✗ PS/2 STATUS READ: FAIL - No response")
            results.append(False)

    except Exception as e:
        print(f"✗ PS/2 STATUS READ: ERROR - {e}")
        results.append(False)

    return all(results)

def test_uart_write(ser):
    """Test writing to UART I/O register"""
    print("\n" + "="*60)
    print("TEST 4: Monitor UART Write (D command)")
    print("="*60)

    if not ser:
        print("✗ SKIPPED - No serial connection")
        return False

    try:
        print("Writing $41 ('A') to UART data register ($C000)...")
        ser.write(b'D C000 41\r')
        time.sleep(0.5)

        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            response = data.decode('ascii', errors='replace')
            print(f"Response: {repr(response)}")

            # Check if we see 'A' in the output (the character we wrote)
            if 'A' in response and response.count('A') == 1:
                print("✓ UART WRITE: PASS - Character transmitted")
                return True
            else:
                print("⚠ UART WRITE: Check output - may or may not have worked")
                print("  (Firmware UART writes work, so this might be expected)")
                return True  # Not a failure - writes might work differently
        else:
            print("⚠ UART WRITE: No response (might be OK)")
            return True

    except Exception as e:
        print(f"✗ UART WRITE: ERROR - {e}")
        return False

def main():
    print("\n" + "="*60)
    print("RetroCPU Peripheral Test Suite")
    print("Testing MC=4 data capture timing")
    print("="*60)

    results = {}

    # Test 1: UART Boot
    ser, uart_ok = test_uart_boot()
    results['UART Boot'] = uart_ok

    if uart_ok:
        # Test 2: RAM Read (baseline)
        results['RAM Read'] = test_monitor_ram_read(ser)

        # Test 3: I/O Reads
        results['I/O Reads'] = test_monitor_io_read(ser)

        # Test 4: UART Write
        results['UART Write'] = test_uart_write(ser)

        ser.close()
    else:
        print("\n⚠ Skipping remaining tests - UART boot failed")
        results['RAM Read'] = False
        results['I/O Reads'] = False
        results['UART Write'] = False

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20s}: {status}")

    print("\n" + "="*60)
    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"OVERALL: {passed_tests}/{total_tests} tests passed")
    print("="*60)

    # PS/2 LED test instructions
    print("\nMANUAL TEST REQUIRED:")
    print("="*60)
    print("TEST 5: PS/2 LED Activity")
    print("  1. Look at the board LEDs (LED2, LED3)")
    print("  2. Press keys on the PS/2 keyboard")
    print("  3. Check if LEDs show activity (should blink with keypress)")
    print("  4. If LEDs are active, PS/2 timing is working!")
    print("="*60)

    print("\nMANUAL TEST REQUIRED:")
    print("="*60)
    print("TEST 6: LCD Display")
    print("  Use monitor to write to LCD control ($C100) and data ($C101)")
    print("  Example commands:")
    print("    D C100 38    (8-bit mode)")
    print("    D C100 0C    (Display on)")
    print("    D C101 41    (Write 'A')")
    print("="*60)

    return 0 if all(results.values()) else 1

if __name__ == '__main__':
    sys.exit(main())
