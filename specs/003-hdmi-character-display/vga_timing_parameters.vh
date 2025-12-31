// =============================================================================
// VGA 640x480 @ 60Hz Timing Parameters
// =============================================================================
// VESA Standard Timing for 640x480 @ 59.940 Hz
// Pixel Clock: 25.175 MHz
//
// This file contains timing constants for implementing VGA video timing
// generators in Verilog/SystemVerilog. Include this file in your video
// timing module to use these standard parameters.
//
// Usage:
//   `include "vga_timing_parameters.vh"
//
// =============================================================================

// =============================================================================
// Horizontal Timing Parameters (in pixel clock cycles)
// =============================================================================

// Active video region
`define H_ACTIVE        640     // Visible pixels per line
`define H_ACTIVE_START  0       // First visible pixel
`define H_ACTIVE_END    639     // Last visible pixel (H_ACTIVE - 1)

// Front porch (blank time after active video)
`define H_FRONT_PORCH   16      // Horizontal front porch width
`define H_FP_START      640     // H_ACTIVE
`define H_FP_END        655     // H_FP_START + H_FRONT_PORCH - 1

// Sync pulse
`define H_SYNC_PULSE    96      // Horizontal sync pulse width
`define H_SYNC_START    656     // H_FP_END + 1
`define H_SYNC_END      751     // H_SYNC_START + H_SYNC_PULSE - 1

// Back porch (blank time before active video)
`define H_BACK_PORCH    48      // Horizontal back porch width
`define H_BP_START      752     // H_SYNC_END + 1
`define H_BP_END        799     // H_BP_START + H_BACK_PORCH - 1

// Total horizontal timing
`define H_TOTAL         800     // Total pixels per line (includes blanking)
`define H_TOTAL_MINUS1  799     // For counter comparison (H_TOTAL - 1)
`define H_BLANKING      160     // Total blanking pixels (FP + SYNC + BP)

// Horizontal sync polarity
`define H_SYNC_POLARITY 0       // 0 = negative (active low), 1 = positive (active high)
`define H_SYNC_ACTIVE   1'b0    // Active state of HSYNC (0 for negative polarity)
`define H_SYNC_IDLE     1'b1    // Idle state of HSYNC (1 for negative polarity)

// Horizontal bit width
`define H_COUNT_BITS    10      // log2(800) = 10 bits needed for h_count

// =============================================================================
// Vertical Timing Parameters (in horizontal lines)
// =============================================================================

// Active video region
`define V_ACTIVE        480     // Visible lines per frame
`define V_ACTIVE_START  0       // First visible line
`define V_ACTIVE_END    479     // Last visible line (V_ACTIVE - 1)

// Front porch (blank lines after active video)
`define V_FRONT_PORCH   10      // Vertical front porch height
`define V_FP_START      480     // V_ACTIVE
`define V_FP_END        489     // V_FP_START + V_FRONT_PORCH - 1

// Sync pulse
`define V_SYNC_PULSE    2       // Vertical sync pulse height
`define V_SYNC_START    490     // V_FP_END + 1
`define V_SYNC_END      491     // V_SYNC_START + V_SYNC_PULSE - 1

// Back porch (blank lines before active video)
`define V_BACK_PORCH    33      // Vertical back porch height
`define V_BP_START      492     // V_SYNC_END + 1
`define V_BP_END        524     // V_BP_START + V_BACK_PORCH - 1

// Total vertical timing
`define V_TOTAL         525     // Total lines per frame (includes blanking)
`define V_TOTAL_MINUS1  524     // For counter comparison (V_TOTAL - 1)
`define V_BLANKING      45      // Total blanking lines (FP + SYNC + BP)

// Vertical sync polarity
`define V_SYNC_POLARITY 0       // 0 = negative (active low), 1 = positive (active high)
`define V_SYNC_ACTIVE   1'b0    // Active state of VSYNC (0 for negative polarity)
`define V_SYNC_IDLE     1'b1    // Idle state of VSYNC (1 for negative polarity)

// Vertical bit width
`define V_COUNT_BITS    10      // log2(525) = 10 bits needed for v_count

// =============================================================================
// Pixel Clock Specification
// =============================================================================

`define PIXEL_CLOCK_HZ      25175000    // 25.175 MHz (exact VESA standard)
`define PIXEL_CLOCK_MHZ     25.175      // For documentation/comments
`define PIXEL_CLOCK_NS      39.72       // Clock period in nanoseconds

// Common approximations (for PLL configuration)
`define PIXEL_CLOCK_25_0    25000000    // 25.0 MHz (-0.69% error)
`define PIXEL_CLOCK_25_2    25200000    // 25.2 MHz (+0.10% error)

// =============================================================================
// Refresh Rates
// =============================================================================

`define H_FREQ_HZ       31469       // Horizontal line frequency (Hz)
`define H_FREQ_KHZ      31.469      // Horizontal line frequency (kHz)
`define H_PERIOD_US     31.778      // Horizontal line period (microseconds)

`define V_FREQ_HZ       59.940      // Vertical frame frequency (Hz)
`define V_FREQ_HZ_APPROX 60         // Approximate vertical frequency
`define V_PERIOD_MS     16.683      // Vertical frame period (milliseconds)

// =============================================================================
// Timing Calculations (for reference/verification)
// =============================================================================

// Total pixels per frame
`define TOTAL_PIXELS    420000      // H_TOTAL * V_TOTAL = 800 * 525

// Active pixels per frame
`define ACTIVE_PIXELS   307200      // H_ACTIVE * V_ACTIVE = 640 * 480

// =============================================================================
// Character Mode Parameters (for text display)
// =============================================================================
// For 80 columns x 30 rows with 8x16 pixel characters

`define CHAR_WIDTH      8           // Character width in pixels
`define CHAR_HEIGHT     16          // Character height in pixels
`define CHAR_COLS       80          // Characters per line (640 / 8)
`define CHAR_ROWS       30          // Character lines (480 / 16)
`define CHAR_TOTAL      2400        // Total characters (80 * 30)

// Character position bit fields
`define CHAR_X_BITS     7           // log2(80) = 7 bits for column
`define CHAR_Y_BITS     5           // log2(30) = 5 bits for row
`define CHAR_ADDR_BITS  12          // log2(2400) = 12 bits for address

// Pixel-within-character bit positions
`define CHAR_PIXEL_X_BITS   3       // log2(8) = 3 bits (pixel X in char)
`define CHAR_PIXEL_Y_BITS   4       // log2(16) = 4 bits (pixel Y in char)

// =============================================================================
// Helper Macros for Counter Comparisons
// =============================================================================

// Horizontal region checks
`define IS_H_ACTIVE(h)      ((h) < `H_ACTIVE)
`define IS_H_FRONT(h)       ((h) >= `H_FP_START && (h) <= `H_FP_END)
`define IS_H_SYNC(h)        ((h) >= `H_SYNC_START && (h) <= `H_SYNC_END)
`define IS_H_BACK(h)        ((h) >= `H_BP_START && (h) <= `H_BP_END)
`define IS_H_BLANKING(h)    ((h) >= `H_ACTIVE)

// Vertical region checks
`define IS_V_ACTIVE(v)      ((v) < `V_ACTIVE)
`define IS_V_FRONT(v)       ((v) >= `V_FP_START && (v) <= `V_FP_END)
`define IS_V_SYNC(v)        ((v) >= `V_SYNC_START && (v) <= `V_SYNC_END)
`define IS_V_BACK(v)        ((v) >= `V_BP_START && (v) <= `V_BP_END)
`define IS_V_BLANKING(v)    ((v) >= `V_ACTIVE)

// Display enable check
`define IS_DISPLAY_ACTIVE(h,v)  (`IS_H_ACTIVE(h) && `IS_V_ACTIVE(v))

// Sync pulse checks
`define H_SYNC_VALUE(h)     (`IS_H_SYNC(h) ? `H_SYNC_ACTIVE : `H_SYNC_IDLE)
`define V_SYNC_VALUE(v)     (`IS_V_SYNC(v) ? `V_SYNC_ACTIVE : `V_SYNC_IDLE)

// =============================================================================
// Character Mode Helper Macros
// =============================================================================

// Extract character position from pixel coordinates
`define GET_CHAR_X(h)       ((h) >> 3)          // h / 8
`define GET_CHAR_Y(v)       ((v) >> 4)          // v / 16

// Extract pixel-within-character coordinates
`define GET_CHAR_PIXEL_X(h) ((h) & 3'h7)        // h % 8
`define GET_CHAR_PIXEL_Y(v) ((v) & 4'hF)        // v % 16

// Calculate character buffer address
`define CHAR_ADDR(x,y)      (((y) * `CHAR_COLS) + (x))

// Alternative: calculate from pixel coordinates directly
`define CHAR_ADDR_FROM_PXL(h,v)  (`CHAR_ADDR(`GET_CHAR_X(h), `GET_CHAR_Y(v)))

// =============================================================================
// Example Usage in Video Timing Module
// =============================================================================
//
// module video_timing (
//     input wire clk_pixel,     // 25.175 MHz pixel clock
//     input wire reset,
//     output reg hsync,
//     output reg vsync,
//     output wire display_enable,
//     output reg [`H_COUNT_BITS-1:0] h_count,
//     output reg [`V_COUNT_BITS-1:0] v_count
// );
//
// // Horizontal counter
// always @(posedge clk_pixel) begin
//     if (reset)
//         h_count <= 0;
//     else if (h_count == `H_TOTAL_MINUS1)
//         h_count <= 0;
//     else
//         h_count <= h_count + 1;
// end
//
// // Vertical counter
// always @(posedge clk_pixel) begin
//     if (reset)
//         v_count <= 0;
//     else if (h_count == `H_TOTAL_MINUS1) begin
//         if (v_count == `V_TOTAL_MINUS1)
//             v_count <= 0;
//         else
//             v_count <= v_count + 1;
//     end
// end
//
// // Sync signal generation (negative polarity)
// always @(posedge clk_pixel) begin
//     hsync <= ~`IS_H_SYNC(h_count);
//     vsync <= ~`IS_V_SYNC(v_count);
// end
//
// // Display enable generation
// assign display_enable = `IS_DISPLAY_ACTIVE(h_count, v_count);
//
// endmodule
//
// =============================================================================

// =============================================================================
// Testbench Verification Values
// =============================================================================
// These values can be used to verify correct timing in simulation

// Key frame timing verification points
`define TB_FIRST_PIXEL_H    0       // First visible pixel h_count
`define TB_FIRST_PIXEL_V    0       // First visible pixel v_count
`define TB_LAST_PIXEL_H     639     // Last visible pixel h_count
`define TB_LAST_PIXEL_V     479     // Last visible pixel v_count
`define TB_H_SYNC_ASSERT    656     // h_count when HSYNC goes low
`define TB_H_SYNC_DEASSERT  752     // h_count when HSYNC goes high
`define TB_V_SYNC_ASSERT    490     // v_count when VSYNC goes low
`define TB_V_SYNC_DEASSERT  492     // v_count when VSYNC goes high
`define TB_LINE_END         799     // Last h_count before wrap
`define TB_FRAME_END        524     // Last v_count before wrap

// Expected timing measurements (for testbench assertions)
`define TB_EXPECT_PIXEL_CLK_MHZ     25.175
`define TB_EXPECT_H_FREQ_KHZ        31.469
`define TB_EXPECT_V_FREQ_HZ         59.940
`define TB_TOLERANCE_PERCENT        0.5     // ±0.5% tolerance

// =============================================================================
// Debug Parameters
// =============================================================================

// Counter comparison watchpoints for debugging
`define DBG_H_QUARTER       160     // 1/4 through active line
`define DBG_H_HALF          320     // 1/2 through active line
`define DBG_H_3QUARTER      480     // 3/4 through active line
`define DBG_V_QUARTER       120     // 1/4 through active frame
`define DBG_V_HALF          240     // 1/2 through active frame
`define DBG_V_3QUARTER      360     // 3/4 through active frame

// =============================================================================
// Standards Compliance Information
// =============================================================================

`define VGA_STANDARD        "VESA DMT"
`define VGA_DMT_ID          8'h04
`define VGA_RESOLUTION      "640x480"
`define VGA_REFRESH_RATE    "60Hz"
`define VGA_ASPECT_RATIO    "4:3"

// =============================================================================
// End of VGA Timing Parameters
// =============================================================================
