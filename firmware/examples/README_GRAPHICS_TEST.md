# Graphics GPU Test Program

This directory contains a 6502 assembly program to test the graphics GPU in 4 BPP mode.

## Files

- `test_gpu_graphics.s` - 6502 assembly source code
- `test_gpu_graphics.bin` - Assembled binary (172 bytes)

## What the Program Does

The test program demonstrates the graphics GPU by:

1. **Setting up a 16-color palette** - VGA-style colors (Black, Blue, Green, Cyan, Red, Magenta, Brown, Light Gray, etc.)
2. **Configuring GPU for 4 BPP mode** - 160×100 resolution with 16 colors
3. **Drawing 16 vertical color bars** - Each bar is 10 pixels wide, showing all 16 palette colors
4. **Switching to graphics display mode** - Changes from character mode to graphics mode

## Building the Program

```bash
cd /opt/wip/retrocpu/firmware/examples

# Assemble
ca65 -o test_gpu_graphics.o test_gpu_graphics.s

# Link
ld65 -t none -o test_gpu_graphics.bin test_gpu_graphics.o

# Check size
ls -lh test_gpu_graphics.bin
```

## Uploading and Running

### Method 1: Upload and Execute (Recommended)

```bash
/opt/wip/retrocpu/tools/load_program.py test_gpu_graphics.bin --execute
```

This will:
- Upload the binary via XMODEM
- Execute it immediately at $0300
- Display 16 color bars on the screen

### Method 2: Upload Only, Execute Later

```bash
# Upload
/opt/wip/retrocpu/tools/load_program.py test_gpu_graphics.bin

# Later, in monitor:
# Connect: screen /dev/ttyACM0 9600
# Type: J<ENTER>  (Jump command executes code at $0300)
```

### Method 3: Verbose Mode for Debugging

```bash
/opt/wip/retrocpu/tools/load_program.py test_gpu_graphics.bin --execute --verbose
```

## Expected Output

After execution, you should see:
- **16 vertical color bars** on your display
- Each bar shows a different color from the palette
- Resolution: 160×100 pixels (scaled to 640×480 VGA output)
- Display mode automatically switches from character to graphics

## Graphics GPU Register Map

The program uses these GPU registers at base address **$C100**:

| Offset | Register | Description |
|--------|----------|-------------|
| $C100 | VRAM_ADDR_LO | VRAM address low byte |
| $C101 | VRAM_ADDR_HI | VRAM address high byte (bits 14:8) |
| $C102 | VRAM_DATA | VRAM read/write (auto-increment in burst mode) |
| $C103 | VRAM_CTRL | Bit 0: Burst mode enable |
| $C104 | FB_BASE_LO | Framebuffer base address low |
| $C105 | FB_BASE_HI | Framebuffer base address high |
| $C106 | GPU_MODE | Graphics mode (00=1BPP, 01=2BPP, 10=4BPP) |
| $C107 | CLUT_INDEX | Palette index (0-15) |
| $C108 | CLUT_DATA_R | Palette red component (4-bit) |
| $C109 | CLUT_DATA_G | Palette green component (4-bit) |
| $C10A | CLUT_DATA_B | Palette blue component (4-bit) |
| $C10D | DISPLAY_MODE | Bit 0: 0=Character, 1=Graphics |

## Graphics Modes

The GPU supports three graphics modes:

| Mode | Resolution | BPP | Colors | VRAM Size |
|------|-----------|-----|--------|-----------|
| 00 | 320×200 | 1 | 2 | 8,000 bytes |
| 01 | 160×200 | 2 | 4 | 8,000 bytes |
| 10 | 160×100 | 4 | 16 | 8,000 bytes |

## Troubleshooting

### No Color Bars Visible

1. **Reset the FPGA** to get back to monitor:
   ```bash
   cd /opt/wip/retrocpu/build
   openFPGALoader -b colorlight-i5 soc_top.bit
   ```

2. **Upload failed** - Check serial port:
   ```bash
   ls -l /dev/ttyACM*
   # Adjust port in load_program.py if needed: -p /dev/ttyUSB0
   ```

3. **Monitor not responding** - Program may still be running:
   - Reprogram FPGA to reset
   - Make sure you're at the monitor prompt (not in BASIC)

### Program Loaded but Not Running

The program enters an infinite loop at the end. To return to monitor:
- Reprogram the FPGA (resets the CPU)

## Example Session

```bash
$ cd /opt/wip/retrocpu/firmware/examples

$ /opt/wip/retrocpu/tools/load_program.py test_gpu_graphics.bin --execute
Loaded test_gpu_graphics.bin (172 bytes)
Transferring 172 bytes via XMODEM...
[====================] 100%
Transfer complete!
Executing program at $0300...

# At this point, you should see 16 color bars on your display!
```

## Notes

- The program is designed to load at **$0300** (safe RAM area)
- Total program size: **172 bytes** (includes code and palette data)
- After execution, the program loops infinitely
- To run another program, reset the FPGA first
