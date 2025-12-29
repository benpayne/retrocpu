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

    ; Wait for input character
    JSR CHRIN          ; Read character into A
    STA TEMP           ; Save command character

    ; Echo the character back
    JSR CHROUT

    ; Print newline
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT

    ; Parse command
    LDA TEMP           ; Restore command character
    CMP #'E'           ; Examine command
    BEQ CMD_EXAMINE
    CMP #'e'
    BEQ CMD_EXAMINE

    CMP #'D'           ; Deposit command
    BEQ CMD_DEPOSIT
    CMP #'d'
    BEQ CMD_DEPOSIT

    CMP #'H'           ; Help command
    BEQ CMD_HELP
    CMP #'h'
    BEQ CMD_HELP

    ; Unknown command
    LDX #0
@UNKNOWN_LOOP:
    LDA UNKNOWN_MSG,X
    BEQ MAIN_LOOP
    JSR CHROUT
    INX
    BNE @UNKNOWN_LOOP

; ============================================================================
; CMD_EXAMINE - Examine memory at address
; ============================================================================
CMD_EXAMINE:
    LDX #0
@E_LOOP:
    LDA EXAMINE_MSG,X
    BEQ MAIN_LOOP
    JSR CHROUT
    INX
    BNE @E_LOOP

; ============================================================================
; CMD_DEPOSIT - Deposit value to memory
; ============================================================================
CMD_DEPOSIT:
    LDX #0
@D_LOOP:
    LDA DEPOSIT_MSG,X
    BEQ MAIN_LOOP
    JSR CHROUT
    INX
    BNE @D_LOOP

; ============================================================================
; CMD_HELP - Display help
; ============================================================================
CMD_HELP:
    LDX #0
@H_LOOP:
    LDA HELP_MSG,X
    BEQ MAIN_LOOP
    JSR CHROUT
    INX
    BNE @H_LOOP

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
; CHRIN - Input character from UART
; Output: A = character received
; Preserves: X, Y
; ============================================================================

CHRIN:
@WAIT_RX:
    LDA UART_STATUS    ; Check RX ready
    AND #$02           ; Bit 1 = RX ready
    BEQ @WAIT_RX       ; Wait if no data available

    LDA UART_DATA      ; Read character (clears RX ready flag)
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

UNKNOWN_MSG:
    .byte "Unknown command", $0D, $0A
    .byte 0

EXAMINE_MSG:
    .byte "E command not yet implemented", $0D, $0A
    .byte 0

DEPOSIT_MSG:
    .byte "D command not yet implemented", $0D, $0A
    .byte 0

HELP_MSG:
    .byte $0D, $0A
    .byte "Available commands:", $0D, $0A
    .byte "  E addr      - Examine memory", $0D, $0A
    .byte "  D addr val  - Deposit value", $0D, $0A
    .byte "  H           - Help", $0D, $0A
    .byte $0D, $0A
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
