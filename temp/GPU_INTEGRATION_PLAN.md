# GPU Integration Plan - 2025-12-28

## Current Status
- ✅ UART RX working perfectly (echo + command parsing)
- ✅ System boots reliably
- ✅ GPU files exist in `rtl/peripherals/video/`
- ✅ Address decoder updated for GPU at 0xC010-0xC01F

## Integration Steps

### 1. soc_top.v Module Port Changes
Add to module ports:
```verilog
// HDMI/DVI Output (TMDS differential pairs)
// Note: Only positive signals declared - LVCMOS33D mode auto-generates negatives
output wire [3:0] gpdi_dp,  // TMDS data positive (3=clk, 2=red, 1=green, 0=blue)
```

### 2. PLL Integration
Add PLL for GPU clocks:
- `clk_pixel`: 25 MHz (640x480@60Hz VGA timing)
- `clk_tmds`: 125 MHz (5x pixel clock for DDR serialization)
- PLL lock detection
- GPU reset synchronization (wait for PLL lock)

### 3. Address Decoder Changes
Already done:
- Added `gpu_cs` output
- UART: 0xC000-0xC00F
- GPU: 0xC010-0xC01F

### 4. GPU Instance
Instantiate `gpu_top`:
- Connect CPU bus (addr[3:0], data_in, data_out, we, re)
- Connect clocks (clk_cpu, clk_pixel, clk_tmds)
- Connect reset (gpu_rst_n)
- Connect TMDS output (gpdi_dp)

### 5. Data Bus Multiplexer
Add GPU to data bus mux:
```verilog
case (1'b1)
    ram_cs:         cpu_data_in_mux = ram_data_out;
    rom_basic_cs:   cpu_data_in_mux = rom_basic_data_out;
    rom_monitor_cs: cpu_data_in_mux = rom_monitor_data_out;
    uart_cs:        cpu_data_in_mux = uart_data_out;
    gpu_cs:         cpu_data_in_mux = gpu_data_out;  // NEW
    default:        cpu_data_in_mux = 8'hFF;
endcase
```

### 6. LPF Pin Constraints
Update `colorlight_i5.lpf` for HDMI pins (GPDI connector)

## Risk Mitigation

1. **PLL Lock Issues**: Add proper reset holdoff
2. **Clock Domain Crossing**: Already handled in gpu_top
3. **Data Bus Conflicts**: GPU and UART in different 16-byte blocks
4. **Timing**: GPU runs on separate clocks from CPU

## Testing Plan

1. Build and verify no syntax errors
2. Check timing (should still pass at 25 MHz system clock)
3. Program FPGA and verify UART still works
4. Test GPU register writes from monitor
5. Check HDMI output on monitor

## Rollback Plan

If GPU causes issues:
- Stash GPU changes
- Revert to working UART RX commit (5084f80)
- Debug GPU separately

## Files to Modify

- [x] `rtl/memory/address_decoder.v` - Add gpu_cs
- [ ] `rtl/system/soc_top.v` - Add PLL, GPU instance, data mux
- [ ] `colorlight_i5.lpf` - Add HDMI pin constraints
- [ ] Test and commit

