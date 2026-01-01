//==============================================================================
// gpu_top.v - Complete GPU Subsystem with DVI Output
//==============================================================================
// Project: RetroCPU - DVI Character Display GPU
// Description: Top-level GPU wrapper integrating character display pipeline
//              and DVI/TMDS transmission for HDMI/DVI output
//
// Author: RetroCPU Project
// License: MIT
// Created: 2025-12-28
//
// Features:
//   - Complete GPU subsystem for character display via HDMI/DVI
//   - Integrates gpu_core (character rendering) and dvi_transmitter (TMDS)
//   - 640x480@60Hz VGA/DVI output with 8-bit RGB color
//   - 40-column and 80-column text modes
//   - Memory-mapped register interface for CPU control
//   - DDR TMDS output for ECP5 FPGA LVDS pins
//
// Integrated Modules:
//   1. gpu_core - Character display pipeline (timing, rendering, registers)
//   2. dvi_transmitter - TMDS encoding and serialization
//
// Clock Domains:
//   - clk_cpu: CPU/system clock domain (for register access)
//   - clk_pixel: Pixel clock (25 MHz for 640x480@60Hz VGA timing)
//   - clk_tmds: TMDS clock (125 MHz, 5x pixel clock for DDR serialization)
//
// CPU Bus Interface:
//   - Address range: 0xC010-0xC016 (7 registers)
//   - 8-bit data bus (data_in/data_out)
//   - Write enable (we) and read enable (re) control signals
//   - See gpu_registers.v in gpu_core for detailed register map
//
// TMDS Output:
//   - DDR differential output for ECP5 FPGA LVDS primitives
//   - 4 channels: Red, Green, Blue, Clock
//   - Each channel: 2-bit DDR (gpdi_dp/gpdi_dn pairs)
//
// Register Map (Base 0xC010):
//   0xC010: CHAR_DATA   - Write character at cursor position
//   0xC011: CURSOR_ROW  - Cursor row (0-29)
//   0xC012: CURSOR_COL  - Cursor column (0-39 or 0-79)
//   0xC013: CONTROL     - Mode control (clear, 40/80-col, cursor enable)
//   0xC014: FG_COLOR    - Foreground color (3-bit RGB)
//   0xC015: BG_COLOR    - Background color (3-bit RGB)
//   0xC016: STATUS      - GPU status (ready, vsync)
//
//==============================================================================

module gpu_top(
    // Clock and reset
    input  wire        clk_cpu,         // CPU/system clock domain
    input  wire        clk_pixel,       // Pixel clock (25 MHz for 640x480@60Hz)
    input  wire        clk_tmds,        // TMDS clock (125 MHz, 5x pixel clock)
    input  wire        rst_n,           // Active-low reset (async, all domains)

    // CPU bus interface (clk_cpu domain)
    input  wire [3:0]  addr,            // Register address offset (0x0-0xF)
    input  wire [7:0]  data_in,         // Data from CPU (for writes)
    output wire [7:0]  data_out,        // Data to CPU (for reads)
    input  wire        we,              // Write enable
    input  wire        re,              // Read enable

    // TMDS parallel output (2-bit DDR data for each channel)
    // These will be fed to ODDRX1F primitives at the top level
    output wire [1:0]  tmds_clk_out,   // TMDS clock channel DDR data
    output wire [1:0]  tmds_red_out,   // TMDS red channel DDR data
    output wire [1:0]  tmds_green_out, // TMDS green channel DDR data
    output wire [1:0]  tmds_blue_out   // TMDS blue channel DDR data
);

    //==========================================================================
    // Internal Signals - GPU Core to DVI Transmitter
    //==========================================================================

    // RGB video signals (8-bit per channel)
    wire [7:0] rgb_red;                 // Red channel from gpu_core
    wire [7:0] rgb_green;               // Green channel from gpu_core
    wire [7:0] rgb_blue;                // Blue channel from gpu_core

    // Sync and control signals
    wire       hsync;                   // Horizontal sync (active-low from gpu_core)
    wire       vsync;                   // Vertical sync (active-low from gpu_core)
    wire       video_active;            // High during visible region

    // Blanking signal for DVI transmitter (inverse of video_active)
    wire       video_blank;
    assign video_blank = ~video_active;

    //==========================================================================
    // Internal Signals - TMDS Output (Positive DDR Pairs)
    //==========================================================================

    wire [1:0] tmds_red;                // TMDS red channel (DDR, positive)
    wire [1:0] tmds_green;              // TMDS green channel (DDR, positive)
    wire [1:0] tmds_blue;               // TMDS blue channel (DDR, positive)
    wire [1:0] tmds_clk;                // TMDS clock channel (DDR, positive)

    //==========================================================================
    // Module Instantiation
    //==========================================================================

    //--------------------------------------------------------------------------
    // 1. GPU Core - Character Display Pipeline
    //    Generates RGB video, sync signals, and handles CPU interface
    //--------------------------------------------------------------------------
    gpu_core gpu_core_inst(
        // Clock and reset
        .clk_cpu       (clk_cpu),        // CPU clock domain
        .clk_pixel     (clk_pixel),      // Pixel clock (25 MHz)
        .rst_n         (rst_n),          // Active-low reset

        // CPU bus interface (clk_cpu domain)
        .addr          (addr),           // Register address (4-bit offset)
        .data_in       (data_in),        // Data from CPU
        .data_out      (data_out),       // Data to CPU
        .we            (we),             // Write enable
        .re            (re),             // Read enable

        // Video output (clk_pixel domain)
        .red           (rgb_red),        // Red channel (8-bit)
        .green         (rgb_green),      // Green channel (8-bit)
        .blue          (rgb_blue),       // Blue channel (8-bit)
        .hsync         (hsync),          // Horizontal sync (active-low)
        .vsync         (vsync),          // Vertical sync (active-low)
        .video_active  (video_active)    // High during visible region
    );

    //--------------------------------------------------------------------------
    // 2. DVI Transmitter - TMDS Encoding and Serialization
    //    Converts RGB + sync to TMDS differential output for HDMI/DVI
    //--------------------------------------------------------------------------
    dvi_transmitter dvi_transmitter_inst(
        // Clock inputs
        .pclk          (clk_pixel),      // Pixel clock (25 MHz)
        .tmds_clk      (clk_tmds),       // TMDS clock (125 MHz)

        // RGB video input (8-bit per channel)
        .in_red        (rgb_red),        // Red channel
        .in_green      (rgb_green),      // Green channel
        .in_blue       (rgb_blue),       // Blue channel

        // Sync and control inputs
        .in_blank      (video_blank),    // Blanking (inverse of video_active)
        .in_vsync      (vsync),          // Vertical sync (active-low)
        .in_hsync      (hsync),          // Horizontal sync (active-low)

        // TMDS output (DDR, 2 bits per channel)
        .out_tmds_red  (tmds_red),       // Red channel DDR output
        .out_tmds_green(tmds_green),     // Green channel DDR output
        .out_tmds_blue (tmds_blue),      // Blue channel DDR output
        .out_tmds_clk  (tmds_clk)        // Clock channel DDR output
    );

    //==========================================================================
    // Output Assignments - TMDS Parallel Data
    //==========================================================================
    // Connect internal TMDS signals to output ports
    // DDR serialization will be performed at the top level (soc_top.v)

    assign tmds_clk_out   = tmds_clk;
    assign tmds_red_out   = tmds_red;
    assign tmds_green_out = tmds_green;
    assign tmds_blue_out  = tmds_blue;

    //==========================================================================
    // Notes on Signal Conversion
    //==========================================================================
    //
    // 1. Blanking Signal:
    //    - gpu_core provides video_active (1=active video, 0=blanking)
    //    - dvi_transmitter expects in_blank (1=blanking, 0=active video)
    //    - Conversion: video_blank = ~video_active
    //
    // 2. Sync Signals:
    //    - gpu_core outputs hsync/vsync as active-low (VGA standard)
    //    - dvi_transmitter expects active-low sync signals
    //    - No conversion needed, direct pass-through
    //
    // 3. TMDS Differential Pairs:
    //    - dvi_transmitter outputs 2-bit DDR data for each channel
    //    - LVDS output primitives expect P (positive) and N (negative) pairs
    //    - N signals are inverted P signals for true differential signaling
    //
    //==========================================================================

    //==========================================================================
    // Notes on Clock Relationships
    //==========================================================================
    //
    // For 640x480@60Hz VGA/DVI timing:
    //   - clk_pixel = 25.175 MHz (typically rounded to 25 MHz)
    //   - clk_tmds  = 125 MHz (5x pixel clock for 10:2 DDR serialization)
    //
    // TMDS Serialization:
    //   - Each pixel generates 10 bits of TMDS-encoded data
    //   - With DDR output, each TMDS clock edge outputs 2 bits
    //   - 5 TMDS clock cycles = 10 bits = 1 pixel
    //   - Hence: clk_tmds = 5 × clk_pixel
    //
    // Clock Generation (typically in top-level or PLL):
    //   - Use PLL to generate clk_pixel (25 MHz) and clk_tmds (125 MHz)
    //   - Ensure phase alignment for proper TMDS serialization
    //
    //==========================================================================

    //==========================================================================
    // Notes on FPGA Pin Constraints
    //==========================================================================
    //
    // The TMDS output pins must be routed to LVDS-capable differential pairs:
    //
    // Example LPF constraints for Colorlight i5 board:
    //   LOCATE COMP "gpdi_dp_red[0]"   SITE "A16";  // Red P
    //   LOCATE COMP "gpdi_dn_red[0]"   SITE "B16";  // Red N
    //   LOCATE COMP "gpdi_dp_green[0]" SITE "A14";  // Green P
    //   LOCATE COMP "gpdi_dn_green[0]" SITE "C14";  // Green N
    //   LOCATE COMP "gpdi_dp_blue[0]"  SITE "A12";  // Blue P
    //   LOCATE COMP "gpdi_dn_blue[0]"  SITE "A13";  // Blue N
    //   LOCATE COMP "gpdi_dp_clk[0]"   SITE "A17";  // Clock P
    //   LOCATE COMP "gpdi_dn_clk[0]"   SITE "B18";  // Clock N
    //
    // Set I/O standards:
    //   IOBUF PORT "gpdi_dp_*" IO_TYPE=LVCMOS33D;
    //
    //==========================================================================

    //==========================================================================
    // Notes on CPU Interface Usage
    //==========================================================================
    //
    // To use the GPU from CPU firmware:
    //
    // 1. Set display mode:
    //    Write 0x00 to CONTROL (0xC013) for 40-column mode
    //    Write 0x01 to CONTROL (0xC013) for 80-column mode
    //
    // 2. Set colors:
    //    Write 3-bit RGB to FG_COLOR (0xC014) - 0b00000RGB
    //    Write 3-bit RGB to BG_COLOR (0xC015) - 0b00000RGB
    //
    // 3. Position cursor:
    //    Write row (0-29) to CURSOR_ROW (0xC011)
    //    Write column (0-39/79) to CURSOR_COL (0xC012)
    //
    // 4. Write character:
    //    Write ASCII code to CHAR_DATA (0xC010)
    //    (Automatically advances cursor to next position)
    //
    // 5. Check status:
    //    Read STATUS (0xC016) - bit 7: ready, bit 0: vsync
    //
    // Example: Print "Hello" at row 10, column 5:
    //    *((volatile uint8_t*)0xC011) = 10;    // Set row
    //    *((volatile uint8_t*)0xC012) = 5;     // Set column
    //    *((volatile uint8_t*)0xC010) = 'H';   // Write 'H'
    //    *((volatile uint8_t*)0xC010) = 'e';   // Write 'e'
    //    *((volatile uint8_t*)0xC010) = 'l';   // Write 'l'
    //    *((volatile uint8_t*)0xC010) = 'l';   // Write 'l'
    //    *((volatile uint8_t*)0xC010) = 'o';   // Write 'o'
    //
    //==========================================================================

endmodule
