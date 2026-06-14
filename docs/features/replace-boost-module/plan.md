# Technical Plan: Replace Discrete Boost Converter Stage with Module (Issue #177)

<!-- feature: replace-boost-module | issue: #177 | branch: feature/177-replace-boost-converter-module -->
<!-- constitution ref: docs/constitution.md v4.3.0 -->

---

## 1. Feature Summary

Replace five discrete boost-converter components (U1/L1/D1/C1/C2) with a single 4-pin
off-the-shelf DC-DC Step-Up Boost Module (Amazon.nl **B0D9VJKD1L**). The module is referenced
as `U_BOOST` in the schematic and PCB. All schematic changes flow through the generator package
(`hardware/generator/`); PCB changes are made in KiCad GUI per P-KI-07.

> ⚠️ **Issue title discrepancy:** The issue and branch are named "LM2596S-ADJ". That part is a
> **buck (step-down)** converter and is explicitly rejected in `docs/kb/DC-DC-boost-module.md`.
> The approved module is **B0D9VJKD1L**, a step-up boost converter. All implementation work
> must target B0D9VJKD1L. The branch name is kept for traceability only.

> ⚠️ **R5 is not a boost component.** The issue body lists R5 (feedback resistor) as a component
> to retire. This is incorrect. In `hardware/generator/components.py`, R5 is the FAN1 TACH
> pull-up resistor (10 kΩ, +3V3 → FAN1_TACH net). The LM2587-12 FB pin is wired directly to
> `+12V` in the generator (no separate resistor). R5 must not be removed from the schematic,
> BOM, or PCB.

---

## 2. Architecture Fit

### 2.1 Constitution Mapping

| Constitution Principle | Impact of This Feature |
|---|---|
| **P-HW-02 — Single-sided placement (F.Cu only)** | U_BOOST footprint must have all pads on F.Cu. No SMD underside pads. |
| **P-HW-04 — Right zone (x = 33.19–56 mm)** | U_BOOST placed in the right zone, exactly where U1/L1/D1/C1/C2 previously resided. |
| **P-HW-05 / P-KI-04 — Schematic generator is source of truth** | All schematic changes (symbol define, wiring) made in `hardware/generator/components.py` only; `.kicad_sch` is regenerated, never hand-edited. |
| **P-KI-05 — Custom footprints in-project** | `DC-Boost-Module.kicad_mod` created in `hardware/kicad/footprints/Custom.pretty/`. |
| **P-KI-07 — PCB is KiCad GUI only** | PCB footprint removal/placement/routing done interactively in KiCad; `.kicad_pcb` not touched by scripts. |
| **P-HW-07 — Power trace widths** | All four boost nets (+5V input, GND, +12V output) must use ≥ 1.0 mm traces. |
| **P-HW-06 — Grid discipline** | U_BOOST symbol origin on 2.54 mm schematic grid; PCB footprint origin on ≤ 0.1 mm grid. |
| **P-SCH-03 — Section header style** | New "5V → 12V Boost Module (U_BOOST)" section header: bold, 2.54 mm, blue. |
| **P-SCH-04 — Power symbol pin types** | OUT+ pin (`+12V`) must use `pin_type="power_out"` — it drives the +12V rail. |
| **P-TEST-01 / P-TEST-03 — Zero ERC / DRC errors** | ERC run after generator; DRC run after PCB edits. Both must be clean before PR merge. |
| **P-DEV-04 — Constitution amendments** | MAJOR amendment required to lock U_BOOST MPN in §2.2. Must be committed before generator change. |
| **P-DEV-01 — Commit message convention** | `hw:` prefix for all hardware file changes. |

### 2.2 Schematic Block Diagram

Before:
```
+5V ──[C1]── GND            (input bypass)
+5V ──[L1]── BOOST_SW ──[D1]──► +12V ──[C2]── GND   (boost path)
                   │
              [U1 LM2587-12]
              OUTPUT(3)=BOOST_SW  FB(4)=+12V  OSC(5)=GND
```

After:
```
+5V ──── IN+  [U_BOOST]  OUT+ ──► +12V
GND  ──── IN−              OUT− ──► GND
```

The module contains the inductor, switching IC, catch diode, input/output capacitors, and
output-voltage trimmer internally. No discrete external passives remain for the boost stage.

---

## 3. Prerequisite: Constitution Amendment (MAJOR)

**Must be completed and committed before any generator changes.**

Per P-DEV-04, MAJOR amendments require:
1. Consultation with `kicad.expert` to confirm footprint approach for a daughter board module
   (4-pin THT header in `Custom.pretty/`).
2. Written amendment to `docs/constitution.md`.
3. Version increment: current is v4.3.0 → this amendment is **v5.0.0** (MAJOR — BOM substitution
   per §2.2 rule: "Substitutions require a MAJOR amendment").

### Amendment v5.0.0 change set

**§2.2 BOM table — remove placeholder U_BOOST row, add locked row:**

| Ref | Value / MPN | Package | Role |
|---|---|---|---|
| U_BOOST | DC-DC Boost Module — Amazon.nl B0D9VJKD1L | 4-pin 2.54 mm pitch THT daughter board header | 5V→12V boost converter for fan +12V rail; replaces discrete U1/L1/D1/C1/C2 stage per issue #177 |

**§2.2 — retire references to U1 (LM2587-12), L1 (100 µH), D1 (1N5822), C1/C2 (100 µF/25 V)**
from the locked BOM table.

**§3.1 P-HW-04 right-zone description** — replace:
> "U1+L1+D1+C1+C2 (boost converter chain)"

with:
> "U_BOOST (DC-DC boost module, Amazon.nl B0D9VJKD1L)"

**§5.2 power budget** — update the boost converter row to reflect the module's efficiency
(93% max, vs LM2587-12 typical 88%) and confirm the margin calculation (see §5 below).

**§10 Amendment History** — add v5.0.0 entry.

---

## 4. Hardware Implementation

### 4.1 Step 1 — Commit the KB file

`docs/kb/DC-DC-boost-module.md` is currently untracked on the branch. Commit it first:

```
git add docs/kb/DC-DC-boost-module.md
git commit -m "docs: add DC-DC boost module KB reference (Amazon B0D9VJKD1L)"
```

### 4.2 Step 2 — Create Custom Footprint

**File:** `hardware/kicad/footprints/Custom.pretty/DC-Boost-Module.kicad_mod`

The footprint represents the 4-pin 2.54 mm pitch THT header on the underside of the boost
module daughter board. Key parameters:

| Parameter | Value | Notes |
|---|---|---|
| Pad type | Through-hole, oval or round | Standard THT |
| Pad count | 4 | Single row, 1×4 |
| Pad pitch | 2.54 mm | Standard 0.1" |
| Pad drill diameter | 1.0 mm (minimum) | Verify against pin diameter of received module |
| Pad copper diameter | 1.8 mm | Standard for 1.0 mm drill |
| Pin numbering | 1=IN+, 2=IN−, 3=OUT+, 4=OUT− | Left to right (or top to bottom — confirm physical orientation) |
| Courtyard | Encloses module body + standoff clearance | Must be verified against physical unit; typical 28 mm × 17 mm for MT3608/XL6009 class |
| Silkscreen | Module outline + pin 1 marker | Include polarity arrow or dot |
| F.Cu only | Yes | All pads on F.Cu; courtyard/silkscreen on F.CrtYd / F.SilkS |
| Mount height | ~8–10 mm above PCB | Notation only (no 3D model required for v0.2) |

> ⚠️ **Physical verification required:** Before finalising the footprint, measure the actual
> B0D9VJKD1L module (pin pitch, body dimensions, header pin diameter) with callipers.
> Do not rely solely on Amazon product photos. The KB states "typical ~28 mm × 17 mm" — this
> must be confirmed.

The footprint can be created manually in KiCad Footprint Editor or via a generator script
following the pattern of `hardware/generator/gen_footprint_dht11.py` and
`hardware/generator/gen_footprint_j8.py`. A script approach is preferred for reproducibility.

### 4.3 Step 3 — Update Schematic Generator

**File:** `hardware/generator/components.py`

#### 4.3.1 Remove discrete boost symbol definitions

Remove the following four `s.define()` blocks (they are used **only** for the boost stage;
no other component in the schematic uses these symbol types):

```python
# REMOVE:
s.define("Custom:Boost_Converter", ...)   # LM2587-12
s.define("Custom:Inductor", ...)          # L1 100µH
s.define("Custom:Diode_Schottky", ...)    # D1 1N5822
s.define("Custom:Cap_Elec", ...)          # C1, C2 100µF/25V
```

#### 4.3.2 Add new module symbol definition

Add one new `s.define()` call for the 4-pin boost module. Position it where the old boost
defines were (preserving readability order — power section before signal section):

```python
# New: DC-DC Step-Up Boost Module (Amazon.nl B0D9VJKD1L)
# 4-pin 2.54mm THT daughter board: IN+(1), IN-(2), OUT+(3), OUT-(4)
# Module contains IC, inductor, diode, caps, and output trimmer internally.
s.define("Custom:DC_Boost_Module", "U", "DC-Boost-Module",
         "Custom:DC-Boost-Module",
         "https://www.amazon.nl/dp/B0D9VJKD1L",
         body_w=10.16, body_h=10.16,
         pins_left=[
             ("IN+",  "1", "power_in"),
             ("IN-",  "2", "power_in"),
         ],
         pins_right=[
             ("OUT+", "3", "power_out"),
             ("OUT-", "4", "power_in"),
         ])
```

> **Pin type rationale (P-SCH-04/P-SCH-05):**
> - `IN+` / `IN-` / `OUT-` → `"power_in"` (consuming or connecting to rail)
> - `OUT+` → `"power_out"` (this pin **drives** the +12V rail; must be `power_out` to prevent
>   `power_pin_not_driven` ERC error)

#### 4.3.3 Remove discrete boost component instantiations

Remove the entire boost subcircuit block from `build_schematic()`, including:

- Constants: `BOOST_ROW_Y`, `BYPASS_Y`, `C1_CX`, `L1_CX`, `U1_CX`, `D1_CX`, `C2_CX`
- Section header: `s.text("5V -> 12V Boost  (U1 / LM2587-12)", ...)`
- Component calls: `s.component(...)` for C1, L1, U1, D1, C2
- All associated `s.power(...)` and `s.label(...)` wiring calls for those components

#### 4.3.4 Add U_BOOST component instantiation

Replace the removed block with:

```python
# -----------------------------------------------------------------------
# U_BOOST — DC-DC Step-Up Boost Module (Amazon.nl B0D9VJKD1L)
# Replaces discrete U1/L1/D1/C1/C2 (issue #177).
# 5V input → 12V regulated output (module trimmer pre-set to 12V before install).
# -----------------------------------------------------------------------
s.text("5V → 12V Boost Module (U_BOOST)", <x>, <y>, size=2.54, bold=True, color=BLUE)

BOOST_MOD_CX = 76*G    # 193.04 mm — centre of module symbol; within right zone (x ≥ 33.19 mm)
BOOST_MOD_Y  = 28*G    # 71.12 mm — same row as the former boost stage

pUB = s.component("Custom:DC_Boost_Module", "U_BOOST", "DC-Boost-Module",
                  "Custom:DC-Boost-Module",
                  BOOST_MOD_CX, BOOST_MOD_Y)
s.power("+5V",   *pUB["1"])                        # IN+  → +5V from J8 pin 40
s.power("GND",   *pUB["2"])                        # IN-  → GND
s.power("+12V",  *pUB["3"], pin_type="power_out")  # OUT+ → +12V rail (drives rail)
s.power("GND",   *pUB["4"])                        # OUT- → GND
```

> **Note on coordinates:** `BOOST_MOD_CX = 76*G` places the symbol well within the right zone
> on the schematic canvas (schematic coordinates are unrelated to PCB mm dimensions). Adjust
> `x`/`y` values to avoid overlap with J8 or fan header symbols. The schematic layout uses
> G=2.54 mm units; all coordinates must be multiples of G (P-HW-06).

#### 4.3.5 Update module docstring

Update the module-level docstring in `components.py`:
- Change "Power chain:" line from referencing `L1/U1 boost converter` to `U_BOOST boost module`.
- Remove `BOOST_SW` label from the power chain description.

#### 4.3.6 Update `bom.py` docstring

Update the module-level docstring in `bom.py`:
- Change "Power chain: J8 pin 40 (+5V from Waveshare VBUS) → U1 / LM2587-12 (5V→12V boost)…"
  to "Power chain: J8 pin 40 (+5V from Waveshare VBUS) → U_BOOST / DC-DC boost module (5V→12V)…"

### 4.4 Step 4 — Update BOM Generator

**File:** `hardware/generator/bom.py`

Remove the four discrete boost rows:
```python
# REMOVE these rows:
["U1","LM2587-12", ...],
["L1","100uH", ...],
["D1","1N5822", ...],
["C1","100uF_25V", ...],
["C2","100uF_25V", ...],
```

Add the module row:
```python
["U_BOOST","DC-Boost-Module","Custom:DC-Boost-Module","1",
 "Generic","B0D9VJKD1L",
 "5V→12V DC-DC Step-Up Boost Module, 2A max, 93% efficiency, 4-pin 2.54mm THT — Amazon.nl B0D9VJKD1L",
 "https://www.amazon.nl/dp/B0D9VJKD1L"],
```

### 4.5 Step 5 — Regenerate Schematic and BOM

```bash
cd hardware
python generate_project.py
```

Expected outputs:
- `hardware/kicad/PoE-FanController.kicad_sch` regenerated (U_BOOST present; U1/L1/D1/C1/C2 absent)
- `hardware/bom/bom.csv` regenerated (U_BOOST row; old discrete rows absent)

### 4.6 Step 6 — Run ERC

```bash
kicad-cli sch erc \
  --output hardware/kicad/erc_output.json \
  hardware/kicad/PoE-FanController.kicad_sch
```

Gate: **zero errors**. Any `power_pin_not_driven` error on +12V indicates `OUT+` pin type was
not set to `power_out` — fix in the define() call and regenerate.

### 4.7 Step 7 — Update PCB in KiCad GUI

Open `hardware/kicad/PoE-FanController.kicad_pcb` in KiCad 10.0.3:

1. **Import updated netlist** (Tools → Update PCB from Schematic) — KiCad will flag
   U1/L1/D1/C1/C2 footprints as "not in netlist" and U_BOOST as "not placed". Remove the
   old footprints, place U_BOOST.
2. **Delete old footprints**: Select and delete U1, L1, D1, C1, C2 on F.Cu.
3. **Place U_BOOST**: Place `Custom:DC-Boost-Module` footprint in right zone (x = 33.19–56 mm,
   y anywhere within 0–78 mm). Centre approximately where U1 was (~(44, 25) mm is a reasonable
   start — adjust for courtyard clearance from J8 Row B pads at x = 33.19 mm and J2–J5 headers).
4. **Route power traces**:
   - IN+ pad → `+5V` copper pour (or trace to nearest `+5V` via point); ≥ 1.0 mm width.
   - IN− pad → `GND` copper pour; ≥ 1.0 mm width.
   - OUT+ pad → `+12V` pour or trace to J2–J5 VCC_FAN pins; ≥ 1.0 mm width.
   - OUT− pad → `GND` copper pour; ≥ 1.0 mm width.
5. **Verify zero-crossing rule**: No trace from U_BOOST crosses x = 33.19 mm (J8 Row B
   boundary). Confirm in PCB inspector.
6. **Regenerate copper pours** (Edit → Fill All Zones).

### 4.8 Step 8 — Run DRC

Run DRC (Inspect → Design Rules Checker) in KiCad or via CLI:

```bash
kicad-cli pcb drc \
  --output hardware/kicad/drc_output.json \
  --exit-code-violations \
  hardware/kicad/PoE-FanController.kicad_pcb
```

Gate: **zero violations**. Common failure modes:
- Unconnected nets on U_BOOST pads → check trace routing
- Courtyard overlap with J8 or fan headers → move U_BOOST placement
- Trace width < 1.0 mm on power nets → widen in interactive router

### 4.9 Step 9 — Commit and Open PR

Commit message convention (P-DEV-01):
```
hw: replace discrete boost stage (U1/L1/D1/C1/C2) with module U_BOOST (#177)
```

Include in the same PR:
- `docs/constitution.md` (amendment v5.0.0)
- `hardware/generator/components.py`
- `hardware/generator/bom.py`
- `hardware/kicad/footprints/Custom.pretty/DC-Boost-Module.kicad_mod`
- `hardware/kicad/PoE-FanController.kicad_sch` (regenerated artefact)
- `hardware/kicad/PoE-FanController.kicad_pcb` (PCB edits)
- `hardware/kicad/erc_output.json`
- `hardware/bom/bom.csv`
- `docs/kb/DC-DC-boost-module.md`
- `docs/features/replace-boost-module/spec.md`
- `docs/features/replace-boost-module/plan.md`

---

## 5. Power Budget Validation

### 5.1 Module Current Budget

| Parameter | Value | Basis |
|---|---|---|
| Fan load (4 fans, 100% duty) | 1.0 A @ 12 V = 12.0 W | Constitution §5.2 (≤1.0 A at max) |
| Module output current at load | 1.0 A | Within 2.0 A rated max — **50% margin** |
| Module efficiency at load | ≥ 90% (spec: 93% max) | KB / Amazon product page |
| Input power required | 12.0 W / 0.90 = 13.3 W | Worst-case at 90% efficiency |
| Input current from +5V rail | 13.3 W / 5.0 V = **2.67 A** | Drawn from J8 pin 40 (VBUS) |

### 5.2 Total PoE Power Budget (Revised)

| Consumer | Rail | Current | Power |
|---|---|---|---|
| 4× PWM fan (max) | 12 V | 1.0 A | 12.0 W |
| U_BOOST conversion loss (90% eff.) | 5V→12V | — | ~1.3 W |
| Waveshare ESP32-P4-ETH board | 5V (via J8) | ~800 mA | ~4.0 W |
| DHT11 + TACH pull-ups | 3.3V | <15 mA | ~0.05 W |
| Waveshare internal losses (est.) | — | — | ~2.0 W |
| **Total** | | | **~19.4 W** |
| **802.3at Class 4 budget (Waveshare onboard PD)** | | | **20.0 W** |
| **Margin** | | | **~0.6 W (3%)** |

> ⚠️ **Tighter margin than before:** The new module is more efficient (90–93% vs LM2587-12
> typical 88%), but the overall PoE margin is now ~0.6 W (3%) vs the constitution's previous
> ~1.1 W (5.5%). The margin is still positive and within the Class 4 budget. The constitution
> §5.2 "tight margin warning" must be updated to reflect this revision.
>
> At the typical fan load (4 fans × 0.3 A = 1.2 A → but capped by the power budget at 1.0 A
> for 12 W): this is within the module's 2.0 A output limit.

### 5.3 VBUS Current Verification (Critical Risk — see §8)

The input current from J8 pin 40 (VBUS, +5V) is **2.67 A** for boost + **0.8 A** for Waveshare
ESP32 = **3.47 A total** from the 5V rail. The Waveshare SKU 32088's VBUS output current capacity
is flagged as "MEDIUM confidence" in the constitution. This must be verified from the Waveshare
SKU 32088 datasheet or schematic before PCB fabrication.

---

## 6. ERC / DRC Gate Requirements

### 6.1 ERC Requirements

The regenerated schematic must satisfy all of the following before PCB work begins:

| Check | Expected Result | Failure Mode |
|---|---|---|
| `power_pin_not_driven` on `+12V` | ✅ Zero — OUT+ is `power_out` | Incorrect pin type in define() |
| `pin_not_connected` on U_BOOST | ✅ Zero — all 4 pins connected | Missing `s.power()` call |
| `wire_dangling` | ✅ Zero — all labels resolve | Stale BOOST_SW label not removed |
| Total ERC errors | **0** | Any non-zero blocks PR merge |

> **BOOST_SW label check:** The old boost schematic used a `BOOST_SW` net label. Ensure no
> orphaned `s.label("BOOST_SW", ...)` calls remain in the generator after the cleanup.

### 6.2 DRC Requirements

The updated PCB must satisfy all of the following before the PR is opened:

| Check | Expected Result |
|---|---|
| Unconnected nets | 0 — all U_BOOST pads routed |
| Courtyard violations | 0 — U_BOOST courtyard clear of all neighbours |
| Clearance violations | 0 — power traces ≥ 0.2 mm general clearance |
| Footprint validity | `Custom:DC-Boost-Module` resolves in project library |
| Track width (power nets) | All +5V, +12V, GND traces on U_BOOST ≥ 1.0 mm |
| Zero-crossing rule | No U_BOOST trace at x < 33.19 mm |

---

## 7. Bring-up Checklist Additions

Add the following steps to the §8.4 hardware bring-up checklist in the constitution:

1. **Pre-install module trim:** With the B0D9VJKD1L powered at 5.0 V on a bench supply
   (not on the PCB), adjust the trimmer potentiometer until OUT+ measures 12.0 V ± 0.1 V.
2. **No-load 12V rail test:** After PCB assembly, power via PoE before seating fans.
   Measure J2 pin 2 (VCC_FAN) → expect 12.0 V ± 0.3 V.
3. **Full-load 12V rail test:** With all 4 fans connected at 100% duty, measure VCC_FAN →
   expect ≥ 11.5 V (allow for module output droop at load).
4. **Module temperature check:** After 10 min full-load, verify module PCB temperature
   ≤ 70 °C by touch or IR thermometer (module has thermal overload protection, but sustained
   >70 °C indicates inadequate derating).

---

## 8. Risks

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | **VBUS current limit too low.** Waveshare SKU 32088 VBUS (J8 pin 40) cannot supply 3.47 A total (boost + ESP32). | Medium | High — feature blocked or requires redesign | Verify from Waveshare schematic / datasheet before PCB fab. If limited, consider adding a dedicated 5V supply via an external regulator. Flag to `poe.expert`. |
| R-02 | **Physical dimensions don't match footprint.** Received B0D9VJKD1L has different body size or pin pitch than documented (Amazon sellers sometimes swap stock). | Low–Medium | Medium — footprint must be re-created; PCB rework if already fabricated | Measure unit with callipers before PCB fabrication. Do not fab until footprint is confirmed against physical unit. |
| R-03 | **Module output voltage not stable.** Trimmer drifts or trim is inaccurate — fans receive <11.5 V or >13 V. | Low | Medium — fans may under/over-speed | Pre-set trimmer before install (bring-up step 1). Consider adding test point TP1 on `+12V` net for in-situ measurement. |
| R-04 | **ERC `power_pin_not_driven` error.** OUT+ pin type set incorrectly in define(). | Low | Low — blocks regeneration; easy fix | Set `pin_type="power_out"` on pin 3 (OUT+) in `s.define()`. Verify in ERC run. |
| R-05 | **Stale BOOST_SW label.** If any `s.label("BOOST_SW", ...)` call is missed during cleanup, a dangling label ERC error appears. | Low | Low — easy fix | Search generator for all "BOOST_SW" references and remove all of them. |
| R-06 | **Courtyard DRC collision.** U_BOOST module body (~28×17 mm) is large relative to the right zone (22.81 mm wide). Courtyard may overlap with J8 Row B or J2–J5. | Medium | Medium — requires PCB placement adjustment | Place U_BOOST so its courtyard left edge ≥ x = 33.19 mm + clearance. Stagger or rotate if needed. Verify with DRC before routing. |
| R-07 | **PoE budget margin very tight (3%).** Any additional load (e.g. more fans, different fan models with higher startup current) could exceed the 20 W Class 4 cap. | Low–Medium | High — device may brown-out under PoE | Keep the constitution's tight-margin warning updated. Do not add further 12V loads without `poe.expert` review. |

---

## 9. Constitution Compliance Summary

| Principle | How This Plan Satisfies It |
|---|---|
| **P-HW-02** | U_BOOST footprint: all pads on F.Cu; courtyard on F.CrtYd only. |
| **P-HW-04** | U_BOOST placed in right zone (x = 33.19–56 mm). Zero-crossing rule enforced. |
| **P-HW-05 / P-KI-04** | All schematic changes in `hardware/generator/components.py`. `.kicad_sch` regenerated by script. No manual edits. |
| **P-HW-06** | Symbol coordinates on 2.54 mm grid. PCB footprint on ≤ 0.1 mm grid. |
| **P-HW-07** | All four U_BOOST power traces ≥ 1.0 mm. Power net class enforced in DRC. |
| **P-HW-08** | GND copper pour unchanged; single GND domain (SELV). OUT− and IN− both connect to GND pour. |
| **P-HW-09** | U_BOOST is a board-to-board mount, not an external cable connector. P-HW-09 does not apply. |
| **P-KI-01** | All PCB work done in KiCad 10.0.3. |
| **P-KI-05** | Custom footprint in `hardware/kicad/footprints/Custom.pretty/`. |
| **P-KI-07** | PCB edited in KiCad GUI only. Generator does not touch `.kicad_pcb`. |
| **P-SCH-03** | Section header: `bold=True`, `size=2.54`, `color=(0,0,255)`. |
| **P-SCH-04** | OUT+ (drives +12V rail) → `pin_type="power_out"`. |
| **P-SCH-05** | IN+ / IN− / OUT− → `"power_in"`. Not `power_out` (they do not drive rails). |
| **P-TEST-01** | ERC run after generator; must report zero errors before PCB work. |
| **P-TEST-03** | DRC run after PCB edits; must report zero violations before PR merge. |
| **P-DEV-01** | Commit messages: `hw:` prefix. |
| **P-DEV-04** | MAJOR amendment (v5.0.0) committed to `docs/constitution.md` before generator changes. |
| **P-POE-01** | No change to PoE class or PD negotiation. Device remains 802.3at Class 4. |
| **P-POE-02** | No primary-side changes. Boost module is entirely on the secondary (SELV) side. |
| **P-ISO-01–05** | Boost module is on the SELV secondary side (x > 38 mm is the old barrier — moot since the daughter board is all-SELV per v3.0.0 amendment). No isolation concern. |

---

## 10. Files Changed

| File | Change Type | Description |
|---|---|---|
| `docs/constitution.md` | Amend (MAJOR v5.0.0) | Lock U_BOOST MPN; retire U1/L1/D1/C1/C2 from §2.2; update P-HW-04 zone description; update §5.2 power budget; add §10 amendment entry |
| `docs/kb/DC-DC-boost-module.md` | Commit (untracked) | KB reference for B0D9VJKD1L module |
| `hardware/generator/components.py` | Modify | Remove 4 symbol defines + 5 component instantiations; add DC_Boost_Module define + U_BOOST instance; update docstrings |
| `hardware/generator/bom.py` | Modify | Remove U1/L1/D1/C1/C2 rows; add U_BOOST row; update docstring |
| `hardware/kicad/footprints/Custom.pretty/DC-Boost-Module.kicad_mod` | Create | 4-pin 1×4 2.54 mm THT footprint for boost module header |
| `hardware/kicad/PoE-FanController.kicad_sch` | Regenerate | Build artefact of generate_project.py |
| `hardware/bom/bom.csv` | Regenerate | Build artefact of generate_project.py |
| `hardware/kicad/erc_output.json` | Update | ERC result: 0 errors |
| `hardware/kicad/PoE-FanController.kicad_pcb` | Edit (KiCad GUI) | Remove U1/L1/D1/C1/C2 footprints; add + place + route U_BOOST |
| `docs/features/replace-boost-module/spec.md` | Create | This feature spec |
| `docs/features/replace-boost-module/plan.md` | Create | This technical plan |

---

## 11. Open Questions / Risks Requiring Resolution Before Fabrication

1. **[VERIFY BEFORE FAB] VBUS current limit of Waveshare SKU 32088 J8 pin 40.** Total current
   drawn from the 5V rail is ~3.47 A (2.67 A boost + 0.8 A ESP32). The Waveshare board's
   internal 5V regulator capacity from its PoE PD must be confirmed. Delegate to `poe.expert`
   if not clearly documented in the SKU 32088 schematic.

2. **[VERIFY BEFORE FAB] Physical module dimensions.** Measure the received B0D9VJKD1L unit
   (body length/width, pin pitch, pin diameter) with callipers before committing the footprint.

3. **[VERIFY BEFORE FAB] Module pin ordering.** Confirm the physical IN+/IN−/OUT+/OUT− pin
   sequence on the received unit against the Amazon product description. Some batches of
   generic boost modules have been shipped with reversed header orientations.

4. **[CONSIDER] Test point for +12V.** Given the tight output voltage trim requirement, adding
   a test point (TP1) on the `+12V` net near U_BOOST OUT+ is strongly recommended for
   in-circuit voltage verification. This would be a small PCB-only addition with no schematic
   impact; confirm with `kicad.expert`.
