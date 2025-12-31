# Feature Reintegration Status - 2025-12-28

## What We Have (Working)
✅ **System Boot** - Stable, no crashes
✅ **M65C02 CPU** - MC=5 timing working
✅ **32KB RAM** - $0000-$7FFF
✅ **16KB BASIC ROM** - $8000-$BFFF (instantiated but not accessible)
✅ **8KB Monitor ROM** - $E000-$FFFF
✅ **UART TX** - Output working perfectly
✅ **UART RX** - Input working perfectly
✅ **Monitor Commands** - H/E/D parsed (E/D not implemented yet)

## What We Lost During Boot Debug
❌ **BASIC Access** - Monitor shows "G - Go to BASIC" but command not implemented
❌ **LCD Integration** - Chip select exists but no module instantiated
❌ **PS/2 Controller** - Chip select exists but no module instantiated
❌ **GPU** - Files exist but not integrated
❌ **Monitor E/D Commands** - Parsed but not functional

## File Status

### Hardware (RTL)
- `soc_top.v`:
  - Has: CPU, RAM, ROM (BASIC/Monitor), UART, reset
  - Missing: LCD module, PS/2 module, GPU module
  - Has dangling: `lcd_cs`, `ps2_cs` signals

- `address_decoder.v`:
  - ✅ Updated: UART at 0xC000-0xC00F, GPU at 0xC010-0xC01F
  - ⚠️ Outdated: LCD/PS/2 still reference full pages (need updating)

### Firmware
- `monitor.s`:
  - ✅ Has: CHROUT, CHRIN, command parser for H/E/D
  - ❌ Missing: G command implementation
  - ❌ Missing: E command implementation (examine memory)
  - ❌ Missing: D command implementation (deposit memory)

- `basic_rom.hex`:
  - ✅ Exists and loaded into BASIC ROM
  - ❌ No way to jump to it ($8000 entry point)

## Systematic Reintegration Plan

### Step 1: Validate Current Monitor Commands (E/D/H)
**Goal:** Create Python test script to verify monitor commands work correctly

**Tasks:**
- [ ] Write Python script to test:
  - H command → displays help
  - E XXXX command → examines memory at address (stub response)
  - D XXXX YY command → deposits value to memory (stub response)
  - Unknown command → error message
- [ ] Commit: "test: Add validation script for monitor commands"

**Success Criteria:** Script passes, documents current behavior

---

### Step 2: Add BASIC Support (G Command)
**Goal:** Restore ability to jump to BASIC from monitor

**Tasks:**
- [ ] Implement G command in monitor.s
  - Parse 'G' command
  - Jump to $8000 (BASIC entry point)
- [ ] Test BASIC boots and runs
- [ ] Document BASIC memory map
- [ ] Commit: "feat: Add G command to jump to BASIC"

**Success Criteria:** Can type "G" in monitor and get BASIC prompt

---

### Step 3: Test BASIC Functionality
**Goal:** Verify BASIC interpreter works correctly

**Tasks:**
- [ ] Test basic commands:
  - PRINT "HELLO"
  - LET A=10: PRINT A
  - FOR/NEXT loops
  - INPUT (uses CHRIN)
- [ ] Create test script for BASIC smoke tests
- [ ] Commit: "test: Add BASIC functionality tests"

**Success Criteria:** Can run simple BASIC programs

---

### Step 4: Integrate LCD
**Goal:** Add LCD module and test memory-mapped I/O

**Tasks:**
- [ ] Check if LCD module files exist
- [ ] Update address_decoder.v for LCD (0xC100-0xC1FF)
- [ ] Add LCD module to soc_top.v
- [ ] Add LCD pins to LPF file
- [ ] Test from BASIC: POKE &HC100, 65 (write 'A')
- [ ] Test from monitor: E C100 (examine LCD status)
- [ ] Test from monitor: D C100 41 (deposit 'A' to LCD)
- [ ] Commit: "feat: Integrate LCD with memory-mapped I/O"

**Success Criteria:** Can write to LCD from BASIC and monitor

---

### Step 5: Integrate PS/2 Controller
**Goal:** Add PS/2 keyboard input

**Tasks:**
- [ ] Check PS/2 controller files (submodule?)
- [ ] Update address_decoder.v for PS/2 (0xC200-0xC2FF)
- [ ] Add PS/2 module to soc_top.v
- [ ] Add PS/2 pins to LPF file
- [ ] Test from monitor: E C200 (examine PS/2 status)
- [ ] Test from monitor: E C201 (read scan code)
- [ ] Create test for reading keystrokes
- [ ] Commit: "feat: Integrate PS/2 keyboard controller"

**Success Criteria:** Can read PS/2 scan codes via D/E commands

---

### Step 6: Add Input Source Selection
**Goal:** Monitor can read from UART or PS/2

**Tasks:**
- [ ] Modify CHRIN to check both UART and PS/2
- [ ] Priority: UART first, then PS/2 (or configurable)
- [ ] Test keyboard input in monitor
- [ ] Test keyboard input in BASIC
- [ ] Commit: "feat: Add PS/2 keyboard input to monitor"

**Success Criteria:** Can type commands via keyboard or serial

---

### Step 7: Integrate GPU
**Goal:** Add HDMI character display

**Tasks:**
- [ ] Add GPU PLL for pixel/TMDS clocks
- [ ] Add gpu_top module to soc_top.v
- [ ] Add HDMI pins to LPF file
- [ ] Test from monitor: E C010 (examine GPU status)
- [ ] Test from monitor: D C010 41 (write 'A' to GPU)
- [ ] Test from BASIC: POKE &HC010, 65
- [ ] Verify HDMI output on monitor
- [ ] Commit: "feat: Integrate GPU with HDMI output"

**Success Criteria:** Can display text on HDMI monitor

---

## Testing Strategy

Each step includes:
1. **Unit test** - Test the new feature in isolation
2. **Integration test** - Verify it works with existing features
3. **Regression test** - Ensure nothing broke
4. **Git commit** - Save working state

## Rollback Strategy

At each step:
- If integration fails, can revert to previous commit
- Can disable new feature via chip select
- Can test new feature independently

## Current Commit
71a722b - Address decoder updated, ready for Step 1

