; Test to compare absolute vs indirect indexed addressing for UART reads
; Assemble with ca65 and load into monitor

.org $0400

UART_STATUS = $C001
TEMP = $00
ADDR_LO = $10
ADDR_HI = $11

test_absolute:
    ; Test 1: Read UART status using absolute addressing (like firmware)
    LDA UART_STATUS      ; Absolute: LDA $C001
    STA TEMP             ; Save result
    RTS

test_indirect:
    ; Test 2: Read UART status using indirect indexed (like monitor E command)
    LDA #$01             ; Set up pointer in zero page
    STA ADDR_LO
    LDA #$C0
    STA ADDR_HI

    LDY #$00             ; Y = 0
    LDA (ADDR_LO),Y      ; Indirect indexed: LDA ($10),Y
    STA TEMP             ; Save result
    RTS

; Results should be in TEMP
; If they're different, we found the problem!
