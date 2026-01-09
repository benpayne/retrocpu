"""
Test suite for gpu_graphics_registers.v module
Tests the GPU Graphics Register Interface for bitmap graphics mode

Register Map (offsets 0x0-0xF):
- 0x0: VRAM_ADDR_LO (RW) - VRAM address pointer low byte
- 0x1: VRAM_ADDR_HI (RW) - VRAM address pointer high byte (15-bit address)
- 0x2: VRAM_DATA (RW) - VRAM data read/write with auto-increment in burst mode
- 0x3: VRAM_CTRL (RW) - bit[0]=BURST_EN (auto-increment on VRAM_DATA access)
- 0x4: FB_BASE_ADDR_LO (RW) - Framebuffer base address low byte
- 0x5: FB_BASE_ADDR_HI (RW) - Framebuffer base address high byte
- 0x6: GPU_MODE (RW) - Graphics mode: 00=1BPP, 01=2BPP, 10=4BPP
- 0x7: CLUT_INDEX (RW) - Color lookup table index (0-255)
- 0x8: CLUT_DATA_R (RW) - CLUT red component (0-255)
- 0x9: CLUT_DATA_G (RW) - CLUT green component (0-255)
- 0xA: CLUT_DATA_B (RW) - CLUT blue component (0-255)
- 0xB: GPU_STATUS (RO) - bit[0]=VBLANK flag
- 0xC: GPU_IRQ_CTRL (RW) - bit[0]=VBLANK_IRQ_EN (VBlank interrupt enable)
- 0xD: DISPLAY_MODE (RW) - 0=character mode, 1=graphics mode
- 0xE-0xF: Reserved

Per TDD: This test is written BEFORE the RTL implementation
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# Register addresses (offsets)
REG_VRAM_ADDR_LO = 0x0
REG_VRAM_ADDR_HI = 0x1
REG_VRAM_DATA = 0x2
REG_VRAM_CTRL = 0x3
REG_FB_BASE_ADDR_LO = 0x4
REG_FB_BASE_ADDR_HI = 0x5
REG_GPU_MODE = 0x6
REG_CLUT_INDEX = 0x7
REG_CLUT_DATA_R = 0x8
REG_CLUT_DATA_G = 0x9
REG_CLUT_DATA_B = 0xA
REG_GPU_STATUS = 0xB
REG_GPU_IRQ_CTRL = 0xC
REG_DISPLAY_MODE = 0xD

# VRAM control register bits
VRAM_CTRL_BURST_EN = 0x01

# GPU mode values
GPU_MODE_1BPP = 0x00
GPU_MODE_2BPP = 0x01
GPU_MODE_4BPP = 0x02

# Display mode values
DISPLAY_MODE_CHAR = 0x00
DISPLAY_MODE_GRAPHICS = 0x01

# VRAM address space
VRAM_MAX_ADDR = 0x7FFF  # 15-bit address (32KB)


async def reset_dut(dut):
    """Reset the DUT and wait for it to stabilize"""
    dut.rst_n.value = 0
    dut.reg_we.value = 0
    dut.reg_re.value = 0
    dut.reg_addr.value = 0
    dut.reg_data_in.value = 0
    dut.vblank.value = 0

    await RisingEdge(dut.clk_cpu)
    await RisingEdge(dut.clk_cpu)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk_cpu)


async def write_register(dut, addr, data):
    """Write to a register"""
    dut.reg_addr.value = addr
    dut.reg_data_in.value = data
    dut.reg_we.value = 1
    dut.reg_re.value = 0
    await RisingEdge(dut.clk_cpu)
    dut.reg_we.value = 0
    await RisingEdge(dut.clk_cpu)


async def read_register(dut, addr):
    """Read from a register"""
    dut.reg_addr.value = addr
    dut.reg_we.value = 0
    dut.reg_re.value = 1
    await RisingEdge(dut.clk_cpu)
    value = int(dut.reg_data_out.value)
    dut.reg_re.value = 0
    await RisingEdge(dut.clk_cpu)
    return value


@cocotb.test()
async def test_reset_values(dut):
    """Test that all registers have correct reset values"""

    clock = Clock(dut.clk_cpu, 40, units="ns")  # 25 MHz
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    # Check reset values
    assert dut.vram_addr.value == 0, "VRAM address should reset to 0"
    assert dut.vram_ctrl.value == 0, "VRAM control should reset to 0 (burst OFF)"
    assert dut.fb_base_addr.value == 0, "Framebuffer base address should reset to 0"
    assert dut.gpu_mode.value == 0, "GPU mode should reset to 0 (1BPP)"
    assert dut.clut_index.value == 0, "CLUT index should reset to 0"
    assert dut.gpu_irq_ctrl.value == 0, "GPU IRQ control should reset to 0"
    assert dut.display_mode.value == 0, "Display mode should reset to 0 (character mode)"


@cocotb.test()
async def test_vram_addr_write_read(dut):
    """Test VRAM_ADDR_LO and VRAM_ADDR_HI register read/write"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write low byte
    await write_register(dut, REG_VRAM_ADDR_LO, 0x34)
    assert dut.vram_addr.value == 0x0034, "VRAM address should be 0x0034"

    # Read back low byte
    lo = await read_register(dut, REG_VRAM_ADDR_LO)
    assert lo == 0x34, "VRAM_ADDR_LO should read back 0x34"

    # Write high byte
    await write_register(dut, REG_VRAM_ADDR_HI, 0x12)
    assert dut.vram_addr.value == 0x1234, "VRAM address should be 0x1234"

    # Read back high byte
    hi = await read_register(dut, REG_VRAM_ADDR_HI)
    assert hi == 0x12, "VRAM_ADDR_HI should read back 0x12"


@cocotb.test()
async def test_vram_addr_15bit_mask(dut):
    """Test that VRAM address is masked to 15 bits"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write high byte with upper bit set (should be masked)
    await write_register(dut, REG_VRAM_ADDR_HI, 0xFF)
    await write_register(dut, REG_VRAM_ADDR_LO, 0xFF)

    # Should be masked to 15 bits (0x7FFF)
    assert dut.vram_addr.value == 0x7FFF, "VRAM address should be masked to 0x7FFF"

    # Read back high byte (should have bit 7 masked)
    hi = await read_register(dut, REG_VRAM_ADDR_HI)
    assert hi == 0x7F, "VRAM_ADDR_HI should read back 0x7F (15-bit mask)"


@cocotb.test()
async def test_vram_addr_various_values(dut):
    """Test writing various VRAM address values"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    test_addrs = [0x0000, 0x0001, 0x00FF, 0x0100, 0x1000, 0x5555, 0x7FFF]

    for addr in test_addrs:
        lo = addr & 0xFF
        hi = (addr >> 8) & 0x7F

        await write_register(dut, REG_VRAM_ADDR_LO, lo)
        await write_register(dut, REG_VRAM_ADDR_HI, hi)

        actual = int(dut.vram_addr.value)
        assert actual == addr, f"VRAM address should be 0x{addr:04X}, got 0x{actual:04X}"


@cocotb.test()
async def test_vram_data_write_no_burst(dut):
    """Test VRAM_DATA write with burst mode OFF (no auto-increment)"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Set VRAM address
    await write_register(dut, REG_VRAM_ADDR_LO, 0x00)
    await write_register(dut, REG_VRAM_ADDR_HI, 0x10)  # Address 0x1000

    # Ensure burst mode is OFF
    await write_register(dut, REG_VRAM_CTRL, 0x00)
    assert dut.vram_ctrl.value == 0, "Burst mode should be OFF"

    # Write data
    await write_register(dut, REG_VRAM_DATA, 0xAA)

    # Address should NOT auto-increment
    assert dut.vram_addr.value == 0x1000, "VRAM address should NOT increment without burst mode"

    # Write another byte
    await write_register(dut, REG_VRAM_DATA, 0x55)

    # Address should still be the same
    assert dut.vram_addr.value == 0x1000, "VRAM address should remain at 0x1000"


@cocotb.test()
async def test_vram_data_write_burst_mode(dut):
    """Test VRAM_DATA write with burst mode ON (auto-increment)"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Set VRAM address
    await write_register(dut, REG_VRAM_ADDR_LO, 0x00)
    await write_register(dut, REG_VRAM_ADDR_HI, 0x20)  # Address 0x2000

    # Enable burst mode
    await write_register(dut, REG_VRAM_CTRL, VRAM_CTRL_BURST_EN)
    assert dut.vram_ctrl.value == 1, "Burst mode should be ON"

    # Write first byte
    await write_register(dut, REG_VRAM_DATA, 0x11)
    assert dut.vram_addr.value == 0x2001, "VRAM address should increment to 0x2001"

    # Write second byte
    await write_register(dut, REG_VRAM_DATA, 0x22)
    assert dut.vram_addr.value == 0x2002, "VRAM address should increment to 0x2002"

    # Write third byte
    await write_register(dut, REG_VRAM_DATA, 0x33)
    assert dut.vram_addr.value == 0x2003, "VRAM address should increment to 0x2003"


@cocotb.test()
async def test_vram_burst_sequential_writes(dut):
    """Test sequential VRAM writes in burst mode"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Set starting address
    await write_register(dut, REG_VRAM_ADDR_LO, 0x00)
    await write_register(dut, REG_VRAM_ADDR_HI, 0x00)  # Address 0x0000

    # Enable burst mode
    await write_register(dut, REG_VRAM_CTRL, VRAM_CTRL_BURST_EN)

    # Write 10 bytes sequentially
    for i in range(10):
        await write_register(dut, REG_VRAM_DATA, i * 0x11)
        expected_addr = i + 1
        actual_addr = int(dut.vram_addr.value)
        assert actual_addr == expected_addr, \
            f"After write {i}, address should be 0x{expected_addr:04X}, got 0x{actual_addr:04X}"


@cocotb.test()
async def test_vram_addr_wrapping(dut):
    """Test VRAM address wrapping at 0x7FFF -> 0x0000 in burst mode"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Set address to 0x7FFE (one before max)
    await write_register(dut, REG_VRAM_ADDR_LO, 0xFE)
    await write_register(dut, REG_VRAM_ADDR_HI, 0x7F)
    assert dut.vram_addr.value == 0x7FFE, "VRAM address should be 0x7FFE"

    # Enable burst mode
    await write_register(dut, REG_VRAM_CTRL, VRAM_CTRL_BURST_EN)

    # Write first byte (address should increment to 0x7FFF)
    await write_register(dut, REG_VRAM_DATA, 0xAA)
    assert dut.vram_addr.value == 0x7FFF, "VRAM address should increment to 0x7FFF"

    # Write second byte (address should wrap to 0x0000)
    await write_register(dut, REG_VRAM_DATA, 0xBB)
    assert dut.vram_addr.value == 0x0000, "VRAM address should wrap to 0x0000"

    # Write third byte (should continue from 0x0000)
    await write_register(dut, REG_VRAM_DATA, 0xCC)
    assert dut.vram_addr.value == 0x0001, "VRAM address should be 0x0001"


@cocotb.test()
async def test_vram_ctrl_toggle(dut):
    """Test toggling burst mode on and off"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Set address
    await write_register(dut, REG_VRAM_ADDR_LO, 0x00)
    await write_register(dut, REG_VRAM_ADDR_HI, 0x10)

    # Test burst OFF
    await write_register(dut, REG_VRAM_CTRL, 0x00)
    await write_register(dut, REG_VRAM_DATA, 0x01)
    assert dut.vram_addr.value == 0x1000, "Address should not increment (burst OFF)"

    # Enable burst
    await write_register(dut, REG_VRAM_CTRL, VRAM_CTRL_BURST_EN)
    await write_register(dut, REG_VRAM_DATA, 0x02)
    assert dut.vram_addr.value == 0x1001, "Address should increment (burst ON)"

    # Disable burst again
    await write_register(dut, REG_VRAM_CTRL, 0x00)
    await write_register(dut, REG_VRAM_DATA, 0x03)
    assert dut.vram_addr.value == 0x1001, "Address should not increment (burst OFF again)"


@cocotb.test()
async def test_fb_base_addr_write_read(dut):
    """Test FB_BASE_ADDR_LO and FB_BASE_ADDR_HI register read/write"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write low byte
    await write_register(dut, REG_FB_BASE_ADDR_LO, 0x00)
    assert dut.fb_base_addr.value == 0x0000, "FB base address should be 0x0000"

    # Write high byte
    await write_register(dut, REG_FB_BASE_ADDR_HI, 0x40)
    assert dut.fb_base_addr.value == 0x4000, "FB base address should be 0x4000"

    # Read back
    lo = await read_register(dut, REG_FB_BASE_ADDR_LO)
    hi = await read_register(dut, REG_FB_BASE_ADDR_HI)
    assert lo == 0x00, "FB_BASE_ADDR_LO should read 0x00"
    assert hi == 0x40, "FB_BASE_ADDR_HI should read 0x40"


@cocotb.test()
async def test_fb_base_addr_various_values(dut):
    """Test various framebuffer base address values"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    test_addrs = [0x0000, 0x1000, 0x2000, 0x4000, 0x7FFF]

    for addr in test_addrs:
        lo = addr & 0xFF
        hi = (addr >> 8) & 0x7F

        await write_register(dut, REG_FB_BASE_ADDR_LO, lo)
        await write_register(dut, REG_FB_BASE_ADDR_HI, hi)

        actual = int(dut.fb_base_addr.value)
        assert actual == addr, f"FB base address should be 0x{addr:04X}, got 0x{actual:04X}"


@cocotb.test()
async def test_gpu_mode_write_read(dut):
    """Test GPU_MODE register read/write (00=1BPP, 01=2BPP, 10=4BPP)"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Test 1BPP mode
    await write_register(dut, REG_GPU_MODE, GPU_MODE_1BPP)
    assert dut.gpu_mode.value == 0, "GPU mode should be 0 (1BPP)"
    mode = await read_register(dut, REG_GPU_MODE)
    assert mode == GPU_MODE_1BPP, "Read should return 1BPP mode"

    # Test 2BPP mode
    await write_register(dut, REG_GPU_MODE, GPU_MODE_2BPP)
    assert dut.gpu_mode.value == 1, "GPU mode should be 1 (2BPP)"
    mode = await read_register(dut, REG_GPU_MODE)
    assert mode == GPU_MODE_2BPP, "Read should return 2BPP mode"

    # Test 4BPP mode
    await write_register(dut, REG_GPU_MODE, GPU_MODE_4BPP)
    assert dut.gpu_mode.value == 2, "GPU mode should be 2 (4BPP)"
    mode = await read_register(dut, REG_GPU_MODE)
    assert mode == GPU_MODE_4BPP, "Read should return 4BPP mode"


@cocotb.test()
async def test_gpu_mode_masking(dut):
    """Test that GPU_MODE masks upper bits (only 2-bit value)"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write value with upper bits set
    await write_register(dut, REG_GPU_MODE, 0xFF)
    # Should be masked to 2 bits (0x03 = 11b, which is reserved but valid)
    assert dut.gpu_mode.value <= 0x03, "GPU mode should be masked to 2 bits"

    # Write 0xFC (upper bits set)
    await write_register(dut, REG_GPU_MODE, 0xFC)
    assert dut.gpu_mode.value == 0, "Should mask to lower 2 bits (0x00)"


@cocotb.test()
async def test_clut_index_write_read(dut):
    """Test CLUT_INDEX register read/write"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Test various index values
    test_indices = [0x00, 0x01, 0x0F, 0x80, 0xFF]

    for idx in test_indices:
        await write_register(dut, REG_CLUT_INDEX, idx)
        assert dut.clut_index.value == idx, f"CLUT index should be 0x{idx:02X}"

        read_idx = await read_register(dut, REG_CLUT_INDEX)
        assert read_idx == idx, f"Read CLUT index should be 0x{idx:02X}"


@cocotb.test()
async def test_clut_data_rgb_write_read(dut):
    """Test CLUT_DATA_R/G/B register read/write"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Set CLUT index
    await write_register(dut, REG_CLUT_INDEX, 0x10)

    # Write RGB values
    await write_register(dut, REG_CLUT_DATA_R, 0xFF)
    await write_register(dut, REG_CLUT_DATA_G, 0x80)
    await write_register(dut, REG_CLUT_DATA_B, 0x40)

    # Read back
    r = await read_register(dut, REG_CLUT_DATA_R)
    g = await read_register(dut, REG_CLUT_DATA_G)
    b = await read_register(dut, REG_CLUT_DATA_B)

    assert r == 0xFF, "CLUT red should be 0xFF"
    assert g == 0x80, "CLUT green should be 0x80"
    assert b == 0x40, "CLUT blue should be 0x40"


@cocotb.test()
async def test_clut_multiple_entries(dut):
    """Test writing and reading multiple CLUT entries"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Define color palette
    colors = [
        (0x00, 0x00, 0x00, 0x00),  # Index 0: Black
        (0x01, 0xFF, 0x00, 0x00),  # Index 1: Red
        (0x02, 0x00, 0xFF, 0x00),  # Index 2: Green
        (0x03, 0x00, 0x00, 0xFF),  # Index 3: Blue
        (0x0F, 0xFF, 0xFF, 0xFF),  # Index 15: White
    ]

    # Write colors
    for idx, r, g, b in colors:
        await write_register(dut, REG_CLUT_INDEX, idx)
        await write_register(dut, REG_CLUT_DATA_R, r)
        await write_register(dut, REG_CLUT_DATA_G, g)
        await write_register(dut, REG_CLUT_DATA_B, b)

    # Read back and verify
    for idx, expected_r, expected_g, expected_b in colors:
        await write_register(dut, REG_CLUT_INDEX, idx)
        r = await read_register(dut, REG_CLUT_DATA_R)
        g = await read_register(dut, REG_CLUT_DATA_G)
        b = await read_register(dut, REG_CLUT_DATA_B)

        assert r == expected_r, f"Index {idx}: Red should be 0x{expected_r:02X}"
        assert g == expected_g, f"Index {idx}: Green should be 0x{expected_g:02X}"
        assert b == expected_b, f"Index {idx}: Blue should be 0x{expected_b:02X}"


@cocotb.test()
async def test_gpu_status_read_only(dut):
    """Test that GPU_STATUS register is read-only"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Set VBlank input
    dut.vblank.value = 0
    await RisingEdge(dut.clk_cpu)

    # Read status
    status = await read_register(dut, REG_GPU_STATUS)
    assert (status & 0x01) == 0, "VBlank bit should be clear"

    # Try to write (should have no effect)
    await write_register(dut, REG_GPU_STATUS, 0xFF)

    # Read again, should still reflect input
    status = await read_register(dut, REG_GPU_STATUS)
    assert (status & 0x01) == 0, "VBlank bit should still be clear (write ignored)"

    # Change input
    dut.vblank.value = 1
    await RisingEdge(dut.clk_cpu)

    # Read status
    status = await read_register(dut, REG_GPU_STATUS)
    assert (status & 0x01) == 1, "VBlank bit should now be set"


@cocotb.test()
async def test_gpu_status_vblank_flag(dut):
    """Test GPU_STATUS register VBlank flag (bit 0)"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Test VBlank low
    dut.vblank.value = 0
    await RisingEdge(dut.clk_cpu)
    status = await read_register(dut, REG_GPU_STATUS)
    assert (status & 0x01) == 0, "VBlank bit should be clear when vblank input is low"

    # Test VBlank high
    dut.vblank.value = 1
    await RisingEdge(dut.clk_cpu)
    status = await read_register(dut, REG_GPU_STATUS)
    assert (status & 0x01) == 1, "VBlank bit should be set when vblank input is high"

    # Test VBlank toggle
    dut.vblank.value = 0
    await RisingEdge(dut.clk_cpu)
    status = await read_register(dut, REG_GPU_STATUS)
    assert (status & 0x01) == 0, "VBlank bit should clear when vblank goes low"


@cocotb.test()
async def test_gpu_irq_ctrl_write_read(dut):
    """Test GPU_IRQ_CTRL register read/write (VBlank interrupt enable)"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Default should be disabled (0)
    assert dut.gpu_irq_ctrl.value == 0, "IRQ control should reset to 0"

    # Enable VBlank interrupt
    await write_register(dut, REG_GPU_IRQ_CTRL, 0x01)
    assert dut.gpu_irq_ctrl.value == 1, "VBlank IRQ should be enabled"

    # Read back
    irq_ctrl = await read_register(dut, REG_GPU_IRQ_CTRL)
    assert (irq_ctrl & 0x01) == 1, "VBlank IRQ enable bit should be set"

    # Disable VBlank interrupt
    await write_register(dut, REG_GPU_IRQ_CTRL, 0x00)
    assert dut.gpu_irq_ctrl.value == 0, "VBlank IRQ should be disabled"

    # Read back
    irq_ctrl = await read_register(dut, REG_GPU_IRQ_CTRL)
    assert (irq_ctrl & 0x01) == 0, "VBlank IRQ enable bit should be clear"


@cocotb.test()
async def test_display_mode_write_read(dut):
    """Test DISPLAY_MODE register read/write (0=char, 1=graphics)"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Default should be character mode (0)
    assert dut.display_mode.value == 0, "Display mode should reset to 0 (character)"

    # Switch to graphics mode
    await write_register(dut, REG_DISPLAY_MODE, DISPLAY_MODE_GRAPHICS)
    assert dut.display_mode.value == 1, "Display mode should be 1 (graphics)"

    # Read back
    mode = await read_register(dut, REG_DISPLAY_MODE)
    assert mode == DISPLAY_MODE_GRAPHICS, "Display mode should read as graphics"

    # Switch back to character mode
    await write_register(dut, REG_DISPLAY_MODE, DISPLAY_MODE_CHAR)
    assert dut.display_mode.value == 0, "Display mode should be 0 (character)"

    # Read back
    mode = await read_register(dut, REG_DISPLAY_MODE)
    assert mode == DISPLAY_MODE_CHAR, "Display mode should read as character"


@cocotb.test()
async def test_display_mode_masking(dut):
    """Test that DISPLAY_MODE masks to single bit"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Write with upper bits set
    await write_register(dut, REG_DISPLAY_MODE, 0xFF)
    # Should be masked to 1 bit
    assert dut.display_mode.value <= 1, "Display mode should be masked to 1 bit"

    # Write 0xFE (even value with upper bits)
    await write_register(dut, REG_DISPLAY_MODE, 0xFE)
    assert dut.display_mode.value == 0, "Should mask to bit 0 only"


@cocotb.test()
async def test_reserved_registers(dut):
    """Test that reserved register addresses don't cause issues"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Try accessing reserved addresses (0xE-0xF)
    for addr in [0xE, 0xF]:
        # Write should not crash
        await write_register(dut, addr, 0x55)

        # Read should not crash
        await read_register(dut, addr)

        # Core registers should be unaffected
        assert dut.vram_addr.value == 0, "Reserved access shouldn't affect vram_addr"
        assert dut.gpu_mode.value == 0, "Reserved access shouldn't affect gpu_mode"


@cocotb.test()
async def test_simultaneous_read_write_protection(dut):
    """Test that simultaneous read/write is handled correctly"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Try to assert both we and re simultaneously (invalid state)
    dut.reg_addr.value = REG_GPU_MODE
    dut.reg_data_in.value = 0x02
    dut.reg_we.value = 1
    dut.reg_re.value = 1
    await RisingEdge(dut.clk_cpu)

    # Implementation should handle gracefully (either prioritize or ignore)
    # Just verify it doesn't crash
    dut.reg_we.value = 0
    dut.reg_re.value = 0
    await RisingEdge(dut.clk_cpu)


@cocotb.test()
async def test_vram_data_read_burst_mode(dut):
    """Test VRAM_DATA read with burst mode (auto-increment on read)"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Set VRAM address
    await write_register(dut, REG_VRAM_ADDR_LO, 0x00)
    await write_register(dut, REG_VRAM_ADDR_HI, 0x30)  # Address 0x3000

    # Enable burst mode
    await write_register(dut, REG_VRAM_CTRL, VRAM_CTRL_BURST_EN)

    # Read first byte (address should increment)
    await read_register(dut, REG_VRAM_DATA)
    assert dut.vram_addr.value == 0x3001, "VRAM address should increment on read"

    # Read second byte
    await read_register(dut, REG_VRAM_DATA)
    assert dut.vram_addr.value == 0x3002, "VRAM address should increment to 0x3002"

    # Read third byte
    await read_register(dut, REG_VRAM_DATA)
    assert dut.vram_addr.value == 0x3003, "VRAM address should increment to 0x3003"


@cocotb.test()
async def test_vram_data_read_no_burst(dut):
    """Test VRAM_DATA read without burst mode (no auto-increment on read)"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # Set VRAM address
    await write_register(dut, REG_VRAM_ADDR_LO, 0x00)
    await write_register(dut, REG_VRAM_ADDR_HI, 0x40)  # Address 0x4000

    # Ensure burst mode is OFF
    await write_register(dut, REG_VRAM_CTRL, 0x00)

    # Read data (address should NOT increment)
    await read_register(dut, REG_VRAM_DATA)
    assert dut.vram_addr.value == 0x4000, "VRAM address should not increment without burst"

    # Read again
    await read_register(dut, REG_VRAM_DATA)
    assert dut.vram_addr.value == 0x4000, "VRAM address should remain at 0x4000"


@cocotb.test()
async def test_complete_register_workflow(dut):
    """Test a complete workflow: setup graphics mode, configure VRAM, write palette"""

    clock = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    # 1. Switch to graphics mode
    await write_register(dut, REG_DISPLAY_MODE, DISPLAY_MODE_GRAPHICS)
    assert dut.display_mode.value == 1, "Should be in graphics mode"

    # 2. Set GPU to 4BPP mode
    await write_register(dut, REG_GPU_MODE, GPU_MODE_4BPP)
    assert dut.gpu_mode.value == 2, "Should be in 4BPP mode"

    # 3. Set framebuffer base address to 0x4000
    await write_register(dut, REG_FB_BASE_ADDR_LO, 0x00)
    await write_register(dut, REG_FB_BASE_ADDR_HI, 0x40)
    assert dut.fb_base_addr.value == 0x4000, "FB base should be 0x4000"

    # 4. Configure palette entry 0 (black)
    await write_register(dut, REG_CLUT_INDEX, 0x00)
    await write_register(dut, REG_CLUT_DATA_R, 0x00)
    await write_register(dut, REG_CLUT_DATA_G, 0x00)
    await write_register(dut, REG_CLUT_DATA_B, 0x00)

    # 5. Configure palette entry 15 (white)
    await write_register(dut, REG_CLUT_INDEX, 0x0F)
    await write_register(dut, REG_CLUT_DATA_R, 0xFF)
    await write_register(dut, REG_CLUT_DATA_G, 0xFF)
    await write_register(dut, REG_CLUT_DATA_B, 0xFF)

    # 6. Enable VBlank interrupt
    await write_register(dut, REG_GPU_IRQ_CTRL, 0x01)
    assert dut.gpu_irq_ctrl.value == 1, "VBlank IRQ should be enabled"

    # 7. Set up VRAM write at address 0x0000
    await write_register(dut, REG_VRAM_ADDR_LO, 0x00)
    await write_register(dut, REG_VRAM_ADDR_HI, 0x00)

    # 8. Enable burst mode for fast writes
    await write_register(dut, REG_VRAM_CTRL, VRAM_CTRL_BURST_EN)

    # 9. Write some data
    for i in range(5):
        await write_register(dut, REG_VRAM_DATA, i * 0x11)

    # Verify final VRAM address
    assert dut.vram_addr.value == 5, "VRAM address should have incremented to 5"

    # 10. Check VBlank status
    dut.vblank.value = 1
    await RisingEdge(dut.clk_cpu)
    status = await read_register(dut, REG_GPU_STATUS)
    assert (status & 0x01) == 1, "VBlank flag should be set"


# cocotb test configuration
def test_runner():
    """pytest entry point for running cocotb tests"""
    import os
    from pathlib import Path

    # Get project root
    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    # RTL source
    verilog_sources = [
        rtl_dir / "peripherals" / "video" / "gpu_graphics_params.vh",
        rtl_dir / "peripherals" / "video" / "gpu_graphics_registers.v"
    ]

    # Include directory for header files
    includes = [
        rtl_dir / "peripherals" / "video"
    ]

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources],
        includes=[str(i) for i in includes],
        toplevel="gpu_graphics_registers",
        module="test_gpu_graphics_registers",
        simulator=simulator,
        waves=True if os.getenv("WAVES") == "1" else False,
    )


if __name__ == "__main__":
    test_runner()
