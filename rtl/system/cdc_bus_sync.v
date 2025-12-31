/*
Clock Domain Crossing (CDC) Bus Synchronizer with Handshake
retrocpu DVI Character Display GPU

Safely crosses multi-bit data between clock domains using
a 4-phase handshake protocol. Guarantees all bits cross
atomically without corruption.

Protocol:
1. Source: Assert data_valid with stable data
2. Dest: Detects data_valid, captures data, asserts data_ack
3. Source: Sees data_ack, deasserts data_valid
4. Dest: Sees data_valid deassert, deasserts data_ack
5. Ready for next transfer

Latency: ~4-6 clock cycles in destination domain
Throughput: Limited by handshake round-trip time

Created: 2025-12-28
*/

module cdc_bus_sync #(
    parameter DATA_WIDTH = 8
)(
    // Source clock domain
    input  wire                    clk_src,
    input  wire                    rst_src_n,
    input  wire [DATA_WIDTH-1:0]   data_src,
    input  wire                    data_valid_src,
    output wire                    data_ready_src,

    // Destination clock domain
    input  wire                    clk_dst,
    input  wire                    rst_dst_n,
    output reg  [DATA_WIDTH-1:0]   data_dst,
    output reg                     data_valid_dst,
    input  wire                    data_ready_dst
);

//=============================================================================
// Source Clock Domain
//=============================================================================

reg [DATA_WIDTH-1:0] data_hold;
reg data_req;

// Synchronize acknowledgment from destination
wire data_ack_sync;
cdc_synchronizer #(
    .INIT_VALUE(1'b0),
    .NUM_STAGES(2)
) sync_ack (
    .clk_dst(clk_src),
    .rst_dst_n(rst_src_n),
    .signal_src(data_ack_sync_raw),
    .signal_dst(data_ack_sync)
);

// State machine for 4-phase handshake (source side)
localparam SRC_IDLE = 2'b00;
localparam SRC_REQ  = 2'b01;
localparam SRC_WAIT = 2'b10;

reg [1:0] src_state;

always @(posedge clk_src or negedge rst_src_n) begin
    if (!rst_src_n) begin
        data_hold  <= 0;
        data_req   <= 1'b0;
        src_state  <= SRC_IDLE;
    end else begin
        case (src_state)
            SRC_IDLE: begin
                if (data_valid_src) begin
                    data_hold <= data_src;  // Capture stable data
                    data_req  <= 1'b1;      // Assert request
                    src_state <= SRC_REQ;
                end
            end

            SRC_REQ: begin
                if (data_ack_sync) begin
                    data_req  <= 1'b0;      // Deassert request after ack
                    src_state <= SRC_WAIT;
                end
            end

            SRC_WAIT: begin
                if (!data_ack_sync) begin   // Wait for ack to clear
                    src_state <= SRC_IDLE;
                end
            end

            default: src_state <= SRC_IDLE;
        endcase
    end
end

assign data_ready_src = (src_state == SRC_IDLE);

//=============================================================================
// Destination Clock Domain
//=============================================================================

// Synchronize request from source
wire data_req_sync;
cdc_synchronizer #(
    .INIT_VALUE(1'b0),
    .NUM_STAGES(2)
) sync_req (
    .clk_dst(clk_dst),
    .rst_dst_n(rst_dst_n),
    .signal_src(data_req),
    .signal_dst(data_req_sync)
);

// State machine for 4-phase handshake (destination side)
localparam DST_IDLE = 2'b00;
localparam DST_CAPT = 2'b01;
localparam DST_WAIT = 2'b10;

reg [1:0] dst_state;
reg data_ack_sync_raw;

always @(posedge clk_dst or negedge rst_dst_n) begin
    if (!rst_dst_n) begin
        data_dst         <= 0;
        data_valid_dst   <= 1'b0;
        data_ack_sync_raw<= 1'b0;
        dst_state        <= DST_IDLE;
    end else begin
        case (dst_state)
            DST_IDLE: begin
                data_valid_dst <= 1'b0;
                if (data_req_sync) begin
                    data_dst          <= data_hold;  // Capture data
                    data_valid_dst    <= 1'b1;       // Signal valid data
                    data_ack_sync_raw <= 1'b1;       // Assert ack
                    dst_state         <= DST_CAPT;
                end
            end

            DST_CAPT: begin
                if (data_ready_dst) begin
                    data_valid_dst <= 1'b0;          // Clear valid after consumed
                end
                if (!data_req_sync) begin            // Wait for req to clear
                    data_ack_sync_raw <= 1'b0;       // Deassert ack
                    dst_state         <= DST_WAIT;
                end
            end

            DST_WAIT: begin
                dst_state <= DST_IDLE;
            end

            default: dst_state <= DST_IDLE;
        endcase
    end
end

endmodule
