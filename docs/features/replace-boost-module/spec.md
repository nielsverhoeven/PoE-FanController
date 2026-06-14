# Feature: Replace Discrete Boost Converter Stage with Module (Issue #177)

<!-- feature: replace-boost-module | issue: #177 | branch: feature/177-replace-boost-converter-module -->

---

## Overview

The current 5 V → 12 V boost converter is implemented using five discrete through-hole components
(U1 LM2587-12 IC, L1 100 µH inductor, D1 1N5822 Schottky diode, C1 100 µF input capacitor,
C2 100 µF output capacitor). These occupy the full right zone of the PCB right zone
(x = 33.19–56 mm), require careful inductor placement for EMC, and contribute significantly to
hand-assembly complexity.

This feature replaces all five discrete components with a single off-the-shelf DC-DC Step-Up
Boost Converter daughter board module (Amazon.nl B0D9VJKD1L). The module exposes a
**4-pin, 2.54 mm pitch THT interface** (IN+, IN−, OUT+, OUT−), contains all boost-converter
circuitry internally (including the switching IC, inductor, Schottky diode, input and output
capacitors, and an adjustable-output trimmer), and mounts in the same PCB right zone.
The change reduces the daughter board component count by five parts, eliminates
inductor-winding EMC concerns, and simplifies future procurement to a single line item.

---

## User Stories

- As a **builder**, I want to solder a single 4-pin module instead of five discrete parts, so that
  board assembly is faster and less error-prone.
- As a **procurer**, I want a single BOM line item for the boost stage, so that sourcing is reduced
  to one purchase from a single supplier.
- As a **hardware maintainer**, I want the schematic generator to reflect the module topology
  faithfully, so that ERC remains clean and future reviewers understand the power chain correctly.

---

## Functional Requirements

1. **FR-01 — Retire discrete boost components.** Schematic symbols for U1 (LM2587-12), L1 (100 µH
   inductor), D1 (1N5822 Schottky), C1 (100 µF/25 V), and C2 (100 µF/25 V) shall be removed from
   the generated schematic. Their PCB footprints shall be removed from `PoE-FanController.kicad_pcb`.

2. **FR-02 — R5 is not retired.** R5 is the FAN1 TACH pull-up resistor (10 kΩ, +3V3 → FAN1_TACH).
   It is unrelated to the boost converter circuit. R5 shall remain in the schematic, BOM, and PCB
   layout unchanged. (The issue body reference to "R5 feedback resistor" reflects a naming confusion;
   the LM2587-12 FB pin is tied directly to +12V in the generator — there is no separate feedback
   resistor component in the schematic.)

3. **FR-03 — Add module schematic symbol.** A new schematic symbol `Custom:DC_Boost_Module` with
   four pins shall be added to the generator:
   - Pin 1: IN+  → net `+5V`
   - Pin 2: IN−  → net `GND`
   - Pin 3: OUT+ → net `+12V`  (power source, `pin_type="power_out"`)
   - Pin 4: OUT− → net `GND`

4. **FR-04 — Add U_BOOST component instance.** The generator shall instantiate the new symbol as
   reference designator `U_BOOST` with value `DC-Boost-Module` and footprint
   `Custom:DC-Boost-Module`.

5. **FR-05 — Create custom PCB footprint.** A new footprint file
   `hardware/kicad/footprints/Custom.pretty/DC-Boost-Module.kicad_mod` shall be created matching
   the module's physical 4-pin 2.54 mm pitch THT header. Physical dimensions of the received
   module (typical ~28 mm × 17 mm for this class) must be verified against the actual unit before
   finalising courtyard bounds.

6. **FR-06 — PCB placement in right zone.** U_BOOST shall be placed in the right zone
   (x = 33.19–56 mm) of the PCB, within the area vacated by the retired discrete components.
   The footprint courtyard must not overlap with J8, J2–J5, R5–R8, or any other retained component.

7. **FR-07 — Net connections.** The four U_BOOST pads shall be routed to:
   - IN+ → `+5V` (power trace, ≥ 1.0 mm per P-HW-07)
   - IN− → `GND` (power trace, ≥ 1.0 mm)
   - OUT+ → `+12V` (power trace, ≥ 1.0 mm)
   - OUT− → `GND` (power trace, ≥ 1.0 mm)

8. **FR-08 — BOM update.** `hardware/generator/bom.py` and `hardware/bom/bom.csv` shall:
   - Remove entries for U1, L1, D1, C1, C2.
   - Add one entry for U_BOOST: Amazon.nl B0D9VJKD1L, 4-pin 2.54 mm THT DC-DC boost module.

9. **FR-09 — Constitution amendment.** The constitution (`docs/constitution.md`) §2.2 BOM table
   shall be amended (MAJOR) to:
   - Remove the placeholder `U_BOOST` row (currently pointing to "e.g. TI LM2587-12 or TI TPS61085").
   - Add a locked `U_BOOST` row: Amazon.nl B0D9VJKD1L, DC-DC Boost Module, 4-pin 2.54 mm THT.
   - Update the P-HW-04 right-zone description to remove "U1+L1+D1+C1+C2 (boost converter chain)"
     and replace with "U_BOOST (DC-DC boost module)".

10. **FR-10 — ERC passes.** The regenerated schematic shall produce zero ERC errors when run via
    `kicad-cli sch erc`. ERC output shall be committed to `hardware/kicad/erc_output.json`.

11. **FR-11 — DRC passes.** The updated PCB layout shall produce zero DRC errors (clearance,
    unconnected nets, courtyard, footprint validity) when run via `kicad-cli pcb drc`.

12. **FR-12 — KB file committed.** `docs/kb/DC-DC-boost-module.md` (currently untracked on the
    branch) shall be staged and committed before or alongside the generator changes.

---

## Non-Functional Requirements

- **NFR-01 — Output current capacity.** The module must be capable of sustaining ≥ 1.2 A at 12 V
  (4 fans × 0.3 A typical). The B0D9VJKD1L is rated 2 A max output — margin is 40%.
- **NFR-02 — Efficiency.** The module shall operate at ≥ 90% efficiency at 1.2 A / 12 V load to
  remain within the PoE Class 4 power budget (20 W hard cap, §5.2).
- **NFR-03 — Output voltage.** The module output trimmer shall be set to 12.0 V ± 0.3 V at
  no-load before PCB installation, verified with a bench power supply at 5 V input.
- **NFR-04 — All components on F.Cu only (P-HW-02).** The U_BOOST footprint must place all pads
  on F.Cu (top copper). No pad, via, or courtyard element may land on B.Cu.
- **NFR-05 — Right zone only (P-HW-04 / zero-crossing rule).** No trace from U_BOOST may cross
  x < 33.19 mm (the J8 Row B boundary). +5V, GND, and +12V pour connections must be made
  entirely at x ≥ 33.19 mm.
- **NFR-06 — Power trace width.** All traces carrying boost-converter input (+5V) or output (+12V)
  currents shall use ≥ 1.0 mm copper width, per P-HW-07 power net class.
- **NFR-07 — Schematic readability.** The new boost section header shall comply with P-SCH-03
  (bold, 2.54 mm, blue). The IN+/OUT+ pins shall use `pin_type="power_out"` for the `+12V`
  driver role (P-SCH-04).

---

## Success Criteria

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| SC-01 | `python hardware/generate_project.py` completes without error | Run locally; inspect console output |
| SC-02 | Generated schematic contains symbol `U_BOOST` with 4 pins connected to +5V, GND, +12V, GND | Open `.kicad_sch` in KiCad or inspect JSON |
| SC-03 | Generated schematic contains no symbols for U1, L1, D1, C1, or C2 | Open `.kicad_sch`; search for old refs |
| SC-04 | ERC reports zero errors | `hardware/kicad/erc_output.json` shows `"error_count": 0` |
| SC-05 | PCB contains footprint `Custom:DC-Boost-Module` at ref `U_BOOST` | Open `.kicad_pcb` in KiCad |
| SC-06 | PCB contains no footprints for U1, L1, D1, C1, or C2 | Open `.kicad_pcb`; search for old refs |
| SC-07 | DRC reports zero errors | DRC report (no unconnected nets, no courtyard violations, no clearance errors) |
| SC-08 | U_BOOST is placed entirely within x = 33.19–56 mm | KiCad footprint placement inspector |
| SC-09 | Power traces (IN+, IN−, OUT+, OUT−) are ≥ 1.0 mm wide | KiCad DRC net-class check |
| SC-10 | `hardware/bom/bom.csv` contains U_BOOST row; contains no rows for U1/L1/D1/C1/C2 | Open CSV; grep |
| SC-11 | Module output voltage pre-set to 12 V ± 0.3 V at 5 V input | Bench measurement before install |
| SC-12 | Fan rail carries ≥ 1.2 A at 12 V in bring-up test (all 4 fans at 100%) | Ammeter on +12V rail during bring-up step 10 |
| SC-13 | `docs/kb/DC-DC-boost-module.md` is committed to the branch | `git log --oneline` shows commit |
| SC-14 | Constitution §2.2 contains locked `U_BOOST` row with MPN `B0D9VJKD1L` | Open `docs/constitution.md` |

---

## Out of Scope

- Output voltage adjustment algorithm or automatic trim via firmware (the module uses a physical
  trimmer potentiometer; no firmware involvement).
- Any change to R5–R8 (TACH pull-ups), J2–J5 (fan headers), or any other retained component.
- Any firmware change: the power chain change is entirely transparent to firmware.
- Any PoE primary-side change (no change to Waveshare SKU 32088 role or power delivery).
- Gerber regeneration (P-KI-06 requires regeneration after PCB change, but this is tracked
  separately as a release gate, not as part of this feature's implementation steps).

---

## Assumptions

- A1. The Waveshare ESP32-P4-POE-ETH (SKU 32088) J8 pin 40 (VBUS) can supply ≥ 3.1 A at 5 V
  (required for 1.2 A @ 12 V at 93% efficiency). This is listed as "MEDIUM confidence" in the
  constitution. If the VBUS current limit is below 3.1 A, the feature cannot be implemented as
  specified without additional power design. **Verification is required before PCB fabrication.**
- A2. The physical module (Amazon.nl B0D9VJKD1L) dimensions are approximately 28 mm × 17 mm,
  consistent with the MT3608/XL6009-class mini boost modules documented in the KB. The exact
  dimensions must be verified against the received unit before the footprint is finalised.
- A3. The module's 4-pin header pin ordering (IN+, IN−, OUT+, OUT−) matches the KB and Amazon
  product description. This must be confirmed against the physical unit before soldering.
- A4. The module's trimmer can be pre-set to 12 V with a screwdriver before board installation;
  no other trim hardware is required on the daughter board.
- A5. The `Custom:DC_Boost_Module` symbol will be defined entirely within
  `hardware/generator/components.py`; no separate KiCad `.kicad_sym` file is required.

---

## Open Questions

None. All [NEEDS CLARIFICATION] items resolved during spec drafting:
- R5 retirement scope: **R5 is not retired** (confirmed from generator code — R5 is TACH pull-up;
  no separate boost feedback resistor exists in the schematic).
- Module identity: **B0D9VJKD1L** is the approved boost module (LM2596S-ADJ in the issue title
  is a naming error; the LM2596S-ADJ is a buck converter and is rejected per KB).
- Footprint name: **`Custom:DC-Boost-Module`** (from `docs/kb/DC-DC-boost-module.md`).
- KB file path: **`docs/kb/DC-DC-boost-module.md`** (the issue body references a non-existent
  `docs/kb/LM2596S-ADJ-module.md`; the correct path is confirmed from the branch).
