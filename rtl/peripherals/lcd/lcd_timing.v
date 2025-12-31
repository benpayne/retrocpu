// ============================================================================
// LCD Timing Generator for HD44780 (4-bit mode)
// ============================================================================
//
// Generates proper timing for HD44780 LCD controller in 4-bit parallel mode.
//
// HD44780 Timing Requirements:
// - Enable pulse width (high): minimum 450ns
// - Data setup time: minimum 80ns
// - Data hold time: minimum 10ns
// - Enable cycle time: minimum 1000ns
//
// At 25 MHz clock (40ns period):
// - Enable high: minimum 12 clocks (480ns) ✓
// - Data setup: minimum 3 clocks (120ns) ✓
// - Data hold: minimum 1 clock (40ns) ✓
// - Full cycle: ~25 clocks (1000ns) ✓
//
// Usage:
// 1. Assert start with data_nibble and rs for one clock
// 2. Wait for busy to assert
// 3. Wait for done pulse (one clock)
// 4. Module returns to idle, ready for next operation
//
// ============================================================================

module lcd_timing (
    input wire clk,                // 25 MHz system clock
    input wire rst,                // Active high reset

    // Control interface
    input wire start,              // Start write cycle (pulse for 1 clock)
    input wire [3:0] data_nibble,  // 4-bit data to write
    input wire rs,                 // Register select (0=command, 1=data)

    output reg busy,               // High during write cycle
    output reg done,               // Pulses high for 1 clock when complete

    // LCD interface
    output reg [3:0] lcd_data,     // LCD D4-D7 pins
    output reg lcd_rs,             // LCD RS pin
    output reg lcd_e               // LCD Enable pin (RW assumed tied low)
);

    // State machine states
    localparam [2:0]
        ST_IDLE        = 3'd0,     // Idle, waiting for start
        ST_SETUP       = 3'd1,     // Data setup time (3 clocks)
        ST_ENABLE_HIGH = 3'd2,     // Enable pulse high (12 clocks)
        ST_ENABLE_LOW  = 3'd3,     // Enable low, data hold (2 clocks)
        ST_DONE        = 3'd4;     // Done, pulse done signal

    reg [2:0] state;
    reg [4:0] counter;             // Up to 31 count for timing

    // Timing parameters (in clock cycles @ 25 MHz)
    localparam SETUP_CYCLES = 5'd5;   // 5 clocks = 200ns (>80ns required)
    localparam ENABLE_CYCLES = 5'd14; // 14 clocks = 560ns (>450ns required)
    localparam HOLD_CYCLES = 5'd6;    // 6 clocks = 240ns (>10ns required)
    // Total: 25 clocks = 1000ns exactly

    // Registered inputs to maintain during cycle
    reg [3:0] data_reg;
    reg rs_reg;

    always @(posedge clk) begin
        if (rst) begin
            state <= ST_IDLE;
            counter <= 5'd0;
            busy <= 1'b0;
            done <= 1'b0;
            lcd_e <= 1'b0;
            lcd_data <= 4'h0;
            lcd_rs <= 1'b0;
            data_reg <= 4'h0;
            rs_reg <= 1'b0;

        end else begin
            // Default: done is a single-cycle pulse
            done <= 1'b0;

            case (state)
                ST_IDLE: begin
                    busy <= 1'b0;
                    lcd_e <= 1'b0;
                    counter <= 5'd0;

                    if (start) begin
                        // Latch inputs
                        data_reg <= data_nibble;
                        rs_reg <= rs;

                        // Set outputs immediately
                        lcd_data <= data_nibble;
                        lcd_rs <= rs;

                        // Move to setup
                        state <= ST_SETUP;
                        busy <= 1'b1;
                    end
                end

                ST_SETUP: begin
                    // Data and RS outputs stable during setup
                    lcd_data <= data_reg;
                    lcd_rs <= rs_reg;
                    lcd_e <= 1'b0;  // Enable still low

                    counter <= counter + 1'b1;

                    if (counter >= SETUP_CYCLES - 1) begin
                        state <= ST_ENABLE_HIGH;
                        counter <= 5'd0;
                    end
                end

                ST_ENABLE_HIGH: begin
                    // Raise enable (data already stable from setup)
                    lcd_e <= 1'b1;
                    lcd_data <= data_reg;
                    lcd_rs <= rs_reg;

                    counter <= counter + 1'b1;

                    if (counter >= ENABLE_CYCLES - 1) begin
                        state <= ST_ENABLE_LOW;
                        counter <= 5'd0;
                    end
                end

                ST_ENABLE_LOW: begin
                    // Lower enable, maintain data for hold time
                    lcd_e <= 1'b0;
                    lcd_data <= data_reg;
                    lcd_rs <= rs_reg;

                    counter <= counter + 1'b1;

                    if (counter >= HOLD_CYCLES - 1) begin
                        state <= ST_DONE;
                    end
                end

                ST_DONE: begin
                    // Pulse done signal
                    done <= 1'b1;
                    busy <= 1'b0;
                    state <= ST_IDLE;

                    // Return outputs to idle state
                    lcd_e <= 1'b0;
                    lcd_data <= 4'h0;
                    lcd_rs <= 1'b0;
                end

                default: begin
                    state <= ST_IDLE;
                end
            endcase
        end
    end

endmodule
