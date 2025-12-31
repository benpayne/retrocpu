"""
Pytest configuration and shared fixtures for RetroCPU firmware tests.
"""

import pytest
import serial
import time
import os
import subprocess


# Serial port configuration
DEFAULT_PORT = os.environ.get('RETROCPU_PORT', '/dev/ttyACM0')
DEFAULT_BAUD = int(os.environ.get('RETROCPU_BAUD', '9600'))
CHAR_DELAY = 0.15  # 150ms between characters (firmware needs time to process)

# FPGA bitstream path (relative to test directory)
BITSTREAM_PATH = os.environ.get('RETROCPU_BITSTREAM',
                                '../../build/soc_top.bit')


def pytest_addoption(parser):
    """Add command-line options for pytest."""
    parser.addoption(
        "--port",
        action="store",
        default=DEFAULT_PORT,
        help=f"Serial port for RetroCPU (default: {DEFAULT_PORT})"
    )
    parser.addoption(
        "--baud",
        action="store",
        default=DEFAULT_BAUD,
        type=int,
        help=f"Baud rate (default: {DEFAULT_BAUD})"
    )
    parser.addoption(
        "--skip-hardware",
        action="store_true",
        default=False,
        help="Skip tests that require hardware"
    )


@pytest.fixture(scope="session")
def serial_config(request):
    """Serial port configuration."""
    return {
        'port': request.config.getoption("--port"),
        'baudrate': request.config.getoption("--baud"),
        'timeout': 1
    }


@pytest.fixture(scope="session")
def skip_hardware(request):
    """Check if hardware tests should be skipped."""
    return request.config.getoption("--skip-hardware")


def reset_fpga(bitstream_path=None):
    """
    Reset FPGA by reprogramming it.

    Args:
        bitstream_path: Path to bitstream file (default from BITSTREAM_PATH)

    Returns:
        True if successful, False otherwise
    """
    if bitstream_path is None:
        bitstream_path = BITSTREAM_PATH

    # Make path absolute
    if not os.path.isabs(bitstream_path):
        test_dir = os.path.dirname(os.path.abspath(__file__))
        bitstream_path = os.path.join(test_dir, bitstream_path)

    if not os.path.exists(bitstream_path):
        print(f"Warning: Bitstream not found at {bitstream_path}")
        return False

    try:
        # Reprogram FPGA
        result = subprocess.run(
            ['openFPGALoader', '-b', 'colorlight-i5', bitstream_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            time.sleep(2)  # Wait for FPGA to stabilize
            return True
        else:
            print(f"FPGA programming failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("FPGA programming timed out")
        return False
    except FileNotFoundError:
        print("openFPGALoader not found - cannot reset FPGA")
        return False


@pytest.fixture(scope="function")
def fpga_reset(skip_hardware):
    """
    Fixture that provides a function to reset the FPGA.

    Usage in tests:
        def test_something(fpga_reset):
            fpga_reset()  # Reset FPGA to clean state
            # ... test code ...
    """
    if skip_hardware:
        pytest.skip("Hardware test skipped (--skip-hardware)")

    def _reset():
        success = reset_fpga()
        if not success:
            pytest.skip("Could not reset FPGA")
        return success

    return _reset


@pytest.fixture(scope="function")
def serial_port(serial_config, skip_hardware):
    """
    Open serial connection to RetroCPU.

    This fixture provides a serial connection that is automatically
    closed after each test. It waits for the monitor prompt before
    returning.
    """
    if skip_hardware:
        pytest.skip("Hardware test skipped (--skip-hardware)")

    try:
        ser = serial.Serial(**serial_config)
        time.sleep(1.0)  # Let connection and firmware stabilize

        # Clear any pending input (boot messages, etc.)
        time.sleep(0.5)
        if ser.in_waiting:
            junk = ser.read(ser.in_waiting)

        # Send newline to get a fresh prompt
        ser.write(b'\r\n')
        time.sleep(0.5)

        # Consume any output until we get a prompt
        timeout = time.time() + 3
        buffer = ""
        while time.time() < timeout:
            if ser.in_waiting:
                buffer += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                if '>' in buffer:
                    break
            time.sleep(0.1)

        yield ser

        # Cleanup
        ser.close()

    except serial.SerialException as e:
        pytest.skip(f"Could not open serial port: {e}")


class MonitorHelper:
    """Helper class for interacting with the RetroCPU monitor."""

    def __init__(self, serial_port):
        self.ser = serial_port

    def send_slow(self, text, delay=CHAR_DELAY):
        """Send text slowly, character by character."""
        for char in text:
            self.ser.write(char.encode('utf-8'))
            time.sleep(delay)

    def read_until(self, marker, timeout=2):
        """Read until marker is found or timeout."""
        start_time = time.time()
        buffer = ""
        while time.time() - start_time < timeout:
            if self.ser.in_waiting:
                data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                buffer += data
                if marker in buffer:
                    return buffer
            time.sleep(0.05)
        return buffer

    def wait_for_prompt(self, timeout=3):
        """Wait for the monitor prompt '> '."""
        buffer = self.read_until('>', timeout)
        return '>' in buffer

    def send_command(self, command, wait_prompt=True):
        """Send a command and optionally wait for prompt."""
        self.send_slow(command)
        time.sleep(0.1)
        if wait_prompt:
            self.wait_for_prompt()

    def examine(self, address):
        """
        Examine memory at address.

        Args:
            address: 4-digit hex address string (e.g., '0200')

        Returns:
            Byte value at address as hex string, or None on error
        """
        # Send inline command: "E 0200\r"
        cmd = f'E {address}\r'
        for char in cmd:
            self.ser.write(char.encode('utf-8'))
            time.sleep(0.1)  # 100ms delay between characters

        time.sleep(0.3)  # Wait for processing
        result = self.read_until('>', timeout=3)

        # Parse result: expect "ADDRESS: VALUE"
        # Look for pattern like "0200: AA"
        for line in result.split('\n'):
            line = line.strip()
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    # Get the value part (after colon)
                    value_part = parts[1].strip().split()[0]
                    if len(value_part) == 2:  # Should be 2-digit hex
                        return value_part.upper()

        return None

    def deposit(self, address, value):
        """
        Deposit value to memory address.

        Args:
            address: 4-digit hex address string (e.g., '0200')
            value: 2-digit hex value string (e.g., 'AA')

        Returns:
            True if successful, False otherwise
        """
        # Send inline command: "D 0200 AA\r"
        cmd = f'D {address} {value}\r'
        for char in cmd:
            self.ser.write(char.encode('utf-8'))
            time.sleep(0.1)  # 100ms delay between characters

        time.sleep(0.5)  # Wait for write to complete
        result = self.read_until('>', timeout=3)

        # Check if we see the address and value in the response
        return address.upper() in result.upper() and value.upper() in result.upper()

    def go_basic(self):
        """Start BASIC interpreter."""
        self.send_slow('G')
        time.sleep(1.0)  # BASIC takes time to initialize
        # Read welcome message
        return self.read_until('OK', timeout=5)


@pytest.fixture
def monitor(serial_port):
    """Provide MonitorHelper instance with clean state."""
    # Ensure we're at monitor prompt
    serial_port.write(b'\r\n')
    time.sleep(0.5)

    # Clear any pending data
    if serial_port.in_waiting:
        serial_port.read(serial_port.in_waiting)

    return MonitorHelper(serial_port)


class BasicHelper:
    """Helper class for interacting with BASIC."""

    def __init__(self, serial_port):
        self.ser = serial_port

    def send_slow(self, text, delay=CHAR_DELAY):
        """Send text slowly, character by character."""
        for char in text:
            self.ser.write(char.encode('utf-8'))
            time.sleep(delay)

    def send_line(self, line):
        """Send a line of BASIC code."""
        self.send_slow(line)
        self.ser.write(b'\r')
        time.sleep(0.2)

    def read_until(self, marker, timeout=2):
        """Read until marker is found or timeout."""
        start_time = time.time()
        buffer = ""
        while time.time() - start_time < timeout:
            if self.ser.in_waiting:
                data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                buffer += data
                if marker in buffer:
                    return buffer
            time.sleep(0.05)
        return buffer

    def wait_for_ok(self, timeout=2):
        """Wait for BASIC 'OK' prompt."""
        buffer = self.read_until('OK', timeout)
        return 'OK' in buffer

    def execute(self, command, timeout=2):
        """
        Execute immediate BASIC command and return output.

        Args:
            command: BASIC command (e.g., 'PRINT 2+2')
            timeout: Max time to wait for response

        Returns:
            Output from BASIC (before next OK prompt)
        """
        self.send_line(command)
        output = self.read_until('OK', timeout)
        return output

    def enter_program(self, lines):
        """
        Enter a BASIC program (list of numbered lines).

        Args:
            lines: List of program lines (e.g., ['10 PRINT "HELLO"', '20 END'])
        """
        for line in lines:
            self.send_line(line)
            time.sleep(0.1)

    def run_program(self, timeout=5):
        """
        Run the program and return output.

        Returns:
            Program output
        """
        self.send_line('RUN')
        output = self.read_until('OK', timeout)
        return output

    def new(self):
        """Clear program memory."""
        self.send_line('NEW')
        self.wait_for_ok()

    def list_program(self):
        """List the current program."""
        self.send_line('LIST')
        output = self.read_until('OK', timeout=3)
        return output


@pytest.fixture
def basic(serial_port):
    """Provide BasicHelper instance (starts BASIC)."""
    helper = BasicHelper(serial_port)

    # Start BASIC from monitor
    serial_port.write(b'G')
    time.sleep(0.5)

    # Wait for BASIC to be ready
    helper.wait_for_ok(timeout=3)

    # Clear any program
    helper.new()

    return helper
