# Quickstart Guide: DVI Character Display GPU

**Feature**: 003-hdmi-character-display
**Date**: 2025-12-27
**Audience**: Developers building and testing the character display GPU

## 1. Prerequisites

### 1.1 Hardware Requirements

- **Colorlight i5 FPGA Board** with HDMI-capable carrier board
- **HDMI Monitor** or display supporting DVI input (640x480 @ 60Hz)
- **HDMI Cable** (standard HDMI cable, Type A)
- **USB Cable** for programming (depends on carrier board - typically USB-C or Micro-USB)
- **Power Supply** for Colorlight i5 (typically 5V via USB or barrel jack)

### 1.2 Software Requirements

Install the open-source FPGA toolchain:

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    yosys \
    nextpnr-ecp5 \
    prjtrellis \
    prjtrellis-db \
    openFPGALoader \
    git \
    make

# Verify installations
yosys -V          # Should show version 0.9 or later
nextpnr-ecp5 -V   # Should show version
openFPGALoader -V # Should show version
```

### 1.3 Python Tools for Testing

```bash
# For cocotb testing
sudo apt-get install -y python3 python3-pip iverilog
pip3 install cocotb pytest

# Verify
python3 -c "import cocotb; print(cocotb.__version__)"
iverilog -v
```

### 1.4 Repository Setup

```bash
# Clone the repo (if not already cloned)
cd /opt/wip/retrocpu

# Verify branch
git branch  # Should show 003-hdmi-character-display

# Create build directory if needed
mkdir -p build
```

---

## 2. Phase 0: Hardware Validation (IMPORTANT - DO THIS FIRST!)

As recommended in the implementation plan, **start by validating the hardware** with the reference DVI implementation before building the character display GPU.

### 2.1 Clone Reference Implementation

```bash
# Clone reference code to temporary location
cd /tmp
git clone https://github.com/splinedrive/my_hdmi_device.git
cd my_hdmi_device
```

### 2.2 Build Reference Implementation

```bash
# Synthesize with yosys
yosys -p "synth_ecp5 -top hdmi_device -json hdmi_device.json" hdmi_device.v tmds_encoder.v

# Place and route with nextpnr
nextpnr-ecp5 \
    --25k \
    --package CABGA381 \
    --lpf colorlighti5.lpf \
    --json hdmi_device.json \
    --textcfg hdmi_device.config

# Pack bitstream
ecppack hdmi_device.config hdmi_device.bit
```

**Expected Output**:
- Build should complete without errors
- Resource usage should be well under ECP5-25F limits
- Timing should meet constraints

### 2.3 Program and Test Hardware

```bash
# Connect Colorlight i5 via USB
# Program the FPGA
openFPGALoader -b colorlight-i5 hdmi_device.bit

# Or for some carrier boards:
openFPGALoader -c ft232 hdmi_device.bit
```

**Expected Behavior**:
1. Connect HDMI monitor to Colorlight i5 HDMI port
2. Monitor should detect video signal and display image
3. You should see a test pattern or color bars (depending on reference design)
4. Image should be stable with no flicker, tearing, or artifacts

**Troubleshooting**:
- **No signal**: Check HDMI cable, monitor input selection, power to board
- **Unstable image**: Verify PLL clock frequency, check pin assignments in LPF file
- **Programming fails**: Check USB connection, try different openFPGALoader cable type

### 2.4 Document Working Configuration

Once reference code works, **document the following** for use in GPU implementation:

```bash
# Extract pin assignments from colorlighti5.lpf
cat colorlighti5.lpf | grep -i "hdmi\|tmds"

# Note PLL configuration
cat hdmi_device.v | grep -i "EHXPLLL" -A 20

# Save notes to project
cd /opt/wip/retrocpu
cat > docs/colorlight_i5_hdmi_pinout.txt <<EOF
# Working HDMI pinout from reference implementation
# Date: $(date)

TMDS Clock+: [PIN from LPF]
TMDS Clock-: [PIN from LPF]
TMDS Data0+: [PIN from LPF]
TMDS Data0-: [PIN from LPF]
TMDS Data1+: [PIN from LPF]
TMDS Data1-: [PIN from LPF]
TMDS Data2+: [PIN from LPF]
TMDS Data2-: [PIN from LPF]

PLL Configuration:
Input Clock: [FREQUENCY]
Pixel Clock: [FREQUENCY]
TMDS Clock: [FREQUENCY]
EOF
```

**✅ Checkpoint**: Do not proceed until reference DVI code displays successfully on monitor.

---

## 3. Building the Character Display GPU

### 3.1 Directory Structure

Verify your source tree:

```bash
cd /opt/wip/retrocpu

# Expected structure (created during implementation)
tree rtl/peripherals/video/
# rtl/peripherals/video/
# ├── dvi_transmitter.v
# ├── video_timing.v
# ├── character_buffer.v
# ├── font_rom.v
# ├── character_renderer.v
# ├── cursor_controller.v
# ├── color_palette.v
# ├── gpu_registers.v
# └── gpu_top.v
```

### 3.2 Synthesis

```bash
cd build

# Synthesize GPU modules
yosys -p "
    read_verilog ../rtl/peripherals/video/*.v
    read_verilog ../rtl/system/soc_top.v
    synth_ecp5 -top soc_top -json soc_top.json
" 2>&1 | tee synthesis.log

# Check for errors
grep -i "error" synthesis.log
# Should return no errors
```

**Expected Resource Usage** (approximate):
```
Logic Cells: ~2000 / 24336 (8%)
Flip-Flops: ~1500 / 24336 (6%)
Block RAM: 3 / 56 (5%)
PLLs: 1 / 2 (50%)
```

### 3.3 Place and Route

```bash
# Place and route
nextpnr-ecp5 \
    --25k \
    --package CABGA381 \
    --lpf ../colorlight_i5.lpf \
    --json soc_top.json \
    --textcfg soc_top.config \
    --timing-allow-fail \
    2>&1 | tee pnr.log

# Check timing
grep "Max frequency" pnr.log
# Should show pixel clock domain > 25 MHz
```

### 3.4 Generate Bitstream

```bash
# Pack bitstream
ecppack soc_top.config soc_top.bit

# Verify bitstream created
ls -lh soc_top.bit
# Should be ~100-200 KB
```

---

## 4. Running Tests

### 4.1 Unit Tests with Cocotb

**Test Individual Modules**:

```bash
cd tests/unit

# Test video timing module
make test_video_timing.py
# Should pass all timing parameter tests

# Test character buffer
make test_character_buffer.py
# Should pass dual-port RAM tests, clear tests

# Test font ROM
make test_font_rom.py
# Should pass font lookup tests

# Test character renderer
make test_character_renderer.py
# Should pass pixel generation tests

# Test cursor controller
make test_cursor_controller.py
# Should pass position and flash tests

# Test GPU registers
make test_gpu_registers.py
# Should pass register read/write, CDC tests

# Run all unit tests
make all
```

**Expected Output**:
```
test_video_timing.py .................. PASSED
test_character_buffer.py .............. PASSED
test_font_rom.py ...................... PASSED
test_character_renderer.py ............ PASSED
test_cursor_controller.py ............. PASSED
test_gpu_registers.py ................. PASSED

========== 6 modules passed ==========
```

### 4.2 Integration Tests

```bash
cd tests/integration

# Test end-to-end character output
make test_gpu_character_output.py
# Should verify character write -> pixel output

# Test color modes
make test_gpu_color_modes.py
# Should verify FG/BG color changes

# Test mode switching
make test_gpu_mode_switching.py
# Should verify 40/80 column switching

# Test scrolling
make test_gpu_scrolling.py
# Should verify auto-scroll behavior

# Run all integration tests
make all
```

### 4.3 Firmware Tests

**Build Test Firmware**:

```bash
cd firmware/gpu

# Assemble test program
ca65 gpu_test.s -o gpu_test.o
ld65 -C gpu_test.cfg gpu_test.o -o gpu_test.bin

# Convert to hex for ROM
xxd -p gpu_test.bin > gpu_test.hex
```

**Test Program Examples** (gpu_test.s):

```assembly
; gpu_test.s - Basic GPU test firmware

.segment "CODE"

start:
    ; Clear screen
    LDA #$01
    STA $C013        ; CONTROL register

    ; Write "HELLO WORLD"
    LDX #$00
write_loop:
    LDA message,X
    BEQ done
    STA $C010        ; CHAR_DATA register
    INX
    JMP write_loop

done:
    JMP done         ; Halt

message:
    .byte "HELLO WORLD", $00
```

---

## 5. Programming and Testing Hardware

### 5.1 Program FPGA

```bash
cd build

# Program bitstream
openFPGALoader -b colorlight-i5 soc_top.bit

# For persistent programming (flash):
openFPGALoader -b colorlight-i5 -f soc_top.bit
```

### 5.2 Visual Verification Checklist

Connect HDMI monitor and verify:

1. **Monitor Detection**:
   - [ ] Monitor detects signal within 2 seconds
   - [ ] Monitor displays 640x480 resolution
   - [ ] No "No Signal" or "Out of Range" errors

2. **Display Quality**:
   - [ ] Image is stable (no flicker, tearing, artifacts)
   - [ ] Colors are correct (white text on black background by default)
   - [ ] Characters are sharp and readable
   - [ ] Cursor flashes at approximately 1Hz

3. **Character Output** (if firmware loaded):
   - [ ] Test message appears on screen
   - [ ] Characters are correctly positioned
   - [ ] Line wrapping works correctly
   - [ ] Screen clear works

4. **40-Column Mode**:
   - [ ] 40 characters per line
   - [ ] Characters are properly sized (16 pixels wide)
   - [ ] All 25-30 rows visible

5. **80-Column Mode** (if firmware switches mode):
   - [ ] 80 characters per line
   - [ ] Characters are properly sized (8 pixels wide)
   - [ ] Text is readable (not too small)

### 5.3 Interactive Testing

**Using Serial Console** (if UART available):

```bash
# Connect to serial console
screen /dev/ttyUSB0 115200

# Test GPU commands interactively:
# (Type assembly instructions or use built-in REPL if available)

# Example commands:
# Clear screen: STA $C013 with A=#$01
# Write char: STA $C010 with A=#$48 ('H')
# Change color: STA $C014 with A=#$04 (red)
```

---

## 6. Troubleshooting Guide

### 6.1 Synthesis Errors

**Error**: "Module not found: video_timing"
```bash
# Solution: Check file paths in synthesis command
ls rtl/peripherals/video/*.v
# Verify all modules exist
```

**Error**: "Syntax error in module gpu_top"
```bash
# Solution: Check Verilog syntax
iverilog -t null -Wall rtl/peripherals/video/gpu_top.v
# Fix reported syntax errors
```

### 6.2 Timing Errors

**Error**: "Pixel clock domain fails timing"
```bash
# Solution: Review critical path in timing report
grep "Critical path" pnr.log

# Add timing constraints to LPF:
echo "FREQUENCY PORT \"clk_pixel\" 25.175 MHZ;" >> colorlight_i5.lpf

# Retry place and route
```

**Error**: "Setup time violation"
```bash
# Solution: Add register stages to pipeline
# Review character_renderer.v pipeline depth
# Ensure adequate pipelining (3 stages recommended)
```

### 6.3 Display Problems

**Problem**: No signal detected

**Possible Causes**:
1. PLL not generating correct pixel clock
   - **Solution**: Verify PLL configuration matches reference code
   - **Check**: 25.175 MHz output on pixel clock
2. TMDS serializers not configured correctly
   - **Solution**: Review ODDRX2F primitive usage from reference
3. Pin assignments incorrect
   - **Solution**: Compare LPF file with working reference pinout

**Problem**: Garbled or unstable image

**Possible Causes**:
1. TMDS encoding errors
   - **Solution**: Verify tmds_encoder.v logic against reference
   - **Test**: Unit test TMDS encoder with known patterns
2. Pixel clock / TMDS clock phase mismatch
   - **Solution**: Check PLL phase relationships
3. Character renderer timing issues
   - **Solution**: Verify pipeline stages meet timing budget

**Problem**: Characters not displaying

**Possible Causes**:
1. Character buffer not being written
   - **Test**: Cocotb test character_buffer.v directly
   - **Check**: CPU bus interface signals
2. Font ROM not initialized
   - **Solution**: Verify font_8x16.hex file loaded
   - **Check**: Font ROM reads return non-zero data
3. Register writes not reaching GPU
   - **Solution**: Verify address decoding (0xC010-0xC01F)
   - **Test**: Read back registers to confirm writes

**Problem**: Wrong colors

**Possible Causes**:
1. Color palette mapping incorrect
   - **Solution**: Verify 3-bit to 8-bit RGB expansion
   - **Check**: color_palette.v logic
2. FG/BG swapped
   - **Solution**: Check pixel_bit logic in character_renderer.v

**Problem**: Cursor not flashing

**Possible Causes**:
1. Flash timer not incrementing
   - **Solution**: Verify vsync edge detection
   - **Test**: Monitor flash_counter in simulation
2. Cursor disabled
   - **Check**: CONTROL register bit 2 (CURSOR_EN)

### 6.4 Cocotb Test Failures

**Error**: "Assertion failed: hsync timing incorrect"
```python
# Debug: Print actual vs expected values
print(f"Expected: {expected_h_sync_start}, Got: {dut.h_count.value}")

# Check timing parameters in video_timing.v match spec
# Horizontal sync should start at pixel 656
```

**Error**: "Character buffer readback mismatch"
```python
# Debug: Verify dual-port RAM clock domain crossing
# Ensure adequate delay between write and read
await Timer(100, units='ns')  # Wait for CDC
```

---

## 7. Performance Validation

### 7.1 Timing Measurements

**Measure Pixel Clock**:
```bash
# Using logic analyzer or oscilloscope
# Probe pixel clock output (if available on test point)
# Expected: 25.175 MHz ± 0.5%
```

**Measure Frame Rate**:
```bash
# Monitor VSYNC signal
# Expected: 59.94 Hz (60 Hz nominal)
# Period: 16.68 ms
```

### 7.2 Resource Utilization

```bash
# Check final resource usage
grep "Logic Cells" pnr.log
grep "Block RAM" pnr.log
grep "PLL" pnr.log

# Should be well under limits:
# Logic: < 10% of 24336
# RAM: < 10% of 56 blocks
# PLL: 1 of 2 used
```

### 7.3 Character Output Latency

**Test**: Write character via register, measure time until visible on screen

**Expected**:
- Register write: 1 CPU cycle (immediate)
- Display update: 1-2 video frames (16-33 ms)

---

## 8. Next Steps After Quickstart

Once basic functionality is verified:

1. **Run Full Test Suite**:
   ```bash
   cd tests
   pytest --cov=rtl/peripherals/video
   ```

2. **Test All User Stories**:
   - Verify each acceptance scenario from spec.md
   - Test edge cases from spec

3. **Integration with CPU**:
   - Integrate GPU into full SOC
   - Test with 6502 firmware
   - Verify memory-mapped I/O from CPU

4. **Performance Testing**:
   - Measure character throughput
   - Test scrolling performance
   - Verify color change latency

5. **Create Demo Applications**:
   - Text editor demo
   - Terminal emulator
   - Retro game text display

---

## 9. Common Build Commands Reference

```bash
# Quick rebuild after code changes
cd build
make clean
make synth        # Synthesis only
make pnr          # Place and route
make bitstream    # Generate .bit file
make program      # Program FPGA

# Or all-in-one:
make all program

# Run specific test
cd tests/unit
make test_video_timing.py

# Run all tests
cd tests
make test

# Clean build artifacts
make clean

# Clean everything including test outputs
make distclean
```

---

## 10. Getting Help

### 10.1 Documentation

- **Feature Specification**: `specs/003-hdmi-character-display/spec.md`
- **Implementation Plan**: `specs/003-hdmi-character-display/plan.md`
- **Research Notes**: `specs/003-hdmi-character-display/research.md`
- **Module Design**: `specs/003-hdmi-character-display/data-model.md`
- **Register Map**: `specs/003-hdmi-character-display/contracts/register_map.md`
- **VGA Timing**: `/opt/wip/retrocpu/VGA_TIMING_SPECIFICATION.md`

### 10.2 Reference Materials

- **Reference DVI Code**: https://github.com/splinedrive/my_hdmi_device
- **ECP5 Documentation**: Lattice ECP5 Family Data Sheet
- **DVI Specification**: Digital Display Working Group (DDWG) DVI 1.0
- **VGA Timing**: VESA Display Monitor Timing (DMT) Standard

### 10.3 Debugging Tools

- **Waveform Viewer**: gtkwave (for viewing cocotb VCD files)
  ```bash
  gtkwave tests/unit/dump.vcd
  ```

- **Logic Analyzer**: For hardware debugging (if available)
  - Probe TMDS signals
  - Verify pixel clock
  - Check sync signals

- **Serial Console**: For firmware interaction
  ```bash
  screen /dev/ttyUSB0 115200
  ```

---

## 11. Success Criteria

You've successfully completed the quickstart when:

- [x] Reference DVI code displays test pattern on monitor
- [x] GPU synthesis completes without errors
- [x] All cocotb unit tests pass
- [x] All cocotb integration tests pass
- [x] FPGA programs successfully
- [x] Monitor detects video signal
- [x] Characters display correctly on screen
- [x] Cursor flashes visibly
- [x] Colors can be changed
- [x] Mode switching works (40/80 column)
- [x] All user stories from spec.md verified

**Congratulations!** You now have a working DVI Character Display GPU.

---

**Document Version**: 1.0
**Last Updated**: 2025-12-27
**Status**: Phase 1 Design Complete
