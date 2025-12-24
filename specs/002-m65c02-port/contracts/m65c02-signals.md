# M65C02 Core Signal Reference

**Date**: 2025-12-23
**Phase**: Phase 1 - Design (Contracts)
**Feature**: [spec.md](../spec.md) | [data-model.md](../data-model.md)

## Purpose

This document provides a complete reference for all M65C02_Core module signals, including electrical characteristics, timing requirements, and usage guidelines.

---

## Signal Summary Table

| Signal | Direction | Width | Type | Purpose |
|--------|-----------|-------|------|---------|
| `Clk` | Input | 1 | Clock | System clock (25 MHz) |
| `Rst` | Input | 1 | Control | System reset (active high) |
| `AO[15:0]` | Output | 16 | Address | Address output bus |
| `DI[7:0]` | Input | 8 | Data | Data input bus (reads) |
| `DO[7:0]` | Output | 8 | Data | Data output bus (writes) |
| `IO_Op[1:0]` | Output | 2 | Control | I/O operation type |
| `MC[2:0]` | Output | 3 | Status | Microcycle state |
| `MemTyp[1:0]` | Output | 2 | Status | Memory access type |
| `Wait` | Input | 1 | Control | Wait state request |
| `Rdy` | Output | 1 | Status | Internal ready signal |
| `Int` | Input | 1 | Control | Interrupt request |
| `Vector[15:0]` | Input | 16 | Data | Interrupt vector |
| `xIRQ` | Input | 1 | Control | External IRQ (active low) |
| `IRQ_Msk` | Output | 1 | Status | Interrupt mask from P |
| `Done` | Output | 1 | Status | Instruction complete |
| `SC` | Output | 1 | Status | Single cycle instruction |
| `Mode[2:0]` | Output | 3 | Status | Instruction type |
| `RMW` | Output | 1 | Status | Read-modify-write flag |
| `IntSvc` | Output | 1 | Status | Interrupt service start |
| `ISR` | Output | 1 | Status | Vector pull start |
| `A[7:0]` | Output | 8 | Debug | Accumulator (read-only) |
| `X[7:0]` | Output | 8 | Debug | X register (read-only) |
| `Y[7:0]` | Output | 8 | Debug | Y register (read-only) |
| `S[7:0]` | Output | 8 | Debug | Stack pointer (read-only) |
| `P[7:0]` | Output | 8 | Debug | Status word (read-only) |
| `PC[15:0]` | Output | 16 | Debug | Program counter (read-only) |
| `IR[7:0]` | Output | 8 | Debug | Instruction register |
| `OP1[7:0]` | Output | 8 | Debug | Operand register 1 |
| `OP2[7:0]` | Output | 8 | Debug | Operand register 2 |

---

## Core Signals (Required for Basic Operation)

### Clk - System Clock

```
Signal: Clk
Direction: Input
Width: 1 bit
Type: Clock

Description:
    Primary system clock input. All synchronous operations occur on
    the rising edge of this clock.

Electrical:
    Frequency: 25 MHz (target for our system)
    Period: 40ns
    Duty Cycle: 40-60% (50% recommended)
    V_IH: 2.0V (3.3V LVCMOS)
    V_IL: 0.8V

Timing:
    All M65C02 operations are synchronous to rising edge
    Minimum frequency: ~1 MHz (for proper operation)
    Maximum frequency: 73+ MHz (verified in Spartan-3A FPGA)
    Our usage: 25 MHz

Connection:
    Connect directly to FPGA 25 MHz clock (P3 pin)
    Do NOT use clock enable or gating
```

### Rst - System Reset

```
Signal: Rst
Direction: Input
Width: 1 bit
Type: Control (active high)

Description:
    Synchronous reset input. When asserted, CPU immediately halts
    current instruction and enters reset sequence.

Polarity: Active High (Rst=1 means reset active)

Timing:
    Synchronous: Sampled on rising edge of Clk
    Minimum duration: 4 clocks (160ns @ 25MHz)
    Recommended: >100ms for system stability

Reset Behavior:
    - PC loaded with reset vector from Vector input or $FFFC
    - Stack pointer S ← 8'hFF
    - Interrupt disable flag I ← 1
    - Decimal mode flag D ← 0
    - All instructions aborted
    - MC state machine ← 2 (ADDR_SETUP)

Connection:
    Connect to reset_controller.rst output
    Ensure proper debouncing (handled by reset_controller)

Post-Reset:
    First instruction fetch from reset vector address
    System begins normal operation
```

### AO[15:0] - Address Output

```
Signal: AO (Address Output)
Direction: Output
Width: 16 bits
Type: Address bus

Description:
    Address output bus from CPU to memory and peripherals.
    Indicates which memory location CPU wants to access.

Valid Range: 0x0000 to 0xFFFF (64KB address space)

Timing:
    Valid when: MC ∈ {2, 3, 1}
    Changes when: MC = 0 (start of new microcycle)
    Setup time: Address stable ≥1 clock before memory access
    Hold time: Address stable through MC=3 and MC=1

Behavior by Microcycle State:
    MC=2: Address becomes valid (may change from previous)
    MC=3: Address stable, memory decoding active
    MC=1: Address still stable, memory access in progress
    MC=0: Address may change to next access

Memory Map (Our System):
    0x0000-0x7FFF: RAM (32KB)
    0x8000-0xBFFF: BASIC ROM (16KB)
    0xC000-0xC0FF: UART (256 bytes)
    0xE000-0xFFFF: Monitor ROM (8KB)

Connection:
    Connect to address decoder input
    Address decoder generates chip selects
    Each memory/peripheral uses appropriate address bits
```

### DI[7:0] - Data Input

```
Signal: DI (Data Input)
Direction: Input
Width: 8 bits
Type: Data bus (read)

Description:
    Data input bus to CPU. Carries instruction opcodes and
    data read from memory and peripherals.

Source: Multiplexed from:
    - RAM data output (when ram_cs=1)
    - BASIC ROM data output (when rom_basic_cs=1)
    - Monitor ROM data output (when rom_monitor_cs=1)
    - UART data output (when uart_cs=1)
    - Default: 8'hFF (unmapped addresses)

Timing:
    Setup time: ≥5ns before capture (rising edge at MC=0)
    Hold time: ≥2ns after capture
    Valid when: MC=1 (for read/fetch operations)
    Captured when: Rising edge of Clk when MC=0

Usage by IO_Op:
    IO_Op=2'b10 (Read): DI contains data from memory
    IO_Op=2'b11 (Fetch): DI contains instruction opcode
    IO_Op=2'b01 (Write): DI ignored (not captured)
    IO_Op=2'b00 (No-op): DI ignored

Connection:
    Connect to data bus multiplexer output
    Multiplexer selects source based on chip selects
    Register DI at MC=0 transition for stable capture

Critical:
    DI MUST be stable during MC=1 and held through MC=0 edge
    If DI changes during MC=0, capture may be corrupted
```

### DO[7:0] - Data Output

```
Signal: DO (Data Output)
Direction: Output
Width: 8 bits
Type: Data bus (write)

Description:
    Data output bus from CPU. Carries data to be written to
    memory and peripherals.

Valid When: IO_Op = 2'b01 (Write operation)
Timing:
    Valid when: MC ∈ {3, 1} during write operations
    Changes when: MC = 2 or MC = 0
    Setup time: ≥10ns before memory write enable
    Hold time: ≥40ns after write enable assertion

Content Sources:
    - ALU result (arithmetic/logic operations)
    - Accumulator A (STA instructions)
    - X register (STX instructions)
    - Y register (STY instructions)
    - PCH (high byte of PC, for stack push)
    - PCL (low byte of PC, for stack push)
    - P (processor status, for stack push)

Usage by IO_Op:
    IO_Op=2'b01 (Write): DO contains valid write data
    IO_Op=2'b10 (Read): DO is don't care (may be previous value)
    IO_Op=2'b11 (Fetch): DO is don't care
    IO_Op=2'b00 (No-op): DO is don't care

Connection:
    Connect to data input of RAM and peripherals
    Use with write enable (mem_we = IO_Op==01 && MC==3)
```

### IO_Op[1:0] - I/O Operation

```
Signal: IO_Op (I/O Operation)
Direction: Output
Width: 2 bits
Type: Control (encoded)

Description:
    Indicates the type of memory/I/O operation being performed
    during current microcycle.

Encoding:
    2'b00 (0): NO_OP - No memory operation
    2'b01 (1): WRITE - Memory write operation
    2'b10 (2): READ - Memory read operation
    2'b11 (3): FETCH - Instruction fetch operation

Timing:
    Valid when: MC ∈ {2, 3, 1}
    Changes when: MC = 0
    Stable for: Entire 4-clock microcycle

Usage - Derive Write Enable:
    mem_we = (IO_Op == 2'b01) && (MC == 3 || MC == 1) && chip_select

Usage - Derive Read Enable (informational):
    mem_oe = (IO_Op == 2'b10 || IO_Op == 2'b11)

Usage - Distinguish Fetch vs Data Read:
    is_fetch = (IO_Op == 2'b11)
    is_data_read = (IO_Op == 2'b10)

Connection:
    Decode to generate memory write enables
    Can be used for instruction/data memory separation
```

### MC[2:0] - Microcycle State

```
Signal: MC (Microcycle State)
Direction: Output
Width: 3 bits
Type: Status (state machine)

Description:
    Current state of the microcycle controller state machine.
    Indicates which phase of the memory access cycle is active.

State Encoding:
    3'b010 (2): ADDR_SETUP - Address presentation
    3'b011 (3): MEM_ACCESS - Memory operation begins
    3'b001 (1): DATA_VALID - Data setup/hold phase
    3'b000 (0): CYCLE_END - Data capture/completion

Normal Sequence: 2 → 3 → 1 → 0 → 2 → ...

State Durations: 1 clock each (40ns @ 25MHz)
Full Cycle: 4 clocks (160ns @ 25MHz)

Wait State Sequence (if Wait asserted at MC=3):
    2 → 3 → 7 → 6 → 3 → 1 → 0 → 2
    (inserts 4-clock wait, returns to MC=3)

Usage - Data Capture Control:
    capture_di = (MC == 0) && rising_edge(Clk)

Usage - Write Enable Window:
    mem_we_window = (MC == 3 || MC == 1)

Usage - Debug/Waveform Analysis:
    Monitor MC to see microcycle progression
    Verify 2→3→1→0 sequence in simulation

Connection:
    Optional: Use for precise data bus timing
    Required: Connect if using data capture logic based on MC
```

---

## Control Signals (Wait States and Interrupts)

### Wait - Wait State Request

```
Signal: Wait
Direction: Input
Width: 1 bit
Type: Control (active high)

Description:
    Request from external logic to insert wait states.
    Allows slow memory/peripherals to extend access time.

Polarity: Active High (Wait=1 means "please wait")

Timing:
    Sampled at: Rising edge when MC=3 or MC=1
    Effect: If Wait=1, inserts 4-clock wait state sequence
    Response latency: 1 clock

Wait State Behavior:
    MC=3, Wait=1: Insert wait, jump to MC=7
    MC=7: Wait state cycle 1
    MC=6: Wait state cycle 2
    MC=3: Return to memory access, re-sample Wait
    (If Wait still=1, repeat sequence)

Our Usage:
    Wait = 1'b0 (constant 0)
    Reason: All internal memory is synchronous block RAM
            with perfect 4-cycle timing match
    No wait states needed

Future Use (External Memory):
    address_decoder can assert Wait for slow peripherals
    Each Wait assertion adds 4 clocks (160ns)

Connection:
    Tie to 1'b0 for MVP (no wait states)
    Future: Connect to address decoder slow_memory signal
```

### Int - Interrupt Request

```
Signal: Int
Direction: Input
Width: 1 bit
Type: Control (active high)

Description:
    Interrupt request input from external interrupt controller.
    When asserted, CPU will vector to interrupt service routine.

Polarity: Active High (Int=1 means interrupt pending)

Behavior:
    - If P.I=0 (interrupts enabled) and Int=1:
        CPU finishes current instruction
        Pushes PCL, PCH, P to stack
        Sets P.I=1 (disable further interrupts)
        Loads PC from Vector input
        Begins interrupt service routine

    - If P.I=1 (interrupts disabled):
        Int is ignored

Relationship with Vector:
    Vector[15:0] must be valid when Int=1
    Vector provides ISR entry address

Relationship with xIRQ:
    xIRQ is external IRQ input (active low)
    Interrupt controller logic converts xIRQ → Int
    Our MVP: Int=0 always (no interrupts)

Connection (MVP):
    Tie to 1'b0 (no interrupts)

Connection (Future):
    Connect to interrupt controller output
    Interrupt controller provides:
        - IRQ edge detection (for xIRQ)
        - Interrupt prioritization
        - Vector generation from memory ($FFFA/$FFFC/$FFFE)
```

### Vector[15:0] - Interrupt Vector

```
Signal: Vector
Direction: Input
Width: 16 bits
Type: Data

Description:
    Address of interrupt service routine, provided by
    external interrupt controller when Int is asserted.

Valid When: Int = 1
Source: Interrupt controller (reads from $FFFA/$FFFC/$FFFE)

Standard 6502 Vectors:
    $FFFA: NMI vector
    $FFFC: Reset vector
    $FFFE: IRQ/BRK vector

M65C02 Behavior:
    - Interrupt controller reads vector from memory
    - Provides vector value on Vector[15:0] input
    - CPU loads PC directly from Vector input
    - No vector fetch cycle by CPU (external controller does it)

Connection (MVP):
    Tie to 16'hFFFC (reset vector, default)
    Not used since Int=0 always

Connection (Future):
    Connect to interrupt controller vector output
    Interrupt controller reads from appropriate vector address
```

### xIRQ - External IRQ Input

```
Signal: xIRQ
Direction: Input
Width: 1 bit
Type: Control (active low)

Description:
    External maskable interrupt request input.
    Asynchronous signal from peripherals/external devices.

Polarity: Active Low (xIRQ=0 means IRQ asserted)

Usage:
    This is the RAW interrupt signal from peripherals
    Requires external interrupt controller to:
        - Synchronize to Clk
        - Edge detection (IRQ is edge-sensitive)
        - Generate Int pulse when appropriate

Connection (MVP):
    Tie to 1'b1 (inactive, no interrupts)

Connection (Future):
    Connect to peripheral interrupt output
    Use interrupt controller module for proper handling
```

### IRQ_Msk - Interrupt Mask

```
Signal: IRQ_Msk
Direction: Output
Width: 1 bit
Type: Status

Description:
    Interrupt mask status from processor status word.
    Indicates whether maskable interrupts are enabled/disabled.

Meaning:
    IRQ_Msk = 1: Interrupts disabled (P.I=1)
    IRQ_Msk = 0: Interrupts enabled (P.I=0)

Source: P[2] (I flag in processor status word)

Usage:
    Provided to external interrupt controller
    Controller can use to determine if IRQ should be asserted
    Also useful for debugging interrupt behavior

Controlled By Software:
    SEI instruction: Sets I flag → IRQ_Msk=1 (disable)
    CLI instruction: Clears I flag → IRQ_Msk=0 (enable)
    RTI instruction: Restores P from stack → restores IRQ_Msk

Connection:
    Optional connection to interrupt controller
    Can be left unconnected in MVP (no interrupts)
```

---

## Status and Debug Signals

### Done - Instruction Complete

```
Signal: Done
Direction: Output
Width: 1 bit
Type: Status (pulse)

Description:
    Pulses high for one clock when instruction completes.
    Asserted during instruction fetch of NEXT instruction.

Timing:
    Pulse width: 1 clock
    Asserted when: Fetching next instruction (IO_Op=2'b11, MC varies)

Usage:
    - Instruction counting in simulation
    - Performance profiling
    - Debug: Verify instruction execution
    - Trigger for instruction trace capture

Connection:
    Optional: Connect to debug/analysis logic
    Not required for functional operation
```

### SC - Single Cycle Instruction

```
Signal: SC
Direction: Output
Width: 1 bit
Type: Status

Description:
    Indicates current instruction completes in single microcycle.

Meaning:
    SC = 1: Instruction completes in 1 microcycle (160ns)
    SC = 0: Instruction requires multiple microcycles

Examples of Single-Cycle Instructions:
    - Register-to-register transfers (TAX, TXA, TAY, TYA, TXS, TSX)
    - Register increment/decrement (INX, DEX, INY, DEY, INA, DEA)
    - Flag set/clear (SEC, CLC, SED, CLD, SEI, CLI)
    - NOP

Connection:
    Optional: For performance analysis
```

### Mode[2:0] - Instruction Type

```
Signal: Mode
Direction: Output
Width: 3 bits
Type: Status (encoded)

Description:
    Indicates the category/type of instruction currently executing.

Encoding:
    3'd0: STP - Stop processor instruction (WAI behavior in some variants)
    3'd1: INV - Invalid opcode (treated as NOP)
    3'd2: BRK - Break instruction
    3'd3: JMP - Branch/jump/return/call instructions
    3'd4: STK - Stack operations (PHA/PLA/PHX/PLX/PHY/PLY/PHP/PLP)
    3'd5: INT - Single-cycle internal operations
    3'd6: MEM - Multi-cycle memory access instructions
    3'd7: WAI - Wait for interrupt instruction

Usage:
    - Instruction profiling and analysis
    - Debug: Identify instruction categories
    - Potential use for instruction/data memory separation

Connection:
    Optional: For debug and analysis
```

### RMW - Read-Modify-Write Flag

```
Signal: RMW
Direction: Output
Width: 1 bit
Type: Status

Description:
    Indicates current instruction is read-modify-write type.
    Asserted during instructions that read, modify, and write
    back to the same memory location.

Meaning:
    RMW = 1: Instruction is RMW (INC, DEC, ASL, LSR, ROL, ROR, TSB, TRB)
    RMW = 0: Instruction is not RMW

Usage:
    - External logic can lock memory during RMW
    - Prevents bus conflicts in multi-master systems
    - Debug: Identify RMW instructions in trace

Connection:
    Optional: For multi-master systems or debug
    Not required in single-master system (MVP)
```

### MemTyp[1:0] - Memory Access Type

```
Signal: MemTyp
Direction: Output
Width: 2 bits
Type: Status (encoded)

Description:
    Classifies current memory access by address range.
    Can be used to route accesses to different memories.

Encoding:
    2'b00: PROGRAM - Program memory (instruction fetch)
    2'b01: PAGE_0 - Zero page memory ($0000-$00FF)
    2'b10: PAGE_1 - Stack page ($0100-$01FF)
    2'b11: DATA - General data memory

Usage:
    - Separate instruction/data memory systems
    - Fast zero page memory (LUT RAM)
    - Stack memory optimization
    - Debug: Identify access patterns

Our Usage (MVP):
    Not used - all memory is unified
    Informational only, available for future optimization

Connection:
    Optional: Can be left unconnected (informational)
```

### Rdy - Internal Ready

```
Signal: Rdy
Direction: Output
Width: 1 bit
Type: Status

Description:
    Internal ready signal from microcycle controller.
    Indicates microcycle is completing without wait states.

Meaning:
    Rdy = 1: Microcycle completing normally (MC advancing)
    Rdy = 0: Microcycle stalled (Wait=1, waiting)

Internal Usage:
    Gates register write enables inside M65C02_Core
    Prevents register updates during wait states

External Usage:
    Informational/debug
    Not typically needed for external logic

Connection:
    Optional: For debug/waveform analysis
```

### IntSvc - Interrupt Service Start

```
Signal: IntSvc
Direction: Output
Width: 1 bit
Type: Status (pulse)

Description:
    Pulses high when interrupt service routine begins.
    Marks the start of interrupt handler execution.

Timing:
    Pulse width: 1 clock
    Asserted when: First instruction of ISR being fetched

Usage:
    - Debug: Track interrupt servicing
    - Performance: Measure interrupt latency
    - Analysis: Count interrupt occurrences

Connection:
    Optional: For debug and interrupt analysis
```

### ISR - Interrupt Vector Pull Start

```
Signal: ISR
Direction: Output
Width: 1 bit
Type: Status (pulse)

Description:
    Indicates interrupt vector pull sequence has started.
    Asserted when CPU begins interrupt vector fetch process.

Usage:
    - Debug: Observe interrupt sequence
    - Can be used to generate VP (Vector Pull) signal
      similar to W65C02S microprocessor

Connection:
    Optional: For W65C02S compatibility or debug
```

---

## Internal Registers (Debug Access)

### A[7:0] - Accumulator

```
Signal: A
Direction: Output (read-only)
Width: 8 bits
Type: Debug

Description:
    Current value of accumulator register.
    Primary register for arithmetic and logic operations.

Usage:
    - Simulation debugging
    - Waveform analysis
    - Verification of ALU operations
    - Test assertions in cocotb

Connection:
    Do not connect in RTL (output only, for debug)
    Access in testbenches: dut.cpu.A.value
```

### X[7:0], Y[7:0] - Index Registers

```
Signal: X, Y
Direction: Output (read-only)
Width: 8 bits each
Type: Debug

Description:
    Current values of X and Y index registers.
    Used for indexed addressing modes and loop counters.

Usage:
    - Verify indexed addressing calculations
    - Debug loop iterations
    - Test register transfer instructions

Connection:
    Debug access only in simulation
```

### S[7:0] - Stack Pointer

```
Signal: S
Direction: Output (read-only)
Width: 8 bits
Type: Debug

Description:
    Current stack pointer value (page 1 offset).
    Full stack address = $0100 + S

Valid Range: $00-$FF (stack addresses $0100-$01FF)
Grows Down: Decrements on push, increments on pop

Usage:
    - Verify stack operations (push/pop)
    - Debug subroutine calls and returns
    - Check for stack overflow ($00) or underflow ($FF)

Connection:
    Debug access only
```

### P[7:0] - Processor Status Word

```
Signal: P
Direction: Output (read-only)
Width: 8 bits
Type: Debug

Description:
    Current processor status word (flags).

Bit Layout:
    P[7]: N - Negative flag (result bit 7)
    P[6]: V - Overflow flag (signed overflow)
    P[5]: 1 - (always 1)
    P[4]: B - Break flag (1 if BRK, 0 if IRQ)
    P[3]: D - Decimal mode flag (BCD arithmetic)
    P[2]: I - Interrupt disable flag
    P[1]: Z - Zero flag (result = 0)
    P[0]: C - Carry flag

Usage:
    - Verify flag setting after ALU operations
    - Debug conditional branches
    - Check interrupt enable state

Connection:
    Debug access only
```

### PC[15:0] - Program Counter

```
Signal: PC
Direction: Output (read-only)
Width: 16 bits
Type: Debug

Description:
    Current program counter value.
    Points to next instruction to be fetched.

Range: $0000-$FFFF

Usage:
    - Trace program execution flow
    - Verify jumps, branches, calls
    - Confirm reset vector loading
    - Debug infinite loops

Connection:
    Debug access only
    Critical for simulation verification
```

### IR[7:0] - Instruction Register

```
Signal: IR
Direction: Output (read-only)
Width: 8 bits
Type: Debug

Description:
    Currently executing instruction opcode.

Usage:
    - Instruction trace generation
    - Disassembly in simulation
    - Verify correct instruction fetch

Connection:
    Debug access only
```

### OP1[7:0], OP2[7:0] - Operand Registers

```
Signal: OP1, OP2
Direction: Output (read-only)
Width: 8 bits each
Type: Debug

Description:
    Internal working registers holding instruction operands.
    OP1: Often holds low byte of address or immediate operand
    OP2: Often holds high byte of address

Usage:
    - Debug complex addressing modes
    - Verify operand fetch sequences
    - Analyze instruction timing

Connection:
    Debug access only
```

---

## Signal Groups by Function

### Minimal Required Connections

For basic CPU operation, only these signals are REQUIRED:

```
Inputs (Required):
    Clk              - System clock (25 MHz)
    Rst              - System reset (active high)
    DI[7:0]          - Data input from memory
    Wait = 1'b0      - No wait states (tie low)
    Int = 1'b0       - No interrupts (tie low, MVP)
    Vector = 16'hFFFC - Default vector (tie to constant)
    xIRQ = 1'b1      - No IRQ (tie high)

Outputs (Required):
    AO[15:0]         - Address to memory/peripherals
    DO[7:0]          - Data to memory (writes)
    IO_Op[1:0]       - Operation type (decode to mem_we)
    MC[2:0]          - Microcycle state (for data capture timing)
```

### Optional Debug Signals

Can be left unconnected, used only for simulation/debug:

```
Outputs (Optional):
    IRQ_Msk, Done, SC, Mode[2:0], RMW, MemTyp[1:0]
    Rdy, IntSvc, ISR
    A, X, Y, S, P, PC, IR, OP1, OP2
```

---

## Timing Specifications

### Setup and Hold Times (@ 25 MHz, 40ns period)

```
Input Signals:
    DI[7:0]:
        Setup:  ≥5ns before rising edge at MC=0
        Hold:   ≥2ns after rising edge at MC=0

    Wait:
        Setup:  ≥10ns before end of MC=3 or MC=1

    Int, Vector[15:0]:
        Setup:  ≥10ns before instruction completion
        Hold:   ≥5ns after Int sampled

Output Signals:
    AO[15:0]:
        Valid:  10ns after rising edge at MC=2
        Stable: Until rising edge at MC=0

    DO[7:0]:
        Valid:  10ns after rising edge at MC=3 (for writes)
        Stable: Until rising edge at MC=0

    IO_Op[1:0]:
        Valid:  5ns after rising edge at MC=2
        Stable: Entire microcycle

    MC[2:0]:
        Valid:  5ns after each rising edge of Clk
```

### Propagation Delays

```
Clock to Output (typical):
    Clk → AO: <15ns
    Clk → DO: <15ns
    Clk → IO_Op: <10ns
    Clk → MC: <5ns

Internal Delays:
    Address decode: <20ns (external logic)
    Data multiplexer: <10ns (external logic)
```

---

## Connection Examples

### Minimal System (MVP)

```verilog
M65C02_Core #(
    .pStkPtr_Rst(8'hFF),
    .pInt_Hndlr(0),
    .pM65C02_uPgm("M65C02_uPgm_V3a.txt"),
    .pM65C02_IDec("M65C02_Decoder_ROM.txt")
) cpu (
    // Required connections
    .Clk(clk_25mhz),
    .Rst(system_rst),
    .AO(cpu_addr),
    .DI(cpu_data_in_reg),  // From registered multiplexer
    .DO(cpu_data_out),
    .IO_Op(cpu_io_op),
    .MC(cpu_mc),

    // Tie-offs for MVP (no interrupts, no wait states)
    .Wait(1'b0),
    .Int(1'b0),
    .Vector(16'hFFFC),
    .xIRQ(1'b1),

    // Optional: Leave unconnected or connect for debug
    .IRQ_Msk(),
    .Done(),
    .SC(),
    .Mode(),
    .RMW(),
    .MemTyp(),
    .Rdy(),
    .IntSvc(),
    .ISR(),
    .A(),
    .X(),
    .Y(),
    .S(),
    .P(),
    .PC(),
    .IR(),
    .OP1(),
    .OP2()
);
```

### Simulation/Debug

```verilog
M65C02_Core cpu (
    // ... (same as above for required signals)

    // Connect debug signals for waveform viewing
    .A(cpu_a_debug),
    .X(cpu_x_debug),
    .Y(cpu_y_debug),
    .S(cpu_s_debug),
    .P(cpu_p_debug),
    .PC(cpu_pc_debug),
    .IR(cpu_ir_debug),

    // ... (others as needed)
);
```

---

## Verification Checklist

### Signal Connection Verification

- [ ] Clk connected to 25 MHz clock source
- [ ] Rst connected to synchronized reset controller
- [ ] AO connected to address decoder
- [ ] DI connected to registered data bus multiplexer
- [ ] DO connected to memory/peripheral data inputs
- [ ] IO_Op decoded to generate memory write enables
- [ ] MC used for data capture timing (MC=0 edge)
- [ ] Wait tied to 1'b0 (MVP, no wait states)
- [ ] Int tied to 1'b0 (MVP, no interrupts)
- [ ] Vector tied to 16'hFFFC
- [ ] xIRQ tied to 1'b1

### Timing Verification

- [ ] Address stable ≥1 clock before memory access
- [ ] Data input stable during MC=1 and MC=0 edge
- [ ] Data output stable during MC=3 and MC=1 (writes)
- [ ] Memory write enable asserted only during MC=3
- [ ] Data captured only at MC=0 rising edge

---

## Related Documents

- **[data-model.md](../data-model.md)** - Signal entities and timing relationships
- **[memory-timing.md](memory-timing.md)** - Detailed timing diagrams
- **[signal-adaptation.md](signal-adaptation.md)** - Arlet-to-M65C02 conversion

**Status**: Signal reference complete ✅
