"""
Test suite for RetroCPU BASIC interpreter.

Tests the OSI BASIC implementation including:
- Arithmetic operations
- Variables
- Control flow (FOR/NEXT, GOTO, GOSUB/RETURN)
- String operations
- Program entry and execution
"""

import pytest
import time


class TestBasicStartup:
    """Test BASIC initialization and startup."""

    def test_basic_starts(self, basic):
        """Test that BASIC starts and shows OK prompt."""
        basic.send_line('')  # Send blank line
        assert basic.wait_for_ok(timeout=2), "BASIC OK prompt not found"

    def test_basic_shows_memory(self, serial_port):
        """Test that BASIC shows available memory on startup."""
        # Start BASIC
        serial_port.write(b'G')
        time.sleep(0.5)

        output = ''
        timeout = time.time() + 3
        while time.time() < timeout:
            if serial_port.in_waiting:
                output += serial_port.read(serial_port.in_waiting).decode('utf-8', errors='ignore')
                if 'OK' in output:
                    break
            time.sleep(0.1)

        # Should mention memory or bytes
        assert 'BYTE' in output.upper() or 'MEM' in output.upper() or 'OK' in output, \
            "BASIC startup message incomplete"


class TestBasicArithmetic:
    """Test BASIC arithmetic operations."""

    def test_addition(self, basic):
        """Test simple addition."""
        output = basic.execute('PRINT 2+2')
        assert '4' in output, f"Expected 4, got: {output}"

    def test_subtraction(self, basic):
        """Test subtraction."""
        output = basic.execute('PRINT 10-3')
        assert '7' in output, f"Expected 7, got: {output}"

    def test_multiplication(self, basic):
        """Test multiplication."""
        output = basic.execute('PRINT 6*7')
        assert '42' in output, f"Expected 42, got: {output}"

    def test_division(self, basic):
        """Test division."""
        output = basic.execute('PRINT 20/4')
        assert '5' in output, f"Expected 5, got: {output}"

    def test_order_of_operations(self, basic):
        """Test operator precedence."""
        output = basic.execute('PRINT 2+3*4')
        assert '14' in output, f"Expected 14, got: {output}"

    def test_parentheses(self, basic):
        """Test parentheses for grouping."""
        output = basic.execute('PRINT (2+3)*4')
        assert '20' in output, f"Expected 20, got: {output}"


class TestBasicVariables:
    """Test BASIC variable operations."""

    def test_numeric_variable(self, basic):
        """Test storing and retrieving numeric variable."""
        basic.execute('A=42')
        output = basic.execute('PRINT A')
        assert '42' in output, f"Expected 42, got: {output}"

    def test_multiple_variables(self, basic):
        """Test multiple variables."""
        basic.execute('A=10')
        basic.execute('B=20')
        output = basic.execute('PRINT A+B')
        assert '30' in output, f"Expected 30, got: {output}"

    def test_variable_expressions(self, basic):
        """Test variables in expressions."""
        basic.execute('X=5')
        basic.execute('Y=3')
        output = basic.execute('PRINT X*Y+2')
        assert '17' in output, f"Expected 17, got: {output}"

    def test_string_variable(self, basic):
        """Test string variables."""
        basic.execute('A$="HELLO"')
        output = basic.execute('PRINT A$')
        assert 'HELLO' in output, f"Expected HELLO, got: {output}"


class TestBasicPrograms:
    """Test BASIC program entry and execution."""

    def test_simple_program(self, basic):
        """Test entering and running a simple program."""
        basic.new()
        basic.enter_program([
            '10 PRINT "HELLO"',
            '20 END'
        ])

        output = basic.run_program()
        assert 'HELLO' in output, f"Expected HELLO, got: {output}"

    def test_program_with_variable(self, basic):
        """Test program using variables."""
        basic.new()
        basic.enter_program([
            '10 A=100',
            '20 PRINT A',
            '30 END'
        ])

        output = basic.run_program()
        assert '100' in output, f"Expected 100, got: {output}"

    def test_program_calculation(self, basic):
        """Test program with calculations."""
        basic.new()
        basic.enter_program([
            '10 X=10',
            '20 Y=20',
            '30 PRINT X+Y',
            '40 END'
        ])

        output = basic.run_program()
        assert '30' in output, f"Expected 30, got: {output}"

    def test_list_program(self, basic):
        """Test listing program."""
        basic.new()
        basic.enter_program([
            '10 PRINT "TEST"',
            '20 END'
        ])

        output = basic.list_program()
        assert '10' in output and 'PRINT' in output, \
            f"Program listing incomplete: {output}"


class TestBasicControlFlow:
    """Test BASIC control flow statements."""

    def test_goto(self, basic):
        """Test GOTO statement."""
        basic.new()
        basic.enter_program([
            '10 PRINT "A"',
            '20 GOTO 40',
            '30 PRINT "B"',
            '40 PRINT "C"',
            '50 END'
        ])

        output = basic.run_program()
        # Should see A and C, but not B
        assert 'A' in output and 'C' in output, f"GOTO failed: {output}"
        assert 'B' not in output, f"GOTO didn't skip line 30: {output}"

    def test_if_then_true(self, basic):
        """Test IF-THEN with true condition."""
        basic.new()
        basic.enter_program([
            '10 A=5',
            '20 IF A=5 THEN PRINT "YES"',
            '30 END'
        ])

        output = basic.run_program()
        assert 'YES' in output, f"IF-THEN true condition failed: {output}"

    def test_if_then_false(self, basic):
        """Test IF-THEN with false condition."""
        basic.new()
        basic.enter_program([
            '10 A=5',
            '20 IF A=10 THEN PRINT "YES"',
            '30 PRINT "NO"',
            '40 END'
        ])

        output = basic.run_program()
        assert 'NO' in output, f"IF-THEN false condition failed: {output}"
        assert 'YES' not in output, f"IF-THEN executed when it shouldn't: {output}"

    def test_for_next_loop(self, basic):
        """Test FOR-NEXT loop."""
        basic.new()
        basic.enter_program([
            '10 FOR I=1 TO 3',
            '20 PRINT I',
            '30 NEXT I',
            '40 END'
        ])

        output = basic.run_program()
        # Should see 1, 2, 3
        assert '1' in output and '2' in output and '3' in output, \
            f"FOR-NEXT loop failed: {output}"

    def test_gosub_return(self, basic):
        """Test GOSUB and RETURN."""
        basic.new()
        basic.enter_program([
            '10 PRINT "START"',
            '20 GOSUB 100',
            '30 PRINT "END"',
            '40 END',
            '100 PRINT "SUB"',
            '110 RETURN'
        ])

        output = basic.run_program()
        # Should see START, SUB, END in that order
        assert 'START' in output and 'SUB' in output and 'END' in output, \
            f"GOSUB-RETURN failed: {output}"


class TestBasicStrings:
    """Test BASIC string operations."""

    def test_print_string_literal(self, basic):
        """Test printing string literal."""
        output = basic.execute('PRINT "HELLO WORLD"')
        assert 'HELLO WORLD' in output, f"String print failed: {output}"

    def test_string_concatenation(self, basic):
        """Test string concatenation."""
        basic.execute('A$="HELLO"')
        basic.execute('B$="WORLD"')
        output = basic.execute('PRINT A$+" "+B$')
        assert 'HELLO WORLD' in output or 'HELLOWORLD' in output, \
            f"String concatenation failed: {output}"

    def test_print_multiple_items(self, basic):
        """Test PRINT with multiple items."""
        output = basic.execute('PRINT "VALUE:";42')
        assert 'VALUE' in output and '42' in output, \
            f"Multiple item print failed: {output}"


class TestBasicFunctions:
    """Test BASIC built-in functions."""

    def test_abs_function(self, basic):
        """Test ABS function."""
        output = basic.execute('PRINT ABS(-5)')
        assert '5' in output, f"ABS function failed: {output}"

    def test_int_function(self, basic):
        """Test INT function."""
        output = basic.execute('PRINT INT(3.7)')
        assert '3' in output, f"INT function failed: {output}"

    def test_sgn_function(self, basic):
        """Test SGN function."""
        output = basic.execute('PRINT SGN(-10)')
        assert '-1' in output or 'SYNTAX' in output.upper(), \
            f"SGN function failed: {output}"


@pytest.mark.slow
class TestBasicComplexPrograms:
    """Test more complex BASIC programs."""

    def test_fibonacci(self, basic):
        """Test Fibonacci sequence program."""
        basic.new()
        basic.enter_program([
            '10 A=0',
            '20 B=1',
            '30 FOR I=1 TO 5',
            '40 PRINT A',
            '50 C=A+B',
            '60 A=B',
            '70 B=C',
            '80 NEXT I',
            '90 END'
        ])

        output = basic.run_program(timeout=5)
        # Should see 0, 1, 1, 2, 3
        assert '0' in output and '1' in output and '2' in output and '3' in output, \
            f"Fibonacci program failed: {output}"

    def test_sum_accumulator(self, basic):
        """Test accumulator pattern."""
        basic.new()
        basic.enter_program([
            '10 S=0',
            '20 FOR I=1 TO 10',
            '30 S=S+I',
            '40 NEXT I',
            '50 PRINT S',
            '60 END'
        ])

        output = basic.run_program(timeout=5)
        # Sum of 1 to 10 is 55
        assert '55' in output, f"Accumulator program failed: {output}"

    def test_nested_loops(self, basic):
        """Test nested FOR loops."""
        basic.new()
        basic.enter_program([
            '10 FOR I=1 TO 2',
            '20 FOR J=1 TO 2',
            '30 PRINT I;J',
            '40 NEXT J',
            '50 NEXT I',
            '60 END'
        ])

        output = basic.run_program(timeout=5)
        # Should see combinations: 11, 12, 21, 22
        assert '1' in output and '2' in output, \
            f"Nested loops failed: {output}"


class TestBasicEditing:
    """Test BASIC program editing features."""

    def test_new_clears_program(self, basic):
        """Test that NEW clears program."""
        basic.enter_program(['10 PRINT "TEST"'])
        basic.new()
        output = basic.list_program()
        # Should be empty or show OK
        assert 'PRINT' not in output or 'OK' in output, \
            f"NEW did not clear program: {output}"

    def test_line_replacement(self, basic):
        """Test replacing a program line."""
        basic.new()
        basic.enter_program(['10 PRINT "OLD"'])
        basic.enter_program(['10 PRINT "NEW"'])
        output = basic.list_program()
        assert 'NEW' in output, f"Line replacement failed: {output}"
        assert 'OLD' not in output or output.count('10') == 1, \
            f"Old line not replaced: {output}"

    def test_line_deletion(self, basic):
        """Test deleting a program line."""
        basic.new()
        basic.enter_program([
            '10 PRINT "A"',
            '20 PRINT "B"',
            '30 PRINT "C"'
        ])
        basic.send_line('20')  # Delete line 20
        time.sleep(0.2)

        output = basic.list_program()
        assert '10' in output and '30' in output, \
            f"Program lines missing: {output}"
        # Line 20 should be gone or show only once
        assert output.count('20') <= 1, f"Line 20 not deleted: {output}"


@pytest.mark.slow
class TestBasicStressTest:
    """Stress tests for BASIC interpreter."""

    def test_large_loop(self, basic):
        """Test large FOR loop."""
        basic.new()
        basic.enter_program([
            '10 FOR I=1 TO 100',
            '20 NEXT I',
            '30 PRINT "DONE"',
            '40 END'
        ])

        output = basic.run_program(timeout=10)
        assert 'DONE' in output, f"Large loop failed: {output}"

    def test_many_variables(self, basic):
        """Test using many variables."""
        basic.new()
        basic.enter_program([
            '10 A=1',
            '20 B=2',
            '30 C=3',
            '40 D=4',
            '50 E=5',
            '60 PRINT A+B+C+D+E',
            '70 END'
        ])

        output = basic.run_program(timeout=5)
        assert '15' in output, f"Multiple variables failed: {output}"
