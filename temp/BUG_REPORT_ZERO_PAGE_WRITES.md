# Bug Report: Zero Page Write Failure

## Summary
All writes to zero page memory ($0000-$00FF) fail and read back as $00. Writes to addresses $0200 and above work correctly. This blocks both the monitor and BASIC interpreter from functioning.

## Evidence

### Test Results (firmware/monitor/monitor.s with ZEROPAGE_TEST)
```
RAM Test at $0200: PASS ✓
Zero Page Test at $0010: FAIL (reads $00) ✗
```

### Symptoms
1. Monitor commands fail - INPUT_BUF ($0010) contains $00 instead of typed characters
2. BASIC input fails - same issue with zero page variables
3. RAM test at $0200 passes consistently
4. Zero page test at $0010, $0020 consistently fails

### Example
```assembly
; This code fails:
LDA #$AA
STA $0010    ; Write to zero page
LDA $0010    ; Read back
; Result: A contains $00, not $AA

; This code works:
LDA #$AA
STA $0200    ; Write to $0200+
LDA $0200    ; Read back
; Result: A contains $AA correctly
```

## Investigation Findings

### Hardware Configuration
- **CPU**: Arlet 6502 core (rtl/cpu/arlet-6502/cpu.v)
- **RAM**: 32KB block RAM at $0000-$7FFF (rtl/memory/ram.v)
- **Clock**: 25MHz system, divided to 1MHz CPU clock via cpu_clk_enable pulse
- **RDY signal**: `cpu_rdy && cpu_clk_enable` (soc_top.v line ~180)

### Key Observations

1. **Address Decoding is Correct**
   - Zero page ($0000-$00FF) is correctly mapped to RAM
   - Address decoder: `ram_cs = (addr[15] == 1'b0)` includes zero page

2. **CPU Address Generation is Correct**
   - CPU core has `ZEROPAGE = 8'h00` constant
   - For ZP0 state: `AB = {ZEROPAGE, DIMUX}` = `{$00, data}`
   - Zero page addresses are generated correctly by CPU

3. **RDY Gating Creates Timing Issues**
   - CPU ABL/ABH registers only latch when `RDY=1` (cpu.v:414)
   - RDY is tied to `cpu_clk_enable`, which pulses briefly every 25 clocks
   - When RDY=0, CPU pauses but address bus may be unstable

4. **RAM Write Timing**
   - RAM write enable: `ram_cs && cpu_we`
   - RAM is synchronous, writes on every `posedge clk` when `we=1`
   - No gating by cpu_clk_enable (simplified after previous debugging)

## Root Cause Hypothesis

**Primary Suspect**: Address bus instability during zero page writes due to RDY gating.

When the CPU writes to zero page:
1. CPU enters ZP0 state, sets WE=1
2. CPU generates address {$00, operand}
3. RDY pulses high briefly (cpu_clk_enable), CPU latches ABL/ABH
4. RDY goes low (cpu_clk_enable low), CPU pauses
5. While paused, ABL/ABH are not being updated
6. BUT: if address generation depends on signals that change while RDY=0...

**Key Question**: Why does $0200 work but $0010 fail?

Possible explanations:
- Different CPU addressing modes used (absolute vs zero page)
- Zero page uses different state machine path in CPU
- Timing difference in how addresses propagate

## Code References

### CPU Core (rtl/cpu/arlet-6502/cpu.v)
- Line 21: Module declaration with RDY input
- Line 358: `ZEROPAGE = 8'h00` constant
- Line 399: `ZP0, INDY0: AB = {ZEROPAGE, DIMUX}`
- Line 414-418: ABL/ABH latching gated by RDY
- Line 460: `ZP0: WE = store`

### SOC Top (rtl/system/soc_top.v)
- RAM instantiation with `we(ram_cs && cpu_we)`
- RDY connection: `cpu_rdy && cpu_clk_enable`

### Monitor Firmware (firmware/monitor/monitor.s)
- Line 112-118: Zero page test at $0010
- Line 120-125: Stack test at $0150 (not yet tested due to early failure)

## Recommended Next Steps

1. **Verify address bus stability during zero page writes**
   - Add simulation/waveform capture
   - Check AB bus during ZP0 state when RDY pulses

2. **Test different addressing modes**
   - Compare absolute addressing to $0010 vs zero page addressing
   - See if `STA $0010` (absolute) works where `STA $10` (zero page) fails

3. **Check CPU state machine timing**
   - Verify ZP0 state duration relative to cpu_clk_enable pulse
   - Ensure write completes during RDY=1 pulse

4. **Consider alternative RDY approach**
   - Maybe RDY should stay high, use different mechanism for clock division
   - Or ensure ABL/ABH remain stable even when RDY=0

5. **Hardware verification**
   - Program FPGA with debug logic to capture AB bus during zero page writes
   - Use LEDs or additional debug output

## Workaround

None available. Zero page is fundamental to 6502 operation.

## Impact

**Critical** - System completely non-functional:
- Monitor cannot parse commands (uses zero page for INPUT_BUF)
- BASIC cannot run (heavily uses zero page)
- All 6502 code relies on zero page for performance

## Files Modified During Debug Session

- `firmware/monitor/monitor.s` - Added RAM and zero page tests
- `firmware/basic/demo_basic_trace.s` - Added debug output, PHA/PLA fixes (not relevant to this bug)
- `tests/unit/test_ram_zeropage.py` - Created but test setup incomplete
- Various rebuilds of `build/soc_top.bit`

## Status

**OPEN** - Bug confirmed, root cause investigation in progress.

Last tested: December 23, 2025, 16:03 UTC
Hardware: ColorLight i5 ECP5 FPGA board
