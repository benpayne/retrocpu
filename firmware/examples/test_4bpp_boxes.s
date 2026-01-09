; 4 BPP mode test - nested boxes to check alignment
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

    ; Color 2: Blue
    LDA #$02
    STA GPU_CLUT_INDEX
    LDA #$00
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    LDA #$0F
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

    ; Color 4: Red
    LDA #$04
    STA GPU_CLUT_INDEX
    LDA #$0F
    STA GPU_CLUT_DATA_R
    LDA #$00
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Color 5: Yellow
    LDA #$05
    STA GPU_CLUT_INDEX
    LDA #$0F
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    LDA #$00
    STA GPU_CLUT_DATA_B

    ; Set 4 BPP mode
    LDA #$02
    STA GPU_MODE

    ; Enable burst mode
    LDA #$01
    STA GPU_VRAM_CTRL

    ; Clear screen to black first
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    LDX #$1F        ; 8000 bytes = $1F40
    LDY #$40
clear_loop:
    LDA #$00
    STA GPU_VRAM_DATA
    DEY
    BNE clear_loop
    DEX
    BNE clear_loop

    ; Draw boxes
    ; Box 1 (White): row 0, row 99, col 0, col 159
    ; Box 2 (Blue): row 1, row 98, col 1, col 158
    ; Box 3 (Green): row 2, row 97, col 2, col 157
    ; Box 4 (Red): row 3, row 96, col 3, col 156
    ; Box 5 (Yellow): row 4, row 95, col 4, col 155

    ; Draw White box (outermost)
    LDA #1
    JSR draw_box

    ; Draw Blue box
    LDA #2
    JSR draw_box

    ; Draw Green box
    LDA #3
    JSR draw_box

    ; Draw Red box
    LDA #4
    JSR draw_box

    ; Draw Yellow box
    LDA #5
    JSR draw_box

    ; Switch to graphics mode
    LDA #$01
    STA GPU_DISPLAY_MODE

forever:
    JMP forever

;===========================================================================
; draw_box - Draw a rectangular box
; Input: A = color index (also box index, so box 1 is at row 0/99, col 0/159)
; Uses: box_color, row_num, col_start, col_end, temp
;===========================================================================
draw_box:
    STA box_color

    ; Calculate box parameters based on color index
    ; Top row = color - 1
    ; Bottom row = 100 - color
    ; Left column = (color - 1) * 2 (in pixels, / 2 for bytes)
    ; Right column = 160 - ((color - 1) * 2)

    SEC
    SBC #1          ; A = color - 1 = inset
    STA temp        ; temp = inset

    ; Top row = inset
    STA row_num
    JSR draw_horizontal_line

    ; Bottom row = 99 - inset
    LDA #99
    SEC
    SBC temp
    STA row_num
    JSR draw_horizontal_line

    ; Now draw vertical sides
    ; Left column: byte offset = inset
    ; Right column: byte offset = 79 - inset

    ; Left vertical
    LDA temp
    STA col_byte
    LDA box_color
    ASL A           ; Shift color to upper nibble
    ASL A
    ASL A
    ASL A
    STA left_byte_val
    JSR draw_left_vertical

    ; Right vertical
    LDA #79
    SEC
    SBC temp
    STA col_byte
    LDA box_color
    STA right_byte_val
    JSR draw_right_vertical

    RTS

;===========================================================================
; draw_horizontal_line - Draw a horizontal line at row_num
;===========================================================================
draw_horizontal_line:
    ; Address = row_num * 80 + temp (column byte offset)
    ; Calculate row_num * 80
    LDA row_num
    STA addr_hi
    LDA #0
    STA addr_lo

    ; Multiply by 80 (= 64 + 16)
    ; First * 16
    LDX #4
shift_loop1:
    ASL addr_lo
    ROL addr_hi
    DEX
    BNE shift_loop1

    ; Save * 16
    LDA addr_lo
    STA temp2
    LDA addr_hi
    STA temp3

    ; Now * 4 more to get * 64
    LDX #2
shift_loop2:
    ASL addr_lo
    ROL addr_hi
    DEX
    BNE shift_loop2

    ; Add the * 16 to get * 80
    CLC
    LDA addr_lo
    ADC temp2
    STA addr_lo
    LDA addr_hi
    ADC temp3
    STA addr_hi

    ; Add column offset (temp)
    CLC
    LDA addr_lo
    ADC temp
    STA GPU_VRAM_ADDR_LO
    LDA addr_hi
    ADC #0
    STA GPU_VRAM_ADDR_HI

    ; Calculate how many bytes to write
    ; Total: 80 bytes
    ; Start: temp, End: 79 - temp
    ; Count = (79 - temp) - temp + 1 = 80 - 2*temp

    LDA #80
    SEC
    SBC temp
    SEC
    SBC temp
    TAX             ; X = byte count

    ; Generate byte value (color in both nibbles)
    LDA box_color
    ASL A
    ASL A
    ASL A
    ASL A
    STA temp2
    LDA box_color
    ORA temp2

hline_loop:
    STA GPU_VRAM_DATA
    DEX
    BNE hline_loop

    RTS

;===========================================================================
; draw_left_vertical - Draw left vertical line
; col_byte has the byte offset (column / 2)
; left_byte_val has the color in upper nibble
;===========================================================================
draw_left_vertical:
    ; Start row = temp + 1, end row = 98 - temp
    LDA temp
    CLC
    ADC #1
    STA row_num

vert_left_loop:
    ; Calculate address = row_num * 80 + col_byte
    LDA row_num
    STA addr_hi
    LDA #0
    STA addr_lo

    ; Multiply by 80
    LDX #4
vl_shift1:
    ASL addr_lo
    ROL addr_hi
    DEX
    BNE vl_shift1

    LDA addr_lo
    STA temp2
    LDA addr_hi
    STA temp3

    LDX #2
vl_shift2:
    ASL addr_lo
    ROL addr_hi
    DEX
    BNE vl_shift2

    CLC
    LDA addr_lo
    ADC temp2
    STA addr_lo
    LDA addr_hi
    ADC temp3
    STA addr_hi

    ; Add column byte
    CLC
    LDA addr_lo
    ADC col_byte
    STA GPU_VRAM_ADDR_LO
    LDA addr_hi
    ADC #0
    STA GPU_VRAM_ADDR_HI

    ; Write the byte
    LDA left_byte_val
    STA GPU_VRAM_DATA

    ; Next row
    INC row_num
    LDA row_num
    CMP #99
    BCC vert_left_loop

    ; Check if we need one more
    LDA #99
    SEC
    SBC temp
    CMP row_num
    BCS vert_left_loop

    RTS

;===========================================================================
; draw_right_vertical - Draw right vertical line
;===========================================================================
draw_right_vertical:
    ; Start row = temp + 1, end row = 98 - temp
    LDA temp
    CLC
    ADC #1
    STA row_num

vert_right_loop:
    ; Calculate address = row_num * 80 + col_byte
    LDA row_num
    STA addr_hi
    LDA #0
    STA addr_lo

    ; Multiply by 80
    LDX #4
vr_shift1:
    ASL addr_lo
    ROL addr_hi
    DEX
    BNE vr_shift1

    LDA addr_lo
    STA temp2
    LDA addr_hi
    STA temp3

    LDX #2
vr_shift2:
    ASL addr_lo
    ROL addr_hi
    DEX
    BNE vr_shift2

    CLC
    LDA addr_lo
    ADC temp2
    STA addr_lo
    LDA addr_hi
    ADC temp3
    STA addr_hi

    ; Add column byte
    CLC
    LDA addr_lo
    ADC col_byte
    STA GPU_VRAM_ADDR_LO
    LDA addr_hi
    ADC #0
    STA GPU_VRAM_ADDR_HI

    ; Write the byte
    LDA right_byte_val
    STA GPU_VRAM_DATA

    ; Next row
    INC row_num
    LDA row_num
    CMP #99
    BCC vert_right_loop

    ; Check if we need one more
    LDA #99
    SEC
    SBC temp
    CMP row_num
    BCS vert_right_loop

    RTS

; Variables
box_color:      .byte 0
row_num:        .byte 0
col_start:      .byte 0
col_end:        .byte 0
col_byte:       .byte 0
temp:           .byte 0
temp2:          .byte 0
temp3:          .byte 0
addr_lo:        .byte 0
addr_hi:        .byte 0
left_byte_val:  .byte 0
right_byte_val: .byte 0
