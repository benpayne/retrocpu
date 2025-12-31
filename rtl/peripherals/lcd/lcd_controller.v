// ============================================================================
// LCD Controller Top-Level Module
// ============================================================================
//
// Integrates LCD timing and initialization FSM to provide a complete
// memory-mapped LCD interface for the CPU.
//
// Register Map:
// $C100 (addr=0x00): Data register (write character ASCII)
// $C101 (addr=0x01): Command register (write HD44780 command)
// $C102 (addr=0x02): Status register (read busy flag in bit 0)
//
// Operation:
// 1. On reset, automatically initializes LCD
// 2. Once init_done, CPU can write to registers
// 3. Each write triggers two nibble transfers (high, then low)
// 4. Busy flag prevents writes while LCD is processing
//
// ============================================================================

module lcd_controller (
    input wire clk,                    // 25 MHz system clock
    input wire rst,                    // Active high reset

    // CPU interface
    input wire cs,                     // Chip select (active high)
    input wire we,                     // Write enable (1=write, 0=read)
    input wire rd,                     // Read enable (for output capture at MC=7)
    input wire [7:0] addr,             // Register address (0x00-0x02)
    input wire [7:0] data_in,          // Data from CPU
    output reg [7:0] data_out,         // Data to CPU (registered at read strobe)

    // LCD interface (4-bit mode)
    output wire [3:0] lcd_data,        // LCD D4-D7 pins
    output wire lcd_rs,                // LCD RS pin
    output wire lcd_rw,                // LCD RW pin (tied low for write-only)
    output wire lcd_e                  // LCD Enable pin
);

    // Tie RW low for write-only operation
    assign lcd_rw = 1'b0;

    // ========================================================================
    // Instantiate sub-modules
    // ========================================================================

    // Timing generator
    wire timing_start;
    wire [3:0] timing_nibble;
    wire timing_rs;
    wire timing_busy;
    wire timing_done;

    lcd_timing timing_inst (
        .clk(clk),
        .rst(rst),
        .start(timing_start),
        .data_nibble(timing_nibble),
        .rs(timing_rs),
        .busy(timing_busy),
        .done(timing_done),
        .lcd_data(lcd_data),
        .lcd_rs(lcd_rs),
        .lcd_e(lcd_e)
    );

    // Initialization FSM
    wire init_done;
    wire init_active;
    wire init_start_timing;
    wire [3:0] init_nibble;
    wire init_rs;

    lcd_init_fsm #(
        .WAIT_POWER_ON(375000),
        .WAIT_4_1MS(102500),
        .WAIT_100US(2500),
        .WAIT_40US(1000)
    ) init_fsm_inst (
        .clk(clk),
        .rst(rst),
        .timing_done(timing_done),
        .start_timing(init_start_timing),
        .nibble_out(init_nibble),
        .rs_out(init_rs),
        .init_done(init_done),
        .init_active(init_active)
    );

    // ========================================================================
    // Controller state machine
    // ========================================================================

    localparam [1:0]
        ST_IDLE       = 2'd0,          // Waiting for CPU write or init
        ST_HIGH_NIBBLE = 2'd1,         // Sending high nibble
        ST_LOW_NIBBLE  = 2'd2;         // Sending low nibble

    reg [1:0] state;
    reg [7:0] byte_reg;                // Byte to send
    reg rs_reg;                        // RS for this byte (0=command, 1=data)
    reg cpu_write_pending;             // CPU write in progress

    // Pulse generation for timing start
    reg start_pulse;

    // Mux timing signals between init FSM and CPU controller
    assign timing_start = init_active ? init_start_timing : start_pulse;
    assign timing_nibble = init_active ? init_nibble :
                          (state == ST_HIGH_NIBBLE) ? byte_reg[7:4] : byte_reg[3:0];
    assign timing_rs = init_active ? init_rs : rs_reg;

    // Busy flag: Set if init active, timing busy, or CPU write pending
    wire controller_busy;
    assign controller_busy = init_active | timing_busy | cpu_write_pending;

    // ========================================================================
    // CPU Register Interface
    // ========================================================================

    always @(posedge clk) begin
        if (rst) begin
            state <= ST_IDLE;
            byte_reg <= 8'h00;
            rs_reg <= 1'b0;
            cpu_write_pending <= 1'b0;
            data_out <= 8'h00;
            start_pulse <= 1'b0;

        end else begin
            // Default: start_pulse is single-cycle
            start_pulse <= 1'b0;

            // Handle CPU reads (registered at read strobe)
            // Captures output when CPU reads (rd strobe at MC=7)
            // Holds value through MC=5 and MC=4 for proper CPU capture timing
            if (rd) begin  // Capture when read strobe arrives (cs && MC=7)
                case (addr[1:0])
                    2'b00: data_out <= 8'h00;              // Data reg (write-only)
                    2'b01: data_out <= 8'h00;              // Command reg (write-only)
                    2'b10: data_out <= {7'h00, controller_busy};  // Status reg (bit 0 = busy)
                    default: data_out <= 8'h00;
                endcase
            end
            // else: hold previous value

            // Handle CPU writes
            if (cs && we && !controller_busy) begin
                case (addr[1:0])
                    2'b00: begin  // Data register ($C100)
                        byte_reg <= data_in;
                        rs_reg <= 1'b1;             // RS=1 for data
                        cpu_write_pending <= 1'b1;
                        state <= ST_HIGH_NIBBLE;
                        start_pulse <= 1'b1;        // Pulse to start high nibble
                    end

                    2'b01: begin  // Command register ($C101)
                        byte_reg <= data_in;
                        rs_reg <= 1'b0;             // RS=0 for command
                        cpu_write_pending <= 1'b1;
                        state <= ST_HIGH_NIBBLE;
                        start_pulse <= 1'b1;        // Pulse to start high nibble
                    end

                    // Status register is read-only, ignore writes
                    default: begin
                        // No action
                    end
                endcase
            end

            // State machine for nibble sequencing
            case (state)
                ST_IDLE: begin
                    // Waiting for write
                    cpu_write_pending <= 1'b0;
                end

                ST_HIGH_NIBBLE: begin
                    // Wait for timing to complete high nibble
                    if (timing_done) begin
                        state <= ST_LOW_NIBBLE;
                        start_pulse <= 1'b1;        // Pulse to start low nibble
                    end
                end

                ST_LOW_NIBBLE: begin
                    // Wait for timing to complete low nibble
                    if (timing_done) begin
                        state <= ST_IDLE;
                        cpu_write_pending <= 1'b0;
                    end
                end

                default: begin
                    state <= ST_IDLE;
                end
            endcase
        end
    end

endmodule
