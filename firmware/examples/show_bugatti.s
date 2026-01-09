; Display bugatti image in 4 BPP mode
; Image: 160×100, 16 colors
; Data: 8000 bytes (2 pixels per byte)
; Palette: 48 bytes (16 colors × 3 bytes RGB)
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

; Zero page variables (for indirect addressing)
temp         = $F0
src_ptr      = $F1  ; 16-bit pointer (uses $F1, $F2)

.org $0300

start:
    CLD

    ; Load palette (16 colors)
    LDX #0
palette_loop:
    ; Set palette index
    TXA
    STA GPU_CLUT_INDEX

    ; Calculate palette data offset (X * 3)
    TXA
    ASL A               ; A = X * 2
    STA temp
    TXA
    CLC
    ADC temp            ; A = X * 3
    TAY

    ; Load R, G, B from palette data
    LDA palette_data,Y
    STA GPU_CLUT_DATA_R
    LDA palette_data+1,Y
    STA GPU_CLUT_DATA_G
    LDA palette_data+2,Y
    STA GPU_CLUT_DATA_B

    INX
    CPX #16
    BNE palette_loop

    ; Set 4 BPP graphics mode
    LDA #$02
    STA GPU_MODE

    ; Enable burst mode for fast VRAM write
    LDA #$01
    STA GPU_VRAM_CTRL

    ; Set VRAM address to start
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    ; Copy image data to VRAM
    ; 8000 bytes = $1F40
    ; Strategy: Use 16-bit pointer to source data

    ; Initialize source pointer to image_data
    LDA #<image_data
    STA src_ptr
    LDA #>image_data
    STA src_ptr+1

    ; Copy 8000 bytes ($1F40) = $1F pages + $40 bytes
    ; We'll copy $20 pages (8192 bytes) to be safe
    LDX #$00        ; Page counter (0-31)

copy_page:
    LDY #$00        ; Byte within page

copy_byte:
    ; Load byte from (src_ptr),Y
    LDA (src_ptr),Y
    STA GPU_VRAM_DATA

    INY
    BNE copy_byte   ; Copy all 256 bytes in this page

    ; Move to next page
    INC src_ptr+1   ; Increment high byte of pointer
    INX
    CPX #$20        ; Copied $20 pages (8192 bytes)?
    BNE copy_page

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

forever:
    JMP forever

; Palette data (16 colors, 3 bytes each: R, G, B in 4-bit format)
palette_data:
    .incbin "bugatti_4bpp.pal"

; Image pixel data (8000 bytes, packed 4BPP)
image_data:
    .incbin "bugatti_4bpp.raw"
