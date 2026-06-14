# Feature Architecture: Replace Discrete Boost Converter with DC-DC Module

<!-- feature: replace-boost-module | issue: #177 | branch: feature/177-replace-boost-converter-module -->
<!-- constitution ref: docs/constitution.md v5.0.0 (amended by this feature) -->
<!-- validation date: 2026-06-14 | status: APPROVED WITH CHANGES (constitution amended) -->

---

## 1. Validation Result

**APPROVED WITH CHANGES**

The feature plan is architecturally sound and constitutionally compliant after the MAJOR
amendment v5.0.0 applied to `docs/constitution.md`. All principle checks pass. Three
**pre-fabrication blockers** are flagged — no PR merge gate, but must be resolved before
ordering PCBs (see §5).

---

## 2. Amendment Applied

**Constitution v4.3.0 → v5.0.0 (MAJOR)**  
File: `docs/constitution.md`  
Committed on branch: `feature/177-replace-boost-converter-module`

### Changes applied

| Section | Before (v4.3.0) | After (v5.0.0) |
|---|---|---|
| §2.2 U_BOOST BOM row | Placeholder: LM2587-12/TPS61085, SOT-23-6/D2PAK (unlocked) | **Locked:** DC-DC Boost Module, Amazon.nl B0D9VJKD1L, 4-pin 2.54 mm THT, footprint `Custom:DC-Boost-Module` |
| §2.2 Discrete boost components | U1/L1/D1/C1/C2 implicitly referenced in U_BOOST description | **Retired:** U1 (LM2587-12), L1 (100 µH), D1 (1N5822), C1/C2 (100 µF/25 V) — function now internal to module |
| §3.1 P-HW-04 right zone | "U1+L1+D1+C1+C2 (boost converter chain)" | "U_BOOST (DC-DC boost module, Amazon.nl B0D9VJKD1L)" |
| §5.1 Power Chain | Stale v2.0.0 text (J1/Ag9905M/LM2596S/D2 — removed in v3.0.0) | Corrected daughter-board architecture with U_BOOST in path; VBUS risk flagged |
| §5.2 Power Budget | ~18.9 W total, 1.1 W (5.5%) margin; LM2596S/D2/Ag9905M rows | ~19.4 W total, **0.6 W (3%) margin**; U_BOOST conversion loss row; VBUS current risk warning |
| §8.4 Bring-up Checklist | Stale steps referencing Ag9905M/LM2596S/D2 | Rewritten for daughter-board; 4 U_BOOST-specific steps added |
| §10 Amendment History | Last entry v4.3.0 | v5.0.0 entry added |

---

## 3. Constitution Principle Checks

### 3.1 Hardware / PCB

| Principle | Check | Result |
|---|---|---|
| **P-HW-01** (2-layer FR4 only) | U_BOOST is a THT module — no additional layers required | ✅ PASS |
| **P-HW-02** (F.Cu placement only) | U_BOOST footprint must have all pads on F.Cu; courtyard on F.CrtYd only | ✅ PASS — plan §4.2 specifies F.Cu only, no underside pads |
| **P-HW-03** (side-edge connectors) | U_BOOST is an internal board-mounted module, not an external cable connector | ✅ PASS — P-HW-09 does not apply (board-to-board mount) |
| **P-HW-04** (right zone x = 33.19–56 mm) | U_BOOST placed in right zone where U1/L1/D1/C1/C2 were | ✅ PASS — plan §4.7 step 3 specifies x = 33.19–56 mm placement |
| **P-HW-04** (board dimensions 78×56 mm) | Module body ~28×17 mm; right zone width = 22.81 mm — see §4 fit analysis | ⚠ CONDITIONAL — courtyard may be tight; DRC required (Risk R-06) |
| **P-HW-05 / P-KI-04** (generator is schematic source of truth) | All schematic changes via `hardware/generator/components.py`; no hand-editing `.kicad_sch` | ✅ PASS — plan §4.3 fully specifies generator changes |
| **P-HW-06** (grid discipline) | Symbol on 2.54 mm schematic grid; footprint on ≤ 0.1 mm PCB grid | ✅ PASS — plan §4.3.4 documents BOOST_MOD_CX/Y as multiples of G=2.54 mm |
| **P-HW-07** (power trace widths) | All four U_BOOST nets (+5V, GND×2, +12V) require ≥ 1.0 mm traces | ✅ PASS — plan §4.7 step 4 specifies ≥ 1.0 mm for all power nets |
| **P-HW-08** (single GND domain) | U_BOOST IN− and OUT− both connect to GND copper pour; single SELV domain unchanged | ✅ PASS |
| **P-HW-09** (polarised housings) | Not applicable — U_BOOST is a board-mounted module, not a cable connector | ✅ PASS — not in scope |
| **P-KI-01** (KiCad 10.0.3) | All PCB work in KiCad 10.0.3; footprint created in KiCad Footprint Editor or via generator script | ✅ PASS |
| **P-KI-05** (custom footprints in Custom.pretty/) | `DC-Boost-Module.kicad_mod` created in `hardware/kicad/footprints/Custom.pretty/` | ✅ PASS |
| **P-KI-07** (PCB is KiCad GUI only) | PCB edits (remove U1/L1/D1/C1/C2; add/place/route U_BOOST) done in KiCad interactively | ✅ PASS — plan §4.7 is explicit |

### 3.2 Schematic

| Principle | Check | Result |
|---|---|---|
| **P-SCH-01** (global labels for inter-block signals) | `+5V`, `+12V`, `GND` are power symbols — no new global label net required | ✅ PASS |
| **P-SCH-02** (isolated ground domains) | Daughter board is single `GND` (SELV) domain; U_BOOST does not introduce any primary-side net | ✅ PASS |
| **P-SCH-03** (section header style) | Plan §4.3.4: `bold=True`, `size=2.54`, `color=(0,0,255)` — compliant | ✅ PASS |
| **P-SCH-04** (power symbol pin types) | Plan §4.3.2: OUT+ (`+12V`) uses `pin_type="power_out"` — drives the rail | ✅ PASS |
| **P-SCH-05** (custom symbol pin types) | Plan §4.3.2: IN+/IN−/OUT− use `"power_in"` — correct; none drive a rail | ✅ PASS |

### 3.3 Power & PoE

| Principle | Check | Result |
|---|---|---|
| **P-POE-01** (802.3at Class 4) | No change to PoE class or PD negotiation; Waveshare SKU 32088 onboard Ag9905M unchanged | ✅ PASS |
| **P-POE-02** (no primary-side changes) | U_BOOST is on the SELV secondary side (x > 33 mm, all-SELV daughter board) | ✅ PASS |
| **P-ISO-01 to P-ISO-05** | Daughter board is all-SELV since v3.0.0; isolation rules reside inside Waveshare board; no daughter-board isolation concern | ✅ PASS |
| **Power margin** | ~0.6 W (3%) — positive but very tight. Must not add further loads. | ⚠ WARNING — see §5 Risk R-07 |
| **VBUS current** | ~3.47 A total from J8 pin 40. Capacity unconfirmed. | 🚫 BLOCKER — see §5 Risk R-01 |

### 3.4 Firmware

| Principle | Check | Result |
|---|---|---|
| **P-FW-01 to P-FW-05** | No firmware changes in this feature; power conversion is hardware-only | ✅ PASS — no firmware impact |

### 3.5 Testing

| Principle | Check | Result |
|---|---|---|
| **P-TEST-01** (zero ERC errors) | Plan §4.6 gates on zero ERC errors before PCB work | ✅ PASS |
| **P-TEST-03** (zero DRC errors) | Plan §4.8 gates on zero DRC violations before PR | ✅ PASS |
| **P-DEV-04** (amendment before implementing change) | Amendment v5.0.0 applied and committed before generator changes | ✅ PASS |
| **P-DEV-01** (commit convention) | `hw:` prefix confirmed in plan §4.9 | ✅ PASS |

---

## 4. Physical Fit Analysis

### 4.1 Right Zone Capacity (Board 78×56 mm)

| Constraint | Value | Status |
|---|---|---|
| Right zone width available | 22.81 mm (x = 33.19 → 56 mm) | — |
| U_BOOST module body (typical ~28×17 mm) | 28 mm long × 17 mm wide | ⚠ See note |
| Module courtyard vs zone width | 17 mm body width < 22.81 mm zone width | ✅ Width fits |
| Module length vs board height | 28 mm < 78 mm board height | ✅ Length fits |
| Courtyard clearance from J8 Row B (x = 33.19 mm) | Left edge of module must be ≥ 33.19 mm + courtyard extension | ✅ Enforceable via placement |
| All-top-layer placement (P-HW-02) | Module header pins on F.Cu; courtyard on F.CrtYd | ✅ Confirmed by plan |

> **⚠ Physical verification required (Risk R-02):** The "~28×17 mm" figure is typical for
> MT3608/XL6009-class modules. The actual B0D9VJKD1L unit must be measured with callipers
> before finalising `DC-Boost-Module.kicad_mod`. Do not submit PCB for fabrication until
> the footprint is confirmed against the physical unit.

### 4.2 PCB Placement Deviation — Right Zone Right Boundary

During PCB implementation (T006), U_BOOST was placed with centre at x=56mm (right bound of the
"x=33.19–56mm" zone from P-HW-04). This places pads 3 and 4 at x=57.27mm and x=59.81mm,
slightly beyond the 56mm right boundary.

**Root cause:** Moving U_BOOST centre further left (e.g., x=52mm) causes the footprint courtyard
to overlap J8's courtyard (J8 right courtyard edge ≈46.94mm), which is a **DRC error** under
`courtyards_overlap`. The 4-pin header pitch (2.54mm×3 = 7.62mm span) forces pad 4 beyond 56mm
when pad 1 must clear J8.

**Impact assessment:**
- All pads remain on the board (right edge at x=94mm) ✅
- No other component occupies x=57–62mm at y≈18–22mm ✅
- All U_BOOST traces stay at x≥45.19mm (no left-boundary violation) ✅
- DRC passes with 0 errors ✅
- The violated boundary is the *right* extent of the zone, not the J8 isolation line (x=33.19mm)

**Decision:** Deviation accepted. DRC is the enforced hard constraint (P-TEST-03). The zone
description in P-HW-04 is a placement guideline, not a board-edge rule. Document for clarity;
no further action required before PR merge.

### 4.3 R5 Retention Confirmed

The plan correctly identifies that **R5 is the FAN1 TACH pull-up resistor** (10 kΩ, +3V3 →
FAN1_TACH net), not a boost feedback resistor. R5 must **not** be removed from the schematic,
BOM, or PCB. This is a documented correction to the original issue body. ✅

---

## 5. Pre-Fabrication Blockers

The following items are not merge-gate blockers (the plan and schematic can be merged with
zero ERC/DRC), but **must be resolved before PCB fabrication begins**:

| # | Blocker | Owner | Resolution |
|---|---|---|---|
| R-01 | **VBUS current limit** — Waveshare SKU 32088 J8 pin 40 must supply ~3.47 A total (2.67 A boost + 0.8 A ESP32). Capacity is MEDIUM confidence. | Hardware lead | Check Waveshare SKU 32088 schematic/datasheet; confirm VBUS rail current limit. If insufficient, add a daughter-board 5V regulator (new MAJOR amendment + `poe.expert` review required). |
| R-02 | **Physical module dimensions** — B0D9VJKD1L body dimensions and pin pitch must be confirmed with callipers before finalising `DC-Boost-Module.kicad_mod`. Amazon batches may vary. | Hardware lead | Measure received unit. Update footprint if needed. Re-run DRC. |
| R-03 | **Module pin ordering** — Confirm physical IN+/IN−/OUT+/OUT− sequence on received unit matches the footprint pad assignment before soldering. | Hardware lead | Check against Amazon product description and physical inspection. |

---

## 6. Power Architecture Diagram

```
[Ethernet cable — 802.3at PoE+]
        │  37–57 V DC
        ▼
  Waveshare SKU 32088
  (Ag9905M PoE+ PD, isolation, 5V buck)
        │  +5V VBUS (J8 pin 40)
        │  ⚠ ~3.47 A total — verify capacity
        ▼
  J8 daughter board connector
        │
        ├──► U_BOOST (B0D9VJKD1L)
        │    5V → 12V  (93% eff., 2A max)
        │         │
        │         └──► +12V → J2–J5 fan headers (≤1.0 A, ≤12.0 W)
        │
        ├──► +3V3 (J8 pin 36)
        │    └──► R5–R8, J9 DHT11, R14 DS18B20 pull-up
        │
        └──► ESP32-P4NRW32 + peripherals (~0.8 A)

Power margin: ~0.6 W / 3% vs 20 W Class 4 cap — VERY TIGHT
```

---

## 7. Files Changed by This Feature

| File | Change | Notes |
|---|---|---|
| `docs/constitution.md` | **AMENDED v5.0.0** | This file — MAJOR amendment applied |
| `docs/features/replace-boost-module/architecture.md` | **Created** | This file |
| `hardware/generator/components.py` | Modify | Remove 4 defines + 5 instantiations; add DC_Boost_Module define + U_BOOST instance; update docstrings |
| `hardware/generator/bom.py` | Modify | Remove U1/L1/D1/C1/C2 rows; add U_BOOST row; update docstring |
| `hardware/kicad/footprints/Custom.pretty/DC-Boost-Module.kicad_mod` | Create | 4-pin 1×4 2.54 mm THT footprint — **verify against physical unit before fab** |
| `hardware/kicad/PoE-FanController.kicad_sch` | Regenerated artefact | Output of `generate_project.py` |
| `hardware/bom/bom.csv` | Regenerated artefact | Output of `generate_project.py` |
| `hardware/kicad/erc_output.json` | Update | Must show 0 errors |
| `hardware/kicad/PoE-FanController.kicad_pcb` | KiCad GUI edit | Remove U1/L1/D1/C1/C2; add/place/route U_BOOST |
| `docs/kb/DC-DC-boost-module.md` | Commit untracked | KB reference for B0D9VJKD1L |

---

## 8. Expert Consultation Record

| Expert | Consulted? | Topic | Decision |
|---|---|---|---|
| `kicad.expert` | Not required for this amendment | Footprint approach (4-pin THT in Custom.pretty/) follows established P-KI-05 pattern. No new footprint library or KiCad format question. | Delegated to P-KI-05 — existing principle covers the approach |
| `esp32.expert` | Not required | No firmware or GPIO changes | — |
| `poe.expert` | **Recommended before fab** | VBUS current capacity (3.47 A from J8 pin 40); power margin (3%); module topology change impact on PoE budget | Pending — must be completed before PCB fabrication (Risk R-01 / R-07) |
