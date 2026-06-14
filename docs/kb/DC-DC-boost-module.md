# DC-DC Step-Up Boost Converter Module — KB Reference

<!-- Created: 2026-06-14 | Updated: 2026-06-14 | Source: Amazon.nl B07RKDB2VP product page + board images -->

---

## Selected Module (approved 2026-06-14)

**Amazon.nl ASIN: B07RKDB2VP**
> "2pcs LM2587 DC-DC Boost Converter 3-30V step up 4-35V Power Supply modules Max 5A"

This module replaces the discrete 5 V → 12 V boost stage (formerly U1/L1/D1/C1/C2).
It is based on the **TI LM2587S-ADJ P+** — the same IC family used in the original discrete design.

---

## Physical Dimensions (measured from board images)

| Dimension | Value |
|---|---|
| PCB length | **48 mm** |
| PCB width | **23 mm** |
| Board height (incl. components) | **~12 mm** |
| Mounting hole diameter | 3 mm (x4 corners) |
| Potentiometer diameter | 3 mm |

> Courtyard for KiCad footprint: **50 mm × 25 mm** (1 mm clearance each side)

---

## Pin Layout (from board labelling images)

The board has **4 through-hole solder pads**, one at each corner:

```
┌─────────────────────────────────┐
│  OUT− (cathode)   OUT+ (anode)  │  ← Output side (top)
│                                 │
│  IN−  (cathode)   IN+  (anode)  │  ← Input side (bottom)
└─────────────────────────────────┘
```

| Corner | Label | Function | Net (PoE FanController) |
|---|---|---|---|
| Top-left | **OUT−** | Output cathode (GND) | GND |
| Top-right | **OUT+** | Output anode (+12V) | +12V |
| Bottom-left | **IN−** | Input cathode (GND) | GND |
| Bottom-right | **IN+** | Input anode (+5V) | +5V |

> ⚠️ **Pin ordering is diagonal, not linear.** IN+ and OUT+ are on the RIGHT side; IN− and OUT− are on the LEFT side. Verify against physical board before soldering.

---

## On-Board Components (visible in images)

| Component | Value | Role |
|---|---|---|
| IC | **LM2587S-ADJ P+** (JMS2RP marking) | Main boost controller |
| C_IN | 220 µF / 35 V electrolytic | Input bulk capacitor |
| C_OUT | 220 µF / 35 V electrolytic | Output bulk capacitor |
| L | 33 µH (M361 marking) | Boost inductor |
| D | **SK54** Schottky diode | Rectifier (5A, 40V) |
| R_feedback | 2R2 + trim network | Output voltage set |
| RV1 | 3 mm blue potentiometer (V-ADJ) | Output voltage adjustment |

---

## Electrical Characteristics

| Parameter | Value |
|---|---|
| Converter type | **Boost (step-UP)** |
| Input voltage | **3 V – 30 V** |
| Output voltage | **4 V – 35 V** adjustable via potentiometer |
| Maximum output current | **5 A** |
| Efficiency | max **92 %** |
| Switching frequency | 100 kHz |
| Output ripple | 50 mV max |
| Load regulation | ± 0.5 % |
| Voltage regulation | ± 0.5 % |
| Potentiometer direction | Clockwise = increase, counter-clockwise = decrease |

**Fan rail budget:** 4 fans × ~0.3 A = 1.2 A typical → well within 5 A limit ✅

---

## KiCad Integration

### Schematic symbol
- Symbol: **DC_Boost_Module** (4-pin)
- Pin assignments:
  - Pin 1 `IN+`  → net `+5V`  (`power_in`)
  - Pin 2 `IN−`  → net `GND`  (`power_in`)
  - Pin 3 `OUT+` → net `+12V` (`power_out`)
  - Pin 4 `OUT−` → net `GND`  (`power_in`)

### Footprint (`Custom:DC-Boost-Module`)
- File: `hardware/kicad/footprints/Custom.pretty/DC-Boost-Module.kicad_mod`
- Pad layout: **4 pads at corners**, 2.54 mm pitch rows, ~43 mm between left/right columns
- Pad drill: 1.0 mm, copper: 1.8 mm round, F.Cu only
- Courtyard: **50 mm × 25 mm** on F.CrtYd
- Silkscreen: pin-1 (IN+) marker on F.SilkS and F.Fab
- Power traces to all pads: ≥ 1.0 mm width (P-HW-07)

---

## Replaces Discrete Stage

| Retired Ref | Value | Reason |
|---|---|---|
| U1 | LM2587-12 IC | Replaced by module IC (LM2587S-ADJ) |
| L1 | 100 µH inductor | Internal to module (33µH on-board) |
| D1 | 1N5822 Schottky diode | Internal to module (SK54 on-board) |
| C1 | 100 µF / 25 V | Internal to module (220µF/35V on-board) |
| C2 | 100 µF / 25 V | Internal to module (220µF/35V on-board) |

> ⚠️ **R5 is NOT retired** — it is the FAN1 TACH pull-up resistor (10 kΩ, +3V3 → FAN1_TACH), not part of the boost stage.

**New BOM entry:**

| Ref | Value | Package | Role |
|---|---|---|---|
| **U_BOOST** | LM2587 Boost Module (Amazon B07RKDB2VP) | 4-pin corner THT, 48×23mm board | 5V→12V boost for fan rail |

---

## Pre-Fabrication Checks

Before ordering PCBs, verify against the physical module:

| # | Check | Action |
|---|---|---|
| R-01 | VBUS current on J8 pin 40 (~3.47A total) | Verify Waveshare SKU 32088 VBUS rail spec |
| R-02 | PCB dimensions (measured: 48×23mm) | Confirm with callipers; update courtyard if needed |
| R-03 | Pin ordering (diagonal: IN+/OUT+ right, IN−/OUT− left) | Verify with multimeter on received unit before soldering |

---

## Procurement

- **Amazon.nl:** [B07RKDB2VP](https://www.amazon.nl/dp/B07RKDB2VP) — 2-pack, EU shipping

---

## ⚠️ Rejected Alternatives

| Module | ASIN | Reason rejected |
|---|---|---|
| LM2596S-ADJ | AliExpress 1005008183314384 | BUCK converter — cannot do 5V→12V |
| Generic MT3608 module | Amazon B0D9VJKD1L | Only 2A max; replaced by this higher-spec module |

---

## References

- TI LM2587 datasheet: https://www.ti.com/lit/ds/symlink/lm2587.pdf
- Board images: `docs/kb/lm2587 booster/`

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
