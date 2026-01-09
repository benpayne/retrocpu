# Feature Specification: Program Loader and I/O Configuration

**Feature Branch**: `004-program-loader-io-config`
**Created**: 2026-01-01
**Status**: Draft
**Input**: User description: "We need to create a way to run programs from our monitor. We don't want to have to update ROM to load new code to the system. So we want to be able to load code into RAM and run it. We should have the ability to do this for compiled code as well as BASIC. We can use the UART to transfer the data across, something that can deal with binary data, is that kermit or something like that? I think this would be a command to the monitor to put it into a mode to recieve the data. For basic I guess we can just hit G and then use the UART to send the text over. So that's kind of supported already. The other thing I'd like to do is switch over to using the PS2 keyboard for input and the DVI/HDMI display for output. We should allow for easy control in the monitor to support input from UART, PS2 or both. And for output to UART, Display or Both."

## User Scenarios & Testing

### User Story 1 - Binary Program Upload via UART (Priority: P1)

As a developer, I want to upload compiled 6502 binary programs to RAM over UART so that I can run and test new code without reprogramming the ROM.

**Why this priority**: This is the foundational capability that enables all dynamic program loading. Without this, developers must rebuild and reflash ROM for every code change, which is time-consuming and wears flash memory. This represents the MVP for the feature.

**Independent Test**: Can be fully tested by uploading a simple binary program (e.g., LED blink routine) via UART, executing it with the monitor's Go command, and observing the expected behavior (LED blinking). Delivers immediate value by eliminating ROM reflash cycles during development.

**Acceptance Scenarios**:

1. **Given** the monitor is running, **When** the user enters the binary upload command, **Then** the monitor enters binary receive mode and displays a ready indicator
2. **Given** the monitor is in binary receive mode, **When** binary data is transmitted via UART, **Then** the data is written sequentially to the specified RAM address range
3. **Given** a binary program has been uploaded to RAM, **When** the user executes the Go command with the program's start address, **Then** the program executes from RAM
4. **Given** a binary transfer is in progress, **When** a transfer error occurs (timeout, checksum failure), **Then** the monitor reports the error and allows retry without corruption
5. **Given** binary data is being received, **When** the upload completes successfully, **Then** the monitor confirms the byte count and returns to command mode

---

### User Story 2 - I/O Source Configuration (Priority: P1)

As a user, I want to configure the monitor to use PS/2 keyboard and/or HDMI display for input/output so that I can operate the system standalone without a PC connection.

**Why this priority**: This is equally critical as P1 because it enables standalone operation. Many users want to use the system as a traditional retro computer with keyboard and display, not just via serial terminal. The two P1 features are complementary - program loading enables development, I/O configuration enables usage.

**Independent Test**: Can be tested by switching I/O modes via monitor command and verifying that input (keystrokes) and output (characters) appear on the selected device(s). For example, configure display output, type commands on PS/2 keyboard, and see results on HDMI screen. Delivers immediate standalone operation capability.

**Acceptance Scenarios**:

1. **Given** the monitor is running with UART I/O, **When** the user switches to PS/2 input via monitor command, **Then** subsequent keystrokes are read from the PS/2 keyboard instead of UART
2. **Given** the monitor is running with UART output, **When** the user switches to display output via monitor command, **Then** subsequent text output appears on the HDMI/DVI display instead of UART
3. **Given** I/O is configured for a specific source, **When** the system resets, **Then** the I/O configuration persists (default: UART for both, or user-configured preference)
4. **Given** dual input mode is enabled (UART + PS/2), **When** input arrives from either source, **Then** the monitor accepts and processes the input regardless of source
5. **Given** dual output mode is enabled (UART + Display), **When** the monitor outputs text, **Then** the same text appears on both UART and display simultaneously

---

### User Story 3 - BASIC Program Text Loading (Priority: P2)

As a BASIC programmer, I want to paste or upload BASIC program text via UART so that I can develop and test BASIC programs without typing them line-by-line at the monitor prompt.

**Why this priority**: This enhances developer productivity for BASIC programming but is secondary to binary program loading (P1). Users can already enter BASIC programs manually; this just makes it more convenient. The Go command already supports entering BASIC immediate mode.

**Independent Test**: Can be tested by configuring UART input, entering BASIC via the Go command, then pasting a multi-line BASIC program from a terminal emulator and verifying it is received correctly and can be executed with RUN.

**Acceptance Scenarios**:

1. **Given** BASIC is running (via Go command), **When** the user pastes BASIC program text with line numbers via UART, **Then** each line is accepted as if typed manually
2. **Given** a BASIC program is being pasted, **When** transmission is too fast for input processing, **Then** flow control (XON/XOFF or hardware handshaking) prevents data loss
3. **Given** BASIC text is being received, **When** the program is complete, **Then** the user can execute it immediately with RUN command
4. **Given** BASIC is active on display output, **When** the user types on the PS/2 keyboard, **Then** the characters appear on screen and are processed by BASIC

---

### User Story 4 - I/O Status Display (Priority: P3)

As a user, I want to see which I/O devices are currently active for input and output so that I understand the current system configuration.

**Why this priority**: This is a quality-of-life feature for user experience but not essential for functionality. Users can infer the configuration from behavior, but explicit status display improves usability and reduces confusion.

**Independent Test**: Can be tested by querying I/O status via monitor command and verifying the displayed configuration matches the actual active devices.

**Acceptance Scenarios**:

1. **Given** the monitor is running, **When** the user requests I/O status, **Then** the monitor displays which devices are active for input (UART/PS2/Both) and output (UART/Display/Both)
2. **Given** I/O configuration has been changed, **When** the user requests status, **Then** the displayed status reflects the current configuration
3. **Given** a device is configured but not physically present (e.g., PS/2 keyboard unplugged), **When** status is queried, **Then** the monitor indicates the device is configured but not detected

---

### Edge Cases

- **Large binary uploads**: What happens when the uploaded program exceeds available RAM space? (Should validate address range and reject if it would overflow into ROM or I/O space)
- **Binary transfer interruption**: How does the system handle incomplete uploads? (Should discard partial data and report failure; retry is user's responsibility)
- **I/O switching mid-operation**: What happens if I/O is switched while a program is running or BASIC is active? (Configuration change should take effect immediately; running programs continue with new I/O)
- **Dual input conflict**: How does the system handle simultaneous input from UART and PS/2? (First-come-first-served; both sources feed same input buffer)
- **Display vs UART output differences**: How are control characters handled differently on display vs UART? (UART sends raw, display interprets ANSI/control codes for cursor movement, clearing, etc.)
- **Binary data containing flow control characters**: How does XMODEM/Kermit protocol handle XON/XOFF bytes in binary data? (Protocol must escape or frame data to avoid false flow control)

## Requirements

### Functional Requirements - Binary Program Loading

- **FR-001**: Monitor MUST provide a command (e.g., 'L' for Load) that enters binary receive mode and accepts parameters for target RAM address and byte count
- **FR-002**: Monitor MUST support XMODEM protocol for reliable binary file transfer with error detection and correction (assumes standard XMODEM with 128-byte packets and checksum)
- **FR-003**: Monitor MUST validate that the target address range falls within RAM (not ROM or I/O space) before accepting data
- **FR-004**: Binary receive mode MUST display real-time transfer progress (bytes received, percentage if count is known)
- **FR-005**: Monitor MUST verify transfer integrity via checksum or CRC and report success/failure to the user
- **FR-006**: After successful binary upload, monitor MUST allow immediate execution via Go command to the start address
- **FR-007**: Monitor MUST provide a timeout mechanism (default 30 seconds) to exit binary receive mode if no data arrives
- **FR-008**: Binary uploads MUST support address ranges from $0200 to $7FFF (general RAM, avoiding zero page, stack, and ROM)

### Functional Requirements - I/O Configuration

- **FR-009**: Monitor MUST provide a command (e.g., 'I' for I/O config) to configure input source: UART only, PS/2 only, or both
- **FR-010**: Monitor MUST provide a command to configure output destination: UART only, Display only, or both
- **FR-011**: I/O configuration changes MUST take effect immediately (next character read/write uses new configuration)
- **FR-012**: Monitor MUST default to UART for both input and output on power-up or reset (maintains compatibility with existing serial workflow)
- **FR-013**: When dual input mode is active, monitor MUST accept input from whichever source provides it first (non-blocking, event-driven)
- **FR-014**: When dual output mode is active, monitor MUST send each output character to both UART and display (synchronized)
- **FR-015**: PS/2 keyboard input MUST be mapped to ASCII characters compatible with monitor command processing (printable chars, Enter, Backspace, etc.)
- **FR-016**: Display output MUST support monitor command responses, memory dumps, and program output with readable formatting

### Functional Requirements - BASIC Text Loading

- **FR-017**: When BASIC is running (entered via Go $8000 or equivalent), UART input MUST be passed directly to BASIC interpreter without monitor intervention
- **FR-018**: BASIC MUST accept pasted text with line numbers (standard BASIC format: "10 PRINT 'HELLO'")
- **FR-019**: UART interface MUST implement flow control (XON/XOFF software handshaking or RTS/CTS hardware handshaking) to prevent data loss during BASIC program paste
- **FR-020**: After loading a BASIC program via paste, user MUST be able to execute it with standard BASIC commands (RUN, LIST, etc.)

### Key Entities

- **Binary Program**: A sequence of 6502 machine code bytes loaded into RAM at a specified address, ready for execution
- **I/O Configuration**: The current selection of active input source(s) and output destination(s), stored in monitor state
- **Transfer Protocol State**: The state machine tracking XMODEM packet reception, including packet number, checksum validation, and retry logic
- **Input Buffer**: A queue that aggregates characters from active input sources (UART and/or PS/2) for processing by the monitor or running program
- **Output Router**: Logic that duplicates output to all active destinations (UART and/or Display) based on configuration

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can upload a 1KB binary program via UART in under 10 seconds (including protocol overhead)
- **SC-002**: Binary transfer success rate exceeds 99% under normal conditions (no line noise)
- **SC-003**: I/O configuration changes take effect within 1 character time (instantaneous from user perspective)
- **SC-004**: Users can operate the monitor entirely from PS/2 keyboard and view all output on display without needing a PC serial connection
- **SC-005**: BASIC programs pasted via UART are received without line loss or corruption when flow control is active
- **SC-006**: Dual output mode produces identical text on both UART and display (character-for-character match)
- **SC-007**: 90% of developers successfully upload and run a test program on their first attempt without consulting documentation (after initial learning)
- **SC-008**: Transfer errors (checksum failure, timeout) are clearly reported to the user with actionable recovery instructions

## Assumptions

- **Binary Transfer Protocol**: XMODEM is assumed as it is simple, widely supported by terminal emulators (Tera Term, minicom, etc.), and suitable for low-speed serial links. Alternative protocols (YMODEM, Kermit, ZMODEM) could be substituted if XMODEM proves inadequate.
- **Flow Control**: XON/XOFF software flow control is assumed for BASIC text paste as it requires no additional hardware. Hardware RTS/CTS could be added if the UART peripheral supports it.
- **PS/2 Keyboard Support**: Assumes existing PS/2 peripheral (referenced in project) is functional and provides ASCII-mapped character events.
- **Display Output**: Assumes existing DVI/HDMI GPU (003-hdmi-character-display) can be used for monitor output via character-at-a-time writes to the GPU's CHAR_DATA register.
- **Default I/O Configuration**: UART-only on reset maintains backward compatibility with existing serial terminal workflow; users opt-in to display/keyboard mode.
- **RAM Address Range**: Binary programs are restricted to $0200-$7FFF to avoid corrupting zero page ($0000-$00FF), stack ($0100-$01FF), and ROM/I/O ($8000-$FFFF).
- **BASIC Integration**: Assumes BASIC interpreter (referenced in project) can be entered via monitor Go command and that UART input during BASIC execution bypasses monitor command parsing.

## Non-Functional Requirements

- **Compatibility**: Binary upload feature must work with standard terminal emulators (Tera Term, PuTTY, minicom, screen) without custom client software
- **Robustness**: Transfer errors must not crash the monitor or corrupt system state; monitor must remain responsive after failed transfers
- **Usability**: Monitor commands for I/O configuration and program loading must be concise (single-letter preferred) and follow existing monitor command conventions
- **Performance**: Binary transfer must utilize full available UART bandwidth (9600 baud baseline, higher if baud rate is configurable)

## Dependencies

- **PS/2 Peripheral**: I/O configuration feature depends on PS/2 keyboard peripheral being integrated and functional
- **DVI/HDMI GPU**: Display output depends on GPU character display (feature 003) being operational
- **BASIC Interpreter**: BASIC text loading depends on BASIC interpreter being present and accessible via monitor
- **UART Peripheral**: All features depend on existing UART functioning correctly for serial communication

## Out of Scope

- **GUI File Browser**: This feature provides command-line program loading only; no graphical file selection interface
- **Persistent Storage**: Binary programs are loaded into RAM only; saving to non-volatile storage (SD card, flash) is not included
- **Debugger Features**: Program loading enables execution but does not include breakpoints, single-stepping, or memory watch features
- **Network Loading**: Transfer is limited to UART serial connection; Ethernet, WiFi, or other network protocols are out of scope
- **Binary Format Conversion**: Monitor loads raw binary data only; conversion from hex files, ELF, or other formats must be done externally
- **Automatic Baud Rate Detection**: UART baud rate is fixed (or manually configured); automatic detection is not included
