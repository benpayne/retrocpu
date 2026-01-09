# Phase 0: Research - Program Loader and I/O Configuration

**Feature**: 004-program-loader-io-config
**Date**: 2026-01-01
**Status**: Complete

## Research Questions

Based on the specification and technical context, the following areas require research to inform the implementation design:

1. **XMODEM Protocol Implementation**: How should XMODEM be implemented in 6502 assembly for resource-constrained firmware?
2. **PS/2 to ASCII Mapping**: What is the current PS/2 peripheral interface and how should scancodes be mapped to ASCII?
3. **GPU Character Output**: What is the GPU's character output interface and how should monitor output be routed to it?
4. **I/O Multiplexing Architecture**: What is the best approach for multiplexing input sources and routing output destinations?
5. **Flow Control Implementation**: How should XON/XOFF flow control be implemented for BASIC text pasting?
6. **Monitor Firmware Extension**: Where in the existing monitor.s should new commands and state machines be added?

## 1. XMODEM Protocol Implementation

### Protocol Overview

XMODEM is a simple error-checking protocol for serial file transfer:

- **Packet Structure**: 128-byte data blocks with header and checksum
- **Start of Header (SOH)**: 0x01
- **Packet Number**: Sequential 1-255, wraps to 1
- **Packet Number Complement**: 255 - packet_number
- **Data**: 128 bytes
- **Checksum**: Simple 8-bit sum of data bytes

**Packet Format**:
```
SOH | Packet# | ~Packet# | Data[128] | Checksum
 1  |    1    |     1    |    128    |     1     = 132 bytes total
```

### Transfer Sequence

**Receiver-Initiated**:
1. Receiver sends NAK (0x15) to start transfer
2. Sender transmits packet
3. Receiver validates checksum and packet number
4. Receiver sends ACK (0x06) if valid, NAK if error
5. Repeat until EOT (0x04) from sender
6. Receiver sends final ACK

### 6502 Assembly Considerations

**Memory Requirements**:
- 128-byte receive buffer for packet data
- State variables: packet number, checksum accumulator, byte counter
- Estimated code size: ~200-300 bytes

**Implementation Approach**:
- State machine with states: IDLE, WAIT_SOH, WAIT_PKT_NUM, RECEIVE_DATA, VERIFY_CHECKSUM
- Use zero page for state variables and counters
- Use 128-byte buffer in RAM ($0200-$027F recommended)
- Timeout handling via polling UART status register

**Error Handling**:
- Checksum mismatch: Send NAK, retry up to 10 times
- Timeout: Send NAK, retry
- Packet number out of sequence: Send NAK
- Abort on too many retries

### Reference Implementation

XMODEM sender/receiver can be tested using standard terminal emulators:
- **Tera Term**: Built-in XMODEM support (File → Transfer → XMODEM → Send)
- **minicom**: `Ctrl-A S` for XMODEM send
- **sx/rx commands**: Linux command-line XMODEM tools

**Example Terminal Usage**:
```bash
# Send file to RetroCPU
sx -X /path/to/program.bin < /dev/ttyUSB0 > /dev/ttyUSB0
```

## 2. PS/2 to ASCII Mapping

### Current PS/2 Peripheral Status

**Files to Investigate**:
- `rtl/peripherals/ps2/*.v` - PS/2 controller implementation
- Expected interface: scancode output register, data-ready flag

### PS/2 Scancode Set 2 (Standard)

**Mapping Strategy**:
- Most keyboards use Scancode Set 2 (default)
- Simple ASCII characters (A-Z, 0-9) map predictably
- Modifier keys (Shift, Ctrl, Alt) require state tracking
- Special keys (Enter=0x5A→0x0D, Backspace=0x66→0x08)

**Example Mapping**:
```
PS/2 Scancode → ASCII
0x1C (A)      → 0x61 ('a') or 0x41 ('A') if shifted
0x45 (0)      → 0x30 ('0')
0x5A (Enter)  → 0x0D (CR)
0x66 (Bksp)   → 0x08 (BS)
0x29 (Space)  → 0x20 (' ')
```

**Implementation Options**:
1. **Lookup Table**: 256-byte table in ROM (scancode → ASCII)
2. **Algorithmic**: Conditional logic for character ranges
3. **Hybrid**: Table for printable chars, logic for special keys

**Recommendation**: Lookup table for simplicity and educational clarity

### Modifier Key Handling

**State Tracking**:
- Shift: Set flag on make code (0x12, 0x59), clear on break code (0xF0 0x12)
- Caps Lock: Toggle flag on make code (0x58)
- Apply modifier to ASCII output based on flags

## 3. GPU Character Output Interface

### Expected GPU Interface

From feature 003-hdmi-character-display:

**Memory-Mapped Registers**:
```
$C000 - $C012: GPU Registers (character display control)
$C010: CHAR_DATA   - Write character to current position
$C011: CURSOR_ROW  - Cursor row position (0-29)
$C012: CURSOR_COL  - Cursor column position (0-39 or 0-79)
$C013: MODE        - Display mode and control flags
```

**Character Output Procedure**:
1. Write ASCII character to $C010 (CHAR_DATA)
2. GPU auto-advances cursor position
3. Monitor can manually control cursor with $C011/$C012 if needed

**Auto-Scroll Behavior**:
- When cursor reaches end of screen, GPU auto-scrolls
- No explicit scroll command needed from monitor

### Monitor Output Routing

**Current Implementation** (UART only):
```asm
; Output character in A to UART
CHROUT:
    STA UART_TX        ; $4000
    ; Wait for transmit complete
    RTS
```

**Enhanced Implementation** (I/O routing):
```asm
; Output character in A based on OUTPUT_MODE
CHROUT:
    PHA                ; Save character
    LDA OUTPUT_MODE    ; 0=UART, 1=Display, 2=Both
    BEQ .uart_only
    CMP #1
    BEQ .display_only
    ; Both: output to UART and Display
    PLA                ; Restore character
    PHA                ; Save again
    STA UART_TX
    PLA
    STA GPU_CHAR_DATA
    RTS
.uart_only:
    PLA
    STA UART_TX
    RTS
.display_only:
    PLA
    STA GPU_CHAR_DATA
    RTS
```

## 4. I/O Multiplexing Architecture

### Requirements

**Input Sources**:
- UART RX: Asynchronous character input
- PS/2 Keyboard: Scancode events → ASCII characters

**Output Destinations**:
- UART TX: Character transmission
- GPU: Memory-mapped character register

**Configuration Modes**:
- Input: UART only, PS/2 only, Both (first-come-first-served)
- Output: UART only, Display only, Both (duplicated)

### Option 1: Firmware Polling (RECOMMENDED)

**Approach**: Monitor firmware polls status registers for both input sources

**Advantages**:
- No RTL changes needed
- Simple to implement and debug
- Firmware has full control over priority

**Implementation**:
```asm
; Get character from configured input source(s)
CHRIN:
    LDA INPUT_MODE     ; 0=UART, 1=PS2, 2=Both
    BEQ .uart_only
    CMP #1
    BEQ .ps2_only
    ; Both: check UART first, then PS/2
.check_both:
    LDA UART_STATUS
    AND #RX_READY
    BNE .read_uart
    LDA PS2_STATUS
    AND #DATA_READY
    BNE .read_ps2
    JMP .check_both    ; Loop until data available
.uart_only:
    ; Wait for UART RX ready
    LDA UART_STATUS
    AND #RX_READY
    BEQ .uart_only
.read_uart:
    LDA UART_RX
    RTS
.ps2_only:
    ; Wait for PS/2 data ready
    LDA PS2_STATUS
    AND #DATA_READY
    BEQ .ps2_only
.read_ps2:
    LDA PS2_DATA
    JSR ASCII_MAP      ; Convert scancode to ASCII
    RTS
```

### Option 2: RTL Input Multiplexer

**Approach**: Create io_controller.v that merges UART and PS/2 into single FIFO

**Advantages**:
- Non-blocking input from multiple sources
- FIFO buffering prevents lost characters

**Disadvantages**:
- More complex RTL design
- Requires additional FPGA resources (FIFO)
- Violates "Simplicity Over Performance" for this use case

**Decision**: Use Option 1 (firmware polling) for initial implementation. Option 2 can be added later if performance issues arise.

## 5. Flow Control Implementation

### XON/XOFF Software Flow Control

**Purpose**: Prevent data loss when pasting BASIC programs via UART

**Protocol**:
- Receiver sends XOFF (0x13) when input buffer nearly full
- Sender pauses transmission
- Receiver sends XON (0x11) when buffer space available
- Sender resumes transmission

### Implementation Strategy

**UART Side** (requires RTL modification):
- Add UART TX output for XON/XOFF
- Monitor input buffer fill level
- Automatically send XOFF at 75% full, XON at 25% full

**Alternative**: Manual flow control from firmware
- Monitor periodically sends XON to keep sender active
- If processing falls behind, stop sending XON (implicit XOFF)

**BASIC Integration**:
- BASIC interpreter processes pasted lines one at a time
- After each line, BASIC returns to input prompt
- Monitor can use this natural pause for flow control

**Recommendation**: Start with manual XON from firmware; add automatic XOFF if data loss occurs during testing.

## 6. Monitor Firmware Extension

### Current Monitor Structure

**Files to Examine**:
- `firmware/monitor/monitor.s` - Main monitor implementation
- Expected structure: Command parser, memory operations, Go command

### Command Integration Points

**New Commands to Add**:
- `L` (Load): Enter binary receive mode, start XMODEM
- `I` (I/O): Configure input/output sources
- `S` (Status): Display current I/O configuration

**Command Parser Modification**:
```asm
; Existing command parser
CMD_PARSER:
    LDA INPUT_CHAR
    CMP #'D'           ; Existing: Deposit memory
    BEQ CMD_DEPOSIT
    CMP #'G'           ; Existing: Go to address
    BEQ CMD_GO
    ; NEW COMMANDS
    CMP #'L'           ; NEW: Load binary
    BEQ CMD_LOAD
    CMP #'I'           ; NEW: I/O config
    BEQ CMD_IO_CONFIG
    CMP #'S'           ; NEW: Status
    BEQ CMD_STATUS
    ; ... more commands
    RTS
```

### XMODEM State Machine Location

**Placement**: Separate subroutine called from CMD_LOAD

**State Variables** (zero page):
```asm
XMODEM_STATE:     .res 1  ; Current state (0-5)
XMODEM_PKT_NUM:   .res 1  ; Expected packet number
XMODEM_CHECKSUM:  .res 1  ; Running checksum
XMODEM_BYTE_CNT:  .res 1  ; Bytes received in current packet
XMODEM_RETRY_CNT: .res 1  ; Retry counter for errors
XMODEM_ADDR_LO:   .res 1  ; Target RAM address (low)
XMODEM_ADDR_HI:   .res 1  ; Target RAM address (high)
```

### I/O Configuration Storage

**Configuration Variables** (zero page or RAM):
```asm
INPUT_MODE:       .res 1  ; 0=UART, 1=PS2, 2=Both
OUTPUT_MODE:      .res 1  ; 0=UART, 1=Display, 2=Both
```

**Persistence**: Store in RAM, reinitialize to default (UART/UART) on reset

## Research Findings Summary

### Key Decisions

1. **XMODEM Implementation**: Standard XMODEM with 8-bit checksum, receiver-initiated, ~200-300 bytes of 6502 code
2. **PS/2 Mapping**: Lookup table approach for scancode-to-ASCII conversion
3. **GPU Output**: Use existing $C010 CHAR_DATA register with auto-advance cursor
4. **I/O Multiplexing**: Firmware polling approach (Option 1) for simplicity
5. **Flow Control**: Manual XON from firmware initially, automatic XOFF if needed
6. **Monitor Extension**: Add L/I/S commands to existing command parser

### Clarifications Resolved

- ✅ XMODEM protocol details and packet structure
- ✅ PS/2 scancode mapping strategy
- ✅ GPU character output interface ($C010)
- ✅ I/O multiplexing architecture (firmware polling)
- ✅ Flow control approach (XON/XOFF)
- ✅ Monitor firmware extension points

### Open Questions for Phase 1

- **PS/2 Peripheral Interface**: Need to examine actual rtl/peripherals/ps2/*.v to confirm register layout
- **UART Status Register**: Need to confirm exact bit positions for RX_READY and TX_READY flags
- **Monitor Code Size**: Need to verify available ROM space for XMODEM code (~300 bytes)
- **BASIC Entry Point**: Need to confirm exact address and calling convention for BASIC interpreter

These will be resolved during Phase 1 data model and contract generation by examining existing code.

## References

- **XMODEM Protocol**: Ward Christensen, 1977; [Wikipedia](https://en.wikipedia.org/wiki/XMODEM)
- **PS/2 Scancode Set 2**: [PS/2 Keyboard Interface](http://www.burtonsys.com/ps2_chapweske.htm)
- **6502 Assembly**: [6502.org](http://www.6502.org/) reference materials
- **cc65 Toolchain**: [cc65 Documentation](https://cc65.github.io/doc/)
