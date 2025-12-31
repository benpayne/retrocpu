; Minimal test - just output 'X' repeatedly
.setcpu "6502"

UART_DATA   = $C000
UART_STATUS = $C001

.segment "CODE"
.org $E000

RESET:
    LDX #$FF
    TXS

LOOP:
    ; Wait for TX ready
    LDA UART_STATUS
    AND #$01
    BEQ LOOP

    ; Send 'X'
    LDA #'X'
    STA UART_DATA

    ; Delay
    LDY #$00
DELAY:
    DEY
    BNE DELAY

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
