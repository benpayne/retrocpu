# Integration Tests

This directory contains integration tests for the RetroGPU monitor firmware.

## test_program_loader.py

Python-based integration test for program loading and I/O configuration features.

### Requirements

```bash
pip install pyserial
```

### Usage

Basic usage (assumes board on /dev/ttyUSB0 at 9600 baud):

```bash
python3 test_program_loader.py
```

With custom port and baud rate:

```bash
python3 test_program_loader.py --port /dev/ttyACM0 --baud 115200
```

Skip XMODEM test (test I/O config only):

```bash
python3 test_program_loader.py --skip-xmodem
```

### What It Tests

1. **I/O Configuration (I command)**:
   - Tests switching between UART, PS/2, and Display modes
   - Validates confirmation messages
   - Tests error handling for invalid modes

2. **XMODEM Binary Upload (L command)**:
   - Uploads a small test binary (hello world program)
   - Verifies XMODEM protocol handshake
   - Tests packet transmission and ACK/NAK responses
   - Confirms successful transfer completion

3. **Program Execution (G command)**:
   - Executes the uploaded program
   - Verifies output ("HELLO WORLD")

### Troubleshooting

#### Permission Denied

Add your user to the dialout group:

```bash
sudo usermod -a -G dialout $USER
```

Then log out and back in.

#### Port Not Found

List available serial ports:

```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

Use the correct port with `--port`:

```bash
python3 test_program_loader.py --port /dev/ttyACM0
```

#### Timeout Waiting for Prompt

The monitor may not be running. Check:

1. Is the FPGA programmed with the SoC bitstream?
2. Is the serial connection working (try `minicom` or `screen`)?
3. Press the reset button on the board

#### XMODEM Transfer Fails

1. Ensure monitor is in UART mode (`I 0 0`)
2. Try slower baud rate (some USB-serial adapters have issues at higher speeds)
3. Check for noise on the serial line

### Example Output

```
Opening serial port /dev/ttyUSB0 at 9600 baud...
Serial port open

Waiting for monitor boot...

M65C02 Monitor v1.0
>
✓ Monitor booted successfully

============================================================
TEST: I/O Configuration (I command)
============================================================

>>> I 0 0
I/O Config: IN=UART, OUT=UART
>
✓ PASS: I 0 0 → IN=UART, OUT=UART

>>> I 1 1
I/O Config: IN=PS2, OUT=Display
>
✓ PASS: I 1 1 → IN=PS2, OUT=Display

...

============================================================
TEST SUMMARY
============================================================
✓ PASS: I/O Config
✓ PASS: XMODEM Upload
✓ PASS: Program Execution

Total: 3/3 tests passed
```

## cocotb Tests

The other test files in this directory use cocotb for HDL simulation:

- `test_xmodem_upload.py` - Full XMODEM protocol simulation
- `test_io_switching.py` - I/O mode switching with simulated peripherals
- `test_program_execution.py` - Program execution verification

These require a full cocotb testbench with the complete SoC simulation.

See the main project README for cocotb setup instructions.
