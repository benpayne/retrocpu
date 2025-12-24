# RetroCPU: 6502 FPGA Microcomputer

An educational 6502-based microcomputer system implemented on FPGA using open-source tools.

## Overview

RetroCPU is a complete retro computing system featuring:
- **M65C02 CPU** running at 25 MHz (6.25 MHz microcycle rate, ~5 MIPS)
- **64 KB memory** (32 KB RAM + 24 KB ROM + 8 KB I/O space)
- **Microsoft 6502 BASIC** in ROM
- **Monitor program** for memory examination and debugging
- **UART interface** for serial communication (115200 baud)
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
$C000-$C0FF : UART Registers
$C100-$C1FF : LCD Registers
$C200-$C2FF : PS/2 Keyboard Registers
$C300-$DFFF : Reserved I/O Space
$E000-$FFFF : Monitor ROM + Vectors (8 KB)
```

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

This project is for educational purposes. Component licenses:
- **M65C02 CPU core**: LGPL v3 (MAM65C02-Processor-Core)
- **EhBASIC**: Lee Davison, free to use
- **Project code**: To be determined (suggest MIT or Apache 2.0)

## Contributing

This is an educational project following strict TDD principles:
1. All contributions must include tests written FIRST
2. Code must follow the project constitution
3. Documentation is mandatory for all modules
4. Simplicity and clarity over optimization

See [specs/001-6502-fpga-microcomputer/tasks.md](specs/001-6502-fpga-microcomputer/tasks.md) for implementation task list.

## Status

**Current Version**: v0.2.0 - M65C02 Port Complete ✅
**System**: Fully operational with M65C02 CPU core
**Zero Page Bug**: Fixed (was broken with Arlet 6502)
**Performance**: 6x improvement (1 MHz → 6.25 MHz effective)
**Next Milestone**: Firmware enhancement (monitor commands, full BASIC)

See [specs/002-m65c02-port/](specs/002-m65c02-port/) for M65C02 integration details and task list.

## Contact

Educational project for learning FPGA design, HDL, and computer architecture.
