# Integration Tests Makefile
# Tests full system integration (CPU + memory + peripherals)

# Paths
RTL_DIR = ../../rtl
TOPLEVEL = cpu_display_test

# Verilog sources for cpu_display_test
VERILOG_SOURCES = \
	$(RTL_DIR)/cpu/arlet-6502/cpu.v \
	$(RTL_DIR)/cpu/arlet-6502/ALU.v \
	$(RTL_DIR)/system/reset_controller.v \
	$(RTL_DIR)/test/$(TOPLEVEL).v

# cocotb configuration
TOPLEVEL_LANG = verilog
MODULE = test_cpu_write_debug

# Simulator (use icarus verilog)
SIM = icarus

# Include cocotb makefiles
include $(shell cocotb-config --makefiles)/Makefile.sim

# Clean target
clean::
	rm -rf __pycache__
	rm -rf sim_build
	rm -f results.xml
	rm -f *.vcd
