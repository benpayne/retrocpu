# Clock and Reset System Documentation

## Overview

The clock and reset system provides stable timing and initialization for the 6502 microcomputer. It consists of two modules:

1. **clock_divider.v** - Divides 25 MHz system clock to 1 MHz CPU clock
2. **reset_controller.v** - Generates clean reset signal from power-on and button press

## Design Philosophy

### Single Clock Domain
The system uses a **single clock domain** design with clock enables rather than derived clocks. This approach:
- Simplifies timing analysis and closure
- Avoids clock domain crossing issues
- Makes the design more reliable and educational
- Follows FPGA best practices

### Synchronous Reset
All resets are **synchronous** (registered on clock edge):
- Prevents metastability issues
- Ensures clean reset release
- Simplifies timing constraints
- Matches modern FPGA design practices

## Module: clock_divider.v

### Purpose
Divides the 25 MHz system clock down to 1 MHz for the 6502 CPU using a clock enable signal.

### Interface

```verilog
module clock_divider #(
    parameter DIVIDE_RATIO = 25
) (
    input  wire clk,         // System clock (25 MHz)
    input  wire rst,         // Synchronous reset (active high)
    output reg  clk_enable   // Clock enable pulse (1 cycle every DIVIDE_RATIO)
);
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| DIVIDE_RATIO | 25 | Clock division ratio (25 MHz / 25 = 1 MHz) |

### Ports

| Port | Direction | Width | Description |
|------|-----------|-------|-------------|
| clk | Input | 1 | System clock (25 MHz from P3 pin) |
| rst | Input | 1 | Synchronous reset (active-high) |
| clk_enable | Output | 1 | Clock enable pulse (high for 1 cycle every 25 clocks) |

### Operation

1. **Counter**: Internal counter increments on each clock cycle
2. **Enable Pulse**: When counter reaches DIVIDE_RATIO-1, clk_enable pulses high for 1 cycle
3. **CPU Gating**: CPU operations only proceed when clk_enable is high
4. **Reset Behavior**: Counter resets to 0, clk_enable goes low

### Timing Diagram

```
clk          : _/‾\_/‾\_/‾\_/‾\_/‾\_/‾\_/‾\_/‾\_/‾\_/‾\_/‾\_/‾\_/‾\_/‾\...
counter      : 0   1   2   3   4 ...  23  24  0   1   2   3   4 ...
clk_enable   : _____________________________/‾\_____________________...
CPU operation:                              [Execute]
```

### Usage Example

```verilog
// Instantiate clock divider
wire clk_enable;
clock_divider #(
    .DIVIDE_RATIO(25)
) clk_div (
    .clk(clk_25mhz),
    .rst(system_rst),
    .clk_enable(clk_enable)
);

// Use clock enable to gate CPU
wire cpu_clk = clk_25mhz && clk_enable;  // Don't do this!
// Instead:
cpu_6502 cpu (
    .clk(clk_25mhz),
    .clk_enable(clk_enable),  // Pass enable signal
    .rst(system_rst),
    // ...
);
```

**Important**: Never use `clk && clk_enable` to create a derived clock. Always pass `clk_enable` as a separate signal and use it inside the module to gate operations.

### Resource Usage

- **LUTs**: ~5-10 (counter + enable logic)
- **Registers**: 5 (counter bits: $\lceil \log_2(25) \rceil = 5$)
- **Fmax**: >200 MHz (simple counter, no timing issues)

### Test Coverage

See `tests/unit/test_clock_divider.py` for complete test suite:
- ✅ Basic functionality (enable pulse generation)
- ✅ Correct 25:1 division ratio
- ✅ Single-cycle pulse width
- ✅ Reset behavior
- ✅ Continuous operation over extended period

## Module: reset_controller.v

### Purpose
Generates a clean, synchronous reset signal from power-on and button press with debouncing.

### Interface

```verilog
module reset_controller #(
    parameter POWER_ON_CYCLES = 100,
    parameter DEBOUNCE_CYCLES = 10,
    parameter RESET_MIN_CYCLES = 50
) (
    input  wire clk,              // System clock (25 MHz)
    input  wire reset_button_n,   // Reset button (active-low, from T1 pin)
    output reg  rst               // Synchronous reset output (active-high)
);
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| POWER_ON_CYCLES | 100 | Power-on reset duration (4 μs @ 25 MHz) |
| DEBOUNCE_CYCLES | 10 | Button debounce time (400 ns @ 25 MHz) |
| RESET_MIN_CYCLES | 50 | Minimum reset pulse width (2 μs @ 25 MHz) |

### Ports

| Port | Direction | Width | Description |
|------|-----------|-------|-------------|
| clk | Input | 1 | System clock (25 MHz) |
| reset_button_n | Input | 1 | Reset button from T1 pin (active-low, has pull-up) |
| rst | Output | 1 | Synchronous reset output (active-high) |

### Operation

The reset controller implements a state machine with four states:

#### State Machine

```
POWER_ON ──[counter >= 100]──> IDLE
   ^                              │
   │                              │ [button pressed]
   │                              v
   └─────────────────────── RESET_WAIT
                                  │ [debounced]
                                  v
                             RESET_HOLD ──[button released && counter >= 50]──> IDLE
                                  ^                                                │
                                  └────────────────[button still pressed]─────────┘
```

#### State Descriptions

1. **POWER_ON**: Initial state after FPGA configuration
   - Holds `rst = 1` for POWER_ON_CYCLES
   - Ensures all flip-flops are initialized
   - Transitions to IDLE after counter expires

2. **IDLE**: Normal operation
   - `rst = 0` (system running)
   - Monitors button input
   - Transitions to RESET_WAIT on button press

3. **RESET_WAIT**: Button debouncing
   - `rst = 0` (reset not yet asserted)
   - Waits for button to be stable low for DEBOUNCE_CYCLES
   - If button released early, returns to IDLE (bounce filtered)
   - If button stable, transitions to RESET_HOLD

4. **RESET_HOLD**: Reset asserted
   - `rst = 1` (system in reset)
   - Holds reset for at least RESET_MIN_CYCLES
   - Continues holding if button still pressed
   - Returns to IDLE when button released and minimum time elapsed

### Button Input Synchronization

To prevent metastability from asynchronous button input:

```verilog
reg button_sync_1;  // First stage synchronizer
reg button_sync_2;  // Second stage synchronizer

always @(posedge clk) begin
    button_sync_1 <= reset_button_n;
    button_sync_2 <= button_sync_1;
end

wire button_pressed = ~button_sync_2;  // Active-high internal signal
```

This 2-flip-flop synchronizer:
- Reduces probability of metastability to negligible levels
- Adds 2 clock cycles of latency (80 ns @ 25 MHz, imperceptible to humans)
- Standard practice for asynchronous inputs

### Timing Characteristics

| Event | Duration | Cycles @ 25 MHz |
|-------|----------|-----------------|
| Power-on reset | 4 μs | 100 |
| Button debounce | 400 ns | 10 |
| Minimum reset pulse | 2 μs | 50 |
| Button sync delay | 80 ns | 2 |

### Hardware Connection

Connect to Colorlight i5 board:

```
FIRE 2 Button (T1 pin) ──> reset_button_n input
    │
    ├─── 10kΩ pull-up to VCC (internal to FPGA, configured in .lpf)
    │
    └─── Button to GND (active-low)
```

LPF configuration:
```tcl
LOCATE COMP "reset_button_n" SITE "T1";
IOBUF PORT "reset_button_n" PULLMODE=UP IO_TYPE=LVCMOS33;
```

### Usage Example

```verilog
// Instantiate reset controller
wire system_rst;
reset_controller #(
    .POWER_ON_CYCLES(100),
    .DEBOUNCE_CYCLES(10),
    .RESET_MIN_CYCLES(50)
) rst_ctrl (
    .clk(clk_25mhz),
    .reset_button_n(fire2_button),  // From T1 pin
    .rst(system_rst)
);

// Use system_rst to reset all modules
cpu_6502 cpu (
    .clk(clk_25mhz),
    .rst(system_rst),  // Active-high synchronous reset
    // ...
);
```

### Resource Usage

- **LUTs**: ~20-30 (state machine + counter + synchronizers)
- **Registers**: 12 (state[2], counter[8], sync[2])
- **Fmax**: >200 MHz (simple state machine)

### Test Coverage

See `tests/unit/test_reset_controller.py` for complete test suite:
- ✅ Power-on reset assertion and duration
- ✅ Button press generates reset
- ✅ Button debouncing filters glitches
- ✅ Minimum reset pulse width enforcement
- ✅ Synchronous output (no mid-cycle changes)
- ✅ Extended button press behavior

## System Integration

### Top-Level Wiring

```verilog
module soc_top (
    input wire clk_25mhz,        // P3 pin
    input wire reset_button_n,   // T1 pin (FIRE 2)
    // ... other ports
);

    // Reset controller
    wire system_rst;
    reset_controller rst_ctrl (
        .clk(clk_25mhz),
        .reset_button_n(reset_button_n),
        .rst(system_rst)
    );

    // Clock divider
    wire cpu_clk_enable;
    clock_divider clk_div (
        .clk(clk_25mhz),
        .rst(system_rst),
        .clk_enable(cpu_clk_enable)
    );

    // CPU
    cpu_6502 cpu (
        .clk(clk_25mhz),
        .clk_enable(cpu_clk_enable),
        .rst(system_rst),
        // ...
    );

    // Memory and peripherals (use system_rst)
    // ...

endmodule
```

## Design Decisions and Rationale

### Why Clock Enable Instead of Derived Clock?

**Derived clock approach (NOT recommended)**:
```verilog
wire cpu_clk = clk_25mhz && clk_enable;  // Creates gated clock
// Problems:
// - Clock skew issues
// - Difficult timing analysis
// - Clock tree not optimized for gated clocks
// - Risk of glitches
```

**Clock enable approach (RECOMMENDED)**:
```verilog
always @(posedge clk_25mhz) begin
    if (clk_enable) begin
        // CPU operations
    end
end
// Benefits:
// - Single clock domain
// - Clean timing analysis
// - No clock skew
// - FPGA tools optimize well
```

### Why Synchronous Reset?

**Asynchronous reset issues**:
- Reset release timing not controlled
- Risk of partial state initialization
- Difficult to meet timing for reset distribution

**Synchronous reset benefits**:
- Reset release synchronized to clock
- All flip-flops initialize on same clock edge
- Easier timing analysis
- Standard practice for modern FPGAs

### Why Button Debouncing?

Mechanical buttons produce electrical bounce:
```
Button press:    \_____/\_____/\___________
                 ↑ glitches before stable low

Without debounce: Multiple reset pulses (bad!)
With debounce:    Single clean reset pulse (good!)
```

## Testing and Verification

### Running Tests

```bash
# Test clock divider
cd tests/unit
pytest test_clock_divider.py -v

# Test reset controller
pytest test_reset_controller.py -v

# Test with waveforms
pytest test_clock_divider.py -v --waves
gtkwave sim_build/clock_divider.vcd
```

### Simulation Waveforms

Clock divider waveforms show:
- Counter incrementing 0 → 24
- clk_enable pulsing high for 1 cycle at counter=24
- Consistent 25:1 ratio

Reset controller waveforms show:
- Power-on reset held for 100 cycles
- Button bounces filtered by debounce logic
- Clean reset pulses with minimum width

## Related Documentation

- **Pin Constraints**: `colorlight_i5.lpf` (clock on P3, button on T1)
- **Test Suite**: `tests/unit/test_clock_divider.py`, `tests/unit/test_reset_controller.py`
- **Integration**: `docs/modules/system_integration.md` (to be written)
- **6502 CPU**: `docs/modules/cpu.md` (to be written)

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-16 | 1.0 | Initial implementation and documentation |
