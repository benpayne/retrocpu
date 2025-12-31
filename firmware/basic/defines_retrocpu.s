; ============================================================================
; RetroCPU Configuration for OSI BASIC
; Based on defines_osi.s from mist64/msbasic
;
; Key Changes for RetroCPU:
; - MONRDKEY: $FFEB → $FFF0 (maps to VEC_CHRIN in monitor)
; - MONCOUT:  $FFEE → $FFF3 (maps to VEC_CHROUT in monitor)
; - MONISCNTC: $FFF1 → $FFF6 (maps to VEC_LOAD in monitor, Ctrl-C check)
; - LOAD/SAVE: Point to monitor stubs at $FFF6/$FFF7
; ============================================================================

; OSI variant configuration
; Also define OSI so we inherit OSI-specific code sections
OSI := 1
CONFIG_10A := 1

; Feature flags
CONFIG_DATAFLG := 1       ; Include DATA statement support
CONFIG_NULL := 1          ; Include NULL handling
CONFIG_PRINT_CR := 1      ; Print CR when line end reached
CONFIG_SCRTCH_ORDER := 3  ; Scratch order
CONFIG_SMALL := 1         ; 6-digit floating point (smaller code size)

; Zero page allocation
; OSI BASIC uses these ranges for variables and workspace
ZP_START1 = $00
ZP_START2 = $0D
ZP_START3 = $5B
ZP_START4 = $65

; Extra ZP variables
USR := $000A              ; USR() function jump vector

; Constants
STACK_TOP       := $FC    ; 6502 stack top
SPACE_FOR_GOSUB := $33    ; Space reserved for GOSUB stack
NULL_MAX        := $0A    ; Maximum NULL count
WIDTH           := 72     ; Screen width for output formatting
WIDTH2          := 56     ; Secondary width setting

; Memory layout
RAMSTART2 := $0300        ; BASIC program storage starts here
                          ; $0000-$00FF: Zero page (CPU + BASIC variables)
                          ; $0100-$01FF: Stack
                          ; $0200-$02FF: System use / buffers
                          ; $0300-$7FFF: BASIC program and variable storage
                          ; $8000-$BFFF: BASIC ROM (this code)
                          ; $C000-$C0FF: UART registers
                          ; $E000-$FFFF: Monitor ROM + vectors

; Magic memory locations
L0200 := $0200            ; System buffer location

; ============================================================================
; RetroCPU Monitor I/O Vectors
; These map OSI BASIC's expected addresses to RetroCPU's actual addresses
; ============================================================================

; Character Input: Monitor provides VEC_CHRIN at $FFF0 (JMP to CHRIN routine)
MONRDKEY := $FFF0         ; Was $FFEB in OSI, now $FFF0 for RetroCPU

; Character Output: Monitor provides VEC_CHROUT at $FFF3 (JMP to CHROUT routine)
MONCOUT := $FFF3          ; Was $FFEE in OSI, now $FFF3 for RetroCPU

; Check for Ctrl-C: Monitor provides VEC_LOAD at $FFF6 (stub or Ctrl-C check)
MONISCNTC := $FFF6        ; Was $FFF1 in OSI, now $FFF6 for RetroCPU
                          ; Returns A=0 (no break) or A=FF (break detected)

; LOAD/SAVE: Not implemented on RetroCPU (no storage device)
; Monitor provides stub RTS at these addresses
LOAD := $FFF6             ; Was $FFF4 in OSI, now $FFF6 (same as MONISCNTC)
SAVE := $FFF7             ; Was $FFF7 in OSI, unchanged (monitor stub)
                          ; Both return immediately with no action

; ============================================================================
; Notes:
;
; 1. Zero Page Usage:
;    - OSI BASIC uses $00-$65 for variables and workspace
;    - Monitor uses $00-$20 for its own variables
;    - These ranges overlap but don't conflict because:
;      * Monitor runs first, sets up vectors, then jumps to BASIC
;      * BASIC takes over and reinitializes its ZP variables
;      * When returning to monitor (via reset), monitor reinitializes
;
; 2. I/O Vectors:
;    - All I/O goes through monitor's CHRIN/CHROUT routines
;    - Monitor handles UART hardware at $C000-$C001
;    - BASIC just calls through vectors, doesn't touch UART directly
;
; 3. Memory Map:
;    - BASIC programs stored from $0300 upward
;    - Variables stored after program text
;    - String space grows down from high RAM
;    - Total available: ~31KB ($0300-$7FFF)
;
; 4. Entry Point:
;    - Monitor "G" command jumps to $8000 (BASIC ROM start)
;    - BASIC cold start: Initialize everything, prompt for memory size
;    - BASIC warm start: Preserve program, reset stack and variables
; ============================================================================
