//
// address_decoder.v - Memory Map Address Decoder
//
// Decodes 16-bit 6502 address to chip selects for memory and I/O
//
// Author: RetroCPU Project
// License: MIT
//
// Memory Map:
//   0x0000-0x7FFF : RAM (32 KB)
//   0x8000-0xBFFF : BASIC ROM (16 KB)
//   0xC000-0xC0FF : UART (256 bytes)
//   0xC100-0xC1FF : LCD (256 bytes)
//   0xC200-0xC2FF : PS/2 Keyboard (256 bytes)
//   0xC300-0xDFFF : Reserved I/O
//   0xE000-0xFFFF : Monitor ROM (8 KB)
//
// Features:
// - Purely combinational (no clock required)
// - Page-aligned I/O devices (256-byte blocks)
// - Mutually exclusive chip selects for main regions
// - Simple decode logic for FPGA efficiency
//

module address_decoder (
    input  wire [15:0] addr,          // 16-bit address from CPU

    // Main memory chip selects
    output wire ram_cs,               // RAM select (0x0000-0x7FFF)
    output wire rom_basic_cs,         // BASIC ROM select (0x8000-0xBFFF)
    output wire rom_monitor_cs,       // Monitor ROM select (0xE000-0xFFFF)

    // I/O region selects
    output wire io_cs,                // I/O region select (0xC000-0xDFFF)
    output wire uart_cs,              // UART select (0xC000-0xC0FF)
    output wire lcd_cs,               // LCD select (0xC100-0xC1FF)
    output wire ps2_cs                // PS/2 select (0xC200-0xC2FF)
);

    //
    // Main Memory Region Decode
    // Uses top address bits for simple decode
    //

    // RAM: addr[15] == 0 (0x0000-0x7FFF)
    assign ram_cs = (addr[15] == 1'b0);

    // BASIC ROM: addr[15:14] == 10 (0x8000-0xBFFF)
    assign rom_basic_cs = (addr[15:14] == 2'b10);

    // I/O Region: addr[15:13] == 110 (0xC000-0xDFFF)
    assign io_cs = (addr[15:13] == 3'b110);

    // Monitor ROM: addr[15:13] == 111 (0xE000-0xFFFF)
    assign rom_monitor_cs = (addr[15:13] == 3'b111);

    //
    // I/O Device Decode (within 0xC000-0xDFFF)
    // Page-aligned: uses addr[11:8] to select 256-byte blocks
    //

    // UART: 0xC0xx (addr[11:8] == 0000)
    assign uart_cs = io_cs && (addr[11:8] == 4'h0);

    // LCD: 0xC1xx (addr[11:8] == 0001)
    assign lcd_cs = io_cs && (addr[11:8] == 4'h1);

    // PS/2: 0xC2xx (addr[11:8] == 0010)
    assign ps2_cs = io_cs && (addr[11:8] == 4'h2);

    // Reserved I/O: 0xC3xx-0xDFxx
    // (io_cs will be high, but no device chip select)

endmodule
