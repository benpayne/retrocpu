//
// clock_divider.v - Clock Divider for 6502 CPU
//
// Divides 25 MHz system clock to 1 MHz CPU clock using clock enable
//
// Author: RetroCPU Project
// License: MIT
//
// Features:
// - 25:1 clock division (25 MHz -> 1 MHz)
// - Clock enable output for single-clock-domain design
// - Synchronous reset
// - Configurable divide ratio via parameter
//
// Usage:
//   Always use clk_enable to gate CPU operations, not a derived clock.
//   This maintains single clock domain and simplifies timing.
//

module clock_divider #(
    parameter DIVIDE_RATIO = 25  // 25 MHz / 25 = 1 MHz
) (
    input  wire clk,         // System clock (25 MHz)
    input  wire rst,         // Synchronous reset (active high)
    output reg  clk_enable   // Clock enable pulse (1 cycle every DIVIDE_RATIO)
);

    // Counter to track clock cycles
    reg [$clog2(DIVIDE_RATIO)-1:0] counter;

    always @(posedge clk) begin
        if (rst) begin
            counter <= 0;
            clk_enable <= 0;
        end else begin
            if (counter == DIVIDE_RATIO - 1) begin
                counter <= 0;
                clk_enable <= 1;
            end else begin
                counter <= counter + 1;
                clk_enable <= 0;
            end
        end
    end

endmodule
