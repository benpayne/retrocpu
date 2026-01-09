#!/usr/bin/env python3
"""
Unit tests for PS2_TO_ASCII function (Feature 004 - User Story 2, T028)

Tests PS/2 scancode to ASCII translation with:
- Letters (a-z, A-Z)
- Numbers (0-9)
- Special characters
- Modifier keys (Shift, Caps Lock)
- Control keys (Enter, Backspace, Space)
- Break codes (key release)
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.binary import BinaryValue


class PS2TestHelper:
    """Helper for testing PS2_TO_ASCII function in isolation"""

    def __init__(self, dut):
        self.dut = dut

    async def call_ps2_to_ascii(self, scancode):
        """
        Call PS2_TO_ASCII function and return result

        In a real test, this would:
        1. Set up the scancode in the A register
        2. Call the PS2_TO_ASCII subroutine
        3. Read the result from the A register

        For this test harness, we'll simulate the function behavior
        by directly accessing zero page state and the lookup table.
        """
        # This is a placeholder - actual implementation would interact
        # with the 6502 CPU simulation
        pass

    def get_ps2_shift_flag(self):
        """Read PS2_SHIFT_FLAG from zero page $2A"""
        return int(self.dut.ram.read(0x2A))

    def get_ps2_caps_flag(self):
        """Read PS2_CAPS_FLAG from zero page $2B"""
        return int(self.dut.ram.read(0x2B))

    def get_ps2_break_flag(self):
        """Read PS2_BREAK from zero page $05"""
        return int(self.dut.ram.read(0x05))


@cocotb.test()
async def test_ps2_letters_unshifted(dut):
    """
    Test unshifted letter scancodes (should return lowercase ASCII)

    Scancode examples:
    0x1C -> 'a' (0x61)
    0x32 -> 'b' (0x62)
    0x1A -> 'z' (0x7A)
    """

    helper = PS2TestHelper(dut)

    test_cases = [
        (0x1C, ord('a')),  # A key -> 'a'
        (0x32, ord('b')),  # B key -> 'b'
        (0x21, ord('c')),  # C key -> 'c'
        (0x1A, ord('z')),  # Z key -> 'z'
    ]

    for scancode, expected_ascii in test_cases:
        result = await helper.call_ps2_to_ascii(scancode)
        assert result == expected_ascii, f"Scancode 0x{scancode:02X} should return {chr(expected_ascii)}"

    dut._log.info("Unshifted letter tests passed")


@cocotb.test()
async def test_ps2_letters_shifted(dut):
    """
    Test shifted letter scancodes (should return uppercase ASCII)

    Process:
    1. Send Left Shift make code (0x12) -> sets PS2_SHIFT_FLAG
    2. Send letter (e.g., 0x1C for 'A') -> should return uppercase
    3. Send Left Shift break code (0xF0 0x12) -> clears PS2_SHIFT_FLAG
    """

    helper = PS2TestHelper(dut)

    # Press Left Shift
    result = await helper.call_ps2_to_ascii(0x12)
    assert result == 0x00, "Shift make code should return 0x00"
    assert helper.get_ps2_shift_flag() == 1, "Shift flag should be set"

    # Press 'A' while shifted
    result = await helper.call_ps2_to_ascii(0x1C)
    assert result == ord('A'), "Shifted 'a' should return 'A'"

    # Release Shift (break code sequence)
    result = await helper.call_ps2_to_ascii(0xF0)  # Break prefix
    assert result == 0x00, "Break prefix should return 0x00"
    assert helper.get_ps2_break_flag() == 1, "Break flag should be set"

    result = await helper.call_ps2_to_ascii(0x12)  # Shift break code
    assert result == 0x00, "Shift break code should return 0x00"
    assert helper.get_ps2_shift_flag() == 0, "Shift flag should be cleared"
    assert helper.get_ps2_break_flag() == 0, "Break flag should be cleared"

    # Press 'A' again (unshifted)
    result = await helper.call_ps2_to_ascii(0x1C)
    assert result == ord('a'), "Unshifted 'a' should return 'a'"

    dut._log.info("Shifted letter tests passed")


@cocotb.test()
async def test_ps2_caps_lock_toggle(dut):
    """
    Test Caps Lock toggle functionality

    Process:
    1. Press Caps Lock (0x58) -> toggles PS2_CAPS_FLAG to 1
    2. Press letter -> should return uppercase
    3. Press Caps Lock again -> toggles PS2_CAPS_FLAG to 0
    4. Press letter -> should return lowercase
    """

    helper = PS2TestHelper(dut)

    # Initial state: Caps Lock off
    assert helper.get_ps2_caps_flag() == 0, "Caps Lock should be off initially"

    # Press Caps Lock (toggle on)
    result = await helper.call_ps2_to_ascii(0x58)
    assert result == 0x00, "Caps Lock make code should return 0x00"
    assert helper.get_ps2_caps_flag() == 1, "Caps Lock should be on"

    # Press 'A' with Caps Lock on
    result = await helper.call_ps2_to_ascii(0x1C)
    assert result == ord('A'), "Caps Lock 'a' should return 'A'"

    # Press Caps Lock again (toggle off)
    result = await helper.call_ps2_to_ascii(0x58)
    assert result == 0x00, "Caps Lock make code should return 0x00"
    assert helper.get_ps2_caps_flag() == 0, "Caps Lock should be off"

    # Press 'A' with Caps Lock off
    result = await helper.call_ps2_to_ascii(0x1C)
    assert result == ord('a'), "Normal 'a' should return 'a'"

    dut._log.info("Caps Lock toggle tests passed")


@cocotb.test()
async def test_ps2_numbers_unshifted(dut):
    """
    Test number scancodes (unshifted should return '0'-'9')

    Scancode examples:
    0x45 -> '0' (0x30)
    0x16 -> '1' (0x31)
    0x46 -> '9' (0x39)
    """

    helper = PS2TestHelper(dut)

    test_cases = [
        (0x45, ord('0')),
        (0x16, ord('1')),
        (0x1E, ord('2')),
        (0x46, ord('9')),
    ]

    for scancode, expected_ascii in test_cases:
        result = await helper.call_ps2_to_ascii(scancode)
        assert result == expected_ascii, f"Scancode 0x{scancode:02X} should return {chr(expected_ascii)}"

    dut._log.info("Number tests passed")


@cocotb.test()
async def test_ps2_special_characters(dut):
    """
    Test special character scancodes

    Examples:
    0x29 -> ' ' (Space)
    0x5A -> 0x0D (Enter/CR)
    0x66 -> 0x08 (Backspace)
    """

    helper = PS2TestHelper(dut)

    test_cases = [
        (0x29, ord(' ')),   # Space
        (0x5A, 0x0D),       # Enter (CR)
        (0x66, 0x08),       # Backspace
        (0x0D, 0x09),       # Tab
    ]

    for scancode, expected_ascii in test_cases:
        result = await helper.call_ps2_to_ascii(scancode)
        assert result == expected_ascii, f"Scancode 0x{scancode:02X} should return 0x{expected_ascii:02X}"

    dut._log.info("Special character tests passed")


@cocotb.test()
async def test_ps2_break_codes(dut):
    """
    Test break code handling (key release)

    Break codes should:
    1. 0xF0 prefix sets PS2_BREAK flag
    2. Next scancode clears PS2_BREAK flag
    3. Non-modifier break codes return 0x00 (ignored)
    """

    helper = PS2TestHelper(dut)

    # Initial state
    assert helper.get_ps2_break_flag() == 0, "Break flag should be off initially"

    # Send break code prefix
    result = await helper.call_ps2_to_ascii(0xF0)
    assert result == 0x00, "Break prefix should return 0x00"
    assert helper.get_ps2_break_flag() == 1, "Break flag should be set"

    # Send letter break code (should be ignored)
    result = await helper.call_ps2_to_ascii(0x1C)  # 'A' break code
    assert result == 0x00, "Letter break code should return 0x00"
    assert helper.get_ps2_break_flag() == 0, "Break flag should be cleared"

    # Verify next make code works normally
    result = await helper.call_ps2_to_ascii(0x1C)
    assert result == ord('a'), "Make code after break should work normally"

    dut._log.info("Break code tests passed")


@cocotb.test()
async def test_ps2_unmapped_scancodes(dut):
    """
    Test unmapped scancodes (function keys, etc.)

    Unmapped scancodes should return 0x00 (ignored)
    """

    helper = PS2TestHelper(dut)

    # Function keys and other unmapped codes
    unmapped_scancodes = [0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C]

    for scancode in unmapped_scancodes:
        result = await helper.call_ps2_to_ascii(scancode)
        assert result == 0x00, f"Unmapped scancode 0x{scancode:02X} should return 0x00"

    dut._log.info("Unmapped scancode tests passed")


@cocotb.test()
async def test_ps2_shift_and_caps_together(dut):
    """
    Test interaction between Shift and Caps Lock

    When both are active for letters:
    - The behavior should be consistent (uppercase with either/both)
    """

    helper = PS2TestHelper(dut)

    # Turn on Caps Lock
    await helper.call_ps2_to_ascii(0x58)
    assert helper.get_ps2_caps_flag() == 1

    # Press Shift
    await helper.call_ps2_to_ascii(0x12)
    assert helper.get_ps2_shift_flag() == 1

    # Press 'A' (both Shift and Caps Lock active)
    result = await helper.call_ps2_to_ascii(0x1C)
    assert result == ord('A'), "Should return uppercase with both modifiers"

    # Release Shift
    await helper.call_ps2_to_ascii(0xF0)
    await helper.call_ps2_to_ascii(0x12)
    assert helper.get_ps2_shift_flag() == 0

    # Press 'A' (only Caps Lock active)
    result = await helper.call_ps2_to_ascii(0x1C)
    assert result == ord('A'), "Should return uppercase with Caps Lock only"

    dut._log.info("Shift+Caps Lock interaction tests passed")


# Note: These tests are currently stubs because they require a full
# 6502 CPU simulation with monitor firmware loaded. They demonstrate
# the test structure and expected behavior.
#
# To run these tests, you would need:
# 1. A cocotb testbench that instantiates the full SoC
# 2. Monitor firmware loaded into ROM
# 3. A way to call PS2_TO_ASCII subroutine and read results
# 4. Ability to read/write zero page variables
#
# For now, these serve as specification and will be implemented
# when the full integration test harness is available.
