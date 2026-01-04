; ============================================================================
; RetroCPU Monitor Program - Feature 004: Program Loader and I/O Config
; 6502 Assembly Language
;
; Commands:
;   E - Examine memory
;   D - Deposit value
;   G - Go to BASIC
;   H - Help
;   J - Jump to/execute code at $0300
;   L - Load binary via XMODEM
;   I - Configure I/O sources
;   S - Status display
;
; Phases 1-4 Implementation:
;   - Enhanced CHRIN/CHROUT with I/O mode switching
;   - XMODEM binary upload protocol
;   - PS/2 keyboard support with translation table
;   - I/O configuration and status commands
; ============================================================================

.setcpu "6502"

; ============================================================================
; Memory Map - Peripherals
; ============================================================================

UART_DATA   = $C000  ; UART data register (R/W)
UART_STATUS = $C001  ; UART status (bit 0 = TX ready, bit 1 = RX ready)

GPU_CHAR_DATA = $C010  ; GPU character data register (write ASCII character)
GPU_CURSOR_COL = $C011 ; GPU cursor column (read/write)
GPU_CURSOR_ROW = $C012 ; GPU cursor row (read/write)
GPU_MODE = $C013       ; GPU control register (bit 1 = mode, bit 2 = cursor enable)

LCD_DATA    = $C100  ; LCD data register (write ASCII character)
LCD_CMD     = $C101  ; LCD command register (write HD44780 command)
LCD_STATUS  = $C102  ; LCD status register (bit 0 = busy flag)

PS2_DATA    = $C200  ; PS/2 data register (read scan code)
PS2_STATUS  = $C201  ; PS/2 status (bit 0 = data ready, bit 1 = interrupt)

; ============================================================================
; Zero Page Variables - Phase 1 & 2
; ============================================================================

; Base variables
TEMP        = $00    ; Temporary storage
TEMP2       = $01    ; Temporary storage 2
ADDR_LO     = $02    ; 16-bit address low byte
ADDR_HI     = $03    ; 16-bit address high byte
VALUE       = $04    ; Byte value
PS2_BREAK   = $05    ; PS/2 break code flag (1 = next code is break)
GPU_MODE_VAR = $06   ; Current GPU mode (0=40-col, 1=80-col)

; Jump vector for CMD_JUMP
JUMP_VECTOR = $07      ; 16-bit address for JMP (indirect)
JUMP_VECTOR_HI = $08
RESERVED_09 = $09
RESERVED_0A = $0A
RESERVED_0B = $0B
RESERVED_0C = $0C
RESERVED_0D = $0D
RESERVED_0E = $0E
RESERVED_0F = $0F

INPUT_BUF   = $10    ; Input buffer start (16 bytes)
INPUT_LEN   = $20    ; Input buffer length

; I/O Configuration (Phase 2)
IO_INPUT_MODE  = $21  ; Input mode: 0=UART, 1=PS2, 2=Both
IO_OUTPUT_MODE = $22  ; Output mode: 0=UART, 1=Display, 2=Both

; XMODEM State Variables (Phase 3)
XMODEM_STATE     = $23  ; XMODEM state machine state
XMODEM_PKT_NUM   = $24  ; Expected packet number
XMODEM_RETRY     = $25  ; Retry counter
XMODEM_CHECKSUM  = $26  ; Calculated checksum
XMODEM_ADDR_LO   = $27  ; Current write address low
XMODEM_ADDR_HI   = $28  ; Current write address high
XMODEM_BYTE_CNT  = $29  ; Byte counter in current packet
XMODEM_LAST_BYTE = $2C  ; Last byte received (for debugging)
XMODEM_TO_LOC    = $2D  ; Timeout location (for debugging)
TIMEOUT_COUNTER  = $2E  ; Timeout loop counter (preserves Y register)

; PS/2 Translation State (Phase 4)
PS2_SHIFT   = $2A    ; Shift key state (0 = not pressed, 1 = pressed)
PS2_CAPS    = $2B    ; Caps Lock state (0 = off, 1 = on)

; ============================================================================
; RAM Buffers - Phase 1 & 2
; ============================================================================

XMODEM_BUFFER = $0200  ; 128-byte XMODEM packet buffer
PS2_XLAT_TABLE = $0280 ; 128-byte PS/2 scancode to ASCII lookup table

; ============================================================================
; XMODEM Protocol Constants
; ============================================================================

SOH = $01    ; Start of header
EOT = $04    ; End of transmission
ACK = $06    ; Acknowledge
NAK = $15    ; Negative acknowledge
CAN = $18    ; Cancel

; XMODEM State Machine States
XMODEM_IDLE       = $00
XMODEM_WAIT_SOH   = $01
XMODEM_RECV_PKT   = $02
XMODEM_RECV_DATA  = $03
XMODEM_VERIFY     = $04
XMODEM_COMPLETE   = $05

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
    STA PS2_BREAK
    STA PS2_SHIFT
    STA PS2_CAPS

    ; Initialize I/O configuration to UART-only (Phase 2 - T005)
    STA IO_INPUT_MODE   ; 0 = UART input only
    STA IO_OUTPUT_MODE  ; 0 = UART output only

    ; Initialize GPU mode to 80-column (default)
    LDA #1
    STA GPU_MODE_VAR    ; 1 = 80-column mode

    ; Set GPU hardware to 80-column mode with cursor enabled
    ; Bit 1 = MODE (1=80-col), Bit 2 = CURSOR_EN (1=enabled)
    LDA #%00000110      ; MODE=1, CURSOR_EN=1
    STA GPU_MODE

    LDA #0              ; Clear A for subsequent initializations

    ; Initialize XMODEM state
    STA XMODEM_STATE
    STA XMODEM_PKT_NUM

    ; Initialize PS/2 lookup table (Phase 2 - T009)
    JSR INIT_PS2_TABLE

    ; Print welcome message
    JSR PRINT_WELCOME

    ; Initialize LCD explicitly (don't rely on hardware auto-init)
    JSR LCD_INIT

    ; Display boot message on LCD
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

    ; Parse command (Phase 2 - T010: added L, I, S commands)
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
    BNE @TRY_L
    JMP CMD_HELP

@TRY_L:
    CMP #'L'           ; Load binary via XMODEM
    BNE @TRY_L_LOWER
    JMP CMD_LOAD
@TRY_L_LOWER:
    CMP #'l'
    BNE @TRY_M
    JMP CMD_LOAD

@TRY_M:
    CMP #'M'           ; Mode (40/80 column)
    BNE @TRY_M_LOWER
    JMP CMD_MODE
@TRY_M_LOWER:
    CMP #'m'
    BNE @TRY_T
    JMP CMD_MODE

@TRY_T:
    CMP #'T'           ; Test buffer (receive 26 bytes and echo)
    BNE @TRY_T_LOWER
    JMP CMD_TEST_BUFFER
@TRY_T_LOWER:
    CMP #'t'
    BNE @TRY_I
    JMP CMD_TEST_BUFFER

@TRY_I:
    CMP #'I'           ; I/O configuration
    BNE @TRY_I_LOWER
    JMP CMD_IO_CONFIG
@TRY_I_LOWER:
    CMP #'i'
    BNE @TRY_J
    JMP CMD_IO_CONFIG

@TRY_J:
    CMP #'J'           ; Jump to address
    BNE @TRY_J_LOWER
    JMP CMD_JUMP
@TRY_J_LOWER:
    CMP #'j'
    BNE @TRY_S
    JMP CMD_JUMP

@TRY_S:
    CMP #'S'           ; Status display
    BNE @TRY_S_LOWER
    JMP CMD_STATUS
@TRY_S_LOWER:
    CMP #'s'
    BNE @UNKNOWN
    JMP CMD_STATUS

    ; Unknown command
@UNKNOWN:
    ; Save the received character
    STA TEMP

    ; Print "Received: '"
    LDX #0
@PRINT_RX_PREFIX:
    LDA RX_DEBUG_PREFIX,X
    BEQ @PRINT_CHAR
    JSR CHROUT
    INX
    BNE @PRINT_RX_PREFIX

@PRINT_CHAR:
    ; Print the actual character
    LDA TEMP
    JSR CHROUT

    ; Print "' (0x"
    LDX #0
@PRINT_HEX_PREFIX:
    LDA HEX_PREFIX,X
    BEQ @PRINT_HEX
    JSR CHROUT
    INX
    BNE @PRINT_HEX_PREFIX

@PRINT_HEX:
    ; Print hex value (high nibble)
    LDA TEMP
    LSR A
    LSR A
    LSR A
    LSR A
    CMP #$0A
    BCC @HIGH_DIGIT
    ADC #6          ; Convert to A-F
@HIGH_DIGIT:
    ADC #'0'
    JSR CHROUT

    ; Print hex value (low nibble)
    LDA TEMP
    AND #$0F
    CMP #$0A
    BCC @LOW_DIGIT
    ADC #6          ; Convert to A-F
@LOW_DIGIT:
    ADC #'0'
    JSR CHROUT

    ; Print ")" and newline
    LDA #')'
    JSR CHROUT
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT

    ; Now print "Unknown command"
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
; CMD_JUMP - Execute code at $0300 (where L command loads code)
; Format: J
; Calls the code at $0300 as a subroutine (JSR), returns to monitor when done
; ============================================================================
CMD_JUMP:
    ; Print execution message
    LDX #0
@MSG_LOOP:
    LDA JUMP_MSG,X
    BEQ @EXECUTE
    JSR CHROUT
    INX
    BNE @MSG_LOOP

@EXECUTE:
    ; Call the user program at $0300 as a subroutine
    ; Set up the address in the jump vector
    LDA #$00
    STA JUMP_VECTOR
    LDA #$03
    STA JUMP_VECTOR+1

    ; JSR to the address
    JSR @DO_CALL

    ; Print completion message
    LDX #0
@DONE_LOOP:
    LDA JUMP_DONE_MSG,X
    BEQ @RETURN
    JSR CHROUT
    INX
    BNE @DONE_LOOP

@RETURN:
    JMP MAIN_LOOP

@DO_CALL:
    JMP (JUMP_VECTOR)

; ============================================================================
; CMD_HELP - Display help
; ============================================================================
CMD_HELP:
    ; Set up pointer to HELP_MSG in zero page
    LDA #<HELP_MSG
    STA TEMP
    LDA #>HELP_MSG
    STA TEMP2

    LDY #0
@H_LOOP:
    LDA (TEMP),Y
    BEQ @DONE_HELP
    JSR CHROUT
    INY
    BNE @H_LOOP
    ; Y wrapped to 0, increment high byte of pointer
    INC TEMP2
    JMP @H_LOOP
@DONE_HELP:
    JMP MAIN_LOOP

; ============================================================================
; CMD_LOAD - Load binary program via XMODEM (Phase 3 - T015-T022)
; Format: L
; Receives binary data via XMODEM protocol and stores to RAM
; ============================================================================
CMD_LOAD:
    ; Print ready message
    LDX #0
@READY_LOOP:
    LDA LOAD_READY_MSG,X
    BEQ @START_XMODEM
    JSR CHROUT
    INX
    BNE @READY_LOOP

@START_XMODEM:
    ; Initialize XMODEM state
    LDA #$0300 & $FF       ; Start address $0300 (after buffers)
    STA XMODEM_ADDR_LO
    LDA #$0300 >> 8
    STA XMODEM_ADDR_HI

    LDA #1
    STA XMODEM_PKT_NUM     ; Start with packet 1

    LDA #0
    STA XMODEM_RETRY       ; Clear retry counter

    ; Call XMODEM receive function
    JSR XMODEM_RECEIVE

    ; Check result (A = 0 for success, non-zero for error)
    BEQ @SUCCESS

    ; Error occurred
    LDX #0
@ERR_LOOP:
    LDA LOAD_ERROR_MSG,X
    BEQ @DONE
    JSR CHROUT
    INX
    BNE @ERR_LOOP
    JMP @DONE

@SUCCESS:
    ; Print success message
    LDX #0
@SUCCESS_LOOP:
    LDA LOAD_SUCCESS_MSG,X
    BEQ @DONE
    JSR CHROUT
    INX
    BNE @SUCCESS_LOOP

@DONE:
    JMP MAIN_LOOP

; ============================================================================
; CMD_TEST_BUFFER - Test UART buffer by receiving 26 bytes and echoing them
; Diagnostic command to check for dropped bytes
; ============================================================================
CMD_TEST_BUFFER:
    ; Print prompt
    LDX #0
@PROMPT_LOOP:
    LDA TEST_PROMPT_MSG,X
    BEQ @START_RECEIVE
    JSR CHROUT
    INX
    BNE @PROMPT_LOOP

@START_RECEIVE:
    ; Receive 26 bytes into buffer at $0200
    LDY #0              ; Counter for received bytes

@RECEIVE_LOOP:
    JSR CHRIN           ; Wait for a byte (no timeout, blocking)
    STA $0200,Y         ; Store in buffer
    INY
    CPY #26             ; Got 26 bytes?
    BNE @RECEIVE_LOOP

    ; Print newline
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT

    ; Echo the buffer
    LDY #0
@ECHO_LOOP:
    LDA $0200,Y
    JSR CHROUT
    INY
    CPY #26
    BNE @ECHO_LOOP

    ; Print newline
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT

    JMP MAIN_LOOP

; ============================================================================
; XMODEM_RECEIVE - Receive binary data via XMODEM protocol
; Phase 3 - T016-T021
; Output: A = 0 for success, non-zero for error
; ============================================================================
XMODEM_RECEIVE:
    ; Save current output mode and set to Display only for debug
    LDA IO_OUTPUT_MODE
    PHA                 ; Save on stack
    LDA #1              ; Mode 1 = Display only (faster, no UART blocking)
    STA IO_OUTPUT_MODE

    ; DEBUG: Print test message to display
    LDX #0
@DEBUG_LOOP:
    LDA DEBUG_START_MSG,X
    BEQ @DEBUG_DONE
    JSR CHROUT
    INX
    BNE @DEBUG_LOOP
@DEBUG_DONE:

    ; Send initial NAK to start transfer
    LDA #NAK
    JSR UART_SEND

@WAIT_PKT:
    ; Reset byte counter for this packet
    LDA #0
    STA XMODEM_BYTE_CNT

    ; Wait for SOH or EOT (Location 1)
    LDA #1
    STA XMODEM_TO_LOC
    JSR CHRIN_TIMEOUT
    BCS @GOTO_TIMEOUT

    ; Check for EOT (end of transmission)
    CMP #EOT
    BNE @CHECK_SOH

    ; EOT received - send ACK and complete
    LDA #ACK
    JSR UART_SEND

    ; Restore output mode
    PLA
    STA IO_OUTPUT_MODE

    LDA #0              ; Success
    RTS

@GOTO_TIMEOUT:
    JMP @TIMEOUT

@CHECK_SOH:
    ; Check for SOH (start of header)
    CMP #SOH
    BEQ @SOH_OK
    JMP @GOTO_BAD_HEADER

@SOH_OK:
    ; SOH received (byte 0) - increment counter
    INC XMODEM_BYTE_CNT

    ; Receive packet number (Location 2)
    LDA #2
    STA XMODEM_TO_LOC
    JSR CHRIN_TIMEOUT
    BCS @GOTO_TIMEOUT
    INC XMODEM_BYTE_CNT  ; Byte 1 received
    CMP XMODEM_PKT_NUM
    BNE @GOTO_BAD_PKT_2
    STA TEMP            ; Save packet number

    ; Receive packet number complement (Location 3)
    LDA #3
    STA XMODEM_TO_LOC
    JSR CHRIN_TIMEOUT
    BCS @GOTO_TIMEOUT
    INC XMODEM_BYTE_CNT  ; Byte 2 received
    EOR #$FF
    CMP TEMP
    BEQ @PKT_NUM_OK

@GOTO_BAD_PKT_2:
    JMP @BAD_PKT_NUM

@PKT_NUM_OK:
    ; Receive 128 data bytes
    LDY #0
    LDA #0
    STA XMODEM_CHECKSUM  ; Initialize checksum

@RECV_DATA:
    ; Receive data byte (Location 4)
    LDA #4
    STA XMODEM_TO_LOC
    JSR CHRIN_TIMEOUT
    BCS @GOTO_TIMEOUT
    INC XMODEM_BYTE_CNT  ; Increment for each data byte (bytes 3-130)
    STA XMODEM_BUFFER,Y

    ; Add to checksum
    CLC
    ADC XMODEM_CHECKSUM
    STA XMODEM_CHECKSUM

    INY
    CPY #128
    BNE @RECV_DATA

    ; Receive checksum (Location 5)
    LDA #5
    STA XMODEM_TO_LOC
    JSR CHRIN_TIMEOUT
    BCC @CHKSUM_OK
    JMP @GOTO_TIMEOUT

@CHKSUM_OK:
    INC XMODEM_BYTE_CNT  ; Byte 132 (checksum) received

    ; DEBUG: Show checksum comparison
    PHA                  ; Save received checksum
    LDA #'C'
    JSR CHROUT
    LDA #'K'
    JSR CHROUT
    LDA #' '
    JSR CHROUT
    LDA #'R'
    JSR CHROUT
    LDA #'='
    JSR CHROUT
    PLA                  ; Restore received checksum
    PHA
    JSR PRINT_HEX       ; Show received
    LDA #' '
    JSR CHROUT
    LDA #'E'
    JSR CHROUT
    LDA #'='
    JSR CHROUT
    LDA XMODEM_CHECKSUM
    JSR PRINT_HEX       ; Show expected (calculated)
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT

    PLA                  ; Restore received checksum
    CMP XMODEM_CHECKSUM
    BNE @GOTO_BAD_CHKSUM
    JMP @CHECKSUM_GOOD   ; Checksum matches - skip error labels

@GOTO_BAD_PKT:
    JMP @BAD_PKT_NUM

@GOTO_BAD_CHKSUM:
    JMP @BAD_CHECKSUM

@GOTO_BAD_HEADER:
    JMP @BAD_HEADER

@CHECKSUM_GOOD:
    ; Checksum good - copy data to target address
    LDY #0
@COPY_DATA:
    LDA XMODEM_BUFFER,Y
    STA (XMODEM_ADDR_LO),Y
    INY
    CPY #128
    BNE @COPY_DATA

    ; Advance target address by 128
    CLC
    LDA XMODEM_ADDR_LO
    ADC #128
    STA XMODEM_ADDR_LO
    LDA XMODEM_ADDR_HI
    ADC #0
    STA XMODEM_ADDR_HI

    ; Increment packet number
    INC XMODEM_PKT_NUM

    ; Send ACK
    LDA #ACK
    JSR UART_SEND

    ; Reset retry counter
    LDA #0
    STA XMODEM_RETRY

    JMP @WAIT_PKT

@BAD_HEADER:
    LDA #'E'
    JSR CHROUT
    LDA #'R'
    JSR CHROUT
    LDA #'R'
    JSR CHROUT
    LDA #':'
    JSR CHROUT
    LDA #'H'            ; Header error
    JSR CHROUT
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT
    JMP @SEND_NAK

@BAD_PKT_NUM:
    LDA #'E'
    JSR CHROUT
    LDA #'R'
    JSR CHROUT
    LDA #'R'
    JSR CHROUT
    LDA #':'
    JSR CHROUT
    LDA #'P'            ; Packet number error
    JSR CHROUT
    LDA #'='
    JSR CHROUT
    LDA TEMP            ; Show the packet number we received
    JSR PRINT_HEX
    LDA #' '
    JSR CHROUT
    LDA #'E'
    JSR CHROUT
    LDA #'='
    JSR CHROUT
    LDA XMODEM_PKT_NUM  ; Show what we expected
    JSR PRINT_HEX
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT
    JMP @SEND_NAK

@BAD_CHECKSUM:
    LDA #'E'
    JSR CHROUT
    LDA #'R'
    JSR CHROUT
    LDA #'R'
    JSR CHROUT
    LDA #':'
    JSR CHROUT
    LDA #'C'            ; Checksum error
    JSR CHROUT
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT
    JMP @SEND_NAK

@SEND_NAK:
    ; Send NAK immediately
    LDA #NAK
    JSR UART_SEND

    ; Increment retry counter
    INC XMODEM_RETRY
    LDA XMODEM_RETRY
    CMP #10
    BCC @RETRY_OK

    ; Too many retries - abort
    LDA #CAN
    JSR UART_SEND

    ; Restore output mode
    PLA
    STA IO_OUTPUT_MODE

    LDA #1              ; Error
    RTS

@RETRY_OK:
    ; Flush any stale data from UART buffer before waiting for retransmission
@FLUSH_LOOP:
    LDA UART_STATUS
    AND #$02
    BEQ @FLUSH_COMPLETE
    LDA UART_DATA       ; Discard byte
    JMP @FLUSH_LOOP
@FLUSH_COMPLETE:
    JMP @WAIT_PKT

@TIMEOUT:
    ; DEBUG: Show timeout with location, byte count, and last byte received
    LDA #'T'
    JSR CHROUT
    LDA #'O'
    JSR CHROUT
    ; Display location ID
    LDA XMODEM_TO_LOC
    CLC
    ADC #'0'            ; Convert to ASCII digit
    JSR CHROUT
    LDA #' '
    JSR CHROUT
    ; Display byte count in hex
    LDA XMODEM_BYTE_CNT
    JSR PRINT_HEX
    LDA #' '
    JSR CHROUT
    LDA #'L'
    JSR CHROUT
    LDA #'='
    JSR CHROUT
    ; Display last byte received in hex
    LDA XMODEM_LAST_BYTE
    JSR PRINT_HEX
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT

    ; Timeout - send NAK and retry
    LDA #NAK
    JSR UART_SEND

    INC XMODEM_RETRY
    LDA XMODEM_RETRY
    CMP #10
    BCC @RETRY_OK2

    ; Too many retries - abort
    LDA #CAN
    JSR UART_SEND

    ; Restore output mode
    PLA
    STA IO_OUTPUT_MODE

    LDA #1              ; Error
    RTS

@RETRY_OK2:
    JMP @WAIT_PKT

; ============================================================================
; CMD_IO_CONFIG - Configure I/O sources (Phase 4 - T030)
; Format: I <input_mode> <output_mode>
; Input modes: 0=UART, 1=PS2, 2=Both
; Output modes: 0=UART, 1=Display, 2=Both
; ============================================================================
CMD_IO_CONFIG:
    ; Skip spaces
    JSR SKIP_SPACES

    ; Read input mode digit
    LDA TEMP
    SEC
    SBC #'0'
    BCS @CHECK_INPUT_RANGE
    JMP @INVALID_INPUT

@CHECK_INPUT_RANGE:
    CMP #3
    BCS @INVALID_INPUT
    STA IO_INPUT_MODE

    ; Skip spaces
    JSR SKIP_SPACES

    ; Read output mode digit
    LDA TEMP
    SEC
    SBC #'0'
    BCS @CHECK_OUTPUT_RANGE
    JMP @INVALID_OUTPUT

@CHECK_OUTPUT_RANGE:
    CMP #3
    BCS @INVALID_OUTPUT
    STA IO_OUTPUT_MODE

    ; Print confirmation
    JSR PRINT_IO_CONFIG_CONFIRM
    JMP MAIN_LOOP

@INVALID_INPUT:
    LDX #0
@INVALID_INPUT_LOOP:
    LDA INVALID_INPUT_MSG,X
    BEQ @DONE_INVALID
    JSR CHROUT
    INX
    BNE @INVALID_INPUT_LOOP
@DONE_INVALID:
    JMP MAIN_LOOP

@INVALID_OUTPUT:
    LDX #0
@INVALID_OUTPUT_LOOP:
    LDA INVALID_OUTPUT_MSG,X
    BEQ @DONE_INVALID2
    JSR CHROUT
    INX
    BNE @INVALID_OUTPUT_LOOP
@DONE_INVALID2:
    JMP MAIN_LOOP

; ============================================================================
; CMD_STATUS - Display I/O status (Phase 4 - T053-T057)
; Format: S
; ============================================================================
CMD_STATUS:
    LDX #0
@STATUS_LOOP:
    LDA STATUS_MSG,X
    BEQ @SHOW_INPUT
    JSR CHROUT
    INX
    BNE @STATUS_LOOP

@SHOW_INPUT:
    ; Display input mode
    LDX #0
@INPUT_LABEL:
    LDA STATUS_INPUT_LABEL,X
    BEQ @INPUT_VALUE
    JSR CHROUT
    INX
    BNE @INPUT_LABEL

@INPUT_VALUE:
    LDA IO_INPUT_MODE
    BEQ @INPUT_UART
    CMP #1
    BEQ @INPUT_PS2

    ; Mode 2 - Both
    LDX #0
@INPUT_BOTH:
    LDA STATUS_BOTH,X
    BEQ @SHOW_OUTPUT
    JSR CHROUT
    INX
    BNE @INPUT_BOTH
    JMP @SHOW_OUTPUT

@INPUT_UART:
    LDX #0
@INPUT_UART_LOOP:
    LDA STATUS_UART,X
    BEQ @SHOW_OUTPUT
    JSR CHROUT
    INX
    BNE @INPUT_UART_LOOP
    JMP @SHOW_OUTPUT

@INPUT_PS2:
    LDX #0
@INPUT_PS2_LOOP:
    LDA STATUS_PS2,X
    BEQ @SHOW_OUTPUT
    JSR CHROUT
    INX
    BNE @INPUT_PS2_LOOP

@SHOW_OUTPUT:
    ; Display output mode
    LDX #0
@OUTPUT_LABEL:
    LDA STATUS_OUTPUT_LABEL,X
    BEQ @OUTPUT_VALUE
    JSR CHROUT
    INX
    BNE @OUTPUT_LABEL

@OUTPUT_VALUE:
    LDA IO_OUTPUT_MODE
    BEQ @OUTPUT_UART
    CMP #1
    BEQ @OUTPUT_DISPLAY

    ; Mode 2 - Both
    LDX #0
@OUTPUT_BOTH:
    LDA STATUS_BOTH,X
    BEQ @STATUS_DONE
    JSR CHROUT
    INX
    BNE @OUTPUT_BOTH
    JMP @STATUS_DONE

@OUTPUT_UART:
    LDX #0
@OUTPUT_UART_LOOP:
    LDA STATUS_UART,X
    BEQ @STATUS_DONE
    JSR CHROUT
    INX
    BNE @OUTPUT_UART_LOOP
    JMP @STATUS_DONE

@OUTPUT_DISPLAY:
    LDX #0
@OUTPUT_DISPLAY_LOOP:
    LDA STATUS_DISPLAY,X
    BEQ @STATUS_DONE
    JSR CHROUT
    INX
    BNE @OUTPUT_DISPLAY_LOOP

@STATUS_DONE:
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT
    JMP MAIN_LOOP

; ============================================================================
; CMD_MODE - Set display mode (40 or 80 column)
; Format: M 0 (40-column) or M 1 (80-column)
; ============================================================================
CMD_MODE:
    ; Skip spaces
    JSR SKIP_SPACES

    ; Check if we have a parameter (SKIP_SPACES puts char in TEMP)
    LDA TEMP
    CMP #$0D           ; End of input?
    BEQ @SHOW_CURRENT  ; No parameter, show current mode

    ; Convert from ASCII digit to value
    SEC
    SBC #'0'
    BCC @ERROR         ; Invalid if less than '0'

    ; Value is in A, check if 0 or 1
    CMP #2
    BCS @ERROR         ; Must be 0 or 1

    ; Save new mode
    STA GPU_MODE_VAR

    ; Write to GPU CONTROL register
    ; Bit 1 = MODE (0=40-col, 1=80-col)
    ; Bit 2 = CURSOR_EN (keep enabled = 1)
    ASL A              ; Shift mode into bit 1
    ORA #%00000100     ; Set CURSOR_EN bit (bit 2)
    STA GPU_MODE

    ; Print confirmation
    LDX #0
@MODE_MSG:
    LDA MODE_SET_MSG,X
    BEQ @DONE_MODE
    JSR CHROUT
    INX
    BNE @MODE_MSG
@DONE_MODE:
    JMP MAIN_LOOP

@SHOW_CURRENT:
    ; Show current mode
    LDX #0
@CURRENT_MSG:
    LDA MODE_CURRENT_MSG,X
    BEQ @SHOW_VALUE
    JSR CHROUT
    INX
    BNE @CURRENT_MSG

@SHOW_VALUE:
    LDA GPU_MODE_VAR
    BEQ @MODE_40

    ; 80-column mode
    LDX #0
@MODE_80_LOOP:
    LDA MODE_80_MSG,X
    BEQ @DONE_SHOW
    JSR CHROUT
    INX
    BNE @MODE_80_LOOP
    JMP @DONE_SHOW

@MODE_40:
    ; 40-column mode
    LDX #0
@MODE_40_LOOP:
    LDA MODE_40_MSG,X
    BEQ @DONE_SHOW
    JSR CHROUT
    INX
    BNE @MODE_40_LOOP

@DONE_SHOW:
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT
    JMP MAIN_LOOP

@ERROR:
    LDX #0
@ERROR_LOOP:
    LDA MODE_ERROR_MSG,X
    BEQ @ERROR_DONE
    JSR CHROUT
    INX
    BNE @ERROR_LOOP
@ERROR_DONE:
    JMP MAIN_LOOP

; ============================================================================
; PRINT_IO_CONFIG_CONFIRM - Print I/O configuration confirmation
; Phase 4 - Uses IO_INPUT_MODE and IO_OUTPUT_MODE
; ============================================================================
PRINT_IO_CONFIG_CONFIRM:
    ; Print "I/O Config: IN="
    LDX #0
@PREFIX_LOOP:
    LDA CONFIG_PREFIX,X
    BEQ @PRINT_INPUT
    JSR CHROUT
    INX
    BNE @PREFIX_LOOP

@PRINT_INPUT:
    ; Print input mode name
    LDA IO_INPUT_MODE
    BEQ @INPUT_UART
    CMP #1
    BEQ @INPUT_PS2

    ; Mode 2 - Both
    LDX #0
@INPUT_BOTH:
    LDA CONFIG_BOTH,X
    BEQ @PRINT_MID
    JSR CHROUT
    INX
    BNE @INPUT_BOTH
    JMP @PRINT_MID

@INPUT_UART:
    LDX #0
@INPUT_UART_LOOP:
    LDA CONFIG_UART,X
    BEQ @PRINT_MID
    JSR CHROUT
    INX
    BNE @INPUT_UART_LOOP
    JMP @PRINT_MID

@INPUT_PS2:
    LDX #0
@INPUT_PS2_LOOP:
    LDA CONFIG_PS2,X
    BEQ @PRINT_MID
    JSR CHROUT
    INX
    BNE @INPUT_PS2_LOOP

@PRINT_MID:
    ; Print ", OUT="
    LDX #0
@MID_LOOP:
    LDA CONFIG_MID,X
    BEQ @PRINT_OUTPUT
    JSR CHROUT
    INX
    BNE @MID_LOOP

@PRINT_OUTPUT:
    ; Print output mode name
    LDA IO_OUTPUT_MODE
    BEQ @OUTPUT_UART
    CMP #1
    BEQ @OUTPUT_DISPLAY

    ; Mode 2 - Both
    LDX #0
@OUTPUT_BOTH:
    LDA CONFIG_BOTH,X
    BEQ @PRINT_NEWLINE
    JSR CHROUT
    INX
    BNE @OUTPUT_BOTH
    JMP @PRINT_NEWLINE

@OUTPUT_UART:
    LDX #0
@OUTPUT_UART_LOOP:
    LDA CONFIG_UART,X
    BEQ @PRINT_NEWLINE
    JSR CHROUT
    INX
    BNE @OUTPUT_UART_LOOP
    JMP @PRINT_NEWLINE

@OUTPUT_DISPLAY:
    LDX #0
@OUTPUT_DISPLAY_LOOP:
    LDA CONFIG_DISPLAY,X
    BEQ @PRINT_NEWLINE
    JSR CHROUT
    INX
    BNE @OUTPUT_DISPLAY_LOOP

@PRINT_NEWLINE:
    LDA #$0D
    JSR CHROUT
    LDA #$0A
    JSR CHROUT
    RTS

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
; UART_SEND - Send byte to UART (Phase 2 - T008)
; Input: A = byte to send
; Preserves: X, Y
; ============================================================================
UART_SEND:
    PHA                ; Save A
@WAIT:
    LDA UART_STATUS    ; Check TX ready
    AND #$01           ; Bit 0 = TX ready
    BEQ @WAIT          ; Wait if not ready
    PLA                ; Restore A
    STA UART_DATA      ; Send byte
    RTS

; ============================================================================
; CHROUT - Output character (Phase 2 - T007 Enhanced)
; Input: A = character to output
; Uses IO_OUTPUT_MODE to route output
; Preserves: X, Y
; ============================================================================
CHROUT:
    PHA                ; Save character

    ; Check output mode
    LDA IO_OUTPUT_MODE
    BEQ @UART_ONLY
    CMP #1
    BEQ @DISPLAY_ONLY

    ; Mode 2 - Both UART and Display
    PLA
    PHA
    JSR @SEND_UART
    PLA
    PHA
    JSR @SEND_DISPLAY
    PLA
    RTS

@UART_ONLY:
    PLA
    JSR @SEND_UART
    RTS

@DISPLAY_ONLY:
    PLA
    JSR @SEND_DISPLAY
    RTS

@SEND_UART:
    PHA
@WAIT_TX:
    LDA UART_STATUS
    AND #$01
    BEQ @WAIT_TX
    PLA
    STA UART_DATA
    RTS

@SEND_DISPLAY:
    ; GPU handles CR/LF in hardware, just send all characters
    STA GPU_CHAR_DATA
    RTS

; ============================================================================
; CHRIN - Input character (Phase 2 - T006 Enhanced)
; Uses IO_INPUT_MODE to poll correct source(s)
; Output: A = character received
; Preserves: X, Y
; ============================================================================
CHRIN:
    ; Check input mode
    LDA IO_INPUT_MODE
    BEQ @UART_ONLY
    CMP #1
    BEQ @PS2_ONLY

    ; Mode 2 - Both (poll both, first-come-first-served)
@POLL_BOTH:
    ; Check PS/2 first
    LDA PS2_STATUS
    AND #$01
    BNE @READ_PS2

    ; Check UART
    LDA UART_STATUS
    AND #$02
    BNE @READ_UART

    ; Neither ready, keep polling
    JMP @POLL_BOTH

@UART_ONLY:
@WAIT_UART:
    LDA UART_STATUS
    AND #$02
    BEQ @WAIT_UART
@READ_UART:
    LDA UART_DATA
    RTS

@PS2_ONLY:
@WAIT_PS2:
    LDA PS2_STATUS
    AND #$01
    BEQ @WAIT_PS2
@READ_PS2:
    LDA PS2_DATA
    JSR PS2_TO_ASCII
    BEQ @PS2_ONLY      ; If returned 0, try again
    RTS

; ============================================================================
; CHRIN_TIMEOUT - Input character with timeout for XMODEM
; Output: A = character received, Carry clear if success
;         Carry set if timeout
; Preserves: X, Y
; Simple timeout implementation (not precise, but functional)
; ============================================================================
CHRIN_TIMEOUT:
    ; Per-byte timeout for XMODEM: ~20ms (20x safety margin for 1ms/byte at 9600 baud)
    ; At 25MHz: ~20ms = 500,000 cycles / 30 cycles per iteration = ~16,666 iterations
    ; Use 256 * 80 = 20,480 iterations for ~25ms timeout
    ; NOTE: Uses TIMEOUT_COUNTER instead of Y to preserve Y register for caller
    LDA #$00
    STA TIMEOUT_COUNTER  ; Outer loop counter

@TIMEOUT_OUTER:
    LDX #$00             ; Inner loop counter

@TIMEOUT_LOOP:
    ; Check if data available
    LDA UART_STATUS
    AND #$02
    BNE @DATA_READY

    ; Delay to avoid hammering UART status register
    NOP
    NOP

    ; Inner loop
    INX
    BNE @TIMEOUT_LOOP

    ; Outer loop - 80 iterations
    INC TIMEOUT_COUNTER
    LDA TIMEOUT_COUNTER
    CMP #$50             ; 80 decimal = 0x50
    BNE @TIMEOUT_OUTER

    ; Timeout occurred
    SEC
    RTS

@DATA_READY:
    LDA UART_DATA
    STA XMODEM_LAST_BYTE  ; Save for debugging
    CLC
    RTS

; ============================================================================
; PS2_TO_ASCII - Convert PS/2 scancode to ASCII (Phase 4 - T029)
; Input: A = PS/2 scancode
; Output: A = ASCII character (or 0 if should be ignored)
; Uses: PS2_BREAK, PS2_SHIFT, PS2_CAPS
; ============================================================================
PS2_TO_ASCII:
    ; Check for break code prefix (0xF0)
    CMP #$F0
    BNE @NOT_BREAK
    LDA #1
    STA PS2_BREAK
    LDA #0              ; Return 0 (ignore)
    RTS

@NOT_BREAK:
    ; Check if this is a break code (release)
    LDX PS2_BREAK
    BEQ @MAKE_CODE

    ; Break code - clear flag
    LDX #0
    STX PS2_BREAK

    ; Check for shift key release
    CMP #$12            ; Left Shift
    BEQ @CLEAR_SHIFT
    CMP #$59            ; Right Shift
    BEQ @CLEAR_SHIFT

    LDA #0              ; Ignore other break codes
    RTS

@CLEAR_SHIFT:
    LDX #0
    STX PS2_SHIFT
    LDA #0
    RTS

@MAKE_CODE:
    ; Check for shift key press
    CMP #$12            ; Left Shift
    BEQ @SET_SHIFT
    CMP #$59            ; Right Shift
    BEQ @SET_SHIFT

    ; Check for Caps Lock toggle
    CMP #$58            ; Caps Lock
    BNE @NOT_CAPS
    LDA PS2_CAPS
    EOR #1
    STA PS2_CAPS
    LDA #0
    RTS

@SET_SHIFT:
    LDA #1
    STA PS2_SHIFT
    LDA #0
    RTS

@NOT_CAPS:
    ; Lookup in translation table
    TAX
    LDA PS2_XLAT_TABLE,X
    BEQ @UNMAPPED

    ; Check if letter and apply shift/caps
    CMP #$61            ; 'a'
    BCC @NOT_LETTER
    CMP #$7B            ; 'z'+1
    BCS @NOT_LETTER

    ; It's a letter - check shift or caps
    TAY                 ; Save ASCII
    LDA PS2_SHIFT
    ORA PS2_CAPS
    BEQ @NO_UPPER

    ; Convert to uppercase
    TYA
    SEC
    SBC #$20
    RTS

@NO_UPPER:
    TYA
    RTS

@NOT_LETTER:
    ; Not a letter - return as-is
    RTS

@UNMAPPED:
    LDA #0
    RTS

; ============================================================================
; INIT_PS2_TABLE - Initialize PS/2 scancode lookup table (Phase 2 - T009)
; Copies ROM data to RAM at $0280
; ============================================================================
INIT_PS2_TABLE:
    LDX #0
@COPY_LOOP:
    LDA PS2_XLAT_ROM,X
    STA PS2_XLAT_TABLE,X
    INX
    CPX #128
    BNE @COPY_LOOP
    RTS

; ============================================================================
; PRINT_WELCOME - Print welcome banner
; ============================================================================
PRINT_WELCOME:
    ; Set up pointer to WELCOME_MSG in zero page
    LDA #<WELCOME_MSG
    STA TEMP
    LDA #>WELCOME_MSG
    STA TEMP2

    LDY #0
@LOOP:
    LDA (TEMP),Y
    BEQ @DONE
    JSR CHROUT
    INY
    BNE @LOOP
    ; Y wrapped to 0, increment high byte of pointer
    INC TEMP2
    JMP @LOOP

@DONE:
    RTS

; ============================================================================
; LCD_INIT - Initialize HD44780 LCD in 4-bit mode
; Uses: A, X
; ============================================================================
LCD_INIT:
    ; Wait for LCD power-up and hardware init to complete
    ; Hardware init takes ~15-20ms, wait ~20ms total
    JSR LCD_DELAY_LONG
    JSR LCD_DELAY_LONG
    JSR LCD_DELAY_LONG
    JSR LCD_DELAY_LONG  ; 4 * 5ms = ~20ms

    ; Clear display (0x01) - needs longer delay
    LDA #$01
    STA LCD_CMD
    JSR LCD_DELAY_LONG  ; Clear needs ~2ms

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
; LCD_DELAY_LONG - Long delay for LCD clear/init commands (~5ms)
; Uses: X, Y
; ============================================================================
LCD_DELAY_LONG:
    ; Nested delay loops for ~5ms at 25 MHz
    ; Outer loop: 160 iterations
    ; Inner loop: 255 iterations each
    ; Total: ~160 * 255 * 3 cycles = ~122,400 cycles = ~4.9ms

    LDY #160       ; Outer loop counter
@OUTER:
    LDX #$FF       ; Inner loop counter
@INNER:
    DEX
    BNE @INNER
    DEY
    BNE @OUTER
    RTS

; ============================================================================
; LCD_DELAY - Standard delay for LCD commands and characters (~1ms)
; Uses: X, Y
; ============================================================================
LCD_DELAY:
    ; Nested delay loops for ~1ms at 25 MHz
    ; Outer loop: 32 iterations
    ; Inner loop: 255 iterations each
    ; Total: ~32 * 255 * 3 cycles = ~24,480 cycles = ~0.98ms

    LDY #32        ; Outer loop counter
@OUTER:
    LDX #$FF       ; Inner loop counter
@INNER:
    DEX
    BNE @INNER
    DEY
    BNE @OUTER
    RTS

; ============================================================================
; LCD_BOOT_MSG - Display boot message on LCD
; Uses: A, X, Y
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

    ; Save X before LCD_DELAY (which clobbers X)
    TXA
    PHA
    JSR LCD_DELAY
    PLA
    TAX

    INX
    CPX #16            ; Limit to 16 chars
    BNE @LINE1

@LINE2_START:
    ; Set cursor to line 2, column 0 (0xC0)
    LDA #$C0
    STA LCD_CMD
    JSR LCD_DELAY

    ; Print "Monitor v2.0" on line 2
    LDX #0
@LINE2:
    LDA LCD_MSG_LINE2,X
    BEQ @DONE

    STA LCD_DATA

    ; Save X before LCD_DELAY (which clobbers X)
    TXA
    PHA
    JSR LCD_DELAY
    PLA
    TAX

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
    .byte $0D, $0A
    .byte "RetroCPU Monitor v2.0", $0D, $0A
    .byte $0D, $0A
    .byte "6502 FPGA Microcomputer", $0D, $0A
    .byte "(c) 2025 - Educational Project", $0D, $0A
    .byte $0D, $0A
    .byte "Commands:", $0D, $0A
    .byte "  E <addr>      - Examine memory", $0D, $0A
    .byte "  D <addr> <val> - Deposit value", $0D, $0A
    .byte "  G             - Go to BASIC", $0D, $0A
    .byte "  H             - Help", $0D, $0A
    .byte "  J             - Jump to/execute code at $0300", $0D, $0A
    .byte "  L             - Load binary (XMODEM)", $0D, $0A
    .byte "  M <mode>      - Display mode (0=40col, 1=80col)", $0D, $0A
    .byte "  I <in> <out>  - Configure I/O", $0D, $0A
    .byte "  S             - Status", $0D, $0A
    .byte $0D, $0A
    .byte 0

LCD_MSG_LINE1:
    .byte "RetroCPU 6502   ", 0

LCD_MSG_LINE2:
    .byte "Monitor v2.0    ", 0

RX_DEBUG_PREFIX:
    .byte "Received: '", 0

HEX_PREFIX:
    .byte "' (0x", 0

UNKNOWN_MSG:
    .byte "Unknown command", $0D, $0A
    .byte 0

ERROR_MSG:
    .byte "Syntax error", $0D, $0A
    .byte 0

GO_MSG:
    .byte "Starting BASIC...", $0D, $0A
    .byte 0

JUMP_MSG:
    .byte "Executing at $0300...", $0D, $0A, 0

JUMP_DONE_MSG:
    .byte "Execution complete", $0D, $0A, 0

HELP_MSG:
    .byte $0D, $0A
    .byte "RetroCPU Monitor Commands:", $0D, $0A
    .byte "  E <addr>        - Examine memory", $0D, $0A
    .byte "  D <addr> <val>  - Deposit value", $0D, $0A
    .byte "  G               - Go to BASIC", $0D, $0A
    .byte "  H               - Help", $0D, $0A
    .byte "  J               - Jump to/execute code at $0300", $0D, $0A
    .byte "  L               - Load binary (XMODEM)", $0D, $0A
    .byte "  M <mode>        - Set display mode (0=40col, 1=80col)", $0D, $0A
    .byte "  I <in> <out>    - Configure I/O", $0D, $0A
    .byte "  S               - Status", $0D, $0A
    .byte $0D, $0A
    .byte "I/O Modes: 0=UART, 1=PS2/Display, 2=Both", $0D, $0A
    .byte $0D, $0A
    .byte 0

DEBUG_START_MSG:
    .byte "*** XMODEM DEBUG START ***", $0D, $0A
    .byte 0

LOAD_READY_MSG:
    .byte "Ready for XMODEM transfer...", $0D, $0A
    .byte 0

LOAD_SUCCESS_MSG:
    .byte "Transfer complete!", $0D, $0A
    .byte 0

LOAD_ERROR_MSG:
    .byte "Transfer failed!", $0D, $0A
    .byte 0

TEST_PROMPT_MSG:
    .byte "Waiting for 26 bytes...", $0D, $0A
    .byte 0

INVALID_INPUT_MSG:
    .byte "Invalid input mode (0=UART, 1=PS2, 2=Both)", $0D, $0A
    .byte 0

INVALID_OUTPUT_MSG:
    .byte "Invalid output mode (0=UART, 1=Display, 2=Both)", $0D, $0A
    .byte 0

CONFIG_PREFIX:
    .byte "I/O Config: IN=", 0

CONFIG_MID:
    .byte ", OUT=", 0

CONFIG_UART:
    .byte "UART", 0

CONFIG_PS2:
    .byte "PS2", 0

CONFIG_DISPLAY:
    .byte "Display", 0

CONFIG_BOTH:
    .byte "Both", 0

MODE_SET_MSG:
    .byte "Display mode set", $0D, $0A
    .byte 0

MODE_CURRENT_MSG:
    .byte "Current mode: ", 0

MODE_40_MSG:
    .byte "40-column", 0

MODE_80_MSG:
    .byte "80-column", 0

MODE_ERROR_MSG:
    .byte "Invalid mode (use 0 or 1)", $0D, $0A
    .byte 0

STATUS_MSG:
    .byte "I/O Status:", $0D, $0A
    .byte 0

STATUS_INPUT_LABEL:
    .byte "  Input:  ", 0

STATUS_OUTPUT_LABEL:
    .byte $0D, $0A, "  Output: ", 0

STATUS_UART:
    .byte "UART", 0

STATUS_PS2:
    .byte "PS/2", 0

STATUS_DISPLAY:
    .byte "Display", 0

STATUS_BOTH:
    .byte "UART + PS/2", 0

; ============================================================================
; PS/2 Scancode to ASCII Translation Table (ROM) - Phase 1 - T004
; 128 bytes mapping scancode to ASCII (unshifted)
; ============================================================================
PS2_XLAT_ROM:
    ; 0x00-0x0F
    .byte $00, $00, $00, $00, $00, $00, $00, $00
    .byte $00, $00, $00, $00, $00, $09, $60, $00  ; 0x0D=Tab, 0x0E=`

    ; 0x10-0x1F
    .byte $00, $00, $00, $00, $00, $71, $31, $00  ; 0x15='q', 0x16='1'
    .byte $00, $00, $7A, $73, $61, $77, $32, $00  ; 0x1A='z', 0x1B='s', 0x1C='a', 0x1D='w', 0x1E='2'

    ; 0x20-0x2F
    .byte $00, $63, $78, $64, $65, $34, $33, $00  ; 0x21='c', 0x22='x', 0x23='d', 0x24='e', 0x25='4', 0x26='3'
    .byte $00, $20, $76, $66, $74, $72, $35, $00  ; 0x29=' ', 0x2A='v', 0x2B='f', 0x2C='t', 0x2D='r', 0x2E='5'

    ; 0x30-0x3F
    .byte $00, $6E, $62, $68, $67, $79, $36, $00  ; 0x31='n', 0x32='b', 0x33='h', 0x34='g', 0x35='y', 0x36='6'
    .byte $00, $00, $6D, $6A, $75, $37, $38, $00  ; 0x3A='m', 0x3B='j', 0x3C='u', 0x3D='7', 0x3E='8'

    ; 0x40-0x4F
    .byte $00, $2C, $6B, $69, $6F, $30, $39, $00  ; 0x41=',', 0x42='k', 0x43='i', 0x44='o', 0x45='0', 0x46='9'
    .byte $00, $2E, $2F, $6C, $3B, $70, $2D, $00  ; 0x49='.', 0x4A='/', 0x4B='l', 0x4C=';', 0x4D='p', 0x4E='-'

    ; 0x50-0x5F
    .byte $00, $00, $27, $00, $5B, $3D, $00, $00  ; 0x52='\'', 0x54='[', 0x55='='
    .byte $00, $00, $0D, $5D, $00, $5C, $00, $00  ; 0x5A=Enter, 0x5B=']', 0x5D='\\'

    ; 0x60-0x6F
    .byte $00, $00, $00, $00, $00, $00, $08, $00  ; 0x66=Backspace
    .byte $00, $00, $00, $00, $00, $00, $00, $00

    ; 0x70-0x7F
    .byte $00, $00, $00, $00, $00, $00, $1B, $00  ; 0x76=Escape
    .byte $00, $00, $00, $00, $00, $00, $00, $00

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
