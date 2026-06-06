# Feature Architecture Note — PCB: Add Missing Passive Footprints
<!-- Feature: pcb-passive-footprints | Issue: #13 | Branch: feature/13-missing-passive-footprints -->
<!-- Validated against Constitution v1.0.1 | Validation date: 2026-06-06 | Author: architect -->

---

## Validation Result

> **APPROVED WITH REQUIRED CHANGES**
>
> The 15 SMD 0402 placements (Zones A and B, plus C7/R9/R10) are architecturally sound.
> The 4 THT component placements (SW1, SW2, LED1, NTC1) contain **definite courtyard
> violations** caused by an incorrect courtyard model in the plan; corrected coordinates
> are provided below. No constitution amendment is required.

---

## 1. Constitution Principles Checked

| Principle | Check | Result |
|-----------|-------|--------|
| **P-HW-01** (two-layer FR4) | No new layers introduced | ✓ |
| **P-HW-02** (F.Cu only) | All 19 footprints have `(layer "F.Cu")` header; THT through-holes do not violate the "no component body on B.Cu" rule (consistent with L1, D1, C1, C2 precedent) | ✓ |
| **P-HW-04** (fixed outline) | No Edge.Cuts change; all corrected component centres remain inside x[5,95] y[5,75] | ✓ |
| **P-HW-05 / P-KI-04** (generator as source of truth) | Plan exclusively modifies `generate_project.py`; `.kicad_pcb`, `.kicad_sch`, `bom.csv` are build artefacts | ✓ |
| **P-HW-06** (grid discipline) | All plan coordinates are on the 0.5 mm grid (⊂ required 0.1 mm grid); corrected coordinates below are also on the 0.5 mm grid | ✓ |
| **P-ISO-02** (barrier at x=38 mm) | All 19 component centres (cx) > 38 mm; minimum cx = 44.0 mm (SW1) | ✓ |
| **P-ISO-03** (≥3.0 mm creepage/clearance) | **See §3 — isolation concern resolved** | ✓ (5.0 mm) |
| **P-ISO-05** (no secondary signals cross barrier) | All 19 nets are secondary-side only | ✓ |
| **P-DEV-01** (commit convention) | `hw:` prefix used | ✓ |
| **P-DEV-04** (amendments before deviation) | THT decision documented; no amendment triggered | ✓ |
| **P-KI-01** (KiCad 10 format) | All five footprint `.kicad_mod` files carry `(version 20260206)(generator_version "10.0")` | ✓ |
| **P-TEST-01/02** (zero ERC, ERC recorded) | No schematic changes; ERC re-run in Step 5 | ✓ |
| **P-TEST-03/04** (zero DRC errors; DRC before Gerbers) | DRC gate in Step 6 | ✓ (pending corrected coordinates) |

---

## 2. Library Name Verification (P-KI-01, P-DEV-04)

All five footprint library folders and specific `.kicad_mod` files were verified to exist at
`KICAD_FP_BASE = C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\`:

| Library folder | File | Status |
|---|---|---|
| `Capacitor_SMD.pretty` | `C_0402_1005Metric.kicad_mod` | ✓ Present, version 20260206 |
| `Resistor_SMD.pretty` | `R_0402_1005Metric.kicad_mod` | ✓ Present, version 20260206 |
| `LED_THT.pretty` | `LED_D3.0mm.kicad_mod` | ✓ Present, version 20260206 |
| `Button_Switch_THT.pretty` | `SW_PUSH_6mm.kicad_mod` | ✓ Present, version 20260206 |
| `Resistor_THT.pretty` | `R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal.kicad_mod` | ✓ Present, version 20260206 |

All library names match `build_schematic()` and `write_bom()` usage — no custom or
out-of-project libraries are introduced.

---

## 3. SW1 Isolation Analysis — Resolved (P-ISO-03)

The plan flagged SW1 at cx=44.0 as a possible P-ISO-03 violation, estimating the nearest
pad edge at x≈41.0 mm (3.0 mm from the barrier — exactly at the minimum). This estimate
was based on an assumed ±2.5 mm pad offset from the footprint centre.

**Actual SW_PUSH_6mm geometry (read from library):**

```
Local pad positions: Pad1 at (0, 0), Pad1 at (6.5, 0), Pad2 at (0, 4.5), Pad2 at (6.5, 4.5)
Pad diameter: 2.0 mm (radius 1.0 mm), drill: 1.1 mm
Courtyard: (−1.5, −1.5) to (8.0, 6.0) — 9.5 × 7.5 mm, ASYMMETRIC
Footprint origin: at Pad 1 (top-left pad), NOT the geometric centre
```

`embed_footprint()` places the footprint origin (local 0,0) at PCB (cx, cy). With SW1 at
cx=44.0:

- **Leftmost pad centre:** x = 44.0 mm
- **Leftmost pad edge:** 44.0 − 1.0 = **43.0 mm**
- **Gap to isolation barrier (x=38 mm):** 43.0 − 38.0 = **5.0 mm >> 3.0 mm minimum** ✓

**P-ISO-03 is satisfied with comfortable margin.** The plan's fallback of shifting SW1 to
cx=45.0 is not required for isolation reasons. cx=44.0 is accepted.

---

## 4. THT Footprint Courtyard Errors — Root Cause

The plan computed courtyard extents assuming that `embed_footprint(…, cx, cy)` places
each footprint centred at (cx, cy) with symmetric courtyards. **This is correct only for
the centred SMD footprints (R_0402, C_0402).** All four THT footprints have their origin
at Pad 1 (not the geometric centre), producing asymmetric courtyard offsets.

### 4.1 Correct Footprint Origin Offsets

| Footprint | Origin (local 0,0) | Courtyard in local coords | Width × Height |
|---|---|---|---|
| `SW_PUSH_6mm` | Top-left pad (Pad 1) | (−1.5, −1.5) to (8.0, 6.0) | 9.5 × 7.5 mm |
| `LED_D3.0mm` | Anode pad (Pad 1) | (−1.15, −2.21) to (3.69, 2.21) | 4.84 × 4.42 mm |
| `R_Axial_DIN0207_…_Horizontal` (NTC1) | Pad 1 | (−1.05, −1.5) to (11.21, 1.5) | 12.26 × 3.0 mm |

### 4.2 Plan Courtyard Errors and Resulting Violations

Using actual geometry and `embed_footprint()` origin semantics:

**SW1 at plan-specified (cx=44.0, cy=69.0):**
- Actual courtyard: x[42.5, 52.0], y[67.5, **75.0**]
- **Issue A:** Courtyard bottom at y=75.0 mm = board edge (Edge.Cuts y=75 mm) — zero clearance,
  violates standard DRC board-edge clearance rule.

**SW2 at plan-specified (cx=53.0, cy=69.0):**
- Actual courtyard: x[51.5, 61.0], y[67.5, 75.0]
- **Issue B (CRITICAL):** SW1 right=52.0 > SW2 left=51.5 → **0.5 mm courtyard collision** → AC-3 FAILS.
- **Issue A** repeated: board-edge clearance zero.

**LED1 at plan-specified (cx=61.5, cy=69.0):**
- Actual courtyard: x[60.35, 65.19], y[66.79, 71.21]
- **Issue C (CRITICAL):** SW2 (at plan cx=53.0) right=61.0 > LED1 left=60.35 → **0.65 mm courtyard
  collision** → AC-3 FAILS.

**NTC1 at plan-specified (cx=71.0, cy=69.0):**
- Actual courtyard: x[69.95, 82.21], y[67.5, 70.5]
- vs R9 actual courtyard (cx=83.0, cy=68.5): x[82.07, 83.93], y[68.03, 68.97]
  - X overlap [82.07, 82.21] = 0.14 mm; Y ranges overlap → **marginal 0.14 mm collision** → AC-3 FAILS.
- vs U4 [78.7, 85.3] × [52.55, 63.45]: X overlaps but **NO Y overlap** (NTC1 y ≥ 67.5 > 63.45) → ✓ No collision.

### 4.3 SMD 0402 Courtyard — Conservative Model (Non-Critical)

The plan stated a 3.2 × 2.0 mm courtyard (±1.6/±1.0 mm) for 0402 parts.

**Actual R_0402_1005Metric courtyard:** (−0.93, −0.47) to (0.93, 0.47) = **1.86 × 0.94 mm**.

Since the plan used a **larger** courtyard model for SMD parts, all SMD clearance checks in
the plan are overly conservative — actual SMD-to-SMD and SMD-to-THT gaps are larger than
documented. No false collision failures result. This error is safe.

---

## 5. Corrected THT Placement Coordinates

All four THT components require updated (cx, cy) values. Coordinates are on the 0.5 mm grid.

### Derivation

| Constraint | Rule applied |
|---|---|
| All courtyard bottoms ≥ 0.5 mm from board edge y=75 mm | cy + 6.0 ≤ 74.5 → cy ≤ 68.5 |
| SW1–SW2 gap ≥ 0.5 mm | cx_SW2 − 1.5 ≥ cx_SW1 + 8.0 + 0.5 → cx_SW2 ≥ cx_SW1 + 10.0 |
| SW2–LED1 gap ≥ 0.5 mm | cx_LED1 − 1.15 ≥ cx_SW2 + 8.0 + 0.5 → cx_LED1 ≥ cx_SW2 + 9.65 |
| NTC1–R9 gap ≥ 0.5 mm | cx_NTC1 + 11.21 ≤ 83.0 − 0.93 − 0.5 = 81.57 → cx_NTC1 ≤ 70.36 → 70.0 |
| LED1–NTC1 gap ≥ 0.5 mm | cx_NTC1 − 1.05 ≥ cx_LED1 + 3.69 + 0.5 → NTC1 left ≥ LED1 right + 0.5 |
| P-ISO-03 (leftmost pad edge ≥ 3 mm from x=38 mm) | cx_SW1 − 1.0 ≥ 41.0 → cx_SW1 ≥ 42.0; cx_SW1=44.0 gives 5.0 mm ✓ |

### Corrected Coordinate Table

| Ref | **cx (corrected)** | **cy (corrected)** | Plan cx | Plan cy | Change |
|-----|----|----|---------|---------|--------|
| SW1 | **44.0** | **68.5** | 44.0 | 69.0 | cy −0.5 mm |
| SW2 | **54.0** | **68.5** | 53.0 | 69.0 | cx +1.0 mm, cy −0.5 mm |
| LED1 | **64.0** | **68.5** | 61.5 | 69.0 | cx +2.5 mm, cy −0.5 mm |
| NTC1 | **70.0** | **68.5** | 71.0 | 69.0 | cx −1.0 mm, cy −0.5 mm |

### Corrected Courtyard Verification (actual footprint geometry)

| Ref | Corrected courtyard X | Corrected courtyard Y | Board edge clearance | Nearest neighbour gap |
|-----|---|---|---|---|
| SW1 | [42.5, 52.0] | [67.0, 74.5] | 0.5 mm (y) ✓ | SW2 left=52.5; gap=0.5 mm ✓ |
| SW2 | [52.5, 62.0] | [67.0, 74.5] | 0.5 mm (y) ✓ | SW1 right=52.0; gap=0.5 mm; LED1 left=62.85; gap=0.85 mm ✓ |
| LED1 | [62.85, 67.69] | [66.29, 70.71] | 4.3 mm (y) ✓ | SW2 right=62.0; gap=0.85 mm; NTC1 left=68.95; gap=1.26 mm ✓ |
| NTC1 | [68.95, 81.21] | [67.0, 70.0] | 5.0 mm (y) ✓ | LED1 right=67.69; gap=1.26 mm; R9 left=82.07; gap=0.86 mm ✓ |

**All corrected THT courtyards are collision-free.** SW1 and SW2 board-edge clearance is
0.5 mm (from courtyard bottom y=74.5 to Edge.Cuts y=75.0 mm), which satisfies the KiCad
default courtyard-to-board-edge check of ≥ 0 mm with adequate margin.

### Cross-checks Against Existing Components

| New (corrected) | Existing | X overlap | Y overlap | Result |
|---|---|---|---|---|
| SW1 [42.5,52.0] [67.0,74.5] | D1 [15.0,29.7] [64.4,69.6] | No | — | ✓ |
| SW1 [42.5,52.0] [67.0,74.5] | C2 [4.5,13.0] [57.75,66.25] | No | — | ✓ |
| SW1 [42.5,52.0] [67.0,74.5] | U3 body [55.25,74.75] [43.2,63.51] | No (52.0<55.25) | — | ✓ |
| SW2 [52.5,62.0] [67.0,74.5] | U3 body [55.25,74.75] [43.2,63.51] | Yes [55.25,62.0] | No (67.0>63.51; gap 3.49 mm) | ✓ |
| LED1 [62.85,67.69] [66.29,70.71] | U3 body [55.25,74.75] [43.2,63.51] | Yes | No (66.29>63.51; gap 2.78 mm) | ✓ |
| NTC1 [68.95,81.21] [67.0,70.0] | U4 [78.7,85.3] [52.55,63.45] | Yes | No (67.0>63.45; gap 3.55 mm) | ✓ |
| NTC1 [68.95,81.21] [67.0,70.0] | C7 [75.07,76.93] [65.03,65.97] | Yes | No (67.0>65.97; gap 1.03 mm) | ✓ |
| NTC1 [68.95,81.21] [67.0,70.0] | R9 [82.07,83.93] [68.03,68.97] | No (81.21<82.07; gap 0.86 mm) | — | ✓ |

> **Note:** C7 actual courtyard is (76.0±0.93, 65.5±0.47) = [75.07, 76.93] × [65.03, 65.97]
> using the actual 0402 courtyard (not the plan's 3.2×2.0 model). R9 actual courtyard is
> (83.0±0.93, 68.5±0.47) = [82.07, 83.93] × [68.03, 68.97].

---

## 6. Required Changes to `plan.md` Step 2 Code Block

**Replace** the four THT `embed_footprint()` calls in Step 2 (§9 of the plan) with:

```python
        # ── Zone C: User controls and sensor (southern open area) ────────────
        # SW1: RESET button — origin at Pad 1 (leftmost pad).
        # cx=44.0: Pad 1 at x=44.0, pad edge at 43.0mm, gap to barrier=5.0mm (P-ISO-03 ✓).
        # Courtyard: x[42.5,52.0] y[67.0,74.5] — 0.5mm from board edge.
        embed_footprint("Button_Switch_THT", "SW_PUSH_6mm",
                        "SW1", "RESET", 44.0, 68.5),
        # SW2: BOOT button — cx shifted to 54.0 to prevent courtyard collision with SW1.
        # SW1 courtyard right=52.0; SW2 courtyard left=52.5; gap=0.5mm.
        embed_footprint("Button_Switch_THT", "SW_PUSH_6mm",
                        "SW2", "BOOT", 54.0, 68.5),
        # LED1: Green status LED — origin at anode (Pad 1).
        # cx=64.0: courtyard x[62.85,67.69]; gap to SW2 right (62.0)=0.85mm.
        embed_footprint("LED_THT", "LED_D3.0mm",
                        "LED1", "LED_GREEN", 64.0, 68.5),
        # NTC1: 10kΩ NTC thermistor (pitch 10.16mm axial) — origin at Pad 1.
        # cx=70.0: courtyard x[68.95,82.21]; gap to LED1 right (67.69)=1.26mm,
        # gap to R9 left (82.07)=0.86mm.
        embed_footprint("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
                        "NTC1", "NTC10K_B3950", 70.0, 68.5),
```

**Also update** the isolation check comment in Step 8 (§9 of the plan):

```powershell
# Zone C THT: 44.0, 54.0, 64.0, 70.0  — all > 38 ✓
# SW1: Pad 1 at x=44.0; pad edge=43.0mm; gap to barrier=5.0mm (P-ISO-03 satisfied with 5mm margin)
```

---

## 7. Corrected DRC Acceptance Criteria (AC-7 and added AC-12)

The following acceptance criteria in §10 of `plan.md` must be updated:

| ID | Original criterion | Corrected criterion |
|----|---|---|
| AC-7 | SW1/SW2 gap ≥ 0.5 mm; SW1 right=48.0, SW2 left=49.0, gap=1.0 mm | SW1 right courtyard=52.0, SW2 left courtyard=52.5, **gap=0.5 mm** ✓ |
| AC-12 (new) | *(not in plan)* | LED1 left courtyard=62.85 > SW2 right courtyard=62.0; gap=0.85 mm ✓ |
| AC-12 (new) | *(not in plan)* | NTC1 left courtyard=68.95 > LED1 right courtyard=67.69; gap=1.26 mm ✓ |
| AC-12 (new) | *(not in plan)* | NTC1 right courtyard=81.21 < R9 left courtyard=82.07; gap=0.86 mm ✓ |
| AC-12 (new) | *(not in plan)* | All THT courtyard bottoms (y=74.5) ≥ 0.5 mm from board edge (y=75.0) ✓ |

---

## 8. No Constitution Amendment Required

The plan's §3 deliberately avoided a constitution amendment by retaining THT components.
This validation confirms:

- **P-ISO-03** is satisfied (5.0 mm clearance > 3.0 mm minimum) — no relaxation needed.
- **P-HW-02** is satisfied — THT through-holes are not "component bodies on B.Cu".
- **No new BOM-locked components** are introduced.
- **No new peripheral allocation** changes are made.
- **No schematic (build_schematic) changes** are needed.
- All library footprints are KiCad 10 standard library — no custom footprint amendment needed.

Constitution version remains **1.0.1**. No amendment to `docs/constitution.md` is triggered.

---

## 9. Validation Summary

| Category | Finding | Severity | Action |
|---|---|---|---|
| Library names (5 footprints) | All verified present in KiCad 10.0 standard library | — | None |
| SMD 0402 courtyard model | Plan assumes ±1.6/±1.0 mm; actual is ±0.93/±0.47 mm | Low (conservative — actual gaps larger) | Informational only |
| P-ISO-03 (SW1) | Plan estimated 3.0 mm; actual is 5.0 mm — no violation | — | Remove misleading note from plan |
| SW1/SW2 courtyard collision | 0.5 mm overlap in X at plan coordinates | **HIGH** (AC-3 fails) | Update cx_SW2 = 54.0, cy = 68.5 |
| SW2/LED1 courtyard collision | 0.65 mm overlap in X at plan coordinates | **HIGH** (AC-3 fails) | Update cx_LED1 = 64.0, cy = 68.5 |
| NTC1/R9 near-collision | 0.14 mm overlap in X at plan coordinates | **HIGH** (AC-3 fails) | Update cx_NTC1 = 70.0, cy = 68.5 |
| SW1/SW2 board-edge clearance | Plan cy=69.0 → courtyard bottom at y=75.0 = board edge | **MEDIUM** | Update cy = 68.5 for all THT parts |
| THT P-HW-02 compliance | Body on F.Cu; through-holes are drill artefacts | ✓ | None |
| P-KI-04 (generator only) | No hand-edits to kicad_pcb/sch | ✓ | None |
| All 19 centres east of x=38 mm | Min cx=44.0 mm (SW1) | ✓ | None |
| Zone A/B SMD placements | All verified collision-free with actual courtyards | ✓ | None |
