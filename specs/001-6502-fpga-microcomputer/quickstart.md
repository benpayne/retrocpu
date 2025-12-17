# Quick Start Guide: 6502 FPGA Microcomputer

**Last Updated**: 2025-12-16
**Target Board**: Colorlight i5 (Lattice ECP5-25F)
**Toolchain**: Open-source (Yosys, nextpnr, cocotb)

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Tool Installation](#tool-installation)
3. [Hardware Setup](#hardware-setup)
4. [Building the Project](#building-the-project)
5. [Programming the FPGA](#programming-the-fpga)
6. [First Boot](#first-boot)
7. [Using the Monitor](#using-the-monitor)
8. [Running BASIC](#running-basic)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

## Prerequisites

### Required Hardware
- **Colorlight i5 FPGA board** (Lattice ECP5-25F)
- **USB cable** (for programming and UART communication)
- **Computer** running Linux (Ubuntu/Debian recommended)

### Optional Hardware (for later user stories)
- HD44780-compatible 2x16 or 2x20 character LCD
- PMOD adapter for LCD (7 pins: 4 data + 3 control)
- PS/2 keyboard (or USB keyboard with PS/2 adapter)
- Logic analyzer or oscilloscope (for debugging)

### Knowledge Prerequisites
- Basic understanding of terminal/command line
- Familiarity with serial terminal programs
- Optional: 6502 assembly or BASIC programming experience

## Tool Installation

### Ubuntu/Debian Linux

```bash
# Update package lists
sudo apt update

# Install FPGA toolchain
sudo apt install yosys nextpnr-ecp5 ecppack openFPGALoader

# Install simulation tools
sudo apt install iverilog gtkwave

# Install Python testing framework
pip3 install --user cocotb cocotb-test pytest

# Install 6502 assembler (for firmware development)
sudo apt install cc65

# Install serial terminal
sudo apt install minicom screen

# Verify installations
yosys --version        # Should show Yosys 0.9+
nextpnr-ecp5 --version # Should show nextpnr-ecp5
iverilog -v            # Should show Icarus Verilog 10.0+
ca65 --version         # Should show ca65 from cc65
```

### Alternative: Docker Container

```bash
# Use pre-built FPGA toolchain container
docker pull hdlc/sim:osvb
docker pull hdlc/impl

# Run tools in container
docker run --rm -v $(pwd):/work -w /work hdlc/impl yosys --version
```

### macOS

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install tools
brew install yosys icarus-verilog gtkwave
brew install --HEAD nextpnr-ecp5

# Install Python tools
pip3 install cocotb cocotb-test pytest

# Serial terminal
brew install minicom
```

## Hardware Setup

### Colorlight i5 Board Connections

```
   +------------------+
   |  Colorlight i5   |
   +------------------+
   |                  |
   | [USB Port] ------+----> USB cable to computer
   |                  |      (Programming + UART)
   | [LED 1-4]        |
   | [FIRE 2] --------+----> Reset button (T1 pin)
   |                  |
   | [PMOD Conn] -----+----> Future: LCD display
   |                  |
   | [PS/2 Pins] -----+----> K5 (CLK), B3 (DATA)
   +------------------+
```

### Pin Assignments (from colorlight_i5.lpf)

| Function | Pin | Notes |
|----------|-----|-------|
| Clock (25 MHz) | P3 | System clock input |
| Reset button | T1 | FIRE 2, active-low with pull-up |
| UART TX | J17 | Transmit to STM32 USB bridge |
| PS/2 Clock | K5 | Keyboard clock (with pull-up) |
| PS/2 Data | B3 | Keyboard data (with pull-up) |
| LED 1 | N18 | Status/debug LED |
| LED 2 | N17 | Status/debug LED |
| LED 3 | L20 | Status/debug LED |
| LED 4 | M18 | Status/debug LED |

### USB Connection

The Colorlight i5 includes an onboard STM32 that provides:
- FPGA programming via openFPGALoader
- USB-to-UART bridge for serial communication
- Single USB cable for both functions

**Linux**: Board appears as `/dev/ttyUSB0` (or `/dev/ttyACM0`)
**macOS**: Board appears as `/dev/cu.usbserial-*` or `/dev/tty.usbserial-*`

Add user to dialout group for serial access (Linux):
```bash
sudo usermod -a -G dialout $USER
# Log out and back in for group change to take effect
```

## Building the Project

### 1. Clone Repository

```bash
git clone https://github.com/yourname/retrocpu.git
cd retrocpu

# Initialize submodules (6502 CPU core)
git submodule update --init --recursive
```

### 2. Build Firmware

The project requires building the monitor and BASIC ROMs before synthesis:

```bash
# Build monitor program
cd firmware/monitor
make clean
make              # Generates monitor.hex

# Build BASIC ROM
cd ../basic
make clean
make              # Generates basic_rom.hex (from EhBASIC source)

cd ../..
```

**Expected output**:
- `firmware/monitor/monitor.hex` (~1 KB)
- `firmware/basic/basic_rom.hex` (~12 KB)

### 3. Run Tests (Optional but Recommended)

```bash
# Unit tests (test individual modules)
cd tests/unit
make test-all

# Integration tests (test system integration)
cd ../integration
make test-all

# View test results
cat test_results.txt
```

**TDD Note**: Per project constitution, all tests should pass before synthesis.

### 4. Synthesize FPGA Bitstream

```bash
cd build

# Full build (synthesis + place-and-route + bitstream)
make all

# Or step-by-step:
make synth        # Yosys synthesis -> soc_top.json
make pnr          # nextpnr place-and-route -> soc_top.config
make bitstream    # ecppack bitstream generation -> soc_top.bit

# View resource utilization
cat synth/reports/utilization.rpt
```

**Expected resources** (P1 + P2 features):
- LUTs: ~12K-15K (50-62% of 24K)
- Block RAMs: 32 (57% of 56)
- Max frequency: >50 MHz (well above 25 MHz system clock)

### 5. Build Time

**Typical build times** (on modern laptop):
- Firmware: <10 seconds
- Tests: 1-5 minutes
- Synthesis: 1-2 minutes
- Place-and-route: 2-3 minutes
- **Total**: ~5-10 minutes for full clean build

## Programming the FPGA

### Using openFPGALoader

```bash
# From build/ directory
make program

# Or manually:
openFPGALoader -b colorlight-i5 build/soc_top.bit
```

**Expected output**:
```
Jtag frequency : requested 6.00MHz   -> real 6.00MHz
Load SRAM via JTAG: [==================================================] 100.00%
Done
Wait for CFG_DONE DONE
```

**Programming time**: ~10-15 seconds

### Verify Programming

The board should:
1. LEDs may blink briefly during programming
2. After programming, system boots automatically
3. Reset button (FIRE 2 / T1) can restart the system

## First Boot

### 1. Connect Serial Terminal

```bash
# Using screen (simple)
screen /dev/ttyUSB0 9600

# Using minicom (more features)
minicom -D /dev/ttyUSB0 -b 9600

# Using PuTTY (GUI, cross-platform)
# Connection: Serial, Port: /dev/ttyUSB0, Speed: 9600
```

**Serial Settings**: 9600 baud, 8 data bits, No parity, 1 stop bit (8N1)

### 2. Reset the System

Press the **FIRE 2 button** (reset button on T1 pin) to boot the system.

### 3. Expected Boot Output

```
RetroCPU Monitor v1.0

6502 FPGA Microcomputer
(c) 2025 - Educational Project

Commands:
  E addr      - Examine memory
  D addr val  - Deposit value to memory
  J addr      - Jump to address
  G           - Go to BASIC

>
```

**Boot time**: <100 milliseconds from reset release

### 4. Test Monitor Commands

```
> E 0000
0000: 00

> D 0200 42
> E 0200
0200: 42

> E FFFC
FFFC: 00 E0
(Shows RESET vector points to $E000)
```

## Using the Monitor

### Monitor Commands

| Command | Syntax | Description | Example |
|---------|--------|-------------|---------|
| **E** | E addr | Examine memory at address | `E C000` |
| **D** | D addr value | Deposit byte to memory (RAM only) | `D 0300 FF` |
| **J** | J addr | Jump to address and execute | `J 0300` |
| **G** | G | Go to BASIC (jump to $8000) | `G` |

### Address Format

- **Hexadecimal** (4 digits): `E 1234`, `D ABCD 99`
- **No $ or 0x prefix**: Just hex digits
- **Leading zeros optional**: `E 200` same as `E 0200`

### Memory Examination Examples

```
# Check zero page
> E 0000
0000: 00

# Check stack
> E 01FF
01FF: 42

# Check ROM
> E E000
E000: 4C    (JMP opcode for RESET handler)

# Check I/O registers
> E C001
C001: 01    (UART TX ready bit set)
```

### Memory Deposit Examples

```
# Write to zero page
> D 0010 42
> E 0010
0010: 42

# Write small program at $0300
> D 0300 A9    ; LDA #$41
> D 0301 41
> D 0302 20    ; JSR CHROUT ($E100)
> D 0303 00
> D 0304 E1
> D 0305 60    ; RTS
> J 0300       ; Execute (prints 'A')
A>
```

## Running BASIC

### 1. Start BASIC

From the monitor prompt:
```
> G
```

### 2. BASIC Boot Output

```
Microsoft BASIC
Version 1.0

Ready
>
```

### 3. Basic BASIC Commands

```basic
# Arithmetic
>PRINT 2+2
4
>PRINT 100*50
5000

# Variables
>LET A=42
>PRINT A
42

# Simple program
>10 PRINT "HELLO WORLD"
>20 GOTO 10
>RUN
HELLO WORLD
HELLO WORLD
HELLO WORLD
...
(Press Ctrl+C to break)

# List program
>LIST
10 PRINT "HELLO WORLD"
20 GOTO 10

# Clear program
>NEW

# Exit to monitor
(Type `CALL 57344` to jump to $E000 monitor)
```

### 4. Example BASIC Programs

**Count to 10**:
```basic
10 FOR I=1 TO 10
20 PRINT I
30 NEXT I
40 END
```

**Fibonacci sequence**:
```basic
10 A=0
20 B=1
30 PRINT A
40 C=A+B
50 A=B
60 B=C
70 IF B<1000 THEN GOTO 30
80 END
```

**Simple calculator**:
```basic
10 INPUT "First number: "; A
20 INPUT "Second number: "; B
30 PRINT "Sum: "; A+B
40 PRINT "Product: "; A*B
50 GOTO 10
```

## Troubleshooting

### No Serial Output

**Symptoms**: Serial terminal shows nothing after reset

**Solutions**:
1. **Check USB connection**: `ls /dev/ttyUSB*` should show device
2. **Check baud rate**: Must be 9600 baud, 8N1
3. **Check permissions**: `sudo chmod 666 /dev/ttyUSB0` or add user to dialout group
4. **Try different terminal**: minicom vs screen vs PuTTY
5. **Press reset button**: System must boot after programming

### Garbled Serial Output

**Symptoms**: Random characters, symbols instead of text

**Solutions**:
1. **Verify baud rate**: 9600 baud exactly
2. **Check parity/stop bits**: Must be 8N1 (no parity, 1 stop bit)
3. **Clock frequency**: Verify 25 MHz clock is stable
4. **Reprogram FPGA**: May have programming glitch

### System Hangs or Freezes

**Symptoms**: No response to commands, system stops

**Solutions**:
1. **Press reset button** (FIRE 2 / T1 pin)
2. **Reprogram FPGA**: `make program` from build/
3. **Check monitor ROM**: Verify monitor.hex built correctly
4. **Run tests**: `make test-all` in tests/ directory
5. **View waveforms**: Run simulation to debug

### Synthesis Fails

**Symptoms**: Yosys or nextpnr reports errors

**Solutions**:
1. **Check tool versions**: Yosys 0.9+, nextpnr-ecp5 latest
2. **Clean build**: `make clean && make all`
3. **Check HDL syntax**: Run `iverilog -t null rtl/**/*.v`
4. **Review error messages**: Look for undefined modules, wire mismatches
5. **Check pin constraints**: Verify colorlight_i5.lpf is correct

### BASIC Won't Start

**Symptoms**: Monitor works but `G` command fails or hangs

**Solutions**:
1. **Check BASIC ROM**: Verify basic_rom.hex was built
2. **Check ROM size**: Should be ~12KB (3072 lines in .hex)
3. **Check RESET vector**: `E FFFC` should show `00 E0` (points to $E000)
4. **Check BASIC ROM location**: `E 8000` should show first bytes of BASIC
5. **Reprogram**: ROM may not have loaded during synthesis

### Can't Write to Memory

**Symptoms**: `D` command doesn't work, values don't stick

**Solutions**:
1. **Check address range**: Only $0000-$7FFF is writable RAM
2. **ROM is read-only**: $8000-$FFFF cannot be written
3. **I/O registers**: Some I/O addresses are read-only
4. **Address decoder**: Run address decoder unit tests

## Next Steps

### Immediate Next Steps (P1/P2 Complete)

1. **Write 6502 assembly programs**
   - Create .s files in firmware/
   - Assemble with ca65
   - Load via monitor D command

2. **Write BASIC programs**
   - Explore BASIC commands (`HELP` in some BASIC versions)
   - Save program listings externally (copy from terminal)

3. **Explore memory map**
   - Examine different memory regions
   - Understand zero page, stack, ROM vectors

### Future Enhancements (P3-P5)

4. **Add LCD display** (User Story 3)
   - Connect HD44780 LCD to PMOD
   - Update .lpf with LCD pins
   - Test LCD module with `E C100` writes

5. **Add PS/2 keyboard** (User Story 4)
   - Connect PS/2 keyboard
   - Read scan codes from $C200
   - Implement scan code to ASCII conversion in monitor

6. **Standalone operation** (User Story 5)
   - Use LCD + keyboard without PC
   - Run BASIC programs standalone

### Learning Resources

- **6502 Architecture**:
  - docs/learning/6502_basics.md
  - http://www.6502.org/ (6502.org reference)
  - "Programming the 6502" by Rodnay Zaks

- **HDL and FPGA**:
  - docs/learning/hdl_patterns.md
  - Verilog tutorial: https://www.asic-world.com/verilog/

- **Module Documentation**:
  - docs/modules/cpu.md
  - docs/modules/memory.md
  - docs/modules/uart.md

- **Testing**:
  - cocotb documentation: https://docs.cocotb.org/
  - tests/unit/README.md (test examples)

## Summary

You now have a working 6502 microcomputer running on FPGA! The system boots to a monitor, allows memory examination and modification, and runs Microsoft BASIC. This foundation can be extended with additional peripherals and features following the prioritized user stories.

**Typical workflow**:
1. Make HDL changes in rtl/
2. Run tests: `make test-all`
3. Rebuild: `make all` in build/
4. Program: `make program`
5. Test via serial terminal

**For help**: Check docs/, review test cases, or examine module documentation.

Happy retro computing!
