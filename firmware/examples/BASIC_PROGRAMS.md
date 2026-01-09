# BASIC Program Examples for RetroCPU

This directory contains example BASIC programs for testing the RetroCPU system,
particularly the UART paste functionality with XON/XOFF flow control.

## Available Programs

### 1. basic_hello.bas
A simple "Hello World" program that demonstrates:
- Basic PRINT statements
- FOR/NEXT loops
- Multi-line program structure

**Lines**: 18
**Purpose**: Quick test of paste functionality

### 2. basic_loop.bas
An infinite loop demonstration that:
- Counts from 0 to 1000
- Can be interrupted with BREAK key
- Useful for testing dual I/O modes

**Lines**: 22
**Purpose**: Testing I/O mode switching during execution

### 3. basic_test.bas
A comprehensive test suite covering:
- Arithmetic operations (+, -, *, /)
- String handling and concatenation
- FOR/NEXT loops
- IF/THEN conditionals
- Variable assignment

**Lines**: 43
**Purpose**: Full BASIC feature validation

## How to Use

### Prerequisites

1. **RetroCPU Hardware**: Colorlight i5 board with monitor firmware
2. **Terminal Emulator**: Tera Term, minicom, or similar with XMODEM support
3. **BASIC Interpreter**: OSI BASIC loaded at $8000-$9FFF (see firmware/basic/)

### Step 1: Configure Terminal for Flow Control

**Tera Term (Windows)**:
```
Setup → Serial Port → Flow Control: XON/XOFF
Setup → Serial Port → Transmit delay: 10 ms/char (for safety)
```

**minicom (Linux)**:
```
Ctrl-A → O → Serial port setup → Hardware Flow Control: No
Ctrl-A → O → Serial port setup → Software Flow Control: Yes
```

**screen (macOS/Linux)**:
```
# XON/XOFF is typically enabled by default in screen
# No additional configuration needed
```

### Step 2: Boot RetroCPU and Start BASIC

1. Connect to RetroCPU via UART (115200 baud, 8N1)
2. Wait for monitor prompt: `> `
3. Configure I/O to UART mode (if not already):
   ```
   > I 0 0
   I/O Config: IN=UART, OUT=UART
   ```
4. Jump to BASIC interpreter:
   ```
   > G
   Starting BASIC...
   ```

You should see the BASIC prompt:
```
OSI 6502 BASIC VERSION 1.0 REV 3.2
COPYRIGHT 1977 BY MICROSOFT CO.

MEMORY SIZE? [Enter]
TERMINAL WIDTH? [Enter]

READY

>
```

### Step 3: Paste BASIC Program

1. In your terminal emulator, open the paste function:
   - **Tera Term**: Edit → Paste File → select basic_hello.bas
   - **minicom**: Ctrl-A → Y → select file
   - **screen**: Copy file contents, then paste into terminal

2. The monitor will send XON ($11) after each character to pace the input

3. You should see each line echo as it's received:
   ```
   >10 REM ===================================
   >20 REM RETROCPU BASIC HELLO WORLD PROGRAM
   >30 REM ===================================
   ...
   ```

4. After paste completes, you're back at BASIC prompt:
   ```
   READY

   >
   ```

### Step 4: Run the Program

At the BASIC prompt, type:
```
>RUN
```

Expected output (for basic_hello.bas):
```
HELLO FROM RETROCPU!
THIS PROGRAM WAS PASTED VIA UART

FLOW CONTROL TEST:
LINE 1
LINE 2
LINE 3
LINE 4
LINE 5
LINE 6
LINE 7
LINE 8
LINE 9
LINE 10

TEST COMPLETE!

READY

>
```

## Testing Different I/O Modes

### Test 1: UART Input, Display Output (I 0 1)

1. Before starting BASIC, configure I/O:
   ```
   > I 0 1
   I/O Config: IN=UART, OUT=Display
   ```

2. Start BASIC and paste program via UART (terminal)

3. Program output appears on HDMI display only

**Use case**: Debugging - paste from computer, view on monitor

### Test 2: PS/2 Input, Display Output (I 1 1)

1. Configure standalone mode:
   ```
   > I 1 1
   I/O Config: IN=PS2, OUT=Display
   ```

2. Start BASIC (command must be typed on PS/2 keyboard now)

3. Type the BASIC program on PS/2 keyboard

4. Output appears on HDMI display

**Use case**: Standalone operation without UART connection

### Test 3: Dual Output (I 0 2)

1. Configure dual output:
   ```
   > I 0 2
   I/O Config: IN=UART, OUT=Both
   ```

2. Start BASIC and paste program

3. Output appears on both UART and HDMI simultaneously

**Use case**: Debugging - compare outputs, capture logs

## Flow Control Details

### XON Character

After each character is read via UART, the monitor sends:
- **Character**: XON ($11, Ctrl-Q, ASCII 17)
- **Purpose**: Signal sender that receiver is ready for next byte
- **Timing**: Sent immediately after character is processed

### Why Flow Control Matters

Without flow control, pasting multi-line BASIC programs can result in:
- Lost characters (buffer overruns)
- Corrupted line numbers
- Syntax errors
- Incomplete programs

With XON flow control:
- Terminal waits for XON before sending next character
- No data loss, even with slow BASIC interpreter
- Reliable paste of programs up to ~100 lines

### XOFF Support (Future Work)

The current implementation only sends XON (ready signal).
Full XON/XOFF would also send XOFF ($13) to pause transmission.
This is deferred to future work but not required for reliable operation.

## Troubleshooting

### Problem: Characters are dropped during paste

**Solution**:
- Verify flow control is enabled in terminal (XON/XOFF)
- Increase character delay in terminal settings (10-20 ms/char)
- Check UART baud rate matches (115200)

### Problem: Program doesn't run after paste

**Solution**:
- List the program in BASIC: `LIST`
- Check for syntax errors or incomplete lines
- Verify REM lines don't have special characters
- Try pasting smaller sections at a time

### Problem: BASIC interpreter not responding

**Solution**:
- Exit BASIC with Ctrl-C or BREAK key
- Return to monitor prompt
- Check I/O configuration: `> S` (status command)
- Reconfigure if needed: `> I 0 0`

### Problem: XON characters appear in BASIC output

**Solution**:
- This indicates terminal is displaying flow control chars
- In Tera Term: Setup → Terminal → Local echo OFF
- In minicom: Ctrl-A → E (toggle local echo)

## Example Session

Complete example of pasting and running basic_hello.bas:

```
$ screen /dev/ttyUSB0 115200

RetroCPU Monitor v1.1

6502 FPGA Microcomputer
(c) 2025 - Educational Project

Commands:
  E <addr>      - Examine memory
  D <addr> <val> - Deposit value
  G             - Go to BASIC
  H             - Help

> I 0 0
I/O Config: IN=UART, OUT=UART
> G
Starting BASIC...

OSI 6502 BASIC VERSION 1.0 REV 3.2
COPYRIGHT 1977 BY MICROSOFT CO.

MEMORY SIZE?
TERMINAL WIDTH?

READY

>[Paste basic_hello.bas here]
>10 REM ===================================
>20 REM RETROCPU BASIC HELLO WORLD PROGRAM
...
>180 END

READY

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

## Next Steps

1. **Create your own programs**: Use these examples as templates
2. **Test I/O modes**: Try different input/output combinations
3. **Benchmark**: Measure paste speed with/without flow control
4. **Contribute**: Add new example programs to this directory

## References

- Feature Specification: `/opt/wip/retrocpu/specs/004-program-loader-io-config/spec.md`
- Quickstart Guide: `/opt/wip/retrocpu/specs/004-program-loader-io-config/quickstart.md`
- Monitor Source: `/opt/wip/retrocpu/firmware/monitor/monitor.s`
- OSI BASIC: `/opt/wip/retrocpu/firmware/basic/`
