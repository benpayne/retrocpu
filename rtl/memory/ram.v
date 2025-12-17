//
// ram.v - Block RAM Module for 6502 System
//
// Implements 32 KB of RAM using FPGA block RAM primitives
//
// Author: RetroCPU Project
// License: MIT
//
// Features:
// - Parameterized address and data width
// - Synchronous read and write
// - Single-cycle access (no wait states)
// - Infers ECP5 block RAM (DP16KD primitives)
//
// Address Range: 0x0000-0x7FFF (32 KB)
// Usage:
//   - Zero Page: 0x0000-0x00FF
//   - Stack: 0x0100-0x01FF
//   - General: 0x0200-0x7FFF
//

module ram #(
    parameter ADDR_WIDTH = 15,  // 32 KB = 2^15 bytes
    parameter DATA_WIDTH = 8    // 8-bit data bus
) (
    input  wire clk,                        // System clock
    input  wire rst,                        // Reset (unused, for consistency)
    input  wire we,                         // Write enable
    input  wire [ADDR_WIDTH-1:0] addr,      // Address input
    input  wire [DATA_WIDTH-1:0] data_in,   // Data input (write)
    output reg  [DATA_WIDTH-1:0] data_out   // Data output (read)
);

    // Memory array - will be inferred as block RAM by synthesis
    reg [DATA_WIDTH-1:0] mem [0:(1<<ADDR_WIDTH)-1];

    // Synchronous read and write
    always @(posedge clk) begin
        if (we) begin
            mem[addr] <= data_in;
        end
        data_out <= mem[addr];
    end

    // Optional: Initialize memory for simulation
    // (Not synthesized - only for testbench)
    integer i;
    initial begin
        for (i = 0; i < (1<<ADDR_WIDTH); i = i + 1) begin
            mem[i] = 8'h00;
        end
    end

endmodule
