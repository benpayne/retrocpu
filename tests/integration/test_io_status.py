#!/usr/bin/env python3
"""
Integration tests for I/O Status Display (Feature 004 - User Story 4, Phase 6)

Tests the S (Status) command that displays:
- Current I/O configuration (input/output modes)
- Peripheral status (UART, PS/2, GPU/Display)

Test Approach:
- T052: Test S command output format and field presence
- T053: Test status accuracy across different I/O mode configurations

This test file can be run in two modes:
1. As a cocotb simulation test (for RTL verification)
2. As a hardware test script (for FPGA verification)

For now, implementing as cocotb test following existing test patterns.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ClockCycles
from cocotb.utils import get_sim_time


class MonitorHelper:
    """Helper class to interact with the monitor firmware"""

    def __init__(self, dut):
        self.dut = dut
        self.cpu_clock = dut.cpu_clk

    async def wait_cycles(self, n):
        """Wait for n CPU clock cycles"""
        for _ in range(n):
            await RisingEdge(self.cpu_clock)

    async def send_uart_char(self, char):
        """Send a character via UART RX to CPU"""
        if isinstance(char, str):
            char = ord(char)

        # Simulate UART RX data ready
        self.dut.uart_rx_data.value = char
        self.dut.uart_rx_ready.value = 1
        await self.wait_cycles(10)  # Give CPU time to read
        self.dut.uart_rx_ready.value = 0
        await self.wait_cycles(5)

    async def read_uart_output(self, timeout_cycles=1000):
        """Read one character from UART TX output"""
        for _ in range(timeout_cycles):
            if self.dut.uart_tx_valid.value == 1:
                char = int(self.dut.uart_tx_data.value)
                await self.wait_cycles(5)  # Allow TX to complete
                return chr(char) if 32 <= char < 127 else char
            await self.wait_cycles(1)
        raise TimeoutError(f"No UART output within {timeout_cycles} cycles")

    async def send_command(self, command):
        """Send a complete command string followed by CR"""
        for char in command:
            await self.send_uart_char(char)
        await self.send_uart_char('\r')  # CR to execute

    async def wait_for_prompt(self, timeout_cycles=5000):
        """Wait for the monitor prompt (> )"""
        prompt = ""
        for _ in range(timeout_cycles):
            try:
                char = await self.read_uart_output(timeout_cycles=10)
                prompt += char if isinstance(char, str) else f"\\x{char:02x}"
                if prompt.endswith("> "):
                    return True
            except TimeoutError:
                await self.wait_cycles(10)
        raise TimeoutError(f"Prompt not seen within {timeout_cycles} cycles. Got: {prompt}")

    async def read_until_prompt(self, timeout_cycles=5000):
        """Read all output until prompt is seen, return as string"""
        output = ""
        for _ in range(timeout_cycles):
            try:
                char = await self.read_uart_output(timeout_cycles=10)
                output += char if isinstance(char, str) else f"\\x{char:02x}"
                if output.endswith("> "):
                    return output
            except TimeoutError:
                await self.wait_cycles(10)
        raise TimeoutError(f"Prompt not seen. Output so far: {output}")


@cocotb.test()
async def test_status_command_output_format(dut):
    """
    T052: Test S command output format

    Verifies that the S command displays:
    - I/O Status section header
    - Input source field
    - Output destination field
    - Peripherals section header
    - UART status line
    - PS/2 status line
    - Display status line (or graceful message if unavailable)
    """

    # Setup
    clock = Clock(dut.cpu_clk, 40, units="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    helper = MonitorHelper(dut)

    # Reset
    dut.reset.value = 1
    await helper.wait_cycles(10)
    dut.reset.value = 0
    await helper.wait_cycles(100)

    # Wait for welcome message and first prompt
    await helper.wait_for_prompt(timeout_cycles=10000)

    dut._log.info("Sending S (status) command...")

    # Send S command
    await helper.send_command("S")

    # Read status output until prompt
    status_output = await helper.read_until_prompt(timeout_cycles=10000)

    dut._log.info(f"Status output:\n{status_output}")

    # Verify output format contains expected sections
    checks = [
        ("I/O Status:" in status_output, "Contains 'I/O Status:' header"),
        ("Input:" in status_output, "Contains 'Input:' field"),
        ("Output:" in status_output, "Contains 'Output:' field"),
        ("Peripherals:" in status_output, "Contains 'Peripherals:' header"),
        ("UART:" in status_output, "Contains 'UART:' status line"),
        ("PS/2:" in status_output or "PS2:" in status_output, "Contains 'PS/2:' status line"),
        ("Display:" in status_output, "Contains 'Display:' status line"),
    ]

    all_passed = True
    for passed, desc in checks:
        status = "PASS" if passed else "FAIL"
        dut._log.info(f"  [{status}] {desc}")
        if not passed:
            all_passed = False

    assert all_passed, "Status output format check failed"

    # Verify default I/O mode is UART (mode 0 0)
    # After reset, should be "Input: UART" and "Output: UART"
    assert "Input:  UART" in status_output or "Input: UART" in status_output, \
        "Default input mode should be UART"
    assert "Output: UART" in status_output, \
        "Default output mode should be UART"

    dut._log.info("Status command output format test PASSED")


@cocotb.test()
async def test_status_reflects_io_configuration(dut):
    """
    T053: Test status accuracy across different I/O modes

    Verifies that the S command accurately reflects the current I/O configuration:
    1. Configure I/O mode with I command (e.g., I 1 1)
    2. Issue S command
    3. Verify status shows correct configuration
    4. Change mode (e.g., I 0 2) and verify S updates
    """

    # Setup
    clock = Clock(dut.cpu_clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    helper = MonitorHelper(dut)

    # Reset
    dut.reset.value = 1
    await helper.wait_cycles(10)
    dut.reset.value = 0
    await helper.wait_cycles(100)

    await helper.wait_for_prompt(timeout_cycles=10000)

    # Test Case 1: Mode 0 0 (UART only) - default
    dut._log.info("Test Case 1: Verifying default mode (I 0 0)")
    await helper.send_command("S")
    status = await helper.read_until_prompt()

    assert "Input:  UART" in status or "Input: UART" in status, \
        "Default input should be UART"
    assert "Output: UART" in status, \
        "Default output should be UART"
    dut._log.info("  Default mode verified")

    # Test Case 2: Mode 1 1 (PS/2 input, Display output)
    dut._log.info("Test Case 2: Testing mode I 1 1 (PS/2 + Display)")
    await helper.send_command("I 1 1")
    await helper.wait_for_prompt()

    await helper.send_command("S")
    status = await helper.read_until_prompt()

    assert "Input:  PS/2" in status or "Input: PS2" in status or "Input:  PS2" in status, \
        "Input should show PS/2 after I 1 1"
    assert "Output: Display" in status, \
        "Output should show Display after I 1 1"
    dut._log.info("  Mode 1 1 verified")

    # Test Case 3: Mode 2 2 (Both inputs, both outputs)
    dut._log.info("Test Case 3: Testing mode I 2 2 (Both + Both)")
    await helper.send_command("I 2 2")
    await helper.wait_for_prompt()

    await helper.send_command("S")
    status = await helper.read_until_prompt()

    assert "UART + PS/2" in status or "UART + PS2" in status or "Both" in status, \
        "Input should show UART + PS/2 or Both after I 2 2"
    assert "UART + Display" in status or "Both" in status, \
        "Output should show UART + Display or Both after I 2 2"
    dut._log.info("  Mode 2 2 verified")

    # Test Case 4: Mode 0 2 (UART input, dual output)
    dut._log.info("Test Case 4: Testing mode I 0 2 (UART input, dual output)")
    await helper.send_command("I 0 2")
    await helper.wait_for_prompt()

    await helper.send_command("S")
    status = await helper.read_until_prompt()

    assert "Input:  UART" in status or "Input: UART" in status, \
        "Input should show UART after I 0 2"
    assert "UART + Display" in status or "Both" in status, \
        "Output should show UART + Display or Both after I 0 2"
    dut._log.info("  Mode 0 2 verified")

    dut._log.info("All I/O configuration status tests PASSED")


@cocotb.test()
async def test_uart_status_display(dut):
    """
    Test UART status line displays correct information

    Should show:
    - Baud rate (9600)
    - TX ready status (bit 0 of UART_STATUS)
    - RX ready status (bit 1 of UART_STATUS)
    """

    # Setup
    clock = Clock(dut.cpu_clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    helper = MonitorHelper(dut)

    # Reset
    dut.reset.value = 1
    await helper.wait_cycles(10)
    dut.reset.value = 0
    await helper.wait_cycles(100)

    await helper.wait_for_prompt(timeout_cycles=10000)

    # Send status command
    await helper.send_command("S")
    status = await helper.read_until_prompt()

    dut._log.info(f"Checking UART status line in:\n{status}")

    # Check for UART status line
    assert "UART:" in status, "Should contain UART status line"

    # Check for baud rate (9600 is typical)
    assert "9600" in status, "Should show baud rate (9600)"

    # TX ready and RX ready status may vary, but should show some status
    # At minimum, should mention TX and/or ready status
    # Not asserting specific values as they depend on hardware state

    dut._log.info("UART status display test PASSED")


@cocotb.test()
async def test_ps2_status_display(dut):
    """
    Test PS/2 status line displays correctly

    Should show:
    - Device detection status
    - Data ready status (bit 0 of PS2_STATUS)
    """

    # Setup
    clock = Clock(dut.cpu_clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    helper = MonitorHelper(dut)

    # Reset
    dut.reset.value = 1
    await helper.wait_cycles(10)
    dut.reset.value = 0
    await helper.wait_cycles(100)

    await helper.wait_for_prompt(timeout_cycles=10000)

    # Send status command
    await helper.send_command("S")
    status = await helper.read_until_prompt()

    dut._log.info(f"Checking PS/2 status line in:\n{status}")

    # Check for PS/2 status line
    assert "PS/2:" in status or "PS2:" in status, "Should contain PS/2 status line"

    # Should show either "Detected" or "No data" or similar status
    # Not asserting specific values as they depend on hardware state

    dut._log.info("PS/2 status display test PASSED")


@cocotb.test()
async def test_gpu_status_display_graceful(dut):
    """
    Test GPU/Display status line

    Should show:
    - Display mode (40 or 80 column) if registers readable
    - Cursor position if registers readable
    - Graceful message if registers not implemented ("Status unavailable")
    """

    # Setup
    clock = Clock(dut.cpu_clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    helper = MonitorHelper(dut)

    # Reset
    dut.reset.value = 1
    await helper.wait_cycles(10)
    dut.reset.value = 0
    await helper.wait_cycles(100)

    await helper.wait_for_prompt(timeout_cycles=10000)

    # Send status command
    await helper.send_command("S")
    status = await helper.read_until_prompt()

    dut._log.info(f"Checking Display/GPU status line in:\n{status}")

    # Check for Display status line
    assert "Display:" in status, "Should contain Display status line"

    # Should show either:
    # - Column mode info (40/80 column)
    # - Cursor position
    # - "Status unavailable" if registers not readable
    # Accept any of these as valid

    dut._log.info("GPU/Display status display test PASSED")
