; UART TX Test - send 'U' (0x55 = 01010101) repeatedly
; 'U' has alternating bits which is good for testing UART timing
.setcpu "6502"

UART_DATA   = $C000
UART_STATUS = $C001

.segment "CODE"
.org $E000

RESET:
    ; Initialize stack
    LDX #$FF
    TXS

    ; Load 'U' into X for quick access
    LDX #$55

SEND_LOOP:
    ; Wait for TX ready (bit 0 of status)
WAIT_TX:
    LDA UART_STATUS
    AND #$01
    BEQ WAIT_TX

    ; Send 'U'
    STX UART_DATA

    ; Small delay between characters
    LDY #$10
DELAY:
    DEY
    BNE DELAY

    ; Loop forever
    JMP SEND_LOOP

NMI:
    RTI

IRQ:
    RTI

.segment "VECTORS"
.org $FFFA
.word NMI
.word RESET
.word IRQ
