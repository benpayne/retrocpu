//
// cpu_uart_test.v - CPU + UART Integration Test
//
// Tests CPU executing from ROM and writing to UART
// Simple program: Repeatedly send 'X' character to UART
// No stack, no JSR, just load/store in a loop
//

module cpu_uart_test (
    input  wire clk_25mhz,        // 25 MHz clock
    input  wire reset_button_n,   // Reset button (active-low)

    // UART
    output wire uart_tx,

    // 7-segment display (shows lower 4 bits of address)
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
    // Clock Enable (10 KHz CPU clock from 25 MHz - slow enough for UART visibility)
    // ========================================================================
    localparam CLOCK_DIVIDER = 2500;  // 25MHz / 2500 = 10 KHz
    reg [11:0] clk_counter = 0;
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
    reg [7:0] cpu_data_in_reg;  // Registered data input

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
    // Program: Send 'X' to UART with delay (wait for UART ready)
    // E000: A9 58        LDA #$58   ('X')
    // E002: 8D 00 C0     STA $C000  (UART data)
    // E005: A2 FF        LDX #$FF   (delay - give UART time)
    // E007: CA           DEX
    // E008: D0 FD        BNE $E007
    // E00A: 4C 00 E0     JMP $E000  (loop)
    //
    // Reset vectors:
    // FFFC: 00 E0        RESET = $E000
    //

    reg [7:0] rom_data;
    always @(*) begin
        case (cpu_addr)
            // Program at $E000
            16'hE000: rom_data = 8'hA9;  // LDA #$58
            16'hE001: rom_data = 8'h58;  // 'X'
            16'hE002: rom_data = 8'h8D;  // STA $C000
            16'hE003: rom_data = 8'h00;
            16'hE004: rom_data = 8'hC0;
            16'hE005: rom_data = 8'hA2;  // LDX #$FF (delay)
            16'hE006: rom_data = 8'hFF;
            16'hE007: rom_data = 8'hCA;  // DEX
            16'hE008: rom_data = 8'hD0;  // BNE $E007
            16'hE009: rom_data = 8'hFD;
            16'hE00A: rom_data = 8'h4C;  // JMP $E000
            16'hE00B: rom_data = 8'h00;
            16'hE00C: rom_data = 8'hE0;

            // Reset vectors
            16'hFFFC: rom_data = 8'h00;  // RESET vector = $E000
            16'hFFFD: rom_data = 8'hE0;
            16'hFFFE: rom_data = 8'h00;  // IRQ vector (not used)
            16'hFFFF: rom_data = 8'hE0;

            default: rom_data = 8'hEA;   // NOP everywhere else
        endcase
    end

    // ========================================================================
    // UART Instance (9600 baud transmit only)
    // ========================================================================
    wire uart_cs = (cpu_addr[15:1] == 15'b110000000000000); // $C000-$C001
    wire [7:0] uart_data_out;

    uart #(
        .CLK_FREQ(25_000_000),
        .BAUD_RATE(9600)
    ) uart_inst (
        .clk(clk_25mhz),
        .rst(system_rst),
        .addr(cpu_addr[0]),
        .data_in(cpu_data_out),
        .data_out(uart_data_out),
        .we(cpu_we && cpu_clk_enable),  // cpu_we=1 means WRITE
        .cs(uart_cs),
        .tx(uart_tx),
        .rx(1'b1)
    );

    // ========================================================================
    // Data Bus Multiplexer (combinational, will be registered before CPU)
    // ========================================================================
    wire [7:0] cpu_data_in_comb = uart_cs ? uart_data_out : rom_data;

    // ========================================================================
    // 7-Segment Display (shows address lower 4 bits)
    // ========================================================================
    wire [3:0] hex_digit = cpu_addr[3:0];

    reg [6:0] segments;
    always @(*) begin
        case (hex_digit)
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
    assign seg_select = 0;

    // ========================================================================
    // LED Debug Indicators
    // ========================================================================
    assign led[0] = system_rst;
    assign led[1] = cpu_clk_enable;
    assign led[2] = cpu_addr[15];       // High address bit (ROM vs RAM)
    assign led[3] = cpu_we;             // Write enable (1=write)

endmodule
