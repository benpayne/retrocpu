# ============================================================================
# Makefile for BASIC ROM (OSI BASIC from mist64/msbasic)
#
# This Makefile builds Microsoft BASIC (OSI variant) for the RetroCPU system.
# It clones the mist64/msbasic repository, applies RetroCPU-specific
# configuration, assembles with ca65, links with ld65, and converts to
# hex format for Verilog $readmemh().
#
# Usage:
#   make        - Build basic_rom.hex (clones repo if needed)
#   make clean  - Remove build artifacts
#   make distclean - Remove build artifacts and cloned repository
# ============================================================================

AS = ca65
LD = ld65
PYTHON = python3

# Paths
MSBASIC_DIR = msbasic
MSBASIC_SRC = $(MSBASIC_DIR)/msbasic.s
DEFINES_RETROCPU = defines_retrocpu.s
LINKER_CFG = retrocpu_osi.cfg

# Build targets
TARGET = osi_retrocpu
HEX = basic_rom.hex

.PHONY: all clean distclean check-repo

all: $(HEX)

# Check if msbasic repository exists, clone if not
check-repo:
	@if [ ! -d "$(MSBASIC_DIR)" ]; then \
		echo "Cloning mist64/msbasic repository..."; \
		git clone https://github.com/mist64/msbasic.git $(MSBASIC_DIR); \
		echo "Repository cloned successfully."; \
	fi

# Copy our custom files into msbasic directory
$(MSBASIC_DIR)/defines_retrocpu.s: $(DEFINES_RETROCPU) | check-repo
	@echo "Copying defines_retrocpu.s to msbasic directory..."
	cp $(DEFINES_RETROCPU) $(MSBASIC_DIR)/

$(MSBASIC_DIR)/retrocpu_osi.cfg: $(LINKER_CFG) | check-repo
	@echo "Copying retrocpu_osi.cfg to msbasic directory..."
	cp $(LINKER_CFG) $(MSBASIC_DIR)/

# Patch defines.s to include retrocpu variant (if not already patched)
$(MSBASIC_DIR)/defines.s: | check-repo
	@if ! grep -q "retrocpu" $(MSBASIC_DIR)/defines.s; then \
		echo "Patching defines.s to add retrocpu variant..."; \
		sed -i '1i.if .def(retrocpu)\nRETROCPU := 1\n.include "defines_retrocpu.s"\n.elseif' $(MSBASIC_DIR)/defines.s; \
		sed -i 's/^\.if \.def(cbmbasic1)/.def(cbmbasic1)/' $(MSBASIC_DIR)/defines.s; \
		echo "Patch applied successfully."; \
	fi

# Build object file
$(TARGET).o: $(MSBASIC_DIR)/defines_retrocpu.s $(MSBASIC_DIR)/retrocpu_osi.cfg $(MSBASIC_DIR)/defines.s
	@echo "Assembling OSI BASIC with ca65..."
	cd $(MSBASIC_DIR) && $(AS) --cpu 6502 -D retrocpu msbasic.s -o ../$(TARGET).o
	@echo "Assembly complete."

# Link binary
$(TARGET).bin: $(TARGET).o
	@echo "Linking with ld65..."
	$(LD) -C $(MSBASIC_DIR)/retrocpu_osi.cfg $(TARGET).o -o $@ -Ln $(TARGET).lbl
	@echo "Link complete. Binary size: $$(stat -c%s $@) bytes (max 16384)"
	@if [ $$(stat -c%s $@) -gt 16384 ]; then \
		echo "ERROR: Binary too large! Must be <= 16384 bytes."; \
		exit 1; \
	fi

# Convert to hex format for Verilog $readmemh
$(HEX): $(TARGET).bin
	@echo "Converting binary to hex format..."
	@$(PYTHON) -c "import sys; data = open('$<', 'rb').read(); \
	               [print(format(b, '02x')) for b in data]" > $@
	@echo "Hex file created: $@"
	@echo "Lines in hex file: $$(wc -l < $@)"

# Clean build artifacts
clean:
	rm -f $(TARGET).o $(TARGET).bin $(TARGET).lbl $(HEX)
	rm -f $(MSBASIC_DIR)/defines_retrocpu.s
	rm -f $(MSBASIC_DIR)/retrocpu_osi.cfg
	@echo "Build artifacts cleaned."

# Remove everything including cloned repository
distclean: clean
	rm -rf $(MSBASIC_DIR)
	@echo "All files removed (including msbasic repository)."

# Help target
help:
	@echo "RetroCPU BASIC Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all (default) - Build basic_rom.hex from OSI BASIC"
	@echo "  clean         - Remove build artifacts"
	@echo "  distclean     - Remove build artifacts and msbasic repository"
	@echo "  help          - Show this help message"
	@echo ""
	@echo "Output:"
	@echo "  basic_rom.hex - Hex file for Verilog $$readmemh (16KB)"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - ca65 assembler (from cc65 package)"
	@echo "  - ld65 linker (from cc65 package)"
	@echo "  - python3"
	@echo "  - git (for cloning repository)"
