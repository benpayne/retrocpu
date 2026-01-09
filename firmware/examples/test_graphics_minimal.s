; Minimal graphics mode test
; Just switches to graphics mode - cursor should disappear
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

    ; Set up minimal 2-color palette for 1 BPP mode
    ; Color 0: Black
    LDA #$00
    STA GPU_CLUT_INDEX
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Color 1: White
    LDA #$01
    STA GPU_CLUT_INDEX
    LDA #$0F                ; Max brightness
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Set 1 BPP graphics mode (320×200, 2 colors)
    LDA #$00
    STA GPU_MODE

    ; Enable burst mode for VRAM writes
    LDA #$01
    STA GPU_VRAM_CTRL

    ; Set VRAM address to start
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    ; Write a simple test pattern (first 256 bytes)
    ; Alternating $FF and $00 creates vertical stripes
    LDX #0
write_pattern:
    TXA
    AND #$01                ; Alternate between 0 and 1
    BEQ write_zero
    LDA #$FF                ; All pixels on
    JMP write_byte
write_zero:
    LDA #$00                ; All pixels off
write_byte:
    STA GPU_VRAM_DATA       ; Write to VRAM (auto-increments)
    INX
    BNE write_pattern       ; Loop 256 times

    ; Now switch to graphics display mode
    ; This should make cursor disappear and show graphics
    LDA #$01
    STA GPU_DISPLAY_MODE

done:
    RTS                     ; Return to monitor
