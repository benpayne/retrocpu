# Data Model: 6502 FPGA Microcomputer
**Feature**: 6502 FPGA Microcomputer
**Date**: 2025-12-16

## Overview

This document defines the complete memory map, register specifications, and data structures for the 6502 FPGA microcomputer system. The design uses a unified 64KB address space with memory-mapped I/O following standard 6502 conventions.

## Memory Map

### Complete 6502 Address Space (64 KB)

```
+------------------+ $FFFF
|  IRQ/BRK Vector  | $FFFE-$FFFF (2 bytes)
+------------------+ $FFFD
|   RESET Vector   | $FFFC-$FFFD (2 bytes)
+------------------+ $FFFB
|    NMI Vector    | $FFFA-$FFFB (2 bytes)
+------------------+ $FFF9
|   I/O Vectors    | $FFF0-$FFF9 (10 bytes) - BASIC I/O hooks
+------------------+ $FFEF
|                  |
|   Monitor ROM    | $E000-$FFEF (~8 KB)
|  (Read-Only)     | - Monitor program
|                  | - Utility routines
|                  | - I/O functions
+------------------+ $DFFF
|                  |
|   Reserved I/O   | $C300-$DFFF (49.75 KB)
|     Space        | - Future peripherals
|                  | - Reads return $FF
+------------------+ $C2FF
| PS/2 Keyboard    | $C200-$C2FF (256 bytes)
|   Registers      | - Data, status registers
+------------------+ $C1FF
|      LCD         | $C100-$C1FF (256 bytes)
|   Registers      | - Data, command, status
+------------------+ $C0FF
|      UART        | $C000-$C0FF (256 bytes)
|   Registers      | - Data, status, control
+------------------+ $BFFF
|                  |
|   BASIC ROM      | $8000-$BFFF (16 KB)
|  (Read-Only)     | - Microsoft 6502 BASIC
|                  | - Interpreter code
+------------------+ $7FFF
|                  |
|                  |
|  General Purpose | $0200-$7FFF (31.5 KB)
|       RAM        | - BASIC programs
|                  | - Variables
|                  | - User workspace
+------------------+ $01FF
|   Stack RAM      | $0100-$01FF (256 bytes)
| (Hardware Stack) | - 6502 stack (grows down)
+------------------+ $00FF
|   Zero Page      | $0000-$00FF (256 bytes)
|      RAM         | - Fast access
|                  | - Temporary variables
+------------------+ $0000
```

## Memory Regions Detail

### Zero Page RAM ($0000-$00FF)

**Purpose**: Fast-access RAM for 6502 zero-page addressing mode
**Size**: 256 bytes
**Access**: Read/Write, single cycle
**Usage**:
- Temporary variables for BASIC and monitor
- Pointer storage (16-bit addresses)
- Frequently accessed data

**Reserved Locations** (monitor conventions):
- $00-$01: Temporary storage
- $02-$03: Pointer for monitor operations
- $04-$05: BASIC workspace pointer
- $06-$FF: Available for BASIC and user programs

### Stack RAM ($0100-$01FF)

**Purpose**: Hardware stack for 6502 processor
**Size**: 256 bytes
**Access**: Read/Write, single cycle
**Usage**:
- Return addresses from JSR/RTS
- Pushed processor status (PHP/PLP)
- Temporary data (PHA/PLA)
- Interrupt context saving

**Stack Behavior**:
- Grows downward from $01FF
- Stack pointer (SP) is 8-bit, page $01 is implicit
- Reset initializes SP to $FF (stack at $01FF)
- Stack overflow wraps to $01FF (no protection)

### General Purpose RAM ($0200-$7FFF)

**Purpose**: Main RAM for programs and data
**Size**: 31,744 bytes (31.5 KB)
**Access**: Read/Write, single cycle
**Usage**:
- BASIC program text storage
- BASIC variable space
- BASIC arrays
- User machine code programs
- Data buffers

**BASIC Memory Usage**:
- Program text: Starts at $0200, grows upward
- Variables: Start after program, grow upward
- Arrays: Allocated from variable space
- String space: Top of RAM, grows downward
- Stack: Between arrays and strings

### BASIC ROM ($8000-$BFFF)

**Purpose**: Microsoft 6502 BASIC interpreter
**Size**: 16,384 bytes (16 KB)
**Access**: Read-only
**Initialization**: Loaded from `basic_rom.hex` during synthesis
**Content**:
- BASIC interpreter code
- Math routines (integer and floating point)
- String handling
- Line editor
- Program execution engine

**Entry Points** (typical EhBASIC):
- $8000: Cold start (initialize BASIC)
- $8003: Warm start (preserve program)
- Other vectors defined in BASIC source

### I/O Region ($C000-$DFFF)

**Purpose**: Memory-mapped I/O devices
**Size**: 8,192 bytes (8 KB)
**Access**: Mixed (read/write depending on device)
**Organization**: Page-aligned 256-byte blocks per device

#### UART Registers ($C000-$C0FF)

| Address | Name | Type | Description |
|---------|------|------|-------------|
| $C000 | UART_DATA | R/W | Data register (TX: write byte, RX: read byte future) |
| $C001 | UART_STATUS | R | Status register (bit 0: TX ready, bit 1: RX ready) |
| $C002 | UART_CONTROL | W | Control register (future: baud rate selection) |
| $C003-$C0FF | - | - | Reserved for future UART features |

**UART_DATA Register ($C000)**:
- **Write**: Transmit byte over UART TX
  - Data queued when TX ready
  - Writing when not ready is undefined (may be ignored or overwrite)
- **Read** (future): Receive byte from UART RX
  - Returns last received byte
  - Clears RX ready flag

**UART_STATUS Register ($C001)**:
- Bit 0: TX Ready (1 = transmitter ready for new byte, 0 = busy)
- Bit 1: RX Ready (1 = received data available, 0 = no data) [future]
- Bit 7: RX Overrun (1 = data lost, 0 = no error) [future]
- Bits 2-6: Reserved (read as 0)

**UART_CONTROL Register ($C002)** [future]:
- Baud rate divider configuration
- Format: 16-bit divider value

#### LCD Registers ($C100-$C1FF)

| Address | Name | Type | Description |
|---------|------|------|-------------|
| $C100 | LCD_DATA | W | Character data register (write ASCII to display) |
| $C101 | LCD_COMMAND | W | Command register (HD44780 commands) |
| $C102 | LCD_STATUS | R | Status register (bit 0: busy flag) |
| $C103-$C1FF | - | - | Reserved for LCD extensions |

**LCD_DATA Register ($C100)**:
- **Write**: Send character to LCD
  - ASCII character written to current cursor position
  - Cursor auto-advances right
  - Wait for busy flag clear before writing

**LCD_COMMAND Register ($C101)**:
- **Write**: Send HD44780 command
  - Common commands:
    - $01: Clear display (1.64ms execution time)
    - $02: Return home
    - $0C: Display on, cursor off
    - $80+addr: Set DDRAM address (cursor position)
  - Wait for busy flag clear before writing

**LCD_STATUS Register ($C102)**:
- Bit 0: Busy (1 = LCD executing command, 0 = ready for next operation)
- Bit 7: Address counter [future] (current DDRAM/CGRAM address)
- Bits 1-6: Reserved (read as 0)

#### PS/2 Keyboard Registers ($C200-$C2FF)

| Address | Name | Type | Description |
|---------|------|------|-------------|
| $C200 | PS2_DATA | R | Scan code data register |
| $C201 | PS2_STATUS | R | Status register (bit 0: data ready) |
| $C202-$C2FF | - | - | Reserved for keyboard extensions |

**PS2_DATA Register ($C200)**:
- **Read**: Last received scan code
  - Returns 8-bit scan code from PS/2 keyboard
  - Reading clears data ready flag
  - Reading when no data available returns last value

**PS2_STATUS Register ($C201)**:
- Bit 0: Data Ready (1 = new scan code available, 0 = no data)
- Bit 1: Make/Break (0 = make code, 1 = break code prefix seen)
- Bit 7: Error (1 = parity or framing error, 0 = no error)
- Bits 2-6: Reserved (read as 0)

**Scan Code Format** (PS/2 Set 2):
- Make code: Single byte (e.g., $1C for 'A')
- Break code: $F0 followed by make code
- Extended keys: $E0 prefix (e.g., arrows, home, end)

### Monitor ROM ($E000-$FFFF)

**Purpose**: Monitor program and system vectors
**Size**: 8,192 bytes (8 KB)
**Access**: Read-only
**Initialization**: Loaded from `monitor_rom.hex` during synthesis

**Memory Layout**:
```
$E000-$FFEF : Monitor code (~8 KB - 17 bytes)
$FFF0-$FFF9 : BASIC I/O vectors (10 bytes)
$FFFA-$FFFB : NMI vector (2 bytes)
$FFFC-$FFFD : RESET vector (2 bytes)
$FFFE-$FFFF : IRQ/BRK vector (2 bytes)
```

**Monitor Entry Points**:
- $E000: RESET entry (cold boot)
- $E003: Warm restart (preserve state)
- CHROUT: Character output to UART
- CHRIN: Character input from UART/keyboard
- HEXOUT: Output hex byte
- HEXIN: Input hex value

**BASIC I/O Vectors ($FFF0-$FFF9)**:
```
$FFF0-$FFF1: CINV - Input vector (get character)
$FFF2-$FFF3: COUTV - Output vector (put character)
$FFF4-$FFF5: CSTATV - Status vector (check input ready)
$FFF6-$FFF7: Reserved
$FFF8-$FFF9: Reserved
```

**Hardware Vectors**:
```
$FFFA-$FFFB: NMI_VEC - Non-maskable interrupt handler
$FFFC-$FFFD: RESET_VEC - Reset/power-on handler ($E000)
$FFFE-$FFFF: IRQ_VEC - IRQ/BRK handler
```

## Data Types and Formats

### Hexadecimal File Format

**ROM Initialization Files** (.hex):
```
# Format: ASCII hex, one byte per line
41
42
43
...
# Used by Verilog $readmemh()
```

**Alternative Format** (.mem):
```
# Format: ASCII hex, space-separated
41 42 43 44 45 46 47 48
...
```

### Binary Format

**.bin files**: Raw binary (e.g., EhBASIC compiled output)
- Converted to .hex using `xxd -p -c 1`

### Assembly Source Format

**.s files**: 6502 assembly source (ca65 format)
```asm
.org $E000
RESET:
    ldx #$FF
    txs
    jmp MAIN
```

## Register Bit Fields Summary

### UART_STATUS ($C001)
```
Bit 7: RX_OVERRUN (future)
Bit 6: Reserved
Bit 5: Reserved
Bit 4: Reserved
Bit 3: Reserved
Bit 2: Reserved
Bit 1: RX_READY (future)
Bit 0: TX_READY
```

### LCD_STATUS ($C102)
```
Bit 7: ADDR_COUNTER (future)
Bit 6: Reserved
Bit 5: Reserved
Bit 4: Reserved
Bit 3: Reserved
Bit 2: Reserved
Bit 1: Reserved
Bit 0: BUSY
```

### PS2_STATUS ($C201)
```
Bit 7: ERROR
Bit 6: Reserved
Bit 5: Reserved
Bit 4: Reserved
Bit 3: Reserved
Bit 2: Reserved
Bit 1: MAKE_BREAK
Bit 0: DATA_READY
```

## State Machines

### LCD Controller States

```
IDLE:
    - Wait for write to LCD_DATA or LCD_COMMAND
    -> SETUP_HIGH on write

SETUP_HIGH:
    - Setup high nibble on data lines
    - Assert RS (command/data)
    -> ENABLE_HIGH after setup delay

ENABLE_HIGH:
    - Assert E (enable) signal
    -> HOLD_HIGH after enable pulse

HOLD_HIGH:
    - Deassert E, hold data
    -> SETUP_LOW after hold delay

SETUP_LOW:
    - Setup low nibble on data lines
    -> ENABLE_LOW after setup delay

ENABLE_LOW:
    - Assert E signal for low nibble
    -> HOLD_LOW after enable pulse

HOLD_LOW:
    - Deassert E, hold data
    -> WAIT after hold delay

WAIT:
    - Wait for command execution (1.64ms for clear, 40μs otherwise)
    - Set BUSY flag
    -> IDLE after delay, clear BUSY
```

### UART TX States

```
IDLE:
    - TX_READY = 1
    - TX line = 1 (mark state)
    -> START on write to UART_DATA

START:
    - TX_READY = 0
    - TX line = 0 (start bit)
    -> BIT0 after 1 bit time

BIT0-BIT7:
    - TX line = data bit (LSB first)
    - Shift data right
    -> STOP after bit 7

STOP:
    - TX line = 1 (stop bit)
    -> IDLE after 1 bit time
    - TX_READY = 1
```

## Memory Access Timing

### RAM Access
- **Read**: Address stable, data available same cycle
- **Write**: Address and data stable, WE asserted
- **Latency**: 0 wait states (single cycle)

### ROM Access
- **Read**: Address stable, data available same cycle
- **Write**: Ignored (writes to ROM have no effect)
- **Latency**: 0 wait states (single cycle)

### I/O Access
- **UART**: Single cycle read/write (registers only)
- **LCD**: Single cycle register access, multi-cycle command execution
  - Must poll BUSY flag before next operation
- **PS/2**: Single cycle read (hardware buffers scan codes)
  - Data ready flag indicates new data

### Wait State Strategy
- No CPU wait states for P1/P2 (all devices non-blocking)
- RDY signal can be used for future slow peripherals
- Polling-based I/O (check status before operation)

## Address Decode Logic

### Memory Region Selection
```verilog
// RAM: $0000-$7FFF
ram_select = (addr[15] == 0);

// BASIC ROM: $8000-$BFFF
rom_basic_select = (addr[15:14] == 2'b10);

// I/O: $C000-$DFFF
io_select = (addr[15:13] == 3'b110);

// Monitor ROM: $E000-$FFFF
rom_monitor_select = (addr[15:13] == 3'b111);
```

### I/O Device Selection (within $C000-$DFFF)
```verilog
// Page-aligned decode (bits [15:8] = page number)
uart_select = io_select && (addr[11:8] == 4'h0);  // $C0xx
lcd_select = io_select && (addr[11:8] == 4'h1);   // $C1xx
ps2_select = io_select && (addr[11:8] == 4'h2);   // $C2xx
```

## Initialization Values

### Power-On State
- **RAM**: Undefined (random values)
- **ROM**: Initialized from .hex files
- **Stack Pointer**: $FF (points to $01FF)
- **Program Counter**: Loaded from RESET vector ($FFFC-$FFFD)
- **I/O Registers**: All zeros

### Reset Behavior
- **CPU**: Loads PC from RESET vector, clears interrupt flags
- **UART**: TX_READY = 1, no data in transit
- **LCD**: BUSY = 1 until initialization complete (~50ms)
- **PS/2**: DATA_READY = 0, no scan codes buffered

## Memory Usage Examples

### Monitor Memory Map
```
$E000: JMP RESET_HANDLER
$E003: JMP WARM_START
...
$E100: CHROUT routine
$E120: CHRIN routine
...
```

### BASIC Program Example
```
Program stored at $0200:
$0200: $00 $0C              ; Line 10 link pointer
$0202: $0A $00              ; Line number (10)
$0204: $99 "HELLO" $00      ; PRINT "HELLO"
$020C: $00 $00              ; End of program marker
```

### Stack Usage Example
```
Before JSR $E100:
  SP = $FF, Stack top = $01FF
After JSR $E100:
  SP = $FD
  $01FF = Return address high byte
  $01FE = Return address low byte
```

## Summary

This data model defines all memory regions, register specifications, and data formats for the 6502 FPGA microcomputer. The design prioritizes simplicity and educational clarity while providing complete functionality for running BASIC programs and interacting with I/O devices.
