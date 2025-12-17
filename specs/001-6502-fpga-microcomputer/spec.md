# Feature Specification: 6502 FPGA Microcomputer

**Feature Branch**: `001-6502-fpga-microcomputer`
**Created**: 2025-12-16
**Status**: Draft
**Input**: User description: "Design an FPGA-based 6502 microcomputer inspired by Ben Eater's breadboard 6502 system, implemented entirely in Verilog and targeting a Lattice ECP5 FPGA (Colorlight i5 board) using open-source tools (yosys + nextpnr)."

## Clarifications

### Session 2025-12-16

- Q: The LCD controller must interface with HD44780 displays. Which data bus width should be used? → A: 4-bit parallel mode (uses 4 data lines + 3 control = 7 pins total, must fit on single PMOD connector)
- Q: The I/O region is $C000-$DFFF (8 KB). How should individual device registers be mapped within this space? → A: Page-aligned 256-byte blocks: UART at $C000-$C0FF, LCD at $C100-$C1FF, PS/2 at $C200-$C2FF (keeps decode logic simple, allows expansion)
- Q: The PS/2 keyboard interface receives scan codes. How should these be processed before presenting to software? → A: Raw scan codes (data register contains raw PS/2 scan codes including make/break, software must decode to ASCII, using existing implementation)
- Q: The system requires a 6502 soft core. Which approach should be taken? → A: Use existing arlet/6502 core (Arlet Ottens' open-source Verilog 6502, proven and well-documented)
- Q: The system needs reset capability. What reset mechanisms should be provided? → A: Hardware reset button (physical button on FPGA board connected to pin, available buttons can be used) plus automatic power-on reset

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic System Boot and Monitor (Priority: P1)

A learner powers on the FPGA board and the 6502 system boots to a monitor program that displays a prompt on the serial terminal. The learner can examine memory locations and jump to addresses, verifying the CPU and memory subsystems are functioning.

**Why this priority**: This is the absolute minimum viable system. Without a working CPU, memory, and basic I/O, nothing else can function. This proves the fundamental hardware works.

**Independent Test**: Can be fully tested by loading a simple monitor ROM, observing serial output on terminal, entering commands via UART, and verifying memory read/write operations work correctly.

**Acceptance Scenarios**:

1. **Given** the FPGA is programmed and powered on, **When** power-on reset completes, **Then** the 6502 executes code from the reset vector and the monitor displays a welcome message on the serial terminal
2. **Given** the monitor is running, **When** a memory examine command is entered (e.g., "E 0200"), **Then** the monitor displays the contents of memory location $0200
3. **Given** the monitor is running, **When** a jump command is entered (e.g., "J 8000"), **Then** the CPU begins executing code at address $8000
4. **Given** the system is running, **When** the hardware reset button is pressed, **Then** the system restarts cleanly and returns to the monitor prompt

---

### User Story 2 - Run BASIC from ROM (Priority: P2)

A user powers on the system and it automatically transfers control from the monitor to Microsoft BASIC in ROM. The user can type BASIC commands on the serial terminal, run simple programs, and see output. This demonstrates a complete working retro computer system.

**Why this priority**: Running BASIC is the primary goal of the system. This proves all core components (CPU, RAM, ROM, I/O) work together as a complete microcomputer. However, it depends on Story 1 being complete first.

**Independent Test**: Can be tested by loading BASIC ROM, verifying auto-start from monitor, typing BASIC commands like "PRINT 2+2", running a simple FOR loop, and confirming correct output appears on terminal.

**Acceptance Scenarios**:

1. **Given** the system boots to the monitor, **When** the monitor auto-starts BASIC, **Then** the BASIC interpreter displays its startup message and prompt
2. **Given** BASIC is running, **When** the user types "PRINT 2+2" and presses enter, **Then** BASIC displays "4" on the next line
3. **Given** BASIC is running, **When** the user enters a simple program (10 PRINT "HELLO" / 20 GOTO 10) and types RUN, **Then** "HELLO" is printed repeatedly until break
4. **Given** a BASIC program is running, **When** the user presses Ctrl+C or break key, **Then** BASIC stops execution and returns to the prompt
5. **Given** BASIC is using RAM for program storage, **When** the user enters and lists programs, **Then** programs persist in RAM until power cycle or NEW command

---

### User Story 3 - Character LCD Display (Priority: P3)

A user has the system connected to a 2x16 or 2x20 character LCD. BASIC output can be directed to the LCD instead of (or in addition to) the serial terminal. The user can see program output on the physical LCD display.

**Why this priority**: The LCD adds a tangible, physical output device like vintage computers had. It enhances the educational experience and makes the system more self-contained. However, the system is fully functional without it using just the UART.

**Independent Test**: Can be tested by connecting an HD44780 LCD, configuring BASIC I/O vectors to output to LCD, running a BASIC program that prints text, and verifying text appears correctly on the LCD with proper initialization and timing.

**Acceptance Scenarios**:

1. **Given** an LCD is connected to the FPGA I/O pins, **When** the system powers on, **Then** the FPGA initializes the LCD (clear display, set mode, cursor settings) automatically
2. **Given** the LCD is initialized, **When** a character is written to the LCD data register, **Then** the character appears on the LCD at the current cursor position
3. **Given** BASIC is configured to output to LCD, **When** the user runs "PRINT HELLO", **Then** "HELLO" appears on the LCD display
4. **Given** the LCD is in use, **When** output exceeds one line (16 or 20 characters), **Then** text wraps to the second line correctly
5. **Given** the LCD is full (2 lines), **When** additional output is generated, **Then** the display scrolls or handles overflow according to LCD controller behavior

---

### User Story 4 - PS/2 Keyboard Input (Priority: P4)

A user connects a PS/2 keyboard to the FPGA. The user can type on the PS/2 keyboard and the input is recognized by BASIC or the monitor. This allows the system to operate standalone without requiring a computer for serial terminal access.

**Why this priority**: Keyboard input completes the standalone computer experience, but the system is fully usable with serial terminal. This is an enhancement for educational demonstrations and standalone operation.

**Independent Test**: Can be tested by connecting a PS/2 keyboard, typing keys, verifying raw scan codes are captured correctly in data register, and confirming monitor or BASIC software can decode scan codes and display characters.

**Acceptance Scenarios**:

1. **Given** a PS/2 keyboard is connected, **When** a key is pressed, **Then** the PS/2 interface captures the raw scan code (make code) and places it in the data register
2. **Given** the keyboard interface is working, **When** a character key is pressed, **Then** the scan code appears in the keyboard data register and status flag indicates data ready
3. **Given** BASIC is configured for keyboard input, **When** the user types on the PS/2 keyboard, **Then** BASIC INPUT statements read from the keyboard
4. **Given** the keyboard buffer is empty, **When** BASIC checks for input, **Then** the status register correctly indicates no data available
5. **Given** multiple keys are pressed rapidly, **When** BASIC reads input, **Then** characters are buffered and read in correct sequence without loss

---

### User Story 5 - Combined LCD and Keyboard Operation (Priority: P5)

A user operates the system with only the PS/2 keyboard for input and the character LCD for output, creating a completely standalone retro computer without requiring a PC and serial terminal.

**Why this priority**: This represents the ultimate "vintage computer" experience, but requires both Stories 3 and 4 to be complete. It's the final integration story.

**Independent Test**: Can be tested by disconnecting serial terminal, using only keyboard and LCD, running BASIC programs, and verifying complete input/output cycle works without serial connection.

**Acceptance Scenarios**:

1. **Given** keyboard and LCD are connected but no serial terminal, **When** the system powers on, **Then** the monitor prompt appears on the LCD and accepts keyboard input
2. **Given** BASIC is running with LCD and keyboard, **When** the user types a BASIC program using only the keyboard and runs it, **Then** output appears only on the LCD
3. **Given** a standalone configuration, **When** the user interacts with BASIC (input, output, program entry, execution), **Then** the system operates identically to serial terminal operation

---

### Edge Cases

- What happens when the CPU attempts to write to ROM address space?
  - Writes to ROM regions should be ignored (no bus error) as per typical 6502 behavior
- What happens when undefined memory regions are accessed (gaps in memory map or reserved I/O space $C300-$DFFF)?
  - Reads return undefined data (typically $FF or last bus value), writes are ignored without error
- What happens when I/O registers are accessed while devices are not ready?
  - Status registers must correctly reflect not-ready state; reads/writes should not hang the CPU
- What happens when the UART receives data faster than the 6502 can read it?
  - UART should set overflow flag in status register; oldest data may be lost (simple UART without FIFO)
- What happens when the LCD is sent commands too quickly (timing violations)?
  - LCD controller in FPGA must enforce proper timing delays; commands should be queued or delayed automatically
- What happens during power-on if the clock is not stable or reset is not clean?
  - Reset circuitry (power-on reset and hardware button) must ensure clean reset with sufficient duration (minimum 2 clock cycles), debounced and synchronized to system clock
- What happens if the ROM hex file is missing or corrupt during synthesis?
  - Synthesis should fail with clear error message, or ROM initializes to all $EA (NOP) with warning
- What happens when BASIC program exceeds available RAM?
  - BASIC should report "OUT OF MEMORY" error and refuse to accept more program lines
- What happens when interrupt signals (IRQ/NMI) are asserted?
  - Initial implementation should support interrupt vectors; interrupt sources to be defined based on I/O devices

## Requirements *(mandatory)*

### Functional Requirements

#### CPU Requirements

- **FR-001**: System MUST use Arlet Ottens' 6502 soft core (arlet/6502 from GitHub) implementing all documented NMOS 6502 opcodes
- **FR-002**: CPU clock frequency MUST be configurable, with initial target of 1 MHz generated from main FPGA clock via clock divider
- **FR-003**: CPU MUST support standard 6502 interrupt handling (IRQ, NMI, RESET vectors)
- **FR-004**: CPU MUST present standard 6502 bus signals (16-bit address, 8-bit data, R/W, clock)
- **FR-005**: Undocumented opcodes are NOT required and may behave as NOP or undefined

#### Memory Requirements

- **FR-006**: System MUST provide full 64 KB address space mapped to FPGA block RAM
- **FR-007**: Memory map MUST be implemented as specified:
  - $0000–$7FFF: 32 KB RAM (read/write)
  - $8000–$BFFF: 16 KB ROM (Microsoft BASIC)
  - $C000–$DFFF: 8 KB memory-mapped I/O region
  - $E000–$FFFF: 8 KB ROM (monitor program and vectors)
- **FR-007a**: I/O device address assignments MUST use page-aligned 256-byte blocks within $C000-$DFFF region:
  - $C000–$C0FF: UART registers (data, status, control)
  - $C100–$C1FF: LCD registers (data, command)
  - $C200–$C2FF: PS/2 keyboard registers (data, status)
  - $C300–$DFFF: Reserved for future I/O expansion
- **FR-008**: RAM MUST support single-cycle read and write operations synchronized to CPU clock
- **FR-009**: ROM MUST be initialized from hexadecimal or memory initialization files during synthesis
- **FR-010**: System MUST include address decoder logic to route accesses to correct memory regions and I/O devices
- **FR-011**: Writes to ROM address space MUST be ignored without causing bus errors

#### UART Requirements

- **FR-012**: System MUST include a memory-mapped UART with 8N1 serial format (8 data bits, no parity, 1 stop bit)
- **FR-013**: UART baud rate MUST be configurable, with default of 9600 baud
- **FR-014**: UART MUST provide at least two memory-mapped registers: data register and status register
- **FR-015**: UART status register MUST indicate: transmit buffer empty, receive data ready, and optionally receive overrun
- **FR-016**: UART MUST be usable for bidirectional communication (send and receive characters)
- **FR-017**: UART receive MUST not block CPU when no data is available (status flag indicates ready state)

#### LCD Requirements

- **FR-018**: System MUST include HD44780-compatible character LCD controller supporting 2-line displays (2x16 or 2x20) using 4-bit parallel interface mode (4 data lines + 3 control lines, fitting on single PMOD connector)
- **FR-019**: LCD controller MUST handle initialization sequence automatically on system reset, including 4-bit mode configuration
- **FR-020**: LCD MUST provide memory-mapped registers for data and control/command access
- **FR-021**: LCD controller MUST enforce proper timing requirements (enable pulse width, setup/hold times, command delays)
- **FR-022**: LCD controller MUST support basic commands: clear display, cursor positioning, display on/off, character write
- **FR-023**: LCD interface timing MUST be generated in FPGA logic; CPU should not be responsible for bit-level timing

#### Keyboard Requirements

- **FR-024**: System MUST include PS/2 keyboard interface supporting standard PS/2 protocol
- **FR-025**: PS/2 interface MUST provide raw scan codes (make and break codes) in data register; software is responsible for ASCII conversion
- **FR-026**: Keyboard MUST provide memory-mapped registers: data register (scan code) and status register (data ready flag, make/break indicator)
- **FR-027**: Keyboard interface MUST handle PS/2 clock and data signals according to PS/2 specification
- **FR-028**: Keyboard data buffer MUST be readable without blocking when no data is available

#### Software Requirements

- **FR-029**: System MUST include Microsoft 6502 BASIC in ROM (MIT licensed version)
- **FR-030**: System MUST include minimal monitor program in ROM providing:
  - Memory examine command (display memory contents)
  - Memory deposit command (write to RAM) or jump to address command
  - Auto-start to BASIC capability
- **FR-031**: BASIC I/O vectors MUST be configured to use UART for character I/O as default
- **FR-032**: BASIC I/O vectors SHOULD be reconfigurable to use LCD and keyboard when available
- **FR-032a**: Monitor and BASIC software MUST include PS/2 scan code to ASCII decoding logic (handle make/break codes, shift states, common keys)
- **FR-033**: ROM MUST contain valid 6502 reset vector pointing to monitor initialization code
- **FR-034**: ROM MUST contain valid IRQ and NMI vectors (may point to simple RTI handlers initially)

#### System Requirements

- **FR-035**: System MUST use a single master clock with clock enable signals for timing control (avoid multiple clock domains)
- **FR-036**: System MUST provide clean reset signal synchronized to system clock, driven by both power-on reset circuit and hardware reset button
- **FR-036a**: Hardware reset button MUST be debounced and synchronized to system clock before use
- **FR-037**: System reset MUST initialize all I/O devices to known states
- **FR-038**: System MUST be synthesizable using Yosys and routable using nextpnr for Lattice ECP5 FPGA
- **FR-039**: System MUST target Colorlight i5 development board with pin assignments documented
- **FR-040**: System design MUST prioritize clarity and debuggability over maximum clock frequency

### Key Entities

- **CPU Core**: 6502-compatible processor implementing fetch-decode-execute cycle, registers (A, X, Y, SP, PC, Status), and instruction execution
- **Address Space**: 64 KB logical memory space divided into RAM, ROM, and I/O regions
- **RAM Block**: 32 KB read/write memory for program variables, stack, and data storage (zero page and general purpose)
- **ROM Blocks**: Two ROM regions totaling 24 KB containing BASIC interpreter and monitor firmware
- **UART Device**: Serial communication interface with configurable baud rate, transmit/receive registers, and status flags
- **LCD Controller**: Character display controller managing HD44780 command sequences, timing, and character output
- **PS/2 Interface**: Keyboard interface implementing PS/2 protocol and raw scan code reception (make/break codes); ASCII conversion performed by software
- **Address Decoder**: Combinational logic determining which memory or I/O device responds to each address
- **Clock Generator**: Clock division and enable generation logic producing CPU clock from FPGA master clock
- **Reset Controller**: Power-on reset circuit and hardware button reset with debouncing, synchronization, and proper pulse generation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully boots and executes first instruction from reset vector within 10 microseconds of reset release
- **SC-002**: Monitor program displays prompt on serial terminal within 100 milliseconds of power-on
- **SC-003**: User can execute complete memory examine and jump command sequence via UART in under 5 seconds
- **SC-004**: Microsoft BASIC starts and displays ready prompt within 500 milliseconds of monitor handoff
- **SC-005**: BASIC correctly executes arithmetic operations (PRINT 2+2 returns 4) within 100 milliseconds
- **SC-006**: BASIC FOR loop program (100 iterations) completes in under 1 second at 1 MHz CPU clock
- **SC-007**: System operates continuously for 1 hour without errors, lockups, or resets during interactive BASIC session
- **SC-008**: LCD displays initialization message within 200 milliseconds of power-on (when LCD is connected)
- **SC-009**: Characters typed on PS/2 keyboard appear in BASIC input within 100 milliseconds (when keyboard is connected)
- **SC-010**: System synthesizes successfully using Yosys and fits on Lattice ECP5 FPGA with at least 20% resource headroom (LUTs, BRAMs)
- **SC-011**: Learner can progress from power-on to running first BASIC program in under 2 minutes following quickstart guide
- **SC-012**: System design contains clear module boundaries with no circular dependencies between CPU, memory, and I/O modules

### Learning Outcomes (Educational Success Criteria)

- **SC-013**: Learner can identify and explain the role of each major component (CPU, RAM, ROM, I/O) by examining module structure
- **SC-014**: Learner can modify memory map by changing address decoder constants and successfully resynthesize
- **SC-015**: Learner can add a new memory-mapped I/O device following patterns established by existing UART/LCD modules
- **SC-016**: System documentation enables learner to understand 6502 address space, instruction execution, and I/O concepts without prior FPGA experience

## Assumptions

- **A-001**: Colorlight i5 board provides sufficient I/O pins for UART (2 pins), LCD (7 pins for 4-bit mode via PMOD), PS/2 keyboard (2 pins), and has hardware buttons available for reset and user controls
- **A-002**: FPGA master clock is stable and adequate frequency (25 MHz or higher) for generating 1 MHz CPU clock via division
- **A-003**: Arlet Ottens' 6502 soft core (arlet/6502) is available, compatible with Yosys synthesis, and suitable for this educational project
- **A-004**: Microsoft 6502 BASIC binary is available under MIT license and can be converted to hex/mem format
- **A-005**: A simple monitor program can be written in 6502 assembly (a few hundred bytes) providing basic functionality
- **A-006**: Standard serial terminal software (minicom, PuTTY, screen) is available on user's computer for UART access
- **A-007**: HD44780 LCD modules are readily available, support 4-bit mode operation, and pinout is compatible with FPGA 3.3V I/O on PMOD connector (or level shifters are used if needed)
- **A-008**: PS/2 keyboards are still available or USB-to-PS/2 adapters work correctly for this application
- **A-009**: Yosys and nextpnr toolchains are installed and functional on the development system
- **A-010**: User has basic familiarity with FPGA development flow (synthesis, place-and-route, bitstream generation)
- **A-011**: The design will initially target functionality over performance; clock speed optimization is not a primary goal
- **A-012**: Bus timing will be simple (single cycle for RAM/ROM, multi-cycle for I/O if needed); no wait states required initially

## Constraints

- **C-001**: Must use only Verilog (not SystemVerilog) to ensure compatibility with Yosys open-source toolchain
- **C-002**: Must target Lattice ECP5 FPGA architecture specifically (Colorlight i5 board variant)
- **C-003**: Must use only open-source tools: Yosys for synthesis, nextpnr for place-and-route, no proprietary vendor tools
- **C-004**: Must fit within Colorlight i5 FPGA resources (specific ECP5 variant on that board, typically 25K or 45K LUTs)
- **C-005**: Must use single clock domain architecture; no crossing clock domains without proper synchronization
- **C-006**: I/O pin assignments must match Colorlight i5 board layout and available connectors
- **C-006a**: LCD interface must fit on a single PMOD connector (7 pins for 4-bit mode)
- **C-007**: Design must be modular with clear boundaries to support incremental development and testing
- **C-008**: ROM size limited to 24 KB total (16 KB for BASIC, 8 KB for monitor) based on memory map specification
- **C-009**: No external memory devices; all RAM and ROM must be implemented in FPGA block RAM
- **C-010**: UART baud rate clock generation must be derived from FPGA master clock using available dividers

## Out of Scope (Non-Goals)

- **OOS-001**: Bitmap video output, VGA display, or graphical capabilities (text LCD only)
- **OOS-002**: Mass storage devices (SD card, disk controller, tape interface)
- **OOS-003**: Cycle-exact emulation of specific commercial systems (Apple II, Commodore PET, BBC Micro timing)
- **OOS-004**: Undocumented 6502 opcodes or CMOS 65C02 extended instructions
- **OOS-005**: Audio output or sound generation capabilities
- **OOS-006**: Multiple CPU configurations or clock speed selection beyond initial configurable divider
- **OOS-007**: Network connectivity (Ethernet, WiFi)
- **OOS-008**: Real-time clock or calendar functions
- **OOS-009**: DMA controller or advanced bus arbitration
- **OOS-010**: Extensive debugging facilities beyond basic serial monitor (no JTAG, logic analyzer integration)
- **OOS-011**: Support for other FPGA boards or vendors in initial version
- **OOS-012**: Compatibility with proprietary FPGA development tools

## Future Extensions

The following capabilities are explicitly out of scope for the initial version but are identified as potential future enhancements:

- **EXT-001**: VGA text mode output (80x25 character display) replacing or augmenting LCD
- **EXT-002**: SD card interface for loading/saving BASIC programs
- **EXT-003**: Simple audio output (1-bit piezo or PWM speaker) for beeps and tones
- **EXT-004**: Multiple pre-configured memory maps selectable via switch or ROM patch
- **EXT-005**: Apple II compatibility mode (with appropriate video and I/O emulation)
- **EXT-006**: 65C02 CMOS variant support with extended instruction set
- **EXT-007**: Cassette tape interface emulation (audio encoding/decoding)
- **EXT-008**: Expansion bus interface allowing external hardware modules
- **EXT-009**: Higher resolution LCD (4x20) or graphical LCD support
- **EXT-010**: Joystick or game controller interface
- **EXT-011**: Real-time clock module for date/time functions in BASIC
- **EXT-012**: Multiple BASIC variants (Applesoft, CBM BASIC) selectable at boot

## Dependencies

- **D-001**: Arlet Ottens' 6502 soft core from GitHub (https://github.com/Arlet/verilog-6502)
- **D-002**: Microsoft 6502 BASIC binary in format suitable for ROM initialization
- **D-003**: 6502 assembler for monitor program development (e.g., ca65, AS65, or other open-source assembler)
- **D-004**: Tools to convert assembled binary to hex or mem file format for Verilog ROM initialization
- **D-005**: Colorlight i5 board documentation for pinout and resource specifications
- **D-006**: HD44780 LCD datasheet for timing requirements and command set
- **D-007**: PS/2 keyboard protocol specification or existing PS/2 interface core
- **D-008**: Yosys synthesis tool and nextpnr place-and-route tool properly installed and configured
- **D-009**: Standard serial terminal software for UART testing and interaction
- **D-010**: cocotb testing framework for HDL module verification per project constitution
