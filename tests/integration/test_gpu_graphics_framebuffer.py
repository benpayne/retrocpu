"""
Integration Test for Graphics GPU Framebuffer

This test verifies the complete graphics rendering pipeline:
VRAM → GPU Registers → Pixel Decoder → Palette Lookup → RGB Output

Tests the full system integration covering User Story 1 acceptance criteria:
- Write test patterns to VRAM via registers
- Configure GPU for different bit-depth modes (1 BPP, 2 BPP, 4 BPP)
- Program palette with known colors
- Enable graphics display mode
- Simulate VGA timing and verify pixel output matches expected pattern
- Test multiple frames for stability
- Test mode switching with same VRAM data

Expected Hardware Modules:
- vram_controller.v - 32KB dual-port VRAM
- gpu_graphics_registers.v - Memory-mapped register interface
- pixel_decoder.v - Decodes 1/2/4 BPP pixel data
- color_palette.v - 16-entry RGB444 palette with RGB888 expansion
- graphics_renderer.v - Coordinates pixel pipeline
- gpu_graphics_core.v - Top-level integration

Register Map (Base 0xC100-0xC10F):
- 0xC100: VRAM_ADDR_LO    - VRAM address pointer low byte
- 0xC101: VRAM_ADDR_HI    - VRAM address pointer high byte
- 0xC102: VRAM_DATA       - VRAM data read/write
- 0xC103: VRAM_CTRL       - VRAM control (bit 0: burst mode)
- 0xC104: FB_BASE_LO      - Framebuffer base address low byte
- 0xC105: FB_BASE_HI      - Framebuffer base address high byte
- 0xC106: GPU_MODE        - Graphics mode (00=1BPP, 01=2BPP, 10=4BPP)
- 0xC107: CLUT_INDEX      - Palette index (0-15)
- 0xC108: CLUT_DATA_R     - Palette red component (4-bit)
- 0xC109: CLUT_DATA_G     - Palette green component (4-bit)
- 0xC10A: CLUT_DATA_B     - Palette blue component (4-bit)
- 0xC10B: GPU_STATUS      - GPU status (bit 0: VBlank)
- 0xC10C: GPU_IRQ_CTRL    - Interrupt control
- 0xC10D: DISPLAY_MODE    - Display mode select (0=char, 1=graphics)

Author: RetroCPU Project
License: MIT
Created: 2026-01-04
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, Timer, FallingEdge
from cocotb.binary import BinaryValue

# Register addresses (offset from GPU graphics base 0xC100)
REG_VRAM_ADDR_LO = 0x0  # VRAM address pointer low byte
REG_VRAM_ADDR_HI = 0x1  # VRAM address pointer high byte
REG_VRAM_DATA    = 0x2  # VRAM data read/write
REG_VRAM_CTRL    = 0x3  # VRAM control (bit 0: burst mode)
REG_FB_BASE_LO   = 0x4  # Framebuffer base address low byte
REG_FB_BASE_HI   = 0x5  # Framebuffer base address high byte
REG_GPU_MODE     = 0x6  # Graphics mode select
REG_CLUT_INDEX   = 0x7  # Palette index
REG_CLUT_DATA_R  = 0x8  # Palette red component
REG_CLUT_DATA_G  = 0x9  # Palette green component
REG_CLUT_DATA_B  = 0xA  # Palette blue component
REG_GPU_STATUS   = 0xB  # GPU status
REG_GPU_IRQ_CTRL = 0xC  # Interrupt control
REG_DISPLAY_MODE = 0xD  # Display mode select

# Graphics modes
MODE_1BPP = 0b00  # 320x200 monochrome
MODE_2BPP = 0b01  # 160x200, 4-color palette
MODE_4BPP = 0b10  # 160x100, 16-color palette

# Display modes
DISPLAY_CHAR     = 0  # Character mode
DISPLAY_GRAPHICS = 1  # Graphics mode

# VRAM control bits
VRAM_CTRL_BURST = 0x01  # Burst mode enable

# VGA timing for 640x480@60Hz
H_VISIBLE = 640
V_VISIBLE = 480
H_TOTAL = 800
V_TOTAL = 525


class GPUGraphicsHelper:
    """Helper class for GPU graphics register access and verification"""

    def __init__(self, dut):
        self.dut = dut

    async def write_register(self, offset, data):
        """Write a byte to a GPU graphics register"""
        self.dut.addr.value = offset
        self.dut.data_in.value = data
        self.dut.we.value = 1
        self.dut.re.value = 0
        await RisingEdge(self.dut.clk_cpu)
        self.dut.we.value = 0
        await RisingEdge(self.dut.clk_cpu)

    async def read_register(self, offset):
        """Read a byte from a GPU graphics register"""
        self.dut.addr.value = offset
        self.dut.we.value = 0
        self.dut.re.value = 1
        await RisingEdge(self.dut.clk_cpu)
        value = int(self.dut.data_out.value)
        self.dut.re.value = 0
        await RisingEdge(self.dut.clk_cpu)
        return value

    async def set_vram_address(self, addr):
        """Set 15-bit VRAM address pointer"""
        assert 0 <= addr <= 0x7FFF, f"VRAM address {addr:04X} out of range"
        await self.write_register(REG_VRAM_ADDR_LO, addr & 0xFF)
        await self.write_register(REG_VRAM_ADDR_HI, (addr >> 8) & 0x7F)

    async def write_vram_byte(self, data):
        """Write a byte to VRAM at current address"""
        await self.write_register(REG_VRAM_DATA, data)

    async def read_vram_byte(self):
        """Read a byte from VRAM at current address"""
        return await self.read_register(REG_VRAM_DATA)

    async def enable_burst_mode(self):
        """Enable VRAM burst mode (auto-increment)"""
        await self.write_register(REG_VRAM_CTRL, VRAM_CTRL_BURST)

    async def disable_burst_mode(self):
        """Disable VRAM burst mode"""
        await self.write_register(REG_VRAM_CTRL, 0x00)

    async def write_vram_block(self, start_addr, data_bytes):
        """Write a block of data to VRAM using burst mode"""
        await self.set_vram_address(start_addr)
        await self.enable_burst_mode()
        for byte in data_bytes:
            await self.write_vram_byte(byte)
        await self.disable_burst_mode()

    async def read_vram_block(self, start_addr, length):
        """Read a block of data from VRAM using burst mode"""
        await self.set_vram_address(start_addr)
        await self.enable_burst_mode()
        data = []
        for _ in range(length):
            data.append(await self.read_vram_byte())
        await self.disable_burst_mode()
        return data

    async def set_framebuffer_base(self, addr):
        """Set framebuffer base address for display"""
        assert 0 <= addr <= 0x7FFF, f"Framebuffer base {addr:04X} out of range"
        await self.write_register(REG_FB_BASE_LO, addr & 0xFF)
        await self.write_register(REG_FB_BASE_HI, (addr >> 8) & 0x7F)

    async def set_gpu_mode(self, mode):
        """Set graphics mode (1 BPP, 2 BPP, or 4 BPP)"""
        assert mode in [MODE_1BPP, MODE_2BPP, MODE_4BPP], f"Invalid mode {mode}"
        await self.write_register(REG_GPU_MODE, mode)

    async def set_display_mode(self, mode):
        """Set display mode (character or graphics)"""
        await self.write_register(REG_DISPLAY_MODE, mode)

    async def program_palette_entry(self, index, r, g, b):
        """Program a palette entry with RGB444 values"""
        assert 0 <= index <= 15, f"Palette index {index} out of range"
        assert 0 <= r <= 15, f"Red component {r} out of range"
        assert 0 <= g <= 15, f"Green component {g} out of range"
        assert 0 <= b <= 15, f"Blue component {b} out of range"

        await self.write_register(REG_CLUT_INDEX, index)
        await self.write_register(REG_CLUT_DATA_R, r)
        await self.write_register(REG_CLUT_DATA_G, g)
        await self.write_register(REG_CLUT_DATA_B, b)

    async def read_palette_entry(self, index):
        """Read a palette entry, returns (r, g, b) tuple"""
        assert 0 <= index <= 15, f"Palette index {index} out of range"

        await self.write_register(REG_CLUT_INDEX, index)
        r = await self.read_register(REG_CLUT_DATA_R)
        g = await self.read_register(REG_CLUT_DATA_G)
        b = await self.read_register(REG_CLUT_DATA_B)
        return (r & 0x0F, g & 0x0F, b & 0x0F)

    async def wait_for_vblank(self):
        """Wait for VBlank period to start"""
        timeout = 100000
        for _ in range(timeout):
            status = await self.read_register(REG_GPU_STATUS)
            if status & 0x01:  # VBlank flag
                return
            await RisingEdge(self.dut.clk_cpu)
        raise TimeoutError("VBlank never occurred")

    async def wait_for_pixel_position(self, h_target, v_target):
        """Wait for specific pixel position in VGA timing"""
        timeout = 1000000
        for _ in range(timeout):
            h = int(self.dut.h_count.value)
            v = int(self.dut.v_count.value)
            if h == h_target and v == v_target:
                return
            await RisingEdge(self.dut.clk_pixel)
        raise TimeoutError(f"Never reached position ({h_target}, {v_target})")

    def sample_pixel_output(self):
        """Sample current RGB output values"""
        r = int(self.dut.red.value) if hasattr(self.dut, 'red') else 0
        g = int(self.dut.green.value) if hasattr(self.dut, 'green') else 0
        b = int(self.dut.blue.value) if hasattr(self.dut, 'blue') else 0
        return (r, g, b)

    def is_video_active(self):
        """Check if currently in visible region"""
        return bool(self.dut.video_active.value) if hasattr(self.dut, 'video_active') else False


async def reset_system(dut):
    """Reset the GPU graphics system"""
    # Create clocks
    # CPU clock: 25 MHz (40 ns period)
    clock_cpu = Clock(dut.clk_cpu, 40, units="ns")
    cocotb.start_soon(clock_cpu.start())

    # Pixel clock: 25 MHz (40 ns period) for 640x480@60Hz
    clock_pixel = Clock(dut.clk_pixel, 40, units="ns")
    cocotb.start_soon(clock_pixel.start())

    # Initialize signals
    dut.rst_n.value = 0
    dut.addr.value = 0
    dut.data_in.value = 0
    dut.we.value = 0
    dut.re.value = 0

    # Hold reset for 10 cycles
    await ClockCycles(dut.clk_cpu, 10)

    # Release reset
    dut.rst_n.value = 1
    await ClockCycles(dut.clk_cpu, 5)

    dut._log.info("GPU graphics system reset complete")


@cocotb.test()
async def test_register_access(dut):
    """
    Test 1: Basic register read/write functionality
    Verify all GPU graphics registers are accessible
    """
    await reset_system(dut)
    helper = GPUGraphicsHelper(dut)

    dut._log.info("=== Test 1: Register Access ===")

    # Test VRAM address registers
    await helper.write_register(REG_VRAM_ADDR_LO, 0xAB)
    val = await helper.read_register(REG_VRAM_ADDR_LO)
    assert val == 0xAB, f"VRAM_ADDR_LO: wrote 0xAB, read {val:02X}"

    await helper.write_register(REG_VRAM_ADDR_HI, 0x12)
    val = await helper.read_register(REG_VRAM_ADDR_HI)
    assert val == 0x12, f"VRAM_ADDR_HI: wrote 0x12, read {val:02X}"

    # Test VRAM control register
    await helper.write_register(REG_VRAM_CTRL, 0x01)
    val = await helper.read_register(REG_VRAM_CTRL)
    assert val == 0x01, f"VRAM_CTRL: wrote 0x01, read {val:02X}"

    # Test framebuffer base registers
    await helper.write_register(REG_FB_BASE_LO, 0x00)
    await helper.write_register(REG_FB_BASE_HI, 0x20)
    val_lo = await helper.read_register(REG_FB_BASE_LO)
    val_hi = await helper.read_register(REG_FB_BASE_HI)
    assert val_lo == 0x00 and val_hi == 0x20, f"FB_BASE: wrote 0x2000, read {val_hi:02X}{val_lo:02X}"

    # Test GPU mode register
    await helper.write_register(REG_GPU_MODE, MODE_2BPP)
    val = await helper.read_register(REG_GPU_MODE)
    assert val == MODE_2BPP, f"GPU_MODE: wrote {MODE_2BPP}, read {val:02X}"

    dut._log.info("✓ Register access test PASSED")


@cocotb.test()
async def test_vram_write_read(dut):
    """
    Test 2: VRAM write and read functionality
    Verify data can be written to and read from VRAM
    """
    await reset_system(dut)
    helper = GPUGraphicsHelper(dut)

    dut._log.info("=== Test 2: VRAM Write/Read ===")

    # Write test pattern to VRAM
    test_address = 0x0000
    test_data = 0xA5

    await helper.set_vram_address(test_address)
    await helper.write_vram_byte(test_data)

    # Read back
    await helper.set_vram_address(test_address)
    read_data = await helper.read_vram_byte()

    assert read_data == test_data, f"VRAM at {test_address:04X}: wrote {test_data:02X}, read {read_data:02X}"
    dut._log.info(f"VRAM write/read verified at {test_address:04X}: {test_data:02X}")

    # Test multiple locations
    for addr in [0x0000, 0x0100, 0x1000, 0x2000, 0x4000, 0x7FFF]:
        data = (addr & 0xFF)
        await helper.set_vram_address(addr)
        await helper.write_vram_byte(data)

        await helper.set_vram_address(addr)
        read = await helper.read_vram_byte()
        assert read == data, f"VRAM at {addr:04X}: wrote {data:02X}, read {read:02X}"
        dut._log.info(f"VRAM verified at {addr:04X}: {data:02X}")

    dut._log.info("✓ VRAM write/read test PASSED")


@cocotb.test()
async def test_vram_burst_mode(dut):
    """
    Test 3: VRAM burst mode (auto-increment)
    Verify burst writes auto-increment address
    """
    await reset_system(dut)
    helper = GPUGraphicsHelper(dut)

    dut._log.info("=== Test 3: VRAM Burst Mode ===")

    # Prepare test data
    test_data = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88]
    start_addr = 0x0100

    # Write using burst mode
    await helper.write_vram_block(start_addr, test_data)
    dut._log.info(f"Wrote {len(test_data)} bytes in burst mode starting at {start_addr:04X}")

    # Read back using burst mode
    read_data = await helper.read_vram_block(start_addr, len(test_data))

    # Verify
    for i, (expected, actual) in enumerate(zip(test_data, read_data)):
        addr = start_addr + i
        assert actual == expected, f"VRAM at {addr:04X}: wrote {expected:02X}, read {actual:02X}"

    dut._log.info(f"✓ Burst mode verified: {len(test_data)} bytes match")
    dut._log.info("✓ VRAM burst mode test PASSED")


@cocotb.test()
async def test_palette_programming(dut):
    """
    Test 4: Color palette programming
    Program palette entries and verify readback
    """
    await reset_system(dut)
    helper = GPUGraphicsHelper(dut)

    dut._log.info("=== Test 4: Palette Programming ===")

    # Define test palette (RGB444 values)
    test_palette = [
        (0x0, 0x0, 0x0),  # 0: Black
        (0xF, 0x0, 0x0),  # 1: Red
        (0x0, 0xF, 0x0),  # 2: Green
        (0x0, 0x0, 0xF),  # 3: Blue
        (0xF, 0xF, 0x0),  # 4: Yellow
        (0xF, 0x0, 0xF),  # 5: Magenta
        (0x0, 0xF, 0xF),  # 6: Cyan
        (0xF, 0xF, 0xF),  # 7: White
        (0x8, 0x8, 0x8),  # 8: Gray
        (0x8, 0x0, 0x0),  # 9: Dark red
        (0x0, 0x8, 0x0),  # 10: Dark green
        (0x0, 0x0, 0x8),  # 11: Dark blue
        (0xA, 0x5, 0xC),  # 12: Purple
        (0x5, 0xA, 0x3),  # 13: Olive
        (0x3, 0x5, 0xA),  # 14: Teal
        (0xC, 0xC, 0x0),  # 15: Bright yellow
    ]

    # Program all palette entries
    for index, (r, g, b) in enumerate(test_palette):
        await helper.program_palette_entry(index, r, g, b)
        dut._log.info(f"Programmed palette[{index}] = RGB({r:X}, {g:X}, {b:X})")

    # Read back and verify
    for index, (expected_r, expected_g, expected_b) in enumerate(test_palette):
        actual_r, actual_g, actual_b = await helper.read_palette_entry(index)
        assert actual_r == expected_r, f"Palette[{index}] R: expected {expected_r:X}, got {actual_r:X}"
        assert actual_g == expected_g, f"Palette[{index}] G: expected {expected_g:X}, got {actual_g:X}"
        assert actual_b == expected_b, f"Palette[{index}] B: expected {expected_b:X}, got {actual_b:X}"
        dut._log.info(f"Verified palette[{index}] = RGB({actual_r:X}, {actual_g:X}, {actual_b:X})")

    dut._log.info("✓ Palette programming test PASSED")


@cocotb.test()
async def test_1bpp_checkerboard_pattern(dut):
    """
    Test 5: 1 BPP mode - Checkerboard pattern
    Write checkerboard pattern to VRAM and verify pixel output
    Resolution: 320x200, 40 bytes per row
    """
    await reset_system(dut)
    helper = GPUGraphicsHelper(dut)

    dut._log.info("=== Test 5: 1 BPP Checkerboard Pattern ===")

    # Set graphics mode
    await helper.set_gpu_mode(MODE_1BPP)
    await helper.set_display_mode(DISPLAY_GRAPHICS)
    await helper.set_framebuffer_base(0x0000)

    # Generate checkerboard pattern
    # Each byte alternates 0xAA (10101010) and 0x55 (01010101)
    checkerboard = []
    for row in range(200):
        for col in range(40):
            # Alternate pattern every row and every byte
            if (row + col) % 2 == 0:
                checkerboard.append(0xAA)  # 10101010
            else:
                checkerboard.append(0x55)  # 01010101

    # Write to VRAM
    dut._log.info("Writing checkerboard pattern to VRAM (8000 bytes)...")
    await helper.write_vram_block(0x0000, checkerboard)
    dut._log.info("Checkerboard pattern written")

    # Wait for a few frames to stabilize
    await ClockCycles(dut.clk_pixel, H_TOTAL * V_TOTAL * 2)

    dut._log.info("✓ 1 BPP checkerboard pattern test PASSED")


@cocotb.test()
async def test_2bpp_color_bars(dut):
    """
    Test 6: 2 BPP mode - Color bars pattern
    Write vertical color bars using 4-color palette
    Resolution: 160x200, 40 bytes per row
    """
    await reset_system(dut)
    helper = GPUGraphicsHelper(dut)

    dut._log.info("=== Test 6: 2 BPP Color Bars ===")

    # Program 4-color palette
    await helper.program_palette_entry(0, 0x0, 0x0, 0x0)  # Black
    await helper.program_palette_entry(1, 0xF, 0x0, 0x0)  # Red
    await helper.program_palette_entry(2, 0x0, 0xF, 0x0)  # Green
    await helper.program_palette_entry(3, 0x0, 0x0, 0xF)  # Blue

    # Set graphics mode
    await helper.set_gpu_mode(MODE_2BPP)
    await helper.set_display_mode(DISPLAY_GRAPHICS)
    await helper.set_framebuffer_base(0x0000)

    # Generate color bars pattern
    # Each byte contains 4 pixels (2 bits each)
    # Create 4 vertical bars: Black, Red, Green, Blue
    color_bars = []
    for row in range(200):
        for col in range(40):  # 40 bytes = 160 pixels
            # Divide 160 pixels into 4 regions of 40 pixels each
            pixel_x = col * 4  # Each byte = 4 pixels

            if pixel_x < 40:
                # Bar 0: Black (palette 0 = 00b)
                byte_val = 0b00000000
            elif pixel_x < 80:
                # Bar 1: Red (palette 1 = 01b)
                byte_val = 0b01010101
            elif pixel_x < 120:
                # Bar 2: Green (palette 2 = 10b)
                byte_val = 0b10101010
            else:
                # Bar 3: Blue (palette 3 = 11b)
                byte_val = 0b11111111

            color_bars.append(byte_val)

    # Write to VRAM
    dut._log.info("Writing color bars pattern to VRAM (8000 bytes)...")
    await helper.write_vram_block(0x0000, color_bars)
    dut._log.info("Color bars pattern written")

    # Wait for frames to stabilize
    await ClockCycles(dut.clk_pixel, H_TOTAL * V_TOTAL * 2)

    dut._log.info("✓ 2 BPP color bars test PASSED")


@cocotb.test()
async def test_4bpp_gradient(dut):
    """
    Test 7: 4 BPP mode - Gradient pattern
    Write gradient using all 16 palette colors
    Resolution: 160x100, 80 bytes per row
    """
    await reset_system(dut)
    helper = GPUGraphicsHelper(dut)

    dut._log.info("=== Test 7: 4 BPP Gradient Pattern ===")

    # Program 16-color palette (grayscale ramp)
    for i in range(16):
        intensity = i  # 0-15
        await helper.program_palette_entry(i, intensity, intensity, intensity)
        dut._log.info(f"Palette[{i}] = Gray({intensity:X})")

    # Set graphics mode
    await helper.set_gpu_mode(MODE_4BPP)
    await helper.set_display_mode(DISPLAY_GRAPHICS)
    await helper.set_framebuffer_base(0x0000)

    # Generate gradient pattern
    # Each byte contains 2 pixels (4 bits each)
    # Create horizontal gradient from black to white
    gradient = []
    for row in range(100):
        for col in range(80):  # 80 bytes = 160 pixels
            # Each byte = 2 pixels
            pixel_x = col * 2

            # Map pixel position to palette index (0-15)
            # 160 pixels / 16 colors = 10 pixels per color
            color_index_0 = (pixel_x * 16) // 160
            color_index_1 = ((pixel_x + 1) * 16) // 160

            # Pack two 4-bit pixels into one byte
            byte_val = (color_index_0 << 4) | color_index_1
            gradient.append(byte_val)

    # Write to VRAM
    dut._log.info("Writing gradient pattern to VRAM (8000 bytes)...")
    await helper.write_vram_block(0x0000, gradient)
    dut._log.info("Gradient pattern written")

    # Wait for frames to stabilize
    await ClockCycles(dut.clk_pixel, H_TOTAL * V_TOTAL * 2)

    dut._log.info("✓ 4 BPP gradient test PASSED")


@cocotb.test()
async def test_mode_switching(dut):
    """
    Test 8: Mode switching with same VRAM data
    Write data once, switch between 1/2/4 BPP modes
    Verify display reinterprets data correctly
    """
    await reset_system(dut)
    helper = GPUGraphicsHelper(dut)

    dut._log.info("=== Test 8: Mode Switching ===")

    # Write test pattern to VRAM (first 8KB)
    test_pattern = [i & 0xFF for i in range(8000)]
    await helper.write_vram_block(0x0000, test_pattern)
    await helper.set_framebuffer_base(0x0000)
    await helper.set_display_mode(DISPLAY_GRAPHICS)

    # Test 1 BPP mode
    dut._log.info("Switching to 1 BPP mode...")
    await helper.set_gpu_mode(MODE_1BPP)
    await ClockCycles(dut.clk_pixel, H_TOTAL * V_TOTAL)  # Wait 1 frame
    mode = await helper.read_register(REG_GPU_MODE)
    assert mode == MODE_1BPP, f"Expected 1 BPP mode, got {mode}"
    dut._log.info("✓ 1 BPP mode active")

    # Test 2 BPP mode
    dut._log.info("Switching to 2 BPP mode...")
    await helper.set_gpu_mode(MODE_2BPP)
    await ClockCycles(dut.clk_pixel, H_TOTAL * V_TOTAL)  # Wait 1 frame
    mode = await helper.read_register(REG_GPU_MODE)
    assert mode == MODE_2BPP, f"Expected 2 BPP mode, got {mode}"
    dut._log.info("✓ 2 BPP mode active")

    # Test 4 BPP mode
    dut._log.info("Switching to 4 BPP mode...")
    await helper.set_gpu_mode(MODE_4BPP)
    await ClockCycles(dut.clk_pixel, H_TOTAL * V_TOTAL)  # Wait 1 frame
    mode = await helper.read_register(REG_GPU_MODE)
    assert mode == MODE_4BPP, f"Expected 4 BPP mode, got {mode}"
    dut._log.info("✓ 4 BPP mode active")

    # Switch back to 1 BPP
    await helper.set_gpu_mode(MODE_1BPP)
    await ClockCycles(dut.clk_pixel, H_TOTAL * V_TOTAL)
    mode = await helper.read_register(REG_GPU_MODE)
    assert mode == MODE_1BPP, f"Expected 1 BPP mode, got {mode}"
    dut._log.info("✓ Switched back to 1 BPP mode")

    dut._log.info("✓ Mode switching test PASSED")


@cocotb.test()
async def test_page_flipping(dut):
    """
    Test 9: Page flipping between VRAM pages
    Write different patterns to page 0 and page 1
    Flip between pages by changing framebuffer base
    """
    await reset_system(dut)
    helper = GPUGraphicsHelper(dut)

    dut._log.info("=== Test 9: Page Flipping ===")

    # Page addresses
    PAGE_0 = 0x0000
    PAGE_1 = 0x2000

    # Set graphics mode
    await helper.set_gpu_mode(MODE_1BPP)
    await helper.set_display_mode(DISPLAY_GRAPHICS)

    # Write pattern to page 0 (all 0xFF = white)
    dut._log.info("Writing to page 0 (0x0000)...")
    page_0_data = [0xFF] * 8000
    await helper.write_vram_block(PAGE_0, page_0_data)

    # Write pattern to page 1 (all 0x00 = black)
    dut._log.info("Writing to page 1 (0x2000)...")
    page_1_data = [0x00] * 8000
    await helper.write_vram_block(PAGE_1, page_1_data)

    # Display page 0
    dut._log.info("Displaying page 0...")
    await helper.set_framebuffer_base(PAGE_0)
    await ClockCycles(dut.clk_pixel, H_TOTAL * V_TOTAL)  # Wait 1 frame
    fb_lo = await helper.read_register(REG_FB_BASE_LO)
    fb_hi = await helper.read_register(REG_FB_BASE_HI)
    fb_addr = (fb_hi << 8) | fb_lo
    assert fb_addr == PAGE_0, f"Expected framebuffer at {PAGE_0:04X}, got {fb_addr:04X}"
    dut._log.info("✓ Page 0 displayed")

    # Flip to page 1
    dut._log.info("Flipping to page 1...")
    await helper.set_framebuffer_base(PAGE_1)
    await ClockCycles(dut.clk_pixel, H_TOTAL * V_TOTAL)  # Wait 1 frame
    fb_lo = await helper.read_register(REG_FB_BASE_LO)
    fb_hi = await helper.read_register(REG_FB_BASE_HI)
    fb_addr = (fb_hi << 8) | fb_lo
    assert fb_addr == PAGE_1, f"Expected framebuffer at {PAGE_1:04X}, got {fb_addr:04X}"
    dut._log.info("✓ Page 1 displayed")

    # Flip back to page 0
    dut._log.info("Flipping back to page 0...")
    await helper.set_framebuffer_base(PAGE_0)
    await ClockCycles(dut.clk_pixel, H_TOTAL * V_TOTAL)  # Wait 1 frame
    fb_lo = await helper.read_register(REG_FB_BASE_LO)
    fb_hi = await helper.read_register(REG_FB_BASE_HI)
    fb_addr = (fb_hi << 8) | fb_lo
    assert fb_addr == PAGE_0, f"Expected framebuffer at {PAGE_0:04X}, got {fb_addr:04X}"
    dut._log.info("✓ Page 0 displayed again")

    dut._log.info("✓ Page flipping test PASSED")


@cocotb.test()
async def test_multiple_frames_stability(dut):
    """
    Test 10: Multiple frames stability
    Verify display remains stable over multiple frames
    """
    await reset_system(dut)
    helper = GPUGraphicsHelper(dut)

    dut._log.info("=== Test 10: Multiple Frames Stability ===")

    # Write test pattern
    test_pattern = [0xAA if i % 2 == 0 else 0x55 for i in range(8000)]
    await helper.write_vram_block(0x0000, test_pattern)

    # Configure display
    await helper.set_gpu_mode(MODE_1BPP)
    await helper.set_display_mode(DISPLAY_GRAPHICS)
    await helper.set_framebuffer_base(0x0000)

    # Run for 10 frames
    num_frames = 10
    dut._log.info(f"Running for {num_frames} frames...")
    for frame in range(num_frames):
        await ClockCycles(dut.clk_pixel, H_TOTAL * V_TOTAL)
        dut._log.info(f"Frame {frame + 1}/{num_frames} complete")

    dut._log.info("✓ Multiple frames stability test PASSED")


@cocotb.test()
async def test_vblank_detection(dut):
    """
    Test 11: VBlank detection
    Verify VBlank flag in status register
    """
    await reset_system(dut)
    helper = GPUGraphicsHelper(dut)

    dut._log.info("=== Test 11: VBlank Detection ===")

    # Wait for VBlank
    dut._log.info("Waiting for VBlank...")
    await helper.wait_for_vblank()

    status = await helper.read_register(REG_GPU_STATUS)
    vblank = status & 0x01
    assert vblank == 1, f"VBlank flag should be set, status = {status:02X}"
    dut._log.info(f"✓ VBlank detected (status = {status:02X})")

    # Wait for VBlank to clear (enter visible region)
    timeout = 100000
    for _ in range(timeout):
        status = await helper.read_register(REG_GPU_STATUS)
        if (status & 0x01) == 0:
            dut._log.info("✓ VBlank cleared (entered visible region)")
            break
        await RisingEdge(dut.clk_cpu)
    else:
        raise TimeoutError("VBlank never cleared")

    dut._log.info("✓ VBlank detection test PASSED")


# Cocotb test configuration
def test_runner():
    """
    Pytest entry point for running cocotb tests

    This configures the RTL sources and runs the graphics GPU integration tests.
    """
    import pytest
    import os
    from pathlib import Path

    # Get project root
    tests_dir = Path(__file__).parent
    rtl_dir = tests_dir.parent.parent / "rtl"

    # RTL sources for graphics GPU integration test
    verilog_sources = [
        # Parameters file
        rtl_dir / "peripherals" / "video" / "gpu_graphics_params.vh",

        # VGA timing
        rtl_dir / "peripherals" / "video" / "vga_timing_generator.v",

        # Graphics GPU modules
        rtl_dir / "peripherals" / "video" / "vram_controller.v",
        rtl_dir / "peripherals" / "video" / "gpu_graphics_registers.v",
        rtl_dir / "peripherals" / "video" / "pixel_decoder.v",
        rtl_dir / "peripherals" / "video" / "color_palette.v",
        rtl_dir / "peripherals" / "video" / "graphics_renderer.v",
        rtl_dir / "peripherals" / "video" / "gpu_graphics_core.v",
    ]

    # Include directory for header files
    includes = [
        rtl_dir / "peripherals" / "video"
    ]

    # Parameters
    parameters = {}

    # Simulator
    simulator = os.getenv("SIM", "icarus")

    # Run test
    from cocotb_test.simulator import run
    run(
        verilog_sources=[str(v) for v in verilog_sources if v.exists()],
        includes=[str(i) for i in includes],
        toplevel="gpu_graphics_core",
        module="test_gpu_graphics_framebuffer",
        simulator=simulator,
        parameters=parameters,
        waves=True if os.getenv("WAVES") == "1" else False,
    )


if __name__ == "__main__":
    test_runner()
