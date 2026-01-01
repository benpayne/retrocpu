//
// gpu_registers.v - Memory-Mapped Register Interface for DVI Character Display GPU
//
// Implements CPU-accessible control and status registers for the text mode GPU
//
// Author: RetroCPU Project
// License: MIT
//
// Features:
// - 7 memory-mapped registers (0xC010-0xC016) for GPU control
// - Character output with automatic cursor advance, line wrap, and scroll
// - Cursor position control (row/column)
// - Display mode control (40-column / 80-column)
// - Foreground and background color control (3-bit RGB)
// - Screen clear command
// - Status register (GPU ready, VSYNC)
// - Direct interface to character buffer for fast writes
//
// Register Map (Base Address: 0xC010-0xC016):
//   0xC010 (offset 0x0): CHAR_DATA (WO) - Write character at cursor, auto-advance
//   0xC011 (offset 0x1): CURSOR_ROW (RW) - Cursor row position (0-29)
//   0xC012 (offset 0x2): CURSOR_COL (RW) - Cursor column position (0-39 or 0-79)
//   0xC013 (offset 0x3): CONTROL (WO) - bit[0]=CLEAR, bit[1]=MODE, bit[2]=CURSOR_EN
//   0xC014 (offset 0x4): FG_COLOR (RW) - Foreground color (3-bit RGB)
//   0xC015 (offset 0x5): BG_COLOR (RW) - Background color (3-bit RGB)
//   0xC016 (offset 0x6): STATUS (RO) - bit[0]=READY, bit[1]=VSYNC
//
// Reset Values:
//   CURSOR_ROW: 0x00, CURSOR_COL: 0x00
//   CONTROL: 0x04 (40-column mode, cursor enabled)
//   FG_COLOR: 0x07 (white), BG_COLOR: 0x00 (black)
//
// Cursor Auto-Advance Behavior:
//   1. Character write increments column
//   2. At end of line (col == max_col), wrap to start of next line
//   3. At last row (row == 29) and end of line, trigger scroll and stay at row 29
//
// Mode Switching:
//   Changing MODE bit (bit 1 of CONTROL) triggers automatic screen clear
//   and cursor reset to (0,0)
//
// Reference: specs/003-hdmi-character-display/contracts/register_map.md
//

module gpu_registers(
    input  wire        clk,             // System clock (CPU clock domain)
    input  wire        rst_n,           // Active-low reset

    // CPU bus interface
    input  wire [3:0]  addr,            // Register offset (0x0-0xF)
    input  wire [7:0]  data_in,         // Data from CPU
    output reg  [7:0]  data_out,        // Data to CPU
    input  wire        we,              // Write enable
    input  wire        re,              // Read enable

    // Control outputs (to GPU core)
    output reg  [4:0]  cursor_row,      // 0-29 (5 bits)
    output reg  [6:0]  cursor_col,      // 0-39 or 0-79 (7 bits)
    output reg         mode_80col,      // 0=40-column, 1=80-column
    output reg         cursor_enable,   // Cursor visibility
    output reg  [2:0]  fg_color,        // Foreground color (3-bit RGB)
    output reg  [2:0]  bg_color,        // Background color (3-bit RGB)
    output reg         clear_screen,    // Pulse when clear requested
    output reg         scroll_screen,   // Pulse when scroll requested

    // Status inputs (from GPU core)
    input  wire        gpu_ready,       // GPU ready for commands
    input  wire        vsync,           // Vertical sync signal

    // Character buffer write interface
    output reg  [11:0] char_buf_addr,   // Address to write in character buffer
    output reg  [7:0]  char_buf_data,   // Character data to write
    output reg         char_buf_we      // Write enable to character buffer
);

    // Register addresses
    localparam ADDR_CHAR_DATA   = 4'h0;
    localparam ADDR_CURSOR_ROW  = 4'h1;
    localparam ADDR_CURSOR_COL  = 4'h2;
    localparam ADDR_CONTROL     = 4'h3;
    localparam ADDR_FG_COLOR    = 4'h4;
    localparam ADDR_BG_COLOR    = 4'h5;
    localparam ADDR_STATUS      = 4'h6;

    // Control register bits
    localparam CTRL_CLEAR       = 0;
    localparam CTRL_MODE        = 1;
    localparam CTRL_CURSOR_EN   = 2;

    // Internal registers
    reg        mode_80col_prev;         // Previous mode for change detection

    // Maximum column based on current mode
    wire [6:0] max_col = mode_80col ? 7'd79 : 7'd39;

    // Calculate character buffer address from cursor position
    // Address = row * columns + col
    wire [11:0] cursor_buffer_addr = mode_80col ?
                                     ({7'b0, cursor_row} * 12'd80) + {5'b0, cursor_col} :
                                     ({7'b0, cursor_row} * 12'd40) + {5'b0, cursor_col};

    // Reset and register write logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all registers to default values
            cursor_row      <= 5'd0;
            cursor_col      <= 7'd0;
            mode_80col      <= 1'b0;        // 40-column mode
            cursor_enable   <= 1'b1;        // Cursor enabled
            fg_color        <= 3'b111;      // White (0x07)
            bg_color        <= 3'b000;      // Black (0x00)
            clear_screen    <= 1'b0;
            scroll_screen   <= 1'b0;
            char_buf_we     <= 1'b0;
            char_buf_addr   <= 12'd0;
            char_buf_data   <= 8'd0;
            mode_80col_prev <= 1'b0;
        end else begin
            // Default: clear one-shot signals
            clear_screen    <= 1'b0;
            scroll_screen   <= 1'b0;
            char_buf_we     <= 1'b0;

            // Track mode changes
            mode_80col_prev <= mode_80col;

            // Handle CPU register writes
            if (we) begin
                case (addr)
                    // 0xC010: CHAR_DATA - Write character and auto-advance cursor
                    ADDR_CHAR_DATA: begin
                        // Write character to buffer at current cursor position
                        char_buf_addr <= cursor_buffer_addr;
                        char_buf_data <= data_in;
                        char_buf_we   <= 1'b1;

                        // Auto-advance cursor
                        if (cursor_col < max_col) begin
                            // Normal advance: increment column
                            cursor_col <= cursor_col + 7'd1;
                        end else begin
                            // End of line: wrap to start of next line
                            cursor_col <= 7'd0;
                            if (cursor_row < 5'd29) begin
                                // Not at last row: advance to next row
                                cursor_row <= cursor_row + 5'd1;
                            end else begin
                                // At last row: trigger scroll and stay at row 29
                                scroll_screen <= 1'b1;
                                cursor_row <= 5'd29;
                            end
                        end
                    end

                    // 0xC011: CURSOR_ROW - Set cursor row (clamp to 0-29)
                    ADDR_CURSOR_ROW: begin
                        if (data_in[4:0] <= 5'd29)
                            cursor_row <= data_in[4:0];
                        else
                            cursor_row <= 5'd29;  // Clamp to max row
                    end

                    // 0xC012: CURSOR_COL - Set cursor column (clamp based on mode)
                    ADDR_CURSOR_COL: begin
                        if (data_in[6:0] <= max_col)
                            cursor_col <= data_in[6:0];
                        else
                            cursor_col <= max_col;  // Clamp to max column
                    end

                    // 0xC013: CONTROL - Display mode, clear, cursor enable
                    ADDR_CONTROL: begin
                        // Bit 0: CLEAR - Trigger screen clear (self-clearing pulse)
                        if (data_in[CTRL_CLEAR]) begin
                            clear_screen <= 1'b1;
                            cursor_row   <= 5'd0;
                            cursor_col   <= 7'd0;
                        end

                        // Bit 1: MODE - Set display mode (40-col / 80-col)
                        // Mode change triggers automatic clear and cursor reset
                        if (data_in[CTRL_MODE] != mode_80col) begin
                            mode_80col   <= data_in[CTRL_MODE];
                            clear_screen <= 1'b1;
                            cursor_row   <= 5'd0;
                            cursor_col   <= 7'd0;
                        end

                        // Bit 2: CURSOR_EN - Cursor visibility
                        cursor_enable <= data_in[CTRL_CURSOR_EN];
                    end

                    // 0xC014: FG_COLOR - Foreground color (mask to 3 bits)
                    ADDR_FG_COLOR: begin
                        fg_color <= data_in[2:0];
                    end

                    // 0xC015: BG_COLOR - Background color (mask to 3 bits)
                    ADDR_BG_COLOR: begin
                        bg_color <= data_in[2:0];
                    end

                    // Other addresses: write ignored
                    default: begin
                        // No action
                    end
                endcase
            end
        end
    end

    // Register read logic
    always @(*) begin
        if (re) begin
            case (addr)
                // 0xC011: CURSOR_ROW - Read cursor row (bits 4:0)
                ADDR_CURSOR_ROW: begin
                    data_out = {3'b000, cursor_row};
                end

                // 0xC012: CURSOR_COL - Read cursor column (bits 6:0)
                ADDR_CURSOR_COL: begin
                    data_out = {1'b0, cursor_col};
                end

                // 0xC014: FG_COLOR - Read foreground color (bits 2:0)
                ADDR_FG_COLOR: begin
                    data_out = {5'b00000, fg_color};
                end

                // 0xC015: BG_COLOR - Read background color (bits 2:0)
                ADDR_BG_COLOR: begin
                    data_out = {5'b00000, bg_color};
                end

                // 0xC016: STATUS - Read GPU status
                ADDR_STATUS: begin
                    data_out = {6'b000000, vsync, gpu_ready};
                end

                // Other addresses: read as 0x00
                default: begin
                    data_out = 8'h00;
                end
            endcase
        end else begin
            data_out = 8'h00;
        end
    end

endmodule
