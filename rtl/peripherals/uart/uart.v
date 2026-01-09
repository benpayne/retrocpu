//
// uart.v - UART Top-Level Module with Memory-Mapped Registers
//
// Integrates UART TX and RX with memory-mapped interface
//
// Author: RetroCPU Project
// License: MIT
//
// Memory Map:
//   $C000: UART_DATA (R/W) - TX data register (write), RX data (read)
//   $C001: UART_STATUS (R) - Status register
//
// Status Register ($C001):
//   Bit 0: TX Ready (1 = can transmit, 0 = busy)
//   Bit 1: RX Ready (1 = data available, 0 = no data)
//   Bits 2-7: Reserved (read as 0)
//
// Usage TX:
//   1. Read $C001, check bit 0 (TX ready)
//   2. If ready, write byte to $C000
//   3. Byte will be transmitted over UART TX
//
// Usage RX:
//   1. Read $C001, check bit 1 (RX ready)
//   2. If data available, read byte from $C000
//   3. Reading $C000 clears RX ready flag
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
    input  wire rx                // UART RX line
);

    // Register addresses
    localparam ADDR_DATA   = 8'h00;  // $C000
    localparam ADDR_STATUS = 8'h01;  // $C001

    // TX control signals
    reg tx_start;
    reg [7:0] tx_data;
    wire tx_busy;

    // RX control signals (with FIFO)
    wire [7:0] rx_data_wire;
    wire rx_ready_flag;
    wire fifo_full;
    wire fifo_empty;
    wire rd_en;

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

    // UART RX instance with FIFO (16 bytes deep)
    uart_rx_fifo #(
        .CLK_FREQ(CLK_FREQ),
        .BAUD_RATE(BAUD_RATE),
        .FIFO_DEPTH(16)
    ) uart_rx_fifo_inst (
        .clk(clk),
        .rst(rst),
        .rx(rx),
        .rd_en(rd_en),
        .rx_data(rx_data_wire),
        .rx_ready(rx_ready_flag),
        .fifo_full(fifo_full),
        .fifo_empty(fifo_empty)
    );

    // RX Read logic - assert rd_en when CPU reads DATA register
    assign rd_en = (cs && !we && addr == ADDR_DATA);

    // TX Write logic
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

    // Read logic (combinational - data valid same cycle as address)
    // The CPU's registered data capture (at MC=5) breaks any combinational loops
    always @(*) begin
        // Default: return 0
        data_out = 8'h00;

        case (addr)
            ADDR_DATA: begin
                // Read RX data directly from FIFO
                data_out = rx_data_wire;
            end
            ADDR_STATUS: begin
                // Read status register - assign all 8 bits at once
                data_out = {6'b000000, rx_ready_flag, ~tx_busy};
            end
            default: begin
                data_out = 8'h00;
            end
        endcase
    end

endmodule
