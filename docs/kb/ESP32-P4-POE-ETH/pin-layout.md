# ESP32-P4-ETH Dev Board — Pin Layout Reference

**Board**: Waveshare ESP32-P4-ETH  
**Source**: Board silkscreen image `ESP32-P4-ETH-details-inter-d78f8087f1a1597badd3a1d077c4c057.webp`  
**Verified by user**: Pin 1 = DP/GPIO25, Pin 21 = GPIO48, Pin 3 = GND, Pin 23 = GND

## CRITICAL: Pin Numbering Convention

The board uses a **consecutive (non-Pico) pin layout**:

```
LEFT COLUMN:  Pin  1 (bottom-left)  →  Pin 20 (top-left)
RIGHT COLUMN: Pin 21 (bottom-right) →  Pin 40 (top-right)
```

**Never use Pico-style (dual-row interleaved) numbering for this board.**

### KiCad schematic symbol orientation

The `Custom:J8_Waveshare` symbol in the schematic is oriented to **match the physical board**:
- `pins_right` list runs **40 → 21** (top-to-bottom in symbol) so pin 40 (VBUS) appears at the **top-right** and pin 21 (GPIO48) at the **bottom-right**
- `pins_left` list runs **20 → 1** (top-to-bottom in symbol) so pin 20 (GPIO54) appears at the **top-left** and pin 1 (DP/GPIO25) at the **bottom-left**

This matches the physical Waveshare board where VBUS is at the top-right corner and GPIO48 is at the bottom-right corner.

---

## Left Column — Pins 1–20

| Pin | Signal         | Type           | Notes                        |
|-----|----------------|----------------|------------------------------|
|  1  | DP / GPIO25    | GPIO           | USB D+ / General IO          |
|  2  | DM / GPIO24    | GPIO           | USB D- / General IO          |
|  3  | GND            | Ground         |                              |
|  4  | SDA / GPIO7    | GPIO           | I²C Data                     |
|  5  | SCL / GPIO8    | GPIO           | I²C Clock                    |
|  6  | GPIO2          | GPIO           |                              |
|  7  | GPIO3          | GPIO           |                              |
|  8  | GND            | Ground         |                              |
|  9  | GPIO4          | GPIO           |                              |
| 10  | GPIO5          | GPIO           |                              |
| 11  | GPIO6          | GPIO           |                              |
| 12  | GPIO14         | GPIO           |                              |
| 13  | GND            | Ground         |                              |
| 14  | GPIO15         | GPIO           |                              |
| 15  | GPIO16         | GPIO           |                              |
| 16  | GPIO17         | GPIO           |                              |
| 17  | GPIO18         | GPIO           |                              |
| 18  | GND            | Ground         |                              |
| 19  | GPIO19         | GPIO           |                              |
| 20  | GPIO54         | GPIO           |                              |

---

## Right Column — Pins 21–40

| Pin | Signal         | Type           | Notes                        |
|-----|----------------|----------------|------------------------------|
| 21  | GPIO48         | GPIO           |                              |
| 22  | GPIO47         | GPIO           |                              |
| 23  | GND            | Ground         |                              |
| 24  | GPIO46         | GPIO           |                              |
| 25  | GPIO33         | GPIO           |                              |
| 26  | GPIO32         | GPIO           |                              |
| 27  | GPIO27         | GPIO           |                              |
| 28  | GND            | Ground         |                              |
| 29  | GPIO26         | GPIO           |                              |
| 30  | RUN            | System Control | Chip enable / run control    |
| 31  | GPIO23         | GPIO           |                              |
| 32  | GPIO22         | GPIO           |                              |
| 33  | GND            | Ground         |                              |
| 34  | GPIO21         | GPIO           |                              |
| 35  | GPIO20         | GPIO           |                              |
| 36  | 3V3            | Power          | 3.3 V output                 |
| 37  | EN             | System Control | Module enable                |
| 38  | GND            | Ground         |                              |
| 39  | VSYS           | Power          | System voltage input         |
| 40  | VBUS           | Power          | USB 5 V — **use for 5 V supply** |

---

## Additional Connectors

### USB-C (top of board, labelled on silkscreen)
| Label | Signal |
|-------|--------|
| D-    | USB D- |
| VCC   | Power  |
| D+    | USB D+ |
| GND   | Ground |

### PoE / ETH Pads (bottom of board)
| Side  | Label | Type     | Notes              |
|-------|-------|----------|--------------------|
| Left  | GND   | Ground   |                    |
| Left  | VCC   | Power    |                    |
| Left  | RJ12  | ETH POE  | PoE rail           |
| Right | RJ78  | ETH POE  | PoE rail           |
| Right | RJ45  | ETH POE  | PoE rail           |
| Right | RJ36  | ETH POE  | PoE rail           |

---

## Power Supply Notes

- **5 V supply → use Pin 40 (VBUS)**, not Pin 39 (VSYS).  
  VBUS is the USB 5 V bus rail and is the correct source for regulated 5 V.  
  VSYS is the system input rail and should not be used as a 5 V supply source.
- **3.3 V output → Pin 36 (3V3)**. Do not use this as a power input.
- GND pins: 3, 8, 13, 18, 23, 28, 33, 38 (8 total across both columns).

---

## Pin Type Legend

| Colour in image | Meaning        |
|-----------------|----------------|
| Green           | GPIO           |
| Black           | Ground         |
| Red             | Power          |
| Pink            | System Control |
| Yellow          | ETH POE        |
