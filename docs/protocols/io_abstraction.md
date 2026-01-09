# I/O Abstraction and Multiplexing Architecture

**Feature**: 004-program-loader-io-config
**Last Updated**: 2026-01-01
**Status**: Implemented and Tested

## Overview

The RetroCPU monitor firmware implements a flexible I/O abstraction layer that allows dynamic switching between multiple input and output devices. This enables the system to operate standalone with PS/2 keyboard and HDMI display, or connected to a PC via UART, or any combination thereof.

## Architecture

### Firmware-Based Multiplexing

The I/O abstraction is implemented entirely in monitor firmware (6502 assembly) with no RTL changes required. This "software multiplexing" approach:

- **Simplicity**: No additional FPGA logic needed
- **Flexibility**: Easy to modify and extend
- **Educational**: Clear demonstration of polling-based I/O
- **Resource Efficient**: Zero FPGA resource overhead

### Configuration Variables

Two zero-page variables control I/O routing:

```assembly
IO_INPUT_MODE   = $21    ; Input source (0=UART, 1=PS2, 2=Both)
IO_OUTPUT_MODE  = $22    ; Output dest (0=UART, 1=Display, 2=Both)
```

These variables are initialized to 0 (UART-only mode) on reset and can be changed at runtime via the `I` command.

## Input Abstraction (CHRIN)

### CHRIN Function

The `CHRIN` function provides a unified character input interface that abstracts the underlying hardware. Applications call `CHRIN` to read a character without knowing which device provided it.

**Interface**:
- **Input**: None
- **Output**: A = ASCII character received
- **Preserves**: X, Y registers
- **Blocking**: Waits until character is available

### Mode 0: UART Only

```assembly
CHRIN:
    LDA IO_INPUT_MODE
    BEQ @UART_ONLY

@UART_ONLY:
    LDA UART_STATUS       ; $C001
    AND #$02              ; Bit 1 = RX ready
    BEQ @UART_ONLY        ; Wait for data
    LDA UART_DATA         ; $C000
    PHA                   ; Save character
    JSR SEND_XON          ; Flow control
    PLA                   ; Restore character
    RTS
```

**Data Flow**:
```
UART RX → UART_STATUS (poll) → UART_DATA (read) → A register
                                      ↓
                                  SEND_XON (flow control)
```

### Mode 1: PS/2 Only

```assembly
@PS2_ONLY:
    LDA PS2_STATUS        ; $C201
    AND #$01              ; Bit 0 = data ready
    BEQ @PS2_ONLY         ; Wait for data
@READ_PS2:
    LDA PS2_DATA          ; $C200 (scancode)
    ; Handle break codes (0xF0 prefix)
    CMP #$F0
    BNE @NOT_BREAK
    LDA #1
    STA PS2_BREAK
    JMP CHRIN             ; Recursively get next scancode

@NOT_BREAK:
    ; Check if this is a break code (key release)
    LDA PS2_BREAK
    BNE @IS_BREAK
    ; Make code (key press) - convert to ASCII
    JSR PS2_TO_ASCII
    RTS

@IS_BREAK:
    ; Handle modifier key releases (Shift)
    ; ... clear flags and get next character ...
```

**Data Flow**:
```
PS/2 Scancode → PS2_STATUS (poll) → PS2_DATA (read scancode)
                                         ↓
                                    PS2_TO_ASCII (translation)
                                         ↓
                                    A register (ASCII)
```

### Mode 2: Both (First-Come-First-Served)

```assembly
@CHECK_BOTH:
    ; Check UART first
    LDA UART_STATUS
    AND #$02              ; Bit 1 = RX ready
    BNE @READ_UART
    ; Check PS/2 second
    LDA PS2_STATUS
    AND #$01              ; Bit 0 = data ready
    BNE @READ_PS2
    ; No data from either source, loop
    JMP @CHECK_BOTH

@READ_UART:
    LDA UART_DATA
    PHA
    JSR SEND_XON
    PLA
    RTS

@READ_PS2:
    ; ... (PS/2 handling as in Mode 1) ...
```

**Data Flow**:
```
                    ┌─ UART_STATUS → UART_DATA → A ───┐
                    │                                   ↓
CHRIN (poll both) ──┤                              A register
                    │                                   ↑
                    └─ PS2_STATUS → PS2_DATA → PS2_TO_ASCII ─┘
```

**Priority**: UART is checked first, then PS/2. This ensures UART input is never missed, which is important for reliable XMODEM transfers.

## Output Abstraction (CHROUT)

### CHROUT Function

The `CHROUT` function provides a unified character output interface that abstracts the underlying hardware. Applications call `CHROUT` to write a character without knowing which device(s) will display it.

**Interface**:
- **Input**: A = ASCII character to output
- **Output**: None
- **Preserves**: X, Y registers
- **Behavior**: Non-blocking (waits for TX ready internally)

### Mode 0: UART Only

```assembly
CHROUT:
    PHA                   ; Save character
    LDA IO_OUTPUT_MODE
    BEQ @UART_ONLY

@UART_ONLY:
    PLA
    JSR UART_SEND         ; Helper function
    RTS
```

**Data Flow**:
```
A register → UART_SEND → UART_STATUS (poll TX ready) → UART_DATA (write)
```

### Mode 1: Display Only

```assembly
@DISPLAY_ONLY:
    PLA
    STA GPU_CHAR_DATA     ; $C010
    RTS
```

**Data Flow**:
```
A register → GPU_CHAR_DATA (write) → GPU (hardware auto-advance cursor)
```

**Note**: GPU character output is non-blocking. Writing to `GPU_CHAR_DATA` immediately outputs the character and advances the cursor. No polling required.

### Mode 2: Both (Duplicate Output)

```assembly
@SEND_BOTH:
    PLA                   ; Restore character
    PHA                   ; Save again for second output
    JSR UART_SEND         ; Send to UART
    PLA
    STA GPU_CHAR_DATA     ; Send to GPU
    RTS
```

**Data Flow**:
```
                      ┌─→ UART_SEND → UART_DATA
                      │
A register (saved) ───┤
                      │
                      └─→ GPU_CHAR_DATA
```

**Synchronization**: UART is sent first (blocking on TX ready), then GPU (non-blocking). This ensures UART output completes before returning, while GPU output is fire-and-forget.

## PS/2 Scancode Translation (PS2_TO_ASCII)

### Overview

The PS/2 keyboard uses Set 2 scancodes, which must be translated to ASCII for compatibility with the monitor and BASIC interpreter. The `PS2_TO_ASCII` function performs this translation with support for modifier keys (Shift, Caps Lock).

### Scancode Set 2

PS/2 Set 2 uses:
- **Make Codes**: Sent when key is pressed (single byte, e.g., 0x1C = 'A' key)
- **Break Codes**: Sent when key is released (0xF0 prefix + make code, e.g., 0xF0 0x1C)
- **Extended Codes**: Sent for special keys (0xE0 prefix, currently ignored)

### Translation Table

A 128-byte lookup table maps scancodes to unshifted ASCII characters:

```assembly
PS2_XLAT_TABLE  = $0280  ; RAM buffer (128 bytes)
PS2_XLAT_ROM    ; ROM data (copied to RAM on init)

; Example entries:
; 0x1C → 'a' (unshifted)
; 0x15 → 'q'
; 0x16 → '1'
; 0x5A → 0x0D (Enter)
; 0x66 → 0x08 (Backspace)
```

### Modifier Key Handling

```assembly
PS2_SHIFT_FLAG  = $2A    ; Shift key state (0=not pressed, 1=pressed)
PS2_CAPS_FLAG   = $2B    ; Caps Lock state (0=off, 1=on)
```

**Shift Keys**:
- **Left Shift**: Scancode 0x12 (make) / 0xF0 0x12 (break)
- **Right Shift**: Scancode 0x59 (make) / 0xF0 0x59 (break)

**Caps Lock**:
- **Scancode**: 0x58 (make toggles state, break ignored)
- **Behavior**: Toggles `PS2_CAPS_FLAG` between 0 and 1

### Translation Algorithm

```assembly
PS2_TO_ASCII:
    ; Check for extended code prefix (0xE0) - ignore
    CMP #$E0
    BNE @NOT_EXTENDED
    LDA #0              ; Return 0 (ignore)
    RTS

@NOT_EXTENDED:
    ; Check for modifier keys (Shift, Caps Lock)
    CMP #$12            ; Left Shift
    BEQ @SET_SHIFT
    CMP #$59            ; Right Shift
    BEQ @SET_SHIFT
    CMP #$58            ; Caps Lock
    BNE @NOT_CAPS
    ; Toggle Caps Lock
    LDA PS2_CAPS_FLAG
    EOR #1
    STA PS2_CAPS_FLAG
    LDA #0              ; Return 0 (don't pass to app)
    RTS

@SET_SHIFT:
    LDA #1
    STA PS2_SHIFT_FLAG
    LDA #0              ; Return 0
    RTS

@NOT_CAPS:
    ; Lookup ASCII in translation table
    TAX                 ; Scancode → index
    LDA PS2_XLAT_TABLE,X
    BEQ @UNMAPPED       ; 0 = unmapped key
    STA TEMP            ; Save ASCII

    ; Apply uppercase if Shift OR Caps Lock active
    LDA PS2_SHIFT_FLAG
    ORA PS2_CAPS_FLAG
    BEQ @NO_UPPERCASE

    ; Check if letter (a-z: 0x61-0x7A)
    LDA TEMP
    CMP #$61            ; 'a'
    BCC @NO_UPPERCASE
    CMP #$7B            ; 'z' + 1
    BCS @NO_UPPERCASE

    ; Convert to uppercase (subtract 0x20)
    SEC
    SBC #$20
    RTS

@NO_UPPERCASE:
    LDA TEMP            ; Return unmodified
    RTS

@UNMAPPED:
    LDA #0              ; Return 0 for unmapped keys
    RTS
```

**State Diagram**:
```
Scancode → Extended? → Modifier? → Lookup → Letter? → Shift/Caps? → ASCII
              ↓            ↓          ↓         ↓          ↓
             0xE0?       0x12/      Table     a-z?      Flag set?
                         0x59/                            ↓
                         0x58?                      Uppercase
                            ↓                       (ASCII - 0x20)
                      Set flags,
                      return 0
```

### Break Code Handling

Break codes (key releases) are handled specially:

```assembly
; In CHRIN @READ_PS2:
LDA PS2_DATA
CMP #$F0              ; Break code prefix?
BNE @NOT_BREAK
; Set break flag and get next scancode
LDA #1
STA PS2_BREAK
JMP CHRIN             ; Recursively read next byte

@NOT_BREAK:
; Check if this is a break code
LDA PS2_BREAK
BNE @IS_BREAK
; Make code - translate normally
JSR PS2_TO_ASCII
RTS

@IS_BREAK:
; Release - check if Shift key
PLA                   ; Restore scancode
CMP #$12              ; Left Shift
BEQ @CLEAR_SHIFT
CMP #$59              ; Right Shift
BEQ @CLEAR_SHIFT
; Other key - ignore release, get next char
LDA #0
STA PS2_BREAK
JMP CHRIN

@CLEAR_SHIFT:
LDA #0
STA PS2_SHIFT_FLAG
STA PS2_BREAK
JMP CHRIN
```

## Hardware Interfaces

### UART Registers ($C000-$C001)

```
$C000: UART_DATA    (R/W) - Transmit/Receive data register
$C001: UART_STATUS  (R)   - Status register
       Bit 0: TX ready (1 = can transmit)
       Bit 1: RX ready (1 = data available)
```

**Read Sequence**:
```assembly
@WAIT_RX:
    LDA UART_STATUS
    AND #$02
    BEQ @WAIT_RX
    LDA UART_DATA       ; Read clears RX ready flag
```

**Write Sequence**:
```assembly
@WAIT_TX:
    LDA UART_STATUS
    AND #$01
    BEQ @WAIT_TX
    STA UART_DATA       ; Write starts transmission
```

### PS/2 Registers ($C200-$C201)

```
$C200: PS2_DATA     (R) - Scancode data register
$C201: PS2_STATUS   (R) - Status register
       Bit 0: Data ready (1 = scancode available)
       Bit 1: Interrupt flag (not used in polling mode)
```

**Read Sequence**:
```assembly
@WAIT_PS2:
    LDA PS2_STATUS
    AND #$01
    BEQ @WAIT_PS2
    LDA PS2_DATA        ; Read clears data ready flag
```

### GPU Registers ($C010-$C016)

```
$C010: GPU_CHAR_DATA  (W) - Character data register
$C011: GPU_CURSOR_ROW (R/W) - Cursor row (0-29)
$C012: GPU_CURSOR_COL (R/W) - Cursor column (0-39/79)
$C013: GPU_CONTROL    (R/W) - Control register
$C014: GPU_FG_COLOR   (R/W) - Foreground color (3-bit RGB)
$C015: GPU_BG_COLOR   (R/W) - Background color (3-bit RGB)
$C016: GPU_STATUS     (R)   - Status register
```

**Write Sequence**:
```assembly
LDA #'A'
STA GPU_CHAR_DATA     ; Character appears, cursor advances
```

**Note**: GPU character output is non-blocking and auto-advancing. The hardware automatically:
1. Displays character at current cursor position
2. Advances cursor to next position
3. Scrolls screen if cursor exceeds bottom-right

## Configuration Commands

### I Command - Set I/O Mode

**Syntax**: `I <input_mode> <output_mode>`

**Parameters**:
- `input_mode`: 0 (UART), 1 (PS/2), 2 (Both)
- `output_mode`: 0 (UART), 1 (Display), 2 (Both)

**Examples**:
```
I 0 0    ; UART input and output (default)
I 1 1    ; PS/2 input, Display output (standalone mode)
I 2 2    ; Both inputs, both outputs (debug mode)
I 0 1    ; UART input, Display output
I 1 0    ; PS/2 input, UART output
```

**Implementation**:
```assembly
CMD_IO_CONFIG:
    JSR SKIP_SPACES
    LDA TEMP              ; First digit from SKIP_SPACES
    JSR READ_HEX_NIBBLE
    BCS @INVALID_INPUT
    CMP #3
    BCS @INVALID_INPUT    ; Must be 0, 1, or 2
    STA VALUE             ; Save input mode

    JSR SKIP_SPACES
    LDA TEMP              ; Second digit
    JSR READ_HEX_NIBBLE
    BCS @INVALID_OUTPUT
    CMP #3
    BCS @INVALID_OUTPUT
    STA IO_OUTPUT_MODE
    LDA VALUE
    STA IO_INPUT_MODE

    JSR PRINT_IO_CONFIG_CONFIRM
    JMP MAIN_LOOP
```

**Confirmation Message**:
```
I/O Config: IN=UART, OUT=UART
I/O Config: IN=PS2, OUT=Display
I/O Config: IN=Both, OUT=Both
```

### S Command - Display Status

**Syntax**: `S`

**Output**:
```
I/O Status:
  Input:  UART
  Output: UART
Peripherals:
  UART:    9600 baud, TX ready, RX empty
  PS/2:    No data
  Display: Ready
```

**Mode Examples**:
```
# Mode 0-0 (UART only)
  Input:  UART
  Output: UART

# Mode 1-1 (PS/2 + Display)
  Input:  PS/2
  Output: Display

# Mode 2-2 (Both)
  Input:  UART + PS/2
  Output: UART + Display
```

## Flow Control Integration

### XON Character Transmission

When reading from UART (modes 0 or 2), `CHRIN` sends an XON character ($11, Ctrl-Q) after processing each character to signal readiness for the next character:

```assembly
SEND_XON:
    ; Only send if IO_INPUT_MODE includes UART (0 or 2)
    PHA
    LDA IO_INPUT_MODE
    CMP #1              ; PS/2 only?
    BEQ @SKIP_XON       ; Don't send XON
@WAIT_TX:
    LDA UART_STATUS
    AND #$01
    BEQ @WAIT_TX
    LDA #$11            ; XON character
    STA UART_DATA
@SKIP_XON:
    PLA
    RTS
```

**Purpose**: Enables reliable pasting of BASIC programs and other multi-line text via UART by preventing buffer overruns in the terminal emulator.

See [Flow Control Documentation](flow_control.md) for details.

## Use Cases

### Use Case 1: Development with UART Terminal

**Configuration**: `I 0 0` (default)
- Input: UART (keyboard via terminal emulator)
- Output: UART (text on terminal emulator)

**Advantages**:
- Direct connection to development PC
- Copy/paste support for BASIC programs
- XMODEM binary uploads
- Terminal logging and capture

### Use Case 2: Standalone Operation

**Configuration**: `I 1 1`
- Input: PS/2 keyboard
- Output: HDMI display

**Advantages**:
- No PC required
- Traditional retro computer experience
- PS/2 keyboard feels authentic
- HDMI display for visual output

### Use Case 3: Debug Mode

**Configuration**: `I 2 2`
- Input: UART + PS/2 (either source)
- Output: UART + Display (simultaneous)

**Advantages**:
- View output on both devices
- Switch between input sources seamlessly
- Monitor serial traffic while using keyboard
- Best for debugging I/O issues

### Use Case 4: BASIC Development

**Configuration**: `I 0 1`
- Input: UART (for pasting programs)
- Output: Display (for viewing results)

**Advantages**:
- Paste BASIC programs from PC
- View results on large HDMI display
- Best of both worlds for development

### Use Case 5: Serial Capture

**Configuration**: `I 1 0`
- Input: PS/2 keyboard
- Output: UART (for logging)

**Advantages**:
- Capture all output to PC for logging
- Use PS/2 keyboard for comfortable typing
- Record session for documentation

## Performance Characteristics

### Polling Overhead

**UART Polling** (Mode 0):
- Single device poll: ~10 cycles per iteration
- Blocking wait until data available
- Minimal overhead

**PS/2 Polling** (Mode 1):
- Single device poll: ~10 cycles per iteration
- Additional scancode translation: ~50-100 cycles
- Modifier key handling: ~20-30 cycles

**Dual Polling** (Mode 2):
- Two device polls: ~20 cycles per iteration
- First-come-first-served priority
- UART checked first for reliability

### Character Throughput

**UART Input**: Limited by baud rate (9600 baud = 960 bytes/sec max)

**PS/2 Input**: Limited by typing speed (~5 chars/sec typical, ~50 chars/sec max)

**Display Output**: Non-blocking write, hardware auto-advance (~1 cycle/char overhead)

**UART Output**: Blocking on TX ready, limited by baud rate (9600 baud = 960 bytes/sec max)

## Memory Usage

### Zero Page Variables (7 bytes)

```
$21: IO_INPUT_MODE      ; 1 byte
$22: IO_OUTPUT_MODE     ; 1 byte
$2A: PS2_SHIFT_FLAG     ; 1 byte
$2B: PS2_CAPS_FLAG      ; 1 byte
$05: PS2_BREAK          ; 1 byte (shared with other uses)
$00-$04: TEMP variables ; 5 bytes (shared with monitor)
```

### RAM Buffers (128 bytes)

```
$0280-$02FF: PS2_XLAT_TABLE (128 bytes)
```

### ROM Code Size

Approximate sizes:
- CHRIN enhancement: ~150 bytes
- CHROUT enhancement: ~80 bytes
- PS2_TO_ASCII function: ~120 bytes
- CMD_IO_CONFIG handler: ~100 bytes
- SEND_XON helper: ~30 bytes
- Configuration messages: ~150 bytes
- **Total**: ~630 bytes

## Testing

### Unit Tests

Test individual functions:
1. `PS2_TO_ASCII` with mock scancodes
2. CHRIN mode switching
3. CHROUT mode switching
4. Modifier key state tracking

### Integration Tests

Located in `tests/integration/test_io_switching.py`:

1. **test_io_mode_all_combinations**: Test all 9 mode combinations (0-2 × 0-2)
2. **test_dual_output_identical**: Verify identical output on UART and Display
3. **test_dual_input_first_come**: Verify first-come-first-served input
4. **test_ps2_translation**: Test PS/2 scancode to ASCII conversion

### Hardware Validation

1. Switch modes via `I` command
2. Type on PS/2 keyboard, observe character input
3. View output on UART terminal and HDMI display
4. Test modifier keys (Shift, Caps Lock)
5. Test special keys (Enter, Backspace, Escape)

## Limitations

### Current Implementation

- **Polling Only**: No interrupt-driven I/O (simplicity over performance)
- **No Input Buffering**: Characters processed immediately (no FIFO)
- **No Output Buffering**: Blocking on UART TX (no background transmission)
- **Limited Special Keys**: Only basic ASCII keys supported (no function keys, arrows)
- **No Dead-Key Composition**: Accented characters not supported

### Future Enhancements

- Interrupt-driven I/O for better responsiveness
- Input buffering for burst typing
- Output buffering for non-blocking UART
- Extended scancode support (arrows, function keys)
- Dead-key composition for accented characters
- Configurable key mappings

## References

- RetroCPU Monitor Firmware: `firmware/monitor/monitor.s`
- Feature Specification: `specs/004-program-loader-io-config/spec.md`
- Implementation Plan: `specs/004-program-loader-io-config/plan.md`
- PS/2 Keyboard Set 2 Scancode Table: [https://www.computer-engineering.org/ps2keyboard/scancodes2.html](https://www.computer-engineering.org/ps2keyboard/scancodes2.html)

## See Also

- [XMODEM Protocol Implementation](xmodem.md)
- [Flow Control Strategy](flow_control.md)
- [Program Loading User Guide](../user_guides/program_loading.md)
- [I/O Configuration User Guide](../user_guides/io_configuration.md)
