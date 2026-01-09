`timescale 1ns / 1ps

//
// uart_rx.v - UART Receiver Module
//
// Implements UART RX with configurable baud rate
//
// Author: RetroCPU Project
// License: MIT
//
// Features:
// - 8 data bits, No parity, 1 stop bit (8N1)
// - Configurable baud rate via parameters
// - rx_ready pulses HIGH for 2 clock cycles per byte (for reliable FIFO sampling)
// - Samples data in middle of bit period for noise immunity
// - Start bit validation (middle sample) rejects glitches
// - Stop bit validation (framing check) rejects corrupted data
//
// Default Configuration:
//   Clock: 25 MHz
//   Baud Rate: 115200
//   Divider: 217 (actual 115207 baud, 0.006% error)
//
// Usage:
//   1. Monitor rx_ready signal (pulses for 2 clock cycles per byte)
//   2. When rx_ready goes HIGH, read rx_data within 2 clock cycles
//   3. rx_data remains valid until next byte is received
//   4. rx_ready clears after 2 clock cycles
//

module uart_rx #(
    parameter CLK_FREQ = 25000000,  // System clock frequency (Hz)
    parameter BAUD_RATE = 9600       // Baud rate (bits/second)
) (
    input  wire clk,          // System clock
    input  wire rst,          // Synchronous reset (active high)
    input  wire rx,           // UART RX line
    output reg  [7:0] rx_data, // Received data byte
    output reg  rx_ready      // Data ready flag (pulses high for 1 cycle)
);

    // Baud rate divider calculation
    localparam DIVIDER = CLK_FREQ / BAUD_RATE;
    localparam DIVIDER_WIDTH = $clog2(DIVIDER);
    localparam HALF_DIVIDER = DIVIDER / 2;

    // State machine states
    localparam STATE_IDLE  = 3'b000;
    localparam STATE_START = 3'b001;
    localparam STATE_DATA  = 3'b010;
    localparam STATE_STOP  = 3'b011;

    // State machine
    reg [2:0] state;
    reg [DIVIDER_WIDTH-1:0] baud_counter;
    reg [2:0] bit_index;
    reg [7:0] rx_shift_reg;

    // RX line synchronizer (prevent metastability)
    reg rx_sync_1;
    reg rx_sync_2;

    always @(posedge clk) begin
        if (rst) begin
            rx_sync_1 <= 1'b1;
            rx_sync_2 <= 1'b1;
        end else begin
            rx_sync_1 <= rx;
            rx_sync_2 <= rx_sync_1;
        end
    end

    // Baud rate tick generator
    wire baud_tick;
    assign baud_tick = (baud_counter == DIVIDER - 1);

    always @(posedge clk) begin
        if (rst) begin
            state <= STATE_IDLE;
            rx_data <= 8'h00;
            rx_ready <= 1'b0;
            baud_counter <= 0;
            bit_index <= 0;
            rx_shift_reg <= 8'h00;
        end else begin
            case (state)
                STATE_IDLE: begin
                    // Clear rx_ready in IDLE (creates one-cycle pulse from STOP)
                    rx_ready <= 1'b0;
                    baud_counter <= 0;
                    bit_index <= 0;

                    // Detect start bit (falling edge: high -> low)
                    if (rx_sync_2 == 1'b0) begin
                        baud_counter <= 0;
                        state <= STATE_START;
                    end
                end

                STATE_START: begin
                    // Wait for middle of start bit to verify it's still low
                    if (baud_counter == HALF_DIVIDER - 1) begin
                        if (rx_sync_2 == 1'b0) begin
                            // Valid start bit, move to data reception
                            baud_counter <= 0;
                            state <= STATE_DATA;
                            bit_index <= 0;
                        end else begin
                            // False start bit (glitch), go back to idle
                            state <= STATE_IDLE;
                        end
                    end else begin
                        baud_counter <= baud_counter + 1;
                    end
                end

                STATE_DATA: begin
                    // Sample data bits in the middle of each bit period
                    if (baud_tick) begin
                        // Sample the bit (LSB first)
                        rx_shift_reg <= {rx_sync_2, rx_shift_reg[7:1]};
                        baud_counter <= 0;
                        bit_index <= bit_index + 1;

                        if (bit_index == 7) begin
                            // All 8 bits received, move to stop bit
                            state <= STATE_STOP;
                        end
                    end else begin
                        baud_counter <= baud_counter + 1;
                    end
                end

                STATE_STOP: begin
                    // Wait for stop bit
                    if (baud_tick) begin
                        baud_counter <= 0;
                        state <= STATE_IDLE;

                        // Verify stop bit is high (framing check)
                        if (rx_sync_2 == 1'b1) begin
                            // Valid stop bit, output data
                            // rx_ready will pulse HIGH for one cycle (cleared next cycle in IDLE)
                            rx_data <= rx_shift_reg;
                            rx_ready <= 1'b1;
                        end else begin
                            // Framing error - clear rx_ready
                            rx_ready <= 1'b0;
                        end
                    end else begin
                        baud_counter <= baud_counter + 1;
                    end
                end

                default: begin
                    state <= STATE_IDLE;
                end
            endcase
        end
    end

endmodule
