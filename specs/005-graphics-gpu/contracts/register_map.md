# Register Map Contract: Graphics GPU

**Feature**: 005-graphics-gpu
**Base Address**: 0xC100-0xC10F
**Date**: 2026-01-04

This document defines the complete register interface for the Graphics Mode GPU.

---

## Register Summary Table

| Address | Name          | Access | Reset | Description |
|---------|---------------|--------|-------|-------------|
| 0xC100  | VRAM_ADDR_LO  | RW     | 0x00  | VRAM address pointer low byte |
| 0xC101  | VRAM_ADDR_HI  | RW     | 0x00  | VRAM address pointer high byte (bits 6:0) |
| 0xC102  | VRAM_DATA     | RW     | 0x00  | VRAM data read/write at current address |
| 0xC103  | VRAM_CTRL     | RW     | 0x00  | VRAM control (bit 0: burst mode) |
| 0xC104  | FB_BASE_LO    | RW     | 0x00  | Framebuffer base address low byte |
| 0xC105  | FB_BASE_HI    | RW     | 0x00  | Framebuffer base address high byte (bits 6:0) |
| 0xC106  | GPU_MODE      | RW     | 0x00  | Graphics mode select (bits 1:0) |
| 0xC107  | CLUT_INDEX    | RW     | 0x00  | Palette index (bits 3:0) |
| 0xC108  | CLUT_DATA_R   | RW     | 0x00  | Palette red component (bits 3:0) |
| 0xC109  | CLUT_DATA_G   | RW     | 0x00  | Palette green component (bits 3:0) |
| 0xC10A  | CLUT_DATA_B   | RW     | 0x00  | Palette blue component (bits 3:0) |
| 0xC10B  | GPU_STATUS    | RO     | 0x00  | GPU status (bit 0: VBlank) |
| 0xC10C  | GPU_IRQ_CTRL  | RW     | 0x00  | Interrupt control (bit 0: VBlank enable) |
| 0xC10D  | DISPLAY_MODE  | RW     | 0x00  | Display mode (bit 0: Char=0/Gfx=1) |
| 0xC10E  | Reserved      | --     | 0x00  | Reserved for future use |
| 0xC10F  | Reserved      | --     | 0x00  | Reserved for future use |

---

## Detailed Register Specifications

### 0xC100 - VRAM_ADDR_LO (VRAM Address Pointer Low Byte)

**Access**: Read/Write
**Reset Value**: 0x00

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
       A7   A6   A5   A4   A3   A2   A1   A0
```

**Description**:
- Contains bits [7:0] of the 15-bit VRAM address pointer
- Combined with VRAM_ADDR_HI to form full 15-bit address ($0000-$7FFF)
- Points to current read/write location in VRAM

**Write Behavior**:
- Updates low byte of address pointer immediately
- Does not trigger VRAM access

**Read Behavior**:
- Returns current value of low byte

**Example**:
```
Write $34 to VRAM_ADDR_LO, $12 to VRAM_ADDR_HI → Address pointer = $1234
```

---

### 0xC101 - VRAM_ADDR_HI (VRAM Address Pointer High Byte)

**Access**: Read/Write
**Reset Value**: 0x00

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
        0   A14  A13  A12  A11  A10   A9   A8
```

**Description**:
- Contains bits [14:8] of the 15-bit VRAM address pointer
- Bit 7 is unused (VRAM is 32KB, not 64KB)
- Maximum valid value: 0x7F (32767 in decimal, $7FFF as full address)

**Write Behavior**:
- Updates high byte of address pointer immediately
- Bit 7 is ignored (always reads back as 0)

**Read Behavior**:
- Returns bits [6:0], bit 7 always reads 0

**Constraints**:
- Writing values >0x7F has no effect on bit 7 (masked to 7 bits)

---

### 0xC102 - VRAM_DATA (VRAM Data Register)

**Access**: Read/Write
**Reset Value**: 0x00

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
       D7   D6   D5   D4   D3   D2   D1   D0
```

**Description**:
- Reads or writes a byte from/to VRAM at the address specified by VRAM_ADDR
- If burst mode enabled (VRAM_CTRL bit 0 = 1), address auto-increments after access

**Write Behavior**:
1. Write data byte to VRAM at current address (VRAM_ADDR_HI:VRAM_ADDR_LO)
2. If burst mode enabled, increment VRAM_ADDR with wraparound at $7FFF → $0000
3. If burst mode disabled, VRAM_ADDR unchanged

**Read Behavior**:
1. Read data byte from VRAM at current address
2. If burst mode enabled, increment VRAM_ADDR with wraparound
3. If burst mode disabled, VRAM_ADDR unchanged

**Timing**:
- Write completes in 1 CPU clock cycle (block RAM single-cycle write)
- Read completes in 1 CPU clock cycle (registered output)

**Example Usage** (Burst Write):
```assembly
LDA #$00
STA $C100       ; VRAM_ADDR_LO = $00
STA $C101       ; VRAM_ADDR_HI = $00 (address = $0000)
LDA #$01
STA $C103       ; Enable burst mode

LDA #$AA
STA $C102       ; Write $AA to $0000, increment to $0001
LDA #$BB
STA $C102       ; Write $BB to $0001, increment to $0002
; ... continue writing bytes
```

---

### 0xC103 - VRAM_CTRL (VRAM Control Register)

**Access**: Read/Write
**Reset Value**: 0x00

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
        0    0    0    0    0    0    0  BURST
```

**Field Descriptions**:

**Bit 0 - BURST (Burst Mode Enable)**:
- 0: Burst mode disabled (manual address updates required)
- 1: Burst mode enabled (auto-increment VRAM_ADDR on VRAM_DATA access)

**Bits [7:1] - Reserved**:
- Read as 0
- Writes ignored

**Write Behavior**:
- Updates burst mode enable bit immediately
- Does not affect current VRAM_ADDR value

**Example**:
```
Write $01 to VRAM_CTRL → Enable burst mode
Write $00 to VRAM_CTRL → Disable burst mode
```

---

### 0xC104 - FB_BASE_LO (Framebuffer Base Address Low Byte)

**Access**: Read/Write
**Reset Value**: 0x00

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
       B7   B6   B5   B4   B3   B2   B1   B0
```

**Description**:
- Contains bits [7:0] of the 15-bit framebuffer base address
- Specifies which VRAM address is the start of the displayed framebuffer
- Used for page flipping (change during VBlank to swap buffers)

**Write Behavior**:
- Updates low byte of framebuffer base address immediately
- Takes effect on next scanline (immediate, but visible change depends on timing)

**Typical Values**:
- $00 (combined with FB_BASE_HI = $00) → Page 0 at $0000
- $00 (combined with FB_BASE_HI = $20) → Page 1 at $2000
- $00 (combined with FB_BASE_HI = $40) → Page 2 at $4000
- $00 (combined with FB_BASE_HI = $60) → Page 3 at $6000

---

### 0xC105 - FB_BASE_HI (Framebuffer Base Address High Byte)

**Access**: Read/Write
**Reset Value**: 0x00

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
        0   B14  B13  B12  B11  B10   B9   B8
```

**Description**:
- Contains bits [14:8] of the 15-bit framebuffer base address
- Bit 7 unused (same as VRAM_ADDR_HI)

**Write Behavior**:
- Updates high byte of framebuffer base address immediately
- Bit 7 ignored (masked to 7 bits)
- Recommended to update during VBlank period to avoid tearing

**Page Flip Procedure**:
```
1. Wait for VBlank interrupt (or poll GPU_STATUS bit 0)
2. Write new framebuffer base address:
   STA FB_BASE_LO
   STA FB_BASE_HI
3. Display seamlessly switches to new page
```

---

### 0xC106 - GPU_MODE (Graphics Mode Select)

**Access**: Read/Write
**Reset Value**: 0x00 (1 BPP mode)

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
        0    0    0    0    0    0   M1   M0
```

**Field Descriptions**:

**Bits [1:0] - M[1:0] (Graphics Mode)**:
- 00: 1 BPP mode (320x200 monochrome)
- 01: 2 BPP mode (160x200, 4-color palette)
- 10: 4 BPP mode (160x100, 16-color palette)
- 11: Reserved (undefined behavior)

**Bits [7:2] - Reserved**:
- Read as 0
- Writes ignored

**Mode Parameters**:

| Mode | M[1:0] | Resolution | Colors | Bytes/Row | Rows | Total Bytes |
|------|--------|------------|--------|-----------|------|-------------|
| 1 BPP| 00     | 320x200    | 2      | 40        | 200  | 8,000       |
| 2 BPP| 01     | 160x200    | 4      | 40        | 200  | 8,000       |
| 4 BPP| 10     | 160x100    | 16     | 80        | 100  | 8,000       |

**Write Behavior**:
- Mode change takes effect immediately (next scanline)
- Recommend changing during VBlank to avoid visual glitches

---

### 0xC107 - CLUT_INDEX (Palette Index Register)

**Access**: Read/Write
**Reset Value**: 0x00

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
        0    0    0    0   I3   I2   I1   I0
```

**Description**:
- Selects which palette entry (0-15) to read/write via CLUT_DATA_R/G/B registers
- Index persists until changed (can write R, then G, then B to same entry)

**Field Descriptions**:

**Bits [3:0] - I[3:0] (Palette Index)**:
- 0-15: Valid palette indices
- Indices 0-3 used in 2 BPP mode
- Indices 0-15 used in 4 BPP mode

**Bits [7:4] - Reserved**:
- Read as 0
- Writes ignored

**Example Usage**:
```assembly
LDA #$05
STA $C107      ; Select palette entry 5
LDA #$0F
STA $C108      ; Set red = 15
LDA #$00
STA $C109      ; Set green = 0
LDA #$00
STA $C10A      ; Set blue = 0
; Palette entry 5 now = bright red (RGB 0xF00)
```

---

### 0xC108 - CLUT_DATA_R (Palette Red Component)

**Access**: Read/Write
**Reset Value**: Grayscale ramp (entry N = N)

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
        0    0    0    0   R3   R2   R1   R0
```

**Description**:
- Red component (4 bits) of palette entry selected by CLUT_INDEX
- Value 0-15 (0x0-0xF)
- Expanded to 8-bit output via bit duplication: `{R[3:0], R[3:0]}`

**Write Behavior**:
- Writes to palette entry currently selected by CLUT_INDEX
- Change takes effect immediately (affects pixels on next scanline)

**Read Behavior**:
- Reads red component of currently selected palette entry

**Color Expansion Example**:
```
Red value = 0xA (1010 binary)
Expanded to 8-bit: {1010, 1010} = 0xAA (10101010 binary)
Output to DVI transmitter: red[7:0] = 0xAA (170 in decimal)
```

---

### 0xC109 - CLUT_DATA_G (Palette Green Component)

**Access**: Read/Write
**Reset Value**: Grayscale ramp (entry N = N)

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
        0    0    0    0   G3   G2   G1   G0
```

**Description**:
- Green component (4 bits) of palette entry selected by CLUT_INDEX
- Value 0-15 (0x0-0xF)
- Expanded to 8-bit output via bit duplication: `{G[3:0], G[3:0]}`

**Behavior**:
- Same as CLUT_DATA_R, but for green channel

---

### 0xC10A - CLUT_DATA_B (Palette Blue Component)

**Access**: Read/Write
**Reset Value**: Grayscale ramp (entry N = N)

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
        0    0    0    0   B3   B2   B1   B0
```

**Description**:
- Blue component (4 bits) of palette entry selected by CLUT_INDEX
- Value 0-15 (0x0-0xF)
- Expanded to 8-bit output via bit duplication: `{B[3:0], B[3:0]}`

**Behavior**:
- Same as CLUT_DATA_R, but for blue channel

**Complete Palette Write Example**:
```assembly
; Program palette entry 7 to RGB (8, 10, 5) = purple-ish
LDA #$07
STA $C107      ; CLUT_INDEX = 7
LDA #$08
STA $C108      ; Red = 8
LDA #$0A
STA $C109      ; Green = 10
LDA #$05
STA $C10A      ; Blue = 5
; Entry 7 now outputs RGB888 = (0x88, 0xAA, 0x55)
```

---

### 0xC10B - GPU_STATUS (GPU Status Register)

**Access**: Read-Only
**Reset Value**: 0x00

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
        0    0    0    0    0    0    0  VBLANK
```

**Field Descriptions**:

**Bit 0 - VBLANK (VBlank Flag)**:
- 0: Not in vertical blanking period (visible region or front porch)
- 1: In vertical blanking period (during vertical sync or back porch)

**Bits [7:1] - Reserved**:
- Read as 0

**VBlank Timing**:
- VBlank flag set when `v_count >= V_SYNC_START` (490 for 640x480@60Hz)
- VBlank flag cleared when `v_count < V_VISIBLE` (0 for 640x480@60Hz)
- Duration: Approximately 2 scanlines (~80 microseconds @ 25 MHz)

**Usage**:
```assembly
wait_vblank:
    LDA $C10B      ; Read GPU_STATUS
    AND #$01       ; Mask VBlank bit
    BEQ wait_vblank ; Loop until VBlank = 1
    ; Now in VBlank period, safe to update FB_BASE_ADDR
```

---

### 0xC10C - GPU_IRQ_CTRL (Interrupt Control Register)

**Access**: Read/Write
**Reset Value**: 0x00 (interrupts disabled)

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
        0    0    0    0    0    0    0   IRQ_EN
```

**Field Descriptions**:

**Bit 0 - IRQ_EN (VBlank Interrupt Enable)**:
- 0: VBlank interrupts disabled
- 1: VBlank interrupts enabled

**Bits [7:1] - Reserved**:
- Read as 0
- Writes ignored

**Interrupt Behavior**:
- When enabled, GPU asserts interrupt signal at start of VBlank period
- Interrupt is edge-triggered (one pulse per VBlank, rising edge of VBlank flag)
- CPU must service interrupt and clear it (typically by reading GPU_STATUS)

**Interrupt Service Routine Example**:
```assembly
vblank_isr:
    PHA            ; Save accumulator
    LDA $C10B      ; Read GPU_STATUS (acknowledge interrupt)
    ; Perform page flip or other VBlank tasks
    LDA #$00
    STA $C104      ; FB_BASE_LO
    LDA #$20
    STA $C105      ; FB_BASE_HI (flip to page 1 at $2000)
    PLA            ; Restore accumulator
    RTI            ; Return from interrupt
```

**Enabling Interrupts**:
```assembly
LDA #$01
STA $C10C      ; Enable VBlank interrupt
CLI            ; Clear CPU interrupt mask (6502 instruction)
```

---

### 0xC10D - DISPLAY_MODE (Display Mode Select)

**Access**: Read/Write
**Reset Value**: 0x00 (Character mode)

**Bit Layout**:
```
Bit:    7    6    5    4    3    2    1    0
        0    0    0    0    0    0    0   GFX_EN
```

**Field Descriptions**:

**Bit 0 - GFX_EN (Graphics Mode Enable)**:
- 0: Character mode active (output from character GPU)
- 1: Graphics mode active (output from graphics framebuffer GPU)

**Bits [7:1] - Reserved**:
- Read as 0
- Writes ignored

**Behavior**:
- Controls output multiplexer that selects between character GPU and graphics GPU
- Both GPUs run simultaneously; mux selects which output goes to DVI transmitter
- Mode change takes effect immediately (next pixel)

**Default State**:
- Power-on reset: Character mode active (backward compatible with existing software)

**Example**:
```assembly
; Switch to graphics mode
LDA #$01
STA $C10D

; Switch back to character mode
LDA #$00
STA $C10D
```

---

### 0xC10E - Reserved

**Access**: --
**Reset Value**: 0x00

Reserved for future use. Reads return 0x00, writes are ignored.

---

### 0xC10F - Reserved

**Access**: --
**Reset Value**: 0x00

Reserved for future use. Reads return 0x00, writes are ignored.

---

## Address Decoding

**GPU Register Block Detection**:
```verilog
wire gpu_graphics_sel = (addr[15:4] == 12'hC10); // Match 0xC10x
```

**Individual Register Select**:
```verilog
wire vram_addr_lo_sel  = gpu_graphics_sel && (addr[3:0] == 4'h0);
wire vram_addr_hi_sel  = gpu_graphics_sel && (addr[3:0] == 4'h1);
wire vram_data_sel     = gpu_graphics_sel && (addr[3:0] == 4'h2);
// ... and so on for all registers
```

---

## Register Access Timing

**Write Timing** (Single-Cycle Write):
```
Clock Cycle:  |   1   |   2   |   3   |
              |       |       |       |
addr ---------|=VALID=|-------|-------|
data_in ------|=VALID=|-------|-------|
we -----------|   1   |   0   |-------|
              |       |       |       |
Internal      |       | UPDATE|-------|
Register      |       |       |       |
```

**Read Timing** (Single-Cycle Read):
```
Clock Cycle:  |   1   |   2   |   3   |
              |       |       |       |
addr ---------|=VALID=|-------|-------|
re -----------|   1   |   0   |-------|
              |       |       |       |
data_out -----|-------|=VALID=|-------|
```

---

## Usage Examples

### Example 1: Fill VRAM with Solid Color (Burst Mode)

```assembly
; Fill first 8KB of VRAM with value $FF (white in 1 BPP)
LDA #$00
STA $C100       ; VRAM_ADDR_LO = $00
STA $C101       ; VRAM_ADDR_HI = $00
LDA #$01
STA $C103       ; Enable burst mode

LDX #$00        ; X = low byte counter
LDY #$1F        ; Y = high byte counter (8000 bytes = $1F40)
LDA #$FF        ; Fill value

fill_loop:
    STA $C102   ; Write to VRAM, auto-increment
    INX
    BNE fill_loop
    DEY
    BNE fill_loop
    ; Loop 8000 times, filling VRAM

LDA #$00
STA $C103       ; Disable burst mode (optional)
```

### Example 2: Animate with Page Flipping

```assembly
; Main loop: Render to off-screen page, flip on VBlank
main_loop:
    JSR render_frame_to_page1  ; Draw animation frame to page 1
    JSR wait_for_vblank        ; Wait for VBlank interrupt
    JSR flip_to_page1          ; Update FB_BASE_ADDR to page 1

    JSR render_frame_to_page0  ; Draw next frame to page 0
    JSR wait_for_vblank
    JSR flip_to_page0          ; Update FB_BASE_ADDR to page 0
    JMP main_loop

wait_for_vblank:
    LDA $C10B                  ; Read GPU_STATUS
    AND #$01                   ; Check VBlank bit
    BEQ wait_for_vblank
    RTS

flip_to_page1:
    LDA #$00
    STA $C104                  ; FB_BASE_LO = $00
    LDA #$20
    STA $C105                  ; FB_BASE_HI = $20 (address $2000)
    RTS

flip_to_page0:
    LDA #$00
    STA $C104                  ; FB_BASE_LO = $00
    STA $C105                  ; FB_BASE_HI = $00 (address $0000)
    RTS
```

---

**Register Map Complete** ✅
