//
// cpu_debug.v - CPU Debug Module with Visual Feedback
//
// Shows CPU activity on 7-segment display and LEDs
// - 7-segment: displays lower 4 bits of address (hex digit)
// - LEDs: show CPU state and address bits
// - Slow clock: 2 Hz for visibility
//

module cpu_debug (
    input  wire clk_25mhz,        // 25 MHz clock
    input  wire reset_button_n,   // Reset button (active-low)

    // 7-segment display (shows lower 4 bits of address)
    output wire seg_a,
    output wire seg_b,
    output wire seg_c,
    output wire seg_d,
    output wire seg_e,
    output wire seg_f,
    output wire seg_g,
    output wire seg_select,       // Digit select (single digit)

    // LEDs for debugging
    output wire [3:0] led         // Status LEDs
);

    // ========================================================================
    // Reset Controller
    // ========================================================================
    wire system_rst;

    reset_controller rst_ctrl (
        .clk(clk_25mhz),
        .reset_button_n(reset_button_n),
        .rst(system_rst)
    );

    // ========================================================================
    // Very Slow Clock Enable (2 Hz for visibility)
    // ========================================================================
    localparam SLOW_DIVIDER = 12_500_000;  // 2 Hz (0.5 second per cycle)
    reg [23:0] slow_counter = 0;
    reg cpu_clk_enable = 0;
    reg cpu_clk_enable_delayed = 0;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            slow_counter <= 0;
            cpu_clk_enable <= 0;
            cpu_clk_enable_delayed <= 0;
        end else begin
            cpu_clk_enable_delayed <= cpu_clk_enable;

            if (slow_counter >= SLOW_DIVIDER - 1) begin
                slow_counter <= 0;
                cpu_clk_enable <= 1;
            end else begin
                slow_counter <= slow_counter + 1;
                cpu_clk_enable <= 0;
            end
        end
    end

    // ========================================================================
    // Simple Test ROM (just NOPs and reset vector)
    // ========================================================================
    wire [15:0] cpu_addr;
    reg [7:0] rom_data;

    always @(*) begin
        case (cpu_addr)
            // Fill with NOPs (0xEA) - PC will increment through 0xE000+
            default: rom_data = 8'hEA;  // NOP
        endcase
    end

    // Register ROM output
    reg [7:0] rom_data_reg;
    always @(posedge clk_25mhz) begin
        rom_data_reg <= rom_data;
    end

    // ========================================================================
    // CPU Instance (minimal, ROM only)
    // ========================================================================
    wire [7:0] cpu_data_out;
    wire cpu_rw;  // 1=read, 0=write

    cpu cpu_inst (
        .clk(clk_25mhz),
        .reset(system_rst),
        .AB(cpu_addr),
        .DI(rom_data_reg),
        .DO(cpu_data_out),
        .WE(cpu_rw),
        .IRQ(1'b1),
        .NMI(1'b1),
        .RDY(1'b1 && cpu_clk_enable_delayed)
    );

    // ========================================================================
    // 7-Segment Display Driver
    // ========================================================================
    // Display lower 4 bits of address as hex digit
    wire [3:0] hex_digit = cpu_addr[3:0];

    // 7-segment decoder - format is GFEDCBA (bit 6 to bit 0)
    // Common anode display requires inverted outputs
    reg [6:0] segments;
    always @(*) begin
        case (hex_digit)
            4'h0: segments = 7'b0111111;  // 0
            4'h1: segments = 7'b0000110;  // 1
            4'h2: segments = 7'b1011011;  // 2
            4'h3: segments = 7'b1001111;  // 3
            4'h4: segments = 7'b1100110;  // 4
            4'h5: segments = 7'b1101101;  // 5
            4'h6: segments = 7'b1111101;  // 6
            4'h7: segments = 7'b0000111;  // 7
            4'h8: segments = 7'b1111111;  // 8
            4'h9: segments = 7'b1101111;  // 9
            4'hA: segments = 7'b1110111;  // A
            4'hB: segments = 7'b1111100;  // b
            4'hC: segments = 7'b0111001;  // C
            4'hD: segments = 7'b1011110;  // d
            4'hE: segments = 7'b1111001;  // E
            4'hF: segments = 7'b1110001;  // F
        endcase
    end

    // Assign segments with inversion for common anode display
    // Format: {seg_g, seg_f, seg_e, seg_d, seg_c, seg_b, seg_a}
    assign {seg_g, seg_f, seg_e, seg_d, seg_c, seg_b, seg_a} = ~segments;
    assign seg_select = 0;  // Always enable single digit

    // ========================================================================
    // LED Debug Indicators
    // ========================================================================
    assign led[0] = system_rst;          // Reset indicator
    assign led[1] = cpu_clk_enable;      // Clock pulse (2 Hz blink)
    assign led[2] = cpu_addr[4];         // Address bit 4
    assign led[3] = cpu_rw;              // Read/write indicator

endmodule
