# Implementation Plan: Graphics Mode GPU with VRAM

**Branch**: `005-graphics-gpu` | **Date**: 2026-01-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-graphics-gpu/spec.md`

## Summary

Extend the existing character-mode GPU to support bitmap graphics by adding a 32KB VRAM framebuffer module with three bit-depth modes (1 BPP, 2 BPP, 4 BPP), a 16-entry RGB444 color palette, burst write mode for efficient transfers, and hardware page flipping with VBlank interrupts. The graphics GPU will coexist with the existing character-mode GPU, sharing the VGA timing infrastructure and register address space.

## Technical Context

**HDL Language**: Verilog (SystemVerilog for testbenches if needed)
**Target Architecture**: 6502-compatible retro computer system
**Testing Framework**: cocotb (Python-based HDL verification)
**Simulation**: Icarus Verilog (iverilog)
**Synthesis**: Yosys for open source synthesis
**Target FPGA**: Lattice ECP5-25F (ColorLight i5 board) - 896KB block RAM available
**Project Type**: FPGA/HDL - extends existing rtl/peripherals/video/ structure
**Existing Infrastructure**:
  - VGA timing generator (640x480@60Hz, 25MHz pixel clock) already implemented
  - DVI transmitter (tmds_encoder.v, dvi_transmitter.v) for HDMI output
  - Dual-port block RAM pattern established in character_buffer.v (2.4KB)
  - GPU register interface pattern in gpu_registers.v (base 0xC010)
**Timing Goals**:
  - 25 MHz pixel clock (existing VGA timing)
  - Single-cycle VRAM read for pixel fetch
  - Burst write: 1 byte per CPU clock cycle with auto-increment
**Resource Constraints**:
  - 32KB VRAM = ~3.6% of 896KB block RAM (easily fits)
  - Palette RAM: 16 entries × 12 bits = 192 bits (minimal)
  - Register space: 0xC100-0xC1FF (256 bytes available, need ~16 registers)
**Module Scope**: Graphics framebuffer GPU coexisting with character GPU

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with RetroCPU Constitution (.specify/memory/constitution.md):

- [x] **Test-Driven Design**: cocotb tests will be written before each module (gpu_vram.v, gpu_pixel_renderer.v, gpu_graphics_registers.v)
- [x] **Simplicity Over Performance**: Design favors clear dual-port RAM pattern over complex caching; straightforward pixel fetch pipeline
- [x] **Module Reusability**: Modules have clear interfaces - VRAM module reusable for other video modes, palette module reusable for sprites
- [x] **Educational Clarity**: Dual-port RAM clock domain crossing clearly documented; RGB444 bit expansion explained
- [x] **Open Source Tooling**: All tools (iverilog, cocotb, yosys) are open source; targets open FPGA toolchain
- [x] **Quality Gates**: Plan includes unit tests (VRAM, palette, registers), integration tests (full framebuffer render), waveform verification
- [x] **Technology Stack**: Using Verilog, cocotb, and yosys synthesis

**Constitution Compliance**: ✅ PASS - No violations

## Project Structure

### Documentation (this feature)

```text
specs/005-graphics-gpu/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - VRAM sizing, palette format, register mapping
├── data-model.md        # Phase 1 output - VRAM layout, palette structure, register definitions
├── quickstart.md        # Phase 1 output - How to display a bitmap in 3 steps
├── contracts/           # Phase 1 output - Register map, memory map, timing diagrams
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
rtl/peripherals/video/
├── gpu_core.v                    # Existing character GPU (unchanged)
├── gpu_registers.v               # Existing character registers (0xC010-0xC016)
├── gpu_graphics_vram.v           # NEW: 32KB dual-port VRAM module
├── gpu_graphics_palette.v        # NEW: 16-entry RGB444 palette (CLUT)
├── gpu_graphics_registers.v      # NEW: Graphics GPU registers (0xC100-0xC10F)
├── gpu_pixel_renderer.v          # NEW: Pixel fetch and bit-depth decoding
├── gpu_graphics_core.v           # NEW: Graphics GPU top-level integration
├── gpu_mux.v                     # NEW: Multiplexer to select char/graphics output
├── character_buffer.v            # Existing character buffer (unchanged)
├── character_renderer.v          # Existing character renderer (unchanged)
├── vga_timing_generator.v        # Existing VGA timing (shared by both GPUs)
├── font_rom.v                    # Existing font ROM (character mode only)
├── dvi_transmitter.v             # Existing DVI output (unchanged)
└── tmds_encoder.v                # Existing TMDS encoder (unchanged)

tests/unit/
├── test_gpu_vram.py              # NEW: VRAM dual-port, wrap, read-write tests
├── test_gpu_palette.py           # NEW: Palette write, read, RGB444 expansion tests
├── test_gpu_graphics_registers.py # NEW: Register writes, address pointer, burst mode
├── test_gpu_pixel_renderer.py    # NEW: 1/2/4 BPP rendering, palette lookup tests
├── test_gpu_registers.py         # Existing character GPU register tests

tests/integration/
├── test_gpu_graphics_framebuffer.py # NEW: Full framebuffer write and display test
├── test_gpu_page_flipping.py        # NEW: VBlank interrupt, page flip, tear-free test
├── test_gpu_mode_switching.py       # NEW: Switch between graphics modes test
└── test_gpu_character_output.py     # Existing character GPU test (unchanged)

docs/modules/
├── gpu_graphics_vram.md          # NEW: VRAM module documentation
├── gpu_graphics_architecture.md  # NEW: Overall graphics GPU architecture
└── gpu_register_map.md           # UPDATED: Add graphics registers 0xC100-0xC10F
```

**Structure Decision**: Extends existing `rtl/peripherals/video/` directory with new graphics modules while preserving existing character GPU. Both GPUs share VGA timing infrastructure and are multiplexed at the final output stage. This modular approach allows independent testing and development while maintaining backward compatibility with existing character display functionality.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - Constitution Check passed. All design choices align with simplicity, reusability, and educational clarity principles.

---

## Phase 0: Research & Technical Decisions

### Research Tasks

The following technical decisions require research to resolve unknowns:

1. **VRAM Block RAM Synthesis**
   - **Question**: How to ensure Yosys synthesizes dual-port RAM as ECP5 block RAM vs. distributed RAM?
   - **Research**: Review Yosys synthesis directives (`(* ram_style = "block" *)`), ECP5 block RAM capabilities, and verify in existing character_buffer.v implementation
   - **Output**: Synthesis directive pattern and memory size constraints

2. **Register Address Mapping**
   - **Question**: What register addresses are available in the current memory map for graphics GPU?
   - **Research**: Review existing I/O map, check for conflicts with character GPU (0xC010-0xC016), UART, PS/2, LCD controller
   - **Output**: Confirmed register base address (propose 0xC100-0xC10F for 16 graphics registers)

3. **Clock Domain Crossing for VBlank Interrupt**
   - **Question**: How to safely cross VBlank signal from pixel clock (25MHz) to CPU clock domain?
   - **Research**: Review existing clock domain crossing patterns, dual-flop synchronizer best practices
   - **Output**: Synchronizer pattern for interrupt signal

4. **RGB444 to RGB888 Expansion**
   - **Question**: What is the best bit expansion method for RGB444 → RGB888 with no color banding?
   - **Research**: Compare bit duplication (`{R[3:0], R[3:0]}`) vs. zero-padding vs. bit replication with MSB
   - **Output**: Bit expansion formula

5. **Graphics/Character Mode Selection**
   - **Question**: How should system switch between character mode and graphics mode?
   - **Research**: Review options (dedicated register bit, automatic based on VRAM writes, manual mode switch)
   - **Output**: Mode selection mechanism and multiplexer design

6. **Burst Write Performance**
   - **Question**: What is the achievable burst write bandwidth with 6502 CPU timing?
   - **Research**: Calculate cycles needed to write 8KB framebuffer, compare to 16.7ms frame period
   - **Output**: Performance analysis and SC-001 validation

### Research Output Location

All findings will be documented in:
```
specs/005-graphics-gpu/research.md
```

---

## Phase 1: Design Artifacts

### 1. Data Model (`data-model.md`)

Defines the structure of:

- **VRAM Layout**: 32KB address space ($0000-$7FFF), 4 pages of 8KB each
  - Page 0: $0000-$1FFF (8,000 bytes)
  - Page 1: $2000-$3FFF (8,000 bytes)
  - Page 2: $4000-$5FFF (8,000 bytes)
  - Page 3: $6000-$7FFF (8,000 bytes)

- **Framebuffer Layouts**:
  - 1 BPP mode: 320x200 pixels, 40 bytes/row, 200 rows = 8,000 bytes
  - 2 BPP mode: 160x200 pixels, 40 bytes/row, 200 rows = 8,000 bytes
  - 4 BPP mode: 160x100 pixels, 80 bytes/row, 100 rows = 8,000 bytes

- **Palette Structure**: 16 entries, each 12 bits (RGB444)
  - Entry format: `{4'b_red, 4'b_green, 4'b_blue}`
  - Index 0-15 for 2 BPP and 4 BPP modes

- **Register File**: 16 registers (0xC100-0xC10F)
  - Address pointer (LO/HI), data, control, mode, palette index, palette RGB, framebuffer base, status, IRQ control

### 2. API Contracts (`contracts/`)

#### `register_map.md`
Complete register specification with bit layouts:

```
0xC100: VRAM_ADDR_LO   [RW] - VRAM address pointer low byte
0xC101: VRAM_ADDR_HI   [RW] - VRAM address pointer high byte (0-$7F for 32KB)
0xC102: VRAM_DATA      [RW] - Read/write data at current address
0xC103: VRAM_CTRL      [RW] - Bit 0: Burst mode enable, Bit 1: Reserved
0xC104: FB_BASE_LO     [RW] - Framebuffer base address low byte
0xC105: FB_BASE_HI     [RW] - Framebuffer base address high byte
0xC106: GPU_MODE       [RW] - Bits 1:0: Mode (00=1BPP, 01=2BPP, 10=4BPP)
0xC107: CLUT_INDEX     [RW] - Palette index (0-15)
0xC108: CLUT_DATA_R    [RW] - Red component (4 bits in lower nibble)
0xC109: CLUT_DATA_G    [RW] - Green component (4 bits in lower nibble)
0xC10A: CLUT_DATA_B    [RW] - Blue component (4 bits in lower nibble)
0xC10B: GPU_STATUS     [RO] - Bit 0: VBlank flag, Bit 1: Reserved
0xC10C: GPU_IRQ_CTRL   [RW] - Bit 0: VBlank interrupt enable
0xC10D: DISPLAY_MODE   [RW] - Bit 0: 0=Character mode, 1=Graphics mode
0xC10E-0xC10F: Reserved
```

#### `memory_map.md`
VRAM address mapping and pixel encoding:

- **1 BPP**: 8 pixels per byte, MSB = leftmost pixel
- **2 BPP**: 4 pixels per byte, each 2-bit value is palette index (0-3)
- **4 BPP**: 2 pixels per byte, each 4-bit value is palette index (0-15)

#### `timing_diagrams.md`
Timing diagrams for:
- Burst write sequence (address setup → data writes with auto-increment)
- VBlank interrupt timing (vsync edge → interrupt assertion)
- Page flip sequence (VBlank ISR → FB_BASE_ADDR update)

### 3. Quick Start Guide (`quickstart.md`)

Step-by-step guide for beginners:

```
How to Display a Bitmap in Graphics Mode
=========================================

1. Set graphics mode (4 BPP for 16 colors):
   POKE $C106, $02  ; GPU_MODE = 4 BPP

2. Program palette (example: red, green, blue, white):
   POKE $C107, $00  ; CLUT_INDEX = 0
   POKE $C108, $00  ; Red = 0
   POKE $C109, $00  ; Green = 0
   POKE $C10A, $00  ; Blue = 0 (black)

   POKE $C107, $01  ; CLUT_INDEX = 1
   POKE $C108, $0F  ; Red = 15
   POKE $C109, $00  ; Green = 0
   POKE $C10A, $00  ; Blue = 0 (red)

   ; ... repeat for indices 2-15

3. Write pixel data using burst mode:
   POKE $C100, $00  ; VRAM_ADDR_LO = $00
   POKE $C101, $00  ; VRAM_ADDR_HI = $00 (start at $0000)
   POKE $C103, $01  ; VRAM_CTRL = burst mode ON

   ; Write 8000 bytes of pixel data
   FOR I = 0 TO 7999
     POKE $C102, PIXELDATA(I)  ; Auto-increment address
   NEXT I

   POKE $C103, $00  ; Burst mode OFF

4. Enable graphics display:
   POKE $C10D, $01  ; DISPLAY_MODE = graphics mode

Done! Your bitmap is now visible on screen.
```

### 4. Agent Context Update

Run `.specify/scripts/bash/update-agent-context.sh claude` to add:
- New technology: "Graphics framebuffer GPU with VRAM"
- Register range: 0xC100-0xC10F for graphics GPU control
- Module list: gpu_graphics_vram.v, gpu_graphics_palette.v, gpu_graphics_registers.v, gpu_pixel_renderer.v

---

## Module Implementation Order (for /speckit.tasks)

When `/speckit.tasks` is run, tasks should be prioritized in this order aligned with user stories:

### P1: Single-Page Graphics Display (MVP)
1. `gpu_graphics_vram.v` - 32KB dual-port VRAM with block RAM synthesis
2. `gpu_graphics_palette.v` - 16-entry RGB444 palette with read/write interface
3. `gpu_graphics_registers.v` - Register file (address pointer, data, mode, palette access)
4. `gpu_pixel_renderer.v` - Pixel fetch and 1/2/4 BPP decoding with palette lookup
5. `gpu_graphics_core.v` - Top-level integration (VRAM + palette + registers + renderer)
6. `gpu_mux.v` - Output multiplexer to select character vs. graphics mode

### P2: Efficient Bulk Transfer
7. Burst mode logic in `gpu_graphics_registers.v` (auto-increment on VRAM_DATA write)

### P2: Palette Programming
8. Palette write interface already covered in step 2 above

### P3: Page Flipping
9. VBlank interrupt generation and synchronization
10. Framebuffer base address register (FB_BASE_ADDR_LO/HI) implementation

---

## Testing Strategy

### Unit Tests (cocotb)

Each module gets comprehensive unit tests:

1. **test_gpu_vram.py**
   - Write to address, read back, verify data
   - Test address wrapping ($7FFF → $0000)
   - Test dual-port operation (simultaneous CPU write, video read)
   - Test clock domain crossing (write on clk_cpu, read on clk_pixel)

2. **test_gpu_palette.py**
   - Write RGB444 values via CLUT_INDEX and CLUT_DATA_R/G/B
   - Read back palette entries
   - Test RGB444 → RGB888 expansion (verify bit duplication)
   - Test invalid index handling (>15)

3. **test_gpu_graphics_registers.py**
   - Write/read VRAM_ADDR_LO/HI, verify address pointer
   - Test burst mode auto-increment
   - Test VRAM_DATA write with auto-increment
   - Test FB_BASE_ADDR register writes
   - Test GPU_MODE register (1/2/4 BPP selection)

4. **test_gpu_pixel_renderer.py**
   - Feed VRAM data and verify pixel output for each mode:
     - 1 BPP: Black/white pixels
     - 2 BPP: 4-color palette lookup
     - 4 BPP: 16-color palette lookup
   - Test scanline generation (row/column to VRAM address mapping)
   - Test framebuffer base offset

### Integration Tests (cocotb)

Full system tests exercising complete workflows:

1. **test_gpu_graphics_framebuffer.py**
   - Write 8KB test pattern to VRAM
   - Configure GPU for 4 BPP mode
   - Program palette with known colors
   - Render frame and verify pixel output matches expected pattern
   - Covers User Story 1 acceptance scenarios

2. **test_gpu_page_flipping.py**
   - Write different patterns to page 0 ($0000) and page 1 ($2000)
   - Set FB_BASE_ADDR to page 0, verify display
   - Wait for VBlank interrupt
   - Set FB_BASE_ADDR to page 1 during VBlank
   - Verify display switches with no tearing
   - Covers User Story 3 acceptance scenarios

3. **test_gpu_mode_switching.py**
   - Write test pattern to VRAM
   - Render in 1 BPP mode, verify output
   - Switch to 2 BPP mode, verify same data reinterpreted
   - Switch to 4 BPP mode, verify again
   - Covers User Story 1 scenario 4

4. **test_gpu_burst_write_performance.py**
   - Measure clock cycles to write 8KB via burst mode
   - Verify performance meets SC-001 (under 100ms)

### Waveform Verification

Key signals to observe in simulation:
- VRAM address pointer auto-increment during burst writes
- VBlank interrupt timing relative to vsync signal
- Pixel data fetch timing (VRAM address → data → RGB output pipeline)
- Page flip timing (FB_BASE_ADDR change → display update)

---

## Risk Analysis

### Technical Risks

1. **Block RAM Synthesis**
   - **Risk**: Yosys may infer distributed RAM instead of block RAM for 32KB VRAM
   - **Mitigation**: Use explicit `(* ram_style = "block" *)` directive, verify in synthesis report
   - **Fallback**: Split VRAM into 4×8KB blocks if single 32KB block fails

2. **Clock Domain Crossing**
   - **Risk**: VBlank interrupt may glitch when crossing from pixel clock to CPU clock
   - **Mitigation**: Use dual-flop synchronizer for interrupt signal
   - **Validation**: Test in cocotb with random phase relationship between clocks

3. **Pixel Fetch Timing**
   - **Risk**: VRAM read latency may not meet pixel clock timing for back-to-back pixels
   - **Mitigation**: Use registered read output (1-cycle latency acceptable), pipeline design
   - **Validation**: Timing analysis in synthesis, waveform verification

4. **Resource Utilization**
   - **Risk**: Additional logic for graphics GPU may exceed FPGA capacity
   - **Mitigation**: Keep design simple (no blitter, no sprites in this phase)
   - **Validation**: Synthesis reports, target <50% LUT utilization

### Scope Creep Risks

1. **Feature Creep**: Temptation to add sprites, blitter, hardware scroll
   - **Mitigation**: Strict adherence to spec; mark extras as "future features"

2. **Complexity Creep**: Over-engineering pixel pipeline with deep buffering
   - **Mitigation**: Follow Constitution principle "Simplicity Over Performance"

---

## Success Criteria Validation Plan

Map each success criterion from spec.md to validation method:

- **SC-001** (8KB in <100ms): Measure in test_gpu_burst_write_performance.py
- **SC-002** (Correct display in all modes): Visual verification + test_gpu_graphics_framebuffer.py
- **SC-003** (Tear-free page flip): test_gpu_page_flipping.py with VBlank sync verification
- **SC-004** (Palette change <16.7ms): Measure in test_gpu_palette.py (should be immediate)
- **SC-005** (VRAM <5% block RAM): Check Yosys synthesis report for EBR usage
- **SC-006** (VBlank ±1 scanline): Measure in test_gpu_page_flipping.py
- **SC-007** (30+ FPS animation): Calculate from SC-001 (10 FPS proven, 30 FPS extrapolated)
- **SC-008** (No color banding): Visual verification of RGB444 expansion in test_gpu_palette.py

---

## Dependencies and Integration Points

### Existing Modules (No Changes Required)
- `vga_timing_generator.v` - Provides h_count, v_count, hsync, vsync, video_active (shared)
- `dvi_transmitter.v` - Accepts RGB888 output (from mux)
- `tmds_encoder.v` - HDMI encoding (unchanged)

### Existing Modules (Minor Changes Required)
- `gpu_top.v` - Instantiate gpu_graphics_core.v and gpu_mux.v, wire display mode select

### New Module Dependencies
- `gpu_graphics_core.v` DEPENDS ON: gpu_graphics_vram.v, gpu_graphics_palette.v, gpu_graphics_registers.v, gpu_pixel_renderer.v
- `gpu_pixel_renderer.v` DEPENDS ON: gpu_graphics_vram.v (read port), gpu_graphics_palette.v (lookup)
- `gpu_mux.v` DEPENDS ON: gpu_core.v (character), gpu_graphics_core.v (graphics), DISPLAY_MODE register

### External Interfaces
- **CPU Bus**: 8-bit data, 8-bit address (offset within GPU space), we/re signals
- **Video Output**: RGB888 (24-bit), hsync, vsync from vga_timing_generator
- **Interrupt**: VBlank interrupt wire to CPU interrupt controller

---

## Open Questions for /speckit.clarify (if needed)

No clarifications needed at this stage. All technical unknowns will be resolved in Phase 0 research.

---

## Appendix: Design Alternatives Considered

### Alternative 1: External SDRAM for VRAM
- **Rejected**: Adds complexity, requires SDRAM controller, violates "Simplicity Over Performance"
- **Chosen**: Block RAM within FPGA (simpler, faster, sufficient capacity)

### Alternative 2: RGB555 Palette Format
- **Rejected**: Only 1 bit left for alpha channel (insufficient for future sprite feature)
- **Chosen**: RGB444 reserves 4 bits for alpha (better future extensibility)

### Alternative 3: Unified Character/Graphics GPU
- **Rejected**: Mixing modes complicates testing and increases risk
- **Chosen**: Separate graphics GPU with output multiplexer (modular, testable independently)

### Alternative 4: Hardware Blitter for Fills
- **Rejected**: Out of scope for MVP, can be added later
- **Chosen**: CPU-driven burst writes (simpler, sufficient for initial graphics)

---

*This plan follows the RetroCPU Constitution principles of Test-Driven Design, Simplicity Over Performance, Module Reusability, Educational Clarity, and Open Source Tooling.*
