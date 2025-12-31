# GPU Register Interface

**Memory-Mapped I/O Interface for DVI Character Display GPU**

## Memory Map

The GPU occupies 7 consecutive bytes in the memory map:

| Address | Register Name | Access | Description |
|---------|--------------|--------|-------------|
| 0xC010 | CHAR_DATA | Write | Character data register - write ASCII character to current cursor position |
| 0xC011 | STATUS | Read | Status register - GPU state and busy flags |
| 0xC012 | CONTROL | Write | Control register - commands and mode selection |
| 0xC013 | CURSOR_X | Read/Write | Cursor X position (column) |
| 0xC014 | CURSOR_Y | Read/Write | Cursor Y position (row) |
| 0xC015 | FG_COLOR | Write | Foreground color (3-bit RGB) |
| 0xC016 | BG_COLOR | Write | Background color (3-bit RGB) |

**Address Range**: 0xC010 - 0xC016 (7 bytes)

## Register Descriptions

### CHAR_DATA (0xC010) - Write Only

Writes an ASCII character to the current cursor position and automatically advances the cursor.

**Bit Layout**:
```
Bit:  7   6   5   4   3   2   1   0
     [ ASCII Character Code 0x00-0xFF ]
```

**Behavior**:
1. Character is written to character buffer at (CURSOR_Y, CURSOR_X)
2. CURSOR_X is incremented by 1
3. If CURSOR_X >= max_columns (40 or 80), wrap to next line:
   - CURSOR_X = 0
   - CURSOR_Y = CURSOR_Y + 1
4. If CURSOR_Y >= 30, scroll screen up by one line:
   - All lines move up one position
   - Bottom line is cleared (filled with spaces)
   - CURSOR_Y = 29

**Character Codes**:
- 0x20-0x7E: Printable ASCII characters
- 0x00-0x1F, 0x7F: Non-printable - display placeholder glyph
- 0x80-0xFF: Extended ASCII - display placeholder glyph

**Timing**: Write completes in 1 system clock cycle. Character appears on screen within 1 frame (16.7ms).

---

### STATUS (0xC011) - Read Only

Reports GPU status and operational state.

**Bit Layout**:
```
Bit:  7   6   5   4   3   2   1   0
     [ RESERVED  ]  │  │  │  │  │  └─ BUSY (0=ready, 1=busy)
                    │  │  │  │  └──── FRAME_SYNC (1=vsync active)
                    │  │  │  └─────── MODE (0=40col, 1=80col)
                    │  │  └────────── CURSOR_EN (0=disabled, 1=enabled)
                    │  └───────────── CURSOR_VIS (0=invisible phase, 1=visible phase)
                    └──────────────── RESERVED
```

**Bit Descriptions**:
- **Bit 0 (BUSY)**: Indicates GPU is processing a command
  - 0 = Ready for next command
  - 1 = Busy (typically only during screen clear or scroll operations)
- **Bit 1 (FRAME_SYNC)**: Vertical sync indicator
  - 1 = Currently in vsync period
  - Can be used for frame timing
- **Bit 2 (MODE)**: Current display mode
  - 0 = 40-column mode
  - 1 = 80-column mode
- **Bit 3 (CURSOR_EN)**: Cursor enable state
  - 0 = Cursor disabled
  - 1 = Cursor enabled
- **Bit 4 (CURSOR_VIS)**: Cursor flash state
  - 0 = Cursor in invisible phase
  - 1 = Cursor in visible phase
  - Toggles at ~1Hz when cursor enabled
- **Bits 5-7**: Reserved for future use (read as 0)

---

### CONTROL (0xC012) - Write Only

Issues commands and configures display mode.

**Bit Layout**:
```
Bit:  7   6   5   4   3   2   1   0
     [ RESERVED  ]  │  │  │  │  │  └─ CLEAR (1=clear screen)
                    │  │  │  │  └──── MODE (0=40col, 1=80col)
                    │  │  │  └─────── CURSOR_EN (0=disable, 1=enable)
                    │  │  └────────── RESERVED
                    │  └───────────── RESERVED
                    └──────────────── RESERVED
```

**Commands**:
- **Bit 0 (CLEAR)**: Clear screen command
  - Write 1 to clear entire screen to current background color
  - All character positions filled with spaces (0x20)
  - Cursor reset to (0, 0)
  - Auto-clears after execution (reads as 0)

- **Bit 1 (MODE)**: Display mode select
  - 0 = 40-column mode (40x30 characters)
  - 1 = 80-column mode (80x30 characters)
  - **Mode switch behavior**: Writing a different mode value:
    1. Clears screen
    2. Resets cursor to (0, 0)
    3. Applies new mode

- **Bit 2 (CURSOR_EN)**: Cursor enable/disable
  - 0 = Cursor not displayed
  - 1 = Cursor displayed and flashing at ~1Hz

**Usage Example**:
```assembly
; Clear screen
LDA #$01
STA $C012

; Switch to 80-column mode (will clear screen automatically)
LDA #$02
STA $C012

; Enable cursor
LDA #$04
STA $C012

; Enable cursor AND 80-column mode
LDA #$06
STA $C012
```

---

### CURSOR_X (0xC013) - Read/Write

Current cursor X position (column).

**Bit Layout**:
```
Bit:  7   6   5   4   3   2   1   0
     [ Column Position 0-79 ]
```

**Range**:
- 40-column mode: 0-39 (values 40-255 clamped to 39)
- 80-column mode: 0-79 (values 80-255 clamped to 79)

**Behavior**:
- **Write**: Sets cursor column position
  - Out-of-range values are clamped to max valid column
  - Takes effect immediately for next character write
- **Read**: Returns current column position

---

### CURSOR_Y (0xC014) - Read/Write

Current cursor Y position (row).

**Bit Layout**:
```
Bit:  7   6   5   4   3   2   1   0
     [ Row Position 0-29 ]
```

**Range**: 0-29 (values 30-255 clamped to 29)

**Behavior**:
- **Write**: Sets cursor row position
  - Out-of-range values are clamped to 29
  - Takes effect immediately for next character write
- **Read**: Returns current row position

---

### FG_COLOR (0xC015) - Write Only

Foreground color for subsequently written characters.

**Bit Layout**:
```
Bit:  7   6   5   4   3   2   1   0
     [ MASKED ]  │  │  └─ R (Red bit)
                 │  └──── G (Green bit)
                 └─────── B (Blue bit)
```

**Color Values** (3-bit RGB):
| Value | Color | RGB |
|-------|-------|-----|
| 0x00 | Black | (0,0,0) |
| 0x01 | Blue | (0,0,1) |
| 0x02 | Green | (0,1,0) |
| 0x03 | Cyan | (0,1,1) |
| 0x04 | Red | (1,0,0) |
| 0x05 | Magenta | (1,0,1) |
| 0x06 | Yellow | (1,1,0) |
| 0x07 | White | (1,1,1) |

**Behavior**:
- Only bits 0-2 are used
- Bits 3-7 are masked and ignored
- Color applies to all subsequently written characters
- Does NOT affect existing characters on screen
- Default on reset: 0x07 (White)

---

### BG_COLOR (0xC016) - Write Only

Background color for subsequently written characters and screen clear operations.

**Bit Layout**: Same as FG_COLOR

**Behavior**:
- Only bits 0-2 are used
- Bits 3-7 are masked and ignored
- Color applies to:
  - Background of subsequently written characters
  - Fill color for screen clear operations
  - Background of scrolled-in lines
- Does NOT affect existing characters on screen
- Default on reset: 0x00 (Black)

---

## Usage Patterns

### Write a String

```assembly
; Write "HELLO" at current position
        LDA #$48        ; 'H'
        STA $C010
        LDA #$45        ; 'E'
        STA $C010
        LDA #$4C        ; 'L'
        STA $C010
        LDA #$4C        ; 'L'
        STA $C010
        LDA #$4F        ; 'O'
        STA $C010
```

### Clear Screen

```assembly
        LDA #$01        ; Clear command
        STA $C012       ; Write to CONTROL
```

### Position Cursor and Write

```assembly
        LDA #$05        ; Row 5
        STA $C014       ; Set CURSOR_Y
        LDA #$10        ; Column 16
        STA $C013       ; Set CURSOR_X
        LDA #$41        ; 'A'
        STA $C010       ; Write character
```

### Change Colors

```assembly
        LDA #$04        ; Red
        STA $C015       ; Set foreground
        LDA #$01        ; Blue
        STA $C016       ; Set background
        ; Next characters will be red on blue
```

### Switch to 80-Column Mode

```assembly
        LDA #$02        ; MODE bit set
        STA $C012       ; Switch mode (auto-clears screen)
```

---

## Clock Domain Crossing

**Important**: Register writes occur in the CPU clock domain (TBD, likely 1-25 MHz), while the GPU operates in the pixel clock domain (25.175 MHz).

**CDC Strategy**:
- All CPU writes to registers are synchronized to pixel clock domain using two-flop synchronizers
- STATUS reads are sampled from pixel clock domain signals
- Synchronization adds 2-3 pixel clock cycles of latency (~100ns)
- This latency is imperceptible for character writes and cursor updates

**Implications**:
- No CPU wait states needed for register access
- Character writes appear on screen within 1 frame (~16.7ms)
- Status reads may be delayed by 2-3 pixel clocks (~100ns)

---

## Performance Characteristics

**Character Write Rate**:
- Maximum throughput: Limited by CPU speed, not GPU
- Recommended: <1000 characters/second for smooth display
- GPU can handle burst writes up to CPU clock rate

**Clear Screen Time**:
- 40-column mode: ~38,400 pixel clocks (~1.5ms)
- 80-column mode: ~76,800 pixel clocks (~3ms)
- During clear, STATUS.BUSY = 1

**Cursor Update**:
- Position updates: Immediate (next frame)
- Flash rate: ~1Hz (0.5s visible, 0.5s invisible)

---

## Edge Cases and Special Behaviors

### Invisible Text
If FG_COLOR = BG_COLOR, text becomes invisible but system continues to function normally.

### Rapid Writes
Writing characters faster than display refresh (~60Hz) works correctly - characters are buffered in character RAM and displayed continuously.

### Mode Switch Mid-Screen
Switching modes via CONTROL clears the screen automatically, so partial content is never displayed in wrong mode.

### Cursor During Clear
Screen clear resets cursor to (0,0) and resets flash timer, so cursor appears in visible phase immediately after clear.

### Non-Printable Characters
Writing 0x00-0x1F, 0x7F, or 0x80-0xFF displays a solid block placeholder glyph, allowing debug visibility of any character code.

---

## See Also

- [Character Rendering Pipeline](character_rendering.md)
- [DVI Timing](dvi_timing.md)
- [Clock Domain Crossing](../timing/clock_domains.md)
- [VGA Timing Specification](../timing/vga_640x480_60hz.md)
