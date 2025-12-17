//
// rom_basic.v - BASIC ROM Module
//
// Implements 16 KB BASIC interpreter ROM
//
// Author: RetroCPU Project
// License: MIT
//
// Features:
// - 16 KB ROM at 0x8000-0xBFFF
// - Initialized from basic_rom.hex file
// - Contains Microsoft 6502 BASIC (EhBASIC)
// - Read-only (writes ignored)
//
// Entry Points (typical EhBASIC):
//   0x8000 : Cold start (initialize BASIC)
//   0x8003 : Warm start (preserve program)
//

module rom_basic #(
    parameter ADDR_WIDTH = 14,  // 16 KB = 2^14 bytes
    parameter DATA_WIDTH = 8,
    parameter HEX_FILE = "../firmware/basic/basic_rom.hex"
) (
    input  wire clk,                        // System clock
    input  wire [ADDR_WIDTH-1:0] addr,      // Address input (14 bits for 16KB)
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
