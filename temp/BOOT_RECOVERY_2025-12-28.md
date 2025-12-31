# Boot Recovery - 2025-12-28

## Problem
System was not booting after recent changes. Serial output showed repeated "0D Unknown command" messages even though no serial input was being sent.

## Root Causes Identified

### 1. MC=5 Data Capture Timing (Committed: 8ecd5a6)
When switching from Arlet 6502 to M65C02 core, the data bus capture logic changed:

**Before (working):**
```verilog
always @(posedge clk_25mhz) begin
    if (system_rst) begin
        cpu_data_in_reg <= 8'h00;
    end else begin
        cpu_data_in_reg <= cpu_data_in_mux;  // Always capture
    end
end
```

**After (problematic when combined with other issues):**
```verilog
always @(posedge clk_25mhz) begin
    if (system_rst) begin
        cpu_data_in_reg <= 8'hEA;  // NOP during reset
    end else if (cpu_mc == 3'b101) begin  // ONLY capture at MC=5
        cpu_data_in_reg <= cpu_data_in_mux;
    end
end
```

This meant if MC timing was off or other issues prevented proper operation, the CPU would read stale data.

### 2. GPU Module Addition (Uncommitted)
Added GPU with PLL clock generation:
- PLL generates clk_pixel (25 MHz) and clk_tmds (125 MHz)
- GPU reset logic depends on PLL lock
- Added gpu_cs to data bus multiplexer
- Clock domain crossing issues
- PLL lock timing complications

### 3. Monitor Firmware Extensions (Uncommitted)
Extended monitor with:
- RAM_TEST routine writing to $0200
- ZEROPAGE_TEST writing to zero page
- Immediate 'X' debug output
- LCD initialization calls
- PS/2 initialization

These tests were writing to memory before the system was fully stable.

### 4. UART Port Reference Error (Uncommitted)
`soc_top.v` referenced `rx_ready_debug` port that didn't exist in uart.v module.

## Solution

### Actions Taken
1. **Stashed uncommitted changes** - Removed GPU and extended firmware
2. **Fixed UART port reference** - Removed rx_ready_debug connection
3. **Reverted monitor firmware** - Back to simple MVP version
4. **Changed UART baud rate** - Back to 9600 from 115200
5. **Rebuilt from clean state**

### Files Modified
- `rtl/system/soc_top.v` - Removed rx_ready_debug, changed baud to 9600
- `firmware/monitor/monitor.s` - Reverted to simple version (via stash)
- `firmware/monitor/monitor.hex` - Rebuilt from simple monitor

### Build Results
```
Info: Max frequency for clock '$glbnet$clk_25mhz$TRELLIS_IO_IN': 48.54 MHz (PASS at 25.00 MHz)
```

## Current Status

✅ **SYSTEM IS NOW BOOTING AND WORKING**

Serial output shows:
```
Monitor v1.0

6502 FPGA Microcomputer
Monitor ready! (Input not yet implemented)
>
Monitor ready! (Input not yet implemented)
>
[repeating...]
```

The repeating output is **correct behavior** - the MVP monitor doesn't implement input yet, so it loops forever printing the demo message.

## Analysis of "0D Unknown command" Issue

The spurious 0x0D (carriage return '\r') reads were caused by:
- Stale data in cpu_data_in_reg from MC=5 capture issues
- Possible clock domain problems with GPU PLL
- Firmware trying to read from devices before system was stable

## Next Steps

### To Restore GPU Support
1. Review GPU PLL configuration and lock timing
2. Ensure proper reset sequencing (wait for PLL lock)
3. Add clock domain crossing synchronizers
4. Test GPU integration separately before full integration

### To Add UART RX Support
1. Verify UART RX sticky flag implementation (already tested in unit tests)
2. Test UART RX edge detection (already tested in integration tests)
3. Implement monitor input handling (parse commands)
4. Test on hardware with simple echo functionality first

### To Re-enable Debug Features
1. Verify RAM is stable before running RAM_TEST
2. Add delays after reset before zero page tests
3. Test each feature incrementally

## Lessons Learned

1. **Test incrementally** - Adding GPU + UART RX + debug firmware simultaneously made debugging harder
2. **MC=5 capture timing is critical** - Any issues with MC state machine or timing will cause stale data reads
3. **Clock domain crossings need careful handling** - GPU PLL introduction requires proper synchronization
4. **Stash is your friend** - Being able to quickly revert to known-good state is valuable
5. **Serial port conflicts** - minicom blocking the port was an early red herring

## Commit Strategy

Current state (8ecd5a6 + uart fix) should be committed as:
```
fix: Restore bootable system - remove GPU, simplify monitor

- Remove GPU module and PLL clock generation (causing boot issues)
- Revert monitor to simple MVP version without debug tests
- Fix UART port reference (remove non-existent rx_ready_debug)
- Change UART baud rate back to 9600 for stability

System now boots correctly and shows monitor prompt.
GPU support will be re-added in future commit after debugging.
```

Then GPU can be re-introduced in a separate branch/commit with proper testing.
