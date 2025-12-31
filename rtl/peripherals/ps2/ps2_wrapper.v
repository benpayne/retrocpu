/**
 * PS/2 Keyboard Memory-Mapped Wrapper for 6502 CPU
 *
 * Direct instantiation of proven ps2-controller-lib components.
 * Bypasses ps2_complete_wrapper to ensure proper reset handling.
 *
 * Memory Map:
 *   $C200 (addr[0]=0): DATA register - Read scan code byte from FIFO
 *   $C201 (addr[0]=1): STATUS register
 *     - Bit 0: data_ready (1 = scan codes available in FIFO)
 *     - Bit 1: interrupt flag (sticky, cleared on STATUS read)
 *     - Bits 2-7: reserved (0)
 *
 * Hardware Interface:
 *   - ps2_clk: PS/2 keyboard clock input (pulled up externally)
 *   - ps2_data: PS/2 keyboard data input (pulled up externally)
 */

module ps2_wrapper #(
    parameter CLK_FREQ_HZ = 25_000_000   // 25 MHz system clock
)(
    // System signals
    input  wire       clk,
    input  wire       reset,             // Active-high reset

    // PS/2 hardware signals (raw)
    input  wire       ps2_clk,
    input  wire       ps2_data,

    // CPU interface (memory-mapped)
    input  wire       cs,                // Chip select (active high)
    input  wire       rd,                // Read strobe (active high)
    input  wire       addr,              // Address bit 0 (0=DATA, 1=STATUS)
    output reg  [7:0] data_out,          // Data output to CPU

    // Interrupt output
    output wire       irq,               // Interrupt request (active high)

    // Debug outputs
    output wire       debug_valid,       // Scan code received (valid pulse)
    output wire       debug_fifo_empty,  // FIFO empty
    output wire [3:0] debug_count,       // FIFO count (0-8)
    output wire       debug_ps2_clk_deb, // Debounced PS/2 clock
    output wire       debug_ps2_data_deb // Debounced PS/2 data
);

    // ========================================================================
    // Debounced PS/2 Signals
    // ========================================================================

    wire ps2_clk_debounced;
    wire ps2_data_debounced;

    // Debounce PS/2 clock - use 128 cycles like proven test
    debounce #(
        .DEBOUNCE_CYCLES(128)  // 128 cycles @ 25MHz (proven to work)
    ) debounce_clk (
        .clk(clk),
        .reset(reset),
        .button(ps2_clk),
        .debounced_button(ps2_clk_debounced)
    );

    // Debounce PS/2 data - use 128 cycles like proven test
    debounce #(
        .DEBOUNCE_CYCLES(128)  // 128 cycles @ 25MHz (proven to work)
    ) debounce_data (
        .clk(clk),
        .reset(reset),
        .button(ps2_data),
        .debounced_button(ps2_data_debounced)
    );

    // ========================================================================
    // PS/2 Decoder Core
    // ========================================================================

    wire       valid;               // Valid scan code pulse from decoder
    wire [7:0] scan_code;           // Raw scan code from decoder
    wire       ps2_interrupt;       // Interrupt from decoder (sticky)

    // Auto-clear interrupt one cycle after valid
    reg int_clear_reg;
    always @(posedge clk) begin
        if (reset) begin
            int_clear_reg <= 1'b0;
        end else begin
            int_clear_reg <= valid;  // Clear interrupt one cycle after valid
        end
    end

    ps2_decoder_core #(
        .CLK_FREQ_HZ(CLK_FREQ_HZ),
        .PS2_CLK_HZ(10_000)         // 10 kHz PS/2 clock (typ 10-16.7 kHz)
    ) ps2_core (
        .clk(clk),
        .reset(reset),
        .ps2_clk(ps2_clk_debounced), // Use debounced signals (proven to work)
        .ps2_data(ps2_data_debounced), // Use debounced signals (proven to work)
        .int_clear(int_clear_reg),
        .valid(valid),
        .interrupt(ps2_interrupt),
        .data(scan_code)
    );

    // ========================================================================
    // FIFO Buffer (8 entries)
    // ========================================================================

    reg [7:0] fifo [0:7];
    reg [2:0] wr_ptr;               // Write pointer (0-7)
    reg [2:0] rd_ptr;               // Read pointer (0-7)
    reg [3:0] count;                // Number of entries in FIFO (0-8)

    wire      fifo_empty;
    wire      fifo_full;
    wire      data_ready;
    reg       interrupt_flag;       // Sticky interrupt flag

    assign fifo_empty = (count == 4'd0);
    assign fifo_full  = (count == 4'd8);
    assign data_ready = !fifo_empty;

    // FIFO control signals
    wire       doing_write;
    wire       doing_read;

    assign doing_write = valid && !fifo_full;
    assign doing_read = cs && rd && (addr == 1'b0) && !fifo_empty;

    // FIFO write/read logic
    always @(posedge clk) begin
        if (reset) begin
            wr_ptr <= 3'd0;
            rd_ptr <= 3'd0;
            count  <= 4'd0;
            interrupt_flag <= 1'b0;
        end else begin
            // Write to FIFO when valid scan code arrives
            if (doing_write) begin
                fifo[wr_ptr] <= scan_code;
                wr_ptr <= wr_ptr + 3'd1;
                interrupt_flag <= 1'b1;
            end

            // Read from FIFO when CPU reads DATA register
            if (doing_read) begin
                rd_ptr <= rd_ptr + 3'd1;
            end

            // Update count based on read/write operations
            case ({doing_write, doing_read})
                2'b10: count <= count + 4'd1;  // Write only
                2'b01: count <= count - 4'd1;  // Read only
                2'b11: count <= count;          // Simultaneous read/write
                2'b00: count <= count;          // No operation
            endcase

            // Clear interrupt flag when CPU reads STATUS register
            if (cs && rd && (addr == 1'b1)) begin
                interrupt_flag <= 1'b0;
            end
        end
    end

    // Data output register (registered at read strobe)
    // Captures output when CPU reads (rd strobe at MC=7)
    // Holds value through MC=5 and MC=4 for proper CPU capture timing
    always @(posedge clk) begin
        if (reset) begin
            data_out <= 8'h00;
        end else if (rd) begin  // Capture when read strobe arrives (cs && MC=7)
            if (addr == 1'b0) begin
                // DATA register - output from FIFO
                if (!fifo_empty)
                    data_out <= fifo[rd_ptr];
                else
                    data_out <= 8'h00;
            end else begin
                // STATUS register
                data_out <= {6'b000000, interrupt_flag, data_ready};
            end
        end
        // else: hold previous value (through MC=5 and MC=4)
    end

    // Interrupt request output
    assign irq = interrupt_flag;

    // ========================================================================
    // Debug: Sticky Valid Flag (visible on LED)
    // ========================================================================

    reg sticky_valid;  // Stays high until CPU reads STATUS

    always @(posedge clk) begin
        if (reset) begin
            sticky_valid <= 1'b0;
        end else begin
            // Set when valid scan code arrives
            if (valid) begin
                sticky_valid <= 1'b1;
            end

            // Clear when CPU reads STATUS register
            if (cs && rd && (addr == 1'b1)) begin
                sticky_valid <= 1'b0;
            end
        end
    end

    // ========================================================================
    // Debug Outputs
    // ========================================================================

    assign debug_valid = sticky_valid;      // Sticky flag (visible on LED)
    assign debug_fifo_empty = fifo_empty;
    assign debug_count = count;             // FIFO count
    assign debug_ps2_clk_deb = ps2_clk_debounced;
    assign debug_ps2_data_deb = ps2_data_debounced;

endmodule
