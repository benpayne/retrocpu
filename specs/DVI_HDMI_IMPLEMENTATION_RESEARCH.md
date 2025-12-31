# DVI/HDMI Implementation Research for Colorlight i5
## Reference: splinedrive/my_hdmi_device

**Research Date:** 2025-12-27
**Target Board:** Colorlight i5 (ECP5U-25 FPGA)
**Purpose:** Foundation for character display GPU implementation

---

## Executive Summary

This document provides comprehensive research on implementing DVI/HDMI output on the Colorlight i5 board using the ECP5 FPGA. The primary reference implementation is the `splinedrive/my_hdmi_device` repository, which provides a clean, well-documented TMDS encoder implementation derived from the DVI standard.

### Key Findings

1. **Working Reference:** The splinedrive/my_hdmi_device repository has proven Colorlight i5 support
2. **Pre-built Demo:** wuxx/Colorlight-FPGA-Projects provides a working HDMI test pattern bitstream
3. **Pin Assignments:** HDMI pins are documented in LiteX platform files and Tom Verbeure's pinout
4. **Toolchain:** Full open-source toolchain support (Yosys/NextPNR)
5. **Implementation Approaches:** Both DDR and SDR TMDS serialization are supported

---

## Repository Structure and Key Files

### Main Repository: splinedrive/my_hdmi_device
**URL:** https://github.com/splinedrive/my_hdmi_device

#### Core Implementation Files

| File | Purpose | Description |
|------|---------|-------------|
| `tmds_encoder.v` | TMDS Encoding | 8b/10b encoding per DVI standard (Page 29) |
| `hdmi_device.v` | HDMI Device | Main HDMI module with ECP5-specific primitives |
| `video_timings.v` | VGA Timings | VGA timing generation (640x480, etc.) |
| `my_vga_clk_generator.v` | Clock Gen | PLL-based pixel clock generation |
| `ecp5pll.sv` | ECP5 PLL | ECP5 EHXPLLL wrapper module |
| `ball.v` | Test Pattern | Bouncing ball demo (from Steven Hugg's book) |
| `chip_balls.v` | Test Pattern | Multiple balls test pattern |

#### Platform-Specific Files

| File | Purpose |
|------|---------|
| `colorlighti5.lpf` | Pin constraints for Colorlight i5 |
| `Makefile.colorlighti5` | Build script (Yosys/NextPNR/ecppack) |

### Supporting Repositories

1. **wuxx/Colorlight-FPGA-Projects**
   - URL: https://github.com/wuxx/Colorlight-FPGA-Projects
   - Contains: Pre-built `hdmi_test_pattern.bit` for Colorlight i5
   - Location: `demo/i5/hdmi_test_pattern.bit`
   - Board documentation and pinouts

2. **litex-hub/litex-boards**
   - URL: https://github.com/litex-hub/litex-boards
   - Platform file: `litex_boards/platforms/colorlight_i5.py`
   - Target file: `litex_boards/targets/colorlight_i5.py`
   - Contains GPDI (HDMI) pin definitions

3. **kazkojima/colorlight-i5-tips**
   - URL: https://github.com/kazkojima/colorlight-i5-tips
   - Tiny tips and tricks for Colorlight i5 usage

---

## ECP5 FPGA Primitives for DVI/TMDS

### 1. ODDRX2F - Output DDR (4:1 serialization)

**Purpose:** Generic 4:1 output DDR primitive for high-speed data output

**Usage in TMDS:**
- Converts 4 bits of parallel data to 2 bits of DDR output
- Used in combination with pixel clock and 2x pixel clock
- Requires 2x clock frequency (50 MHz for 25 MHz pixel clock)

**Key Characteristics:**
- Less complex than ODDRX1F
- Lower clock frequency requirements
- Standard approach for 640x480@60Hz

### 2. ODDRX1F - Output DDR (2:1 serialization)

**Purpose:** Generic 2:1 output DDR primitive for specialized applications

**Usage in TMDS:**
- Can shift and send two bits per clock
- Allows using 125 MHz clock instead of 250 MHz
- Better for higher resolutions
- Specialized block with lower effective latency

**Important Notes:**
- Clock routing between PLL and ODDRX1F.CLK can be done via fabric routing
- May require phase adjustment (output delayed by one ECLK period)
- All port names MUST be uppercase for Yosys recognition

### 3. EHXPLLL - ECP5 Phase-Locked Loop

**Purpose:** Clock generation and frequency multiplication

**Key Parameters:**
- `CLKI_DIV` - Input clock divider
- `CLKFB_DIV` - Feedback divider
- `CLKOP_DIV` - Output clock divider
- `CLKOS_DIV` - Secondary output divider
- `FEEDBK_PATH` - Feedback path selection
- VCO frequency must be in range 400-800 MHz

**Example Configuration for ~25 MHz:**
```
Input: 12.5 MHz
CLKI_DIV = 4
CLKFB_DIV = 67
CLKOP_DIV = 3
CLKOS_DIV = 25
FEEDBK_PATH = "CLKOP"
Result: VCO = 628.125 MHz, Output = 25.125 MHz
```

**Tool Support:**
- Use `ecppll` tool from Project Trellis
- Add `--highres` flag for better frequency matching
- Wrapper modules recommended for simpler integration

---

## Pin Assignments - Colorlight i5 HDMI

### HDMI Connector Pinout

Based on LiteX platform definition and wuxx/Colorlight-FPGA-Projects:

| Signal | FPGA Pin | IOStandard | Drive | Notes |
|--------|----------|------------|-------|-------|
| TMDS Clock (+) | J19 | LVCMOS33D | 4 | Pixel clock |
| TMDS Data0 (+) | G19 | LVCMOS33D | 4 | Blue channel |
| TMDS Data1 (+) | E20 | LVCMOS33D | 4 | Green channel |
| TMDS Data2 (+) | C20 | LVCMOS33D | 4 | Red channel |

**Critical Notes:**
1. **LVCMOS33D:** Differential signaling - negative pins auto-generated from positive
2. **Impedance:** HDMI requires 100Ω ±5% differential impedance
3. **Matching:** ±3mm length matching between TMDS signal pairs required
4. **Missing Signals:** I2C, HOTPLUG, and CEC pins are NOT connected on Colorlight i5
5. **One-Way Only:** Colorlight i5 HDMI is output-only (no video input capability)

### J4/J5 Connector Mapping

Per wuxx/Colorlight-FPGA-Projects documentation:
- **J4:** Pin B1 (FPGA pins 143/144)
- **J5:** Pin C1 (FPGA pins 145/146)

### Current RetroCPU Pin Usage

The existing `/opt/wip/retrocpu/colorlight_i5.lpf` currently uses:
- Clock: P3 (25 MHz)
- UART: J17 (TX), H18 (RX)
- LEDs: N18, N17, L20, M18
- LCD: E5, F4, F5, E6, G5, D16, D18
- PS/2: K5, B3

**No conflicts detected with HDMI pins (J19, G19, E20, C20)**

---

## PLL Configuration for Pixel Clock Generation

### Standard Video Modes

| Resolution | Refresh | Pixel Clock | Tolerance | Practical |
|------------|---------|-------------|-----------|-----------|
| 640x480 | 60 Hz | 25.175 MHz | ±0.5% | 25.2 MHz ✓ |
| 800x600 | 60 Hz | 40.000 MHz | ±0.5% | 40.0 MHz ✓ |
| 1024x768 | 60 Hz | 65.000 MHz | ±0.5% | 65.0 MHz ✓ |

### Recommended Approach for 640x480@60Hz

**Option 1: Use 25 MHz (Simple)**
- Input clock: Already available (25 MHz system clock)
- No PLL required
- Slightly out of VESA spec but works in practice
- Tolerance: -0.69% (borderline acceptable)

**Option 2: Use 25.2 MHz (Recommended)**
- Within VESA tolerance
- Easy to generate via PLL
- Exact 60 Hz refresh rate
- Tolerance: +0.10% (excellent)

**Option 3: Use 25.125 MHz (Close Match)**
- Very close to 25.175 MHz
- Example config provided above
- Requires `--highres` flag in ecppll
- Tolerance: -0.20% (excellent)

### Clock Domain Architecture

For TMDS serialization, need multiple clock domains:

1. **Pixel Clock (25 MHz)** - Video timing and pixel data
2. **TMDS Clock (250 MHz or 125 MHz)** - Serialization
   - DDR approach: 125 MHz with ODDRX1F (2:1 serialization)
   - SDR approach: 250 MHz with ODDRX2F (4:1 serialization)

**Important:** Clock domain crossing between pixel and TMDS clocks requires careful synchronization (use shallow FIFO or well-timed handshaking)

---

## TMDS Encoding Approach

### 8b/10b Encoding (TMDS-specific)

The TMDS encoding algorithm is different from IBM's original 8b/10b:
- Created by Silicon Image in 1999
- Designed for DVI/HDMI applications
- Goals:
  1. Transition minimization (reduce EMI)
  2. DC balance (ensure equal 1s and 0s)
  3. Clock recovery (sufficient transitions for PLL)

### Implementation Details (from splinedrive/my_hdmi_device)

**Encoding Process:**
1. **Input:** 8-bit pixel data (R, G, or B channel)
2. **Control Signals:** DE (Display Enable), HSYNC, VSYNC
3. **Output:** 10-bit TMDS symbol

**Key Features:**
- Maintains running disparity for DC balance
- Control periods use special 10-bit symbols
- Active video uses transition-minimized encoding
- Separate encoder per color channel (3 total)

**Reference:** DVI Standard, Page 29

### Differential Pair Requirements

- **Impedance:** 100Ω ±5%
- **Matching:** ±3mm between pairs
- **IO Standard:** LVCMOS33D on ECP5
- **Drive Strength:** 4 (per LiteX configuration)

---

## Build Process and Toolchain

### Required Tools (Open Source)

1. **Yosys** - Synthesis
2. **NextPNR-ECP5** - Place and route
3. **ecppack** - Bitstream packing
4. **OpenOCD** - Programming (JTAG)
5. **ecppll** - PLL configuration calculator

### Build Flow

```bash
# 1. Synthesis
yosys -p "synth_ecp5 -json design.json" design.v

# 2. Place and Route
nextpnr-ecp5 --25k --package CABGA256 \
  --json design.json \
  --lpf constraints.lpf \
  --textcfg design.config

# 3. Bitstream Generation
ecppack design.config design.bit

# 4. Programming
openocd -f colorlight_i5.cfg \
  -c "svf -quiet -progress design.svf; exit"
```

### Makefile Example (from splinedrive/my_hdmi_device)

Expected structure in `Makefile.colorlighti5`:
```makefile
DEVICE = LFE5U-25F
PACKAGE = CABGA256
SPEED = 6

%.json: %.v
    yosys -p "synth_ecp5 -json $@" $^

%.config: %.json
    nextpnr-ecp5 --$(DEVICE) --package $(PACKAGE) \
      --json $< --lpf colorlighti5.lpf --textcfg $@

%.bit: %.config
    ecppack $< $@

%.svf: %.bit
    ecppack --svf $@ $<

program: design.svf
    openocd -f openocd.cfg -c "svf $<; exit"
```

### Programming via DAPLink

The Colorlight i5 breakout board includes an ARMMbed DAPLink debugger:
- Supports JTAG programming
- USB interface for easy connection
- OpenOCD configuration required

**OpenOCD Config Example:**
```tcl
interface cmsis-dap
transport select jtag
adapter speed 10000

jtag newtap ecp5 tap -irlen 8 -expected-id 0x41111043
```

---

## Synthesis Settings and Constraints

### Critical Constraints

1. **Clock Constraints**
```lpf
FREQUENCY PORT "clk_pixel" 25 MHZ;
FREQUENCY PORT "clk_tmds" 250 MHZ;
```

2. **Differential Pairs**
```lpf
LOCATE COMP "tmds_clk_p" SITE "J19";
IOBUF PORT "tmds_clk_p" IO_TYPE=LVCMOS33D DRIVE=4;
```

3. **Timing Constraints**
- May need to constrain paths between clock domains
- Consider false paths for asynchronous crossings
- Use FIFO for reliable clock domain crossing

### Synthesis Considerations

1. **Primitive Instantiation:**
   - MUST use uppercase for ECP5 primitives (ODDRX1F, EHXPLLL)
   - Yosys requires exact naming
   - Case sensitivity critical for synthesis success

2. **Resource Usage:**
   - Colorlight i5: ECP5U-25F (24K LUTs)
   - TMDS encoder: ~200 LUTs per channel (600 total)
   - PLLs: 2 available (1 for pixel clock, 1 for TMDS clock)
   - Block RAM: 1,008 Kbits (useful for framebuffer)

3. **Timing Closure:**
   - 250 MHz TMDS clock is challenging
   - DDR approach (125 MHz) recommended for timing closure
   - May need to pipeline critical paths

---

## Test Patterns and Example Code

### Available Test Patterns

From splinedrive/my_hdmi_device:

1. **ball.v** - Single bouncing ball
   - Demonstrates basic video timing
   - Simple pixel generation
   - Physics simulation

2. **chip_balls.v** - Multiple balls
   - More complex test pattern
   - Tests throughput

3. **Color Bars** (common pattern)
   - Standard SMPTE color bars
   - Easy to implement
   - Good for testing

### Simple Test Pattern Implementation

```verilog
// Test pattern: Color bars
always @(posedge clk_pixel) begin
    if (video_active) begin
        if (h_pos < 80)        {r, g, b} <= {8'hFF, 8'hFF, 8'hFF}; // White
        else if (h_pos < 160)  {r, g, b} <= {8'hFF, 8'hFF, 8'h00}; // Yellow
        else if (h_pos < 240)  {r, g, b} <= {8'h00, 8'hFF, 8'hFF}; // Cyan
        else if (h_pos < 320)  {r, g, b} <= {8'h00, 8'hFF, 8'h00}; // Green
        else if (h_pos < 400)  {r, g, b} <= {8'hFF, 8'h00, 8'hFF}; // Magenta
        else if (h_pos < 480)  {r, g, b} <= {8'hFF, 8'h00, 8'h00}; // Red
        else if (h_pos < 560)  {r, g, b} <= {8'h00, 8'h00, 8'hFF}; // Blue
        else                   {r, g, b} <= {8'h00, 8'h00, 8'h00}; // Black
    end else begin
        {r, g, b} <= 24'h000000; // Blanking
    end
end
```

### Pre-built Test Bitstream

**Location:** wuxx/Colorlight-FPGA-Projects/demo/i5/hdmi_test_pattern.bit

**How to Use:**
1. Download bitstream from repository
2. Program via OpenOCD and DAPLink
3. Connect HDMI monitor
4. Should display test pattern immediately

**Verification:**
- Confirms HDMI hardware is working
- Validates pin assignments
- Tests clock generation
- Validates before custom implementation

---

## Known Working Configurations

### Configuration 1: DDR with ODDRX1F (Recommended)

**Clocks:**
- Pixel clock: 25 MHz
- TMDS clock: 125 MHz (5x pixel clock)

**Advantages:**
- Lower clock frequency (easier timing closure)
- Standard approach
- Well-tested

**Primitives:**
- EHXPLLL for clock generation
- ODDRX1F for DDR output (one per TMDS lane)

### Configuration 2: SDR with ODDRX2F (Alternative)

**Clocks:**
- Pixel clock: 25 MHz
- TMDS clock: 250 MHz (10x pixel clock)

**Advantages:**
- Simpler primitive
- More straightforward

**Disadvantages:**
- Higher clock frequency (timing more challenging)
- May not meet timing on ECP5-25

### Configuration 3: LiteX VideoHDMIPHY

**Framework:** LiteX SoC builder

**Features:**
- Integrated HDMI PHY
- Framebuffer support
- Terminal support
- Multiple resolution support

**Usage:**
```python
from litex.soc.cores.video import VideoHDMIPHY

self.videophy = VideoHDMIPHY(
    platform.request("gpdi"),
    clock_domain="hdmi"
)
```

---

## Implementation Gotchas and Best Practices

### Critical Gotchas

1. **Case Sensitivity**
   - ECP5 primitives MUST be uppercase
   - Port names MUST be uppercase
   - Yosys will silently fail otherwise

2. **Clock Domain Crossing**
   - Pixel clock → TMDS clock crossing is critical
   - Don't use simple registers
   - Use FIFO or carefully timed handshaking
   - Metastability is a real risk

3. **LVCMOS33D Behavior**
   - Only define positive pins in LPF
   - Negative pins auto-generated
   - Don't try to control both explicitly

4. **I2C/HOTPLUG Missing**
   - Colorlight i5 doesn't connect these signals
   - Monitor may not detect connection immediately
   - Some monitors may not work at all
   - DVI monitors more likely to work than HDMI

5. **PLL Lock Time**
   - Wait for PLL lock before enabling output
   - Use LOCK signal from EHXPLLL
   - Reset video timing generator on PLL lock

6. **Timing Constraints**
   - MUST constrain all clocks in LPF
   - Check timing reports from NextPNR
   - Don't ignore timing warnings

### Best Practices

1. **Start Simple**
   - Test with pre-built bitstream first
   - Verify hardware before custom code
   - Start with color bars, not complex graphics

2. **Use Reference Implementations**
   - splinedrive/my_hdmi_device is proven
   - Don't reinvent TMDS encoder
   - Copy working code, modify incrementally

3. **Debugging Approach**
   - Use ILA (Integrated Logic Analyzer) for debugging
   - Monitor PLL lock status
   - Check video timing with logic analyzer
   - Test with multiple monitors

4. **Resource Planning**
   - Reserve PLLs for clock generation
   - Plan Block RAM usage for framebuffer
   - Consider character ROM in Block RAM
   - Leave headroom for character display logic

5. **Clock Strategy**
   - Generate all clocks from single PLL if possible
   - Use phase-aligned outputs
   - Minimize clock domain crossings
   - Document all clock domains clearly

---

## Integration Plan for RetroCPU Character Display

### Phase 1: HDMI Hardware Validation

1. **Test with pre-built bitstream**
   - Download wuxx hdmi_test_pattern.bit
   - Program Colorlight i5
   - Verify HDMI output works

2. **Integrate basic HDMI module**
   - Copy splinedrive modules (tmds_encoder.v, hdmi_device.v)
   - Add pin constraints to colorlight_i5.lpf
   - Generate test pattern (color bars)
   - Verify custom implementation

### Phase 2: Video Timing Generator

1. **Implement 640x480@60Hz timing**
   - Horizontal: 640 visible, 800 total
   - Vertical: 480 visible, 525 total
   - Use video_timings.v as reference

2. **Test with simple patterns**
   - Color bars
   - Moving test pattern
   - Validate all timing parameters

### Phase 3: Character Display GPU

1. **Character ROM**
   - Store 8x8 font in Block RAM
   - Use ASCII encoding
   - Generate ROM from bitmap font file

2. **Character Buffer**
   - 80x30 or 80x25 text mode
   - Dual-port RAM for CPU writes
   - Video read during display

3. **Character Generator**
   - Convert character codes to pixels
   - Support foreground/background colors
   - Handle cursor rendering

4. **Memory Mapping**
   - Map character buffer to CPU address space
   - Support memory-mapped control registers
   - Integrate with existing memory controller

### Phase 4: Integration and Testing

1. **System Integration**
   - Connect to M65C02 CPU
   - Update memory map
   - Add character display driver to firmware

2. **Testing**
   - Port monitor to output to HDMI
   - Test BASIC interpreter with display
   - Performance validation

---

## Resource Links

### Primary References

1. **splinedrive/my_hdmi_device**
   - https://github.com/splinedrive/my_hdmi_device
   - Main HDMI implementation reference

2. **wuxx/Colorlight-FPGA-Projects**
   - https://github.com/wuxx/Colorlight-FPGA-Projects
   - Colorlight i5 pinouts and demos

3. **litex-hub/litex-boards**
   - https://github.com/litex-hub/litex-boards
   - LiteX platform definitions

### Documentation

4. **Tom Verbeure's Blog**
   - https://tomverbeure.github.io/2021/01/22/The-Colorlight-i5-as-FPGA-development-board.html
   - Getting started with Colorlight i5
   - https://tomverbeure.github.io/2021/01/30/Colorlight-i5-Extension-Board-Pin-Mapping.html
   - Extension board pinout

5. **Project F - ECP5 FPGA Clock Generation**
   - https://projectf.io/posts/ecp5-fpga-clock/
   - PLL configuration guide

6. **ECP5 PLL Configuration**
   - https://blog.dave.tf/post/ecp5-pll/
   - Detailed PLL setup

7. **Learn FPGA - HDMI Tutorial**
   - https://github.com/BrunoLevy/learn-fpga/blob/master/FemtoRV/TUTORIALS/HDMI.md
   - HDMI basics and implementation

### Technical Documentation

8. **NextPNR ECP5 Primitives**
   - https://github.com/YosysHQ/nextpnr/blob/master/ecp5/docs/primitives.md
   - Official primitive documentation

9. **Lattice ECP5 Family Datasheet**
   - https://www.latticesemi.com/-/media/LatticeSemi/Documents/DataSheets/ECP5/FPGA-DS-02012-3-4-ECP5-ECP5G-Family-Data-Sheet.ashx

10. **Project Trellis**
    - https://github.com/yosyshq/prjtrellis
    - ECP5 bitstream documentation

### Related Projects

11. **kazkojima/colorlight-i5-tips**
    - https://github.com/kazkojima/colorlight-i5-tips
    - Tips and tricks

12. **johnwinans/FPGA_hdmi_device**
    - https://github.com/johnwinans/FPGA_hdmi_device
    - Fork of splinedrive implementation

### Video Timing Resources

13. **Project F - Video Timings**
    - https://projectf.io/posts/video-timings-vga-720p-1080p/
    - Standard video mode timings

14. **FPGA4Fun - HDMI**
    - https://www.fpga4fun.com/HDMI.html
    - HDMI basics tutorial

---

## Conclusion

The Colorlight i5 board is well-supported for HDMI/DVI output with multiple working reference implementations. The splinedrive/my_hdmi_device repository provides a clean, understandable TMDS encoder implementation that can be directly integrated into the RetroCPU project.

### Key Takeaways

1. **Hardware is Proven:** Pre-built bitstream confirms HDMI output works
2. **Open Source Toolchain:** Full Yosys/NextPNR support
3. **Clean Reference Code:** splinedrive implementation is well-documented
4. **Pin Availability:** No conflicts with existing peripherals
5. **Resource Sufficient:** ECP5-25 has enough resources for character display

### Recommended Next Steps

1. Test with wuxx pre-built bitstream (hardware validation)
2. Integrate splinedrive TMDS encoder and HDMI device modules
3. Implement simple test pattern (validate custom implementation)
4. Develop character display GPU (80x30 text mode)
5. Integrate with M65C02 CPU and memory system

### Risk Assessment

- **Low Risk:** Hardware validation with pre-built bitstream
- **Low Risk:** TMDS encoder integration (proven reference)
- **Medium Risk:** Timing closure at 125/250 MHz (use DDR approach)
- **Medium Risk:** Clock domain crossing (use FIFO or careful handshaking)
- **Low Risk:** Resource availability (sufficient LUTs and Block RAM)

**Overall:** Implementation is feasible with low to medium risk.

---

**Document Version:** 1.0
**Last Updated:** 2025-12-27
**Author:** Research based on open-source implementations
