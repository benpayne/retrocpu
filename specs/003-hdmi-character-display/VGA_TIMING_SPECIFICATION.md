# VGA 640x480 @ 60Hz Timing Specification

Complete VESA standard timing parameters for implementing video_timing.v module for DVI transmitter.

## Standard Overview

- **Resolution**: 640 x 480 pixels
- **Refresh Rate**: 59.940 Hz (typically specified as 60 Hz)
- **Pixel Clock**: 25.175 MHz (industry standard)
- **Horizontal Line Frequency**: 31.469 kHz
- **Total Pixels per Frame**: 800 × 525 = 420,000 pixels

## 1. Horizontal Timing Parameters

| Parameter | Symbol | Value | Unit | Description |
|-----------|--------|-------|------|-------------|
| Active Video | Ha | 640 | pixels | Visible horizontal pixels |
| Front Porch | Hfp | 16 | pixels | Blank pixels after active video |
| Sync Pulse | Hs | 96 | pixels | Horizontal sync pulse width |
| Back Porch | Hbp | 48 | pixels | Blank pixels before active video |
| Total Line Time | Ht | 800 | pixels | Total horizontal period |
| Blanking Period | Hblank | 160 | pixels | Hfp + Hs + Hbp |

### Horizontal Sync Polarity
- **HSYNC Polarity**: Negative (Active Low)
- HSYNC goes LOW during the sync pulse period
- HSYNC is HIGH during active video and porch periods

### Horizontal Timing Breakdown (pixel clock cycles)
```
Pixel:        0                 640  656           752           800
             |-------------------|---|-------------|-------------|
Phase:       | Active Video      |Hfp|  H Sync     | Back Porch  |
HSYNC:       |     HIGH          |HIGH|    LOW     |    HIGH     |
DE:          |     HIGH          |LOW |    LOW     |    LOW      |
Duration:    |   640 pixels      | 16 |  96 pixels |  48 pixels  |
```

### Horizontal Time Calculations
- **Line Period**: 800 / 25.175 MHz = 31.778 μs
- **Active Video Time**: 640 / 25.175 MHz = 25.422 μs
- **Horizontal Blanking**: 160 / 25.175 MHz = 6.356 μs
- **Line Frequency**: 25.175 MHz / 800 = 31.469 kHz

## 2. Vertical Timing Parameters

| Parameter | Symbol | Value | Unit | Description |
|-----------|--------|-------|------|-------------|
| Active Lines | Va | 480 | lines | Visible vertical lines |
| Front Porch | Vfp | 10 | lines | Blank lines after active video |
| Sync Pulse | Vs | 2 | lines | Vertical sync pulse width |
| Back Porch | Vbp | 33 | lines | Blank lines before active video |
| Total Frame Lines | Vt | 525 | lines | Total vertical period |
| Blanking Period | Vblank | 45 | lines | Vfp + Vs + Vbp |

### Vertical Sync Polarity
- **VSYNC Polarity**: Negative (Active Low)
- VSYNC goes LOW during the sync pulse period
- VSYNC is HIGH during active video and porch periods

### Vertical Timing Breakdown (horizontal lines)
```
Line:         0                 480 490    492              525
             |-------------------|---|------|----------------|
Phase:       | Active Video      |Vfp|Vsync | Back Porch     |
VSYNC:       |     HIGH          |HIGH| LOW  |     HIGH       |
DE:          | HIGH (per line)   |LOW | LOW  |     LOW        |
Duration:    |   480 lines       | 10 | 2    |   33 lines     |
```

### Vertical Time Calculations
- **Frame Period**: 525 / 31.469 kHz = 16.683 ms
- **Active Frame Time**: 480 / 31.469 kHz = 15.253 ms
- **Vertical Blanking**: 45 / 31.469 kHz = 1.430 ms
- **Frame Rate**: 31.469 kHz / 525 = 59.940 Hz

## 3. Sync Signal Polarities

Both sync signals use **negative polarity**:

| Signal | Active Level | Idle Level |
|--------|--------------|------------|
| HSYNC | LOW (0) | HIGH (1) |
| VSYNC | LOW (0) | HIGH (1) |

## 4. Pixel Clock Calculation & Verification

### Pixel Clock Frequency
```
Pixel Clock = Horizontal Total × Vertical Total × Frame Rate
            = 800 × 525 × 59.940 Hz
            = 25,175,040 Hz
            = 25.175 MHz (standard)
```

### Frame Rate Verification
```
Frame Rate = Pixel Clock / (Horizontal Total × Vertical Total)
           = 25.175 MHz / (800 × 525)
           = 25,175,000 / 420,000
           = 59.940 Hz
```

### Practical Clock Generation
The exact 25.175 MHz pixel clock is often approximated in practice:
- **Ideal**: 25.175 MHz (VESA standard)
- **Common approximations**: 25.0 MHz or 25.2 MHz
- **Tolerance**: Monitors typically accept ±0.5% deviation

## 5. Display Enable (DE) Signal Generation

The Display Enable (DE) signal indicates when valid pixel data should be output.

### DE Signal Rules
```verilog
// Horizontal DE: Active during visible pixel region
h_display_enable = (h_count >= 0) && (h_count < 640)

// Vertical DE: Active during visible line region
v_display_enable = (v_count >= 0) && (v_count < 480)

// Combined DE: Both horizontal and vertical must be active
display_enable = h_display_enable && v_display_enable
```

### DE Signal Characteristics
- DE is HIGH only during the active video region (640×480)
- DE is LOW during all blanking intervals:
  - Horizontal blanking (front porch, sync, back porch)
  - Vertical blanking (front porch, sync, back porch)
- Pixel data should only be output when DE is HIGH
- RGB data is ignored when DE is LOW

## 6. Timing Counter Implementation

### Horizontal Counter
```verilog
// h_count: 0 to 799 (800 total states)
reg [9:0] h_count;  // 10 bits for 0-799

always @(posedge pixel_clk) begin
    if (h_count == 799)
        h_count <= 0;
    else
        h_count <= h_count + 1;
end

// Horizontal sync generation
assign hsync = ~((h_count >= 656) && (h_count < 752));  // Negative polarity

// Horizontal display enable
assign h_de = (h_count < 640);
```

### Vertical Counter
```verilog
// v_count: 0 to 524 (525 total states)
reg [9:0] v_count;  // 10 bits for 0-524

always @(posedge pixel_clk) begin
    if (h_count == 799) begin  // Increment at end of each line
        if (v_count == 524)
            v_count <= 0;
        else
            v_count <= v_count + 1;
    end
end

// Vertical sync generation
assign vsync = ~((v_count >= 490) && (v_count < 492));  // Negative polarity

// Vertical display enable
assign v_de = (v_count < 480);
```

### Combined Display Enable
```verilog
assign display_enable = h_de && v_de;
```

## 7. Coordinate Calculation from Counters

### Pixel Address Calculation
```verilog
// X coordinate (0-639 when valid)
wire [9:0] pixel_x = h_count;  // Valid when h_count < 640

// Y coordinate (0-479 when valid)
wire [9:0] pixel_y = v_count;  // Valid when v_count < 480

// Linear pixel address for framebuffer
wire [18:0] pixel_addr = (pixel_y * 640) + pixel_x;  // 0 to 307,199
```

### Character Cell Calculation (for text mode)
For 80×30 character display (8×16 pixel characters):
```verilog
// Character position
wire [6:0] char_x = pixel_x[9:3];  // Divide by 8: 0-79
wire [4:0] char_y = pixel_y[9:4];  // Divide by 16: 0-29

// Pixel within character cell
wire [2:0] char_pixel_x = pixel_x[2:0];  // 0-7
wire [3:0] char_pixel_y = pixel_y[3:0];  // 0-15

// Character buffer address (80×30 = 2400 characters)
wire [11:0] char_addr = (char_y * 80) + char_x;
```

## 8. Blanking Interval Explanations

### Horizontal Blanking
The horizontal blanking interval (160 pixels) occurs at the end of each scanline:

1. **Front Porch (16 pixels)**: Brief delay after active video ends
   - Allows analog signals to settle
   - Prevents video artifacts at line edges
   - Duration: 635.6 ns

2. **Sync Pulse (96 pixels)**: HSYNC goes LOW
   - Signals monitor to start horizontal retrace
   - CRT beam returns to left edge of screen
   - Duration: 3.813 μs

3. **Back Porch (48 pixels)**: Delay before next active video
   - Allows beam positioning to stabilize
   - Historical timing for CRT retrace completion
   - Duration: 1.907 μs

### Vertical Blanking
The vertical blanking interval (45 lines) occurs at the end of each frame:

1. **Front Porch (10 lines)**: Brief delay after last active line
   - Duration: 317.78 μs (10 × 31.778 μs)

2. **Sync Pulse (2 lines)**: VSYNC goes LOW
   - Signals monitor to start vertical retrace
   - CRT beam returns to top of screen
   - Duration: 63.56 μs (2 × 31.778 μs)

3. **Back Porch (33 lines)**: Delay before next frame
   - Allows beam positioning to stabilize
   - Duration: 1.049 ms (33 × 31.778 μs)

### Purpose of Blanking Intervals
- **CRT Legacy**: Originally designed for CRT electron beam retrace
- **Modern Digital**: Still required by VESA standards for compatibility
- **Signal Integrity**: Provides time for signal settling and synchronization
- **No Data Transfer**: RGB/pixel data is ignored during blanking

## 9. Tolerance Specifications

### Pixel Clock Tolerance
- **Nominal**: 25.175 MHz
- **Typical Range**: 25.0 MHz to 25.2 MHz accepted by most monitors
- **VESA Tolerance**: ±0.5% is generally acceptable
- **Minimum**: ~25.05 MHz
- **Maximum**: ~25.30 MHz

### Timing Tolerances
Most VGA monitors are forgiving of small timing variations:
- **Horizontal timing**: ±1-2 pixels typically acceptable
- **Vertical timing**: ±1 line typically acceptable
- **Frame rate**: 59-61 Hz range usually works
- **Sync pulse width**: Can vary by ±10% in practice

### Critical Parameters
These parameters should be kept as close to standard as possible:
- Total horizontal pixels (800)
- Total vertical lines (525)
- Sync pulse polarities (both negative)
- Active region size (640×480)

## 10. Timing Diagrams

### Complete Horizontal Line Timing
```
Pixel Clock: _|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_
             (25.175 MHz)

H_Count:     0................639|640...655|656.......751|752.....799|0
             |<--- Active ------>|<- Hfp ->|<-- Sync --->|<- Hbp --->|

HSYNC:       ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾____‾‾‾‾‾‾‾‾‾‾‾
             (Negative polarity - LOW during sync)

H_DE:        ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾____________________________
             (HIGH only during active video)

RGB Data:    [Pixel 0][Pixel 1]...[Pixel 639][Black/Ignored............]
```

### Complete Vertical Frame Timing
```
Line Clock:  _|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_
             (31.469 kHz - one pulse per H line)

V_Count:     0................479|480...489|490.491|492.......524|0
             |<--- Active ------>|<- Vfp ->|<Sync>|<--- Vbp --->|

VSYNC:       ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾___‾‾‾‾‾‾‾‾‾‾‾‾‾
             (Negative polarity - LOW during sync)

V_DE:        ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾____________________________
             (HIGH only during active lines)
```

### Single Pixel Timing Detail
```
Pixel Clock:     _|‾‾‾|___|‾‾‾|___|‾‾‾|___
                 39.72 ns period (25.175 MHz)

Data Valid:      |<--- Stable --->|
                    (setup/hold around clock edge)

DE Signal:       ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ (during active region)

RGB Output:      [Pixel N Data   ]
```

### Frame Structure Visualization
```
Frame = 525 lines × 31.778 μs/line = 16.683 ms (59.940 Hz)

Line 0    |██████████████████████████████████████| <- Active video (480 lines)
Line 1    |██████████████████████████████████████|
...       |██████████████████████████████████████|
Line 479  |██████████████████████████████████████|
Line 480  |______________________________________| <- Front porch (10 lines)
Line 481  |______________________________________|
...       |______________________________________|
Line 489  |______________________________________|
Line 490  |======================================| <- Vsync (2 lines)
Line 491  |======================================|
Line 492  |--------------------------------------| <- Back porch (33 lines)
Line 493  |--------------------------------------|
...       |--------------------------------------|
Line 524  |--------------------------------------|
          Repeat to Line 0

Legend:
██ = Active video (DE high, VSYNC high)
__ = Vertical front porch (DE low, VSYNC high)
== = Vertical sync (DE low, VSYNC low)
-- = Vertical back porch (DE low, VSYNC high)
```

## 11. State Machine for Video Timing Generator

### State Definitions
```verilog
// Horizontal states
localparam H_ACTIVE     = 2'b00;  // Pixels 0-639
localparam H_FRONT      = 2'b01;  // Pixels 640-655
localparam H_SYNC       = 2'b10;  // Pixels 656-751
localparam H_BACK       = 2'b11;  // Pixels 752-799

// Vertical states
localparam V_ACTIVE     = 2'b00;  // Lines 0-479
localparam V_FRONT      = 2'b01;  // Lines 480-489
localparam V_SYNC       = 2'b10;  // Lines 490-491
localparam V_BACK       = 2'b11;  // Lines 492-524
```

### Reference Implementation Structure
```verilog
module video_timing (
    input wire clk_25mhz,      // 25.175 MHz pixel clock
    input wire reset,

    // Sync outputs
    output reg hsync,          // Horizontal sync (negative)
    output reg vsync,          // Vertical sync (negative)
    output reg display_enable, // Display enable (active high)

    // Position outputs
    output reg [9:0] h_count,  // 0-799
    output reg [9:0] v_count,  // 0-524
    output wire [9:0] pixel_x, // 0-639 (valid when DE=1)
    output wire [9:0] pixel_y  // 0-479 (valid when DE=1)
);
```

## 12. Quick Reference Table

### All Timing Parameters
| Parameter | Horizontal | Vertical | Unit |
|-----------|------------|----------|------|
| Active | 640 | 480 | pixels/lines |
| Front Porch | 16 | 10 | pixels/lines |
| Sync Pulse | 96 | 2 | pixels/lines |
| Back Porch | 48 | 33 | pixels/lines |
| Total | 800 | 525 | pixels/lines |
| Blanking | 160 | 45 | pixels/lines |
| Sync Polarity | Negative | Negative | - |
| Frequency | 31.469 kHz | 59.940 Hz | - |

### Key Counter Values
| Event | H_Count | V_Count |
|-------|---------|---------|
| Active video start | 0 | 0 |
| Active video end | 639 | 479 |
| Front porch start | 640 | 480 |
| Sync pulse start | 656 | 490 |
| Sync pulse end | 751 | 491 |
| Back porch start | 752 | 492 |
| Counter reset | 799 | 524 |

### Signal States Summary
| Region | HSYNC | VSYNC | H_DE | V_DE | DE |
|--------|-------|-------|------|------|-----|
| Active video | HIGH | HIGH | HIGH | HIGH | HIGH |
| H front porch | HIGH | HIGH | LOW | HIGH/LOW | LOW |
| H sync pulse | LOW | HIGH | LOW | HIGH/LOW | LOW |
| H back porch | HIGH | HIGH | LOW | HIGH/LOW | LOW |
| V front porch | varies | HIGH | varies | LOW | LOW |
| V sync pulse | varies | LOW | varies | LOW | LOW |
| V back porch | varies | HIGH | varies | LOW | LOW |

## References and Standards

This specification is based on the VESA (Video Electronics Standards Association) DMT (Display Monitor Timing) standard for 640x480 @ 60Hz, which is the industry-standard VGA timing mode supported by virtually all monitors.

### Standards Documentation
- VESA Display Monitor Timing Standard Version 1.0, Revision 13
- VESA DMT ID: 0x04 (640x480 @ 60Hz)
- CEA-861 compatibility for digital displays

### Implementation Notes
1. This timing is compatible with both analog VGA and digital DVI/HDMI interfaces
2. The DE signal is required for DVI/HDMI but not used in analog VGA
3. For DVI implementation, ensure pixel data is synchronized to the pixel clock
4. Consider using ODDR (Output Double Data Rate) primitives for sync signals if needed
5. The 25.175 MHz clock can be generated using FPGA PLLs/DCMs from various input clocks

### Common FPGA Clock Generation
From 50 MHz input:
- Multiply by 121, divide by 240 → 25.208 MHz (0.13% error)
- Acceptable for most monitors

From 100 MHz input:
- Divide by 4 → 25.0 MHz (0.69% error)
- Acceptable for most monitors

From 27 MHz input:
- Multiply by 28, divide by 30 → 25.2 MHz (0.10% error)
- Excellent accuracy

---

*Document Version: 1.0*
*Last Updated: 2025-12-27*
*For use with: video_timing.v module implementation*
