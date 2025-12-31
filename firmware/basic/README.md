# OSI BASIC for RetroCPU

This directory contains **Microsoft OSI BASIC** for the RetroCPU 6502 FPGA microcomputer. It is authentic 1977 Microsoft BASIC (Version 1.0 REV 3.2) ported from the [mist64/msbasic](https://github.com/mist64/msbasic) project.

## Overview

**OSI BASIC** (Ohio Scientific Incorporated BASIC) is a variant of Microsoft 6502 BASIC from 1977. This implementation:
- Runs on the M65C02 CPU core at 1 MHz
- Uses 16KB ROM space ($8000-$BFFF)
- Provides ~32KB free for BASIC programs
- Supports 6-digit floating point arithmetic
- Includes strings, arrays, and control flow

## What is OSI BASIC?

OSI BASIC is the same BASIC that shipped with Ohio Scientific computers in 1977. It's a "minimal" variant of Microsoft BASIC, meaning it has clean core features without platform-specific extensions. This makes it excellent for educational purposes.

**Features:**
- Floating-point arithmetic (6-digit precision)
- String variables and operations
- Arrays (DIM statement)
- Control flow (FOR/NEXT, IF/THEN, GOTO, GOSUB/RETURN)
- Standard I/O (INPUT, PRINT)
- Program management (LIST, NEW, RUN)
- Mathematical functions (SIN, COS, TAN, ATN, EXP, LOG, SQR, ABS, etc.)

**What's NOT included:**
- File I/O (LOAD/SAVE) - no storage device
- Graphics commands - text only
- Machine language CALL - not implemented

## Memory Map

```
$0000-$00FF : Zero Page RAM (CPU + BASIC variables)
$0100-$01FF : Stack
$0200-$02FF : System buffers / Monitor workspace
$0300-$7FFF : BASIC program storage & variables (~32KB free)
$8000-$BFFF : BASIC ROM (16KB) ← This code
$C000-$C0FF : UART registers
$E000-$FFFF : Monitor ROM
```

## Building

### Prerequisites

- `ca65` assembler (from cc65 package)
- `ld65` linker (from cc65 package)
- `python3`
- `git`

### Build Commands

```bash
# Build basic_rom.hex from OSI BASIC
make

# Clean build artifacts
make clean

# Remove everything including cloned repository
make distclean
```

### Build Process

The Makefile automatically:
1. Clones the `mist64/msbasic` repository if not present
2. Copies RetroCPU-specific configuration files
3. Assembles OSI BASIC with ca65
4. Links to produce a 16KB binary
5. Converts to hex format for Verilog `$readmemh()`

### Output Files

- `basic_rom.hex` - Hex file loaded by `rtl/memory/rom_basic.v`
- `osi_retrocpu.bin` - Binary file (16384 bytes)
- `osi_retrocpu.lbl` - Label file for debugging

## I/O Vector Integration

OSI BASIC communicates with the RetroCPU monitor through three I/O vectors:

| Vector | Address | Function | Monitor Routine |
|--------|---------|----------|-----------------|
| MONRDKEY | $FFF0 | Character input | JMP to CHRIN (UART RX) |
| MONCOUT | $FFF3 | Character output | JMP to CHROUT (UART TX) |
| MONISCNTC | $FFF6 | Check for Ctrl-C | Returns A=0 (no break) |

These are defined in `defines_retrocpu.s` and map to the monitor's I/O routines.

## Using BASIC

### Starting BASIC

From the monitor prompt:
```
> G
```

BASIC will ask two configuration questions:
```
MEMORY SIZE? 32000
TERMINAL WIDTH? 72
```

You'll then see:
```
31999 BYTES FREE

OSI 6502 BASIC VERSION 1.0 REV 3.2
COPYRIGHT 1977 BY MICROSOFT CO.

OK
```

### Example Programs

**Hello World:**
```basic
10 PRINT "HELLO WORLD"
RUN
```

**Counting Loop:**
```basic
10 FOR I=1 TO 10
20 PRINT I
30 NEXT I
RUN
```

**Variables and Math:**
```basic
10 A=10
20 B=20
30 C=A+B
40 PRINT "SUM=";C
RUN
```

**Temperature Conversion:**
```basic
10 PRINT "CELSIUS TO FAHRENHEIT"
20 INPUT "TEMP IN C"; C
30 F=C*9/5+32
40 PRINT C;"C = ";F;"F"
50 GOTO 20
RUN
```

**Subroutines:**
```basic
10 GOSUB 100
20 PRINT "BACK IN MAIN"
30 END
100 PRINT "IN SUBROUTINE"
110 RETURN
RUN
```

### Available Commands

| Command | Description |
|---------|-------------|
| `LIST` | Display program |
| `RUN` | Execute program |
| `NEW` | Clear program |
| `PRINT` or `?` | Output to terminal |
| `INPUT` | Get user input |
| `LET A=value` | Assign variable (LET optional) |
| `IF condition THEN statement` | Conditional execution |
| `FOR I=start TO end` | Loop start |
| `NEXT I` | Loop end |
| `GOTO line` | Jump to line |
| `GOSUB line` | Call subroutine |
| `RETURN` | Return from subroutine |
| `END` | Stop program |
| `REM comment` | Comment |
| `DIM array(size)` | Declare array |

### Mathematical Functions

- `SIN(x)`, `COS(x)`, `TAN(x)` - Trigonometric (radians)
- `ATN(x)` - Arctangent
- `EXP(x)` - e^x
- `LOG(x)` - Natural logarithm
- `SQR(x)` - Square root
- `ABS(x)` - Absolute value
- `INT(x)` - Integer part
- `SGN(x)` - Sign (-1, 0, or 1)
- `RND(x)` - Random number

### String Operations

```basic
10 A$="HELLO"
20 B$=" WORLD"
30 C$=A$+B$
40 PRINT C$
```

- `LEFT$(str,n)` - Leftmost n characters
- `RIGHT$(str,n)` - Rightmost n characters
- `MID$(str,start,n)` - Substring
- `LEN(str)` - String length

## Configuration Files

### defines_retrocpu.s

Configures OSI BASIC for RetroCPU:
- I/O vector addresses ($FFF0, $FFF3, $FFF6)
- Memory layout (RAM starts at $0300)
- Feature flags (6-digit floating point)
- Also sets `OSI := 1` to inherit OSI-specific code

### retrocpu_osi.cfg

Linker configuration:
- Places BASIC ROM at $8000-$BFFF (16KB)
- Fills unused space with NOP ($EA)
- Organizes segments (HEADER, CODE, KEYWORDS, etc.)

## Entry Point

**Important:** The BASIC cold start entry point is at **$9D11**, not $8000!

- `$8000` contains TOKEN_ADDRESS_TABLE (data tables)
- `$9D11` is COLD_START (actual executable code)

The monitor's `G` command jumps to $9D11.

## Known Issues

### UART Input Timing

The RetroCPU UART RX requires ~50ms between characters for reliable input. When typing in BASIC:
- Type at normal speed (INPUT statements work fine)
- For pasting, configure terminal with 50ms character delay

This is a hardware limitation, not specific to BASIC.

### No Ctrl-C Break

Currently, VEC_LOAD always returns "no break" (A=0). This means:
- You cannot interrupt running programs with Ctrl-C
- Use the reset button to restart if a program hangs
- Future enhancement: Implement actual Ctrl-C detection

## Educational Value

OSI BASIC is excellent for learning because:

1. **Historical Authenticity**: This is real 1977 Microsoft BASIC
2. **Clean Implementation**: No platform-specific cruft
3. **Source Available**: Full commented assembly in mist64/msbasic
4. **Small Size**: ~8KB of code, understandable
5. **Well-Documented**: Both code and behavior documented

### Learning Resources

- [mist64/msbasic](https://github.com/mist64/msbasic) - Source code repository
- [Pagetable Blog](https://www.pagetable.com/?p=46) - "Create Your Own Microsoft BASIC"
- Ben Eater's 6502 videos - Uses same BASIC variant
- [OSI BASIC Manual](https://osiweb.org/manuals.html) - Original documentation

## Attribution

This BASIC implementation is derived from:

**mist64/msbasic** by Michael Steil
License: BSD 2-Clause
Repository: https://github.com/mist64/msbasic

Based on disassembly and reconstruction of:

**Microsoft 6502 BASIC Version 1.0**
Copyright 1977 Microsoft Corporation
Now open-sourced under MIT license (2025)

RetroCPU adaptation by: RetroCPU Project (2025)
License: MIT (for RetroCPU-specific files)

## Technical Details

### Zero Page Usage

OSI BASIC uses these zero page ranges:
- `$00-$0C`: BASIC interpreter variables
- `$0D-$5A`: More interpreter state
- `$5B-$64`: Additional workspace
- `$65+`: Available for monitor/system

### Cold Start Sequence

1. Monitor sets up I/O vectors at $0300-$0303
2. Monitor jumps to COLD_START ($9D11)
3. BASIC initializes zero page variables
4. BASIC prompts for MEMORY SIZE
5. BASIC prompts for TERMINAL WIDTH
6. BASIC displays banner and "OK" prompt
7. Ready for input!

### Program Storage

Programs are tokenized and stored starting at $0300:
- Each line: [link pointer][line number][tokenized code][$00]
- Variables stored after program text
- String space grows down from top of memory
- Careful memory management prevents collisions

## Testing

### Quick Test

```bash
# From monitor prompt
> G
MEMORY SIZE? 32000
TERMINAL WIDTH? 72

# At OK prompt
PRINT 2+2
(should output: 4)
```

### Full Test Suite

See the comprehensive test in the plan that covers:
- Arithmetic
- Variables
- Program entry and LIST
- RUN command
- FOR loops
- String operations

All tests pass! ✓

## Troubleshooting

**Q: BASIC doesn't start, system resets?**
A: Check that monitor jumps to $9D11 (COLD_START), not $8000

**Q: Characters garbled or dropped?**
A: Slow down typing or add 50ms character delay in terminal

**Q: "MEMORY SIZE?" appears but no input works?**
A: UART RX timing issue - try slower typing

**Q: Program won't break with Ctrl-C?**
A: Ctrl-C not yet implemented - use reset button

**Q: "SYNTAX ERROR" on valid code?**
A: Check for:
  - Line numbers (required for programs, not immediate mode)
  - Proper statement terminators
  - No lowercase (BASIC keywords must be uppercase)

## Future Enhancements

Potential improvements:
1. Implement full Ctrl-C detection in VEC_LOAD
2. Fix UART RX timing for faster input
3. Add LOAD/SAVE to SD card or similar storage
4. Create library of example programs
5. Add PS/2 keyboard support (User Story 4)
6. Add LCD output (User Story 3)

## Success!

🎉 **Congratulations!** You now have authentic 1977 Microsoft BASIC running on your FPGA! This is the same BASIC that powered the microcomputer revolution.

**31,999 bytes free** - plenty of space for your programs!

---

For questions or issues, see the main RetroCPU documentation or file an issue on GitHub.
