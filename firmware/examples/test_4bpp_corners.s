; 4 BPP mode test - just mark the four corners
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

    ; Color 2: Red
    LDA #$02
    STA GPU_CLUT_INDEX
    LDA #$0F
    STA GPU_CLUT_DATA_R
    LDA #$00
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Color 3: Green
    LDA #$03
    STA GPU_CLUT_INDEX
    LDA #$00
    STA GPU_CLUT_DATA_R
    LDA #$0F
    STA GPU_CLUT_DATA_G
    LDA #$00
    STA GPU_CLUT_DATA_B

    ; Color 4: Blue
    LDA #$04
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

    ; Disable burst mode for precise addressing
    LDA #$00
    STA GPU_VRAM_CTRL

    ; Fill screen with black (color 0)
    LDA #$01
    STA GPU_VRAM_CTRL       ; Enable burst
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    LDX #$00
    LDA #$00
clear_loop:
    STA GPU_VRAM_DATA
    STA GPU_VRAM_DATA
    STA GPU_VRAM_DATA
    STA GPU_VRAM_DATA
    INX
    BNE clear_loop

    ; Disable burst mode for precise pixel placement
    LDA #$00
    STA GPU_VRAM_CTRL

    ; Top-left corner: Address 0 (row 0, col 0-1)
    ; Write white (color 1)
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI
    LDA #$11                ; White in both pixels
    STA GPU_VRAM_DATA

    ; Top-right corner: Address 79 (row 0, col 158-159)
    ; Write red (color 2)
    LDA #79
    STA GPU_VRAM_ADDR_LO
    LDA #$00
    STA GPU_VRAM_ADDR_HI
    LDA #$22                ; Red in both pixels
    STA GPU_VRAM_DATA

    ; Bottom-left corner: Address 7920 = $1EF0 (row 99, col 0-1)
    ; Write green (color 3)
    LDA #$F0
    STA GPU_VRAM_ADDR_LO
    LDA #$1E
    STA GPU_VRAM_ADDR_HI
    LDA #$33                ; Green in both pixels
    STA GPU_VRAM_DATA

    ; Bottom-right corner: Address 7999 = $1F3F (row 99, col 158-159)
    ; Write blue (color 4)
    LDA #$3F
    STA GPU_VRAM_ADDR_LO
    LDA #$1F
    STA GPU_VRAM_ADDR_HI
    LDA #$44                ; Blue in both pixels
    STA GPU_VRAM_DATA

    ; Also mark middle of screen for reference
    ; Row 50, col 80 (middle): Address = 50*80 + 40 = 4040 = $0FC8
    LDA #$C8
    STA GPU_VRAM_ADDR_LO
    LDA #$0F
    STA GPU_VRAM_ADDR_HI
    LDA #$11                ; White
    STA GPU_VRAM_DATA

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

forever:
    JMP forever
