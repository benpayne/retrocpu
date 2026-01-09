; Simple RGB bars test - 3 wide vertical bars
; 4 BPP mode: 160×100
; Each bar is about 53 pixels wide (26-27 bytes)
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

    ; Palette entry 1: PURE RED
    LDA #$01
    STA GPU_CLUT_INDEX
    LDA #$0F
    STA GPU_CLUT_DATA_R
    LDA #$00
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Palette entry 2: PURE GREEN
    LDA #$02
    STA GPU_CLUT_INDEX
    LDA #$00
    STA GPU_CLUT_DATA_R
    LDA #$0F
    STA GPU_CLUT_DATA_G
    LDA #$00
    STA GPU_CLUT_DATA_B

    ; Palette entry 3: PURE BLUE
    LDA #$03
    STA GPU_CLUT_INDEX
    LDA #$00
    STA GPU_CLUT_DATA_R
    LDA #$00
    STA GPU_CLUT_DATA_G
    LDA #$0F
    STA GPU_CLUT_DATA_B

    ; Set 4 BPP mode
    LDA #$02
    STA GPU_MODE

    ; Enable burst mode
    LDA #$01
    STA GPU_VRAM_CTRL

    ; Set VRAM address to start
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    ; Fill screen: 3 vertical bars
    ; 80 bytes per scanline, 100 scanlines
    ; Bar 1 (RED):   bytes 0-26   (27 bytes = 54 pixels)
    ; Bar 2 (GREEN): bytes 27-53  (27 bytes = 54 pixels)
    ; Bar 3 (BLUE):  bytes 54-79  (26 bytes = 52 pixels)

    LDY #0              ; Scanline counter

scanline_loop:
    ; Write bar 1: RED (27 bytes of $11)
    LDA #$11
    LDX #27
bar1_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE bar1_loop

    ; Write bar 2: GREEN (27 bytes of $22)
    LDA #$22
    LDX #27
bar2_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE bar2_loop

    ; Write bar 3: BLUE (26 bytes of $33)
    LDA #$33
    LDX #26
bar3_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE bar3_loop

    ; Next scanline
    INY
    CPY #100
    BNE scanline_loop

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

forever:
    JMP forever
