# Fixes Applied During MC=5 Investigation
## Date: 2025-12-28

## Problems Found and Fixed

### 1. **ROM Initialization Failure** ✅ FIXED
**Problem**: ROMs were not being properly initialized as block RAM
- Only 17 DP16KD blocks used (expected ~29)
- ROMs were being synthesized as distributed logic
- $readmemh() initialization wasn't working

**Fix**: Added synthesis directives to ROM modules:
```verilog
(* ram_style = "block" *)
(* ram_init_file = HEX_FILE *)
reg [DATA_WIDTH-1:0] rom [0:(1<<ADDR_WIDTH)-1];

// Synchronous read - required for block RAM inference
always @(posedge clk) begin
    data_out <= rom[addr];
end
```

**Result**: Now using 29 DP16KD blocks ✅
**Files Modified**:
- `rtl/memory/rom_monitor.v`
- `rtl/memory/rom_basic.v`

### 2. **Monitor Firmware Infinite Loop** ✅ FIXED
**Problem**: CHRIN function had infinite loop polling PS/2 and UART
```assembly
@TRY_PS2:
    JSR PS2_READ_KEY
    BCS @GOT_CHAR
@TRY_UART:
    LDA UART_STATUS
    AND #$02
    BEQ @TRY_PS2             ; ← INFINITE LOOP!
```

**Impact**: Firmware booted and printed banner, then hung forever waiting for input

**Fix**: Simplified CHRIN to wait only for UART (PS/2 disabled for testing):
```assembly
CHRIN:
    ; Simple blocking wait for UART input
@WAIT_UART:
    LDA UART_STATUS
    AND #$02
    BEQ @WAIT_UART
    LDA UART_DATA
    RTS
```

**Result**: Monitor no longer hangs ✅
**Files Modified**: `firmware/monitor/monitor.s`

### 3. **UART Address Registration Timing Issue** ✅ FIXED
**Problem**: UART module registered the address before using it:
```verilog
always @(posedge clk) begin
    addr_reg <= addr;   // 1 cycle delay
end

always @(*) begin
    case (addr_reg)  // Uses OLD address!
```

**Impact at MC=5**:
- Address $C001 arrives at cycle 2 (MC=7)
- But `addr_reg` still contains previous cycle's address
- `data_out` returns data for **wrong register**
- Monitor reads garbage values from I/O registers

**Fix**: Removed address registration, made data_out combinational:
```verilog
always @(*) begin
    case (addr)  // Use current address directly
        ADDR_STATUS: begin
            data_out[0] = ~tx_busy;
            data_out[1] = 1'b0;
```

**Result**: UART registers now return correct data same cycle as address ✅
**Files Modified**: `rtl/peripherals/uart/uart.v`

## Remaining Issues

### 4. **UART RX Not Implemented** ❌ NOT FIXED YET
**Problem**:
- `uart_rx.v` exists but isn't instantiated in `uart.v`
- UART_STATUS bit 1 (RX ready) is hardwired to 0
- No way to receive serial data
- Monitor firmware expects to read from UART but can't

**Symptoms**:
- Monitor prints "0D Unknown command" repeatedly
- CHRIN returns immediately with $0D (shouldn't happen if bit 1 is 0)
- Suggests UART_STATUS may still be reading incorrectly at MC=5

**Next Steps**:
1. Add uart_rx instance to uart.v
2. Connect RX status and data registers properly
3. Test if monitor can read commands over UART

### 5. **PS/2 State Machine at MC=5** ❌ NOT TESTED YET
**Original Issue**: User reported PS/2 LEDs (3rd/4th) don't change at MC=5 but do at MC=4

**Status**: Not yet investigated - PS/2 disabled in CHRIN for testing

**Next Steps**:
1. After UART RX works, re-enable PS/2 in CHRIN
2. Test if PS/2 controller works at MC=5
3. If not, investigate PS/2 register read timing

## Key Discoveries

1. **MC=5 is the correct capture point** for M65C02
   - Address is stable from MC=6 through MC=5
   - Data from memory/peripherals is valid at MC=5
   - Address changes at MC=4 (too early to capture)

2. **Peripherals must have combinational outputs** for MC=5
   - Any address registration adds 1-cycle delay
   - At MC=5, we need data for the *current* address
   - The CPU's data capture register (at MC=5) breaks combinational loops

3. **Block RAM timing is correct**
   - Synchronous block RAM naturally holds data correctly
   - 1-cycle latency matches M65C02 timing expectations

4. **Firmware bugs can mask timing issues**
   - The CHRIN infinite loop hid all I/O timing problems
   - Always test basic firmware functionality first!

## Files Changed Summary

| File | Status | Purpose |
|------|--------|---------|
| `rtl/memory/rom_monitor.v` | Modified | Added block RAM directives, synchronous read |
| `rtl/memory/rom_basic.v` | Modified | Added block RAM directives, synchronous read |
| `firmware/monitor/monitor.s` | Modified | Fixed CHRIN infinite loop |
| `rtl/peripherals/uart/uart.v` | Modified | Removed address registration, made combinational |

## Build Statistics

- **Block RAM usage**: 29/56 DP16KD (51%) ✅
- **Logic utilization**: ~6% LUT4s
- **Timing**: 48.31 MHz (PASS at 25 MHz target)

## Next Session Goals

1. Implement UART RX module connection
2. Test complete UART RX/TX at MC=5
3. Re-enable PS/2 and test state machine
4. Verify monitor E/D commands work for all I/O registers
