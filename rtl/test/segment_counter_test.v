//
// segment_counter_test.v - Simple 7-Segment Display Counter Test
//
// Counts 0-F on the 7-segment display to verify hardware
//

module segment_counter_test (
    input  wire clk_25mhz,
    input  wire reset_button_n,

    // 7-segment display
    output wire seg_a,
    output wire seg_b,
    output wire seg_c,
    output wire seg_d,
    output wire seg_e,
    output wire seg_f,
    output wire seg_g,
    output wire seg_select,

    // LEDs show counter too
    output wire [3:0] led
);

    // Reset
    wire system_rst;
    reset_controller rst_ctrl (
        .clk(clk_25mhz),
        .reset_button_n(reset_button_n),
        .rst(system_rst)
    );

    // Counter: increment every 0.5 seconds
    reg [24:0] timer;
    reg [3:0] counter;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            timer <= 0;
            counter <= 0;
        end else begin
            if (timer >= 25'd12_500_000) begin  // 0.5 seconds at 25MHz
                timer <= 0;
                counter <= counter + 1;  // Will wrap 0-15
            end else begin
                timer <= timer + 1;
            end
        end
    end

    // 7-segment decoder
    reg [6:0] segments;
    always @(*) begin
        case (counter)
            4'h0: segments = 7'b0111111;  // 0
            4'h1: segments = 7'b0000110;  // 1
            4'h2: segments = 7'b1011011;  // 2
            4'h3: segments = 7'b1001111;  // 3
            4'h4: segments = 7'b1100110;  // 4
            4'h5: segments = 7'b1101101;  // 5
            4'h6: segments = 7'b1111101;  // 6
            4'h7: segments = 7'b0000111;  // 7
            4'h8: segments = 7'b1111111;  // 8
            4'h9: segments = 7'b1101111;  // 9
            4'hA: segments = 7'b1110111;  // A
            4'hB: segments = 7'b1111100;  // b
            4'hC: segments = 7'b0111001;  // C
            4'hD: segments = 7'b1011110;  // d
            4'hE: segments = 7'b1111001;  // E
            4'hF: segments = 7'b1110001;  // F
        endcase
    end

    // Output assignments (active-low segments)
    assign {seg_g, seg_f, seg_e, seg_d, seg_c, seg_b, seg_a} = ~segments;
    assign seg_select = 1'b0;  // Select first digit

    // Show counter on LEDs too
    assign led = counter;

endmodule
