# RetroCPU Example Programs

Example programs for testing XMODEM upload and execution on RetroCPU.

## Programs

### hello_world.s
Simple test program that outputs "HELLO WORLD" via UART.

**Purpose**: Verify XMODEM upload and program execution work correctly.

**Usage**:
```
1. Build: make hello
2. In monitor: L 0300
3. In terminal: Send hello_world.bin via XMODEM
4. In monitor: G 0300
5. Observe: "HELLO WORLD" appears on terminal
```

**How it works**:
- Uses monitor CHROUT vector at $FFF3 for UART output
- Prints null-terminated string character by character
- Returns to monitor with RTS

### led_blink.s (Future)
LED blink program to verify GPIO output.

**Purpose**: Test programs that interact with hardware peripherals.

## Building

### Requirements
- `ca65` - 6502 assembler (part of cc65 toolchain)
- `ld65` - Linker

### Build Commands
```bash
# Build all examples
make

# Build specific example
make hello
make led

# Clean
make clean
```

## Memory Map

Example programs are designed to be loaded into RAM:

```
$0000-$00FF: Zero page (reserved for monitor)
$0100-$01FF: Stack (reserved for system)
$0200-$02FF: Monitor buffers (XMODEM, PS/2 tables)
$0300-$7FFF: User program space (valid XMODEM upload range)
$8000-$BFFF: BASIC ROM (OSI BASIC interpreter)
$C000-$CFFF: I/O peripherals (UART, GPU, PS/2, etc.)
$E000-$FFFF: Monitor ROM (includes I/O vectors)
```

## XMODEM Upload Process

1. **Start Transfer**:
   ```
   > L 0300
   Ready to receive XMODEM. Start transfer now...
   ```

2. **Send File**: In your terminal emulator:
   - Tera Term: File → Transfer → XMODEM → Send
   - minicom: Ctrl-A S → xmodem
   - Command line: `sx hello_world.bin < /dev/ttyUSB0 > /dev/ttyUSB0`

3. **Wait for Completion**:
   ```
   Transfer complete: 128 bytes loaded
   >
   ```

4. **Execute**:
   ```
   > G 0300
   HELLO WORLD
   >
   ```

## Using Monitor Vectors

Programs can call monitor functions via vectors at $FFF0-$FFFF:

```assembly
CHRIN  = $FFF0  ; Character input (waits for keystroke)
CHROUT = $FFF3  ; Character output (A register)
LOAD   = $FFF6  ; Load/break check (returns A=0)

; Example usage:
    LDA #'H'
    JSR CHROUT  ; Output 'H' to current output device
```

## Testing

Integration tests are available in `tests/integration/`:
- `test_xmodem_upload.py` - Tests XMODEM protocol
- `test_program_execution.py` - Tests program execution after upload

Run tests with cocotb after implementing UART RX.

## Future Examples

Planned example programs:
- `led_blink.s` - GPIO LED blinking
- `echo.s` - Character echo via UART
- `counter.s` - Count and display on 7-segment
- `ps2_test.s` - PS/2 keyboard input test
- `gpu_test.s` - GPU character display test

## Notes

- All programs must fit within available RAM ($0300-$7FFF)
- Programs should preserve monitor state (zero page, stack)
- Use RTS to return to monitor
- Monitor vectors are safe to call from user programs
- XMODEM uploads in 128-byte blocks (programs are padded to multiples of 128)
