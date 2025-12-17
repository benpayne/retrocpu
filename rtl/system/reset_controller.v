//
// reset_controller.v - Reset Controller with Power-On Reset and Button Debouncing
//
// Generates clean reset signal from power-on and button press
//
// Author: RetroCPU Project
// License: MIT
//
// Features:
// - Power-on reset (holds reset for POWER_ON_CYCLES after startup)
// - Button debouncing (requires button stable for DEBOUNCE_CYCLES)
// - Minimum reset pulse width (RESET_MIN_CYCLES)
// - Synchronous reset output (safe for single clock domain)
// - Active-low button input (matches FIRE 2 button on Colorlight i5)
//
// Usage:
//   Connect reset_button_n to T1 pin (FIRE 2 button, active-low with pull-up)
//   Use rst output to reset all system modules
//

module reset_controller #(
    parameter POWER_ON_CYCLES = 100,  // Hold reset for 100 cycles at power-on (4 us @ 25 MHz)
    parameter DEBOUNCE_CYCLES = 10,   // Button must be stable for 10 cycles (400 ns @ 25 MHz)
    parameter RESET_MIN_CYCLES = 50   // Minimum reset pulse width (2 us @ 25 MHz)
) (
    input  wire clk,              // System clock (25 MHz)
    input  wire reset_button_n,   // Reset button input (active-low, from FIRE 2 / T1)
    output reg  rst               // Synchronous reset output (active-high)
);

    // State machine states
    localparam STATE_POWER_ON    = 2'b00;  // Power-on reset phase
    localparam STATE_IDLE        = 2'b01;  // Normal operation, monitoring button
    localparam STATE_RESET_WAIT  = 2'b10;  // Button pressed, debouncing
    localparam STATE_RESET_HOLD  = 2'b11;  // Reset asserted, holding for minimum time

    reg [1:0] state;
    reg [7:0] counter;  // 8-bit counter sufficient for our parameters

    // Button input synchronizer (prevent metastability)
    reg button_sync_1;
    reg button_sync_2;

    always @(posedge clk) begin
        button_sync_1 <= reset_button_n;
        button_sync_2 <= button_sync_1;
    end

    // Detect button press (synchronized input goes low)
    wire button_pressed;
    assign button_pressed = ~button_sync_2;

    // Main state machine
    always @(posedge clk) begin
        case (state)
            STATE_POWER_ON: begin
                // Power-on reset: hold reset asserted for POWER_ON_CYCLES
                rst <= 1;

                if (counter < POWER_ON_CYCLES - 1) begin
                    counter <= counter + 1;
                end else begin
                    counter <= 0;
                    state <= STATE_IDLE;
                end
            end

            STATE_IDLE: begin
                // Normal operation: monitor button
                rst <= 0;

                if (button_pressed) begin
                    counter <= 0;
                    state <= STATE_RESET_WAIT;
                end
            end

            STATE_RESET_WAIT: begin
                // Button pressed: wait for debounce period
                rst <= 0;  // Don't assert reset until debounced

                if (button_pressed) begin
                    // Button still pressed, increment counter
                    if (counter < DEBOUNCE_CYCLES - 1) begin
                        counter <= counter + 1;
                    end else begin
                        // Debounce complete, assert reset
                        counter <= 0;
                        rst <= 1;
                        state <= STATE_RESET_HOLD;
                    end
                end else begin
                    // Button released too quickly (bounce), go back to idle
                    counter <= 0;
                    state <= STATE_IDLE;
                end
            end

            STATE_RESET_HOLD: begin
                // Reset asserted: hold for minimum time or until button released
                rst <= 1;

                if (counter < RESET_MIN_CYCLES - 1) begin
                    counter <= counter + 1;
                end else begin
                    // Minimum time elapsed, check if button still pressed
                    if (!button_pressed) begin
                        // Button released, go to idle
                        counter <= 0;
                        rst <= 0;
                        state <= STATE_IDLE;
                    end
                    // If button still pressed, stay in this state with reset asserted
                end
            end

            default: begin
                // Should never reach here, go to power-on reset
                state <= STATE_POWER_ON;
                counter <= 0;
                rst <= 1;
            end
        endcase
    end

    // Initialize state machine at power-on
    initial begin
        state = STATE_POWER_ON;
        counter = 0;
        rst = 1;
        button_sync_1 = 1;
        button_sync_2 = 1;
    end

endmodule
