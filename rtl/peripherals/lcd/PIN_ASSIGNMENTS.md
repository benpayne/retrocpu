# LCD Pin Assignments for Colorlight i5

## HD44780 LCD Connection (4-bit parallel mode)

**PMOD 5A Connector Pins:**

| LCD Signal | FPGA Pin | Description |
|------------|----------|-------------|
| D4         | E5       | Data bit 4 (LSB in 4-bit mode) |
| D5         | F4       | Data bit 5 |
| D6         | F5       | Data bit 6 |
| D7         | E6       | Data bit 7 (MSB) |
| RS         | G5       | Register Select (0=command, 1=data) |
| RW         | D16      | Read/Write (0=write, 1=read) |
| E          | D18      | Enable (falling edge latches data) |

**Total pins: 7**

## LCD Module Pinout (Typical 16-pin HD44780)

```
LCD Pin 1  (VSS)  → Ground
LCD Pin 2  (VDD)  → +5V
LCD Pin 3  (V0)   → Contrast adjust (potentiometer)
LCD Pin 4  (RS)   → FPGA G5
LCD Pin 5  (RW)   → FPGA D16
LCD Pin 6  (E)    → FPGA D18
LCD Pin 7  (D0)   → Not connected (4-bit mode)
LCD Pin 8  (D1)   → Not connected (4-bit mode)
LCD Pin 9  (D2)   → Not connected (4-bit mode)
LCD Pin 10 (D3)   → Not connected (4-bit mode)
LCD Pin 11 (D4)   → FPGA E5
LCD Pin 12 (D5)   → FPGA F4
LCD Pin 13 (D6)   → FPGA F5
LCD Pin 14 (D7)   → FPGA E6
LCD Pin 15 (A)    → +5V (backlight anode, via resistor)
LCD Pin 16 (K)    → Ground (backlight cathode)
```

## Notes

- 4-bit mode uses only D4-D7 pins (saves 4 pins)
- Each byte is sent as two 4-bit nibbles (high nibble first)
- RW pin can be tied to ground if write-only operation is sufficient
- Contrast (V0) typically needs 10kΩ potentiometer between VDD and GND
