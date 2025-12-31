#!/usr/bin/env python3
"""
Test suite for BASIC POKE and PEEK commands.

Tests the OSI BASIC interpreter's memory access commands:
- POKE (write to memory)
- PEEK (read from memory)
- Interaction with RAM
"""

import pytest
import time


class TestBasicMemoryAccess:
    """Test BASIC POKE and PEEK commands."""

    def test_basic_starts(self, basic):
        """Test that BASIC starts and is ready for commands."""
        # The 'basic' fixture already started BASIC and got to OK prompt
        # Just verify we can send a simple command
        result = basic.execute('PRINT 1')
        assert '1' in result, "BASIC should execute PRINT 1"

    def test_poke_single_byte(self, basic):
        """Test POKE writes a single byte to memory."""
        # POKE a value to RAM at $0400
        basic.execute('POKE 1024, 170')  # 1024 = $0400, 170 = $AA
        time.sleep(0.5)

        # Verify with PEEK
        result = basic.execute('PRINT PEEK(1024)')
        assert '170' in result, f"PEEK should return 170, got: {result}"

    def test_poke_different_values(self, basic):
        """Test POKE with various byte values."""
        test_values = [
            (1024, 0),      # $0400 = $00
            (1025, 85),     # $0401 = $55
            (1026, 170),    # $0402 = $AA
            (1027, 255),    # $0403 = $FF
        ]

        for addr, val in test_values:
            basic.execute(f'POKE {addr}, {val}')
            time.sleep(0.3)

            result = basic.execute(f'PRINT PEEK({addr})')
            assert str(val) in result, f"PEEK({addr}) should return {val}, got: {result}"

    def test_poke_sequential_addresses(self, basic):
        """Test POKE to sequential memory locations."""
        # Write pattern to $0500-$0507
        base = 1280  # $0500

        for i in range(8):
            val = i * 10
            basic.execute(f'POKE {base + i}, {val}')
            time.sleep(0.2)

        # Verify all values
        for i in range(8):
            expected = i * 10
            result = basic.execute(f'PRINT PEEK({base + i})')
            assert str(expected) in result, \
                f"PEEK({base + i}) should return {expected}, got: {result}"

    def test_poke_program(self, basic):
        """Test POKE in a BASIC program."""
        # Create a program that uses POKE and PEEK
        basic.enter_program([
            '10 A=1536',      # $0600
            '20 POKE A,42',
            '30 B=PEEK(A)',
            '40 PRINT B',
        ])

        result = basic.run_program()
        assert '42' in result, f"Program should output 42, got: {result}"

    def test_poke_loop(self, basic):
        """Test POKE in a FOR loop."""
        # Fill memory with a pattern using a loop
        basic.enter_program([
            '10 FOR I=0 TO 7',
            '20 POKE 1600+I,I*16',  # $0640+I
            '30 NEXT I',
            '40 PRINT "DONE"',
        ])

        result = basic.run_program()
        assert 'DONE' in result, "Program should complete"

        # Verify the pattern was written
        for i in range(8):
            expected = i * 16
            result = basic.execute(f'PRINT PEEK({1600 + i})')
            assert str(expected) in result, \
                f"PEEK({1600 + i}) should return {expected}, got: {result}"

    def test_peek_rom(self, basic):
        """Test PEEK reading from ROM."""
        # BASIC ROM starts at $8000 (32768)
        result = basic.execute('PRINT PEEK(32768)')
        # Should read something from BASIC ROM
        assert result.strip() != '', "Should read a value from ROM"

        # Monitor ROM at $E000 (57344)
        result = basic.execute('PRINT PEEK(57344)')
        assert result.strip() != '', "Should read a value from Monitor ROM"

    def test_peek_zero_page(self, basic):
        """Test PEEK reading from zero page."""
        # BASIC uses some zero page locations
        # Just verify we can read them without crashing
        result = basic.execute('PRINT PEEK(0)')
        assert result.strip() != '', "Should be able to PEEK zero page"

    def test_poke_peek_roundtrip(self, basic):
        """Test POKE then PEEK returns same value."""
        test_addr = 2048  # $0800

        for val in [0, 1, 127, 128, 254, 255]:
            basic.execute(f'POKE {test_addr}, {val}')
            time.sleep(0.3)

            result = basic.execute(f'PRINT PEEK({test_addr})')
            assert str(val) in result, \
                f"POKE {val} then PEEK should return {val}, got: {result}"

    def test_poke_array_initialization(self, basic):
        """Test using POKE to initialize data for array operations."""
        # Use POKE to set up a lookup table
        basic.enter_program([
            '10 REM Initialize lookup table',
            '20 FOR I=0 TO 9',
            '30 POKE 2560+I,I*I',  # $0A00+I = I squared
            '40 NEXT I',
            '50 PRINT "TABLE READY"',
            '60 PRINT PEEK(2564)',  # $0A04 = 4^2 = 16
        ])

        result = basic.run_program()
        assert 'TABLE READY' in result
        assert '16' in result, "PEEK(2564) should return 16"

    def test_poke_string_buffer(self, basic):
        """Test POKE to create ASCII string in memory."""
        # POKE ASCII codes for "HI"
        basic.enter_program([
            '10 POKE 3072,72',   # $0C00 = 'H'
            '20 POKE 3073,73',   # $0C01 = 'I'
            '30 POKE 3074,0',    # $0C02 = null terminator
            '40 PRINT PEEK(3072)',
            '50 PRINT PEEK(3073)',
        ])

        result = basic.run_program()
        assert '72' in result  # 'H'
        assert '73' in result  # 'I'


@pytest.mark.slow
class TestBasicMemoryStress:
    """Stress tests for BASIC memory operations."""

    def test_large_poke_sequence(self, basic):
        """Test POKE to a large block of memory."""
        # Fill 256 bytes with a pattern
        basic.enter_program([
            '10 FOR I=0 TO 255',
            '20 POKE 4096+I,I',  # $1000+I
            '30 NEXT I',
            '40 PRINT "FILLED 256 BYTES"',
        ])

        result = basic.run_program(timeout=15)
        assert 'FILLED 256 BYTES' in result

        # Spot check a few values
        test_indices = [0, 1, 127, 128, 254, 255]
        for i in test_indices:
            result = basic.execute(f'PRINT PEEK({4096 + i})')
            assert str(i) in result, \
                f"PEEK({4096 + i}) should return {i}, got: {result}"

    def test_poke_peek_alternating_pattern(self, basic):
        """Test alternating $AA/$55 pattern."""
        basic.enter_program([
            '10 FOR I=0 TO 15',
            '20 IF I/2=INT(I/2) THEN V=170 ELSE V=85',
            '30 POKE 5120+I,V',  # $1400+I
            '40 NEXT I',
            '50 PRINT "PATTERN WRITTEN"',
        ])

        result = basic.run_program(timeout=10)
        assert 'PATTERN WRITTEN' in result

        # Verify pattern
        for i in range(16):
            expected = 170 if i % 2 == 0 else 85
            result = basic.execute(f'PRINT PEEK({5120 + i})')
            assert str(expected) in result


class TestBasicMonitorInteraction:
    """Test BASIC POKE/PEEK interaction with monitor memory."""

    def test_poke_visible_to_monitor(self, fpga_reset, serial_port, monitor):
        """Test that BASIC POKE is visible to monitor E command."""
        # Start BASIC
        serial_port.write(b'G')
        time.sleep(2)

        # Wait for BASIC prompts and answer them
        serial_port.write(b'\r')  # MEMORY SIZE
        time.sleep(1)
        serial_port.write(b'\r')  # TERMINAL WIDTH
        time.sleep(1)

        # Clear buffer
        if serial_port.in_waiting:
            serial_port.read(serial_port.in_waiting)

        # Send POKE command in BASIC
        cmd = 'POKE 6144,123\r'  # $1800 = 123
        for char in cmd:
            serial_port.write(char.encode())
            time.sleep(0.15)
        time.sleep(1)

        # Reset to get back to monitor
        fpga_reset()
        time.sleep(3)

        # Send newline to get monitor prompt
        serial_port.write(b'\r\n')
        time.sleep(0.5)
        if serial_port.in_waiting:
            serial_port.read(serial_port.in_waiting)

        # Check with monitor E command
        value = monitor.examine('1800')
        assert value == '7B', f"Monitor should see $7B (123), got ${value}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
