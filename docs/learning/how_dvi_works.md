# How DVI Works: A Practical Guide

**Purpose**: Educational reference for understanding DVI video signal generation on FPGAs
**Target Audience**: Hardware engineers learning about digital video interfaces
**Reference Implementation**: splinedrive/my_hdmi_device for Lattice ECP5 FPGAs

---

## Table of Contents

1. [DVI vs HDMI: What's the Difference?](#dvi-vs-hdmi-whats-the-difference)
2. [TMDS Encoding: The Magic of 8b/10b](#tmds-encoding-the-magic-of-8b10b)
3. [DVI Signal Structure](#dvi-signal-structure)
4. [Clock Relationships: The 10x Rule](#clock-relationships-the-10x-rule)
5. [ECP5 LVDS Primitives](#ecp5-lvds-primitives)
6. [Control Periods vs Video Data Periods](#control-periods-vs-video-data-periods)
7. [Practical Implementation Patterns](#practical-implementation-patterns)
8. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)

---

## DVI vs HDMI: What's the Difference?

### DVI: Digital Visual Interface

DVI is a **video-only** digital interface standard introduced in 1999. Think of it as the pure video transport layer:

- **Video Only**: No audio, no fancy features
- **No Encryption**: No HDCP (High-bandwidth Digital Content Protection)
- **Simpler Protocol**: Just video timing and pixel data
- **Perfect for FPGA Projects**: Less complexity means easier implementation

### HDMI: The Enhanced Cousin

HDMI builds on DVI by adding:

- **Audio**: Multiple channels of digital audio
- **HDCP**: Copy protection (requires licensing)
- **CEC**: Consumer Electronics Control (device control via HDMI cable)
- **Higher Resolutions**: 4K, 8K support in newer versions
- **Metadata**: InfoFrames for color space, aspect ratio, etc.

### The Practical Truth

**DVI signals work over HDMI cables!** The physical connectors and electrical signaling are nearly identical. For FPGA projects, implementing "DVI over HDMI connector" gives you:

- Simple video output without licensing concerns
- Works with most modern monitors (they accept DVI signals)
- Reduces implementation complexity dramatically
- Same great picture quality

**Bottom Line**: For FPGA-based retro computer displays, DVI is the sweet spot.

---

## TMDS Encoding: The Magic of 8b/10b

TMDS stands for **Transition Minimized Differential Signaling**. It's a clever encoding scheme that solves three critical problems in high-speed digital video transmission.

### The Three Problems TMDS Solves

#### Problem 1: Electromagnetic Interference (EMI)

**The Issue**: Rapidly changing digital signals emit radio frequency interference.

**The Solution**: Minimize transitions (bit changes from 0→1 or 1→0).

#### Problem 2: DC Balance

**The Issue**: Differential pairs work best when the average voltage is zero. Too many 1s or 0s creates DC offset.

**The Solution**: Balance the number of 1s and 0s over time (DC balance).

#### Problem 3: Clock Recovery

**The Issue**: How does the receiver know when to sample the data without a separate clock per bit?

**The Solution**: Ensure enough transitions for the receiver's PLL to lock onto.

### How TMDS Encoding Works

TMDS converts 8 bits of pixel data into 10 bits of encoded data through a two-stage process:

#### Stage 1: Transition Minimization

**Goal**: Reduce the number of bit transitions to lower EMI.

**Algorithm**:
```
1. Count the number of '1' bits in the 8-bit input data
2. If count > 4:
   - Use XNOR encoding: bit[n+1] = bit[n] XNOR input[n]
   - This creates fewer transitions when data has many 1s
3. If count <= 4:
   - Use XOR encoding: bit[n+1] = bit[n] XOR input[n]
   - This creates fewer transitions when data has many 0s
4. Set bit 8 of output to indicate which encoding was used
```

**Visual Example**:
```
Input:     10110101 (5 ones - use XNOR)
Process:   Start with bit 0 = input[0] = 1
           bit 1 = 1 XNOR 0 = 1
           bit 2 = 1 XNOR 1 = 0
           bit 3 = 0 XNOR 1 = 1
           ...and so on
Result:    111010100 (9 bits so far, bit 8 = 0 for XNOR)
```

#### Stage 2: DC Balance

**Goal**: Keep equal numbers of 1s and 0s over time.

**Algorithm**:
```
1. Track "running disparity" (cumulative difference between 1s and 0s)
2. Count 1s in the 9-bit word from Stage 1
3. If disparity is positive and word has more 1s:
   - Invert all 9 bits
4. If disparity is negative and word has more 0s:
   - Invert all 9 bits
5. Set bit 9 to indicate if inversion occurred
6. Update running disparity based on final word
```

**The Result**: A 10-bit TMDS symbol that:
- Has fewer transitions than the original 8-bit data
- Maintains long-term DC balance on the differential pair
- Provides enough transitions for reliable clock recovery

### Special Control Symbols

During blanking periods (when no video is being transmitted), TMDS uses special 10-bit control symbols to encode HSYNC and VSYNC signals:

| HSYNC | VSYNC | TMDS Symbol (Channel 0) |
|-------|-------|-------------------------|
| 0     | 0     | 0b1101010100            |
| 1     | 0     | 0b0010101011            |
| 0     | 1     | 0b0101010100            |
| 1     | 1     | 0b1010101011            |

These symbols are specially chosen to:
- Maintain DC balance
- Be easily distinguishable from video data
- Never occur during normal TMDS encoding of pixel data

---

## DVI Signal Structure

DVI transmits video using **four differential pairs** (8 wires total):

### The Four Differential Pairs

#### 1. TMDS Data Channel 0 (Blue)
- Transmits blue pixel data during active video
- Transmits control signals (HSYNC/VSYNC) during blanking
- Uses TMDS encoding

#### 2. TMDS Data Channel 1 (Green)
- Transmits green pixel data during active video
- Transmits control signals during blanking
- Uses TMDS encoding

#### 3. TMDS Data Channel 2 (Red)
- Transmits red pixel data during active video
- Transmits control signals during blanking
- Uses TMDS encoding

#### 4. TMDS Clock Channel
- Transmits the pixel clock directly (not encoded)
- Runs at the pixel clock frequency (e.g., 25.175 MHz for 640x480@60Hz)
- Provides timing reference for data recovery

### Why Differential Pairs?

Differential signaling offers several advantages:

1. **Noise Immunity**: External interference affects both wires equally, canceling out
2. **Lower EMI**: Opposite signals on paired wires cancel electromagnetic emissions
3. **Higher Speed**: Can run faster than single-ended signals
4. **Longer Cables**: Reliable over several meters

**How It Works**: One wire carries the signal, the other carries the inverted signal. The receiver looks at the voltage difference between the two wires.

```
Wire A: ─┐  ┌─┐  ┌─
         └──┘ └──┘

Wire B: ┐  ┌─┐  ┌─┐
        └──┘ └──┘

Voltage Difference (A-B) = Digital Signal
```

---

## Clock Relationships: The 10x Rule

Understanding the clock domains is crucial for DVI implementation.

### Three Clock Domains

#### 1. Pixel Clock
- **Frequency**: Determined by video mode (25.175 MHz for 640x480@60Hz)
- **Purpose**: Times the generation of each pixel
- **Drives**: Video timing generators, pixel data multiplexers

#### 2. TMDS Bit Clock
- **Frequency**: 10x the pixel clock (251.75 MHz for 640x480@60Hz)
- **Purpose**: Serializes the 10-bit TMDS symbols
- **Why 10x?**: Because each TMDS symbol has 10 bits!

#### 3. TMDS Clock Output
- **Frequency**: Same as pixel clock (25.175 MHz)
- **Purpose**: Provides timing reference for the receiver
- **Not Encoded**: Transmitted directly as differential clock

### The 10x Serialization Rule

Here's the math:

```
For 640x480@60Hz:
- Pixel Clock: 25.175 MHz
- Each pixel needs: 8 bits red + 8 bits green + 8 bits blue = 24 bits
- TMDS encoding: 8 bits → 10 bits
- Each pixel transmits: 10 bits red + 10 bits green + 10 bits blue = 30 bits
- Bit rate per channel: 25.175 MHz × 10 = 251.75 Mbps
- Total bandwidth: 3 channels × 251.75 Mbps = 755.25 Mbps
```

### Clock Generation with PLLs

FPGAs use Phase-Locked Loops (PLLs) to generate these clocks from a reference oscillator:

**Example for ECP5 FPGA**:
```
Input: 25 MHz oscillator
PLL Configuration:
  - Output 1 (Pixel Clock): 25.175 MHz (multiply by 121, divide by 120)
  - Output 2 (TMDS Bit Clock): 251.75 MHz (multiply by 121, divide by 12)
```

**Critical**: Both clocks must be phase-aligned to avoid timing issues!

---

## ECP5 LVDS Primitives

Lattice ECP5 FPGAs provide specialized primitives for high-speed differential signaling.

### EHXPLLL: The PLL Primitive

**Purpose**: Generate multiple synchronized clock frequencies from a single reference.

**Key Parameters**:
```verilog
EHXPLLL #(
    .CLKI_DIV(1),        // Input clock divider
    .CLKFB_DIV(5),       // Feedback divider (multiplier)
    .CLKOP_DIV(8),       // Primary output divider
    .CLKOS_DIV(40),      // Secondary output divider
    .FEEDBK_PATH("CLKOP") // Feedback path selection
) pll_inst (
    .CLKI(clk_25mhz),    // Input clock
    .CLKOP(clk_tmds),    // Output clock 1 (125 MHz for DDR approach)
    .CLKOS(clk_pixel),   // Output clock 2 (25 MHz)
    .LOCK(pll_locked)    // PLL lock indicator
);
```

**VCO Constraint**: The internal VCO frequency must be between 400-800 MHz.

**Formula**:
```
VCO_freq = Input_freq × (CLKFB_DIV / CLKI_DIV)
Output_freq = VCO_freq / CLKOP_DIV
```

### ODDRX2F: Output DDR Primitive (4:1 Serialization)

**Purpose**: Convert 4 bits of parallel data into 2 bits of DDR (Double Data Rate) output.

**How It Works**:
- Takes 4 input bits (D0, D1, D2, D3)
- Outputs 2 bits per clock cycle using both rising and falling edges
- Effectively multiplies the data rate by 2

**Verilog Instantiation**:
```verilog
ODDRX2F oddr_inst (
    .D0(tmds_bit[0]),    // Bit 0 (output on falling edge)
    .D1(tmds_bit[1]),    // Bit 1 (output on rising edge)
    .D2(tmds_bit[2]),    // Bit 2 (output on falling edge, next cycle)
    .D3(tmds_bit[3]),    // Bit 3 (output on rising edge, next cycle)
    .SCLK(clk_tmds),     // Serialization clock (125 MHz for DDR)
    .RST(reset),         // Reset signal
    .Q(tmds_out)         // DDR output to differential pair
);
```

**Timing Diagram**:
```
Clock:   ___╱‾╲_╱‾╲_╱‾╲_╱‾╲___

D0-D3:   [D0][D1][D2][D3]

Output:    D0  D1  D2  D3
           ↓   ↓   ↓   ↓
         __|‾|_|‾|_|‾|_|‾|__
           ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
          Fall Rise Fall Rise
```

### ODDRX1F: Output DDR Primitive (2:1 Serialization)

**Purpose**: Convert 2 bits of parallel data into DDR output.

**When to Use**:
- Higher clock frequencies (250 MHz instead of 125 MHz)
- More straightforward for simple applications
- May be easier to meet timing constraints in some designs

**Verilog Instantiation**:
```verilog
ODDRX1F oddr_inst (
    .D0(tmds_bit[0]),    // Bit 0 (output on falling edge)
    .D1(tmds_bit[1]),    // Bit 1 (output on rising edge)
    .SCLK(clk_tmds),     // Serialization clock (250 MHz for SDR equivalent)
    .RST(reset),         // Reset signal
    .Q(tmds_out)         // DDR output
);
```

### Two Implementation Approaches

#### Approach 1: DDR with ODDRX1F (Recommended)

**Clocks**:
- Pixel clock: 25 MHz
- TMDS clock: 125 MHz (5x pixel clock)

**Advantages**:
- Lower clock frequency (easier timing closure)
- More reliable across FPGA speed grades
- Standard approach used in reference implementations

**How It Works**:
- Send 10-bit TMDS symbol over 5 clock cycles
- Each cycle outputs 2 bits (rising and falling edge)
- 5 cycles × 2 bits = 10 bits per symbol

#### Approach 2: SDR with ODDRX2F (Alternative)

**Clocks**:
- Pixel clock: 25 MHz
- TMDS clock: 250 MHz (10x pixel clock)

**Advantages**:
- Simpler conceptually
- Uses more common primitive

**Disadvantages**:
- Higher clock frequency (challenging for timing closure)
- May not work on slower FPGA speed grades

---

## Control Periods vs Video Data Periods

DVI transmission alternates between two modes during each frame.

### Video Data Period (Active Video)

**When**: During the visible portion of the video frame

**What Happens**:
- Each data channel transmits TMDS-encoded pixel data
- Channel 0: Blue pixel data (8 bits → 10 bits)
- Channel 1: Green pixel data (8 bits → 10 bits)
- Channel 2: Red pixel data (8 bits → 10 bits)
- All three channels synchronized to the pixel clock

**Display Enable Signal**: A signal (often called `video_active` or `display_enable`) indicates when we're in the active video region.

**Example Logic**:
```verilog
wire video_active = (h_count < H_VISIBLE) && (v_count < V_VISIBLE);

// During active video, encode pixel data
assign tmds_data_ch0 = video_active ? tmds_encode(blue)  : control_symbols;
assign tmds_data_ch1 = video_active ? tmds_encode(green) : control_symbols;
assign tmds_data_ch2 = video_active ? tmds_encode(red)   : control_symbols;
```

### Control Period (Blanking)

**When**: During horizontal and vertical blanking intervals

**What Happens**:
- Channel 0 transmits control symbols encoding HSYNC and VSYNC
- Channels 1 and 2 transmit fixed control symbols
- No pixel data transmitted (blanking = black)

**Control Symbol Encoding**:

The four possible combinations of HSYNC and VSYNC are encoded into specific 10-bit patterns on Channel 0:

```verilog
// Control symbol lookup (transmitted on Channel 0 during blanking)
case ({vsync, hsync})
    2'b00: control_symbol = 10'b1101010100;
    2'b01: control_symbol = 10'b0010101011;
    2'b10: control_symbol = 10'b0101010100;
    2'b11: control_symbol = 10'b1010101011;
endcase
```

### Timing Diagram Example (640x480@60Hz)

```
Horizontal Line:
┌────────────┬─────┬──────┬──────┬──────────────┐
│ Active     │Front│ Sync │ Back │   Active     │
│ Video      │Porch│Pulse │Porch │   Video      │
│ 640 pixels │16 px│96 px │48 px │  640 pixels  │
│ (Data)     │(Ctl)│(Ctl) │(Ctl) │  (Data)      │
└────────────┴─────┴──────┴──────┴──────────────┘
     ↑                ↑
   video_active    HSYNC

Vertical Frame:
┌─────────────────────────────────┐
│ Active Video (480 lines)        │ ← Transmit pixel data
│ (video_active = 1)              │
├─────────────────────────────────┤
│ Vertical Front Porch (10 lines) │ ← Control period
├─────────────────────────────────┤
│ Vertical Sync (2 lines)         │ ← VSYNC asserted
├─────────────────────────────────┤
│ Vertical Back Porch (33 lines)  │ ← Control period
└─────────────────────────────────┘
```

---

## Practical Implementation Patterns

Let's walk through a complete implementation based on the reference code patterns.

### Module Hierarchy

A typical DVI implementation has this structure:

```
dvi_top.v
├── video_timing.v        (Generates H/V sync, counters, video_active)
├── pixel_source.v        (Generates RGB pixel data - e.g., test pattern)
├── tmds_encoder.v (×3)   (One encoder per color channel)
├── tmds_serializer.v (×3) (ODDRX2F instantiation per channel)
├── tmds_clock_out.v      (ODDRX2F for clock channel)
└── pll.v                 (EHXPLLL for clock generation)
```

### Step 1: Video Timing Generator

**Purpose**: Generate horizontal and vertical counters, sync pulses, and video_active signal.

**Key Outputs**:
- `h_count`: Horizontal pixel counter (0-799 for 640x480)
- `v_count`: Vertical line counter (0-524 for 640x480)
- `hsync`: Horizontal sync pulse
- `vsync`: Vertical sync pulse
- `video_active`: High during visible portion (h < 640 && v < 480)

**Example Implementation**:
```verilog
module video_timing (
    input wire clk_pixel,
    input wire reset,
    output reg [9:0] h_count,
    output reg [9:0] v_count,
    output reg hsync,
    output reg vsync,
    output wire video_active
);
    // 640x480@60Hz parameters
    localparam H_VISIBLE = 640;
    localparam H_FRONT   = 16;
    localparam H_SYNC    = 96;
    localparam H_BACK    = 48;
    localparam H_TOTAL   = 800;

    localparam V_VISIBLE = 480;
    localparam V_FRONT   = 10;
    localparam V_SYNC    = 2;
    localparam V_BACK    = 33;
    localparam V_TOTAL   = 525;

    // Horizontal counter
    always @(posedge clk_pixel) begin
        if (reset) begin
            h_count <= 0;
        end else if (h_count == H_TOTAL - 1) begin
            h_count <= 0;
        end else begin
            h_count <= h_count + 1;
        end
    end

    // Vertical counter
    always @(posedge clk_pixel) begin
        if (reset) begin
            v_count <= 0;
        end else if (h_count == H_TOTAL - 1) begin
            if (v_count == V_TOTAL - 1) begin
                v_count <= 0;
            end else begin
                v_count <= v_count + 1;
            end
        end
    end

    // Sync signals (negative polarity for 640x480)
    always @(posedge clk_pixel) begin
        hsync <= ~((h_count >= H_VISIBLE + H_FRONT) &&
                   (h_count < H_VISIBLE + H_FRONT + H_SYNC));
        vsync <= ~((v_count >= V_VISIBLE + V_FRONT) &&
                   (v_count < V_VISIBLE + V_FRONT + V_SYNC));
    end

    // Video active flag
    assign video_active = (h_count < H_VISIBLE) && (v_count < V_VISIBLE);
endmodule
```

### Step 2: TMDS Encoder

**Purpose**: Convert 8-bit pixel data to 10-bit TMDS symbols.

**Key Features**:
- Implements two-stage encoding (transition minimization + DC balance)
- Handles control symbols during blanking
- Maintains running disparity

**Simplified Implementation** (see reference for complete version):
```verilog
module tmds_encoder (
    input wire clk,
    input wire [7:0] data,      // Pixel data (R, G, or B)
    input wire video_active,    // Video active flag
    input wire [1:0] ctrl,      // Control signals (HSYNC/VSYNC for channel 0)
    output reg [9:0] tmds_out   // 10-bit TMDS symbol
);
    reg signed [4:0] disparity = 0;  // Running disparity tracker

    always @(posedge clk) begin
        if (!video_active) begin
            // Control period - output control symbols
            case (ctrl)
                2'b00: tmds_out <= 10'b1101010100;
                2'b01: tmds_out <= 10'b0010101011;
                2'b10: tmds_out <= 10'b0101010100;
                2'b11: tmds_out <= 10'b1010101011;
            endcase
            disparity <= 0;  // Reset disparity during blanking
        end else begin
            // Video period - encode pixel data
            // Stage 1: Transition minimization
            // Stage 2: DC balance
            // (Full implementation follows DVI spec, see reference code)
            // ...
        end
    end
endmodule
```

### Step 3: TMDS Serializer

**Purpose**: Serialize 10-bit TMDS symbols to DDR output.

**Implementation with ODDRX1F** (DDR approach, 5x clock):
```verilog
module tmds_serializer (
    input wire clk_pixel,        // 25 MHz pixel clock
    input wire clk_tmds,         // 125 MHz TMDS clock (5x pixel)
    input wire [9:0] tmds_data,  // 10-bit TMDS symbol
    output wire tmds_out_p,      // TMDS output (positive)
    output wire tmds_out_n       // TMDS output (negative)
);
    reg [9:0] shift_reg;
    reg [2:0] bit_counter;

    // Load shift register on pixel clock
    always @(posedge clk_pixel) begin
        shift_reg <= tmds_data;
    end

    // Serialize on TMDS clock
    always @(posedge clk_tmds) begin
        bit_counter <= bit_counter + 1;
        if (bit_counter == 4) begin  // After 5 cycles (0-4), reload
            bit_counter <= 0;
        end
    end

    // DDR output primitive
    ODDRX1F oddr_inst (
        .D0(shift_reg[bit_counter * 2]),
        .D1(shift_reg[bit_counter * 2 + 1]),
        .SCLK(clk_tmds),
        .RST(1'b0),
        .Q(tmds_out_p)
    );

    // Negative output is inverted
    assign tmds_out_n = ~tmds_out_p;
endmodule
```

### Step 4: Top-Level Integration

**Purpose**: Connect all modules and instantiate differential outputs.

**Example Structure**:
```verilog
module dvi_top (
    input wire clk_25mhz,
    output wire tmds_clk_p,
    output wire tmds_clk_n,
    output wire tmds_d0_p,  // Blue
    output wire tmds_d0_n,
    output wire tmds_d1_p,  // Green
    output wire tmds_d1_n,
    output wire tmds_d2_p,  // Red
    output wire tmds_d2_n
);
    // Clock generation
    wire clk_pixel, clk_tmds, pll_locked;
    pll_video pll (
        .clk_in(clk_25mhz),
        .clk_pixel(clk_pixel),
        .clk_tmds(clk_tmds),
        .locked(pll_locked)
    );

    // Video timing
    wire [9:0] h_count, v_count;
    wire hsync, vsync, video_active;
    video_timing timing (
        .clk_pixel(clk_pixel),
        .reset(~pll_locked),
        .h_count(h_count),
        .v_count(v_count),
        .hsync(hsync),
        .vsync(vsync),
        .video_active(video_active)
    );

    // Pixel generation (e.g., test pattern)
    wire [7:0] red, green, blue;
    test_pattern pattern (
        .h_count(h_count),
        .v_count(v_count),
        .video_active(video_active),
        .red(red),
        .green(green),
        .blue(blue)
    );

    // TMDS encoding
    wire [9:0] tmds_ch0, tmds_ch1, tmds_ch2;
    tmds_encoder enc0 (.data(blue),  .ctrl({vsync, hsync}), .tmds_out(tmds_ch0), ...);
    tmds_encoder enc1 (.data(green), .ctrl(2'b00), .tmds_out(tmds_ch1), ...);
    tmds_encoder enc2 (.data(red),   .ctrl(2'b00), .tmds_out(tmds_ch2), ...);

    // TMDS serialization
    tmds_serializer ser0 (.tmds_data(tmds_ch0), .tmds_out_p(tmds_d0_p), ...);
    tmds_serializer ser1 (.tmds_data(tmds_ch1), .tmds_out_p(tmds_d1_p), ...);
    tmds_serializer ser2 (.tmds_data(tmds_ch2), .tmds_out_p(tmds_d2_p), ...);

    // TMDS clock output (not encoded, direct pixel clock)
    tmds_clock_out clk_out (.clk_pixel(clk_pixel), .tmds_clk_p(tmds_clk_p), ...);
endmodule
```

### Step 5: Pin Constraints

**Purpose**: Map internal signals to physical FPGA pins.

**Example LPF (Lattice Preference File) for Colorlight i5**:
```lpf
## HDMI Output (GPDI Connector) ##
LOCATE COMP "tmds_clk_p" SITE "J19";
LOCATE COMP "tmds_d0_p" SITE "G19";  # Blue
LOCATE COMP "tmds_d1_p" SITE "E20";  # Green
LOCATE COMP "tmds_d2_p" SITE "C20";  # Red

IOBUF PORT "tmds_clk_p" IO_TYPE=LVCMOS33D DRIVE=4;
IOBUF PORT "tmds_d0_p" IO_TYPE=LVCMOS33D DRIVE=4;
IOBUF PORT "tmds_d1_p" IO_TYPE=LVCMOS33D DRIVE=4;
IOBUF PORT "tmds_d2_p" IO_TYPE=LVCMOS33D DRIVE=4;

## Clock Frequency Constraints ##
FREQUENCY PORT "clk_pixel" 25 MHZ;
FREQUENCY PORT "clk_tmds" 125 MHZ;
```

**Important Note on LVCMOS33D**:
- The `D` suffix means differential mode
- Only specify the positive pin (_p) in constraints
- The negative pin (_n) is automatically assigned by the tools
- DO NOT manually assign negative pins!

---

## Common Pitfalls and Solutions

### Pitfall 1: Case Sensitivity in Primitive Names

**Problem**: Instantiating primitives with lowercase names fails synthesis.

**Wrong**:
```verilog
oddrx1f my_oddr (...);  // Will NOT work!
```

**Correct**:
```verilog
ODDRX1F my_oddr (...);  // All caps required
```

**Why**: Yosys (the open-source synthesis tool) requires exact case matching for ECP5 primitives.

**Solution**: Always use UPPERCASE for ECP5 primitives: `ODDRX1F`, `ODDRX2F`, `EHXPLLL`, etc.

### Pitfall 2: Clock Domain Crossing Issues

**Problem**: Passing signals directly between pixel clock and TMDS clock domains causes metastability.

**Symptom**: Random bit errors, unstable image, occasional glitches.

**Solution**: Use proper synchronization techniques:

**Option A: Dual-Clock FIFO**
```verilog
// Write side (pixel clock domain)
always @(posedge clk_pixel) begin
    if (video_active) begin
        fifo_write <= 1;
        fifo_din <= {red, green, blue};
    end
end

// Read side (TMDS clock domain)
always @(posedge clk_tmds) begin
    if (!fifo_empty) begin
        fifo_read <= 1;
        {red_sync, green_sync, blue_sync} <= fifo_dout;
    end
end
```

**Option B: Carefully Timed Handshaking** (used in reference implementation)
- Load TMDS shift registers on pixel clock edge
- Ensure timing constraint that shift register is stable before TMDS clock samples it
- Requires careful timing analysis

### Pitfall 3: Differential Pair Negative Pin Assignment

**Problem**: Manually assigning both positive and negative differential pins causes conflicts.

**Wrong**:
```lpf
LOCATE COMP "tmds_d0_p" SITE "G19";
LOCATE COMP "tmds_d0_n" SITE "G20";  # Don't do this!
```

**Correct**:
```lpf
LOCATE COMP "tmds_d0_p" SITE "G19";
# Negative pin automatically assigned by IO_TYPE=LVCMOS33D
```

**Why**: The LVCMOS33D IO type tells the tools this is a differential pair. The tools automatically assign the complementary pin based on the FPGA's differential pair routing.

### Pitfall 4: PLL Lock Ignored

**Problem**: Starting video output before PLL locks causes garbage on screen.

**Symptom**: No display, or unstable image that stabilizes after a few seconds.

**Solution**: Always wait for PLL lock signal:
```verilog
wire pll_locked;
EHXPLLL pll (..., .LOCK(pll_locked), ...);

// Reset video logic until PLL is locked
wire video_reset = ~pll_locked;

video_timing timing (
    .reset(video_reset),
    ...
);
```

### Pitfall 5: Wrong Sync Polarity

**Problem**: Display shows nothing or distorted image.

**Cause**: VGA timing standards specify sync polarity (positive or negative).

**For 640x480@60Hz**: Both HSYNC and VSYNC are **negative polarity** (active LOW).

**Correct Implementation**:
```verilog
// Sync pulse is LOW during sync period, HIGH otherwise
assign hsync = ~((h_count >= H_VISIBLE + H_FRONT) &&
                 (h_count < H_VISIBLE + H_FRONT + H_SYNC));
```

**Check Your Timing Spec**: Different resolutions have different sync polarities!

### Pitfall 6: Not Constraining Clock Frequencies

**Problem**: Tools don't optimize timing, resulting in setup/hold violations.

**Symptom**: Design works in simulation but fails on hardware, or works intermittently.

**Solution**: Always add frequency constraints in your LPF file:
```lpf
FREQUENCY PORT "clk_pixel" 25 MHZ;
FREQUENCY PORT "clk_tmds" 125 MHZ;
```

**Also Check**: Timing reports from NextPNR to ensure all timing is met with positive slack.

### Pitfall 7: Running Disparity Not Reset

**Problem**: Artifacts appear at the start of each line or after long blanking.

**Cause**: TMDS disparity tracker not reset during blanking periods.

**Solution**: Reset disparity to 0 during control periods:
```verilog
always @(posedge clk_pixel) begin
    if (!video_active) begin
        disparity <= 0;  // Reset during blanking
    end else begin
        // Update disparity during active video
    end
end
```

---

## Conclusion and Next Steps

You now understand:

1. **DVI vs HDMI**: DVI is simpler, royalty-free, and perfect for FPGA projects
2. **TMDS Encoding**: How 8b/10b encoding reduces EMI and maintains DC balance
3. **Signal Structure**: Four differential pairs (3 data + 1 clock)
4. **Clock Relationships**: The critical 10x relationship between pixel and bit clocks
5. **ECP5 Primitives**: How to use ODDRX1F/ODDRX2F and EHXPLLL for implementation
6. **Control vs Data Periods**: When to transmit pixels vs sync signals
7. **Practical Patterns**: Complete module hierarchy from reference code
8. **Common Pitfalls**: What to watch out for (case sensitivity, clock domains, differential pairs)

### Recommended Learning Path

1. **Study Reference Code**: Clone and examine `splinedrive/my_hdmi_device`
2. **Build Test Pattern**: Start with simple color bars to validate hardware
3. **Verify Timing**: Use logic analyzer or oscilloscope to check signal integrity
4. **Add Character Display**: Once basic DVI works, add character rendering
5. **Optimize**: Pipeline character lookup, use block RAM efficiently

### Further Reading

- **DVI 1.0 Specification**: Complete TMDS encoding tables and timing requirements
- **Lattice ECP5 Family Datasheet**: Primitive specifications and timing parameters
- **VESA DMT Standard**: Detailed timing for all standard video modes
- **Reference Implementation**: splinedrive/my_hdmi_device on GitHub

---

**Document Version**: 1.0
**Last Updated**: 2025-12-28
**Target Hardware**: Lattice ECP5 (Colorlight i5)
**Reference**: splinedrive/my_hdmi_device

---

**Happy Hardware Hacking!**
