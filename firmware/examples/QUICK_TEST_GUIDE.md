# Quick Graphics GPU Test Guide

## ✅ What's Done

- ✅ FPGA bitstream built and flashed (212 KB with Graphics GPU!)
- ✅ All 3 firmware test programs compiled:
  - `gpu_test_1bpp.bin` - Checkerboard pattern
  - `gpu_test_4bpp.bin` - Rainbow color bars
  - `gpu_test_interactive.bin` - Interactive tester

## 🎯 How to Test (2 Options)

### Option 1: Quick Python Upload (Automated)

```bash
cd /opt/wip/retrocpu/firmware/examples

# Find your serial port
ls /dev/tty* | grep -E "(USB|ACM)"

# Upload 1 BPP checkerboard test
python3 upload_and_run.py /dev/ttyUSB0 gpu_test_1bpp.bin

# Or upload interactive test
python3 upload_and_run.py /dev/ttyUSB0 gpu_test_interactive.bin
```

### Option 2: Manual Upload via Terminal (Step-by-Step)

1. **Connect to serial monitor**:
   ```bash
   screen /dev/ttyUSB0 115200
   # or
   minicom -D /dev/ttyUSB0 -b 115200
   ```

2. **Press ENTER** - you should see the monitor prompt (`>`)

3. **Type 'L' and press ENTER** - starts XMODEM receive mode

4. **In another terminal, send the file**:
   ```bash
   sx gpu_test_1bpp.bin < /dev/ttyUSB0 > /dev/ttyUSB0
   ```

5. **Watch the display** - checkerboard should appear!

## 🎨 What You Should See

### Test 1: 1 BPP Checkerboard (`gpu_test_1bpp.bin`)

**Expected Display**:
```
████ ████ ████ ████ ████
 ████ ████ ████ ████ ████
████ ████ ████ ████ ████
 ████ ████ ████ ████ ████
```

- Full-screen alternating black & white pixels
- Pattern: $AA / $55 bytes (10101010 / 01010101)
- Tests: Basic VRAM, 1 BPP mode, display switching

### Test 2: 4 BPP Rainbow Bars (`gpu_test_4bpp.bin`)

**Expected Display**:
- 16 vertical color stripes across screen
- Colors (left to right):
  - Black, Dark Red, Red, Orange
  - Yellow, Yellow-Green, Green, Cyan
  - Light Blue, Blue, Purple, Magenta
  - Pink, Gray, Light Gray, White
- Tests: 16-color palette, 4 BPP mode, burst VRAM writes

### Test 3: Interactive (`gpu_test_interactive.bin`)

**Commands** (type in serial terminal):
- `1` - Switch to 1 BPP checkerboard
- `2` - Switch to 2 BPP gradient
- `4` - Switch to 4 BPP gradient
- `C` - Back to character (text) mode
- `G` - Back to graphics mode
- `X` - Clear VRAM (black screen)

**Example session**:
```
> (upload interactive test)
(press '4' - see gradient)
(press 'C' - see text console)
(press 'G' - back to gradient)
(press '1' - see checkerboard)
```

## 🐛 Troubleshooting

**Problem**: "No such file or directory: /dev/ttyUSB0"
- Find correct port: `ls /dev/tty* | grep -E "(USB|ACM)"`
- Try: `/dev/ttyACM0`, `/dev/ttyUSB1`, etc.

**Problem**: "Permission denied"
- Add user to dialout group: `sudo usermod -a -G dialout $USER`
- Log out and back in

**Problem**: Monitor doesn't respond or no NAK received
- Press reset button on FPGA board
- Try unplugging and reconnecting USB
- If you disabled character display mode, the monitor may need a reset
- Verify serial connection: `screen /dev/ttyACM0 9600` (press ENTER, you should see `>`)

**Problem**: Display shows garbage
- FPGA might not be programmed correctly
- Re-flash: `cd /opt/wip/retrocpu/build && make program`
- Check HDMI cable connection

**Problem**: XMODEM transfer fails
- Make sure you typed 'L' in monitor first
- Try slower baud rate (9600 instead of 115200)
- Check that binary file exists

**Problem**: No graphics appear
- Display might be in character mode
- Programs should auto-switch to graphics mode
- Try interactive test and press 'G' for graphics mode

## ⚡ Quick Success Test

**Fastest way to confirm Graphics GPU works**:

```bash
cd /opt/wip/retrocpu/firmware/examples

# Method 1: Python script (if serial port is /dev/ttyUSB0)
python3 upload_and_run.py /dev/ttyUSB0 gpu_test_1bpp.bin
```

**Expected**: Within 5 seconds, your display should switch from text mode to a black & white checkerboard pattern filling the entire screen.

**Success!** ✅ You now have a working Graphics GPU!

## 📊 Register Quick Reference

For writing your own programs:

| Reg | Address | Function |
|-----|---------|----------|
| GPU_MODE | $C106 | 00=1BPP, 01=2BPP, 10=4BPP |
| DISPLAY_MODE | $C10D | 0=text, 1=graphics |
| VRAM_ADDR_LO/HI | $C100-C101 | Set VRAM address |
| VRAM_DATA | $C102 | Write/read VRAM |
| VRAM_CTRL | $C103 | bit 0: Burst mode |
| CLUT_INDEX | $C107 | Palette index (0-15) |
| CLUT_DATA_R/G/B | $C108-C10A | RGB444 color |

## 🎓 Example: Quick Test in Monitor

```assembly
; Switch to graphics mode manually via monitor
> W C10D 01    ; DISPLAY_MODE = graphics
> W C106 00    ; GPU_MODE = 1 BPP
> W C103 01    ; Enable burst mode
> W C100 00    ; VRAM address = $0000
> W C101 00
> W C102 AA    ; Write $AA pattern
> W C102 55    ; Write $55 pattern
> W C102 AA    ; Write $AA pattern
; etc... (tedious, use firmware instead!)
```

## 🚀 Next Steps

1. **Verify checkerboard works** - Upload `gpu_test_1bpp.bin`
2. **Try color bars** - Upload `gpu_test_4bpp.bin`
3. **Test interactively** - Upload `gpu_test_interactive.bin`
4. **Write your own graphics** - Use firmware examples as templates

## 📸 Post Your Results!

When it works, take a photo of your display showing:
- Checkerboard pattern
- Rainbow color bars
- Your own graphics!

---

**Files Location**:
- Firmware binaries: `/opt/wip/retrocpu/firmware/examples/gpu_test_*.bin`
- Upload script: `/opt/wip/retrocpu/firmware/examples/upload_and_run.py`
- FPGA bitstream: `/opt/wip/retrocpu/build/soc_top.bit`

**For Help**: See `/opt/wip/retrocpu/GRAPHICS_GPU_TESTING_GUIDE.md`
