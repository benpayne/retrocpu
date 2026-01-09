;==============================================================================
; gpu_test_1bpp.s - 1 BPP Graphics Mode Test
;
; Tests the Graphics GPU in 1 BPP (monochrome) mode
; - Programs a simple 2-color palette (black and white)
; - Fills VRAM with a checkerboard pattern
; - Switches to graphics display mode
;
; Register Map:
;   GPU Graphics Base: $C100
;   $C100: VRAM_ADDR_LO
;   $C101: VRAM_ADDR_HI
;   $C102: VRAM_DATA
;   $C103: VRAM_CTRL (bit 0: burst mode)
;   $C104: FB_BASE_LO
;   $C105: FB_BASE_HI
;   $C106: GPU_MODE (00=1BPP, 01=2BPP, 10=4BPP)
;   $C107: CLUT_INDEX
;   $C108: CLUT_DATA_R
;   $C109: CLUT_DATA_G
;   $C10A: CLUT_DATA_B
;   $C10B: GPU_STATUS
;   $C10C: GPU_IRQ_CTRL
;   $C10D: DISPLAY_MODE (0=char, 1=graphics)
;
; Graphics Mode: 1 BPP (320x200, 8000 bytes)
; Palette: Index 0 = Black, Index 1 = White
;
; Author: RetroCPU Project
; License: BSD 3-Clause
;==============================================================================

.segment "CODE"

; GPU register addresses
GPU_VRAM_ADDR_LO  = $C100
GPU_VRAM_ADDR_HI  = $C101
GPU_VRAM_DATA     = $C102
GPU_VRAM_CTRL     = $C103
GPU_FB_BASE_LO    = $C104
GPU_FB_BASE_HI    = $C105
GPU_MODE          = $C106
GPU_CLUT_INDEX    = $C107
GPU_CLUT_DATA_R   = $C108
GPU_CLUT_DATA_G   = $C109
GPU_CLUT_DATA_B   = $C10A
GPU_STATUS        = $C10B
GPU_IRQ_CTRL      = $C10C
GPU_DISPLAY_MODE  = $C10D

; Graphics modes
MODE_1BPP = $00
MODE_2BPP = $01
MODE_4BPP = $02

; Display modes
DISPLAY_CHAR     = $00
DISPLAY_GRAPHICS = $01

; VRAM control
VRAM_BURST_EN = $01

.proc main
    ;==========================================================================
    ; Setup Palette
    ;==========================================================================

    ; Program palette entry 0: Black (R=0, G=0, B=0)
    LDA #$00
    STA GPU_CLUT_INDEX
    LDA #$0
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Program palette entry 1: White (R=15, G=15, B=15)
    LDA #$01
    STA GPU_CLUT_INDEX
    LDA #$F
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ;==========================================================================
    ; Configure Graphics GPU
    ;==========================================================================

    ; Set framebuffer base address to $0000
    LDA #$00
    STA GPU_FB_BASE_LO
    STA GPU_FB_BASE_HI

    ; Set graphics mode to 1 BPP
    LDA #MODE_1BPP
    STA GPU_MODE

    ;==========================================================================
    ; Fill VRAM with Checkerboard Pattern
    ;==========================================================================

    ; Set VRAM address to $0000
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    ; Enable burst mode for fast writes
    LDA #VRAM_BURST_EN
    STA GPU_VRAM_CTRL

    ; Fill 8000 bytes with alternating pattern
    ; X = pattern selector (alternates between $AA and $55)
    ; Y = byte counter within page (0-255)
    ; $00 (ZP) = page counter (0-31, for 8000 bytes = 31 pages + 64 bytes)

    LDX #$AA        ; Start with $AA pattern
    LDY #$00        ; Byte counter
    LDA #$00
    STA $00         ; Page counter in zero page

fill_loop:
    ; Write current pattern to VRAM
    STX GPU_VRAM_DATA

    ; Toggle pattern between $AA and $55
    TXA
    EOR #$FF        ; Invert bits: $AA -> $55, $55 -> $AA
    TAX

    ; Increment byte counter
    INY
    BNE fill_loop   ; Continue if not rolled over

    ; Increment page counter
    INC $00
    LDA $00
    CMP #32         ; Check if we've written 32 pages (8192 bytes)
    BCC fill_loop   ; Continue if less than 32

    ; Write final 64 bytes (to reach 8000 bytes total)
    ; Actually, 8000 = 31*256 + 64, so we need one more partial page
    LDY #$00
final_bytes:
    STX GPU_VRAM_DATA
    TXA
    EOR #$FF
    TAX
    INY
    CPY #64         ; Write 64 more bytes
    BCC final_bytes

    ; Disable burst mode
    LDA #$00
    STA GPU_VRAM_CTRL

    ;==========================================================================
    ; Switch to Graphics Mode
    ;==========================================================================

    LDA #DISPLAY_GRAPHICS
    STA GPU_DISPLAY_MODE

    ;==========================================================================
    ; Done - Loop Forever
    ;==========================================================================

done:
    JMP done

.endproc

; Reset vector
.segment "RESET"
.word main
