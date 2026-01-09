# XMODEM Protocol Implementation

**Feature**: 004-program-loader-io-config
**Last Updated**: 2026-01-01
**Status**: Implemented and Tested

## Overview

The RetroCPU monitor firmware implements the XMODEM file transfer protocol for uploading binary programs to RAM via UART. XMODEM is a simple, reliable protocol that uses 128-byte packets with checksum error detection and acknowledgment-based flow control.

## Protocol Specification

### XMODEM Standard

This implementation follows the original XMODEM protocol specification:

- **Packet Size**: 128 bytes of data per packet
- **Error Detection**: 8-bit checksum (sum of all data bytes)
- **Flow Control**: ACK/NAK acknowledgment system
- **Retry Mechanism**: Up to 10 retries per packet
- **Timeout**: Approximately 10 seconds per packet

### Control Characters

| Character | Hex  | Decimal | Purpose                          |
|-----------|------|---------|----------------------------------|
| SOH       | 0x01 | 1       | Start of Header (packet begin)   |
| EOT       | 0x04 | 4       | End of Transmission (transfer complete) |
| ACK       | 0x06 | 6       | Acknowledge (packet accepted)    |
| NAK       | 0x15 | 21      | Negative Acknowledge (retry)     |

## Packet Structure

Each XMODEM packet consists of 132 bytes total:

```
+----------+--------+----------+----------------+----------+
| SOH (1)  | PKT(1) | ~PKT(1)  | DATA (128)     | CKSUM(1) |
+----------+--------+----------+----------------+----------+
```

### Field Descriptions

1. **SOH** (1 byte): Start of Header byte (0x01)
2. **PKT** (1 byte): Packet number (1-255, wraps after 255)
3. **~PKT** (1 byte): Complement of packet number (bitwise NOT)
4. **DATA** (128 bytes): Payload data
5. **CKSUM** (1 byte): Checksum (low 8 bits of sum of all 128 data bytes)

### Packet Number

- First packet is numbered 1
- Increments by 1 for each subsequent packet
- Wraps from 255 to 0 (then continues 1, 2, 3...)
- Complement (~PKT) must equal bitwise NOT of PKT for validation

### Checksum Calculation

The checksum is the low 8 bits of the sum of all 128 data bytes:

```
checksum = 0
for each byte in data[0..127]:
    checksum = (checksum + byte) & 0xFF
```

## State Machine

The XMODEM receiver is implemented as a finite state machine with the following states:

```
┌─────────────────────────────────────────────────────────────┐
│                      XMODEM State Machine                    │
└─────────────────────────────────────────────────────────────┘

    IDLE (0)
      │
      ├──> WAIT_SOH (1) <───────────────────┐
      │         │                            │
      │         ├─ Receive SOH ──> RECV_PKT (2)
      │         │                      │
      │         ├─ Receive EOT ──> HANDLE_EOT ──> IDLE
      │         │                            │
      │         └─ Timeout/Error ──> Send NAK ┘
      │                  │
      └─────────────────>│
                         ↓
                   RECV_PKT (2)
                         │
                         ├─ Read packet number
                         ├─ Read complement
                         ├─ Verify match
                         │
                         ├─ Valid ──> RECV_DATA (4)
                         │                │
                         └─ Invalid ──> Send NAK ──> WAIT_SOH
                                          │
                                          ↓
                                    RECV_DATA (4)
                                          │
                                          ├─ Read 128 data bytes
                                          ├─ Accumulate checksum
                                          │
                                          ↓
                                    RECV_CKSUM (5)
                                          │
                                          ├─ Read checksum byte
                                          ├─ Compare with calculated
                                          │
                                          ├─ Match ──> Write to RAM
                                          │              ├─> Send ACK
                                          │              ├─> Increment PKT#
                                          │              └─> WAIT_SOH
                                          │
                                          └─ Mismatch ──> Send NAK
                                                          ├─> Increment retry count
                                                          └─> WAIT_SOH (or abort if retry > 10)
```

### State Definitions

| State | Value | Description |
|-------|-------|-------------|
| IDLE | 0 | Not receiving; ready to start new transfer |
| WAIT_SOH | 1 | Waiting for SOH or EOT byte |
| RECV_PKT | 2 | Receiving packet number and complement |
| RECV_INV | 3 | (Reserved for future use) |
| RECV_DATA | 4 | Receiving 128 data bytes |
| RECV_CKSUM | 5 | Receiving checksum byte |
| VERIFY | 6 | (Reserved for future use) |

## Transfer Protocol

### Initialization

1. User enters monitor command: `L 0300` (load at address $0300)
2. Monitor validates address is in writable RAM ($0200-$7FFF)
3. Monitor initializes XMODEM state variables:
   - `XMODEM_STATE = WAIT_SOH` (1)
   - `XMODEM_PKT_NUM = 1` (expect first packet)
   - `XMODEM_RETRY_CNT = 0`
   - `XMODEM_ADDR_LO/HI = target address`
4. Monitor displays: "Ready to receive XMODEM. Start transfer now..."
5. Monitor enters XMODEM receive loop

### Transfer Sequence

```
Sender                           Receiver (RetroCPU)
------                           -------------------
                             <── (waiting, no output)

SOH + PKT + ~PKT + DATA + CKSUM ──>
                                    (verify packet number)
                                    (verify complement)
                                    (receive 128 bytes)
                                    (verify checksum)
                                    (write to RAM)
                             <── ACK (0x06)

SOH + PKT + ~PKT + DATA + CKSUM ──>
                             <── ACK (0x06)

... (repeat for all packets) ...

EOT (0x04) ──>
                             <── ACK (0x06)
                                    "Transfer complete"
                                    (return to monitor prompt)
```

### Error Handling

If any error occurs, the receiver sends NAK and waits for retransmission:

```
Sender                           Receiver
------                           --------
SOH + PKT + ~PKT + DATA + CKSUM ──>
                                    (checksum mismatch!)
                             <── NAK (0x15)

SOH + PKT + ~PKT + DATA + CKSUM ──> (retransmit same packet)
                                    (checksum OK)
                             <── ACK (0x06)
```

### Timeout Handling

If no data arrives within the timeout period (~10 seconds):

```
Sender                           Receiver
------                           --------
                             <── (waiting for SOH)
                                    ... (10 seconds pass)
                                    (timeout!)
                             <── NAK (0x15)

SOH + ... ──>                       (sender resumes)
```

## Memory Layout

### Zero Page Variables ($23-$29)

```
$23: XMODEM_STATE       ; Current state (0-6)
$24: XMODEM_PKT_NUM     ; Expected packet number (1-255)
$25: XMODEM_CHECKSUM    ; Running checksum accumulator
$26: XMODEM_BYTE_CNT    ; Bytes received in current packet (0-127)
$27: XMODEM_RETRY_CNT   ; Retry counter (0-10, max)
$28: XMODEM_ADDR_LO     ; Target RAM address low byte
$29: XMODEM_ADDR_HI     ; Target RAM address high byte
```

### RAM Buffer ($0200-$027F)

```
$0200-$027F: XMODEM_BUFFER (128 bytes)
```

This buffer holds the data portion of each packet before it is written to the target RAM address.

## Implementation Details

### Command Handler (CMD_LOAD)

Location: `firmware/monitor/monitor.s`

The `CMD_LOAD` command initiates an XMODEM transfer:

1. Parse target address from user input (e.g., "L 0300")
2. Validate address range ($0200-$7FFF)
   - Reject if address < $0200 (zero page, stack)
   - Reject if address >= $8000 (ROM, I/O space)
3. Initialize XMODEM state variables
4. Display ready message
5. Call `XMODEM_RECEIVE` main loop

### Main Receive Loop (XMODEM_RECEIVE)

The main loop processes packets until EOT or fatal error:

```assembly
XMODEM_RECEIVE:
@MAIN_LOOP:
    ; Check current state
    LDA XMODEM_STATE
    BEQ @DONE              ; State 0 (IDLE) = done

    ; Dispatch to state handler
    CMP #XMODEM_WAIT_SOH
    BEQ @STATE_WAIT_SOH

    ; ... other states ...

@STATE_WAIT_SOH:
    JSR XMODEM_READ_BYTE_TIMEOUT
    BCC @HAVE_DATA
    JMP @TIMEOUT

@HAVE_DATA:
    CMP #XMODEM_EOT
    BEQ @HANDLE_EOT
    CMP #XMODEM_SOH
    BEQ @GOT_SOH
    JMP @BAD_HEADER

    ; ... continue processing ...
```

### Timeout Implementation (XMODEM_READ_BYTE_TIMEOUT)

Due to lack of hardware timer, timeout is implemented via polling loop:

```assembly
XMODEM_READ_BYTE_TIMEOUT:
    LDY #200               ; Outer loop counter
@TIMEOUT_OUTER:
    LDX #0                 ; Inner loop counter
@TIMEOUT_INNER:
    LDA UART_STATUS
    AND #$02               ; Bit 1 = RX ready
    BNE @DATA_READY

    DEX
    BNE @TIMEOUT_INNER
    DEY
    BNE @TIMEOUT_OUTER

    SEC                    ; Timeout occurred
    RTS

@DATA_READY:
    LDA UART_DATA
    CLC                    ; Success
    RTS
```

### Packet Validation

```assembly
; Verify packet number and complement
LDA TEMP               ; Packet number
EOR #$FF               ; Invert
CMP TEMP2              ; Should match complement
BNE @BAD_PACKET        ; Mismatch - reject
```

### Checksum Verification

```assembly
; Accumulate checksum during data reception
@RECV_DATA_LOOP:
    JSR XMODEM_READ_BYTE_TIMEOUT
    BCC @DATA_OK
    JMP @TIMEOUT

@DATA_OK:
    STA XMODEM_BUFFER,X    ; Store byte
    CLC
    ADC XMODEM_CHECKSUM    ; Add to checksum
    STA XMODEM_CHECKSUM

    INC XMODEM_BYTE_CNT
    LDA XMODEM_BYTE_CNT
    CMP #128               ; All 128 bytes?
    BNE @RECV_DATA_LOOP

; Verify checksum
JSR XMODEM_READ_BYTE_TIMEOUT
CMP XMODEM_CHECKSUM
BNE @BAD_CHECKSUM
```

### Writing to RAM (XMODEM_WRITE_BLOCK)

```assembly
XMODEM_WRITE_BLOCK:
    LDY #0
@WRITE_LOOP:
    LDA XMODEM_BUFFER,Y
    STA (XMODEM_ADDR_LO),Y  ; Write via indirect addressing
    INY
    CPY #128
    BNE @WRITE_LOOP

    ; Increment target address by 128
    CLC
    LDA XMODEM_ADDR_LO
    ADC #128
    STA XMODEM_ADDR_LO
    LDA XMODEM_ADDR_HI
    ADC #0
    STA XMODEM_ADDR_HI
    RTS
```

## Timing Characteristics

### Timeout Values

- **Packet Timeout**: ~10 seconds (200 × 256 × polling loop)
- **Transfer Timeout**: 10 retries × 10 seconds = ~100 seconds max per packet
- **Overall Timeout**: Depends on file size and error rate

### Transfer Speed

At 9600 baud with 8N1 (8 data bits, no parity, 1 stop bit):

- **Effective Rate**: 9600 bits/sec ÷ 10 bits/byte = 960 bytes/sec
- **Packet Overhead**: 132 bytes transmitted per 128 bytes payload = 3% overhead
- **Protocol Overhead**: ACK/NAK exchanges, processing time
- **Actual Throughput**: ~800-900 bytes/sec typical

Example transfer times:
- 1 KB program: ~1.2 seconds
- 4 KB program: ~5 seconds
- 16 KB program: ~20 seconds

## Error Conditions

### Address Validation Errors

```
Error Message: "Address too low (min: 0200)"
Cause: User specified address < $0200
Action: Retry with valid address

Error Message: "Address in ROM/IO space (max: 7FFF)"
Cause: User specified address >= $8000
Action: Retry with valid address in RAM range
```

### Transfer Errors

```
Error Message: "Transfer failed: too many checksum errors"
Cause: More than 10 consecutive NAKs for a single packet
Action: Check UART connection, baud rate, cable quality; retry transfer

Error Message: "Transfer failed: timeout"
Cause: No data received within timeout period (10 retries exhausted)
Action: Check sender is transmitting, UART connection, baud rate; retry

Error Message: "Transfer failed: protocol error"
Cause: Invalid packet structure or unexpected state
Action: Reset monitor, retry transfer from beginning
```

## Usage Example

### Terminal Session

```
> L 0300
Ready to receive XMODEM. Start transfer now...
[User initiates XMODEM send in terminal emulator]
...........  [dots appear as packets are received]
Transfer complete

> E 0300
0300: 4C

> G 0300
[Program executes from $0300]
```

### Terminal Emulator Configuration

#### Tera Term (Windows)

1. File → Transfer → XMODEM → Send
2. Select binary file
3. Protocol: XMODEM (checksum)
4. Block size: 128 bytes

#### minicom (Linux)

1. Press Ctrl-A, then Z for menu
2. Select "S" for Send files
3. Choose "xmodem"
4. Select binary file
5. Transfer begins automatically

#### screen (Linux/Mac)

Screen does not have built-in XMODEM support. Use `sx` command:

```bash
# In another terminal (while screen is running):
sx -X /dev/ttyUSB0 < program.bin
```

## Testing

### Unit Tests

Test individual XMODEM functions:

1. Checksum calculation accuracy
2. Packet number validation
3. Timeout behavior
4. State transitions

### Integration Tests

Located in `tests/integration/test_xmodem_upload.py`:

1. **test_xmodem_upload_256bytes**: Upload 256-byte program, verify RAM contents
2. **test_xmodem_checksum_error**: Simulate corrupted packet, verify NAK and retry
3. **test_xmodem_timeout**: Test timeout and recovery
4. **test_program_execution**: Upload program, execute with G command, verify output

### Hardware Validation

1. Upload known binary (e.g., LED blink program)
2. Verify RAM contents with E (examine) command
3. Execute program with G (go) command
4. Observe expected behavior (LED blinking, UART output, etc.)

## Limitations

### Current Implementation

- **Checksum Only**: Uses 8-bit checksum, not CRC (XMODEM-CRC not supported)
- **128-Byte Packets**: Does not support XMODEM-1K (1024-byte packets)
- **No Sender Mode**: Receiver only; cannot send files from RetroCPU
- **Software Timeout**: Timeout is approximate, not precise hardware timer
- **Single File**: No batch transfer support

### Future Enhancements

- Implement XMODEM-CRC for better error detection
- Add XMODEM-1K support for faster transfers
- Implement sender mode (upload from RetroCPU to PC)
- Add hardware timer for precise timeouts
- Support YMODEM for batch transfers and metadata

## References

- [XMODEM Protocol Specification](http://web.archive.org/web/20190729123437/https://www.menie.org/georges/embedded/xmodem.html)
- Ward Christensen's original XMODEM specification (1977)
- RetroCPU Monitor Firmware: `firmware/monitor/monitor.s`
- Feature Specification: `specs/004-program-loader-io-config/spec.md`
- Implementation Plan: `specs/004-program-loader-io-config/plan.md`

## See Also

- [I/O Abstraction Architecture](io_abstraction.md)
- [Flow Control Strategy](flow_control.md)
- [Program Loading User Guide](../user_guides/program_loading.md)
