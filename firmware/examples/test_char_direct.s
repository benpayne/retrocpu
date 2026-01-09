; Simple test to write directly to character display
; Prints "HELLO WORLD" without using CHROUT
.setcpu "6502"

; Character display GPU registers
CHAR_DATA   = $C010  ; Write character at cursor position
CURSOR_ROW  = $C011  ; Cursor row (0-29)
CURSOR_COL  = $C012  ; Cursor column (0-39 or 0-79)
CONTROL     = $C013  ; Mode control
FG_COLOR    = $C014  ; Foreground color
BG_COLOR    = $C015  ; Background color

.org $0300

start:
    CLD                     ; Clear decimal mode

    ; Set cursor to row 0, column 0
    LDA #0
    STA CURSOR_ROW
    STA CURSOR_COL

    ; Set colors: white on black
    LDA #$07                ; White (RGB 111)
    STA FG_COLOR
    LDA #$00                ; Black (RGB 000)
    STA BG_COLOR

    ; Write "HELLO WORLD" character by character
    LDX #0
loop:
    LDA message,X           ; Load character
    BEQ done                ; If zero, we're done
    STA CHAR_DATA           ; Write to display (auto-advances cursor)
    INX                     ; Next character
    BNE loop                ; Loop (should never wrap)

done:
    RTS                     ; Return to monitor

message:
    .byte "HELLO WORLD", 0  ; Null-terminated string
