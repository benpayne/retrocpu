; EhBASIC Main File for RetroCPU
; Configures EhBASIC to use monitor I/O routines

; Zero page vectors that EhBASIC expects (in RAM)
VEC_IN  = $02    ; Input vector (2 bytes)
VEC_OUT = $04    ; Output vector (2 bytes)
VEC_LD  = $06    ; Load vector (2 bytes)
VEC_SV  = $08    ; Save vector (2 bytes)

; Monitor I/O routines (in monitor ROM at $FFF0-$FFFF)
MON_CHRIN  = $FFF0   ; Character input from monitor
MON_CHROUT = $FFF3   ; Character output from monitor

; BASIC program starts at $8000
.org $8000

; Cold start entry - Initialize and start BASIC
basic_entry:
    CLD                    ; Clear decimal mode
    LDX #$FF               ; Initialize stack
    TXS

    ; Set up I/O vectors in zero page to point to monitor routines
    LDA #<MON_CHRIN
    STA VEC_IN
    LDA #>MON_CHRIN
    STA VEC_IN+1

    LDA #<MON_CHROUT
    STA VEC_OUT
    LDA #>MON_CHROUT
    STA VEC_OUT+1

    ; Load/Save not implemented - point to RTS
    LDA #<dummy_rts
    STA VEC_LD
    STA VEC_SV
    LDA #>dummy_rts
    STA VEC_LD+1
    STA VEC_SV+1

    ; Jump to BASIC cold start
    JMP LAB_COLD

dummy_rts:
    RTS

; Include EhBASIC source code
.include "ehbasic.asm"
