# GPU Register Interface

**Module**: GPU Memory-Mapped Registers
**Base Address**: 0xC010
**Date**: 2026-01-01
**Status**: Implemented and Hardware Validated

## Overview

The GPU is accessed via 7 memory-mapped registers at 0xC010-0xC016. The CPU can write characters, control the cursor, configure colors, and read status through these registers.

## Reset Values

On power-up or system reset, the GPU registers initialize to:

| Register | Default Value | Description |
|----------|---------------|-------------|
| CURSOR_ROW | 0x00 | Top row |
| CURSOR_COL | 0x00 | Leftmost column |
| CONTROL | 0x04 | 40-column mode, cursor enabled |
| FG_COLOR | 0x07 | White |
| BG_COLOR | 0x00 | Black |

**Important**: The GPU defaults to **40-column mode** (CONTROL[1]=0). To use 80-column mode, write `0x06` to CONTROL register (sets MODE_80COL and CURSOR_EN bits).

## Memory Map

| Address | Name | Access | Width | Description |
|---------|------|--------|-------|-------------|
| 0xC010 | CHAR_DATA | W | 8-bit | Character data - write ASCII to display |
| 0xC011 | CURSOR_ROW | R/W | 5-bit | Cursor row position (0-29) |
| 0xC012 | CURSOR_COL | R/W | 7-bit | Cursor column position (0-39 in 40-col, 0-79 in 80-col) |
| 0xC013 | CONTROL | W | 8-bit | Control register (clear, mode, cursor enable) |
| 0xC014 | FG_COLOR | R/W | 3-bit | Foreground color (3-bit RGB) |
| 0xC015 | BG_COLOR | R/W | 3-bit | Background color (3-bit RGB) |
| 0xC016 | STATUS | R | 8-bit | GPU status flags |

## Register Details

### 0xC010: CHAR_DATA (Write-Only)

Writes an ASCII character to the character buffer at the current cursor position.

**Behavior**:
1. ASCII code written to buffer at current cursor position
2. Cursor automatically advances to next position
3. At end of row (column 39/79), cursor wraps to column 0 of next row
4. At end of screen (row 29, last column), screen scrolls up automatically
   - All rows shift up by one (row 0 disappears, row 1→0, row 2→1, etc.)
   - New blank row appears at bottom (row 29)
   - Cursor remains at row 29, column 0
   - Implemented using circular buffer for efficiency

**Example**:
```asm
; Write 'H' to screen
LDA #$48       ; ASCII 'H'
STA $C010      ; Write to CHAR_DATA - cursor advances automatically
```

**Timing**: Character appears on display within 1-2 frames (16-33 ms @ 60 Hz)

### 0xC011: CURSOR_ROW (Read/Write)

Sets or reads the cursor row position.

**Width**: 5 bits (values 0-29, upper 3 bits ignored)
**Default**: 0 (top row)

**Write Behavior**:
- Values 0-29: Set cursor to specified row
- Values 30-31: Clamped to row 29

**Read Behavior**:
- Returns current cursor row (0-29)

**Example**:
```asm
; Move cursor to row 5
LDA #5
STA $C011      ; CURSOR_ROW = 5

; Read current row
LDA $C011      ; A now contains cursor row
```

### 0xC012: CURSOR_COL (Read/Write)

Sets or reads the cursor column position.

**Width**: 7 bits (values 0-79 in 80-col mode, upper bit ignored)
**Default**: 0 (leftmost column)

**Write Behavior**:
- Values 0-79: Set cursor to specified column (80-col mode)
- Values 0-39: Valid range in 40-col mode
- Values out of range: Clamped to max column

**Read Behavior**:
- Returns current cursor column (0-79)

**Example**:
```asm
; Move cursor to column 10
LDA #10
STA $C012      ; CURSOR_COL = 10

; Move to position (row=2, col=15)
LDA #2
STA $C011      ; Row = 2
LDA #15
STA $C012      ; Col = 15
```

### 0xC013: CONTROL (Write-Only)

Control register for GPU operations.

**Bit Map**:

| Bit | Name | Description |
|-----|------|-------------|
| 0 | CLEAR | Clear screen (write 1 to clear, auto-clears after) |
| 1 | MODE_80COL | Display mode: 0=40-column (default), 1=80-column |
| 2 | CURSOR_EN | Cursor enable: 0=hidden, 1=visible (future) |
| 3-7 | Reserved | Reserved for future use |

#### Bit 0: CLEAR

Writing 1 clears the entire screen (fills buffer with spaces, resets cursor to 0,0).

**Example**:
```asm
; Clear screen
LDA #$01       ; Bit 0 = 1
STA $C013      ; Clear screen
```

**Timing**: Clear operation completes within a few microseconds. New frame displays cleared screen within 16 ms.

#### Bit 1: MODE_80COL

Controls display mode selection between 40-column and 80-column modes.

- 0 = 40-column mode (40×30, characters doubled horizontally) **[DEFAULT]**
- 1 = 80-column mode (80×30, native character width)

**Important**: The GPU resets to 40-column mode. To use 80-column mode, write `0x06` to enable MODE_80COL and CURSOR_EN.

**Mode Switching Behavior**:
- Automatically clears entire screen (fills with spaces)
- Resets cursor position to (0, 0)
- Resets circular buffer offset (top_line = 0)

**Example**:
```asm
; Switch to 80-column mode
LDA #$06       ; Bit 1 (MODE) + Bit 2 (CURSOR_EN)
STA $C013      ; Auto-clears screen and resets cursor
```

#### Bit 2: CURSOR_EN (Future Feature)

Controls cursor visibility. **Note**: Cursor display not yet implemented.

- 0 = Cursor hidden
- 1 = Cursor visible (flashing block at cursor position)

### 0xC014: FG_COLOR (Read/Write)

Foreground (text) color in 3-bit RGB format.

**Width**: 3 bits (bits 0-2), upper 5 bits ignored
**Default**: 0x07 (white)

**Bit Map**:

| Bit | Color | Value |
|-----|-------|-------|
| 2 | Red | 1=on, 0=off |
| 1 | Green | 1=on, 0=off |
| 0 | Blue | 1=on, 0=off |

**Color Palette**:

| Value | Binary | Color Name |
|-------|--------|------------|
| 0x00 | 000 | Black |
| 0x01 | 001 | Blue |
| 0x02 | 010 | Green |
| 0x03 | 011 | Cyan |
| 0x04 | 100 | Red |
| 0x05 | 101 | Magenta |
| 0x06 | 110 | Yellow |
| 0x07 | 111 | White |

**Example**:
```asm
; Set foreground to yellow (red + green)
LDA #$06       ; Binary 110
STA $C014      ; FG_COLOR = yellow
```

### 0xC015: BG_COLOR (Read/Write)

Background color in 3-bit RGB format.

**Width**: 3 bits (bits 0-2), upper 5 bits ignored
**Default**: 0x01 (blue)

**Format**: Same as FG_COLOR (3-bit RGB)

**Example**:
```asm
; Set background to blue
LDA #$01       ; Binary 001
STA $C015      ; BG_COLOR = blue

; White text on black background
LDA #$07       ; White
STA $C014      ; FG_COLOR = white
LDA #$00       ; Black
STA $C015      ; BG_COLOR = black
```

### 0xC016: STATUS (Read-Only)

GPU status register. **Note**: Currently returns fixed value 0xC0.

**Bit Map**:

| Bit | Name | Description |
|-----|------|-------------|
| 7 | GPU_READY | 1 = GPU initialized and ready |
| 6 | PLL_LOCK | 1 = GPU PLL locked (stable clocks) |
| 5 | Reserved | Future: VBLANK flag |
| 4 | Reserved | Future: HBLANK flag |
| 3-0 | Reserved | Reserved for future use |

**Example**:
```asm
; Check if GPU is ready
LDA $C016      ; Read STATUS
AND #$80       ; Test bit 7
BEQ not_ready  ; Branch if not set
; GPU is ready...
```

## Usage Examples

### Example 1: Clear Screen and Write "HELLO"

```asm
; Clear screen
LDA #$01
STA $C013      ; Clear

; Set cursor to (0, 0) - redundant after clear, but explicit
LDA #$00
STA $C011      ; Row = 0
STA $C012      ; Col = 0

; Write "HELLO"
LDA #$48
STA $C010      ; 'H'
LDA #$45
STA $C010      ; 'E'
LDA #$4C
STA $C010      ; 'L'
STA $C010      ; 'L'
LDA #$4F
STA $C010      ; 'O'
```

### Example 2: Write String at Specific Position

```asm
; Position cursor at row 5, column 10
LDA #5
STA $C011      ; CURSOR_ROW
LDA #10
STA $C012      ; CURSOR_COL

; Write "CPU OK"
LDA #$43
STA $C010      ; 'C'
LDA #$50
STA $C010      ; 'P'
LDA #$55
STA $C010      ; 'U'
LDA #$20
STA $C010      ; ' '
LDA #$4F
STA $C010      ; 'O'
LDA #$4B
STA $C010      ; 'K'
```

### Example 3: Set Colors

```asm
; Yellow text on blue background
LDA #$06       ; Yellow (red + green)
STA $C014      ; FG_COLOR
LDA #$01       ; Blue
STA $C015      ; BG_COLOR

; Now write characters...
LDA #$48
STA $C010      ; 'H' in yellow on blue
```

### Example 4: String Write Loop

```asm
; Write string with pointer
string: .byte "RetroCPU 6502", $00

        LDX #0
loop:   LDA string,X
        BEQ done       ; End if null terminator
        STA $C010      ; Write character
        INX
        BNE loop       ; Continue if X != 0
done:   RTS
```

## Python API Example

Using the monitor D command via serial:

```python
import serial
import time

ser = serial.Serial("/dev/ttyACM0", 9600, timeout=1)

def write_char(addr, value):
    """Write to GPU register using monitor D command"""
    cmd = f"D {addr:04X} {value:02X}\r"
    ser.write(cmd.encode())
    time.sleep(0.02)

# Clear screen
write_char(0xC013, 0x01)

# Set white on blue
write_char(0xC014, 0x07)  # White foreground
write_char(0xC015, 0x01)  # Blue background

# Write "HELLO"
write_char(0xC010, ord('H'))
write_char(0xC010, ord('E'))
write_char(0xC010, ord('L'))
write_char(0xC010, ord('L'))
write_char(0xC010, ord('O'))
```

## Bus Timing

### Write Timing

The GPU registers are mapped to the CPU memory bus and use the M65C02 microcycle timing:

```
Microcycle 0-6: Address and data setup
Microcycle 7:   Write strobe (WE asserted)
                GPU samples data on rising edge of clk_cpu at MC=7
```

### Read Timing

```
Microcycle 0-6: Address setup
Microcycle 7:   GPU drives data bus
                CPU samples on rising edge at MC=7
```

## Clock Domain Crossing

The registers operate in the CPU clock domain (25 MHz) and provide data to the pixel clock domain (25 MHz). Although nominally the same frequency, these clocks are asynchronous (from different PLLs).

**Synchronization strategy**:
- Color registers (FG_COLOR, BG_COLOR): Direct async read (stable values, glitches acceptable for 1 pixel)
- Cursor position: Direct async read (stable values between writes)
- Character buffer: Dual-port RAM handles CDC automatically (separate read/write ports)

## CPU-GPU Performance

### Write Performance

- **Character write latency**: ~40 ns (1 CPU clock cycle)
- **Maximum write rate**: 25 million characters/second (far exceeds display rate)
- **Practical write rate**: Limited by software loop overhead (~100k chars/sec typical)

### Display Update Latency

- **Frame time**: 16.67 ms (60 Hz)
- **Character-to-display latency**: 0-16.67 ms (depends on when in frame written)
- **Worst case**: Character written just after scanline rendered, visible next frame

## Hardware Implementation

### Module Hierarchy

```
gpu_top.v
├── gpu_core.v
│   ├── gpu_registers.v (this interface)
│   ├── character_buffer.v
│   ├── character_renderer.v
│   └── font_rom.v
├── vga_timing_generator.v
└── dvi_transmitter.v
```

### Address Decoder Integration

In `address_decoder.v`:

```verilog
// GPU chip select: 0xC010-0xC01F
wire gpu_cs = (addr[15:4] == 12'hC01);
```

The lower 4 bits (addr[3:0]) select the specific register within the GPU.

### Register File

In `gpu_registers.v`:

```verilog
// Register addresses (lower 4 bits of address)
localparam ADDR_CHAR_DATA  = 4'h0;  // 0xC010
localparam ADDR_CURSOR_ROW = 4'h1;  // 0xC011
localparam ADDR_CURSOR_COL = 4'h2;  // 0xC012
localparam ADDR_CONTROL    = 4'h3;  // 0xC013
localparam ADDR_FG_COLOR   = 4'h4;  // 0xC014
localparam ADDR_BG_COLOR   = 4'h5;  // 0xC015
localparam ADDR_STATUS     = 4'h6;  // 0xC016
```

## Future Enhancements

### Phase 5: Screen Control (Planned)

- **Auto-scroll**: When cursor reaches (29, 79), scroll screen up one line
- **CONTROL register expansion**: Full support for MODE_80COL and CURSOR_EN bits

### Phase 6: Additional Features (Planned)

- **Hardware cursor**: Flashing block cursor at current position (~1 Hz blink rate)
- **40-column mode**: Larger characters for easier reading (16 pixels wide)
- **Line wrap control**: Option to disable auto-advance

### Status Register Expansion (Future)

- **Bit 5 (VBLANK)**: 1 during vertical blanking (safe time for bulk updates)
- **Bit 4 (HBLANK)**: 1 during horizontal blanking
- **Bit 3 (SCROLL_BUSY)**: 1 while auto-scroll in progress

## Validation Status

### Hardware Tested

- ✅ CHAR_DATA writes characters correctly
- ✅ CURSOR_ROW/COL position cursor
- ✅ CONTROL[0] clears screen
- ✅ FG_COLOR/BG_COLOR set display colors
- ✅ STATUS returns 0xC0 (GPU ready)
- ✅ Auto-advance after CHAR_DATA write
- ✅ Python monitor scripts working

### Pending Features

- ⏳ Auto-scroll at screen bottom
- ⏳ 40-column mode switching
- ⏳ Hardware cursor display
- ⏳ VBLANK/HBLANK status flags

## References

- Character rendering pipeline: `docs/modules/character_rendering.md`
- GPU specification: `specs/003-hdmi-character-display/spec.md`
- Hardware validation: `tests/integration/test_gpu_character_output.py`
- Python examples: `temp/test_gpu_demo.py`
