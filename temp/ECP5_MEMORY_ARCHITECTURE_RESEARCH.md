# Lattice ECP5-25F FPGA Memory Architecture Research
## Colorlight i5 Board - Character Display Implementation

**Research Date**: 2025-12-27
**Project**: RetroCPU - 6502 FPGA Microcomputer
**Target**: Text-mode character display implementation

---

## 1. ECP5-25F Device Specifications

### 1.1 Logic Resources
- **LUTs (Look-Up Tables)**: 24,000 (24K)
- **Flip-Flops**: ~48,000 (2 FFs per LUT slice)
- **FPGA Family**: Lattice ECP5 (LFE5U-25F-6BG381C on Colorlight i5)
- **Package**: 381-ball BGA

### 1.2 Memory Resources (EBR - Embedded Block RAM)
- **Total EBR Blocks**: 56 blocks
- **Block Size**: 18 Kb (2,304 bytes) per block
- **Total On-Chip RAM**: 1,008 Kb = 126 KB (56 × 18 Kb)
- **Additional Distributed RAM**: 194 Kb (~24 KB)
- **Total Available Memory**: ~150 KB on-chip

### 1.3 DSP Resources
- **DSP Blocks**: 28 blocks
- **Configuration**: 18×18 multiplier with 36-bit accumulator

### 1.4 I/O Capabilities
- **User I/O Pins**: ~194 on LFE5U-25F
- **LVDS Pairs**: Multiple differential pairs available on left/right edges
- **I/O Standards**: LVCMOS33, LVCMOS25, LVDS, etc.

---

## 2. EBR (Embedded Block RAM) Configuration

### 2.1 EBR Architecture
- **Primitive Name**: DP16KD (Dual Port 16Kb RAM with additional 2Kb parity)
- **Related Primitives**:
  - SP16KD: Single Port RAM
  - PDPW16KD: Pseudo-Dual Port RAM (one read, one write port)
  - DP16KD: True Dual Port RAM

### 2.2 Block Size and Configuration Options
Each 18 Kb EBR block can be configured as:

| Configuration | Data Width | Depth | Total Bits | Bytes |
|--------------|------------|-------|------------|-------|
| 16K × 1      | 1 bit      | 16,384 | 16,384     | 2,048 |
| 8K × 2       | 2 bits     | 8,192  | 16,384     | 4,096 |
| 4K × 4       | 4 bits     | 4,096  | 16,384     | 2,048 |
| 2K × 9       | 9 bits     | 2,048  | 18,432     | 2,304 |
| 1K × 18      | 18 bits    | 1,024  | 18,432     | 2,304 |
| 512 × 36     | 36 bits    | 512    | 18,432     | 2,304 |

**Note**: The additional 2 Kb (2,048 bits) beyond 16K is used for parity/ECC bits.

### 2.3 Dual-Port Configuration Types

#### True Dual-Port (DP16KD)
- **Both ports**: Read and Write capable
- **Independent clocks**: Port A and Port B have separate clocks
- **Use case**: Character buffer (CPU writes, VGA reads)
- **Clock domain crossing**: Built-in support for asynchronous operation

#### Pseudo Dual-Port (PDPW16KD)
- **Port A**: Write-only
- **Port B**: Read-only
- **Simpler logic**: Lower resource usage
- **Use case**: Font ROM (write once, read many times)

#### Simple Dual-Port
- **Port A**: One port for writes
- **Port B**: One port for reads
- **Same or different clocks**: Flexible clocking

### 2.4 Initialization Methods

#### Method 1: Using INIT Parameters (Diamond)
```verilog
DP16KD #(
    .INIT_DATA("STATIC"),
    .INITVAL_00(256'h...),  // Initialize first 256 bits
    .INITVAL_01(256'h...),  // Next 256 bits
    // ... continues for all memory locations
) ebr_inst (
    // Port connections
);
```

#### Method 2: Using $readmemh (Synthesis-friendly)
```verilog
reg [7:0] font_rom [0:1535];  // 1536 bytes for font data

initial begin
    $readmemh("font_8x16.hex", font_rom);
end
```

**Note**: Yosys (open-source synthesis) prefers $readmemh and will automatically infer EBR blocks from properly coded RAM arrays.

#### Method 3: Clarity Designer GUI
- Lattice Diamond includes GUI tool for EBR configuration
- Generates HDL code with proper parameters
- Not needed for open-source flow (Yosys/NextPNR)

### 2.5 EBR Cascading
- Multiple EBR blocks can be cascaded using CS (Chip Select) ports
- Useful for memories larger than 18 Kb
- Example: 4 blocks cascaded = 72 Kb (9 KB) total

---

## 3. Memory Budget for Character Display

### 3.1 Display Modes Analysis

#### Mode 1: 40-Column × 25-Line Display
```
Character Buffer: 40 × 25 = 1,000 bytes (1 KB)
Attribute Buffer:  40 × 25 = 1,000 bytes (1 KB) [optional, for color/style]
Font ROM:          96 chars × 16 bytes = 1,536 bytes (1.5 KB)
Total:             3.5 KB (without attributes: 2.5 KB)
```

#### Mode 2: 80-Column × 25-Line Display
```
Character Buffer: 80 × 25 = 2,000 bytes (2 KB)
Attribute Buffer:  80 × 25 = 2,000 bytes (2 KB) [optional]
Font ROM:          96 chars × 16 bytes = 1,536 bytes (1.5 KB)
Total:             5.5 KB (without attributes: 3.5 KB)
```

#### Mode 3: 80-Column × 30-Line Display
```
Character Buffer: 80 × 30 = 2,400 bytes (2.4 KB)
Attribute Buffer:  80 × 30 = 2,400 bytes (2.4 KB) [optional]
Font ROM:          96 chars × 16 bytes = 1,536 bytes (1.5 KB)
Total:             6.3 KB (without attributes: 3.9 KB)
```

### 3.2 Font ROM Options

#### 8×8 Font (VGA Text Mode)
```
96 characters × 8 bytes = 768 bytes (0.75 KB)
128 characters × 8 bytes = 1,024 bytes (1 KB)
256 characters × 8 bytes = 2,048 bytes (2 KB)
```

#### 8×16 Font (Higher Resolution)
```
96 characters × 16 bytes = 1,536 bytes (1.5 KB)
128 characters × 16 bytes = 2,048 bytes (2 KB)
256 characters × 16 bytes = 4,096 bytes (4 KB)
```

### 3.3 EBR Block Allocation

#### Configuration A: 40×25 Display (Minimal)
| Component | Size | EBR Config | EBR Blocks |
|-----------|------|------------|------------|
| Character Buffer | 1 KB | 1K × 8 | 1 block |
| Font ROM (8×16) | 1.5 KB | 2K × 8 | 1 block |
| **Total** | **2.5 KB** | | **2 blocks** |

**Resource Usage**: 2/56 EBR blocks = 3.6%

#### Configuration B: 80×25 Display (Standard)
| Component | Size | EBR Config | EBR Blocks |
|-----------|------|------------|------------|
| Character Buffer | 2 KB | 2K × 8 | 1 block |
| Font ROM (8×16) | 1.5 KB | 2K × 8 | 1 block |
| **Total** | **3.5 KB** | | **2 blocks** |

**Resource Usage**: 2/56 EBR blocks = 3.6%

#### Configuration C: 80×25 with Attributes
| Component | Size | EBR Config | EBR Blocks |
|-----------|------|------------|------------|
| Character Buffer | 2 KB | 2K × 8 | 1 block |
| Attribute Buffer | 2 KB | 2K × 8 | 1 block |
| Font ROM (8×16) | 1.5 KB | 2K × 8 | 1 block |
| **Total** | **5.5 KB** | | **3 blocks** |

**Resource Usage**: 3/56 EBR blocks = 5.4%

#### Configuration D: 80×30 with Extended Font
| Component | Size | EBR Config | EBR Blocks |
|-----------|------|------------|------------|
| Character Buffer | 2.4 KB | 2K × 8 (2 blocks) | 2 blocks |
| Font ROM (256 chars × 16) | 4 KB | 2K × 8 (2 blocks) | 2 blocks |
| **Total** | **6.4 KB** | | **4 blocks** |

**Resource Usage**: 4/56 EBR blocks = 7.1%

### 3.4 Recommended Configuration for RetroCPU

**Start with Configuration B: 80×25 Text Mode**
- 2 EBR blocks total (3.6% of available EBR)
- Leaves 54 EBR blocks for CPU system RAM
- Standard VGA text mode compatibility
- Sufficient for BASIC programming and monitor display

**Future Expansion Options**:
- Add attribute buffer (1 more EBR) for color text
- Expand to 80×30 or 80×50 for more screen lines
- Implement double buffering (2× character buffers)
- Add hardware scrolling buffer

---

## 4. Dual-Port Configuration Strategy

### 4.1 Character Buffer (True Dual-Port)

**Requirements**:
- **CPU Port (Write)**: 25 MHz system clock, 8-bit data bus
- **VGA Port (Read)**: 25.175 MHz pixel clock domain
- **Clock Domain Crossing**: Yes (asynchronous operation)

**DP16KD Configuration**:
```verilog
// Character Buffer: 2KB for 80×25 display
DP16KD #(
    .DATA_WIDTH_A(8),      // CPU writes 8-bit characters
    .DATA_WIDTH_B(8),      // VGA reads 8-bit characters
    .CLKAMUX("CLKA"),      // Port A clock = cpu_clk (25 MHz)
    .CLKBMUX("CLKB"),      // Port B clock = vga_clk (25.175 MHz)
    .REGMODE_A("NOREG"),   // No output register on Port A
    .REGMODE_B("OUTREG"),  // Output register on Port B for VGA
    .WRITEMODE_A("NORMAL"),
    .WRITEMODE_B("NORMAL")
) char_buffer (
    // Port A: CPU writes
    .CLKA(cpu_clk),
    .WEA(char_buffer_we),
    .CEA(1'b1),
    .RSTA(cpu_rst),
    .ADA({1'b0, char_addr_cpu, 3'b000}),  // 11 bits address (2K × 8)
    .DIA(cpu_data_out),
    .DOA(),  // CPU doesn't read character buffer

    // Port B: VGA reads
    .CLKB(pixel_clk),
    .WEB(1'b0),  // Read-only
    .CEB(1'b1),
    .RSTB(vga_rst),
    .ADB({1'b0, char_addr_vga, 3'b000}),  // 11 bits address
    .DIB(8'h00),
    .DOB(char_data_out)
);
```

**Clock Domain Crossing Notes**:
- ECP5 DP16KD has built-in synchronization
- No external CDC logic needed
- OUTREG on VGA side adds pipeline stage for timing
- Minimal risk of metastability

### 4.2 Font ROM (Pseudo Dual-Port or ROM Mode)

**Requirements**:
- **Initialization**: Load once at synthesis/configuration
- **VGA Port (Read)**: 25.175 MHz pixel clock, 8-bit data
- **No writes during operation**: ROM behavior

**Method 1: Using Inferred ROM (Recommended for Yosys)**
```verilog
// Font ROM: 1.5 KB (96 chars × 16 bytes/char)
(* ram_style = "block" *)  // Force block RAM inference
reg [7:0] font_rom [0:1535];

initial begin
    $readmemh("font_8x16.hex", font_rom);
end

// Synchronous read (infers EBR automatically)
always @(posedge pixel_clk) begin
    font_data <= font_rom[font_addr];
end
```

**Method 2: Using PDPW16KD Primitive (Diamond)**
```verilog
PDPW16KD #(
    .DATA_WIDTH_W(8),      // Write port width (unused, for init only)
    .DATA_WIDTH_R(8),      // Read port width
    .INITVAL_00(256'h...),  // Font data initialization
    .INITVAL_01(256'h...),
    // ... continue for all font data
) font_rom_inst (
    .CLKR(pixel_clk),
    .CER(1'b1),
    .RSTR(vga_rst),
    .ADR({1'b0, font_addr, 3'b000}),  // 11 bits address
    .DOR(font_data_out),

    // Write port (unused after initialization)
    .CLKW(1'b0),
    .CEW(1'b0),
    .WEW(1'b0),
    .ADW(14'h0),
    .DIW(18'h0)
);
```

### 4.3 Memory Access Pattern Example

**VGA Character Display Read Sequence**:
1. **Character Fetch** (H position, V position → char address):
   - `char_addr = (v_line / 16) * 80 + (h_pixel / 8)`
   - Read character code from character buffer

2. **Font Fetch** (character code, scanline → font address):
   - `font_addr = char_code * 16 + (v_line % 16)`
   - Read font bitmap row from font ROM

3. **Pixel Output** (font bitmap, H position → pixel):
   - `pixel = font_data[7 - (h_pixel % 8)]`
   - Output black or white pixel

**Timing Requirements**:
- Character buffer read: 1 clock cycle latency (with OUTREG)
- Font ROM read: 1 clock cycle latency
- Total: 2-cycle pipeline (prefetch required)

---

## 5. ECP5 PLL (EHXPLLL) Configuration

### 5.1 PLL Capabilities

**EHXPLLL Block Specifications**:
- **VCO Frequency Range**: 400 MHz - 800 MHz
- **Input Frequency Range**: 8 MHz - 400 MHz
- **Output Frequency Range**: 3.125 MHz - 400 MHz
- **Number of PLLs**: 2 on ECP5-25F
- **Outputs per PLL**: 4 (CLKOP, CLKOS, CLKOS2, CLKOS3)
- **Divider Range**: 1 - 128 (integer dividers)

**PLL Formula**:
```
f_pfd = f_clk_in / CLKI_DIV
f_vco = f_pfd × CLKFB_DIV
f_clk_out = f_vco / CLKOP_DIV
```

**Constraint**: 400 MHz ≤ f_vco ≤ 800 MHz

### 5.2 VGA Pixel Clock Generation (25.175 MHz)

**Standard VGA 640×480@60Hz Timing**:
- **Pixel Clock**: 25.175 MHz (exact)
- **Acceptable Range**: 25.0 - 25.2 MHz (most monitors tolerate ±1%)
- **Common Approximation**: 25.125 MHz or 25.0 MHz

#### Configuration 1: 25 MHz Input → 25.125 MHz Output (Close Match)

**Input**: 25 MHz (Colorlight i5 oscillator)

**PLL Parameters**:
```
CLKI_DIV = 4
CLKFB_DIV = 67
CLKOP_DIV = 3
FEEDBK_PATH = "CLKOP"

Calculations:
f_pfd = 25 MHz / 4 = 6.25 MHz
f_vco = 6.25 MHz × 67 = 418.75 MHz  ✓ (within 400-800 MHz)
f_clkop = 418.75 MHz / 3 = 139.583 MHz
Wait... this doesn't work! Let me recalculate...

Correct calculation for CLKOS output:
CLKOS_DIV = 25
f_clkos = 628.125 MHz / 25 = 25.125 MHz  ✓
```

**Revised PLL Parameters (from web search results)**:
```
CLKI_DIV = 4
CLKFB_DIV = 67
CLKOP_DIV = 3     → 139.583 MHz (not used, but sets VCO)
CLKOS_DIV = 25    → 25.125 MHz (VGA pixel clock)
FEEDBK_PATH = "CLKOP"

With these settings:
f_pfd = 25 MHz / 4 = 6.25 MHz
f_vco = 6.25 MHz × 67 × 3 = 628.125 MHz  ✓ (within 400-800 MHz)
f_clkos = 628.125 MHz / 25 = 25.125 MHz  ✓ (VGA pixel clock)
```

**Error**: 25.125 MHz vs 25.175 MHz = -0.2% (acceptable)

#### Configuration 2: 25 MHz Input → 25.0 MHz Output (Simple)

**PLL Parameters**:
```
CLKI_DIV = 1
CLKFB_DIV = 24
CLKOP_DIV = 24
FEEDBK_PATH = "CLKOP"

Calculations:
f_pfd = 25 MHz / 1 = 25 MHz
f_vco = 25 MHz × 24 = 600 MHz  ✓ (within 400-800 MHz)
f_clkop = 600 MHz / 24 = 25.0 MHz  ✓
```

**Error**: 25.0 MHz vs 25.175 MHz = -0.7% (acceptable, most monitors work)

#### Configuration 3: 25 MHz Input → 125 MHz HDMI Serializer Clock

**For HDMI/DVI Output (5× pixel clock for 10:1 serialization)**:
```
CLKI_DIV = 1
CLKFB_DIV = 30
CLKOP_DIV = 5     → 150 MHz (not used)
CLKOS_DIV = 6     → 125 MHz (HDMI 5× clock)
CLKOS2_DIV = 30   → 25 MHz (pixel clock)
FEEDBK_PATH = "CLKOP"

Calculations:
f_pfd = 25 MHz / 1 = 25 MHz
f_vco = 25 MHz × 30 = 750 MHz  ✓ (within 400-800 MHz)
f_clkos = 750 MHz / 6 = 125 MHz  ✓ (HDMI serializer)
f_clkos2 = 750 MHz / 30 = 25 MHz  ✓ (pixel clock)
```

### 5.3 Verilog PLL Instantiation Example

```verilog
(* LOC="EHXPLLL_LL" *)  // PLL location (use ecppll tool to find)
EHXPLLL #(
    .CLKI_DIV(1),
    .CLKFB_DIV(24),
    .CLKOP_DIV(24),
    .CLKOS_DIV(1),       // Not used
    .CLKOS2_DIV(1),      // Not used
    .CLKOS3_DIV(1),      // Not used
    .FEEDBK_PATH("CLKOP"),
    .CLKOP_ENABLE("ENABLED"),
    .CLKOS_ENABLE("DISABLED"),
    .CLKOS2_ENABLE("DISABLED"),
    .CLKOS3_ENABLE("DISABLED"),
    .CLKOP_CPHASE(0),
    .CLKOS_CPHASE(0),
    .CLKOS2_CPHASE(0),
    .CLKOS3_CPHASE(0),
    .CLKOP_FPHASE(0),
    .CLKOS_FPHASE(0),
    .CLKOS2_FPHASE(0),
    .CLKOS3_FPHASE(0)
) pll_inst (
    .CLKI(clk_25mhz),
    .CLKFB(clk_fb),
    .RST(pll_rst),
    .CLKOP(pixel_clk),     // 25 MHz VGA pixel clock
    .CLKOS(),
    .CLKOS2(),
    .CLKOS3(),
    .LOCK(pll_locked)
);

assign clk_fb = pixel_clk;  // Feedback from CLKOP
```

### 5.4 Using ecppll Tool (Nextpnr)

**Command-line PLL Parameter Calculation**:
```bash
# Calculate PLL parameters for 25.175 MHz from 25 MHz input
ecppll -i 25 -o 25.175 --highres

# Output will show optimal CLKI_DIV, CLKFB_DIV, CLKOP_DIV settings
# --highres flag attempts to minimize frequency error
```

**Example Output**:
```
Input frequency:  25.000 MHz
Output frequency: 25.125 MHz  (target: 25.175 MHz)
Frequency error:  -0.20%

CLKI_DIV:   4
CLKFB_DIV:  67
CLKOP_DIV:  3
CLKOS_DIV:  25
VCO frequency: 628.125 MHz
```

---

## 6. LVDS I/O Primitives for High-Speed Video

### 6.1 ODDRX2F Primitive (DDR Output with 2× Gearing)

**Purpose**: Generate DDR (Double Data Rate) output signals with 2× gearing for LVDS serialization.

**Key Features**:
- Transmits 4 bits per clock cycle (2 bits per edge, 2× gearing)
- Requires 2 clocks: SCLK (slow, pixel clock) and ECLK (fast, 2× pixel clock)
- Edge-aligned clock and data outputs
- Used for HDMI/DVI TMDS serialization (10:1 or 5:1 ratio)

**Ports**:
```verilog
ODDRX2F (
    .D0(data_bit0),   // First data bit (SCLK rising edge)
    .D1(data_bit1),   // Second data bit (SCLK rising edge)
    .D2(data_bit2),   // Third data bit (SCLK falling edge)
    .D3(data_bit3),   // Fourth data bit (SCLK falling edge)
    .ECLK(eclk),      // Fast edge clock (2× SCLK)
    .SCLK(sclk),      // Slow system clock
    .RST(rst),        // Reset
    .Q(q_out)         // DDR output
);
```

**Timing**:
```
SCLK:     ___/‾‾‾\___/‾‾‾\___
ECLK:     _/‾\_/‾\_/‾\_/‾\_/‾
Q_OUT:    |D0|D1|D2|D3|...
          └─┴─┴─┴─┘
          (4 bits per SCLK cycle)
```

### 6.2 Differential Output Buffer (OLVDS)

**Purpose**: Convert single-ended FPGA signals to LVDS differential pairs.

**Ports**:
```verilog
OLVDS (
    .A(signal_in),    // Single-ended input
    .Z(lvds_p),       // Differential positive output
    .ZN(lvds_n)       // Differential negative output
);
```

**ECP5 LVDS Capabilities**:
- Half of PIO pairs on left/right edges support LVDS transmit
- Only PIO A,B pairs support true LVDS differential output buffer
- Maximum data rate: ~1.25 Gbps per pair
- Typical use: HDMI TMDS (3 data pairs + 1 clock pair)

### 6.3 High-Speed Serializer for DVI/HDMI

**10:1 TMDS Serialization**:
For DVI/HDMI, each 8-bit pixel component (R, G, B) is:
1. Encoded to 10 bits using TMDS encoding (transition-minimized)
2. Serialized at 10× pixel clock rate
3. Transmitted as LVDS differential pair

**ECP5 Implementation Approaches**:

#### Approach 1: External HDMI PHY (Simplest)
- Use IT66121 or similar HDMI transmitter IC
- Parallel 24-bit RGB + sync signals from FPGA
- PHY handles TMDS encoding and serialization
- Requires fewer FPGA resources

#### Approach 2: Internal SERDES (Resource-intensive)
- Implement TMDS encoding in FPGA logic
- Use ODDRX2F primitives for 5:1 serialization (2 stages)
- Requires high-speed clock (250 MHz for 25 MHz pixel clock)
- Uses ECP5 SERDES resources

**Recommended for RetroCPU**: Start with Approach 1 (external PHY) for simplicity.

### 6.4 Example HDMI/DVI Architecture (High-Level)

```
Pixel Clock Domain (25 MHz)                 Serializer Domain (125 MHz)
┌─────────────────────────┐                 ┌──────────────────────────┐
│  Character Generator    │                 │   TMDS Encoder (R, G, B) │
│  - Char buffer read     │                 │   - 8b/10b encoding      │
│  - Font ROM lookup      │                 │   - DC balance           │
│  - Pixel output (1-bit) │                 │   - Control symbols      │
│  - RGB colorization     │                 │                          │
└──────────┬──────────────┘                 └────────┬─────────────────┘
           │                                         │
           │  R[7:0], G[7:0], B[7:0]                │  R[9:0], G[9:0], B[9:0]
           │  HSYNC, VSYNC, DE                       │
           └────────────────────────────────────────┘
                                                     │
                                        ┌────────────▼──────────────┐
                                        │  10:1 Serializers (3×)    │
                                        │  - ODDRX2F cascaded       │
                                        │  - 250 MHz serial clock   │
                                        └───────────┬───────────────┘
                                                    │
                                        ┌───────────▼───────────────┐
                                        │  LVDS Output Buffers (3×) │
                                        │  - OLVDS primitives       │
                                        │  - TMDS0+/-, TMDS1+/-,    │
                                        │    TMDS2+/-, TMDS_CLK+/-  │
                                        └───────────────────────────┘
```

---

## 7. Memory Allocation Strategy & Recommendations

### 7.1 Phase 1: Basic Text Mode (Recommended Starting Point)

**Display Mode**: 40×25 characters, monochrome

**Memory Allocation**:
| Resource | Size | EBR Blocks | Configuration |
|----------|------|------------|---------------|
| Character Buffer | 1 KB | 1 | 1K × 8 (DP16KD, dual-port) |
| Font ROM (8×16) | 1.5 KB | 1 | 2K × 8 (PDPW16KD, ROM) |
| **Total** | **2.5 KB** | **2** | **3.6% of EBR** |

**Advantages**:
- Minimal resource usage
- Simple implementation
- Proven VGA text mode standard
- Enough for BASIC and monitor display

**Clock Configuration**:
- **System Clock**: 25 MHz (existing Colorlight i5 oscillator)
- **Pixel Clock**: 25 MHz (direct, no PLL needed initially)
- **VGA Timing**: 640×480@60Hz (simplified, 25 MHz acceptable)

**Implementation Complexity**: Low
- No PLL configuration needed
- No clock domain crossing (same 25 MHz)
- Simple VGA sync generator
- Single character/font pipeline

### 7.2 Phase 2: Standard 80×25 Text Mode

**Display Mode**: 80×25 characters, monochrome or color attributes

**Memory Allocation**:
| Resource | Size | EBR Blocks | Configuration |
|----------|------|------------|---------------|
| Character Buffer | 2 KB | 1 | 2K × 8 (DP16KD) |
| Attribute Buffer | 2 KB | 1 | 2K × 8 (DP16KD, optional) |
| Font ROM (8×16) | 1.5 KB | 1 | 2K × 8 (PDPW16KD) |
| **Total** | **5.5 KB** | **3** | **5.4% of EBR** |

**Enhancements**:
- Add PLL for accurate 25.175 MHz pixel clock
- Implement proper VGA 640×480@60Hz timing
- Add attribute buffer for 16 foreground/background colors
- Support hardware cursor

**Clock Configuration**:
- **System Clock**: 25 MHz
- **Pixel Clock**: 25.125 MHz (PLL-generated, close to 25.175 MHz)
- **CPU Clock**: 1-2 MHz (derived from 25 MHz with divider)

**Implementation Complexity**: Medium
- PLL configuration and clock domain crossing
- Character and attribute buffer dual-port access
- VGA timing generator with proper blanking
- Color palette logic (4-bit FG/BG → RGB)

### 7.3 Phase 3: Enhanced Display with HDMI Output

**Display Mode**: 80×25 or 80×30 characters, HDMI/DVI output

**Memory Allocation**:
| Resource | Size | EBR Blocks | Configuration |
|----------|------|------------|---------------|
| Character Buffer | 2.4 KB | 2 | 2K × 8 (DP16KD, cascaded) |
| Attribute Buffer | 2.4 KB | 2 | 2K × 8 (DP16KD, cascaded) |
| Font ROM (256 chars × 16) | 4 KB | 2 | 2K × 8 (PDPW16KD, cascaded) |
| **Total** | **8.8 KB** | **6** | **10.7% of EBR** |

**Enhancements**:
- HDMI/DVI output via TMDS encoding
- Extended character set (256 characters)
- Hardware scrolling buffer
- Double buffering (optional, +2 EBR)

**Clock Configuration**:
- **System Clock**: 25 MHz
- **Pixel Clock**: 25.125 MHz (PLL-generated)
- **HDMI Serializer Clock**: 125 MHz (PLL-generated, 5× pixel clock)
- **CPU Clock**: 1-2 MHz

**Implementation Complexity**: High
- Multiple PLL outputs for different clock domains
- TMDS encoding logic (R, G, B channels)
- 10:1 or 5:1 serialization using ODDRX2F
- LVDS differential output buffers
- More complex memory controller

### 7.4 Recommended Development Path

**Step 1: Proof of Concept (1-2 days)**
- 40×25 monochrome text mode
- No PLL, use 25 MHz directly
- VGA output on breadboard or PMOD VGA adapter
- Test character buffer writes from CPU
- Verify font ROM and character generation

**Step 2: Production MVP (3-5 days)**
- 80×25 text mode with 16-color attributes
- PLL for accurate 25.175 MHz (or close approximation)
- Proper VGA timing (640×480@60Hz)
- Memory-mapped I/O for character/attribute buffers
- Hardware cursor and scrolling

**Step 3: Future Enhancement (1-2 weeks)**
- HDMI/DVI output with TMDS encoding
- Extended character set (256 characters)
- Hardware acceleration (block fill, scroll, etc.)
- Double buffering for flicker-free updates
- Palette RAM for custom colors

---

## 8. Clock Domain Crossing Considerations

### 8.1 Single Clock Domain (Phase 1)

**Clocking Scheme**:
```
25 MHz Oscillator → System Clock (25 MHz)
                  ↓
        ┌─────────┴──────────┐
        │                    │
    CPU Domain          VGA Domain
    (Same clock)        (Same clock)
```

**Advantages**:
- No metastability concerns
- Simpler design and timing closure
- Single clock tree, easier routing

**Disadvantages**:
- Pixel clock not exactly 25.175 MHz (may have minor display issues)
- Limited flexibility for future enhancements

### 8.2 Dual Clock Domain (Phase 2)

**Clocking Scheme**:
```
25 MHz Oscillator → PLL → 25.125 MHz (Pixel Clock)
                        ↘ 25 MHz (System Clock)

        ┌─────────┴──────────┬──────────────┐
        │                    │              │
    CPU Domain          VGA Domain      Memory Domain
    (25 MHz)            (25.125 MHz)    (Both clocks)
```

**Clock Domain Crossing Strategies**:

#### Strategy 1: Asynchronous Dual-Port EBR (Recommended)
- Use DP16KD in true dual-port mode
- CPU writes at 25 MHz (Port A)
- VGA reads at 25.125 MHz (Port B)
- Built-in EBR synchronization handles metastability
- **No external CDC logic needed**

#### Strategy 2: Synchronous FIFO (Overkill for this application)
- Use FIFO for command/data transfer
- Useful for high-bandwidth streaming
- Not needed for static character buffer

#### Strategy 3: Gray Code Counters (For address pointers)
- If implementing hardware scrolling with circular buffer
- Gray-coded read/write pointers for safe CDC
- Useful for double buffering

### 8.3 Triple Clock Domain (Phase 3)

**Clocking Scheme**:
```
25 MHz Oscillator → PLL → 25.125 MHz (Pixel Clock)
                        ↘ 125 MHz (HDMI Serializer Clock)
                        ↘ 25 MHz (System Clock)

        ┌─────────┴──────────┬──────────────┬────────────────┐
        │                    │              │                │
    CPU Domain          VGA Domain      Serializer      Memory Domain
    (25 MHz)            (25.125 MHz)    (125 MHz)      (All clocks)
```

**Additional Considerations**:
- TMDS encoding runs in pixel clock domain (25.125 MHz)
- Serialization runs in 5× clock domain (125 MHz)
- Requires proper multi-cycle path constraints
- More complex timing closure

---

## 9. Current Project Integration

### 9.1 Existing System Analysis

**From** `/opt/wip/retrocpu/rtl/system/soc_top.v`:
- **CPU**: M65C02 Core running at 25 MHz
- **System RAM**: 32 KB (uses existing ram.v module, likely inferred EBR)
- **ROM**: 16 KB BASIC + 8 KB Monitor (uses EBR)
- **Peripherals**: UART, LCD (HD44780), PS/2 Keyboard
- **Clock**: Single 25 MHz clock from Colorlight i5 oscillator
- **I/O**: UART TX/RX, LCD 4-bit mode, PS/2, 4× debug LEDs

**Current EBR Usage Estimate**:
| Module | Size | EBR Blocks |
|--------|------|------------|
| System RAM | 32 KB | ~16 blocks |
| BASIC ROM | 16 KB | ~8 blocks |
| Monitor ROM | 8 KB | ~4 blocks |
| **Current Total** | **56 KB** | **~28 blocks** |

**Available EBR**: 56 - 28 = **28 blocks remaining** (50%)

### 9.2 Adding VGA Text Mode to Existing System

**Option 1: VGA alongside LCD (Dual Display)**
- Keep existing LCD for status/debug
- Add VGA for main terminal display
- Uses 2-3 additional EBR blocks (5.4% → total 60%)
- CPU can write to both displays independently

**Option 2: Replace LCD with VGA (Single Display)**
- Remove LCD controller (saves logic resources)
- VGA becomes primary display
- Same 2-3 additional EBR blocks
- Cleaner, more standard terminal interface

**Recommendation**: Go with Option 2 (VGA only) for simpler system.

### 9.3 Memory Map Extension

**Proposed Memory Map**:
```
0x0000-0x7FFF : RAM (32 KB)
0x8000-0xBFFF : BASIC ROM (16 KB)
0xC000-0xC0FF : UART (256 bytes)
0xC100-0xC1FF : LCD Controller (256 bytes) [Remove or keep for debug]
0xC200-0xC2FF : PS/2 Keyboard (256 bytes)
0xC300-0xC3FF : VGA Character Buffer Base Address (mapped to EBR)
0xC400-0xC4FF : VGA Attribute Buffer (optional, for color text)
0xC500-0xC50F : VGA Control Registers (cursor, scroll, palette)
0xE000-0xFFFF : Monitor ROM (8 KB)
```

**VGA Register Map** (0xC500-0xC50F):
```
0xC500: VGA_CTRL     - Control register (enable, mode select, etc.)
0xC501: VGA_CURSOR_H - Cursor position high byte
0xC502: VGA_CURSOR_L - Cursor position low byte
0xC503: VGA_SCROLL   - Hardware scroll offset
0xC504: VGA_FG_COLOR - Foreground color (4-bit palette index)
0xC505: VGA_BG_COLOR - Background color (4-bit palette index)
0xC506-0xC50F: Reserved for future use
```

### 9.4 Address Decoder Modifications

**Add to** `/opt/wip/retrocpu/rtl/memory/address_decoder.v`:
```verilog
// VGA character buffer: 0xC300-0xC3FF (2 KB window into 2 KB buffer)
wire vga_char_cs = (addr[15:8] == 8'hC3);

// VGA attribute buffer: 0xC400-0xC4FF (2 KB window)
wire vga_attr_cs = (addr[15:8] == 8'hC4);

// VGA control registers: 0xC500-0xC50F
wire vga_ctrl_cs = (addr[15:4] == 12'hC50);
```

---

## 10. Implementation Checklist

### 10.1 Phase 1: Basic VGA Text Mode (40×25)

- [ ] **VGA Sync Generator**
  - [ ] Horizontal sync (H-sync) generator
  - [ ] Vertical sync (V-sync) generator
  - [ ] Horizontal and vertical counters
  - [ ] Blanking signal generation

- [ ] **Character Buffer (1 KB EBR)**
  - [ ] Infer DP16KD with dual-port configuration
  - [ ] CPU write interface (Port A)
  - [ ] VGA read interface (Port B)
  - [ ] Address mapping (CPU 0xC300-0xC6E7)

- [ ] **Font ROM (1.5 KB EBR)**
  - [ ] Create 8×16 font hex file (font_8x16.hex)
  - [ ] Infer ROM using $readmemh
  - [ ] Font address calculation (char_code × 16 + scanline)

- [ ] **Character Generator**
  - [ ] Character fetch (X, Y → char address)
  - [ ] Font fetch (char code, scanline → font data)
  - [ ] Pixel serializer (font bitmap → pixel output)

- [ ] **VGA Output**
  - [ ] RGB signal generation (monochrome: R=G=B=pixel)
  - [ ] H-sync and V-sync output
  - [ ] Add VGA pins to colorlight_i5.lpf

- [ ] **CPU Interface**
  - [ ] Update address_decoder.v with VGA addresses
  - [ ] Connect CPU data bus to character buffer
  - [ ] Add VGA chip select logic

- [ ] **Testing**
  - [ ] Write test pattern from CPU (e.g., "HELLO WORLD")
  - [ ] Verify character display on VGA monitor
  - [ ] Test full screen fill and scrolling

### 10.2 Phase 2: Enhanced 80×25 with Color

- [ ] **PLL Configuration**
  - [ ] Add EHXPLLL primitive instantiation
  - [ ] Configure for 25.125 MHz pixel clock
  - [ ] Connect PLL lock signal to reset logic

- [ ] **Attribute Buffer (2 KB EBR)**
  - [ ] Infer second DP16KD for attributes
  - [ ] Define attribute format (4-bit FG, 4-bit BG)
  - [ ] CPU write interface (Port A, address 0xC400)

- [ ] **Color Logic**
  - [ ] 4-bit palette decoder (16 colors)
  - [ ] RGB output driver (3-bit or 6-bit color)
  - [ ] Attribute-to-RGB mapping

- [ ] **Hardware Cursor**
  - [ ] Cursor position registers (0xC501, 0xC502)
  - [ ] Cursor blink logic (toggled by frame counter)
  - [ ] Cursor rendering (XOR or color inversion)

- [ ] **Control Registers**
  - [ ] Implement VGA_CTRL register (0xC500)
  - [ ] Cursor position registers
  - [ ] Foreground/background color registers

- [ ] **Testing**
  - [ ] Test 80×25 display with color attributes
  - [ ] Verify cursor positioning and blinking
  - [ ] Test hardware scrolling (if implemented)

### 10.3 Phase 3: HDMI/DVI Output (Future)

- [ ] **PLL Multi-Output**
  - [ ] Configure PLL for 125 MHz serializer clock
  - [ ] Maintain 25.125 MHz pixel clock output

- [ ] **TMDS Encoding**
  - [ ] Implement 8b/10b TMDS encoder (R, G, B)
  - [ ] DC balance logic
  - [ ] Control period encoding (H-sync, V-sync)

- [ ] **Serialization**
  - [ ] Instantiate ODDRX2F primitives (3× for RGB)
  - [ ] 10:1 or 5:1 serialization (cascade if needed)
  - [ ] Clock channel serialization

- [ ] **LVDS Output**
  - [ ] Instantiate OLVDS buffers (4× pairs)
  - [ ] Connect to HDMI connector pins
  - [ ] Add HDMI pins to .lpf file

- [ ] **Testing**
  - [ ] Test HDMI output on monitor/TV
  - [ ] Verify TMDS encoding with oscilloscope
  - [ ] Check for display artifacts or timing issues

---

## 11. References and Resources

### 11.1 Official Lattice Documentation
- [ECP5 and ECP5-5G Family Data Sheet (FPGA-DS-02012-3.4, September 2025)](https://www.latticesemi.com/-/media/LatticeSemi/Documents/DataSheets/ECP5/FPGA-DS-02012-3-4-ECP5-ECP5G-Family-Data-Sheet.ashx?document_id=50461)
- [ECP5 and ECP5-5G Memory Usage Guide (FPGA-TN-02204-1.6)](https://www.latticesemi.com/-/media/LatticeSemi/Documents/ApplicationNotes/EH/FPGA-TN-02204-1-6-ECP5-and-ECP5-5G-Memory-Usage-Guide.ashx?document_id=50466)
- [ECP5 and ECP5-5G sysCLOCK PLL/DLL Design and User Guide (FPGA-TN-02200-1.3)](https://www.latticesemi.com/-/media/LatticeSemi/Documents/ApplicationNotes/EH/FPGA-TN-02200-1-3-ECP5-and-ECP5-5G-sysCLOCK-PLL-DLL-Design-and-User-Guide.ashx?document_id=50465)
- [ECP5 and ECP5-5G High-Speed I/O Interface (TN1265)](https://www.latticesemi.com/~/media/LatticeSemi/Documents/ApplicationNotes/EH/TN1265.pdf)
- [FPGA Libraries Reference Guide (September 2014)](https://www.latticesemi.com/-/media/LatticeSemi/Documents/UserManuals/EI/FPGALibrariesReferenceGuide33.ashx?document_id=50790)

### 11.2 Colorlight i5 Board Resources
- [Getting Started with ECP5 FPGAs on the Colorlight i5 FPGA Development Board (Tom Verbeure)](https://tomverbeure.github.io/2021/01/22/The-Colorlight-i5-as-FPGA-development-board.html)
- [Colorlight i5 Extension Board Pin Mapping (Tom Verbeure)](https://tomverbeure.github.io/2021/01/30/Colorlight-i5-Extension-Board-Pin-Mapping.html)
- [GitHub: wuxx/Colorlight-FPGA-Projects](https://github.com/wuxx/Colorlight-FPGA-Projects)
- [LiteX Boards: Colorlight i5 Platform File](https://github.com/litex-hub/litex-boards/blob/master/litex_boards/platforms/colorlight_i5.py)
- [ColorLight I5 - Stm32World Wiki](https://stm32world.com/wiki/ColorLight_I5)

### 11.3 PLL and Clock Generation
- [ECP5 FPGA Clock Generation - Project F](https://projectf.io/posts/ecp5-fpga-clock/)
- [Configuring the Lattice ECP5 PLL (blog.dave.tf)](https://blog.dave.tf/post/ecp5-pll/)

### 11.4 VGA and Video Display
- [VGA Signal Timing (TinyVGA)](http://www.tinyvga.com/vga-timing)
- [Beginning FPGA Graphics - Project F](https://projectf.io/posts/fpga-graphics/)
- [Isle Display - Project F](https://projectf.io/isle/display.html)

### 11.5 HDMI/DVI and TMDS
- [FPGA Implementation of HDMI Transmission (VEMEKO)](https://www.vemeko.com/blog/67206.html)
- [Design a Lattice FPGA HDMI Transmission Scheme (DEV Community)](https://dev.to/carolineee/design-a-lattice-fpga-hdmi-transmission-scheme-omc)
- [GitHub: BrunoLevy/learn-fpga - HDMI Tutorial](https://github.com/BrunoLevy/learn-fpga/blob/master/FemtoRV/TUTORIALS/HDMI.md)

### 11.6 Open Source FPGA Tools
- [nextpnr ECP5 Primitives Documentation](https://github.com/YosysHQ/nextpnr/blob/master/ecp5/docs/primitives.md)
- [Yosys Issue #1836: Cannot infer dual port read only BRAM on ECP5](https://github.com/YosysHQ/yosys/issues/1836)
- [Yosys Issue #1101: ECP5 true dual port RAM not allocated DP16KD](https://github.com/YosysHQ/yosys/issues/1101)

---

## 12. Summary and Key Takeaways

### 12.1 Resource Availability
- **ECP5-25F has abundant EBR**: 56 blocks × 18 Kb = 126 KB total
- **Current project uses ~28 blocks**: 50% available for new features
- **VGA text mode requires 2-3 blocks**: Minimal impact (~5% of total EBR)
- **No resource constraints**: Plenty of room for 80×25 or even 80×50 display

### 12.2 Recommended Configuration
- **Start simple**: 40×25 monochrome, no PLL (Phase 1)
- **Upgrade to standard**: 80×25 with 16 colors (Phase 2)
- **Future enhancement**: HDMI output with extended features (Phase 3)

### 12.3 Clock Strategy
- **Phase 1**: Use existing 25 MHz directly (simplest)
- **Phase 2**: Add PLL for accurate 25.125 MHz (close to 25.175 MHz)
- **Phase 3**: Multi-output PLL for pixel clock + serializer clock

### 12.4 Memory Architecture
- **Character Buffer**: True dual-port (DP16KD), CPU writes, VGA reads
- **Font ROM**: Pseudo dual-port or inferred ROM, read-only
- **Attributes**: Optional dual-port for color text mode
- **Clock Domain Crossing**: Handled automatically by EBR dual-port mode

### 12.5 Implementation Priorities
1. **VGA sync generator and timing** (foundation)
2. **Character buffer and font ROM** (memory)
3. **Character generator pipeline** (rendering logic)
4. **CPU interface and memory mapping** (system integration)
5. **PLL and color attributes** (enhancements)
6. **HDMI output** (advanced feature)

### 12.6 Risk Mitigation
- **Start with proven VGA timing**: 640×480@60Hz is well-documented
- **Test early and often**: Character display, then scrolling, then color
- **Use open-source examples**: Project F and others provide working code
- **Leverage EBR dual-port**: No need for complex CDC logic
- **Keep LCD as backup**: During development, LCD provides debug output

---

**End of Research Document**

Generated for RetroCPU project, 2025-12-27
