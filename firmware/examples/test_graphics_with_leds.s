; Graphics mode test with LED debugging
; Uses writes to $0010 to show progress on LEDs
.setcpu "6502"

; Graphics GPU registers
GPU_VRAM_ADDR_LO  = $C100
GPU_VRAM_ADDR_HI  = $C101
GPU_VRAM_DATA     = $C102
GPU_VRAM_CTRL     = $C103
GPU_MODE          = $C106
GPU_CLUT_INDEX    = $C107
GPU_CLUT_DATA_R   = $C108
GPU_CLUT_DATA_G   = $C109
GPU_CLUT_DATA_B   = $C10A
GPU_DISPLAY_MODE  = $C10D

; LED debug register
DEBUG_LEDS        = $0010

.org $0300

start:
    CLD

    ; LED Pattern 1: Program started (write $01 to $0010)
    ; led[0]=1, led[1]=1
    LDA #$01
    STA DEBUG_LEDS

    ; Set up palette entry 0 (black)
    LDA #$00
    STA GPU_CLUT_INDEX
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; Set up palette entry 1 (white)
    LDA #$01
    STA GPU_CLUT_INDEX
    LDA #$0F
    STA GPU_CLUT_DATA_R
    STA GPU_CLUT_DATA_G
    STA GPU_CLUT_DATA_B

    ; LED Pattern 2: Palette configured (write $03 to $0010)
    ; led[0]=1, led[1]=1
    LDA #$03
    STA DEBUG_LEDS

    ; Set 1 BPP mode
    LDA #$00
    STA GPU_MODE

    ; Enable burst mode
    LDA #$01
    STA GPU_VRAM_CTRL

    ; Set VRAM address to 0
    LDA #$00
    STA GPU_VRAM_ADDR_LO
    STA GPU_VRAM_ADDR_HI

    ; LED Pattern 3: About to write VRAM (write $07 to $0010)
    ; led[0]=1, led[1]=1, led[2]=?
    LDA #$07
    STA DEBUG_LEDS

    ; Write simple pattern to first 256 bytes of VRAM
    LDX #0
write_loop:
    LDA #$FF                ; All pixels white
    STA GPU_VRAM_DATA
    INX
    BNE write_loop

    ; LED Pattern 4: VRAM written (write $0F to $0010)
    ; All LEDs that can be on
    LDA #$0F
    STA DEBUG_LEDS

    ; Now switch to graphics mode
    ; THIS IS THE CRITICAL WRITE
    LDA #$01
    STA GPU_DISPLAY_MODE

    ; LED Pattern 5: Switched to graphics (write $1F to $0010)
    LDA #$1F
    STA DEBUG_LEDS

done:
    ; Keep writing alternating patterns so LEDs flash
    LDA #$FF
flash_loop:
    STA DEBUG_LEDS
    EOR #$FF                ; Toggle all bits
    ; Small delay
    LDY #$FF
delay:
    DEY
    BNE delay
    JMP flash_loop          ; Keep flashing
