//
// soc_uart_slow_test.v - Full SoC with Simple UART Test ROM
//
// Tests full soc_top design but with a simple ROM that sends
// characters slowly with explicit delays to verify UART works
//

module soc_uart_slow_test (
    // Clock and reset
    input  wire clk_25mhz,
    input  wire reset_button_n,

    // UART
    output wire uart_tx,

    // Debug LEDs
    output wire [3:0] led
);

    // Use full soc_top but we'll override the monitor ROM with our test ROM
    // Actually, easier to just instantiate components directly here

    // ========================================================================
    // Reset and Clock
    // ========================================================================
    wire system_rst;
    wire cpu_clk_enable;

    reset_controller rst_ctrl (
        .clk(clk_25mhz),
        .reset_button_n(reset_button_n),
        .rst(system_rst)
    );

    // Slow CPU: 10 KHz
    clock_divider #(
        .DIVIDE_RATIO(2500)
    ) clk_div (
        .clk(clk_25mhz),
        .rst(system_rst),
        .clk_enable(cpu_clk_enable)
    );

    // ========================================================================
    // CPU
    // ========================================================================
    wire [15:0] cpu_addr;
    wire [7:0] cpu_data_out;
    wire [7:0] cpu_data_in;
    wire cpu_we;
    reg [7:0] cpu_data_in_reg;

    // Register data path
    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            cpu_data_in_reg <= 8'hEA;
        end else if (cpu_clk_enable) begin
            cpu_data_in_reg <= cpu_data_in;
        end
    end

    cpu cpu_inst (
        .clk(clk_25mhz),
        .reset(system_rst),
        .AB(cpu_addr),
        .DI(cpu_data_in_reg),
        .DO(cpu_data_out),
        .WE(cpu_we),
        .IRQ(1'b1),
        .NMI(1'b1),
        .RDY(1'b1 && cpu_clk_enable)
    );

    // ========================================================================
    // Simple Test ROM
    // ========================================================================
    // Program: Send "OK\r\n" repeatedly with single-loop delays (127ms each)
    //
    // E000: A9 4F        LDA #'O'
    // E002: 8D 00 C0     STA $C000
    // E005: A2 FF        LDX #$FF    (delay ~127ms)
    // E007: CA           DEX
    // E008: D0 FD        BNE $E007
    //
    // E00A: A9 4B        LDA #'K'
    // E00C: 8D 00 C0     STA $C000
    // E00F: A2 FF        LDX #$FF
    // E011: CA           DEX
    // E012: D0 FD        BNE $E011
    //
    // E014: A9 0D        LDA #$0D    (CR)
    // E016: 8D 00 C0     STA $C000
    // E019: A2 FF        LDX #$FF
    // E01B: CA           DEX
    // E01C: D0 FD        BNE $E01B
    //
    // E01E: A9 0A        LDA #$0A    (LF)
    // E020: 8D 00 C0     STA $C000
    // E023: A2 FF        LDX #$FF
    // E025: CA           DEX
    // E026: D0 FD        BNE $E025
    //
    // E028: 4C 00 E0     JMP $E000

    reg [7:0] rom_data;
    always @(*) begin
        case (cpu_addr)
            // 'O'
            16'hE000: rom_data = 8'hA9;
            16'hE001: rom_data = 8'h4F;  // 'O'
            16'hE002: rom_data = 8'h8D;
            16'hE003: rom_data = 8'h00;
            16'hE004: rom_data = 8'hC0;
            16'hE005: rom_data = 8'hA2;  // LDX #$FF
            16'hE006: rom_data = 8'hFF;
            16'hE007: rom_data = 8'hCA;  // DEX
            16'hE008: rom_data = 8'hD0;  // BNE $E007
            16'hE009: rom_data = 8'hFD;

            // 'K'
            16'hE00A: rom_data = 8'hA9;
            16'hE00B: rom_data = 8'h4B;  // 'K'
            16'hE00C: rom_data = 8'h8D;
            16'hE00D: rom_data = 8'h00;
            16'hE00E: rom_data = 8'hC0;
            16'hE00F: rom_data = 8'hA2;  // LDX #$FF
            16'hE010: rom_data = 8'hFF;
            16'hE011: rom_data = 8'hCA;  // DEX
            16'hE012: rom_data = 8'hD0;  // BNE $E011
            16'hE013: rom_data = 8'hFD;

            // CR
            16'hE014: rom_data = 8'hA9;
            16'hE015: rom_data = 8'h0D;  // CR
            16'hE016: rom_data = 8'h8D;
            16'hE017: rom_data = 8'h00;
            16'hE018: rom_data = 8'hC0;
            16'hE019: rom_data = 8'hA2;  // LDX #$FF
            16'hE01A: rom_data = 8'hFF;
            16'hE01B: rom_data = 8'hCA;  // DEX
            16'hE01C: rom_data = 8'hD0;  // BNE $E01B
            16'hE01D: rom_data = 8'hFD;

            // LF
            16'hE01E: rom_data = 8'hA9;
            16'hE01F: rom_data = 8'h0A;  // LF
            16'hE020: rom_data = 8'h8D;
            16'hE021: rom_data = 8'h00;
            16'hE022: rom_data = 8'hC0;
            16'hE023: rom_data = 8'hA2;  // LDX #$FF
            16'hE024: rom_data = 8'hFF;
            16'hE025: rom_data = 8'hCA;  // DEX
            16'hE026: rom_data = 8'hD0;  // BNE $E025
            16'hE027: rom_data = 8'hFD;

            // Loop
            16'hE028: rom_data = 8'h4C;  // JMP $E000
            16'hE029: rom_data = 8'h00;
            16'hE02A: rom_data = 8'hE0;

            // Reset vector
            16'hFFFC: rom_data = 8'h00;
            16'hFFFD: rom_data = 8'hE0;

            default: rom_data = 8'hEA;  // NOP
        endcase
    end

    // ========================================================================
    // UART
    // ========================================================================
    wire uart_cs = (cpu_addr[15:8] == 8'hC0);
    wire [7:0] uart_data_out;

    uart #(
        .CLK_FREQ(25000000),
        .BAUD_RATE(9600)
    ) uart_inst (
        .clk(clk_25mhz),
        .rst(system_rst),
        .cs(uart_cs),
        .we(cpu_we && cpu_clk_enable),
        .addr(cpu_addr[7:0]),
        .data_in(cpu_data_out),
        .data_out(uart_data_out),
        .tx(uart_tx),
        .rx(1'b1)
    );

    // ========================================================================
    // Data Bus
    // ========================================================================
    assign cpu_data_in = uart_cs ? uart_data_out : rom_data;

    // ========================================================================
    // Debug LEDs
    // ========================================================================
    assign led[0] = system_rst;
    assign led[1] = cpu_clk_enable;
    assign led[2] = uart_cs;
    assign led[3] = cpu_we;

endmodule
