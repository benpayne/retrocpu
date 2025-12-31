// ============================================================================
// Simple LCD Test Top Module
// ============================================================================
//
// Minimal test design that:
// 1. Initializes LCD on power-up
// 2. Writes "TEST" repeatedly every 2 seconds
// 3. Blinks LED to show it's running
//
// This isolates LCD hardware testing from CPU/memory complexity
//
// ============================================================================

module lcd_test_top (
    // Clock and reset
    input  wire clk_25mhz,         // 25 MHz system clock
    input  wire reset_button_n,    // Reset button (active-low)

    // LCD interface
    output wire [3:0] lcd_data,    // LCD D4-D7 data pins
    output wire lcd_rs,            // LCD Register Select
    output wire lcd_rw,            // LCD Read/Write
    output wire lcd_e,             // LCD Enable

    // Debug LEDs
    output wire [3:0] led          // Status LEDs
);

    // ========================================================================
    // Reset Controller
    // ========================================================================

    reg [7:0] reset_counter;
    reg system_rst;

    always @(posedge clk_25mhz) begin
        if (!reset_button_n) begin
            reset_counter <= 8'd0;
            system_rst <= 1'b1;
        end else begin
            if (reset_counter < 8'd255) begin
                reset_counter <= reset_counter + 1'b1;
                system_rst <= 1'b1;
            end else begin
                system_rst <= 1'b0;
            end
        end
    end

    // ========================================================================
    // LCD Controller Instance
    // ========================================================================

    wire [7:0] lcd_data_out;
    reg lcd_cs;
    reg lcd_we;
    reg [7:0] lcd_addr;
    reg [7:0] lcd_data_in;

    lcd_controller lcd_inst (
        .clk(clk_25mhz),
        .rst(system_rst),
        .cs(lcd_cs),
        .we(lcd_we),
        .addr(lcd_addr),
        .data_in(lcd_data_in),
        .data_out(lcd_data_out),
        .lcd_data(lcd_data),
        .lcd_rs(lcd_rs),
        .lcd_rw(lcd_rw),
        .lcd_e(lcd_e)
    );

    // ========================================================================
    // Simple Test State Machine
    // ========================================================================

    localparam [3:0]
        ST_WAIT_INIT    = 4'd0,   // Wait for LCD initialization
        ST_DELAY_START  = 4'd1,   // Initial delay
        ST_WRITE_T      = 4'd2,   // Write 'T'
        ST_WAIT_T       = 4'd3,   // Wait for 'T' to complete
        ST_WRITE_E      = 4'd4,   // Write 'E'
        ST_WAIT_E       = 4'd5,   // Wait for 'E' to complete
        ST_WRITE_S      = 4'd6,   // Write 'S'
        ST_WAIT_S       = 4'd7,   // Wait for 'S' to complete
        ST_WRITE_T2     = 4'd8,   // Write 'T' again
        ST_WAIT_T2      = 4'd9,   // Wait for 'T' to complete
        ST_DELAY_REPEAT = 4'd10;  // Delay before repeating

    reg [3:0] state;
    reg [27:0] delay_counter;     // Up to 268 million (10+ seconds @ 25MHz)

    // Delay parameters (in clock cycles @ 25 MHz)
    localparam DELAY_INIT    = 28'd50000000;  // 2 seconds for init
    localparam DELAY_CHAR    = 28'd50000;     // 2ms between characters
    localparam DELAY_REPEAT  = 28'd50000000;  // 2 seconds before repeat

    // LED blinker (1 Hz heartbeat)
    reg [24:0] led_counter;
    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            led_counter <= 25'd0;
        end else begin
            led_counter <= led_counter + 1'b1;
        end
    end

    // LED assignments
    assign led[0] = system_rst;                    // LED 0: Reset active
    assign led[1] = led_counter[24];               // LED 1: Heartbeat (1 Hz)
    assign led[2] = (state != ST_WAIT_INIT);       // LED 2: Past init
    assign led[3] = lcd_cs && lcd_we;              // LED 3: Writing to LCD

    // Main state machine
    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            state <= ST_WAIT_INIT;
            delay_counter <= 28'd0;
            lcd_cs <= 1'b0;
            lcd_we <= 1'b0;
            lcd_addr <= 8'h00;
            lcd_data_in <= 8'h00;

        end else begin
            // Default: no write
            lcd_cs <= 1'b0;
            lcd_we <= 1'b0;

            case (state)
                ST_WAIT_INIT: begin
                    // Wait for LCD initialization (2 seconds)
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_INIT) begin
                        state <= ST_DELAY_START;
                        delay_counter <= 28'd0;
                    end
                end

                ST_DELAY_START: begin
                    // Short delay before starting
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_CHAR) begin
                        state <= ST_WRITE_T;
                        delay_counter <= 28'd0;
                    end
                end

                ST_WRITE_T: begin
                    // Write 'T' (0x54) to data register ($C100)
                    lcd_cs <= 1'b1;
                    lcd_we <= 1'b1;
                    lcd_addr <= 8'h00;        // Data register
                    lcd_data_in <= 8'h54;     // 'T'
                    state <= ST_WAIT_T;
                    delay_counter <= 28'd0;
                end

                ST_WAIT_T: begin
                    // Wait for write to complete
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_CHAR) begin
                        state <= ST_WRITE_E;
                        delay_counter <= 28'd0;
                    end
                end

                ST_WRITE_E: begin
                    // Write 'E' (0x45)
                    lcd_cs <= 1'b1;
                    lcd_we <= 1'b1;
                    lcd_addr <= 8'h00;
                    lcd_data_in <= 8'h45;     // 'E'
                    state <= ST_WAIT_E;
                    delay_counter <= 28'd0;
                end

                ST_WAIT_E: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_CHAR) begin
                        state <= ST_WRITE_S;
                        delay_counter <= 28'd0;
                    end
                end

                ST_WRITE_S: begin
                    // Write 'S' (0x53)
                    lcd_cs <= 1'b1;
                    lcd_we <= 1'b1;
                    lcd_addr <= 8'h00;
                    lcd_data_in <= 8'h53;     // 'S'
                    state <= ST_WAIT_S;
                    delay_counter <= 28'd0;
                end

                ST_WAIT_S: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_CHAR) begin
                        state <= ST_WRITE_T2;
                        delay_counter <= 28'd0;
                    end
                end

                ST_WRITE_T2: begin
                    // Write 'T' again (0x54)
                    lcd_cs <= 1'b1;
                    lcd_we <= 1'b1;
                    lcd_addr <= 8'h00;
                    lcd_data_in <= 8'h54;     // 'T'
                    state <= ST_WAIT_T2;
                    delay_counter <= 28'd0;
                end

                ST_WAIT_T2: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_CHAR) begin
                        state <= ST_DELAY_REPEAT;
                        delay_counter <= 28'd0;
                    end
                end

                ST_DELAY_REPEAT: begin
                    // Wait 2 seconds, then repeat
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_REPEAT) begin
                        // Send clear command before repeating
                        lcd_cs <= 1'b1;
                        lcd_we <= 1'b1;
                        lcd_addr <= 8'h01;     // Command register
                        lcd_data_in <= 8'h01;  // Clear display
                        state <= ST_DELAY_START;
                        delay_counter <= 28'd0;
                    end
                end

                default: begin
                    state <= ST_WAIT_INIT;
                end
            endcase
        end
    end

endmodule
