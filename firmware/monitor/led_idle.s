; LED idle test - just halt immediately
; This shows us the "idle" LED pattern
.setcpu "6502"

.segment "CODE"
.org $E000

RESET:
    ; Don't initialize stack - just halt
    ; This is the absolute minimum code
    NOP
    NOP
    NOP

HALT:
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
