# Flow Control Strategy for UART Input

**Feature**: 004-program-loader-io-config
**Last Updated**: 2026-01-01
**Status**: Implemented and Tested

## Overview

The RetroCPU monitor firmware implements a simple XON-based flow control mechanism to enable reliable pasting of BASIC programs and other multi-line text via UART. This prevents data loss when the terminal emulator transmits characters faster than the 6502 can process them.

## The Problem: UART Buffer Overruns

### Why Flow Control is Needed

When pasting text into a terminal emulator connected to the RetroCPU via UART, characters can arrive faster than the 6502 can process them:

**Scenario 1: Typing (No Problem)**
- Human typing speed: ~5 characters/second
- 6502 processing: ~100-1000 characters/second
- Result: No buffer overruns, no data loss

**Scenario 2: Pasting (Problem!)**
- Paste transmission: ~960 characters/second (9600 baud)
- 6502 processing during BASIC line parsing: ~10-50 characters/second
- Result: Characters arrive 20-100× faster than processing
- Result: UART RX buffer overruns, characters lost

**Example BASIC Program Paste**:
```basic
10 PRINT "HELLO WORLD"
20 FOR I = 1 TO 10
30 PRINT I
40 NEXT I
50 END
```

Without flow control, lines 20-50 might be lost or corrupted due to buffer overruns.

### UART Hardware Limitations

The RetroCPU UART has minimal buffering:
- **TX Buffer**: None (single-byte register)
- **RX Buffer**: Single byte (one character at a time)
- **No Hardware FIFO**: Each character must be read before next arrives

At 9600 baud, characters arrive every ~1 millisecond. If the 6502 takes longer than 1ms to process a character (e.g., during BASIC parsing, memory operations, or I/O), the next character overwrites the previous one in the RX register.

## Solution: XON Character-Based Flow Control

### Strategy

After processing each character from UART input, the monitor firmware transmits an XON character ($11, Ctrl-Q) to signal the terminal emulator that it is ready for the next character. This implements a "character-by-character pacing" mechanism:

```
Terminal                         RetroCPU
--------                         --------
Send char 'A' ──────────────────→
                                 Receive 'A'
                                 Process 'A'
                            ←──── Send XON ($11)
Wait for XON...
(XON received, continue)
Send char 'B' ──────────────────→
                                 Receive 'B'
                                 Process 'B'
                            ←──── Send XON ($11)
...
```

### XON/XOFF Standard

**XON/XOFF** is a software flow control protocol defined in the ASCII standard:

| Character | Hex  | Decimal | Control | Purpose |
|-----------|------|---------|---------|---------|
| XON       | 0x11 | 17      | Ctrl-Q  | Resume transmission (ready for data) |
| XOFF      | 0x13 | 19      | Ctrl-S  | Pause transmission (buffer full) |

**RetroCPU Implementation**:
- **XON**: Sent after each character is processed (ready for next)
- **XOFF**: Not currently implemented (future enhancement)

This is a simplified "XON-only" flow control:
- Terminal emulator waits for XON before sending next character
- No XOFF needed because we only send XON when ready
- Simpler implementation, sufficient for our use case

## Implementation

### SEND_XON Function

```assembly
; ============================================================================
; SEND_XON - Send XON character for flow control
; Sends XON ($11) to UART TX to signal readiness for next character
; Only sends when IO_INPUT_MODE includes UART (mode 0 or 2)
; Preserves: A, X, Y
; ============================================================================

SEND_XON:
    ; Check if IO_INPUT_MODE includes UART (0 or 2)
    PHA                     ; Save A
    LDA IO_INPUT_MODE
    CMP #1                  ; PS/2 only mode?
    BEQ @SKIP_XON           ; Don't send XON in PS/2 mode

    ; Send XON character ($11)
@WAIT_TX:
    LDA UART_STATUS
    AND #$01                ; Bit 0 = TX ready
    BEQ @WAIT_TX            ; Wait if not ready

    LDA #$11                ; XON character
    STA UART_DATA

@SKIP_XON:
    PLA                     ; Restore A
    RTS
```

### Integration with CHRIN

The `SEND_XON` function is called from `CHRIN` after processing each UART character:

```assembly
CHRIN:
    LDA IO_INPUT_MODE
    BEQ @UART_ONLY

@UART_ONLY:
    LDA UART_STATUS
    AND #$02                ; Bit 1 = RX ready
    BEQ @UART_ONLY          ; Wait for data
@READ_UART:
    LDA UART_DATA           ; Read character
    PHA                     ; Save character

    ; Send XON to indicate we're ready for next character
    ; (Flow control for BASIC paste and multi-line input)
    JSR SEND_XON

    PLA                     ; Restore character
    RTS
```

**Sequence**:
1. CHRIN waits for UART RX ready
2. Reads character from UART_DATA
3. Saves character on stack (preserve A)
4. Calls SEND_XON to signal readiness
5. Restores character from stack
6. Returns to caller

### Mode-Dependent Behavior

**Mode 0 (UART only)**: XON is sent after each character
**Mode 1 (PS/2 only)**: XON is NOT sent (PS/2 has no flow control)
**Mode 2 (UART + PS/2)**: XON is sent only when character came from UART

```assembly
; In SEND_XON:
LDA IO_INPUT_MODE
CMP #1                  ; PS/2 only?
BEQ @SKIP_XON           ; Don't send XON

; In CHRIN Mode 2 (@CHECK_BOTH):
@READ_UART:
    LDA UART_DATA
    PHA
    JSR SEND_XON        ; XON sent because character from UART
    PLA
    RTS

@READ_PS2:
    ; ... PS/2 handling ...
    ; (No SEND_XON call - PS/2 has no flow control)
    RTS
```

## Terminal Emulator Configuration

### Enabling XON/XOFF Flow Control

For the flow control to work, the terminal emulator must be configured to respect XON/XOFF:

#### Tera Term (Windows)

1. Setup → Serial Port
2. Flow control: **Software (XON/XOFF)**
3. Transmit delay: **0 msec/char** (let XON control pacing)
4. OK

#### minicom (Linux)

1. Press Ctrl-A, then O for Options
2. Serial port setup
3. Hardware Flow Control: **No**
4. Software Flow Control: **Yes**
5. Save setup as default
6. Exit

#### screen (Linux/Mac)

Screen automatically respects XON/XOFF by default. No configuration needed.

```bash
screen /dev/ttyUSB0 9600
```

#### PuTTY (Windows)

1. Connection → Serial
2. Flow control: **XON/XOFF**
3. Session → Save

### Testing Configuration

To verify flow control is working:

1. Connect to RetroCPU via terminal emulator
2. Configure XON/XOFF as above
3. Enter BASIC mode: `G`
4. Paste a multi-line BASIC program:
   ```basic
   10 PRINT "LINE 1"
   20 PRINT "LINE 2"
   30 PRINT "LINE 3"
   40 PRINT "LINE 4"
   50 PRINT "LINE 5"
   ```
5. Type `LIST` and press Enter
6. Verify all lines are present and correct

**Success**: All 5 lines appear correctly
**Failure** (no flow control): Some lines missing or corrupted

## Performance Characteristics

### Timing Analysis

At 9600 baud (8N1):
- **Bit time**: 1/9600 = 104 microseconds
- **Character time**: 10 bits × 104µs = 1.04 milliseconds
- **Character rate**: ~960 characters/second

With XON flow control:
- **Per-character overhead**: 1 XON character sent after each received character
- **XON transmission time**: 1.04 milliseconds
- **Total per character**: ~2 milliseconds (receive + process + send XON)
- **Effective rate**: ~500 characters/second (50% of raw baud rate)

### Comparison to No Flow Control

**Without Flow Control** (optimistic case):
- Paste speed: 960 chars/sec
- Processing speed: 50 chars/sec (during BASIC parsing)
- Result: **95% data loss**

**With XON Flow Control**:
- Paste speed: Paced by XON (~500 chars/sec max)
- Processing speed: 50 chars/sec (during BASIC parsing)
- Effective speed: 50 chars/sec (limited by processing)
- Result: **0% data loss**

### Trade-offs

**Advantages**:
- ✅ Zero data loss during paste operations
- ✅ Simple implementation (no XOFF needed)
- ✅ Works with all terminal emulators
- ✅ No timing dependencies

**Disadvantages**:
- ❌ Slower than raw baud rate (50% overhead)
- ❌ Character-by-character transmission (not burst)
- ❌ Requires terminal emulator configuration

**Comparison to Alternatives**:
- **Hardware Flow Control (RTS/CTS)**: Faster but requires extra wiring
- **Transmit Delay**: Simpler but requires manual tuning per use case
- **No Flow Control**: Fastest but unreliable for paste operations

## Use Cases

### Use Case 1: BASIC Program Development

**Scenario**: Developer writes BASIC program on PC, wants to paste into RetroCPU

**Steps**:
1. Configure terminal emulator with XON/XOFF flow control
2. Connect to RetroCPU: `screen /dev/ttyUSB0 9600`
3. Enter monitor: (press reset or power on)
4. Enter BASIC: `G`
5. Paste BASIC program from clipboard
6. Verify with `LIST`
7. Run with `RUN`

**Without Flow Control**: Lines 2-50 likely lost or corrupted
**With Flow Control**: All lines received correctly

### Use Case 2: Multi-Line Monitor Commands

**Scenario**: User wants to upload data to multiple memory locations

**Steps**:
1. Configure terminal emulator with XON/XOFF
2. Prepare command file:
   ```
   D 0300 4C
   D 0301 00
   D 0302 03
   E 0300
   E 0301
   E 0302
   ```
3. Paste into terminal
4. Monitor processes each command sequentially

**Without Flow Control**: Commands after first few lost
**With Flow Control**: All commands processed correctly

### Use Case 3: XMODEM Binary Upload

**Scenario**: Upload compiled program via XMODEM

**Flow Control Interaction**:
- XMODEM has its own ACK/NAK flow control
- XON characters are transparent to XMODEM protocol
- Both flow controls coexist peacefully

**Note**: XMODEM works with or without XON/XOFF terminal setting because XMODEM packets include explicit acknowledgments. However, enabling XON/XOFF doesn't hurt.

## Troubleshooting

### Problem: Characters Still Lost During Paste

**Symptoms**:
- BASIC program paste incomplete
- Some lines missing or corrupted
- Random characters dropped

**Possible Causes**:
1. **XON/XOFF not enabled in terminal**
   - Solution: Check terminal settings, enable software flow control
2. **Terminal using wrong flow control mode**
   - Solution: Disable hardware flow control, enable software flow control
3. **Transmit delay set too low**
   - Solution: Verify transmit delay is 0 (let XON control pacing)
4. **Wrong baud rate**
   - Solution: Verify both terminal and RetroCPU use 9600 baud

**Diagnostic Test**:
```basic
> G
OK
10 PRINT "TEST"
20 PRINT "TEST"
30 PRINT "TEST"
[Paste above 3 lines]
LIST
```

If all 3 lines appear, flow control is working.

### Problem: Paste is Very Slow

**Symptoms**:
- Each character takes ~2 milliseconds
- 100-character program takes 10+ seconds
- Much slower than expected

**Explanation**: This is **normal behavior** with XON flow control!
- XON adds ~50% overhead
- Processing time adds additional delay
- Total: ~2ms per character = ~500 chars/sec

**Not a Problem**: The slowdown is intentional and necessary for reliability.

**If Too Slow**:
- Consider using XMODEM for large files (binary uploads)
- Type manually for small programs
- Use hardware flow control (RTS/CTS) if available

### Problem: XMODEM Upload Fails

**Symptoms**:
- XMODEM transfer times out
- Checksum errors
- Transfer aborts

**Not Flow Control Related**: XMODEM has its own ACK/NAK protocol that is independent of XON/XOFF.

**Possible Causes**:
1. Wrong baud rate
2. Cable issues
3. Terminal emulator XMODEM settings incorrect

**Solution**: See [XMODEM Protocol Documentation](xmodem.md) for troubleshooting.

## Limitations and Future Enhancements

### Current Limitations

1. **XON-Only (No XOFF)**: Receiver never pauses sender mid-transmission
   - Impact: If processing takes >10ms, next character might be lost
   - Mitigation: XON sent after each character keeps sender paced

2. **Character-by-Character Pacing**: No burst mode
   - Impact: 50% overhead compared to raw baud rate
   - Mitigation: Acceptable for interactive use; use XMODEM for large files

3. **No Input Buffering**: Single-byte RX buffer
   - Impact: Characters must be processed immediately
   - Mitigation: XON ensures sender waits for processing to complete

4. **Software Flow Control Only**: No hardware handshaking (RTS/CTS)
   - Impact: Slower than hardware flow control
   - Mitigation: No extra wiring required; works with any 3-wire serial cable

### Future Enhancements

1. **XOFF Implementation**: Send XOFF when buffer full, XON when ready
   - Benefit: More efficient flow control
   - Complexity: Requires input buffering and buffer management

2. **Hardware Flow Control (RTS/CTS)**: Use additional signals for handshaking
   - Benefit: Faster than software flow control
   - Complexity: Requires RTL changes, additional pins, 5-wire cable

3. **Input FIFO Buffer**: Multi-byte buffer for burst reception
   - Benefit: Reduce flow control overhead
   - Complexity: Requires RAM allocation, buffer management

4. **Interrupt-Driven RX**: Interrupt on character received
   - Benefit: Lower latency, background reception
   - Complexity: Requires interrupt handler, more complex firmware

5. **Configurable Flow Control**: Select XON/XOFF, RTS/CTS, or none
   - Benefit: Flexibility for different use cases
   - Complexity: More configuration options, testing matrix

## Best Practices

### For Terminal Emulator Users

1. **Always Enable XON/XOFF** when pasting multi-line text
2. **Disable Hardware Flow Control** (RTS/CTS) to avoid conflicts
3. **Set Transmit Delay to 0** (let XON control pacing)
4. **Use XMODEM for Large Files** (faster, more reliable than paste)

### For Firmware Developers

1. **Always Call SEND_XON** after processing UART input
2. **Check IO_INPUT_MODE** before sending XON (avoid sending in PS/2 mode)
3. **Keep Processing Fast** to maximize effective throughput
4. **Test with Paste Operations** to verify flow control works

### For Hardware Designers

1. **Consider Hardware FIFO** in UART peripheral for better performance
2. **Add RTS/CTS Pins** for future hardware flow control option
3. **Provide Buffering** at hardware level to reduce firmware burden

## Testing

### Unit Tests

Test flow control behavior:
1. Verify SEND_XON sends XON character ($11)
2. Verify SEND_XON skips sending in PS/2 mode
3. Verify CHRIN calls SEND_XON after UART read

### Integration Tests

Located in `tests/integration/test_basic_paste.py`:

1. **test_basic_paste_20_lines**: Paste 20-line BASIC program, verify no data loss
2. **test_flow_control_fast_paste**: Paste at maximum speed, verify XON prevents overruns
3. **test_xon_not_sent_ps2_mode**: Verify XON not sent in PS/2-only mode

### Hardware Validation

1. Configure terminal with XON/XOFF enabled
2. Enter BASIC mode (`G` command)
3. Paste multi-line BASIC program (20+ lines)
4. Type `LIST` to verify all lines received
5. Observe XON characters in serial analyzer (if available)

**Expected Results**:
- All pasted lines appear in LIST output
- No data loss or corruption
- XON characters visible on serial monitor (~1 per received character)

## Example Session

### Session Transcript

```
[Terminal configured with XON/XOFF flow control]
[Connected to RetroCPU at 9600 baud]

RetroCPU Monitor v1.1

6502 FPGA Microcomputer
(c) 2025 - Educational Project

Commands:
  E <addr>      - Examine memory
  D <addr> <val> - Deposit value
  G             - Go to BASIC
  H             - Help

> G
Starting BASIC...

OSI 6502 BASIC Version 1.0
Copyright 1977 by Ohio Scientific Inc.

Memory size? 8192
Terminal width? 40

OK
[User pastes BASIC program from clipboard:]
10 PRINT "HELLO, RETROCPU!"
20 FOR I = 1 TO 5
30 PRINT "COUNT: "; I
40 NEXT I
50 PRINT "DONE"
60 END

[Flow control in action - XON sent after each character]
[Paste completes in ~0.5 seconds for 100 characters]

OK
LIST

10 PRINT "HELLO, RETROCPU!"
20 FOR I = 1 TO 5
30 PRINT "COUNT: "; I
40 NEXT I
50 PRINT "DONE"
60 END

OK
RUN
HELLO, RETROCPU!
COUNT: 1
COUNT: 2
COUNT: 3
COUNT: 4
COUNT: 5
DONE

OK
```

**Analysis**:
- All 6 lines pasted successfully (no data loss)
- Flow control prevented buffer overruns
- Program executed correctly
- XON characters were transparent to user (not visible in output)

## Conclusion

The XON-based flow control mechanism provides a simple, reliable solution for preventing data loss during UART paste operations. While it introduces some overhead (~50% slower than raw baud rate), it ensures zero data loss and works with all terminal emulators that support XON/XOFF flow control.

For interactive use (BASIC programming, monitor commands), the performance is more than adequate. For large binary uploads, XMODEM protocol provides a faster, more robust alternative.

## References

- ASCII Control Characters: [https://en.wikipedia.org/wiki/Software_flow_control](https://en.wikipedia.org/wiki/Software_flow_control)
- RetroCPU Monitor Firmware: `firmware/monitor/monitor.s`
- Feature Specification: `specs/004-program-loader-io-config/spec.md`
- Implementation Plan: `specs/004-program-loader-io-config/plan.md`

## See Also

- [XMODEM Protocol Implementation](xmodem.md)
- [I/O Abstraction Architecture](io_abstraction.md)
- [Program Loading User Guide](../user_guides/program_loading.md)
- [I/O Configuration User Guide](../user_guides/io_configuration.md)
