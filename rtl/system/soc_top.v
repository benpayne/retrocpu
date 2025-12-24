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
    wire uart_rx_ready_debug;

    uart #(
        .CLK_FREQ(25000000),
        .BAUD_RATE(115200),
        .HOLDOFF_CYCLES(2500)  // ~100us @ 25MHz (1.2 char times @ 115200 baud)
    ) uart_inst (
        .clk(clk_25mhz),
        .rst(system_rst),
        .cs(uart_cs),
        .we(uart_cs && mem_we),  // Write when CPU executes write operation at MC=3
        .addr(cpu_addr[7:0]),
        .data_in(cpu_data_out),
        .data_out(uart_data_out),
        .tx(uart_tx),
        .rx(uart_rx),  // Connected to UART RX pin
        .rx_ready_debug(uart_rx_ready_debug)
    );

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
    // Debug LEDs
    // ========================================================================

    // LED indicators for debugging
    // Debug: Capture write attempts to address $0010
    reg [7:0] debug_addr_low;
    reg debug_write_seen;
    reg [7:0] debug_data_written;
    reg [7:0] debug_data_read;

    always @(posedge clk_25mhz) begin
        if (system_rst) begin
            debug_addr_low <= 8'h00;
            debug_write_seen <= 1'b0;
            debug_data_written <= 8'h00;
            debug_data_read <= 8'h00;
        end else if (cpu_addr == 16'h0010 && ram_cs && mem_we) begin
            debug_addr_low <= cpu_addr[7:0];
            debug_write_seen <= 1'b1;
            debug_data_written <= cpu_data_out;
        end else if (cpu_addr == 16'h0010 && ram_cs && (cpu_io_op == 2'b10 || cpu_io_op == 2'b11)) begin
            debug_data_read <= cpu_data_in_mux;
        end
    end

    assign led[0] = debug_write_seen;         // Saw write to $0010
    assign led[1] = (debug_data_written != 8'h00);  // Data written was non-zero
    assign led[2] = (debug_data_read == debug_data_written);  // Read matches write
    assign led[3] = mem_we;                    // Current memory write enable

endmodule
