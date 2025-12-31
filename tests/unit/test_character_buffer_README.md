# Character Buffer Unit Tests

This test suite verifies the `character_buffer.v` module, which implements a dual-port RAM for storing ASCII character codes for the DVI character display.

## Module Under Test

**File**: `rtl/video/character_buffer.v` (to be implemented)

**Interface**:
```verilog
module character_buffer(
    // CPU write port (system clock domain)
    input  wire        clk_cpu,
    input  wire [10:0] addr_write,      // 0-1199 (40-col) or 0-2399 (80-col)
    input  wire [7:0]  data_write,
    input  wire        we,              // Write enable

    // Video read port (pixel clock domain)
    input  wire        clk_video,
    input  wire [10:0] addr_read,
    output wire [7:0]  data_read
);
```

## Running Tests

### Run all tests:
```bash
cd tests/unit
pytest test_character_buffer.py -v
```

### Run with waveforms (for debugging):
```bash
pytest test_character_buffer.py -v --waves
```

### Run specific test:
```bash
pytest test_character_buffer.py::test_basic_write_read -v
```

### Using the convenience script:
```bash
./run_character_buffer_test.sh           # Normal run
./run_character_buffer_test.sh --waves   # With waveforms
```

## Test Coverage

### 1. Basic Operations
- **test_basic_write_read**: Write a single character and read it back
- **test_multiple_writes_reads**: Write multiple characters at different addresses and verify

### 2. Display Mode Support
- **test_40col_addressing**: Test full 40-column mode range (0-1199, 40x30 chars)
- **test_80col_addressing**: Test 80-column mode range (0-2399, 80x30 chars)

### 3. Dual-Port RAM Behavior
- **test_simultaneous_read_write**: Verify simultaneous read/write on different addresses
- **test_read_write_same_address**: Test reading and writing to the same address
- **test_clock_domain_crossing**: Verify operation with different clock domains (50 MHz CPU, ~74 MHz video)

### 4. Control Logic
- **test_write_enable_control**: Verify writes only occur when WE is asserted

### 5. Stress Testing
- **test_random_access_pattern**: Random read/write pattern (50 operations)
- **test_full_screen_write**: Write and verify entire 40-column screen (1200 bytes)

### 6. Boundary Conditions
- **test_address_boundaries**: Test behavior at critical boundaries (0, 255, 256, 1199, 1200, 2399, etc.)

## Expected Behavior

### Initial State
- Tests will **FAIL** initially because `character_buffer.v` doesn't exist yet
- This is expected for TDD (Test-Driven Development)

### After Implementation
- All tests should pass once the module is correctly implemented
- Tests verify:
  - Correct dual-port RAM behavior
  - Independent clock domain operation
  - Full address range support for both display modes
  - Data integrity across read/write operations

## Design Requirements Verified

From spec.md:
- Dual-port RAM with independent read/write ports
- Write port: System clock domain (clk_cpu)
- Read port: Video clock domain (clk_video)
- Address range: 11 bits (0-2047, but only 0-2399 used)
- Data width: 8 bits (ASCII character codes)
- Support for 40-column mode (1200 bytes: 40 cols × 30 rows)
- Support for 80-column mode (2400 bytes: 80 cols × 30 rows)

## Test Data Patterns

Tests use various data patterns:
- ASCII printable characters (0x20-0x7E)
- Known test values ('A', 'B', 'C', etc.)
- Address-derived patterns for verification
- Random patterns for stress testing

## Clock Domains

- **CPU Clock**: 50 MHz (20ns period) - Write port
- **Video Clock**: ~74.25 MHz (13ns period) - Read port (720p pixel clock)

Different clock frequencies verify the dual-port RAM works correctly across clock domains.

## Notes

- Tests include 2-cycle delays after reads to account for RAM latency
- Write enable must be asserted for writes to occur
- Tests verify data integrity after simultaneous read/write operations
- Random tests use fixed seed (12345) for reproducibility
