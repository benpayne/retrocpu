; Solid blue screen test
; Fill entire screen with palette entry 3 (pure blue)
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

    ; Fill entire screen with $33 (both pixels = palette entry 3 = blue)
    LDX #0
    LDY #0
fill_loop:
    LDA #$33
    STA GPU_VRAM_DATA
    INX
    BNE fill_loop
    INY
    CPY #32             ; 8000 bytes / 256 ~= 32
    BNE fill_loop

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

forever:
    JMP forever
