# Character Rendering Pipeline

**Module**: GPU Character Display Subsystem
**Date**: 2026-01-01
**Status**: Implemented and Hardware Validated

## Overview

The character rendering pipeline converts ASCII character codes stored in video memory into pixel data for DVI/HDMI output. It operates at 640x480@60Hz resolution in 80-column text mode, displaying 80 characters per row × 30 rows using an 8x16 pixel VGA font.

## Pipeline Architecture

The rendering pipeline is a **3-stage pipelined architecture** that processes one horizontal scanline at a time. Each stage operates on the 25 MHz pixel clock.

###Stage Summary

| Stage | Module | Latency | Function |
|-------|--------|---------|----------|
| 1 | Character Address Calculation | Combinational | Calculate which character to fetch |
| 2 | Character Buffer Read | 1 cycle | Read ASCII code from dual-port RAM |
| 3 | Font ROM Read | 1 cycle | Read 8-pixel bitmap for character |
| 4 | Pixel Extraction & Color | Combinational + 1 reg | Extract pixel bit, apply colors, output RGB |

**Total Latency**: 2 clock cycles from address calculation to pixel output

## Stage 1: Character Address Calculation

**Module**: `character_renderer.v` (lines 77-108)

Calculates which character to display based on current pixel position (`h_count`, `v_count`).

### 80-Column Mode Addressing

```
Character column = h_count / 8       (each char is 8 pixels wide)
Character row    = v_count / 16      (each char is 16 pixels tall)
Buffer address   = row * 80 + column
Scanline within char = v_count % 16
```

### Implementation

```verilog
// No prefetch offset needed - pipeline naturally aligns
wire [9:0] h_fetch = h_count;

// 80-col mode: divide by 8 to get character column
wire [6:0] char_col_80 = h_fetch[9:3];  // h_fetch / 8

// Divide by 16 to get character row
wire [4:0] char_row = v_count[9:4];  // v_count / 16

// Calculate buffer address: row * 80 + col
// Optimization: row * 80 = row * 64 + row * 16
wire [10:0] char_addr_80 = {char_row, 6'b0} + {char_row, 4'b0} + {4'b0, char_col_80};

// Scanline within character (0-15)
wire [3:0] char_scanline = v_count[3:0];
```

### Critical Fix: Pipeline Alignment

**Bug History**: Original code used `h_fetch = h_count + 3`, which caused character boundary crossing too early. When displaying pixel 5-7 of a character, it would fetch the NEXT character's data, resulting in artifacts on the right edge of characters.

**Fix**: Changed to `h_fetch = h_count` because:
- Character buffer read: 1 cycle delay
- Font ROM read: 1 cycle delay
- Total data path delay: 2 cycles
- Position tracking (`h_count_d2`): also 2 cycles delay
- Both paths naturally align - no offset needed!

## Stage 2: Character Buffer Read

**Module**: `character_buffer.v`

Dual-port block RAM storing 2400 ASCII character codes (80 × 30).

### Interface

```verilog
// Video read port (pixel clock domain)
input  wire        clk_video,      // 25 MHz pixel clock
input  wire [10:0] addr_read,      // From stage 1 calculation
output reg  [7:0]  data_read       // ASCII character code
```

### Timing

```
Clock edge N:   addr_read updated with character address
Clock edge N+1: data_read contains ASCII code for that address
```

The one-cycle latency is handled by the pipeline delay registers (`h_count_d1`, `v_count_d1`).

### Initial Content

Buffer initializes with "HELLO WORLD" test message at address 0-10:

```verilog
initial begin
    char_mem[0]  = 8'h48;  // 'H'
    char_mem[1]  = 8'h45;  // 'E'
    char_mem[2]  = 8'h4C;  // 'L'
    char_mem[3]  = 8'h4C;  // 'L'
    char_mem[4]  = 8'h4F;  // 'O'
    char_mem[5]  = 8'h20;  // ' '
    char_mem[6]  = 8'h57;  // 'W'
    char_mem[7]  = 8'h4F;  // 'O'
    char_mem[8]  = 8'h52;  // 'R'
    char_mem[9]  = 8'h4C;  // 'L'
    char_mem[10] = 8'h44;  // 'D'
end
```

## Stage 3: Font ROM Read

**Module**: `font_rom.v`

ROM containing 8x16 pixel bitmaps for 96 printable ASCII characters (0x20-0x7F).

### Interface

```verilog
input  wire        clk,            // 25 MHz pixel clock
input  wire [7:0]  char_code,      // From character buffer (stage 2)
input  wire [3:0]  scanline,       // From stage 1 (0-15)
output reg  [7:0]  pixel_row       // 8 pixels: 1=foreground, 0=background
```

### Address Calculation

```verilog
// ROM address = (char_code - 0x20) * 16 + scanline
wire [7:0] char_offset = char_code - 8'h20;
wire [10:0] rom_address = {char_offset, 4'b0000} + {7'b0, scanline};
```

For character 'A' (0x41) at scanline 5:
```
char_offset = 0x41 - 0x20 = 0x21 (33)
rom_address = 33 * 16 + 5 = 528 + 5 = 533
```

### Font Data Format

- **Total size**: 1536 bytes (96 characters × 16 bytes/char)
- **Source**: Standard 8x16 VGA font
- **File**: `font_data.hex` (loaded via `$readmemh`)
- **Encoding**: Each byte represents 8 horizontal pixels, MSB = leftmost pixel

Example for 'A' (0x41):
```
Scanline 0:  00000000  (top of character)
Scanline 1:  00000000
Scanline 2:  00011000  (start of 'A')
Scanline 3:  00111100
Scanline 4:  01100110
Scanline 5:  01100110
Scanline 6:  01111110  (horizontal bar)
Scanline 7:  01100110
Scanline 8:  01100110
...
```

### Non-Printable Characters

Characters outside 0x20-0x7F display as a solid block (placeholder glyph):

```verilog
if (is_printable) begin
    pixel_row <= rom_data[rom_address];
end else begin
    pixel_row <= 8'hFF;  // Solid block
end
```

## Stage 4: Pixel Extraction and Color Application

**Module**: `character_renderer.v` (lines 171-224)

Extracts the specific pixel bit from the 8-pixel font row and applies foreground/background colors.

### Pixel Position Extraction

```verilog
// In 80-column mode, each font pixel = 1 screen pixel
wire [2:0] pixel_x_80 = h_count_d2[2:0];  // 0-7 within character

// Font data is MSB-first: pixel 0 = bit 7, pixel 7 = bit 0
wire [2:0] pixel_bit_index = 3'd7 - pixel_x_80;
wire pixel_on = font_pixels[pixel_bit_index];
```

### Color Expansion

Colors are 3-bit RGB (1 bit per channel) expanded to 24-bit (8 bits per channel):

```verilog
wire [7:0] fg_r = fg_color[2] ? 8'hFF : 8'h00;
wire [7:0] fg_g = fg_color[1] ? 8'hFF : 8'h00;
wire [7:0] fg_b = fg_color[0] ? 8'hFF : 8'h00;

wire [7:0] bg_r = bg_color[2] ? 8'hFF : 8'h00;
wire [7:0] bg_g = bg_color[1] ? 8'hFF : 8'h00;
wire [7:0] bg_b = bg_color[0] ? 8'hFF : 8'h00;
```

### Color Selection

```verilog
wire [7:0] pixel_r = pixel_on ? fg_r : bg_r;
wire [7:0] pixel_g = pixel_on ? fg_g : bg_g;
wire [7:0] pixel_b = pixel_on ? fg_b : bg_b;
```

### RGB Output Register

Final stage registers the RGB output (adds 1 cycle latency, but this is absorbed by DVI transmitter pipeline):

```verilog
always @(posedge clk) begin
    if (video_active_d2) begin
        red   <= pixel_r;
        green <= pixel_g;
        blue  <= pixel_b;
    end else begin
        // Black during blanking
        red   <= 8'h00;
        green <= 8'h00;
        blue  <= 8'h00;
    end
end
```

## Pipeline Delay Tracking

The pipeline maintains synchronization by delaying the pixel position counters to match the data path:

```verilog
// Stage 2 delay registers
reg [9:0] h_count_d1;
reg [9:0] v_count_d1;
always @(posedge clk) begin
    h_count_d1 <= h_count;
    v_count_d1 <= v_count;
end

// Stage 3 delay registers
reg [9:0] h_count_d2;
reg [9:0] v_count_d2;
always @(posedge clk) begin
    h_count_d2 <= h_count_d1;
    v_count_d2 <= v_count_d1;
end
```

This ensures that when `font_pixels` contains the bitmap for character X at scanline Y, the `h_count_d2` and `v_count_d2` values correctly indicate which pixel of that character to display.

## Timing Diagram

```
Pixel Clock:  __|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|
              Cycle 0  Cycle 1  Cycle 2  Cycle 3

h_count:      0        1        2        3
v_count:      0        0        0        0

Stage 1:
  char_addr   [calc]   [calc]   [calc]   [calc]

Stage 2:
  char_data   ----     [char0]  [char0]  [char0]

Stage 3:
  font_pixels ----     ----     [pix0]   [pix0]

Stage 4:
  h_count_d2  ----     ----     0        1
  RGB output  BLACK    BLACK    [col]    [col]
```

At cycle 2, we output the first visible pixel using:
- `font_pixels` from character 0 (fetched at cycle 0, available cycle 2)
- `h_count_d2 = 0` (position delayed by 2 cycles to match data)

## Display Modes

### 80-Column Mode (Current Implementation)

- **Resolution**: 640×480 pixels (VGA)
- **Text grid**: 80 columns × 30 rows = 2400 characters
- **Character size**: 8 pixels wide × 16 pixels tall
- **Screen usage**: 640 pixels (80×8) × 480 pixels (30×16)
- **Buffer size**: 2400 bytes

### 40-Column Mode (Supported by hardware, not yet enabled)

- **Resolution**: 640×480 pixels
- **Text grid**: 40 columns × 30 rows = 1200 characters
- **Character size**: 16 pixels wide (doubled) × 16 pixels tall
- **Screen usage**: 640 pixels (40×16) × 480 pixels (30×16)
- **Buffer size**: 1200 bytes

## Performance

### Throughput

- **Pixel clock**: 25.175 MHz (VGA standard)
- **Pixels per frame**: 640 × 480 = 307,200
- **Characters per frame**: 80 × 30 = 2,400
- **Frame rate**: 60 Hz
- **Character fetch rate**: 2,400 × 60 = 144,000 characters/second

### Latency

- **Pipeline depth**: 3 cycles (2 memory reads + 1 output register)
- **Time per pixel**: 39.7 ns (25.175 MHz)
- **Pipeline latency**: 119 ns

## Resource Utilization

### Memory

- **Character buffer**: 2400 bytes (block RAM)
- **Font ROM**: 1536 bytes (block RAM)
- **Total block RAM**: 3936 bytes (uses 2 EBR blocks on ECP5)

### Logic

- **Character renderer**: ~150 LUTs (address calculation, muxing)
- **Pipeline registers**: ~60 FFs (delay stages, color registers)

## Clock Domains

The rendering pipeline crosses between two clock domains:

1. **CPU clock domain** (25 MHz) - Character buffer write port
2. **Pixel clock domain** (25 MHz) - Character buffer read port, entire rendering pipeline

Although both are 25 MHz, they are asynchronous (derived from different PLLs). The character_buffer uses dual-port block RAM which inherently handles clock domain crossing safely.

## Hardware Validation

### Test Results

- ✅ **Display working**: "HELLO WORLD" displays cleanly on HDMI monitor
- ✅ **No artifacts**: Pipeline timing fix eliminated character edge artifacts
- ✅ **Manual writes verified**: CPU can write characters via monitor D command
- ✅ **Python scripts working**: test_gpu_demo.py successfully writes multiple lines

### Known Issues

None - pipeline working correctly after prefetch offset fix.

## Related Modules

- **character_buffer.v**: Dual-port RAM storage for character codes
- **font_rom.v**: Font bitmap storage
- **gpu_registers.v**: CPU interface for writing characters
- **vga_timing_generator.v**: Provides h_count, v_count, video_active signals
- **dvi_transmitter.v**: Converts RGB to TMDS signals

## References

- VGA timing: `docs/timing/vga_640x480_60hz.md`
- Register map: `docs/modules/register_interface.md`
- Font format: Standard IBM VGA 8x16 font
