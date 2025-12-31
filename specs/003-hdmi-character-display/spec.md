# Feature Specification: DVI Character Display GPU

**Feature Branch**: `003-hdmi-character-display`
**Created**: 2025-12-27
**Status**: Draft
**Input**: User description: "I want to start a new feature that is to create a GPU for this project. The colorlight i5 board and carrier board has support for HDMI. I want to use this to create this GPU, initially let's focus on getting a character display. This should be similar to how a commador or an apple II worked. I presume we'll have a single register that we can write chars to and they'll get displayed, we'll have a second reg for control things, like clear screen or moving to specific lines/columns. Let's emaulate a 40 column and 80 column display. We'll need to drive the HDMI signals for this. this repo claims to get gotten this to work on the colorlight i5 https://github.com/splinedrive/my_hdmi_device. So we can leverage this code and even use this to prove out the hardware setup."

**Note**: This feature uses DVI signaling (digital video without audio) over the physical HDMI connector, not true HDMI with audio support.

## User Scenarios & Testing

### User Story 1 - Basic Character Output (Priority: P1)

As a developer, I want to write ASCII characters to video memory and see them displayed on a monitor, so that I can provide basic text output for the retrocpu system.

**Why this priority**: This is the foundation of the GPU - without the ability to display characters, no other functionality matters. This represents the MVP that proves DVI connectivity and basic video generation work.

**Independent Test**: Can be fully tested by writing a single character to the character data register and verifying it appears at the expected screen position on the display. Delivers immediate visual feedback that the hardware connection and video signal generation are working.

**Acceptance Scenarios**:

1. **Given** the system is powered on and display is connected, **When** firmware writes ASCII value 0x41 ('A') to the character data register, **Then** the letter 'A' appears at the current cursor position on screen
2. **Given** the display is showing characters, **When** firmware writes ASCII value 0x20 (space) to the character data register, **Then** a blank space appears at the cursor position
3. **Given** the cursor is at column 39 of a 40-column display, **When** firmware writes a character, **Then** the character appears at column 39 and cursor wraps to column 0 of the next line
4. **Given** the display is in 80-column mode, **When** firmware writes 80 characters, **Then** all 80 characters appear on a single line before wrapping

---

### User Story 2 - Display Mode Configuration (Priority: P2)

As a developer, I want to switch between 40-column and 80-column display modes, so that I can choose the appropriate character density for different applications.

**Why this priority**: Mode switching is essential for emulating both Commodore-style (40 column) and modern terminal-style (80 column) displays, but it's not needed for the initial MVP.

**Independent Test**: Can be tested by writing to the control register to set display mode, then writing a full line of text and verifying the correct number of columns before wrapping occurs.

**Acceptance Scenarios**:

1. **Given** the system starts in default 40-column mode, **When** firmware explicitly sets 40-column mode via control register, **Then** subsequent text continues to display with 40 characters per line
2. **Given** the system is in 40-column mode with text displayed, **When** firmware switches to 80-column mode, **Then** the screen clears, cursor resets to (0,0), and new text follows 80-column layout
3. **Given** the system is in 80-column mode with text displayed, **When** firmware switches to 40-column mode, **Then** the screen clears, cursor resets to (0,0), and new text follows 40-column layout

---

### User Story 3 - Screen Control Operations (Priority: P2)

As a developer, I want to clear the screen, move the cursor to specific positions, and control where text appears, so that I can create formatted text displays and user interfaces.

**Why this priority**: Control operations are essential for creating usable text interfaces, but basic character output must work first.

**Independent Test**: Can be tested by writing characters, issuing a clear screen command via control register, and verifying all positions return to blank/default state. Cursor positioning can be tested by setting row/column values and verifying next character appears at that position.

**Acceptance Scenarios**:

1. **Given** the screen contains text, **When** firmware writes clear screen command to control register, **Then** all character positions are set to spaces and cursor returns to position (0,0)
2. **Given** firmware wants to write at row 10 column 20, **When** firmware writes row value 10 and column value 20 to position registers, **Then** the next character write appears at that position
3. **Given** the cursor is at position (5, 15), **When** firmware writes multiple characters without changing position, **Then** characters appear sequentially starting from (5, 15) with automatic column increment
4. **Given** firmware sets cursor to an invalid position beyond screen bounds, **When** the position is set, **Then** position is clamped to valid screen dimensions

---

### User Story 4 - DVI Signal Generation (Priority: P1)

As a user, I want the system to generate valid DVI video signals at standard resolution, so that the display works with common monitors without configuration.

**Why this priority**: This is foundational infrastructure - without proper DVI signaling, nothing will display. This must work for P1 MVP.

**Independent Test**: Can be tested by connecting to multiple DVI/HDMI monitors and verifying sync/detection occurs and a stable image appears (even if just a blank screen or test pattern initially).

**Acceptance Scenarios**:

1. **Given** a monitor is connected to the colorlight i5 board via the HDMI connector, **When** the system powers on, **Then** the monitor detects a valid DVI video signal and displays the output
2. **Given** the system is generating video, **When** displaying a full screen of text, **Then** the image is stable with no flicker, tearing, or sync issues
3. **Given** the video output is active, **When** observed over 1 hour of operation, **Then** the display remains stable without artifacts or signal loss

---

### User Story 5 - Visual Cursor Display (Priority: P2)

As a developer, I want to see a flashing cursor at the current input position, so that I know where the next character will appear when typing.

**Why this priority**: A visible cursor is essential for interactive text input and debugging, making the system feel like a real terminal. Not critical for initial MVP but important for usability.

**Independent Test**: Can be tested by observing the cursor position on screen and verifying it flashes at a regular interval (approximately 1-2Hz) and moves correctly when cursor position changes.

**Acceptance Scenarios**:

1. **Given** the display is active, **When** no characters are being written, **Then** a cursor block flashes at the current cursor position at approximately 1Hz
2. **Given** the cursor is at position (5, 10), **When** firmware moves the cursor to position (7, 20), **Then** the flashing cursor appears at the new position within one refresh cycle
3. **Given** the cursor is flashing, **When** firmware writes a character, **Then** the character appears and the cursor moves to the next position and continues flashing
4. **Given** the cursor is visible, **When** firmware disables cursor display via control register, **Then** the cursor stops being displayed

---

### User Story 6 - Color Configuration (Priority: P2)

As a developer, I want to configure the foreground and background colors of displayed text, so that I can create visually distinct interfaces and highlight important information.

**Why this priority**: Color control enhances readability and allows for visual hierarchy in user interfaces. The default white-on-black will work for MVP, but color control adds significant value for applications.

**Independent Test**: Can be tested by writing color values to color control registers and verifying text renders in the specified colors on screen.

**Acceptance Scenarios**:

1. **Given** the system powers on, **When** no color settings have been written, **Then** text displays as white foreground on black background (default)
2. **Given** the display is showing text, **When** firmware writes a new foreground color value, **Then** subsequently written characters appear in the new foreground color
3. **Given** the display is showing text, **When** firmware writes a new background color value, **Then** subsequently written characters appear with the new background color
4. **Given** both foreground and background colors are set, **When** firmware writes the screen clear command, **Then** the screen clears using the current background color

---

### Edge Cases

- What happens when firmware writes characters faster than the display refresh rate can handle?
- How does the system handle extended ASCII codes (0x80-0xFF)?
- What happens when the cursor advances past the last row of the display?
- How does the system behave if the DVI cable is disconnected during operation?
- What happens if firmware writes to position registers while a character write is in progress?
- What happens if foreground and background colors are set to the same value (text becomes invisible)?
- How does the cursor appear when foreground/background colors change?
- What happens to the cursor flash state during screen clear operations?

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate valid DVI video signals compatible with standard DVI/HDMI monitors (digital video only, no audio)
- **FR-002**: System MUST support 40-column display mode with 25 rows of text
- **FR-003**: System MUST support 80-column display mode with 25 rows of text
- **FR-021**: System MUST default to 40-column display mode on power-up or reset
- **FR-022**: System MUST clear the screen and reset cursor to (0,0) when switching between 40-column and 80-column display modes
- **FR-004**: System MUST provide a memory-mapped character data register that accepts 8-bit ASCII values
- **FR-005**: System MUST provide a memory-mapped control register for display commands (clear screen, set mode, cursor enable/disable)
- **FR-006**: System MUST provide memory-mapped position registers for setting cursor row and column
- **FR-007**: System MUST automatically advance cursor position after each character write
- **FR-008**: System MUST wrap cursor to next line when reaching end of current line
- **FR-009**: System MUST support rendering all printable ASCII characters (0x20-0x7E)
- **FR-023**: System MUST display a placeholder glyph (visible indicator such as solid block or question mark) when firmware writes non-printable ASCII characters (0x00-0x1F, 0x7F)
- **FR-010**: System MUST scroll text up automatically when cursor advances past the last row, moving all lines up one position and clearing the bottom line
- **FR-011**: System MUST maintain character video memory separate from main system RAM
- **FR-012**: System MUST refresh the display at 60Hz
- **FR-013**: System MUST generate visible output at 640x480 resolution (VGA/DVI timing)
- **FR-014**: System MUST display a flashing cursor at the current cursor position with approximately 1Hz flash rate
- **FR-015**: System MUST allow firmware to enable or disable cursor visibility via control register
- **FR-016**: System MUST provide a memory-mapped foreground color register that accepts 3-bit RGB color values (8 colors: Black=0, Blue=1, Green=2, Cyan=3, Red=4, Magenta=5, Yellow=6, White=7); upper bits beyond bit 2 are masked and ignored
- **FR-017**: System MUST provide a memory-mapped background color register that accepts 3-bit RGB color values (8 colors: Black=0, Blue=1, Green=2, Cyan=3, Red=4, Magenta=5, Yellow=6, White=7); upper bits beyond bit 2 are masked and ignored
- **FR-018**: System MUST default to white foreground and black background on power-up or reset
- **FR-019**: System MUST apply color settings to all subsequently written characters
- **FR-020**: System MUST render the cursor in a visually distinct manner (inverted colors or distinct color)

### Key Entities

- **Character Cell**: Represents a single character position on screen, contains ASCII value, positioned by row and column coordinates
- **Video Frame Buffer**: Storage for all character cells currently displayed, organized as rows and columns based on display mode
- **Cursor Position**: Current row and column where next character will be written, automatically updated after writes
- **Cursor State**: Visibility flag (enabled/disabled) and current flash state (visible/invisible) for the blinking cursor
- **Display Mode**: Configuration state indicating 40-column or 80-column layout
- **Character Font**: Bitmap representation of each ASCII character used for rendering pixels (8x8 or 8x16 pixel glyphs)
- **Color Configuration**: Current foreground and background 3-bit RGB color values (0-7) applied to new character writes, representing 8-color classic palette

## Success Criteria

### Measurable Outcomes

- **SC-001**: Monitor successfully detects and displays DVI video signal from colorlight i5 output within 2 seconds of power-on
- **SC-002**: System displays readable text in both 40-column and 80-column modes without visible artifacts
- **SC-003**: Character writes from firmware appear on screen within one display refresh cycle
- **SC-004**: Display maintains stable 60Hz refresh rate without flicker or tearing
- **SC-005**: System successfully renders all 95 printable ASCII characters visibly and distinctly
- **SC-006**: Screen clear operation completes within one frame time (16.7ms at 60Hz)
- **SC-007**: Cursor positioning commands take effect for the next character write without delay
- **SC-008**: Mode switching between 40 and 80 column displays completes within 100ms, with screen clear and cursor reset
- **SC-009**: Firmware can continuously write characters at 1000 characters per second without dropped characters or display errors
- **SC-010**: Cursor flashes at a rate between 0.5Hz and 2Hz, providing clear visual indication of input position
- **SC-011**: Cursor enable/disable commands take effect within one refresh cycle
- **SC-012**: Color changes apply to the next character written with no visible delay
- **SC-013**: All configured color combinations produce readable, distinct text on screen
- **SC-014**: System defaults to white-on-black text immediately on power-up without configuration
- **SC-015**: System defaults to 40-column display mode on power-up without configuration
- **SC-016**: Non-printable ASCII characters display as a distinct, visible placeholder glyph that is easily distinguishable from printable characters

## Clarifications

### Session 2025-12-27

- Q: What color format and bit depth should the foreground/background color registers support? → A: 8 colors (3-bit RGB) - Classic palette: Black, Blue, Green, Cyan, Red, Magenta, Yellow, White
- Q: What should be the default display mode on power-up or reset? → A: 40-column mode (Commodore-style default)
- Q: What should happen to existing text when switching between 40-column and 80-column display modes? → A: Clear screen on mode switch - All text cleared, cursor reset to (0,0)
- Q: How should the system handle color register writes with values beyond the 3-bit range? → A: Mask to 3 bits, ignore upper bits - Use only lower 3 bits
- Q: How should the system handle non-printable ASCII characters (0x00-0x1F, 0x7F) when written to the character data register? → A: Display placeholder glyph - Show special symbol for unprintable characters

## Dependencies

- Colorlight i5 FPGA board with HDMI-capable carrier board (using DVI signaling over HDMI connector)
- Reference DVI/HDMI implementation from https://github.com/splinedrive/my_hdmi_device
- FPGA toolchain capable of synthesizing for colorlight i5 (yosys, nextpnr)
- Test monitor supporting DVI/HDMI input

## Assumptions

- The colorlight i5 board and carrier board have functional HDMI connectors that support DVI signaling
- DVI signaling (digital video without audio) is sufficient for this application
- The reference implementation (my_hdmi_device) provides working video signal generation code that can be adapted
- Standard VGA timing (640x480 @ 60Hz) will be used as baseline resolution, transmitted via DVI protocol
- 8x16 pixel font will be used for characters (industry standard for readable text terminals)
- Display will default to white text on black background with configurable foreground/background colors
- CPU memory-mapped I/O registers will be used for GPU interface (specific addresses to be determined during planning)
- Text scrolling will move content up one line and clear the bottom line (standard terminal behavior)
- 3-bit RGB color format (8 colors) provides classic palette matching vintage computer aesthetics while minimizing FPGA resource usage
- Color registers mask upper bits (only bits 0-2 used), ensuring robust handling of any write value without validation logic
- Non-printable characters will be rendered using a placeholder glyph (specific glyph choice to be determined during planning - options include solid block, checkerboard pattern, or question mark symbol)
- Cursor will be rendered as a solid block character (inverse video of character cell)
