# PCB Routing Pending — PoE FanController Daughter Board (Issue #75)

**Branch:** `feature/75-esp32-p4-poe-eth-daughterboard`  
**Status:** Layout scripted, routing requires KiCad GUI  
**Date:** 2026-06-08

---

## Component Placement Status

After running `hardware/pcb_cleanup_v2.py`, the PCB contains the following footprints:

| Ref | Value | Notes |
|-----|-------|-------|
| J8 | 2×20 PinSocket | Waveshare ESP32-P4-POE-ETH interface — placed centrally |
| J2–J5 | Fan header 1×04 | Moved to right side edge (x≈97mm) for side-accessible fan cables |
| R3 | 330Ω | Status LED current limiter |
| R4 | 10kΩ | NTC voltage divider pull-up |
| R5–R8 | 10kΩ | TACH pull-up resistors (one per fan channel) |
| LED1 | LED_GREEN | Status LED |
| NTC1 | NTC10K_B3950 | Temperature sensor |
| **U_BOOST** | **LM2587-12** | **⚠️ NOT YET IN PCB — add via "Update PCB from Schematic"** |

**Board outline:** 100 mm (W) × 85.6 mm (H), origin at (5.0, 5.0) mm

---

## Nets Requiring Routing

PCB routing must be performed in the KiCad GUI after running  
**Tools → Update PCB from Schematic** to import U_BOOST.

### Power Nets (trace width ≥ 1.0 mm per NFR-E-01)

| Net | From | To | Current |
|-----|------|----|---------|
| `+5V` | J8 pins 2, 4 | U_BOOST VIN (pin 1) | ≤ 2 A (boost input) |
| `+12V` | U_BOOST VOUT (pin 3) | J2–J5 pin 2 (VCC_FAN) | ≤ 1 A total |
| `GND` | J8 pins 6,9,14,20,25,29,33,38; U_BOOST pin 2 | All GND pads | Return path |

### Signal Nets (trace width ≥ 0.25 mm per NFR-E-02)

| Net | From | To |
|-----|------|----|
| `FAN1_PWM` | J8 pin 7 | J2 pin 4 |
| `FAN2_PWM` | J8 pin 8 | J3 pin 4 |
| `FAN3_PWM` | J8 pin 10 | J4 pin 4 |
| `FAN4_PWM` | J8 pin 11 | J5 pin 4 |
| `FAN1_TACH` | J2 pin 3 | J8 pin 12 + R5 pin 2 |
| `FAN2_TACH` | J3 pin 3 | J8 pin 13 + R6 pin 2 |
| `FAN3_TACH` | J4 pin 3 | J8 pin 15 + R7 pin 2 |
| `FAN4_TACH` | J5 pin 3 | J8 pin 16 + R8 pin 2 |
| `+3V3` | J8 pins 1, 17 | R4 pin 1 + R5–R8 pin 1 |
| `NTC_ADC` | R4 pin 2 ↔ NTC1 pin 1 | J8 pin 23 |
| `STATUS_LED` | J8 pin 3 | R3 pin 1 |
| `LED_A` | R3 pin 2 | LED1 anode (pin 1) |

---

## Routing Instructions

1. Open `hardware/kicad/PoE-FanController.kicad_pcb` in KiCad 10 GUI
2. **Tools → Update PCB from Schematic** → accept all changes → U_BOOST footprint appears
3. Place U_BOOST between J8 and fan headers (suggested: x≈60mm, y≈30mm)
4. Place external boost components if using discrete LM2587-12:
   - L_BOOST (33µH inductor): between U_BOOST SW pin and +12V
   - D_BOOST (Schottky diode): catch diode from SW node to +12V
   - C_IN (10µF/16V): input decoupling at U_BOOST VIN
   - C_OUT (100µF/25V): output cap at +12V rail
5. Route power planes first (+12V, +5V, GND) using ≥ 1.0 mm traces
6. Route signal traces (PWM, TACH, NTC, LED) using ≥ 0.25 mm traces
7. Add GND copper pours on F.Cu and B.Cu (per NFR-E-03)
8. Run **DRC** → verify zero violations and zero unconnected nets

---

## DRC Baseline

| Step | Violations | Unconnected |
|------|-----------|-------------|
| After pcb_cleanup_v2.py | 0 | 0 |
| Target after routing | 0 | 0 |

> **PCB routing requires KiCad GUI — run DRC after routing to verify zero violations**

---

## Design Rules Reference

- `+12V` traces: ≥ 1.0 mm (carries up to 1 A total fan load)
- `+5V` traces: ≥ 1.0 mm (boost converter input, ~2 A)
- Signal traces: ≥ 0.25 mm
- GND: copper pour on F.Cu and B.Cu
- Board: 2-layer FR4, 1.6 mm, 1 oz copper, all components on F.Cu
- Board size: 100 × 85.6 mm (to match Waveshare SKU 32088 length — verify OQ-01)
