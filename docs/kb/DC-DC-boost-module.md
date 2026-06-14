# DC-DC Step-Up Boost Converter Module — KB Reference

<!-- Created: 2026-06-14 | Updated: 2026-06-14 | Source: Amazon.nl B07RKDB2VP product page -->

---

## Selected Module (approved 2026-06-14)

**Amazon.nl ASIN: B07RKDB2VP**
> "2pcs LM2587 DC-DC Boost Converter 3-30V step up 4-35V Power Supply modules Max 5A"

This module replaces the discrete 5 V → 12 V boost stage (formerly U1/L1/D1/C1/C2).
It is based on the **TI LM2587** — the same IC family used in the original discrete design.

---

## Electrical Characteristics (from Amazon product page)

| Parameter | Value |
|---|---|
| Converter type | **Boost (step-UP)** ✅ |
| Input voltage | **3 V – 30 V** (5V input ✅) |
| Output voltage | **4 V – 35 V** adjustable via potentiometer (12V output ✅) |
| Maximum output current | **5 A** |
| Efficiency | max **92 %** |
| Switching frequency | 100 kHz |
| Output ripple | 50 mV max |
| Load regulation | ± 0.5 % |
| Voltage regulation | ± 0.5 % |
| Potentiometer direction | Clockwise = increase, counter-clockwise = decrease |

**Fan rail budget:** 4 fans × ~0.3 A = 1.2 A typical → well within 5 A limit ✅

---

## Pinout — 4-Pin Daughter Board Interface

| Pin | Label | Description | Net (PoE FanController) |
|---|---|---|---|
| 1 | **IN+** | Positive supply input | +5V |
| 2 | **IN−** | Ground / negative input | GND |
| 3 | **OUT+** | Regulated output (12V) | +12V |
| 4 | **OUT−** | Ground / negative output | GND |

> IN− and OUT− are internally connected; treat as common GND on the PCB.

---

## KiCad Integration

### Schematic symbol
- Symbol name: **DC_Boost_Module** (or reuse existing U_BOOST symbol)
- Net assignments: Pin 1 → `+5V`, Pin 2 → `GND`, Pin 3 → `+12V`, Pin 4 → `GND`

### Footprint
- Custom footprint **`Custom:DC-Boost-Module`** in `hardware/kicad/footprints/Custom.pretty/`
- Pad layout: 1×4 single-row, 2.54 mm pitch THT
- Verify physical dimensions against received module before finalising courtyard
- Power traces to all 4 pins must be ≥ 1.0 mm width (P-HW-07)

---

## Replaces Discrete Stage

| Retired Ref | Value | Reason |
|---|---|---|
| U1 | LM2587-12 IC | Replaced by module (module contains LM2587 internally) |
| L1 | 100 µH inductor | Internal to module |
| D1 | 1N5822 Schottky diode | Internal to module |
| C1 | 100 µF / 25 V | Internal to module |
| C2 | 100 µF / 25 V | Internal to module |

> ⚠️ **R5 is NOT retired** — it is the FAN1 TACH pull-up resistor (10 kΩ, +3V3 → FAN1_TACH), not a boost converter component.

**New BOM entry:**

| Ref | Value | Package | Role |
|---|---|---|---|
| **U_BOOST** | LM2587 Boost Module (Amazon B07RKDB2VP) | 4-pin 2.54mm THT daughter board | 5V→12V boost for fan rail |

---

## Procurement

- **Amazon.nl:** [B07RKDB2VP](https://www.amazon.nl/dp/B07RKDB2VP) — 2-pack, EU shipping
- Also available as generic "LM2587 boost module" on AliExpress

---

## ⚠️ Rejected Alternatives

| Module | ASIN | Reason rejected |
|---|---|---|
| LM2596S-ADJ | AliExpress 1005008183314384 | BUCK converter — cannot do 5V→12V |
| Generic MT3608 module | Amazon B0D9VJKD1L | Only 2A max; replaced by this higher-spec module |

---

## References

- TI LM2587 datasheet: https://www.ti.com/lit/ds/symlink/lm2587.pdf

---

## Pinout — 4-Pin Daughter Board Interface

| Pin | Label | Description | Net (PoE FanController) |
|---|---|---|---|
| 1 | **IN+** | Positive supply input | +5V |
| 2 | **IN−** | Ground / negative input | GND |
| 3 | **OUT+** | Regulated output (12V) | +12V |
| 4 | **OUT−** | Ground / negative output | GND |

> IN− and OUT− are internally connected; treat as common GND on the PCB.

---

## KiCad Integration

### Schematic symbol
- Use generic symbol or create **DC_Boost_Module** in project library.
- Net assignments: Pin 1 → `+5V`, Pin 2 → `GND`, Pin 3 → `+12V`, Pin 4 → `GND`

### Footprint
- Custom footprint **`Custom:DC-Boost-Module`** in `hardware/kicad/footprints/Custom.pretty/`
- Pad layout: 1×4 single-row, 2.54 mm pitch THT
- Module PCB footprint: verify physical dimensions against received unit (typical ~28 mm × 17 mm for this class of mini boost module)
- Mount height: ~8–10 mm above daughter board

---

## Replaces Discrete Stage

| Retired Ref | Value | Reason |
|---|---|---|
| U1 | LM2587-12 IC | Replaced by module IC |
| L1 | 100 µH inductor | Internal to module |
| D1 | 1N5822 Schottky diode | Internal to module |
| C1 | 100 µF / 25 V | Internal to module |
| C2 | 100 µF / 25 V | Internal to module |
| R5 | Feedback resistor | Internal to module (trimmer) |

**New BOM entry:**
| Ref | Value | Package | Role |
|---|---|---|---|
| **U_BOOST** | DC-DC Boost Module (Amazon B0D9VJKD1L) | 4-pin 2.54mm THT daughter board | 5V→12V boost for fan rail |

---

## Procurement

- **Amazon.nl:** [B0D9VJKD1L](https://www.amazon.nl/dp/B0D9VJKD1L) — 10-pack
- Price: ~€X.99 for 10 units (< €1/unit)
- Also available on AliExpress as generic "DC-DC MT3608 / XL6009 step-up module"

---

## ⚠️ Note on LM2596S-ADJ (rejected alternative)

The LM2596S-ADJ (AliExpress item 1005008183314384) is a **BUCK (step-DOWN)** converter
(3V–40V → 1.5V–35V) and **cannot** be used for the 5V→12V rail. It is documented here
for reference only — do not substitute.

---

## References

- Amazon product: https://www.amazon.nl/dp/B0D9VJKD1L
- MT3608 datasheet (common IC in this class): https://www.olimex.com/Products/Breadboarding/BB-PWR-3608/resources/MT3608.pdf
