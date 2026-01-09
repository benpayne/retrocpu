; 2 BPP mode test - 4 vertical color bars
; 2 BPP: 160×200, 4 colors, 4 pixels/byte
; 40 bytes per scanline, 200 scanlines
.setcpu "6502"

GPU_VRAM_ADDR_LO  = $C100
GPU_VRAM_ADDR_HI  = $C101
GPU_VRAM_DATA     = $C102
GPU_VRAM_CTRL     = $C103
GPU_MODE          = $C106
GPU_CLUT_INDEX    = $C107
GPU_CLUT_DATA_R   = $C108
GPU_CLUT_DATA_G   = $C109
GPU_CLUT_DATA_B   = $C10A
GPU_DISPLAY_MODE  = $C10D

.org $0300

start:
    CLD

    ; Palette entry 0: Black
    LDA #$00
    STA GPU_CLUT_INDEX
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Palette entry 1: Red
    LDA #$01
    STA GPU_CLUT_INDEX
    LDA #$0F
    STA GPU_CLUT_DATA_R
    LDA #$00
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Palette entry 2: Green
    LDA #$02
    STA GPU_CLUT_INDEX
    LDA #$00
    STA GPU_CLUT_DATA_R
    LDA #$0F
    STA GPU_CLUT_DATA_G
    LDA #$00
    STA GPU_CLUT_DATA_B

    ; Palette entry 3: Blue
    LDA #$03
    STA GPU_CLUT_INDEX
    LDA #$00
    STA GPU_CLUT_DATA_R
    LDA #$00
    STA GPU_CLUT_DATA_G
    LDA #$0F
    STA GPU_CLUT_DATA_B

    ; Set 2 BPP mode
    LDA #$01
    STA GPU_MODE

    ; Enable burst mode
    LDA #$01
    STA GPU_VRAM_CTRL

    ; Set VRAM address to start
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    ; Fill screen with 4 vertical bars
    ; Each bar is 40 pixels wide = 10 bytes in 2BPP mode
    ; Scanline: 40 bytes total
    ; Bar pattern in 2BPP (2 bits per pixel, 4 pixels per byte):
    ;   Color 0: %00_00_00_00 = $00
    ;   Color 1: %01_01_01_01 = $55
    ;   Color 2: %10_10_10_10 = $AA
    ;   Color 3: %11_11_11_11 = $FF

    LDY #0              ; Scanline counter (0-199)

scanline_loop:
    ; Bar 1: Black (10 bytes of $00)
    LDA #$00
    LDX #10
bar1_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE bar1_loop

    ; Bar 2: Red (10 bytes of $55)
    LDA #$55
    LDX #10
bar2_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE bar2_loop

    ; Bar 3: Green (10 bytes of $AA)
    LDA #$AA
    LDX #10
bar3_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE bar3_loop

    ; Bar 4: Blue (10 bytes of $FF)
    LDA #$FF
    LDX #10
bar4_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE bar4_loop

    ; Next scanline
    INY
    CPY #200
    BNE scanline_loop

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

forever:
    JMP forever
