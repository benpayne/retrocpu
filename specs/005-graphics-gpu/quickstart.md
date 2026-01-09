# Quick Start Guide: Graphics Mode GPU

**Feature**: 005-graphics-gpu
**Audience**: Beginners and intermediate programmers
**Date**: 2026-01-04

This guide shows you how to display bitmap graphics on the Graphics GPU in 3 simple steps.

---

## Overview

The Graphics GPU adds three bitmap graphics modes to your retro computer:
- **1 BPP**: 320×200 monochrome (black and white)
- **2 BPP**: 160×200 with 4 custom colors
- **4 BPP**: 160×100 with 16 custom colors

All modes use an 8KB framebuffer stored in VRAM (video RAM), which you access via memory-mapped registers.

---

## Prerequisites

- CPU running and connected to GPU registers at 0xC100-0xC10F
- Display output connected (HDMI/DVI)
- Character GPU working (optional - we'll switch to graphics mode)

---

## Step-by-Step: Display Your First Bitmap

### Step 1: Set Graphics Mode

Choose which graphics mode you want:

```assembly
; Option A: 1 BPP mode (320×200 monochrome)
LDA #$00
STA $C106      ; GPU_MODE = 00 (1 BPP)

; Option B: 2 BPP mode (160×200, 4 colors)
LDA #$01
STA $C106      ; GPU_MODE = 01 (2 BPP)

; Option C: 4 BPP mode (160×100, 16 colors) ← Most colorful!
LDA #$02
STA $C106      ; GPU_MODE = 10 (4 BPP)
```

**For this example, we'll use 4 BPP mode** (16 colors).

---

### Step 2: Program the Color Palette

In 2 BPP and 4 BPP modes, you need to define what colors palette indices 0-15 represent.

```assembly
; Define palette entry 0: Black (RGB = 0, 0, 0)
LDA #$00
STA $C107      ; CLUT_INDEX = 0
LDA #$00
STA $C108      ; Red = 0
STA $C109      ; Green = 0
STA $C10A      ; Blue = 0

; Define palette entry 1: Bright Red (RGB = 15, 0, 0)
LDA #$01
STA $C107      ; CLUT_INDEX = 1
LDA #$0F
STA $C108      ; Red = 15 (max)
LDA #$00
STA $C109      ; Green = 0
STA $C10A      ; Blue = 0

; Define palette entry 2: Bright Green (RGB = 0, 15, 0)
LDA #$02
STA $C107      ; CLUT_INDEX = 2
LDA #$00
STA $C108      ; Red = 0
LDA #$0F
STA $C109      ; Green = 15 (max)
LDA #$00
STA $C10A      ; Blue = 0

; Define palette entry 3: Bright Blue (RGB = 0, 0, 15)
LDA #$03
STA $C107      ; CLUT_INDEX = 3
LDA #$00
STA $C108      ; Red = 0
STA $C109      ; Green = 0
LDA #$0F
STA $C10A      ; Blue = 15 (max)

; Define palette entry 4: Yellow (RGB = 15, 15, 0)
LDA #$04
STA $C107      ; CLUT_INDEX = 4
LDA #$0F
STA $C108      ; Red = 15
STA $C109      ; Green = 15
LDA #$00
STA $C10A      ; Blue = 0

; Define palette entry 5: Magenta (RGB = 15, 0, 15)
LDA #$05
STA $C107      ; CLUT_INDEX = 5
LDA #$0F
STA $C108      ; Red = 15
LDA #$00
STA $C109      ; Green = 0
LDA #$0F
STA $C10A      ; Blue = 15

; Define palette entry 6: Cyan (RGB = 0, 15, 15)
LDA #$06
STA $C107      ; CLUT_INDEX = 6
LDA #$00
STA $C108      ; Red = 0
LDA #$0F
STA $C109      ; Green = 15
STA $C10A      ; Blue = 15

; Define palette entry 7: White (RGB = 15, 15, 15)
LDA #$07
STA $C107      ; CLUT_INDEX = 7
LDA #$0F
STA $C108      ; Red = 15
STA $C109      ; Green = 15
STA $C10A      ; Blue = 15

; Entries 8-15: Define more colors or leave as default grayscale
```

**Palette Summary** (RGB444 values):
```
0: Black     (0,0,0)
1: Red       (F,0,0)
2: Green     (0,F,0)
3: Blue      (0,0,F)
4: Yellow    (F,F,0)
5: Magenta   (F,0,F)
6: Cyan      (0,F,F)
7: White     (F,F,F)
8-15: Grayscale (default)
```

---

### Step 3: Write Pixel Data to VRAM

Now fill the framebuffer with pixel data. In 4 BPP mode, each byte contains 2 pixels (4 bits per pixel = palette index 0-15).

**Example: Fill screen with colored stripes**

```assembly
; Set VRAM address to start of page 0 ($0000)
LDA #$00
STA $C100      ; VRAM_ADDR_LO = $00
STA $C101      ; VRAM_ADDR_HI = $00

; Enable burst mode for fast writes
LDA #$01
STA $C103      ; VRAM_CTRL = burst mode ON

; Fill first row with alternating red (1) and green (2)
; Byte value $12 = pixel 0: palette 1 (red), pixel 1: palette 2 (green)
LDX #80        ; 160 pixels / 2 pixels per byte = 80 bytes per row
LDA #$12       ; Red-green pattern
fill_row0:
    STA $C102  ; Write to VRAM_DATA (auto-increments address)
    DEX
    BNE fill_row0

; Fill next row with blue (3) and yellow (4)
LDX #80
LDA #$34       ; Blue-yellow pattern
fill_row1:
    STA $C102
    DEX
    BNE fill_row1

; Fill next row with magenta (5) and cyan (6)
LDX #80
LDA #$56       ; Magenta-cyan pattern
fill_row2:
    STA $C102
    DEX
    BNE fill_row2

; Continue filling rows...
; For a complete framebuffer, you need to write 8,000 bytes total

; Disable burst mode (optional)
LDA #$00
STA $C103      ; VRAM_CTRL = burst mode OFF
```

---

### Step 4: Enable Graphics Mode

Finally, switch the display from character mode to graphics mode:

```assembly
LDA #$01
STA $C10D      ; DISPLAY_MODE = 1 (graphics mode)
```

**Done!** Your screen should now display the colorful bitmap pattern you just created.

---

## Alternative: Copy Bitmap from ROM or RAM

If you have bitmap data stored in ROM or RAM, you can copy it to VRAM efficiently:

```assembly
; Assume bitmap data is at $4000-$5F3F (8,000 bytes)

; Setup VRAM address
LDA #$00
STA $C100      ; VRAM_ADDR_LO = $00
STA $C101      ; VRAM_ADDR_HI = $00

; Enable burst mode
LDA #$01
STA $C103      ; VRAM_CTRL = burst ON

; Setup source pointer
LDA #$00
STA $10        ; Zero page pointer low byte
LDA #$40
STA $11        ; Zero page pointer high byte ($4000)

; Copy 8000 bytes
LDX #$00       ; X = byte counter low
LDY #$1F       ; Y = byte counter high (8000 = $1F40)
copy_loop:
    LDA ($10),Y  ; Load byte from source
    STA $C102    ; Write to VRAM (auto-increment)
    INC $10      ; Increment source pointer
    BNE no_carry
    INC $11
no_carry:
    INX
    BNE copy_loop
    DEY
    BPL copy_loop

; Disable burst mode
LDA #$00
STA $C103
```

---

## Switching Back to Character Mode

To return to text mode:

```assembly
LDA #$00
STA $C10D      ; DISPLAY_MODE = 0 (character mode)
```

Both GPUs run simultaneously - switching just changes which output is displayed.

---

## Tips and Tricks

### Tip 1: Test with Simple Patterns

Before drawing complex graphics, test with simple patterns:

**Horizontal stripes** (same byte repeated for each row):
```assembly
LDA #$77       ; All pixels = palette 7 (white)
LDX #80
fill_white_row:
    STA $C102
    DEX
    BNE fill_white_row
```

**Checkerboard** (alternating $0F and $F0):
```assembly
; Row 0: $0F, $F0, $0F, $F0, ...
; Row 1: $F0, $0F, $F0, $0F, ...
```

### Tip 2: Double-Buffering for Smooth Animation

Use page flipping to avoid flicker:

1. Render frame to page 1 ($2000-$3FFF)
2. Wait for VBlank interrupt or poll GPU_STATUS
3. Flip to page 1: `STA $C104 #$00, STA $C105 #$20`
4. Render next frame to page 0 ($0000-$1FFF)
5. Flip back to page 0, repeat

**VBlank Polling Example**:
```assembly
wait_vblank:
    LDA $C10B      ; Read GPU_STATUS
    AND #$01       ; Check VBlank bit
    BEQ wait_vblank ; Loop until VBlank = 1
```

### Tip 3: Use Lookup Tables for Palette

Create a table of common colors:

```assembly
color_table:
    .byte $00, $00, $00  ; 0: Black (R, G, B)
    .byte $0F, $00, $00  ; 1: Red
    .byte $00, $0F, $00  ; 2: Green
    .byte $00, $00, $0F  ; 3: Blue
    .byte $0F, $0F, $00  ; 4: Yellow
    .byte $0F, $00, $0F  ; 5: Magenta
    .byte $00, $0F, $0F  ; 6: Cyan
    .byte $0F, $0F, $0F  ; 7: White

; Program palette from table
LDX #$00
program_palette:
    STX $C107           ; CLUT_INDEX = X
    LDA color_table,X   ; Red
    STA $C108
    LDA color_table+1,X ; Green
    STA $C109
    LDA color_table+2,X ; Blue
    STA $C10A
    INX
    INX
    INX
    CPX #24             ; 8 colors × 3 components
    BNE program_palette
```

---

## Troubleshooting

### Problem: Screen is all black
- Check DISPLAY_MODE register (0xC10D) - should be 1 for graphics
- Verify VRAM contains non-zero data
- Check FB_BASE_ADDR points to valid page (0x0000, 0x2000, 0x4000, or 0x6000)

### Problem: Wrong colors displayed
- Verify palette is programmed correctly (CLUT_INDEX + CLUT_DATA_R/G/B)
- Check GPU_MODE matches your data format (1/2/4 BPP)
- Ensure pixel data uses valid palette indices (0-3 for 2 BPP, 0-15 for 4 BPP)

### Problem: Garbage/noise on screen
- VRAM address may not be set correctly before writing
- Burst mode may not be enabled (writing to random addresses)
- GPU_MODE may not match data format

---

## Next Steps

Once you have basic graphics displaying:

1. **Animation**: Use page flipping and VBlank interrupts
2. **Sprites**: Draw small bitmaps at specific VRAM positions
3. **Scrolling**: Change FB_BASE_ADDR to scroll through VRAM
4. **Games**: Combine graphics with character text overlays
5. **Art Tools**: Create bitmap editors that write to VRAM

---

## Complete Example Program

Here's a minimal complete program that displays a rainbow gradient:

```assembly
.org $8000

start:
    ; Set 4 BPP mode
    LDA #$02
    STA $C106

    ; Program 8-color palette (rainbow)
    JSR setup_palette

    ; Fill VRAM with gradient
    JSR fill_gradient

    ; Enable graphics display
    LDA #$01
    STA $C10D

    ; Infinite loop
forever:
    JMP forever

setup_palette:
    ; (Use palette code from Step 2 above)
    RTS

fill_gradient:
    ; Setup VRAM address and burst mode
    LDA #$00
    STA $C100
    STA $C101
    LDA #$01
    STA $C103

    ; Fill with repeating color pattern
    LDX #$00
    LDY #$1F       ; 8000 bytes = $1F40
gradient_loop:
    TXA            ; Use X as pattern value
    AND #$77       ; Mask to valid palette indices
    STA $C102      ; Write to VRAM
    INX
    BNE gradient_loop
    DEY
    BPL gradient_loop

    LDA #$00
    STA $C103      ; Disable burst
    RTS
```

---

**Quick Start Complete!** ✅

You now know how to:
- Set graphics mode
- Program color palette
- Write bitmap data to VRAM
- Switch between character and graphics display

Happy coding!
