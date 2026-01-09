# I/O Configuration User Guide

**Feature**: 004-program-loader-io-config
**Last Updated**: 2026-01-01
**Audience**: End Users

## Overview

The RetroCPU monitor allows you to switch between different input and output devices:

- **Input Sources**: UART (serial terminal), PS/2 keyboard, or both
- **Output Destinations**: UART (serial terminal), DVI/HDMI display, or both

This flexibility enables you to use the RetroCPU as:
- A PC-connected development system (UART only)
- A standalone retro computer (PS/2 keyboard + HDMI display)
- A debug system (both sources for maximum flexibility)

## Quick Start

### Default Mode: UART Only

Out of the box, RetroCPU uses UART for both input and output:

```
> S
I/O Status:
  Input:  UART
  Output: UART
```

This is the default mode for development and programming.

### Switch to Standalone Mode

To use PS/2 keyboard and HDMI display:

```
> I 1 1
I/O Config: IN=PS2, OUT=Display
```

Now you can:
- Type commands on PS/2 keyboard
- See output on HDMI display
- No PC required!

### Return to UART Mode

To switch back to UART:

```
> I 0 0
I/O Config: IN=UART, OUT=UART
```

## The I Command

### Syntax

```
I <input_mode> <output_mode>
```

**Parameters**:
- `input_mode`: 0 (UART), 1 (PS/2), 2 (Both)
- `output_mode`: 0 (UART), 1 (Display), 2 (Both)

**Examples**:
```
I 0 0    # UART input and output
I 1 1    # PS/2 input, Display output
I 2 2    # Both inputs, both outputs
I 0 1    # UART input, Display output
I 1 0    # PS/2 input, UART output
```

### Mode Values

#### Input Modes

| Mode | Name | Description |
|------|------|-------------|
| 0 | UART | Read from serial terminal |
| 1 | PS/2 | Read from PS/2 keyboard |
| 2 | Both | Read from either (first-come-first-served) |

#### Output Modes

| Mode | Name | Description |
|------|------|-------------|
| 0 | UART | Write to serial terminal |
| 1 | Display | Write to HDMI display |
| 2 | Both | Write to both simultaneously |

## The S Command

### Syntax

```
S
```

Display current I/O configuration and peripheral status.

**Example Output**:

```
> S
I/O Status:
  Input:  UART
  Output: UART
Peripherals:
  UART:    9600 baud, TX ready, RX empty
  PS/2:    No data
  Display: Ready
```

### Status Information

**I/O Status Section**:
- Shows current input source(s)
- Shows current output destination(s)

**Peripherals Section**:
- **UART**: Baud rate (always 9600), TX status, RX status
- **PS/2**: Data ready status
- **Display**: GPU status

## Use Cases

### Use Case 1: Development with PC

**Configuration**: `I 0 0` (default)

**Setup**:
1. Connect UART to PC via USB-to-serial adapter
2. Open terminal emulator (9600 baud, 8N1)
3. Use default configuration (no I command needed)

**Best For**:
- Uploading programs via XMODEM
- Pasting BASIC programs
- Logging output to PC
- Development and debugging

**Advantages**:
- Full terminal emulator features (copy/paste, logging, macros)
- Easy file transfer (XMODEM)
- Can capture output for documentation
- No additional hardware required

**Disadvantages**:
- Requires PC connection
- Not portable
- Less "authentic" retro feel

### Use Case 2: Standalone Retro Computer

**Configuration**: `I 1 1`

**Setup**:
1. Connect PS/2 keyboard to PS/2 port
2. Connect HDMI display to DVI/HDMI port
3. Switch to standalone mode: `I 1 1`

**Best For**:
- Using BASIC without PC
- Authentic retro computing experience
- Demonstrations and shows
- Portable operation

**Advantages**:
- No PC required
- Authentic keyboard feel
- Large display for easy reading
- Portable and self-contained

**Disadvantages**:
- No file transfer (can't upload programs)
- No logging or capture
- Must type programs manually
- Requires PS/2 keyboard and HDMI display

### Use Case 3: Debug Mode (Everything Enabled)

**Configuration**: `I 2 2`

**Setup**:
1. Connect UART, PS/2 keyboard, and HDMI display
2. Switch to debug mode: `I 2 2`

**Best For**:
- Debugging I/O issues
- Verifying PS/2 keyboard works
- Monitoring serial traffic while using keyboard
- Testing and validation

**Advantages**:
- Maximum flexibility
- See output on both devices
- Input from either source
- Best for troubleshooting

**Disadvantages**:
- Requires all hardware connected
- Duplicate output may be distracting
- Slightly more complex to understand

### Use Case 4: BASIC Development

**Configuration**: `I 0 1`

**Setup**:
1. Connect UART for input (paste programs)
2. Connect HDMI for output (large display)
3. Switch mode: `I 0 1`

**Best For**:
- Writing BASIC programs on PC, viewing results on display
- Comfortable viewing while programming
- Presentations and demos

**Advantages**:
- Paste programs from PC
- View results on large display
- Best of both worlds

**Disadvantages**:
- Requires both UART and display
- Can't use PS/2 keyboard

### Use Case 5: Serial Logging

**Configuration**: `I 1 0`

**Setup**:
1. Connect PS/2 keyboard for input
2. Connect UART for output (logging to PC)
3. Switch mode: `I 1 0`

**Best For**:
- Capturing session for documentation
- Logging output while using keyboard
- Recording programs and results

**Advantages**:
- Use PS/2 keyboard for comfortable typing
- Capture all output to PC for later review
- Good for documentation and tutorials

**Disadvantages**:
- Can't see output without PC terminal
- Requires both keyboard and UART

## Hardware Requirements

### UART Connection

**Required for Modes**: Input 0 or 2, Output 0 or 2

**Pin Connections**:
- UART TX (J17) → USB-to-serial RX
- UART RX → USB-to-serial TX
- GND → USB-to-serial GND

**Settings**: 9600 baud, 8 data bits, no parity, 1 stop bit (8N1)

**Terminal Emulators**:
- Windows: Tera Term, PuTTY
- Linux: minicom, screen
- macOS: screen, ZOC Terminal

### PS/2 Keyboard

**Required for Modes**: Input 1 or 2

**Pin Connections**:
- PS/2 Clock (K5) → Keyboard Clock
- PS/2 Data (B3) → Keyboard Data
- +5V → Keyboard VCC
- GND → Keyboard GND

**Compatible Keyboards**:
- Any standard PS/2 keyboard
- PS/2 to USB adapters (passive adapters only, NOT active converters)
- Vintage keyboards (most work without issue)

**Supported Keys**:
- Letters (a-z, A-Z with Shift)
- Numbers (0-9)
- Symbols (punctuation on US layout)
- Enter, Backspace, Escape, Tab
- Space bar
- Shift (left and right)
- Caps Lock (toggle)

**Not Currently Supported**:
- Function keys (F1-F12)
- Arrow keys
- Home, End, Page Up, Page Down
- Numeric keypad
- Extended scancodes (Windows keys, etc.)

### DVI/HDMI Display

**Required for Modes**: Output 1 or 2

**Pin Connections**:
- DVI output → HDMI display (via DVI-to-HDMI cable or adapter)

**Display Modes**:
- 640×480 @ 60Hz (VGA timing)
- 40-column text mode (16×16 character cells)
- 80-column text mode (8×16 character cells) - if implemented
- 8-color palette (3-bit RGB)

**Compatible Displays**:
- Any HDMI monitor or TV
- DVI monitors (with DVI cable)
- Older VGA monitors (with HDMI-to-VGA adapter)

## Switching Modes Dynamically

### Mode Changes Take Effect Immediately

When you issue the `I` command, the new mode takes effect for the next character read or written:

```
> I 1 1
I/O Config: IN=PS2, OUT=Display
[Last output goes to UART]
> H
[Output now appears on Display]
```

**Note**: The confirmation message from the `I` command itself goes to the **previous** output mode. Subsequent output uses the new mode.

### Mode Persistence

**Current Behavior**: Mode resets to UART-only (0 0) on system reset.

**Why**: I/O configuration is stored in RAM variables, which are initialized on reset.

**Future Enhancement**: Save mode to non-volatile storage (future firmware version).

### Safe Mode Switching

**Best Practice**: Switch from UART to standalone mode carefully:

1. Make sure PS/2 keyboard is connected
2. Make sure HDMI display is connected and on
3. Issue `I 1 1` command via UART
4. Verify prompt appears on HDMI display
5. Test PS/2 keyboard by typing `H` command
6. Confirm help appears on display

**Recovery**: If you can't see output or type input after mode switch, press **reset button** to return to default UART mode.

## Troubleshooting

### Problem: "Invalid input mode"

**Cause**: Input mode parameter is not 0, 1, or 2

**Example**:
```
> I 3 0
Invalid input mode (0=UART, 1=PS2, 2=Both)
```

**Solution**: Use mode value 0, 1, or 2:
```
> I 0 0    # Correct
> I 1 1    # Correct
> I 2 2    # Correct
```

### Problem: "Invalid output mode"

**Cause**: Output mode parameter is not 0, 1, or 2

**Example**:
```
> I 0 5
Invalid output mode (0=UART, 1=Disp, 2=Both)
```

**Solution**: Use mode value 0, 1, or 2.

### Problem: Can't type after switching to PS/2 mode

**Cause**: PS/2 keyboard not connected or not working

**Symptoms**:
```
> I 1 1
I/O Config: IN=PS2, OUT=Display
[No response to keyboard input]
```

**Solutions**:
1. **Check Connection**: Verify PS/2 keyboard is plugged into PS/2 port
2. **Check Power**: Verify keyboard lights turn on (if it has LEDs)
3. **Try Different Keyboard**: Some keyboards may not be compatible
4. **Check Pinout**: Verify PS/2 clock and data pins are correct
5. **Reset to UART**: Press reset button to return to UART mode

**Recovery**: Press reset button to return to UART mode (default).

### Problem: No output on display after switching

**Cause**: Display not connected or not configured correctly

**Symptoms**:
```
> I 0 1
I/O Config: IN=UART, OUT=Display
> H
[No output visible anywhere]
```

**Solutions**:
1. **Check Connection**: Verify HDMI cable is connected
2. **Check Display Power**: Verify display is turned on
3. **Check Input Selection**: Verify display is set to correct HDMI input
4. **Try Both Output Mode**: `I 0 2` to see output on both UART and display
5. **Check GPU Status**: Use `S` command to check display status

**Recovery**: Switch to UART output mode: `I 0 0` to see output on UART.

### Problem: PS/2 keyboard produces wrong characters

**Cause**: Scancode translation issue or non-US keyboard layout

**Symptoms**:
- Pressing 'A' produces different character
- Shift key doesn't work
- Some keys produce nothing

**Solutions**:
1. **Check Keyboard Layout**: RetroCPU assumes US keyboard layout
2. **Check Scancode Set**: Verify keyboard uses Set 2 scancodes (most do)
3. **Check Key Mapping**: Some keys may not be mapped (see supported keys above)
4. **Update Firmware**: Future firmware may support more layouts

**Workaround**: Use UART mode for complex typing, PS/2 for basic operation.

### Problem: Shift key doesn't work on PS/2 keyboard

**Cause**: Shift key state tracking issue

**Symptoms**:
- Pressing Shift+A produces 'a' instead of 'A'
- Shift seems to have no effect

**Solutions**:
1. **Release All Keys**: Release all keys and try again
2. **Press and Hold Shift**: Make sure to press Shift before letter key
3. **Check Break Code Handling**: Firmware may not be processing Shift release correctly

**Diagnostic**: Try Caps Lock instead - if Caps Lock works but Shift doesn't, report as firmware bug.

### Problem: Caps Lock gets stuck

**Cause**: Caps Lock is a toggle state, not a momentary key

**Symptoms**:
- All letters are uppercase even when Caps Lock light is off
- Can't type lowercase letters

**Solution**: Press Caps Lock key again to toggle state.

**Explanation**: Caps Lock toggles between on and off state. Press once to enable, press again to disable.

### Problem: Both mode doesn't work as expected

**Cause**: Misunderstanding of "first-come-first-served" for input

**Example**:
```
> I 2 0
I/O Config: IN=Both, OUT=UART
[Type on PS/2 keyboard: nothing happens]
[Type in UART terminal: works]
```

**Explanation**: In "Both" mode for input, the monitor polls UART **first**, then PS/2. If UART has data, it is processed before checking PS/2.

**How It Works**:
- Monitor checks UART RX ready
- If UART has data, read from UART
- If UART has no data, check PS/2
- If PS/2 has data, read from PS/2
- If neither has data, loop and check again

**Solution**: This is normal behavior. Both sources work, but UART is prioritized when both have data simultaneously (rare in practice).

### Problem: Output appears twice in "Both" mode

**Cause**: Output mode set to "Both" (2) means **duplicate** output

**Example**:
```
> I 0 2
I/O Config: IN=UART, OUT=Both
> H
[Help appears on both UART terminal AND HDMI display]
```

**Explanation**: This is **correct behavior**! "Both" mode sends every character to both UART and display simultaneously.

**Use Case**: Good for debugging, demos, or when you want to see output in two places.

**Solution**: If you only want output on one device, use mode 0 or 1, not 2.

## Best Practices

### Development Workflow

1. **Start with UART mode (default)**: `I 0 0`
2. **Upload and test programs via UART**
3. **Switch to standalone mode for demos**: `I 1 1`
4. **Return to UART mode for debugging**: `I 0 0`

### When to Use Each Mode

**UART-Only (0 0)**: Default for development
- Uploading programs (XMODEM)
- Pasting BASIC code
- Logging and debugging

**Standalone (1 1)**: Portable operation
- Running BASIC without PC
- Demonstrations
- Authentic retro experience

**Debug (2 2)**: Testing and troubleshooting
- Verifying PS/2 keyboard works
- Checking display output
- Monitoring multiple sources

**Hybrid Modes**: Special use cases
- `I 0 1`: BASIC development (paste programs, view on display)
- `I 1 0`: Session logging (type on keyboard, capture to UART)

### Mode Switching Safety

**Before Switching to Standalone Mode**:
1. Verify PS/2 keyboard is connected and working
2. Verify HDMI display is connected and showing RetroCPU output
3. Test with `I 2 2` (both mode) first to verify both devices work
4. Only then switch to `I 1 1` (standalone mode)

**If Something Goes Wrong**:
- Press **reset button** to return to default UART mode
- Reconnect via UART terminal
- Troubleshoot the issue before trying again

### Testing PS/2 Keyboard

Before relying on PS/2 keyboard, test it:

```
> I 2 0
I/O Config: IN=Both, OUT=UART
> [Type on PS/2 keyboard]
[Output appears on UART]
> [Type in UART terminal]
[Output appears on UART]
```

This confirms PS/2 keyboard is working before switching fully to standalone mode.

## Reference

### I Command Syntax

```
I <input_mode> <output_mode>

input_mode:  0 (UART), 1 (PS/2), 2 (Both)
output_mode: 0 (UART), 1 (Display), 2 (Both)
```

### S Command Syntax

```
S

Displays:
- Current I/O configuration
- UART status (baud rate, TX ready, RX ready)
- PS/2 status (data ready)
- Display status (GPU ready)
```

### Mode Combinations (9 total)

| Input | Output | Use Case |
|-------|--------|----------|
| 0 (UART) | 0 (UART) | **Development (default)** |
| 0 (UART) | 1 (Display) | BASIC development |
| 0 (UART) | 2 (Both) | Debug: UART in, both out |
| 1 (PS/2) | 0 (UART) | Session logging |
| 1 (PS/2) | 1 (Display) | **Standalone operation** |
| 1 (PS/2) | 2 (Both) | Demo with logging |
| 2 (Both) | 0 (UART) | Testing PS/2 keyboard |
| 2 (Both) | 1 (Display) | Flexible input, display out |
| 2 (Both) | 2 (Both) | **Full debug mode** |

### Supported PS/2 Keys

**Printable Characters**:
- Letters: a-z (lowercase), A-Z (uppercase with Shift)
- Digits: 0-9
- Symbols: ` ~ ! @ # $ % ^ & * ( ) - _ = + [ ] { } \ | ; : ' " , < . > / ?

**Control Keys**:
- Enter (0x0D, carriage return)
- Backspace (0x08)
- Escape (0x1B)
- Tab (0x09)
- Space (0x20)

**Modifier Keys**:
- Shift (left and right)
- Caps Lock (toggle)

## See Also

- [I/O Abstraction Architecture](../protocols/io_abstraction.md)
- [Program Loading Guide](program_loading.md)
- [Flow Control Strategy](../protocols/flow_control.md)
- [Main README](../../README.md)

## Support

For questions or issues:
- Check Troubleshooting section above
- Review I/O abstraction documentation: `docs/protocols/io_abstraction.md`
- Consult feature specification: `specs/004-program-loader-io-config/spec.md`
