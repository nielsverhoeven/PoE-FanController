# Feature: Route All PCB Traces

**GitHub Issue:** #83 — hw(pcb): route all PCB traces
**Feature path:** `docs/features/route-pcb-traces/`
**Branch:** `feature/148-correct-gpio-pin-assignments`
**Date:** 2026-06-10
**Constitution version referenced:** v4.2.1

---

## Overview

The PoE FanController daughter board PCB has all 33 footprints placed. As of
2026-06-10, after the J8 pin assignment corrections merged via issue #148, the
board carries **invalid legacy signal traces** that cause **35 DRC
`shorting_items`** and **125 `solder_mask_bridge` violations**. These traces
were routed against the pre-correction pad-to-net mapping and must be deleted
before any new routing begins.

The GND copper pour zones (`GND_TOP` on F.Cu, `GND_BOT` on B.Cu) are
**already correctly assigned** to the `GND` net — this was fixed as part of
issue #148 and is **not** a routing task.

This feature completes the PCB by:

1. Deleting all existing invalid signal traces (the source of all current DRC
   shorts).
2. Routing every net to its correct destination using the authoritative J8
   pad-to-net mapping established by issue #148.
3. Performing a GND zone fill so that the design reaches a fabrication-ready
   state: **0 errors, 0 unconnected** in DRC.

The routing scope is exclusively copper — no component moves, no netlist
changes, and no schematic touches are permitted.

---

## User Stories

- As a **PCB fabricator**, I want a complete, DRC-clean Gerber set so that I
  can manufacture the board without any missing connections.
- As a **board assembler**, I want GND copper pours on both layers so that
  ground return paths are low-impedance and heat is distributed across the
  board.
- As a **firmware developer**, I want the board to be electrically complete so
  that I can begin hardware bring-up and firmware validation.
- As a **project maintainer**, I want every routing decision documented and
  reviewable in a committed `.kicad_pcb` file so that future contributors
  understand the rationale for trace layout.

---

## Functional Requirements

1. **FR-01 — All ratsnest cleared.** After deleting old traces and re-routing,
   every previously unconnected item must be resolved by a routed copper trace
   or, where necessary, a via. Zero unconnected items must remain after routing.
   Intentional NC pads (J8 pads 25, 26, 30, 37, 39) are permanently excluded
   — they must never be routed.

2. **FR-02 — Delete invalid legacy traces (PREREQUISITE).** All existing signal
   traces on the PCB (which reflect the pre-#148 incorrect pad-to-net mapping)
   must be deleted as the first action. These traces are the source of 35 DRC
   `shorting_items` and 125 `solder_mask_bridge` violations. No new routing
   may begin until all invalid traces are removed and DRC is re-run to confirm
   the short violations are gone.

   > **Resolved prerequisite — GND zone net assignment:** Both copper pour
   > zones (`GND_TOP` on F.Cu, `GND_BOT` on B.Cu) are already assigned to
   > the `GND` net. This was completed in issue #148 and is confirmed before
   > this branch starts. Zone reassignment is **not** a routing task here.

3. **FR-03 — Power trace width.** All traces carrying power nets (`+5V`,
   `+12V`, `+3V3`, `GND`, `BOOST_SW`) must be **>= 1.0 mm** wide at every
   point along their length.

4. **FR-04 — Signal trace width.** All traces carrying signal nets
   (`FAN1_PWM`–`FAN4_PWM`, `FAN1_TACH`–`FAN4_TACH`, `DHT11_DATA`,
   `DS18B20_DATA`, `/FAN1_IND`–`/FAN4_IND`, `STATUS_LED`, `PROBE_LED`,
   `PROG_LED`, `/LED_A`, `/PROBE_LED_A`, `/PROG_LED_A`) must be **>= 0.25 mm**
   wide.

5. **FR-05 — Layer constraint.** All routed traces must be placed on **F.Cu**.
   B.Cu is reserved for the GND copper pour and for via returns only; no
   signal or power trace segment may be placed entirely on B.Cu.

6. **FR-06 — BOOST_SW loop area minimised.** The `L1 -> U1 -> D1` switching
   loop must be routed with minimal enclosed loop area to limit radiated EMI.
   Traces in this loop must be >= 1.0 mm (power net class).

7. **FR-07 — Zone fill after routing.** After all traces are routed, both GND
   zones must be filled. The filled zones must connect to all GND-net pads
   they overlap without creating isolated islands on either layer.

8. **FR-08 — DRC clean.** After routing and zone fill, DRC must report
   **0 errors** and **0 unconnected** items.

9. **FR-09 — EMAC forbidden pads never routed.** J8 pads 25 (GPIO33 EMAC)
   and 26 (GPIO32 EMAC) are permanently reserved for the Ethernet MAC and must
   carry the `NC` net. No trace may connect to or pass through these pads.
   Similarly, pads 30 (RUN), 37 (EN), and 39 (VSYS) must remain unconnected.

10. **FR-10 — Gerbers regenerated.** After the routed `.kicad_pcb` is
    committed, Gerber and drill files must be regenerated into
    `hardware/kicad/gerbers/` and committed on the same branch.

---

## Non-Functional Requirements

- **NFR-01 — Thermal.** All power traces must carry their rated currents
  within the 1 oz copper (35 µm) specification at >= 1.0 mm width, consistent
  with the <= 3 A trace design limit in the constitution.
- **NFR-02 — EMI.** The BOOST_SW switching node loop area must be minimised
  (FR-06) to stay within conducted and radiated EMI constraints for a
  SELV-class board.
- **NFR-03 — Reproducibility.** The routing result must be committed as a
  `.kicad_pcb` file and reviewed in a pull request so that any contributor
  can verify or reproduce the layout.
- **NFR-04 — No new DRC violations.** The 35 `shorting_items` and 125
  `solder_mask_bridge` violations present in the current baseline must be
  entirely eliminated by deleting the old traces (FR-02). No new violations
  may be introduced by the new routing.

---

## Success Criteria

1. `kicad-cli pcb drc hardware/kicad/PoE-FanController.kicad_pcb` reports **0
   errors** and **0 unconnected** after deleting old traces, re-routing, and
   zone fill.
2. Visual inspection in KiCad PCB editor confirms all ratsnest lines are gone
   and no legacy traces remain.
3. Every power net trace measures >= 1.0 mm on inspection of the `.kicad_pcb`
   XML.
4. Every signal net trace measures >= 0.25 mm on inspection of the `.kicad_pcb`
   XML.
5. All traces are on F.Cu; only vias and GND pours occupy B.Cu.
6. Both zones (`GND_TOP`, `GND_BOT`) show `net "GND"` assignment in the
   `.kicad_pcb` file (already confirmed by issue #148).
7. J8 pads 25, 26, 30, 37, and 39 have no connected tracks in the `.kicad_pcb`
   file.
8. Gerber files in `hardware/kicad/gerbers/` reflect the fully routed board.

---

## J8 Authoritative Pad-to-Net Mapping (Issue #148)

### Row B — pads 21–40 (PCB x ≈ 18.19 mm) — route RIGHT toward fan headers

| Pad | Net | GPIO | Notes |
|-----|-----|------|-------|
| 21 | PROBE_LED | GPIO48 | Route to R15 -> LED6 |
| 22 | FAN4_TACH | GPIO47 | Via R8 pull-up |
| 23 | GND | — | Physical GND |
| 24 | FAN3_TACH | GPIO46 | Via R7 pull-up |
| 25 | NC | GPIO33 | **EMAC FORBIDDEN — never route** |
| 26 | NC | GPIO32 | **EMAC FORBIDDEN — never route** |
| 27 | FAN4_PWM | GPIO27 | Route to J5 pin 4 |
| 28 | GND | — | Physical GND |
| 29 | FAN3_PWM | GPIO26 | Route to J4 pin 4 |
| 30 | NC | RUN | Reserved — no route |
| 31 | FAN2_TACH | GPIO23 | Via R6 pull-up |
| 32 | FAN1_TACH | GPIO22 | Via R5 pull-up |
| 33 | GND | — | Physical GND |
| 34 | FAN2_PWM | GPIO21 | Route to J3 pin 4 |
| 35 | FAN1_PWM | GPIO20 | Route to J2 pin 4 |
| 36 | +3V3 | — | Sole 3.3V source on J8 |
| 37 | NC | EN | Reserved — no route |
| 38 | GND | — | Physical GND |
| 39 | NC | VSYS | No route |
| 40 | +5V | VBUS | Sole 5V source on J8 |

### Row A — pads 1–20 (PCB x ≈ 2.81 mm) — route LEFT then across board

| Pad | Net | GPIO | Notes |
|-----|-----|------|-------|
| 3 | GND | — | Physical GND |
| 6 | STATUS_LED | GPIO2 | Route to R3 -> LED1 |
| 8 | GND | — | Physical GND |
| 13 | GND | — | Physical GND |
| 14 | PROG_LED | GPIO15 | Route to R13 -> LED2 |
| 15 | DHT11_DATA | GPIO16 | Route to J9 pin 2 |
| 18 | GND | — | Physical GND |
| 19 | DS18B20_DATA | GPIO19 | Route via R14 to J6 pin 2 |
| All others | NC | — | No route |

---

## Out of Scope

- Schematic changes — the netlist is frozen after issue #148; `.kicad_sch`
  must not be touched.
- Component placement changes — all 33 footprints are placed; no repositioning
  is permitted.
- GND zone net reassignment — already completed in issue #148.
- Re-evaluation of isolated nets at the schematic level — that is a schematic
  design decision for a future issue.
- Firmware changes.
- BOM or procurement updates.
- Courtyard, silkscreen, or fabrication layer edits beyond what zone fill and
  trace routing inherently produce.
- PCB design rule (`.kicad_dru`) changes.

---

## Assumptions

1. The authoritative J8 pad-to-net mapping is the table established by issue
   #148 (reproduced above). Any discrepancy discovered during routing must be
   documented as a comment in the PR.
2. GND copper pour zones (`GND_TOP` on F.Cu, `GND_BOT` on B.Cu) are already
   assigned to the `GND` net at branch start — confirmed by issue #148. No
   zone reassignment script is needed.
3. The J8 footprint is `Custom:ESP32-P4-PoE-ETH-PinSocket` (renamed from
   `Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical` by Amendment v4.2.1).
   Geometry is unchanged; only the name was updated.
4. The DHT11 breakout (Reichelt 239086) includes an onboard pull-up resistor
   for `DHT11_DATA`; no additional PCB pull-up resistor is needed (see §2.2
   note in constitution v4.2.1).
5. All power nets must be rated for <= 3 A per the constitution copper-weight
   spec; 1.0 mm trace width on 1 oz copper is sufficient for the currents in
   this design.
6. The pcbnew Python API at
   `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe` can
   execute the legacy-trace deletion script (Phase 0) as a documented,
   auditable exception to P-KI-07.

---

## Open Questions

*(None — all [NEEDS CLARIFICATION] items resolved prior to planning.)*
