# Phase 1: Data Model - Program Loader and I/O Configuration

**Feature**: 004-program-loader-io-config
**Date**: 2026-01-01
**Status**: Complete

## Overview

This data model defines the memory layout, state variables, and data structures required for implementing program loading and I/O configuration in the RetroCPU monitor firmware and peripheral RTL.

## Memory Map

### Existing Peripherals (No Changes)

```
$C000: UART_DATA    - UART TX/RX data register
$C001: UART_STATUS  - Status (bit 0=TX ready, bit 1=RX ready)

$C010: GPU_CHAR_DATA - GPU character output register
$C011: GPU_CURSOR_ROW - Cursor row (0-29)
$C012: GPU_CURSOR_COL - Cursor column (0-39/79)
$C013: GPU_MODE      - Display mode and control

$C200: PS2_DATA      - PS/2 scan code data (read)
$C201: PS2_STATUS    - Status (bit 0=data ready, bit 1=interrupt)
```

### New Peripheral: I/O Controller (Optional RTL Enhancement)

If implementing RTL-based I/O multiplexing (Phase 2+ optional):

```
$C300: IO_CONFIG     - I/O configuration register
  Bits 0-1: Input mode  (00=UART, 01=PS2, 10=Both, 11=Reserved)
  Bits 2-3: Output mode (00=UART, 01=Display, 10=Both, 11=Reserved)
  Bits 4-7: Reserved (0)

$C301: IO_STATUS     - I/O status (read-only)
  Bit 0: Input available (from any configured source)
  Bit 1: PS/2 device detected
  Bit 2: GPU ready
  Bits 3-7: Reserved (0)
```

**Note**: For initial implementation (firmware polling), these registers are NOT needed. Configuration is stored in monitor RAM variables.

## Monitor Firmware Data Structures

### Zero Page Variables (Existing)

```
$00: TEMP        - Temporary storage
$01: TEMP2       - Temporary storage 2
$02: ADDR_LO     - 16-bit address low byte
$03: ADDR_HI     - 16-bit address high byte
$04: VALUE       - Byte value
$05: PS2_BREAK   - PS/2 break code flag
$10-$1F: INPUT_BUF (16 bytes) - Input buffer
$20: INPUT_LEN   - Input buffer length
```

### Zero Page Variables (New)

```
$21: IO_INPUT_MODE   - Input source (0=UART, 1=PS2, 2=Both)
$22: IO_OUTPUT_MODE  - Output dest (0=UART, 1=Display, 2=Both)

; XMODEM State Machine Variables
$23: XMODEM_STATE    - Current state (0=IDLE, 1=WAIT_SOH, 2=RECV_DATA, ...)
$24: XMODEM_PKT_NUM  - Expected packet number (1-255)
$25: XMODEM_CHECKSUM - Running checksum accumulator
$26: XMODEM_BYTE_CNT - Bytes received in current packet (0-127)
$27: XMODEM_RETRY_CNT - Retry counter for errors (max 10)
$28: XMODEM_ADDR_LO  - Target RAM address low byte
$29: XMODEM_ADDR_HI  - Target RAM address high byte
```

### RAM Buffers

```
$0200-$027F: XMODEM_BUFFER (128 bytes) - Packet data buffer
$0280-$02FF: PS2_XLAT_TABLE (128 bytes) - PS/2 scancode-to-ASCII lookup table
```

**Total Zero Page Usage**: $00-$29 (42 bytes)
**Total RAM Usage**: $0200-$02FF (256 bytes)

## XMODEM State Machine

### States

```c
enum xmodem_state {
    XMODEM_IDLE         = 0,  // Not in XMODEM mode
    XMODEM_WAIT_SOH     = 1,  // Waiting for Start of Header (0x01)
    XMODEM_RECV_PKT_NUM = 2,  // Receiving packet number
    XMODEM_RECV_PKT_INV = 3,  // Receiving packet number complement
    XMODEM_RECV_DATA    = 4,  // Receiving 128 data bytes
    XMODEM_RECV_CKSUM   = 5,  // Receiving checksum byte
    XMODEM_VERIFY       = 6,  // Verifying packet integrity
};
```

### State Transitions

```
IDLE → WAIT_SOH:        Monitor L command invoked
WAIT_SOH → RECV_PKT_NUM: Received SOH (0x01)
WAIT_SOH → IDLE:         Received EOT (0x04) or timeout
RECV_PKT_NUM → RECV_PKT_INV: Packet number received
RECV_PKT_INV → RECV_DATA: Complement verified
RECV_PKT_INV → WAIT_SOH: Complement error (send NAK)
RECV_DATA → RECV_CKSUM:  All 128 bytes received
RECV_CKSUM → VERIFY:     Checksum received
VERIFY → WAIT_SOH:       Success (send ACK) or error (send NAK)
```

### Control Characters

```
SOH (Start of Header):   0x01
EOT (End of Transmission): 0x04
ACK (Acknowledge):       0x06
NAK (Negative Acknowledge): 0x15
CAN (Cancel):            0x18
```

## PS/2 Scancode Translation

### Scancode Set 2 Mapping

The PS/2 peripheral outputs raw Scancode Set 2 codes. Monitor firmware must translate to ASCII.

**Key Categories**:

1. **Printable Characters (A-Z, 0-9, punctuation)**:
   - Direct lookup table: scancode → ASCII (lowercase)
   - Apply Shift modifier: ASCII ± offset

2. **Modifier Keys**:
   - Shift (Left=0x12, Right=0x59): Set SHIFT_FLAG
   - Caps Lock (0x58): Toggle CAPS_FLAG
   - Break codes (0xF0 prefix): Clear modifier flags

3. **Special Keys**:
   - Enter (0x5A) → CR (0x0D)
   - Backspace (0x66) → BS (0x08)
   - Space (0x29) → 0x20
   - Tab (0x0D) → TAB (0x09)

### Translation Algorithm

```
if scancode == 0xF0:
    PS2_BREAK = 1
    return  # Wait for next code

if PS2_BREAK:
    if scancode == SHIFT_LEFT or scancode == SHIFT_RIGHT:
        SHIFT_FLAG = 0
    PS2_BREAK = 0
    return  # Ignore break codes for other keys

if scancode == SHIFT_LEFT or scancode == SHIFT_RIGHT:
    SHIFT_FLAG = 1
    return

if scancode == CAPS_LOCK:
    CAPS_FLAG = CAPS_FLAG XOR 1
    return

ascii = PS2_XLAT_TABLE[scancode]

if SHIFT_FLAG or CAPS_FLAG:
    if ascii >= 'a' and ascii <= 'z':
        ascii = ascii - 0x20  # Uppercase

return ascii
```

### Lookup Table (Partial Example)

```
Scancode → ASCII (Unshifted)
0x1C → 'a'
0x32 → 'b'
0x21 → 'c'
...
0x45 → '0'
0x16 → '1'
...
0x5A → 0x0D (CR)
0x66 → 0x08 (BS)
0x29 → 0x20 (Space)
```

**Full table**: 128 bytes stored at $0280-$02FF

## I/O Routing Logic

### Input Multiplexing (Firmware Polling)

**CHRIN Function Enhancement**:

```asm
CHRIN:
    LDA IO_INPUT_MODE
    BEQ .uart_only        ; Mode 0: UART only
    CMP #1
    BEQ .ps2_only         ; Mode 1: PS/2 only
    ; Mode 2: Both (poll both sources)
.check_both:
    LDA UART_STATUS
    AND #$02              ; Bit 1 = RX ready
    BNE .read_uart
    LDA PS2_STATUS
    AND #$01              ; Bit 0 = data ready
    BNE .read_ps2
    JMP .check_both       ; Loop until data available

.uart_only:
    LDA UART_STATUS
    AND #$02
    BEQ .uart_only        ; Wait for data
.read_uart:
    LDA UART_DATA
    RTS

.ps2_only:
    LDA PS2_STATUS
    AND #$01
    BEQ .ps2_only         ; Wait for data
.read_ps2:
    LDA PS2_DATA
    JSR PS2_TO_ASCII      ; Translate scancode to ASCII
    RTS
```

### Output Routing (Firmware Multiplexing)

**CHROUT Function Enhancement**:

```asm
CHROUT:
    PHA                   ; Save character
    LDA IO_OUTPUT_MODE
    BEQ .uart_only        ; Mode 0: UART only
    CMP #1
    BEQ .display_only     ; Mode 1: Display only
    ; Mode 2: Both (output to both)
    PLA                   ; Restore character
    PHA                   ; Save again
    JSR UART_SEND         ; Send to UART
    PLA
    STA GPU_CHAR_DATA     ; Send to GPU
    RTS

.uart_only:
    PLA
    JSR UART_SEND
    RTS

.display_only:
    PLA
    STA GPU_CHAR_DATA
    RTS

UART_SEND:
    PHA                   ; Save character
.wait_tx_ready:
    LDA UART_STATUS
    AND #$01              ; Bit 0 = TX ready
    BEQ .wait_tx_ready
    PLA
    STA UART_DATA
    RTS
```

## Monitor Command Enhancements

### New Commands

**L (Load Binary)**:
```
Format: L <start_addr>
Example: L 0200
Action: Enter XMODEM receive mode, load binary to RAM starting at address
```

**I (I/O Config)**:
```
Format: I <in_mode> <out_mode>
Example: I 2 2  (input=both, output=both)
Values: 0=UART, 1=PS2/Display, 2=Both
Action: Set I/O routing configuration
```

**S (Status)**:
```
Format: S
Action: Display current I/O configuration and peripheral status
Output:
  IN: UART+PS2  OUT: UART+DISP
  PS2: READY  GPU: READY  UART: 9600
```

### Command Parser Addition

```asm
MAIN_LOOP:
    ; ... existing code ...
    LDA TEMP              ; Command character
    CMP #'L'
    BNE @TRY_L_LOWER
    JMP CMD_LOAD
@TRY_L_LOWER:
    CMP #'l'
    BNE @TRY_I
    JMP CMD_LOAD

@TRY_I:
    CMP #'I'
    BNE @TRY_I_LOWER
    JMP CMD_IO_CONFIG
@TRY_I_LOWER:
    CMP #'i'
    BNE @TRY_S
    JMP CMD_IO_CONFIG

@TRY_S:
    CMP #'S'
    BNE @TRY_S_LOWER
    JMP CMD_STATUS
@TRY_S_LOWER:
    CMP #'s'
    BNE @TRY_E          ; Continue with existing commands
    JMP CMD_STATUS
```

## Data Flow Diagrams

### XMODEM Binary Upload Flow

```
Terminal (Sender)           Monitor (Receiver)
      |                           |
      |<------- NAK --------------|  (Monitor sends NAK to start)
      |                           |
      |------ Packet 1 ---------->|  (SOH + PKT# + ~PKT# + Data[128] + CKSUM)
      |                           |--- Verify checksum
      |                           |--- Write data to RAM
      |<------- ACK --------------|
      |                           |
      |------ Packet 2 ---------->|
      |<------- ACK --------------|
      |                           |
      |         ...               |
      |                           |
      |------ EOT --------------->|  (End of transmission)
      |<------- ACK --------------|
      |                           |
```

### I/O Multiplexing Flow

```
Input Sources:
┌─────────┐
│ UART RX │──────┐
└─────────┘      │
                 v
           ┌───────────┐
           │ CHRIN     │────> ASCII character to monitor
           │ (polling) │
           └───────────┘
                 ^
┌─────────┐      │
│ PS2 KB  │──────┘ (with scancode→ASCII translation)
└─────────┘

Output Destinations:
                 ┌───────────┐
ASCII char ────> │ CHROUT    │──────> UART TX
                 │ (routing) │
                 └───────────┘──────> GPU CHAR_DATA
```

## Validation

### Data Integrity Checks

1. **XMODEM Checksum**: Simple 8-bit sum of 128 data bytes must match transmitted checksum
2. **Packet Number Sequence**: Packet numbers must increment sequentially (1, 2, 3, ..., 255, 1, ...)
3. **Packet Number Complement**: ~PKT# must equal 255 - PKT#
4. **Address Range**: Target RAM address must be in $0200-$7FFF (enforced before starting XMODEM)

### Error Handling

1. **Checksum Mismatch**: Send NAK, retry up to 10 times, then abort
2. **Packet Number Error**: Send NAK, retry (sender will retransmit same packet)
3. **Timeout**: Send NAK after 10 seconds of no data
4. **Too Many Retries**: Abort transfer, display error message, return to command prompt

## Configuration Persistence

**Default Configuration** (after reset):
```
IO_INPUT_MODE  = 0  (UART only)
IO_OUTPUT_MODE = 0  (UART only)
```

**Persistence**: Configuration variables stored in zero page RAM; lost on reset. Future enhancement could store in EEPROM or battery-backed RAM.

## Memory Budget

**Zero Page**: 42 bytes used (of 256 available)
**RAM Buffers**: 256 bytes ($0200-$02FF)
**ROM Code**:
- XMODEM implementation: ~300 bytes
- I/O routing enhancements: ~100 bytes
- PS/2 translation: ~150 bytes
- New commands (L/I/S): ~200 bytes
- **Total new code**: ~750 bytes

**ROM Availability**: Needs verification; monitor.s currently uses ~4KB of 8KB ROM space, so ~4KB available for new code.
