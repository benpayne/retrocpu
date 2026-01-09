# Contract: Monitor I/O Configuration Interface

**Component**: Monitor Firmware - I/O Configuration Commands
**Interface Type**: User Command Interface
**Version**: 1.0
**Date**: 2026-01-01

## Purpose

Defines the user-facing interface for configuring input/output sources and displaying I/O status in the monitor.

## Command Specifications

### I (I/O Config) Command

**Syntax**:
```
I <input_mode> <output_mode>
```

**Parameters**:
- `input_mode`: Single digit (0, 1, or 2)
  - `0` = UART only
  - `1` = PS/2 keyboard only
  - `2` = Both UART and PS/2 (first-come-first-served)
- `output_mode`: Single digit (0, 1, or 2)
  - `0` = UART only
  - `1` = Display (GPU) only
  - `2` = Both UART and Display (duplicated output)

**Examples**:
```
> I 0 0   (UART input, UART output - default)
> I 1 1   (PS/2 input, Display output - standalone mode)
> I 2 2   (Both inputs, both outputs - maximum connectivity)
```

### Behavior

1. **Parameter Parsing**:
   - Skip whitespace after 'I' command
   - Read first digit (input mode)
   - Skip whitespace
   - Read second digit (output mode)

2. **Validation**:
   - If input_mode not in {0, 1, 2}: Display "Invalid input mode (0=UART, 1=PS2, 2=Both)"
   - If output_mode not in {0, 1, 2}: Display "Invalid output mode (0=UART, 1=Disp, 2=Both)"
   - On validation error: Do not change configuration, return to prompt

3. **Configuration Update**:
   - Store `input_mode` in zero page variable `IO_INPUT_MODE` ($21)
   - Store `output_mode` in zero page variable `IO_OUTPUT_MODE` ($22)
   - Display confirmation message (see examples below)

4. **Immediate Effect**:
   - Next CHRIN call uses new input source(s)
   - Next CHROUT call uses new output destination(s)

**Confirmation Messages**:
```
> I 0 0
I/O Config: IN=UART, OUT=UART

> I 1 1
I/O Config: IN=PS2, OUT=Display

> I 2 2
I/O Config: IN=Both, OUT=Both
```

### S (Status) Command

**Syntax**:
```
S
```

**Parameters**: None

**Example**:
```
> S
```

### Behavior

Display current I/O configuration and peripheral status:

**Output Format**:
```
I/O Status:
  Input:  <source>
  Output: <destination>
Peripherals:
  UART:    9600 baud, TX ready, RX ready
  PS/2:    Detected, data ready
  Display: 80-column mode, cursor at (5, 20)
```

**Field Details**:

1. **Input Source**:
   - `IO_INPUT_MODE == 0`: "UART"
   - `IO_INPUT_MODE == 1`: "PS/2"
   - `IO_INPUT_MODE == 2`: "UART + PS/2"

2. **Output Destination**:
   - `IO_OUTPUT_MODE == 0`: "UART"
   - `IO_OUTPUT_MODE == 1`: "Display"
   - `IO_OUTPUT_MODE == 2`: "UART + Display"

3. **UART Status**:
   - Baud rate (fixed at 9600 for now)
   - TX ready: Read UART_STATUS bit 0
   - RX ready: Read UART_STATUS bit 1

4. **PS/2 Status**:
   - Detected: Check if PS2_STATUS bit 0 ever set (indicates keyboard present)
   - Data ready: Read PS2_STATUS bit 0 (current state)

5. **Display Status** (optional for Phase 1):
   - Mode: Read GPU_MODE register to determine 40 or 80 column
   - Cursor: Read GPU_CURSOR_ROW and GPU_CURSOR_COL

## State Variables (Zero Page)

```
$21: IO_INPUT_MODE   - Input source (0=UART, 1=PS2, 2=Both)
$22: IO_OUTPUT_MODE  - Output dest (0=UART, 1=Display, 2=Both)
```

**Initial Values** (after RESET):
```
IO_INPUT_MODE  = 0  (UART only)
IO_OUTPUT_MODE = 0  (UART only)
```

## Functional Contracts

### CHRIN Enhancement

**Precondition**: `IO_INPUT_MODE` set to 0, 1, or 2

**Behavior**:
- Mode 0 (UART): Poll UART_STATUS bit 1, return UART_DATA when ready
- Mode 1 (PS/2): Poll PS2_STATUS bit 0, return PS2_DATA → ASCII when ready
- Mode 2 (Both): Poll both status registers, return first available character

**Postcondition**: Returns ASCII character in A register

**Blocking**: CHRIN blocks until character available from any configured source

### CHROUT Enhancement

**Precondition**: `IO_OUTPUT_MODE` set to 0, 1, or 2; ASCII character in A register

**Behavior**:
- Mode 0 (UART): Write A to UART_DATA when TX ready
- Mode 1 (Display): Write A to GPU_CHAR_DATA (immediate, non-blocking)
- Mode 2 (Both): Write A to UART_DATA, then write A to GPU_CHAR_DATA

**Postcondition**: Character sent to configured destination(s)

**Note**: UART output waits for TX ready (blocking); GPU output is immediate (non-blocking)

## Testing Contract

### Test Case 1: Switch to Standalone Mode (PS/2 + Display)

**Setup**: PS/2 keyboard connected, HDMI display connected

**Steps**:
1. Connect via UART terminal
2. Enter: `I 1 1`
3. Observe confirmation on UART: "I/O Config: IN=PS2, OUT=Display"
4. Next command prompt should appear on HDMI display
5. Type commands on PS/2 keyboard
6. See output on HDMI display

**Expected**:
- No further UART output after I command
- All subsequent I/O on PS/2 keyboard and HDMI display

### Test Case 2: Switch to Dual Output Mode

**Setup**: UART terminal and HDMI display connected

**Steps**:
1. Enter: `I 0 2` (UART input, both outputs)
2. Enter: `E 0200` (examine memory)

**Expected**:
- Memory dump appears on both UART terminal AND HDMI display simultaneously
- Character-for-character match on both outputs

### Test Case 3: Status Display

**Setup**: All peripherals connected, configuration set to `I 2 2`

**Steps**:
1. Enter: `S`

**Expected Output**:
```
I/O Status:
  Input:  UART + PS/2
  Output: UART + Display
Peripherals:
  UART:    9600 baud, TX ready, RX ready
  PS/2:    Detected, data ready
  Display: 80-column mode, cursor at (0, 0)
```

### Test Case 4: Invalid Input Mode

**Steps**:
1. Enter: `I 5 0`

**Expected**:
- Error message: "Invalid input mode (0=UART, 1=PS2, 2=Both)"
- Configuration unchanged (remains at previous settings)
- Prompt returns

### Test Case 5: Configuration Persistence (Across Commands)

**Steps**:
1. Enter: `I 1 1` (standalone mode)
2. Enter: `E 0200` (examine memory)
3. Memory dump appears on display (not UART)

**Expected**:
- I/O configuration persists across commands
- All subsequent operations use PS/2 input and Display output
- Configuration remains until changed or reset

### Test Case 6: Reset Behavior

**Steps**:
1. Enter: `I 2 2` (dual mode)
2. Press hardware reset button
3. System resets, monitor restarts

**Expected**:
- Welcome message appears on UART only (default output)
- Prompt accepts input from UART only (default input)
- Configuration reset to `I 0 0` (UART/UART)

## Dependencies

- **UART Peripheral**: Functional UART at $C000-$C001
- **PS/2 Peripheral**: Functional PS/2 at $C200-$C201 with scancode FIFO
- **GPU Peripheral**: Functional GPU at $C010-$C013 with character output
- **PS/2 Translation**: PS2_TO_ASCII function (maps scancodes to ASCII)

## Edge Cases

### Dual Input Priority

When `IO_INPUT_MODE == 2` (Both):
- Poll UART first, then PS/2
- Return first available character
- No buffering of "lost" characters from non-selected source

**Rationale**: Simplicity over fairness; user can switch to single-source mode if needed

### Display vs UART Control Characters

**UART Output**: Send raw ASCII (including control characters like 0x0D, 0x0A)
**Display Output**:
- 0x0D (CR): Move cursor to column 0 (if GPU supports), otherwise ignore
- 0x0A (LF): Newline, advance to next row
- 0x08 (BS): Backspace, move cursor left
- Other control chars: Ignore or display as '?'

**Note**: GPU character renderer may handle control characters differently; monitor should send raw ASCII and let GPU interpret.

### PS/2 Keyboard Not Present

If `IO_INPUT_MODE == 1` (PS/2 only) but keyboard not connected:
- CHRIN polls PS2_STATUS bit 0 forever (blocking)
- User must reset or switch I/O mode via hardware intervention

**Future Enhancement**: Add timeout or "no device" detection

## Future Enhancements

- Configuration persistence in EEPROM or battery-backed RAM
- Hotkey (e.g., Ctrl-Alt-I) to toggle I/O modes without typing command
- Automatic fallback to UART if PS/2 keyboard not detected
- I/O mode indicator on display status line
