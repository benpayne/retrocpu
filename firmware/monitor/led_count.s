; LED counter test - count 0,1,2,3 on LEDs with visible delay
; Writes to $0010 trigger LED debug in soc_top.v
; led[0] = write_seen, led[1] = data!=0, led[2] = read==write, led[3] = mem_we
.setcpu "6502"

.segment "CODE"
.org $E000

RESET:
    LDX #$FF
    TXS

    ; Counter in A
    LDA #$00

LOOP:
    ; Write counter to $0010 (triggers LED debug)
    STA $0010

    ; Read back to trigger led[2] match
    LDA $0010

    ; Increment counter (will wrap 0->1->2->3->0)
    CLC
    ADC #$01
    AND #$03    ; Keep only bits 0-1 (values 0-3)

    ; Long delay so we can see the pattern
    LDX #$00
DELAY_OUTER:
    LDY #$00
DELAY_INNER:
    DEY
    BNE DELAY_INNER
    DEX
    BNE DELAY_OUTER

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
