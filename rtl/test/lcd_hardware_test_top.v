// ============================================================================
// LCD Hardware Test - Direct CPU Writes
// ============================================================================
// Simplified SOC that writes "HW" to LCD at boot without BASIC
// ============================================================================

module lcd_hardware_test_top (
    input  wire clk_25mhz,
    input  wire reset_button_n,

    // LCD interface
    output wire [3:0] lcd_data,
    output wire lcd_rs,
    output wire lcd_rw,
    output wire lcd_e,

    // Debug LEDs
    output wire [3:0] led,

    // UART (for debug output)
    output wire uart_tx
);

    // Reset controller
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

    // Test state machine
    localparam [3:0]
        ST_INIT_WAIT    = 4'd0,   // Wait for LCD init
        ST_CLEAR_CMD    = 4'd1,   // Clear display command (hold write)
        ST_CLEAR_HOLD   = 4'd2,   // Hold write signals
        ST_CLEAR_WAIT   = 4'd3,   // Wait for clear
        ST_WRITE_H      = 4'd4,   // Write 'H'
        ST_HOLD_H       = 4'd5,   // Hold write signals
        ST_WAIT_H       = 4'd6,   // Wait after H
        ST_WRITE_W      = 4'd7,   // Write 'W'
        ST_HOLD_W       = 4'd8,   // Hold write signals
        ST_WAIT_W       = 4'd9,   // Wait after W
        ST_DONE         = 4'd10;  // Done

    reg [3:0] state;
    reg [27:0] delay_counter;

    // LCD controller signals
    reg lcd_cs;
    reg lcd_we;
    reg [7:0] lcd_addr;
    reg [7:0] lcd_data_in;
    wire [7:0] lcd_data_out;

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

    // Simple UART for debug
    reg uart_tx_start;
    reg [7:0] uart_tx_data;
    wire uart_tx_busy;

    uart_tx #(
        .CLK_FREQ(25000000),
        .BAUD_RATE(115200)
    ) uart_tx_inst (
        .clk(clk_25mhz),
        .rst(system_rst),
        .tx_start(uart_tx_start),
        .tx_data(uart_tx_data),
        .tx(uart_tx),
        .tx_busy(uart_tx_busy)
    );

    // LED indicators
    assign led[0] = (state > ST_CLEAR_WAIT);  // Past clear
    assign led[1] = (state > ST_WAIT_H);      // Past H
    assign led[2] = (state > ST_WAIT_W);      // Past W
    assign led[3] = (state == ST_DONE);       // Done

    // Delays
    localparam DELAY_15MS = 28'd375000;   // Wait for LCD init
    localparam DELAY_2MS  = 28'd50000;    // Between commands
    localparam DELAY_1MS  = 28'd25000;    // Between chars

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            state <= ST_INIT_WAIT;
            delay_counter <= 28'd0;
            lcd_cs <= 1'b0;
            lcd_we <= 1'b0;
            lcd_addr <= 8'h00;
            lcd_data_in <= 8'h00;
            uart_tx_start <= 1'b0;
            uart_tx_data <= 8'h00;

        end else begin
            // Default: no writes
            lcd_cs <= 1'b0;
            lcd_we <= 1'b0;
            uart_tx_start <= 1'b0;

            case (state)
                ST_INIT_WAIT: begin
                    // Wait for LCD initialization to complete
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_15MS) begin
                        state <= ST_CLEAR_CMD;
                        delay_counter <= 28'd0;
                        // Send 'I' to UART (Init done)
                        uart_tx_data <= 8'h49;  // 'I'
                        uart_tx_start <= 1'b1;
                    end
                end

                ST_CLEAR_CMD: begin
                    // Write clear command (0x01) to LCD command register
                    lcd_cs <= 1'b1;
                    lcd_we <= 1'b1;
                    lcd_addr <= 8'h01;      // Command register
                    lcd_data_in <= 8'h01;   // Clear display
                    state <= ST_CLEAR_HOLD;
                    delay_counter <= 28'd0;
                    // Send 'C' to UART (Clear sent)
                    uart_tx_data <= 8'h43;  // 'C'
                    uart_tx_start <= 1'b1;
                end

                ST_CLEAR_HOLD: begin
                    // Hold write signals for a few more cycles
                    lcd_cs <= 1'b1;
                    lcd_we <= 1'b1;
                    lcd_addr <= 8'h01;
                    lcd_data_in <= 8'h01;
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= 28'd10) begin  // Hold for 10 cycles
                        state <= ST_CLEAR_WAIT;
                        delay_counter <= 28'd0;
                    end
                end

                ST_CLEAR_WAIT: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_2MS) begin
                        state <= ST_WRITE_H;
                        delay_counter <= 28'd0;
                    end
                end

                ST_WRITE_H: begin
                    // Write 'H' to LCD data register
                    lcd_cs <= 1'b1;
                    lcd_we <= 1'b1;
                    lcd_addr <= 8'h00;      // Data register
                    lcd_data_in <= 8'h48;   // 'H'
                    state <= ST_HOLD_H;
                    delay_counter <= 28'd0;
                    // Send 'H' to UART
                    uart_tx_data <= 8'h48;  // 'H'
                    uart_tx_start <= 1'b1;
                end

                ST_HOLD_H: begin
                    // Hold write signals
                    lcd_cs <= 1'b1;
                    lcd_we <= 1'b1;
                    lcd_addr <= 8'h00;
                    lcd_data_in <= 8'h48;
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= 28'd10) begin
                        state <= ST_WAIT_H;
                        delay_counter <= 28'd0;
                    end
                end

                ST_WAIT_H: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_1MS) begin
                        state <= ST_WRITE_W;
                        delay_counter <= 28'd0;
                    end
                end

                ST_WRITE_W: begin
                    // Write 'W' to LCD data register
                    lcd_cs <= 1'b1;
                    lcd_we <= 1'b1;
                    lcd_addr <= 8'h00;      // Data register
                    lcd_data_in <= 8'h57;   // 'W'
                    state <= ST_HOLD_W;
                    delay_counter <= 28'd0;
                    // Send 'W' to UART
                    uart_tx_data <= 8'h57;  // 'W'
                    uart_tx_start <= 1'b1;
                end

                ST_HOLD_W: begin
                    // Hold write signals
                    lcd_cs <= 1'b1;
                    lcd_we <= 1'b1;
                    lcd_addr <= 8'h00;
                    lcd_data_in <= 8'h57;
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= 28'd10) begin
                        state <= ST_WAIT_W;
                        delay_counter <= 28'd0;
                    end
                end

                ST_WAIT_W: begin
                    delay_counter <= delay_counter + 1'b1;
                    if (delay_counter >= DELAY_1MS) begin
                        state <= ST_DONE;
                        // Send newline to UART
                        uart_tx_data <= 8'h0A;  // '\n'
                        uart_tx_start <= 1'b1;
                    end
                end

                ST_DONE: begin
                    // Stay here, LCD should show "HW"
                end

                default: state <= ST_INIT_WAIT;
            endcase
        end
    end

endmodule
