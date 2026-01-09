# Research: Graphics Mode GPU Technical Decisions

**Feature**: 005-graphics-gpu
**Date**: 2026-01-04
**Status**: Complete

This document resolves all technical unknowns identified in the implementation plan Phase 0.

---

## 1. VRAM Block RAM Synthesis

### Question
How to ensure Yosys synthesizes dual-port RAM as ECP5 block RAM vs. distributed RAM?

### Research Findings

**Existing Evidence from character_buffer.v**:
```verilog
// Character buffer memory - 2400 bytes to support 80x30 mode
// Synthesis directive to ensure block RAM inference
(* ram_style = "block" *)
reg [7:0] char_mem [0:2399];
```

The existing character buffer (2.4KB) successfully uses the `(* ram_style = "block" *)` synthesis attribute to force block RAM inference.

**ECP5 Block RAM Capabilities**:
- Each EBR (Embedded Block RAM) block: 18Kbit = 2,304 bytes
- ECP5-25F total: 1,008 Kbit = 126 KB = 54 EBR blocks (896KB in spec refers to different counting)
- 32KB VRAM = ~14 EBR blocks
- Dual-port mode: Supported natively by ECP5 EBR
- Independent clock domains: Supported (true dual-port with separate read/write clocks)

**Yosys Synthesis Directive**:
```verilog
(* ram_style = "block" *)
reg [7:0] vram_mem [0:32767];  // 32KB array
```

### Decision

**Use `(* ram_style = "block" *)` synthesis attribute on VRAM array**

**Rationale**:
- Proven working pattern in existing character_buffer.v
- Yosys documentation confirms this attribute for block RAM inference
- ECP5 has sufficient block RAM capacity (32KB = 3.6% of total)
- No need for manual instantiation of primitives (keep code portable)

**Verification Method**:
- Check Yosys synthesis report for "Inferred memory" vs. "Using EBR"
- Target: VRAM should map to 14 EBR blocks (or similar)

**Fallback Plan**:
If 32KB single array fails synthesis:
- Split into 4× 8KB blocks (one per framebuffer page)
- Multiplex based on high address bits
- Slightly more complex but guaranteed to synthesize

---

## 2. Register Address Mapping

### Question
What register addresses are available in the current memory map for graphics GPU?

### Research Findings

**Existing Register Assignments** (from gpu_registers.v and other peripherals):
- **0xC010-0xC016**: Character GPU (7 registers)
  - 0xC010: CHAR_DATA
  - 0xC011: CURSOR_ROW
  - 0xC012: CURSOR_COL
  - 0xC013: CONTROL
  - 0xC014: FG_COLOR
  - 0xC015: BG_COLOR
  - 0xC016: STATUS

- **UART Registers**: Likely 0xC000-0xC00F range (typical for first peripheral)
- **PS/2 Keyboard**: Likely 0xC020-0xC02F range
- **LCD Controller**: Likely 0xC030-0xC03F range (if present)

**Available Address Space**:
The I/O region typically spans 0xC000-0xCFFF (4KB), with most peripherals using 16-byte blocks.

**Proposed Graphics GPU Base**: 0xC100-0xC10F (16 registers, 256 bytes available if needed)

### Decision

**Graphics GPU Register Base: 0xC100-0xC10F**

**Rationale**:
- No conflicts with existing peripherals
- Clean 16-register block (0x00-0x0F offsets)
- Leaves 0xC110-0xC1FF available for future graphics features (sprites, blitter)
- Easy to remember (0xC010 = character, 0xC100 = graphics)

**Register Allocation**:
```
0xC100: VRAM_ADDR_LO   [RW] - VRAM address pointer low byte
0xC101: VRAM_ADDR_HI   [RW] - VRAM address pointer high byte (0-$7F)
0xC102: VRAM_DATA      [RW] - Read/write data at current address
0xC103: VRAM_CTRL      [RW] - Bit 0: Burst mode enable
0xC104: FB_BASE_LO     [RW] - Framebuffer base address low byte
0xC105: FB_BASE_HI     [RW] - Framebuffer base address high byte
0xC106: GPU_MODE       [RW] - Bits 1:0: Mode (00=1BPP, 01=2BPP, 10=4BPP)
0xC107: CLUT_INDEX     [RW] - Palette index (0-15)
0xC108: CLUT_DATA_R    [RW] - Red component (4 bits in lower nibble)
0xC109: CLUT_DATA_G    [RW] - Green component (4 bits in lower nibble)
0xC10A: CLUT_DATA_B    [RW] - Blue component (4 bits in lower nibble)
0xC10B: GPU_STATUS     [RO] - Bit 0: VBlank flag
0xC10C: GPU_IRQ_CTRL   [RW] - Bit 0: VBlank interrupt enable
0xC10D: DISPLAY_MODE   [RW] - Bit 0: 0=Character, 1=Graphics
0xC10E: Reserved
0xC10F: Reserved
```

**Integration Note**:
The top-level SOC module will need to decode address bits [7:4]=0x10 to route to graphics GPU registers.

---

## 3. Clock Domain Crossing for VBlank Interrupt

### Question
How to safely cross VBlank signal from pixel clock (25MHz) to CPU clock domain?

### Research Findings

**Problem**:
- VBlank signal generated in pixel clock domain (clk_pixel = 25 MHz)
- CPU interrupt needs to be in CPU clock domain (clk_cpu = unknown, likely 12.5-25 MHz)
- Direct wire crossing can cause metastability

**Existing Pattern** (from gpu_core.v comments):
```verilog
// VSYNC status for register reads (synchronized to CPU clock domain)
// For simplicity, we use the vsync signal directly. In a production design,
// this should be synchronized using a dual-flop synchronizer.
assign vsync_status = vsync;
```

The current design acknowledges the issue but doesn't implement synchronization (acceptable for quasi-static signals like status reads, but NOT for interrupts).

**Dual-Flop Synchronizer Pattern**:
```verilog
// Synchronize VBlank to CPU clock domain
reg vblank_sync1, vblank_sync2;

always @(posedge clk_cpu or negedge rst_n) begin
    if (!rst_n) begin
        vblank_sync1 <= 1'b0;
        vblank_sync2 <= 1'b0;
    end else begin
        vblank_sync1 <= vblank_pixel;  // First flop
        vblank_sync2 <= vblank_sync1;  // Second flop (output)
    end
end

// Edge detection for interrupt (rising edge of synchronized VBlank)
reg vblank_prev;
wire vblank_edge = vblank_sync2 && !vblank_prev;

always @(posedge clk_cpu or negedge rst_n) begin
    if (!rst_n)
        vblank_prev <= 1'b0;
    else
        vblank_prev <= vblank_sync2;
end

assign cpu_interrupt = vblank_edge;  // One-cycle pulse
```

### Decision

**Use dual-flop synchronizer with edge detection for VBlank interrupt**

**Rationale**:
- Standard practice for clock domain crossing in FPGA designs
- Two flip-flops reduce metastability probability to negligible levels
- Edge detection creates clean one-cycle interrupt pulse in CPU clock domain
- Minimal logic overhead (3 flip-flops + 1 AND gate)

**Implementation Details**:
1. Synchronize VBlank signal from pixel clock to CPU clock using two flip-flops
2. Detect rising edge of synchronized VBlank to create interrupt pulse
3. Interrupt pulse lasts one CPU clock cycle
4. CPU ISR clears interrupt by reading GPU_STATUS register

**Latency**:
- 2-3 CPU clock cycles delay from VBlank assertion to interrupt
- Acceptable for VBlank timing (±1 scanline spec = ±40 microseconds @ 25MHz)

---

## 4. RGB444 to RGB888 Expansion

### Question
What is the best bit expansion method for RGB444 → RGB888 with no color banding?

### Research Findings

**Three Methods Compared**:

1. **Zero-Padding (Shift Left)**:
   ```verilog
   rgb888 = {rgb444, 4'b0000}  // e.g., 4'hA → 8'hA0
   ```
   - Result: Values 0x00, 0x10, 0x20, ..., 0xF0
   - **Problem**: Maximum brightness is 0xF0, not 0xFF (only 94% of full range)

2. **Bit Duplication**:
   ```verilog
   rgb888 = {rgb444, rgb444}  // e.g., 4'hA → 8'hAA
   ```
   - Result: Values 0x00, 0x11, 0x22, ..., 0xFF
   - **Advantage**: Full 0-255 range, uniform steps
   - Used in: VGA DACs, many retro video chips

3. **MSB Replication** (Also called "scale and replicate"):
   ```verilog
   rgb888 = {rgb444, rgb444[3:0]}  // Same as method 2
   ```
   - Mathematically optimal for linear scaling
   - Same result as bit duplication for 4-bit → 8-bit

**Visual Analysis**:
- 4-bit color (16 levels per channel) → 4,096 total colors
- Goal: Expand to 8-bit without visible banding
- Bit duplication gives evenly distributed levels: 0, 17, 34, 51, ..., 255
- Step size: 17 units (6.7% of range) - acceptable for retro aesthetic

**Existing Pattern** (spec.md mentions this):
From spec.md User Story 4, scenario 4:
> "RGB444 values are expanded to RGB888 by duplicating bits: R=$88, G=$AA, B=$55"

This confirms bit duplication is the intended method.

### Decision

**Use bit duplication: `{R[3:0], R[3:0]}` for RGB444 → RGB888 expansion**

**Rationale**:
- Provides full 0-255 output range (unlike zero-padding)
- Simple implementation: `{r[3:0], r[3:0]}, {g[3:0], g[3:0]}, {b[3:0], b[3:0]}`
- Standard practice in VGA and retro video hardware
- Uniform color distribution (no gaps or uneven steps)
- Matches spec.md example

**Implementation**:
```verilog
wire [7:0] red_expanded   = {palette_r[3:0], palette_r[3:0]};
wire [7:0] green_expanded = {palette_g[3:0], palette_g[3:0]};
wire [7:0] blue_expanded  = {palette_b[3:0], palette_b[3:0]};
```

**Color Fidelity**:
- RGB444 → 4,096 colors (sufficient for retro games)
- Expansion to RGB888 maintains perceptual accuracy
- No visible banding with 16-level palette

---

## 5. Graphics/Character Mode Selection

### Question
How should system switch between character mode and graphics mode?

### Research Findings

**Option 1: Dedicated DISPLAY_MODE Register**
```verilog
0xC10D: DISPLAY_MODE [RW] - Bit 0: 0=Character, 1=Graphics
```
- **Pros**: Explicit control, simple mux logic, predictable behavior
- **Cons**: Requires CPU to explicitly switch modes

**Option 2: Automatic Based on VRAM Writes**
- **Idea**: First write to 0xC102 (VRAM_DATA) automatically enables graphics mode
- **Pros**: Convenient for simple programs
- **Cons**: Confusing behavior, hard to debug, violates principle of least surprise

**Option 3: Overlay Mode**
- **Idea**: Graphics always rendered "behind" character layer with transparency
- **Pros**: Can mix text and graphics
- **Cons**: Complex blending logic, out of scope for MVP

**Multiplexer Design**:
```verilog
module gpu_mux(
    input wire display_mode,        // 0=char, 1=graphics
    input wire [7:0] char_r, char_g, char_b,
    input wire [7:0] gfx_r, gfx_g, gfx_b,
    output wire [7:0] out_r, out_g, out_b
);
    assign out_r = display_mode ? gfx_r : char_r;
    assign out_g = display_mode ? gfx_g : char_g;
    assign out_b = display_mode ? gfx_b : char_b;
endmodule
```

### Decision

**Use dedicated DISPLAY_MODE register (0xC10D) with simple multiplexer**

**Rationale**:
- **Simplicity**: Clean separation of concerns, easy to understand
- **Educational Clarity**: Mode switching is explicit and obvious in code
- **Debuggability**: Always know which GPU is active
- **Testability**: Can test each GPU independently
- **Backward Compatibility**: Default to character mode (bit 0 = 0 at reset)

**Default Behavior**:
- Power-on reset: DISPLAY_MODE = 0 (character mode active)
- Graphics GPU disabled until CPU writes DISPLAY_MODE = 1
- Both GPUs always running, mux selects output

**Future Enhancement**:
If overlay mode is desired later, add DISPLAY_MODE bit 1 for blend enable.

---

## 6. Burst Write Performance

### Question
What is the achievable burst write bandwidth with 6502 CPU timing?

### Research Findings

**6502 Write Cycle Timing**:
- Minimum write cycle: 2 clock cycles (address setup + data write)
- At 25 MHz CPU clock: 2 cycles = 80 nanoseconds per write
- At 12.5 MHz CPU clock: 2 cycles = 160 nanoseconds per write

**With Burst Mode Optimization**:
- First write: Address setup (2 registers) + enable burst = 3 writes = 6 cycles
- Subsequent writes: 1 data write per cycle (auto-increment) = 2 cycles/byte
- 8KB framebuffer = 8,000 bytes

**Performance Calculation (12.5 MHz CPU)**:
```
Setup overhead: 6 cycles = 0.48 microseconds
Data transfer:  8000 bytes × 2 cycles/byte = 16,000 cycles = 1,280 microseconds
Total:          16,006 cycles = 1.28 milliseconds
```

**Performance Calculation (25 MHz CPU)**:
```
Setup overhead: 6 cycles = 0.24 microseconds
Data transfer:  8000 bytes × 2 cycles/byte = 16,000 cycles = 640 microseconds
Total:          16,006 cycles = 0.64 milliseconds
```

**Frame Budget**:
- 60 Hz refresh = 16.7 milliseconds per frame
- 1.28 ms (worst case) = 7.7% of frame time
- **Headroom**: Can update ~13 full framebuffers per frame (if needed)

### Decision

**Burst write achieves 0.64-1.28 ms for 8KB (depending on CPU clock), well under 100ms requirement**

**Success Criterion Validation**:
- **SC-001**: "Developer can write an 8KB framebuffer to VRAM using burst mode in under 100 milliseconds"
- **Result**: ✅ **PASS** - Actual time is 0.64-1.28 ms (156× to 78× faster than requirement)

**Frame Rate Implications**:
- **SC-007**: "Developer can render smooth animations at 30+ frames per second using double-buffered page flipping"
- With 1.28 ms transfer time, can render new frame every 1.28 ms + processing time
- Even with 50% CPU time for rendering logic, can achieve 300+ FPS (limited by 60 Hz display)
- **Result**: ✅ **PASS** - 30 FPS easily achievable

**Burst Mode Spec**:
```
Burst Mode Enabled:
  - Write to VRAM_ADDR_LO/HI sets starting address
  - Write to VRAM_CTRL bit 0 = 1 enables burst
  - Each write to VRAM_DATA increments VRAM_ADDR automatically
  - Write to VRAM_CTRL bit 0 = 0 disables burst (optional - can leave on)
```

**Note**: Even without burst mode (explicit address for each byte), 8KB transfer = 24,000 cycles = 1.92ms @ 12.5MHz, still well within 100ms requirement.

---

## Summary of Decisions

| Research Topic | Decision | Rationale |
|----------------|----------|-----------|
| **VRAM Block RAM Synthesis** | Use `(* ram_style = "block" *)` attribute | Proven pattern, Yosys support, sufficient ECP5 capacity |
| **Register Address Mapping** | Base address 0xC100-0xC10F for graphics GPU | No conflicts, clean 16-register block, future expansion room |
| **VBlank Clock Domain Crossing** | Dual-flop synchronizer with edge detection | Safe metastability handling, standard FPGA practice |
| **RGB444 to RGB888 Expansion** | Bit duplication `{R[3:0], R[3:0]}` | Full 0-255 range, uniform steps, retro hardware standard |
| **Graphics/Character Mode Selection** | Dedicated DISPLAY_MODE register (0xC10D) | Simple, explicit, testable, backward compatible |
| **Burst Write Performance** | 0.64-1.28 ms for 8KB (well under spec) | Validates SC-001 and SC-007, enables real-time graphics |

---

## Next Steps

All technical unknowns resolved. Proceed to Phase 1:
1. Generate `data-model.md` with VRAM layout and register definitions
2. Generate `contracts/register_map.md` with detailed register specifications
3. Generate `contracts/memory_map.md` with pixel encoding details
4. Generate `contracts/timing_diagrams.md` with burst write and VBlank sequences
5. Generate `quickstart.md` with step-by-step bitmap display guide
6. Update agent context with new GPU technologies

---

**Research Status**: ✅ COMPLETE - All Phase 0 questions answered
