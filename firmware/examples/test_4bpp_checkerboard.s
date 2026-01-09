; 4 BPP mode test - checkerboard pattern (1-pixel squares)
; Alternating black/white on each line
; Even rows: $01 (black, white, black, white...)
; Odd rows:  $10 (white, black, white, black...)
.setcpu "6502"

; Graphics GPU registers
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

    ; Set up palette
    ; Color 0: Black
    LDA #$00
    STA GPU_CLUT_INDEX
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Color 1: White
    LDA #$01
    STA GPU_CLUT_INDEX
    LDA #$0F
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
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

    ; Fill screen with checkerboard
    LDY #0              ; Scanline counter (0-99)

scanline_loop:
    ; Check if Y is even or odd
    TYA
    AND #$01            ; Test bit 0
    BNE odd_row

even_row:
    ; Even row: pattern $01 (black, white pixels)
    LDX #80
    LDA #$01
even_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE even_loop
    JMP next_row

odd_row:
    ; Odd row: pattern $10 (white, black pixels)
    LDX #80
    LDA #$10
odd_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE odd_loop

next_row:
    INY
    CPY #100
    BNE scanline_loop

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

forever:
    JMP forever
