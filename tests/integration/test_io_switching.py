#!/usr/bin/env python3
"""
Integration tests for I/O source configuration (Feature 004 - User Story 2)

Tests all 9 combinations of input/output modes:
- Mode 0: UART only
- Mode 1: PS/2 keyboard / Display only
- Mode 2: Both (dual mode)

Test Approach:
- T025: Test all 9 mode combinations (switching and basic I/O)
- T026: Test dual output mode (verify identical output on UART and Display)
- T027: Test dual input mode (verify input accepted from either source)
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

    async def send_ps2_scancode(self, scancode):
        """Send a PS/2 scancode to CPU"""
        # Simulate PS/2 data ready
        self.dut.ps2_data.value = scancode
        self.dut.ps2_data_ready.value = 1
        await self.wait_cycles(10)  # Give CPU time to read
        self.dut.ps2_data_ready.value = 0
        await self.wait_cycles(5)

    async def read_uart_output(self, timeout_cycles=1000):
        """Read one character from UART TX output"""
        start_time = get_sim_time('ns')
        for _ in range(timeout_cycles):
            if self.dut.uart_tx_valid.value == 1:
                char = int(self.dut.uart_tx_data.value)
                await self.wait_cycles(5)  # Allow TX to complete
                return chr(char) if 32 <= char < 127 else char
            await self.wait_cycles(1)
        raise TimeoutError(f"No UART output within {timeout_cycles} cycles")

    async def read_gpu_output(self, timeout_cycles=1000):
        """Read one character from GPU character output"""
        start_time = get_sim_time('ns')
        for _ in range(timeout_cycles):
            if self.dut.gpu_char_write.value == 1:
                char = int(self.dut.gpu_char_data.value)
                await self.wait_cycles(2)
                return chr(char) if 32 <= char < 127 else char
            await self.wait_cycles(1)
        raise TimeoutError(f"No GPU output within {timeout_cycles} cycles")

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


@cocotb.test()
async def test_io_mode_switching_all_combinations(dut):
    """
    T025: Test all 9 I/O mode combinations

    Tests that the I command correctly switches between:
    - Input modes: 0=UART, 1=PS2, 2=Both
    - Output modes: 0=UART, 1=Display, 2=Both
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

    # Test all 9 combinations
    test_cases = [
        (0, 0, "UART", "UART"),
        (0, 1, "UART", "Display"),
        (0, 2, "UART", "Both"),
        (1, 0, "PS2", "UART"),
        (1, 1, "PS2", "Display"),
        (1, 2, "PS2", "Both"),
        (2, 0, "Both", "UART"),
        (2, 1, "Both", "Display"),
        (2, 2, "Both", "Both"),
    ]

    for in_mode, out_mode, in_name, out_name in test_cases:
        dut._log.info(f"Testing I/O mode: IN={in_name} ({in_mode}), OUT={out_name} ({out_mode})")

        # Send I command
        await helper.send_command(f"I {in_mode} {out_mode}")

        # Read confirmation message
        # Expected: "I/O Config: IN=<mode>, OUT=<mode>\r\n"
        confirmation = ""
        for _ in range(100):
            try:
                char = await helper.read_uart_output(timeout_cycles=50)
                confirmation += char if isinstance(char, str) else ""
                if "\n" in confirmation:
                    break
            except TimeoutError:
                break

        dut._log.info(f"Confirmation: {confirmation}")
        assert f"IN={in_name}" in confirmation, f"Expected 'IN={in_name}' in confirmation"
        assert f"OUT={out_name}" in confirmation, f"Expected 'OUT={out_name}' in confirmation"

        # Wait for next prompt
        await helper.wait_for_prompt()

    dut._log.info("All 9 I/O mode combinations tested successfully")


@cocotb.test()
async def test_dual_output_mode(dut):
    """
    T026: Test dual output mode (mode 2)

    Verifies that when output mode is set to 2 (Both), identical output
    appears on both UART and GPU character display.
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

    # Wait for welcome and prompt
    await helper.wait_for_prompt(timeout_cycles=10000)

    # Set output to dual mode (input=UART for easy control)
    await helper.send_command("I 0 2")
    await helper.wait_for_prompt()

    # Send a simple command that generates output
    await helper.send_command("E 0200")

    # Collect output from both UART and GPU
    uart_output = []
    gpu_output = []

    # Read characters from both outputs (with timeout)
    for _ in range(100):
        try:
            # Try UART
            uart_char = await helper.read_uart_output(timeout_cycles=10)
            uart_output.append(uart_char)
        except TimeoutError:
            pass

        try:
            # Try GPU
            gpu_char = await helper.read_gpu_output(timeout_cycles=10)
            gpu_output.append(gpu_char)
        except TimeoutError:
            pass

        await helper.wait_cycles(5)

        # Stop when we see prompt on UART
        uart_str = "".join(str(c) for c in uart_output)
        if "> " in uart_str:
            break

    uart_str = "".join(str(c) for c in uart_output)
    gpu_str = "".join(str(c) for c in gpu_output)

    dut._log.info(f"UART output: {uart_str}")
    dut._log.info(f"GPU output:  {gpu_str}")

    # Verify both outputs contain the memory address (0200)
    assert "0200" in uart_str, "UART should contain memory address"
    assert "0200" in gpu_str, "GPU should contain memory address"

    # Verify outputs are character-for-character identical (ignoring control chars)
    uart_printable = "".join(c for c in uart_output if isinstance(c, str) and c.isprintable())
    gpu_printable = "".join(c for c in gpu_output if isinstance(c, str) and c.isprintable())

    assert uart_printable == gpu_printable, f"Output mismatch: UART={uart_printable}, GPU={gpu_printable}"

    dut._log.info("Dual output mode verified successfully")


@cocotb.test()
async def test_dual_input_mode(dut):
    """
    T027: Test dual input mode (mode 2)

    Verifies that when input mode is set to 2 (Both), input is accepted
    from either UART or PS/2 keyboard (first-come-first-served).
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

    # Wait for welcome and prompt
    await helper.wait_for_prompt(timeout_cycles=10000)

    # Set input to dual mode (output=UART for verification)
    await helper.send_command("I 2 0")
    await helper.wait_for_prompt()

    # Test 1: Send 'H' via UART
    dut._log.info("Test 1: Sending 'H' via UART")
    await helper.send_uart_char('H')
    await helper.send_uart_char('\r')

    # Should see help message
    output = ""
    for _ in range(500):
        try:
            char = await helper.read_uart_output(timeout_cycles=10)
            output += char if isinstance(char, str) else ""
            if "Commands" in output:
                break
        except TimeoutError:
            await helper.wait_cycles(10)

    assert "Commands" in output or "Help" in output, "Help command should work via UART"
    await helper.wait_for_prompt()

    # Test 2: Send 'H' via PS/2 (scancode 0x33)
    dut._log.info("Test 2: Sending 'H' via PS/2")
    await helper.send_ps2_scancode(0x33)  # 'H' make code
    await helper.send_ps2_scancode(0xF0)  # Break prefix
    await helper.send_ps2_scancode(0x33)  # 'H' break code
    await helper.send_ps2_scancode(0x5A)  # Enter make code
    await helper.send_ps2_scancode(0xF0)  # Break prefix
    await helper.send_ps2_scancode(0x5A)  # Enter break code

    # Should see help message again
    output = ""
    for _ in range(500):
        try:
            char = await helper.read_uart_output(timeout_cycles=10)
            output += char if isinstance(char, str) else ""
            if "Commands" in output:
                break
        except TimeoutError:
            await helper.wait_cycles(10)

    assert "Commands" in output or "Help" in output, "Help command should work via PS/2"

    dut._log.info("Dual input mode verified successfully")


@cocotb.test()
async def test_invalid_io_modes(dut):
    """
    Test that invalid I/O mode values (> 2) produce error messages
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

    # Test invalid input mode
    await helper.send_command("I 5 0")

    output = ""
    for _ in range(200):
        try:
            char = await helper.read_uart_output(timeout_cycles=10)
            output += char if isinstance(char, str) else ""
            if "\n" in output:
                break
        except TimeoutError:
            break

    assert "Invalid" in output or "Error" in output, "Should report invalid input mode"

    dut._log.info("Invalid mode detection verified")
