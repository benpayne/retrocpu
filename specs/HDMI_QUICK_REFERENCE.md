# HDMI Quick Reference - Colorlight i5
## Fast lookup for implementation details

---

## Pin Assignments (Add to colorlight_i5.lpf)

```lpf
## HDMI Output (GPDI) ##################################
LOCATE COMP "tmds_clk_p" SITE "J19";
LOCATE COMP "tmds_d0_p" SITE "G19";  # Blue
LOCATE COMP "tmds_d1_p" SITE "E20";  # Green
LOCATE COMP "tmds_d2_p" SITE "C20";  # Red

IOBUF PORT "tmds_clk_p" IO_TYPE=LVCMOS33D DRIVE=4;
IOBUF PORT "tmds_d0_p" IO_TYPE=LVCMOS33D DRIVE=4;
IOBUF PORT "tmds_d1_p" IO_TYPE=LVCMOS33D DRIVE=4;
IOBUF PORT "tmds_d2_p" IO_TYPE=LVCMOS33D DRIVE=4;

FREQUENCY PORT "clk_pixel" 25 MHZ;
FREQUENCY PORT "clk_tmds" 125 MHZ;
```

---

## Clock Configuration (640x480@60Hz)

### Option 1: Direct 25 MHz (Simplest)
```
Source: System clock (25 MHz)
Pixel Clock: 25 MHz (no PLL needed)
TMDS Clock: 125 MHz (5x, via PLL)
Note: Slightly out of spec but works
```

### Option 2: 25.2 MHz (Recommended)
```
ecppll -i 25 -o 25.2 --highres
Result: Within VESA tolerance, exact 60 Hz
```

### Option 3: 25.125 MHz (Close to 25.175 MHz)
```
ecppll -i 12.5 -o 25.125 --highres
CLKI_DIV=4, CLKFB_DIV=67, CLKOP_DIV=3
```

---

## Video Timing Parameters (640x480@60Hz)

```verilog
// Horizontal timing
parameter H_VISIBLE = 640;
parameter H_FRONT   = 16;
parameter H_SYNC    = 96;
parameter H_BACK    = 48;
parameter H_TOTAL   = 800;

// Vertical timing
parameter V_VISIBLE = 480;
parameter V_FRONT   = 10;
parameter V_SYNC    = 2;
parameter V_BACK    = 33;
parameter V_TOTAL   = 525;

// Sync polarities
parameter H_POL = 0; // Negative
parameter V_POL = 0; // Negative
```

---

## ECP5 Primitive Instantiation

### EHXPLLL (PLL)
```verilog
EHXPLLL #(
    .CLKI_DIV(1),
    .CLKFB_DIV(5),
    .CLKOP_DIV(8),
    .CLKOS_DIV(40),
    .FEEDBK_PATH("CLKOP")
) pll_inst (
    .CLKI(clk_25mhz),
    .CLKOP(clk_tmds),    // 125 MHz
    .CLKOS(clk_pixel),   // 25 MHz
    .LOCK(pll_locked)
);
```

### ODDRX1F (DDR Output)
```verilog
ODDRX1F oddr_inst (
    .D0(tmds_bit0),
    .D1(tmds_bit1),
    .SCLK(clk_tmds),
    .RST(1'b0),
    .Q(tmds_out)
);
```

**CRITICAL:** All uppercase for primitive names and ports!

---

## Module Integration Checklist

### Files to Copy from splinedrive/my_hdmi_device
- [ ] `tmds_encoder.v` - TMDS 8b/10b encoder
- [ ] `hdmi_device.v` - Top-level HDMI module
- [ ] `video_timings.v` - VGA timing generator
- [ ] `ecp5pll.sv` - PLL wrapper (optional)

### Pin Constraint Updates
- [ ] Add HDMI pins to `colorlight_i5.lpf`
- [ ] Add clock frequency constraints
- [ ] Verify no pin conflicts with existing design

### Top-level Integration
- [ ] Instantiate HDMI module
- [ ] Connect pixel data source
- [ ] Connect video timing signals
- [ ] Add PLL for clock generation
- [ ] Handle PLL lock signal

---

## Test Pattern - Color Bars

```verilog
// Simple 8-color bars for testing
always @(posedge clk_pixel) begin
    if (video_active) begin
        case (h_pos[9:7])  // Divide into 8 regions
            3'd0: {r,g,b} <= 24'hFFFFFF;  // White
            3'd1: {r,g,b} <= 24'hFFFF00;  // Yellow
            3'd2: {r,g,b} <= 24'h00FFFF;  // Cyan
            3'd3: {r,g,b} <= 24'h00FF00;  // Green
            3'd4: {r,g,b} <= 24'hFF00FF;  // Magenta
            3'd5: {r,g,b} <= 24'hFF0000;  // Red
            3'd6: {r,g,b} <= 24'h0000FF;  // Blue
            3'd7: {r,g,b} <= 24'h000000;  // Black
        endcase
    end else begin
        {r,g,b} <= 24'h000000;  // Blanking
    end
end
```

---

## Build Commands

```bash
# Synthesis
yosys -p "synth_ecp5 -json design.json" top.v

# Place and Route
nextpnr-ecp5 --25k --package CABGA256 \
    --json design.json \
    --lpf colorlight_i5.lpf \
    --textcfg design.config

# Bitstream
ecppack design.config design.bit

# Programming
openocd -f colorlight_i5.cfg \
    -c "svf -quiet design.svf; exit"
```

---

## Character Display - 80x30 Text Mode

### Memory Requirements

```
Character Buffer: 80 x 30 = 2,400 bytes
Color Attributes: 80 x 30 = 2,400 bytes (fg/bg)
Character ROM: 256 chars x 8 bytes = 2,048 bytes
Total: ~7 KB (easily fits in Block RAM)
```

### Pixel Generation Logic

```verilog
// Character position
wire [6:0] char_x = h_pos[9:3];  // 80 chars (0-79)
wire [4:0] char_y = v_pos[8:4];  // 30 rows (0-29)
wire [2:0] pixel_x = h_pos[2:0]; // 8 pixels per char
wire [3:0] pixel_y = v_pos[3:0]; // 16 lines per char (8x16)

// Character lookup
wire [7:0] char_code = char_buffer[char_y * 80 + char_x];
wire [7:0] char_row = char_rom[{char_code, pixel_y[3:1]}];
wire pixel_on = char_row[7 - pixel_x];
```

---

## Resource Usage Estimates

| Component | LUTs | Block RAM | PLLs |
|-----------|------|-----------|------|
| TMDS Encoders (3x) | ~600 | 0 | 0 |
| Video Timing | ~50 | 0 | 0 |
| Clock Generation | ~20 | 0 | 1 |
| Character Buffer | ~50 | 2 blocks | 0 |
| Character ROM | ~100 | 1 block | 0 |
| Character Generator | ~150 | 0 | 0 |
| **Total** | ~970 | 3 blocks | 1 |

**Available on ECP5-25:**
- LUTs: 24,000 (4% used)
- Block RAM: 1,008 Kbits / 126 blocks (2% used)
- PLLs: 2 (50% used)

**Plenty of headroom!**

---

## Pre-built Test Bitstream

```bash
# Download from wuxx repository
wget https://github.com/wuxx/Colorlight-FPGA-Projects/raw/master/demo/i5/hdmi_test_pattern.bit

# Program to Colorlight i5
openocd -f colorlight_i5.cfg \
    -c "svf hdmi_test_pattern.svf; exit"
```

If this works, your HDMI hardware is confirmed working!

---

## Common Issues and Solutions

### Problem: No display output
- Check PLL lock signal
- Verify clock frequencies
- Test with known-good bitstream
- Try different monitor

### Problem: Unstable image
- Check clock domain crossing
- Add FIFO between domains
- Verify timing constraints met

### Problem: Wrong colors
- Check TMDS lane assignment
- Verify R/G/B channel order
- Check TMDS encoder polarity

### Problem: Synthesis fails
- Verify primitive names are UPPERCASE
- Check port name case sensitivity
- Ensure correct ECP5 device selected

### Problem: Timing not met
- Use DDR approach (125 MHz vs 250 MHz)
- Pipeline critical paths
- Check NextPNR timing report
- Consider lower resolution

---

## Critical Reminders

1. **UPPERCASE PRIMITIVES:** `ODDRX1F`, `EHXPLLL` (not oddrx1f)
2. **LVCMOS33D:** Only specify positive pin, negative auto-generated
3. **PLL LOCK:** Wait for lock before enabling video
4. **CLOCK DOMAINS:** Use FIFO for crossing pixel ↔ TMDS clocks
5. **NO I2C/HOTPLUG:** Not connected on Colorlight i5 (DVI mode only)

---

## Next Steps

1. ✅ Research complete (this document)
2. ⬜ Test pre-built bitstream (hardware validation)
3. ⬜ Integrate TMDS encoder modules
4. ⬜ Generate color bar test pattern
5. ⬜ Implement character ROM and buffer
6. ⬜ Create character generator logic
7. ⬜ Integrate with M65C02 CPU
8. ⬜ Update firmware for HDMI output

---

**Quick Reference Version:** 1.0
**Last Updated:** 2025-12-27
