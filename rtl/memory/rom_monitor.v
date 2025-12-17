//
// rom_monitor.v - Monitor ROM Module
//
// Implements 8 KB monitor program ROM
//
// Author: RetroCPU Project
// License: MIT
//
// Features:
// - 8 KB ROM at 0xE000-0xFFFF
// - Initialized from monitor.hex file
// - Contains monitor program and 6502 vectors
// - Read-only (writes ignored)
//
// Memory Layout:
//   0xE000-0xFFEF : Monitor code (~8 KB - 17 bytes)
//   0xFFF0-0xFFF9 : BASIC I/O vectors (10 bytes)
//   0xFFFA-0xFFFB : NMI vector
//   0xFFFC-0xFFFD : RESET vector
//   0xFFFE-0xFFFF : IRQ/BRK vector
//

module rom_monitor #(
    parameter ADDR_WIDTH = 13,  // 8 KB = 2^13 bytes
    parameter DATA_WIDTH = 8,
    parameter HEX_FILE = "../firmware/monitor/monitor.hex"
) (
    input  wire clk,                        // System clock
    input  wire [ADDR_WIDTH-1:0] addr,      // Address input (13 bits for 8KB)
    output reg  [DATA_WIDTH-1:0] data_out   // Data output
);

    // ROM array
    reg [DATA_WIDTH-1:0] rom [0:(1<<ADDR_WIDTH)-1];

    // Synchronous read
    always @(posedge clk) begin
        data_out <= rom[addr];
    end

    // Initialize ROM from hex file
    initial begin
        $readmemh(HEX_FILE, rom);
    end

endmodule
