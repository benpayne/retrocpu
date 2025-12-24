# Memory Timing Diagrams and Specifications

**Date**: 2025-12-23
**Phase**: Phase 1 - Design (Contracts)
**Feature**: [spec.md](../spec.md) | [data-model.md](../data-model.md)

## Purpose

This document provides detailed timing diagrams for M65C02 memory cycles, including read, write, and instruction fetch operations. All timing is for our system configuration: 25 MHz clock, 4-cycle microcycles, synchronous block RAM.

---

## System Timing Parameters

```
System Clock Frequency:    25 MHz
System Clock Period:       40 ns
Microcycle Length:         4 clocks
Microcycle Period:         160 ns
Microcycle Frequency:      6.25 MHz

Block RAM Read Latency:    1 clock (40 ns)
Block RAM Write Latency:   0 clocks (writes on clock edge)
```

---

## Microcycle State Sequence

### Normal Operation (No Wait States)

```
Time:    0ns   40ns  80ns  120ns  160ns  200ns  240ns  280ns  320ns
         |     |     |     |      |      |      |      |      |
Clock:   ┐   ┌─┐   ┌─┐   ┌─┐    ┌─┐    ┌─┐    ┌─┐    ┌─┐    ┌─
         ┘───┘ └───┘ └───┘ └────┘ └────┘ └────┘ └────┘ └────┘

MC:      2   │ 3   │ 1   │  0    │  2   │  3   │  1   │  0   │  2
         ────┴─────┴─────┴───────┴──────┴──────┴──────┴──────┴────
         │◄── Microcycle 1 ──►│  │◄─── Microcycle 2 ──►│

States:  ADDR │ MEM │DATA │ END   │ ADDR │ MEM  │ DATA │ END  │
         SETUP│ ACC │VALID│ CYCLE │ SETUP│ ACC  │ VALID│ CYCLE│
```

**State Descriptions**:
- **MC=2 (ADDR_SETUP)**: Address presented, IO_Op becomes valid
- **MC=3 (MEM_ACCESS)**: Memory begins access, Write occurs here
- **MC=1 (DATA_VALID)**: Read data must be stable
- **MC=0 (CYCLE_END)**: Data captured, next cycle begins

---

## Read Cycle Timing

### Standard Read from Synchronous Block RAM

```
Time:    0ns   40ns  80ns  120ns  160ns
         |     |     |     |      |
Clock:   ┐   ┌─┐   ┌─┐   ┌─┐    ┌─
         ┘───┘ └───┘ └───┘ └────┘

MC:      2   │ 3   │ 1   │  0    │  2
         ────┴─────┴─────┴───────┴────

AO:      │◄────── ADDRESS A ───────►│◄─ ADDR B
         XXXX│◄─── STABLE ──────►│XXXX
              t_setup │      │ t_hold
                      │      │
IO_Op:   │◄─── 2'b10 (READ) ─────►│
         XXXX│                  │XXXX

RAM:          │ Addr │       │     │
              │  A   │ Read  │ Out │
              │  In  │ Proc  │ Valid
              └──────┴───────┴─────
                     │◄──────┤
                     │ 1 clk │
                     │latency│

DI:           │ XXXX │ Prop  │◄─ DATA A ──►│
              │      │ delay │   STABLE    │
              │      │       │ ────────────┤
                                    ▲
                                    │
Data                              Capture
Captured:                         at MC=0
                                  rising edge
```

**Timing Requirements**:
```
t_setup(AO):     Address valid 10ns before MC=3 begins
t_hold(AO):      Address stable until MC=0
t_access(RAM):   1 clock (40ns) from address to data valid
t_setup(DI):     Data stable ≥5ns before MC=0 edge
t_hold(DI):      Data stable ≥2ns after MC=0 edge
t_capture:       MC=0 rising edge
```

**Cycle Phases**:
1. **MC=2 (0-40ns)**: CPU presents address on AO, IO_Op=2'b10 (READ)
2. **MC=3 (40-80ns)**: RAM captures address, begins internal read
3. **MC=1 (80-120ns)**: RAM outputs data on DI, data becomes valid
4. **MC=0 (120-160ns)**: CPU captures DI at rising edge

---

## Write Cycle Timing

### Standard Write to Synchronous Block RAM

```
Time:    0ns   40ns  80ns  120ns  160ns
         |     |     |     |      |
Clock:   ┐   ┌─┐   ┌─┐   ┌─┐    ┌─
         ┘───┘ └───┘ └───┘ └────┘
              ▲
              │
           Write occurs
           here (rising
           edge MC=3)

MC:      2   │ 3   │ 1   │  0    │  2
         ────┴─────┴─────┴───────┴────

AO:      │◄────── ADDRESS A ───────►│◄─ ADDR B
         XXXX│◄─── STABLE ──────►│XXXX

IO_Op:   │◄─── 2'b01 (WRITE) ────►│
         XXXX│                  │XXXX

DO:      │ XXXX │◄── DATA A ──────►│
         │      │   STABLE        │XXXX
         │      │ ────────────────┤
                │ t_setup │◄─ t_hold ─►│

mem_we:  ────│         ┌────────┐     │────
         (low) │         │  HIGH  │     │ (low)
              │         │        │     │
              │         └────────┘     │
              │         MC=3 & MC=1    │
              └──────────────────────┘
                 WE pulse width: 80ns

RAM:          │ Addr │ Write│      │
              │  A   │ Data │      │
              │  In  │  In  │ Done │
              └──────┴──────┴──────
                     ▲
                     │
                  Write
                 happens
                 on this
                 clock edge
```

**Timing Requirements**:
```
t_setup(AO):     Address valid 10ns before MC=3 rising edge
t_setup(DO):     Data valid 10ns before MC=3 rising edge
t_hold(AO):      Address stable through MC=1
t_hold(DO):      Data stable through MC=1
t_pulse(mem_we): Write enable high for 80ns (MC=3 + MC=1)
```

**Cycle Phases**:
1. **MC=2 (0-40ns)**: CPU presents address, IO_Op=2'b01 (WRITE), DO may be changing
2. **MC=3 (40-80ns)**: DO valid, mem_we asserted, write occurs at rising edge (40ns)
3. **MC=1 (80-120ns)**: AO and DO held stable, mem_we still asserted
4. **MC=0 (120-160ns)**: mem_we deasserted, write complete, next cycle

**Write Enable Generation**:
```verilog
assign mem_we = (IO_Op == 2'b01) && (MC == 3 || MC == 1) && chip_select;

// Alternative: Write only on MC=3 rising edge
assign mem_we = (IO_Op == 2'b01) && (MC == 3) && chip_select;
```

---

## Instruction Fetch Timing

### Instruction Fetch Cycle (Same as Read, IO_Op=2'b11)

```
Time:    0ns   40ns  80ns  120ns  160ns
         |     |     |     |      |
Clock:   ┐   ┌─┐   ┌─┐   ┌─┐    ┌─
         ┘───┘ └───┘ └───┘ └────┘

MC:      2   │ 3   │ 1   │  0    │  2
         ────┴─────┴─────┴───────┴────

AO:      │◄─────── PC ──────────►│◄─ PC+1
         XXXX│ Program Counter │XXXX

IO_Op:   │◄──── 2'b11 (FETCH) ───►│
         XXXX│                  │XXXX

DI:      │ XXXX │ Prop  │◄ OPCODE ─►│
         │      │ delay │  STABLE   │
                              ▲
                              │
IR ← DI:                  Captured
                          at MC=0

Done:    ──────────────────┐ ┌─────
                           └─┘
                      Pulse at MC=0
                      (instruction
                       complete)
```

**Timing**:
- Identical to read cycle timing
- IO_Op = 2'b11 distinguishes fetch from data read
- Done pulse marks instruction completion
- PC increments after fetch (for sequential execution)

---

## Data Bus Multiplexer Timing

### Read Data Path with Registered Multiplexer

```
Address Decoder              Data Multiplexer          CPU Input Register
┌────────────┐              ┌──────────────┐          ┌─────────────┐
│            │              │              │          │             │
│ AO → decode│              │  ram_out ────┤          │ DI_reg      │
│            │              │              │          │             │
│ ram_cs ────┼────────────→ │  rom_out ────┤          │  ← DI_mux   │
│ rom_cs ────┼────────────→ │              ├─ DI_mux ─┤             │
│ uart_cs ───┼────────────→ │  uart_out ───┤          │             │
│            │              │              │          │             │
│            │              │  default: FF ┤          │ enable: MC==0│
└────────────┘              └──────────────┘          └─────────────┘
    │                             │                         │
    └─── 1 clock decode ───┘     └─ combo mux ─┘          └─ register


Timing Diagram:

Clock:   ┐   ┌─┐   ┌─┐   ┌─┐    ┌─
         ┘───┘ └───┘ └───┘ └────┘

MC:      2   │ 3   │ 1   │  0    │

AO:      │◄──── ADDRESS ──────►│

CS:           │◄─ chip_select ─►│
         ─────┐ valid           └────
              └─────────────────

RAM_out:      │ XXXX │◄─ VALID ─►│
              │      │  DATA    │

DI_mux:       │ XXXX │◄─ VALID ─►│
              │      │  (combo) │
              │      │          │
                     │          │
DI_reg:       │ OLD  │◄──────────│◄ NEW
              │ DATA │           │  DATA
                                 ▲
                                 │
                             Captured
                             at MC=0
                             rising edge
```

**Implementation**:
```verilog
// Combinational multiplexer
always @(*) begin
    case (1'b1)
        ram_cs:         cpu_data_in_mux = ram_data_out;
        rom_basic_cs:   cpu_data_in_mux = rom_basic_data_out;
        rom_monitor_cs: cpu_data_in_mux = rom_monitor_data_out;
        uart_cs:        cpu_data_in_mux = uart_data_out;
        default:        cpu_data_in_mux = 8'hFF;
    endcase
end

// Registered at MC=0 for stable capture
always @(posedge clk_25mhz) begin
    if (system_rst)
        cpu_data_in_reg <= 8'hEA;  // NOP during reset
    else if (cpu_mc == 3'b000)  // MC = 0
        cpu_data_in_reg <= cpu_data_in_mux;
end

assign cpu_data_in = cpu_data_in_reg;
```

---

## Wait State Timing

### Microcycle with Wait State Insertion

Our system doesn't use wait states (Wait=0), but here's how they work:

```
Time:    0ns   40ns  80ns  120ns  160ns  200ns  240ns  280ns  320ns
         |     |     |     |      |      |      |      |      |
Clock:   ┐   ┌─┐   ┌─┐   ┌─┐    ┌─┐    ┌─┐    ┌─┐    ┌─┐    ┌─
         ┘───┘ └───┘ └───┘ └────┘ └────┘ └────┘ └────┘ └────┘

Wait:    ──────────────┐                    ┌─────────────────
                       └────────────────────┘
                       Asserted at MC=3    │ Deasserted
                                           │ at MC=3

MC:      2   │ 3   │ 7   │  6    │  3   │  1   │  0   │
         ────┴─────┴─────┴───────┴──────┴──────┴──────┴────
         │        Wait detected  │          Normal resume

         │◄── Original ──►│◄─ Wait State ──►│◄─ Complete ─►│
         │   Cycle Start  │   Inserted      │  Cycle End   │

Duration: Normal cycle: 4 clocks (160ns)
         With 1 wait:  8 clocks (320ns)
         Each wait:    +4 clocks (+160ns)
```

**Wait State Sequence**:
1. MC=3: Wait sampled at end of cycle
2. If Wait=1: Jump to MC=7 (wait state 1)
3. MC=7 → MC=6 (wait state 2)
4. MC=6 → MC=3 (return to memory access)
5. MC=3: Re-sample Wait
6. If Wait=0: Continue to MC=1 (normal completion)
7. If Wait=1: Repeat wait sequence

**Our Usage**: `Wait = 1'b0` (constant) → No wait states ever inserted

---

## Reset Timing

### System Reset and First Instruction Fetch

```
Time:    -40ns  0ns   40ns  80ns  120ns  160ns  200ns  240ns
         |      |     |     |     |      |      |      |
Reset:   ──────┐      ┌─────────────────────────────────────
Button   ──────┘      └───── Released ──────────────────────
Press            │
                 │
System   ──────┐ │    ┌─────────────────────────────────────
Rst:     ──────┘ └────┘ Debounced, synchronized
                 │ ◄─►│
                 │  4+ │
                 │clocks│

Clock:   ┐   ┌─┐   ┌─┐   ┌─┐    ┌─┐    ┌─┐    ┌─┐    ┌─
         ┘───┘ └───┘ └───┘ └────┘ └────┘ └────┘ └────┘

MC:      X   │ 2   │ 3   │  1   │  0   │  2   │  3   │
         ────┴─────┴─────┴──────┴──────┴──────┴──────┴────
              │◄──── First Instruction Fetch ──────►│

AO:      XXXX │◄─────── $FFFC ───────►│◄─ Next PC ──
              │  (Reset Vector Addr)  │

IO_Op:   XXXX │◄────── 2'b11 ────────►│
              │     (Instruction      │
              │      Fetch)           │

DI:      XXXX │ XXXX │ Prop  │◄ Vector│
              │      │ delay │  Low   │
                                  ▲
PC:      XXXX │◄─ Initialize ────►│◄─ Vector Addr ─►
              │   from Vector    │  (from $FFFC/D)
              │                  │  First instruction

S:       XXXX │◄──── $FF ─────────────────────►
              │  (Stack pointer initialized)

P:       XXXX │◄──── $34 ─────────────────────►
              │  (I=1, D=0, others undefined)
```

**Reset Sequence**:
1. **-40ns to 0ns**: Reset button pressed
2. **0ns**: System_rst asserted (synchronized, debounced)
3. **0-40ns**: MPC resets, MC → 2
4. **40-160ns**: First instruction fetch from reset vector address
5. **160ns**: PC loaded with ISR address, execution begins

**Reset Vector Fetch**:
- Address $FFFC/$FFFD contains reset vector (typically $E000 for monitor)
- CPU reads 2 bytes (low, high) to load PC
- First instruction executed from reset vector address

---

## Multi-Cycle Instruction Timing Example

### STA $0010 (Store Accumulator to Zero Page)

```
Cycle 1: Fetch Opcode ($85)
---------------------------------------------------------------------------
Time:    0ns   40ns  80ns  120ns  160ns
Clock:   ┐   ┌─┐   ┌─┐   ┌─┐    ┌─
         ┘───┘ └───┘ └───┘ └────┘

MC:      2   │ 3   │ 1   │  0    │
AO:      │◄────── PC ──────────►│  (e.g., $E100)
IO_Op:   │◄──── 2'b11 ────────►│  (Fetch)
DI:           │      │◄── $85 ──►│  (STA zp opcode)
IR:                          ▲
                             │ IR ← $85


Cycle 2: Fetch Operand ($10)
---------------------------------------------------------------------------
Time:    160ns 200ns 240ns  280ns  320ns
Clock:   ┐   ┌─┐   ┌─┐   ┌─┐    ┌─
         ┘───┘ └───┘ └───┘ └────┘

MC:      2   │ 3   │ 1   │  0    │
AO:      │◄───── PC+1 ───────►│  (e.g., $E101)
IO_Op:   │◄──── 2'b11 ────────►│  (Fetch operand)
DI:           │      │◄── $10 ──►│  (Zero page address)
OP1:                         ▲
                             │ OP1 ← $10


Cycle 3: Write to Memory
---------------------------------------------------------------------------
Time:    320ns 360ns 400ns  440ns  480ns
Clock:   ┐   ┌─┐   ┌─┐   ┌─┐    ┌─
         ┘───┘ └───┘ └───┘ └────┘

MC:      2   │ 3   │ 1   │  0    │
AO:      │◄───── $0010 ───────►│  (Zero page addr from OP1)
IO_Op:   │◄──── 2'b01 ────────►│  (Write)
DO:           │◄── A ──────────►│  (Accumulator value)
mem_we:       └─────┐  ┌───────┘
                    └──┘

RAM[$0010]: XXXX       ▲        NEW  (Write occurs at MC=3 edge)
                       │
                    Write
                   happens


Total Time: 3 microcycles = 12 clocks = 480ns
```

**Phases**:
1. **Microcycle 1**: Fetch opcode $85 (STA zp) into IR
2. **Microcycle 2**: Fetch zero page address $10 into OP1
3. **Microcycle 3**: Write accumulator value to $0010

---

## Comparison: Arlet vs M65C02 Timing

### Arlet 6502 (Previous System)

```
Clock:       25 MHz (40ns period)
Clock Enable: 1 MHz (every 25 clocks)
Instruction:  Variable, typically 2-8 cycles
              But "cycle" is at 1 MHz (1000ns)

Example - STA $0010:
    Cycle 0-2:   Fetch opcode (1 MHz cycle = 25 clocks)
    Cycle 2-4:   Fetch operand
    Cycle 4-7:   Write to memory
    Total: 3 cycles @ 1 MHz = 3000ns (3 μs)

Problem: RDY-based clock enable causes zero page corruption!
```

### M65C02 (New System)

```
Clock:        25 MHz (40ns period) - Full speed, no clock enable
Microcycle:   4 clocks = 160ns
Instruction:  Variable, typically 2-5 microcycles (pipelined)

Example - STA $0010:
    Microcycle 1:  Fetch opcode (4 clocks = 160ns)
    Microcycle 2:  Fetch operand (4 clocks = 160ns)
    Microcycle 3:  Write to memory (4 clocks = 160ns)
    Total: 3 microcycles = 480ns

Speedup: 3000ns / 480ns = 6.25x faster!
Benefit: No RDY corruption, zero page works correctly
```

---

## Timing Violations and Debug

### Common Timing Issues

**Issue 1: Data Not Stable at Capture**
```
DI should be stable:  │◄──── STABLE ────►│
                              ▲
                              │
But actually is:      │ XXXX ? │ VALID  │
                            ▲  Wrong!
                            │
                      Changed too late,
                      captured wrong value

Fix: Ensure memory has 1-cycle latency, data valid by MC=1
```

**Issue 2: Write Enable Too Short**
```
mem_we should be:     ┌────────────┐
                      │  MC=3, 1   │
                      └────────────┘

But actually is:      ┌──┐
                      │  │ Too short!
                      └──┘

Fix: Assert mem_we for both MC=3 and MC=1
```

**Issue 3: Address Changes During Access**
```
AO should be:         │◄─── STABLE ───►│
                      │    MC=2,3,1    │

But actually is:      │ ADDR1 │ ADDR2 │
                              ▲ Changed!
                              │ during access

Fix: Ensure AO driven by registered source, stable through microcycle
```

### Debug Checklist

Use waveform viewer (GTKWave) to verify:

- [ ] MC sequence is always 2 → 3 → 1 → 0
- [ ] AO stable for ≥3 clocks during access
- [ ] IO_Op doesn't change during microcycle
- [ ] DI stable during MC=1 and MC=0 edge
- [ ] DO valid during MC=3 and MC=1 (for writes)
- [ ] mem_we asserted only when IO_Op=01 and MC∈{3,1}
- [ ] Data captured into DI_reg at MC=0 rising edge
- [ ] No glitches on address or data buses

---

## Signal Timing Summary Table

| Signal | Setup Time | Hold Time | Valid Period | Notes |
|--------|------------|-----------|--------------|-------|
| `AO` | 10ns before MC=3 | Until MC=0 | MC=2,3,1 | Address stable 3 clocks |
| `DI` | 5ns before MC=0 | 2ns after MC=0 | MC=1 | Must be stable at capture |
| `DO` | 10ns before MC=3 | Through MC=1 | MC=3,1 (writes) | Stable during write |
| `IO_Op` | At MC=2 start | Until MC=0 | MC=2,3,1,0 | Stable entire microcycle |
| `MC` | N/A (output) | N/A | Always | Updates every clock |
| `Wait` | 10ns before MC=3/1 end | 5ns after | When needed | We use 0 (no waits) |
| `mem_we` | N/A (derived) | N/A | MC=3,1 | Pulse width 80ns |

---

## Related Documents

- **[m65c02-signals.md](m65c02-signals.md)** - Complete signal reference
- **[signal-adaptation.md](signal-adaptation.md)** - Arlet-to-M65C02 conversion
- **[data-model.md](../data-model.md)** - Signal entities and relationships

**Status**: Memory timing complete ✅
