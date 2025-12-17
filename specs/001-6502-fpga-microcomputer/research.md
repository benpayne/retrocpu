# Research & Technology Decisions
**Feature**: 6502 FPGA Microcomputer
**Date**: 2025-12-16

## Overview

This document captures research findings and technology decisions for implementing a 6502 microcomputer on the Lattice ECP5 FPGA using open-source tools. All decisions prioritize simplicity, educational value, and test-driven development per project constitution.

## 1. Arlet 6502 CPU Core

### Decision
Use Arlet Ottens' 6502 Verilog core from https://github.com/Arlet/verilog-6502

###Rationale
- **Well-tested**: Battle-tested implementation used in multiple FPGA projects
- **Yosys compatible**: Successfully synthesizes with open-source toolchain
- **Clean interface**: Standard 6502 bus signals, easy integration
- **Documentation**: Good code comments and usage examples
- **License**: BSD-style open source license
- **Resource efficient**: ~1000 LUTs typical (leaves room for peripherals)

### Alternatives Considered
- **T65 core**: VHDL-based, would require mixed-language support
- **opencores 6502**: Less maintained, unclear Yosys compatibility
- **Custom implementation**: Educational value but significant time investment, deferred to future

### Interface Signals
```verilog
module cpu(
    input clk,              // System clock
    input reset,            // Active-high reset
    input [7:0] DI,         // Data input from memory/I/O
    output [7:0] DO,        // Data output to memory/I/O
    output [15:0] AB,       // Address bus
    output WE,              // Write enable (1 = write, 0 = read)
    input IRQ,              // Interrupt request (active-low)
    input NMI,              // Non-maskable interrupt (active-low)
    input RDY               // Ready signal for wait states
);
```

### Integration Notes
- Core expects single-cycle memory access by default
- RDY signal can insert wait states for slow peripherals
- Reset should be held for minimum 2 clock cycles
- IRQ/NMI are level-sensitive, active-low

## 2. Memory Architecture

### Decision
Implement all 64KB memory using Lattice ECP5 block RAM primitives inferred by Yosys

### Rationale
- **Sufficient capacity**: ECP5-25F has 1.1 Mbit block RAM (137.5 KB), 64KB uses 47% capacity
- **Performance**: Single-cycle access at 1 MHz CPU clock (trivial timing)
- **Synthesis**: Yosys correctly infers block RAM from Verilog patterns
- **Initialization**: `$readmemh()` supported for ROM initialization

### Block RAM Configuration
- **Primitive**: DP16KD (16Kbit dual-port block RAM)
- **Required blocks**: 64KB = 512Kbit = 32 blocks
- **RAM organization**: 32KB = 16 blocks
- **ROM organization**: 24KB = 12 blocks (16KB BASIC + 8KB monitor)
- **Remaining capacity**: ~50KB available for future expansion

### Verilog Pattern for Block RAM Inference
```verilog
// RAM inference pattern
reg [7:0] ram [0:32767];  // 32KB = 32768 bytes
always @(posedge clk) begin
    if (we && ram_select)
        ram[addr[14:0]] <= data_in;
    data_out <= ram[addr[14:0]];
end

// ROM inference pattern with initialization
reg [7:0] rom [0:16383];  // 16KB BASIC ROM
initial begin
    $readmemh("basic_rom.hex", rom);
end
assign rom_data = rom[addr[13:0]];
```

### Alternatives Considered
- **Distributed RAM**: Insufficient capacity, uses LUTs (expensive)
- **External SRAM**: Not available on Colorlight i5 board
- **Partial block RAM**: More complex, no benefit at 1 MHz

## 3. UART Implementation

### Decision
Implement simple transmit-only UART with configurable baud rate generator

### Rationale
- **P1/P2 requirement**: Only TX needed for monitor and BASIC output
- **RX future**: Can add receive path in later user stories (P3+)
- **Simplicity**: TX-only is ~50 lines of Verilog, easy to test
- **Baud rate**: 9600 baud adequate for interactive use

### Baud Rate Calculation
```
System clock: 25 MHz
Target baud rate: 9600
Oversampling: 16x (standard for UART)

Divider = 25,000,000 / (16 * 9600) = 162.76 ≈ 163

Actual baud rate = 25,000,000 / (16 * 163) = 9585 baud
Error = (9600 - 9585) / 9600 = 0.16% (acceptable, <3% tolerance)

Alternative: 115200 baud
Divider = 25,000,000 / (16 * 115200) = 13.56 ≈ 14
Actual = 111,607 baud, error = 3.1% (marginal)
```

### Register Map
- **$C000**: Data register (write to transmit)
- **$C001**: Status register (read)
  - Bit 0: TX ready (1 = can accept new byte)
  - Bits 1-7: Reserved

### Timing
- 8N1 format: 1 start + 8 data + 1 stop = 10 bits per byte
- At 9600 baud: 1.04 ms per byte
- At 1 MHz CPU: 1041 clock cycles per byte (no CPU blocking)

### Alternatives Considered
- **Full UART with FIFO**: Overengineered for P1/P2, defer to future
- **Higher baud rates**: 115200 has marginal error at 25 MHz clock
- **Software bit-banging**: CPU too slow (1 MHz), impractical

## 4. HD44780 LCD Controller

### Decision
Implement 4-bit parallel interface with hardware timing generation

### Rationale
- **Pin efficiency**: 7 pins total (4 data + 3 control) fits PMOD connector
- **Hardware timing**: CPU freed from microsecond-level delays
- **Standard interface**: HD44780 is ubiquitous, well-documented
- **Educational**: Shows state machine design, timing constraints

### 4-Bit Mode Timing (HD44780 Datasheet)
```
Initialization sequence:
  1. Wait 15ms after power-on
  2. Function set (0x03) - wait 4.1ms
  3. Function set (0x03) - wait 100μs
  4. Function set (0x03)
  5. Function set (0x02) - enter 4-bit mode
  6. Function set (0x28) - 2 lines, 5x8 font
  7. Display on (0x0C)
  8. Clear display (0x01)

Enable pulse timing:
  - Enable high time: minimum 450ns (12 clocks @ 25MHz)
  - Data setup: 80ns (3 clocks)
  - Data hold: 10ns (1 clock)

Command execution times:
  - Clear/home: 1.64ms
  - Other commands: 40μs
  - Character write: 40μs
```

### Register Map
- **$C100**: Data register (character ASCII code)
- **$C101**: Command register (HD44780 commands)
- **$C102**: Status register
  - Bit 0: Busy (1 = executing command, 0 = ready)

### Pin Assignments (to be defined in .lpf)
```
LCD_D4-D7: 4 data lines
LCD_RS: Register select (0=command, 1=data)
LCD_RW: Read/write (tied low for write-only, save 1 pin)
LCD_E: Enable pulse
```

### Alternatives Considered
- **8-bit mode**: Requires 11 pins (too many for single PMOD)
- **I2C LCD**: Requires I2C controller (more complex)
- **Software timing**: CPU polling is inaccurate at 1 MHz

## 5. PS/2 Keyboard Interface

### Decision
Integrate existing ps2_keyboard.v module, provide raw scan codes to software

### Rationale
- **Existing implementation**: Working PS/2 module already available
- **Raw scan codes**: Software decoding provides flexibility
- **Educational**: Shows hardware/software division of labor
- **Pin availability**: Pins K5 and B3 already assigned in colorlight_i5.lpf

### PS/2 Protocol
```
Clock: 10-16.7 kHz (device-driven, bidirectional)
Data format: 11 bits per transmission
  - 1 start bit (always 0)
  - 8 data bits (LSB first)
  - 1 odd parity bit
  - 1 stop bit (always 1)

Scan code set: Set 2 (default)
  - Make codes: Single byte for most keys
  - Break codes: 0xF0 prefix + make code
  - Extended keys: 0xE0 prefix
```

### Register Map
- **$C200**: Scan code data register
- **$C201**: Status register
  - Bit 0: Data ready (1 = new scan code available)
  - Bit 1: Make/break (0 = make, 1 = break)
  - Bit 7: Error (parity/framing error)

### Software Decoding
Monitor/BASIC firmware must implement:
- Scan code to ASCII translation table
- Shift/Ctrl/Alt state tracking
- Special key handling (arrows, function keys)
- Typical table: ~100 bytes for basic key set

### Alternatives Considered
- **Hardware ASCII conversion**: Inflexible, complex state machine
- **USB keyboard**: Requires USB host controller (much more complex)
- **New PS/2 implementation**: Unnecessary, existing module works

## 6. Clock and Reset Strategy

### Decision
Single 25 MHz clock domain with clock enable for CPU; hardware reset button with debouncing

### Rationale
- **No CDC issues**: Single clock domain eliminates clock domain crossing bugs
- **Simple timing**: Clock enable generation is trivial (divide by 25 counter)
- **Flexible**: Can adjust CPU speed by changing divider ratio
- **Reset button**: Essential for development and debugging

### Clock Generation
```verilog
reg [4:0] clk_div = 0;
reg cpu_clk_en = 0;

always @(posedge clk) begin
    clk_div <= clk_div + 1;
    cpu_clk_en <= (clk_div == 0);  // Pulse every 25 cycles = 1 MHz
end
```

### Reset Controller
```verilog
// Power-on reset: Hold reset for 256 clock cycles (~10ms)
reg [7:0] por_count = 0;
reg por_done = 0;

always @(posedge clk) begin
    if (!por_done) begin
        por_count <= por_count + 1;
        if (&por_count) por_done <= 1;
    end
end

// Button debounce: Require stable for 50ms (1.25M clocks at 25MHz)
reg [20:0] debounce_count = 0;
reg [2:0] btn_sync = 3'b111;  // Synchronizer
reg btn_stable = 1;

always @(posedge clk) begin
    btn_sync <= {btn_sync[1:0], reset_n_pin};  // Synchronize to clock

    if (btn_sync[2] == btn_stable) begin
        debounce_count <= 0;
    end else begin
        debounce_count <= debounce_count + 1;
        if (debounce_count[20]) begin  // ~40ms @ 25MHz
            btn_stable <= btn_sync[2];
        end
    end
end

assign system_reset = !por_done || !btn_stable;
```

### Pin Assignment
- Reset button: T1 (FIRE 2), active-low with internal pullup per .lpf file

### Alternatives Considered
- **Multiple clock domains**: Complex CDC, unnecessary for 1 MHz CPU
- **PLL for CPU clock**: Overkill, adds jitter and complexity
- **No debounce**: Mechanical bounce causes multiple resets

## 7. Microsoft BASIC Selection

### Decision
Use EhBASIC (Enhanced BASIC) by Lee Davison - clean 6502 BASIC with MIT-style license

### Rationale
- **Open source**: Free to use, modify, and distribute
- **Size**: ~8-12KB, fits comfortably in 16KB ROM space
- **Quality**: Well-tested, full-featured BASIC interpreter
- **I/O vectors**: Clean abstraction, easy to patch for UART
- **Documentation**: Good documentation and examples available

### I/O Vector Patching
EhBASIC uses vectors for I/O abstraction:
```
$FFEE-$FFEF: CHRIN (character input)
$FFF0-$FFF1: CHROUT (character output)
$FFF2-$FFF3: GETCHR (get character without wait)
$FFF4-$FFF5: RDKEY (check for key)
```

Monitor firmware provides implementations:
```asm
CHROUT:  ; Output character in A to UART
    pha
:   lda $C001    ; Check UART status
    and #$01     ; TX ready?
    beq :-       ; Wait if not ready
    pla
    sta $C000    ; Write to UART
    rts

CHRIN:   ; Input character from UART (future)
    ; Poll keyboard or UART RX
    rts
```

### Build Process
```bash
# Obtain EhBASIC source
wget http://www.sunrise-ev.com/6502/ehbasic.zip

# Assemble with ca65
ca65 --cpu 6502 ehbasic.s -o ehbasic.o
ld65 -C ehbasic.cfg ehbasic.o -o ehbasic.bin

# Convert to hex for Verilog $readmemh
xxd -p -c 1 ehbasic.bin > basic_rom.hex
```

### Alternatives Considered
- **OSI BASIC**: Good but less documented, harder to patch
- **Applesoft BASIC**: Requires floating point, larger (~10KB)
- **TINY BASIC**: Too limited, not "Microsoft BASIC" as specified

## 8. Monitor Program Design

### Decision
Minimal monitor in <1KB with commands: E (examine), D (deposit), J (jump), G (go to BASIC)

### Rationale
- **Simplicity**: Basic functionality for P1 bring-up and testing
- **Size**: Leaves room in 8KB ROM for BASIC I/O vectors and utilities
- **Educational**: Shows 6502 assembly programming, UART I/O

### Monitor Commands
```
E addr         - Examine memory (display hex value)
D addr value   - Deposit byte to memory
J addr         - Jump to address
G              - Go to BASIC (jump to $8000)
```

### Monitor Code Structure
```asm
; Reset vector points here
.org $E000
RESET:
    ldx #$FF        ; Initialize stack
    txs

    ; Print welcome message
    ldx #0
:   lda MSG,X
    beq :+
    jsr CHROUT
    inx
    bne :-

:   ; Main command loop
    jsr CHRIN       ; Get command character
    cmp #'E'
    beq CMD_EXAMINE
    ; ... other commands
    jmp :-

CMD_EXAMINE:
    jsr GETHEX      ; Get address (4 hex digits)
    ; ... display memory value
    jmp :-

; I/O routines
CHROUT:
    ; Output char in A to UART
    ; (see BASIC section above)
    rts

CHRIN:
    ; Input char from UART
    rts

GETHEX:
    ; Parse hex digits into address
    rts

MSG: .asciiz "RetroCPU Monitor v1.0\n\n> "
```

### Assembler Choice
Use ca65 from cc65 toolchain:
- Widely available (apt install cc65)
- Good macro support
- Generates clean 6502 code
- Can target specific addresses

### Alternatives Considered
- **Full monitor (Wozmon style)**: Too large, too complex for P1
- **No monitor**: Harder to debug, no BASIC entry point
- **Software only in BASIC**: Can't bootstrap without monitor

## 9. Address Decoder Design

### Decision
Simple combinational logic decoder using address range comparisons

### Rationale
- **Simplicity**: Easy to understand, easy to test
- **Performance**: Combinational, no latency
- **Flexibility**: Easy to modify memory map
- **Resource efficient**: Minimal LUT usage (~10 LUTs)

### Decoder Logic
```verilog
module address_decoder(
    input [15:0] addr,
    input we,
    output ram_select,
    output rom_basic_select,
    output rom_monitor_select,
    output uart_select,
    output lcd_select,
    output ps2_select
);

assign ram_select = (addr < 16'h8000);  // $0000-$7FFF
assign rom_basic_select = (addr >= 16'h8000) && (addr < 16'hC000);  // $8000-$BFFF
assign rom_monitor_select = (addr >= 16'hE000);  // $E000-$FFFF

// I/O decoding (page-aligned)
assign uart_select = (addr[15:8] == 8'hC0);  // $C000-$C0FF
assign lcd_select = (addr[15:8] == 8'hC1);   // $C100-$C1FF
assign ps2_select = (addr[15:8] == 8'hC2);   // $C200-$C2FF

endmodule
```

### Alternatives Considered
- **Registered decoder**: Adds latency, unnecessary
- **Priority encoder**: More complex, same result
- **Full address decode**: Wasteful (page-aligned is sufficient)

## 10. Synthesis and Timing Constraints

### Decision
Minimal timing constraints; rely on conservative clock speeds and Yosys defaults

### Rationale
- **1 MHz CPU**: Extremely slow, trivial timing closure
- **25 MHz system**: Well below ECP5 capabilities (>100 MHz possible)
- **Educational focus**: Timing optimization not a learning objective for P1/P2

### Synthesis Constraints (Makefile)
```bash
# Yosys synthesis
yosys -p "read_verilog rtl/**/*.v; synth_ecp5 -top soc_top -json build/soc_top.json"

# nextpnr place-and-route
nextpnr-ecp5 --25k --package CABGA256 --json build/soc_top.json \
    --lpf colorlight_i5.lpf --textcfg build/soc_top.config

# ecppack bitstream generation
ecppack build/soc_top.config build/soc_top.bit
```

### Resource Budget
- **LUTs**: Target <15K (62% of 24K), measured after synthesis
- **Block RAM**: 32 blocks (of 56 available)
- **I/O pins**: 15 pins used (clock, reset, UART, PS/2, LCD, LEDs)

### Timing Expectations
- **Setup/hold**: No violations expected (conservative clocks)
- **Max frequency**: Report from nextpnr, but not critical
- **Power**: Not measured (board powered via USB, adequate)

### Alternatives Considered
- **Aggressive timing constraints**: Unnecessary complexity, no benefit
- **Multi-frequency clocking**: Over-engineered for educational project

## Summary of Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| CPU Core | Arlet 6502 | Proven, Yosys-compatible, efficient |
| Memory | ECP5 block RAM (64KB total) | Sufficient capacity, single-cycle access |
| UART | TX-only, 9600 baud | Simple, adequate for P1/P2 |
| LCD | 4-bit HD44780, hardware timing | Pin-efficient, educational value |
| Keyboard | Existing PS/2 module, raw scan codes | Reuse working code, flexible decoding |
| Clock | Single 25MHz domain, clock enable | Simple, no CDC issues |
| Reset | Hardware button + debounce | Essential for development |
| BASIC | EhBASIC (Lee Davison) | Open source, well-documented |
| Monitor | Minimal <1KB monitor | Sufficient for P1, easy to test |
| Address Decode | Combinational page-aligned | Simple, flexible, efficient |
| Synthesis | Conservative, minimal constraints | Focus on functionality over performance |

## Next Steps

All technology decisions are complete. Ready to proceed to Phase 1 design artifacts (data-model.md, contracts/, quickstart.md).
