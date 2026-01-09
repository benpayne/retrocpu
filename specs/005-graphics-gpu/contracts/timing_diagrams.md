# Timing Diagrams Contract: Graphics GPU

**Feature**: 005-graphics-gpu
**Date**: 2026-01-04

This document illustrates timing relationships for key GPU operations.

---

## 1. Burst Write Sequence

```
Cycle:    0    1    2    3    4    5    6    7    8    9
         ___  ___  ___  ___  ___  ___  ___  ___  ___  ___
CLK   __|   |_|   |_|   |_|   |_|   |_|   |_|   |_|   |_|   |_

Addr  ----[C100][C101][C103][C102][C102][C102][C102][C102]---

Data  ----[$00][$00][$01][$AA][$BB][$CC][$DD][$EE]-----------

WE    ____/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\___________

                    [Burst ON]

VRAM  ----[----][----][----][$AA→$0000][$BB→$0001][$CC→$0002]
Addr                          [$0000→$0001][$0001→$0002][$0002→$0003]
```

**Explanation**:
- Cycle 0: Write $00 to VRAM_ADDR_LO
- Cycle 1: Write $00 to VRAM_ADDR_HI (address = $0000)
- Cycle 2: Write $01 to VRAM_CTRL (enable burst mode)
- Cycle 3: Write $AA to VRAM_DATA → writes to $0000, increments to $0001
- Cycle 4: Write $BB to VRAM_DATA → writes to $0001, increments to $0002
- Cycle 5+: Continue writing bytes with auto-increment

---

## 2. VBlank Interrupt Timing

```
Scanline: 479   480   481   490   491   492   493   494   0    1
         _______________                 _____________________
v_active                |_______________|                     |___

                                  ___________
VBlank                           |           |
Signal   ________________________|           |___________________

                                       ___
VBlank                                |   |
IRQ      _____________________________| R |_____________________
                                       (Rising Edge)

GPU_IRQ                                ___________________
Output   _________________________________|               |_______
         (synchronized to CPU clock,  ^^^ Interrupt
          edge-detected pulse)         Asserted
```

**Key Timing Points**:
- Scanline 480-489: Front porch (video_active = 0, VBlank = 0)
- Scanline 490-491: Vertical sync (VBlank flag = 1)
- Scanline 492-524: Back porch (VBlank = 1)
- Scanline 0: Return to visible region (VBlank = 0)

**Interrupt Generation**:
- VBlank signal crosses from pixel clock to CPU clock via dual-flop synchronizer
- Rising edge detector creates one-cycle interrupt pulse
- Total latency: 2-3 CPU clock cycles from VBlank assertion

---

## 3. Page Flip Sequence

```
Frame N                    VBlank          Frame N+1
(Displaying Page 0)                       (Displaying Page 1)

         |<--- Visible --->|<-VBlank->|<--- Visible --->|
         |                 |          |                 |
v_count: 0 ... 479 480 ... 491 ... 0 ... 479 480 ...
         |                 |^         |                 |
         |                 ||         |                 |
FB_BASE: $0000             ||         $2000             |
                           ||                           |
                    VBlank IRQ
                    Fires Here
                           ||                           |
                           vv                           |
CPU:     [Render to       [Update FB_BASE_ADDR]  [Render to
         Page 1]           to $2000               Page 0]

VRAM:    Page 0 Page 1    Page 0 Page 1         Page 0 Page 1
         [Displaying]     [Rendering]            [Displaying]
```

**Page Flip Steps**:
1. Frame N: Display shows page 0 ($0000), CPU renders to page 1 ($2000)
2. VBlank interrupt fires at scanline 490
3. ISR executes: write FB_BASE_LO=$00, FB_BASE_HI=$20 (address $2000)
4. Frame N+1: Display switches to page 1, CPU renders to page 0
5. Repeat with roles swapped

**Tear-Free Guarantee**:
- FB_BASE_ADDR update during VBlank ensures no visible scanlines affected
- New address takes effect at start of frame N+1 (scanline 0)

---

## 4. Pixel Fetch Pipeline

```
Pixel Clock Cycles:  1    2    3    4    5    6    7    8
                    ___  ___  ___  ___  ___  ___  ___  ___
CLK_PIXEL        __|   |_|   |_|   |_|   |_|   |_|   |_|   |_

h_count, v_count -[0,0][1,0][2,0][3,0][4,0][5,0][6,0][7,0]--

VRAM Address     -[Calc][A0] [A1] [A2] [A3] [A4] [A5] [A6]--
  (calculated)         |‾‾‾‾ ‾‾‾‾ ‾‾‾‾ ‾‾‾‾ ‾‾‾‾ ‾‾‾‾ ‾‾‾‾|

VRAM Data Out    -----[  ][D0] [D1] [D2] [D3] [D4] [D5] [D6]-
  (registered)   1 cycle latency ^

Pixel Decode     -----[  ][  ][P0] [P1] [P2] [P3] [P4] [P5]-
  (bit extract)       |‾‾‾‾ ‾‾‾‾ ‾‾‾‾ ‾‾‾‾ ‾‾‾‾ ‾‾‾‾|

Palette Lookup   -----[  ][  ][  ][RGB0][RGB1][RGB2][RGB3]--
  (if 2/4 BPP)              1 cycle latency ^

RGB888 Output    -----[  ][  ][  ][  ][RGB0][RGB1][RGB2]----
  (to DVI)              |‾‾‾‾‾‾‾‾‾‾‾‾ ‾‾‾‾‾‾‾‾‾‾‾‾|
                        Pipeline latency: 4 cycles
```

**Pipeline Stages**:
1. Address Calculation: From h_count, v_count, FB_BASE_ADDR, mode → VRAM address
2. VRAM Read: Registered output (1-cycle latency)
3. Pixel Decode: Extract pixel bits (1 BPP: shift bit, 2/4 BPP: extract nibble)
4. Palette Lookup: Index into palette (2/4 BPP only)
5. RGB Expansion: RGB444 → RGB888 bit duplication
6. Output: Drive RGB888 to DVI transmitter

**Latency**: 4 pixel clock cycles from address calculation to RGB output

---

## 5. Mode Switch Timing

```
Scanline: 10    11    12    13    14    15
         _______________         _____________________
video    Active         |_VBlank_|        Active      |___
_active

                    ^
                    | CPU writes GPU_MODE register
                    | (change from 1 BPP to 4 BPP)

Mode     1 BPP     1 BPP  1 BPP  4 BPP  4 BPP  4 BPP
Value    [320x200] [320x200]     [160x100]

Display  [Line 10] [Line 11]     [Line 13] [Line 14] [Line 15]
Output   [Old Mode][Old Mode][Glitch?][New Mode][New Mode]
                                  ^^^^^^
                                  Recommend changing
                                  during VBlank to
                                  avoid this
```

**Recommendation**:
- Change GPU_MODE during VBlank period (scanlines 480-524)
- Avoids mid-frame glitches from mode switch
- New mode takes full effect at start of next frame

---

## 6. Register Write and Read Timing

### Single-Cycle Write
```
Cycle:    N     N+1    N+2
         ___   ___   ___
CLK   __|   |_|   |_|   |_

Addr  ---[Reg]-------

Data  ---[Val]-------

WE    ___/‾‾‾\________

Reg   ---[Old][New]---
Value      ^   ^ Updated
```

### Single-Cycle Read
```
Cycle:    N     N+1    N+2
         ___   ___   ___
CLK   __|   |_|   |_|   |_

Addr  ---[Reg]-------

RE    ___/‾‾‾\________

Data  -------[Val]----
Out        ^   ^ Valid data
```

---

**Timing Diagrams Complete** ✅
