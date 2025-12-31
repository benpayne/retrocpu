; LED static pattern test
; Write $AA (10101010) to $0010 once, then halt
; This should give us a FIXED LED pattern we can verify
.setcpu "6502"

.segment "CODE"
.org $E000

RESET:
    LDX #$FF
    TXS

    ; Write $AA to $0010
    LDA #$AA
    STA $0010

    ; Read it back
    LDA $0010

    ; Now write $55 to different address to change pattern
    LDA #$55
    STA $0011

HALT:
    ; Infinite loop - LEDs should be STATIC now
    JMP HALT

NMI:
    RTI

IRQ:
    RTI

.segment "VECTORS"
.org $FFFA
.word NMI
.word RESET
.word IRQ
