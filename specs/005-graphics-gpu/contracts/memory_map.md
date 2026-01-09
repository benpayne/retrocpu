# Memory Map Contract: VRAM and Pixel Encoding

**Feature**: 005-graphics-gpu
**Date**: 2026-01-04

This document defines VRAM address mapping and pixel encoding formats for all graphics modes.

---

## VRAM Address Space

**Total Size**: 32,768 bytes (32KB)
**Address Range**: $0000-$7FFF (15-bit addressing)
**Organization**: 4 pages × 8KB per page

```
Page 0: $0000-$1FFF (0     - 8,191)  - Framebuffer page 0
Page 1: $2000-$3FFF (8,192 - 16,383) - Framebuffer page 1
Page 2: $4000-$5FFF (16,384- 24,575) - Framebuffer page 2
Page 3: $6000-$7FFF (24,576- 32,767) - Framebuffer page 3
```

**Address Wrapping**:
- Addresses beyond $7FFF wrap to $0000
- Example: $7FFF + 1 = $0000, $7FFF + 2 = $0001

---

## Pixel Encoding by Mode

### 1 BPP Mode: 320×200 Monochrome

**Byte Encoding**: 8 pixels per byte
```
Bit Position:  7    6    5    4    3    2    1    0
Pixel Index:   0    1    2    3    4    5    6    7
               (leftmost → rightmost)
```

**Pixel Value**: 0 = black, 1 = white (or custom colors)

**Address Calculation**:
```
byte_offset = (y * 40) + (x / 8)
vram_address = FB_BASE_ADDR + byte_offset
bit_position = 7 - (x % 8)
pixel_value = (vram[vram_address] >> bit_position) & 1
```

**Example** (pixel at x=10, y=5):
```
byte_offset = 5 * 40 + (10 / 8) = 200 + 1 = 201 ($00C9)
bit_position = 7 - (10 % 8) = 7 - 2 = 5
pixel = (vram[$00C9] >> 5) & 1
```

---

### 2 BPP Mode: 160×200, 4-Color Palette

**Byte Encoding**: 4 pixels per byte (2 bits each)
```
Bit Position:  7:6  5:4  3:2  1:0
Pixel Index:    0    1    2    3
               (leftmost → rightmost)
Palette Index: 0-3  0-3  0-3  0-3
```

**Address Calculation**:
```
byte_offset = (y * 40) + (x / 4)
vram_address = FB_BASE_ADDR + byte_offset
bit_position = 6 - ((x % 4) * 2)  // 6, 4, 2, 0
palette_index = (vram[vram_address] >> bit_position) & 0x03
```

**Example Byte**: 0b11100100 = 0xE4
- Pixel 0: bits [7:6] = 11 = palette index 3
- Pixel 1: bits [5:4] = 10 = palette index 2
- Pixel 2: bits [3:2] = 01 = palette index 1
- Pixel 3: bits [1:0] = 00 = palette index 0

---

### 4 BPP Mode: 160×100, 16-Color Palette

**Byte Encoding**: 2 pixels per byte (4 bits each)
```
Bit Position:  7:4    3:0
Pixel Index:    0      1
               (left) (right)
Palette Index: 0-15   0-15
```

**Address Calculation**:
```
byte_offset = (y * 80) + (x / 2)
vram_address = FB_BASE_ADDR + byte_offset
bit_position = ((x % 2) == 0) ? 4 : 0  // High nibble or low nibble
palette_index = (vram[vram_address] >> bit_position) & 0x0F
```

**Example Byte**: 0xA5
- Pixel 0: bits [7:4] = 0xA = palette index 10
- Pixel 1: bits [3:0] = 0x5 = palette index 5

---

## Scanline Organization

### 1 BPP Mode (320×200)
```
Scanline 0:   $0000-$0027 (40 bytes)
Scanline 1:   $0028-$004F (40 bytes)
Scanline 2:   $0050-$0077 (40 bytes)
...
Scanline 199: $1F10-$1F37 (40 bytes, ends at $1F37)
```

### 2 BPP Mode (160×200)
```
Scanline 0:   $0000-$0027 (40 bytes)
Scanline 1:   $0028-$004F (40 bytes)
...
Scanline 199: $1F10-$1F37 (40 bytes, same layout as 1 BPP)
```

### 4 BPP Mode (160×100)
```
Scanline 0:  $0000-$004F (80 bytes)
Scanline 1:  $0050-$009F (80 bytes)
Scanline 2:  $00A0-$00EF (80 bytes)
...
Scanline 99: $1F30-$1F7F (80 bytes, ends at $1F7F)
```

---

## Palette Memory Map

**Structure**: 16 entries × 12 bits (RGB444)
**Address**: Not directly addressable (accessed via CLUT_INDEX and CLUT_DATA_R/G/B registers)

**Internal Organization**:
```
Entry 0:  R[3:0] G[3:0] B[3:0]
Entry 1:  R[3:0] G[3:0] B[3:0]
...
Entry 15: R[3:0] G[3:0] B[3:0]
```

**Color Expansion** (RGB444 → RGB888):
```
red_output[7:0]   = {R[3:0], R[3:0]}
green_output[7:0] = {G[3:0], G[3:0]}
blue_output[7:0]  = {B[3:0], B[3:0]}
```

**Default Grayscale Ramp**:
```
Entry  R  G  B   RGB888 Output
0:     0  0  0   (0x00, 0x00, 0x00) - Black
1:     1  1  1   (0x11, 0x11, 0x11) - Dark gray
...
15:    F  F  F   (0xFF, 0xFF, 0xFF) - White
```

---

**Memory Map Complete** ✅
