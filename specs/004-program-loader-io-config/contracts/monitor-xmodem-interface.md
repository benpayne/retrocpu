# Contract: Monitor XMODEM Interface

**Component**: Monitor Firmware - XMODEM Binary Loader
**Interface Type**: User Command Interface
**Version**: 1.0
**Date**: 2026-01-01

## Purpose

Defines the user-facing interface for the XMODEM binary upload command in the monitor firmware.

## Command Specification

### L (Load Binary) Command

**Syntax**:
```
L <start_address>
```

**Parameters**:
- `start_address`: 4-digit hexadecimal address ($0200-$7FFF) where binary will be loaded

**Example**:
```
> L 0200
```

### Behavior

1. **Address Validation**:
   - Monitor validates address is in range $0200-$7FFF
   - If address < $0200: Display error "Address too low (min: 0200)"
   - If address > $7FFF: Display error "Address in ROM/IO space (max: 7FFF)"

2. **XMODEM Start**:
   - Display message: "Ready to receive XMODEM. Start transfer now..."
   - Send NAK (0x15) to initiate XMODEM transfer
   - Enter XMODEM state machine (WAIT_SOH state)

3. **Transfer Progress** (optional for Phase 1):
   - Display '.' for each successful packet received
   - Display 'R' for each retry (NAK sent)

4. **Transfer Completion**:
   - On EOT received: Send ACK, display "Transfer complete: NNN bytes loaded"
   - Return to command prompt

5. **Transfer Error**:
   - On too many retries: Display "Transfer failed: checksum errors"
   - On timeout: Display "Transfer failed: timeout"
   - On user abort (Ctrl-C / 0x03): Display "Transfer aborted by user"
   - Return to command prompt

### XMODEM Protocol Details

**Packet Structure** (132 bytes total):
```
Byte 0:     SOH (0x01)
Byte 1:     Packet number (1-255)
Byte 2:     Packet number complement (255 - packet_number)
Bytes 3-130: Data (128 bytes)
Byte 131:   Checksum (8-bit sum of data bytes)
```

**Control Flow**:
1. Receiver (monitor) sends NAK to start
2. Sender transmits packet
3. Receiver validates checksum and packet number
4. Receiver sends ACK if valid, NAK if invalid
5. Sender repeats packet on NAK, sends next packet on ACK
6. Sender sends EOT (0x04) when done
7. Receiver sends final ACK

**Error Handling**:
- Maximum 10 retries per packet
- 10-second timeout between packets
- Abort on 10 consecutive failures

### State Variables (Zero Page)

```
$23: XMODEM_STATE    - Current state (0=IDLE, 1=WAIT_SOH, ...)
$24: XMODEM_PKT_NUM  - Expected packet number (1-255)
$25: XMODEM_CHECKSUM - Running checksum
$26: XMODEM_BYTE_CNT - Bytes in current packet (0-127)
$27: XMODEM_RETRY_CNT - Retry counter (0-10)
$28: XMODEM_ADDR_LO  - Current target address (low)
$29: XMODEM_ADDR_HI  - Current target address (high)
```

### RAM Usage

```
$0200-$027F: XMODEM_BUFFER (128 bytes) - Packet data buffer
```

**Note**: XMODEM buffer overlaps user program space. If loading to $0200, first packet will be temporarily buffered here, then written to $0200 after validation, overwriting the buffer. This is acceptable as buffer is only used during transfer.

## Testing Contract

### Test Case 1: Valid Binary Upload

**Setup**: Terminal emulator with XMODEM send capability

**Steps**:
1. Enter monitor command: `L 0300`
2. Monitor displays: "Ready to receive XMODEM. Start transfer now..."
3. In terminal, initiate XMODEM send of test binary (e.g., 512 bytes)
4. Monitor sends NAK, receives packets, sends ACKs
5. Transfer completes

**Expected**:
- Monitor displays: "Transfer complete: 512 bytes loaded"
- Memory $0300-$04FF contains binary data
- Monitor returns to prompt

### Test Case 2: Invalid Address (Too Low)

**Steps**:
1. Enter: `L 0100`

**Expected**:
- Error message: "Address too low (min: 0200)"
- Monitor returns to prompt immediately (does not enter XMODEM mode)

### Test Case 3: Invalid Address (ROM Space)

**Steps**:
1. Enter: `L 8000`

**Expected**:
- Error message: "Address in ROM/IO space (max: 7FFF)"
- Monitor returns to prompt

### Test Case 4: Checksum Error Recovery

**Setup**: Simulated checksum error (modify terminal or use corrupted file)

**Steps**:
1. Enter: `L 0400`
2. Start XMODEM transfer with intentional checksum error in packet 3

**Expected**:
- Packets 1-2 transfer successfully (ACK sent)
- Packet 3 fails checksum (monitor sends NAK)
- Sender retransmits packet 3
- Transfer continues and completes

### Test Case 5: Timeout Abort

**Steps**:
1. Enter: `L 0400`
2. Monitor sends NAK
3. Do not start terminal transfer (let timeout occur)

**Expected**:
- After 10 seconds: "Transfer failed: timeout"
- Monitor returns to prompt

### Test Case 6: User Abort

**Steps**:
1. Enter: `L 0400`
2. Start XMODEM transfer
3. Press Ctrl-C during transfer

**Expected**:
- Monitor aborts immediately
- Display: "Transfer aborted by user"
- Monitor returns to prompt

## Dependencies

- **UART**: Must be functional for receiving binary data at 9600 baud
- **Timer**: Timeout mechanism (10 seconds) - can be implemented via polling loop
- **Memory**: RAM space $0200-$7FFF must be writable

## Terminal Compatibility

Tested with:
- **Tera Term**: File → Transfer → XMODEM → Send
- **minicom**: Ctrl-A S → xmodem
- **sx command**: `sx -X file.bin < /dev/ttyUSB0 > /dev/ttyUSB0`

## Future Enhancements

- CRC-16 checksum (XMODEM-CRC) for better error detection
- 1K block size (XMODEM-1K) for faster transfers
- Progress bar or percentage display
- Automatic baud rate adjustment for faster transfers
