# Contract: PS/2 Scancode to ASCII Translation

**Component**: Monitor Firmware - PS/2 Input Handler
**Interface Type**: Internal Function
**Version**: 1.0
**Date**: 2026-01-01

## Purpose

Defines the translation layer between PS/2 Scancode Set 2 (from ps2_wrapper.v hardware) and ASCII characters for monitor input processing.

## Interface

### Function: PS2_TO_ASCII

**Input**:
- A register: PS/2 scancode byte (from PS2_DATA register at $C200)
- Zero page state: `PS2_BREAK` flag, `PS2_SHIFT` flag, `PS2_CAPS` flag

**Output**:
- A register: ASCII character (or 0x00 if scancode should be ignored)

**Side Effects**:
- May update `PS2_BREAK`, `PS2_SHIFT`, `PS2_CAPS` flags in zero page

**Usage**:
```asm
    LDA PS2_DATA        ; Read scancode from hardware
    JSR PS2_TO_ASCII    ; Convert to ASCII
    BEQ .ignore         ; If A == 0, ignore (modifier key or break code)
    ; Process ASCII character in A
```

## State Variables (Zero Page)

```
$05: PS2_BREAK  - Break code flag (0 = make code next, 1 = break code next)
$2A: PS2_SHIFT  - Shift key state (0 = not pressed, 1 = pressed)
$2B: PS2_CAPS   - Caps Lock state (0 = off, 1 = on)
```

**Initial Values** (after RESET):
```
PS2_BREAK = 0
PS2_SHIFT = 0
PS2_CAPS  = 0
```

## Scancode Set 2 Mapping

### Special Scancodes

| Scancode | Meaning | Action |
|----------|---------|--------|
| 0xF0 | Break prefix | Set PS2_BREAK = 1, return 0x00 |
| 0xE0 | Extended prefix | Ignore (future: handle extended keys) |

### Modifier Keys

| Key | Make Scancode | Break Scancode | Action |
|-----|---------------|----------------|--------|
| Left Shift | 0x12 | 0xF0 0x12 | Make: Set PS2_SHIFT = 1, Break: Clear PS2_SHIFT = 0 |
| Right Shift | 0x59 | 0xF0 0x59 | Make: Set PS2_SHIFT = 1, Break: Clear PS2_SHIFT = 0 |
| Caps Lock | 0x58 | 0xF0 0x58 | Make: Toggle PS2_CAPS, Break: Ignore |

**Return Value**: 0x00 (do not pass modifier keys to application)

### Printable Characters (Unshifted)

#### Letters (a-z)

| Key | Scancode | ASCII (Unshifted) | ASCII (Shifted/Caps) |
|-----|----------|-------------------|----------------------|
| A | 0x1C | 0x61 ('a') | 0x41 ('A') |
| B | 0x32 | 0x62 ('b') | 0x42 ('B') |
| C | 0x21 | 0x63 ('c') | 0x43 ('C') |
| D | 0x23 | 0x64 ('d') | 0x44 ('D') |
| E | 0x24 | 0x65 ('e') | 0x45 ('E') |
| F | 0x2B | 0x66 ('f') | 0x46 ('F') |
| G | 0x34 | 0x67 ('g') | 0x47 ('G') |
| H | 0x33 | 0x68 ('h') | 0x48 ('H') |
| I | 0x43 | 0x69 ('i') | 0x49 ('I') |
| J | 0x3B | 0x6A ('j') | 0x4A ('J') |
| K | 0x42 | 0x6B ('k') | 0x4B ('K') |
| L | 0x4B | 0x6C ('l') | 0x4C ('L') |
| M | 0x3A | 0x6D ('m') | 0x4D ('M') |
| N | 0x31 | 0x6E ('n') | 0x4E ('N') |
| O | 0x44 | 0x6F ('o') | 0x4F ('O') |
| P | 0x4D | 0x70 ('p') | 0x50 ('P') |
| Q | 0x15 | 0x71 ('q') | 0x51 ('Q') |
| R | 0x2D | 0x72 ('r') | 0x52 ('R') |
| S | 0x1B | 0x73 ('s') | 0x53 ('S') |
| T | 0x2C | 0x74 ('t') | 0x54 ('T') |
| U | 0x3C | 0x75 ('u') | 0x55 ('U') |
| V | 0x2A | 0x76 ('v') | 0x56 ('V') |
| W | 0x1D | 0x77 ('w') | 0x57 ('W') |
| X | 0x22 | 0x78 ('x') | 0x58 ('X') |
| Y | 0x35 | 0x79 ('y') | 0x59 ('Y') |
| Z | 0x1A | 0x7A ('z') | 0x5A ('Z') |

#### Numbers (0-9)

| Key | Scancode | ASCII (Unshifted) | ASCII (Shifted) |
|-----|----------|-------------------|-----------------|
| 0 | 0x45 | 0x30 ('0') | 0x29 (')') |
| 1 | 0x16 | 0x31 ('1') | 0x21 ('!') |
| 2 | 0x1E | 0x32 ('2') | 0x40 ('@') |
| 3 | 0x26 | 0x33 ('3') | 0x23 ('#') |
| 4 | 0x25 | 0x34 ('4') | 0x24 ('$') |
| 5 | 0x2E | 0x35 ('5') | 0x25 ('%') |
| 6 | 0x36 | 0x36 ('6') | 0x5E ('^') |
| 7 | 0x3D | 0x37 ('7') | 0x26 ('&') |
| 8 | 0x3E | 0x38 ('8') | 0x2A ('*') |
| 9 | 0x46 | 0x39 ('9') | 0x28 ('(') |

#### Punctuation and Symbols

| Key | Scancode | ASCII (Unshifted) | ASCII (Shifted) |
|-----|----------|-------------------|-----------------|
| Space | 0x29 | 0x20 (' ') | 0x20 (' ') |
| - | 0x4E | 0x2D ('-') | 0x5F ('_') |
| = | 0x55 | 0x3D ('=') | 0x2B ('+') |
| [ | 0x54 | 0x5B ('[') | 0x7B ('{') |
| ] | 0x5B | 0x5D (']') | 0x7D ('}') |
| \\ | 0x5D | 0x5C ('\\') | 0x7C ('\|') |
| ; | 0x4C | 0x3B (';') | 0x3A (':') |
| ' | 0x52 | 0x27 ('\'') | 0x22 ('"') |
| , | 0x41 | 0x2C (',') | 0x3C ('<') |
| . | 0x49 | 0x2E ('.') | 0x3E ('>') |
| / | 0x4A | 0x2F ('/') | 0x3F ('?') |
| ` | 0x0E | 0x60 ('\`') | 0x7E ('~') |

### Control Characters

| Key | Scancode | ASCII | Description |
|-----|----------|-------|-------------|
| Enter | 0x5A | 0x0D | Carriage Return (CR) |
| Backspace | 0x66 | 0x08 | Backspace (BS) |
| Tab | 0x0D | 0x09 | Horizontal Tab (HT) |
| Escape | 0x76 | 0x1B | Escape (ESC) |

**Note**: Shift state does not affect control characters (Enter always returns 0x0D, etc.)

## Translation Algorithm

### Pseudocode

```
function PS2_TO_ASCII(scancode):
    # Handle break code prefix
    if scancode == 0xF0:
        PS2_BREAK = 1
        return 0x00

    # Handle extended code prefix (ignore for now)
    if scancode == 0xE0:
        return 0x00

    # Handle modifier keys
    if PS2_BREAK == 1:
        # Break code (key released)
        if scancode == 0x12 or scancode == 0x59:  # Shift keys
            PS2_SHIFT = 0
        PS2_BREAK = 0
        return 0x00
    else:
        # Make code (key pressed)
        if scancode == 0x12 or scancode == 0x59:  # Shift keys
            PS2_SHIFT = 1
            return 0x00
        if scancode == 0x58:  # Caps Lock
            PS2_CAPS = PS2_CAPS XOR 1  # Toggle
            return 0x00

    # Lookup ASCII in translation table
    ascii = PS2_XLAT_TABLE[scancode]

    # If table returns 0, scancode is unmapped
    if ascii == 0x00:
        return 0x00

    # Apply shift/caps lock for letters
    if (PS2_SHIFT == 1 or PS2_CAPS == 1) and ascii >= 0x61 and ascii <= 0x7A:
        # Uppercase: a-z (0x61-0x7A) → A-Z (0x41-0x5A)
        ascii = ascii - 0x20

    # Apply shift for numbers and punctuation (use shifted table entry)
    if PS2_SHIFT == 1 and ascii >= 0x30 and ascii <= 0x39:
        # Numbers: use shifted table (table should have both unshifted and shifted entries)
        ascii = PS2_XLAT_TABLE_SHIFTED[scancode]

    return ascii
```

### 6502 Assembly Implementation

```asm
PS2_TO_ASCII:
    ; Check for break code prefix (0xF0)
    CMP #$F0
    BNE @NOT_BREAK
    LDA #1
    STA PS2_BREAK
    LDA #0              ; Return 0 (ignore)
    RTS

@NOT_BREAK:
    ; Check if this is a break code (release)
    LDX PS2_BREAK
    BEQ @MAKE_CODE      ; If PS2_BREAK == 0, it's a make code

    ; Break code handling
    LDX #0
    STX PS2_BREAK       ; Clear break flag

    ; Check if it's a shift key release
    CMP #$12            ; Left Shift
    BEQ @CLEAR_SHIFT
    CMP #$59            ; Right Shift
    BEQ @CLEAR_SHIFT

    LDA #0              ; Ignore other break codes
    RTS

@CLEAR_SHIFT:
    LDX #0
    STX PS2_SHIFT
    LDA #0              ; Return 0
    RTS

@MAKE_CODE:
    ; Check for shift key press
    CMP #$12            ; Left Shift
    BEQ @SET_SHIFT
    CMP #$59            ; Right Shift
    BEQ @SET_SHIFT

    ; Check for Caps Lock toggle
    CMP #$58            ; Caps Lock
    BNE @NOT_CAPS
    LDA PS2_CAPS
    EOR #1              ; Toggle
    STA PS2_CAPS
    LDA #0              ; Return 0
    RTS

@SET_SHIFT:
    LDA #1
    STA PS2_SHIFT
    LDA #0              ; Return 0
    RTS

@NOT_CAPS:
    ; Lookup ASCII in table (scancode in A)
    TAX                 ; Use scancode as index
    LDA PS2_XLAT_TABLE,X
    BEQ @UNMAPPED       ; If 0, scancode not mapped

    ; Apply uppercase for letters if Shift or Caps Lock
    TAY                 ; Save ASCII
    LDA PS2_SHIFT
    ORA PS2_CAPS        ; A = 1 if either Shift or Caps
    BEQ @NO_UPPERCASE

    ; Check if letter (a-z: 0x61-0x7A)
    TYA                 ; Restore ASCII
    CMP #$61
    BCC @NO_UPPERCASE   ; Less than 'a'
    CMP #$7B
    BCS @NO_UPPERCASE   ; Greater than 'z'

    ; Uppercase: subtract 0x20
    SEC
    SBC #$20
    RTS

@NO_UPPERCASE:
    TYA                 ; Restore ASCII
    RTS

@UNMAPPED:
    LDA #0              ; Return 0 for unmapped scancodes
    RTS
```

## Lookup Table Structure

### Table: PS2_XLAT_TABLE ($0280-$02FF, 128 bytes)

**Index**: PS/2 scancode (0x00-0x7F)
**Value**: ASCII character (unshifted) or 0x00 if unmapped

**Example Entries**:
```
$0280: .byte $00, $00, $00, $00, $00, $00, $00, $00  ; 0x00-0x07 (unmapped)
$0288: .byte $00, $00, $00, $00, $00, $09, $60, $00  ; 0x08-0x0F (0x0D=Tab, 0x0E=`)
$0290: .byte $00, $00, $00, $00, $00, $71, $31, $00  ; 0x10-0x17 (0x15='q', 0x16='1')
$0298: .byte $00, $00, $7A, $73, $61, $77, $32, $00  ; 0x18-0x1F (z,s,a,w,2)
...
$02C8: .byte $00, $6D, $6A, $75, $37, $38, $00, $00  ; 0x40-0x47 (m,j,u,7,8)
...
```

**Note**: For simplicity, this table contains unshifted ASCII only. Shifted characters (e.g., '!' for '1') are handled algorithmically or via a second table.

### Alternative: Dual Tables (Unshifted + Shifted)

If algorithmic shift handling is complex, use two tables:

- `PS2_XLAT_TABLE` ($0280-$02FF): Unshifted ASCII
- `PS2_XLAT_TABLE_SHIFTED` ($0300-$037F): Shifted ASCII

Lookup shifted table when PS2_SHIFT == 1 for non-letter keys.

## Testing Contract

### Test Case 1: Simple Character Input

**Steps**:
1. Configure I/O: `I 1 0` (PS/2 input, UART output for verification)
2. Press 'A' key on PS/2 keyboard

**Expected**:
- PS2_DATA = 0x1C (scancode for 'A')
- PS2_TO_ASCII(0x1C) returns 0x61 ('a')
- Monitor receives 'a' via CHRIN

### Test Case 2: Shifted Character (Uppercase)

**Steps**:
1. Hold Left Shift (scancode 0x12)
2. Press 'A' key (scancode 0x1C)
3. Release 'A' (0xF0 0x1C)
4. Release Shift (0xF0 0x12)

**Expected**:
- Step 1: PS2_TO_ASCII(0x12) sets PS2_SHIFT = 1, returns 0x00
- Step 2: PS2_TO_ASCII(0x1C) returns 0x41 ('A') because PS2_SHIFT = 1
- Step 3: PS2_TO_ASCII(0xF0) sets PS2_BREAK = 1; PS2_TO_ASCII(0x1C) clears PS2_BREAK, returns 0x00
- Step 4: PS2_TO_ASCII(0xF0) sets PS2_BREAK = 1; PS2_TO_ASCII(0x12) clears PS2_SHIFT and PS2_BREAK, returns 0x00

### Test Case 3: Caps Lock Toggle

**Steps**:
1. Press Caps Lock (0x58)
2. Press 'a' (0x1C)
3. Press Caps Lock again (0x58)
4. Press 'a' (0x1C)

**Expected**:
- Step 1: PS2_TO_ASCII(0x58) toggles PS2_CAPS to 1, returns 0x00
- Step 2: PS2_TO_ASCII(0x1C) returns 0x41 ('A') because PS2_CAPS = 1
- Step 3: PS2_TO_ASCII(0x58) toggles PS2_CAPS to 0, returns 0x00
- Step 4: PS2_TO_ASCII(0x1C) returns 0x61 ('a') because PS2_CAPS = 0

### Test Case 4: Control Characters

**Steps**:
1. Press Enter key (0x5A)

**Expected**:
- PS2_TO_ASCII(0x5A) returns 0x0D (CR)
- Monitor processes as newline/command terminator

### Test Case 5: Unmapped Scancode

**Steps**:
1. Press function key (e.g., F1 = 0x05)

**Expected**:
- PS2_TO_ASCII(0x05) looks up PS2_XLAT_TABLE[0x05] = 0x00
- Returns 0x00 (ignore)
- No character passed to monitor

## Dependencies

- **PS/2 Hardware**: ps2_wrapper.v providing scancode FIFO at $C200
- **Zero Page RAM**: Variables at $05, $2A, $2B
- **ROM Space**: Lookup table at $0280-$02FF (128 bytes in ROM or copied to RAM at startup)

## Future Enhancements

- Extended scancodes (0xE0 prefix) for arrow keys, Insert, Delete, Home, End, etc.
- Ctrl and Alt modifier key support
- International keyboard layouts (ISO/ANSI variants)
- Configurable key mapping (user-defined table)
