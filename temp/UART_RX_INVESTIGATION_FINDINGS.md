# UART RX Investigation - Critical Findings

## Summary
After extensive testing, we discovered **the problem is NOT in the UART RX module**. The issue is elsewhere in the data path or timing.

## Tests Performed & Results

### Test 1: UART RX Completely Disabled
**Method**: Disabled RX capture logic entirely (`if (1'b0)`)  
**Expected**: Monitor should wait forever (no rx_ready_flag ever set)  
**Result**: ❌ Still seeing "0D Unknown command" spam  
**Conclusion**: Problem is NOT in UART RX flag logic

### Test 2: STATUS Register Forced to 0x00
**Method**: Hardcoded `data_out = 8'h00` for STATUS register  
**Expected**: Firmware should wait forever (STATUS always 0)  
**Result**: ❌ Still seeing "0D Unknown command" spam  
**Conclusion**: Problem is NOT in UART STATUS register read

### Test 3: RX Data Register Initialized to 0xFF
**Method**: Changed `rx_data_reg <= 8'hFF` on reset  
**Expected**: Should see "FF Unknown command" if UART DATA read works  
**Result**: ❌ Still seeing "0D Unknown command" (not 0xFF!)  
**Conclusion**: CPU is NOT reading from rx_data_reg

## The Smoking Gun

**Even with:**
- RX capture disabled (rx_ready_flag stays 0)
- STATUS forced to 0x00 (bit 1 = RX ready always 0)
- DATA initialized to 0xFF (not 0x0D)

**We STILL see:** "0D Unknown command" repeatedly

## What This Proves

1. ✅ uart_rx.v unit tests pass - module itself works
2. ✅ Edge detection logic tested and works
3. ❌ **But the CPU is reading 0x0D from somewhere else**

## Possible Root Causes

### 1. MC=5 Data Capture Not Working
The data capture at MC=5 in soc_top.v may not be happening:
```verilog
always @(posedge clk_25mhz) begin
    if (system_rst) begin
        cpu_data_in_reg <= 8'hEA;  // NOP
    end else if (cpu_mc == 3'b101) begin  // MC=5
        cpu_data_in_reg <= cpu_data_in_mux;
    end
end
```
If MC=5 condition never true, `cpu_data_in_reg` holds stale data.

### 2. Data Bus Mux Priority Issue
Priority mux uses `case (1'b1)`:
```verilog
case (1'b1)
    ram_cs:         cpu_data_in_mux = ram_data_out;
    rom_basic_cs:   cpu_data_in_mux = rom_basic_data_out;
    rom_monitor_cs: cpu_data_in_mux = rom_monitor_data_out;
    uart_cs:        cpu_data_in_mux = uart_data_out;
    gpu_cs:         cpu_data_in_mux = gpu_data_out;
    default:        cpu_data_in_mux = 8'hFF;
endcase
```
If multiple chip selects active, wrong source selected.

### 3. Chip Select Overlap
- UART: 0xC000-0xC00F  
- GPU: 0xC010-0xC01F  
- LCD: 0xC100-0xC1FF  
- PS/2: 0xC200-0xC2FF  

Maybe `uart_cs` stays HIGH or overlaps with another device?

### 4. Another Device Returning 0x0D
Maybe LCD, PS/2, or GPU is returning 0x0D?

### 5. Firmware Reading Wrong Address
Maybe firmware isn't reading $C000/$C001 but some other address?

## Next Steps

1. **Add debug output** to see:
   - What address CPU is reading when it gets 0x0D
   - Which chip select is active
   - What cpu_mc value is during capture
   - What cpu_data_in_mux contains

2. **Check firmware** assembly to verify:
   - CHRIN actually reads $C001 (STATUS)
   - Then reads $C000 (DATA)
   - Not reading some other address

3. **Test data mux** by forcing different values:
   - Force uart_cs path to 0xAA
   - See if 0xAA appears or still 0x0D

4. **Check MC timing** - verify MC=5 condition is true during I/O reads

## Files Involved

- `rtl/system/soc_top.v` - Data bus mux and MC=5 capture
- `rtl/memory/address_decoder.v` - Chip select generation
- `rtl/peripherals/uart/uart.v` - UART module (proven NOT the issue)
- `firmware/monitor/monitor.s` - CHRIN function reading UART

## Current Status

- ✅ UART RX tests pass
- ✅ Integration tests pass
- ❌ Hardware shows spurious 0x0D reads
- ❌ Root cause is in SOC-level data path, NOT UART

