//
// soc_top.v - Top-Level System-on-Chip Integration
//
// Integrates all system components for 6502 microcomputer
//
// Author: RetroCPU Project
// License: MIT
//
// Components:
// - Arlet 6502 CPU core
// - 32KB RAM ($0000-$7FFF)
// - 16KB BASIC ROM ($8000-$BFFF)
// - 8KB Monitor ROM ($E000-$FFFF)
// - UART at $C000-$C0FF
// - Clock divider (25 MHz → 1 MHz)
// - Reset controller
//

module soc_top (
    // Clock and reset
    input  wire clk_25mhz,         // P3: 25 MHz system clock
    input  wire reset_button_n,    // T1: Reset button (active-low, FIRE 2)

    // UART
    output wire uart_tx,           // J17: UART TX to USB bridge

    // Debug LEDs
    output wire [3:0] led          // Status LEDs
);

    // ========================================================================
    // Reset and Clock Generation
    // ========================================================================

    wire system_rst;
    wire cpu_clk_enable;

    reset_controller rst_ctrl (
        .clk(clk_25mhz),
        .reset_button_n(reset_button_n),
        .rst(system_rst)
    );

    clock_divider clk_div (
        .clk(clk_25mhz),
        .rst(system_rst),
        .clk_enable(cpu_clk_enable)
    );

    // ========================================================================
    // CPU Interface Signals
    // ========================================================================

    wire [15:0] cpu_addr;
    wire [7:0] cpu_data_out;
    wire [7:0] cpu_data_in;
    wire cpu_rw;           // 1 = read, 0 = write
    wire cpu_sync;
    wire cpu_irq_n = 1'b1; // No interrupts in MVP
    wire cpu_nmi_n = 1'b1; // No NMI in MVP
    wire cpu_rdy = 1'b1;   // Always ready (no wait states)

    // ========================================================================
    // Address Decoder
    // ========================================================================

    wire ram_cs;
    wire rom_basic_cs;
    wire rom_monitor_cs;
    wire io_cs;
    wire uart_cs;
    wire lcd_cs;
    wire ps2_cs;

    address_decoder addr_dec (
        .addr(cpu_addr),
        .ram_cs(ram_cs),
        .rom_basic_cs(rom_basic_cs),
        .rom_monitor_cs(rom_monitor_cs),
        .io_cs(io_cs),
        .uart_cs(uart_cs),
        .lcd_cs(lcd_cs),
        .ps2_cs(ps2_cs)
    );

    // ========================================================================
    // Memory Modules
    // ========================================================================

    wire [7:0] ram_data_out;

    ram #(
        .ADDR_WIDTH(15),  // 32KB
        .DATA_WIDTH(8)
    ) main_ram (
        .clk(clk_25mhz),
        .rst(system_rst),
        .we(ram_cs && !cpu_rw && cpu_clk_enable),
        .addr(cpu_addr[14:0]),
        .data_in(cpu_data_out),
        .data_out(ram_data_out)
    );

    wire [7:0] rom_basic_data_out;

    rom_basic #(
        .ADDR_WIDTH(14),  // 16KB
        .DATA_WIDTH(8),
        .HEX_FILE("../firmware/basic/basic_rom.hex")
    ) basic_rom (
        .clk(clk_25mhz),
        .addr(cpu_addr[13:0]),
        .data_out(rom_basic_data_out)
    );

    wire [7:0] rom_monitor_data_out;

    rom_monitor #(
        .ADDR_WIDTH(13),  // 8KB
        .DATA_WIDTH(8),
        .HEX_FILE("../firmware/monitor/monitor.hex")
    ) monitor_rom (
        .clk(clk_25mhz),
        .addr(cpu_addr[12:0]),
        .data_out(rom_monitor_data_out)
    );

    // ========================================================================
    // UART
    // ========================================================================

    wire [7:0] uart_data_out;

    uart #(
        .CLK_FREQ(25000000),
        .BAUD_RATE(9600)
    ) uart_inst (
        .clk(clk_25mhz),
        .rst(system_rst),
        .cs(uart_cs),
        .we(!cpu_rw && cpu_clk_enable),
        .addr(cpu_addr[7:0]),
        .data_in(cpu_data_out),
        .data_out(uart_data_out),
        .tx(uart_tx),
        .rx(1'b1)  // Not connected yet
    );

    // ========================================================================
    // Data Bus Multiplexer (Registered to break combinational loops)
    // ========================================================================

    reg [7:0] cpu_data_in_mux;
    reg [7:0] cpu_data_in_reg;

    always @(*) begin
        case (1'b1)
            ram_cs:         cpu_data_in_mux = ram_data_out;
            rom_basic_cs:   cpu_data_in_mux = rom_basic_data_out;
            rom_monitor_cs: cpu_data_in_mux = rom_monitor_data_out;
            uart_cs:        cpu_data_in_mux = uart_data_out;
            default:        cpu_data_in_mux = 8'hFF;  // Unmapped reads return $FF
        endcase
    end

    // Register the data bus to break the combinational loop
    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            cpu_data_in_reg <= 8'h00;
        end else begin
            cpu_data_in_reg <= cpu_data_in_mux;
        end
    end

    assign cpu_data_in = cpu_data_in_reg;

    // ========================================================================
    // CPU Instance
    // ========================================================================

    cpu cpu_inst (
        .clk(clk_25mhz),
        .reset(system_rst),
        .AB(cpu_addr),
        .DI(cpu_data_in),
        .DO(cpu_data_out),
        .WE(cpu_rw),
        .IRQ(cpu_irq_n),
        .NMI(cpu_nmi_n),
        .RDY(cpu_rdy && cpu_clk_enable)  // Gate CPU with clock enable
    );

    // ========================================================================
    // Debug LEDs
    // ========================================================================

    // LED indicators for debugging
    assign led[0] = system_rst;        // LED on when in reset
    assign led[1] = cpu_clk_enable;    // Blink at CPU clock rate
    assign led[2] = uart_cs;           // On when accessing UART
    assign led[3] = cpu_rw;            // Read/write indicator

endmodule
