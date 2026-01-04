# RetroCPU: 6502 FPGA Microcomputer

An educational 6502-based microcomputer system implemented on FPGA using open-source tools, featuring a complete DVI/HDMI character display GPU.

## Overview

RetroCPU is a complete retro computing system featuring:
- **M65C02 CPU** running at 25 MHz (6.25 MHz microcycle rate, ~5 MIPS)
- **64 KB memory** (32 KB RAM + 24 KB ROM + 8 KB I/O space)
- **DVI/HDMI GPU** with 640×480@60Hz character display
  - 40-column and 80-column text modes
  - 8-color palette (3-bit RGB)
  - Blinking cursor with auto-scroll
- **Microsoft 6502 BASIC** in ROM
- **Monitor program** for memory examination and debugging
- **UART interface** for serial communication (9600 baud)
- **HD44780 LCD display** support (2x16 or 2x20 character LCD)
- **PS/2 keyboard** interface

**Target Hardware**: Lattice ECP5-25F FPGA (Colorlight i5 board)
**Toolchain**: 100% open-source (Yosys, nextpnr, cocotb, Icarus Verilog)

## Quick Start

See [specs/001-6502-fpga-microcomputer/quickstart.md](specs/001-6502-fpga-microcomputer/quickstart.md) for detailed setup and usage instructions.

### Prerequisites

```bash
# Install FPGA toolchain (Ubuntu/Debian)
sudo apt install yosys nextpnr-ecp5 ecppack openFPGALoader

# Install simulation tools
sudo apt install iverilog gtkwave

# Install Python testing framework
pip3 install cocotb cocotb-test pytest

# Install 6502 assembler
sudo apt install cc65

# Install serial terminal
sudo apt install minicom screen
```

### Build and Program

```bash
# 1. Build firmware
cd firmware/monitor && make
cd ../basic && make

# 2. Run tests (optional but recommended)
cd tests && make test-all

# 3. Build FPGA bitstream
cd build && make all

# 4. Program FPGA
make program

# 5. Connect serial terminal
screen /dev/ttyUSB0 9600
```

## Project Structure

```
retrocpu/
├── rtl/                    # Verilog HDL source files
│   ├── cpu/               # M65C02 CPU core
│   ├── memory/            # RAM, ROM, address decoder
│   ├── peripherals/       # UART, LCD, PS/2 modules
│   └── system/            # Top-level integration, clock/reset
├── tests/                 # cocotb test suite
│   ├── unit/             # Unit tests for individual modules
│   └── integration/      # System integration tests
├── firmware/              # 6502 software
│   ├── monitor/          # Monitor program (ROM at $E000)
│   └── basic/            # BASIC interpreter (ROM at $8000)
├── docs/                  # Documentation
│   ├── modules/          # Module-specific documentation
│   └── learning/         # Educational resources
├── build/                 # Build system and outputs
│   └── Makefile          # Synthesis and programming targets
└── specs/                 # Feature specifications and planning
    └── 001-6502-fpga-microcomputer/
        ├── spec.md       # Complete specification
        ├── plan.md       # Implementation plan
        ├── tasks.md      # Task breakdown
        └── quickstart.md # User guide
```

## Architecture

### Memory Map

```
$0000-$00FF : Zero Page RAM (256 bytes)
$0100-$01FF : Stack RAM (256 bytes)
$0200-$7FFF : General Purpose RAM (31.5 KB)
$8000-$BFFF : BASIC ROM (16 KB)
$C000-$C00F : UART Registers
$C010-$C016 : GPU Registers (DVI Character Display)
$C100-$C1FF : LCD Registers
$C200-$C2FF : PS/2 Keyboard Registers
$C300-$DFFF : Reserved I/O Space
$E000-$FFFF : Monitor ROM + Vectors (8 KB)
```

### GPU Registers (0xC010-0xC016)

| Address | Register | Description |
|---------|----------|-------------|
| 0xC010 | CHAR_DATA | Write character at cursor (auto-advance) |
| 0xC011 | CURSOR_ROW | Cursor row (0-29) |
| 0xC012 | CURSOR_COL | Cursor column (0-39 or 0-79) |
| 0xC013 | CONTROL | Clear, mode, cursor enable |
| 0xC014 | FG_COLOR | Foreground color (3-bit RGB) |
| 0xC015 | BG_COLOR | Background color (3-bit RGB) |
| 0xC016 | STATUS | GPU status (ready, vsync) |

See `docs/modules/register_interface.md` for complete GPU documentation.

### Pin Assignments (Colorlight i5)

| Function | Pin | Notes |
|----------|-----|-------|
| Clock (25 MHz) | P3 | System clock input |
| Reset button | T1 | FIRE 2, active-low with pull-up |
| UART TX | J17 | To STM32 USB bridge |
| PS/2 Clock | K5 | With pull-up |
| PS/2 Data | B3 | With pull-up |
| LED 1-4 | N18, N17, L20, M18 | Status/debug LEDs |

See `colorlight_i5.lpf` for complete pin definitions.

## Monitor Commands

The RetroCPU monitor provides a command-line interface for system control and program loading:

| Command | Syntax | Description |
|---------|--------|-------------|
| **E** | `E <addr>` | Examine memory at hex address (e.g., `E 0200`) |
| **D** | `D <addr> <val>` | Deposit hex value to memory (e.g., `D 0200 42`) |
| **G** | `G [addr]` | Go to address or BASIC (e.g., `G 0300` or just `G`) |
| **H** | `H` | Display help with all commands and examples |
| **L** | `L <addr>` | Load binary program via XMODEM to address (e.g., `L 0300`) |
| **I** | `I <in> <out>` | Configure I/O sources (0=UART, 1=PS2/Display, 2=Both) |
| **S** | `S` | Display I/O status and peripheral information |

### Quick Examples

```bash
# Examine memory
> E 0200
0200: 00

# Write to memory
> D 0200 4C
0200: 4C

# Upload binary program via XMODEM
> L 0300
Ready to receive XMODEM. Start transfer now...
[Send file via terminal emulator's XMODEM feature]
..................
Transfer complete
> G 0300

# Configure I/O for standalone operation (PS/2 keyboard + HDMI display)
> I 1 1
I/O Config: IN=PS2, OUT=Display

# Check system status
> S
I/O Status:
  Input:  PS/2
  Output: Display
Peripherals:
  UART:    9600 baud, TX ready, RX empty
  PS/2:    No data
  Display: Ready

# Return to UART mode
> I 0 0
I/O Config: IN=UART, OUT=UART
```

### Program Loading

The monitor supports multiple ways to load programs:

1. **XMODEM Binary Upload** (recommended for compiled programs):
   - Compile 6502 assembly to binary
   - Use `L <address>` command in monitor
   - Send file via terminal emulator's XMODEM feature
   - Execute with `G <address>`

2. **BASIC Program Pasting**:
   - Enter BASIC with `G` command
   - Enable XON/XOFF flow control in terminal
   - Paste BASIC source code
   - Run with `RUN` command

3. **Manual Entry**:
   - Use `D` command to deposit bytes one at a time
   - Use `E` command to verify

See [docs/user_guides/program_loading.md](docs/user_guides/program_loading.md) for detailed instructions.

### I/O Configuration Modes

The system supports flexible I/O routing:

| Mode | Input | Output | Use Case |
|------|-------|--------|----------|
| `I 0 0` | UART | UART | **Development** (default) - PC connection |
| `I 1 1` | PS/2 | Display | **Standalone** - No PC required |
| `I 2 2` | Both | Both | **Debug** - Maximum flexibility |
| `I 0 1` | UART | Display | **BASIC development** - Paste code, view on display |
| `I 1 0` | PS/2 | UART | **Session logging** - Keyboard input, log to PC |

See [docs/user_guides/io_configuration.md](docs/user_guides/io_configuration.md) for complete guide.

## Development Workflow

This project follows **Test-Driven Development (TDD)**:

1. Write cocotb test for module (REQUIRED before implementation)
2. Run test and verify it fails (red phase)
3. Implement Verilog module to pass the test
4. Run test and verify it passes (green phase)
5. Refactor if needed while keeping tests passing

### Running Tests

```bash
# Run all unit tests
cd tests/unit
make test-all

# Run specific test
pytest test_uart_tx.py -v

# Run with waveform generation
pytest test_uart_tx.py -v --waves
```

### Building Hardware

```bash
cd build

# Synthesis only
make synth

# Place-and-route
make pnr

# Generate bitstream
make bitstream

# Full build
make all

# View resource utilization
make util

# View timing report
make timing
```

## User Stories and Priorities

The system is developed in phases following prioritized user stories:

- **P1 (MVP)**: Monitor program with UART (examine/deposit memory, jump to code)
- **P2**: Microsoft BASIC interpreter from ROM
- **P3**: HD44780 LCD character display support
- **P4**: PS/2 keyboard input
- **P5**: Standalone operation (LCD + keyboard without PC)

See [specs/001-6502-fpga-microcomputer/spec.md](specs/001-6502-fpga-microcomputer/spec.md) for complete requirements.

## Constitution

RetroCPU follows five core principles:

1. **Test-Driven Design (NON-NEGOTIABLE)** - All modules must have cocotb tests written FIRST
2. **Simplicity Over Performance** - Clarity and educational value prioritized
3. **Module Reusability** - Self-contained, well-documented modules
4. **Educational Clarity** - Code and docs support teaching mission
5. **Open Source Tooling** - 100% open-source development stack

See [.specify/memory/constitution.md](.specify/memory/constitution.md) for complete governance document.

## Resources

### Hardware
- **Colorlight i5 Board**: https://github.com/wuxx/Colorlight-FPGA-Projects
- **ECP5 Documentation**: https://www.latticesemi.com/Products/FPGAandCPLD/ECP5

### 6502 Resources
- **6502.org**: http://www.6502.org/ (CPU reference)
- **M65C02 Core**: https://github.com/MorrisMA/MAM65C02-Processor-Core (current CPU)
- **EhBASIC**: https://github.com/Klaus2m5/6502_EhBASIC_V2.22

### FPGA Tools
- **Yosys**: https://yosyshq.net/yosys/
- **nextpnr**: https://github.com/YosysHQ/nextpnr
- **cocotb**: https://docs.cocotb.org/

### Learning
- **Programming the 6502** by Rodnay Zaks
- **Code the Classics** (Retro game programming)
- Project documentation in `docs/learning/`

## License

This project is licensed under the **BSD 3-Clause License** - see the [LICENSE](LICENSE) file.

### Third-Party Components

This project includes code from third-party sources under different licenses:

- **M65C02 CPU** (`rtl/cpu/m65c02/`): GNU LGPL v2.1+
  - Copyright 2012-2013 Michael A. Morris
  - https://github.com/MorrisMA/M65C02A

- **TMDS Encoder** (`rtl/peripherals/video/tmds_encoder.v`): ISC License
  - Copyright 2021 Hirosh Dabui
  - https://github.com/splinedrive/my_hdmi_device

See [NOTICE](NOTICE) file for complete attribution details.

## Contributing

This is an educational project following strict TDD principles:
1. All contributions must include tests written FIRST
2. Code must follow the project constitution
3. Documentation is mandatory for all modules
4. Simplicity and clarity over optimization

See [specs/001-6502-fpga-microcomputer/tasks.md](specs/001-6502-fpga-microcomputer/tasks.md) for implementation task list.

## Status

**Current Version**: v0.3.0 - DVI Character Display GPU Complete ✅

### Completed Features
- ✅ M65C02 CPU core (25 MHz, 6.25 MHz effective)
- ✅ 64 KB memory system with RAM/ROM
- ✅ DVI/HDMI GPU (640×480@60Hz, 40/80-column modes, 8 colors, cursor)
- ✅ UART serial interface (9600 baud)
- ✅ PS/2 keyboard interface with ASCII translation
- ✅ Monitor firmware with memory commands
- ✅ XMODEM binary program upload via UART
- ✅ Flexible I/O configuration (UART/PS2/Display routing)
- ✅ XON/XOFF flow control for BASIC program pasting
- ✅ Open-source toolchain (Yosys, nextpnr-ecp5)

### Recent Milestones
- **2026-01-01**: DVI Character Display GPU complete (all 6 user stories validated)
- **2025-12-31**: Auto-scroll and color configuration working
- **2025-12-28**: Basic character output and DVI signal generation
- **2025-12-27**: M65C02 port complete with monitor firmware

### Next Steps
- Integration with PS/2 keyboard for standalone operation
- BASIC interpreter integration with GPU
- Enhanced monitor commands

See [specs/003-hdmi-character-display/](specs/003-hdmi-character-display/) for GPU implementation details.

## Contact

Educational project for learning FPGA design, HDL, and computer architecture.
