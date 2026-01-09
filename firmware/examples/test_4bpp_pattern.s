; 4 BPP mode test - repeating pattern to check alignment
; Fill with pattern: $01, $23, $45, $67, $89, $AB, $CD, $EF (repeating)
; This gives us: color 0,1 then 2,3 then 4,5 then 6,7 then 8,9 then A,B then C,D then E,F
; With distinct colors we can see exactly where each pixel lands
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

    ; Set up 16-color palette - each color distinct
    LDX #0
palette_loop:
    TXA
    STA GPU_CLUT_INDEX

    ; Simple gradient palette
    ; R = index & 0x0C (bits 3:2)
    ; G = index & 0x03 shifted (bits 1:0)
    ; B = index & 0x0C shifted (bits 3:2)

    TXA
    AND #$0C
    STA GPU_CLUT_DATA_R

    TXA
    AND #$03
    ASL A
    ASL A
    STA GPU_CLUT_DATA_G

    TXA
    AND #$0C
    STA GPU_CLUT_DATA_B

    INX
    CPX #16
    BNE palette_loop

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

    ; Fill screen with repeating pattern
    ; Pattern: $01, $23, $45, $67, $89, $AB, $CD, $EF
    LDY #0              ; Scanline counter

scanline_loop:
    ; Write pattern 10 times per line (80 bytes / 8 = 10)
    LDX #10
pattern_loop:
    LDA #$01
    STA GPU_VRAM_DATA
    LDA #$23
    STA GPU_VRAM_DATA
    LDA #$45
    STA GPU_VRAM_DATA
    LDA #$67
    STA GPU_VRAM_DATA
    LDA #$89
    STA GPU_VRAM_DATA
    LDA #$AB
    STA GPU_VRAM_DATA
    LDA #$CD
    STA GPU_VRAM_DATA
    LDA #$EF
    STA GPU_VRAM_DATA

    DEX
    BNE pattern_loop

    INY
    CPY #100
    BNE scanline_loop

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

forever:
    JMP forever
