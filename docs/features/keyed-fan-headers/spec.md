# Feature: Keyed Fan Headers (J2–J5)

**GitHub Issue:** #100 — Replace fan headers with keyed 4-pin female headers to enforce correct connector orientation
**Feature path:** `docs/features/keyed-fan-headers/`
**Branch:** `feature/100-keyed-fan-headers`
**Date:** 2026-06-09

---

## Overview

The four fan connector footprints J2–J5 currently use generic, unkeyed 1×4 2.54 mm pin headers
(`Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical`). A standard 4-pin PC fan cable
housing can be plugged into these backwards, reversing the +12 V / GND polarity and potentially
damaging fans or the PCB. This feature replaces the four footprints with a shrouded, keyed Molex
KK-254 compatible 4-pin vertical header, making reverse insertion physically impossible. The
change satisfies the mandate in constitution principle P-HW-09 (amendment v3.2.0), which
explicitly requires polarised/keyed housings for all external cable connectors on the daughter
board, and brings J2–J5 into compliance with the policy already applied to J6 (DS18B20 probe
connector).

---

## User Stories

- As a **board assembler**, I want fan connectors that cannot be plugged in backwards so that I do
  not accidentally damage fans or the PCB during assembly.
- As a **field technician**, I want a physical key on each fan connector so that I can attach fan
  cables in the dark or under cable clutter without verifying polarity visually.
- As a **project maintainer**, I want J2–J5 to use the same Molex KK-254 connector family already
  used on J6 so that the BOM and assembly process remain consistent.

---

## Functional Requirements

1. **FR-01 — Keyed footprint.** J2, J3, J4, and J5 must use a shrouded/keyed 1×4 2.54 mm pitch
   Molex KK-254 compatible footprint that accepts the standard 4-pin PC fan female housing and
   physically prevents reverse insertion.
2. **FR-02 — Pin mapping preserved.** Pin numbering and net assignment must remain unchanged:
   Pin 1 = GND, Pin 2 = VCC_FAN (+12 V), Pin 3 = TACH, Pin 4 = PWM.
3. **FR-03 — Generator source of truth.** The footprint string in the schematic generator package
   (`hardware/generator/components.py`) must be updated before any schematic file is changed.
   The `.kicad_sch` must be the product of re-running `python hardware/generate_project.py`.
4. **FR-04 — PCB footprint swap.** The four PCB footprints must be updated to match the new
   schematic footprint. All four must be placed on the PCB with a courtyard that does not overlap
   any adjacent component courtyard.
5. **FR-05 — Key tab orientation.** The shroud key tab on each of J2–J5 must face the board edge
   (cable exit toward the side cut-out), not toward the interior of the board.
6. **FR-06 — ERC clean.** After schematic regeneration, ERC must report 0 violations.
7. **FR-07 — DRC clean.** After PCB update and placement, DRC must report 0 errors and
   0 unconnected items (routing is PENDING per `ROUTING_PENDING.md`; the baseline 16 warnings
   must not increase).
8. **FR-08 — BOM entry updated.** The §2.2 BOM entry for J2–J5 must be amended from `47053-1000`
   to the keyed KK-254 compatible MPN (`22-23-2041` or `22-27-2041`) before PCB fabrication.

---

## Non-Functional Requirements

- **NFR-01 — No power-budget impact.** The footprint swap introduces no new power consumers;
  power budget in §5.2 of the constitution is unaffected.
- **NFR-02 — No firmware changes.** PWM, TACH, and GPIO assignments are unchanged; no firmware
  modification is required.
- **NFR-03 — No isolation concern.** J2–J5 are entirely on the SELV secondary side; no isolation
  analysis is required.
- **NFR-04 — Mechanical fit.** The shrouded connector body must fit within the board outline and
  side-edge cut-out envelope used for cable access, without requiring a board outline change.
- **NFR-05 — Standard library only (preferred).** The target footprint must come from the KiCad
  10.0 standard `Connector_Molex` library. A custom footprint in `hardware/kicad/footprints/Custom.pretty/`
  is permitted only if no standard library footprint matches the pad layout.

---

## Success Criteria

| # | Criterion | How to verify |
|---|-----------|---------------|
| SC-01 | J2–J5 footprints are keyed Molex KK-254 1×4 | Inspect footprint property in KiCad schematic and PCB |
| SC-02 | A 4-pin fan cable housing cannot be inserted backwards | Physical fit check against connector datasheet drawing |
| SC-03 | Pin 1 = GND, Pin 2 = +12V, Pin 3 = TACH, Pin 4 = PWM on all four headers | Net inspector in KiCad PCB |
| SC-04 | ERC: 0 violations | `kicad-cli sch erc` output, saved to `erc_output.json` |
| SC-05 | DRC: 0 errors, 0 unconnected items | `kicad-cli pcb drc` output, saved to `drc_output.json` |
| SC-06 | DRC baseline warnings do not increase beyond 16 | Compare DRC warning count with baseline in `drc_current.json` |
| SC-07 | No courtyard overlaps between J2–J5 and adjacent components | DRC courtyard check passes |
| SC-08 | Changes are committed to `feature/100-keyed-fan-headers`, not `main` | Git log |

---

## Out of Scope

- Changes to fan PWM frequency, TACH wiring, or firmware logic.
- Replacing the connector family (e.g., switching to JST XH or screw terminals).
- Modifying the board outline or repositioning the J8 header.
- Routing copper traces (routing is deferred; see `hardware/kicad/ROUTING_PENDING.md`).
- Changes to any component other than the J2–J5 footprints.

---

## Assumptions

- KiCad 10.0.3 is installed locally at `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\`.
- The `Connector_Molex` standard library is accessible from the installed KiCad instance.
- The current PCB baseline (16 DRC warnings, 0 DRC errors, 71 unconnected due to ROUTING_PENDING)
  is the accepted starting state.
- The key-tab direction "facing the board edge" is achievable at the current J2–J5 positions
  (x ≈ 58 mm, y = 10/22/34/46 mm, rotation = 90°) without repositioning.

---

## Open Questions

None — all key decisions are resolved by the footprint availability check documented in the
technical plan (`plan.md`).
