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

---

## Daughter Board Signal Assignments (PoE FanController PCB)

### Right Column (Pins 21–40) — Fan + Power signals

| Pin | GPIO | Signal | Direction | Connected to |
|-----|------|--------|-----------|--------------|
| 21  | GPIO48 | **FAN4_PWM**  | Output | J5 pin 4, via D5/R12 PWM LED |
| 22  | GPIO47 | **FAN4_TACH** | Input  | R8 TACH pull-up (10kΩ to +3V3) |
| 23  | GND    | GND           | —      | — |
| 24  | GPIO46 | **FAN3_PWM**  | Output | J4 pin 4, via D4/R11 PWM LED |
| 25  | GPIO33 | **FAN3_TACH** | Input  | R7 TACH pull-up (10kΩ to +3V3) |
| 26  | GPIO32 | NC            | —      | EMAC_RXD0 — do not use |
| 27  | GPIO27 | NC            | —      | — |
| 28  | GND    | GND           | —      | — |
| 29  | GPIO26 | NC            | —      | — |
| 30  | RUN    | NC            | —      | System control — reserved |
| 31  | GPIO23 | **FAN2_PWM**  | Output | J3 pin 4, via D3/R10 PWM LED |
| 32  | GPIO22 | **FAN2_TACH** | Input  | R6 TACH pull-up (10kΩ to +3V3) |
| 33  | GND    | GND           | —      | — |
| 34  | GPIO21 | **FAN1_PWM**  | Output | J2 pin 4, via D2/R9 PWM LED |
| 35  | GPIO20 | **FAN1_TACH** | Input  | R5 TACH pull-up (10kΩ to +3V3) |
| 36  | +3V3   | **+3V3**      | Power  | TACH pull-ups R5-R8, sensor VCC |
| 37  | EN     | NC            | —      | Module enable — reserved |
| 38  | GND    | GND           | —      | — |
| 39  | VSYS   | NC            | —      | Do NOT use for 5V supply |
| 40  | VBUS   | **+5V**       | Power  | U_BOOST IN+ (5V→12V boost input) |

> ⚠️ PWM and TACH are on **adjacent pins per fan** — PWM on the lower-numbered pin, TACH on the higher. This is the result of a board layout reshuffle (2026-06-14) that required swapping from the original TACH-low/PWM-high order.

### Left Column (Pins 1–20) — Sensor + LED signals

| Pin | GPIO | Signal | Direction | Connected to |
|-----|------|--------|-----------|--------------|
| 6   | GPIO2  | DS18B20_DATA | Bidirectional | R14 pull-up (4.7kΩ to +3V3), J6 |
| 10  | GPIO5  | DHT11_DATA   | Input         | HUM1 pin 2 |
| 11  | GPIO6  | PROBE_LED    | Output        | R15 → LED6 |
| 16  | GPIO17 | PROG_LED     | Output        | R13 → LED2 |
| 17  | GPIO18 | PWR_LED      | Output        | R3 → LED1 |
| 3,8,13,18 | GND | GND | — | — |

### PCB Component Positions (as-built, 2026-06-14)

| Ref | X (mm) | Y (mm) | Rotation | Role |
|-----|--------|--------|----------|------|
| U_BOOST | 77.00 | 25.14 | 0° | DC-DC boost module (LM2587) |
| J2 | 96.5 | 46.5 | 180° | FAN1 header |
| J3 | 96.5 | 58.5 | 180° | FAN2 header |
| J4 | 96.5 | 70.5 | 180° | FAN3 header |
| J5 | 96.5 | 82.5 | 180° | FAN4 header |
| R5 | 65.00 | 47.77 | 90° | FAN1 TACH pull-up (10kΩ) |
| R6 | 65.00 | 60.45 | 90° | FAN2 TACH pull-up (10kΩ) |
| R7 | 65.00 | 73.13 | 90° | FAN3 TACH pull-up (10kΩ) |
| R8 | 65.00 | 85.81 | 90° | FAN4 TACH pull-up (10kΩ) |
| R9 | 69.00 | 40.15 | -90° | FAN1 PWM LED resistor (150Ω) |
| R10 | 69.00 | 52.83 | -90° | FAN2 PWM LED resistor (150Ω) |
| R11 | 69.00 | 65.51 | -90° | FAN3 PWM LED resistor (150Ω) |
| R12 | 69.00 | 78.19 | -90° | FAN4 PWM LED resistor (150Ω) |
| D2 | 77.46 | 46.5 | 0° | FAN1 PWM activity LED |
| D3 | 77.46 | 58.5 | 0° | FAN2 PWM activity LED |
| D4 | 77.46 | 70.5 | 0° | FAN3 PWM activity LED |
| D5 | 77.46 | 82.5 | 0° | FAN4 PWM activity LED |
| LED1 | 18.00 | 30.975 | -90° | Power status LED |
| LED2 | 24.50 | 30.73 | -90° | OTA/prog LED |
| LED6 | 17.975 | 51.475 | -90° | DS18B20 probe LED |
| R3 | 17.975 | 18.475 | -90° | PWR_LED resistor (330Ω) |
| R13 | 24.50 | 18.23 | -90° | PROG_LED resistor (330Ω) |
| R14 | 27.00 | 55.095 | 90° | DS18B20 pull-up (4.7kΩ) |
| R15 | 18.00 | 39.475 | -90° | PROBE_LED resistor (330Ω) |
| HUM1 | 22.00 | 71.475 | 180° | DHT11 temperature/humidity |
| J6 | 19.92 | 61.995 | 0° | DS18B20 probe connector |
