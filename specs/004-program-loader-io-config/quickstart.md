# Quickstart: Program Loader and I/O Configuration

**Feature**: 004-program-loader-io-config
**Audience**: Developers implementing this feature
**Date**: 2026-01-01

## Overview

This feature adds three major capabilities to the RetroCPU monitor:

1. **Binary Program Upload**: Load compiled 6502 programs via UART using XMODEM protocol
2. **I/O Configuration**: Switch between UART, PS/2 keyboard, and GPU display for input/output
3. **BASIC Text Loading**: Paste BASIC programs via UART with flow control

## Quick Reference

### New Monitor Commands

```
L <addr>       - Load binary program via XMODEM to address
I <in> <out>   - Configure I/O (0=UART, 1=PS2/Display, 2=Both)
S              - Show I/O status and peripheral info
```

### Example Workflow

```bash
# 1. Connect via UART terminal (Tera Term, minicom, etc.)
> S
I/O Status: IN=UART, OUT=UART

# 2. Load binary program to RAM
> L 0300
Ready to receive XMODEM. Start transfer now...
[In terminal: File → Transfer → XMODEM → Send → select program.bin]
Transfer complete: 512 bytes loaded

# 3. Switch to standalone mode (PS/2 keyboard + HDMI display)
> I 1 1
I/O Config: IN=PS2, OUT=Display

# 4. (Now use PS/2 keyboard and view output on HDMI)
# Execute the loaded program
> G 0300

# 5. To return to UART mode, use PS/2 keyboard to type:
> I 0 0
I/O Config: IN=UART, OUT=UART
```

## Implementation Roadmap

### Phase 1: Core XMODEM Implementation

**Files to Modify**:
- `firmware/monitor/monitor.s`

**Tasks**:
1. Add zero page variables for XMODEM state ($23-$29)
2. Implement `CMD_LOAD` command handler
   - Parse hex address argument
   - Validate address in range $0200-$7FFF
   - Call `XMODEM_RECV` subroutine
3. Implement `XMODEM_RECV` state machine
   - States: IDLE, WAIT_SOH, RECV_PKT_NUM, RECV_DATA, VERIFY
   - Send NAK to initiate
   - Receive and validate packets
   - Write data to RAM
   - Send ACK/NAK for each packet
   - Handle EOT (end of transfer)
4. Implement checksum verification
5. Implement error handling (retry, timeout, abort)

**Testing**:
- Use `tests/integration/test_xmodem_upload.py`
- Test with small binary file (256 bytes)
- Test checksum error recovery
- Test timeout handling

**Estimated Effort**: 300 lines of 6502 assembly

---

### Phase 2: I/O Configuration

**Files to Modify**:
- `firmware/monitor/monitor.s`

**Tasks**:
1. Add zero page variables for I/O config ($21-$22)
2. Implement `CMD_IO_CONFIG` command handler
   - Parse input mode digit
   - Parse output mode digit
   - Validate modes (0-2)
   - Store in `IO_INPUT_MODE` and `IO_OUTPUT_MODE`
3. Enhance `CHRIN` function
   - Check `IO_INPUT_MODE`
   - Poll UART or PS/2 or both based on mode
   - For PS/2: call `PS2_TO_ASCII` for translation
4. Enhance `CHROUT` function
   - Check `IO_OUTPUT_MODE`
   - Send to UART, GPU, or both based on mode
   - Wait for UART TX ready when needed
5. Initialize I/O config to defaults (0, 0) in RESET handler

**Testing**:
- Use `tests/integration/test_io_switching.py`
- Test all 9 combinations of input/output modes (0-2 × 0-2)
- Verify dual output produces identical text on UART and display
- Verify dual input accepts characters from either source

**Estimated Effort**: 150 lines of 6502 assembly

---

### Phase 3: PS/2 Translation Layer

**Files to Modify**:
- `firmware/monitor/monitor.s`

**Files to Create**:
- `firmware/monitor/ps2_table.s` (lookup table data)

**Tasks**:
1. Add zero page variables for PS/2 state ($2A-$2B: SHIFT, CAPS)
2. Create `PS2_XLAT_TABLE` lookup table (128 bytes)
   - Map Scancode Set 2 to ASCII (unshifted)
   - Include all printable characters and control keys
3. Implement `PS2_TO_ASCII` function
   - Handle break code prefix (0xF0)
   - Detect and track modifier keys (Shift, Caps Lock)
   - Lookup scancode in table
   - Apply uppercase transformation for letters when shifted/caps
   - Return ASCII or 0x00 for unmapped/modifier keys
4. Handle make/break codes correctly
   - Make codes (key press): process and return ASCII
   - Break codes (key release): update modifier state, return 0x00

**Testing**:
- Unit test PS2_TO_ASCII function with known scancodes
- Test uppercase/lowercase with Shift and Caps Lock
- Test control characters (Enter, Backspace, Esc)
- Test unmapped scancodes return 0x00

**Estimated Effort**: 200 lines of 6502 assembly + 128 byte table

---

### Phase 4: Status Display

**Files to Modify**:
- `firmware/monitor/monitor.s`

**Tasks**:
1. Implement `CMD_STATUS` command handler
   - Display current I/O configuration modes
   - Read and display UART status (TX ready, RX ready)
   - Read and display PS/2 status (data ready)
   - Read and display GPU status (mode, cursor position)
2. Format output as multi-line status report

**Testing**:
- Manual verification: Check status output matches actual configuration
- Test status display in different I/O modes

**Estimated Effort**: 100 lines of 6502 assembly

---

### Phase 5: Integration Testing

**Files to Create**:
- `tests/integration/test_program_execution.py`
- `tests/integration/test_basic_paste.py`
- `firmware/examples/hello_world.s`
- `firmware/examples/led_blink.s`

**Tasks**:
1. Create example binary programs for testing
2. Write integration tests:
   - Full workflow: Upload binary via XMODEM, execute with Go command
   - BASIC paste: Configure UART input, paste BASIC program, run
   - I/O switching: Test switching modes during operation
3. Hardware-in-loop validation on actual FPGA board

**Testing Scenarios**:
- Load 1KB binary program to $0300, execute, verify output
- Paste 20-line BASIC program via UART, run, verify output
- Switch from UART to PS/2+Display mid-session, verify continuity

**Estimated Effort**: 4 test scripts, 2 example programs

---

### Phase 6: Documentation

**Files to Create**:
- `docs/protocols/xmodem.md`
- `docs/protocols/io_abstraction.md`
- `docs/user_guides/program_loading.md`

**Tasks**:
1. Document XMODEM protocol implementation details
2. Document I/O multiplexing architecture with diagrams
3. Write user guide for loading programs (XMODEM setup in terminal emulators)
4. Update main README.md with new monitor commands

**Estimated Effort**: 3 documentation files, README update

---

## Development Environment Setup

### Prerequisites

- **Assembler**: ca65 (part of cc65 toolchain)
- **FPGA Tools**: Yosys, nextpnr-ecp5, openFPGALoader
- **Python**: Python 3.8+ with pyserial library for test scripts
- **Terminal Emulator**: Tera Term (Windows) or minicom (Linux) with XMODEM support
- **Hardware**: Colorlight i5 board with UART, PS/2, and HDMI connections

### Build and Test Workflow

```bash
# 1. Modify monitor firmware
cd firmware/monitor
vim monitor.s

# 2. Assemble and link
ca65 -o monitor.o monitor.s
ld65 -C monitor.cfg -o monitor.bin monitor.o

# 3. Convert to hex for ROM initialization
../scripts/bin2hex.py monitor.bin > monitor.hex

# 4. Rebuild FPGA bitstream
cd ../../build
make clean
make all

# 5. Program FPGA
make program

# 6. Run integration test
cd ../tests/integration
python3 test_xmodem_upload.py
```

## Code Organization

### Monitor Firmware Structure

```asm
; monitor.s

; ============================================================================
; Zero Page Variables
; ============================================================================
.segment "ZEROPAGE"

; Existing variables
TEMP:        .res 1
ADDR_LO:     .res 1
ADDR_HI:     .res 1
...

; NEW: I/O Configuration
IO_INPUT_MODE:  .res 1  ; 0=UART, 1=PS2, 2=Both
IO_OUTPUT_MODE: .res 1  ; 0=UART, 1=Display, 2=Both

; NEW: PS/2 Translation State
PS2_BREAK:   .res 1     ; Break code flag
PS2_SHIFT:   .res 1     ; Shift key state
PS2_CAPS:    .res 1     ; Caps Lock state

; NEW: XMODEM State
XMODEM_STATE:    .res 1
XMODEM_PKT_NUM:  .res 1
XMODEM_CHECKSUM: .res 1
XMODEM_BYTE_CNT: .res 1
XMODEM_RETRY_CNT: .res 1
XMODEM_ADDR_LO:  .res 1
XMODEM_ADDR_HI:  .res 1

; ============================================================================
; RAM Buffers
; ============================================================================
.segment "RAM"
.org $0200

XMODEM_BUFFER: .res 128     ; Packet data buffer

.org $0280
PS2_XLAT_TABLE: .res 128    ; PS/2 scancode → ASCII lookup

; ============================================================================
; Code
; ============================================================================
.segment "CODE"
.org $E000

RESET:
    ; Initialize stack, zero page, etc.
    ; ...

    ; NEW: Initialize I/O configuration to defaults
    LDA #0
    STA IO_INPUT_MODE   ; UART input
    STA IO_OUTPUT_MODE  ; UART output
    STA PS2_BREAK
    STA PS2_SHIFT
    STA PS2_CAPS

    JSR INIT_PS2_TABLE  ; Initialize PS/2 lookup table

    ; Continue with welcome message, etc.
    ; ...

MAIN_LOOP:
    ; Existing command parser
    ; ...

    ; NEW: Add L, I, S commands
    CMP #'L'
    BEQ CMD_LOAD
    CMP #'I'
    BEQ CMD_IO_CONFIG
    CMP #'S'
    BEQ CMD_STATUS

    ; ...

; ============================================================================
; NEW: Command Handlers
; ============================================================================

CMD_LOAD:
    ; Parse address, validate, call XMODEM_RECV
    ; ...
    RTS

CMD_IO_CONFIG:
    ; Parse modes, validate, update config
    ; ...
    RTS

CMD_STATUS:
    ; Display I/O status and peripheral info
    ; ...
    RTS

; ============================================================================
; NEW: XMODEM Implementation
; ============================================================================

XMODEM_RECV:
    ; State machine for receiving XMODEM packets
    ; ...
    RTS

; ============================================================================
; NEW: PS/2 Translation
; ============================================================================

PS2_TO_ASCII:
    ; Convert scancode to ASCII with modifier handling
    ; ...
    RTS

INIT_PS2_TABLE:
    ; Copy PS/2 lookup table from ROM to RAM
    ; ...
    RTS

; ============================================================================
; MODIFIED: I/O Functions
; ============================================================================

CHRIN:
    ; Check IO_INPUT_MODE
    ; Poll UART, PS/2, or both
    ; Call PS2_TO_ASCII if reading from PS/2
    ; ...
    RTS

CHROUT:
    ; Check IO_OUTPUT_MODE
    ; Send to UART, GPU, or both
    ; ...
    RTS

; ============================================================================
; Data Tables
; ============================================================================

PS2_TABLE_DATA:
    ; 128-byte table: scancode → ASCII (unshifted)
    .byte $00, $00, $00, ... ; 0x00-0x0F
    .byte $00, $00, $71, ... ; 0x10-0x1F (0x15='q')
    ; ... (full table)
```

## Memory Map

### Zero Page ($00-$FF)

```
$00-$20: Existing monitor variables
$21-$22: I/O configuration (INPUT_MODE, OUTPUT_MODE)
$23-$29: XMODEM state variables
$2A-$2B: PS/2 translation state (SHIFT, CAPS)
```

### RAM ($0200-$7FFF)

```
$0200-$027F: XMODEM packet buffer (128 bytes)
$0280-$02FF: PS/2 scancode lookup table (128 bytes)
$0300-$7FFF: User program space (31 KB)
```

### ROM ($E000-$FFFF)

```
$E000-$EFFF: Monitor code (~4 KB)
$F000-$FFEF: NEW monitor code (~4 KB available)
$FFF0-$FFFF: Vectors (NMI, RESET, IRQ)
```

## Testing Strategy

### Unit Tests

- `test_ps2_translation.py`: Test PS2_TO_ASCII function with mock scancodes
- `test_xmodem_state_machine.py`: Test state transitions and error handling

### Integration Tests

- `test_xmodem_upload.py`: Full XMODEM transfer with actual terminal
- `test_io_switching.py`: Switch I/O modes and verify routing
- `test_program_execution.py`: Upload, execute, verify output
- `test_basic_paste.py`: Paste BASIC program and run

### Hardware-in-Loop Tests

- Connect UART, PS/2 keyboard, and HDMI display
- Run all 4 user stories from spec.md acceptance scenarios
- Verify success criteria (transfer speed, success rate, etc.)

## Common Pitfalls

### XMODEM Implementation

- **Off-by-one errors**: Packet numbers start at 1, not 0
- **Checksum calculation**: 8-bit sum wraps at 255, don't forget overflow
- **Timeout handling**: Must respond within ~10 seconds or sender will abort
- **Buffer overwrite**: Be careful loading to $0200 (XMODEM buffer location)

### PS/2 Translation

- **Break code handling**: Must track state across multiple calls (break prefix, then scancode)
- **Modifier key release**: Shift/Caps release must clear flags correctly
- **Caps Lock logic**: Toggle on make, ignore on break (unlike Shift which is press/release)

### I/O Multiplexing

- **Blocking behavior**: CHRIN must block until data available from any configured source
- **Output synchronization**: When dual output, UART must wait for TX ready, but GPU is immediate
- **UART TX overflow**: Don't write to UART_DATA if TX busy (check status first)

## Performance Considerations

- **XMODEM transfer speed**: At 9600 baud, 128-byte packet takes ~130ms. With protocol overhead (ACK/NAK), expect ~750 bytes/sec (6 KB/min)
- **PS/2 polling overhead**: Polling PS2_STATUS in CHRIN adds ~10 cycles per iteration. Acceptable for human typing speed.
- **Display output latency**: GPU character output is immediate (1 cycle write to memory-mapped register). No buffering needed.

## BASIC Program Text Loading (Phase 5)

### Overview

In addition to binary program upload via XMODEM, the monitor supports pasting
multi-line BASIC programs via UART with automatic flow control. This allows
you to develop BASIC programs on your computer and transfer them to RetroCPU
by simply pasting them into your terminal emulator.

### Flow Control Strategy

To prevent data loss during rapid input (paste operations), the monitor implements
a simple XON flow control mechanism:

1. **After each character is read** via UART, the monitor sends XON ($11, Ctrl-Q)
2. **Terminal emulator waits** for XON before sending the next character
3. **No data loss** occurs, even with slow BASIC interpreter processing

**Note**: Full XON/XOFF flow control (where monitor sends XOFF to pause) is
deferred to future work. The current implementation only sends XON to signal
readiness.

### Terminal Configuration

#### XON/XOFF Settings

Configure your terminal emulator to use XON/XOFF flow control:

**Tera Term (Windows)**:
```
Setup → Serial Port → Flow Control: XON/XOFF
Setup → Serial Port → Transmit delay: 10 ms/char (optional safety margin)
```

**minicom (Linux)**:
```
Ctrl-A → O → Serial port setup
  Hardware Flow Control: No
  Software Flow Control: Yes
```

**screen (macOS/Linux)**:
```
# XON/XOFF is typically enabled by default
# No additional configuration needed
```

### Example BASIC Paste Session

#### Step 1: Configure I/O Mode

Start with UART input and output for development:

```
> I 0 0
I/O Config: IN=UART, OUT=UART
```

#### Step 2: Start BASIC Interpreter

```
> G
Starting BASIC...

OSI 6502 BASIC VERSION 1.0 REV 3.2
COPYRIGHT 1977 BY MICROSOFT CO.

MEMORY SIZE? [Press Enter]
TERMINAL WIDTH? [Press Enter]

READY

>
```

#### Step 3: Paste BASIC Program

Open one of the example programs:
- `firmware/examples/basic_hello.bas` - Simple hello world
- `firmware/examples/basic_loop.bas` - Loop demonstration
- `firmware/examples/basic_test.bas` - Comprehensive test

In your terminal, use the paste function to paste the file contents.
The monitor will send XON after each character to pace the input.

You should see each line echo as it's received:

```
>10 REM ===================================
>20 REM RETROCPU BASIC HELLO WORLD PROGRAM
>30 REM ===================================
>40 REM
...
>180 END

READY

>
```

#### Step 4: Run the Program

```
>RUN
HELLO FROM RETROCPU!
THIS PROGRAM WAS PASTED VIA UART

FLOW CONTROL TEST:
LINE 1
LINE 2
...
LINE 10

TEST COMPLETE!

READY

>
```

### Testing Different I/O Modes with BASIC

#### Scenario 1: Dual Output for Debugging

Paste program via UART but see output on both UART and HDMI display:

```
> I 0 2
I/O Config: IN=UART, OUT=Both
> G
[Start BASIC, paste program, run]
[Output appears on terminal AND display simultaneously]
```

**Use case**: Compare outputs, capture logs while viewing on monitor

#### Scenario 2: Standalone Mode

Paste program via UART, then switch to PS/2 keyboard and display for execution:

```
# First, paste program via UART
> I 0 0
I/O Config: IN=UART, OUT=UART
> G
[Paste BASIC program]
>SAVE "PROG"
[Ctrl-C to exit BASIC]

# Switch to standalone mode
> I 1 1
I/O Config: IN=PS2, OUT=Display
> G
[On PS/2 keyboard, type: LOAD "PROG"]
[On PS/2 keyboard, type: RUN]
[Output appears on HDMI display]
```

**Use case**: Development on PC, execution on standalone system

#### Scenario 3: Type on PS/2, View on Both

Type BASIC program on PS/2 keyboard, see output on both UART and display:

```
> I 1 2
I/O Config: IN=PS2, OUT=Both
> G
[Type program on PS/2 keyboard]
[Output appears on terminal and display]
```

**Use case**: Classroom demonstration, remote monitoring

### Flow Control Implementation Details

The flow control is implemented in the CHRIN function in monitor.s:

```asm
@READ_UART:
    LDA UART_DATA       ; Read character
    PHA                 ; Save character

    ; Send XON to indicate we're ready for next character
    JSR SEND_XON

    PLA                 ; Restore character
    RTS

SEND_XON:
    ; Only send XON if IO_INPUT_MODE includes UART (0 or 2)
    ; XON character = $11 (ASCII 17, Ctrl-Q)
    ; Waits for UART TX ready before sending
    ...
```

Key points:
- XON is sent **after** each character is read from UART
- XON is **only sent** when IO_INPUT_MODE is 0 (UART) or 2 (Both)
- XON is **not sent** in PS/2-only mode (mode 1)
- The UART TX ready flag is checked before sending XON

### Troubleshooting BASIC Paste

#### Problem: Characters are dropped or corrupted

**Cause**: Flow control not enabled or terminal sending too fast

**Solution**:
1. Verify XON/XOFF is enabled in terminal settings
2. Add character delay (10-20 ms/char) in terminal settings
3. Check baud rate matches (115200)
4. Try pasting smaller sections at a time

#### Problem: XON characters appear in output

**Cause**: Terminal is displaying flow control characters

**Solution**:
- Disable local echo in terminal settings
- Tera Term: Setup → Terminal → Local echo OFF
- minicom: Ctrl-A → E (toggle local echo)

#### Problem: Paste works but program won't run

**Cause**: Syntax errors or incomplete lines

**Solution**:
1. In BASIC, type `LIST` to see what was received
2. Check for missing line numbers or syntax errors
3. Manually retype any corrupted lines
4. Verify REM lines don't have special characters

#### Problem: Paste is too slow

**Cause**: Character delay too long, or BASIC interpreter is slow

**Solution**:
- Reduce character delay in terminal (try 5 ms or 0 ms)
- XON flow control should be sufficient without delay
- For very long programs, consider saving/loading to storage

### Example Programs

See `firmware/examples/` for ready-to-paste BASIC programs:

1. **basic_hello.bas** (18 lines)
   - Simple hello world with loop
   - Quick test of paste functionality

2. **basic_loop.bas** (22 lines)
   - Infinite loop with counter
   - Tests BREAK key and I/O mode switching

3. **basic_test.bas** (43 lines)
   - Comprehensive test suite
   - Arithmetic, strings, loops, conditionals

Each program includes detailed documentation in `firmware/examples/BASIC_PROGRAMS.md`.

### Next Steps with BASIC

1. **Create your own programs**: Use examples as templates
2. **Test I/O modes**: Try all 9 combinations of input/output modes
3. **Benchmark**: Measure paste speed with/without flow control
4. **Save programs**: Use BASIC SAVE/LOAD commands (if storage available)

---

## Next Steps

After completing this feature:

1. **Test thoroughly**: Run all integration tests and user acceptance scenarios
2. **Document**: Complete user guide and protocol documentation
3. **Optimize**: If XMODEM is too slow, consider XMODEM-1K or ZMODEM
4. **Enhance**: Add features like progress bar, CRC checksum, configuration persistence

## References

- [XMODEM Protocol Specification](https://en.wikipedia.org/wiki/XMODEM)
- [PS/2 Scancode Set 2](http://www.burtonsys.com/ps2_chapweske.htm)
- [ca65 Assembler Manual](https://cc65.github.io/doc/ca65.html)
- Feature Specification: `specs/004-program-loader-io-config/spec.md`
- Data Model: `specs/004-program-loader-io-config/data-model.md`
- Contracts: `specs/004-program-loader-io-config/contracts/`
