; Full-screen checkerboard pattern
; 1 BPP mode: 320x200 = 40 bytes/line x 200 lines = 8000 bytes
; Even scanlines: $AA repeated 40 times
; Odd scanlines: $55 repeated 40 times
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

    ; Set up palette entry 0 (black)
    LDA #$00
    STA GPU_CLUT_INDEX
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Set up palette entry 1 (white - full brightness R,G,B)
    LDA #$01
    STA GPU_CLUT_INDEX
    LDA #$0F
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Set 1 BPP graphics mode
    LDA #$00
    STA GPU_MODE

    ; Enable burst mode
    LDA #$01
    STA GPU_VRAM_CTRL

    ; Set VRAM address to start
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    ; Fill screen with checkerboard
    ; Y = scanline counter (0-199)
    ; X = byte counter within scanline (0-39)

    LDY #0              ; Scanline counter

scanline_loop:
    ; Determine pattern for this scanline
    ; Even scanlines get $AA, odd get $55
    TYA
    AND #$01
    BEQ even_line

    ; Odd line: use $55
    LDA #$55
    JMP write_scanline

even_line:
    ; Even line: use $AA
    LDA #$AA

write_scanline:
    ; Write this byte 40 times for the scanline
    LDX #40

byte_loop:
    STA GPU_VRAM_DATA   ; Write byte (auto-increments address)
    DEX
    BNE byte_loop

    ; Next scanline
    INY
    CPY #200            ; Done all 200 scanlines?
    BNE scanline_loop

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

    ; Infinite loop
forever:
    JMP forever
