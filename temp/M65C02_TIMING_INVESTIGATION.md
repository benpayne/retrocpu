# M65C02 Data Capture Timing Investigation

## Problem Statement

Monitor E/D commands cannot read I/O registers correctly - they return wrong values ($00 or constant values), but RAM reads work fine. This prevents debugging PS/2 and other peripherals from the monitor.

## M65C02 Timing Background

The M65C02 uses a 4-clock microcycle with internal state machine:
- **MC Sequence**: 4 → 6 → 7 → 5 → (repeat)
- **MC=6**: Address setup (Cycle 1)
- **MC=7**: Control asserted, memory access begins (Cycle 2)
- **MC=5**: Memory operation completes (Cycle 3 end)
- **MC=4**: Data capture window / next cycle starts (Cycle 4 start)

## Current Status (MC=5 Baseline)

### What Works ✓
- Firmware boots and outputs to UART
- Firmware I/O operations (CHROUT uses absolute addressing)
- RAM reads from monitor: `E 0200` returns correct value
- RAM writes from monitor: `D 0200 AA` → `E 0200` returns AA

### What Doesn't Work ✗
- Monitor I/O reads: `E C001` returns $00 (should show UART status with TX ready bit)
- Monitor I/O reads: `E C000` returns constant $30 in some tests
- Monitor I/O writes: `D C000 41` behavior uncertain
- PS/2 status register reads: `E C201` returns $00
- PS/2 LED activity not observed at MC=5

## Key Experimental Findings

### MC=4 Timing Test
**Observation**: With pure MC=4 timing:
- ✗ Firmware DOES NOT boot (no UART output)
- ✓ PS/2 LEDs show activity (LED0, LED1 flash, LED2 on, LED3 off with keypresses)
- This confirms PS/2 requires MC=4 timing

### MC=5 Timing Test
**Observation**: With MC=5 timing (current baseline):
- ✓ Firmware boots successfully
- ✓ Firmware UART writes work
- ✗ Monitor can't read I/O registers
- ✗ PS/2 doesn't show LED activity

### Firmware Dependency Discovery
**Critical Finding**: When UART status register was hardcoded to return $42:
- ✗ Firmware FAILED TO BOOT
- **Implication**: Firmware reads UART status during boot and expects specific values
- This means firmware uses data READ operations (not just instruction FETCH)

## Attempted Solutions (All Failed)

### 1. Dual-Capture with Address Latching
**Approach**: Latch I/O flag at MC=5, re-capture at MC=4
- **Result**: ✗ MC=4 is in next cycle with wrong address

### 2. FETCH at MC=5, READ at MC=4 Split
**Approach**: Instruction fetches at MC=5, data reads at MC=4
- **Result**: ✗ Firmware didn't boot (needs data reads at MC=5 too)

### 3. Peripheral-Specific Timing
**Approach**: MC=5 for everything except PS/2 at MC=4
- **Result**: ✗ Can't check io_cs at MC=4 (address already changed)

### 4. Double-Capture (MC=4 + MC=5)
**Approach**: Capture at both MC=4 and MC=5
- **Result**: ✓ Firmware boots, ✗ I/O still returns $00 (MC=5 overwrites MC=4)

### 5. Continuous Capture (Every Clock)
**Approach**: Update data_in every clock cycle
- **Result**: ✓ Firmware boots, ✗ I/O still returns $00

## Root Cause Analysis

The fundamental conflict is:
1. **Firmware needs MC=5 timing** for both instruction fetches AND data reads
2. **PS/2 peripheral needs MC=4 timing** for external controller data stability
3. **These requirements are mutually exclusive** with simple capture logic

The monitor's indirect indexed addressing `LDA (ADDR_LO),Y` for I/O reads goes through the same data path as firmware reads, so they need the same timing. But PS/2 external hardware needs different timing than internal RAM/ROM.

## Why Monitor I/O Reads Fail

Even though firmware I/O writes work (STA $C000), and firmware likely reads UART status during boot, the monitor's `E` command consistently returns $00 for I/O addresses. Possible reasons:

1. **Addressing mode difference**: Monitor uses indirect indexed, firmware uses absolute
2. **Timing within instruction**: Different steps of multi-cycle instructions sample data at different MC states
3. **Firmware workaround**: Firmware might retry reads or have timing-tolerant code
4. **Hardware issue**: UART/PS/2 peripherals might not drive data bus correctly at MC=5

## Peripheral-Specific Observations

### UART
- Status register returns $00 when read via monitor
- Should return bit 0 = TX ready (~tx_busy)
- Firmware writes work (proves UART TX functional)
- Data path verified (hardcoded test breaks boot, proving firmware reads it)

### PS/2
- No LED activity at MC=5 timing
- Strong LED activity at MC=4 timing (confirmed working)
- Suggests external PS/2 controller needs extra clock cycle

## Next Steps for Resolution

The problem requires one of:

1. **Modify M65C02 core** to support different capture timing for different operations
2. **Add hold registers** in peripherals to capture data at MC=4 and hold through MC=5
3. **Modify monitor firmware** to use absolute addressing instead of indirect
4. **Add wait states** for I/O peripherals to extend data valid window
5. **Use different CPU core** that doesn't have this timing constraint

## Files Modified During Investigation

- `/opt/wip/retrocpu/rtl/system/soc_top.v` lines 266-277 (data capture logic)

## Testing Environment

- Board: Colorlight i5 (ECP5 FPGA)
- Clock: 25 MHz
- Baud: 9600
- Monitor: Via `/dev/ttyACM0`
- Issue discovered: 2024-12-27

## Conclusion

This is a **fundamental hardware timing issue** in the M65C02 integration. The current MC=5 baseline works for basic operation but prevents monitor-based I/O debugging. A complete solution requires either core modification or peripheral redesign with timing adaptation.

**Current Status**: System functional with MC=5 timing, but monitor I/O register access not working. PS/2 confirmed working at MC=4 but incompatible with firmware requirements.
