# UART RX Implementation - Sticky Flag with Edge Detection

## Design Decision: Sticky Flag ✅

**Rationale**: Sticky flag is more robust and simpler for memory-mapped I/O with slow CPU polling.

## Architecture

### uart_rx.v (Low-Level UART Receiver)
**Behavior**: `rx_ready` is **STICKY**
- Goes HIGH when valid byte received (end of stop bit)
- Stays HIGH until next start bit arrives
- Simple, robust state machine
- Can't miss data with slow polling

### uart.v (Memory-Mapped Interface)
**Behavior**: Edge detection converts sticky to single-shot
```
rx_ready_sticky (from uart_rx) → Edge Detector → rx_ready_flag (to CPU)
```

**Edge Detection Logic**:
1. Track previous state: `rx_ready_prev <= rx_ready_sticky`
2. Detect rising edge: `if (rx_ready_sticky && !rx_ready_prev)`
3. Capture data once: `rx_data_reg <= rx_data_wire; rx_ready_flag <= 1`
4. Clear on read: `if (cs && !we && addr == DATA) rx_ready_flag <= 0`

**Key Benefit**: Sticky rx_ready can't be missed, but edge detection prevents re-reading stale data.

## Test Results

### Unit Tests (uart_rx.v)
✅ **test_uart_rx.py**: All 10 tests PASS
- Idle state detection
- Single byte reception
- Back-to-back bytes
- Start bit validation
- Stop bit framing check
- Baud rate tolerance
- Reset during reception

### Integration Tests (uart.v)
✅ **test_uart_status.py**: 2/2 tests PASS
- TX status polling
- Rapid writes

✅ **test_uart_rx_edge.py**: 2/2 tests PASS
- Edge detection (prevents stale reads)
- No spurious rx_ready after idle

## Hardware Testing

**Status**: Ready for hardware test
**Files Modified**:
- `rtl/peripherals/uart/uart_rx.v` - Sticky flag implementation
- `rtl/peripherals/uart/uart.v` - Edge detection logic
- `colorlight_i5.lpf` - Added PULLMODE=UP to uart_rx pin

**Expected Behavior**:
- Monitor should wait for input (no spurious $0D)
- Typing commands should work correctly
- No repeated/stale character reads

## Next Steps
1. Build and program FPGA
2. Test monitor prompt (should wait for input)
3. Test E/D commands with UART input
4. Verify PS/2 still works if enabled

