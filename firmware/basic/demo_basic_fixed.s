; Demo BASIC - Fixed Version
; Explicitly place buffer in RAM at known addresses

; Monitor I/O vectors
VEC_CHRIN  = $FFF0
VEC_CHROUT = $FFF3

; RAM buffer locations (use low RAM that we know exists)
INPUT_BUFFER = $0200    ; Put buffer at $0200-$0227 (40 bytes)
INPUT_LEN    = $0228    ; Length byte at $0228

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
    STA INPUT_BUFFER,X
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
    STX INPUT_LEN           ; Store length

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
    CPX INPUT_LEN
    BCS @debug_done
    LDA INPUT_BUFFER,X
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

    ; Check first character
    LDA INPUT_BUFFER
    CMP #'P'
    BNE @not_p
    JMP @maybe_print
@not_p:
    CMP #'L'
    BNE @not_l
    JMP @maybe_list
@not_l:
    CMP #'N'
    BNE @not_n
    JMP @maybe_new
@not_n:
    CMP #'R'
    BEQ @do_run
    JMP @cmd_unknown
@do_run:
    JMP @maybe_run

@maybe_print:
    ; Check for "PRINT"
    LDX INPUT_LEN
    CPX #5
    BCS @print_check        ; Long enough
    JMP @cmd_unknown
@print_check:
    LDA INPUT_BUFFER+1
    CMP #'R'
    BEQ @print_r
    JMP @cmd_unknown
@print_r:
    LDA INPUT_BUFFER+2
    CMP #'I'
    BEQ @print_i
    JMP @cmd_unknown
@print_i:
    LDA INPUT_BUFFER+3
    CMP #'N'
    BEQ @print_n
    JMP @cmd_unknown
@print_n:
    LDA INPUT_BUFFER+4
    CMP #'T'
    BEQ @print_got_command
    JMP @cmd_unknown

@print_got_command:
    ; Got PRINT command
    ; Check for "PRINT 2+2"
    LDX INPUT_LEN
    CPX #9
    BEQ @check_2plus2
    JMP @print_general
@check_2plus2:
    LDA INPUT_BUFFER+6
    CMP #'2'
    BNE @print_general
    LDA INPUT_BUFFER+7
    CMP #'+'
    BNE @print_general
    LDA INPUT_BUFFER+8
    CMP #'2'
    BNE @print_general

    ; Print " 4"
    LDA #' '
    JSR VEC_CHROUT
    LDA #'4'
    JSR VEC_CHROUT
    JMP @cmd_done

@print_general:
    ; Echo what's after PRINT
    LDX #6
@print_loop:
    CPX INPUT_LEN
    BCS @cmd_done
    LDA INPUT_BUFFER,X
    JSR VEC_CHROUT
    INX
    JMP @print_loop

@maybe_list:
    LDX #0
@list_msg_loop:
    LDA list_msg,X
    BEQ @cmd_done
    JSR VEC_CHROUT
    INX
    JMP @list_msg_loop

@maybe_new:
    LDX #0
@new_msg_loop:
    LDA new_msg,X
    BEQ @cmd_done
    JSR VEC_CHROUT
    INX
    JMP @new_msg_loop

@maybe_run:
    LDX #0
@run_msg_loop:
    LDA run_msg,X
    BEQ @cmd_done
    JSR VEC_CHROUT
    INX
    JMP @run_msg_loop

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
    .byte "Demo BASIC v1.2 (Fixed RAM)", $0D, $0A
    .byte "Ready", $0D, $0A
    .byte $0D, $0A
    .byte 0

debug_msg:
    .byte "Buffer (hex): ", 0

list_msg:
    .byte "No program in memory", 0

new_msg:
    .byte "Ready", 0

run_msg:
    .byte "No program to run", 0

error_msg:
    .byte "?Syntax error", 0
