# Feature Specification: M65C02 CPU Core Port

**Feature Branch**: `002-m65c02-port`
**Created**: 2025-12-23
**Status**: Draft
**Input**: Port from Arlet 6502 to M65C02 CPU core to fix zero page write bug

## Overview

This specification defines the port of the existing 6502 FPGA microcomputer from the Arlet 6502 CPU core to the M65C02 CPU core. This port is necessary to resolve a critical hardware bug where all zero page memory writes ($0000-$00FF) fail, completely blocking BASIC interpreter functionality, monitor commands, and any complex 6502 programs.

**Root Cause**: The Arlet 6502 core's DIMUX signal logic is incompatible with using the RDY signal for clock division via clock enable pulses. When RDY pulses high for CPU execution, DIMUX switches to the data bus which contains incorrect data (RAM readback instead of the operand), corrupting zero page addresses.

**Solution**: The M65C02 core features a built-in microcycle controller specifically designed for flexible FPGA memory timing, which properly handles clock division without the RDY signal incompatibility.

## User Scenarios & Testing

### User Story 1 - Core Integration and Boot Verification (Priority: P1)

Replace the Arlet 6502 CPU core with the M65C02 core in the system-on-chip design while preserving all existing peripherals and memory. The system must boot successfully and display the monitor prompt via UART.

**Why this priority**: This is the foundational work that must succeed before any other functionality can be validated. Without a working CPU integration, the entire system is non-functional.

**Independent Test**: Power on the FPGA after synthesis and programming. The system boots, the monitor displays its welcome message and prompt on the serial terminal, demonstrating successful CPU integration with memory and UART.

**Acceptance Scenarios**:

1. **Given** the M65C02 core is integrated into soc_top.v, **When** the FPGA is programmed and powered on, **Then** the system boots without hanging
2. **Given** the system has booted, **When** observing the serial terminal, **Then** the monitor welcome message appears within 1 second
3. **Given** the monitor has displayed its welcome, **When** observing the serial terminal, **Then** the command prompt ("> ") is displayed
4. **Given** the reset button is pressed, **When** the button is released, **Then** the system reboots and displays the welcome message again

---

### User Story 2 - Zero Page Memory Access (Priority: P1)

All zero page memory addresses ($0000-$00FF) must support correct read and write operations. This is the primary bug fix that motivated the entire port.

**Why this priority**: Zero page memory is fundamental to 6502 operation and is the root cause of the current system failure. BASIC and monitor commands cannot function without working zero page.

**Independent Test**: Write test patterns to multiple zero page addresses (e.g., $0000, $0010, $0080, $00FF) and read them back. All values must match what was written, demonstrating zero page is fully functional.

**Acceptance Scenarios**:

1. **Given** the monitor has booted, **When** writing $11 to address $0000 and reading it back, **Then** the value read is $11 (not $00)
2. **Given** the monitor has booted, **When** writing $22 to address $0010 and reading it back, **Then** the value read is $22
3. **Given** the monitor has booted, **When** writing $33 to address $0080 and reading it back, **Then** the value read is $33
4. **Given** the monitor has booted, **When** writing $44 to address $00FF and reading it back, **Then** the value read is $44
5. **Given** multiple zero page addresses have been written, **When** reading them back in any order, **Then** all values are retained correctly

---

### User Story 3 - Monitor Command Functionality (Priority: P2)

The monitor's examine (E) and deposit (D) commands must work correctly, allowing users to inspect and modify memory contents. These commands depend on zero page for their internal variables.

**Why this priority**: The monitor provides essential debugging and memory inspection capabilities. These commands are the primary interface for verifying memory operations and were previously broken due to the zero page bug.

**Independent Test**: From the monitor prompt, execute "E 0200" to examine memory at address $0200, and execute "D 0200 AA" to deposit value $AA at that address. Both commands complete successfully and display the expected output.

**Acceptance Scenarios**:

1. **Given** the monitor prompt is displayed, **When** typing "E 0200" and pressing Enter, **Then** the memory contents at $0200 are displayed in hexadecimal
2. **Given** the monitor prompt is displayed, **When** typing "D 0200 AA" and pressing Enter, **Then** the value $AA is written to address $0200
3. **Given** a value has been deposited, **When** examining that same address, **Then** the deposited value is displayed correctly
4. **Given** the monitor prompt is displayed, **When** typing "E 0010" to examine zero page, **Then** the zero page contents are displayed (not all zeros)

---

### User Story 4 - BASIC Interpreter Operation (Priority: P2)

The BASIC interpreter (EhBASIC) must start successfully from the monitor and execute commands. BASIC depends heavily on zero page memory for variables and stack operations.

**Why this priority**: BASIC interpreter functionality is User Story 2 from the original specification and is the main feature blocked by the zero page bug. Restoring BASIC operation validates that the core port has solved the underlying issue.

**Independent Test**: From the monitor, execute the "G" command to start BASIC. The BASIC prompt appears. Type "PRINT 2+2" and press Enter. The output displays "4", demonstrating full BASIC functionality.

**Acceptance Scenarios**:

1. **Given** the monitor prompt is displayed, **When** typing "G" and pressing Enter, **Then** BASIC displays its startup message and "Ready" prompt
2. **Given** the BASIC prompt is displayed, **When** typing "PRINT 2+2" and pressing Enter, **Then** the output shows "4"
3. **Given** the BASIC prompt is displayed, **When** entering a FOR loop program and running it, **Then** the loop executes and displays repeated output correctly
4. **Given** the BASIC prompt is displayed, **When** defining a variable "A=10" and then typing "PRINT A", **Then** the output shows "10"
5. **Given** a BASIC program has been entered, **When** typing "LIST", **Then** the program listing is displayed
6. **Given** a BASIC program is loaded, **When** typing "NEW", **Then** the program is cleared

---

### User Story 5 - Memory Timing Configuration (Priority: P1)

The M65C02's microcycle controller must be correctly configured for the existing memory subsystem (synchronous block RAM, UART, ROM) to ensure proper timing and data validity.

**Why this priority**: Correct memory timing is essential for all CPU operations. Misconfigured timing will cause data corruption, system hangs, or unpredictable behavior even if the integration appears successful.

**Independent Test**: Run comprehensive memory tests accessing RAM, ROM, and UART at various addresses and speeds. All operations complete successfully with no timing violations or data corruption, demonstrating proper microcycle configuration.

**Acceptance Scenarios**:

1. **Given** the M65C02 microcycle controller is configured, **When** the CPU reads from ROM ($E000-$FFFF), **Then** correct instruction data is fetched on every access
2. **Given** the microcycle controller is configured, **When** the CPU writes to RAM ($0000-$7FFF), **Then** data is stored correctly without timing violations
3. **Given** the microcycle controller is configured, **When** the CPU accesses UART registers ($C000-$C001), **Then** I/O operations complete correctly
4. **Given** the system is running, **When** rapid consecutive memory accesses occur, **Then** no wait-state conflicts or bus contention occurs
5. **Given** the system is running for extended periods, **When** monitoring for errors, **Then** no data corruption or timing violations are detected

---

### Edge Cases

- What happens when attempting to write to ROM addresses ($8000-$BFFF, $E000-$FFFF)? System should ignore writes without crashing
- How does the system handle interrupt signals (IRQ, NMI) with the new M65C02 core? Must maintain compatibility with existing firmware
- What happens if memory timing is misconfigured? System should fail gracefully in simulation or display clear error indicators
- How does the microcycle controller handle transitions between different memory types (RAM, ROM, I/O)? Timing must adapt correctly
- What happens when accessing unmapped address space? System should return $FF without hanging (current behavior)
- How does the M65C02's pipelined execution affect timing compared to the Arlet core? Monitor and BASIC firmware must remain compatible

## Requirements

### Functional Requirements

**Core Integration:**

- **FR-001**: System MUST integrate the M65C02 CPU core from the MAM65C02-Processor-Core repository
- **FR-002**: System MUST map M65C02 address bus (16-bit) to existing memory map ($0000-$7FFF RAM, $8000-$BFFF BASIC ROM, $C000-$C0FF UART, $E000-$FFFF Monitor ROM)
- **FR-003**: System MUST map M65C02 data bus (8-bit) to existing peripheral data connections
- **FR-004**: System MUST adapt M65C02's separate read (nOE) and write (nWR) strobes to replace Arlet's combined write enable (WE) signal
- **FR-005**: System MUST connect M65C02 interrupt inputs (IRQ, NMI) to maintain compatibility with future interrupt-driven peripherals

**Memory Timing:**

- **FR-006**: System MUST configure M65C02 microcycle controller for synchronous block RAM (1-2 cycle access)
- **FR-007**: System MUST configure microcycle controller to achieve approximately 1 MHz CPU operating frequency from 25 MHz system clock
- **FR-008**: System MUST ensure read/write strobes have correct timing relationships with address and data signals
- **FR-009**: System MUST maintain data bus stability during memory read cycles
- **FR-010**: System MUST prevent bus contention when switching between memory read and write operations

**Peripheral Compatibility:**

- **FR-011**: System MUST preserve existing UART transmit functionality at 115200 baud
- **FR-012**: System MUST preserve existing UART receive functionality at 115200 baud
- **FR-013**: System MUST maintain address decoder logic for memory-mapped peripherals
- **FR-014**: System MUST preserve reset controller and clock divider functionality
- **FR-015**: System MUST maintain compatibility with existing monitor firmware (monitor.hex)
- **FR-016**: System MUST maintain compatibility with existing BASIC firmware (basic_rom.hex)

**Zero Page Operation:**

- **FR-017**: System MUST support correct read operations for all addresses in range $0000-$00FF
- **FR-018**: System MUST support correct write operations for all addresses in range $0000-$00FF
- **FR-019**: System MUST retain zero page data across multiple read/write cycles
- **FR-020**: System MUST allow zero page addressing modes to execute correctly

**Debugging and Validation:**

- **FR-021**: System MUST expose M65C02 debug signals (Mode, Done, SC, RMW, IO_Op) for integration testing and waveform analysis
- **FR-022**: System MUST provide test points or debug visibility into CPU state during execution
- **FR-023**: System MUST support existing cocotb test infrastructure for unit testing
- **FR-024**: System MUST allow cycle-accurate simulation of M65C02 behavior

### Key Entities

**M65C02 CPU Core**:
- Microprogrammed 65C02-compatible processor
- Built-in microcycle controller with configurable memory cycle lengths (1, 2, or 4 cycles)
- Separate read/write strobes (nOE, nWR) instead of combined write enable
- Status outputs: Mode (instruction type), Done (instruction completion), SC (single-cycle), RMW (read-modify-write), IO_Op (memory operation type)
- Supports Rockwell instruction extensions
- Pipelined execution for improved performance

**Memory Subsystem**:
- 32KB synchronous block RAM ($0000-$7FFF)
- 16KB BASIC ROM ($8000-$BFFF)
- 8KB Monitor ROM ($E000-$FFFF)
- Memory-mapped UART ($C000-$C0FF)
- Address decoder for peripheral selection

**Microcycle Controller**:
- Configurable memory cycle timing
- Supports different cycle lengths for different memory types
- Handles wait states for slower peripherals
- Maintains bus signal timing relationships

## Success Criteria

### Measurable Outcomes

**Boot and System Stability:**

- **SC-001**: System boots successfully within 1 second of power-on or reset, displaying monitor welcome message via UART
- **SC-002**: System remains stable during continuous operation for at least 30 minutes without crashes or hangs
- **SC-003**: Reset button successfully reboots system 100% of the time

**Zero Page Memory Access (Primary Fix Validation):**

- **SC-004**: 100% of zero page write operations ($0000-$00FF) succeed and read back correctly
- **SC-005**: Zero page memory access latency matches or improves upon addresses $0100+ (previously working)
- **SC-006**: Zero page addressing modes execute without errors in both monitor and BASIC

**Monitor Functionality:**

- **SC-007**: Monitor E (examine) command displays memory contents correctly for any address in the memory map
- **SC-008**: Monitor D (deposit) command successfully writes values to any RAM address
- **SC-009**: Monitor G command starts BASIC interpreter 100% of the time
- **SC-010**: Users can interact with monitor commands without encountering zero page-related errors

**BASIC Interpreter Operation:**

- **SC-011**: BASIC interpreter boots and displays "Ready" prompt within 2 seconds of executing monitor G command
- **SC-012**: BASIC "PRINT 2+2" command executes and displays correct result ("4") in under 1 second
- **SC-013**: BASIC FOR loop programs execute and display repeated output without errors
- **SC-014**: BASIC variable assignment and retrieval work correctly (demonstrating zero page usage)
- **SC-015**: BASIC LIST and NEW commands execute successfully

**Peripheral Compatibility:**

- **SC-016**: UART transmit continues to operate at 115200 baud with no character loss
- **SC-017**: UART receive continues to operate at 115200 baud with correct character recognition
- **SC-018**: All existing memory-mapped peripherals remain accessible at their defined addresses

**Build and Synthesis:**

- **SC-019**: Design synthesizes successfully with Yosys for ECP5 FPGA target
- **SC-020**: Place-and-route completes successfully with nextpnr-ecp5 with positive timing slack
- **SC-021**: Resource utilization (LUTs, block RAM) remains within acceptable limits (<50% of available resources)
- **SC-022**: Maximum clock frequency meets or exceeds 25 MHz system clock requirement

**Testing and Validation:**

- **SC-023**: All existing unit tests (RAM, UART, address decoder, reset controller) continue to pass
- **SC-024**: New M65C02-specific integration tests pass with 100% success rate
- **SC-025**: Cycle-accurate simulation validates correct CPU behavior for key instruction sequences

## Scope

### In Scope

- Integration of M65C02 CPU core into existing soc_top.v
- Configuration of M65C02 microcycle controller for memory timing
- Signal mapping and adaptation between M65C02 and existing peripherals
- Validation of zero page memory operation
- Testing with existing monitor and BASIC firmware
- Unit and integration test updates for M65C02 compatibility
- Documentation updates for new CPU core

### Out of Scope

- Changes to monitor firmware (monitor.s) - should work as-is
- Changes to BASIC firmware (basic_rom.hex) - should work as-is
- New peripheral development (LCD, PS/2 keyboard) - deferred to subsequent user stories
- Performance optimization beyond fixing the zero page bug
- Support for 65C816 extended addressing modes
- Interrupt handler implementation (IRQ/NMI remain unused in current firmware)

## Assumptions

1. **M65C02 Core Availability**: The M65C02 core from https://github.com/MorrisMA/MAM65C02-Processor-Core is compatible with our Verilog-2001 toolchain (Yosys, nextpnr-ecp5)
2. **Firmware Compatibility**: Existing monitor and BASIC firmware are 65C02-compatible and will execute correctly on M65C02 without source changes (only re-assembly if needed)
3. **Memory Interface**: M65C02's memory interface can be configured to work with our existing synchronous block RAM without requiring asynchronous memory support
4. **Timing Closure**: The M65C02 core will meet timing at 25 MHz system clock given its documented capability of 73+ MHz
5. **Signal Mapping**: The differences between M65C02 signals (nOE, nWR) and Arlet signals (WE) can be resolved with simple combinational logic
6. **Test Infrastructure**: Existing cocotb test infrastructure can be adapted for M65C02 by updating signal names and timing expectations
7. **Microcycle Configuration**: The microcycle controller can be configured through parameters or input signals without requiring core modifications
8. **Debug Signals**: M65C02 debug signals (Mode, Done, SC, RMW, IO_Op) are optional and their absence does not prevent basic functionality

## Dependencies

**External Dependencies:**

- M65C02 CPU core source code from https://github.com/MorrisMA/MAM65C02-Processor-Core
- M65C02 documentation from OpenCores or core repository
- Existing monitor firmware (firmware/monitor/monitor.hex)
- Existing BASIC firmware (firmware/basic/basic_rom.hex)

**Internal Dependencies:**

- Existing memory modules (ram.v, rom_basic.v, rom_monitor.v) from specs/001-6502-fpga-microcomputer
- Existing address decoder (address_decoder.v)
- Existing UART peripheral (uart.v, uart_tx.v, uart_rx.v)
- Existing clock divider (clock_divider.v)
- Existing reset controller (reset_controller.v)
- Existing build system (build/Makefile)
- Existing test infrastructure (tests/unit/, tests/integration/)

**Blocking Issues:**

- Zero page write failure in current Arlet 6502 implementation blocks all further development on User Stories 2-5
- Cannot proceed with BASIC testing, LCD display, or keyboard integration until CPU core is replaced

## Risks and Mitigations

**Risk 1: M65C02 Core Incompatibility**
- *Likelihood*: Low
- *Impact*: High (would require different core selection)
- *Mitigation*: Review M65C02 core source before integration; validate Verilog-2001 compatibility; have fallback cores identified (T65, cpu6502_tc)

**Risk 2: Microcycle Configuration Complexity**
- *Likelihood*: Medium
- *Impact*: Medium (could delay integration)
- *Mitigation*: Study M65C02 documentation thoroughly; start with simplest configuration (single-cycle); iterate based on simulation results

**Risk 3: Firmware Incompatibility**
- *Likelihood*: Low
- *Impact*: High (would require firmware rewrites)
- *Mitigation*: M65C02 is 65C02-compatible; existing firmware should work; test early with simple programs before full validation

**Risk 4: Timing Closure Failure**
- *Likelihood*: Low
- *Impact*: Medium (would require optimization)
- *Mitigation*: M65C02 documented at 73+ MHz, far exceeding our 25 MHz requirement; use conservative microcycle settings initially

**Risk 5: Test Infrastructure Breakage**
- *Likelihood*: Medium
- *Impact*: Low (tests can be updated)
- *Mitigation*: Plan for test updates during integration; maintain test documentation; validate one module at a time

## References

**Internal Documentation:**
- `specs/001-6502-fpga-microcomputer/` - Original system specification
- `specs/001-6502-fpga-microcomputer/STATUS.md` - Current project status
- `ROOT_CAUSE_ANALYSIS.md` - Technical analysis of zero page bug
- `6502_CORE_COMPARISON.md` - Comparison of alternative CPU cores
- `BUG_REPORT_ZERO_PAGE_WRITES.md` - Zero page bug investigation
- `RAM_DEBUG_NOTES.md` - Memory debugging notes

**External Resources:**
- M65C02 Core Repository: https://github.com/MorrisMA/MAM65C02-Processor-Core
- M65C02 OpenCores Project: https://opencores.org/projects/m65c02
- WDC 65C02 Datasheet: Industry-standard reference for 65C02 instruction set
- EhBASIC Documentation: Reference for BASIC interpreter expectations

**Existing System Files:**
- `rtl/system/soc_top.v` - System-on-chip integration (to be modified)
- `rtl/cpu/arlet-6502/cpu.v` - Current CPU core (to be replaced)
- `rtl/memory/*.v` - Memory modules (to be preserved)
- `rtl/peripherals/uart/*.v` - UART peripheral (to be preserved)
- `firmware/monitor/monitor.s` - Monitor source code (to be preserved)
- `firmware/basic/basic_rom.hex` - BASIC interpreter binary (to be preserved)
