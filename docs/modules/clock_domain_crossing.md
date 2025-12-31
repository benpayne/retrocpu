# Clock Domain Crossing (CDC) Strategy
## retrocpu DVI Character Display GPU

**Created**: 2025-12-28
**Status**: Design Documentation

## Overview

The DVI Character Display GPU operates across multiple clock domains:
- **CPU Clock Domain**: M65C02 CPU clock (variable, typically 1-8 MHz)
- **Pixel Clock Domain**: 25 MHz for 640x480@60Hz video timing
- **TMDS Clock Domain**: 125 MHz for TMDS DDR serialization

All data crossing between these domains must be properly synchronized to prevent:
- Metastability (flip-flops entering undefined states)
- Data corruption (partial/stale data reads)
- Timing violations (setup/hold violations)

## Clock Domain Architecture

```
┌─────────────────┐         ┌──────────────────┐        ┌─────────────────┐
│   CPU Domain    │         │  Pixel Domain    │        │  TMDS Domain    │
│   (1-8 MHz)     │         │    (25 MHz)      │        │   (125 MHz)     │
├─────────────────┤         ├──────────────────┤        ├─────────────────┤
│                 │         │                  │        │                 │
│  CPU Writes     │  CDC    │  Character       │ Sync   │  TMDS Encoder   │
│  Registers ────>├────────>│  Renderer ──────>├───────>│  Serializer     │
│  (0xC010-C016)  │  Sync   │  Text Buffer     │        │  DDR Output     │
│                 │         │  Font ROM        │        │                 │
└─────────────────┘         └──────────────────┘        └─────────────────┘
```

## CDC Boundaries

### 1. CPU → Pixel Clock Domain

**Signals Crossing:**
- Register writes (CHAR_DATA, CONTROL, CURSOR_X, CURSOR_Y, FG_COLOR, BG_COLOR)
- STATUS register reads (busy flags)

**Synchronization Method:**
- **Write Path**: 4-phase handshake with `cdc_bus_sync`
- **Read Path**: Double-synchronizer with `cdc_synchronizer`

**Critical Properties:**
- Register writes are infrequent (relative to pixel clock)
- Data must cross atomically (all 8 bits together)
- No risk of overflow (write rate << pixel rate)

### 2. Pixel Clock → TMDS Clock Domain

**Signals Crossing:**
- RGB pixel data (24 bits)
- Sync signals (HSYNC, VSYNC, BLANK)

**Synchronization Method:**
- **Direct connection** (synchronous relationship)
- TMDS clock is exactly 5x pixel clock (from same PLL)
- Phase-aligned outputs from PLL ensure safe sampling

**Critical Properties:**
- Clocks are phase-locked (same PLL source)
- TMDS clock samples on defined pixel clock edges
- No metastability risk due to synchronous relationship

## Synchronization Modules

### cdc_synchronizer (Single-Bit)

**Purpose**: Synchronize single-bit control signals between clock domains

**Implementation**: 2-stage flip-flop chain
```verilog
always @(posedge clk_dst) begin
    sync_chain <= {sync_chain[0], signal_src};
end
```

**Latency**: 2 destination clock cycles

**Use Cases:**
- Reset signals
- Enable flags
- Status bits (busy, error flags)

**Limitations:**
- Single-bit only
- Input must be stable for ≥2 destination clock cycles
- No guarantee on detection of short pulses

### cdc_bus_sync (Multi-Bit with Handshake)

**Purpose**: Safely transfer multi-bit data buses between clock domains

**Implementation**: 4-phase handshake protocol

**Protocol Sequence:**
1. **Source asserts** `data_valid` with stable data
2. **Destination detects** valid, captures data, asserts `data_ack`
3. **Source sees** ack, deasserts `data_valid`
4. **Destination sees** deassert, deasserts `data_ack`
5. **Ready** for next transfer

**Latency**: 4-6 destination clock cycles

**Use Cases:**
- Register writes from CPU to video domain
- Configuration updates
- Multi-bit status/counter values

**Advantages:**
- Atomic transfer (all bits guaranteed consistent)
- Handshake prevents data loss
- Works with any clock ratio

**Disadvantages:**
- Higher latency than direct sync
- Limited throughput (handshake overhead)
- More complex (requires state machines both sides)

## Register Interface CDC Design

### Write Path (CPU → Pixel Domain)

```
CPU Write          CDC Handshake           Register Update
─────────          ──────────────          ───────────────
 Write to         [cdc_bus_sync]           Update internal
 0xC010   ───────>  4-phase     ─────────> register in
 (8 bits)           handshake              pixel domain

 CPU stalls       Handshake ACK            Register ready
 until ACK   <────  completes   <──────── for use by
 received                                  renderer
```

**Key Design Points:**
1. CPU write triggers handshake initiation
2. CPU waits for ACK before proceeding (ensures write completes)
3. Video domain captures data atomically
4. Video renderer always sees consistent register values

### Read Path (Pixel Domain → CPU)

```
Pixel Domain       CDC Sync                CPU Read
────────────       ────────                ────────
 STATUS bits      [cdc_synchronizer]       CPU reads
 (busy, etc.) ───>  2-stage FF    ─────>  STATUS
                    synchronizer           register
```

**Key Design Points:**
1. STATUS register is read-only from CPU perspective
2. Simple 2-FF synchronizer sufficient (no multi-bit atomicity needed)
3. CPU may see slightly stale data (2 pixel clocks old) - acceptable
4. No handshake required (read doesn't modify state)

## Metastability Protection

### What is Metastability?

When an async signal changes near a clock edge, a flip-flop can enter an undefined state between 0 and 1, potentially taking arbitrarily long to resolve. This can cause:
- Logic errors (undefined values propagate)
- Timing violations (late resolution misses next stage)
- System failures (glitches, incorrect behavior)

### Protection Strategy

**1. Multi-Stage Synchronizers**
- First FF captures potentially metastable signal
- Subsequent FFs filter metastability
- Probability of metastability decreases exponentially with stages
- 2 stages typically sufficient for most designs
- 3 stages for high-reliability applications

**2. Handshake Protocols**
- Source holds data stable during transfer
- Destination acknowledges successful capture
- No timing dependencies between domains
- Guaranteed safe transfer (no race conditions)

**3. ASYNC_REG Attribute**
```verilog
(* ASYNC_REG = "TRUE" *) reg [1:0] sync_chain;
```
- Instructs synthesis/P&R tools to keep FFs close together
- Reduces routing delay (faster metastability resolution)
- Places FFs in same slice when possible

## Timing Constraints

### Required SDC/LPF Constraints

**1. False Path Declaration**
```sdc
# Asynchronous crossings handled by synchronizers
set_false_path -from [get_clocks cpu_clk] -to [get_clocks pixel_clk]
```

**2. Maximum Delay for CDC Paths**
```sdc
# Synchronizer input must be stable before sampling
set_max_delay -from [get_pins */data_hold*/Q] \
              -to [get_pins */sync_chain[0]/D] \
              [expr 1.5 * $pixel_clk_period]
```

**3. Synchronous Clock Relationship (PLL Outputs)**
```sdc
# Pixel clock and TMDS clock are synchronous (same PLL)
set_clock_groups -physically_exclusive -group pixel_clk -group tmds_clk
```

## Design Rules for CDC

### DO:
✅ Use dedicated CDC synchronizers (cdc_synchronizer, cdc_bus_sync)
✅ Hold data stable during handshake
✅ Add timing constraints (false paths, max delays)
✅ Use ASYNC_REG attribute on synchronizer FFs
✅ Document all CDC boundaries clearly
✅ Simulate CDC behavior (verify protocol)

### DON'T:
❌ Cross multi-bit buses without handshake/gray code
❌ Use combinational logic between clock domains
❌ Assume synchronous relationship without PLL proof
❌ Ignore metastability (even "slow" signals need sync)
❌ Create feedback loops across domains
❌ Use latches in CDC paths (flip-flops only)

## Verification Strategy

### Simulation

**CDC-Specific Tests:**
1. **Metastability injection**: Force X values on synchronizer inputs
2. **Clock ratio sweep**: Test with various clock frequency ratios
3. **Back-to-back transfers**: Verify handshake protocol under stress
4. **Reset crossing**: Ensure safe reset across all domains

**Coverage Metrics:**
- All handshake states exercised
- Both valid and invalid input sequences
- Corner cases (simultaneous writes, resets)

### Static Analysis

**Lint Checks:**
- Identify all CDC crossings
- Verify synchronizers on all async paths
- Check for combinational logic in CDC
- Flag missing timing constraints

**Formal Verification:**
- Prove handshake protocol correctness
- Verify no data loss/corruption
- Check for deadlock conditions

## Performance Analysis

### Latency Budget

| Transfer | Method | Latency (pixel clks) | Notes |
|----------|--------|---------------------|-------|
| CPU Write → Pixel Domain | 4-phase handshake | 4-6 cycles | Includes round-trip |
| Pixel → TMDS | Direct (PLL-sync) | 0 cycles | Same PLL, phase-aligned |
| STATUS Read → CPU | 2-FF sync | 2 cycles | Acceptable staleness |

### Throughput Analysis

**Maximum Write Rate (CPU → Pixel):**
- Handshake round-trip: ~6 pixel clock cycles
- At 25 MHz pixel clock: ~240 ns per write
- Maximum write rate: ~4.2 million writes/second

**CPU Write Rate:**
- M65C02 at 4 MHz: ~250 ns per write instruction
- Write rate well below CDC capacity
- No risk of overflow or backpressure

## Future Enhancements

### Phase 5+ Optimizations

1. **Gray Code Counters**: For high-throughput pointer sync (circular buffers)
2. **Async FIFOs**: If write rate increases (DMA, burst transfers)
3. **Toggle Synchronizers**: For low-latency single-bit pulses
4. **Multi-Cycle Paths**: Relax timing where safe (improve routability)

## References

1. **Cliff Cummings**: "Clock Domain Crossing (CDC) Design & Verification Techniques"
2. **Sunburst Design**: "Synthesis and Scripting Strategies for Designing Multi-Asynchronous Clock Designs"
3. **ECP5 Family Handbook**: Clock domain crossing recommendations
4. **IEEE 1364-2005**: Verilog HDL standard (synchronizer idioms)

---

**Document Status**: ✅ Complete - Ready for Implementation
**Next Steps**: Implement CDC in register interface module (Phase 4)
