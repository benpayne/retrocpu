//
// uart_counter_test.v - Simple UART test without CPU
//
// Just sends incrementing counters to UART to verify hardware works
//

module uart_counter_test (
    input  wire clk_25mhz,
    input  wire reset_button_n,
    output wire uart_tx,
    output wire [3:0] led
);

    // Reset
    wire system_rst;
    reset_controller rst_ctrl (
        .clk(clk_25mhz),
        .reset_button_n(reset_button_n),
        .rst(system_rst)
    );

    // Counter to send data periodically
    reg [23:0] timer;
    reg [7:0] counter;
    reg we_uart;
    wire [7:0] uart_status;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            timer <= 0;
            counter <= 8'h41;  // Start at 'A'
            we_uart <= 0;
        end else begin
            we_uart <= 0;  // Default: no write

            if (timer == 24'd12_500_000) begin  // Every 0.5 seconds
                timer <= 0;
                // Check if TX is ready (bit 0 of status)
                if (uart_status[0]) begin
                    we_uart <= 1;  // Write to UART data register
                    counter <= counter + 1;
                    if (counter >= 8'h5A) counter <= 8'h41;  // A-Z loop
                end
            end else begin
                timer <= timer + 1;
            end
        end
    end

    // UART instance
    uart #(
        .CLK_FREQ(25_000_000),
        .BAUD_RATE(9600)
    ) uart_inst (
        .clk(clk_25mhz),
        .rst(system_rst),
        .addr(8'h00),  // Write to data register
        .data_in(counter),
        .data_out(uart_status),
        .we(we_uart),
        .cs(1'b1),
        .tx(uart_tx),
        .rx(1'b1)
    );

    assign led = {system_rst, we_uart, counter[1:0]};

endmodule
