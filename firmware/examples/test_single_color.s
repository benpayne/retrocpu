; Single color test - fill screen with solid color to test RGB channels
; User can run this multiple times with different colors
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

    ; Set up palette entry 0 (black)
    LDA #$00
    STA GPU_CLUT_INDEX
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Set up palette entry 1 (PURE RED - test red channel)
    LDA #$01
    STA GPU_CLUT_INDEX
    LDA #$0F          ; Red = MAX
    STA GPU_CLUT_DATA_R
    LDA #$00          ; Green = 0
    STA GPU_CLUT_DATA_G
    LDA #$00          ; Blue = 0
    STA GPU_CLUT_DATA_B

    ; Set 1 BPP mode
    LDA #$00
    STA GPU_MODE

    ; Enable burst mode
    LDA #$01
    STA GPU_VRAM_CTRL

    ; Set VRAM address to start
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    ; Fill screen with all 1's (palette entry 1 = red)
    LDX #0
    LDY #0
fill_loop:
    LDA #$FF            ; All pixels = color 1 (red)
    STA GPU_VRAM_DATA
    INX
    BNE fill_loop
    INY
    CPY #32             ; 8000 bytes / 256 = 31.25, so 32 iterations
    BNE fill_loop

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

forever:
    JMP forever
