#!/usr/bin/env python3
"""
Test script for Monitor and BASIC functionality after M65C02 port.
Tests:
1. Zero page read/write (automatic on boot)
2. Monitor E command (examine memory)
3. BASIC arithmetic (PRINT 2+2)
4. BASIC programming (FOR loop, variables, LIST, NEW)
"""

import serial
import time
import sys

def open_serial(port='/dev/ttyACM0', baudrate=115200, timeout=2):
    """Open serial connection to FPGA."""
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(0.1)  # Allow port to stabilize
        ser.reset_input_buffer()
        return ser
    except Exception as e:
        print(f"Error opening serial port: {e}")
        sys.exit(1)

def read_until_prompt(ser, timeout=5):
    """Read serial output until we see a prompt or timeout."""
    output = []
    start_time = time.time()

    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            text = data.decode('ascii', errors='replace')
            output.append(text)
            print(text, end='', flush=True)

            # Check for common prompts
            if any(p in ''.join(output) for p in ['>', '?', 'Ready', 'READY']):
                break
        time.sleep(0.1)

    return ''.join(output)

def send_command(ser, command, delay=0.5):
    """Send a command and wait for response."""
    print(f"\n>>> Sending: {command}")
    ser.write((command + '\r').encode('ascii'))
    time.sleep(delay)
    return read_until_prompt(ser)

def test_zero_page_output(output):
    """Verify zero page test results in boot output."""
    print("\n" + "="*60)
    print("TEST 1: Zero Page Read/Write")
    print("="*60)

    # Expected patterns if M65C02 fix worked:
    # 00:11 10:22 80:33 FF:44
    # 0100:55 0150:66 0200:77

    checks = [
        ('00:11', 'Zero page $0000 write/read'),
        ('10:22', 'Zero page $0010 write/read'),
        ('80:33', 'Zero page $0080 write/read'),
        ('FF:44', 'Zero page $00FF write/read'),
        ('0100:55', 'Stack page $0100 write/read'),
        ('0150:66', 'Stack page $0150 write/read'),
        ('0200:77', 'RAM $0200 write/read'),
    ]

    results = []
    for pattern, description in checks:
        if pattern in output:
            print(f"✓ PASS: {description} - found '{pattern}'")
            results.append(True)
        else:
            print(f"✗ FAIL: {description} - pattern '{pattern}' not found")
            results.append(False)

    if all(results):
        print("\n🎉 ZERO PAGE FIX VERIFIED! All writes/reads correct.")
        return True
    else:
        print("\n❌ ZERO PAGE BUG STILL PRESENT - Some writes failed.")
        return False

def test_basic_arithmetic(ser):
    """Test BASIC arithmetic (PRINT 2+2)."""
    print("\n" + "="*60)
    print("TEST 3: BASIC Arithmetic (PRINT 2+2)")
    print("="*60)

    response = send_command(ser, 'PRINT 2+2', delay=1.0)

    if '4' in response:
        print("✓ PASS: BASIC correctly calculated 2+2=4")
        return True
    else:
        print("✗ FAIL: Expected '4' in response")
        return False

def test_basic_for_loop(ser):
    """Test BASIC FOR loop."""
    print("\n" + "="*60)
    print("TEST 4: BASIC FOR Loop")
    print("="*60)

    # Clear any existing program
    send_command(ser, 'NEW', delay=0.5)

    # Enter a simple FOR loop program
    send_command(ser, '10 FOR I=1 TO 3', delay=0.3)
    send_command(ser, '20 PRINT I', delay=0.3)
    send_command(ser, '30 NEXT I', delay=0.3)

    # List the program to verify it was entered
    list_output = send_command(ser, 'LIST', delay=0.5)

    # Run the program
    run_output = send_command(ser, 'RUN', delay=1.5)

    # Check if we see 1, 2, 3 in output
    if '1' in run_output and '2' in run_output and '3' in run_output:
        print("✓ PASS: FOR loop executed and printed 1, 2, 3")
        return True
    else:
        print("✗ FAIL: Expected to see 1, 2, 3 in output")
        return False

def test_basic_variables(ser):
    """Test BASIC variables and commands."""
    print("\n" + "="*60)
    print("TEST 5: BASIC Variables, LIST, NEW")
    print("="*60)

    # Clear program
    send_command(ser, 'NEW', delay=0.5)

    # Test immediate mode variable assignment
    send_command(ser, 'A=42', delay=0.3)
    response = send_command(ser, 'PRINT A', delay=0.5)

    var_ok = '42' in response
    if var_ok:
        print("✓ PASS: Variable assignment and retrieval works")
    else:
        print("✗ FAIL: Variable test failed")

    # Test NEW command clears program
    send_command(ser, '10 PRINT "TEST"', delay=0.3)
    send_command(ser, 'NEW', delay=0.5)
    list_output = send_command(ser, 'LIST', delay=0.5)

    new_ok = '10' not in list_output
    if new_ok:
        print("✓ PASS: NEW command clears program")
    else:
        print("✗ FAIL: NEW command did not clear program")

    return var_ok and new_ok

def main():
    print("="*60)
    print("RetroCPU Monitor & BASIC Test Suite")
    print("Post-M65C02 Port Validation")
    print("="*60)

    # Open serial connection
    ser = open_serial()
    print("✓ Serial port opened: /dev/ttyACM0 @ 115200 baud\n")

    # Wait for reset and capture boot output
    print("Waiting for boot output (reset board if needed)...")
    print("-"*60)
    boot_output = read_until_prompt(ser, timeout=10)
    print("-"*60)

    # Test 1: Check zero page test results
    zp_pass = test_zero_page_output(boot_output)

    # Test 2: Monitor E command (skipped - would need to parse monitor prompt)
    print("\n" + "="*60)
    print("TEST 2: Monitor E Command")
    print("="*60)
    print("⚠ Manual test - Type 'E 0000' at monitor prompt to examine memory")
    print("  (This test requires monitor prompt detection)")

    # Determine if we're at monitor or BASIC prompt
    if 'Starting BASIC' in boot_output or 'BASIC' in boot_output.upper():
        print("\n→ System appears to be in BASIC mode")

        # Test 3: BASIC arithmetic
        basic_arith_pass = test_basic_arithmetic(ser)

        # Test 4: BASIC FOR loop
        basic_loop_pass = test_basic_for_loop(ser)

        # Test 5: BASIC variables
        basic_vars_pass = test_basic_variables(ser)

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Zero Page Fix:    {'PASS ✓' if zp_pass else 'FAIL ✗'}")
        print(f"BASIC Arithmetic: {'PASS ✓' if basic_arith_pass else 'FAIL ✗'}")
        print(f"BASIC FOR Loop:   {'PASS ✓' if basic_loop_pass else 'FAIL ✗'}")
        print(f"BASIC Variables:  {'PASS ✓' if basic_vars_pass else 'FAIL ✗'}")

        all_pass = zp_pass and basic_arith_pass and basic_loop_pass and basic_vars_pass
        print("="*60)
        if all_pass:
            print("🎉 ALL TESTS PASSED! Feature 001 User Story 2 Complete!")
        else:
            print("⚠ Some tests failed - review output above")
        print("="*60)
    else:
        print("\n→ System appears to be in Monitor mode")
        print("  Type 'G' to start BASIC, then re-run this script")

    ser.close()

if __name__ == '__main__':
    main()
