; 4 BPP mode test - simple white border
; 4 BPP: 160×100, 16 colors, 2 pixels/byte
; 80 bytes/line × 100 lines = 8000 bytes
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

    ; Set up simple palette
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

    ; Fill entire screen with black first
    ; 8000 bytes = $1F40
    LDX #$00
    LDY #$00
    LDA #$00        ; Black (color 0 in both pixels)
clear_outer:
clear_inner:
    STA GPU_VRAM_DATA
    INY
    BNE clear_inner
    INX
    CPX #$20        ; 32 * 256 = 8192 bytes (more than enough)
    BNE clear_outer

    ; Now draw white border
    ; Top line (row 0): 80 bytes of white
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    LDX #80
    LDA #$11        ; White in both pixels
top_line:
    STA GPU_VRAM_DATA
    DEX
    BNE top_line

    ; Bottom line (row 99): Address = 99 * 80 = 7920 = $1EF0
    LDA #$F0
    STA GPU_VRAM_ADDR_LO
    LDA #$1E
    STA GPU_VRAM_ADDR_HI

    LDX #80
    LDA #$11
bottom_line:
    STA GPU_VRAM_DATA
    DEX
    BNE bottom_line

    ; Left edge (column 0): First byte of each row
    ; Rows 1-98
    LDY #1
left_edge_loop:
    ; Calculate address = Y * 80
    ; Use temp storage for 16-bit math
    STY temp_row

    ; Calculate row * 80
    ; 80 = 64 + 16 = $50
    TYA
    STA temp_hi
    LDA #0
    STA temp_lo

    ; Shift left 4 times (multiply by 16)
    LDX #4
left_shift1:
    ASL temp_lo
    ROL temp_hi
    DEX
    BNE left_shift1

    ; Save * 16
    LDA temp_lo
    STA temp2_lo
    LDA temp_hi
    STA temp2_hi

    ; Shift left 2 more times (now * 64)
    LDX #2
left_shift2:
    ASL temp_lo
    ROL temp_hi
    DEX
    BNE left_shift2

    ; Add * 16 to get * 80
    CLC
    LDA temp_lo
    ADC temp2_lo
    STA temp_lo
    LDA temp_hi
    ADC temp2_hi
    STA temp_hi

    ; Set VRAM address
    LDA temp_lo
    STA GPU_VRAM_ADDR_LO
    LDA temp_hi
    STA GPU_VRAM_ADDR_HI

    ; Write white to first byte (left edge, 2 pixels)
    LDA #$11
    STA GPU_VRAM_DATA

    LDY temp_row
    INY
    CPY #99
    BNE left_edge_loop

    ; Right edge (column 158-159 = byte 79): Last byte of each row
    LDY #1
right_edge_loop:
    ; Calculate address = Y * 80 + 79
    STY temp_row

    TYA
    STA temp_hi
    LDA #0
    STA temp_lo

    LDX #4
right_shift1:
    ASL temp_lo
    ROL temp_hi
    DEX
    BNE right_shift1

    LDA temp_lo
    STA temp2_lo
    LDA temp_hi
    STA temp2_hi

    LDX #2
right_shift2:
    ASL temp_lo
    ROL temp_hi
    DEX
    BNE right_shift2

    CLC
    LDA temp_lo
    ADC temp2_lo
    STA temp_lo
    LDA temp_hi
    ADC temp2_hi
    STA temp_hi

    ; Add 79 for right edge
    CLC
    LDA temp_lo
    ADC #79
    STA GPU_VRAM_ADDR_LO
    LDA temp_hi
    ADC #0
    STA GPU_VRAM_ADDR_HI

    ; Write white to last byte (right edge, 2 pixels)
    LDA #$11
    STA GPU_VRAM_DATA

    LDY temp_row
    INY
    CPY #99
    BNE right_edge_loop

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

forever:
    JMP forever

; Temporary storage
temp_row:   .byte 0
temp_lo:    .byte 0
temp_hi:    .byte 0
temp2_lo:   .byte 0
temp2_hi:   .byte 0
