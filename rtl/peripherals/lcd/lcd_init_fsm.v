// ============================================================================
// LCD Initialization FSM for HD44780 (4-bit mode)
// ============================================================================
//
// Automatically executes the HD44780 power-on initialization sequence.
//
// HD44780 4-bit Initialization Sequence (from datasheet):
// 1. Wait 15ms after power-on (Vcc reaches 4.5V)
// 2. Send 0x3 (Function set) - wait 4.1ms
// 3. Send 0x3 (Function set) - wait 100μs
// 4. Send 0x3 (Function set) - wait 40μs
// 5. Send 0x2 (Set 4-bit mode) - wait 40μs
// 6. Send 0x28 (Function set: 4-bit, 2 lines, 5x8 font) [2 nibbles]
// 7. Send 0x0C (Display on, cursor off, blink off) [2 nibbles]
// 8. Send 0x01 (Clear display) [2 nibbles]
// 9. Initialization complete
//
// At 25 MHz (40ns period):
// - 15ms = 375,000 clocks
// - 4.1ms = 102,500 clocks
// - 100μs = 2,500 clocks
// - 40μs = 1,000 clocks
//
// For simulation speed, delays are shortened with parameter overrides.
//
// ============================================================================

module lcd_init_fsm #(
    parameter WAIT_POWER_ON = 375000,    // 15ms @ 25MHz
    parameter WAIT_4_1MS    = 102500,    // 4.1ms
    parameter WAIT_100US    = 2500,      // 100μs
    parameter WAIT_40US     = 1000       // 40μs
) (
    input wire clk,                      // 25 MHz system clock
    input wire rst,                      // Active high reset

    // Timing module interface
    input wire timing_done,              // Timing module done signal
    output reg start_timing,             // Start timing cycle
    output reg [3:0] nibble_out,         // Nibble to send
    output reg rs_out,                   // RS signal (always 0 for init)

    // Status
    output reg init_done,                // High when initialization complete
    output reg init_active               // High during initialization
);

    // State machine
    localparam [4:0]
        ST_IDLE           = 5'd0,
        ST_WAIT_POWER     = 5'd1,        // Wait 15ms
        ST_FUNC_SET_1     = 5'd2,        // Send 0x3
        ST_WAIT_4_1MS     = 5'd3,        // Wait 4.1ms
        ST_FUNC_SET_2     = 5'd4,        // Send 0x3
        ST_WAIT_100US     = 5'd5,        // Wait 100μs
        ST_FUNC_SET_3     = 5'd6,        // Send 0x3
        ST_WAIT_40US_1    = 5'd7,        // Wait 40μs
        ST_SET_4BIT       = 5'd8,        // Send 0x2 (enter 4-bit mode)
        ST_WAIT_40US_2    = 5'd9,        // Wait 40μs
        ST_FUNC_SET_HIGH  = 5'd10,       // Send 0x2 (high nibble of 0x28)
        ST_FUNC_SET_LOW   = 5'd11,       // Send 0x8 (low nibble of 0x28)
        ST_DISP_ON_HIGH   = 5'd12,       // Send 0x0 (high nibble of 0x0C)
        ST_DISP_ON_LOW    = 5'd13,       // Send 0xC (low nibble of 0x0C)
        ST_ENTRY_MODE_HIGH = 5'd14,      // Send 0x0 (high nibble of 0x06)
        ST_ENTRY_MODE_LOW  = 5'd15,      // Send 0x6 (low nibble of 0x06)
        ST_CLEAR_HIGH     = 5'd16,       // Send 0x0 (high nibble of 0x01)
        ST_CLEAR_LOW      = 5'd17,       // Send 0x1 (low nibble of 0x01)
        ST_COMPLETE       = 5'd18;       // Done

    reg [4:0] state;
    reg [19:0] delay_counter;            // Up to 375,000 for 15ms delay

    always @(posedge clk) begin
        if (rst) begin
            state <= ST_IDLE;
            delay_counter <= 20'd0;
            start_timing <= 1'b0;
            nibble_out <= 4'h0;
            rs_out <= 1'b0;
            init_done <= 1'b0;
            init_active <= 1'b0;

        end else begin
            // Default: start_timing is a pulse
            start_timing <= 1'b0;

            case (state)
                ST_IDLE: begin
                    init_done <= 1'b0;
                    init_active <= 1'b1;  // Start init
                    rs_out <= 1'b0;       // All init commands use RS=0
                    delay_counter <= 20'd0;
                    state <= ST_WAIT_POWER;
                end

                ST_WAIT_POWER: begin
                    // Wait 15ms for power stabilization
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= WAIT_POWER_ON - 1) begin
                        state <= ST_FUNC_SET_1;
                        delay_counter <= 20'd0;
                    end
                end

                ST_FUNC_SET_1: begin
                    // Send first function set (0x3)
                    nibble_out <= 4'h3;
                    start_timing <= 1'b1;
                    state <= ST_WAIT_4_1MS;
                end

                ST_WAIT_4_1MS: begin
                    // Wait for timing to complete, then delay 4.1ms
                    // Count after timing_done goes high OR if already counting
                    if (timing_done || delay_counter > 0) begin
                        delay_counter <= delay_counter + 1'b1;
                        if (delay_counter >= WAIT_4_1MS - 1) begin
                            state <= ST_FUNC_SET_2;
                            delay_counter <= 20'd0;
                        end
                    end
                end

                ST_FUNC_SET_2: begin
                    // Send second function set (0x3)
                    nibble_out <= 4'h3;
                    start_timing <= 1'b1;
                    state <= ST_WAIT_100US;
                end

                ST_WAIT_100US: begin
                    // Count after timing_done goes high OR if already counting
                    if (timing_done || delay_counter > 0) begin
                        delay_counter <= delay_counter + 1'b1;
                        if (delay_counter >= WAIT_100US - 1) begin
                            state <= ST_FUNC_SET_3;
                            delay_counter <= 20'd0;
                        end
                    end
                end

                ST_FUNC_SET_3: begin
                    // Send third function set (0x3)
                    nibble_out <= 4'h3;
                    start_timing <= 1'b1;
                    state <= ST_WAIT_40US_1;
                end

                ST_WAIT_40US_1: begin
                    // Count after timing_done goes high OR if already counting
                    if (timing_done || delay_counter > 0) begin
                        delay_counter <= delay_counter + 1'b1;
                        if (delay_counter >= WAIT_40US - 1) begin
                            state <= ST_SET_4BIT;
                            delay_counter <= 20'd0;
                        end
                    end
                end

                ST_SET_4BIT: begin
                    // Enter 4-bit mode (0x2)
                    nibble_out <= 4'h2;
                    start_timing <= 1'b1;
                    state <= ST_WAIT_40US_2;
                end

                ST_WAIT_40US_2: begin
                    // Count after timing_done goes high OR if already counting
                    if (timing_done || delay_counter > 0) begin
                        delay_counter <= delay_counter + 1'b1;
                        if (delay_counter >= WAIT_40US - 1) begin
                            state <= ST_FUNC_SET_HIGH;
                            delay_counter <= 20'd0;
                        end
                    end
                end

                ST_FUNC_SET_HIGH: begin
                    // Function set 0x28 (4-bit, 2 lines, 5x8) - high nibble
                    nibble_out <= 4'h2;
                    start_timing <= 1'b1;
                    state <= ST_FUNC_SET_LOW;  // Unconditional transition
                end

                ST_FUNC_SET_LOW: begin
                    if (timing_done) begin
                        // Low nibble of 0x28
                        nibble_out <= 4'h8;
                        start_timing <= 1'b1;
                        state <= ST_DISP_ON_HIGH;
                    end
                end

                ST_DISP_ON_HIGH: begin
                    if (timing_done) begin
                        // Display on 0x0C - high nibble
                        nibble_out <= 4'h0;
                        start_timing <= 1'b1;
                        state <= ST_DISP_ON_LOW;
                    end
                end

                ST_DISP_ON_LOW: begin
                    if (timing_done) begin
                        // Low nibble of 0x0C
                        nibble_out <= 4'hC;
                        start_timing <= 1'b1;
                        state <= ST_ENTRY_MODE_HIGH;
                    end
                end

                ST_ENTRY_MODE_HIGH: begin
                    if (timing_done) begin
                        // Entry mode 0x06 (increment cursor, no shift) - high nibble
                        nibble_out <= 4'h0;
                        start_timing <= 1'b1;
                        state <= ST_ENTRY_MODE_LOW;
                    end
                end

                ST_ENTRY_MODE_LOW: begin
                    if (timing_done) begin
                        // Low nibble of 0x06
                        nibble_out <= 4'h6;
                        start_timing <= 1'b1;
                        state <= ST_CLEAR_HIGH;
                    end
                end

                ST_CLEAR_HIGH: begin
                    if (timing_done) begin
                        // Clear display 0x01 - high nibble
                        nibble_out <= 4'h0;
                        start_timing <= 1'b1;
                        state <= ST_CLEAR_LOW;
                    end
                end

                ST_CLEAR_LOW: begin
                    if (timing_done) begin
                        // Low nibble of 0x01
                        nibble_out <= 4'h1;
                        start_timing <= 1'b1;
                        state <= ST_COMPLETE;
                    end
                end

                ST_COMPLETE: begin
                    if (timing_done) begin
                        // Initialization done
                        init_done <= 1'b1;
                        init_active <= 1'b0;
                        // Stay in this state
                    end
                end

                default: begin
                    state <= ST_IDLE;
                end
            endcase
        end
    end

endmodule
