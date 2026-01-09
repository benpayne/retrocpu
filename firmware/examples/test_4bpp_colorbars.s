; 4 BPP mode test - 16 vertical color bars
; 4 BPP: 160×100, 16 colors, 2 pixels/byte
; 80 bytes/line × 100 lines = 8000 bytes
; Draw 16 vertical bars, each 10 pixels wide
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

    ; Set up 16-color VGA palette
    LDX #0
palette_loop:
    TXA
    STA GPU_CLUT_INDEX

    ; Load palette entry from table
    ; Compute Y = X * 3 (each palette entry is 3 bytes: R,G,B)
    TXA
    ASL A               ; A = X * 2
    STA temp            ; temp = X * 2
    TXA                 ; A = X
    CLC
    ADC temp            ; A = X + (X * 2) = X * 3
    TAY

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
    LDA #$02            ; 4 BPP
    STA GPU_MODE

    ; Enable burst mode
    LDA #$01
    STA GPU_VRAM_CTRL

    ; Set VRAM address to start
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    ; Fill screen with color bars
    ; Each scanline: 80 bytes
    ; Each color bar: 10 pixels wide = 5 bytes (2 pixels/byte)
    ; Pattern for one scanline:
    ;   Color 0: 5 bytes of $00
    ;   Color 1: 5 bytes of $11
    ;   ...
    ;   Color 15: 5 bytes of $FF

    LDY #0              ; Scanline counter (0-99)

scanline_loop:
    ; For each scanline, write 16 color bars
    LDX #0              ; Color index (0-15)

color_loop:
    ; Generate byte value (color in both nibbles)
    TXA
    ASL A
    ASL A
    ASL A
    ASL A               ; Shift to upper nibble
    STA temp
    TXA
    ORA temp            ; Combine: both nibbles same color

    ; Write this byte 5 times (10 pixels = 5 bytes in 4bpp)
    STA GPU_VRAM_DATA
    STA GPU_VRAM_DATA
    STA GPU_VRAM_DATA
    STA GPU_VRAM_DATA
    STA GPU_VRAM_DATA

    INX
    CPX #16
    BNE color_loop

    ; Next scanline
    INY
    CPY #100
    BNE scanline_loop

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

forever:
    JMP forever

; Temporary storage
temp:
    .byte 0

; 16-color VGA palette (R, G, B values, 4-bit each)
palette_data:
    .byte $00, $00, $00  ; 0: Black
    .byte $00, $00, $0A  ; 1: Blue
    .byte $00, $0A, $00  ; 2: Green
    .byte $00, $0A, $0A  ; 3: Cyan
    .byte $0A, $00, $00  ; 4: Red
    .byte $0A, $00, $0A  ; 5: Magenta
    .byte $0A, $05, $00  ; 6: Brown
    .byte $0A, $0A, $0A  ; 7: Light Gray
    .byte $05, $05, $05  ; 8: Dark Gray
    .byte $05, $05, $0F  ; 9: Light Blue
    .byte $05, $0F, $05  ; 10: Light Green
    .byte $05, $0F, $0F  ; 11: Light Cyan
    .byte $0F, $05, $05  ; 12: Light Red
    .byte $0F, $05, $0F  ; 13: Light Magenta
    .byte $0F, $0F, $05  ; 14: Yellow
    .byte $0F, $0F, $0F  ; 15: White
