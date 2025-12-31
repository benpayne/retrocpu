// ============================================================================
// LCD Diagnostic Test - Raw Commands
// ============================================================================
//
// Sends raw nibbles directly to LCD to diagnose 4-bit mode issues
// LED indicators show exactly what we're sending
//
// ============================================================================

module lcd_diagnostic_top (
    input  wire clk_25mhz,
    input  wire reset_button_n,

    // LCD interface - raw control
    output reg [3:0] lcd_data,
    output reg lcd_rs,
    output wire lcd_rw,
    output reg lcd_e,

    // Debug LEDs
    output wire [3:0] led
);

    assign lcd_rw = 1'b0;  // Always write

    // Reset
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

    // Timing counters
    reg [27:0] delay_counter;
    reg [4:0] enable_counter;

    // State machine
    localparam [4:0]
        ST_POWER_WAIT     = 5'd0,   // Wait 15ms
        ST_INIT_1_HIGH    = 5'd1,   // Send 0x3 nibble
        ST_INIT_1_PULSE   = 5'd2,   // Enable pulse
        ST_INIT_1_WAIT    = 5'd3,   // Wait 4.1ms
        ST_INIT_2_HIGH    = 5'd4,   // Send 0x3 again
        ST_INIT_2_PULSE   = 5'd5,
        ST_INIT_2_WAIT    = 5'd6,   // Wait 100us
        ST_INIT_3_HIGH    = 5'd7,   // Send 0x3 third time
        ST_INIT_3_PULSE   = 5'd8,
        ST_INIT_3_WAIT    = 5'd9,
        ST_4BIT_HIGH      = 5'd10,  // Send 0x2 (enter 4-bit)
        ST_4BIT_PULSE     = 5'd11,
        ST_4BIT_WAIT      = 5'd12,
        ST_FUNC_H         = 5'd13,  // 0x28: 4-bit, 2 lines, 5x8
        ST_FUNC_H_PULSE   = 5'd14,
        ST_FUNC_L         = 5'd15,
        ST_FUNC_L_PULSE   = 5'd16,
        ST_DISP_H         = 5'd17,  // 0x0C: Display on
        ST_DISP_H_PULSE   = 5'd18,
        ST_DISP_L         = 5'd19,
        ST_DISP_L_PULSE   = 5'd20,
        ST_CLEAR_H        = 5'd21,  // 0x01: Clear
        ST_CLEAR_H_PULSE  = 5'd22,
        ST_CLEAR_L        = 5'd23,
        ST_CLEAR_L_PULSE  = 5'd24,
        ST_CHAR_H         = 5'd25,  // Write 'A' (0x41)
        ST_CHAR_H_PULSE   = 5'd26,
        ST_CHAR_L         = 5'd27,
        ST_CHAR_L_PULSE   = 5'd28,
        ST_DONE           = 5'd29;

    reg [4:0] state;

    // LED outputs show state
    assign led[0] = (state > ST_4BIT_WAIT);       // Past 4-bit entry
    assign led[1] = (state > ST_FUNC_L_PULSE);    // Past function set
    assign led[2] = (state > ST_CLEAR_L_PULSE);   // Past clear
    assign led[3] = (state == ST_DONE);           // Done

    // Delays (in 25MHz clocks)
    localparam DELAY_15MS = 28'd375000;
    localparam DELAY_4MS  = 28'd100000;
    localparam DELAY_100US = 28'd2500;
    localparam DELAY_40US = 28'd1000;
    localparam DELAY_2MS  = 28'd50000;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            state <= ST_POWER_WAIT;
            delay_counter <= 28'd0;
            enable_counter <= 5'd0;
            lcd_data <= 4'h0;
            lcd_rs <= 1'b0;
            lcd_e <= 1'b0;

        end else begin
            case (state)
                ST_POWER_WAIT: begin
                    lcd_e <= 1'b0;
                    lcd_rs <= 1'b0;
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_15MS) begin
                        state <= ST_INIT_1_HIGH;
                        delay_counter <= 28'd0;
                    end
                end

                // Init sequence 1: Send 0x3
                ST_INIT_1_HIGH: begin
                    lcd_data <= 4'h3;
                    lcd_rs <= 1'b0;  // Command
                    lcd_e <= 1'b0;
                    enable_counter <= 5'd0;
                    state <= ST_INIT_1_PULSE;
                end

                ST_INIT_1_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;  // Setup
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;  // Enable high
                    else begin
                        lcd_e <= 1'b0;  // Enable low
                        state <= ST_INIT_1_WAIT;
                        delay_counter <= 28'd0;
                    end
                end

                ST_INIT_1_WAIT: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_4MS) begin
                        state <= ST_INIT_2_HIGH;
                        delay_counter <= 28'd0;
                    end
                end

                // Init sequence 2: Send 0x3
                ST_INIT_2_HIGH: begin
                    lcd_data <= 4'h3;
                    enable_counter <= 5'd0;
                    state <= ST_INIT_2_PULSE;
                end

                ST_INIT_2_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;
                    else begin
                        lcd_e <= 1'b0;
                        state <= ST_INIT_2_WAIT;
                        delay_counter <= 28'd0;
                    end
                end

                ST_INIT_2_WAIT: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_100US) begin
                        state <= ST_INIT_3_HIGH;
                        delay_counter <= 28'd0;
                    end
                end

                // Init sequence 3: Send 0x3
                ST_INIT_3_HIGH: begin
                    lcd_data <= 4'h3;
                    enable_counter <= 5'd0;
                    state <= ST_INIT_3_PULSE;
                end

                ST_INIT_3_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;
                    else begin
                        lcd_e <= 1'b0;
                        state <= ST_INIT_3_WAIT;
                        delay_counter <= 28'd0;
                    end
                end

                ST_INIT_3_WAIT: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_40US) begin
                        state <= ST_4BIT_HIGH;
                        delay_counter <= 28'd0;
                    end
                end

                // Enter 4-bit mode: Send 0x2
                ST_4BIT_HIGH: begin
                    lcd_data <= 4'h2;  // CRITICAL: This enters 4-bit mode
                    enable_counter <= 5'd0;
                    state <= ST_4BIT_PULSE;
                end

                ST_4BIT_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;
                    else begin
                        lcd_e <= 1'b0;
                        state <= ST_4BIT_WAIT;
                        delay_counter <= 28'd0;
                    end
                end

                ST_4BIT_WAIT: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_40US) begin
                        state <= ST_FUNC_H;
                        delay_counter <= 28'd0;
                    end
                end

                // NOW IN 4-BIT MODE: Send function set 0x28
                ST_FUNC_H: begin
                    lcd_data <= 4'h2;  // High nibble of 0x28
                    lcd_rs <= 1'b0;    // Command
                    enable_counter <= 5'd0;
                    state <= ST_FUNC_H_PULSE;
                end

                ST_FUNC_H_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;
                    else begin
                        lcd_e <= 1'b0;
                        state <= ST_FUNC_L;
                        delay_counter <= 28'd0;
                    end
                end

                ST_FUNC_L: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_40US) begin
                        lcd_data <= 4'h8;  // Low nibble of 0x28
                        enable_counter <= 5'd0;
                        state <= ST_FUNC_L_PULSE;
                        delay_counter <= 28'd0;
                    end
                end

                ST_FUNC_L_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;
                    else begin
                        lcd_e <= 1'b0;
                        state <= ST_DISP_H;
                        delay_counter <= 28'd0;
                    end
                end

                // Display on 0x0C
                ST_DISP_H: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_2MS) begin
                        lcd_data <= 4'h0;  // High nibble of 0x0C
                        lcd_rs <= 1'b0;    // Command
                        enable_counter <= 5'd0;
                        state <= ST_DISP_H_PULSE;
                        delay_counter <= 28'd0;
                    end
                end

                ST_DISP_H_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;
                    else begin
                        lcd_e <= 1'b0;
                        state <= ST_DISP_L;
                        delay_counter <= 28'd0;
                    end
                end

                ST_DISP_L: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_40US) begin
                        lcd_data <= 4'hC;  // Low nibble of 0x0C
                        enable_counter <= 5'd0;
                        state <= ST_DISP_L_PULSE;
                        delay_counter <= 28'd0;
                    end
                end

                ST_DISP_L_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;
                    else begin
                        lcd_e <= 1'b0;
                        state <= ST_CLEAR_H;
                        delay_counter <= 28'd0;
                    end
                end

                // Clear display 0x01
                ST_CLEAR_H: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_2MS) begin
                        lcd_data <= 4'h0;  // High nibble of 0x01
                        lcd_rs <= 1'b0;    // Command
                        enable_counter <= 5'd0;
                        state <= ST_CLEAR_H_PULSE;
                        delay_counter <= 28'd0;
                    end
                end

                ST_CLEAR_H_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;
                    else begin
                        lcd_e <= 1'b0;
                        state <= ST_CLEAR_L;
                        delay_counter <= 28'd0;
                    end
                end

                ST_CLEAR_L: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_40US) begin
                        lcd_data <= 4'h1;  // Low nibble of 0x01
                        enable_counter <= 5'd0;
                        state <= ST_CLEAR_L_PULSE;
                        delay_counter <= 28'd0;
                    end
                end

                ST_CLEAR_L_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;
                    else begin
                        lcd_e <= 1'b0;
                        state <= ST_CHAR_H;
                        delay_counter <= 28'd0;
                    end
                end

                // Write 'A' (0x41) as DATA
                ST_CHAR_H: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_2MS) begin
                        lcd_data <= 4'h4;  // High nibble of 0x41
                        lcd_rs <= 1'b1;    // DATA (not command!)
                        enable_counter <= 5'd0;
                        state <= ST_CHAR_H_PULSE;
                        delay_counter <= 28'd0;
                    end
                end

                ST_CHAR_H_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;
                    else begin
                        lcd_e <= 1'b0;
                        state <= ST_CHAR_L;
                        delay_counter <= 28'd0;
                    end
                end

                ST_CHAR_L: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_40US) begin
                        lcd_data <= 4'h1;  // Low nibble of 0x41
                        lcd_rs <= 1'b1;    // Still DATA
                        enable_counter <= 5'd0;
                        state <= ST_CHAR_L_PULSE;
                        delay_counter <= 28'd0;
                    end
                end

                ST_CHAR_L_PULSE: begin
                    enable_counter <= enable_counter + 1'b1;
                    if (enable_counter < 5'd10)
                        lcd_e <= 1'b0;
                    else if (enable_counter < 5'd22)
                        lcd_e <= 1'b1;
                    else begin
                        lcd_e <= 1'b0;
                        state <= ST_DONE;
                    end
                end

                ST_DONE: begin
                    // Stay here, character 'A' should be visible
                    lcd_e <= 1'b0;
                end

                default: state <= ST_POWER_WAIT;
            endcase
        end
    end

endmodule
