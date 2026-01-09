//
// soc_top.v - Top-Level System-on-Chip Integration
//
// Integrates all system components for 6502 microcomputer
//
// Author: RetroCPU Project
// License: MIT
//
// Components:
// - M65C02 CPU core (replaces Arlet 6502 - fixes zero page bug)
// - 32KB RAM ($0000-$7FFF)
// - 16KB BASIC ROM ($8000-$BFFF)
// - 8KB Monitor ROM ($E000-$FFFF)
// - UART at $C000-$C0FF
// - Reset controller
// - No clock divider needed (M65C02 has built-in microcycle controller)
//

module soc_top (
    // Clock and reset
    input  wire clk_25mhz,         // P3: 25 MHz system clock
    input  wire reset_button_n,    // T1: Reset button (active-low, FIRE 2)

    // UART
    output wire uart_tx,           // J17: UART TX to USB bridge
    input  wire uart_rx,           // K17: UART RX from USB bridge

    // LCD (HD44780 4-bit mode)
    output wire [3:0] lcd_data,    // E5,F4,F5,E6: LCD D4-D7
    output wire lcd_rs,            // G5: LCD Register Select
    output wire lcd_rw,            // D16: LCD Read/Write
    output wire lcd_e,             // D18: LCD Enable

    // PS/2 Keyboard
    input  wire ps2_clk,           // PS/2 keyboard clock
    input  wire ps2_data,          // PS/2 keyboard data

    // DVI/HDMI Output (differential TMDS pairs)
    // Note: Only gpdi_dp is declared - LVCMOS33D mode automatically generates differential negative signals
    output wire [3:0] gpdi_dp,     // TMDS data positive (3=clk, 2=red, 1=green, 0=blue)

    // Debug LEDs
    output wire [3:0] led          // Status LEDs
);

    // ========================================================================
    // Reset and Clock Generation
    // ========================================================================

    wire system_rst;

    reset_controller rst_ctrl (
        .clk(clk_25mhz),
        .reset_button_n(reset_button_n),
        .rst(system_rst)
    );

    // M65C02 has built-in microcycle controller - no external clock divider needed
    // The core runs at 25 MHz with 4-clock microcycles (6.25 MHz microcycle rate)

    // OLD: Arlet required external clock divider
    // wire cpu_clk_enable;
    // reg cpu_clk_enable_delayed;
    // clock_divider #(
    //     .DIVIDE_RATIO(25)  // 25 MHz / 25 = 1 MHz CPU clock
    // ) clk_div (
    //     .clk(clk_25mhz),
    //     .rst(system_rst),
    //     .clk_enable(cpu_clk_enable)
    // );

    // ========================================================================
    // CPU Interface Signals
    // ========================================================================

    wire [15:0] cpu_addr;      // Address bus from CPU (M65C02.AO)
    wire [7:0] cpu_data_out;   // Data output from CPU (M65C02.DO)
    wire [7:0] cpu_data_in;    // Data input to CPU (M65C02.DI)
    wire [1:0] cpu_io_op;      // I/O operation type (M65C02.IO_Op)
    wire [2:0] cpu_mc;         // Microcycle state (M65C02.MC)

    // M65C02 IO_Op encoding:
    // 2'b00 = NO_OP   (no memory operation)
    // 2'b01 = WRITE   (memory write)
    // 2'b10 = READ    (memory read)
    // 2'b11 = FETCH   (instruction fetch)

    // M65C02 MC state sequence (normal operation, Wait=0): 4 → 6 → 7 → 5 → 4 → ...
    // MC=6: Cycle 1 (Address setup)
    // MC=7: Cycle 2 (Control asserted, memory access begins)
    // MC=5: Cycle 3 (Memory operation completes)
    // MC=4: Cycle 4 (Data capture at start of cycle)

    // OLD: Arlet signals (no longer used)
    // wire cpu_we;           // WE from CPU: 1 = write, 0 = read
    // wire cpu_sync;
    // wire cpu_irq_n = 1'b1; // No interrupts in MVP
    // wire cpu_nmi_n = 1'b1; // No NMI in MVP
    // wire cpu_rdy = 1'b1;   // Always ready (no wait states)

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
    wire gpu_cs;

    address_decoder addr_dec (
        .addr(cpu_addr),
        .ram_cs(ram_cs),
        .rom_basic_cs(rom_basic_cs),
        .rom_monitor_cs(rom_monitor_cs),
        .io_cs(io_cs),
        .uart_cs(uart_cs),
        .gpu_cs(gpu_cs),
        .lcd_cs(lcd_cs),
        .ps2_cs(ps2_cs)
    );

    // ========================================================================
    // Memory Modules
    // ========================================================================

    wire [7:0] ram_data_out;

    // M65C02 write enable: assert when IO_Op=WRITE (01) and MC=7 (Cycle 2)
    // Write occurs at MC=7 when control signals are asserted
    wire mem_we = (cpu_io_op == 2'b01) && (cpu_mc == 3'b111);

    ram #(
        .ADDR_WIDTH(15),  // 32KB
        .DATA_WIDTH(8)
    ) main_ram (
        .clk(clk_25mhz),
        .rst(system_rst),
        .we(ram_cs && mem_we),  // Write when CPU executes write operation at MC=3
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
        .we(uart_cs && mem_we),  // Write when CPU executes write operation at MC=7
        .addr(cpu_addr[7:0]),
        .data_in(cpu_data_out),
        .data_out(uart_data_out),
        .tx(uart_tx),
        .rx(uart_rx)  // Connected to UART RX pin
    );

    // ========================================================================
    // LCD Controller (HD44780 4-bit mode)
    // ========================================================================

    wire [7:0] lcd_data_out;

    // M65C02: Read enable at MC=7 (when control signals are asserted)
    wire lcd_rd = (cpu_io_op == 2'b10) && (cpu_mc == 3'b111);

    lcd_controller lcd_inst (
        .clk(clk_25mhz),
        .rst(system_rst),
        .cs(lcd_cs),
        .we(lcd_cs && mem_we),  // Write when CPU executes write operation at MC=7
        .rd(lcd_cs && lcd_rd),  // Read at MC=7
        .addr(cpu_addr[7:0]),
        .data_in(cpu_data_out),
        .data_out(lcd_data_out),
        .lcd_data(lcd_data),
        .lcd_rs(lcd_rs),
        .lcd_rw(lcd_rw),
        .lcd_e(lcd_e)
    );

    // ========================================================================
    // PS/2 Keyboard Controller
    // ========================================================================

    wire [7:0] ps2_data_out;
    wire ps2_rd = (cpu_io_op == 2'b10) && (cpu_mc == 3'b111);

    ps2_wrapper #(
        .CLK_FREQ_HZ(25000000)  // 25 MHz system clock
    ) ps2_inst (
        .clk(clk_25mhz),
        .reset(system_rst),
        .ps2_clk(ps2_clk),
        .ps2_data(ps2_data),
        .cs(ps2_cs),
        .rd(ps2_cs && ps2_rd),  // Read at MC=7
        .addr(cpu_addr[0]),     // A0 selects DATA (0) or STATUS (1)
        .data_out(ps2_data_out),
        .irq(),                 // Not connected yet (no interrupt support)
        .debug_valid(),         // Could connect to LED
        .debug_fifo_empty(),
        .debug_count(),
        .debug_ps2_clk_deb(),
        .debug_ps2_data_deb()
    );

    // ========================================================================
    // GPU Clock Generation (PLL)
    // ========================================================================

    wire [3:0] gpu_clocks;
    wire gpu_pll_locked;

    ecp5_pll #(
        .in_hz(25_000_000),      // 25 MHz input
        .out0_hz(125_000_000),   // TMDS clock (5x pixel clock for DDR)
        .out1_hz(25_000_000)     // Pixel clock
    ) gpu_pll_inst (
        .clk_i(clk_25mhz),
        .clk_o(gpu_clocks),
        .locked(gpu_pll_locked),
        // Tie off unused ports
        .reset(1'b0),
        .standby(1'b0),
        .phasesel(2'b00),
        .phasedir(1'b0),
        .phasestep(1'b0),
        .phaseloadreg(1'b0)
    );

    wire clk_tmds  = gpu_clocks[0];  // 125 MHz
    wire clk_pixel = gpu_clocks[1];  // 25 MHz

    // ========================================================================
    // GPU (DVI Character Display)
    // ========================================================================

    wire [7:0] gpu_data_out;
    wire gpu_rd = (cpu_io_op == 2'b10) && (cpu_mc == 3'b111);

    // Reset signal for GPU (active-low)
    wire gpu_rst_n = ~system_rst & gpu_pll_locked;

    // TMDS parallel data from GPU (2-bit DDR for each channel)
    wire [1:0] tmds_clk_parallel;
    wire [1:0] tmds_red_parallel;
    wire [1:0] tmds_green_parallel;
    wire [1:0] tmds_blue_parallel;

    // GPU debug signals for LEDs
    wire gpu_debug_display_mode;
    wire gpu_debug_gfx_gpu_cs;
    wire gpu_debug_char_gpu_cs;
    wire gpu_debug_vsync;

    gpu_top gpu_inst (
        // Clock and reset
        .clk_cpu(clk_25mhz),              // CPU clock domain
        .clk_pixel(clk_pixel),            // 25 MHz pixel clock
        .clk_tmds(clk_tmds),              // 125 MHz TMDS clock
        .rst_n(gpu_rst_n),                // Active-low reset (wait for PLL lock)

        // CPU bus interface
        .addr(cpu_addr[7:0]),             // Register address (0xC0xx-0xC1xx)
        .data_in(cpu_data_out),           // Data from CPU
        .data_out(gpu_data_out),          // Data to CPU
        .we(gpu_cs && mem_we),            // Write enable at MC=7
        .re(gpu_cs && gpu_rd),            // Read enable at MC=7

        // TMDS parallel output (2-bit DDR for each channel)
        .tmds_clk_out(tmds_clk_parallel),
        .tmds_red_out(tmds_red_parallel),
        .tmds_green_out(tmds_green_parallel),
        .tmds_blue_out(tmds_blue_parallel),

        // Debug outputs
        .debug_display_mode(gpu_debug_display_mode),
        .debug_gfx_gpu_cs(gpu_debug_gfx_gpu_cs),
        .debug_char_gpu_cs(gpu_debug_char_gpu_cs),
        .debug_vsync(gpu_debug_vsync)
    );

    // ========================================================================
    // DDR Output Primitives - TMDS Serialization
    // ========================================================================
    // ECP5 ODDRX1F primitives must be at the top level connecting directly
    // to output pins (requirement of ECP5 architecture)

    // TMDS Clock output
    ODDRX1F ddr_clk (
        .D0(tmds_clk_parallel[0]),
        .D1(tmds_clk_parallel[1]),
        .Q(gpdi_dp[3]),
        .SCLK(clk_tmds),
        .RST(1'b0)
    );

    // TMDS Red output
    ODDRX1F ddr_red (
        .D0(tmds_red_parallel[0]),
        .D1(tmds_red_parallel[1]),
        .Q(gpdi_dp[2]),
        .SCLK(clk_tmds),
        .RST(1'b0)
    );

    // TMDS Green output
    ODDRX1F ddr_green (
        .D0(tmds_green_parallel[0]),
        .D1(tmds_green_parallel[1]),
        .Q(gpdi_dp[1]),
        .SCLK(clk_tmds),
        .RST(1'b0)
    );

    // TMDS Blue output
    ODDRX1F ddr_blue (
        .D0(tmds_blue_parallel[0]),
        .D1(tmds_blue_parallel[1]),
        .Q(gpdi_dp[0]),
        .SCLK(clk_tmds),
        .RST(1'b0)
    );

    // Note: gpdi_dn outputs are automatically generated by LVCMOS33D IO type
    // (differential mode in the LPF file - no explicit assignment needed)

    // ========================================================================
    // Data Bus Multiplexer (Registered)
    // ========================================================================
    // Register the data bus to break combinational loops.
    // M65C02: Capture data when MC=0 (CYCLE_END) on rising edge

    reg [7:0] cpu_data_in_mux;
    reg [7:0] cpu_data_in_reg;

    always @(*) begin
        case (1'b1)
            ram_cs:         cpu_data_in_mux = ram_data_out;
            rom_basic_cs:   cpu_data_in_mux = rom_basic_data_out;
            rom_monitor_cs: cpu_data_in_mux = rom_monitor_data_out;
            uart_cs:        cpu_data_in_mux = uart_data_out;
            lcd_cs:         cpu_data_in_mux = lcd_data_out;
            ps2_cs:         cpu_data_in_mux = ps2_data_out;
            gpu_cs:         cpu_data_in_mux = gpu_data_out;
            default:        cpu_data_in_mux = 8'hFF;  // Unmapped reads return $FF
        endcase
    end

    // M65C02: Register data input at end of cycle 3 (MC=5)
    // Data must be captured while address is still stable (before cycle 4)
    // Memory outputs are valid at MC=5, and address hasn't changed yet
    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            cpu_data_in_reg <= 8'hEA;  // NOP during reset
        end else if (cpu_mc == 3'b101) begin  // Capture at MC=5 (Cycle 3 end)
            cpu_data_in_reg <= cpu_data_in_mux;
        end
    end

    assign cpu_data_in = cpu_data_in_reg;

    // ========================================================================
    // CPU Instance - M65C02 Core
    // ========================================================================

    M65C02_Core #(
        .pStkPtr_Rst(8'hFF),                        // Standard 6502 stack init
        .pInt_Hndlr(0),                             // Default interrupt handler
        .pM65C02_uPgm("M65C02_uPgm_V3a.coe"),       // Microprogram ROM V3a
        .pM65C02_IDec("M65C02_Decoder_ROM.coe")     // Decoder ROM
    ) cpu_inst (
        // Clock and reset
        .Clk(clk_25mhz),                            // 25 MHz system clock
        .Rst(system_rst),                           // Active high reset

        // Address and data buses
        .AO(cpu_addr),                              // Address output [15:0]
        .DI(cpu_data_in),                           // Data input [7:0]
        .DO(cpu_data_out),                          // Data output [7:0]

        // Control signals
        .IO_Op(cpu_io_op),                          // I/O operation type [1:0]
        .MC(cpu_mc),                                // Microcycle state [2:0]

        // Memory control (no wait states for internal RAM)
        .Wait(1'b0),                                // No wait states needed

        // Interrupts (disabled in MVP)
        .Int(1'b0),                                 // Interrupt request (inactive)
        .Vector(16'hFFFC),                          // Reset vector address
        .xIRQ(1'b1),                                // External IRQ (inactive, active-low)

        // Unconnected outputs (for future use/debugging)
        .MemTyp(),                                  // Memory type classification
        .Done(),                                    // Instruction complete
        .SC(),                                      // Single cycle instruction
        .Mode(),                                    // Instruction type
        .RMW(),                                     // Read-modify-write flag
        .Rdy(),                                     // Internal ready signal
        .IntSvc(),                                  // Interrupt service active
        .ISR(),                                     // In interrupt service routine
        .A(),                                       // Accumulator (debug)
        .X(),                                       // X register (debug)
        .Y(),                                       // Y register (debug)
        .S(),                                       // Stack pointer (debug)
        .P(),                                       // Processor status (debug)
        .PC(),                                      // Program counter (debug)
        .IR(),                                      // Instruction register (debug)
        .OP1(),                                     // Operand 1 (debug)
        .OP2(),                                     // Operand 2 (debug)
        .IRQ_Msk()                                  // Interrupt mask bit (debug)
    );

    // OLD: Arlet 6502 CPU (replaced by M65C02)
    // cpu cpu_inst (
    //     .clk(clk_25mhz),
    //     .reset(system_rst),
    //     .AB(cpu_addr),
    //     .DI(cpu_data_in),
    //     .DO(cpu_data_out),
    //     .WE(cpu_we),  // 1=write, 0=read
    //     .IRQ(cpu_irq_n),
    //     .NMI(cpu_nmi_n),
    //     .RDY(cpu_rdy && cpu_clk_enable)
    // );

    // ========================================================================
    // Debug LEDs - GPU Status Indicators
    // ========================================================================
    // LED[0]: Display mode (0=character, 1=graphics)
    // LED[1]: Graphics GPU chip select active (accessing $C100-$C10F)
    // LED[2]: Character GPU chip select active (accessing $C010-$C01F)
    // LED[3]: VSync signal (blinks at 60Hz when display is active)

    assign led[0] = gpu_debug_display_mode;   // 1=Graphics mode, 0=Character mode
    assign led[1] = gpu_debug_gfx_gpu_cs;     // Graphics GPU accessed
    assign led[2] = gpu_debug_char_gpu_cs;    // Character GPU accessed
    assign led[3] = gpu_debug_vsync;          // VSync pulse (60Hz blink)

endmodule
