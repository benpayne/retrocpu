; Demo BASIC - Simple BASIC-like interpreter for testing
; Responds to simple commands to verify UART RX works

; Monitor I/O vectors
VEC_CHRIN  = $FFF0
VEC_CHROUT = $FFF3

.segment "CODE"
.org $8000

; Entry point - called from monitor G command
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

    ; Check for PRINT command
    LDA input_buffer
    CMP #'P'
    BEQ @check_print

    ; Check for LIST command
    CMP #'L'
    BEQ @cmd_list

    ; Check for NEW command
    CMP #'N'
    BEQ @cmd_new

    ; Check for RUN command
    CMP #'R'
    BEQ @cmd_run

    ; Unknown command
    JMP @cmd_unknown

@check_print:
    ; Check if it's "PRINT"
    LDA input_buffer+1
    CMP #'R'
    BNE @cmd_unknown
    LDA input_buffer+2
    CMP #'I'
    BNE @cmd_unknown
    LDA input_buffer+3
    CMP #'N'
    BNE @cmd_unknown
    LDA input_buffer+4
    CMP #'T'
    BNE @cmd_unknown

    ; Handle PRINT command
    JMP @cmd_print

@cmd_print:
    ; Check for "PRINT 2+2"
    LDA input_buffer+6
    CMP #'2'
    BNE @print_general
    LDA input_buffer+7
    CMP #'+'
    BNE @print_general
    LDA input_buffer+8
    CMP #'2'
    BNE @print_general

    ; Print " 4"
    LDA #' '
    JSR VEC_CHROUT
    LDA #'4'
    JSR VEC_CHROUT
    JMP @cmd_done

@print_general:
    ; Just echo what's after PRINT
    LDX #6                  ; Start after "PRINT "
@print_loop:
    CPX input_len
    BCS @cmd_done
    LDA input_buffer,X
    JSR VEC_CHROUT
    INX
    JMP @print_loop

@cmd_list:
    ; LIST command
    LDX #0
@list_msg:
    LDA list_msg,X
    BEQ @cmd_done
    JSR VEC_CHROUT
    INX
    JMP @list_msg

@cmd_new:
    ; NEW command
    LDX #0
@new_msg:
    LDA new_msg,X
    BEQ @cmd_done
    JSR VEC_CHROUT
    INX
    JMP @new_msg

@cmd_run:
    ; RUN command
    LDX #0
@run_msg:
    LDA run_msg,X
    BEQ @cmd_done
    JSR VEC_CHROUT
    INX
    JMP @run_msg

@cmd_unknown:
    ; Print error
    LDX #0
@error_msg:
    LDA error_msg,X
    BEQ @cmd_done
    JSR VEC_CHROUT
    INX
    JMP @error_msg

@cmd_done:
    ; Print newline and loop
    LDA #$0D
    JSR VEC_CHROUT
    LDA #$0A
    JSR VEC_CHROUT
    JMP main_loop

; Messages
banner_msg:
    .byte $0D, $0A
    .byte "Demo BASIC v1.0", $0D, $0A
    .byte "Ready", $0D, $0A
    .byte $0D, $0A
    .byte 0

list_msg:
    .byte "No program in memory", 0

new_msg:
    .byte "Ready", 0

run_msg:
    .byte "No program to run", 0

error_msg:
    .byte "?Syntax error", 0

; Input buffer (in RAM via zero page)
.segment "BSS"
input_buffer: .res 40
input_len: .res 1
