;==============================================================================
; gpu_test_4bpp.s - 4 BPP Graphics Mode Test
;
; Tests the Graphics GPU in 4 BPP mode (16 colors)
; - Programs all 16 palette entries with different colors
; - Draws vertical color bars in VRAM
; - Switches to graphics display mode
;
; Graphics Mode: 4 BPP (160x100, 8000 bytes, 16 colors)
; Each byte contains 2 pixels (4 bits per pixel)
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
    ; Program 16-Color Palette
    ;==========================================================================

    ; We'll create a nice rainbow palette
    ; 0: Black
    ; 1: Dark Red
    ; 2: Red
    ; 3: Orange
    ; 4: Yellow
    ; 5: Yellow-Green
    ; 6: Green
    ; 7: Cyan
    ; 8: Light Blue
    ; 9: Blue
    ; 10: Purple
    ; 11: Magenta
    ; 12: Pink
    ; 13: Gray
    ; 14: Light Gray
    ; 15: White

    ; Entry 0: Black
    LDA #$00
    STA GPU_CLUT_INDEX
    LDA #$0
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Entry 1: Dark Red
    LDA #$01
    STA GPU_CLUT_INDEX
    LDA #$8
    STA GPU_CLUT_DATA_R
    LDA #$0
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Entry 2: Red
    LDA #$02
    STA GPU_CLUT_INDEX
    LDA #$F
    STA GPU_CLUT_DATA_R
    LDA #$0
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Entry 3: Orange
    LDA #$03
    STA GPU_CLUT_INDEX
    LDA #$F
    STA GPU_CLUT_DATA_R
    LDA #$8
    STA GPU_CLUT_DATA_G
    LDA #$0
    STA GPU_CLUT_DATA_B

    ; Entry 4: Yellow
    LDA #$04
    STA GPU_CLUT_INDEX
    LDA #$F
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    LDA #$0
    STA GPU_CLUT_DATA_B

    ; Entry 5: Yellow-Green
    LDA #$05
    STA GPU_CLUT_INDEX
    LDA #$8
    STA GPU_CLUT_DATA_R
    LDA #$F
    STA GPU_CLUT_DATA_G
    LDA #$0
    STA GPU_CLUT_DATA_B

    ; Entry 6: Green
    LDA #$06
    STA GPU_CLUT_INDEX
    LDA #$0
    STA GPU_CLUT_DATA_R
    LDA #$F
    STA GPU_CLUT_DATA_G
    LDA #$0
    STA GPU_CLUT_DATA_B

    ; Entry 7: Cyan
    LDA #$07
    STA GPU_CLUT_INDEX
    LDA #$0
    STA GPU_CLUT_DATA_R
    LDA #$F
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Entry 8: Light Blue
    LDA #$08
    STA GPU_CLUT_INDEX
    LDA #$0
    STA GPU_CLUT_DATA_R
    LDA #$8
    STA GPU_CLUT_DATA_G
    LDA #$F
    STA GPU_CLUT_DATA_B

    ; Entry 9: Blue
    LDA #$09
    STA GPU_CLUT_INDEX
    LDA #$0
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    LDA #$F
    STA GPU_CLUT_DATA_B

    ; Entry 10: Purple
    LDA #$0A
    STA GPU_CLUT_INDEX
    LDA #$8
    STA GPU_CLUT_DATA_R
    LDA #$0
    STA GPU_CLUT_DATA_G
    LDA #$F
    STA GPU_CLUT_DATA_B

    ; Entry 11: Magenta
    LDA #$0B
    STA GPU_CLUT_INDEX
    LDA #$F
    STA GPU_CLUT_DATA_R
    LDA #$0
    STA GPU_CLUT_DATA_G
    LDA #$F
    STA GPU_CLUT_DATA_B

    ; Entry 12: Pink
    LDA #$0C
    STA GPU_CLUT_INDEX
    LDA #$F
    STA GPU_CLUT_DATA_R
    LDA #$8
    STA GPU_CLUT_DATA_G
    LDA #$F
    STA GPU_CLUT_DATA_B

    ; Entry 13: Gray
    LDA #$0D
    STA GPU_CLUT_INDEX
    LDA #$8
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Entry 14: Light Gray
    LDA #$0E
    STA GPU_CLUT_INDEX
    LDA #$C
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Entry 15: White
    LDA #$0F
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

    ; Set graphics mode to 4 BPP
    LDA #MODE_4BPP
    STA GPU_MODE

    ;==========================================================================
    ; Draw Vertical Color Bars
    ;==========================================================================
    ; 4 BPP mode: 160 pixels wide, 100 pixels tall, 80 bytes per row
    ; Each byte contains 2 pixels (high nibble = pixel 0, low nibble = pixel 1)
    ; We'll draw 16 vertical bars, 10 pixels wide each (160 / 16 = 10)
    ; Each bar uses one color from the palette (0-15)

    ; Set VRAM address to $0000
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    ; Enable burst mode
    LDA #VRAM_BURST_EN
    STA GPU_VRAM_CTRL

    ; Draw 100 rows
    LDX #100        ; Row counter

row_loop:
    ; Draw 16 color bars (each 10 pixels = 5 bytes wide)
    ; Bar 0: pixels 0-9   (bytes 0-4)   -> color 0
    ; Bar 1: pixels 10-19 (bytes 5-9)   -> color 1
    ; ... and so on

    LDY #$00        ; Color index for current bar

bar_loop:
    ; Each bar is 10 pixels = 5 bytes
    ; Each byte has same color in both nibbles (high and low)
    ; Byte pattern for color Y = YY (Y in high nibble, Y in low nibble)

    ; Calculate byte pattern: (Y << 4) | Y
    TYA             ; Load color index
    ASL A           ; Shift left 4 times to put in high nibble
    ASL A
    ASL A
    ASL A
    STA $00         ; Store in ZP temp
    TYA             ; Load color index again
    ORA $00         ; Combine with high nibble

    ; Now A contains the pattern (e.g., $00, $11, $22, ... $FF)

    ; Write 5 bytes of this pattern
    STA GPU_VRAM_DATA
    STA GPU_VRAM_DATA
    STA GPU_VRAM_DATA
    STA GPU_VRAM_DATA
    STA GPU_VRAM_DATA

    ; Next color bar
    INY
    CPY #16         ; Have we drawn all 16 bars?
    BCC bar_loop

    ; Next row
    DEX
    BNE row_loop

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
