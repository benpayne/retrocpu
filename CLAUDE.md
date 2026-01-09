# retrocpu Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-23

## Active Technologies

- (002-m65c02-port)

## Project Structure

```text
src/
tests/
```

## Commands

# Add commands for 

## Code Style

: Follow standard conventions

## Recent Changes

- 002-m65c02-port: Added

<!-- MANUAL ADDITIONS START -->

## Temporary Files Policy

**IMPORTANT**: All temporary files created during development, debugging, or investigation MUST be placed in the `temp/` directory:

- **Investigation notes**: `temp/UART_RX_INVESTIGATION.md`
- **Debug scripts**: `temp/test_serial_fix.py`
- **Progress tracking**: `temp/BOOT_FAILURE_NOTES.md`
- **Research documents**: `temp/ECP5_MEMORY_RESEARCH.md`
- **Status reports**: Any `.md` files documenting temporary state

**Do NOT create temporary `.md` or `.py` files in the root directory.**

The `temp/` directory is in `.gitignore` and will not pollute the codebase. Clean, permanent documentation should go in the appropriate `docs/` or `specs/` directories.

## Development Environment

**Full documentation:** See [`docs/development-guide.md`](docs/development-guide.md) for complete development environment reference.

### Critical Information

**Hardware:**
- **FPGA Board:** ColorLight i5 with Lattice ECP5-25F
- **Serial Port:** `/dev/ttyACM0` @ 9600 baud (NOT /dev/ttyUSB0)
- **Display:** HDMI (TMDS/DVI output), 640×400 @ 70Hz (VGA standard mode)

**Resetting the Board:**
```bash
cd /opt/wip/retrocpu/build
openFPGALoader -b colorlight-i5 soc_top.bit
```
This reprograms the FPGA and **resets the entire system** (clears RAM, resets CPU). Use this to:
- Recover from stuck programs
- Exit from BASIC (no exit command exists)
- Return to monitor prompt

**Program Loading (Official Tool):**
```bash
# Load and execute
/opt/wip/retrocpu/tools/load_program.py program.bin --execute

# Load only (execute with 'J' command in monitor)
/opt/wip/retrocpu/tools/load_program.py program.bin
```

**Monitor Commands:**
- `L` - Load binary via XMODEM
- `J` - Jump/execute code at $0300
- `E <addr>` - Examine memory
- `D <addr> <val>` - Deposit value (NO "P" poke command)
- `G` - Go to BASIC
- `H` - Help

**Assembly Build:**
```bash
ca65 -o program.o program.s
ld65 -t none -o program.bin program.o
```

**Memory Map Quick Reference:**
- `$0300` - **Safe program load address**
- `$C000-$C00F` - UART
- `$C100-$C10F` - **Graphics GPU registers**
- `$C10D` - Display mode (0=Character, 1=Graphics)
- `$FFF3` - Monitor CHROUT vector

**Graphics GPU Base:** `$C100-$C10F`
- Display mode register: `$C10D` (bit 0: 0=char, 1=graphics)
- Graphics mode: `$C106` (00=1BPP, 01=2BPP, 10=4BPP)
- VRAM data: `$C102` (auto-increment with burst mode)

**Graphics Modes & Scaling:**
- Display: 640×400 VGA (allows simple 2x/4x integer scaling)
- 1BPP: 320×200, 2 colors, each pixel 2×2 VGA pixels
- 2BPP: 160×200, 4 colors, each pixel 4×2 VGA pixels
- 4BPP: 160×100, 16 colors, each pixel 4×4 VGA pixels
- All scaling uses simple bit shifts (no multiplication/division)

**Build System:**
- Build time: ~18-22 minutes with optimizations (was ~30 min)
- **IMPORTANT:** Always run builds using the Task tool with a general-purpose agent in the background
  - Direct Bash commands have 15-minute timeout (too short for full builds)
  - Use agent to allow full build time without timeout
  - Example:
    ```
    Task tool: "Build the FPGA bitstream in /opt/wip/retrocpu/build by running 'make soc_top.bit'"
    ```
- Build optimizations enabled:
  - `--threads 16` (uses all CPU cores)
  - `--parallel-refine` (parallel placement optimization)
  - `--seed 1` (deterministic timing)
  - Simplified pixel scaling (no multipliers, meets timing constraints)
- "Removing unused module" warnings are **NORMAL** (parameterized modules)
- All modules (CPU, UART, RAM, GPU) ARE in the design

**Common Issues:**
- **Stuck in BASIC:** Reprogram FPGA (no exit command)
- **No monitor prompt:** Reprogram FPGA to reset
- **XMODEM fails:** Check serial port, ensure at monitor prompt (not BASIC)

<!-- MANUAL ADDITIONS END -->
