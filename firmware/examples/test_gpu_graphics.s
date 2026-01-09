; ============================================================================
; Graphics GPU Test Program
; Tests 4 BPP graphics mode by drawing color bars
; ============================================================================

.setcpu "6502"

; ============================================================================
; Graphics GPU Register Map (Base: $C100)
; ============================================================================

GPU_VRAM_ADDR_LO  = $C100  ; VRAM address low byte
GPU_VRAM_ADDR_HI  = $C101  ; VRAM address high byte (bits 14:8)
GPU_VRAM_DATA     = $C102  ; VRAM read/write with auto-increment
GPU_VRAM_CTRL     = $C103  ; Bit 0: Burst mode enable
GPU_FB_BASE_LO    = $C104  ; Framebuffer base address low byte
GPU_FB_BASE_HI    = $C105  ; Framebuffer base address high byte
GPU_MODE          = $C106  ; Graphics mode (00=1BPP, 01=2BPP, 10=4BPP)
GPU_CLUT_INDEX    = $C107  ; Palette index (0-15)
GPU_CLUT_DATA_R   = $C108  ; Palette red component (4-bit)
GPU_CLUT_DATA_G   = $C109  ; Palette green component (4-bit)
GPU_CLUT_DATA_B   = $C10A  ; Palette blue component (4-bit)
GPU_STATUS        = $C10B  ; Bit 0: VBlank flag
GPU_IRQ_CTRL      = $C10C  ; Bit 0: VBlank interrupt enable
GPU_DISPLAY_MODE  = $C10D  ; Bit 0: 0=Character, 1=Graphics

; ============================================================================
; Zero Page Variables
; ============================================================================

TEMP      = $00    ; Temporary storage
TEMP2     = $01    ; Temporary storage 2
COUNTER   = $02    ; Loop counter
COLOR_IDX = $03    ; Current color index

; ============================================================================
; Program Start (Load at $0300 for safety)
; ============================================================================

.segment "CODE"
.org $0300

start:
    ; Initialize
    CLD                     ; Clear decimal mode

    ; Step 1: Configure 16-color palette
    JSR setup_palette

    ; Step 2: Configure GPU for 4 BPP graphics mode
    JSR configure_gpu

    ; Step 3: Draw color bars pattern
    JSR draw_color_bars

    ; Step 4: Switch to graphics display mode
    JSR switch_to_graphics

    ; Done - infinite loop
done:
    JMP done

; ============================================================================
; Subroutine: setup_palette
; Sets up a 16-color VGA-like palette
; ============================================================================

setup_palette:
    LDX #0                  ; Start with palette index 0

palette_loop:
    ; Set palette index
    STX GPU_CLUT_INDEX

    ; Use X as index into color table
    TXA
    ASL A                   ; Multiply by 3 (R, G, B)
    STA TEMP
    TXA
    ASL A
    CLC
    ADC TEMP                ; A = X * 3
    TAY                     ; Y = index into color table

    ; Write R, G, B components
    LDA palette_colors,Y
    STA GPU_CLUT_DATA_R
    INY
    LDA palette_colors,Y
    STA GPU_CLUT_DATA_G
    INY
    LDA palette_colors,Y
    STA GPU_CLUT_DATA_B

    ; Next palette entry
    INX
    CPX #16                 ; Done all 16 colors?
    BNE palette_loop

    RTS

; 16-color palette (R, G, B) - 48 bytes total
palette_colors:
    .byte $0, $0, $0        ; 0: Black
    .byte $0, $0, $A        ; 1: Blue
    .byte $0, $A, $0        ; 2: Green
    .byte $0, $A, $A        ; 3: Cyan
    .byte $A, $0, $0        ; 4: Red
    .byte $A, $0, $A        ; 5: Magenta
    .byte $A, $5, $0        ; 6: Brown
    .byte $A, $A, $A        ; 7: Light Gray
    .byte $5, $5, $5        ; 8: Dark Gray
    .byte $5, $5, $F        ; 9: Light Blue
    .byte $5, $F, $5        ; 10: Light Green
    .byte $5, $F, $F        ; 11: Light Cyan
    .byte $F, $5, $5        ; 12: Light Red
    .byte $F, $5, $F        ; 13: Light Magenta
    .byte $F, $F, $0        ; 14: Yellow
    .byte $F, $F, $F        ; 15: White

; ============================================================================
; Subroutine: configure_gpu
; Sets up GPU for 4 BPP graphics mode
; ============================================================================

configure_gpu:
    ; Set framebuffer base address to $0000
    LDA #$00
    STA GPU_FB_BASE_LO
    STA GPU_FB_BASE_HI

    ; Set graphics mode to 4 BPP (mode = 2)
    LDA #$02
    STA GPU_MODE

    ; Enable burst mode for fast VRAM writes
    LDA #$01
    STA GPU_VRAM_CTRL

    RTS

; ============================================================================
; Subroutine: draw_color_bars
; Draws 16 vertical color bars in 4 BPP mode
; Resolution: 160x100, each bar is 10 pixels wide x 100 tall
; VRAM: 80 bytes per row x 100 rows = 8000 bytes
; ============================================================================

draw_color_bars:
    ; Set VRAM write address to $0000
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    ; Outer loop: 100 rows
    LDA #100
    STA TEMP                ; TEMP = row counter

row_loop:
    ; Inner loop: Draw 16 color bars across the row
    ; Each bar: 10 pixels = 5 bytes (2 pixels per byte in 4 BPP)

    LDX #0                  ; X = color index (0-15)

bar_loop:
    ; Color index is in X
    ; Pack two pixels: (color << 4) | color
    TXA
    ASL A
    ASL A
    ASL A
    ASL A                   ; A = color << 4
    STA TEMP2
    TXA
    ORA TEMP2               ; A = (color << 4) | color

    ; Write 5 bytes for this bar (10 pixels)
    LDY #5
byte_loop:
    STA GPU_VRAM_DATA       ; Write and auto-increment
    DEY
    BNE byte_loop

    ; Next color bar
    INX
    CPX #16
    BNE bar_loop

    ; Next row
    DEC TEMP
    BNE row_loop

    RTS

; ============================================================================
; Subroutine: switch_to_graphics
; Switch display from character mode to graphics mode
; ============================================================================

switch_to_graphics:
    LDA #$01                ; 1 = Graphics mode
    STA GPU_DISPLAY_MODE
    RTS

; ============================================================================
; End of program
; ============================================================================
