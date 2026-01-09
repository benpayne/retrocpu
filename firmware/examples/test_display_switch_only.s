; Ultra-minimal test - just switch display mode
; Uses LEDs to show progress
.setcpu "6502"

; Graphics GPU registers
GPU_DISPLAY_MODE  = $C10D

; LED debug register
DEBUG_LEDS        = $0010

.org $0300

start:
    CLD

    ; LED Pattern 1: Starting ($AA)
    LDA #$AA
    STA DEBUG_LEDS

    ; Small delay so we can see LED pattern
    LDX #$FF
delay1:
    DEX
    BNE delay1

    ; LED Pattern 2: About to switch display ($55)
    LDA #$55
    STA DEBUG_LEDS

    ; Small delay
    LDX #$FF
delay2:
    DEX
    BNE delay2

    ; THIS IS THE TEST: Write to display mode register
    LDA #$01
    STA GPU_DISPLAY_MODE

    ; LED Pattern 3: After display switch ($0F)
    LDA #$0F
    STA DEBUG_LEDS

    ; Small delay
    LDX #$FF
delay3:
    DEX
    BNE delay3

    ; LED Pattern 4: Done ($00)
    LDA #$00
    STA DEBUG_LEDS

    ; Return to monitor
    RTS
