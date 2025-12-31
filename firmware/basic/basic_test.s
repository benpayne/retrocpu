; ============================================================================
; Simple BASIC ROM Test Program
; Prints "BASIC WORKS!" repeatedly to verify system
; ============================================================================

.setcpu "6502"

; Monitor I/O vectors (JMP instructions in monitor ROM)
VEC_CHRIN  = $FFF0  ; JMP to CHRIN
VEC_CHROUT = $FFF3  ; JMP to CHROUT

; ============================================================================
; BASIC ROM starts at $8000
; ============================================================================

.segment "CODE"
.org $8000

; Entry point - called from monitor's G command
BASIC_START:
    ; Print welcome message
    LDX #0
@PRINT_MSG:
    LDA TEST_MSG,X
    BEQ @START_ECHO
    JSR VEC_CHROUT  ; Call monitor's CHROUT via vector
    INX
    BNE @PRINT_MSG

@START_ECHO:
    ; Echo characters back to user
@ECHO_LOOP:
    JSR VEC_CHRIN   ; Get character from input
    JSR VEC_CHROUT  ; Echo it back
    JMP @ECHO_LOOP  ; Loop forever (unconditional)

TEST_MSG:
    .byte $0D, $0A
    .byte "BASIC ROM Test - Interactive Echo", $0D, $0A
    .byte "Type characters to see them echoed...", $0D, $0A
    .byte $0D, $0A
    .byte 0

; Fill rest of ROM with NOPs
.res $4000 - (* - $8000), $EA

; ============================================================================
; End of BASIC ROM at $BFFF
; ============================================================================
