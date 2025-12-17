//
// uart.v - UART Top-Level Module with Memory-Mapped Registers
//
// Integrates UART TX (and future RX) with memory-mapped interface
//
// Author: RetroCPU Project
// License: MIT
//
// Memory Map:
//   $C000: UART_DATA (R/W) - TX data register (write), RX data (read, future)
//   $C001: UART_STATUS (R) - Status register
//
// Status Register ($C001):
//   Bit 0: TX Ready (1 = can transmit, 0 = busy)
//   Bit 1: RX Ready (1 = data available, 0 = no data) [future]
//   Bits 2-7: Reserved (read as 0)
//
// Usage:
//   1. Read $C001, check bit 0 (TX ready)
//   2. If ready, write byte to $C000
//   3. Byte will be transmitted over UART TX
//

module uart #(
    parameter CLK_FREQ = 25000000,
    parameter BAUD_RATE = 9600
) (
    input  wire clk,              // System clock
    input  wire rst,              // Synchronous reset

    // Memory-mapped interface
    input  wire cs,               // Chip select (from address decoder)
    input  wire we,               // Write enable
    input  wire [7:0] addr,       // Address within UART region (bottom 8 bits)
    input  wire [7:0] data_in,    // Data from CPU
    output reg  [7:0] data_out,   // Data to CPU

    // UART physical interface
    output wire tx,               // UART TX line
    input  wire rx                // UART RX line (future)
);

    // Register addresses
    localparam ADDR_DATA   = 8'h00;  // $C000
    localparam ADDR_STATUS = 8'h01;  // $C001

    // TX control signals
    reg tx_start;
    reg [7:0] tx_data;
    wire tx_busy;

    // UART TX instance
    uart_tx #(
        .CLK_FREQ(CLK_FREQ),
        .BAUD_RATE(BAUD_RATE)
    ) uart_tx_inst (
        .clk(clk),
        .rst(rst),
        .tx_start(tx_start),
        .tx_data(tx_data),
        .tx(tx),
        .tx_busy(tx_busy)
    );

    // Write logic
    always @(posedge clk) begin
        if (rst) begin
            tx_start <= 1'b0;
            tx_data <= 8'h00;
        end else begin
            tx_start <= 1'b0;  // Default: no transmission

            if (cs && we) begin
                case (addr)
                    ADDR_DATA: begin
                        // Write to data register: start transmission
                        if (!tx_busy) begin  // Only accept if TX ready
                            tx_data <= data_in;
                            tx_start <= 1'b1;
                        end
                    end
                    // Other registers: writes ignored
                    default: begin
                        // No action
                    end
                endcase
            end
        end
    end

    // Read logic (registered to break combinational loops)
    // Register the address to avoid addr->data_out->CPU feedback
    reg [7:0] addr_reg;

    always @(posedge clk) begin
        if (rst) begin
            addr_reg <= 8'h00;
        end else begin
            addr_reg <= addr;
        end
    end

    always @(*) begin
        case (addr_reg)
            ADDR_DATA: begin
                // Read data register (future: RX data)
                data_out = 8'h00;  // No RX yet
            end
            ADDR_STATUS: begin
                // Read status register
                data_out[0] = ~tx_busy;  // TX ready = NOT busy
                data_out[1] = 1'b0;      // RX ready (future)
                data_out[7:2] = 6'b000000; // Reserved
            end
            default: begin
                data_out = 8'h00;
            end
        endcase
    end

endmodule
