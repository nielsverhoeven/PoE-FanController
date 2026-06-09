# Feature: Route All PCB Traces

**GitHub Issue:** #83 — hw(pcb): route all PCB traces (51 unconnected ratsnest)
**Feature path:** `docs/features/route-pcb-traces/`
**Branch:** `feature/83-route-pcb-traces`
**Date:** 2026-06-09
**Constitution version referenced:** v4.1.0

---

## Overview

The PoE FanController daughter board PCB has all 33 footprints placed and
passing DRC with 0 errors, but as of 2026-06-09 (after PR #136 merged) the
board carries **70 unconnected ratsnest items** across 26 nets. No copper
trace exists between any pad pair. This feature completes the PCB by routing
every net, reassigning the GND copper pour zones from the isolated
`Net-(U1-GND)` net to `GND`, and performing a zone fill so that the design
reaches a fabrication-ready state: **0 errors, 0 unconnected** in DRC. The
routing scope is exclusively copper — no component moves, no netlist changes,
and no schematic touches are permitted.

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

1. **FR-01 — All ratsnest cleared.** Every ratsnest item (70 as of the issue
   baseline) must be resolved by a routed copper trace or, where necessary, a
   via. Zero unconnected items must remain after routing.

2. **FR-02 — GND zone net reassignment.** Both copper pour zones —
   `GND_TOP` (F.Cu) and `GND_BOT` (B.Cu) — must be reassigned from
   `Net-(U1-GND)` to the `GND` net before the zone fill is executed.

3. **FR-03 — Power trace width.** All traces carrying power nets (`+5V`,
   `+12V`, `+3V3`, `GND`, `BOOST_SW`) must be **≥ 1.0 mm** wide at every
   point along their length.

4. **FR-04 — Signal trace width.** All traces carrying signal nets
   (`FAN1_PWM`–`FAN4_PWM`, `FAN1_TACH`–`FAN4_TACH`, `DHT11_DATA`,
   `DS18B20_DATA`, `/FAN1_IND`–`/FAN4_IND`, `STATUS_LED`, `PROBE_LED`,
   `PROG_LED`, `/LED_A`, `/PROBE_LED_A`, `/PROG_LED_A`) must be **≥ 0.25 mm**
   wide.

5. **FR-05 — Layer constraint.** All routed traces must be placed on **F.Cu**.
   B.Cu is reserved for the GND copper pour and for via returns only; no
   signal or power trace segment may be placed entirely on B.Cu.

6. **FR-06 — BOOST_SW loop area minimised.** The `L1 → U1 → D1` switching
   loop must be routed with minimal enclosed loop area to limit radiated EMI.
   Traces in this loop must be ≥ 1.0 mm (power net class).

7. **FR-07 — Zone fill after routing.** After all traces are routed, both GND
   zones must be filled. The filled zones must connect to all GND-net pads
   they overlap without creating isolated islands on either layer.

8. **FR-08 — DRC clean.** After routing and zone fill, DRC must report
   **0 errors** and **0 unconnected** items. Pre-existing silk/library
   warnings (16 warnings in the current baseline report) must not increase in
   count.

9. **FR-09 — Net-(U1-GND) isolation preserved.** The `Net-(U1-GND)` net
   (U1's isolated GND pin) must remain a distinct net in the netlist. No
   trace may connect it to the `GND` net. Only the zone net assignment is
   changed (FR-02); the component pin net is untouched.

10. **FR-10 — Gerbers regenerated.** After the routed `.kicad_pcb` is
    committed, Gerber and drill files must be regenerated into
    `hardware/kicad/gerbers/` and committed on the same branch.

---

## Non-Functional Requirements

- **NFR-01 — Thermal.** All power traces must carry their rated currents
  within the 1 oz copper (35 µm) specification at ≥ 1.0 mm width, consistent
  with the ≤ 3 A trace design limit in the constitution.
- **NFR-02 — EMI.** The BOOST_SW switching node loop area must be minimised
  (FR-06) to stay within conducted and radiated EMI constraints for a
  SELV-class board.
- **NFR-03 — Reproducibility.** The routing result must be committed as a
  `.kicad_pcb` file and reviewed in a pull request so that any contributor
  can verify or reproduce the layout.
- **NFR-04 — No new DRC violations.** The count of pre-existing DRC warnings
  (16 in the current baseline) must not increase. The two `isolated_copper`
  warnings for `Net-(U1-GND)` zones must be eliminated by the zone
  reassignment.

---

## Success Criteria

1. `kicad-cli pcb drc hardware/kicad/PoE-FanController.kicad_pcb` reports **0
   errors** and **0 unconnected** after routing and zone fill.
2. Visual inspection in KiCad PCB editor confirms all ratsnest lines are gone.
3. Every power net trace measures ≥ 1.0 mm on inspection of the `.kicad_pcb`
   XML.
4. Every signal net trace measures ≥ 0.25 mm on inspection of the `.kicad_pcb`
   XML.
5. All traces are on F.Cu; only vias and GND pours occupy B.Cu.
6. Both zones (`GND_TOP`, `GND_BOT`) show `net "GND"` assignment in the
   `.kicad_pcb` file, not `net "Net-(U1-GND)"`.
7. The two `isolated_copper` DRC warnings present in the baseline are gone
   from the post-routing DRC report.
8. Gerber files in `hardware/kicad/gerbers/` reflect the routed board.

---

## Out of Scope

- Schematic changes — the netlist is frozen after PR #136; the `.kicad_sch`
  must not be touched.
- Component placement changes — all 33 footprints are placed; no repositioning
  is permitted.
- Re-evaluation of the `Net-(U1-GND)` isolation intent at the schematic level
  — that is a schematic design decision for a future issue.
- Firmware changes.
- BOM or procurement updates.
- Courtyard, silkscreen, or fabrication layer edits beyond what the zone fill
  and trace routing inherently produce.
- PCB design rule (`.kicad_dru`) changes.

---

## Assumptions

1. The 70-item ratsnest count is the correct baseline as of the branch start.
   Any discrepancy discovered during routing must be documented as a comment in
   the PR.
2. `Net-(U1-GND)` is intentionally isolated at the schematic level and must
   not receive a routed connection to `GND`. Only the zone assignment is
   corrected.
3. The DHT11 breakout (Reichelt 239086) includes an onboard pull-up resistor
   for `DHT11_DATA`; no additional PCB pull-up resistor is needed (see §2.2
   note in constitution v4.1.0).
4. All power nets must be rated for ≤ 3 A per the constitution's copper-weight
   spec; 1.0 mm trace width on 1 oz copper is sufficient for the currents in
   this design.
5. The pcbnew Python API at
   `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe` can
   execute the GND zone reassignment script (Phase 1) even though the
   interactive router is the primary routing tool. See plan §6 (Risks) for the
   P-KI-07 tension.

---

## Open Questions

*(None — all [NEEDS CLARIFICATION] items resolved prior to planning.)*
