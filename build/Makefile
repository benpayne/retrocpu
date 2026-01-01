# RetroCPU 6502 FPGA Build System
# Target: Lattice ECP5-25F (Colorlight i5)
# Toolchain: Yosys + nextpnr-ecp5

# Configuration
PROJECT = soc_top
TOP = soc_top
DEVICE = 25k
PACKAGE = CABGA381
SPEED = 6
LPF = ../colorlight_i5_debug.lpf

# Directories
RTL_DIR = ../rtl
BUILD_DIR = .
SYNTH_DIR = $(BUILD_DIR)/synth
PNR_DIR = $(BUILD_DIR)/pnr

# Source files
RTL_SOURCES = \
	$(RTL_DIR)/cpu/m65c02/M65C02_Core.v \
	$(RTL_DIR)/cpu/m65c02/M65C02_MPCv4.v \
	$(RTL_DIR)/cpu/m65c02/M65C02_AddrGen.v \
	$(RTL_DIR)/cpu/m65c02/M65C02_ALU.v \
	$(RTL_DIR)/cpu/m65c02/M65C02_BIN.v \
	$(RTL_DIR)/cpu/m65c02/M65C02_BCD.v \
	$(RTL_DIR)/system/reset_controller.v \
	$(RTL_DIR)/memory/ram.v \
	$(RTL_DIR)/memory/rom_basic.v \
	$(RTL_DIR)/memory/rom_monitor.v \
	$(RTL_DIR)/memory/address_decoder.v \
	$(RTL_DIR)/peripherals/uart/uart.v \
	$(RTL_DIR)/peripherals/uart/uart_tx.v \
	$(RTL_DIR)/peripherals/uart/uart_rx.v \
	$(RTL_DIR)/peripherals/lcd/lcd_controller.v \
	$(RTL_DIR)/peripherals/lcd/lcd_timing.v \
	$(RTL_DIR)/peripherals/lcd/lcd_init_fsm.v \
	$(RTL_DIR)/peripherals/ps2/ps2_wrapper.v \
	$(RTL_DIR)/peripherals/ps2/ps2-controller-lib/rtl/ps2_decoder_core.v \
	$(RTL_DIR)/peripherals/ps2/ps2-controller-lib/rtl/debounce.v \
	$(RTL_DIR)/system/ecp5_pll.sv \
	$(RTL_DIR)/peripherals/video/gpu_top.v \
	$(RTL_DIR)/peripherals/video/gpu_core.v \
	$(RTL_DIR)/peripherals/video/gpu_registers.v \
	$(RTL_DIR)/peripherals/video/character_buffer.v \
	$(RTL_DIR)/peripherals/video/character_renderer.v \
	$(RTL_DIR)/peripherals/video/font_rom.v \
	$(RTL_DIR)/peripherals/video/vga_timing_generator.v \
	$(RTL_DIR)/peripherals/video/dvi_transmitter.v \
	$(RTL_DIR)/peripherals/video/tmds_encoder.v \
	$(RTL_DIR)/system/$(TOP).v

# Arlet 6502 core (commented out - replaced by M65C02)
#	$(RTL_DIR)/cpu/arlet-6502/cpu.v \
#	$(RTL_DIR)/cpu/arlet-6502/ALU.v \
#	$(RTL_DIR)/system/clock_divider.v \

# Firmware hex files (must be built first)
FIRMWARE_MONITOR = ../firmware/monitor/monitor.hex
FIRMWARE_BASIC = ../firmware/basic/basic_rom.hex

# Output files
JSON = $(SYNTH_DIR)/$(PROJECT).json
CONFIG = $(PNR_DIR)/$(PROJECT).config
BITSTREAM = $(PROJECT).bit
TIMING_RPT = $(PNR_DIR)/timing.rpt
UTIL_RPT = $(SYNTH_DIR)/utilization.rpt

# Tools
YOSYS = yosys
NEXTPNR = nextpnr-ecp5
ECPPACK = ecppack
OPENFPGALOADER = openFPGALoader

# Yosys synthesis flags
YOSYS_FLAGS = -q -l $(SYNTH_DIR)/yosys.log
YOSYS_INCLUDE = -I$(RTL_DIR)/cpu/m65c02

# nextpnr flags
NEXTPNR_FLAGS = \
	--$(DEVICE) \
	--package $(PACKAGE) \
	--speed $(SPEED) \
	--json $(JSON) \
	--lpf $(LPF) \
	--textcfg $(CONFIG) \
	--timing-allow-fail \
	--ignore-loops \
	--log $(PNR_DIR)/nextpnr.log

# Targets
.PHONY: all clean synth pnr bitstream program util timing dirs help

all: dirs bitstream util timing

help:
	@echo "RetroCPU Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all        - Full build (synthesis + place-and-route + bitstream)"
	@echo "  synth      - Run Yosys synthesis"
	@echo "  pnr        - Run nextpnr place-and-route"
	@echo "  bitstream  - Generate bitstream (.bit file)"
	@echo "  program    - Program FPGA via openFPGALoader"
	@echo "  util       - Display resource utilization"
	@echo "  timing     - Display timing report"
	@echo "  clean      - Remove build artifacts"
	@echo "  dirs       - Create build directories"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - Firmware must be built first (firmware/monitor/monitor.hex)"
	@echo "  - All RTL modules must exist in rtl/"
	@echo ""

dirs:
	@mkdir -p $(SYNTH_DIR) $(PNR_DIR)

# Check firmware exists before synthesis
.PHONY: check-firmware
check-firmware:
	@if [ ! -f $(FIRMWARE_MONITOR) ]; then \
		echo "ERROR: Monitor firmware not found at $(FIRMWARE_MONITOR)"; \
		echo "Please run 'make' in firmware/monitor/ first"; \
		exit 1; \
	fi
	@if [ ! -f $(FIRMWARE_BASIC) ]; then \
		echo "ERROR: BASIC firmware not found at $(FIRMWARE_BASIC)"; \
		echo "Please run 'make' in firmware/basic/ first"; \
		exit 1; \
	fi
	@echo "Firmware check passed"

# Synthesis
synth: dirs
	@echo "Running Yosys synthesis..."
	$(YOSYS) $(YOSYS_FLAGS) -p \
		"read_verilog -sv $(YOSYS_INCLUDE) $(RTL_SOURCES); \
		 synth_ecp5 -top $(TOP) -json $(JSON)" \
		2>&1 | tee $(SYNTH_DIR)/yosys.log
	@echo "Synthesis complete: $(JSON)"

# Place and route
pnr: synth
	@echo "Running nextpnr-ecp5 place-and-route..."
	$(NEXTPNR) $(NEXTPNR_FLAGS)
	@echo "Place-and-route complete: $(CONFIG)"

# Generate bitstream
bitstream: pnr
	@echo "Generating bitstream..."
	$(ECPPACK) --compress --input $(CONFIG) --bit $(BITSTREAM)
	@echo "Bitstream ready: $(BITSTREAM)"
	@ls -lh $(BITSTREAM)

# Program FPGA
program: bitstream
	@echo "Programming FPGA (Colorlight i5)..."
	$(OPENFPGALOADER) -b colorlight-i5 $(BITSTREAM)

# Resource utilization report
util: synth
	@echo "=== Resource Utilization ==="
	@if [ -f $(SYNTH_DIR)/yosys.log ]; then \
		grep -A 20 "Printing statistics" $(SYNTH_DIR)/yosys.log | tee $(UTIL_RPT); \
	else \
		echo "No synthesis log found. Run 'make synth' first."; \
	fi

# Timing report
timing: pnr
	@echo "=== Timing Report ==="
	@if [ -f $(PNR_DIR)/nextpnr.log ]; then \
		grep -A 30 "Max frequency" $(PNR_DIR)/nextpnr.log | tee $(TIMING_RPT); \
	else \
		echo "No place-and-route log found. Run 'make pnr' first."; \
	fi

# Clean build artifacts
clean:
	rm -rf $(SYNTH_DIR) $(PNR_DIR)
	rm -f $(BITSTREAM)
	rm -f *.log
	@echo "Build artifacts cleaned"

# Dependency tracking (rebuild if sources change)
$(JSON): $(RTL_SOURCES) $(FIRMWARE_MONITOR) $(FIRMWARE_BASIC)
	$(MAKE) synth

$(CONFIG): $(JSON)
	$(MAKE) pnr

$(BITSTREAM): $(CONFIG)
	$(MAKE) bitstream
