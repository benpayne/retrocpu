# Register Map Specification: DVI Character Display GPU

**Feature**: 003-hdmi-character-display
**Date**: 2025-12-27
**Base Address**: 0xC010-0xC01F (16 bytes)

## 1. Register Summary Table

| Address | Offset | Name | Access | Reset | Description |
|---------|--------|------|--------|-------|-------------|
| 0xC010 | 0x00 | CHAR_DATA | WO | N/A | Write character at cursor position |
| 0xC011 | 0x01 | CURSOR_ROW | RW | 0x00 | Cursor row position (0-29) |
| 0xC012 | 0x02 | CURSOR_COL | RW | 0x00 | Cursor column position (0-39/0-79) |
| 0xC013 | 0x03 | CONTROL | WO | 0x04 | Control register (mode, clear, cursor enable) |
| 0xC014 | 0x04 | FG_COLOR | RW | 0x07 | Foreground color (3-bit RGB) |
| 0xC015 | 0x05 | BG_COLOR | RW | 0x00 | Background color (3-bit RGB) |
| 0xC016 | 0x06 | STATUS | RO | varies | Status register (ready, vsync) |
| 0xC017-0xC01F | 0x07-0x0F | RESERVED | - | - | Reserved for future expansion |

## 2. Register Definitions

### 2.1 CHAR_DATA (0xC010) - Write Character

**Access**: Write-Only
**Reset Value**: N/A (write-only register)

**Description**:
Writing to this register outputs an ASCII character at the current cursor position. After writing, the cursor automatically advances to the next position (with line wrapping and scrolling as needed).

**Bit Layout**:
```
Bit:     7       6       5       4       3       2       1       0
     +-------+-------+-------+-------+-------+-------+-------+-------+
     |                   ASCII Character Code                       |
     +-------+-------+-------+-------+-------+-------+-------+-------+
```

**Bit Definitions**:
| Bits | Name | Description |
|------|------|-------------|
| 7:0 | CHAR | ASCII character code (0x00-0xFF) |

**Character Rendering Rules**:
- **Printable Characters** (0x20-0x7E): Rendered using font ROM
- **Non-Printable Characters** (0x00-0x1F, 0x7F): Rendered as placeholder glyph (solid block)
- **Extended ASCII** (0x80-0xFF): Implementation-defined (suggest placeholder glyph)

**Cursor Auto-Advance Behavior**:

1. **Normal Advance**: Cursor moves to next column
   ```
   if (current_col < max_col):
       cursor_col = cursor_col + 1
   ```

2. **Line Wrap**: At end of line, wrap to start of next line
   ```
   if (cursor_col == max_col):
       cursor_col = 0
       cursor_row = cursor_row + 1
   ```

3. **Scrolling**: At last row, trigger scroll and keep cursor at last row
   ```
   if (cursor_row == 29):
       trigger_scroll()
       cursor_row = 29  // Stay at bottom
       cursor_col = 0
   ```

**Example Usage**:
```assembly
; Write "HI" to screen
LDA #$48        ; 'H'
STA $C010       ; Write at cursor (auto-advances)
LDA #$49        ; 'I'
STA $C010       ; Write at next position
```

**Timing**: Character write completes in 1 CPU clock cycle. Display update occurs within one video frame (16.7ms).

---

### 2.2 CURSOR_ROW (0xC011) - Cursor Row Position

**Access**: Read/Write
**Reset Value**: 0x00

**Description**:
Sets or reads the cursor row position (0-29 for 30 rows of text).

**Bit Layout**:
```
Bit:     7       6       5       4       3       2       1       0
     +-------+-------+-------+-------+-------+-------+-------+-------+
     |   X   |   X   |   X   |       CURSOR_ROW (5 bits)            |
     +-------+-------+-------+-------+-------+-------+-------+-------+
```

**Bit Definitions**:
| Bits | Name | Description |
|------|------|-------------|
| 4:0 | ROW | Cursor row (0-29) |
| 7:5 | - | Reserved (read as 0, writes ignored) |

**Valid Range**: 0-29 (0x00-0x1D)
**Behavior on Invalid Value**: Values > 29 are clamped to 29

**Example Usage**:
```assembly
; Move cursor to row 10
LDA #$0A        ; Row 10
STA $C011       ; CURSOR_ROW

; Read current cursor row
LDA $C011       ; Returns current row in bits 4:0
```

**Notes**:
- Writing CURSOR_ROW does NOT trigger any side effects (no clear, no scroll)
- Subsequent CHAR_DATA write occurs at the new position
- Cursor flash state is not affected by position changes

---

### 2.3 CURSOR_COL (0xC012) - Cursor Column Position

**Access**: Read/Write
**Reset Value**: 0x00

**Description**:
Sets or reads the cursor column position (0-39 for 40-column mode, 0-79 for 80-column mode).

**Bit Layout**:
```
Bit:     7       6       5       4       3       2       1       0
     +-------+-------+-------+-------+-------+-------+-------+-------+
     |   X   |           CURSOR_COL (7 bits)                        |
     +-------+-------+-------+-------+-------+-------+-------+-------+
```

**Bit Definitions**:
| Bits | Name | Description |
|------|------|-------------|
| 6:0 | COL | Cursor column (0-39 or 0-79 depending on mode) |
| 7 | - | Reserved (read as 0, writes ignored) |

**Valid Range**:
- **40-column mode**: 0-39 (0x00-0x27)
- **80-column mode**: 0-79 (0x00-0x4F)

**Behavior on Invalid Value**: Values beyond valid range for current mode are clamped to max column.

**Example Usage**:
```assembly
; Move cursor to column 20
LDA #$14        ; Column 20
STA $C012       ; CURSOR_COL

; Position cursor at row 5, column 10
LDA #$05
STA $C011       ; Set row
LDA #$0A
STA $C012       ; Set column

; Next write to CHAR_DATA appears at (5, 10)
```

**Notes**:
- Writing CURSOR_COL does NOT trigger side effects
- Reading CURSOR_COL returns the actual cursor column value
- Value is automatically clamped based on current display mode

---

### 2.4 CONTROL (0xC013) - Control Register

**Access**: Write-Only
**Reset Value**: 0x04 (cursor enabled, 40-column mode, no clear)

**Description**:
Control register for display mode, screen clear, and cursor visibility.

**Bit Layout**:
```
Bit:     7       6       5       4       3       2       1       0
     +-------+-------+-------+-------+-------+-------+-------+-------+
     |   X   |   X   |   X   |   X   |   X   |CURSOR |  MODE | CLEAR |
     +-------+-------+-------+-------+-------+-------+-------+-------+
```

**Bit Definitions**:
| Bit | Name | Description |
|-----|------|-------------|
| 0 | CLEAR | Clear screen (self-clearing) |
| 1 | MODE | Display mode: 0=40-column, 1=80-column |
| 2 | CURSOR_EN | Cursor visibility: 0=hidden, 1=visible |
| 7:3 | - | Reserved (writes ignored) |

**Bit 0 - CLEAR (Clear Screen)**:
- **Write 1**: Trigger screen clear operation
- **Write 0**: No effect
- **Behavior**: Automatically clears after operation starts (self-clearing)
- **Effect**: All character buffer locations set to 0x20 (space), cursor moved to (0,0)
- **Duration**: ~96μs (2400 pixel clocks @ 25MHz)

**Bit 1 - MODE (Display Mode)**:
- **0**: 40-column mode (40 characters x 30 rows)
- **1**: 80-column mode (80 characters x 30 rows)
- **Side Effect**: Changing mode triggers screen clear and cursor reset to (0,0)
- **Timing**: Mode switch completes within 100ms

**Bit 2 - CURSOR_EN (Cursor Enable)**:
- **0**: Cursor hidden (not displayed)
- **1**: Cursor visible (flashing at ~1Hz)
- **Default**: Enabled (1)
- **Flash Rate**: Toggles every 30 frames (0.5 second intervals at 60Hz)

**Example Usage**:
```assembly
; Clear screen
LDA #$01        ; CLEAR bit set
STA $C013       ; Trigger clear (bit auto-clears)

; Switch to 80-column mode (clears screen automatically)
LDA #$06        ; MODE=1 (80-col), CURSOR_EN=1, CLEAR=0
STA $C013

; Switch to 40-column mode, hide cursor
LDA #$00        ; MODE=0 (40-col), CURSOR_EN=0
STA $C013

; Show cursor without changing mode
LDA #$04        ; CURSOR_EN=1, keep current mode
STA $C013
```

**Important Notes**:
- **Mode Change Behavior**: Per specification, changing MODE (bit 1) triggers automatic screen clear and cursor reset to (0,0)
- **CLEAR Bit**: Self-clearing (reads as 0 after clear operation starts)
- **Atomic Operations**: All control bits take effect simultaneously
- **Cursor Flash**: Continues running even when cursor is hidden (flash state preserved)

**Register Write Examples**:
| Value | Binary | Effect |
|-------|--------|--------|
| 0x01 | 00000001 | Clear screen only |
| 0x02 | 00000010 | Switch to 80-col mode (clears screen) |
| 0x00 | 00000000 | Switch to 40-col mode, hide cursor (clears screen) |
| 0x04 | 00000100 | Enable cursor (current mode) |
| 0x06 | 00000110 | 80-col mode, cursor enabled |
| 0x05 | 00000101 | Clear screen, cursor enabled (40-col mode) |

---

### 2.5 FG_COLOR (0xC014) - Foreground Color

**Access**: Read/Write
**Reset Value**: 0x07 (white)

**Description**:
Sets the foreground color for subsequently written characters. Uses 3-bit RGB encoding.

**Bit Layout**:
```
Bit:     7       6       5       4       3       2       1       0
     +-------+-------+-------+-------+-------+-------+-------+-------+
     |   X   |   X   |   X   |   X   |   X   |   R   |   G   |   B   |
     +-------+-------+-------+-------+-------+-------+-------+-------+
```

**Bit Definitions**:
| Bits | Name | Description |
|------|------|-------------|
| 2 | R | Red component (1=on, 0=off) |
| 1 | G | Green component (1=on, 0=off) |
| 0 | B | Blue component (1=on, 0=off) |
| 7:3 | - | Reserved (read as 0, writes masked to 3 bits) |

**Color Palette**:
| Value | RGB | Color | Name |
|-------|-----|-------|------|
| 0x00 | 000 | Black | RGB(0x00, 0x00, 0x00) |
| 0x01 | 001 | Blue | RGB(0x00, 0x00, 0xFF) |
| 0x02 | 010 | Green | RGB(0x00, 0xFF, 0x00) |
| 0x03 | 011 | Cyan | RGB(0x00, 0xFF, 0xFF) |
| 0x04 | 100 | Red | RGB(0xFF, 0x00, 0x00) |
| 0x05 | 101 | Magenta | RGB(0xFF, 0x00, 0xFF) |
| 0x06 | 110 | Yellow | RGB(0xFF, 0xFF, 0x00) |
| 0x07 | 111 | White | RGB(0xFF, 0xFF, 0xFF) |

**Bit Masking**: Upper 5 bits are masked (ignored) on write. Writing 0xFF is equivalent to 0x07 (white).

**Example Usage**:
```assembly
; Set foreground to green
LDA #$02        ; RGB 010 = green
STA $C014

; Set foreground to yellow
LDA #$06        ; RGB 110 = yellow
STA $C014

; Write "Hi" in yellow on blue
LDA #$06        ; Yellow foreground
STA $C014
LDA #$01        ; Blue background
STA $C015
LDA #$48        ; 'H'
STA $C010
LDA #$69        ; 'i'
STA $C010
```

**Notes**:
- Color change affects only **subsequently written characters**
- Existing characters on screen retain their original color
- To change color of existing text: Set new color, rewrite characters
- Reading FG_COLOR returns the current foreground color (bits 2:0)

---

### 2.6 BG_COLOR (0xC015) - Background Color

**Access**: Read/Write
**Reset Value**: 0x00 (black)

**Description**:
Sets the background color for subsequently written characters. Uses 3-bit RGB encoding (same as FG_COLOR).

**Bit Layout**:
```
Bit:     7       6       5       4       3       2       1       0
     +-------+-------+-------+-------+-------+-------+-------+-------+
     |   X   |   X   |   X   |   X   |   X   |   R   |   G   |   B   |
     +-------+-------+-------+-------+-------+-------+-------+-------+
```

**Bit Definitions**:
| Bits | Name | Description |
|------|------|-------------|
| 2 | R | Red component (1=on, 0=off) |
| 1 | G | Green component (1=on, 0=off) |
| 0 | B | Blue component (1=on, 0=off) |
| 7:3 | - | Reserved (read as 0, writes masked to 3 bits) |

**Color Palette**: Same as FG_COLOR (see 2.5)

**Example Usage**:
```assembly
; Set background to blue
LDA #$01        ; RGB 001 = blue
STA $C015

; White on black (default)
LDA #$07        ; White foreground
STA $C014
LDA #$00        ; Black background
STA $C015

; Black on white (inverted)
LDA #$00        ; Black foreground
STA $C014
LDA #$07        ; White background
STA $C015
```

**Clear Screen Behavior**:
When CLEAR command is issued (CONTROL bit 0), the screen is filled with spaces (0x20) using the **current background color**. This allows colored backgrounds:

```assembly
; Clear screen to blue background
LDA #$01        ; Blue background
STA $C015
LDA #$01        ; Clear screen
STA $C013       ; Screen now shows blue background
```

**Warning**: Setting FG_COLOR == BG_COLOR makes text invisible (but cursor still visible).

---

### 2.7 STATUS (0xC016) - Status Register

**Access**: Read-Only
**Reset Value**: 0x01 (ready, vsync state varies)

**Description**:
Provides status information about the GPU state.

**Bit Layout**:
```
Bit:     7       6       5       4       3       2       1       0
     +-------+-------+-------+-------+-------+-------+-------+-------+
     |   0   |   0   |   0   |   0   |   0   |   0   | VSYNC | READY |
     +-------+-------+-------+-------+-------+-------+-------+-------+
```

**Bit Definitions**:
| Bit | Name | Description |
|-----|------|-------------|
| 0 | READY | GPU ready for commands: 1=ready, 0=busy |
| 1 | VSYNC | Vertical sync state: 1=vsync active, 0=not in vsync |
| 7:2 | - | Reserved (read as 0) |

**Bit 0 - READY**:
- **1**: GPU is ready for register writes
- **0**: GPU is busy (during clear screen or scroll operation)
- **Usage**: Poll before issuing commands if immediate response needed
- **Typical Behavior**: Almost always 1 (busy periods are very short, ~100μs)

**Bit 1 - VSYNC**:
- **1**: Vertical sync period (VSYNC signal active)
- **0**: Not in vertical sync period
- **Usage**: Wait for vsync before bulk updates to avoid tearing
- **Duration**: VSYNC active for 2 scanlines (~63μs) per frame

**Example Usage**:
```assembly
; Wait for GPU ready
wait_ready:
    LDA $C016       ; Read STATUS
    AND #$01        ; Check READY bit
    BEQ wait_ready  ; Loop if not ready

; Wait for vsync (for flicker-free updates)
wait_vsync:
    LDA $C016       ; Read STATUS
    AND #$02        ; Check VSYNC bit
    BEQ wait_vsync  ; Loop until vsync active

; Now safe to update multiple characters without tearing
```

**Notes**:
- Reading STATUS does not cause side effects
- READY bit transitions: 1 → 0 (on clear/scroll start), 0 → 1 (on completion)
- VSYNC bit reflects real-time vsync signal state
- Polling VSYNC is optional (GPU handles updates automatically)

---

## 3. Register Interaction Examples

### 3.1 Basic Character Output

```assembly
; Write "Hello" at default position (0,0)
        LDA #$48        ; 'H'
        STA $C010
        LDA #$65        ; 'e'
        STA $C010
        LDA #$6C        ; 'l'
        STA $C010
        LDA #$6C        ; 'l'
        STA $C010
        LDA #$6F        ; 'o'
        STA $C010
; Cursor now at position (0, 5)
```

### 3.2 Positioned Text

```assembly
; Write "Hi" at row 10, column 20
        LDA #$0A        ; Row 10
        STA $C011
        LDA #$14        ; Column 20
        STA $C012
        LDA #$48        ; 'H'
        STA $C010
        LDA #$69        ; 'i'
        STA $C010
; Cursor now at position (10, 22)
```

### 3.3 Colored Text

```assembly
; Write "ERROR" in red on yellow background
        LDA #$04        ; Red foreground
        STA $C014
        LDA #$06        ; Yellow background
        STA $C015

        LDA #$45        ; 'E'
        STA $C010
        LDA #$52        ; 'R'
        STA $C010
        LDA #$52        ; 'R'
        STA $C010
        LDA #$4F        ; 'O'
        STA $C010
        LDA #$52        ; 'R'
        STA $C010

; Restore default colors
        LDA #$07        ; White foreground
        STA $C014
        LDA #$00        ; Black background
        STA $C015
```

### 3.4 Clear Screen

```assembly
; Clear screen and reset cursor
        LDA #$01        ; CLEAR bit
        STA $C013

; Optional: Wait for clear to complete
wait_clear:
        LDA $C016       ; Read STATUS
        AND #$01        ; Check READY
        BEQ wait_clear  ; Wait until ready
```

### 3.5 Mode Switch

```assembly
; Switch to 80-column mode
        LDA #$06        ; MODE=1, CURSOR_EN=1
        STA $C013
; Screen clears automatically, cursor at (0,0)

; Switch back to 40-column mode
        LDA #$04        ; MODE=0, CURSOR_EN=1
        STA $C013
; Screen clears automatically, cursor at (0,0)
```

### 3.6 Cursor Control

```assembly
; Hide cursor
        LDA #$00        ; CURSOR_EN=0, MODE=0
        STA $C013

; Show cursor
        LDA #$04        ; CURSOR_EN=1, MODE=0
        STA $C013
```

### 3.7 Flicker-Free Screen Update

```assembly
; Update multiple characters without tearing
; (Wait for vsync before writing)

wait_vsync:
        LDA $C016       ; Read STATUS
        AND #$02        ; Check VSYNC bit
        BEQ wait_vsync  ; Wait for vsync

; Now in vsync period - update screen
        LDA #$00        ; Reset cursor
        STA $C011
        STA $C012

; Write full line (40 or 80 characters)
        LDX #$00
write_loop:
        LDA message,X
        STA $C010       ; Write character
        INX
        CPX #40         ; 40 characters
        BNE write_loop

; Update completes during vsync/blanking
```

---

## 4. Memory Map in Context

### 4.1 Full Peripheral Address Space

| Address Range | Device | Description |
|---------------|--------|-------------|
| 0xC000-0xC00F | UART | Serial communication |
| 0xC010-0xC01F | GPU | Character display controller (this device) |
| 0xC020-0xCFFF | Reserved | Future peripherals |

### 4.2 GPU Register Decode Logic

```verilog
// Address decoder for GPU registers
wire gpu_select = (addr[15:4] == 12'hC01);  // 0xC010-0xC01F
wire [3:0] reg_addr = addr[3:0];            // Register offset 0-15

// Register access
wire gpu_write = gpu_select && we && phi2;  // Write on CPU clock high
wire gpu_read = gpu_select && re && phi2;   // Read on CPU clock high
```

---

## 5. Reset Behavior

On system reset (power-up or reset signal assertion):

| Register | Reset Value | Description |
|----------|-------------|-------------|
| CURSOR_ROW | 0x00 | Cursor at row 0 (top) |
| CURSOR_COL | 0x00 | Cursor at column 0 (left) |
| CONTROL | 0x04 | 40-col mode, cursor enabled, no clear |
| FG_COLOR | 0x07 | White foreground |
| BG_COLOR | 0x00 | Black background |
| Character Buffer | 0x20 (all) | All spaces (blank screen) |

**Result**: After reset, screen is blank with white-on-black cursor at top-left in 40-column mode.

---

## 6. Performance Characteristics

### 6.1 Register Access Timing

| Operation | Latency | Notes |
|-----------|---------|-------|
| Register write | 1 CPU cycle | Immediate (CPU clock domain) |
| Register read | 1 CPU cycle | Immediate (CPU clock domain) |
| Character display | 1-2 frames (16-33ms) | Video update occurs next frame |
| Clear screen | <100μs | 2400 writes @ 25MHz pixel clock |
| Mode switch | <100ms | Includes clear screen operation |
| Cursor flash | 500ms period | 30 frames on, 30 frames off |

### 6.2 Throughput

| Metric | Value | Notes |
|--------|-------|-------|
| Max character writes | ~1000 chars/sec | Limited by CPU speed, not GPU |
| Screen fill time | 2.4ms (40-col) | 1200 chars @ CPU speed |
| Screen fill time | 4.8ms (80-col) | 2400 chars @ CPU speed |
| Scroll operation | <100μs | Hardware accelerated |

---

## 7. Errata & Known Issues

### 7.1 Known Limitations

1. **Global Colors Only**: All characters on screen share same foreground/background colors
   - **Workaround**: Rewrite characters when changing colors

2. **No Per-Character Attributes**: Cannot have different colors per character
   - **Future Enhancement**: Could add attribute buffer in next version

3. **Mode Switch Clears Screen**: Cannot preserve text when switching between 40/80 column
   - **Specification Requirement**: By design (avoids reformatting complexity)

4. **No Hardware Scrolling Region**: Cannot define scrollable window
   - **Workaround**: Use manual cursor positioning for split screens

### 7.2 Edge Case Behaviors

1. **Invisible Text**: If FG_COLOR == BG_COLOR, text is invisible (cursor still visible)
   - **Prevention**: Application should validate color choices

2. **Cursor at Bottom Right**: Writing character at last position (29, 39/79) triggers scroll
   - **Behavior**: Correct per specification (auto-scroll when advancing past last row)

3. **Rapid Mode Switching**: Switching modes rapidly may result in intermediate clears
   - **Recommendation**: Wait for STATUS.READY before mode switch

---

## 8. Compliance & Standards

This register map complies with:
- **Feature Specification**: 003-hdmi-character-display (all functional requirements met)
- **6502 Memory-Mapped I/O Conventions**: Standard address decoding, single-cycle access
- **RetroCPU Constitution**: Simple, testable, well-documented design

---

**Document Version**: 1.0
**Last Updated**: 2025-12-27
**Status**: Phase 1 Design Complete
