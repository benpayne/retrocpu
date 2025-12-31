//
// cpu_display_test.v - CPU Execution Test with 7-Segment Output
//
// Tests CPU by having it write a sequence of values to the display
// Program: Display 1, 2, 3, 4 in sequence with delays
//

module cpu_display_test (
    input  wire clk_25mhz,
    input  wire reset_button_n,

    // 7-segment display
    output wire seg_a,
    output wire seg_b,
    output wire seg_c,
    output wire seg_d,
    output wire seg_e,
    output wire seg_f,
    output wire seg_g,
    output wire seg_select,

    // LEDs for debugging
    output wire [3:0] led
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
    // Clock Enable (125 KHz CPU clock)
    // ========================================================================
    localparam CLOCK_DIVIDER = 200;
    reg [7:0] clk_counter = 0;
    reg cpu_clk_enable = 0;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            clk_counter <= 0;
            cpu_clk_enable <= 0;
        end else begin
            if (clk_counter >= CLOCK_DIVIDER - 1) begin
                clk_counter <= 0;
                cpu_clk_enable <= 1;
            end else begin
                clk_counter <= clk_counter + 1;
                cpu_clk_enable <= 0;
            end
        end
    end

    // ========================================================================
    // CPU Instance
    // ========================================================================
    wire [15:0] cpu_addr;
    wire [7:0] cpu_data_out;
    wire cpu_we;  // WE from CPU: 1=write, 0=read
    reg [7:0] cpu_data_in_reg;

    // Register data path to break timing path
    // CRITICAL: Only update when CPU is actually reading (cpu_clk_enable)
    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            cpu_data_in_reg <= 8'hEA;  // NOP during reset
        end else if (cpu_clk_enable) begin
            cpu_data_in_reg <= cpu_data_in_comb;
        end
    end

    cpu cpu_inst (
        .clk(clk_25mhz),
        .reset(system_rst),
        .AB(cpu_addr),
        .DI(cpu_data_in_reg),
        .DO(cpu_data_out),
        .WE(cpu_we),  // 1=write, 0=read
        .IRQ(1'b1),
        .NMI(1'b1),
        .RDY(1'b1 && cpu_clk_enable)
    );

    // ========================================================================
    // Simple Test ROM
    // ========================================================================
    // Program: Write 1, 2, 3, 4 to display port with VISIBLE delays (~0.5s each)
    //
    // Nested delay loop: outer * inner * cycles = 255 * 255 * 5 = 325,125 cycles
    // At 125 KHz CPU clock = 2.6 seconds per digit
    //
    // E000: A9 01        LDA #$01
    // E002: 8D 00 C0     STA $C000    (display port)
    // E005: A0 FF        LDY #$FF     (outer loop counter)
    // E007: A2 FF        LDX #$FF     (inner loop counter)
    // E009: CA           DEX
    // E00A: D0 FD        BNE $E009    (inner loop)
    // E00C: 88           DEY
    // E00D: D0 F8        BNE $E007    (outer loop)
    // E00F: A9 02        LDA #$02
    // E011: 8D 00 C0     STA $C000
    // E014: A0 FF        LDY #$FF
    // E016: A2 FF        LDX #$FF
    // E018: CA           DEX
    // E019: D0 FD        BNE $E018
    // E01B: 88           DEY
    // E01C: D0 F8        BNE $E016
    // E01E: A9 03        LDA #$03
    // E020: 8D 00 C0     STA $C000
    // E023: A0 FF        LDY #$FF
    // E025: A2 FF        LDX #$FF
    // E027: CA           DEX
    // E028: D0 FD        BNE $E027
    // E02A: 88           DEY
    // E02B: D0 F8        BNE $E025
    // E02D: A9 04        LDA #$04
    // E02F: 8D 00 C0     STA $C000
    // E032: 4C 00 E0     JMP $E000    (restart)

    reg [7:0] rom_data;
    always @(*) begin
        case (cpu_addr)
            // Display 1 with nested delay
            16'hE000: rom_data = 8'hA9;  // LDA #$01
            16'hE001: rom_data = 8'h01;
            16'hE002: rom_data = 8'h8D;  // STA $C000
            16'hE003: rom_data = 8'h00;
            16'hE004: rom_data = 8'hC0;
            16'hE005: rom_data = 8'hA0;  // LDY #$FF (outer loop)
            16'hE006: rom_data = 8'hFF;
            16'hE007: rom_data = 8'hA2;  // LDX #$FF (inner loop)
            16'hE008: rom_data = 8'hFF;
            16'hE009: rom_data = 8'hCA;  // DEX
            16'hE00A: rom_data = 8'hD0;  // BNE $E009
            16'hE00B: rom_data = 8'hFD;
            16'hE00C: rom_data = 8'h88;  // DEY
            16'hE00D: rom_data = 8'hD0;  // BNE $E007
            16'hE00E: rom_data = 8'hF8;

            // Display 2 with nested delay
            16'hE00F: rom_data = 8'hA9;  // LDA #$02
            16'hE010: rom_data = 8'h02;
            16'hE011: rom_data = 8'h8D;  // STA $C000
            16'hE012: rom_data = 8'h00;
            16'hE013: rom_data = 8'hC0;
            16'hE014: rom_data = 8'hA0;  // LDY #$FF
            16'hE015: rom_data = 8'hFF;
            16'hE016: rom_data = 8'hA2;  // LDX #$FF
            16'hE017: rom_data = 8'hFF;
            16'hE018: rom_data = 8'hCA;  // DEX
            16'hE019: rom_data = 8'hD0;  // BNE $E018
            16'hE01A: rom_data = 8'hFD;
            16'hE01B: rom_data = 8'h88;  // DEY
            16'hE01C: rom_data = 8'hD0;  // BNE $E016
            16'hE01D: rom_data = 8'hF8;

            // Display 3 with nested delay
            16'hE01E: rom_data = 8'hA9;  // LDA #$03
            16'hE01F: rom_data = 8'h03;
            16'hE020: rom_data = 8'h8D;  // STA $C000
            16'hE021: rom_data = 8'h00;
            16'hE022: rom_data = 8'hC0;
            16'hE023: rom_data = 8'hA0;  // LDY #$FF
            16'hE024: rom_data = 8'hFF;
            16'hE025: rom_data = 8'hA2;  // LDX #$FF
            16'hE026: rom_data = 8'hFF;
            16'hE027: rom_data = 8'hCA;  // DEX
            16'hE028: rom_data = 8'hD0;  // BNE $E027
            16'hE029: rom_data = 8'hFD;
            16'hE02A: rom_data = 8'h88;  // DEY
            16'hE02B: rom_data = 8'hD0;  // BNE $E025
            16'hE02C: rom_data = 8'hF8;

            // Display 4 with nested delay
            16'hE02D: rom_data = 8'hA9;  // LDA #$04
            16'hE02E: rom_data = 8'h04;
            16'hE02F: rom_data = 8'h8D;  // STA $C000
            16'hE030: rom_data = 8'h00;
            16'hE031: rom_data = 8'hC0;
            16'hE032: rom_data = 8'h4C;  // JMP $E000
            16'hE033: rom_data = 8'h00;
            16'hE034: rom_data = 8'hE0;

            // Reset vectors
            16'hFFFC: rom_data = 8'h00;  // RESET vector = $E000
            16'hFFFD: rom_data = 8'hE0;
            16'hFFFE: rom_data = 8'h00;
            16'hFFFF: rom_data = 8'hE0;

            default: rom_data = 8'hEA;   // NOP everywhere else
        endcase
    end

    wire [7:0] cpu_data_in_comb = rom_data;

    // ========================================================================
    // Display Port ($C000) - captures CPU writes
    // ========================================================================
    reg [3:0] display_value;
    wire display_cs = (cpu_addr == 16'hC000);

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            display_value <= 4'h0;
        end else if (display_cs && cpu_we && cpu_clk_enable) begin  // cpu_we=1 means WRITE
            display_value <= cpu_data_out[3:0];
        end
    end

    // ========================================================================
    // 7-Segment Display
    // ========================================================================
    reg [6:0] segments;
    always @(*) begin
        case (display_value)
            4'h0: segments = 7'b0111111;
            4'h1: segments = 7'b0000110;
            4'h2: segments = 7'b1011011;
            4'h3: segments = 7'b1001111;
            4'h4: segments = 7'b1100110;
            4'h5: segments = 7'b1101101;
            4'h6: segments = 7'b1111101;
            4'h7: segments = 7'b0000111;
            4'h8: segments = 7'b1111111;
            4'h9: segments = 7'b1101111;
            4'hA: segments = 7'b1110111;
            4'hB: segments = 7'b1111100;
            4'hC: segments = 7'b0111001;
            4'hD: segments = 7'b1011110;
            4'hE: segments = 7'b1111001;
            4'hF: segments = 7'b1110001;
        endcase
    end

    assign {seg_g, seg_f, seg_e, seg_d, seg_c, seg_b, seg_a} = ~segments;
    assign seg_select = 1'b0;

    // ========================================================================
    // LED Debug (better visibility)
    // ========================================================================
    reg led_write_pulse;
    reg [23:0] led_timer;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            led_write_pulse <= 0;
            led_timer <= 0;
        end else begin
            // Stretch write pulse so it's visible
            if (display_cs && cpu_we && cpu_clk_enable) begin
                led_write_pulse <= 1;
                led_timer <= 0;
            end else if (led_timer < 24'd2_500_000) begin  // Hold for 100ms
                led_timer <= led_timer + 1;
            end else begin
                led_write_pulse <= 0;
            end
        end
    end

    assign led[0] = ~system_rst;           // ON when running
    assign led[1] = display_value[0];      // Show display value in binary
    assign led[2] = display_value[1];
    assign led[3] = led_write_pulse;       // Pulse on each CPU write to display

endmodule
