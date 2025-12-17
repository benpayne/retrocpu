# RetroCPU Unit Tests Makefile
# Uses cocotb for HDL verification

# Common settings
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
WAVES ?= 0

# Python test discovery
PYTHONPATH := $(PWD):$(PYTHONPATH)
export PYTHONPATH

# Targets for individual tests
.PHONY: test-clock-divider test-reset-controller test-all clean

test-all: test-clock-divider test-reset-controller

test-clock-divider:
	@echo "Running clock_divider tests..."
	pytest test_clock_divider.py -v $(if $(filter 1,$(WAVES)),--waves,)

test-reset-controller:
	@echo "Running reset_controller tests..."
	pytest test_reset_controller.py -v $(if $(filter 1,$(WAVES)),--waves,)

clean:
	rm -rf sim_build __pycache__ .pytest_cache *.vcd *.fst
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete

help:
	@echo "RetroCPU Unit Test Suite"
	@echo ""
	@echo "Targets:"
	@echo "  test-all            - Run all unit tests"
	@echo "  test-clock-divider  - Test clock divider module"
	@echo "  test-reset-controller - Test reset controller module"
	@echo "  clean               - Remove simulation artifacts"
	@echo ""
	@echo "Options:"
	@echo "  WAVES=1             - Generate waveform files (.vcd)"
	@echo "  SIM=<simulator>     - Select simulator (icarus, verilator)"
	@echo ""
	@echo "Examples:"
	@echo "  make test-all WAVES=1"
	@echo "  make test-clock-divider"
