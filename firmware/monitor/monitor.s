; ============================================================================
; RetroCPU Monitor Program
; 6502 Assembly Language
;
; Simple monitor with commands: E (examine), D (deposit), J (jump), G (go)
; Outputs via UART at $C000
; ============================================================================

.setcpu "6502"

; ============================================================================
; Memory Map
; ============================================================================

UART_DATA   = $C000  ; UART data register (write to transmit)
UART_STATUS = $C001  ; UART status (bit 0 = TX ready)

; Zero page variables
TEMP        = $00    ; Temporary storage
ADDR_LO     = $02    ; 16-bit address low byte
ADDR_HI     = $03    ; 16-bit address high byte
VALUE       = $04    ; Byte value
INPUT_BUF   = $10    ; Input buffer start (16 bytes)
INPUT_LEN   = $20    ; Input buffer length

; ============================================================================
; ROM starts at $E000
; ============================================================================

.segment "CODE"
.org $E000

; ============================================================================
; RESET Handler - Entry point on power-on or reset
; ============================================================================

RESET:
    ; Initialize stack pointer
    LDX #$FF
    TXS

    ; Initialize zero page
    LDA #0
    STA INPUT_LEN

    ; Print welcome message
    JSR PRINT_WELCOME

    ; Fall through to main loop

; ============================================================================
; Main Command Loop
; ============================================================================

MAIN_LOOP:
    ; Print prompt
    LDA #'>'
    JSR CHROUT
    LDA #' '
    JSR CHROUT

    ; Read command (for now, just loop - no input yet)
    ; In MVP we'll just demonstrate output

    ; Print demo message
    LDX #0
:   LDA DEMO_MSG,X
    BEQ MAIN_LOOP      ; Loop forever
    JSR CHROUT
    INX
    BNE :-

; ============================================================================
; CHROUT - Output character to UART
; Input: A = character to output
; Preserves: X, Y
; ============================================================================

CHROUT:
    PHA                ; Save A

@WAIT_TX:
    LDA UART_STATUS    ; Check TX ready
    AND #$01           ; Bit 0 = TX ready
    BEQ @WAIT_TX       ; Wait if not ready

    PLA                ; Restore A
    STA UART_DATA      ; Send character
    RTS

; ============================================================================
; PRINT_STR - Print null-terminated string
; Input: X = string address low, Y = string address high
; ============================================================================

PRINT_STR:
    STX ADDR_LO
    STY ADDR_HI
    LDY #0

@LOOP:
    LDA (ADDR_LO),Y
    BEQ @DONE
    JSR CHROUT
    INY
    BNE @LOOP

@DONE:
    RTS

; ============================================================================
; PRINT_WELCOME - Print welcome banner
; ============================================================================

PRINT_WELCOME:
    LDX #0
@LOOP:
    LDA WELCOME_MSG,X
    BEQ @DONE
    JSR CHROUT
    INX
    BNE @LOOP

@DONE:
    RTS

; ============================================================================
; PRINT_HEX - Print byte in hex
; Input: A = byte to print
; ============================================================================

PRINT_HEX:
    PHA                ; Save original value

    ; Print high nibble
    LSR A
    LSR A
    LSR A
    LSR A
    JSR PRINT_NIBBLE

    ; Print low nibble
    PLA                ; Restore original
    AND #$0F
    JSR PRINT_NIBBLE
    RTS

PRINT_NIBBLE:
    CMP #$0A
    BCC @DIGIT
    ; A-F
    ADC #('A'-$0A-1)   ; Carry is set
    JSR CHROUT
    RTS
@DIGIT:
    ; 0-9
    ADC #'0'
    JSR CHROUT
    RTS

; ============================================================================
; Messages
; ============================================================================

WELCOME_MSG:
    .byte $0D, $0A                    ; CR LF
    .byte "RetroCPU Monitor v1.0", $0D, $0A
    .byte $0D, $0A
    .byte "6502 FPGA Microcomputer", $0D, $0A
    .byte "(c) 2025 - Educational Project", $0D, $0A
    .byte $0D, $0A
    .byte "Commands:", $0D, $0A
    .byte "  E addr      - Examine memory", $0D, $0A
    .byte "  D addr val  - Deposit value", $0D, $0A
    .byte "  J addr      - Jump to address", $0D, $0A
    .byte "  G           - Go to BASIC", $0D, $0A
    .byte $0D, $0A
    .byte 0

DEMO_MSG:
    .byte $0D, $0A
    .byte "Monitor ready! (Input not yet implemented)", $0D, $0A
    .byte 0

; ============================================================================
; NMI Handler (not used in MVP)
; ============================================================================

NMI:
    RTI

; ============================================================================
; IRQ Handler (not used in MVP)
; ============================================================================

IRQ:
    RTI

; ============================================================================
; Vectors at end of ROM ($FFFA-$FFFF)
; ============================================================================

.segment "VECTORS"
.org $FFFA

.word NMI           ; $FFFA-$FFFB: NMI vector
.word RESET         ; $FFFC-$FFFD: RESET vector
.word IRQ           ; $FFFE-$FFFF: IRQ/BRK vector
