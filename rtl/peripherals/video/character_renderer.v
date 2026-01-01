//==============================================================================
// character_renderer.v - Character Rendering Pipeline for Text Display
//==============================================================================
// Project: RetroCPU - DVI Character Display GPU
// Description: Converts character codes to pixel data for display output
//
// Features:
//   - Dual mode operation: 40-column and 80-column text display
//   - Scanline-based rendering (processes one horizontal line at a time)
//   - Pipelined architecture for efficient operation
//   - 8x16 pixel character cells
//   - Configurable foreground/background colors (3-bit RGB)
//
// Display Modes:
//   40-Column Mode (mode_80col = 0):
//     - 40 characters per row × 30 rows = 1200 characters
//     - Each character: 16 pixels wide (8 font pixels doubled horizontally)
//     - Screen width: 40 × 16 = 640 pixels
//
//   80-Column Mode (mode_80col = 1):
//     - 80 characters per row × 30 rows = 2400 characters
//     - Each character: 8 pixels wide (native font pixel width)
//     - Screen width: 80 × 8 = 640 pixels
//
// Character Cell:
//   - Width: 8 pixels (font data), displayed as 8 or 16 pixels depending on mode
//   - Height: 16 pixels (scanlines)
//   - Screen height: 30 × 16 = 480 pixels
//
// Color Format:
//   - Input: 3-bit RGB (1 bit each for R, G, B)
//   - Output: 24-bit RGB (8 bits per channel)
//   - Color expansion: 0 → 0x00, 1 → 0xFF
//
// Pipeline Stages:
//   Stage 1: Calculate character position and address from h_count/v_count
//   Stage 2: Read character code from character buffer (1 cycle delay)
//   Stage 3: Read font pixels from font ROM (1 cycle delay)
//   Stage 4: Extract pixel, apply color, output RGB
//
// Timing:
//   - Total pipeline depth: 3 cycles
//   - Requires pre-fetching characters ahead of current display position
//   - Blank pixels output during video blanking (video_active = 0)
//
//==============================================================================

module character_renderer(
    input  wire        clk,             // Pixel clock (25 MHz)
    input  wire        rst_n,           // Active-low reset

    // Video timing inputs
    input  wire [9:0]  h_count,         // Horizontal pixel position (0-639)
    input  wire [9:0]  v_count,         // Vertical pixel position (0-479)
    input  wire        video_active,    // High during visible region

    // Mode and color configuration
    input  wire        mode_80col,      // 0=40-column, 1=80-column
    input  wire [2:0]  fg_color,        // Foreground color (3-bit RGB)
    input  wire [2:0]  bg_color,        // Background color (3-bit RGB)

    // Character buffer interface
    output wire [10:0] char_addr,       // Address to character buffer
    input  wire [7:0]  char_data,       // Character code from buffer

    // Font ROM interface
    output wire [7:0]  font_char,       // Character code to font ROM
    output wire [3:0]  font_scanline,   // Scanline (0-15)
    input  wire [7:0]  font_pixels,     // 8 pixels from font ROM

    // Pixel output (to DVI encoder)
    output reg  [7:0]  red,             // Red channel (8-bit)
    output reg  [7:0]  green,           // Green channel (8-bit)
    output reg  [7:0]  blue             // Blue channel (8-bit)
);

    //==========================================================================
    // Pipeline Stage 1: Calculate Character Position and Address
    //==========================================================================

    // Pipeline delay compensation:
    // - Character buffer read: 1 cycle
    // - Font ROM read: 1 cycle
    // - h_count_d2 delay: 2 cycles
    // Both data and position align after 2 cycles, so no prefetch offset needed
    wire [9:0] h_fetch = h_count;

    // Calculate character column based on display mode
    // 40-col: Each character is 16 pixels wide (char_col = h_fetch / 16)
    // 80-col: Each character is 8 pixels wide (char_col = h_fetch / 8)
    wire [5:0] char_col_40 = h_fetch[9:4];  // Divide by 16 (shift right 4 bits)
    wire [6:0] char_col_80 = h_fetch[9:3];  // Divide by 8 (shift right 3 bits)

    // Select character column based on mode
    wire [6:0] char_col = mode_80col ? char_col_80 : {1'b0, char_col_40};

    // Calculate character row (same for both modes)
    // Each character is 16 pixels tall (char_row = v_count / 16)
    wire [4:0] char_row = v_count[9:4];  // Divide by 16 (shift right 4 bits)

    // Calculate character buffer address
    // 40-col: address = row * 40 + col = row * 32 + row * 8 + col
    // 80-col: address = row * 80 + col = row * 64 + row * 16 + col
    wire [10:0] char_addr_40 = {char_row, 5'b0} + {char_row, 3'b0} + {5'b0, char_col_40};
    wire [10:0] char_addr_80 = {char_row, 6'b0} + {char_row, 4'b0} + {4'b0, char_col_80};

    // Select character address based on mode
    assign char_addr = mode_80col ? char_addr_80 : char_addr_40;

    // Calculate scanline within character (0-15)
    wire [3:0] char_scanline = v_count[3:0];  // Lower 4 bits of v_count

    //==========================================================================
    // Pipeline Stage 2: Character Buffer Read (Registered)
    //==========================================================================

    // Pipeline registers for stage 2
    reg [9:0]  h_count_d1;
    reg [9:0]  v_count_d1;
    reg        video_active_d1;
    reg        mode_80col_d1;
    reg [3:0]  char_scanline_d1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            h_count_d1      <= 0;
            v_count_d1      <= 0;
            video_active_d1 <= 0;
            mode_80col_d1   <= 0;
            char_scanline_d1 <= 0;
        end else begin
            h_count_d1      <= h_count;
            v_count_d1      <= v_count;
            video_active_d1 <= video_active;
            mode_80col_d1   <= mode_80col;
            char_scanline_d1 <= char_scanline;
        end
    end

    // Font ROM inputs: character code comes from buffer (1 cycle delayed)
    assign font_char = char_data;
    assign font_scanline = char_scanline_d1;

    //==========================================================================
    // Pipeline Stage 3: Font ROM Read (Registered)
    //==========================================================================

    // Pipeline registers for stage 3
    reg [9:0]  h_count_d2;
    reg [9:0]  v_count_d2;
    reg        video_active_d2;
    reg        mode_80col_d2;
    reg [2:0]  fg_color_d2;
    reg [2:0]  bg_color_d2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            h_count_d2      <= 0;
            v_count_d2      <= 0;
            video_active_d2 <= 0;
            mode_80col_d2   <= 0;
            fg_color_d2     <= 0;
            bg_color_d2     <= 0;
        end else begin
            h_count_d2      <= h_count_d1;
            v_count_d2      <= v_count_d1;
            video_active_d2 <= video_active_d1;
            mode_80col_d2   <= mode_80col_d1;
            fg_color_d2     <= fg_color;
            bg_color_d2     <= bg_color;
        end
    end

    //==========================================================================
    // Pipeline Stage 4: Pixel Extraction and Color Application
    //==========================================================================

    // Calculate pixel position within character
    // 40-col: Each font pixel is displayed as 2 screen pixels (doubled horizontally)
    //         pixel_x = (h_count % 16) / 2 = h_count[3:1]
    // 80-col: Font pixels are displayed at native width
    //         pixel_x = h_count % 8 = h_count[2:0]

    wire [2:0] pixel_x_40 = h_count_d2[3:1];  // Divide by 2 for doubled pixels
    wire [2:0] pixel_x_80 = h_count_d2[2:0];  // Native pixel position
    wire [2:0] pixel_x = mode_80col_d2 ? pixel_x_80 : pixel_x_40;

    // Extract the specific pixel bit from font_pixels
    // Font data is MSB first: pixel 0 = bit 7, pixel 7 = bit 0
    wire [2:0] pixel_bit_index = 3'd7 - pixel_x;
    wire pixel_on = font_pixels[pixel_bit_index];

    // Color expansion: Convert 3-bit RGB to 8-bit per channel
    // 0 → 0x00, 1 → 0xFF
    wire [7:0] fg_r = fg_color_d2[2] ? 8'hFF : 8'h00;
    wire [7:0] fg_g = fg_color_d2[1] ? 8'hFF : 8'h00;
    wire [7:0] fg_b = fg_color_d2[0] ? 8'hFF : 8'h00;

    wire [7:0] bg_r = bg_color_d2[2] ? 8'hFF : 8'h00;
    wire [7:0] bg_g = bg_color_d2[1] ? 8'hFF : 8'h00;
    wire [7:0] bg_b = bg_color_d2[0] ? 8'hFF : 8'h00;

    // Select foreground or background color based on pixel value
    wire [7:0] pixel_r = pixel_on ? fg_r : bg_r;
    wire [7:0] pixel_g = pixel_on ? fg_g : bg_g;
    wire [7:0] pixel_b = pixel_on ? fg_b : bg_b;

    // Output pixel color (black during blanking)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            red   <= 8'h00;
            green <= 8'h00;
            blue  <= 8'h00;
        end else begin
            if (video_active_d2) begin
                // Character rendering
                red   <= pixel_r;
                green <= pixel_g;
                blue  <= pixel_b;
            end else begin
                // Output black during blanking period
                red   <= 8'h00;
                green <= 8'h00;
                blue  <= 8'h00;
            end
        end
    end

endmodule
