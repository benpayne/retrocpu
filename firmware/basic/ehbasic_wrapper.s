; EhBASIC Wrapper for RetroCPU
; This file configures EhBASIC to use our monitor I/O routines

; Memory configuration for EhBASIC
; RAM: $0000-$7FFF (32KB)
; BASIC ROM: $8000-$BFFF (16KB)
; Monitor ROM: $E000-$FFFF (8KB with I/O vectors at $FFF0)

; Configure EhBASIC I/O vectors to use monitor routines
VEC_IN  = $FFF0    ; Monitor CHRIN (character input)
VEC_OUT = $FFF3    ; Monitor CHROUT (character output)
VEC_LOAD = $FFF6   ; Monitor LOAD (not implemented, return)
VEC_SAVE = $FFF9   ; Monitor SAVE (not implemented, return)

; EhBASIC configuration
RAM_TOP = $8000    ; Top of RAM (BASIC uses $0000-$7FFF)

.segment "BASIC"   ; This goes to $8000-$BFFF

; EhBASIC cold start entry point
basic_cold_start:
    ; Initialize EhBASIC
    CLD                 ; Clear decimal mode
    LDX #$FF            ; Initialize stack
    TXS

    ; Set up EhBASIC I/O vectors
    LDA #<input_char
    STA LAB_INPT
    LDA #>input_char
    STA LAB_INPT+1

    LDA #<output_char
    STA LAB_OUTP
    LDA #>output_char
    STA LAB_OUTP+1

    LDA #<load_
```rout
    STA LAB_LOAD
    LDA #>load_rout
    STA LAB_LOAD+1

    LDA #<save_rout
    STA LAB_SAVE
    LDA #>save_rout
    STA LAB_SAVE+1

    ; Jump to EhBASIC initialization
    JMP LAB_COLD

; I/O routines that call monitor
input_char:
    JMP VEC_IN      ; Jump to monitor CHRIN

output_char:
    JMP VEC_OUT     ; Jump to monitor CHROUT

load_rout:
    RTS             ; Not implemented

save_rout:
    RTS             ; Not implemented

; Include EhBASIC source
.include "ehbasic.asm"
