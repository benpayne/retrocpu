# RetroCPU Monitor Firmware Build System
# Uses cc65 toolchain to build 6502 assembly

# Tools
CA65 = ca65
LD65 = ld65
HEXDUMP = hexdump

# Source files
SRC = monitor.s

# Output files
OBJ = monitor.o
ELF = monitor.elf
BIN = monitor.bin
HEX = monitor.hex

# Linker configuration
# ROM is at $E000-$FFFF (8KB)
LDCONFIG = monitor.cfg

# Assembler flags
ASFLAGS = --cpu 6502

# Linker flags
LDFLAGS = -C $(LDCONFIG)

# Default target
all: $(HEX)

# Assemble source to object
$(OBJ): $(SRC)
	$(CA65) $(ASFLAGS) -o $(OBJ) $(SRC)

# Link object to binary
$(BIN): $(OBJ) $(LDCONFIG)
	$(LD65) $(LDFLAGS) -o $(BIN) $(OBJ)

# Convert binary to hex format for Verilog $readmemh
$(HEX): $(BIN)
	@echo "Converting binary to hex..."
	@# Create hex file with one byte per line in ASCII hex
	@hexdump -v -e '1/1 "%02x\n"' $(BIN) > $(HEX)
	@echo "Monitor firmware size: $$(wc -c < $(BIN)) bytes"
	@echo "Hex file: $(HEX)"

# Clean build artifacts
clean:
	rm -f $(OBJ) $(BIN) $(HEX)

# Display info
info:
	@echo "Monitor Firmware Build System"
	@echo "Source: $(SRC)"
	@echo "Output: $(HEX)"
	@if [ -f $(HEX) ]; then \
		echo "Size: $$(wc -c < $(BIN)) bytes"; \
		echo "Lines: $$(wc -l < $(HEX))"; \
	fi

.PHONY: all clean info
