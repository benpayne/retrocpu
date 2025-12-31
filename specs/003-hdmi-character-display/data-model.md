# Data Model & Module Design: DVI Character Display GPU

**Feature**: 003-hdmi-character-display
**Date**: 2025-12-27
**Phase**: Phase 1 - Design & Contracts

## Overview

This document specifies the complete module hierarchy, interfaces, state machines, and data structures for the DVI Character Display GPU. All modules are designed for Test-Driven Development with cocotb and follow the RetroCPU constitution principles of simplicity, reusability, and educational clarity.

## 1. Module Hierarchy

```
gpu_top
├── gpu_registers (CPU bus interface)
│   ├── Address decoder
│   ├── Register file
│   └── Clock domain crossing logic
│
├── character_buffer (2KB dual-port RAM)
│   ├── CPU write port (Port A)
│   └── Video read port (Port B)
│
├── font_rom (1.5KB single-port ROM)
│   └── 8x16 font data (96 characters)
│
├── video_timing (VGA timing generator)
│   ├── Horizontal counter
│   ├── Vertical counter
│   └── Sync/DE generation
│
├── character_renderer (scanline pixel generator)
│   ├── Character fetch logic
│   ├── Font lookup logic
│   ├── Pixel shift register
│   └── Color application
│
├── cursor_controller (cursor position & flash)
│   ├── Position tracking
│   ├── Flash timer (1Hz)
│   └── Visibility control
│
├── color_palette (3-bit to 24-bit expansion)
│   └── RGB expansion lookup
│
└── dvi_transmitter (TMDS encoding & output)
    ├── TMDS encoder (×3 for RGB)
    ├── Control character encoder
    ├── ODDRX2F serializers (×4)
    └── PLL (pixel clock generation)
```

## 2. Module Specifications

### 2.1 gpu_top (Top-Level Integration)

**Purpose**: Integrates all GPU submodules and provides CPU bus interface.

**Module Interface**:
```verilog
module gpu_top (
    // System clocks and reset
    input wire clk_sys,          // System/CPU clock (e.g., 1-4 MHz)
    input wire clk_pixel,        // 25.175 MHz pixel clock (from PLL)
    input wire clk_tmds,         // 251.75 MHz TMDS clock (from PLL)
    input wire reset,            // Active-high reset

    // CPU bus interface
    input wire [15:0] addr,      // CPU address bus
    input wire [7:0] data_in,    // CPU data bus (write)
    output wire [7:0] data_out,  // CPU data bus (read)
    input wire we,               // Write enable
    input wire re,               // Read enable
    input wire cs,               // Chip select (0xC010-0xC01F)

    // DVI/HDMI output (differential pairs)
    output wire tmds_clk_p,      // TMDS clock positive
    output wire tmds_clk_n,      // TMDS clock negative
    output wire tmds_data0_p,    // TMDS data channel 0 positive (Blue)
    output wire tmds_data0_n,    // TMDS data channel 0 negative
    output wire tmds_data1_p,    // TMDS data channel 1 positive (Green)
    output wire tmds_data1_n,    // TMDS data channel 1 negative
    output wire tmds_data2_p,    // TMDS data channel 2 positive (Red)
    output wire tmds_data2_n     // TMDS data channel 2 negative
);
```

**Submodule Instantiation Strategy**:
- All submodules instantiated within gpu_top
- Internal wiring between modules (character data flow, sync signals)
- Clock domain crossing handled by gpu_registers module
- Reset distribution to all submodules

**Internal Signals**:
```verilog
// Video timing signals
wire [9:0] pixel_x, pixel_y;
wire hsync, vsync, display_enable;

// Character rendering signals
wire [6:0] char_x;           // 0-79 (80-col) or 0-39 (40-col)
wire [4:0] char_y;           // 0-29 (30 rows)
wire [11:0] char_addr;       // Character buffer address
wire [7:0] char_data;        // ASCII code from buffer
wire [7:0] font_data;        // Font scanline bitmap
wire [7:0] pixel_rgb;        // Final pixel color

// Cursor signals
wire cursor_at_position;     // Cursor is at current pixel
wire cursor_visible;         // Cursor flash state

// Control registers (synchronized to pixel clock)
wire [4:0] cursor_row_sync;
wire [6:0] cursor_col_sync;
wire mode_80col_sync;
wire cursor_enable_sync;
wire [2:0] fg_color_sync, bg_color_sync;
```

---

### 2.2 gpu_registers (CPU Bus Interface & Registers)

**Purpose**: Implements memory-mapped register file and handles clock domain crossing between CPU and pixel clock domains.

**Module Interface**:
```verilog
module gpu_registers (
    // CPU clock domain
    input wire clk_cpu,
    input wire reset,

    input wire [3:0] addr,       // Register address (0xC010-0xC01F → 0-15)
    input wire [7:0] data_in,    // Write data
    output reg [7:0] data_out,   // Read data
    input wire we,               // Write enable
    input wire re,               // Read enable

    // Pixel clock domain - synchronized outputs
    input wire clk_pixel,
    output reg [4:0] cursor_row, // Cursor row (0-29)
    output reg [6:0] cursor_col, // Cursor column (0-79)
    output reg mode_80col,       // 0=40col, 1=80col
    output reg cursor_enable,    // Cursor visibility
    output reg [2:0] fg_color,   // Foreground color (3-bit RGB)
    output reg [2:0] bg_color,   // Background color (3-bit RGB)
    output reg clear_screen,     // Clear screen pulse

    // Character buffer write interface (pixel clock domain)
    output wire [11:0] buf_addr,  // Character buffer address
    output wire [7:0] buf_data,   // Character data to write
    output wire buf_we,           // Buffer write enable

    // Status signals from pixel clock domain
    input wire vsync,            // Vertical sync (for status register)
    input wire ready             // GPU ready flag
);
```

**Register File** (CPU clock domain):
```verilog
// Register addresses (offset from base 0xC010)
localparam CHAR_DATA    = 4'h0;  // Write character at cursor
localparam CURSOR_ROW   = 4'h1;  // Cursor row position
localparam CURSOR_COL   = 4'h2;  // Cursor column position
localparam CONTROL      = 4'h3;  // Control register
localparam FG_COLOR     = 4'h4;  // Foreground color
localparam BG_COLOR     = 4'h5;  // Background color
localparam STATUS       = 4'h6;  // Status register (read-only)

// CPU-side registers
reg [7:0] char_data_reg;
reg [4:0] cursor_row_reg;
reg [6:0] cursor_col_reg;
reg [2:0] control_reg;       // [2]=cursor_en, [1]=mode, [0]=clear
reg [2:0] fg_color_reg;
reg [2:0] bg_color_reg;
```

**Clock Domain Crossing**:
```verilog
// Two-stage synchronizers for control signals
reg [4:0] cursor_row_sync1, cursor_row_sync2;
reg [6:0] cursor_col_sync1, cursor_col_sync2;
reg mode_sync1, mode_sync2;
reg cursor_en_sync1, cursor_en_sync2;
reg [2:0] fg_sync1, fg_sync2;
reg [2:0] bg_sync1, bg_sync2;

always @(posedge clk_pixel) begin
    // First stage
    cursor_row_sync1 <= cursor_row_reg;
    cursor_col_sync1 <= cursor_col_reg;
    mode_sync1 <= control_reg[1];
    cursor_en_sync1 <= control_reg[2];
    fg_sync1 <= fg_color_reg;
    bg_sync1 <= bg_color_reg;

    // Second stage (safe in pixel domain)
    cursor_row_sync2 <= cursor_row_sync1;
    cursor_col_sync2 <= cursor_col_sync1;
    mode_sync2 <= mode_sync1;
    cursor_en_sync2 <= cursor_en_sync1;
    fg_sync2 <= fg_sync1;
    bg_sync2 <= bg_sync1;
end

assign cursor_row = cursor_row_sync2;
assign cursor_col = cursor_col_sync2;
assign mode_80col = mode_sync2;
assign cursor_enable = cursor_en_sync2;
assign fg_color = fg_sync2;
assign bg_color = bg_sync2;
```

**Character Write Logic**:
```verilog
// When CPU writes to CHAR_DATA register:
// 1. Write character to buffer at current cursor position
// 2. Auto-increment cursor (with wrap and scroll)

always @(posedge clk_cpu) begin
    if (reset) begin
        cursor_row_reg <= 0;
        cursor_col_reg <= 0;
    end else if (we && addr == CHAR_DATA) begin
        // Write to character buffer happens via buf_addr/buf_data/buf_we

        // Auto-increment cursor
        if (mode_80col_reg ? (cursor_col_reg == 79) : (cursor_col_reg == 39)) begin
            cursor_col_reg <= 0;
            if (cursor_row_reg == 29) begin
                // At last row: trigger scroll (handled by character_buffer)
                // Keep cursor at row 29
            end else begin
                cursor_row_reg <= cursor_row_reg + 1;
            end
        end else begin
            cursor_col_reg <= cursor_col_reg + 1;
        end
    end
end
```

**Clear Screen & Mode Change**:
```verilog
// Control register bit 0: Clear screen (auto-clearing)
// Control register bit 1: Mode select (triggers clear + cursor reset)

reg prev_mode;
always @(posedge clk_cpu) begin
    if (reset) begin
        control_reg <= 3'b100;  // Cursor enabled, 40-col mode, no clear
        prev_mode <= 0;
    end else if (we && addr == CONTROL) begin
        control_reg <= data_in[2:0];

        // Detect mode change
        if (data_in[1] != prev_mode) begin
            // Mode changed: reset cursor, trigger clear
            cursor_row_reg <= 0;
            cursor_col_reg <= 0;
            // Set clear_screen pulse (will be synchronized to pixel domain)
        end
        prev_mode <= data_in[1];
    end
end
```

---

### 2.3 character_buffer (Dual-Port RAM)

**Purpose**: Stores character data (ASCII codes) for the display. CPU writes via Port A, video logic reads via Port B.

**Module Interface**:
```verilog
module character_buffer (
    // Port A: CPU write port
    input wire clk_a,            // CPU clock
    input wire we_a,             // Write enable
    input wire [11:0] addr_a,    // Address (0-2399 for 80x30)
    input wire [7:0] data_a,     // Write data (ASCII code)

    // Port B: Video read port
    input wire clk_b,            // Pixel clock
    input wire [11:0] addr_b,    // Address (0-2399)
    output reg [7:0] data_b,     // Read data (ASCII code)

    // Clear screen control
    input wire clear,            // Pulse to clear buffer (pixel clock domain)
    output reg clear_busy        // Clear operation in progress
);
```

**Memory Organization**:
```verilog
// 2400 bytes = 80 columns × 30 rows (max size for 80-col mode)
// For 40-col mode: Only use 1200 bytes (40 × 30)

reg [7:0] mem [0:2399];  // Character buffer memory

// Address calculation:
// addr = row * columns + col
// 80-col: addr = row * 80 + col
// 40-col: addr = row * 40 + col
```

**Port A - CPU Write**:
```verilog
always @(posedge clk_a) begin
    if (we_a) begin
        mem[addr_a] <= data_a;
    end
end
```

**Port B - Video Read**:
```verilog
always @(posedge clk_b) begin
    data_b <= mem[addr_b];
end
```

**Clear Screen Operation**:
```verilog
// State machine to clear buffer (write 0x20 spaces to all locations)
reg [11:0] clear_addr;
reg clearing;

always @(posedge clk_b) begin
    if (clear && !clearing) begin
        clearing <= 1;
        clear_addr <= 0;
        clear_busy <= 1;
    end else if (clearing) begin
        mem[clear_addr] <= 8'h20;  // Space character
        clear_addr <= clear_addr + 1;

        if (clear_addr == 2399) begin
            clearing <= 0;
            clear_busy <= 0;
        end
    end
end
```

**Scrolling Operation**:
```verilog
// Scroll text up one line (copy line N+1 to line N, clear bottom line)
// Triggered when cursor advances past last row

reg [4:0] scroll_line;
reg [6:0] scroll_col;
reg scrolling;

always @(posedge clk_b) begin
    if (scroll_trigger && !scrolling) begin
        scrolling <= 1;
        scroll_line <= 0;
        scroll_col <= 0;
    end else if (scrolling) begin
        // Copy from (scroll_line+1, scroll_col) to (scroll_line, scroll_col)
        mem[scroll_line * cols + scroll_col] <=
            mem[(scroll_line + 1) * cols + scroll_col];

        scroll_col <= scroll_col + 1;
        if (scroll_col == (cols - 1)) begin
            scroll_col <= 0;
            scroll_line <= scroll_line + 1;

            if (scroll_line == 28) begin  // Finished copying
                // Clear last line (line 29)
                scrolling <= 0;
                // Trigger clear_last_line state
            end
        end
    end
end
```

---

### 2.4 font_rom (Character Font ROM)

**Purpose**: Stores 8x16 pixel font bitmaps for ASCII characters 0x20-0x7F plus placeholder glyph.

**Module Interface**:
```verilog
module font_rom (
    input wire clk,              // Pixel clock
    input wire [7:0] char_code,  // ASCII character code
    input wire [3:0] scanline,   // Which row of character (0-15)
    output reg [7:0] font_data   // 8 pixels for this scanline
);
```

**Memory Organization**:
```verilog
// 96 characters × 16 bytes per character = 1536 bytes
// Character 0x20 (space) at address 0
// Character 0x7F (DEL/placeholder) at address 1535

// Address calculation:
// font_addr = (char_code - 0x20) * 16 + scanline
// For non-printable (< 0x20 or == 0x7F): use placeholder (95 * 16)

wire [10:0] font_addr;
assign font_addr = (char_code < 8'h20 || char_code == 8'h7F) ?
                   (11'd95 * 4'd16 + scanline) :  // Placeholder
                   ((char_code - 8'h20) * 4'd16 + scanline);

// Font data ROM
reg [7:0] font_mem [0:1535];

// Initialize from file or include inline
initial begin
    $readmemh("font_8x16.hex", font_mem);
end

always @(posedge clk) begin
    font_data <= font_mem[font_addr];
end
```

**Font Data Format**:
```
Each character: 16 bytes (one per scanline)
Each byte: 8 bits representing 8 horizontal pixels
Bit 7 = leftmost pixel, Bit 0 = rightmost pixel

Example: 'A' (0x41)
Scanline 0:  00000000  (top, blank)
Scanline 1:  00000000
Scanline 2:  00011000  (top of A)
Scanline 3:  00111100
Scanline 4:  01100110
Scanline 5:  01100110
Scanline 6:  01111110  (crossbar)
Scanline 7:  01100110
Scanline 8:  01100110
Scanline 9:  01100110
Scanline 10: 01100110
Scanline 11: 00000000
Scanline 12: 00000000  (bottom, blank)
Scanline 13: 00000000
Scanline 14: 00000000
Scanline 15: 00000000
```

**Placeholder Glyph** (for non-printable characters):
```
Use solid block or checkerboard pattern
Recommendation: Solid block (all 0xFF)
Scanline 0-15: 11111111 (solid)
```

---

### 2.5 video_timing (VGA Timing Generator)

**Purpose**: Generates VGA-compatible timing signals (HSYNC, VSYNC, Display Enable) for 640x480 @ 60Hz.

**Module Interface**:
```verilog
module video_timing (
    input wire clk_pixel,        // 25.175 MHz pixel clock
    input wire reset,

    // Sync outputs
    output reg hsync,            // Horizontal sync (negative polarity)
    output reg vsync,            // Vertical sync (negative polarity)
    output wire display_enable,  // High during active video

    // Position outputs
    output reg [9:0] h_count,    // Horizontal counter (0-799)
    output reg [9:0] v_count,    // Vertical counter (0-524)
    output wire [9:0] pixel_x,   // X coordinate (valid when DE=1)
    output wire [9:0] pixel_y    // Y coordinate (valid when DE=1)
);
```

**Timing Parameters**:
```verilog
// Horizontal timing (pixels)
localparam H_ACTIVE     = 640;
localparam H_FRONT      = 16;
localparam H_SYNC       = 96;
localparam H_BACK       = 48;
localparam H_TOTAL      = 800;  // H_ACTIVE + H_FRONT + H_SYNC + H_BACK

localparam H_SYNC_START = H_ACTIVE + H_FRONT;           // 656
localparam H_SYNC_END   = H_ACTIVE + H_FRONT + H_SYNC; // 752

// Vertical timing (lines)
localparam V_ACTIVE     = 480;
localparam V_FRONT      = 10;
localparam V_SYNC       = 2;
localparam V_BACK       = 33;
localparam V_TOTAL      = 525;  // V_ACTIVE + V_FRONT + V_SYNC + V_BACK

localparam V_SYNC_START = V_ACTIVE + V_FRONT;           // 490
localparam V_SYNC_END   = V_ACTIVE + V_FRONT + V_SYNC; // 492
```

**Counter Logic**:
```verilog
// Horizontal counter
always @(posedge clk_pixel) begin
    if (reset) begin
        h_count <= 0;
    end else begin
        if (h_count == H_TOTAL - 1)
            h_count <= 0;
        else
            h_count <= h_count + 1;
    end
end

// Vertical counter
always @(posedge clk_pixel) begin
    if (reset) begin
        v_count <= 0;
    end else begin
        if (h_count == H_TOTAL - 1) begin  // Increment at end of line
            if (v_count == V_TOTAL - 1)
                v_count <= 0;
            else
                v_count <= v_count + 1;
        end
    end
end
```

**Sync Signal Generation**:
```verilog
// HSYNC: negative polarity (LOW during sync pulse)
always @(posedge clk_pixel) begin
    hsync <= ~((h_count >= H_SYNC_START) && (h_count < H_SYNC_END));
end

// VSYNC: negative polarity (LOW during sync pulse)
always @(posedge clk_pixel) begin
    vsync <= ~((v_count >= V_SYNC_START) && (v_count < V_SYNC_END));
end
```

**Display Enable & Coordinates**:
```verilog
// Display Enable: HIGH only during active video region
wire h_active = (h_count < H_ACTIVE);
wire v_active = (v_count < V_ACTIVE);
assign display_enable = h_active && v_active;

// Pixel coordinates (valid only when display_enable=1)
assign pixel_x = h_count;
assign pixel_y = v_count;
```

---

### 2.6 character_renderer (Scanline Pixel Generator)

**Purpose**: Generates pixel RGB values by fetching characters from buffer, looking up font data, and applying colors.

**Module Interface**:
```verilog
module character_renderer (
    input wire clk_pixel,
    input wire reset,
    input wire display_enable,

    // Pixel position from video_timing
    input wire [9:0] pixel_x,    // 0-639
    input wire [9:0] pixel_y,    // 0-479

    // Display mode
    input wire mode_80col,       // 0=40col, 1=80col

    // Character buffer interface
    output wire [11:0] char_addr,
    input wire [7:0] char_data,  // ASCII code from buffer

    // Font ROM interface
    output wire [7:0] font_char,
    output wire [3:0] font_scanline,
    input wire [7:0] font_data,  // 8-bit scanline from font

    // Color configuration
    input wire [2:0] fg_color,
    input wire [2:0] bg_color,

    // Cursor overlay
    input wire cursor_at_position,

    // Pixel output
    output reg [7:0] pixel_rgb   // 3-bit RGB expanded to 8-bit
);
```

**Character Address Calculation**:
```verilog
// Character position in grid
wire [6:0] char_x;  // 0-79 (80-col) or 0-39 (40-col)
wire [4:0] char_y;  // 0-29 (30 rows)

// For 80-column mode: char_width = 8 pixels
// For 40-column mode: char_width = 16 pixels (double-wide)
assign char_x = mode_80col ? pixel_x[9:3] : pixel_x[9:4];  // Divide by 8 or 16
assign char_y = pixel_y[9:4];  // Divide by 16 (character height)

// Character buffer address
assign char_addr = mode_80col ?
                   (char_y * 7'd80 + char_x) :  // 80-col: row*80 + col
                   (char_y * 7'd40 + char_x);   // 40-col: row*40 + col
```

**Font Lookup**:
```verilog
// Font ROM inputs
assign font_char = char_data;             // ASCII code from buffer
assign font_scanline = pixel_y[3:0];      // Which row of character (0-15)

// Font data returned is 8-bit scanline bitmap
```

**Pixel Generation Pipeline**:
```verilog
// Pipeline stage 1: Character fetch (registered)
reg [7:0] char_data_d1;
always @(posedge clk_pixel) begin
    char_data_d1 <= char_data;
end

// Pipeline stage 2: Font lookup (registered)
reg [7:0] font_data_d1;
reg [2:0] pixel_bit_sel_d1;
always @(posedge clk_pixel) begin
    font_data_d1 <= font_data;
    // Which bit of font_data for this pixel
    pixel_bit_sel_d1 <= mode_80col ?
                        pixel_x[2:0] :       // 80-col: pixel 0-7 within char
                        pixel_x[3:1];        // 40-col: pixel 0-7, doubled
end

// Pipeline stage 3: Pixel color selection
reg pixel_bit;
always @(posedge clk_pixel) begin
    // Extract pixel bit from font scanline (MSB = leftmost pixel)
    pixel_bit <= font_data_d1[7 - pixel_bit_sel_d1];
end

// Final color output (with cursor overlay)
always @(posedge clk_pixel) begin
    if (!display_enable) begin
        pixel_rgb <= 8'b00000000;  // Black during blanking
    end else if (cursor_at_position) begin
        // Cursor: inverted colors (or solid color)
        pixel_rgb <= {bg_color, bg_color, bg_color[1:0]};  // Use BG as cursor color
    end else begin
        // Normal character rendering
        pixel_rgb <= pixel_bit ?
                     {fg_color, fg_color, fg_color[1:0]} :  // Foreground
                     {bg_color, bg_color, bg_color[1:0]};   // Background
    end
end
```

**40-Column Mode Doubling**:
```verilog
// In 40-column mode, each character is 16 pixels wide
// Use same font bit for 2 consecutive pixels
// Implemented by using pixel_x[3:1] instead of pixel_x[2:0] for bit selection
```

---

### 2.7 cursor_controller (Cursor Position & Flash)

**Purpose**: Tracks cursor position, generates flash timing (~1Hz), and determines if cursor should be displayed at current pixel.

**Module Interface**:
```verilog
module cursor_controller (
    input wire clk_pixel,
    input wire reset,

    // Cursor configuration (synchronized from CPU)
    input wire [4:0] cursor_row,   // Cursor row (0-29)
    input wire [6:0] cursor_col,   // Cursor column (0-79)
    input wire cursor_enable,      // Cursor visibility enable
    input wire mode_80col,         // Display mode

    // Current pixel position
    input wire [9:0] pixel_x,
    input wire [9:0] pixel_y,

    // Timing signals
    input wire vsync,              // Vertical sync (for frame counting)

    // Output
    output wire cursor_at_position // Cursor should be displayed at this pixel
);
```

**Flash Timer**:
```verilog
// Flash at ~1Hz (toggle every 30 frames at 60Hz)
reg [5:0] flash_counter;  // Count frames (0-59)
reg flash_state;          // 0=hidden, 1=visible

always @(posedge clk_pixel) begin
    if (reset) begin
        flash_counter <= 0;
        flash_state <= 1;  // Start visible
    end else if (vsync_posedge) begin  // Detect vsync rising edge
        if (flash_counter == 29) begin
            flash_counter <= 0;
            flash_state <= ~flash_state;  // Toggle every 30 frames
        end else begin
            flash_counter <= flash_counter + 1;
        end
    end
end

// Vsync edge detection
reg vsync_d;
always @(posedge clk_pixel) vsync_d <= vsync;
wire vsync_posedge = vsync && !vsync_d;
```

**Cursor Position Matching**:
```verilog
// Determine if current pixel is within cursor character cell
wire [6:0] current_char_x = mode_80col ? pixel_x[9:3] : pixel_x[9:4];
wire [4:0] current_char_y = pixel_y[9:4];

wire cursor_char_match = (current_char_x == cursor_col) &&
                         (current_char_y == cursor_row);

// Cursor visible at this pixel?
assign cursor_at_position = cursor_enable &&
                           flash_state &&
                           cursor_char_match;
```

---

### 2.8 color_palette (3-bit RGB to 24-bit Expansion)

**Purpose**: Expands 3-bit RGB color codes to full RGB bit depth for DVI output.

**Module Interface**:
```verilog
module color_palette (
    input wire [2:0] color_3bit,  // 3-bit RGB input
    output wire [23:0] color_24bit // 24-bit RGB output (8:8:8)
);
```

**Color Mapping**:
```verilog
// 3-bit RGB: [2]=R, [1]=G, [0]=B
// Expand each bit to 8 bits by replication
// 0 → 0x00, 1 → 0xFF

assign color_24bit = {
    {8{color_3bit[2]}},  // Red: replicate bit 2 eight times
    {8{color_3bit[1]}},  // Green: replicate bit 1 eight times
    {8{color_3bit[0]}}   // Blue: replicate bit 0 eight times
};
```

**Standard 8-Color Palette**:
```
000 (0): Black   - RGB(0x00, 0x00, 0x00)
001 (1): Blue    - RGB(0x00, 0x00, 0xFF)
010 (2): Green   - RGB(0x00, 0xFF, 0x00)
011 (3): Cyan    - RGB(0x00, 0xFF, 0xFF)
100 (4): Red     - RGB(0xFF, 0x00, 0x00)
101 (5): Magenta - RGB(0xFF, 0x00, 0xFF)
110 (6): Yellow  - RGB(0xFF, 0xFF, 0x00)
111 (7): White   - RGB(0xFF, 0xFF, 0xFF)
```

---

### 2.9 dvi_transmitter (TMDS Encoding & Output)

**Purpose**: Encodes RGB pixel data into TMDS format and outputs via differential pairs using ECP5 LVDS primitives.

**Module Interface**:
```verilog
module dvi_transmitter (
    input wire clk_pixel,        // 25.175 MHz pixel clock
    input wire clk_tmds,         // 251.75 MHz TMDS serialization clock
    input wire reset,

    // Video input
    input wire [7:0] red,
    input wire [7:0] green,
    input wire [7:0] blue,
    input wire hsync,
    input wire vsync,
    input wire display_enable,

    // DVI differential outputs
    output wire tmds_clk_p,
    output wire tmds_clk_n,
    output wire tmds_data0_p,    // Blue channel
    output wire tmds_data0_n,
    output wire tmds_data1_p,    // Green channel
    output wire tmds_data1_n,
    output wire tmds_data2_p,    // Red channel
    output wire tmds_data2_n
);
```

**TMDS Encoder Instantiation**:
```verilog
// TMDS encoder for each color channel
wire [9:0] tmds_red, tmds_green, tmds_blue;

tmds_encoder tmds_enc_red (
    .clk(clk_pixel),
    .data(red),
    .c0(1'b0),           // Control bits (unused for red)
    .c1(1'b0),
    .de(display_enable),
    .tmds_out(tmds_red)
);

tmds_encoder tmds_enc_green (
    .clk(clk_pixel),
    .data(green),
    .c0(1'b0),           // Control bits (unused for green)
    .c1(1'b0),
    .de(display_enable),
    .tmds_out(tmds_green)
);

tmds_encoder tmds_enc_blue (
    .clk(clk_pixel),
    .data(blue),
    .c0(hsync),          // HSYNC encoded in blue channel during blanking
    .c1(vsync),          // VSYNC encoded in blue channel during blanking
    .de(display_enable),
    .tmds_out(tmds_blue)
);
```

**Serialization with ODDRX2F**:
```verilog
// Serialize 10-bit TMDS words to DDR output
// Note: Full serialization requires shift registers + ODDRX2F
// Reference implementation details to be extracted during hardware validation

// Simplified structure (actual implementation more complex):
oddrx2f_serializer ser_red (
    .clk_pixel(clk_pixel),
    .clk_tmds(clk_tmds),
    .data_in(tmds_red),
    .out_p(tmds_data2_p),
    .out_n(tmds_data2_n)
);

oddrx2f_serializer ser_green (
    .clk_pixel(clk_pixel),
    .clk_tmds(clk_tmds),
    .data_in(tmds_green),
    .out_p(tmds_data1_p),
    .out_n(tmds_data1_n)
);

oddrx2f_serializer ser_blue (
    .clk_pixel(clk_pixel),
    .clk_tmds(clk_tmds),
    .data_in(tmds_blue),
    .out_p(tmds_data0_p),
    .out_n(tmds_data0_n)
);

// Clock output (direct, not encoded)
oddrx2f_clock_out clk_out (
    .clk_pixel(clk_pixel),
    .clk_tmds(clk_tmds),
    .out_p(tmds_clk_p),
    .out_n(tmds_clk_n)
);
```

**Note**: Complete TMDS encoder and serializer implementation to be adapted from reference code during Phase 2 implementation.

---

## 3. State Machines

### 3.1 Clear Screen State Machine

**Location**: character_buffer module

**States**:
```verilog
localparam IDLE        = 2'b00;
localparam CLEARING    = 2'b01;
localparam CLEAR_DONE  = 2'b10;

reg [1:0] clear_state;
reg [11:0] clear_addr;
```

**State Diagram**:
```
        +------+
        | IDLE |
        +------+
            |
     clear_pulse
            |
            v
     +----------+
     | CLEARING | ----+
     +----------+     |
           ^          |
           |    (write space)
           +----------+
                      |
            addr==2399 |
                      |
                      v
                +-----------+
                | CLEAR_DONE|
                +-----------+
                      |
                (1 cycle)
                      |
                      v
                   [IDLE]
```

**State Transitions**:
```verilog
always @(posedge clk_b) begin
    case (clear_state)
        IDLE: begin
            if (clear_pulse) begin
                clear_state <= CLEARING;
                clear_addr <= 0;
            end
        end

        CLEARING: begin
            mem[clear_addr] <= 8'h20;  // Write space
            clear_addr <= clear_addr + 1;

            if (clear_addr == 2399) begin
                clear_state <= CLEAR_DONE;
            end
        end

        CLEAR_DONE: begin
            clear_state <= IDLE;
        end
    endcase
end
```

### 3.2 Scroll State Machine

**Location**: character_buffer module

**States**:
```verilog
localparam SCROLL_IDLE      = 2'b00;
localparam SCROLL_COPY      = 2'b01;
localparam SCROLL_CLEAR_END = 2'b10;

reg [1:0] scroll_state;
reg [4:0] scroll_row;
reg [6:0] scroll_col;
```

**Operation**:
- Copy lines 1-29 to lines 0-28
- Clear line 29 (bottom line)

---

## 4. Memory Layouts

### 4.1 Character Buffer Layout

**80-Column Mode**:
```
Address Calculation: addr = row * 80 + col

Row 0:  [0000] [0001] [0002] ... [0079]  (columns 0-79)
Row 1:  [0080] [0081] [0082] ... [0159]
Row 2:  [0160] [0161] [0162] ... [0239]
...
Row 29: [2320] [2321] [2322] ... [2399]

Total: 2400 bytes (80 * 30)
```

**40-Column Mode**:
```
Address Calculation: addr = row * 40 + col

Row 0:  [0000] [0001] [0002] ... [0039]  (columns 0-39)
Row 1:  [0040] [0041] [0042] ... [0079]
Row 2:  [0080] [0081] [0082] ... [0119]
...
Row 29: [1160] [1161] [1162] ... [1199]

Total: 1200 bytes (40 * 30)
Note: Uses same buffer, only first 1200 locations used
```

### 4.2 Font ROM Layout

```
Character 0x20 (space):
  Address 0x000-0x00F: 16 bytes (scanlines 0-15)

Character 0x21 ('!'):
  Address 0x010-0x01F: 16 bytes

...

Character 0x7E ('~'):
  Address 0x5E0-0x5EF: 16 bytes

Placeholder (non-printable):
  Address 0x5F0-0x5FF: 16 bytes (all 0xFF for solid block)

Total: 96 characters * 16 bytes = 1536 bytes
```

---

## 5. Timing Diagrams

### 5.1 Character Rendering Pipeline Timing

```
Clock Cycle:    0     1     2     3     4     5
                |     |     |     |     |     |
pixel_x,y:      [X0]  [X1]  [X2]  [X3]  [X4]  [X5]
                |     |     |     |     |     |
char_addr:      [A0]  [A1]  [A2]  [A3]  [A4]  [A5]
                |     |     |     |     |     |
char_data:      ---- [C0]  [C1]  [C2]  [C3]  [C4]  (1 cycle latency)
                |     |     |     |     |     |
font_lookup:    ----  ---- [F0]  [F1]  [F2]  [F3]  (1 cycle latency)
                |     |     |     |     |     |
pixel_out:      ----  ----  ---- [P0]  [P1]  [P2]  (3 cycle total latency)

Pipeline depth: 3 clocks
Compensation: Start fetching 3 pixels early (h_count - 3)
```

### 5.2 Register Write Timing (Clock Domain Crossing)

```
CPU Clock:      __‾‾__‾‾__‾‾__‾‾__‾‾__‾‾__‾‾__‾‾__‾‾__‾‾__‾‾__
                  |     |     |     |     |     |     |
CPU writes:     --|WR|--|---|---|---|---|---|---|---|---|---
register            ^
                    |
Pixel Clock:    _‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾_‾
                  |   |   |   |   |   |   |   |   |   |
Sync Stage 1:   --[X]--|D1|---|---|---|---|---|---|---|---
                            ^
Sync Stage 2:   --[X]--|X]--|D2|---|---|---|---|---|---|---
                                  ^
Safe in pixel               [Safe to use]
domain after 2
sync stages
```

---

## 6. Design Decisions & Rationale

### 6.1 Scanline Rendering vs Frame Buffer
- **Decision**: Scanline rendering
- **Rationale**: Minimizes memory usage (3KB vs 300KB), proven approach in classic systems, fits FPGA block RAM perfectly

### 6.2 30 Rows vs 25 Rows
- **Decision**: 30 rows
- **Rationale**: 480 pixels ÷ 16 pixel character height = 30 rows exactly, maximizes text capacity

### 6.3 Global Color Registers vs Per-Character Attributes
- **Decision**: Global color registers
- **Rationale**: Simplifies design, minimizes memory (no attribute byte per character), meets spec requirements

### 6.4 Cursor Rendering Method
- **Decision**: Solid block override (not XOR)
- **Rationale**: Simpler logic, clearer visibility, easier to test

### 6.5 Placeholder Glyph Design
- **Decision**: Solid block (all pixels on)
- **Rationale**: Clearly visible, easy to distinguish from printable characters, simple to implement

### 6.6 Clear Screen Implementation
- **Decision**: Hardware state machine (not CPU loop)
- **Rationale**: Faster (2400 cycles at 25MHz = 96μs vs >24ms with CPU), frees CPU for other tasks

---

## 7. Testability

Every module is designed for independent cocotb testing:

- **video_timing**: Test counter values, sync timing, DE signal correctness
- **character_buffer**: Test dual-port read/write, clear operation, scrolling
- **font_rom**: Verify font data integrity, address calculation
- **character_renderer**: Test character-to-pixel pipeline, color application
- **cursor_controller**: Verify flash timing, position matching
- **color_palette**: Test RGB expansion
- **gpu_registers**: Test register writes, clock domain crossing, auto-increment
- **dvi_transmitter**: Test TMDS encoding (unit test), serialization (hardware test)

Integration tests verify end-to-end character output with known patterns.

---

**Document Status**: Phase 1 Design Complete
**Next Step**: Create contracts/register_map.md with detailed register specifications
