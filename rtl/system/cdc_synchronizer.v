/*
Clock Domain Crossing (CDC) Synchronizer
retrocpu DVI Character Display GPU

Two-flip-flop synchronizer for safely crossing single-bit signals
between clock domains. Prevents metastability issues.

Usage: For crossing control signals (e.g., reset, enable flags)
       NOT for multi-bit data buses (use cdc_bus_sync for that)

Created: 2025-12-28
*/

module cdc_synchronizer #(
    parameter INIT_VALUE = 1'b0,  // Initial/reset value
    parameter NUM_STAGES = 2      // Number of flip-flop stages (min 2)
)(
    input  wire clk_dst,          // Destination clock domain
    input  wire rst_dst_n,        // Destination clock domain reset (active low)
    input  wire signal_src,       // Signal from source clock domain
    output wire signal_dst        // Synchronized signal in destination domain
);

// Synchronizer chain
(* ASYNC_REG = "TRUE" *) reg [NUM_STAGES-1:0] sync_chain = {NUM_STAGES{INIT_VALUE}};

// First stage captures potentially metastable signal
// Subsequent stages filter metastability
always @(posedge clk_dst or negedge rst_dst_n) begin
    if (!rst_dst_n) begin
        sync_chain <= {NUM_STAGES{INIT_VALUE}};
    end else begin
        sync_chain <= {sync_chain[NUM_STAGES-2:0], signal_src};
    end
end

assign signal_dst = sync_chain[NUM_STAGES-1];

endmodule
