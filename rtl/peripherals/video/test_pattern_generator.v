/*
Test Pattern Generator
retrocpu DVI Character Display GPU

Generates various test patterns for validating DVI output:
- Color bars (8 vertical bars: white, yellow, cyan, green, magenta, red, blue, black)
- Checkerboard pattern
- Grid pattern
- Solid color

Useful for:
- Hardware validation
- Monitor compatibility testing
- Timing verification
- Signal quality assessment

Created: 2025-12-28
*/

module test_pattern_generator(
    input  wire        clk,           // Pixel clock
    input  wire        rst_n,         // Active-low reset

    input  wire [9:0]  h_count,       // Horizontal counter (0-639 visible)
    input  wire [9:0]  v_count,       // Vertical counter (0-479 visible)
    input  wire        video_active,  // High during visible region

    input  wire [1:0]  pattern_sel,   // Pattern selection
                                      // 00 = Color bars
                                      // 01 = Checkerboard
                                      // 10 = Grid
                                      // 11 = Solid color

    output reg  [7:0]  red,           // 8-bit red output
    output reg  [7:0]  green,         // 8-bit green output
    output reg  [7:0]  blue           // 8-bit blue output
);

//=============================================================================
// Pattern Generation
//=============================================================================

// Color bars: 8 vertical bars (exactly 80 pixels each)
// 640 pixels / 8 bars = 80 pixels per bar
// bar_index = h_count / 80 gives us exactly 8 bars (0-7)
wire [2:0] bar_index = h_count / 80;

// Checkerboard: 32x32 pixel squares
wire checkerboard = h_count[5] ^ v_count[5];

// Grid: Lines every 80 pixels horizontal and 60 pixels vertical
wire grid_h = (h_count[6:0] < 2);     // Vertical lines every 80 pixels
wire grid_v = (v_count[5:0] < 2);     // Horizontal lines every 60 pixels
wire grid = grid_h | grid_v;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        red   <= 8'h00;
        green <= 8'h00;
        blue  <= 8'h00;
    end else begin
        if (video_active) begin
            case (pattern_sel)
                2'b00: begin
                    // Color bars pattern
                    case (bar_index)
                        3'b000: begin red <= 8'hFF; green <= 8'hFF; blue <= 8'hFF; end // White
                        3'b001: begin red <= 8'hFF; green <= 8'hFF; blue <= 8'h00; end // Yellow
                        3'b010: begin red <= 8'h00; green <= 8'hFF; blue <= 8'hFF; end // Cyan
                        3'b011: begin red <= 8'h00; green <= 8'hFF; blue <= 8'h00; end // Green
                        3'b100: begin red <= 8'hFF; green <= 8'h00; blue <= 8'hFF; end // Magenta
                        3'b101: begin red <= 8'hFF; green <= 8'h00; blue <= 8'h00; end // Red
                        3'b110: begin red <= 8'h00; green <= 8'h00; blue <= 8'hFF; end // Blue
                        3'b111: begin red <= 8'h00; green <= 8'h00; blue <= 8'h00; end // Black
                    endcase
                end

                2'b01: begin
                    // Checkerboard pattern (black and white)
                    if (checkerboard) begin
                        red   <= 8'hFF;
                        green <= 8'hFF;
                        blue  <= 8'hFF;
                    end else begin
                        red   <= 8'h00;
                        green <= 8'h00;
                        blue  <= 8'h00;
                    end
                end

                2'b10: begin
                    // Grid pattern (white lines on blue background)
                    if (grid) begin
                        red   <= 8'hFF;
                        green <= 8'hFF;
                        blue  <= 8'hFF;
                    end else begin
                        red   <= 8'h00;
                        green <= 8'h40;
                        blue  <= 8'h80;
                    end
                end

                2'b11: begin
                    // Solid color (medium gray)
                    red   <= 8'h80;
                    green <= 8'h80;
                    blue  <= 8'h80;
                end
            endcase
        end else begin
            // Blanking: output black
            red   <= 8'h00;
            green <= 8'h00;
            blue  <= 8'h00;
        end
    end
end

endmodule
