`timescale 1ns / 1ps

//
// uart_rx_7seg_test.v - Standalone UART RX Test with 7-Segment Display
//
// Receives characters via UART RX and displays the lower nibble on 7-segment display
// Completely bypasses CPU to test UART RX hardware in isolation
//

module uart_rx_7seg_test (
    // Clock and reset
    input  wire clk_25mhz,         // P3: 25 MHz system clock
    input  wire reset_button_n,    // T1: Reset button (active-low)

    // UART
    input  wire uart_rx,           // J18: UART RX from USB bridge

    // 7-Segment Display
    output wire seg_a,
    output wire seg_b,
    output wire seg_c,
    output wire seg_d,
    output wire seg_e,
    output wire seg_f,
    output wire seg_g,
    output wire seg_select,

    // Debug LEDs
    output wire [3:0] led
);

    // ========================================================================
    // Reset Controller
    // ========================================================================

    reg [7:0] reset_counter;
    reg system_rst;

    always @(posedge clk_25mhz) begin
        if (!reset_button_n) begin
            reset_counter <= 8'hFF;
            system_rst <= 1'b1;
        end else if (reset_counter != 0) begin
            reset_counter <= reset_counter - 1;
            system_rst <= 1'b1;
        end else begin
            system_rst <= 1'b0;
        end
    end

    // ========================================================================
    // UART RX Instance
    // ========================================================================

    wire [7:0] rx_data;
    wire rx_ready;

    uart_rx #(
        .CLK_FREQ(25000000),
        .BAUD_RATE(115200)
    ) uart_rx_inst (
        .clk(clk_25mhz),
        .rst(system_rst),
        .rx(uart_rx),
        .rx_data(rx_data),
        .rx_ready(rx_ready)
    );

    // ========================================================================
    // Capture received character
    // ========================================================================

    reg [7:0] last_char;
    reg char_received;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            last_char <= 8'h00;
            char_received <= 1'b0;
        end else begin
            if (rx_ready) begin
                last_char <= rx_data;
                char_received <= 1'b1;
            end
        end
    end

    // ========================================================================
    // Slow counter for display test (counts 0-F every ~1 second)
    // ========================================================================

    reg [27:0] counter;
    always @(posedge clk_25mhz) begin
        if (system_rst)
            counter <= 0;
        else
            counter <= counter + 1;
    end

    // ========================================================================
    // 7-Segment Display Driver
    // ========================================================================
    // Display the lower nibble of the received character
    // OR if no character received yet, show a counting pattern

    wire [3:0] display_value = char_received ? last_char[3:0] : counter[27:24];
    reg [6:0] segments;

    // Select single digit (always on)
    assign seg_select = 1'b1;

    // 7-segment decoder (common anode, active low - inverted)
    always @(*) begin
        case (display_value)
            4'h0: segments = ~7'b0111111;  // 0
            4'h1: segments = ~7'b0000110;  // 1
            4'h2: segments = ~7'b1011011;  // 2
            4'h3: segments = ~7'b1001111;  // 3
            4'h4: segments = ~7'b1100110;  // 4
            4'h5: segments = ~7'b1101101;  // 5
            4'h6: segments = ~7'b1111101;  // 6
            4'h7: segments = ~7'b0000111;  // 7
            4'h8: segments = ~7'b1111111;  // 8
            4'h9: segments = ~7'b1101111;  // 9
            4'hA: segments = ~7'b1110111;  // A
            4'hB: segments = ~7'b1111100;  // b
            4'hC: segments = ~7'b0111001;  // C
            4'hD: segments = ~7'b1011110;  // d
            4'hE: segments = ~7'b1111001;  // E
            4'hF: segments = ~7'b1110001;  // F
        endcase
    end

    assign seg_a = segments[0];
    assign seg_b = segments[1];
    assign seg_c = segments[2];
    assign seg_d = segments[3];
    assign seg_e = segments[4];
    assign seg_f = segments[5];
    assign seg_g = segments[6];

    // ========================================================================
    // Debug LEDs
    // ========================================================================

    assign led[0] = system_rst;         // Reset indicator
    assign led[1] = char_received;      // Character has been received at least once
    assign led[2] = rx_ready;           // RX ready (pulse indicator)
    assign led[3] = last_char[7];       // MSB of last received character

endmodule
