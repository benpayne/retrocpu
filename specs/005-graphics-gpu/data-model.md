# Data Model: Graphics Mode GPU

**Feature**: 005-graphics-gpu
**Date**: 2026-01-04
**Purpose**: Define data structures, memory layouts, and state for graphics GPU

---

## 1. VRAM (Video RAM)

### Structure
- **Type**: Dual-port block RAM array
- **Size**: 32,768 bytes (32KB)
- **Address Range**: $0000-$7FFF (15-bit address, 0-32767)
- **Organization**: Linear byte array, divided into 4 pages of 8KB each

### Page Layout

```
Page 0: $0000-$1FFF (8,192 bytes) - Framebuffer 0
Page 1: $2000-$3FFF (8,192 bytes) - Framebuffer 1
Page 2: $4000-$5FFF (8,192 bytes) - Framebuffer 2
Page 3: $6000-$7FFF (8,192 bytes) - Framebuffer 3
```

Each page can hold one complete framebuffer in any graphics mode (1 BPP, 2 BPP, or 4 BPP).

### Dual-Port Interface

**Write Port** (CPU Clock Domain):
- Clock: `clk_cpu` (system clock, ~12.5-25 MHz)
- Address: 15-bit VRAM address pointer (from registers)
- Data: 8-bit write data (from VRAM_DATA register)
- Write Enable: Asserted during VRAM_DATA write

**Read Port** (Pixel Clock Domain):
- Clock: `clk_pixel` (25 MHz VGA pixel clock)
- Address: Calculated from h_count, v_count, FB_BASE_ADDR, GPU_MODE
- Data: 8-bit pixel data (fed to pixel renderer)
- Read Enable: Always active during video_active period

### Address Wrapping

VRAM addresses wrap at 32KB boundary:
- Write to address $7FFF, then increment → wraps to $0000
- Read from address $7FFF + 1 → wraps to $0000

---

## 2. Framebuffer Layouts

### 1 BPP Mode (320x200 Monochrome)

```
Resolution: 320 pixels wide × 200 pixels tall
Bytes per row: 40 (320 pixels / 8 bits per byte)
Total rows: 200
Framebuffer size: 40 × 200 = 8,000 bytes
```

**Pixel Encoding**:
- Each byte contains 8 pixels
- Bit 7 (MSB) = leftmost pixel, Bit 0 = rightmost pixel
- Pixel value: 0 = background color, 1 = foreground color
- Color palette: Not used (fixed black/white or configurable via separate register)

**Address Calculation**:
```
byte_address = (y * 40) + (x / 8)
bit_position = 7 - (x % 8)
pixel_value = (vram[byte_address] >> bit_position) & 1
```

**Example Row**:
```
Row 0: $0000-$0027 (40 bytes)
Row 1: $0028-$004F (40 bytes)
Row 2: $0050-$0077 (40 bytes)
...
Row 199: $1F10-$1F37 (40 bytes, end at $1F37 = 7,999)
```

### 2 BPP Mode (160x200, 4-color Palette)

```
Resolution: 160 pixels wide × 200 pixels tall
Bytes per row: 40 (160 pixels × 2 bits / 8 bits per byte)
Total rows: 200
Framebuffer size: 40 × 200 = 8,000 bytes
```

**Pixel Encoding**:
- Each byte contains 4 pixels (2 bits each)
- Bits [7:6] = pixel 0 (leftmost), bits [5:4] = pixel 1, bits [3:2] = pixel 2, bits [1:0] = pixel 3 (rightmost)
- Pixel value: 0-3 (index into palette entries 0-3)

**Address Calculation**:
```
byte_address = (y * 40) + (x / 4)
bit_position = 6 - ((x % 4) * 2)  // 6, 4, 2, 0 for pixels 0-3
palette_index = (vram[byte_address] >> bit_position) & 0x03
```

**Example Byte**:
```
Byte value: 0b11100100 = 0xE4
Pixel 0 (bits 7:6): 11 = palette index 3
Pixel 1 (bits 5:4): 10 = palette index 2
Pixel 2 (bits 3:2): 01 = palette index 1
Pixel 3 (bits 1:0): 00 = palette index 0
```

### 4 BPP Mode (160x100, 16-color Palette)

```
Resolution: 160 pixels wide × 100 pixels tall
Bytes per row: 80 (160 pixels × 4 bits / 8 bits per byte)
Total rows: 100
Framebuffer size: 80 × 100 = 8,000 bytes
```

**Pixel Encoding**:
- Each byte contains 2 pixels (4 bits each)
- Bits [7:4] = pixel 0 (leftmost), bits [3:0] = pixel 1 (rightmost)
- Pixel value: 0-15 (index into palette entries 0-15)

**Address Calculation**:
```
byte_address = (y * 80) + (x / 2)
bit_position = ((x % 2) == 0) ? 4 : 0  // High nibble (4) or low nibble (0)
palette_index = (vram[byte_address] >> bit_position) & 0x0F
```

**Example Byte**:
```
Byte value: 0xA5
Pixel 0 (bits 7:4): 0xA = palette index 10
Pixel 1 (bits 3:0): 0x5 = palette index 5
```

**Example Row**:
```
Row 0: $0000-$004F (80 bytes)
Row 1: $0050-$009F (80 bytes)
Row 2: $00A0-$00EF (80 bytes)
...
Row 99: $1F30-$1F7F (80 bytes, end at $1F7F = 7,999)
```

---

## 3. Color Palette (CLUT - Color Lookup Table)

### Structure
- **Type**: 16-entry register array
- **Size**: 16 entries × 12 bits (RGB444) = 192 bits total
- **Index Range**: 0-15
- **Color Format**: RGB444 (4 bits red, 4 bits green, 4 bits blue)

### Palette Entry Format

```
Entry Structure (12 bits):
  [11:8] Red component   (4 bits, 0-15)
  [7:4]  Green component (4 bits, 0-15)
  [3:0]  Blue component  (4 bits, 0-15)
```

**Storage**:
```verilog
reg [3:0] palette_r [0:15];  // Red components
reg [3:0] palette_g [0:15];  // Green components
reg [3:0] palette_b [0:15];  // Blue components
```

### RGB444 to RGB888 Expansion

```verilog
red_output[7:0]   = {palette_r[index][3:0], palette_r[index][3:0]}
green_output[7:0] = {palette_g[index][3:0], palette_g[index][3:0]}
blue_output[7:0]  = {palette_b[index][3:0], palette_b[index][3:0]}
```

**Example**:
```
Palette entry 5: R=0xA, G=0x5, B=0xC
RGB444: {0xA, 0x5, 0xC} = {1010, 0101, 1100}
RGB888 expansion: {0xAA, 0x55, 0xCC} = {10101010, 01010101, 11001100}
```

### Palette Usage by Mode

- **1 BPP**: Palette not used (monochrome or fixed colors)
- **2 BPP**: Uses palette entries 0-3 (4 colors)
- **4 BPP**: Uses all palette entries 0-15 (16 colors)

### Default Palette (Reset Values)

Power-on reset initializes palette to grayscale ramp:

```
Entry  R  G  B   Description
0:     0  0  0    Black
1:     1  1  1    Dark gray 1
2:     2  2  2    Dark gray 2
3:     3  3  3    Dark gray 3
4:     4  4  4    Gray 4
5:     5  5  5    Gray 5
6:     6  6  6    Gray 6
7:     7  7  7    Gray 7
8:     8  8  8    Gray 8
9:     9  9  9    Gray 9
10:    A  A  A    Gray 10
11:    B  B  B    Gray 11
12:    C  C  C    Light gray 12
13:    D  D  D    Light gray 13
14:    E  E  E    Light gray 14
15:    F  F  F    White
```

---

## 4. Register File

### Register Structure

16 registers spanning 0xC100-0xC10F:

```
Address   Name           Access  Bits  Description
-------   -----------    ------  ----  -----------
0xC100    VRAM_ADDR_LO   RW      [7:0] VRAM address pointer low byte
0xC101    VRAM_ADDR_HI   RW      [6:0] VRAM address pointer high byte (bit 7 unused)
0xC102    VRAM_DATA      RW      [7:0] VRAM data read/write at current address
0xC103    VRAM_CTRL      RW      [0]   Bit 0: Burst mode enable
0xC104    FB_BASE_LO     RW      [7:0] Framebuffer base address low byte
0xC105    FB_BASE_HI     RW      [6:0] Framebuffer base address high byte (bit 7 unused)
0xC106    GPU_MODE       RW      [1:0] Graphics mode (00=1BPP, 01=2BPP, 10=4BPP)
0xC107    CLUT_INDEX     RW      [3:0] Palette index (0-15, bits 7:4 unused)
0xC108    CLUT_DATA_R    RW      [3:0] Red component (bits 7:4 unused)
0xC109    CLUT_DATA_G    RW      [3:0] Green component (bits 7:4 unused)
0xC10A    CLUT_DATA_B    RW      [3:0] Blue component (bits 7:4 unused)
0xC10B    GPU_STATUS     RO      [0]   Bit 0: VBlank flag
0xC10C    GPU_IRQ_CTRL   RW      [0]   Bit 0: VBlank interrupt enable
0xC10D    DISPLAY_MODE   RW      [0]   Bit 0: 0=Character mode, 1=Graphics mode
0xC10E    Reserved       --      --    Future use
0xC10F    Reserved       --      --    Future use
```

### Register Details

#### VRAM_ADDR (0xC100-0xC101)

**Type**: 15-bit address pointer (split into low/high bytes)
**Range**: $0000-$7FFF (0-32767)

**Behavior**:
- Write VRAM_ADDR_LO sets bits [7:0] of address pointer
- Write VRAM_ADDR_HI sets bits [14:8] of address pointer
- Read VRAM_ADDR_LO returns current bits [7:0]
- Read VRAM_ADDR_HI returns current bits [14:8] (bit 7 always reads 0)

**Auto-Increment**:
- When burst mode enabled (VRAM_CTRL bit 0 = 1), writing to VRAM_DATA increments VRAM_ADDR
- Increment wraps at $7FFF → $0000

#### VRAM_DATA (0xC102)

**Type**: 8-bit data register

**Write Behavior**:
- Writes data to VRAM at address specified by VRAM_ADDR
- If burst mode enabled, increments VRAM_ADDR after write

**Read Behavior**:
- Reads data from VRAM at address specified by VRAM_ADDR
- If burst mode enabled, increments VRAM_ADDR after read

#### VRAM_CTRL (0xC103)

**Type**: Control register

**Bit Layout**:
```
Bit 0: Burst mode enable (0=disabled, 1=enabled)
Bits 7:1: Reserved (read as 0)
```

#### FB_BASE_ADDR (0xC104-0xC105)

**Type**: 15-bit framebuffer base address (split into low/high bytes)
**Range**: $0000-$7FFF (typically $0000, $2000, $4000, $6000 for pages 0-3)

**Purpose**:
- Specifies which VRAM address is the start of the framebuffer displayed on screen
- Used for page flipping (change during VBlank to swap buffers)

**Typical Values**:
- $0000: Page 0
- $2000: Page 1
- $4000: Page 2
- $6000: Page 3

#### GPU_MODE (0xC106)

**Type**: Mode select register

**Bit Layout**:
```
Bits [1:0]: Graphics mode
  00 = 1 BPP (320x200 monochrome)
  01 = 2 BPP (160x200, 4-color palette)
  10 = 4 BPP (160x100, 16-color palette)
  11 = Reserved
Bits [7:2]: Reserved (read as 0)
```

#### CLUT_INDEX (0xC107)

**Type**: Palette index register

**Bit Layout**:
```
Bits [3:0]: Palette index (0-15)
Bits [7:4]: Reserved (read as 0)
```

**Usage**:
- Write index 0-15 to select palette entry for read/write via CLUT_DATA_R/G/B
- Index persists until changed (can write R, G, B sequentially to same entry)

#### CLUT_DATA_R/G/B (0xC108-0xC10A)

**Type**: Palette color component registers

**Bit Layout**:
```
Bits [3:0]: Color component value (0-15)
Bits [7:4]: Reserved (read as 0)
```

**Write Behavior**:
- Writes to palette entry selected by CLUT_INDEX
- Immediate effect on displayed pixels using that palette entry

**Read Behavior**:
- Reads from palette entry selected by CLUT_INDEX

#### GPU_STATUS (0xC10B)

**Type**: Read-only status register

**Bit Layout**:
```
Bit 0: VBlank flag (1 during vertical blanking period, 0 otherwise)
Bits [7:1]: Reserved (read as 0)
```

**VBlank Timing**:
- VBlank flag set at start of vertical retrace (v_count >= V_SYNC_START)
- VBlank flag cleared when entering visible region (v_count < V_VISIBLE)
- Duration: ~2 scanlines at 25 MHz = ~80 microseconds

#### GPU_IRQ_CTRL (0xC10C)

**Type**: Interrupt control register

**Bit Layout**:
```
Bit 0: VBlank interrupt enable (0=disabled, 1=enabled)
Bits [7:1]: Reserved (read as 0)
```

**Interrupt Behavior**:
- When enabled and VBlank occurs, asserts interrupt signal to CPU
- Interrupt is edge-triggered (one pulse per VBlank)
- CPU clears interrupt by servicing it (reading GPU_STATUS)

#### DISPLAY_MODE (0xC10D)

**Type**: Display mode select register

**Bit Layout**:
```
Bit 0: Display mode (0=Character mode, 1=Graphics mode)
Bits [7:1]: Reserved (read as 0)
```

**Reset Value**: 0 (character mode)

---

## 5. State Machine: Pixel Rendering

### States

**IDLE**: Waiting for visible region
**FETCH**: Fetching pixel data from VRAM
**DECODE**: Decoding pixel bits and palette lookup
**OUTPUT**: Outputting RGB888 to video pipeline

### State Transitions

```
IDLE → FETCH: When video_active asserts (entering visible region)
FETCH → DECODE: One cycle after VRAM read (registered output)
DECODE → OUTPUT: One cycle for palette lookup
OUTPUT → FETCH: Next pixel position, or OUTPUT → IDLE at end of line
```

### Pipeline Depth

- **Latency**: 3 cycles (fetch + decode + output)
- **Throughput**: 1 pixel per cycle (pipelined after initial latency)

---

## 6. Timing Relationships

### Burst Write Sequence

```
Cycle 0: CPU writes VRAM_ADDR_LO ($00)
Cycle 1: CPU writes VRAM_ADDR_HI ($00)  → Address pointer = $0000
Cycle 2: CPU writes VRAM_CTRL (bit 0 = 1) → Enable burst mode
Cycle 3: CPU writes VRAM_DATA ($AA)      → Write to $0000, increment to $0001
Cycle 4: CPU writes VRAM_DATA ($BB)      → Write to $0001, increment to $0002
...
Cycle 8002: CPU writes VRAM_DATA ($FF)   → Write to $1F3F, increment to $1F40
Cycle 8003: CPU writes VRAM_CTRL (bit 0 = 0) → Disable burst mode (optional)
```

### Page Flip Sequence

```
Frame N (displaying page 0):
  - CPU renders to page 1 ($2000-$3FFF) while page 0 displays
  - VBlank interrupt fires at v_count = V_SYNC_START

VBlank ISR:
  - Read GPU_STATUS to acknowledge interrupt
  - Write FB_BASE_LO = $00, FB_BASE_HI = $20 → Change to page 1
  - Return from interrupt

Frame N+1 (displaying page 1):
  - Display seamlessly switches to page 1 with no tearing
  - CPU now renders to page 0 for next flip
```

---

## 7. Data Flow Diagram

```
+----------+       VRAM_ADDR        +--------------+
|  CPU     | --------------------> |              |
| (write)  |       VRAM_DATA        |   32KB VRAM  |
+----------+ --------------------> |  (dual-port) |
                                    |              |
                                    +-------+------+
                                            |
                                    FB_BASE_ADDR + h_count + v_count
                                            |
                                            v
                                    +---------------+
                                    | Pixel Decoder |
                                    | (1/2/4 BPP)   |
                                    +-------+-------+
                                            |
                                    Palette Index
                                            |
                                            v
                                    +---------------+
                                    | Palette (CLUT)|
                                    | 16 × RGB444   |
                                    +-------+-------+
                                            |
                                       RGB444 value
                                            |
                                            v
                                    +----------------+
                                    | RGB444→RGB888  |
                                    | Bit Expansion  |
                                    +-------+--------+
                                            |
                                       RGB888 output
                                            |
                                            v
                                    +-----------------+
                                    | Display MUX     |
                                    | (Char/Graphics) |
                                    +-------+---------+
                                            |
                                       To DVI Transmitter
```

---

## 8. Memory Initialization

### VRAM

**Power-On State**:
- All 32KB initialized to $00 (black in all modes)
- Alternative: Initialize to test pattern for debugging

### Palette

**Power-On State**:
- Grayscale ramp (entries 0-15 from black to white)
- Ensures meaningful display even without CPU palette programming

### Registers

**Power-On State**:
```
VRAM_ADDR:    $0000
VRAM_CTRL:    $00 (burst mode disabled)
FB_BASE_ADDR: $0000 (page 0)
GPU_MODE:     $00 (1 BPP mode)
CLUT_INDEX:   $00
GPU_IRQ_CTRL: $00 (interrupts disabled)
DISPLAY_MODE: $00 (character mode)
```

---

**Data Model Complete** ✅

All structures, layouts, and relationships defined for implementation.
