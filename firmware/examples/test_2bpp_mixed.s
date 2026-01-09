; 2 BPP mode test - mixed colors (multi-channel)
; Test: Cyan, Magenta, Yellow, White
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

    ; Palette entry 0: Cyan (Green + Blue)
    LDA #$00
    STA GPU_CLUT_INDEX
    LDA #$00
    STA GPU_CLUT_DATA_R
    LDA #$0F
    STA GPU_CLUT_DATA_G
    LDA #$0F
    STA GPU_CLUT_DATA_B

    ; Palette entry 1: Magenta (Red + Blue)
    LDA #$01
    STA GPU_CLUT_INDEX
    LDA #$0F
    STA GPU_CLUT_DATA_R
    LDA #$00
    STA GPU_CLUT_DATA_G
    LDA #$0F
    STA GPU_CLUT_DATA_B

    ; Palette entry 2: Yellow (Red + Green)
    LDA #$02
    STA GPU_CLUT_INDEX
    LDA #$0F
    STA GPU_CLUT_DATA_R
    LDA #$0F
    STA GPU_CLUT_DATA_G
    LDA #$00
    STA GPU_CLUT_DATA_B

    ; Palette entry 3: White (Red + Green + Blue)
    LDA #$03
    STA GPU_CLUT_INDEX
    LDA #$0F
    STA GPU_CLUT_DATA_R
    LDA #$0F
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
    ; Bar pattern: $00, $55, $AA, $FF

    LDY #0              ; Scanline counter (0-199)

scanline_loop:
    ; Bar 1: Cyan (10 bytes of $00)
    LDA #$00
    LDX #10
bar1_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE bar1_loop

    ; Bar 2: Magenta (10 bytes of $55)
    LDA #$55
    LDX #10
bar2_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE bar2_loop

    ; Bar 3: Yellow (10 bytes of $AA)
    LDA #$AA
    LDX #10
bar3_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE bar3_loop

    ; Bar 4: White (10 bytes of $FF)
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
