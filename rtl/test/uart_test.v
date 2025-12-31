//
// uart_test.v - Simple UART Test Module
//
// Sends ASCII characters 'A' through 'Z' repeatedly, one per second
// For debugging UART transmission and baud rate
//

module uart_test (
    input  wire clk_25mhz,        // 25 MHz clock
    input  wire reset_button_n,   // Reset button (active-low)

    output wire uart_tx,          // UART TX line
    output wire [3:0] led         // Status LEDs
);

    // Reset controller
    wire system_rst;

    reset_controller rst_ctrl (
        .clk(clk_25mhz),
        .reset_button_n(reset_button_n),
        .rst(system_rst)
    );

    // Timer for 1 second intervals (25M cycles at 25 MHz)
    localparam SECOND_COUNT = 25_000_000;
    reg [24:0] timer;
    reg send_pulse;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            timer <= 0;
            send_pulse <= 0;
        end else begin
            send_pulse <= 0;  // One-cycle pulse

            if (timer >= SECOND_COUNT - 1) begin
                timer <= 0;
                send_pulse <= 1;
            end else begin
                timer <= timer + 1;
            end
        end
    end

    // Character counter (A-Z, then repeat)
    reg [7:0] char_data;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            char_data <= 8'h41;  // 'A'
        end else if (send_pulse) begin
            if (char_data >= 8'h5A) begin  // 'Z'
                char_data <= 8'h41;  // Wrap to 'A'
            end else begin
                char_data <= char_data + 1;
            end
        end
    end

    // UART transmitter
    reg tx_start;
    wire tx_busy;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            tx_start <= 0;
        end else begin
            tx_start <= 0;  // Default

            if (send_pulse && !tx_busy) begin
                tx_start <= 1;
            end
        end
    end

    uart_tx #(
        .CLK_FREQ(25_000_000),
        .BAUD_RATE(9600)
    ) uart_tx_inst (
        .clk(clk_25mhz),
        .rst(system_rst),
        .tx_start(tx_start),
        .tx_data(char_data),
        .tx(uart_tx),
        .tx_busy(tx_busy)
    );

    // LED indicators
    assign led[0] = system_rst;           // On during reset
    assign led[1] = timer[23];            // Blink ~1.5 Hz (visible heartbeat)
    assign led[2] = tx_busy;              // On when transmitting
    assign led[3] = char_data[0];         // Toggle with character changes

endmodule
