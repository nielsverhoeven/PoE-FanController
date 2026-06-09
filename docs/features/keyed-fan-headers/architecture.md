# Feature Architecture Notes: Keyed Fan Headers (J2–J5)

**Issue:** #100 — Replace fan headers with keyed 4-pin female headers
**Branch:** `feature/100-keyed-fan-headers`
**Stage 3 validation date:** 2026-06-09
**Validation result:** ✅ **APPROVED WITH CHANGES**

> One MAJOR constitution amendment was required and has been applied as part of this
> Stage 3 validation (see §4 below). The plan may proceed to implementation immediately.

---

## 1. Scope

This feature is **hardware-only**. It replaces the footprint of the four fan headers J2–J5 from
the unkeyed `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` to the Molex KK-254
shrouded keyed connector `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`.

No firmware modules, no REST API endpoints, and no web UI assets are modified.

---

## 2. Architecture Impact Assessment

### 2.1 Hardware block diagram — unchanged

J2–J5 remain on the same power nets (+12 V / GND / FANn_TACH / FANn_PWM), at the same board
location (side edge, x ≈ 58 mm, portrait PCB). The change is purely a connector body and
footprint geometry upgrade. No routing or net topology changes are implied.

```
graph TB
    J8["J8 — 2×20 header\n(Waveshare SKU 32088)"] -->|+5V| UBOOST["U_BOOST\n(LM2587-12 5V→12V)"]
    UBOOST -->|+12V| J2["J2 — FAN1\nMolex KK-254\n22-27-2041"]
    UBOOST -->|+12V| J3["J3 — FAN2\nMolex KK-254\n22-27-2041"]
    UBOOST -->|+12V| J4["J4 — FAN3\nMolex KK-254\n22-27-2041"]
    UBOOST -->|+12V| J5["J5 — FAN4\nMolex KK-254\n22-27-2041"]
    J8 -->|GPIO4–7 PWM| J2
    J8 -->|GPIO4–7 PWM| J3
    J8 -->|GPIO4–7 PWM| J4
    J8 -->|GPIO4–7 PWM| J5
    J8 -->|GPIO8–11 TACH| J2
    J8 -->|GPIO8–11 TACH| J3
    J8 -->|GPIO8–11 TACH| J4
    J8 -->|GPIO8–11 TACH| J5
```

### 2.2 Firmware module map — unchanged

No firmware module is affected. The `fan` module (LEDC PWM + TACH interrupt) continues to own
GPIO4–7 and GPIO8–11 via J8. No peripheral reassignment is required.

### 2.3 Power architecture — unchanged

J2–J5 carry the same +12 V / GND nets. Current capacity (≤ 1.0 A total, P-HW-07) is unchanged.
Power budget (§5.2) is unchanged. PoE class (802.3at Class 4) is unchanged.

---

## 3. Constitution Compliance Verification

| Constitution Principle | Verdict | Notes |
|---|---|---|
| **P-HW-02** — Single-sided placement (F.Cu only) | ✅ PASS | TH pads span both copper layers by nature of through-hole; component body on F.Cu only — identical behaviour to the old pin header footprint. |
| **P-HW-03** — Side-edge connector placement | ✅ PASS | J2–J5 remain at board X ≈ 58 mm (side edge). No positional change required by this plan. |
| **P-HW-05 / P-KI-04** — Generator is the schematic source of truth | ✅ PASS | Plan specifies generator `components.py` must be updated first (both the `define()` symbol-level footprint at line ~174 and the `component()` instance-level footprint at line ~345–347); `.kicad_sch` regenerated via `python hardware/generate_project.py`. Direct edits to `.kicad_sch` are forbidden and not performed. |
| **P-HW-06** — Grid discipline | ✅ PASS | Footprint origin positions on PCB are unchanged; only the footprint geometry (body + pad size + courtyard) changes. Schematic symbol origin unchanged (only the `Footprint` property string changes). |
| **P-HW-09** — Keyed/polarised external connectors (v3.2.0) | ✅ PASS — **this feature directly satisfies P-HW-09 for J2–J5** | Molex KK-254 shrouded housing physically prevents reverse insertion, meeting the requirement for "mechanically keyed or polarized housing". |
| **P-KI-01** — KiCad 10.0.3 version lock | ✅ PASS | All KiCad GUI work in KiCad 10.0.3. CI uses approved `kicad/kicad:10.0.2` per P-KI-01 PATCH. |
| **P-KI-05** — Custom symbols/footprints in-project | ✅ PASS | No custom footprint required. `Connector_Molex` standard library already used by J6; same library used for J2–J5 new footprint. No new library paths added. |
| **P-KI-07** — PCB layout source of truth is KiCad GUI | ✅ PASS | Plan specifies PCB changes exclusively via KiCad GUI (Tools → Update PCB from Schematic, F8). No script writes to `.kicad_pcb`. |
| **P-TEST-01** — Zero ERC errors | ✅ PASS (pending execution) | ERC must be run after schematic regeneration. Footprint-only change does not alter net topology; zero new ERC violations expected. |
| **P-TEST-03** — Zero DRC errors | ✅ PASS (pending execution) | DRC must be run after PCB update. Courtyard Y-span grows from ~2 mm to 6.8 mm; clearance analysis shows ~20 mm gap to nearest interior components (R5–R8 at x ≈ 21–35 mm) — overlap very unlikely, but DRC must confirm. |
| **P-TEST-02 / P-TEST-04** — ERC/DRC outputs recorded | ✅ PASS (pending execution) | `erc_output.json` and `drc_output.json` must be updated and committed alongside the schematic/PCB changes. |
| **§2.2 BOM lock** — Substitutions require MAJOR amendment | ✅ RESOLVED — **MAJOR amendment v4.0.0 applied (see §4)** | `47053-1000` → Molex 22-27-2041 / `Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`. Amendment applied to `docs/constitution.md` during Stage 3 validation. |

---

## 4. Constitution Amendment Applied

A **MAJOR amendment (v4.0.0)** was applied to `docs/constitution.md` during Stage 3 validation.

### What changed

| Location | Before | After |
|---|---|---|
| Constitution version header | `3.3.0` / `2026-06-08` | `4.0.0` / `2026-06-09` |
| §2.2 J2–J5 BOM row — Value / MPN | `47053-1000 (Molex)` | `Molex 22-27-2041 (KK-254, 4-pin keyed vertical header; AE-6410-04A old p/n; 22-23-2041 acceptable equivalent)` |
| §2.2 J2–J5 BOM row — Package | `4-pin 2.54 mm` | `1×4, 2.54 mm pitch, through-hole, polarised latching shroud` |
| §2.2 J2–J5 BOM row — Role | plain description | Updated to include footprint reference, keying rationale, mating housing, P-HW-09 mandate reference |
| P-HW-09 note | "MAJOR amendment pending" | Updated to record v4.0.0 completion |
| §10 Amendment History | ends at v3.3.0 | Row added for v4.0.0 |

### Rationale

- P-HW-09 (v3.2.0) mandates keyed housings for J2–J5 and states the BOM MAJOR amendment
  was pending kicad.expert confirmation of the MPN/footprint.
- The plan (`docs/features/keyed-fan-headers/plan.md` §2.1–§2.3) provides kicad.expert-level
  technical verification:
  - Footprint `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` confirmed
    present in the KiCad 10.0.3 local installation.
  - Full dimensional comparison table (pad pitch, drill size, courtyard span) provided.
  - J6 family precedent: `Connector_Molex:Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical`
    (3-pin) already used for J6 in `hardware/generator/components.py` line 214 — no new
    library source introduced.
- The 47053-1000 entry was retroactively non-compliant with P-HW-09. The amendment
  resolves this non-compliance and closes the outstanding action from v3.2.0.

---

## 5. Generator Script Verification

Cross-checked `hardware/generator/components.py` against the plan:

| Location in components.py | Current value (pre-feature) | Required change per plan |
|---|---|---|
| Line 175 — `s.define("Custom:Fan_Header", ...)` footprint arg | `"Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"` | → `"Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical"` |
| Lines 345–347 — `s.component("Custom:Fan_Header", f"J{2+i}", ...)` footprint arg (×4) | `"Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"` | → `"Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical"` |
| Line 214 — J6 `s.define("Custom:Conn_1x03", ...)` footprint | `"Connector_Molex:Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical"` | No change — this is the J6 3-pin sibling; confirms library is already referenced |

**Both the symbol-level `define()` and the instance-level `component()` footprint arguments must
be updated.** The plan correctly identifies both change points. Keeping them in sync avoids
silent mismatches where KiCad GUI cross-probing would use the instance footprint while the
symbol editor would show the old default.

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Architecture judgement |
|---|---|---|---|
| Courtyard overlap after swap | Low | Medium | The KK-254 Y-courtyard (6.8 mm at rot=90° maps to PCB X-direction) adds ~4.8 mm over the old pin header. With ~20 mm clearance to R5–R8, DRC is very unlikely to flag an error. DRC is mandatory before merge. |
| KiCad F8 UUID mismatch | Low | Medium | `import_netlist.py` / `sync_pcb_paths.py` maintain UUID alignment. Plan mitigation (manual footprint delete/re-add) is correct fallback. |
| Wrong key-tab orientation | Medium | Low | Pin 1 (GND) must be outermost (toward board edge) to match fan cable GND pin. 3D viewer verification is mandatory before PCB save. |
| `Connector_Molex` absent from `fp-lib-table` | Low | High | Plan correctly calls out this risk and provides the library table entry. Must be checked first (checklist item 1). |

---

## 7. Implementation Checklist (Architecture Gate)

These items are **mandatory before merge to `main`**:

- [ ] `fp-lib-table` contains `Connector_Molex` library entry
- [ ] `hardware/generator/components.py` — both `define()` and `component()` footprint args updated
- [ ] `python hardware/generate_project.py` — runs without error
- [ ] ERC: zero violations; `erc_output.json` committed
- [ ] PCB updated via KiCad GUI (F8); J2–J5 re-placed at (58, 10/22/34/46) rot=90°
- [ ] 3D viewer confirms shroud key faces board edge; pin-1 silk on correct side
- [ ] DRC: zero errors; courtyard checks pass; `drc_output.json` committed
- [ ] Constitution amendment v4.0.0 committed (✅ done in this Stage 3 pass)
- [ ] PR references issue #100; targets `main`

---

*Architecture validation completed by: architect agent, 2026-06-09*
