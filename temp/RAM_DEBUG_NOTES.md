# RAM Debug Investigation - Address $0000-$00FF Failure

## Current Status
**CONFIRMED**: All addresses $0000-$00FF fail (read back as $00)
**CONFIRMED**: All addresses $0100+ work correctly

## Test Results Summary
```
Address Test Results:
$0000: wrote $11, read $00  FAIL
$0010: wrote $22, read $00  FAIL
$0080: wrote $33, read $00  FAIL
$00FF: wrote $44, read $00  FAIL
$0100: wrote $55, read $55  PASS ✓
$0150: wrote $66, read $66  PASS ✓
$0200: wrote $77, read $77  PASS ✓
```

## Key Findings

1. **Exact boundary at $0100**
   - Failure affects ALL of page zero ($00xx)
   - Success for ALL addresses $0100 and above
   - Boundary corresponds to address bit 8

2. **Not an addressing mode issue**
   - Both absolute and zero page addressing modes fail equally
   - CPU addressing mode logic is NOT the problem

3. **Not a timing/RDY issue**
   - Higher addresses work fine with same timing
   - Stack operations ($0100+) work throughout monitor execution

4. **Address decoder correct**
   - `ram_cs = (addr[15] == 0)` correctly includes $0000-$7FFF
   - No chip select conflicts found

## Hypothesis: Address Bit 8 Anomaly

The failure boundary at $0100 (bit 8 transition) suggests:

### Possible Causes to Investigate:

1. **CPU Address Bus Stability**
   - Maybe ABL/ABH latching fails for addr[8]=0?
   - RDY gating might affect low byte differently?

2. **RAM Address Connection**
   - RAM gets `cpu_addr[14:0]`
   - Need to verify bit 8 is actually connected

3. **Synthesis Issue**
   - Perhaps optimizer/synthesizer doing something wrong with low bits?
   - Block RAM inference might have address bit issue?

4. **Hardware Defect**
   - FPGA routing issue with address bit 8?
   - RAM block configuration problem?

## Next Investigation Steps

### Step 1: Verify Hardware Signals
Added LED debug to capture:
- Write seen to $0010
- Data written value
- Data read back value
- Match status

Need to observe LEDs on actual hardware.

### Step 2: Check Synthesis Output
```bash
grep -i "DP16KD\|BRAM\|address" build/synth/yosys.log
```
Look for any warnings about RAM addressing.

### Step 3: Direct RAM Test
Create minimal testbench that:
- Writes to addresses $00, $FF, $100, $101
- Reads back immediately
- Verifies all work correctly in simulation

### Step 4: Check CPU Address Output
Add debug to capture cpu_addr during:
- Write cycle to $0010
- Read cycle from $0010
- Verify they're the same address

### Step 5: Scope the FPGA
If possible, use logic analyzer to capture:
- cpu_addr[14:0] during write to $0010
- cpu_we signal
- ram_cs signal
- cpu_data_out value

## Code Locations

- RAM module: `rtl/memory/ram.v` (lines 38-43)
- RAM instantiation: `rtl/system/soc_top.v` (line 103)
- Address decoder: `rtl/memory/address_decoder.v` (line 46)
- CPU address generation: `rtl/cpu/arlet-6502/cpu.v` (lines 369-405)
- Test firmware: `firmware/monitor/monitor.s` (ZEROPAGE_TEST function)

## Temporary Workarounds

None available - zero page is fundamental to 6502 operation.

## Impact

CRITICAL - Blocks:
- All monitor commands (use zero page for variables)
- All BASIC operation (heavy zero page usage)
- Most 6502 programs (zero page is fastest memory)

System completely non-functional until resolved.
