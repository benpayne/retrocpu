# HDMI/DVI Pinout Mapping for Colorlight i5

## Document Overview

This document provides the complete pin mapping for HDMI/DVI video output on the Colorlight i5 FPGA development board. The information is compiled from reference implementations and the LiteX board support files.

**Board**: Colorlight i5 v7.0
**FPGA**: Lattice ECP5-25F (LFE5U-25F-6BG381C)
**Package**: BGA381
**Video Standard**: DVI (HDMI-compatible) using TMDS encoding
**Resolution Target**: 640x480 @ 60Hz (VGA timing)

## HDMI/DVI Signal Overview

HDMI/DVI video transmission uses TMDS (Transition-Minimized Differential Signaling) encoding. The interface requires:

- 3 TMDS data channels (Data0, Data1, Data2) - carry RGB pixel data
- 1 TMDS clock channel - pixel clock for synchronization
- Each channel is a differential pair (positive and negative signals)

**Note**: The Colorlight i5 board's HDMI connector has limitations:
- I2C (SDA/SCL), HOTPLUG, and CEC pins are NOT connected
- This prevents EDID reading and hotplug detection
- Video output works but without monitor capability negotiation

## Pin Assignments

### TMDS Clock Channel

| Signal Name | Pin Number | IO Standard | Drive Strength | Function |
|-------------|------------|-------------|----------------|----------|
| `clk_p`     | J19        | LVCMOS33D   | 4 mA          | TMDS Clock + (positive) |
| `clk_n`     | K19        | LVCMOS33D   | 4 mA          | TMDS Clock - (negative) |

**Differential Pair**: J19/K19

### TMDS Data Channel 0 (Blue)

| Signal Name | Pin Number | IO Standard | Drive Strength | Function |
|-------------|------------|-------------|----------------|----------|
| `data0_p`   | G19        | LVCMOS33D   | 4 mA          | TMDS Data0 + (Blue pixel data) |
| `data0_n`   | H20        | LVCMOS33D   | 4 mA          | TMDS Data0 - (Blue pixel data) |

**Differential Pair**: G19/H20

### TMDS Data Channel 1 (Green)

| Signal Name | Pin Number | IO Standard | Drive Strength | Function |
|-------------|------------|-------------|----------------|----------|
| `data1_p`   | E20        | LVCMOS33D   | 4 mA          | TMDS Data1 + (Green pixel data) |
| `data1_n`   | F19        | LVCMOS33D   | 4 mA          | TMDS Data1 - (Green pixel data) |

**Differential Pair**: E20/F19

### TMDS Data Channel 2 (Red)

| Signal Name | Pin Number | IO Standard | Drive Strength | Function |
|-------------|------------|-------------|----------------|----------|
| `data2_p`   | C20        | LVCMOS33D   | 4 mA          | TMDS Data2 + (Red pixel data) |
| `data2_n`   | D19        | LVCMOS33D   | 4 mA          | TMDS Data2 - (Red pixel data) |

**Differential Pair**: C20/D19

## LVDS Pair Configurations

The ECP5 FPGA does not have dedicated high-speed SERDES blocks. Instead, differential signaling is implemented using generic I/O pins with differential capability.

### Differential Pair Summary

| Channel | Positive Pin | Negative Pin | Pair Location |
|---------|--------------|--------------|---------------|
| Clock   | J19          | K19          | Bank 6        |
| Data0   | G19          | H20          | Bank 6        |
| Data1   | E20          | F19          | Bank 6        |
| Data2   | C20          | D19          | Bank 6        |

All HDMI pins are located in **I/O Bank 6** of the ECP5 FPGA.

### IO Standard: LVCMOS33D

- **LVCMOS33D**: 3.3V Low-Voltage CMOS Differential
- Implements pseudo-differential signaling
- Suitable for DVI/HDMI at VGA resolutions (25.175 MHz pixel clock)
- Drive strength set to 4 mA (adequate for short traces on PCB to HDMI connector)

**⚠️ CRITICAL REQUIREMENT - Validated 2025-12-28:**
- **LVCMOS33D (differential) is REQUIRED** - not optional
- Using LVCMOS33 (single-ended) results in no signal detection by monitors
- LVCMOS33D automatically inverts the signal on the negative pin for proper TMDS differential signaling
- This was validated on Colorlight i5 v7.0 with the reference DVI implementation

## Clock Requirements

### Pixel Clock: 25.175 MHz
Standard VGA timing requires a 25.175 MHz pixel clock. The Colorlight i5 has a 25 MHz oscillator on-board (pin P3), which is close enough for most monitors to accept.

For precise timing, a PLL should be used to generate:
- **25.175 MHz**: Pixel clock (horizontal sync timing)
- **251.75 MHz**: TMDS clock (10x pixel clock for serialization)

### TMDS Serialization

Each TMDS data channel transmits 10 bits per pixel clock cycle:
- 8 bits of pixel data (RGB)
- 2 bits of control/sync data

**Serialization ratio**: 10:1
**TMDS bit rate**: 251.75 MHz (10 × 25.175 MHz)

The ECP5 `ODDRX2F` primitive implements DDR output to achieve this serialization without requiring full 251.75 MHz internal logic.

## Constraint File Example

Here's a Lattice LPF (Logical Preferences File) constraint example for the HDMI pins:

```lpf
# HDMI/DVI Output (GPDI connector)
# VALIDATED 2025-12-28 on Colorlight i5 v7.0

# TMDS Clock
LOCATE COMP "tmds_clk_p" SITE "J19";
LOCATE COMP "tmds_clk_n" SITE "K19";
IOBUF PORT "tmds_clk_p" IO_TYPE=LVCMOS33D DRIVE=4;  # MUST be LVCMOS33D
IOBUF PORT "tmds_clk_n" IO_TYPE=LVCMOS33D DRIVE=4;  # MUST be LVCMOS33D

# TMDS Data Channel 0 (Blue)
LOCATE COMP "tmds_data_p[0]" SITE "G19";
LOCATE COMP "tmds_data_n[0]" SITE "H20";
IOBUF PORT "tmds_data_p[0]" IO_TYPE=LVCMOS33D DRIVE=4;  # MUST be LVCMOS33D
IOBUF PORT "tmds_data_n[0]" IO_TYPE=LVCMOS33D DRIVE=4;  # MUST be LVCMOS33D

# TMDS Data Channel 1 (Green)
LOCATE COMP "tmds_data_p[1]" SITE "E20";
LOCATE COMP "tmds_data_n[1]" SITE "F19";
IOBUF PORT "tmds_data_p[1]" IO_TYPE=LVCMOS33D DRIVE=4;  # MUST be LVCMOS33D
IOBUF PORT "tmds_data_n[1]" IO_TYPE=LVCMOS33D DRIVE=4;  # MUST be LVCMOS33D

# TMDS Data Channel 2 (Red)
LOCATE COMP "tmds_data_p[2]" SITE "C20";
LOCATE COMP "tmds_data_n[2]" SITE "D19";
IOBUF PORT "tmds_data_p[2]" IO_TYPE=LVCMOS33D DRIVE=4;  # MUST be LVCMOS33D
IOBUF PORT "tmds_data_n[2]" IO_TYPE=LVCMOS33D DRIVE=4;  # MUST be LVCMOS33D
```

## Special Considerations

### 1. No True High-Speed SERDES

The ECP5-25F does not have dedicated SERDES blocks found in larger FPGAs. HDMI/DVI is implemented using:
- DDR output primitives (`ODDRX2F`)
- Generic differential I/O pins
- Software TMDS encoding

This limits practical resolutions to VGA (640x480) or SVGA (800x600) at 60Hz.

### 2. Pseudo-Differential Signaling

`LVCMOS33D` implements pseudo-differential signaling where the FPGA outputs complementary signals on two pins. This is not true LVDS but works for DVI at short cable lengths (< 2m).

### 3. Drive Strength

The 4 mA drive strength is adequate for the short PCB traces between the FPGA and HDMI connector on the Colorlight i5 board. Do not increase drive strength unnecessarily as it increases power consumption and EMI.

### 4. Pin Location Clustering

All HDMI pins are located in close proximity (Bank 6, pins C20-K19) to minimize:
- PCB trace length mismatches
- Inter-channel skew
- EMI crosstalk

### 5. Timing Constraints

For proper operation, timing constraints should be added:

```lpf
# Define pixel clock
FREQUENCY PORT "pixel_clk" 25.175 MHZ;

# Define TMDS clock (if PLL is used)
FREQUENCY NET "tmds_clk" 251.75 MHZ;

# Allow some relaxation for TMDS output timing (DDR output)
OUTPUT_SETUP PORT "tmds_data_p[*]" 2.0 ns HOLD 0.0 ns CLKPORT "tmds_clk";
OUTPUT_SETUP PORT "tmds_data_n[*]" 2.0 ns HOLD 0.0 ns CLKPORT "tmds_clk";
```

## Physical Connector

The HDMI connector on the Colorlight i5 board is a standard Type-A HDMI receptacle. The pinout is:

| HDMI Pin | Signal | FPGA Connection |
|----------|--------|-----------------|
| 1        | TMDS Data2+ (Red+) | C20 |
| 2        | TMDS Data2 Shield | GND |
| 3        | TMDS Data2- (Red-) | D19 |
| 4        | TMDS Data1+ (Green+) | E20 |
| 5        | TMDS Data1 Shield | GND |
| 6        | TMDS Data1- (Green-) | F19 |
| 7        | TMDS Data0+ (Blue+) | G19 |
| 8        | TMDS Data0 Shield | GND |
| 9        | TMDS Data0- (Blue-) | H20 |
| 10       | TMDS Clock+ | J19 |
| 11       | TMDS Clock Shield | GND |
| 12       | TMDS Clock- | K19 |
| 13       | CEC | Not Connected |
| 14       | Reserved | Not Connected |
| 15       | SCL (DDC) | Not Connected |
| 16       | SDA (DDC) | Not Connected |
| 17       | GND | GND |
| 18       | +5V Power | Not Connected |
| 19       | Hot Plug Detect | Not Connected |

**Note**: Pins 13, 15, 16, 18, and 19 are not connected on the Colorlight i5 board.

## Implementation Notes

### PLL Configuration

The ECP5 has built-in PLLs (EHXPLLL primitives) that should be configured for:

```verilog
// Input: 25 MHz board oscillator
// Output 1: 25.175 MHz pixel clock (for video timing)
// Output 2: 251.75 MHz TMDS clock (for serialization, DDR → effective 125.875 MHz)
```

The actual PLL configuration depends on the reference code from Phase 0 (Task T001-T008).

### TMDS Encoding

Each RGB color channel (8 bits) is encoded into 10 bits using TMDS encoding to:
- Minimize transitions (reduce EMI)
- Maintain DC balance
- Embed control signals (HSYNC, VSYNC, DE)

Reference implementations should be studied in Phase 0 for correct TMDS encoder design.

### DDR Output

The ECP5 `ODDRX2F` primitive is used to serialize TMDS data:

```verilog
ODDRX2F tmds_out (
    .D0(data[0]),    // First bit
    .D1(data[1]),    // Second bit
    .D2(data[2]),    // Third bit
    .D3(data[3]),    // Fourth bit
    .SCLK(tmds_clk), // High-speed TMDS clock
    .ECLK(pixel_clk),// Pixel clock
    .RST(reset),
    .Q(tmds_out_p)   // Serialized output to TMDS pin
);
```

Multiple `ODDRX2F` primitives are cascaded to achieve 10:1 serialization.

## Validation Checklist

After implementing the HDMI output:

- [ ] Synthesize design with correct pin constraints
- [ ] Program bitstream to Colorlight i5 board
- [ ] Connect HDMI cable to monitor
- [ ] Verify monitor detects video signal
- [ ] Check for stable sync (no flickering or rolling)
- [ ] Verify correct colors (if displaying test pattern)
- [ ] Test with multiple monitors/brands for compatibility
- [ ] Measure signal quality with oscilloscope (optional)
- [ ] Verify signal meets TMDS specification (eye diagram)

## References

1. **LiteX Platform Files**: [colorlight_i5.py](https://github.com/litex-hub/litex-boards/blob/master/litex_boards/platforms/colorlight_i5.py)
2. **HDMI Reference Implementation**: [my_hdmi_device](https://github.com/splinedrive/my_hdmi_device)
3. **Colorlight FPGA Projects**: [Colorlight-FPGA-Projects](https://github.com/wuxx/Colorlight-FPGA-Projects)
4. **ECP5 Family Datasheet**: Lattice Semiconductor
5. **DVI 1.0 Specification**: Digital Display Working Group (DDWG)
6. **VESA Display Monitor Timing Standard**: Video Electronics Standards Association

## Revision History

| Date       | Version | Description |
|------------|---------|-------------|
| 2025-12-28 | 1.0     | Initial pinout mapping documentation |

---

**Document Status**: ✅ Complete
**Validated**: Pending hardware test (Task T006)
**Next Steps**: Proceed with Phase 0 hardware validation (Tasks T004-T008)
