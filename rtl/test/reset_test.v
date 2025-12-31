//
// reset_test.v - Test reset controller behavior
//
// Shows reset state on display and blinks when out of reset
//

module reset_test (
    input  wire clk_25mhz,
    input  wire reset_button_n,

    output wire seg_a,
    output wire seg_b,
    output wire seg_c,
    output wire seg_d,
    output wire seg_e,
    output wire seg_f,
    output wire seg_g,
    output wire seg_select,

    output wire [3:0] led
);

    // Reset controller
    wire system_rst;
    reset_controller rst_ctrl (
        .clk(clk_25mhz),
        .reset_button_n(reset_button_n),
        .rst(system_rst)
    );

    // Counter that only runs when NOT in reset
    reg [24:0] counter;
    reg [3:0] display_value;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            counter <= 0;
            display_value <= 4'h0;  // Show 0 when in reset
        end else begin
            counter <= counter + 1;
            // Change display every 0.5 seconds when out of reset
            if (counter >= 25'd12_500_000) begin
                counter <= 0;
                display_value <= display_value + 1;
            end
        end
    end

    // 7-segment decoder
    reg [6:0] segments;
    always @(*) begin
        case (display_value)
            4'h0: segments = 7'b0111111;
            4'h1: segments = 7'b0000110;
            4'h2: segments = 7'b1011011;
            4'h3: segments = 7'b1001111;
            4'h4: segments = 7'b1100110;
            4'h5: segments = 7'b1101101;
            4'h6: segments = 7'b1111101;
            4'h7: segments = 7'b0000111;
            4'h8: segments = 7'b1111111;
            4'h9: segments = 7'b1101111;
            4'hA: segments = 7'b1110111;
            4'hB: segments = 7'b1111100;
            4'hC: segments = 7'b0111001;
            4'hD: segments = 7'b1011110;
            4'hE: segments = 7'b1111001;
            4'hF: segments = 7'b1110001;
        endcase
    end

    assign {seg_g, seg_f, seg_e, seg_d, seg_c, seg_b, seg_a} = ~segments;
    assign seg_select = 1'b0;

    // LED indicators
    assign led[0] = system_rst;           // ON = in reset
    assign led[1] = ~system_rst;          // ON = running
    assign led[2] = reset_button_n;       // Shows actual button state (should be HIGH when not pressed)
    assign led[3] = counter[23];          // Blinks at ~3Hz when running

endmodule
