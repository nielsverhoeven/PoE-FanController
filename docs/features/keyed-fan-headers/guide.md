<!-- Last updated: 2026-06-09 -->

# Feature Guide: Keyed Fan Headers (J2–J5)

**GitHub Issue:** [#100 — Replace fan headers J2–J5 with keyed Molex KK-254 connectors](https://github.com/nielsverhoeven/PoE-FanController/issues/100)
**Branch:** `feature/100-keyed-fan-headers`
**Constitution amendment:** v4.0.0 (MAJOR — §2.2 BOM J2–J5: `47053-1000` → `Molex 22-27-2041`)
**Status:** ✅ Complete — CI PR #129 merged; ERC 0 errors; DRC 0 errors, 16 warnings ≤ baseline

---

## Purpose

The four fan headers J2–J5 previously used a generic unkeyed 1×4 2.54 mm pin header
(`Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical`). A standard 4-pin PC fan
cable housing can be inserted backwards into an unkeyed header, reversing the +12 V / GND
polarity and potentially damaging the fan or the board.

This feature replaces all four footprints with a shrouded, polarised **Molex KK-254** 4-pin
vertical header. The latching shroud makes reverse insertion physically impossible,
satisfying constitution principle **P-HW-09** (amendment v3.2.0) — *"all external cable
connectors must use a mechanically keyed or polarised housing"* — and bringing J2–J5 into
compliance with the policy already applied to J6 (DS18B20 probe connector).

---

## User-Facing Behaviour

- **Assembler / field technician:** A standard 4-pin PC fan cable housing can only be
  inserted in the correct orientation. Attempting reverse insertion is blocked by the
  shroud key tab on the connector body.
- **End user:** No change to fan control, RPM reporting, or web UI behaviour. This is
  a hardware-only change.

---

## Hardware Changes

### Connector specification

| Property | Old (unkeyed) | New (keyed) |
|---|---|---|
| MPN | Molex 47053-1000 | **Molex 22-27-2041** (old p/n AE-6410-04A; 22-23-2041 acceptable equivalent) |
| Footprint | `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` | `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` |
| Pin count | 4 | 4 |
| Pitch | 2.54 mm | 2.54 mm |
| Pad drill | 1.0 mm | 1.19 mm |
| Courtyard (Y span) | ~2 mm | 6.8 mm (shroud body) |
| Housing | Unkeyed, open pin row | Shrouded, polarised latching |
| Mating housing | Any 4-pin 2.54 mm female | Molex 22-01-2042 or standard 4-pin PC fan female |

The footprint comes from the KiCad 10.0.3 standard `Connector_Molex` library — no custom
footprint file is required. J6 (DS18B20 probe connector) already uses the 3-pin sibling
`Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical`, so no new library entry is needed in
`hardware/kicad/fp-lib-table`.

### Pin mapping (unchanged)

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | GND | Ground |
| 2 | +12V | Fan supply (12 V from U_BOOST) |
| 3 | TACH | Tachometer output; 10 kΩ pull-up to +3V3 via R5–R8 |
| 4 | PWM | 25 kHz PWM input from ESP32 LEDC (GPIO4–7) via J8 |

### PCB placement (all four connectors)

| Ref | Position | Rotation | Notes |
|-----|----------|----------|-------|
| J2 | (58, 10) mm | 90° | Shroud key toward board edge (+X direction) |
| J3 | (58, 22) mm | 90° | 12 mm centre-to-centre from J2 |
| J4 | (58, 34) mm | 90° | 12 mm centre-to-centre from J3 |
| J5 | (58, 46) mm | 90° | 12 mm centre-to-centre from J4 |

At rotation 90° the footprint courtyard Y-span (6.8 mm) maps to the board X-direction.
The nearest interior components (TACH pull-ups R5–R8) are at x ≈ 21–35 mm, leaving
~20 mm clearance. DRC confirmed **0 courtyard collisions**.

### Affected schematic sections

The footprint property of each J2–J5 instance was updated in the schematic generator:

- **`hardware/generator/components.py`** — footprint string changed at two sites:
  - `s.define("Custom:Fan_Header", ...)` symbol-level default (line ~175)
  - `s.component(...)` per-instance override inside the `fan_data` loop (lines ~345–347)
- **`hardware/kicad/PoE-FanController.kicad_sch`** — regenerated artefact (never edit
  directly per P-HW-05 / P-KI-04); four J2–J5 instances carry the updated `Footprint`
  property.
- **`hardware/kicad/PoE-FanController.kicad_pcb`** — updated via KiCad 10.0.3 GUI
  (Tools → Update PCB from Schematic, F8), then J2–J5 re-placed at target coordinates.
- **`hardware/kicad/fp-lib-table`** — `Connector_Molex` library entry added (commit
  `feccf6f`) so KiCad resolves `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`.

Net topology is **unchanged** — only the connector body geometry changed.

---

## Firmware Changes

**None.** GPIO assignments (GPIO4–7 PWM, GPIO8–11 TACH), LEDC configuration, TACH ISR
logic, and all REST API endpoints are unaffected by this hardware-only change.

All 22 native unit tests pass without modification (`pio test -e native`).

---

## Web UI Changes

**None.** No new pages, endpoints, or configuration options.

---

## BOM Entry

| Ref | MPN | Description | Footprint |
|-----|-----|-------------|-----------|
| J2–J5 (×4) | **Molex 22-27-2041** | 4-pin 2.54 mm keyed vertical header — Molex KK-254 shrouded latching; AE-6410-04A old p/n; 22-23-2041 acceptable equivalent | `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` |

Full BOM: `hardware/bom/bom.csv`

---

## Constitution Compliance

This feature directly satisfies **P-HW-09** (constitution v3.2.0) for J2–J5 and required
a **MAJOR amendment (v4.0.0)** to §2.2 (BOM-locked components) to update the J2–J5 MPN
from `47053-1000` to `Molex 22-27-2041`. The amendment was applied during Stage 3
(Architecture Validation) at commit `edea822` and recorded in
[`docs/constitution.md`](../../constitution.md).

---

## Test Results Summary

| Gate | Result | Evidence |
|------|--------|----------|
| ERC | ✅ 0 violations | `hardware/kicad/erc_output.json` |
| DRC | ✅ 0 errors, 16 warnings, 0 courtyard collisions | `hardware/kicad/drc_output.json` |
| DRC warnings vs 16-warning baseline | ✅ 16 ≤ 16 | `hardware/kicad/drc_output.json` |
| Native unit tests | ✅ 22/22 pass | `test-results/test-results.md` |
| CI PR #129 | ✅ All 4 checks pass | GitHub Actions |

Full test report: [`test-results/test-results.md`](../../../test-results/test-results.md)

---

## Related Documents

- [`spec.md`](spec.md) — feature requirements and acceptance criteria
- [`plan.md`](plan.md) — technical implementation plan (footprint selection, dimensional analysis)
- [`architecture.md`](architecture.md) — architecture validation and constitution compliance
- [`tasks.md`](tasks.md) — task breakdown with commit references (T001–T009)
- [`hardware/DESIGN.md`](../../../hardware/DESIGN.md) — updated fan header pinout, placement table, and DRC baseline
- [`docs/constitution.md`](../../constitution.md) — §2.2 BOM table (v4.0.0); §10 amendment history
