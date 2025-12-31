# Boot Failure Investigation - 2025-12-28

## Problem
Firmware fails to boot on FPGA - no serial output at all, across multiple commits and configurations.

## What I've Tried

### 1. Original Approach (MC=5 baseline with LCD/PS/2 added)
- **Result**: No boot
- **Issue Found**: LCD controller `rd` input was not connected in soc_top.v
- **Fix Applied**: Added lcd_rd signal generation
- **Outcome**: Still no boot

### 2. ROM Module Timing Investigation
- **Hypothesis**: ROM modules had combinational output while RAM had registered output
- **Action**: Changed both ROM modules to registered output (synchronous read)
- **Result**: Still no boot
- **Revert**: Changed back to combinational output
- **Outcome**: Still no boot

### 3. Reset Controller Investigation
- **Found**: reset_controller.v was modified to use inline initialization instead of initial blocks
- **Action**: Reverted to committed version with initial blocks
- **Result**: Still no boot

### 4. Repository State Issues
- **Found**: Committed soc_top.v references UART ports/parameters that don't exist:
  - `.HOLDOFF_CYCLES(2500)` - parameter doesn't exist in uart.v
  - `.rx_ready_debug(uart_rx_ready_debug)` - port doesn't exist in uart.v
- **Fix**: Removed these references, changed baud to 9600
- **Result**: Build succeeds, but still no boot

### 5. Branch Testing
- **Tested**: Branch `002-m65c02-port` (M65C02 core)
- **Result**: No boot
- **Tested**: Commit f4c5d8a "Complete Phase 3: Monitor MVP - First bootable system" (Arlet core)
- **Result**: No boot

## Current Status
**NO configuration boots**, including commits that should be working.

##Possible Root Causes

### 1. Firmware Hex Files
- Monitor ROM hex file exists (8192 bytes)
- Reset vector at $FFFC-$FFFD points to $E000 (correct)
- But: Firmware may have been built for wrong address map or with errors

### 2. ROM Initialization
- ROMs use `$readmemh()` in `initial` blocks
- Yosys should support this, but initialization may not be working
- Synthesis log shows no errors about missing hex files
- Only 17 DP16KD blocks used (expected ~28 for all memories)
  - This suggests ROMs may NOT be inferred as block RAM!
  - ROMs may be implemented as distributed logic/LUTs instead
  - If so, $readmemh initialization might not work correctly

### 3. Synthesis/Place-and-Route Issues
- Builds complete successfully with no critical errors
- Timing passes (31-46 MHz vs 25 MHz target)
- But: Some warnings about implicitly declared identifiers in M65C02 core

### 4. Environmental Issues
- Serial port works (opens successfully)
- FPGA programs successfully
- But: Absolutely no output on UART at any baud rate
- LEDs status unknown (not tested)

## Key Evidence

### Memory Block Usage Discrepancy
```
Info: DP16KD: 17/ 56 30%
```

Expected usage:
- RAM (32KB): ~16 blocks
- BASIC ROM (16KB): ~8 blocks
- Monitor ROM (8KB): ~4 blocks
- M65C02 microcode ROMs: ~2-4 blocks
- **Total expected: ~28-32 blocks**

**Actual: Only 17 blocks used!**

This strongly suggests **ROMs are NOT being synthesized as block RAM**, which would explain why initialization fails and CPU can't fetch instructions.

## Recommended Next Steps

1. **Fix ROM Inference**: Modify ROM modules to ensure they're properly inferred as block RAM:
   - Try registered output with explicit memory attributes
   - Or use explicit ECP5 DP16KD primitives

2. **Verify ROM Contents**: Add synthesis directives to check if $readmemh is actually working

3. **Create Minimal Test**: Build a tiny ROM with just a few instructions to verify fetch works

4. **Check Generated Bitstream**: Analyze the actual bitstream to see if ROM initialization data is present

5. **Hardware Debug**: If ROM init is working, check if CPU is actually running:
   - Connect logic analyzer to see if address bus is changing
   - Check LED outputs
   - Verify reset timing

## Files Modified
- `/opt/wip/retrocpu/rtl/system/soc_top.v` - Fixed UART port references
- `/opt/wip/retrocpu/rtl/memory/rom_monitor.v` - Reverted to combinational (tested both ways)
- `/opt/wip/retrocpu/rtl/memory/rom_basic.v` - Reverted to combinational (tested both ways)

## Test Results Summary
| Configuration | Branch/Commit | Boot Result |
|--------------|---------------|-------------|
| MC=5 baseline + LCD/PS/2 | 003-hdmi-character-display | ❌ No boot |
| MC=5 with UART fixes | 002-m65c02-port | ❌ No boot |
| Original Arlet core | f4c5d8a | ❌ No boot |
| Registered ROMs | (test) | ❌ No boot |
| Combinational ROMs | (current) | ❌ No boot |

**Conclusion**: The problem is NOT with the timing changes or peripheral additions. Something more fundamental is preventing ANY firmware from running.
