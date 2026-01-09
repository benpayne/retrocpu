`timescale 1ns / 1ps

//
// uart_rx_fifo.v - UART Receiver with FIFO Buffer
//
// Wraps uart_rx.v with a FIFO buffer to prevent data loss
//
// Features:
// - Configurable FIFO depth (default 16 bytes)
// - Prevents overflow when CPU can't read fast enough
// - Compatible interface with original uart_rx
//

module uart_rx_fifo #(
    parameter CLK_FREQ = 25000000,   // System clock frequency (Hz)
    parameter BAUD_RATE = 9600,      // Baud rate (bits/second)
    parameter FIFO_DEPTH = 16        // FIFO depth in bytes (must be power of 2)
) (
    input  wire clk,                 // System clock
    input  wire rst,                 // Synchronous reset (active high)
    input  wire rx,                  // UART RX line
    input  wire rd_en,               // Read enable from CPU
    output wire [7:0] rx_data,       // Data output to CPU
    output wire rx_ready,            // Data available flag
    output wire fifo_full,           // FIFO full flag (for debugging)
    output wire fifo_empty           // FIFO empty flag
);

    // FIFO pointer width
    localparam PTR_WIDTH = $clog2(FIFO_DEPTH);

    // Internal signals from UART RX core
    wire [7:0] uart_rx_data;
    wire uart_rx_ready;

    // Instantiate the core UART RX module
    uart_rx #(
        .CLK_FREQ(CLK_FREQ),
        .BAUD_RATE(BAUD_RATE)
    ) uart_rx_inst (
        .clk(clk),
        .rst(rst),
        .rx(rx),
        .rx_data(uart_rx_data),
        .rx_ready(uart_rx_ready)
    );

    // FIFO storage
    reg [7:0] fifo_mem [0:FIFO_DEPTH-1];
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [PTR_WIDTH-1:0] rd_ptr;
    reg [PTR_WIDTH:0] count;  // Extra bit to distinguish full from empty
    reg [7:0] rx_data_reg;  // Register output data to hold stable during CPU read

    // FIFO status
    assign fifo_empty = (count == 0);
    assign fifo_full = (count == FIFO_DEPTH);
    assign rx_ready = ~fifo_empty;
    assign rx_data = rx_data_reg;  // Output from registered value

    // Separate always block for output register to ensure it updates correctly
    always @(posedge clk) begin
        if (rst) begin
            rx_data_reg <= 8'h00;
        end else begin
            // Update output register when FIFO becomes non-empty or when rd_ptr changes
            // This ensures stable output during CPU read cycles
            if (count > 0) begin
                rx_data_reg <= fifo_mem[rd_ptr];
            end
        end
    end

    // FIFO read/write pointer management
    always @(posedge clk) begin
        if (rst) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            count <= 0;
        end else begin
            // Handle FIFO read and write with proper count management
            // uart_rx_ready is a one-cycle pulse - sample directly
            case ({uart_rx_ready && !fifo_full, rd_en && !fifo_empty})
                2'b10: begin // Write only
                    fifo_mem[wr_ptr] <= uart_rx_data;
                    wr_ptr <= wr_ptr + 1;
                    count <= count + 1;
                end
                2'b01: begin // Read only
                    rd_ptr <= rd_ptr + 1;
                    count <= count - 1;
                end
                2'b11: begin // Both read and write (count stays same)
                    fifo_mem[wr_ptr] <= uart_rx_data;
                    wr_ptr <= wr_ptr + 1;
                    rd_ptr <= rd_ptr + 1;
                    // count stays the same
                end
                default: begin // Neither read nor write
                    // Nothing to do
                end
            endcase
        end
    end

endmodule
