# RetroCPU Firmware Test Suite

Pytest-based test suite for RetroCPU monitor and BASIC firmware.

## Overview

This test suite validates the firmware running on the RetroCPU FPGA system via UART communication. It includes tests for:

- **Monitor Commands**: E (examine), D (deposit), G (go to BASIC)
- **BASIC Interpreter**: Arithmetic, variables, control flow, programs
- **Memory Map**: RAM, ROM, zero page, stack page
- **System Integration**: Boot process, reset, error handling

## Prerequisites

### Hardware Setup

1. **FPGA Programmed**: RetroCPU bitstream must be loaded on the FPGA
2. **Serial Connection**: USB-to-serial adapter connected to UART pins
3. **Serial Port**: Device accessible (typically `/dev/ttyACM0` or `/dev/ttyUSB0`)
4. **Baud Rate**: 9600 baud (default)
5. **JTAG Programmer**: CMSIS-DAP programmer for FPGA reset (optional but recommended)

### Software Dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Or install from project root:

```bash
cd /opt/wip/retrocpu
pip install -r tests/firmware/requirements.txt
```

## Running Tests

### Quick Start

Run all tests with default settings:

```bash
cd /opt/wip/retrocpu/tests/firmware
pytest
```

### Common Options

**Specify serial port:**
```bash
pytest --port=/dev/ttyUSB0
```

**Specify baud rate:**
```bash
pytest --baud=115200
```

**Run specific test file:**
```bash
pytest test_monitor.py
pytest test_basic.py
```

**Run specific test class:**
```bash
pytest test_monitor.py::TestExamineCommand
pytest test_basic.py::TestBasicArithmetic
```

**Run specific test:**
```bash
pytest test_monitor.py::TestExamineCommand::test_examine_rom_start
```

**Skip slow tests:**
```bash
pytest -m "not slow"
```

**Verbose output:**
```bash
pytest -v
```

**Show test output (print statements):**
```bash
pytest -s
```

**Stop on first failure:**
```bash
pytest -x
```

### Environment Variables

Set default serial port and baud rate:

```bash
export RETROCPU_PORT=/dev/ttyACM0
export RETROCPU_BAUD=9600
pytest
```

### Skip Hardware Tests

If hardware is not available:

```bash
pytest --skip-hardware
```

This will skip all tests that require serial connection.

## FPGA Reset for Testing

Some tests (like the G command that starts BASIC) leave the system in a state where it cannot return to the monitor prompt. To solve this, the test suite includes **automatic FPGA reset capability**.

### How FPGA Reset Works

The `fpga_reset` fixture reprograms the FPGA with the existing bitstream (takes ~5-10 seconds):

```python
def test_something(fpga_reset):
    # Test that changes system state
    # ...

    # Reset FPGA to clean state
    fpga_reset()
```

The reset function uses `openFPGALoader -b colorlight-i5 soc_top.bit` to reprogram the FPGA via the CMSIS-DAP interface.

### Configuration

Set the bitstream path via environment variable (optional):

```bash
export RETROCPU_BITSTREAM=/path/to/soc_top.bit
```

Default: `../../build/soc_top.bit` (relative to test directory)

## Test Structure

### Test Files

- **`test_monitor.py`**: Monitor command tests
  - `TestMonitorBasic`: Basic monitor functionality
  - `TestExamineCommand`: E (examine) command
  - `TestDepositCommand`: D (deposit) command
  - `TestGoCommand`: G (go to BASIC) command
  - `TestMonitorRobustness`: Error handling
  - `TestMemoryMap`: Memory map validation
  - `TestMemoryStressTest`: Stress tests

- **`test_basic.py`**: BASIC interpreter tests
  - `TestBasicStartup`: Initialization
  - `TestBasicArithmetic`: Math operations
  - `TestBasicVariables`: Variable storage
  - `TestBasicPrograms`: Program entry and execution
  - `TestBasicControlFlow`: FOR, GOTO, GOSUB, IF-THEN
  - `TestBasicStrings`: String handling
  - `TestBasicFunctions`: Built-in functions
  - `TestBasicComplexPrograms`: Integration tests
  - `TestBasicEditing`: NEW, LIST, line editing
  - `TestBasicStressTest`: Performance tests

### Fixtures

Defined in `conftest.py`:

- **`serial_port`**: Opens serial connection to RetroCPU
- **`monitor`**: Provides `MonitorHelper` for monitor interaction
- **`basic`**: Provides `BasicHelper` for BASIC interaction (starts BASIC)

### Markers

- **`@pytest.mark.slow`**: Marks long-running tests (excluded with `-m "not slow"`)
- **`@pytest.mark.hardware`**: Marks tests requiring hardware (auto-applied to all)

## Example Test Sessions

### Validate Monitor Commands

```bash
pytest test_monitor.py -v
```

Expected output:
```
test_monitor.py::TestExamineCommand::test_examine_rom_start PASSED
test_monitor.py::TestExamineCommand::test_examine_ram PASSED
test_monitor.py::TestDepositCommand::test_deposit_to_ram PASSED
test_monitor.py::TestDepositCommand::test_deposit_and_verify PASSED
...
```

### Validate BASIC Functionality

```bash
pytest test_basic.py::TestBasicArithmetic -v
```

### Full Test Suite (excluding slow tests)

```bash
pytest -v -m "not slow"
```

### Generate HTML Report

```bash
pytest --html=report.html --self-contained-html
```

## Troubleshooting

### Serial Port Permission Denied

Add user to dialout group:

```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

Or run with sudo (not recommended):

```bash
sudo pytest --port=/dev/ttyACM0
```

### Serial Port Not Found

List available ports:

```bash
ls /dev/tty*
```

Common ports:
- `/dev/ttyACM0` - CMSIS-DAP, Arduino
- `/dev/ttyUSB0` - FTDI, CH340
- `/dev/ttyS0` - Built-in serial

### Tests Timeout

Increase timeout in `pytest.ini` or:

```bash
pytest --timeout=600
```

### FPGA Not Responding

1. Verify FPGA is programmed: Check LEDs
2. Press reset button on FPGA
3. Reconnect serial cable
4. Check baud rate matches firmware (default: 9600)

### Tests Fail Intermittently

Serial timing issues - try:
1. Increase `CHAR_DELAY` in `conftest.py` (default 0.05s)
2. Use lower baud rate: `--baud=9600`
3. Reset FPGA before test run

## Writing New Tests

### Monitor Command Test Example

```python
def test_my_monitor_feature(monitor):
    """Test description."""
    # Deposit value
    result = monitor.deposit('0600', 'FF')
    assert result, "Deposit failed"

    # Verify
    value = monitor.examine('0600')
    assert value == 'FF', f"Expected FF, got {value}"
```

### BASIC Test Example

```python
def test_my_basic_feature(basic):
    """Test description."""
    basic.new()
    basic.enter_program([
        '10 X=42',
        '20 PRINT X',
        '30 END'
    ])

    output = basic.run_program()
    assert '42' in output, f"Expected 42, got: {output}"
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Firmware Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r tests/firmware/requirements.txt
      - run: pytest tests/firmware/ --skip-hardware
```

## Contributing

When adding new firmware features:

1. Write tests first (TDD)
2. Implement feature
3. Verify all tests pass
4. Update documentation

## Test Coverage Goals

- **Monitor**: 100% command coverage
- **BASIC**: Core functionality (arithmetic, variables, control flow)
- **Memory**: All address ranges validated
- **Integration**: Boot to BASIC to program execution

## References

- Monitor firmware: `/opt/wip/retrocpu/firmware/monitor/monitor.s`
- BASIC source: `/opt/wip/retrocpu/firmware/basic/`
- Hardware tests: Run on Colorlight i5 FPGA board
- Simulation tests: Cocotb tests in `/opt/wip/retrocpu/tests/unit/`
