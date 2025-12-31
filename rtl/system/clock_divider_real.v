//
// clock_divider_real.v - Real Clock Divider for 6502 CPU
//
// Generates an actual divided clock output instead of just an enable signal
// This is necessary because the Arlet 6502 core's DIMUX logic expects RDY
// to be used for memory wait states, not for clock division.
//
// Author: RetroCPU Project
// License: MIT
//

module clock_divider_real #(
    parameter DIVIDE_RATIO = 25  // 25 MHz / 25 = 1 MHz
) (
    input  wire clk,          // System clock (25 MHz)
    input  wire rst,          // Synchronous reset (active high)
    output reg  clk_out,      // Divided clock output
    output reg  clk_enable    // Optional enable signal aligned with clk_out edges
);

    // Counter to track clock cycles
    reg [$clog2(DIVIDE_RATIO)-1:0] counter;

    always @(posedge clk) begin
        if (rst) begin
            counter <= 0;
            clk_out <= 0;
            clk_enable <= 0;
        end else begin
            if (counter == DIVIDE_RATIO - 1) begin
                counter <= 0;
                clk_out <= ~clk_out;  // Toggle creates divided clock
                clk_enable <= 1;      // Pulse on toggle
            end else begin
                counter <= counter + 1;
                clk_enable <= 0;
            end
        end
    end

endmodule
