# Makefile for example programs

CA65 = ca65
LD65 = ld65

all: hello.bin

hello.o: hello.s
	$(CA65) --cpu 6502 -o hello.o hello.s

hello.bin: hello.o hello.cfg
	$(LD65) -C hello.cfg -o hello.bin hello.o
	@echo "Binary size: $$(wc -c < hello.bin) bytes"
	@ls -lh hello.bin

clean:
	rm -f hello.o hello.bin

.PHONY: all clean
