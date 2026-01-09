; Hello World example program for RetroCPU
; Demonstrates XMODEM upload and execution
;
; This program prints "Hello, World!" and returns to monitor

.segment "CODE"

; Program loaded at $0300 (typical user program area)
.org $0300

start:
    ; Print "Hello, World!" message
    LDX #0
print_loop:
    LDA message,X
    BEQ done           ; If zero, we're done
    JSR CHROUT         ; Print character via monitor
    INX
    JMP print_loop

done:
    ; Loop forever - user can reset to return to monitor
    JMP done

; CHROUT vector in monitor (sends character in A to output)
; This is the OSI BASIC I/O vector that JSRs to the actual CHROUT routine
CHROUT = $FFF3

message:
    .byte "Hello, World!", $0D, $0A, 0
