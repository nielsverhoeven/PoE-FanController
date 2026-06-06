# Technical Plan: PCB — Add Missing SMD Passive Footprints to Generator

**GitHub Issue:** #13 — "PCB: add missing SMD passive footprints to generator (C3-C7, R1-R10, LED1, SW1/2, NTC1)"
**Feature path:** `docs/features/pcb-passive-footprints/`
**Branch:** `feature/13-missing-passive-footprints`
**Date:** 2026-06-06
**Constitution version referenced:** 1.0.1

---

## 1. Problem Statement

`hardware/generate_project.py` defines 34 component instances in `build_schematic()` but only
embeds 15 footprints in `write_pcb()`. The 19 missing footprints generate one
`missing_footprint` DRC violation each, for a total of **19 violations** against the PR #12
baseline of 36.

This plan adds the 19 missing `embed_footprint()` calls — and documents all coordinate, library,
and BOM decisions necessary for an implementer to execute the change with no ambiguity.

---

## 2. Architecture Fit

### 2.1 Constitution Principles Governing This Work

| Principle | Rule | Relevance to This Issue |
|-----------|------|------------------------|
| **P-HW-02** | All components on F.Cu only | Every new `embed_footprint()` call writes to F.Cu; THT pads drill through but body layer is F.Cu |
| **P-HW-05 / P-KI-04** | Generator is the single source of truth | Only `write_pcb()` and `write_bom()` in `generate_project.py` may be modified; `.kicad_pcb` and `.kicad_sch` are build artefacts |
| **P-HW-06** | Grid discipline | All footprint origin coordinates must be on the 0.1 mm grid (all coordinates in this plan are on a 0.5 mm grid, a strict subset) |
| **P-ISO-02 / P-ISO-03** | Isolation barrier at x = 38 mm; 3 mm creepage/clearance | Every new component centre must be x > 38 mm; all pad copper must be ≥ 3 mm from x = 38 mm |
| **P-ISO-05** | No secondary signals may cross the barrier | Confirmed: all 19 missing components connect exclusively to secondary-side nets |
| **P-TEST-01 / P-TEST-02** | Zero ERC errors; ERC output recorded | Schematic is unchanged so ERC re-run is a verification step only |
| **P-TEST-03 / P-TEST-04** | Zero DRC errors (long-term); DRC run before Gerbers | Acceptance criterion is `missing_footprint` = 0 and total violations ≤ 36 (the pre-routing DRC baseline) |
| **P-DEV-01** | Commit convention | All commits: `hw: <subject>` |
| **P-DEV-04** | Constitution amendments required for any deviation | See §3 — THT decision explicitly avoids the need for an amendment |

### 2.2 Board Coordinate System (reminder)

```
Canvas: 100 × 80 mm
Usable PCB outline (Edge.Cuts): x[5, 95], y[5, 75]
Isolation barrier: x = 38 mm (dashed line on Cmts.User layer)
GND pours (F.Cu and B.Cu): start at x = 40 mm (2 mm buffer inside barrier)
ESP32 antenna keepout: x[41, 89] y[22.26, 43.2] — no courtyard may overlap this zone
ESP32 module body courtyard: x[55.25, 74.75] y[43.2, 63.51]
```

---

## 3. THT vs SMD Decision for LED1, SW1, SW2, NTC1

### 3.1 Decision: **Retain THT as defined in `build_schematic()`**

**Choice: Option A — no schematic changes.**

### 3.2 Rationale

| Factor | Analysis |
|--------|----------|
| **Schematic cost** | LED1, SW1, SW2, and NTC1 are already defined with THT footprints in `build_schematic()` (lines 514–530). Retaining THT requires zero schematic changes — no `s.define(...)` edits, no BOM MPN updates, no constitution amendment (P-DEV-04). |
| **Assembly process** | The board already requires THT assembly for L1 (Axial), D1 (DO-201AD), C1/C2 (radial electrolytic), and J6 (USB-C THT). Adding four more THT parts does not introduce a new assembly process step. |
| **P-HW-02 compliance** | THT component bodies sit on F.Cu (top). Solder joints on B.Cu are inherent to THT and do not violate P-HW-02, which prohibits component bodies on B.Cu — not THT through-holes. This is consistent with the existing THT population (L1, D1, C1, C2, J6). |
| **SW1/SW2 mechanical** | SW_PUSH_6mm THT switches have superior mechanical stability for repeated pressing during firmware development. SMD equivalents require hand-soldering jigs. |
| **Space availability** | Zone C (x[40, 95] y[64.5, 74]) provides 55 × 9.5 mm — sufficient for SW1 (8 × 8 mm) + SW2 (8 × 8 mm) + LED1 (4 × 4 mm) + NTC1 (12.5 × 4 mm) with ≥ 0.5 mm inter-courtyard gaps (verified §5). |
| **P-DEV-04 avoidance** | SMD conversion would require a constitution amendment and `kicad.expert` consultation. THT avoids this entirely. |

### 3.3 What this means for the implementer

- **`build_schematic()` is not modified.**
- **BOM footprint columns are unchanged** (generator already lists correct THT footprint strings for these four refs).
- **Only `write_pcb()` is extended** — 19 new `embed_footprint()` calls are added to the `fps` list.
- **Only `write_bom()` is extended** — MPN fields for the 19 components are populated (§7).

---

## 4. Exact Footprint Library Strings

All strings match the KiCad 10 standard library. Paths are relative to
`KICAD_FP_BASE = C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\`.

| Component(s) | `embed_footprint(lib_name, fp_name, ...)` | Library `.pretty` folder |
|---|---|---|
| C3, C4, C5, C6, C7 | `"Capacitor_SMD"`, `"C_0402_1005Metric"` | `Capacitor_SMD.pretty` |
| R1 – R10 | `"Resistor_SMD"`, `"R_0402_1005Metric"` | `Resistor_SMD.pretty` |
| LED1 | `"LED_THT"`, `"LED_D3.0mm"` | `LED_THT.pretty` |
| SW1, SW2 | `"Button_Switch_THT"`, `"SW_PUSH_6mm"` | `Button_Switch_THT.pretty` |
| NTC1 | `"Resistor_THT"`, `"R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"` | `Resistor_THT.pretty` |

> These library names match what is already used in `build_schematic()` lines 491–530 and
> what `write_bom()` uses. No custom or out-of-project footprint libraries are needed.

---

## 5. Placement Zones Reference

```
Board top edge (y = 5 mm)
  ┌──────────────────────────────────────────────────────────────────────────────────────┐
  │  J1   │       J2     J3     J4     J5        J6                                      │
  │  RJ45 │       fan    fan    fan    fan        USB-C                                  │  y≈5–17
  ├────────┼──────────────────────────────────────────────────────────────────────────────┤
  │PRIMARY │ [Zone A: y[17.5,21.5] ─ between fan headers and above ESP32 antenna keepout] │  y≈17–22
  │  SIDE  ├──────────────────────────────────────────────────────────────────────────────┤
  │x<38mm  │ [ESP32 ANTENNA KEEPOUT: x[41,89] y[22.26,43.2] — NO COMPONENTS INSIDE]      │  y≈22–43
  │        ├──────────────────────────────────────────────────────────────────────────────┤
  │  U1    │ [Zone B: x[40,54.75] y[43.5,63.5] ─ left of ESP32 body, below keepout]      │
  │        │          U3 ESP32-WROOM-32 body         │    U4 CH340C                      │  y≈43–64
  │  U2    │                                          │                                  │
  │  L1 D1 ├──────────────────────────────────────────────────────────────────────────────┤
  │  C1 C2 │ [Zone C: x[40,95] y[64.5,74] ─ below ESP32 body bottom and U4 bottom]       │  y≈64–74
  └────────┴──────────────────────────────────────────────────────────────────────────────┘
                                                                              board bottom y=75
```

**Zone assignments for the 19 missing components:**

| Zone | Assigned components | Rationale |
|------|---------------------|-----------|
| **Zone A** | R5, R6, R7, R8 | Fan TACH pull-ups sit directly above their associated fan headers (J2–J5). 4 mm strip cleared by J2–J5 courtyard bottoms at y = 17.01 mm. Below ESP32 antenna keepout (keepout starts at y = 22.26). |
| **Zone B** | R1, R2, R3, R4, C3, C4, C5, C6 | ESP32-adjacent: R1/R2 (EN/BOOT pull-ups), R3 (LED resistor), R4 (NTC divider top half), C3–C6 (ESP32 3.3 V decoupling). Packed in two columns at x = 45 and x = 52, rows at y = 47/50/53/56. |
| **Zone C** | C7, R9, R10, SW1, SW2, LED1, NTC1 | C7 (CH340C V3 decoupling) near U4; R9/R10 (USB-C CC pull-downs) near J6/U4; SW1/SW2/LED1/NTC1 user-accessible in the southern open area. |

---

## 6. Coordinate Table (All 19 Components)

**Courtyard abbreviations:** CY = courtyard (absolute mm on PCB canvas).

> 0402 SMD courtyard model: 3.2 × 2.0 mm centred on the component origin
> (±1.6 mm in X, ±1.0 mm in Y).

### 6.1 Zone A — Fan tachometer pull-up resistors (R5–R8)

| Ref | cx | cy | rot | Footprint | Courtyard X | Courtyard Y | Gap to nearest existing |
|-----|----|----|-----|-----------|-------------|-------------|------------------------|
| R5 | 51.5 | 19.5 | 0° | `Resistor_SMD:R_0402_1005Metric` | [49.9, 53.1] | [18.5, 20.5] | 1.55 mm right of J2 (48.35) |
| R6 | 62.1 | 19.5 | 0° | `Resistor_SMD:R_0402_1005Metric` | [60.5, 63.7] | [18.5, 20.5] | 1.45 mm right of J3 (59.05) |
| R7 | 72.8 | 19.5 | 0° | `Resistor_SMD:R_0402_1005Metric` | [71.2, 74.4] | [18.5, 20.5] | 1.55 mm right of J4 (69.65) |
| R8 | 92.0 | 19.5 | 0° | `Resistor_SMD:R_0402_1005Metric` | [90.4, 93.6] | [18.5, 20.5] | 3.33 mm below J6 (y=15.17); 1.4 mm right of antenna keepout (x=89) |

**R8 placement note:** The space between J5 (right edge x = 80.35) and J6 (left edge x ≈ 81.0) is
only 0.65 mm — too narrow for a 0402 courtyard (3.2 mm). The next available window east of J6 and
east of the antenna keepout (x > 89.0) places R8 at x = 92.0, within 2 mm of the board right edge
clearance and satisfying all keepout rules. The FAN4_TACH trace will be longer than the others but
this is acceptable pre-routing (routing is out of scope for this issue).

### 6.2 Zone B — ESP32 support resistors and decoupling caps (R1–R4, C3–C6)

Two-column layout: resistors at x = 45.0, caps at x = 52.0; four rows at y = 47.0/50.0/53.0/56.0.

| Ref | cx | cy | rot | Footprint | Courtyard X | Courtyard Y | Function |
|-----|----|----|-----|-----------|-------------|-------------|----------|
| R1 | 45.0 | 47.0 | 0° | `Resistor_SMD:R_0402_1005Metric` | [43.4, 46.6] | [46.0, 48.0] | ESP32 EN pull-up (10 kΩ) |
| R2 | 45.0 | 50.0 | 0° | `Resistor_SMD:R_0402_1005Metric` | [43.4, 46.6] | [49.0, 51.0] | ESP32 IO0/BOOT pull-up (10 kΩ) |
| R3 | 45.0 | 53.0 | 0° | `Resistor_SMD:R_0402_1005Metric` | [43.4, 46.6] | [52.0, 54.0] | Status LED current limit (330 Ω) |
| R4 | 45.0 | 56.0 | 0° | `Resistor_SMD:R_0402_1005Metric` | [43.4, 46.6] | [55.0, 57.0] | NTC voltage divider top half (10 kΩ) |
| C3 | 52.0 | 47.0 | 0° | `Capacitor_SMD:C_0402_1005Metric` | [50.4, 53.6] | [46.0, 48.0] | ESP32 +3V3 decoupling (100 nF) |
| C4 | 52.0 | 50.0 | 0° | `Capacitor_SMD:C_0402_1005Metric` | [50.4, 53.6] | [49.0, 51.0] | ESP32 +3V3 decoupling (100 nF) |
| C5 | 52.0 | 53.0 | 0° | `Capacitor_SMD:C_0402_1005Metric` | [50.4, 53.6] | [52.0, 54.0] | ESP32 +3V3 decoupling (100 nF) |
| C6 | 52.0 | 56.0 | 0° | `Capacitor_SMD:C_0402_1005Metric` | [50.4, 53.6] | [55.0, 57.0] | ESP32 +3V3 decoupling (100 nF) |

**Column-to-column gap:** R-column right edge (x = 46.6) → C-column left edge (x = 50.4) = **3.8 mm** ✓  
**Row-to-row gap (within each column):** 1.0 mm between consecutive courtyards ✓  
**Left pad edge to isolation barrier:** R-column left pad edge ≈ x = 43.4 − 0.25 (half-pad) = 43.15 mm.
Distance from barrier (x = 38 mm) = **5.15 mm > 3.0 mm (P-ISO-03)** ✓  
**Right edge to U3 body left:** C-column right (53.6) vs U3 body left (55.25) = **1.65 mm** ✓

### 6.3 Zone C — CH340C decoupling, USB-CC resistors, user controls (C7, R9, R10, SW1, SW2, LED1, NTC1)

| Ref | cx | cy | rot | Footprint | Courtyard X | Courtyard Y | Notes |
|-----|----|----|-----|-----------|-------------|-------------|-------|
| C7 | 76.0 | 65.5 | 0° | `Capacitor_SMD:C_0402_1005Metric` | [74.4, 77.6] | [64.5, 66.5] | CH340C V3 decoupling; AC-6 check: x=76.0 ∈ [73.7, 78.2] ✓ |
| R9 | 83.0 | 68.5 | 0° | `Resistor_SMD:R_0402_1005Metric` | [81.4, 84.6] | [67.5, 69.5] | USB-C CC1 pull-down (5.1 kΩ) |
| R10 | 83.0 | 71.5 | 0° | `Resistor_SMD:R_0402_1005Metric` | [81.4, 84.6] | [70.5, 72.5] | USB-C CC2 pull-down (5.1 kΩ) |
| SW1 | 44.0 | 69.0 | 0° | `Button_Switch_THT:SW_PUSH_6mm` | [40.0, 48.0] | [65.0, 73.0] | RESET button; operator-accessible |
| SW2 | 53.0 | 69.0 | 0° | `Button_Switch_THT:SW_PUSH_6mm` | [49.0, 57.0] | [65.0, 73.0] | BOOT button; operator-accessible |
| LED1 | 61.5 | 69.0 | 0° | `LED_THT:LED_D3.0mm` | [59.5, 63.5] | [67.0, 71.0] | Green status LED |
| NTC1 | 71.0 | 69.0 | 0° | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | [64.75, 77.25] | [67.0, 71.0] | 10 kΩ NTC thermistor |

**C7 placement rationale:** The 3.95 mm gap between U3 body right (x = 74.75) and U4 left (x = 78.7)
is insufficient to fit a 0402 courtyard (3.2 mm) with 0.5 mm clearance on each side (requires 4.2 mm).
C7 is therefore placed in Zone C below U4 (y = 65.5 > U4 bottom y = 63.45), where it clears both
U3 body (gap 0.99 mm below y = 63.51) and U4 (gap 1.05 mm below y = 63.45) while satisfying AC-6
(|C7_x − U4_left| = |76.0 − 78.7| = 2.7 mm < 5.0 mm). The trace from U4 pin 4 (V3) to C7 will be
short and routed on F.Cu or B.Cu post-routing.

**SW1 isolation check (P-ISO-03):** SW_PUSH_6mm pads are located approximately ±2.5 mm from the switch
centre (pad centres at x ≈ 41.5 and 46.5). Minimum pad edge x ≈ 41.5 − 0.5 = 41.0 mm.
Distance from isolation barrier (x = 38 mm): **41.0 − 38 = 3.0 mm** — exactly at the minimum.
SW1 centre is at x = 44.0 mm; to maintain ≥ 3.0 mm clearance from the barrier to the nearest
copper, the implementer must confirm the exact pad layout of `SW_PUSH_6mm` in KiCad's footprint
editor before committing. If pad edge < 3.0 mm from x = 38, shift SW1 to cx = 45.0 (SW1 courtyard
moves to x[41.0, 49.0]; SW2 to cx = 54.0, courtyard x[50.0, 58.0]; all other spacings remain valid).

---

## 7. Courtyard Collision Proof

All checks below use the courtyard extents from §6 vs. existing components from the issue context.
A "✓" means **no overlap** (gap ≥ 0 mm) and a "✓+" means ample clearance (gap ≥ 1.0 mm).

### 7.1 Zone A components vs. existing courtyards

| New | Existing | X-overlap? | Y-overlap? | Verdict |
|-----|----------|-----------|-----------|---------|
| R5 [49.9,53.1] [18.5,20.5] | J2 [43.85,48.35] [5,17.01] | No (49.9 > 48.35) | — | ✓+ |
| R5 [49.9,53.1] [18.5,20.5] | J3 [54.55,59.05] [5,17.01] | No (53.1 < 54.55) | — | ✓+ |
| R5 [49.9,53.1] [18.5,20.5] | U3 antenna [41,89] [22.26,43.2] | Yes | No (20.5 < 22.26; gap 1.76 mm) | ✓+ |
| R6 [60.5,63.7] [18.5,20.5] | J3 [54.55,59.05] [5,17.01] | No (60.5 > 59.05) | — | ✓+ |
| R6 [60.5,63.7] [18.5,20.5] | J4 [65.15,69.65] [5,17.01] | No (63.7 < 65.15) | — | ✓+ |
| R6 [60.5,63.7] [18.5,20.5] | U3 antenna [41,89] [22.26,43.2] | Yes | No (20.5 < 22.26; gap 1.76 mm) | ✓+ |
| R7 [71.2,74.4] [18.5,20.5] | J4 [65.15,69.65] [5,17.01] | No (71.2 > 69.65) | — | ✓+ |
| R7 [71.2,74.4] [18.5,20.5] | J5 [75.85,80.35] [5,17.01] | No (74.4 < 75.85) | — | ✓+ |
| R7 [71.2,74.4] [18.5,20.5] | U3 antenna [41,89] [22.26,43.2] | Yes | No (20.5 < 22.26; gap 1.76 mm) | ✓+ |
| R8 [90.4,93.6] [18.5,20.5] | J5 [75.85,80.35] [5,17.01] | No (90.4 > 80.35) | — | ✓+ |
| R8 [90.4,93.6] [18.5,20.5] | J6 [82.7,93.25] [5,15.17] | Yes (x overlap) | No (18.5 > 15.17; gap 3.33 mm) | ✓+ |
| R8 [90.4,93.6] [18.5,20.5] | U3 antenna [41,89] [22.26,43.2] | No (90.4 > 89) | — | ✓+ |

### 7.2 Zone B components vs. existing courtyards

| New | Existing | X-overlap? | Y-overlap? | Verdict |
|-----|----------|-----------|-----------|---------|
| R1–R4 [43.4,46.6] [46–57] | U3 antenna [41,89] [22.26,43.2] | Yes | No (46.0 > 43.2; gap 2.8 mm) | ✓+ |
| R1–R4 [43.4,46.6] [46–57] | U3 body [55.25,74.75] [43.2,63.51] | No (46.6 < 55.25) | — | ✓+ |
| R1–R4 [43.4,46.6] [46–57] | U2 [16.8,33.45] [51.35,62.65] | No (43.4 > 33.45) | — | ✓+ |
| R1–R4 [43.4,46.6] [46–57] | L1 [7,24.24] [43.25,48.75] | No (43.4 > 24.24) | — | ✓+ |
| C3–C6 [50.4,53.6] [46–57] | U3 antenna [41,89] [22.26,43.2] | Yes | No (46.0 > 43.2; gap 2.8 mm) | ✓+ |
| C3–C6 [50.4,53.6] [46–57] | U3 body [55.25,74.75] [43.2,63.51] | No (53.6 < 55.25; gap 1.65 mm) | — | ✓+ |
| C3–C6 [50.4,53.6] [46–57] | U2 [16.8,33.45] [51.35,62.65] | No (50.4 > 33.45) | — | ✓+ |
| R1/C3 [46–57] | R2/C4 [49–51] | Same column; row spacing 1.0 mm | — | ✓ |

### 7.3 Zone C components vs. existing courtyards

| New | Existing | X-overlap? | Y-overlap? | Verdict |
|-----|----------|-----------|-----------|---------|
| C7 [74.4,77.6] [64.5,66.5] | U3 body [55.25,74.75] [43.2,63.51] | Yes ([74.4,74.75]) | No (64.5 > 63.51; gap 0.99 mm) | ✓ |
| C7 [74.4,77.6] [64.5,66.5] | U4 [78.7,85.3] [52.55,63.45] | No (77.6 < 78.7; gap 1.1 mm) | No (64.5 > 63.45; gap 1.05 mm) | ✓+ |
| R9 [81.4,84.6] [67.5,69.5] | U4 [78.7,85.3] [52.55,63.45] | Yes | No (67.5 > 63.45; gap 4.05 mm) | ✓+ |
| R9 [81.4,84.6] [67.5,69.5] | J7 [85.73,90.27] [47.62,52.38] | No (84.6 < 85.73; gap 1.13 mm) | No | ✓+ |
| R10 [81.4,84.6] [70.5,72.5] | R9 [81.4,84.6] [67.5,69.5] | Yes (same column) | No (70.5 > 69.5; gap 1.0 mm) | ✓ |
| R10 [81.4,84.6] [70.5,72.5] | Edge.Cuts y=75 | — | No (72.5 < 75; gap 2.5 mm) | ✓+ |
| SW1 [40.0,48.0] [65.0,73.0] | D1 [15,29.7] [64.4,69.6] | No (40.0 > 29.7; gap 10.3 mm) | — | ✓+ |
| SW1 [40.0,48.0] [65.0,73.0] | C2 [4.5,13] [57.75,66.25] | No (40.0 > 13.0) | — | ✓+ |
| SW1 [40.0,48.0] [65.0,73.0] | U3 body [55.25,74.75] [43.2,63.51] | No (48.0 < 55.25) | — | ✓+ |
| SW2 [49.0,57.0] [65.0,73.0] | SW1 [40.0,48.0] [65.0,73.0] | No (49.0 > 48.0; gap 1.0 mm) | — | ✓ |
| SW2 [49.0,57.0] [65.0,73.0] | U3 body [55.25,74.75] [43.2,63.51] | Yes ([55.25,57.0]) | No (65.0 > 63.51; gap 1.49 mm) | ✓+ |
| LED1 [59.5,63.5] [67.0,71.0] | SW2 [49.0,57.0] [65.0,73.0] | No (59.5 > 57.0; gap 2.5 mm) | — | ✓+ |
| LED1 [59.5,63.5] [67.0,71.0] | U3 body [55.25,74.75] [43.2,63.51] | Yes ([59.5,63.5]) | No (67.0 > 63.51; gap 3.49 mm) | ✓+ |
| NTC1 [64.75,77.25] [67.0,71.0] | LED1 [59.5,63.5] [67.0,71.0] | No (64.75 > 63.5; gap 1.25 mm) | — | ✓ |
| NTC1 [64.75,77.25] [67.0,71.0] | U3 body [55.25,74.75] [43.2,63.51] | Yes ([64.75,74.75]) | No (67.0 > 63.51; gap 3.49 mm) | ✓+ |
| NTC1 [64.75,77.25] [67.0,71.0] | U4 [78.7,85.3] [52.55,63.45] | No (77.25 < 78.7; gap 1.45 mm) | No (67.0 > 63.45; gap 3.55 mm) | ✓+ |
| NTC1 [64.75,77.25] [67.0,71.0] | C7 [74.4,77.6] [64.5,66.5] | Yes ([74.4,77.25]) | No (67.0 > 66.5; gap 0.5 mm) | ✓ |

### 7.4 Summary

**All 19 new footprints clear every existing courtyard and the antenna keepout zone.**
Minimum courtyard gap across all checks: **0.5 mm** (NTC1 top vs C7 bottom; x ranges overlap but y does not).
No courtyard collision is expected. Zero `courtyard_collision` DRC violations introduced.

---

## 8. BOM Additions

The following rows must be updated in `write_bom()` in `generate_project.py`. Fields that are already
present (ref, value, footprint) are listed for completeness; only the MPN and Description fields add information.

| Reference | Value | Footprint | Qty | Manufacturer | MPN | Description |
|-----------|-------|-----------|-----|--------------|-----|-------------|
| C3,C4,C5,C6 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | 4 | Murata | GRM155R61C104KA88D | 100 nF X5R 16 V 0402 SMD capacitor |
| C7 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | 1 | Murata | GRM155R61C104KA88D | 100 nF X5R 16 V 0402 SMD capacitor (CH340C V3 decoupling) |
| R1,R2 | 10k | `Resistor_SMD:R_0402_1005Metric` | 2 | Yageo | RC0402FR-0710KL | 10 kΩ ±1% 62.5 mW 0402 SMD resistor |
| R3 | 330R | `Resistor_SMD:R_0402_1005Metric` | 1 | Yageo | RC0402FR-07330RL | 330 Ω ±1% 62.5 mW 0402 SMD resistor |
| R4 | 10k | `Resistor_SMD:R_0402_1005Metric` | 1 | Yageo | RC0402FR-0710KL | 10 kΩ ±1% 62.5 mW 0402 SMD resistor (NTC divider) |
| R5,R6,R7,R8 | 10k | `Resistor_SMD:R_0402_1005Metric` | 4 | Yageo | RC0402FR-0710KL | 10 kΩ ±1% 62.5 mW 0402 SMD resistor (TACH pull-up) |
| R9,R10 | 5.1k | `Resistor_SMD:R_0402_1005Metric` | 2 | Yageo | RC0402FR-075K1L | 5.1 kΩ ±1% 62.5 mW 0402 SMD resistor (USB-C CC) |
| LED1 | LED_GREEN | `LED_THT:LED_D3.0mm` | 1 | Kingbright | WP7113SGC | 3 mm green LED, 565 nm, 20 mA, THT |
| SW1 | RESET | `Button_Switch_THT:SW_PUSH_6mm` | 1 | C&K | PTS645SM43SMTR92 LFS | 6×6 mm tactile switch, 4.3 mm actuator, 50 mA 12 V, THT |
| SW2 | BOOT | `Button_Switch_THT:SW_PUSH_6mm` | 1 | C&K | PTS645SM43SMTR92 LFS | 6×6 mm tactile switch, 4.3 mm actuator, 50 mA 12 V, THT |
| NTC1 | NTC10K_B3950 | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | 1 | Vishay | NTCALUG02A103F | 10 kΩ NTC thermistor B=3950 K, ±1%, axial THT, pitch 10.16 mm |

**Note on consolidation:** C3–C7 share one MPN. R1/R2/R4/R5/R6/R7/R8 share one MPN (all 10 kΩ 0402).
`write_bom()` already groups refs by value/footprint; the implementer should update the MPN and
Description cells in the existing rows rather than adding duplicate rows.

---

## 9. Implementation Sequence

Steps are ordered to satisfy the generator-is-source-of-truth constraint (P-HW-05) and the
ERC/DRC gate requirement (P-DEV-02). **No `.kicad_pcb`, `.kicad_sch`, or `bom.csv` file is
edited by hand** (AC-9).

### Step 0 — Establish DRC baseline (pre-work validation)

```powershell
# Regenerate the current project to get a clean baseline
python hardware/generate_project.py

# Run DRC and capture baseline
$cli = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
& $cli pcb drc `
    --schematic-parity `
    "hardware/kicad/PoE-FanController.kicad_pcb" `
    --output "hardware/kicad/drc_report_baseline.json" `
    --format json

# Verify baseline: 19 missing_footprint, total ≤ 36
$r = Get-Content hardware/kicad/drc_report_baseline.json | ConvertFrom-Json
Write-Host "missing_footprint: $(($r.violations | Where-Object {$_.type -eq 'missing_footprint'}).Count)"
Write-Host "total violations: $($r.violations.Count)"
```

Expected output: `missing_footprint: 19`, `total violations: ≤ 36`

### Step 1 — Add 15 SMD 0402 passive `embed_footprint()` calls to `write_pcb()`

In `generate_project.py`, extend the `fps = [...]` list inside `write_pcb()` with 15 new calls.
Insert **after** the existing `embed_footprint("Package_SO", "SOIC-16_3.9x9.9mm_P1.27mm", "U4", ...)` call
and **before** the closing `]` of the `fps` list.

The exact code block to append (in coordinate order: Zone A → Zone B → Zone C):

```python
        # ── Zone A: Fan TACH pull-up resistors (between fan headers) ─────────
        # R5: FAN1 TACH pull-up — between J2 (right x=48.35) and J3 (left x=54.55)
        embed_footprint("Resistor_SMD", "R_0402_1005Metric",
                        "R5", "10k", 51.5, 19.5),
        # R6: FAN2 TACH pull-up — between J3 (right x=59.05) and J4 (left x=65.15)
        embed_footprint("Resistor_SMD", "R_0402_1005Metric",
                        "R6", "10k", 62.1, 19.5),
        # R7: FAN3 TACH pull-up — between J4 (right x=69.65) and J5 (left x=75.85)
        embed_footprint("Resistor_SMD", "R_0402_1005Metric",
                        "R7", "10k", 72.8, 19.5),
        # R8: FAN4 TACH pull-up — right of J6/antenna keepout (x > 89)
        embed_footprint("Resistor_SMD", "R_0402_1005Metric",
                        "R8", "10k", 92.0, 19.5),

        # ── Zone B: ESP32 support passives (left of U3 body, below antenna keepout) ──
        # Two columns at x=45 (resistors) and x=52 (caps); 4 rows at y=47/50/53/56
        embed_footprint("Resistor_SMD", "R_0402_1005Metric",
                        "R1", "10k", 45.0, 47.0),   # EN pull-up
        embed_footprint("Resistor_SMD", "R_0402_1005Metric",
                        "R2", "10k", 45.0, 50.0),   # BOOT pull-up
        embed_footprint("Resistor_SMD", "R_0402_1005Metric",
                        "R3", "330R", 45.0, 53.0),  # LED current limit
        embed_footprint("Resistor_SMD", "R_0402_1005Metric",
                        "R4", "10k", 45.0, 56.0),   # NTC divider top
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric",
                        "C3", "100nF", 52.0, 47.0), # ESP32 +3V3 decoupling
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric",
                        "C4", "100nF", 52.0, 50.0),
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric",
                        "C5", "100nF", 52.0, 53.0),
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric",
                        "C6", "100nF", 52.0, 56.0),

        # ── Zone C: CH340C decoupling and USB-C CC pull-downs ────────────────
        # C7: CH340C V3 (pin 4) decoupling — below U4 left; x=76.0 satisfies AC-6
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric",
                        "C7", "100nF", 76.0, 65.5), # AC-6: |76.0-78.7|=2.7mm < 5mm ✓
        # R9/R10: USB-C CC1/CC2 pull-downs — below U4, right of NTC1
        embed_footprint("Resistor_SMD", "R_0402_1005Metric",
                        "R9", "5.1k", 83.0, 68.5),  # CC1 pull-down
        embed_footprint("Resistor_SMD", "R_0402_1005Metric",
                        "R10", "5.1k", 83.0, 71.5), # CC2 pull-down
```

### Step 2 — Add 4 THT passive `embed_footprint()` calls to `write_pcb()`

Append after the 15 SMD calls from Step 1, still within the `fps = [...]` list:

```python
        # ── Zone C: User controls and sensor (southern open area) ────────────
        # SW1: RESET button — THT SW_PUSH_6mm
        # Centre x=44 → pads at x≈41.5 and 46.5; pad edge x≈41.0, gap to barrier=3.0mm (P-ISO-03 ✓)
        # If DRC flags pad clearance to barrier, shift to cx=45.0 (see §6.3 note).
        embed_footprint("Button_Switch_THT", "SW_PUSH_6mm",
                        "SW1", "RESET", 44.0, 69.0),
        # SW2: BOOT button — 1.0mm courtyard gap to SW1
        embed_footprint("Button_Switch_THT", "SW_PUSH_6mm",
                        "SW2", "BOOT", 53.0, 69.0),
        # LED1: Green status LED — 2.5mm courtyard gap to SW2
        embed_footprint("LED_THT", "LED_D3.0mm",
                        "LED1", "LED_GREEN", 61.5, 69.0),
        # NTC1: 10kΩ NTC thermistor (pitch 10.16mm axial) — 1.25mm courtyard gap to LED1
        embed_footprint("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
                        "NTC1", "NTC10K_B3950", 71.0, 69.0),
```

### Step 3 — Update `write_bom()` with MPNs

In `write_bom()`, update the `rows` list to add `Manufacturer` and `MPN` values for the 9 passive
rows that currently have empty strings. Use the MPNs from §8.

Key rows to update (current generator lines 1104–1114):

```python
# Replace blank MPN fields in these rows:
["C3,C4,C5,C6","100nF","Capacitor_SMD:C_0402_1005Metric","4","Murata","GRM155R61C104KA88D","3.3V decoupling capacitors","~"],
["C7","100nF","Capacitor_SMD:C_0402_1005Metric","1","Murata","GRM155R61C104KA88D","CH340C V3 decoupling","~"],
["R1,R2","10k","Resistor_SMD:R_0402_1005Metric","2","Yageo","RC0402FR-0710KL","EN and GPIO0 pull-up resistors","~"],
["R3","330R","Resistor_SMD:R_0402_1005Metric","1","Yageo","RC0402FR-07330RL","Status LED series resistor","~"],
["R4","10k","Resistor_SMD:R_0402_1005Metric","1","Yageo","RC0402FR-0710KL","NTC voltage divider resistor","~"],
["R5,R6,R7,R8","10k","Resistor_SMD:R_0402_1005Metric","4","Yageo","RC0402FR-0710KL","Fan TACH pull-up resistors","~"],
["R9,R10","5.1k","Resistor_SMD:R_0402_1005Metric","2","Yageo","RC0402FR-075K1L","USB-C CC pull-down resistors","~"],
["LED1","LED_GREEN","LED_THT:LED_D3.0mm","1","Kingbright","WP7113SGC","Green status LED","~"],
["SW1","RESET","Button_Switch_THT:SW_PUSH_6mm","1","C&K","PTS645SM43SMTR92 LFS","Tactile reset button","~"],
["SW2","BOOT","Button_Switch_THT:SW_PUSH_6mm","1","C&K","PTS645SM43SMTR92 LFS","Tactile boot button","~"],
["NTC1","NTC10K_B3950","Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal","1","Vishay","NTCALUG02A103F","10k NTC thermistor B=3950","~"],
```

### Step 4 — Run the generator

```powershell
cd C:\repos-github\PoE-FanController
python hardware/generate_project.py
```

Expected console output: `wrote hardware/kicad/PoE-FanController.kicad_sch`, `wrote hardware/kicad/PoE-FanController.kicad_pcb`, `wrote hardware/bom/bom.csv`

### Step 5 — Run ERC (verify schematic unchanged)

```powershell
$cli = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
& $cli sch erc `
    "hardware/kicad/PoE-FanController.kicad_sch" `
    --output "hardware/kicad/erc_output.json" `
    --format json

$erc = Get-Content hardware/kicad/erc_output.json | ConvertFrom-Json
Write-Host "ERC error_count: $($erc.error_count)"
# Expected: 0
```

### Step 6 — Run DRC (acceptance gate)

```powershell
& $cli pcb drc `
    --schematic-parity `
    "hardware/kicad/PoE-FanController.kicad_pcb" `
    --output "hardware/kicad/drc_report.json" `
    --format json

$r = Get-Content hardware/kicad/drc_report.json | ConvertFrom-Json

$missing  = ($r.violations | Where-Object { $_.type -eq "missing_footprint" }).Count
$collide  = ($r.violations | Where-Object { $_.type -eq "courtyard_collision" }).Count
$total    = $r.violations.Count

Write-Host "missing_footprint violations : $missing  (target: 0)"
Write-Host "courtyard_collision violations: $collide (target: 0)"
Write-Host "total violations             : $total   (target: ≤ 36)"

# Assert all acceptance criteria
if ($missing -ne 0) { throw "AC-1 FAILED: missing_footprint = $missing" }
if ($collide -ne 0) { throw "AC-3 FAILED: courtyard_collision = $collide" }
if ($total -gt 36)  { throw "AC-2 FAILED: total violations $total > 36" }
Write-Host "All DRC acceptance criteria PASSED"
```

### Step 7 — Verify F.Cu placement (AC-4)

```powershell
# Confirm no new footprint has B.Cu as its primary layer
# (THT pads appear on both layers, but the footprint header must say F.Cu)
Select-String -Pattern 'B\.Cu' hardware/kicad/PoE-FanController.kicad_pcb |
    Select-String -Pattern 'footprint' |
    Measure-Object | Select-Object Count
# Expected: Count = 0  (zone/trace B.Cu entries are not footprint headers)
```

### Step 8 — Verify isolation constraint (AC-5)

```powershell
# All 19 new embed_footprint() cx arguments must be > 38mm
# Manual review of the code additions in Steps 1-2:
#   Zone A: 51.5, 62.1, 72.8, 92.0  — all > 38 ✓
#   Zone B: 45.0, 45.0, 45.0, 45.0, 52.0, 52.0, 52.0, 52.0  — all > 38 ✓
#   Zone C: 76.0, 83.0, 83.0, 44.0, 53.0, 61.5, 71.0  — all > 38 ✓
```

### Step 9 — Commit and push

```powershell
git -C "C:\repos-github\PoE-FanController" add `
    hardware/generate_project.py `
    hardware/kicad/PoE-FanController.kicad_pcb `
    hardware/kicad/PoE-FanController.kicad_sch `
    hardware/kicad/erc_output.json `
    hardware/kicad/drc_report.json `
    hardware/bom/bom.csv

git -C "C:\repos-github\PoE-FanController" commit `
    -m "hw: add 19 missing passive footprints to write_pcb() (C3-C7, R1-R10, LED1, SW1/2, NTC1)"

git -C "C:\repos-github\PoE-FanController" push origin feature/13-missing-passive-footprints
```

---

## 10. DRC Acceptance Criteria

| ID | Criterion | Verification method | Expected value |
|----|-----------|---------------------|----------------|
| AC-1 | Zero `missing_footprint` DRC violations | `jq '[.violations[] \| select(.type=="missing_footprint")] \| length'` on `drc_report.json` | `0` |
| AC-2 | Total DRC violation count does not exceed PR #12 baseline | `jq '.violations \| length'` on `drc_report.json` | `≤ 36` |
| AC-3 | Zero new `courtyard_collision` violations | `jq '[.violations[] \| select(.type=="courtyard_collision")] \| length'` | `0` (or unchanged from baseline if baseline already contained some) |
| AC-4 | All footprints on F.Cu | `Select-String -Pattern 'B\.Cu' ... \| Select-String 'footprint'` — count = 0 | `0` matches in footprint headers |
| AC-5 | All footprint centres east of isolation barrier | Manual review of all 19 `cx` arguments in `generate_project.py` | All `cx > 38.0` |
| AC-6 | C7 within 5 mm of U4 left courtyard edge | `\|C7_cx − 78.7\| ≤ 5.0` | C7 at cx=76.0: `\|76.0 − 78.7\| = 2.7 mm` ✓ |
| AC-7 | SW1 and SW2 ≥ 0.5 mm inter-courtyard gap | DRC (AC-3) and visual inspection | SW1 right=48.0, SW2 left=49.0, gap=1.0 mm ✓ |
| AC-8 | THT/SMD decision documented | This plan §3 | THT retained; no constitution amendment required |
| AC-9 | Generator is the only modified source file | `git diff --name-only` must not include `.kicad_pcb`, `.kicad_sch`, or `bom.csv` before `python generate_project.py` | Only `generate_project.py` modified by hand |
| AC-10 | BOM consistent with footprint references | `write_bom()` footprint strings match `embed_footprint()` library:name strings | Verified by cross-check in §4 vs §8 |
| AC-11 | ERC remains clean | `jq '.error_count'` on `erc_output.json` | `0` |

---

## 11. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **SW1 pad clearance < 3.0 mm from isolation barrier** | Medium | P-ISO-03 violation | Shift SW1 to cx=45.0 and SW2 to cx=54.0 (see §6.3 note); re-verify all spacing with updated courtyards |
| **SW_PUSH_6mm courtyard is larger than 8×8 mm** | Low | Courtyard collision with SW2 or C2 | Measure actual courtyard in KiCad footprint editor before coding; adjust cx of SW1/SW2 accordingly |
| **R8 long FAN4_TACH trace (x=92 vs J5 at x=78.1)** | Medium | Trace routing difficulty; potential noise on TACH signal | 10 kΩ pull-up near GPIO (GPIO39) rather than J5 is acceptable; add pull-up next to ESP32 pin as routing detail. Not a placement correctness issue. |
| **C7 courtyard gap to U3 body = 0.99 mm** | Low | DRC marginal on courtyard clearance if KiCad uses non-zero minimum courtyard gap rule | If DRC reports violation, move C7 to cy=66.0 (gap increases to 1.49 mm); no other component collisions result |
| **NTC1/C7 courtyard Y-gap = 0.5 mm** | Low | KiCad DRC courtyard collision | Gap of 0.5 mm means courtyards are adjacent, not overlapping; DRC checks for overlap (< 0 mm gap), not near-miss. If still flagged, move NTC1 to cy=70.0 (gap becomes 3.5 mm; NTC1 bottom y=72.0 < board edge y=75 ✓) |
| **R8 at x=92 partially overlaps J6 courtyard in X** | Low | Courtyard collision | J6 x[82.7,93.25] and R8 x[90.4,93.6] overlap in X, but J6 y[5,15.17] and R8 y[18.5,20.5] do not overlap in Y. No actual collision; DRC checks 2D overlap, not 1D projections. |
| **LED_D3.0mm footprint is taller than 4 mm** | Low | Courtyard collision with U3 body or NTC1 | If LED courtyard exceeds ±2mm, shift LED1 cx to 62.0 (increases gap to SW2 to 3.0 mm); verify against actual footprint |
| **KiCad `.kicad_mod` file not found at KICAD_FP_BASE path** | Very low | `embed_footprint()` throws FileNotFoundError | All five footprint types are verified present: they are referenced in the existing `build_schematic()` calls in the same generator |

---

## 12. Constitution Compliance

| Constitution principle | How this plan satisfies it |
|------------------------|---------------------------|
| **P-HW-02** — F.Cu only | All 19 footprints use `(layer "F.Cu")` in their embedded header via `embed_footprint()`. THT through-holes are inherent to THT parts; the body/courtyard layer is F.Cu (consistent with L1, D1, C1, C2 precedent). |
| **P-HW-04** — Fixed board outline | No Edge.Cuts change. All component centres in [5, 95] × [5, 75]. |
| **P-HW-05 / P-KI-04** — Generator as source of truth | All changes made exclusively in `generate_project.py`. `.kicad_pcb`, `.kicad_sch`, and `bom.csv` are regenerated artefacts; none are hand-edited. |
| **P-HW-06** — Grid discipline | All 19 coordinates are on the 0.5 mm grid (a strict subset of the required 0.1 mm grid). |
| **P-ISO-02** — Isolation barrier x = 38 mm | No component centre has cx ≤ 38 mm. Minimum cx = 44.0 mm (SW1). |
| **P-ISO-03** — 3 mm creepage/clearance | Left pad edge of leftmost component (SW1, approximately x = 41.0 mm) is 3.0 mm from barrier. All SMD components have left pad edges ≥ 5.15 mm from barrier (R1-column). THT SW1 pad clearance is a Step 6 DRC verify point. |
| **P-ISO-05** — No secondary signals cross barrier | All 19 components connect to secondary-side nets (+3V3, GND, GPIOs, FAN_TACH, USB CC, CH340_V3, LED_A, NTC_ADC, BOOT, ESP_EN). |
| **P-TEST-01 / P-TEST-02** — Zero ERC; ERC recorded | ERC is re-run in Step 5. Since no `build_schematic()` changes are made, ERC is expected to remain clean. `erc_output.json` is committed. |
| **P-TEST-03 / P-TEST-04** — Zero DRC errors; DRC before Gerbers | DRC gate in Step 6 with PowerShell assertions. `drc_report.json` committed. Gerber regeneration is explicitly out of scope for this issue. |
| **P-DEV-01** — Commit convention | Commit message uses `hw:` type prefix. |
| **P-DEV-04** — Constitution amendments | THT decision (§3) deliberately avoids a constitution amendment. No MPN changes from §2.2 BOM-locked components. No new amendment is triggered. |

---

## 13. Out of Scope

- **Trace routing** — All 19 footprints are placed but unconnected. Ratsnest lines will appear in KiCad; routing is a separate issue.
- **Gerber regeneration** — Blocked by P-TEST-04 until DRC is zero. Not applicable pre-routing.
- **Copper pours** — Existing GND pours (F.Cu and B.Cu from x = 40) are unchanged.
- **Firmware changes** — All peripherals for the 19 passives are already allocated in `docs/constitution.md` §P-FW-02.
- **Schematic net changes** — The 19 components are already fully wired in `build_schematic()`.
- **SMD conversion of LED1/SW1/SW2/NTC1** — Explicitly decided against in §3. Future work if board space becomes critical.

---

## 14. Open Questions

None. All ambiguities identified in the issue enrichment have been resolved:

| Question | Resolution |
|----------|------------|
| THT vs SMD for LED1/SW1/SW2/NTC1? | **Retain THT** — no schematic change needed; space available in Zone C (§3). |
| Where does C7 go if the gap between U3 and U4 is too small? | Place below U4 in Zone C at (76.0, 65.5); satisfies AC-6 (§6.3, §11). |
| Does R8 fit between J5 and J6? | No (0.65 mm gap < 3.2 mm courtyard). Place right of antenna keepout at x = 92.0 (§6.1). |
| Does SW1 violate P-ISO-03? | Margin is tight (3.0 mm); Step 6 DRC confirms. Fallback: cx = 45.0 mm (§6.3). |
