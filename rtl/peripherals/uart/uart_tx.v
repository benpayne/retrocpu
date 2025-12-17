//
// uart_tx.v - UART Transmitter Module
//
// Implements UART TX with configurable baud rate
//
// Author: RetroCPU Project
// License: MIT
//
// Features:
// - 8 data bits, No parity, 1 stop bit (8N1)
// - Configurable baud rate via parameters
// - tx_busy flag indicates transmission in progress
// - Single-cycle tx_start pulse triggers transmission
//
// Default Configuration:
//   Clock: 25 MHz
//   Baud Rate: 9600
//   Divider: 163 (actual 9585 baud, 0.16% error)
//
// Usage:
//   1. Wait for tx_busy == 0
//   2. Set tx_data to byte to transmit
//   3. Pulse tx_start high for 1 clock cycle
//   4. Wait for tx_busy == 0 before next byte
//

module uart_tx #(
    parameter CLK_FREQ = 25000000,  // System clock frequency (Hz)
    parameter BAUD_RATE = 9600       // Baud rate (bits/second)
) (
    input  wire clk,          // System clock
    input  wire rst,          // Synchronous reset (active high)
    input  wire tx_start,     // Start transmission (pulse high for 1 cycle)
    input  wire [7:0] tx_data, // Data byte to transmit
    output reg  tx,           // UART TX line
    output reg  tx_busy       // Busy flag (1 = transmission in progress)
);

    // Baud rate divider calculation
    localparam DIVIDER = CLK_FREQ / BAUD_RATE;
    localparam DIVIDER_WIDTH = $clog2(DIVIDER);

    // State machine states
    localparam STATE_IDLE  = 3'b000;
    localparam STATE_START = 3'b001;
    localparam STATE_DATA  = 3'b010;
    localparam STATE_STOP  = 3'b011;

    // State machine
    reg [2:0] state;
    reg [DIVIDER_WIDTH-1:0] baud_counter;
    reg [2:0] bit_index;
    reg [7:0] tx_shift_reg;

    // Baud rate tick generator
    wire baud_tick;
    assign baud_tick = (baud_counter == DIVIDER - 1);

    always @(posedge clk) begin
        if (rst) begin
            state <= STATE_IDLE;
            tx <= 1'b1;  // Idle high
            tx_busy <= 1'b0;
            baud_counter <= 0;
            bit_index <= 0;
            tx_shift_reg <= 8'h00;
        end else begin
            case (state)
                STATE_IDLE: begin
                    tx <= 1'b1;  // Idle high
                    tx_busy <= 1'b0;
                    baud_counter <= 0;
                    bit_index <= 0;

                    if (tx_start) begin
                        tx_shift_reg <= tx_data;
                        tx_busy <= 1'b1;
                        state <= STATE_START;
                    end
                end

                STATE_START: begin
                    tx <= 1'b0;  // Start bit (low)

                    if (baud_tick) begin
                        baud_counter <= 0;
                        state <= STATE_DATA;
                        bit_index <= 0;
                    end else begin
                        baud_counter <= baud_counter + 1;
                    end
                end

                STATE_DATA: begin
                    tx <= tx_shift_reg[0];  // Transmit LSB first

                    if (baud_tick) begin
                        baud_counter <= 0;
                        tx_shift_reg <= {1'b0, tx_shift_reg[7:1]};  // Shift right
                        bit_index <= bit_index + 1;

                        if (bit_index == 7) begin
                            state <= STATE_STOP;
                        end
                    end else begin
                        baud_counter <= baud_counter + 1;
                    end
                end

                STATE_STOP: begin
                    tx <= 1'b1;  // Stop bit (high)

                    if (baud_tick) begin
                        baud_counter <= 0;
                        state <= STATE_IDLE;
                        tx_busy <= 1'b0;
                    end else begin
                        baud_counter <= baud_counter + 1;
                    end
                end

                default: begin
                    state <= STATE_IDLE;
                    tx <= 1'b1;
                    tx_busy <= 1'b0;
                end
            endcase
        end
    end

endmodule
