# Tool Dependency Status

**Date**: 2025-12-16
**System**: Linux 5.15.0-161-generic

## FPGA Synthesis and Place-and-Route

### ✅ Yosys (Synthesis)
- **Status**: INSTALLED
- **Version**: 0.41+69 (git sha1 07ac4c2fa)
- **Required for**: RTL synthesis to netlist

### ✅ nextpnr-ecp5 (Place-and-Route)
- **Status**: INSTALLED
- **Version**: nextpnr-0.7-37-g423f1b71
- **Required for**: Mapping netlist to ECP5 FPGA

### ✅ openFPGALoader (Programming)
- **Status**: INSTALLED
- **Required for**: Programming Colorlight i5 board via USB

## HDL Simulation

### ✅ Icarus Verilog (iverilog)
- **Status**: INSTALLED
- **Version**: 11.0 (stable)
- **Required for**: Verilog simulation

## Testing Framework

### ❌ cocotb (Python HDL testing)
- **Status**: NOT INSTALLED
- **Required for**: Test-driven development (MANDATORY per constitution)
- **Installation**: `pip3 install --user cocotb cocotb-test pytest`
- **Priority**: HIGH - Required before Phase 2 (foundational tests)

## 6502 Software Development

### ❌ cc65 (6502 Assembler/Compiler)
- **Status**: NOT INSTALLED
- **Required for**: Building monitor and firmware
- **Installation**: `sudo apt install cc65`
- **Priority**: HIGH - Required before firmware builds

## Optional Tools

### GTKWave (Waveform Viewer)
- **Status**: Not checked
- **Required for**: Viewing simulation waveforms (debugging)
- **Installation**: `sudo apt install gtkwave`
- **Priority**: MEDIUM

### minicom/screen (Serial Terminal)
- **Status**: Not checked
- **Required for**: UART communication with FPGA
- **Installation**: `sudo apt install minicom screen`
- **Priority**: MEDIUM - Required for User Story 1 testing

## Installation Commands

### Required Tools (before proceeding)
```bash
# Install cocotb testing framework
pip3 install --user cocotb cocotb-test pytest

# Install 6502 assembler
sudo apt install cc65
```

### Recommended Tools
```bash
# Install waveform viewer and serial terminal
sudo apt install gtkwave minicom screen

# Verify installations
python3 -c "import cocotb; print(f'cocotb {cocotb.__version__}')"
ca65 --version
```

## Summary

**Ready to proceed**: Synthesis toolchain (Yosys, nextpnr, openFPGALoader) is complete
**Required before Phase 2**: Install cocotb and cc65
**Recommended**: Install GTKWave and serial terminal tools

The project can proceed with Phase 1 (setup) tasks, but Phase 2 (foundational tests) will require cocotb installation first.
