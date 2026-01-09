# Feature Specification: Graphics Mode GPU with VRAM

**Feature Branch**: `005-graphics-gpu`
**Created**: 2026-01-04
**Status**: Draft
**Input**: User description: "Implement a register-based graphics processing unit (GPU) with 32KB dedicated VRAM using FPGA block RAM, supporting multiple bit-depths and hardware page flipping"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single-Page Graphics Display (Priority: P1)

A developer writes a bitmap image to VRAM and displays it on screen in a single graphics mode. This is the foundational capability that proves the GPU can accept pixel data and render it correctly.

**Why this priority**: This is the minimum viable product - without the ability to write and display graphics, no other features matter. This establishes the core register interface, VRAM storage, and pixel output pipeline.

**Independent Test**: Can be fully tested by writing a known test pattern (checkerboard, color bars, etc.) to VRAM via registers and verifying the display output matches the expected bitmap. Delivers immediate value by enabling basic graphics rendering.

**Acceptance Scenarios**:

1. **Given** GPU is in 320x200 monochrome mode (1 BPP), **When** developer writes bitmap data to VRAM starting at address $0000, **Then** the display shows the bitmap as a black and white image
2. **Given** GPU is in 160x200 4-color mode (2 BPP), **When** developer programs a 4-color palette and writes bitmap data, **Then** the display shows the bitmap using the programmed colors
3. **Given** GPU is in 160x100 16-color mode (4 BPP), **When** developer programs a 16-color palette and writes bitmap data, **Then** the display shows the bitmap using all 16 colors correctly
4. **Given** VRAM contains a test pattern, **When** developer changes GPU_MODE register, **Then** display reinterprets the same VRAM data according to the new bit-depth mode

---

### User Story 2 - Efficient Bulk Data Transfer (Priority: P2)

A developer transfers a complete framebuffer from CPU memory to VRAM quickly enough for interactive graphics updates. This requires burst write mode to avoid the overhead of setting the address for every byte.

**Why this priority**: Without efficient bulk transfer, graphics updates would be too slow for games or animations. This is essential for practical use but depends on the basic display capability from P1.

**Independent Test**: Can be tested by measuring the time to write an 8KB framebuffer and verifying it completes within acceptable performance bounds (e.g., within one frame period). Delivers value by enabling full-screen graphics updates.

**Acceptance Scenarios**:

1. **Given** burst mode is disabled, **When** developer writes VRAM_ADDR_LO/HI for each byte written to VRAM_DATA, **Then** VRAM address must be explicitly set for each write operation
2. **Given** developer sets VRAM_ADDR to $0000 and enables burst mode, **When** developer writes 100 consecutive bytes to VRAM_DATA, **Then** VRAM address auto-increments from $0000 to $0063 (99 decimal)
3. **Given** burst mode is enabled, **When** developer writes an entire 8KB framebuffer, **Then** the transfer completes using only one address setup operation plus 8000 data writes
4. **Given** VRAM address is at end of a scanline, **When** burst write continues, **Then** address automatically advances to the start of the next scanline

---

### User Story 3 - Page Flipping for Tear-Free Animation (Priority: P3)

A developer renders animation frames to an off-screen VRAM page while a different page displays, then flips to the new page during vertical blanking to avoid tearing. This enables smooth animation and double-buffering.

**Why this priority**: Page flipping is critical for professional-quality graphics, but it requires both basic display (P1) and efficient writes (P2) to be useful. It's the final piece for game-quality graphics.

**Independent Test**: Can be tested by alternately rendering to two pages and flipping between them while verifying no screen tearing occurs and VBlank interrupt timing is correct. Delivers value by enabling smooth animations.

**Acceptance Scenarios**:

1. **Given** VRAM contains two framebuffers (page 0 at $0000, page 1 at $2000), **When** developer sets FB_BASE_ADDR to $0000, **Then** display shows page 0
2. **Given** display is showing page 0, **When** developer writes to VRAM page 1 ($2000-$3FFF), **Then** the displayed image remains stable with no visual artifacts
3. **Given** GPU enters vertical blanking period, **When** VBlank interrupt fires, **Then** GPU_STATUS register shows VBlank flag set
4. **Given** VBlank interrupt has fired, **When** developer changes FB_BASE_ADDR from $0000 to $2000, **Then** display seamlessly switches to show page 1 with no tearing
5. **Given** VBlank interrupt is enabled via GPU_IRQ_CTRL, **When** vertical blanking period starts, **Then** CPU receives interrupt signal

---

### User Story 4 - Palette Programming for Color Customization (Priority: P2)

A developer programs custom color palettes to achieve specific artistic styles or technical requirements (e.g., matching period-accurate game colors, creating visual themes).

**Why this priority**: Palette control is essential for practical use of 2 BPP and 4 BPP modes, but it depends on basic display functionality. The ability to customize colors distinguishes this from a fixed-palette system.

**Independent Test**: Can be tested by programming specific RGB444 values into palette entries and verifying displayed colors match the specified values. Delivers value by enabling full color customization.

**Acceptance Scenarios**:

1. **Given** GPU is in 4 BPP mode, **When** developer sets CLUT_INDEX to 0 and writes CLUT_DATA_R=$F, CLUT_DATA_G=$0, CLUT_DATA_B=$0, **Then** palette entry 0 becomes bright red
2. **Given** palette has been programmed, **When** developer writes pixel data using palette index 5, **Then** display shows the color defined in palette entry 5
3. **Given** display is showing an image, **When** developer changes a palette entry (e.g., CLUT_INDEX=3 to new RGB values), **Then** all pixels using that palette index immediately change color
4. **Given** palette entry 7 is set to RGB444 values $8A5, **When** GPU outputs the color to display, **Then** RGB444 values are expanded to RGB888 by duplicating bits: R=$88, G=$AA, B=$55

---

### Edge Cases

- What happens when VRAM_ADDR is set to address >32767 (beyond VRAM size)? System should wrap address to stay within 32KB range ($0000-$7FFF)
- What happens when burst mode writes past the end of VRAM ($7FFF)? Address should wrap to $0000 and continue
- What happens when FB_BASE_ADDR points to an address that would cause framebuffer to extend beyond VRAM end? Display should wrap around to beginning of VRAM
- What happens when CPU writes to VRAM while GPU is reading same address for display? Dual-port RAM architecture ensures CPU writes never corrupt GPU reads - writes appear on next frame
- What happens when developer programs invalid CLUT_INDEX values (>15)? System should ignore writes to invalid indices or mask to valid range (index & $0F)
- What happens when GPU_MODE is changed mid-frame? Display may show visual glitches until next frame; recommend mode changes during VBlank only
- What happens when palette is not programmed after reset? System should provide sensible defaults (e.g., grayscale ramp or basic primary colors)

## Requirements *(mandatory)*

### Functional Requirements

#### VRAM Storage and Access

- **FR-001**: System MUST provide 32KB of dedicated video RAM implemented using FPGA block RAM (not external SDRAM)
- **FR-002**: VRAM MUST be organized as dual-port RAM with one read port for pixel display (GPU clock domain) and one write port for CPU access (CPU clock domain)
- **FR-003**: System MUST provide memory-mapped registers for CPU to set VRAM address pointer via 16-bit VRAM_ADDR_LO and VRAM_ADDR_HI registers
- **FR-004**: System MUST provide VRAM_DATA register for CPU to read/write bytes at current VRAM address
- **FR-005**: System MUST provide VRAM_CTRL register to enable/disable burst mode and auto-increment functionality

#### Graphics Modes and Display

- **FR-006**: System MUST support three graphics modes selectable via GPU_MODE register:
  - 1 BPP: 320x200 monochrome (8,000 bytes per framebuffer)
  - 2 BPP: 160x200 with 4 colors from palette (8,000 bytes per framebuffer)
  - 4 BPP: 160x100 with 16 colors from palette (8,000 bytes per framebuffer)
- **FR-007**: All graphics modes MUST align scanlines on byte boundaries (no sub-byte pixel addressing)
- **FR-008**: System MUST provide FB_BASE_ADDR_LO and FB_BASE_ADDR_HI registers (16-bit) to set which VRAM address is used as framebuffer start for display
- **FR-009**: GPU MUST continuously read pixel data from VRAM starting at FB_BASE_ADDR and convert to output pixels according to GPU_MODE setting

#### Burst Write Mode

- **FR-010**: When burst mode is enabled in VRAM_CTRL, successive writes to VRAM_DATA MUST auto-increment VRAM_ADDR
- **FR-011**: When burst mode is disabled, VRAM_ADDR MUST remain unchanged after VRAM_DATA writes (require explicit address updates)
- **FR-012**: Burst mode auto-increment MUST support line wrapping to advance to next scanline start when reaching scanline end

#### Color Palette (CLUT)

- **FR-013**: System MUST provide 16-entry color lookup table (palette) for use in 2 BPP and 4 BPP modes
- **FR-014**: Each palette entry MUST store 12-bit RGB444 color (4 bits red, 4 bits green, 4 bits blue)
- **FR-015**: System MUST provide CLUT_INDEX register to select palette entry for programming (0-15)
- **FR-016**: System MUST provide CLUT_DATA_R, CLUT_DATA_G, CLUT_DATA_B registers to set red, green, blue components of selected palette entry
- **FR-017**: GPU MUST expand RGB444 palette colors to RGB888 output by duplicating bits (e.g., 4-bit value $A becomes 8-bit value $AA)
- **FR-018**: Palette changes MUST take effect immediately on displayed pixels

#### Vertical Blanking and Interrupts

- **FR-019**: GPU MUST generate vertical blanking (VBlank) signal at start of vertical retrace period
- **FR-020**: System MUST provide GPU_STATUS register with readable VBlank flag indicating VBlank period
- **FR-021**: System MUST provide GPU_IRQ_CTRL register to enable/disable VBlank interrupt to CPU
- **FR-022**: When VBlank interrupt is enabled, GPU MUST assert interrupt signal to CPU at start of VBlank period

#### Page Flipping

- **FR-023**: CPU MUST be able to write to any VRAM address via VRAM_ADDR registers independent of FB_BASE_ADDR setting
- **FR-024**: Changing FB_BASE_ADDR MUST immediately change which VRAM region is displayed (allow multiple 8KB pages within 32KB VRAM)
- **FR-025**: System MUST support at least 4 framebuffer pages in 32KB VRAM (page 0: $0000, page 1: $2000, page 2: $4000, page 3: $6000)

### Key Entities

- **VRAM (Video RAM)**: 32KB linear address space ($0000-$7FFF) storing pixel data, accessible via address pointer and data registers. Contains multiple 8KB framebuffer pages.
- **Framebuffer Page**: 8KB region of VRAM containing pixel data for one complete screen image. Up to 4 pages fit in 32KB VRAM.
- **Color Palette (CLUT)**: 16-entry lookup table mapping pixel values (in 2 BPP and 4 BPP modes) to RGB444 colors. Each entry has independent R, G, B components.
- **VRAM Address Pointer**: 16-bit register pair (VRAM_ADDR_LO/HI) pointing to current read/write location in VRAM. Auto-increments in burst mode.
- **Framebuffer Base Address**: 16-bit register pair (FB_BASE_ADDR_LO/HI) pointing to start of framebuffer currently displayed on screen. Enables page flipping.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developer can write an 8KB framebuffer to VRAM using burst mode in under 100 milliseconds (sufficient for 10+ frames per second full-screen updates)
- **SC-002**: Display correctly shows bitmap images in all three graphics modes (1 BPP, 2 BPP, 4 BPP) with visual accuracy verified by test patterns
- **SC-003**: Page flipping between two VRAM pages completes with zero visible tearing when triggered during VBlank period
- **SC-004**: Palette color changes take effect within one video frame (16.7ms at 60Hz) of register write
- **SC-005**: VRAM implementation consumes less than 5% of available FPGA block RAM resources (32KB out of 896KB = 3.6%)
- **SC-006**: VBlank interrupt fires with timing accuracy within ±1 scanline of actual vertical retrace start
- **SC-007**: Developer can render smooth animations at 30+ frames per second using double-buffered page flipping
- **SC-008**: All RGB444 palette colors expand correctly to display with no visible color banding or artifacts

### Assumptions

- Display output operates at standard video timings (e.g., 640x480@60Hz VGA or equivalent) with graphics modes scaled/centered as needed
- CPU has sufficient performance to transfer 8KB within frame period when needed (6502-compatible timing)
- System already has working display output infrastructure (HDMI/DVI transmitter or VGA DAC)
- Power-on reset initializes all GPU registers to safe default values
- CPU memory map has available I/O address space for GPU registers (e.g., $C100-$C1FF range)
- FPGA synthesis tools support dual-port block RAM with clock domain crossing
