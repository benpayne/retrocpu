;==============================================================================
; gpu_test_interactive.s - Interactive Graphics GPU Test
;
; Interactive test program for graphics GPU
; - Press '1' to switch to 1 BPP mode with checkerboard
; - Press '2' to switch to 2 BPP mode with color gradientalternating
; - Press '4' to switch to 4 BPP mode with rainbow bars
; - Press 'C' to return to character mode
; - Press 'G' to return to graphics mode
; - Press 'X' to clear VRAM
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

; UART addresses (for keyboard input)
UART_RX_DATA      = $C000
UART_STATUS       = $C002

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
    ; Initialize - Setup Default Palette
    ;==========================================================================

    JSR setup_palette

    ;==========================================================================
    ; Main Loop - Wait for Key Press
    ;==========================================================================

main_loop:
    ; Check UART status for received data
    LDA UART_STATUS
    AND #$01        ; Check RX ready bit
    BEQ main_loop   ; Loop if no data

    ; Read character
    LDA UART_RX_DATA

    ; Check what key was pressed
    CMP #'1'
    BEQ do_1bpp
    CMP #'2'
    BEQ do_2bpp
    CMP #'4'
    BEQ do_4bpp
    CMP #'C'
    BEQ do_char_mode
    CMP #'G'
    BEQ do_graphics_mode
    CMP #'X'
    BEQ do_clear

    ; Unknown key, ignore
    JMP main_loop

do_1bpp:
    JSR test_1bpp
    JMP main_loop

do_2bpp:
    JSR test_2bpp
    JMP main_loop

do_4bpp:
    JSR test_4bpp
    JMP main_loop

do_char_mode:
    LDA #DISPLAY_CHAR
    STA GPU_DISPLAY_MODE
    JMP main_loop

do_graphics_mode:
    LDA #DISPLAY_GRAPHICS
    STA GPU_DISPLAY_MODE
    JMP main_loop

do_clear:
    JSR clear_vram
    JMP main_loop

.endproc

;==============================================================================
; setup_palette - Initialize a default 16-color palette
;==============================================================================
.proc setup_palette
    ; Entry 0: Black
    LDA #$00
    STA GPU_CLUT_INDEX
    LDA #$0
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Entry 1: White
    LDA #$01
    STA GPU_CLUT_INDEX
    LDA #$F
    STA GPU_CLUT_DATA_R
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

    ; Entry 3: Green
    LDA #$03
    STA GPU_CLUT_INDEX
    LDA #$0
    STA GPU_CLUT_DATA_R
    LDA #$F
    STA GPU_CLUT_DATA_G
    LDA #$0
    STA GPU_CLUT_DATA_B

    ; Entry 4: Blue
    LDA #$04
    STA GPU_CLUT_INDEX
    LDA #$0
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    LDA #$F
    STA GPU_CLUT_DATA_B

    ; Entry 5: Yellow
    LDA #$05
    STA GPU_CLUT_INDEX
    LDA #$F
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    LDA #$0
    STA GPU_CLUT_DATA_B

    ; Entry 6: Cyan
    LDA #$06
    STA GPU_CLUT_INDEX
    LDA #$0
    STA GPU_CLUT_DATA_R
    LDA #$F
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Entry 7: Magenta
    LDA #$07
    STA GPU_CLUT_INDEX
    LDA #$F
    STA GPU_CLUT_DATA_R
    LDA #$0
    STA GPU_CLUT_DATA_G
    LDA #$F
    STA GPU_CLUT_DATA_B

    ; Continue with grayscale for entries 8-15
    LDX #$08
pal_loop:
    TXA
    STA GPU_CLUT_INDEX
    TXA
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B
    INX
    CPX #$10
    BCC pal_loop

    RTS
.endproc

;==============================================================================
; test_1bpp - Fill VRAM with checkerboard in 1 BPP mode
;==============================================================================
.proc test_1bpp
    ; Set 1 BPP mode
    LDA #MODE_1BPP
    STA GPU_MODE

    ; Set framebuffer base
    LDA #$00
    STA GPU_FB_BASE_LO
    STA GPU_FB_BASE_HI

    ; Fill with alternating pattern
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    LDA #VRAM_BURST_EN
    STA GPU_VRAM_CTRL

    LDX #$AA        ; Alternating pattern
    LDY #32         ; Page counter

page_loop:
    LDA #$00
byte_loop:
    STX GPU_VRAM_DATA
    TXA
    EOR #$FF        ; Toggle pattern
    TAX
    INX
    BNE byte_loop
    DEY
    BNE page_loop

    LDA #$00
    STA GPU_VRAM_CTRL

    ; Switch to graphics mode
    LDA #DISPLAY_GRAPHICS
    STA GPU_DISPLAY_MODE

    RTS
.endproc

;==============================================================================
; test_2bpp - Fill VRAM with horizontal stripes in 2 BPP mode
;==============================================================================
.proc test_2bpp
    ; Set 2 BPP mode
    LDA #MODE_2BPP
    STA GPU_MODE

    ; Set framebuffer base
    LDA #$00
    STA GPU_FB_BASE_LO
    STA GPU_FB_BASE_HI

    ; Fill with pattern that creates horizontal color stripes
    ; Each byte: bits [7:6]=pixel0, [5:4]=pixel1, [3:2]=pixel2, [1:0]=pixel3
    ; Pattern $E4 = 11100100 = colors 3,2,1,0

    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    LDA #VRAM_BURST_EN
    STA GPU_VRAM_CTRL

    LDY #32         ; Page counter
    LDX #$00        ; Pattern: starts at $00, increments

page_loop2:
    LDA #$00
byte_loop2:
    STX GPU_VRAM_DATA
    INX             ; Change pattern each byte
    INX
    BNE byte_loop2
    DEY
    BNE page_loop2

    LDA #$00
    STA GPU_VRAM_CTRL

    ; Switch to graphics mode
    LDA #DISPLAY_GRAPHICS
    STA GPU_DISPLAY_MODE

    RTS
.endproc

;==============================================================================
; test_4bpp - Fill VRAM with vertical gradient in 4 BPP mode
;==============================================================================
.proc test_4bpp
    ; Set 4 BPP mode
    LDA #MODE_4BPP
    STA GPU_MODE

    ; Set framebuffer base
    LDA #$00
    STA GPU_FB_BASE_LO
    STA GPU_FB_BASE_HI

    ; Fill with gradient pattern
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    LDA #VRAM_BURST_EN
    STA GPU_VRAM_CTRL

    ; Draw 100 rows of gradient
    LDX #100        ; Row counter

row_loop:
    LDY #$00        ; Byte/color counter

byte_loop4:
    ; Create pattern where both nibbles have same value
    ; Y = byte index (0-79), map to color (0-15)
    ; 80 bytes / 16 colors = 5 bytes per color
    TYA
    LSR A           ; Divide by 5 to get color
    LSR A           ; Y/5 approximated by Y/4 for simplicity
    AND #$0F        ; Mask to 4 bits
    STA $00         ; Store color
    ASL A           ; Shift to high nibble
    ASL A
    ASL A
    ASL A
    ORA $00         ; Combine with low nibble

    STA GPU_VRAM_DATA

    INY
    CPY #80         ; 80 bytes per row
    BCC byte_loop4

    DEX
    BNE row_loop

    LDA #$00
    STA GPU_VRAM_CTRL

    ; Switch to graphics mode
    LDA #DISPLAY_GRAPHICS
    STA GPU_DISPLAY_MODE

    RTS
.endproc

;==============================================================================
; clear_vram - Clear all VRAM to $00
;==============================================================================
.proc clear_vram
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    LDA #VRAM_BURST_EN
    STA GPU_VRAM_CTRL

    LDY #32         ; 32 pages
clear_page:
    LDX #$00
clear_byte:
    LDA #$00
    STA GPU_VRAM_DATA
    DEX
    BNE clear_byte
    DEY
    BNE clear_page

    LDA #$00
    STA GPU_VRAM_CTRL

    RTS
.endproc

; Reset vector
.segment "RESET"
.word main
