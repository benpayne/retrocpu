; ============================================================================
; Hello World Test Program
; Simple test program for XMODEM upload verification
;
; This program outputs "HELLO WORLD" via UART using the monitor CHROUT vector
; and then returns to the monitor.
;
; Usage:
;   1. Assemble this file to create hello_world.bin
;   2. Upload via XMODEM: L 0300
;   3. Execute: G 0300
;
; Expected output: "HELLO WORLD\r\n"
; ============================================================================

.setcpu "6502"

; Monitor I/O vectors (defined in monitor firmware)
CHROUT = $FFF3  ; Character output vector (JMP to monitor's CHROUT)

; This program will be loaded at $0300 (or any address specified in L command)
.org $0300

START:
    ; Print "HELLO WORLD" string
    LDX #0              ; Index into string

PRINT_LOOP:
    LDA MESSAGE,X       ; Load character from message
    BEQ DONE            ; If zero (null terminator), we're done

    JSR CHROUT          ; Call monitor CHROUT vector to output character

    INX                 ; Next character
    BNE PRINT_LOOP      ; Loop (BNE is safe since message < 256 bytes)

DONE:
    ; Print newline (CR + LF)
    LDA #$0D            ; Carriage return
    JSR CHROUT
    LDA #$0A            ; Line feed
    JSR CHROUT

    ; Return to monitor
    RTS

MESSAGE:
    .byte "HELLO WORLD", 0  ; Null-terminated string

; End of program
