; Demo BASIC - Debug Version
; Shows what's in the buffer to help debug parsing

; Monitor I/O vectors
VEC_CHRIN  = $FFF0
VEC_CHROUT = $FFF3

.segment "CODE"
.org $8000

; Entry point
basic_entry:
    ; Print BASIC banner
    LDX #0
@print_banner:
    LDA banner_msg,X
    BEQ @banner_done
    JSR VEC_CHROUT
    INX
    JMP @print_banner

@banner_done:
    ; Main command loop
main_loop:
    ; Print prompt
    LDA #'>'
    JSR VEC_CHROUT
    LDA #' '
    JSR VEC_CHROUT

    ; Read command line into buffer
    LDX #0
@read_line:
    JSR VEC_CHRIN           ; Get character
    CMP #$0D                ; Check for Enter
    BEQ @process_command
    CMP #$08                ; Check for backspace
    BEQ @handle_backspace

    ; Echo character and store
    JSR VEC_CHROUT
    STA input_buffer,X
    INX
    CPX #40                 ; Max 40 characters
    BCC @read_line
    JMP @process_command

@handle_backspace:
    CPX #0
    BEQ @read_line          ; Ignore if buffer empty
    DEX
    ; Send backspace sequence: BS, space, BS
    LDA #$08
    JSR VEC_CHROUT
    LDA #' '
    JSR VEC_CHROUT
    LDA #$08
    JSR VEC_CHROUT
    JMP @read_line

@process_command:
    STX input_len           ; Store length

    ; Print newline
    LDA #$0D
    JSR VEC_CHROUT
    LDA #$0A
    JSR VEC_CHROUT

    ; Check if empty
    CPX #0
    BEQ main_loop

    ; DEBUG: Print buffer contents
    LDX #0
@debug_print_msg:
    LDA debug_msg,X
    BEQ @debug_print_buffer
    JSR VEC_CHROUT
    INX
    JMP @debug_print_msg

@debug_print_buffer:
    LDX #0
@debug_loop:
    CPX input_len
    BCS @debug_done
    LDA input_buffer,X
    JSR print_hex           ; Print as hex
    LDA #' '
    JSR VEC_CHROUT
    INX
    JMP @debug_loop

@debug_done:
    LDA #$0D
    JSR VEC_CHROUT
    LDA #$0A
    JSR VEC_CHROUT

    ; Now do simple command check
    LDA input_buffer
    CMP #'P'
    BEQ @maybe_print
    CMP #'L'
    BEQ @maybe_list
    JMP @cmd_unknown

@maybe_print:
    LDX #0
@print_msg:
    LDA print_msg,X
    BEQ @cmd_done
    JSR VEC_CHROUT
    INX
    JMP @print_msg

@maybe_list:
    LDX #0
@list_msg_loop:
    LDA list_msg,X
    BEQ @cmd_done
    JSR VEC_CHROUT
    INX
    JMP @list_msg_loop

@cmd_unknown:
    LDX #0
@error_msg:
    LDA error_msg,X
    BEQ @cmd_done
    JSR VEC_CHROUT
    INX
    JMP @error_msg

@cmd_done:
    LDA #$0D
    JSR VEC_CHROUT
    LDA #$0A
    JSR VEC_CHROUT
    JMP main_loop

; Print byte in A as hex
print_hex:
    PHA
    LSR A
    LSR A
    LSR A
    LSR A
    JSR print_hex_nibble
    PLA
    AND #$0F
    JSR print_hex_nibble
    RTS

print_hex_nibble:
    CMP #10
    BCC @digit
    ; A-F
    CLC
    ADC #('A'-10)
    JSR VEC_CHROUT
    RTS
@digit:
    ; 0-9
    CLC
    ADC #'0'
    JSR VEC_CHROUT
    RTS

; Messages
banner_msg:
    .byte $0D, $0A
    .byte "Demo BASIC v1.1 (Debug)", $0D, $0A
    .byte "Ready", $0D, $0A
    .byte $0D, $0A
    .byte 0

debug_msg:
    .byte "Buffer (hex): ", 0

print_msg:
    .byte "Got PRINT command", 0

list_msg:
    .byte "Got LIST command", 0

error_msg:
    .byte "?Syntax error", 0

; Input buffer (in RAM)
.segment "BSS"
input_buffer: .res 40
input_len: .res 1
