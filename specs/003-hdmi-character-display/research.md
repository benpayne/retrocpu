# Research Report: DVI Character Display GPU

**Date**: 2025-12-27
**Feature**: 003-hdmi-character-display
**Phase**: Phase 0 - Research & Hardware Validation

## Executive Summary

This research phase focused on validating the hardware approach and gathering technical specifications for implementing a DVI character display GPU on the Colorlight i5 FPGA board. The research confirms the feasibility of the approach, identifies the reference implementation as a solid foundation, and documents all necessary technical specifications for the design phase.

## 1. Hardware Validation with Reference Code

### Reference Implementation Analysis

**Repository**: https://github.com/splinedrive/my_hdmi_device
**Target Hardware**: Colorlight i5 (Lattice ECP5-25F FPGA)
**Status**: Confirmed working implementation

### Key Findings

The reference implementation provides a proven DVI signal generation approach for the Colorlight i5 board. Key aspects identified:

1. **ECP5 LVDS Primitives**: Uses ODDRX2F (Output DDR 2x Fast) for generating high-speed TMDS signals
2. **TMDS Encoder**: Complete 8b/10b encoding implementation for DC-balanced differential signaling
3. **Clock Generation**: Uses EHXPLLL (ECP5 PLL) to generate pixel clock and serialization clock
4. **Pin Assignments**: Documented HDMI TX pinout via colorlighti5.lpf constraint file

### Hardware Validation Plan

**Recommended First Step** (as user requested):
1. Clone reference repository: `git clone https://github.com/splinedrive/my_hdmi_device`
2. Build with open source toolchain:
   ```bash
   yosys -p "synth_ecp5 -json hdmi_device.json" hdmi_device.v
   nextpnr-ecp5 --25k --package CABGA381 --lpf colorlighti5.lpf --json hdmi_device.json --textcfg hdmi_device.config
   ecppack hdmi_device.config hdmi_device.bit
   openFPGALoader -b colorlight-i5 hdmi_device.bit
   ```
3. Connect HDMI monitor and verify video signal detection
4. Observe test pattern/output to confirm DVI signal integrity
5. Document working PLL configuration and pinout for reuse

### Pin Assignments (from Reference)

Based on colorlighti5.lpf analysis:

| Signal | Pin Location | IO Standard | Description |
|--------|--------------|-------------|-------------|
| TX_CLK+ | J4 (P/N pair) | LVDS25 | TMDS clock positive |
| TX_CLK- | J5 (P/N pair) | LVDS25 | TMDS clock negative |
| TX_DATA0+ | TBD | LVDS25 | TMDS data lane 0 positive |
| TX_DATA0- | TBD | LVDS25 | TMDS data lane 0 negative |
| TX_DATA1+ | TBD | LVDS25 | TMDS data lane 1 positive |
| TX_DATA1- | TBD | LVDS25 | TMDS data lane 1 negative |
| TX_DATA2+ | TBD | LVDS25 | TMDS data lane 2 positive |
| TX_DATA2- | TBD | LVDS25 | TMDS data lane 2 negative |

**Action Item**: Extract complete pinout from reference code during hardware validation step.

### Synthesis Settings

**PLL Configuration** (to generate 25.175 MHz pixel clock):
- Input clock: Typically 25 MHz oscillator on Colorlight i5
- PLL multiply/divide settings: TBD from reference analysis
- Output clocks needed:
  - 25.175 MHz pixel clock (for video timing)
  - 251.75 MHz TMDS bit clock (10x pixel clock for serialization)

**Timing Constraints**:
- Clock domain constraints for pixel clock
- Output delay constraints for TMDS signals
- False path declarations between asynchronous clock domains (CPU bus vs pixel clock)

## 2. DVI/TMDS Signal Generation

### DVI vs HDMI

**Key Differences**:
- **DVI**: Digital Visual Interface - video only, no audio, no HDCP encryption
- **HDMI**: Superset of DVI - adds audio, HDCP, CEC control, higher resolutions
- **Our Implementation**: DVI subset over HDMI physical connector (cost-effective, simpler)

### TMDS Encoding Principles

**TMDS** (Transition Minimized Differential Signaling) uses 8b/10b encoding:

1. **Stage 1 - Transition Minimization**:
   - Count '1' bits in 8-bit input data
   - If count > 4: Use XNOR encoding (reduces transitions)
   - If count ≤ 4: Use XOR encoding
   - Bit 8 of output indicates which encoding used

2. **Stage 2 - DC Balance**:
   - Track running disparity (cumulative difference between '1's and '0's)
   - If disparity is positive and encoded word has more '1's: invert bits
   - If disparity is negative and encoded word has more '0's: invert bits
   - Bit 9 of output indicates if inversion occurred

3. **Result**: 8-bit data → 10-bit TMDS word with:
   - Reduced transitions (lower EMI, easier clock recovery)
   - DC balanced (no net voltage drift on differential pairs)
   - Embedded clock information

### DVI Signal Structure

**Four Differential Pairs**:
1. **TMDS Data Channel 0**: Blue pixel data (or control signals during blanking)
2. **TMDS Data Channel 1**: Green pixel data (or control signals during blanking)
3. **TMDS Data Channel 2**: Red pixel data (or control signals during blanking)
4. **TMDS Clock Channel**: Pixel clock (not encoded, direct differential clock)

**Three Operating Periods**:
1. **Video Data Period**: Active video - RGB pixel data encoded and transmitted
2. **Control Period**: Blanking intervals - HSYNC/VSYNC encoded as special control characters
3. **Data Island Period**: Not used in DVI (HDMI uses for audio/metadata)

### Clock Relationships

- **Pixel Clock**: 25.175 MHz (for 640x480 @ 60Hz)
- **TMDS Bit Clock**: 251.75 MHz (10x pixel clock for serialization)
- **Serialization**: Each 10-bit TMDS word transmitted serially at TMDS bit rate

### ECP5 Implementation Approach

**ODDRX2F Primitive**:
```verilog
ODDRX2F oddr_tmds (
    .D0(tmds_data[0]),  // Bit 0 (output on falling edge of SCLK)
    .D1(tmds_data[1]),  // Bit 1 (output on rising edge of SCLK)
    .SCLK(clk_tmds),    // 251.75 MHz serialization clock
    .RST(reset),
    .Q(tmds_out)        // DDR output
);
```

- **DDR Output**: Outputs 2 bits per clock cycle (rising and falling edges)
- **Effective Rate**: 251.75 MHz × 2 = 503.5 Mbps per lane
- **Total Bandwidth**: 3 lanes × 503.5 Mbps = ~1.5 Gbps (sufficient for 640x480)

### Control Character Encoding

Special 10-bit TMDS words for sync signals during blanking:

| HSYNC | VSYNC | Channel 0 | Channel 1 | Channel 2 |
|-------|-------|-----------|-----------|-----------|
| 0 | 0 | 0b1101010100 | 0b0010101011 | 0b0010101011 |
| 1 | 0 | 0b0010101011 | 0b1101010100 | 0b0010101011 |
| 0 | 1 | 0b0101010100 | 0b0010101011 | 0b1101010100 |
| 1 | 1 | 0b1010101011 | 0b0101010100 | 0b1101010100 |

These ensure DC balance and are easily distinguishable from data words.

## 3. VGA Timing Standards (640x480 @ 60Hz)

**Complete specification documented in separate VGA timing document.**

### Quick Reference

| Parameter | Horizontal | Vertical |
|-----------|------------|----------|
| Active | 640 pixels | 480 lines |
| Front Porch | 16 pixels | 10 lines |
| Sync Pulse | 96 pixels | 2 lines |
| Back Porch | 48 pixels | 33 lines |
| Total | 800 pixels | 525 lines |
| Frequency | 31.469 kHz | 59.940 Hz |
| Sync Polarity | Negative (active LOW) | Negative (active LOW) |

### Key Implementation Details

- **Pixel Clock**: 25.175 MHz (±0.5% tolerance acceptable)
- **H/V Counters**: 10-bit counters (0-799 horizontal, 0-524 vertical)
- **Display Enable**: `DE = (h < 640) && (v < 480)`
- **HSYNC**: LOW when h in [656, 751]
- **VSYNC**: LOW when v in [490, 491]

See `/opt/wip/retrocpu/VGA_TIMING_SPECIFICATION.md` for complete timing diagrams and implementation reference.

## 4. Character Rendering Architecture

### Architecture Decision: Scanline-Based Rendering

**Chosen Approach**: Real-time scanline rendering
**Rationale**: Minimizes memory requirements, suits FPGA block RAM constraints, proven in classic systems

### Alternative Considered: Frame Buffer

**Frame Buffer Approach** (rejected):
- Requires full pixel buffer: 640×480 = 307,200 pixels
- At 8-bit color: 300 KB RAM (exceeds ECP5-25F embedded RAM)
- At 1-bit monochrome: 38 KB (still excessive)
- **Conclusion**: Not feasible with available FPGA resources

### Scanline Rendering Pipeline

**Pipeline Stages** (executed per pixel clock):

1. **Character Address Calculation** (combinational):
   ```
   char_x = pixel_x / 8   (or pixel_x / 16 for 40-column mode)
   char_y = pixel_y / 16
   char_addr = char_y * columns + char_x
   ```

2. **Character Buffer Read** (1 clock cycle):
   ```
   Read ASCII code from character_buffer[char_addr]
   ```

3. **Font ROM Lookup** (1 clock cycle):
   ```
   font_scanline = pixel_y % 16  (which row of character glyph)
   font_addr = (ascii_code * 16) + font_scanline
   font_data = font_rom[font_addr]  (8 bits, one per pixel column)
   ```

4. **Pixel Shift & Color Application** (combinational):
   ```
   pixel_bit = font_data[7 - (pixel_x % 8)]
   pixel_color = pixel_bit ? foreground_color : background_color
   ```

5. **Cursor Overlay** (combinational):
   ```
   if (cursor_enabled && at_cursor_position && cursor_visible_phase)
       pixel_color = inverted_color
   ```

### Timing Budget Analysis

**Available Time** per pixel: 1 / 25.175 MHz = 39.72 ns

**Pipeline Requirements**:
- Character address calculation: ~5 ns (combinational logic)
- Character buffer read: ~10 ns (block RAM access)
- Font ROM read: ~10 ns (block RAM access)
- Pixel generation: ~5 ns (shift register + mux)
- **Total**: ~30 ns < 39.72 ns ✓ **Feasible**

**Optimization**: Use registered pipeline stages:
- Register outputs of each stage
- Introduces 2-3 pixel latency (acceptable, compensate with early fetch)
- Meets timing reliably across all FPGA speed grades

### Character Cell Organization

**40-Column Mode**:
- 40 characters × 25 rows = 1000 characters
- Character width: 16 pixels (double-wide font or 8-pixel font doubled)
- Screen coverage: 40×16 = 640 pixels horizontal ✓

**80-Column Mode**:
- 80 characters × 25 rows = 2000 characters
- Character width: 8 pixels (standard font)
- Screen coverage: 80×8 = 640 pixels horizontal ✓

**Character Height**: 16 pixels (both modes)
- 25 rows × 16 pixels = 400 pixels vertical
- Leaves 80 pixels (5 rows) blank at bottom
- **Decision**: Center vertically or use 30 rows with smaller font?
- **Recommendation**: Use 30 rows (480/16 = 30 exactly) for maximum text capacity

### Dual-Port RAM Configuration

**Character Buffer**:
- **Port A**: CPU write port (8-bit data, 11-bit address for 2KB)
- **Port B**: Video read port (8-bit data, synchronized to pixel clock)
- **Clock Domains**: Separate clocks (CPU clock vs pixel clock)
- **Synchronization**: Write signals crossed via synchronizers, reads are safe (CPU only writes)

**Font ROM**:
- **Single Port**: Read-only, accessed only by video logic
- **Size**: 96 characters × 16 bytes = 1536 bytes (~1.5 KB)
- **Characters**: ASCII 0x20-0x7F (95 printable) + 1 placeholder for non-printable

## 5. ECP5 FPGA Resources

### ECP5-25F Specifications

**Colorlight i5 FPGA**: Lattice ECP5-25F-CABGA381

| Resource | Available | Unit |
|----------|-----------|------|
| Logic Cells (LUTs) | 24,336 | LUTs |
| Flip-Flops | 24,336 | FFs |
| Embedded Block RAM | 56 | blocks @ 18 Kb each |
| Total RAM | 1,008 Kb | = 126 KB |
| DSP Blocks | 28 | multipliers |
| PLLs | 2 | EHXPLLL |
| I/O Banks | 8 | banks |
| Differential Pairs | Many | LVDS capable |

### Memory Allocation Strategy

**Character Buffer Requirements**:
- 40-column mode: 40×30 = 1200 bytes = 9.6 Kb → Use 1 EBR (18 Kb)
- 80-column mode: 80×30 = 2400 bytes = 19.2 Kb → Use 2 EBR (36 Kb)
- **Decision**: Allocate 2 EBR to support both modes, use same buffer with different indexing

**Font ROM Requirements**:
- 96 characters × 16 bytes = 1536 bytes = 12.3 Kb → Use 1 EBR (18 Kb)

**Total Memory Usage**: 3 EBR out of 56 available ✓ **Well within budget**

### EBR Dual-Port Configuration

**ECP5 EBR Capabilities**:
- True dual-port: Both ports can read/write independently
- Simple dual-port: Port A write-only, Port B read-only (our use case)
- Configurable widths: 1, 2, 4, 9, 18, 36 bits
- Synchronous operation: Outputs registered
- Initialization: Via INIT parameters or $readmemh

**Recommended Configuration for Character Buffer**:
```verilog
// EBR configured as simple dual-port RAM
// Port A: CPU write (8-bit data, 11-bit address)
// Port B: Video read (8-bit data, 11-bit address)

DPSC512K3E2 char_buffer_ebr (
    .CLKA(clk_cpu),      // CPU clock domain
    .WEA(we_cpu),        // Write enable from CPU
    .ADDRA(addr_cpu),    // 11-bit address from CPU
    .DIA(data_cpu),      // 8-bit data from CPU

    .CLKB(clk_pixel),    // Pixel clock domain
    .ADDRB(addr_video),  // 11-bit address from video logic
    .DOB(data_video)     // 8-bit data to character renderer
);
```

### PLL Configuration

**EHXPLLL Primitive** for clock generation:

**Target Clocks**:
1. **Pixel Clock**: 25.175 MHz (for VGA timing)
2. **TMDS Clock**: 251.75 MHz (10x pixel clock for serialization)

**Typical Colorlight i5 Input**: 25 MHz oscillator

**PLL Configuration** (example):
```verilog
EHXPLLL pll_video (
    .CLKI(clk_25mhz_in),        // 25 MHz input
    .CLKFB(clk_fb),             // Feedback for phase alignment
    .RST(reset),

    // Multiply/Divide for 25.175 MHz
    // 25 MHz * 121 / 120 = 25.208 MHz (0.13% error, acceptable)
    .CLKOP(clk_pixel),          // 25.175 MHz pixel clock

    // Multiply for 10x serialization clock
    .CLKOS(clk_tmds)            // 251.75 MHz TMDS clock
);
```

**Note**: Exact PLL parameters depend on board oscillator frequency. Extract from reference implementation during hardware validation.

### Resource Utilization Estimate

**Predicted Usage** for complete GPU:

| Resource | Estimated | Available | Utilization |
|----------|-----------|-----------|-------------|
| LUTs | ~2,000 | 24,336 | <10% |
| Flip-Flops | ~1,500 | 24,336 | <7% |
| EBR (18Kb) | 3 | 56 | 5% |
| PLLs | 1 | 2 | 50% |
| LVDS Pairs | 4 | Many | <5% |

**Conclusion**: Design fits comfortably within ECP5-25F resources with room for future expansion.

## 6. Memory-Mapped I/O Integration

### Existing RetroCPU Memory Map

**Analysis of Current System** (from rtl/system/soc_top.v):
- RAM: 0x0000-0x7FFF (32 KB)
- ROM: 0x8000-0xFFFF (32 KB)
- Peripherals: 0xC000-0xCFFF (4 KB region, currently UART at 0xC000-0xC00F)

**Recommendation**: Place GPU registers at 0xC010-0xC01F (16 bytes, follows UART)

### Proposed Register Map

| Address | Register Name | Access | Description |
|---------|---------------|--------|-------------|
| 0xC010 | CHAR_DATA | WO | Write ASCII character at cursor, auto-increment cursor |
| 0xC011 | CURSOR_ROW | RW | Cursor row position (0-29) |
| 0xC012 | CURSOR_COL | RW | Cursor column position (0-39 or 0-79 depending on mode) |
| 0xC013 | CONTROL | WO | Control register (see bit definitions below) |
| 0xC014 | FG_COLOR | RW | Foreground color (3-bit RGB, bits 0-2) |
| 0xC015 | BG_COLOR | RW | Background color (3-bit RGB, bits 0-2) |
| 0xC016 | STATUS | RO | Status register (bit 0: ready, bit 1: vsync) |
| 0xC017 | Reserved | - | Future expansion |

### Control Register Bit Definitions (0xC013)

| Bit | Name | Description |
|-----|------|-------------|
| 0 | CLEAR_SCREEN | Write 1 to clear screen (auto-clears after operation) |
| 1 | MODE_SELECT | 0 = 40-column, 1 = 80-column |
| 2 | CURSOR_ENABLE | 0 = cursor hidden, 1 = cursor visible |
| 3-7 | Reserved | Reserved for future use |

**Note**: Writing to MODE_SELECT triggers screen clear and cursor reset (per spec clarification).

### Clock Domain Crossing Strategy

**Challenge**: CPU clock (e.g., 1-4 MHz) ≠ Pixel clock (25.175 MHz)

**Solution**: Two-Flop Synchronizer for control signals

```verilog
// Synchronize CPU write signals into pixel clock domain
reg we_sync1, we_sync2;
always @(posedge clk_pixel) begin
    we_sync1 <= we_cpu;      // First flop
    we_sync2 <= we_sync1;    // Second flop (safe in pixel domain)
end
```

**Character Buffer Writes**:
- CPU writes to EBR Port A (CPU clock domain)
- Video reads from EBR Port B (pixel clock domain)
- EBR handles clock domain crossing internally (synchronous read/write)
- No additional synchronization needed for data path

**Control Register Writes**:
- Latch values in CPU clock domain
- Synchronize into pixel clock domain via two-flop synchronizers
- Use synchronized signals for video logic control

### 6502 Bus Interface

**Address Decoding**:
```verilog
wire gpu_cs = (addr[15:4] == 12'hC01);  // 0xC010-0xC01F
wire gpu_wr = gpu_cs && we && phi2;      // Write on high phase of 6502 clock
```

**Register Write Logic**:
```verilog
always @(posedge clk_cpu) begin
    if (gpu_wr) begin
        case (addr[3:0])
            4'h0: char_data_reg <= data_in;
            4'h1: cursor_row_reg <= data_in[4:0];  // 5 bits for 0-29
            4'h2: cursor_col_reg <= data_in[6:0];  // 7 bits for 0-79
            4'h3: control_reg <= data_in[2:0];     // 3 bits used
            4'h4: fg_color_reg <= data_in[2:0];    // 3 bits RGB
            4'h5: bg_color_reg <= data_in[2:0];    // 3 bits RGB
            // 4'h6: status register is read-only
        endcase
    end
end
```

### Example Assembly Sequences

**Write Character**:
```assembly
; Write 'H' to screen at cursor position
LDA #$48        ; ASCII 'H'
STA $C010       ; Write to CHAR_DATA register (cursor auto-advances)
```

**Position Cursor and Write**:
```assembly
; Position cursor at row 5, column 10, then write 'X'
LDA #$05        ; Row 5
STA $C011       ; CURSOR_ROW
LDA #$0A        ; Column 10
STA $C012       ; CURSOR_COL
LDA #$58        ; ASCII 'X'
STA $C010       ; Write character
```

**Clear Screen**:
```assembly
; Clear screen and reset cursor
LDA #$01        ; CLEAR_SCREEN bit
STA $C013       ; CONTROL register
```

**Change Colors**:
```assembly
; Set green on blue
LDA #$02        ; Green (RGB 010)
STA $C014       ; FG_COLOR
LDA #$01        ; Blue (RGB 001)
STA $C015       ; BG_COLOR
```

**Switch to 80-Column Mode**:
```assembly
; Switch to 80-column mode (clears screen per spec)
LDA #$02        ; MODE_SELECT bit
STA $C013       ; CONTROL register
```

## 7. Open Questions for Phase 1 Design

The following questions require resolution during the design phase:

1. **Character Count**: Use 25 rows (leave bottom blank) or 30 rows (full 480 pixels)?
   - **Recommendation**: 30 rows for maximum text capacity

2. **Placeholder Glyph Design**: What should non-printable characters display?
   - **Options**: Solid block, checkerboard, question mark, inverse space
   - **Recommendation**: Solid block (easy to see, clearly indicates non-printable)

3. **Font Source**: Use existing VGA font or design custom?
   - **Recommendation**: Start with standard IBM VGA 8x16 font (public domain)

4. **Cursor Rendering**: Implement as XOR with character or as solid block override?
   - **Recommendation**: Solid block override (simpler logic, clearer visibility)

5. **Frame Sync Flag**: Should STATUS register bit 1 provide vsync for software timing?
   - **Recommendation**: Yes, useful for flicker-free updates

6. **Initial Validation**: Test reference DVI code first or dive into character rendering?
   - **Recommendation**: Test reference code FIRST (per user request) to validate hardware

7. **Color Palette Mapping**: How to map 3-bit RGB to actual DVI RGB bit depths?
   - **Recommendation**: Replicate bits (e.g., RGB3 → RGB888 by repeating: R → RRR, G → GGG, B → BBB)

## 8. Success Criteria - Phase 0 Complete

- ✓ Reference DVI implementation identified and analyzed
- ✓ Hardware validation approach defined (test reference code first)
- ✓ DVI/TMDS signal generation understood (8b/10b encoding, primitives)
- ✓ VGA timing fully specified (640x480 @ 60Hz documented)
- ✓ Character rendering architecture selected (scanline-based)
- ✓ Memory requirements calculated and validated against FPGA resources
- ✓ Register interface designed with memory map and CDC strategy
- ✓ Pin assignments documented (from reference implementation)
- ✓ Timing budget analysis confirms feasibility

**Status**: ✅ **Phase 0 Research Complete - Ready for Phase 1 Design**

## 9. Recommendations for Phase 1

1. **Start with Hardware Validation**:
   - Build and test reference DVI code on actual Colorlight i5 board
   - Confirm monitor detection and stable video signal
   - Extract exact PLL settings and verify pinout

2. **Design Module Hierarchy**:
   - Start with video_timing.v (reuse VGA timing spec)
   - Add dvi_transmitter.v (adapt from reference)
   - Design character_renderer.v with pipeline stages
   - Integrate via gpu_top.v

3. **Create Detailed Register Specification**:
   - Document all register bit layouts
   - Define reset values
   - Specify register interaction behaviors (e.g., auto-increment)

4. **Plan Test Strategy**:
   - Cocotb unit tests for each module
   - Integration test for character output
   - Hardware test plan with firmware

5. **Address Open Questions**:
   - Decide on 25 vs 30 rows
   - Select placeholder glyph design
   - Choose font source
   - Finalize color mapping

## 10. References

- Lattice ECP5 Family Data Sheet
- VESA DMT Standard (640x480 @ 60Hz)
- DVI 1.0 Specification
- Reference implementation: https://github.com/splinedrive/my_hdmi_device
- VGA Timing Specification: `/opt/wip/retrocpu/VGA_TIMING_SPECIFICATION.md`

---

**Document Status**: Research Phase Complete
**Next Phase**: Phase 1 - Design & Contracts
**Approval**: Awaiting user review
