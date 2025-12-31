"""
Debug test - monitor CPU write attempts to display port
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


@cocotb.test()
async def test_monitor_cpu_writes(dut):
    """Monitor CPU and look for write attempts to $C000"""

    clock = Clock(dut.clk_25mhz, 40, unit="ns")
    cocotb.start_soon(clock.start())

    dut.reset_button_n.value = 1
    await ClockCycles(dut.clk_25mhz, 300)  # Wait for reset

    dut._log.info("=== Monitoring for CPU writes to $C000 ===")

    write_attempts = 0
    for i in range(100000):
        await RisingEdge(dut.clk_25mhz)

        # Check for write to display port
        addr_val = dut.cpu_addr.value
        we_val = dut.cpu_we.value  # WE: 1=write, 0=read
        clk_en = dut.cpu_clk_enable.value
        display_cs_val = dut.display_cs.value

        # Log any writes
        if clk_en == 1 and we_val == 1:  # CPU write cycle (WE=1)
            addr_str = str(addr_val)
            if 'x' not in addr_str.lower():
                addr_int = int(addr_val)
                data_out = int(dut.cpu_data_out.value) if 'x' not in str(dut.cpu_data_out.value).lower() else 0
                dut._log.info(f"Cycle {i}: CPU WRITE addr={addr_int:#06x} data={data_out:#04x} display_cs={display_cs_val}")
                write_attempts += 1

                # Check if it's to display port
                if display_cs_val == 1:
                    dut._log.info(f"  ✓ Write to DISPLAY PORT! data={data_out}")
                    dut._log.info(f"  display_value before: {dut.display_value.value}")
                    await RisingEdge(dut.clk_25mhz)
                    dut._log.info(f"  display_value after: {dut.display_value.value}")

                if write_attempts >= 5:
                    break

    if write_attempts == 0:
        dut._log.error("✗ NO WRITES DETECTED - CPU may not be executing write instructions")
        assert False
    else:
        dut._log.info(f"✓ Detected {write_attempts} write(s)")
