# 6502 Core Comparison for FPGA Implementation

## Executive Summary

This document compares open-source 6502 CPU cores suitable for FPGA implementation, with particular focus on compatibility with clock-enable style operation needed for our RetroCPU project. Our current issue is that the Arlet 6502 core's RDY signal implementation is incompatible with clock division via RDY gating.

## Current Core: Arlet 6502 (verilog-6502)

**Repository**: [GitHub - Arlet/verilog-6502](https://github.com/Arlet/verilog-6502)
**Language**: Verilog
**Status**: Active, widely used (363 stars, 100 forks)

### Features
- Clean, compact implementation
- Synchronous memory interface (expects valid data cycle after address)
- Direct compatibility with Xilinx block RAMs
- Extended to cover 65C02 opcodes by Ed Spittles and David Banks

### Interface
- Standard 6502 signals: AB (address bus), DI (data in), DO (data out), WE (write enable)
- RDY signal for wait states
- IRQ/NMI interrupt inputs

### Critical Issue
- **DIMUX logic**: `assign DIMUX = ~RDY ? DIHOLD : DI;`
- Designed for memory wait states, NOT clock division
- When RDY=1 for CPU execution, DIMUX switches to DI which may contain wrong data
- Causes zero page addressing to fail when RDY is used for clock enable

### Verdict
❌ **Not suitable** for clock-enable style operation without modification

---

## Alternative Cores

### 1. M65C02 - Microprogrammed Enhanced Core

**Repository**: [GitHub - MorrisMA/MAM65C02-Processor-Core](https://github.com/MorrisMA/MAM65C02-Processor-Core)
**OpenCores**: [M65C02 Project](https://opencores.org/projects/m65c02)
**Language**: Verilog-2001
**Status**: Stable, FPGA proven, actively maintained

#### Features
- Microprogrammed synthesizable 65C02-compatible core
- **Performance**: 73.728 MHz achieved in XC3S50A-4VQG100I FPGA
- Pipelined execution - many instructions in fewer cycles than 6502/65C02
- All undefined instructions implemented as single-cycle NOPs
- Includes Rockwell instruction opcodes, WAI, and STP

#### Memory Interface
- **Flexible microcycle controller**: Supports 1, 2, or 4-cycle memory access
- Wait states in integer multiples of memory cycle
- Separate read (nOE) and write (nWR) strobes for SRAM/EPROM
- Built-in address decoders
- Supports dual instruction/data memory spaces (doubles available memory)

#### Clock & Wait State Handling
✅ **Built-in microcycle length controller** specifically designed for flexible clocking
- Can configure 1-cycle LUT-based zero page
- 2-cycle internal block RAM
- 4-cycle external memory with wait states
- **This solves our clock division problem!**

#### Status Signals
- Mode indicators (STP, INV, BRK, JMP, STK, INT, MEM, WAI)
- Done flag for instruction completion
- SC (single-cycle instruction indicator)
- RMW (read-modify-write for memory locking)
- IO_Op (differentiates memory read/write/instruction fetch)
- All internal registers (A, X, Y, S, P) accessible

#### Differences from Standard 6502
- BRK, IRQ/NMI, JSR push address of last byte (not next instruction)
- Not all instructions are interruptible (CLI, SEI, jumps, branches, calls, returns)
- External interrupt prioritization and vector provision
- Branch instructions execute in 2 cycles (vs 2/3 on standard 6502)

#### Verdict
✅ **HIGHLY RECOMMENDED** - Designed specifically for flexible FPGA memory timing, includes built-in wait state support

---

### 2. cpu6502_tc - True Cycle Accurate Core

**OpenCores**: [cpu6502_tc Project](https://opencores.org/projects/cpu6502_true_cycle)
**GitHub Mirror**: [freecores/cpu6502_true_cycle](https://github.com/freecores/cpu6502_true_cycle/)
**Language**: VHDL
**Status**: Stable, FPGA proven (Rev 1.4, 2018)

#### Features
- True cycle timing for all official opcodes
- Unknown opcodes decoded as NOP/0xEA
- One clock source
- Fully synthesizable
- GPL licensed

#### Interface
- Input signal `rdy_i` for generating wait states
- Output signal `sync_o` to indicate opcode fetch

#### Recent Fixes (Rev 1.4)
- RESET generating SYNC
- ADC/SBC flags corrections
- Decimal mode bug fixes
- Branch instruction fixes

#### Verdict
⚠️ **Possible but requires VHDL** - Good cycle-accurate implementation with proper RDY support, but need to convert VHDL to Verilog or add VHDL to build system

---

### 3. T65 - Configurable Multi-CPU Core

**OpenCores**: [T65 CPU Project](https://opencores.org/projects/t65)
**Better Version**: FPGAArcade fork (recommended over OpenCores)
**Language**: VHDL
**Status**: Stable, widely used, FPGA proven

#### Features
- Configurable: Supports 6502, 65C02, and 65C816 instruction sets
- Small logic footprint (30% of xc3s200)
- Well-defined synchronous interface
- Ready mechanism for wait states
- Mimics real 6502 with inverted signals

#### Known Issues
- OpenCores version has bugs (e.g., ADC (),Y broken)
- **Use FPGAArcade fork** which fixes these issues
- Used in 5+ projects successfully

#### Verdict
✅ **Good option** - Mature, tested, proper wait state handling, but requires VHDL support

---

### 4. secworks/6502 - Educational Implementation

**Repository**: [GitHub - secworks/6502](https://github.com/secworks/6502)
**Language**: Verilog
**Status**: Hobby/educational project

#### Features
- Clean RTL design based on instruction set
- "Just for fun" implementation
- **Not cycle-accurate** (by design)

#### Verdict
❌ **Not recommended** - Educational quality, not cycle-accurate, unclear production readiness

---

### 5. 65F02 - High-Speed Pin-Compatible Core

**Website**: [e-basteln.de 65F02](https://www.e-basteln.de/computing/65f02/65f02/)
**Language**: Verilog/VHDL (mixed)
**Status**: Active (2024 update), reaching FPGA limits

#### Features
- Re-implementation of 65C02 for 100 MHz operation
- Pin-compatible format for upgrading old computers
- **July 2024 update**: Reaching FPGA resource limits

#### Verdict
⚠️ **Specialized use case** - Designed for high-speed retrofits, may be overkill and resource-heavy for our needs

---

### 6. ag_6502 - Phase-Level Accurate Core

**OpenCores**: [ag_6502 Project](https://opencores.org/projects/ag_6502)
**Language**: VHDL
**Status**: Available on OpenCores

#### Features
- Phase-level accuracy (more detailed than cycle accuracy)
- Designed for precise timing simulation

#### Verdict
⚠️ **Unknown** - Limited information available, requires VHDL

---

### 7. Visual 6502 Derived Core

**Website**: [aholme.co.uk/6502](http://www.aholme.co.uk/6502/Main.htm)
**Language**: Verilog
**Status**: Proven implementation

#### Features
- **Automatically generated from transistor-level netlist** (Visual 6502 project)
- Cycle-accurate by design (derived from actual chip)
- Performance: 10 MHz equivalent using <700 LUTs in Spartan-3E

#### Resource Efficiency
- Very compact: Under 700 LUTs
- Good for resource-constrained designs

#### Verdict
✅ **Interesting option** - Highly accurate, compact, Verilog, but may have similar RDY issues as Arlet core

---

## Comparison Matrix

| Core | Language | Cycle Accurate | RDY/Wait States | Clock Flexibility | Resources | Status | Our Compatibility |
|------|----------|----------------|-----------------|-------------------|-----------|--------|-------------------|
| **Arlet 6502** (current) | Verilog | No | For memory wait | ❌ RDY=CE breaks | Low | Active | ❌ Known issue |
| **M65C02** | Verilog | Enhanced | Microcycle controller | ✅ Excellent | Medium | Active | ✅ **BEST MATCH** |
| **cpu6502_tc** | VHDL | Yes | rdy_i input | ✅ Good | Low | Stable | ⚠️ Needs VHDL |
| **T65** | VHDL | Yes | Ready mechanism | ✅ Good | Low | Mature | ⚠️ Needs VHDL |
| **secworks** | Verilog | No | Unknown | ❓ Unknown | Unknown | Hobby | ❌ Not production |
| **65F02** | Mixed | Yes | Unknown | ❓ Unknown | High | Active | ⚠️ Overkill |
| **ag_6502** | VHDL | Phase-level | Unknown | ❓ Unknown | Unknown | Unknown | ❓ Insufficient info |
| **Visual 6502** | Verilog | Yes | Like real chip | ❓ May have same issue | Very Low | Proven | ⚠️ Needs investigation |

---

## Recommendations

### 1st Choice: M65C02 ⭐

**Why**: Specifically designed for flexible FPGA memory timing with built-in microcycle controller that handles wait states properly. This directly addresses our clock division issue.

**Migration Path**:
1. Replace Arlet core with M65C02 in soc_top.v
2. Configure microcycle controller for our memory timing (25 MHz system, 1 MHz CPU)
3. Use built-in wait state mechanism instead of RDY for clock division
4. Test zero page operations
5. Leverage status signals (Done, SC, RMW) for debugging

**Advantages**:
- ✅ Verilog (no language change needed)
- ✅ Designed for FPGA memory timing flexibility
- ✅ Higher performance (73+ MHz capable)
- ✅ Better debugging signals
- ✅ Rockwell extensions included
- ✅ Proven in FPGA implementations

**Disadvantages**:
- Different timing behavior (faster execution)
- Slightly different interrupt handling
- Need to learn new interface signals

### 2nd Choice: T65 (FPGAArcade fork)

**Why**: Mature, widely-used core with proper ready mechanism, but requires adding VHDL to build system.

**Migration Path**:
1. Add GHDL or equivalent to toolchain for VHDL synthesis
2. Create Verilog wrapper for T65 core
3. Connect ready mechanism for clock division
4. Test thoroughly (use FPGAArcade fixes)

**Advantages**:
- ✅ Proven in multiple projects
- ✅ Configurable (6502/65C02/65C816)
- ✅ Small resource footprint
- ✅ Proper wait state handling

**Disadvantages**:
- ❌ Requires VHDL toolchain
- ❌ Need wrapper/interface layer
- ❌ Inverted signals (different from standard)

### 3rd Choice: Fix Arlet Core

**Why**: Smallest change to existing system, but requires careful modification.

**Migration Path**:
1. Add proper DIHOLD initialization
2. Modify DIMUX logic to work with clock-enable RDY
3. Extensive testing required
4. Document changes for maintainability

**Advantages**:
- ✅ Minimal system changes
- ✅ Keep existing Verilog-only toolchain
- ✅ Maintain familiar interface

**Disadvantages**:
- ❌ May break other functionality
- ❌ Diverges from upstream
- ❌ Multiple failed attempts already

---

## Implementation Plan (M65C02)

### Phase 1: Core Integration (1-2 hours)
1. Download M65C02 core from GitHub
2. Review interface documentation
3. Create new soc_top.v with M65C02 instantiation
4. Map signals to existing memory/peripheral interfaces

### Phase 2: Microcycle Configuration (1-2 hours)
1. Configure microcycle controller for 25:1 clock division
2. Set memory cycle timing for block RAM
3. Connect wait state signals if needed
4. Update address decoder if required

### Phase 3: Testing (2-4 hours)
1. Synthesize and program FPGA
2. Verify basic boot and UART output
3. Test zero page writes specifically
4. Run full address range test
5. Test monitor commands
6. Test BASIC interpreter

### Phase 4: Optimization (1-2 hours)
1. Leverage status signals for debugging
2. Optimize memory timing if needed
3. Update documentation
4. Commit working solution

**Total Estimated Time**: 5-10 hours

---

## Conclusion

The **M65C02** core is the clear winner for our use case. Its built-in microcycle controller was specifically designed to handle the flexible memory timing we need for FPGA implementation with clock division. This directly solves our zero page write failure without requiring:
- Changes to the CPU core itself
- Addition of VHDL tooling
- Complex clock domain crossing
- Divergence from a maintained upstream

The migration should be straightforward, and the enhanced features (better performance, status signals, Rockwell extensions) provide additional benefits beyond just fixing the current issue.

---

## References

### Primary Sources
- [Arlet 6502 - GitHub](https://github.com/Arlet/verilog-6502)
- [M65C02 - GitHub](https://github.com/MorrisMA/MAM65C02-Processor-Core)
- [M65C02 - OpenCores](https://opencores.org/projects/m65c02)
- [cpu6502_tc - OpenCores](https://opencores.org/projects/cpu6502_true_cycle)
- [T65 - OpenCores](https://opencores.org/projects/t65)
- [secworks 6502 - GitHub](https://github.com/secworks/6502)
- [65F02 Project](https://www.e-basteln.de/computing/65f02/65f02/)
- [Visual 6502 Core](http://www.aholme.co.uk/6502/Main.htm)

### Community Discussion
- [FPGA Related - stable, tested 6502 core](https://www.fpgarelated.com/showthread/comp.arch.fpga/46627-1.php)
- [FPGA Arcade - T65 Core Discussion](http://www.fpgaarcade.com/punbb/viewtopic.php?id=291)

### Related Documentation
- ROOT_CAUSE_ANALYSIS.md - Detailed analysis of current Arlet core issue
- BUG_REPORT_ZERO_PAGE_WRITES.md - Zero page write failure documentation
- RAM_DEBUG_NOTES.md - Investigation notes

---

*Document created: December 23, 2025*
*Last updated: December 23, 2025*
