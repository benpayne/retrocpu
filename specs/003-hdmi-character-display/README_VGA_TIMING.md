# VGA 640x480 @ 60Hz Timing Documentation

Complete VESA-compliant timing documentation for implementing the video_timing.v module for the HDMI character display GPU.

## Documentation Files

This directory contains comprehensive VGA timing documentation in multiple formats for different use cases:

### 1. Quick Reference Card
**File**: `VGA_TIMING_QUICK_REFERENCE.txt`
- **Purpose**: Fast lookup during implementation and debugging
- **Format**: Plain text table
- **Best for**: Having open while writing Verilog code
- **Contents**:
  - All timing parameters in tabular format
  - Counter ranges and critical values
  - Verilog code templates
  - Common PLL configurations
  - Debugging checklist

### 2. Complete Specification
**File**: `VGA_TIMING_SPECIFICATION.md`
- **Purpose**: Comprehensive technical reference
- **Format**: Markdown with detailed explanations
- **Best for**: Understanding the standard and design decisions
- **Contents**:
  - Complete VESA standard timing parameters
  - Horizontal and vertical timing breakdown
  - Sync polarity explanations
  - Pixel clock calculations with verification
  - Display Enable (DE) signal generation logic
  - Coordinate calculation formulas
  - Blanking interval explanations with historical context
  - Tolerance specifications
  - Reference Verilog implementation structure
  - Standards compliance information

### 3. Timing Diagrams
**File**: `VGA_TIMING_DIAGRAMS.txt`
- **Purpose**: Visual representation of timing relationships
- **Format**: ASCII art timing diagrams
- **Best for**: Understanding signal relationships and debugging
- **Contents**:
  - Horizontal line timing waveforms
  - Vertical frame timing waveforms
  - Combined frame structure visualization
  - DE signal generation examples
  - State machine region diagrams
  - Coordinate mapping examples
  - Character mode calculations
  - Pixel clock domain timing details

### 4. Verilog Parameters File
**File**: `vga_timing_parameters.vh`
- **Purpose**: Direct inclusion in Verilog/SystemVerilog modules
- **Format**: Verilog header file with `define` macros
- **Best for**: Including in your video_timing.v module
- **Contents**:
  - All timing constants as Verilog defines
  - Helper macros for region detection
  - Character mode parameters
  - Testbench verification values
  - Preprocessor macros for common calculations
  - Example usage code

## Quick Start

### For Implementation
1. Start with the **Quick Reference Card** to get all the numbers
2. Include **vga_timing_parameters.vh** in your Verilog module:
   ```verilog
   `include "vga_timing_parameters.vh"
   ```
3. Reference the **Complete Specification** for detailed explanations

### For Understanding
1. Read the **Complete Specification** for the big picture
2. Study the **Timing Diagrams** for visual understanding
3. Use the **Quick Reference** for quick lookups

### For Debugging
1. Check the **Quick Reference** debugging checklist
2. Compare your waveforms to the **Timing Diagrams**
3. Verify counter values against critical points in the **Specification**

## Key Timing Values Summary

### Horizontal (per line)
- **Active pixels**: 640
- **Front porch**: 16 pixels
- **Sync pulse**: 96 pixels (negative polarity)
- **Back porch**: 48 pixels
- **Total**: 800 pixels (31.778 μs @ 25.175 MHz)

### Vertical (per frame)
- **Active lines**: 480
- **Front porch**: 10 lines
- **Sync pulse**: 2 lines (negative polarity)
- **Back porch**: 33 lines
- **Total**: 525 lines (16.683 ms @ 31.469 kHz)

### Clock and Rates
- **Pixel clock**: 25.175 MHz (standard)
- **Line frequency**: 31.469 kHz
- **Frame rate**: 59.940 Hz

### Critical Points
- **HSYNC**: Negative polarity (LOW = sync, HIGH = idle)
- **VSYNC**: Negative polarity (LOW = sync, HIGH = idle)
- **DE**: HIGH only in visible region (h<640 AND v<480)

## Implementation Checklist

- [ ] Generate 25.175 MHz pixel clock (or close approximation)
- [ ] Implement horizontal counter (0-799)
- [ ] Implement vertical counter (0-524)
- [ ] Generate HSYNC with negative polarity
- [ ] Generate VSYNC with negative polarity
- [ ] Generate Display Enable signal
- [ ] Output pixel coordinates (pixel_x, pixel_y)
- [ ] Verify timing with simulation
- [ ] Test on actual monitor/display

## Verification Points

Your implementation should meet these criteria:

1. **Counter Ranges**:
   - h_count: 0 to 799, wraps at 800
   - v_count: 0 to 524, wraps at 525

2. **Sync Signals** (negative polarity):
   - HSYNC LOW when h_count ∈ [656, 751]
   - VSYNC LOW when v_count ∈ [490, 491]

3. **Display Enable**:
   - DE HIGH when h_count < 640 AND v_count < 480
   - DE LOW at all other times

4. **Timing Frequencies**:
   - Pixel clock: 25.175 MHz ±0.5%
   - Line frequency: 31.469 kHz ±0.5%
   - Frame rate: 59.940 Hz ±1 Hz

## Character Mode Support

For 80×30 text mode with 8×16 pixel characters:

- **Character columns**: 80 (640 ÷ 8)
- **Character rows**: 30 (480 ÷ 16)
- **Total characters**: 2400
- **Character X**: h_count[9:3] (divide by 8)
- **Character Y**: v_count[9:4] (divide by 16)
- **Pixel within char X**: h_count[2:0] (mod 8)
- **Pixel within char Y**: v_count[3:0] (mod 16)

## Common PLL Configurations

Generate 25.175 MHz from common FPGA clock sources:

| Source Clock | PLL Config | Output | Error |
|--------------|------------|--------|-------|
| 50 MHz | ×121 ÷240 | 25.208 MHz | +0.13% |
| 100 MHz | ÷4 | 25.000 MHz | -0.69% |
| 27 MHz | ×28 ÷30 | 25.200 MHz | +0.10% |
| 12 MHz | ×503 ÷240 | 25.150 MHz | -0.10% |

All configurations above are within acceptable tolerance (±0.5%).

## Standards Compliance

This timing specification is based on:
- **VESA DMT** (Display Monitor Timing) Standard v1.0 Rev. 13
- **DMT ID**: 0x04 (640×480 @ 60Hz)
- **Industry standard** VGA timing
- **Compatible with**: VGA, SVGA, DVI, HDMI, DisplayPort

## Related Modules

This timing specification is used by:
- `video_timing.v` - Main timing generator module
- `character_generator.v` - Uses pixel coordinates for character rendering
- `dvi_transmitter.v` - Uses sync signals and DE for DVI encoding
- Video memory controllers - Uses coordinates for addressing

## References

- VESA Display Monitor Timing Standard Version 1.0, Revision 13
- Industry-standard VGA timing (de facto standard since 1987)
- Compatible with modern digital display interfaces (DVI/HDMI/DisplayPort)

## Author Notes

These timing specifications are exact VESA standard values for 640×480 @ 60Hz. While monitors are typically tolerant of small variations (±0.5% on pixel clock, ±1 pixel on timing), staying as close to these standard values as possible ensures maximum compatibility across all displays.

The negative sync polarities are critical - both HSYNC and VSYNC must be active-low to meet the standard. The Display Enable (DE) signal is required for DVI/HDMI but not used in analog VGA.

## Version History

- **v1.0** (2025-12-27): Initial comprehensive documentation
  - Complete VESA standard timing parameters
  - Verilog parameter header file
  - Detailed timing diagrams
  - Quick reference card
  - Implementation examples and verification points

---

*For questions or clarifications about these timing specifications, refer to the VESA DMT standard document or consult the detailed explanations in VGA_TIMING_SPECIFICATION.md.*
