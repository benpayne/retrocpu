# Program Loading User Guide

**Feature**: 004-program-loader-io-config
**Last Updated**: 2026-01-01
**Audience**: End Users and Developers

## Overview

The RetroCPU monitor provides multiple ways to load and run programs:

1. **Binary Program Upload (XMODEM)**: Upload compiled 6502 machine code via UART
2. **BASIC Program Pasting**: Paste BASIC source code into the BASIC interpreter
3. **Manual Entry**: Type BASIC programs or deposit machine code byte-by-byte

This guide covers how to use each method effectively.

## Prerequisites

### Hardware Setup

- RetroCPU board powered and connected via USB-to-serial adapter
- UART TX/RX connected (3-wire: TX, RX, GND)
- Serial port available (e.g., `/dev/ttyUSB0` on Linux, `COM3` on Windows)

### Software Setup

- Terminal emulator installed (Tera Term, minicom, screen, PuTTY)
- 6502 assembler installed (ca65 from cc65 toolchain) for compiling programs
- XMODEM-capable terminal or separate tool (sx, lsx, etc.)

### Verify Connection

1. Open terminal emulator
2. Configure: 9600 baud, 8 data bits, no parity, 1 stop bit (8N1)
3. Connect to serial port
4. Press reset button on RetroCPU
5. Verify you see the welcome banner:

```
RetroCPU Monitor v1.1

6502 FPGA Microcomputer
(c) 2025 - Educational Project

Commands:
  E <addr>      - Examine memory
  D <addr> <val> - Deposit value
  G             - Go to BASIC
  H             - Help

>
```

## Method 1: Binary Program Upload (XMODEM)

### Overview

Use XMODEM to upload compiled 6502 machine code to RAM for execution. This is the fastest and most reliable method for uploading binary programs.

**Advantages**:
- Fast: ~900 bytes/second at 9600 baud
- Reliable: Checksum verification with automatic retry
- Binary-safe: Handles all byte values including control characters
- Progress indication: Dots show transfer progress

**Disadvantages**:
- Requires compilation step (assembling source to binary)
- Requires XMODEM-capable terminal or tool
- Must specify target address manually

### Step 1: Write Your Program

Create a 6502 assembly program. Example `hello_world.s`:

```assembly
; hello_world.s - Simple UART output test
.setcpu "6502"

UART_DATA   = $C000
UART_STATUS = $C001

.segment "CODE"
.org $0300

START:
    LDX #0
LOOP:
    LDA MESSAGE,X
    BEQ DONE
    JSR PRINT_CHAR
    INX
    BNE LOOP

DONE:
    RTS

PRINT_CHAR:
    PHA
@WAIT:
    LDA UART_STATUS
    AND #$01
    BEQ @WAIT
    PLA
    STA UART_DATA
    RTS

MESSAGE:
    .byte "Hello from RAM!", $0D, $0A, 0
```

### Step 2: Compile Your Program

Using ca65 (cc65 assembler):

```bash
# Assemble
ca65 -o hello_world.o hello_world.s

# Link to binary starting at $0300
ld65 -C hello_world.cfg -o hello_world.bin hello_world.o
```

Linker config file `hello_world.cfg`:

```
MEMORY {
    RAM: start = $0300, size = $7D00, fill = yes, fillval = $00;
}

SEGMENTS {
    CODE: load = RAM, type = ro;
}
```

This produces `hello_world.bin` ready for upload.

### Step 3: Configure Terminal Emulator for XMODEM

#### Option A: Tera Term (Windows)

1. File → Transfer → XMODEM → Send
2. Select `hello_world.bin`
3. Protocol: **XMODEM** (checksum, not CRC)
4. Block size: **128 bytes**
5. Keep dialog open, but don't start yet

#### Option B: minicom (Linux)

1. Press Ctrl-A, then Z for menu
2. Select "S" for Send files
3. Choose "xmodem"
4. Navigate to and select `hello_world.bin`
5. minicom will wait for monitor ready signal

#### Option C: screen + sx (Linux/Mac)

Screen doesn't have built-in XMODEM support, so use external tool:

```bash
# In one terminal: Connect via screen
screen /dev/ttyUSB0 9600

# In another terminal: Send file via sx
sx -X /dev/ttyUSB0 < hello_world.bin
```

### Step 4: Initiate Upload on RetroCPU

In the monitor prompt:

```
> L 0300
Ready to receive XMODEM. Start transfer now...
```

**Address Selection**:
- `0300` is a safe starting address for small programs
- Valid range: `0200` to `7FFF` (RAM only)
- Avoid: `0000-01FF` (zero page + stack), `8000-FFFF` (ROM/IO)

### Step 5: Start XMODEM Transfer

**Tera Term**: Click "Send" button in XMODEM dialog
**minicom**: Transfer starts automatically after "S" menu
**screen + sx**: Run `sx` command in second terminal

### Step 6: Monitor Transfer Progress

Watch for progress indicators:

```
Ready to receive XMODEM. Start transfer now...
..................
Transfer complete

>
```

Each dot represents a successfully received packet (128 bytes).

**If Errors Occur**:
- `R` = Retry due to checksum error (normal, up to 10 retries per packet)
- `Transfer failed: too many checksum errors` = Cable/connection issue
- `Transfer failed: timeout` = Sender not transmitting or wrong baud rate
- `Transfer failed: protocol error` = Unexpected packet format

See Troubleshooting section below.

### Step 7: Verify Upload

Examine the first few bytes to verify upload:

```
> E 0300
0300: A2

> E 0301
0301: 00

> E 0302
0302: BD
```

Compare with assembled binary (use `hexdump -C hello_world.bin`).

### Step 8: Run Your Program

Execute from the uploaded address:

```
> G 0300
Hello from RAM!
```

**Note**: The program should RTS (return from subroutine) to return to monitor. If it doesn't, you'll need to reset the system.

## Method 2: BASIC Program Pasting

### Overview

Paste BASIC source code directly into the BASIC interpreter. Useful for developing and testing BASIC programs without typing line-by-line.

**Advantages**:
- No compilation required
- Works with any terminal emulator
- Can edit and re-run immediately
- Source code remains readable

**Disadvantages**:
- Slower than XMODEM (character-by-character pacing)
- Requires flow control configuration
- Text only (not binary)

### Step 1: Write Your BASIC Program

Create a BASIC program in a text editor. Example `fibonacci.bas`:

```basic
10 REM FIBONACCI SEQUENCE
20 A = 0
30 B = 1
40 FOR I = 1 TO 10
50 PRINT A
60 C = A + B
70 A = B
80 B = C
90 NEXT I
100 END
```

### Step 2: Configure Terminal for Flow Control

**Critical**: Enable XON/XOFF flow control to prevent data loss.

#### Tera Term

1. Setup → Serial Port
2. Flow control: **Software (XON/XOFF)**
3. Transmit delay: **0 msec/char** (let XON control pacing)
4. OK

#### minicom

1. Press Ctrl-A, then O for Options
2. Serial port setup
3. Hardware Flow Control: **No**
4. Software Flow Control: **Yes**
5. Save setup as default
6. Exit

#### screen

Screen respects XON/XOFF by default. No configuration needed.

#### PuTTY

1. Connection → Serial
2. Flow control: **XON/XOFF**
3. Session → Save

### Step 3: Enter BASIC Mode

At the monitor prompt:

```
> G
Starting BASIC...

OSI 6502 BASIC Version 1.0
Copyright 1977 by Ohio Scientific Inc.

Memory size? 8192
Terminal width? 40

OK
```

**First-time Setup**:
- Memory size: 8192 (or less if RAM is limited)
- Terminal width: 40 (matches GPU 40-column mode)

### Step 4: Paste BASIC Program

Copy the BASIC program to clipboard, then paste into terminal:

**Tera Term**: Right-click → Paste
**minicom**: Press Ctrl-A, then Y to paste
**screen**: Paste normally (Shift-Insert or Ctrl-Shift-V)
**PuTTY**: Right-click to paste

**What Happens**:
- Each line is transmitted one character at a time
- RetroCPU sends XON ($11) after processing each character
- Terminal waits for XON before sending next character
- Total time: ~0.5 seconds for 100 characters

**Expected Output** (during paste):

```
10 REM FIBONACCI SEQUENCE
20 A = 0
30 B = 1
40 FOR I = 1 TO 10
50 PRINT A
60 C = A + B
70 A = B
80 B = C
90 NEXT I
100 END

OK
```

### Step 5: Verify Program

List the program to verify all lines were received:

```
LIST

10 REM FIBONACCI SEQUENCE
20 A = 0
30 B = 1
40 FOR I = 1 TO 10
50 PRINT A
60 C = A + B
70 A = B
80 B = C
90 NEXT I
100 END

OK
```

If any lines are missing, flow control may not be configured correctly. See Troubleshooting section.

### Step 6: Run Your Program

```
RUN
0
1
1
2
3
5
8
13
21
34

OK
```

### Step 7: Exit BASIC (if needed)

To return to monitor, reset the system (press reset button). There is no "exit" command in OSI BASIC.

**Note**: Resetting will erase the BASIC program from memory. If you want to preserve it, consider uploading it via XMODEM as a binary (after saving from BASIC) in future firmware versions.

## Method 3: Manual Entry

### Depositing Machine Code

For very small programs, you can deposit machine code byte-by-byte using the `D` command:

```
> D 0300 A9    ; LDA #$42
> D 0301 42
> D 0302 8D    ; STA $C000
> D 0303 00
> D 0304 C0
> D 0305 60    ; RTS
```

Verify with `E` command:

```
> E 0300
0300: A9
> E 0301
0301: 42
```

Run with `G` command:

```
> G 0300
(Outputs 'B' to UART)
```

**Advantages**:
- No tools required
- Immediate feedback
- Good for testing and debugging

**Disadvantages**:
- Tedious for programs >10 bytes
- Error-prone (typos)
- Must know machine code opcodes

### Typing BASIC Programs

Enter BASIC mode and type line-by-line:

```
> G
Starting BASIC...
OK
10 PRINT "HELLO"
20 END
RUN
HELLO
OK
```

**Advantages**:
- Simple and immediate
- Good for learning

**Disadvantages**:
- Slow for long programs
- No syntax highlighting or editor features
- Mistakes require retyping entire line

## Terminal Emulator Recommendations

### Best Overall: Tera Term (Windows)

**Pros**:
- Excellent XMODEM support
- Easy flow control configuration
- Logging and capture features
- Macro support

**Cons**:
- Windows only

**Configuration**:
- Baud: 9600, 8N1
- Flow control: XON/XOFF
- XMODEM: Checksum, 128-byte blocks

### Best for Linux: minicom

**Pros**:
- Ubiquitous on Linux systems
- Built-in XMODEM support
- Configurable flow control
- Color support

**Cons**:
- Complex configuration
- Keyboard shortcuts take getting used to

**Configuration**:
```bash
sudo minicom -s
# Configure serial port, flow control, save as default
```

### Best for Simplicity: screen

**Pros**:
- Pre-installed on most Unix systems
- Simple, no configuration needed
- Automatic XON/XOFF support

**Cons**:
- No built-in XMODEM (use external sx tool)
- Limited features

**Usage**:
```bash
screen /dev/ttyUSB0 9600
# Press Ctrl-A, then K to exit
```

### Best for macOS: screen + ZOC Terminal

**screen**: Free, simple, works well for basic use
**ZOC Terminal**: Commercial, excellent features, XMODEM support

## Example Programs

### Example 1: LED Blink

```assembly
; led_blink.s - Toggle LED on GPIO port
.setcpu "6502"

LED_PORT = $C300

.segment "CODE"
.org $0300

START:
    LDA #$01
LOOP:
    STA LED_PORT
    JSR DELAY
    LDA #$00
    STA LED_PORT
    JSR DELAY
    JMP LOOP

DELAY:
    LDX #$00
@OUTER:
    LDY #$00
@INNER:
    DEY
    BNE @INNER
    DEX
    BNE @OUTER
    RTS
```

**Compile and Upload**:
```bash
ca65 -o led_blink.o led_blink.s
ld65 -C led_blink.cfg -o led_blink.bin led_blink.o

# Upload via XMODEM (in monitor):
# > L 0300
# [Send led_blink.bin via XMODEM]
# > G 0300
```

### Example 2: Echo Server

```assembly
; echo_server.s - Echo characters back to UART
.setcpu "6502"

UART_DATA   = $C000
UART_STATUS = $C001

.segment "CODE"
.org $0300

START:
LOOP:
    ; Wait for RX ready
    LDA UART_STATUS
    AND #$02
    BEQ LOOP

    ; Read character
    LDA UART_DATA

    ; Echo it back
@WAIT:
    LDA UART_STATUS
    AND #$01
    BEQ @WAIT
    STA UART_DATA

    ; Loop forever
    JMP LOOP
```

### Example 3: Fibonacci (BASIC)

```basic
10 REM FIBONACCI SEQUENCE GENERATOR
20 PRINT "HOW MANY TERMS? ";
30 INPUT N
40 A = 0
50 B = 1
60 FOR I = 1 TO N
70 PRINT A
80 C = A + B
90 A = B
100 B = C
110 NEXT I
120 END
```

## Troubleshooting

### Problem: "Transfer failed: timeout"

**Cause**: Monitor waiting for XMODEM data, but sender not transmitting

**Solutions**:
1. Verify terminal emulator is configured for XMODEM
2. Check baud rate matches (9600)
3. Try starting transfer again
4. Verify USB cable is connected
5. Check /dev/ttyUSB0 permissions (Linux)

### Problem: "Transfer failed: too many checksum errors"

**Cause**: Data corruption during transmission

**Solutions**:
1. Check UART cable quality (use shorter cable)
2. Verify baud rate is exactly 9600 on both sides
3. Check for electrical noise (move away from power supplies)
4. Try different USB port
5. Verify terminal emulator XMODEM settings (checksum, not CRC)

### Problem: "Address too low (min: 0200)"

**Cause**: Attempted to upload to address below $0200

**Solution**: Use address $0200 or higher:
```
> L 0200    ; Minimum valid address
```

### Problem: "Address in ROM/IO space (max: 7FFF)"

**Cause**: Attempted to upload to ROM or I/O address

**Solution**: Use address $7FFF or lower:
```
> L 7F00    ; Within RAM range
```

### Problem: BASIC paste loses lines

**Cause**: Flow control not enabled in terminal emulator

**Solutions**:
1. Enable XON/XOFF flow control in terminal settings
2. Disable hardware flow control (RTS/CTS)
3. Set transmit delay to 0 (let XON control pacing)
4. Verify terminal respects XON/XOFF

**Test**:
```
> G
OK
10 PRINT "TEST"
20 PRINT "TEST"
30 PRINT "TEST"
[Paste 3 lines]
LIST
```

If all 3 lines appear, flow control is working.

### Problem: BASIC paste is very slow

**Cause**: XON flow control adds character-by-character pacing

**Solution**: This is normal! Flow control ensures reliability at the cost of speed.

**Typical Speeds**:
- Without flow control: 960 chars/sec (unreliable)
- With XON flow control: ~500 chars/sec (reliable)

For large programs, consider using XMODEM instead.

### Problem: Program crashes or hangs after G command

**Cause**: Program doesn't return to monitor (missing RTS)

**Solutions**:
1. Add RTS instruction at end of program
2. Reset system to return to monitor
3. Use JMP instruction to loop forever (if intended behavior)

**Good Example** (returns to monitor):
```assembly
START:
    ; ... program code ...
    RTS    ; Return to monitor
```

**Bad Example** (hangs):
```assembly
START:
    ; ... program code ...
    ; (no RTS - falls through to random memory)
```

### Problem: Upload succeeded but program doesn't work

**Diagnostic Steps**:

1. **Verify upload address**: Program must be loaded at correct address
   ```
   > E 0300
   0300: A2    ; Verify first byte matches assembled code
   ```

2. **Verify execution address**: Use same address for G command
   ```
   > G 0300    ; Not G 0400 if loaded at 0300!
   ```

3. **Check program for RTS**: Program must return to monitor
   ```assembly
   START:
       ; ... code ...
       RTS    ; Required!
   ```

4. **Examine assembled code**: Use hexdump to verify binary
   ```bash
   hexdump -C hello_world.bin | head -20
   ```

5. **Test with simpler program**: Try LED blink or echo server first

## Best Practices

### For XMODEM Upload

1. **Start with small programs**: Test with 256-byte programs first
2. **Use consistent addresses**: $0300 is a safe default for most programs
3. **Verify before running**: Always examine first few bytes after upload
4. **Add RTS instruction**: Ensure program returns to monitor cleanly
5. **Test incrementally**: Upload, test, debug, repeat

### For BASIC Pasting

1. **Always enable flow control**: XON/XOFF is mandatory for reliable pasting
2. **Test with 3-line program first**: Verify flow control works before large paste
3. **Use LIST to verify**: Always check program received correctly
4. **Save source externally**: BASIC programs lost on reset
5. **Keep programs small**: Large BASIC programs are slow to paste

### For Manual Entry

1. **Use for small programs only**: <10 bytes is reasonable limit
2. **Verify each byte**: Use E command to check after each D command
3. **Keep reference handy**: Have opcode table available
4. **Comment your work**: Document what each byte does
5. **Test frequently**: Run program after every few instructions

## Advanced Topics

### Loading Programs to Different Addresses

Programs can be assembled for different addresses. Example linker configs:

**Low RAM** ($0200-$02FF):
```
MEMORY {
    RAM: start = $0200, size = $0100;
}
```

**High RAM** ($7000-$7FFF):
```
MEMORY {
    RAM: start = $7000, size = $1000;
}
```

**Position-Independent Code**:
Use relative branches (BEQ, BNE, BCC, etc.) instead of absolute jumps (JMP) when possible.

### Creating Multi-File Programs

Assemble multiple source files:

```bash
ca65 -o main.o main.s
ca65 -o utils.o utils.s
ld65 -C program.cfg -o program.bin main.o utils.o
```

### Using Labels and Symbols

Export labels for debugging:

```bash
ca65 -o hello.o -l hello.lst hello.s
```

The `.lst` file shows addresses for all labels.

### Binary Patching

Modify uploaded program without re-uploading:

```
> E 0305       ; Find byte to patch
0305: 42
> D 0305 43    ; Change value
0305: 43
> G 0300       ; Re-run with patch
```

## Reference

### Monitor Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| E | `E <addr>` | Examine memory at address |
| D | `D <addr> <val>` | Deposit value to memory |
| G | `G [addr]` | Go to address or BASIC |
| H | `H` | Display help |
| L | `L <addr>` | Load binary via XMODEM |
| I | `I <in> <out>` | Configure I/O sources |
| S | `S` | Display system status |

### Memory Map

| Range | Description | Writable? |
|-------|-------------|-----------|
| $0000-$00FF | Zero Page | Yes (avoid) |
| $0100-$01FF | Stack | Yes (avoid) |
| $0200-$7FFF | General RAM | **Yes (upload here)** |
| $8000-$BFFF | BASIC ROM | No |
| $C000-$DFFF | I/O Registers | Special |
| $E000-$FFFF | Monitor ROM | No |

### Terminal Settings

| Setting | Value |
|---------|-------|
| Baud Rate | 9600 |
| Data Bits | 8 |
| Parity | None |
| Stop Bits | 1 |
| Flow Control | XON/XOFF (software) |
| Hardware Flow | No (off) |

### XMODEM Parameters

| Parameter | Value |
|-----------|-------|
| Protocol | XMODEM (checksum) |
| Packet Size | 128 bytes |
| Checksum | 8-bit sum |
| Timeout | ~10 seconds |
| Max Retries | 10 |

## See Also

- [XMODEM Protocol Implementation](../protocols/xmodem.md)
- [Flow Control Strategy](../protocols/flow_control.md)
- [I/O Configuration Guide](io_configuration.md)
- [Monitor Commands Reference](../../README.md)

## Support

For questions or issues:
- Check [Troubleshooting](#troubleshooting) section above
- Review protocol documentation in `docs/protocols/`
- Consult feature specification in `specs/004-program-loader-io-config/spec.md`
