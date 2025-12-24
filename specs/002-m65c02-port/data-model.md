# Data Model: M65C02 CPU Core Integration

**Date**: 2025-12-23
**Phase**: Phase 1 - Design
**Feature**: [spec.md](spec.md) | [plan.md](plan.md) | [research.md](research.md)

## Purpose

This document defines the data entities, signal relationships, and state machines for the M65C02 CPU core integration. It provides a formal model of how signals interact and change over time.

---

## 1. Signal Entities

### 1.1 Clock and Reset Domain

**Entity**: `ClockDomain`

```
ClockDomain {
    signal: clk_25mhz        // Primary system clock
    period: 40ns            // 25 MHz
    type: rising_edge       // Active on rising edge

    signal: system_rst       // System reset
    polarity: active_high    // 1 = reset active
    synchronous: true        // Synchronized to clk_25mhz
    duration_min: 4_cycles   // Minimum reset assertion time
}
```

**State Transitions**:
```
RESET_INACTIVE (rst=0) ⟷ RESET_ACTIVE (rst=1)
    ↑ trigger: reset_button_n falling edge
    ↓ trigger: reset_controller release
```

### 1.2 Address Bus Entity

**Entity**: `AddressBus`

```
AddressBus {
    signal: AO[15:0]         // Address output from CPU
    width: 16_bits
    timing: setup_time = 1_clock_before_MC3
           hold_time = 2_clocks_after_MC3

    memory_map: {
        0x0000..0x7FFF: RAM (32KB)
        0x8000..0xBFFF: BASIC_ROM (16KB)
        0xC000..0xC0FF: UART (256 bytes)
        0xE000..0xFFFF: MONITOR_ROM (8KB)
    }

    state_validity: VALID when MC ∈ {2, 3, 1}, CHANGING when MC = 0
}
```

**Timing Constraints**:
```
t_setup(AO → memory):   ≥ 10ns  (address stable before memory access)
t_hold(AO):             ≥ 40ns  (address held through memory cycle)
```

### 1.3 Data Bus Entities

**Entity**: `DataOutput`

```
DataOutput {
    signal: DO[7:0]          // Data output from CPU (writes)
    width: 8_bits
    driver: M65C02_Core
    timing: valid_when = (IO_Op == 2'b01) && (MC ∈ {3, 1})
           tristate_when = (IO_Op != 2'b01) || (MC ∈ {2, 0})

    sources: {
        ALU_Out:     when writing ALU result
        PCH:         when pushing PC high byte to stack
        PCL:         when pushing PC low byte to stack
        PSW:         when pushing processor status
    }
}
```

**Entity**: `DataInput`

```
DataInput {
    signal: DI[7:0]          // Data input to CPU (reads)
    width: 8_bits
    receiver: M65C02_Core
    timing: sampled_when = (MC == 0) && rising_edge(Clk)
           setup_time = 5ns_before_MC0

    sources: {
        RAM:          when (ram_cs == 1)
        BASIC_ROM:    when (rom_basic_cs == 1)
        MONITOR_ROM:  when (rom_monitor_cs == 1)
        UART:         when (uart_cs == 1)
        default:      8'hFF (unmapped read)
    }

    multiplexer: {
        select_timing: combinational (address-based)
        output_timing: registered at MC=0 transition
    }
}
```

**Data Bus State Machine**:
```
State: DATA_IDLE
    MC = 2 or MC = 0
    DO = previous_value (may be changing)
    DI = previous_captured_value

State: DATA_WRITE_SETUP
    MC = 3, IO_Op = 2'b01
    DO = valid_write_data
    DI = don't_care

State: DATA_WRITE_HOLD
    MC = 1, IO_Op = 2'b01
    DO = valid_write_data (stable)
    DI = don't_care

State: DATA_READ_SETUP
    MC = 3, IO_Op ∈ {2'b10, 2'b11}
    DO = don't_care (tristate)
    DI = memory_propagating

State: DATA_READ_VALID
    MC = 1, IO_Op ∈ {2'b10, 2'b11}
    DO = don't_care (tristate)
    DI = valid_read_data (stable)

State: DATA_CAPTURE
    MC = 0, rising_edge(Clk)
    DO = don't_care
    DI = CAPTURED into internal registers
```

### 1.4 Control Signal Entities

**Entity**: `IO_Operation`

```
IO_Operation {
    signal: IO_Op[1:0]       // I/O operation type
    width: 2_bits
    encoding: {
        2'b00: NO_OP         // No memory operation
        2'b01: WRITE         // Memory write operation
        2'b10: READ          // Memory read operation
        2'b11: FETCH         // Instruction fetch operation
    }

    timing: valid_when = (MC ∈ {2, 3, 1})
           changes_at = (MC == 0) transition

    derived_signals: {
        mem_we = (IO_Op == 2'b01) && (MC ∈ {3, 1})
        mem_oe = (IO_Op ∈ {2'b10, 2'b11}) && (MC ∈ {3, 1})
    }
}
```

**Entity**: `MicrocycleState`

```
MicrocycleState {
    signal: MC[2:0]          // Microcycle state counter
    width: 3_bits
    state_space: {0, 1, 2, 3} // Only 4 states used (0-3)

    state_sequence: 2 → 3 → 1 → 0 → 2 → ...

    state_meanings: {
        MC=2: ADDR_SETUP     // Address presentation
        MC=3: MEM_ACCESS     // Memory operation begins
        MC=1: DATA_VALID     // Data setup/hold
        MC=0: CYCLE_END      // Data capture/completion
    }

    timing: changes_on = rising_edge(Clk)
           period = 4_clocks (160ns @ 25MHz)
}
```

**Entity**: `WaitRequest`

```
WaitRequest {
    signal: Wait             // Wait state insertion request
    width: 1_bit
    polarity: active_high    // 1 = request wait state

    timing: sampled_at = (MC == 3) || (MC == 1)
           effect = insert_4_clock_wait_sequence if (Wait == 1)

    usage_in_system: Wait = 1'b0  // Always 0 for internal memory
}
```

**Entity**: `InternalReady`

```
InternalReady {
    signal: Rdy              // Internal ready signal from MPC
    width: 1_bit
    purpose: internal_gating // Gates register updates

    timing: Rdy = 1 when (MC == 0) && (Wait == 0)
           Rdy = 0 when (Wait == 1)
}
```

### 1.5 Interrupt Entities

**Entity**: `InterruptRequest`

```
InterruptRequest {
    signal: Int              // Interrupt request to core
    width: 1_bit
    polarity: active_high    // 1 = interrupt pending

    signal: Vector[15:0]     // Interrupt service routine address
    width: 16_bits
    valid_when: Int == 1

    usage_mvp: {
        Int = 1'b0           // No interrupts in MVP
        Vector = 16'hFFFC    // Default to reset vector
    }
}
```

**Entity**: `ExternalIRQ`

```
ExternalIRQ {
    signal: xIRQ             // External maskable interrupt
    width: 1_bit
    polarity: active_low     // 0 = IRQ asserted

    usage_mvp: xIRQ = 1'b1   // Inactive (no interrupts)
}
```

**Entity**: `InterruptMask`

```
InterruptMask {
    signal: IRQ_Msk          // Interrupt mask bit from P register
    width: 1_bit
    source: P[2]             // I flag in processor status word
    direction: output        // From CPU to interrupt controller

    meaning: IRQ_Msk = 1 → interrupts disabled
            IRQ_Msk = 0 → interrupts enabled
}
```

### 1.6 Status Signal Entities

**Entity**: `InstructionStatus`

```
InstructionStatus {
    signal: Done             // Instruction complete indicator
    width: 1_bit
    assertion: pulse_1_clock // Pulses high when instruction completes
    timing: asserted_when = instruction_fetch_of_next_instruction

    signal: SC               // Single cycle instruction indicator
    width: 1_bit
    meaning: SC = 1 → instruction completes in 1 microcycle

    signal: Mode[2:0]        // Instruction type indicator
    width: 3_bits
    encoding: {
        3'd0: STP            // Stop processor
        3'd1: INV            // Invalid opcode
        3'd2: BRK            // Break instruction
        3'd3: JMP            // Branch/jump/return
        3'd4: STK            // Stack operation
        3'd5: INT            // Single cycle ALU op
        3'd6: MEM            // Multi-cycle memory op
        3'd7: WAI            // Wait for interrupt
    }

    signal: RMW              // Read-modify-write flag
    width: 1_bit
    meaning: RMW = 1 → instruction is RMW (INC, DEC, ASL, etc.)
}
```

**Entity**: `MemoryType`

```
MemoryType {
    signal: MemTyp[1:0]      // Memory access classification
    width: 2_bits
    encoding: {
        2'b00: PROGRAM       // Program memory (instruction fetch)
        2'b01: PAGE_0        // Zero page memory
        2'b10: PAGE_1        // Stack page (page 1, $0100-$01FF)
        2'b11: DATA          // General data memory
    }

    usage: informational     // Not used in MVP, provided for debugging
}
```

### 1.7 Internal Register Entities

**Entity**: `InternalRegisters`

```
InternalRegisters {
    // Programmer-visible registers
    signal: A[7:0]           // Accumulator
    signal: X[7:0]           // X index register
    signal: Y[7:0]           // Y index register
    signal: S[7:0]           // Stack pointer
    signal: P[7:0]           // Processor status word
    signal: PC[15:0]         // Program counter

    // Internal working registers
    signal: IR[7:0]          // Instruction register
    signal: OP1[7:0]         // Operand register 1
    signal: OP2[7:0]         // Operand register 2

    purpose: debug_access    // Exposed for simulation/debugging
    direction: output        // Read-only from external view
}
```

---

## 2. Timing Relationships

### 2.1 Microcycle State Transitions

**State Machine**: `MicrocycleController`

```
States: {ADDR_SETUP(2), MEM_ACCESS(3), DATA_VALID(1), CYCLE_END(0)}

Transitions (Normal Operation, Wait=0):
    ADDR_SETUP(2) → MEM_ACCESS(3)    [1 clock]
    MEM_ACCESS(3) → DATA_VALID(1)    [1 clock]
    DATA_VALID(1) → CYCLE_END(0)     [1 clock]
    CYCLE_END(0)  → ADDR_SETUP(2)    [1 clock]

Transitions (Wait State, Wait=1 sampled at MC=3):
    MEM_ACCESS(3) → WAIT_1(7)        [1 clock, wait detected]
    WAIT_1(7)     → WAIT_2(6)        [1 clock, waiting]
    WAIT_2(6)     → MEM_ACCESS(3)    [1 clock, retry]
    (then normal sequence if Wait=0)

Period: 4 clocks (normal), 8+ clocks (with wait states)
Frequency: 6.25 MHz (normal), <6.25 MHz (with waits)
```

**Timing Diagram** (see `contracts/memory-timing.md` for visual diagrams):

```
Clock Cycle:  |  0  |  1  |  2  |  3  |  4  |  5  |  6  |  7  |
MC State:     |  2  |  3  |  1  |  0  |  2  |  3  |  1  |  0  |
AO:           |<-ADDR1--->|     |  X  |<-ADDR2--->|     |  X  |
IO_Op:        |<--OP1----->|     |  X  |<--OP2----->|     |  X  |
DO (write):   |  X  |<-DATA1->|  X  |  X  |<-DATA2->|  X  |
DI (read):    |  X  |  ?  | VALID ↑   |  X  |  ?  | VALID ↑   |
                                 capture              capture
```

### 2.2 Memory Access Timing

**Read Cycle Timing**:

```
Cycle 0 (MC=2):
    - CPU presents address on AO
    - IO_Op = 2'b10 or 2'b11 (read/fetch)
    - Address decoder begins decode

Cycle 1 (MC=3):
    - AO stable and valid
    - Memory reads address, begins internal access
    - Block RAM latency begins (1 clock)

Cycle 2 (MC=1):
    - AO still stable
    - Memory outputs data on DI
    - DI must be stable by end of this cycle

Cycle 3 (MC=0):
    - Rising edge: CPU captures DI into internal registers
    - Next microcycle begins (AO may change)
```

**Write Cycle Timing**:

```
Cycle 0 (MC=2):
    - CPU presents address on AO
    - IO_Op = 2'b01 (write)
    - DO may not be valid yet

Cycle 1 (MC=3):
    - AO stable, DO becomes valid
    - mem_we = (ram_cs && IO_Op==01 && MC==3) asserted
    - Block RAM write occurs on this rising edge

Cycle 2 (MC=1):
    - AO and DO held stable
    - Write completes

Cycle 3 (MC=0):
    - mem_we deasserted
    - Next microcycle begins
```

### 2.3 Synchronous RAM Integration

**RAM Timing Characteristics**:

```
RAM_Type: Synchronous Block RAM
    Read_Latency: 1 clock
    Write_Latency: 0 clocks (write on current cycle)

    Read_Timing:
        Clock N:   Address presented → RAM_addr input
        Clock N+1: Data available ← RAM_data output

    Write_Timing:
        Clock N:   Address + Data + WE asserted
                   → Write occurs on rising edge
        Clock N+1: Write complete, data stored
```

**Integration with M65C02**:

```
Perfect 4-cycle match:
    MC=2 (cycle 0): Address → RAM
    MC=3 (cycle 1): RAM latency cycle, Data → RAM output
    MC=1 (cycle 2): Data valid on DI
    MC=0 (cycle 3): Data captured by CPU

No wait states needed: Wait = 1'b0 (always)
```

---

## 3. Memory Cycle State Machine

### 3.1 State Machine Definition

**Entity**: `MemoryCycleFSM`

```
States:
    IDLE         - No memory operation
    FETCH_ADDR   - Instruction fetch address phase (MC=2, IO_Op=11)
    FETCH_DATA   - Instruction fetch data phase (MC=3,1, IO_Op=11)
    READ_ADDR    - Data read address phase (MC=2, IO_Op=10)
    READ_DATA    - Data read data phase (MC=3,1, IO_Op=10)
    WRITE_ADDR   - Data write address phase (MC=2, IO_Op=01)
    WRITE_DATA   - Data write data phase (MC=3,1, IO_Op=01)

Inputs:
    MC[2:0]      - Current microcycle state
    IO_Op[1:0]   - Current I/O operation

Outputs:
    mem_we       - Memory write enable
    mem_oe       - Memory output enable (informational)
    addr_valid   - Address is valid and stable
    data_capture - Capture DI on this clock
```

**State Transitions**:

```
IDLE → FETCH_ADDR:   when (MC == 2) && (IO_Op == 2'b11)
FETCH_ADDR → FETCH_DATA: when (MC == 3)
FETCH_DATA → IDLE:   when (MC == 0) [capture instruction]

IDLE → READ_ADDR:    when (MC == 2) && (IO_Op == 2'b10)
READ_ADDR → READ_DATA: when (MC == 3)
READ_DATA → IDLE:    when (MC == 0) [capture data]

IDLE → WRITE_ADDR:   when (MC == 2) && (IO_Op == 2'b01)
WRITE_ADDR → WRITE_DATA: when (MC == 3)
WRITE_DATA → IDLE:   when (MC == 0) [write complete]
```

### 3.2 Write Enable Generation

**Logic**: `MemoryWriteEnable`

```
mem_we = (IO_Op == 2'b01) &&        // Write operation
         (MC == 3 || MC == 1) &&    // Active during cycles 1-2
         chip_select                // Specific memory selected

Examples:
    ram_we = (IO_Op == 2'b01) && (MC == 3 || MC == 1) && ram_cs

    Note: Some implementations use (MC == 3) only for synchronous write
          Our block RAM writes on rising edge at MC=3
```

### 3.3 Data Capture Logic

**Logic**: `DataCaptureControl`

```
data_capture_enable = (IO_Op == 2'b10 || IO_Op == 2'b11) &&  // Read or fetch
                      (MC == 0) &&                             // End of cycle
                      rising_edge(Clk)                         // Clock edge

Implementation:
    always @(posedge Clk) begin
        if (system_rst)
            cpu_data_in_reg <= 8'hEA;  // NOP during reset
        else if (MC == 0)  // Capture when microcycle completes
            cpu_data_in_reg <= cpu_data_in_mux;  // Capture from mux
    end
```

---

## 4. Microcycle Controller Configuration

### 4.1 MPCv4 Parameters

**Module**: `M65C02_MPCv4`

```
Parameters:
    pAddrWidth = 9           // Microprogram address width (512 locations)
    pRst_Addrs = 0           // Reset address in microprogram ROM

Configuration:
    Microcycle_Length: FIXED at 4 clocks
    Wait_States: Supported (4-clock increments)

    No uLen input (unlike MPCv3):
        MPCv4 has fixed 4-cycle length
        MPCv3 had configurable 1/2/4 cycle length via uLen[1:0]
```

### 4.2 Wait State Configuration

**Configuration**: `WaitStateControl`

```
System Configuration:
    Wait = 1'b0              // Constant 0 for internal memory

    Reason: All internal memory (RAM, ROMs) are synchronous block RAM
            with 1-cycle read latency, perfectly matching 4-cycle microcycle

Future Use (External Memory):
    Wait = address_decoder_slow_memory_signal
    Effect: Adds 4-clock wait states per assertion
    Example: External SRAM with 70ns access time might need 1 wait state
```

### 4.3 Frequency Configuration

**Configuration**: `ClockFrequency`

```
Input Clock:
    clk_25mhz = 25.000 MHz   // FPGA system clock
    period = 40ns

Microcycle:
    length = 4 clocks
    period = 160ns
    frequency = 6.25 MHz

Instruction Execution:
    M65C02 is pipelined: many instructions complete in <4 microcycles
    Effective IPC (instructions per cycle): varies, avg ~0.7
    Effective instruction rate: ~4-5 MIPS

Comparison to Arlet Core:
    Arlet: 1 MHz clock enable, ~1 MHz instruction rate
    M65C02: 6.25 MHz microcycle, ~4 MHz effective instruction rate
    Speedup: ~4x faster instruction execution ✅
```

---

## 5. Reset Behavior

### 5.1 Reset Sequence

**Sequence**: `SystemResetSequence`

```
1. External Reset:
    reset_button_n pressed (active low)
    ↓
2. Reset Controller:
    Detects button press with debounce
    Asserts system_rst (active high)
    ↓
3. M65C02 Core Reset:
    Rst input asserted (active high)
    PC ← Vector from address $FFFC (reset vector)
    S ← 8'hFF (stack pointer initialized)
    P ← 8'b00110100 (I flag set, D cleared)
    ↓
4. Microprogram Reset:
    MPC resets to address pInt_Hndlr (parameter)
    MC state machine resets to MC=2
    ↓
5. First Instruction Fetch:
    Fetches instruction from reset vector address
    System begins normal operation

Minimum Reset Duration: 4 clocks (160ns @ 25MHz)
Recommended: 100ms+ (handled by reset_controller debounce)
```

### 5.2 Reset State Values

**State**: `ResetInitialConditions`

```
Registers:
    PC = Vector[15:0] from $FFFC/$FFFD
    S = 8'hFF
    A = 8'h00 (undefined, typically 0)
    X = 8'h00 (undefined, typically 0)
    Y = 8'h00 (undefined, typically 0)
    P = 8'b00110100 (I=1, D=0, others undefined)

Control Signals:
    MC = 2 (ADDR_SETUP state)
    IO_Op = 2'b11 (instruction fetch)
    Done = 0
    SC = 0
    Mode = 3'd5 (INT - single cycle, typical for first fetch)

Bus:
    AO = Vector[15:0]
    DO = 8'h00
    DI = captured during first fetch
```

---

## 6. Data Flow Diagrams

### 6.1 Read Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Read Cycle Data Flow                     │
└─────────────────────────────────────────────────────────────────┘

Cycle 0 (MC=2):
    M65C02_Core                    Address        Memory
    ┌──────────┐                   Decoder        Subsystem
    │          │                  ┌────────┐    ┌──────────┐
    │   MAR    │──AO[15:0]───────→│ Decode │───→│ RAM/ROM  │
    │          │                  │  CS    │    │          │
    └──────────┘                  └────────┘    │  addr←   │
         │                                       └──────────┘
         ↓ MC advances

Cycle 1 (MC=3):
    M65C02_Core                                   Memory
    ┌──────────┐                                ┌──────────┐
    │          │                                │ RAM/ROM  │
    │  (wait)  │                                │          │
    │          │                                │ internal │
    └──────────┘                                │ latency  │
         │                                       └──────────┘
         ↓ MC advances

Cycle 2 (MC=1):
    M65C02_Core                   Data            Memory
    ┌──────────┐                   Mux           Subsystem
    │          │    ┌────────┐    (comb)       ┌──────────┐
    │          │←───│ DI_mux │←──select────────│ RAM/ROM  │
    │          │    └────────┘                  │          │
    └──────────┘       ↑                        │ data_out │
         │             │                        └──────────┘
         │             └── CS signals
         ↓ MC advances

Cycle 3 (MC=0):
    M65C02_Core                   Data
    ┌──────────┐                  Register
    │          │    ┌────────┐   (MC=0 edge)
    │ Internal │←───│DI_reg  │← DI_mux
    │ Regs     │    └────────┘   CAPTURE
    └──────────┘
         │
         ↓ Next instruction/operand
```

### 6.2 Write Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Write Cycle Data Flow                     │
└─────────────────────────────────────────────────────────────────┘

Cycle 0 (MC=2):
    M65C02_Core                    Address        WE
    ┌──────────┐                   Decoder      Generator
    │          │                  ┌────────┐    ┌──────┐
    │   MAR    │──AO[15:0]───────→│ Decode │───→│ WE=0 │
    │          │                  │  CS    │    │ Logic│
    │   DO←    │──DO[7:0]────┐   └────────┘    └──────┘
    └──────────┘              │
         │                     └─────────────────┐
         ↓ MC advances                           ↓

Cycle 1 (MC=3):
    M65C02_Core                   Write           Memory
    ┌──────────┐                  Enable         Subsystem
    │          │                 ┌──────┐       ┌──────────┐
    │   MAR    │──AO[15:0]──────→│      │──────→│ RAM      │
    │          │                  │ WE=1 │ we   │ addr     │
    │   DO     │──DO[7:0]────────→│      │─────→│ data_in  │
    └──────────┘                 └──────┘       │          │
         │                       ↑ (MC==3)      │ WRITE ←  │
         ↓ MC advances           CS + IO_Op     │ occurs   │
                                                 └──────────┘

Cycle 2 (MC=1):
    M65C02_Core                                   Memory
    ┌──────────┐                                ┌──────────┐
    │          │──AO[15:0]──(stable)───────────→│ RAM      │
    │          │                                 │          │
    │   DO     │──DO[7:0]───(stable)────────────→│ (hold)   │
    └──────────┘                                 └──────────┘
         │
         ↓ MC advances

Cycle 3 (MC=0):
    M65C02_Core                   WE              Memory
    ┌──────────┐                Generator        Subsystem
    │          │                 ┌──────┐       ┌──────────┐
    │          │                 │ WE=0 │──────→│ RAM      │
    │          │                 └──────┘       │          │
    └──────────┘                               │ complete │
         │                                       └──────────┘
         ↓ Next microcycle
```

---

## 7. Error Conditions and Edge Cases

### 7.1 Undefined States

**Case**: MC state outside {0, 1, 2, 3}

```
MC values 4-7 are possible in MC[2:0] but not used by MPCv4

Prevention: MPCv4 state machine only generates {0,1,2,3}
Detection: If MC ∉ {0,1,2,3} → design error in MPC
Handling: mem_we defaults to 0, data capture disabled
```

**Case**: IO_Op = 2'b00 (no operation)

```
Meaning: No memory operation this cycle
Handling: mem_we = 0, data not captured, normal microcycle progression
Usage: Internal ALU operations, register-to-register moves
```

### 7.2 Race Conditions

**Case**: Data bus capture timing

```
Risk: DI changes during MC=0 clock edge
Mitigation: DI registered when MC=1→0 transition
           Memory must hold data stable through MC=1

Constraint: t_hold(DI) ≥ 5ns after rising edge at MC=0
```

**Case**: Write enable pulse timing

```
Risk: mem_we pulse too short or misaligned
Mitigation: mem_we asserted for full MC=3 and MC=1 cycles (80ns)
           Block RAM write occurs at rising edge of MC=3

Constraint: mem_we must be stable ≥10ns before clock edge
```

### 7.3 Reset During Operation

**Case**: Reset asserted during mid-instruction

```
Behavior: Immediate abort of current instruction
          MPC jumps to reset microcode address
          MC state machine resets to MC=2
          All registers reset to initial values

Safety: No partial writes occur (mem_we deasserted immediately)
```

---

## 8. Signal Integrity Constraints

### 8.1 Setup and Hold Times

```
Signal: AO[15:0] (Address Output)
    t_setup:  ≥ 10ns before memory access (end of MC=2)
    t_hold:   ≥ 40ns after memory access begins (through MC=3, MC=1)

Signal: DO[7:0] (Data Output, writes)
    t_setup:  ≥ 10ns before mem_we assertion
    t_hold:   ≥ 40ns after mem_we assertion (through MC=1)

Signal: DI[7:0] (Data Input, reads)
    t_setup:  ≥ 5ns before capture (rising edge at MC=0)
    t_hold:   ≥ 2ns after capture

Signal: IO_Op[1:0]
    t_stable: Must be stable entire microcycle (MC=2 through MC=0)

Signal: Wait
    t_setup:  ≥ 10ns before sampled (end of MC=3 or MC=1)
```

### 8.2 Clock Domain Constraints

```
All signals are synchronous to clk_25mhz:
    Single clock domain
    No CDC (Clock Domain Crossing) issues
    No metastability concerns for internal signals

External signals (UART rx):
    Handled by UART module with synchronizers
    Not directly connected to CPU
```

---

## 9. Design Validation Criteria

### 9.1 Signal Timing Validation

✅ AO stable for ≥3 clocks during microcycle
✅ DO valid before mem_we asserted
✅ DI captured only at MC=0 transition
✅ IO_Op doesn't change during microcycle
✅ MC sequence is always 2→3→1→0

### 9.2 Functional Validation

✅ Read cycle: data captured from memory correct
✅ Write cycle: data written to memory correct
✅ Instruction fetch: PC increments correctly
✅ Zero page access: addresses $0000-$00FF work
✅ Reset sequence: system boots to monitor

### 9.3 Performance Validation

✅ Microcycle frequency = 6.25 MHz (4 clocks @ 25 MHz)
✅ No unintended wait states (Wait always 0)
✅ Instruction execution starts within 1 microcycle of reset
✅ Memory access completes within 4 clocks (single microcycle)

---

## Next Steps

This data model provides the foundation for:

1. **Signal Timing Diagrams** → `contracts/memory-timing.md`
2. **Interface Specifications** → `contracts/m65c02-signals.md`
3. **Integration Logic** → `contracts/signal-adaptation.md`
4. **Implementation** → RTL modifications in soc_top.v

**Status**: Data model complete ✅ | Ready for contract specifications
