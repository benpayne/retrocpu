# UART RX Investigation Summary - 2025-12-28

## Problem Identified
Monitor continuously reads spurious $0D (CR) characters even when no serial data is being sent.
User confirmed: **NO activity on TX/RX lines** - this is a code issue, not actual serial input.

## Root Causes Found

### 1. ✅ FIXED: UART Status Register Read Logic
**Problem**: Partial bit assignments in combinational logic caused synthesis issues
```verilog
// BROKEN:
data_out[0] = ~tx_busy;
data_out[1] = rx_ready_flag;
data_out[7:2] = 6'b000000;
```

**Fix**: Use full 8-bit assignment
```verilog
data_out = {6'b000000, rx_ready_flag, ~tx_busy};
```

### 2. ❌ IN PROGRESS: uart_rx rx_ready Pulse
**Problem**: Original uart_rx.v has rx_ready as sticky flag (stays HIGH until next reception), not a one-cycle pulse as documented.

**Impact**:
- After boot, any momentary glitch could set rx_ready HIGH
- rx_ready stays HIGH forever (no new data to clear it)
- Monitor continuously sees "data ready" and reads stale/garbage data

**Attempted Fixes** (all broke tests):
- Adding STATE_WAIT_IDLE for line stabilization
- Clearing rx_ready by default at top of always block  
- Explicitly clearing rx_ready in each state

**Issue**: Tests expect rx_ready to be sticky, but uart.v expects it to be a pulse.

## Files Modified
- `rtl/peripherals/uart/uart.v` - Fixed STATUS register read, added RX integration
- `rtl/peripherals/uart/uart_rx.v` - Attempted pulse fixes (currently broken)
- `colorlight_i5.lpf` - Added PULLMODE=UP to uart_rx pin

## Next Steps
1. Revert uart_rx.v to version that passes tests (sticky rx_ready)
2. Modify uart.v to handle sticky rx_ready properly
3. Clear rx_ready_flag when reading STATUS register (not DATA register)
4. Test hardware with proper handling

## Hardware Test Results
- UART TX: ✅ Works
- UART RX Module (tests): ❓ Broken by pulse changes
- Full System RX: ❌ Spurious $0D reads
- Build: ✅ Passes timing at 46 MHz
- Block RAM: ✅ 29/56 DP16KD blocks

