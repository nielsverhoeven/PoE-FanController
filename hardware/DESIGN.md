# PoE FanController – Hardware Design Notes

<!-- Last updated: 2026-06-06 -->

## Overview
A PoE 802.3at (PoE+) powered device that controls up to 4 PWM fans via an
ESP32-WROOM-32 microcontroller and exposes a web-based configuration interface.

## Block Diagram
```
[Ethernet cable / PoE+]
       │
   ┌───▼────────────────┐
   │  J1  RJ45 + magnetics │  ← Shielded, PoE-capable
   └───┬────────────────┘
       │ 37–57 V DC (PoE pair)
   ┌───▼────────────────┐
   │  U1  Ag9905M module │  ← PoE PD negotiation + isolated flyback
   └───┬────────────────┘
       │ 12 V, 1.67 A (20 W)
       ├──────────────────────────────► J2-J5  Fan headers (12 V PWM)
       │
   ┌───▼────────────────┐
   │  U2  LM2596-3.3    │  ← 12 V → 3.3 V, 3 A step-down
   └───┬────────────────┘
       │ 3.3 V
       ├──── U3 ESP32-WROOM-32
       ├──── U4 CH340C
       └──── Logic decoupling caps
```

## Power Budget (802.3at PoE+ = 25.5 W at PD)

| Consumer          | Voltage | Current  | Power  |
|-------------------|---------|----------|--------|
| 4 × 12 V fan (max)| 12 V   | 4×0.25 A | 12 W   |
| ESP32 (peak WiFi) | 3.3 V   | 0.35 A   | 1.15 W |
| CH340C + logic    | 3.3 V   | 0.10 A   | 0.33 W |
| LM2596 losses     | –       | –        | ~1.5 W |
| Ag9905M losses    | –       | –        | ~2.0 W |
| **Total**         |         |          |**~17 W**|

Available margin: 25.5 − 17 = 8.5 W.  Safe for 802.3at Class 4.

## ESP32 GPIO Allocation

| GPIO   | Function         | Direction | Notes                          |
|--------|------------------|-----------|--------------------------------|
| GPIO0  | BOOT             | Input     | Pull-up R2; BOOT button SW2    |
| GPIO2  | Status LED       | Output    | Active HIGH, R3 330 Ω          |
| GPIO4  | (reserved)       | –         | 1-Wire or I2C SDA alternative  |
| GPIO14 | FAN4 PWM         | Output    | LEDC channel 3, 25 kHz         |
| GPIO21 | I2C SDA (future) | I/O       | Not populated on v0.1          |
| GPIO22 | I2C SCL (future) | I/O       | Not populated on v0.1          |
| GPIO25 | FAN1 PWM         | Output    | LEDC channel 0, 25 kHz         |
| GPIO26 | FAN2 PWM         | Output    | LEDC channel 1, 25 kHz         |
| GPIO27 | FAN3 PWM         | Output    | LEDC channel 2, 25 kHz         |
| GPIO32 | NTC ADC          | ADC Input | 12-bit ADC, voltage divider    |
| GPIO34 | FAN1 TACH        | Input     | Input-only pin, pull-up R5     |
| GPIO35 | FAN2 TACH        | Input     | Input-only pin, pull-up R6     |
| GPIO36 | FAN3 TACH        | Input     | Input-only pin, pull-up R7     |
| GPIO39 | FAN4 TACH        | Input     | Input-only pin, pull-up R8     |
| GPIO1  | TXD0 (UART0)     | Output    | To CH340C RXD                  |
| GPIO3  | RXD0 (UART0)     | Input     | From CH340C TXD                |
| EN     | Reset            | Input     | Pull-up R1; RESET button SW1   |

## Safety & Isolation Requirements (CRITICAL)

- **Minimum creepage across isolation barrier (J1↔U1 output)**: 3.0 mm
- **Minimum clearance**: 3.0 mm
- **Hipot test**: 1.5 kV AC for 60 s across isolation barrier
- **Slot**: Consider adding a PCB slot between primary (PoE) and secondary sides
- The dashed line in the PCB comment layer marks the isolation barrier at x = 38 mm
- **Never route secondary-side signals across the isolation barrier without the Ag9905M module**

## Fan Header Pinout (J2–J5, all identical)

| Pin | Signal   | Notes                              |
|-----|----------|------------------------------------|
| 1   | GND      | Ground                             |
| 2   | +12V     | Fan supply (12 V from Ag9905M)     |
| 3   | TACH     | Tachometer output from fan, 10k pull-up to 3.3V |
| 4   | PWM      | 25 kHz PWM input from ESP32 LEDC  |

Standard PC fan pinout (Intel spec). Compatible with 4-wire 12V PWM fans.

## PCB Design Guidelines

- **Layer stack**: 2-layer FR4, 1.6 mm, 1 oz Cu
- **Track widths**: Signal = 0.25 mm; Power (+12V, GND) = 1.0 mm
- **Via**: 0.8 mm diameter, 0.4 mm drill
- **Ground pour**: Both layers (GND). Split at isolation barrier.
- **Component placement priority**:
  1. **All external connectors on top board edge** (y = 5 mm, per constitution P-HW-03):
     | Ref | Part | Centre X | Side | Notes |
     |-----|------|----------|------|-------|
     | J1 | RJ45 Amphenol 54602 | 20.0 mm | Primary (x < 38 mm) | rot=180°, port exits top edge |
     | J2 | Fan header 1×4 | 46.1 mm | Secondary | Courtyard left ≥ 41.0 mm (3 mm creepage) |
     | J3 | Fan header 1×4 | 56.8 mm | Secondary | |
     | J4 | Fan header 1×4 | 67.4 mm | Secondary | |
     | J5 | Fan header 1×4 | 78.1 mm | Secondary | |
     | J6 | USB-C GCT USB4085 | 85.0 mm | Secondary | Port faces top edge (rot=0°) |
     | J7 | Debug UART 1×3 | 91.0 mm | Right edge | Documented exception P-HW-03 v1.0.1; rot=90° |
  2. U1 (Ag9905M) close to J1, primary-side power traces (≈ x=20, y=40)
  3. Isolation gap/slot at x=38 mm, y=10–70 mm, 1.0 mm wide (P-ISO-04)
  4. U2 (LM2596) + L1 + D1 grouped together, primary side (≈ x=15–32, y=55–62)
  5. U3 (ESP32) on secondary side (≈ x=65, y=42)
  6. U4 (CH340C) near J6 on secondary side (≈ x=82, y=58)
  7. Decoupling caps (C3–C6) as close as possible to U3 (ESP32) power pins

## Firmware Overview

- **Framework**: Arduino for ESP32 (PlatformIO)
- **Fan PWM**: ESP32 LEDC peripheral, 25 kHz, 8-bit resolution
- **TACH**: GPIO interrupt counting or PCNT peripheral, Hz → RPM
- **Temperature**: ADC + Steinhart-Hart equation for NTC
- **Web interface**: ESPAsyncWebServer + LittleFS (static HTML/CSS/JS)
- **Configuration persistence**: NVS (Non-Volatile Storage)
- **OTA**: ArduinoOTA over local WiFi

## Bring-up Procedure

1. **No-load power test**: Connect PoE+ switch. Measure Ag9905M output (expect 12.0 ± 0.3 V).
2. **Secondary rail**: Measure LM2596 output (expect 3.30 ± 0.05 V).
3. **UART test**: Connect USB-C. CH340C should enumerate. Open serial at 115200 baud.
4. **Flash firmware**: `pio run -e esp32dev --target upload` via CH340C.
5. **Fan test**: Connect one fan to J2. Command 50% duty cycle from firmware/web UI.
6. **Full load test**: Connect all 4 fans at 100%, run for 10 min. Check temperatures.
