; ============================================================================
; RetroCPU Monitor Program
; 6502 Assembly Language
;
; Simple monitor with commands: E (examine), D (deposit), H (help), G (go)
; Uses inline argument format: "E 0200" or "D 0200 42"
; Outputs via UART at $C000
; ============================================================================

.setcpu "6502"

; ============================================================================
; Memory Map
; ============================================================================

UART_DATA   = $C000  ; UART data register (R/W)
UART_STATUS = $C001  ; UART status (bit 0 = TX ready, bit 1 = RX ready)

LCD_DATA    = $C100  ; LCD data register (write ASCII character)
LCD_CMD     = $C101  ; LCD command register (write HD44780 command)
LCD_STATUS  = $C102  ; LCD status register (bit 0 = busy flag)

; Zero page variables
TEMP        = $00    ; Temporary storage
TEMP2       = $01    ; Temporary storage 2
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

    ; Initialize LCD and display boot message
    JSR LCD_INIT
    JSR LCD_BOOT_MSG

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
    BNE @TRY_E_LOWER
    JMP CMD_EXAMINE
@TRY_E_LOWER:
    CMP #'e'
    BNE @TRY_D
    JMP CMD_EXAMINE

@TRY_D:
    CMP #'D'           ; Deposit command
    BNE @TRY_D_LOWER
    JMP CMD_DEPOSIT
@TRY_D_LOWER:
    CMP #'d'
    BNE @TRY_G
    JMP CMD_DEPOSIT

@TRY_G:
    CMP #'G'           ; Go to BASIC
    BNE @TRY_G_LOWER
    JMP CMD_GO
@TRY_G_LOWER:
    CMP #'g'
    BNE @TRY_H
    JMP CMD_GO

@TRY_H:
    CMP #'H'           ; Help command
    BNE @TRY_H_LOWER
    JMP CMD_HELP
@TRY_H_LOWER:
    CMP #'h'
    BNE @UNKNOWN
    JMP CMD_HELP

    ; Unknown command
@UNKNOWN:
    LDX #0
@UNKNOWN_LOOP:
    LDA UNKNOWN_MSG,X
    BEQ @BACK_TO_MAIN
    JSR CHROUT
    INX
    BNE @UNKNOWN_LOOP
@BACK_TO_MAIN:
    JMP MAIN_LOOP

; ============================================================================
; CMD_EXAMINE - Examine memory at address
; Format: E 0200 (inline - reads hex from UART after command)
; ============================================================================
CMD_EXAMINE:
    ; Skip spaces
    JSR SKIP_SPACES

    ; Read 4-digit hex address
    JSR READ_HEX_WORD
    BCS @ERROR         ; Carry set = error

    ; Read byte from memory
    LDY #0
    LDA (ADDR_LO),Y
    STA VALUE

    ; Print address in hex (4 digits)
    LDA ADDR_HI
    JSR PRINT_HEX
    LDA ADDR_LO
    JSR PRINT_HEX

    ; Print ": "
    LDA #':'
    JSR CHROUT
    LDA #' '
    JSR CHROUT

    ; Print value in hex (2 digits)
    LDA VALUE
    JSR PRINT_HEX

    ; Print newline
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT

    JMP MAIN_LOOP

@ERROR:
    LDX #0
@ERR_LOOP:
    LDA ERROR_MSG,X
    BEQ @DONE_ERR
    JSR CHROUT
    INX
    BNE @ERR_LOOP
@DONE_ERR:
    JMP MAIN_LOOP

; ============================================================================
; CMD_DEPOSIT - Deposit value to memory
; Format: D 0200 42 (inline - reads hex from UART after command)
; ============================================================================
CMD_DEPOSIT:
    ; Skip spaces
    JSR SKIP_SPACES

    ; Read 4-digit hex address
    JSR READ_HEX_WORD
    BCS @ERROR         ; Carry set = error

    ; Skip spaces before value
    JSR SKIP_SPACES

    ; Read 2-digit hex value
    JSR READ_HEX_BYTE
    BCS @ERROR         ; Carry set = error

    ; Store value to memory
    STA VALUE
    LDY #0
    STA (ADDR_LO),Y

    ; Read back and verify (for display)
    LDA (ADDR_LO),Y

    ; Print address in hex
    LDA ADDR_HI
    JSR PRINT_HEX
    LDA ADDR_LO
    JSR PRINT_HEX

    ; Print ": "
    LDA #':'
    JSR CHROUT
    LDA #' '
    JSR CHROUT

    ; Print value in hex
    LDA VALUE
    JSR PRINT_HEX

    ; Print newline
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT

    JMP MAIN_LOOP

@ERROR:
    LDX #0
@ERR_LOOP:
    LDA ERROR_MSG,X
    BEQ @DONE_ERR
    JSR CHROUT
    INX
    BNE @ERR_LOOP
@DONE_ERR:
    JMP MAIN_LOOP

; ============================================================================
; CMD_GO - Jump to BASIC entry point
; Format: G
; Jumps to OSI BASIC COLD_START at $9D11
; NEVER RETURNS - BASIC takes over
; NOTE: $8000 contains data tables, $9D11 is actual entry point!
; ============================================================================
CMD_GO:
    ; Print message
    LDX #0
@MSG_LOOP:
    LDA GO_MSG,X
    BEQ @JUMP
    JSR CHROUT
    INX
    BNE @MSG_LOOP

@JUMP:
    JMP $9D11          ; OSI BASIC COLD_START entry point (not $8000!)

; ============================================================================
; CMD_HELP - Display help
; ============================================================================
CMD_HELP:
    LDX #0
@H_LOOP:
    LDA HELP_MSG,X
    BEQ @DONE_HELP
    JSR CHROUT
    INX
    BNE @H_LOOP
@DONE_HELP:
    JMP MAIN_LOOP

; ============================================================================
; SKIP_SPACES - Skip whitespace characters
; Reads characters from UART until non-space found
; Output: TEMP = first non-space character
; ============================================================================
SKIP_SPACES:
@LOOP:
    JSR CHRIN
    CMP #' '
    BEQ @LOOP
    CMP #$09           ; Tab
    BEQ @LOOP
    ; Non-space found, put it in TEMP for next function
    STA TEMP
    RTS

; ============================================================================
; READ_HEX_NIBBLE - Read one hex character and convert to nibble
; Input: A = ASCII hex character ('0'-'9', 'A'-'F', 'a'-'f')
; Output: A = nibble value (0-15), Carry clear if valid
;         Carry set if invalid character
; ============================================================================
READ_HEX_NIBBLE:
    ; Check for '0'-'9'
    CMP #'0'
    BCC @INVALID       ; Less than '0'
    CMP #'9'+1
    BCC @DIGIT         ; '0'-'9'

    ; Check for 'A'-'F'
    CMP #'A'
    BCC @INVALID
    CMP #'F'+1
    BCC @UPPER_HEX

    ; Check for 'a'-'f'
    CMP #'a'
    BCC @INVALID
    CMP #'f'+1
    BCS @INVALID

    ; Convert 'a'-'f' to 10-15
    SEC
    SBC #'a'-10
    CLC                ; Success
    RTS

@UPPER_HEX:
    ; Convert 'A'-'F' to 10-15
    SEC
    SBC #'A'-10
    CLC                ; Success
    RTS

@DIGIT:
    ; Convert '0'-'9' to 0-9
    SEC
    SBC #'0'
    CLC                ; Success
    RTS

@INVALID:
    SEC                ; Error
    RTS

; ============================================================================
; READ_HEX_BYTE - Read two hex characters and convert to byte
; Output: A = byte value, Carry clear if valid
;         Carry set if invalid
; Uses: TEMP, TEMP2
; ============================================================================
READ_HEX_BYTE:
    ; Read first nibble (high)
    LDA TEMP           ; Get character from SKIP_SPACES or previous read
    JSR READ_HEX_NIBBLE
    BCS @ERROR
    ASL A              ; Shift to high nibble
    ASL A
    ASL A
    ASL A
    STA TEMP2          ; Save high nibble

    ; Read second nibble (low)
    JSR CHRIN
    JSR READ_HEX_NIBBLE
    BCS @ERROR

    ; Combine nibbles
    ORA TEMP2          ; OR with high nibble
    CLC                ; Success
    RTS

@ERROR:
    SEC                ; Error
    RTS

; ============================================================================
; READ_HEX_WORD - Read four hex characters and convert to 16-bit word
; Output: ADDR_HI:ADDR_LO = word value, Carry clear if valid
;         Carry set if invalid
; Uses: TEMP, TEMP2, VALUE
; ============================================================================
READ_HEX_WORD:
    ; Read high byte (first 2 hex digits)
    LDA TEMP           ; Get first character
    JSR READ_HEX_NIBBLE
    BCS @ERROR
    ASL A
    ASL A
    ASL A
    ASL A
    STA TEMP2

    JSR CHRIN
    JSR READ_HEX_NIBBLE
    BCS @ERROR
    ORA TEMP2
    STA ADDR_HI        ; Store high byte

    ; Read low byte (next 2 hex digits)
    JSR CHRIN
    JSR READ_HEX_NIBBLE
    BCS @ERROR
    ASL A
    ASL A
    ASL A
    ASL A
    STA TEMP2

    JSR CHRIN
    JSR READ_HEX_NIBBLE
    BCS @ERROR
    ORA TEMP2
    STA ADDR_LO        ; Store low byte

    CLC                ; Success
    RTS

@ERROR:
    SEC                ; Error
    RTS

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
; LCD_INIT - Initialize HD44780 LCD in 4-bit mode
; Uses: A, X
; ============================================================================

LCD_INIT:
    ; Wait 50ms for LCD power-up (approximate delay loop)
    LDX #$FF
@DELAY1:
    DEX
    BNE @DELAY1
    LDX #$FF
@DELAY2:
    DEX
    BNE @DELAY2

    ; Clear display (0x01)
    LDA #$01
    STA LCD_CMD
    JSR LCD_DELAY

    ; Display on, cursor off (0x0C)
    LDA #$0C
    STA LCD_CMD
    JSR LCD_DELAY

    ; Entry mode: increment, no shift (0x06)
    LDA #$06
    STA LCD_CMD
    JSR LCD_DELAY

    RTS

; ============================================================================
; LCD_DELAY - Delay for LCD command to complete
; Uses: X
; ============================================================================

LCD_DELAY:
    LDX #$FF
@LOOP:
    DEX
    BNE @LOOP
    RTS

; ============================================================================
; LCD_BOOT_MSG - Display boot message on LCD
; Uses: A, X
; ============================================================================

LCD_BOOT_MSG:
    ; Set cursor to home position (0x80)
    LDA #$80
    STA LCD_CMD
    JSR LCD_DELAY

    ; Print "RetroCPU 6502" on line 1
    LDX #0
@LINE1:
    LDA LCD_MSG_LINE1,X
    BEQ @LINE2_START
    STA LCD_DATA
    JSR LCD_DELAY
    INX
    CPX #16            ; Limit to 16 chars
    BNE @LINE1

@LINE2_START:
    ; Set cursor to line 2, column 0 (0xC0)
    LDA #$C0
    STA LCD_CMD
    JSR LCD_DELAY

    ; Print "Monitor v1.0" on line 2
    LDX #0
@LINE2:
    LDA LCD_MSG_LINE2,X
    BEQ @DONE
    STA LCD_DATA
    JSR LCD_DELAY
    INX
    CPX #16            ; Limit to 16 chars
    BNE @LINE2

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
    .byte "RetroCPU Monitor v1.1", $0D, $0A
    .byte $0D, $0A
    .byte "6502 FPGA Microcomputer", $0D, $0A
    .byte "(c) 2025 - Educational Project", $0D, $0A
    .byte $0D, $0A
    .byte "Commands:", $0D, $0A
    .byte "  E <addr>      - Examine memory", $0D, $0A
    .byte "  D <addr> <val> - Deposit value", $0D, $0A
    .byte "  G             - Go to BASIC", $0D, $0A
    .byte "  H             - Help", $0D, $0A
    .byte $0D, $0A
    .byte 0

LCD_MSG_LINE1:
    .byte "RetroCPU 6502   ", 0  ; 16 chars + null terminator

LCD_MSG_LINE2:
    .byte "Monitor v1.1    ", 0  ; 16 chars + null terminator

UNKNOWN_MSG:
    .byte "Unknown command", $0D, $0A
    .byte 0

ERROR_MSG:
    .byte "Syntax error", $0D, $0A
    .byte 0

GO_MSG:
    .byte "Starting BASIC...", $0D, $0A
    .byte 0

HELP_MSG:
    .byte $0D, $0A
    .byte "RetroCPU Monitor Commands:", $0D, $0A
    .byte "  E <addr>        - Examine memory (hex address)", $0D, $0A
    .byte "  D <addr> <val>  - Deposit value to memory", $0D, $0A
    .byte "  G               - Go to BASIC interpreter", $0D, $0A
    .byte "  H               - Display this help", $0D, $0A
    .byte $0D, $0A
    .byte "Examples:", $0D, $0A
    .byte "  E 0200          - Read byte at $0200", $0D, $0A
    .byte "  D 0200 42       - Write $42 to $0200", $0D, $0A
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
; OSI BASIC I/O Vectors ($FFF0-$FFF8)
; These vectors are required for OSI BASIC to work properly.
; BASIC JSRs to these addresses for character I/O.
; ============================================================================

.segment "IOVECTORS"

VEC_CHRIN:
    JMP CHRIN       ; $FFF0-$FFF2: Character input vector

VEC_CHROUT:
    JMP CHROUT      ; $FFF3-$FFF5: Character output vector

VEC_LOAD:
    ; BASIC calls this to check for BREAK key
    ; Return with A=0 for no break
    LDA #0          ; $FFF6-$FFF8: Load/break check
    RTS

; ============================================================================
; Hardware Interrupt Vectors ($FFFA-$FFFF)
; ============================================================================

.segment "VECTORS"

.word NMI           ; $FFFA-$FFFB: NMI vector
.word RESET         ; $FFFC-$FFFD: RESET vector
.word IRQ           ; $FFFE-$FFFF: IRQ/BRK vector
