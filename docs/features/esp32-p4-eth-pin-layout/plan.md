# Technical Plan: ESP32-P4-ETH Module Pin Layout Fix

> Issue: [#133](https://github.com/nielsverhoeven/PoE-FanController/issues/133) (original), [#148](https://github.com/nielsverhoeven/PoE-FanController/issues/148) (pin corrections)
> Branch: `feature/148-correct-gpio-pin-assignments`
> Status: **IMPLEMENTED** (2026-06-10, constitution v4.2.1)

---

## Summary of Implemented State

The ESP32-P4-POE-ETH (Waveshare SKU 32088) J8 connector is correctly defined in
`hardware/generator/components.py` with the following properties:

- **Footprint**: `Custom:ESP32-P4-PoE-ETH-PinSocket` (15.38mm row spacing, 2.54mm pitch)
- **Pin numbering**: Consecutive-column (NOT Pico-style) — pins 1–20 left, 21–40 right
- **Symbol orientation**: Matches physical board — pin 40 (VBUS/+5V) at **top-right**, pin 21 (GPIO48) at **bottom-right**; pin 20 (GPIO54) at **top-left**, pin 1 (DP/GPIO25) at **bottom-left**

### Authoritative pin assignments (left column, pins 1–20, bottom → top)

| Pin | Physical signal | This project | Notes |
|-----|----------------|--------------|-------|
| 1  | DP / GPIO25 | NC | USB D+ |
| 2  | DM / GPIO24 | NC | USB D- |
| 3  | GND | GND | |
| 4  | SDA / GPIO7 | NC | I2C Data |
| 5  | SCL / GPIO8 | NC | I2C Clock |
| 6  | GPIO2 | STATUS_LED | Status indicator |
| 7  | GPIO3 | NC | |
| 8  | GND | GND | |
| 9  | GPIO4 | NC | |
| 10 | GPIO5 | NC | |
| 11 | GPIO6 | NC | |
| 12 | GPIO14 | NC | |
| 13 | GND | GND | |
| 14 | GPIO15 | PROG_LED | OTA/write indicator |
| 15 | GPIO16 | DHT11_DATA | Single-wire sensor |
| 16 | GPIO17 | NC | |
| 17 | GPIO18 | NC | |
| 18 | GND | GND | |
| 19 | GPIO19 | DS18B20_DATA | 1-Wire probe |
| 20 | GPIO54 | NC | NOT GND |

### Authoritative pin assignments (right column, pins 21–40, bottom → top)

| Pin | Physical signal | This project | Notes |
|-----|----------------|--------------|-------|
| 21 | GPIO48 | PROBE_LED | Probe health LED |
| 22 | GPIO47 | FAN4_TACH | IRQ pull-up via R8 |
| 23 | GND | GND | |
| 24 | GPIO46 | FAN3_TACH | IRQ pull-up via R7 |
| 25 | GPIO33 | NC | EMAC_RXD1 — FORBIDDEN by IO_MUX |
| 26 | GPIO32 | NC | EMAC_RXD0 — FORBIDDEN by IO_MUX |
| 27 | GPIO27 | FAN4_PWM | LEDC CH3 |
| 28 | GND | GND | |
| 29 | GPIO26 | FAN3_PWM | LEDC CH2 |
| 30 | RUN | NC | System control — reserved |
| 31 | GPIO23 | FAN2_TACH | IRQ pull-up via R6 |
| 32 | GPIO22 | FAN1_TACH | IRQ pull-up via R5 |
| 33 | GND | GND | Physical GND — NOT a signal |
| 34 | GPIO21 | FAN2_PWM | LEDC CH1 |
| 35 | GPIO20 | FAN1_PWM | LEDC CH0 |
| 36 | 3V3 | +3V3 | SOLE 3.3V source for daughter board |
| 37 | EN | NC | Chip enable — reserved |
| 38 | GND | GND | |
| 39 | VSYS | NC | Do NOT use as 5V source (issue #137) |
| 40 | VBUS | +5V | SOLE 5V source for U_BOOST |

### Key corrections applied (issue #148)

| Pin | Was | Correct | Reason |
|-----|-----|---------|--------|
| 2 (left) | +5V | NC | DM/GPIO24 = USB D- |
| 4 (left) | +5V | NC | SDA/GPIO7 = I2C Data |
| 20 (left) | GND | NC | GPIO54, not GND |
| 25 (right) | GND | NC | GPIO33/EMAC_RXD1 FORBIDDEN |
| 26 (right) | GND | NC | GPIO32/EMAC_RXD0 FORBIDDEN |
| 30 (right) | GND | NC | RUN = system control |
| 33 (right) | FAN2_PWM | GND | Physical GND pad |
| 34 (right) | GND | FAN2_PWM | GPIO21 = FAN2 LEDC CH1 |

### Symbol orientation correction (2026-06-10)

The schematic symbol pin list order was corrected so the symbol visually matches
the physical board layout in KiCad Eeschema:
- `pins_left` lists pins **20 → 1** (top-to-bottom in symbol)
- `pins_right` lists pins **40 → 21** (top-to-bottom in symbol)

This puts VBUS (+5V, pin 40) at the **top-right** and GPIO48 (pin 21) at the
**bottom-right** — matching the physical Waveshare board image.

The `Custom:J8_Waveshare` schematic symbol (defined in `hardware/generator/components.py`) assigns
pins to left/right sides using an **alternating odd/even (PICO-style)** numbering scheme:

| Symbol side | Pin numbers |
|---|---|
| Left (current) | 1, 3, 5, 7, 9, 11, … 39 (odd) |
| Right (current) | 2, 4, 6, 8, 10, 12, … 40 (even) |

The Waveshare ESP32-P4-POE-ETH (SKU 32088) physical module uses a **consecutive row numbering**
scheme:

| Physical side | Pin numbers |
|---|---|
| Left column (bottom → top) | 1, 2, 3, 4, 5, … 20 |
| Right column (bottom → top) | 21, 22, 23, 24, 25, … 40 |

The footprint `PinSocket_2x20_P2.54mm_P15.38mm_Vertical.kicad_mod` (in
`hardware/kicad/footprints/Custom.pretty/`) was built to match the PICO-style symbol, not the
physical module:

| Footprint row | y-coordinate | Pad numbers |
|---|---|---|
| Row A | −7.690 mm | 1, 3, 5, … 39 (odd) |
| Row B | +7.690 mm | 2, 4, 6, … 40 (even) |

Because the footprint maps pad *n* to a pad at a physical position that corresponds to the physical
module's pin *(2k−1)* (for odd pads) or pin *(k+20)* (for even pads), every signal that is not on
pin 1 is solder-connected to the wrong physical pad. The worst case is **+5V VSYS**:

| Layer | Intended | Actual |
|---|---|---|
| Schematic | Pin 39 = +5V (VSYS) | Correct |
| Footprint pad 39 | At Row A, far-right position | Row A = physical 1–20 range |
| Physical module pin at that position | Physical pin 20 = **GND** | **+5V drives a GND pad → boost converter starved / possible short** |
| Footprint pad 40 | At Row B, far-right position | Row B = physical 21–40 range |
| Physical module pin 40 | +5V (VBUS) | Correct (coincidence: pad 40 = physical 40) |

---

## Root Cause

**Dual mismatch between PICO-style numbering in the generator/footprint and the physical module's
consecutive row numbering.** Two independent artefacts are wrong:

1. `hardware/generator/components.py` — `Custom:J8_Waveshare` symbol definition uses odd pins on
   the left list and even pins on the right list, causing every pin to appear on the wrong schematic
   side and the generated `.kicad_sch` to carry incorrect positional metadata.

2. `hardware/kicad/footprints/Custom.pretty/PinSocket_2x20_P2.54mm_P15.38mm_Vertical.kicad_mod` —
   Pad numbering inherited the same PICO-style convention; Row A carries odd pad numbers and Row B
   carries even pad numbers, so netlist connections from pad *n* land on the wrong physical copper
   island.

The two artefacts must be fixed together, or the netlist will still be wrong after either fix alone.

---

## Correct Pin Mapping Table

Physical pin correspondence after the fix. Left column = physical Row A (pins 1–20 from the end
near the board's short edge); Right column = Row B (pins 21–40 same positional order).

| Position | Physical Pin (Left / Row A) | Net (signal) | Physical Pin (Right / Row B) | Net (signal) |
|---|---|---|---|---|
| 1 (near pin-1 end) | **1** | `+3V3` | **21** | NC (GPIO14) |
| 2 | **2** | NC | **22** | `PROG_LED` (GPIO15, OTA/write LED) |
| 3 | **3** | `STATUS_LED` (GPIO2) | **23** | `NTC_ADC` (GPIO16, SAR ADC) |
| 4 | **4** | NC | **24** | NC (GPIO17) |
| 5 | **5** | NC (GPIO3) | **25** | GND |
| 6 | **6** | GND | **26** | NC (GPIO18) |
| 7 | **7** | `FAN1_PWM` (GPIO4, LEDC CH0) | **27** | `DS18B20_DATA` (GPIO19, 1-Wire) |
| 8 | **8** | `FAN2_PWM` (GPIO5, LEDC CH1) ⚠️ | **28** | `PROBE_LED` (GPIO20, probe LED) |
| 9 | **9** | GND | **29** | GND |
| 10 | **10** | `FAN3_PWM` (GPIO6, LEDC CH2) ⚠️ | **30** | NC (GPIO21) |
| 11 | **11** | `FAN4_PWM` (GPIO7, LEDC CH3) | **31** | NC (GPIO22) |
| 12 | **12** | `FAN1_TACH` (GPIO8, IRQ) ⚠️ | **32** | NC (GPIO26) |
| 13 | **13** | `FAN2_TACH` (GPIO9, IRQ) | **33** | GND |
| 14 | **14** | GND ⚠️ | **34** | NC (GPIO27) |
| 15 | **15** | `FAN3_TACH` (GPIO10, IRQ) | **35** | NC (GPIO28, ETH_MDIO NC) |
| 16 | **16** | `FAN4_TACH` (GPIO11, IRQ) ⚠️ | **36** | NC (3V3\_EN/RUN) |
| 17 | **17** | `+3V3` | **37** | NC (GPIO29) |
| 18 | **18** | NC (GPIO12) ⚠️ | **38** | GND |
| 19 | **19** | NC (GPIO13) | **39** | **`+5V` (VSYS — PoE PD output)** ⚠️⚠️ |
| 20 | **20** | GND ⚠️ | **40** | **`+5V` (VBUS — USB 5V)** |

> ⚠️ marks a net that is **currently wired to the wrong physical pad** due to the PICO/consecutive
> mismatch. Pins 39 (+5V VSYS → physical GND pin 20) and 16, 12, 14 (signals routed to wrong row)
> are the most critical cases.

**Sources:** `docs/kb/ESP32-P4-POE-ETH/board-reference.md` (§4.1, §4.2), OQ-02 resolution
(confirmed from Waveshare schematic), `hardware/generator/components.py` current signal assignments.

> ⚠️ **Verification required before implementation:** The exact physical orientation of pin 1
> (board's long-edge end that receives the first pad) must be confirmed against the Waveshare
> ESP32-P4-POE-ETH schematic PDF (`docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-datasheet.pdf`). This
> affects which footprint row end carries pad 1 vs pad 20 / 21 vs 40 — see Acceptance Criterion A0.

---

## Architecture Fit

| Constitution principle | Relevance to this fix |
|---|---|
| **P-HW-05** — Schematic is generated, not hand-edited | All changes to the schematic symbol and wiring **must** go through `hardware/generator/components.py` and be materialised by re-running `hardware/generate_project.py`. The `.kicad_sch` output file must never be edited by hand. |
| **P-HW-06** — Grid discipline | The generator already enforces 2.54 mm grid via `snap()`. Rewriting `pins_left`/`pins_right` lists does not change placement anchors; the body size remains `body_w=25.4, body_h=50.8` (10×G, 20×G). |
| **P-KI-07** (PCB not generated) | The footprint file is NOT generated by `generate_project.py`. It is a static file in `hardware/kicad/footprints/Custom.pretty/` and must be edited directly and committed. |
| **P-HW-04** — Board outline | J8 mechanical placement (left edge, 78 mm span, row-to-row 15.38 mm) is unchanged. Only pad numbers change, not pad coordinates. |

This bug is purely a **data/numbering error** — no schematic topology changes, no new components,
no firmware changes, and no PCB outline changes are required.

---

## Implementation Approach

> All changes are in the generator package or the footprint file. The `.kicad_sch` and `.kicad_pcb`
> are not touched directly.

### Change 1 — `hardware/generator/components.py`: Symbol definition

**Location:** The `s.define("Custom:J8_Waveshare", …)` call (~line 122).

Rewrite `pins_left` to list physical pins 1–20 in order (top of symbol = pin 1 end):

```python
pins_left=[
    # Physical Row A — pins 1..20 (top to bottom in symbol)
    ("+3V3",        "1",  "power_out"),
    ("NC",          "2",  "no_connect"),
    ("LED",         "3",  "bidirectional"),  # GPIO2 — status LED
    ("NC",          "4",  "no_connect"),
    ("NC",          "5",  "no_connect"),     # GPIO3
    ("GND",         "6",  "passive"),
    ("FAN1_PWM",    "7",  "output"),         # GPIO4 LEDC CH0
    ("FAN2_PWM",    "8",  "output"),         # GPIO5 LEDC CH1  ← was right side
    ("GND",         "9",  "passive"),
    ("FAN3_PWM",    "10", "output"),         # GPIO6 LEDC CH2  ← was right side
    ("FAN4_PWM",    "11", "output"),         # GPIO7 LEDC CH3
    ("FAN1_TACH",   "12", "input"),          # GPIO8            ← was right side
    ("FAN2_TACH",   "13", "input"),          # GPIO9
    ("GND",         "14", "passive"),        #                  ← was right side
    ("FAN3_TACH",   "15", "input"),          # GPIO10
    ("FAN4_TACH",   "16", "input"),          # GPIO11           ← was right side
    ("+3V3",        "17", "power_out"),
    ("NC",          "18", "no_connect"),     # GPIO12           ← was right side
    ("NC",          "19", "no_connect"),     # GPIO13
    ("GND",         "20", "passive"),        #                  ← was right side
],
```

Rewrite `pins_right` to list physical pins 21–40 in order:

```python
pins_right=[
    # Physical Row B — pins 21..40 (top to bottom in symbol)
    ("NC",             "21", "no_connect"),  # GPIO14           ← was left side
    ("PROG_LED",       "22", "output"),      # GPIO15 OTA LED   ← was NC, fix type
    ("NTC_ADC",        "23", "input"),       # GPIO16 ADC       ← was left side
    ("NC",             "24", "no_connect"),  # GPIO17
    ("GND",            "25", "passive"),     #                  ← was left side
    ("NC",             "26", "no_connect"),  # GPIO18
    ("DS18B20_DATA",   "27", "bidirectional"), # GPIO19 1-Wire  ← was left side
    ("PROBE_LED",      "28", "output"),      # GPIO20
    ("GND",            "29", "passive"),     #                  ← was left side
    ("NC",             "30", "no_connect"),  # GPIO21
    ("NC",             "31", "no_connect"),  # GPIO22           ← was left side
    ("NC",             "32", "no_connect"),  # GPIO26
    ("GND",            "33", "passive"),     #                  ← was left side
    ("NC",             "34", "no_connect"),  # GPIO27
    ("NC",             "35", "no_connect"),  # GPIO28 ETH_MDIO  ← was left side
    ("NC",             "36", "no_connect"),  # 3V3_EN/RUN
    ("NC",             "37", "no_connect"),  # GPIO29           ← was left side
    ("GND",            "38", "passive"),
    ("+5V",            "39", "power_out"),   # VSYS PoE +5V     ← was left side ⚠️
    ("+5V",            "40", "power_out"),   # VBUS USB +5V
],
```

**Secondary symbol fix:** Pin "22" (`PROG_LED`) was previously typed as `no_connect` while being
wired in the schematic. It must be changed to `output` (done in the rewrite above) so ERC does not
report a conflict.

### Change 2 — `hardware/generator/components.py`: Wiring section

**Location:** The J8 component placement block (~line 488 onward, the `p["n"]` calls).

After the symbol rewrite, `pin_pos()` will return new (x, y) coordinates because every pin's
position index within its list changes. Labels connected to pins that **switch sides** must have
their `angle` argument updated:

| Pin | Signal | Old side | New side | Angle change |
|---|---|---|---|---|
| 8 | FAN2_PWM | Right (angle=0) | Left (angle=180) | 0 → 180 |
| 10 | FAN3_PWM | Right (angle=0) | Left (angle=180) | 0 → 180 |
| 12 | FAN1_TACH | Right (angle=0) | Left (angle=180) | 0 → 180 |
| 16 | FAN4_TACH | Right (angle=0) | Left (angle=180) | 0 → 180 |
| 22 | PROG_LED | Right (angle=0) | Right (angle=0) | unchanged (but add if missing) |
| 23 | NTC_ADC | Left (angle=180) | Right (angle=0) | 180 → 0 |
| 25 | GND | Left | Right | Power symbol — no angle |
| 27 | DS18B20_DATA | Left (angle=180) | Right (angle=0) | 180 → 0 |
| 29 | GND | Left | Right | Power symbol — no angle |
| 31 | NC | Left | Right | No wire needed (NC) |
| 33 | GND | Left | Right | Power symbol — no angle |
| 35 | NC | Left | Right | No wire needed |
| 37 | NC | Left | Right | No wire needed |
| 39 | +5V (VSYS) | Left | Right | Power symbol — no angle |

The wiring block comment header (~line 498) that reads `Left side (odd)` / `Right side (even)` must
be rewritten to `Left side (pins 1–20)` / `Right side (pins 21–40)`.

### Change 3 — Footprint: re-number pads

**File:** `hardware/kicad/footprints/Custom.pretty/PinSocket_2x20_P2.54mm_P15.38mm_Vertical.kicad_mod`

The pad **coordinates** (x, y) are physically correct — the 15.38 mm row spacing and 2.54 mm pin
pitch match the Waveshare module. Only the **pad numbers** need to change.

Current → Correct pad number mapping (renumber all 40 pads):

| Row | x-position index (0–19, left to right) | Current pad# | New pad# |
|---|---|---|---|
| Row A (y=−7.690) | 0 (x=−24.130) | 1 | 1 |
| Row A | 1 (x=−21.590) | 3 | 2 |
| Row A | 2 (x=−19.050) | 5 | 3 |
| … | … | … | … |
| Row A | k | 2k+1 | k+1 |
| … | … | … | … |
| Row A | 19 (x=+24.130) | 39 | 20 |
| Row B (y=+7.690) | 0 (x=−24.130) | 2 | 21 |
| Row B | 1 (x=−21.590) | 4 | 22 |
| … | … | … | … |
| Row B | k | 2k+2 | k+21 |
| … | … | … | … |
| Row B | 19 (x=+24.130) | 40 | 40 |

The pad 1 square marker (silk-screen triangle at top-left) remains on the pad that will carry pad
number "1" — no silk change required.

> ⚠️ Before editing the footprint, verify the **orientation of physical pin 1** against
> `docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-datasheet.pdf`. Confirm that Row A (y=−7.690 in footprint
> coordinates, which becomes one specific long edge when the part is rotated on the PCB) is the
> physical row that carries the module's pins 1–20 — not pins 21–40. If Row A corresponds to pins
> 21–40, swap the numbering assignment: Row A = 21–40, Row B = 1–20.

### Change 4 — Regenerate schematic

```
cd hardware
python generate_project.py
```

The generated `hardware/kicad/PoE-FanController.kicad_sch` is the only file in `hardware/kicad/`
that should change (apart from normal UUID churn).

### Change 5 — ERC verification

Open `hardware/kicad/PoE-FanController.kicad_sch` in KiCad 10, run **Inspect → Electrical Rules
Checker**. Target: **zero errors, zero warnings** (excluding any pre-existing suppressed items
documented in `hardware/DESIGN.md`).

---

## Testing Strategy

### Pre-implementation verification (A0)
- Open `docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-datasheet.pdf`, locate the 40-pin header pinout
  diagram, and confirm:
  - Which physical long-edge of the connector carries pins 1–20 vs 21–40
  - Which positional end of the row carries pin 1 vs pin 20
  - Record findings in `hardware/DESIGN.md` with a reference to the datasheet page

### Schematic validation (A1–A3)
- **A1:** After regeneration, open the schematic and confirm J8 left column shows pins 1–20 with
  the correct labels and J8 right column shows pins 21–40.
- **A2:** Trace the +5V net from pin 39 (right column, second-to-last from bottom) and confirm it
  reaches `U1:VIN` (boost converter input) via the net name `+5V`.
- **A3:** Run ERC — zero violations.

### Footprint netlist check (A4)
- In KiCad PCB Editor, open `hardware/kicad/PoE-FanController.kicad_pcb`, run **Update PCB from
  Schematic** (sync netlist), confirm **zero unresolved net changes** after the schematic fix. If
  net changes appear, inspect each changed pad to confirm the new assignment is physically correct.

### Signal-by-signal spot check (A5)
Verify each of the 10 project-used GPIO nets against the KB pinout table
(`docs/kb/ESP32-P4-POE-ETH/board-reference.md §4.2`):

| Net | Expected physical pin | Expected footprint pad after fix |
|---|---|---|
| STATUS_LED | 3 (Row A) | 3 |
| FAN1_PWM | 7 (Row A) | 7 |
| FAN2_PWM | 8 (Row A) | 8 |
| FAN3_PWM | 10 (Row A) | 10 |
| FAN4_PWM | 11 (Row A) | 11 |
| FAN1_TACH | 12 (Row A) | 12 |
| FAN2_TACH | 13 (Row A) | 13 |
| FAN3_TACH | 15 (Row A) | 15 |
| FAN4_TACH | 16 (Row A) | 16 |
| NTC_ADC | 23 (Row B) | 23 |
| DS18B20_DATA | 27 (Row B) | 27 |
| +5V (VSYS) | 39 (Row B) | 39 |
| +5V (VBUS) | 40 (Row B) | 40 |

### PCB DRC (A6)
- Run DRC in KiCad PCB Editor — zero errors after any rerouting needed by the netlist update.

### Power path continuity (A7)
- Confirm in the schematic net inspector that the `+5V` net includes J8 pin 39, J8 pin 40, and the
  positive terminal of C1 (input bypass cap) and U1:VIN (boost converter input).

---

## Acceptance Criteria

| ID | Criterion | Verifiable by |
|---|---|---|
| **A0** | Physical orientation of pin 1 confirmed from `ESP32-P4-ETH-datasheet.pdf`; finding recorded in `hardware/DESIGN.md` | Manual inspection |
| **A1** | `Custom:J8_Waveshare` symbol in the regenerated `.kicad_sch` has pins 1–20 on the left column and pins 21–40 on the right column | KiCad schematic viewer |
| **A2** | Pins 39 and 40 (both `+5V`) appear on the **right column** of J8 in the schematic | KiCad schematic viewer |
| **A3** | ERC reports zero errors after regeneration | KiCad ERC |
| **A4** | Footprint pads 1–20 are on Row A and pads 21–40 are on Row B of `PinSocket_2x20_P2.54mm_P15.38mm_Vertical.kicad_mod` | Footprint editor pad inspector |
| **A5** | All 13 project-used GPIO/power nets are on the correct footprint pad (per signal-by-signal table above) | Schematic net inspector |
| **A6** | PCB DRC reports zero errors after netlist sync | KiCad DRC |
| **A7** | Net `+5V` traces from J8 pad 39 to `U1:VIN` in the schematic without interruption | Net inspector |
| **A8** | `hardware/DESIGN.md` updated with a note about the consecutive (non-PICO) pin layout and a reference to the datasheet | Diff review |

---

## Risks

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Physical pin 1 orientation is opposite to assumption → Row A = pins 21–40 | Medium | High | Resolve via A0 before touching any file |
| PCB traces already routed to wrong pads; after footprint renumber, DRC shows airwires | High | Medium | Run "Update PCB from Schematic" and inspect; reroute affected traces; all signals stay on same physical copper islands, only the KiCad net annotation changes |
| `pin_pos()` angle changes missed for switching-side signals → ERC "pin not connected" | Medium | Low | ERC catches immediately after regeneration |
| `PROG_LED` pin type changed from `no_connect` to `output` introduces new ERC warning | Low | Low | The change is correct; ERC should be clean |
| OQ-04 (GPIO positions unverified) means some NC assignments may mask real signals | Medium | Low | NC assignments carry no traces; worst case is a missing net, not a short |

---

## Constitution Compliance

| Principle | Compliance |
|---|---|
| **P-HW-05** — Schematic generated, never hand-edited | All schematic changes go through `components.py` + `generate_project.py`. `.kicad_sch` is only written by the generator. |
| **P-HW-06** — Grid discipline | Symbol `body_w=25.4, body_h=50.8` (multiples of G=2.54). Footprint pad x-coordinates remain on 2.54 mm pitch. Pin endpoint positions computed by `snap()`. |
| **P-HW-01/02** — PCB layer rules | No layer changes. Footprint pads remain on `*.Cu *.Mask` through-hole. No component side change. |
| **P-HW-04** — Board outline and J8 placement | Connector physical footprint coordinates unchanged — only pad numbers change. J8 stays on left edge, 15.38 mm row-to-row, 2.54 mm pin pitch. |
| **P-HW-09** — Polarized connectors | J8 is explicitly exempt (board-to-board, not external cable). No change. |
| **P-DEV-06** — Python style | `components.py` edits follow existing 4-space indentation and comment conventions. |

---

## References

| Resource | Location |
|---|---|
| GitHub issue #133 | https://github.com/nielsverhoeven/PoE-FanController/issues/133 |
| Waveshare ESP32-P4-POE-ETH wiki (pinout diagram) | https://www.waveshare.com/wiki/ESP32-P4-POE-ETH |
| Waveshare board datasheet/schematic | `docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-datasheet.pdf` |
| Board dimensions webp | `docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-details-size-*.webp` |
| KB board reference (§4 pinout, OQ-02 resolution) | `docs/kb/ESP32-P4-POE-ETH/board-reference.md` |
| Generator schematic builder | `hardware/generator/schematic.py` |
| Generator component definitions + wiring | `hardware/generator/components.py` |
| Custom footprint (to be fixed) | `hardware/kicad/footprints/Custom.pretty/PinSocket_2x20_P2.54mm_P15.38mm_Vertical.kicad_mod` |
| Generated schematic (read-only for humans) | `hardware/kicad/PoE-FanController.kicad_sch` |
| Constitution P-HW-05, P-HW-06 | `docs/constitution.md` §3.1 |
