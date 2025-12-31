; Ultra-simple test: output 'H' once and halt
.setcpu "6502"

UART_DATA   = $C000
UART_STATUS = $C001

.segment "CODE"
.org $E000

RESET:
    LDX #$FF
    TXS

    ; Wait for UART TX ready
WAIT:
    LDA UART_STATUS
    AND #$01
    BEQ WAIT

    ; Output 'H' (0x48)
    LDA #$48
    STA UART_DATA

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
