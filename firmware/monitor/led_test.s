; LED blink test - verify clock and CPU are running
; Write to RAM at $0010 which triggers LED debug logic in soc_top.v
.setcpu "6502"

.segment "CODE"
.org $E000

RESET:
    LDX #$FF
    TXS

    ; Write different patterns to $0010 to trigger LEDs
    ; soc_top.v debug logic:
    ;   led[0] = saw write to $0010
    ;   led[1] = data written != 0
    ;   led[2] = read matches write
    ;   led[3] = mem_we signal

LOOP:
    ; Write $42 to $0010
    LDA #$42
    STA $0010

    ; Read it back
    LDA $0010

    ; Delay
    LDY #$FF
DELAY1:
    DEY
    BNE DELAY1

    ; Write $00 to $0010
    LDA #$00
    STA $0010

    ; Delay
    LDY #$FF
DELAY2:
    DEY
    BNE DELAY2

    JMP LOOP

NMI:
    RTI

IRQ:
    RTI

.segment "VECTORS"
.org $FFFA
.word NMI
.word RESET
.word IRQ
