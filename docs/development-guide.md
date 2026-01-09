# RetroCPU Development Guide

Complete reference for developing with the RetroCPU FPGA system.

## Hardware Configuration

### FPGA Board
- **Board:** ColorLight i5 with Lattice ECP5-25F FPGA
- **Programmer:** DAPLink CMSIS-DAP (built-in JTAG)
- **Display:** TMDS/DVI output (HDMI connector), 640×480 @ 60Hz

### Serial Connection
- **Port:** `/dev/ttyACM0` (NOT `/dev/ttyUSB0`)
- **Baud rate:** 9600
- **Connection:** `screen /dev/ttyACM0 9600`

## FPGA Build System

### Build Location
- **Directory:** `/opt/wip/retrocpu/build/`
- **Command:** `make soc_top.bit`

### Build Process
1. **Yosys synthesis** (~5-6 minutes) → `soc_top.json` (6.1MB)
2. **nextpnr-ecp5 P&R** → `soc_top.config`
3. **ecppack bitstream** → `soc_top.bit` (~258KB)
4. **Total time:** 10-12 minutes

### Build Artifacts
```
/opt/wip/retrocpu/build/
├── soc_top.bit              # Final bitstream
├── synth/yosys.log          # Synthesis log
└── pnr/nextpnr.log          # Place-and-route log
```

### Important Build Warnings (NORMAL)

**"Removing unused module" warnings are EXPECTED:**
- Yosys creates parameterized versions of modules (e.g., `$paramod$850c4cd8...`)
- Generic template modules are removed after parameterization
- **All critical modules ARE in the design** (CPU, UART, RAM, peripherals)
- This is optimization, not an error

Example:
```
Removing unused module `\M65C02_Core'.
Used module: $paramod$850c4cd8635f79c833acaa893320239ec55f6798\M65C02_Core
```
This means the CPU is present in parameterized form.

## FPGA Programming (Flashing)

### Programming Command
```bash
cd /opt/wip/retrocpu/build
openFPGALoader -b colorlight-i5 soc_top.bit
```

**Must run from build directory** or specify full path to `.bit` file.

### Programming Effects
- Takes ~5-10 seconds
- **RESETS THE FPGA** - this is how you "reboot" the system
- Clears all RAM
- Resets CPU to monitor prompt
- Use this to recover from stuck programs or BASIC

### Recovery Workflow
When stuck or in BASIC:
1. Reprogram FPGA: `openFPGALoader -b colorlight-i5 soc_top.bit`
2. Wait 2 seconds after programming
3. Connect to serial: `screen /dev/ttyACM0 9600`
4. Fresh monitor prompt appears

## Monitor ROM

### Monitor Prompt
```
>
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `E <addr>` | Examine memory | `E 0300` |
| `D <addr> <val>` | Deposit value | `D 0300 A9` |
| `G` | Go to BASIC ROM | `G` |
| `H` | Help (show commands) | `H` |
| `J` | Jump/execute at $0300 | `J` |
| `L` | Load binary (XMODEM) | `L` |
| `M <mode>` | Set display mode | `M 1` (80-col) |
| `I <in> <out>` | Configure I/O | `I 0 0` |
| `S` | Status display | `S` |

### I/O Modes
- `0` = UART
- `1` = PS2/Display
- `2` = Both

### Important Notes
- **No "Poke" (P) command** - use `D` (Deposit) instead
- Programs return to monitor with `RTS`
- **No exit from BASIC** - must reprogram FPGA to return to monitor
- Monitor CHROUT vector: `$FFF3` (for printing from programs)

## Program Loading

### Official Tool
```bash
/opt/wip/retrocpu/tools/load_program.py
```

### Usage Examples

```bash
# Load only
/opt/wip/retrocpu/tools/load_program.py program.bin

# Load and execute at $0300
/opt/wip/retrocpu/tools/load_program.py program.bin --execute

# Verbose mode (shows packet details)
/opt/wip/retrocpu/tools/load_program.py program.bin --execute --verbose

# Different serial port
/opt/wip/retrocpu/tools/load_program.py program.bin -p /dev/ttyUSB0 --execute
```

### Loading Protocol
- **Protocol:** XMODEM with 128-byte packets
- **Load Address:** `$0300` (safe RAM location)
- **Execution:** Use `--execute` flag or manual `J` command

### Manual Loading (via Monitor)
1. Connect: `screen /dev/ttyACM0 9600`
2. Type: `L<ENTER>` (monitor waits for XMODEM)
3. Upload: `load_program.py program.bin`
4. Execute: Type `J<ENTER>` in monitor

## Assembly Development

### Toolchain
- **Assembler:** ca65 (cc65 suite)
- **Linker:** ld65
- **CPU:** 6502 compatible (M65C02 core)

### Build Commands

```bash
# Assemble source file
ca65 -o program.o program.s

# Link to raw binary (no header)
ld65 -t none -o program.bin program.o

# Check binary size
ls -lh program.bin
```

### Assembly File Template

```assembly
; Program template for RetroCPU
.setcpu "6502"

; Monitor vectors
CHROUT = $FFF3  ; Character output

; Load at $0300 (safe RAM area)
.org $0300

START:
    ; Your code here

    ; Return to monitor
    RTS
```

### Example: Hello World

```assembly
.setcpu "6502"

CHROUT = $FFF3

.org $0300

START:
    LDX #0
LOOP:
    LDA MESSAGE,X
    BEQ DONE
    JSR CHROUT
    INX
    BNE LOOP
DONE:
    RTS

MESSAGE:
    .byte "HELLO WORLD", $0D, $0A, 0
```

Build and run:
```bash
ca65 -o hello.o hello.s
ld65 -t none -o hello.bin hello.o
/opt/wip/retrocpu/tools/load_program.py hello.bin --execute
```

## Memory Map

| Address Range | Device | Size | Description |
|--------------|--------|------|-------------|
| `$0000-$7FFF` | RAM | 32 KB | General purpose memory |
| **`$0300`** | **User Programs** | - | **Safe load address** |
| `$8000-$BFFF` | BASIC ROM | 16 KB | OSI BASIC interpreter |
| `$C000-$C00F` | UART | 16 bytes | Serial I/O |
| `$C010-$C01F` | GPU Character | 16 bytes | Character display mode |
| `$C100-$C10F` | GPU Graphics | 16 bytes | Graphics display mode |
| `$C110-$C1FF` | LCD | 240 bytes | HD44780 LCD controller |
| `$C200-$C2FF` | PS/2 | 256 bytes | Keyboard interface |
| `$C300-$DFFF` | Reserved I/O | - | Future expansion |
| `$E000-$FFFF` | Monitor ROM | 8 KB | Firmware monitor |

## Graphics GPU Programming

### Graphics GPU Registers

**Base Address:** `$C100-$C10F`

| Offset | Register | Description |
|--------|----------|-------------|
| `$C100` | VRAM_ADDR_LO | VRAM address low byte |
| `$C101` | VRAM_ADDR_HI | VRAM address high byte (bits 14:8) |
| `$C102` | VRAM_DATA | VRAM read/write (auto-increment in burst mode) |
| `$C103` | VRAM_CTRL | Bit 0: Burst mode enable |
| `$C104` | FB_BASE_LO | Framebuffer base address low byte |
| `$C105` | FB_BASE_HI | Framebuffer base address high byte |
| `$C106` | GPU_MODE | Graphics mode (00=1BPP, 01=2BPP, 10=4BPP) |
| `$C107` | CLUT_INDEX | Palette index (0-15) |
| `$C108` | CLUT_DATA_R | Palette red component (4-bit, 0-15) |
| `$C109` | CLUT_DATA_G | Palette green component (4-bit, 0-15) |
| `$C10A` | CLUT_DATA_B | Palette blue component (4-bit, 0-15) |
| `$C10B` | GPU_STATUS | Bit 0: VBlank flag (read-only) |
| `$C10C` | GPU_IRQ_CTRL | Bit 0: VBlank interrupt enable |
| `$C10D` | DISPLAY_MODE | **Bit 0: 0=Character, 1=Graphics** |

### Graphics Modes

| Mode | Value | Resolution | BPP | Colors | VRAM Size | Pixels/Byte |
|------|-------|-----------|-----|--------|-----------|-------------|
| 1 BPP | `$00` | 320×200 | 1 | 2 | 8,000 bytes | 8 |
| 2 BPP | `$01` | 160×200 | 2 | 4 | 8,000 bytes | 4 |
| 4 BPP | `$02` | 160×100 | 4 | 16 | 8,000 bytes | 2 |

### Graphics Programming Example

```assembly
; Set up 4 BPP graphics mode
GPU_MODE = $C106
GPU_DISPLAY_MODE = $C10D
CLUT_INDEX = $C107
CLUT_DATA_R = $C108
CLUT_DATA_G = $C109
CLUT_DATA_B = $C10A

; Configure palette entry 1 (white)
LDA #$01
STA CLUT_INDEX
LDA #$0F          ; Red = 15
STA CLUT_DATA_R
LDA #$0F          ; Green = 15
STA CLUT_DATA_G
LDA #$0F          ; Blue = 15
STA CLUT_DATA_B

; Set 4 BPP mode
LDA #$02
STA GPU_MODE

; Switch to graphics display
LDA #$01
STA GPU_DISPLAY_MODE
```

### VRAM Access

**Burst Mode (Recommended for bulk writes):**
```assembly
VRAM_ADDR_LO = $C100
VRAM_ADDR_HI = $C101
VRAM_DATA = $C102
VRAM_CTRL = $C103

; Enable burst mode
LDA #$01
STA VRAM_CTRL

; Set VRAM address to $0000
LDA #$00
STA VRAM_ADDR_LO
STA VRAM_ADDR_HI

; Write data (address auto-increments)
LDA #$FF
STA VRAM_DATA  ; Write to $0000
STA VRAM_DATA  ; Write to $0001 (auto-incremented)
STA VRAM_DATA  ; Write to $0002 (auto-incremented)
```

## Clock Domains and Timing

### System Clocks
- **CPU clock:** 25 MHz (specification)
- **Pixel clock:** 25 MHz target, **19.13 MHz achieved** (timing warning)
- **TMDS clock:** 125 MHz (5× pixel clock for DVI serialization)

### Known Timing Issue
The pixel clock currently achieves only 19.13 MHz instead of the target 25 MHz. This may cause:
- Minor display artifacts or jitter
- Slight reduction in refresh rate
- **System remains functional** - not critical

This can be optimized in future revisions if needed.

## Common Issues & Solutions

### "Monitor not responding" / No prompt
**Cause:** System stuck in BASIC or program loop
**Solution:** Reprogram FPGA to reset
```bash
cd /opt/wip/retrocpu/build
openFPGALoader -b colorlight-i5 soc_top.bit
```

### "Removing unused module" warnings during build
**Status:** NORMAL and EXPECTED
**Reason:** Yosys creates parameterized versions of modules
**Action:** Ignore these warnings - all modules are in the design

### XMODEM upload fails
**Checks:**
1. Correct serial port? (`/dev/ttyACM0`)
2. At monitor prompt (not BASIC)?
3. Serial port permissions? (`ls -l /dev/ttyACM0`)

**Solutions:**
- Reprogram FPGA if stuck in BASIC
- Check port: `ls -l /dev/tty*`
- Add user to dialout group: `sudo usermod -a -G dialout $USER`

### Graphics not displaying
**Checklist:**
1. Display mode switched? (`$C10D = $01`)
2. VRAM data written?
3. Palette configured?
4. Correct graphics mode set? (`$C106`)

**Debug approach:**
- Use Python scripts to verify register writes via UART
- Check monitor output for errors
- Verify bitstream includes graphics GPU modules

### Build timeout (>15 minutes)
**Cause:** Yosys synthesis can be slow
**Solution:** Increase timeout or use faster machine
```bash
timeout 1200 make soc_top.bit  # 20-minute timeout
```

### Program stuck in infinite loop
**Cause:** Program has no RTS or enters infinite loop
**Solution:** Reprogram FPGA to reset CPU

## File Structure

```
/opt/wip/retrocpu/
├── build/                    # Build directory
│   ├── Makefile             # Build system
│   ├── soc_top.bit          # FPGA bitstream
│   ├── synth/               # Synthesis artifacts
│   └── pnr/                 # Place-and-route artifacts
│
├── rtl/                     # Verilog RTL source
│   ├── cpu/                 # M65C02 CPU core
│   ├── memory/              # RAM, ROM, decoder
│   ├── peripherals/         # UART, GPU, LCD, PS/2
│   └── system/              # Top-level, PLL, reset
│
├── firmware/                # Software
│   ├── examples/            # Example programs
│   └── monitor/             # Monitor firmware source
│
├── tools/                   # Development tools
│   └── load_program.py      # Official program loader
│
├── docs/                    # Documentation
│   └── development-guide.md # This file
│
├── tests/                   # Test suites
│   ├── unit/               # Unit tests (cocotb)
│   └── integration/        # Integration tests
│
└── CLAUDE.md               # Project instructions
```

## Development Workflow

### Typical Development Session

1. **Write/edit assembly program**
   ```bash
   vim program.s
   ```

2. **Assemble and link**
   ```bash
   ca65 -o program.o program.s
   ld65 -t none -o program.bin program.o
   ```

3. **Upload and execute**
   ```bash
   /opt/wip/retrocpu/tools/load_program.py program.bin --execute
   ```

4. **If stuck or need to reset**
   ```bash
   cd /opt/wip/retrocpu/build
   openFPGALoader -b colorlight-i5 soc_top.bit
   ```

### RTL Modification Workflow

1. **Edit Verilog files**
   ```bash
   vim rtl/peripherals/gpu/gpu_core.v
   ```

2. **Run unit tests (optional)**
   ```bash
   cd tests/unit
   pytest test_gpu_core.py
   ```

3. **Rebuild bitstream**
   ```bash
   cd /opt/wip/retrocpu/build
   timeout 1200 make soc_top.bit
   ```

4. **Flash to FPGA**
   ```bash
   openFPGALoader -b colorlight-i5 soc_top.bit
   ```

5. **Test on hardware**

## Known Working Programs

### Hello World
- **File:** `firmware/examples/hello_world.bin`
- **Size:** 36 bytes
- **Function:** Prints "HELLO WORLD" via UART
- **Status:** ✅ Working

### Graphics Test
- **File:** `firmware/examples/test_gpu_graphics.bin`
- **Size:** 172 bytes
- **Function:** Draws 16 color bars in 4 BPP mode
- **Status:** ⚠️ Uploads successfully, graphics not displaying (under investigation)

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│ RetroCPU Quick Reference                                    │
├─────────────────────────────────────────────────────────────┤
│ Serial:      /dev/ttyACM0 @ 9600 baud                      │
│ Reset:       openFPGALoader -b colorlight-i5 soc_top.bit   │
│ Load:        /opt/wip/retrocpu/tools/load_program.py       │
│ Execute:     J (in monitor)                                 │
│ Load addr:   $0300                                          │
├─────────────────────────────────────────────────────────────┤
│ Monitor Commands:                                           │
│   H - Help    L - Load     J - Jump/execute                │
│   E - Examine D - Deposit  G - Go to BASIC                 │
├─────────────────────────────────────────────────────────────┤
│ Graphics GPU: $C100-$C10F                                   │
│   $C10D: Display mode (0=Char, 1=Graphics)                 │
│   $C106: GPU mode (00=1BPP, 01=2BPP, 10=4BPP)              │
└─────────────────────────────────────────────────────────────┘
```

## Support and Resources

- **Project Repository:** (Add GitHub URL when published)
- **Issue Tracker:** (Add GitHub Issues URL)
- **Documentation:** `/opt/wip/retrocpu/docs/`
- **Examples:** `/opt/wip/retrocpu/firmware/examples/`

---

**Last Updated:** 2026-01-05
**Version:** 1.0
