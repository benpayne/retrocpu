# Graphics GPU Firmware Tests

This directory contains firmware test programs for the Graphics Mode GPU feature.

## Test Programs

### 1. gpu_test_1bpp.s - 1 BPP Checkerboard Test

**Purpose**: Tests basic graphics functionality in 1 BPP (monochrome) mode

**What it does**:
- Programs a 2-color palette (black and white)
- Fills VRAM with alternating checkerboard pattern ($AA / $55)
- Switches to graphics display mode
- Should display a black and white checkerboard pattern on screen

**Build & Run**:
```bash
ca65 gpu_test_1bpp.s -o gpu_test_1bpp.o
ld65 gpu_test_1bpp.o -C <linker_config> -o gpu_test_1bpp.bin
# Upload to FPGA via program loader
```

**Expected Result**: Full-screen checkerboard pattern (alternating black/white pixels)

---

### 2. gpu_test_4bpp.s - 4 BPP Color Bars Test

**Purpose**: Tests advanced graphics with 16-color palette in 4 BPP mode

**What it does**:
- Programs all 16 palette entries with rainbow colors:
  - 0: Black, 1: Dark Red, 2: Red, 3: Orange
  - 4: Yellow, 5: Yellow-Green, 6: Green, 7: Cyan
  - 8: Light Blue, 9: Blue, 10: Purple, 11: Magenta
  - 12: Pink, 13: Gray, 14: Light Gray, 15: White
- Draws 16 vertical color bars (10 pixels wide each)
- Switches to graphics display mode

**Build & Run**:
```bash
ca65 gpu_test_4bpp.s -o gpu_test_4bpp.o
ld65 gpu_test_4bpp.o -C <linker_config> -o gpu_test_4bpp.bin
# Upload to FPGA via program loader
```

**Expected Result**: 16 vertical rainbow color bars across the screen

---

### 3. gpu_test_interactive.s - Interactive Mode Switcher

**Purpose**: Interactive test allowing real-time mode switching via keyboard

**What it does**:
- Waits for keyboard input via UART
- Responds to commands:
  - `1` - Switch to 1 BPP mode with checkerboard
  - `2` - Switch to 2 BPP mode with gradient
  - `4` - Switch to 4 BPP mode with vertical gradient
  - `C` - Return to character mode (text display)
  - `G` - Return to graphics mode
  - `X` - Clear VRAM (fill with $00)

**Build & Run**:
```bash
ca65 gpu_test_interactive.s -o gpu_test_interactive.o
ld65 gpu_test_interactive.o -C <linker_config> -o gpu_test_interactive.bin
# Upload to FPGA via program loader
# Use serial terminal to send commands
```

**Expected Result**: Interactive switching between modes and patterns

---

## GPU Register Map

All GPU registers are at base address `$C100`:

| Offset | Name | Access | Description |
|--------|------|--------|-------------|
| $C100 | VRAM_ADDR_LO | RW | VRAM address pointer low byte |
| $C101 | VRAM_ADDR_HI | RW | VRAM address pointer high byte (15-bit) |
| $C102 | VRAM_DATA | RW | VRAM data read/write |
| $C103 | VRAM_CTRL | RW | VRAM control (bit 0: burst mode) |
| $C104 | FB_BASE_LO | RW | Framebuffer base address low byte |
| $C105 | FB_BASE_HI | RW | Framebuffer base address high byte |
| $C106 | GPU_MODE | RW | Graphics mode (00=1BPP, 01=2BPP, 10=4BPP) |
| $C107 | CLUT_INDEX | RW | Color palette index (0-15) |
| $C108 | CLUT_DATA_R | RW | Palette red component (4-bit) |
| $C109 | CLUT_DATA_G | RW | Palette green component (4-bit) |
| $C10A | CLUT_DATA_B | RW | Palette blue component (4-bit) |
| $C10B | GPU_STATUS | RO | GPU status (bit 0: VBlank) |
| $C10C | GPU_IRQ_CTRL | RW | Interrupt control (bit 0: VBlank IRQ enable) |
| $C10D | DISPLAY_MODE | RW | Display mode (0=character, 1=graphics) |

## Graphics Modes

### 1 BPP Mode (MODE_1BPP = $00)
- Resolution: 320x200 pixels
- Colors: 2 (palette indices 0-1)
- VRAM: 8,000 bytes (40 bytes per row × 200 rows)
- Encoding: 8 pixels per byte, MSB first
- Byte $AA = 10101010 = alternating black/white pixels

### 2 BPP Mode (MODE_2BPP = $01)
- Resolution: 160x200 pixels
- Colors: 4 (palette indices 0-3)
- VRAM: 8,000 bytes (40 bytes per row × 200 rows)
- Encoding: 4 pixels per byte, 2 bits per pixel, MSB first
- Byte $E4 = 11100100 = pixels with colors 3,2,1,0

### 4 BPP Mode (MODE_4BPP = $02)
- Resolution: 160x100 pixels
- Colors: 16 (palette indices 0-15)
- VRAM: 8,000 bytes (80 bytes per row × 100 rows)
- Encoding: 2 pixels per byte, 4 bits per pixel, MSB first
- Byte $A5 = 10100101 = two pixels with colors 10 and 5

## Burst Mode

For efficient VRAM writes, enable burst mode:

```assembly
; Enable burst mode
LDA #$01
STA GPU_VRAM_CTRL

; Set starting address
LDA #$00
STA GPU_VRAM_ADDR_LO
STA GPU_VRAM_ADDR_HI

; Write bytes - address auto-increments after each write
LDA #$AA
STA GPU_VRAM_DATA  ; Writes to $0000, addr becomes $0001
LDA #$55
STA GPU_VRAM_DATA  ; Writes to $0001, addr becomes $0002
; ... continue writing

; Disable burst mode when done
LDA #$00
STA GPU_VRAM_CTRL
```

## Palette Programming

RGB444 palette with 16 entries (indices 0-15):

```assembly
; Program palette entry 5 to bright yellow (R=15, G=15, B=0)
LDA #$05        ; Select palette index 5
STA GPU_CLUT_INDEX

LDA #$0F        ; Red = 15 (max)
STA GPU_CLUT_DATA_R

LDA #$0F        ; Green = 15 (max)
STA GPU_CLUT_DATA_G

LDA #$00        ; Blue = 0
STA GPU_CLUT_DATA_B
```

RGB444 values are expanded to RGB888 by bit duplication:
- $0 → $00 (0)
- $F → $FF (255)
- $8 → $88 (136)
- $A → $AA (170)

## Debugging Tips

1. **No display**: Check that DISPLAY_MODE is set to $01 (graphics mode)
2. **Wrong colors**: Verify palette programming with correct indices
3. **Garbled image**: Ensure correct GPU_MODE for your data format
4. **Partial image**: Check that full 8,000 bytes were written to VRAM
5. **Tearing**: Use VBlank status (GPU_STATUS bit 0) to sync updates

## Hardware Testing Procedure

1. **Upload firmware**: Use XMODEM program loader to upload `.bin` file
2. **Monitor startup**: Watch for any boot failures via serial console
3. **Verify display**: Check that graphics appear on connected display
4. **Test interactions**: For interactive test, send keyboard commands via UART
5. **Check timing**: Verify smooth display without tearing or artifacts

## Success Criteria

- ✅ Checkerboard pattern appears correctly in 1 BPP mode
- ✅ Color bars display with correct colors in 4 BPP mode
- ✅ Mode switching works without glitches
- ✅ Display is stable with no flickering or tearing
- ✅ All 16 palette colors are distinguishable

## Troubleshooting

If tests fail on hardware:
1. Check synthesis logs for timing violations
2. Verify block RAM usage (should use ECP5 EBR)
3. Check clock domain crossing constraints
4. Verify DVI/VGA output timing
5. Test with waveform viewer in simulation first

## References

- Feature Spec: `/specs/004-program-loader-io-config/spec.md`
- Hardware Modules: `/rtl/peripherals/video/gpu_graphics_*.v`
- Integration Test: `/tests/integration/test_gpu_graphics_framebuffer.py`
