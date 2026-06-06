# Technical Plan: SCH — Improve Schematic Readability to Match DMX_NODE Reference Style

**GitHub Issue:** #25 — "SCH: improve schematic readability to match DMX_NODE reference style"
**Branch:** `feature/25-schematic-readability`
**Merged via:** PR #24 (core implementation complete on `main`)
**Status:** Implementation complete; this document records decisions, acceptance criteria, and remaining gaps
**Date:** 2026-06-06

---

## 1. Overview

The PoE FanController schematic is produced entirely by `hardware/generate_project.py` — manual edits to
the `.kicad_sch` file are forbidden (P-HW-05, P-KI-04). Issue #25 tasked the team with closing the gap
between the generated schematic and the KiCad 10 best-practice patterns demonstrated by the reference
project at `docs/reference-samples/DMX_NODE/DMX_NODE.kicad_sch`.

The core implementation was delivered in PR #24 (commit `6e7d1b1`). This plan documents:

- What was implemented and where in the generator (§2)
- The technical decisions behind each change (§3)
- Acceptance criteria a tester can verify without opening Python (§4)
- Remaining gaps not addressed by PR #24 (§5)
- Constitution compliance mapping (§6)

---

## 2. Architecture Fit

### 2.1 Schematic Block Layout (A2 sheet)

| Block | x range (mm) | y range (mm) | Section header |
|---|---|---|---|
| PoE Power Input | 25–110 | 30–100 | ✅ Blue bold 2.54 mm |
| 3.3V Regulator | 25–145 | 110–185 | ✅ Blue bold 2.54 mm |
| ESP32-WROOM-32 | 155–295 | 30–210 | ✅ Blue bold 2.54 mm |
| Fan Headers (4×) | 305–420 | 30–200 | ✅ Blue bold 2.54 mm |
| USB / UART Bridge | 25–195 | 215–385 | ✅ Blue bold 2.54 mm |

The isolation barrier at x = 38 mm (P-ISO-02) bisects the PoE Input block. J1 (x ≈ 38 mm) sits on
the barrier; U1 Ag9905M (x ≈ 97 mm) sits to the right, on the secondary (SELV) side of the isolation
domain boundary. `GND_PRI` is connected only to U1 pin 6 (VOUT_N) and has no connections to `GND`.

### 2.2 Signal Classification

Per P-SCH-01, every signal crossing two functional blocks must use `global_label`. The table below
shows every net in the schematic and its correct label type:

| Net(s) | Crosses blocks? | Correct type | Implemented |
|---|---|---|---|
| `FAN1_PWM` … `FAN4_PWM` | ESP32 ↔ Fan Headers | `global_label` | ✅ |
| `FAN1_TACH` … `FAN4_TACH` | ESP32 ↔ Fan Headers | `global_label` | ✅ |
| `ESP_EN` | ESP32 ↔ USB/UART Bridge | `global_label` | ✅ |
| `BOOT` | ESP32 ↔ USB/UART Bridge | `global_label` | ✅ |
| `ESP_TX` | ESP32 ↔ USB/UART Bridge | `global_label` | ✅ |
| `ESP_RX` | ESP32 ↔ USB/UART Bridge | `global_label` | ✅ |
| `USB_DP` | USB/UART Bridge (J6 ↔ U4) | `global_label` | ✅ |
| `USB_DN` | USB/UART Bridge (J6 ↔ U4) | `global_label` | ✅ |
| `POE_A+`, `POE_A-`, `POE_B+`, `POE_B-` | Intra-block (J1 and U1 both in PoE Input block) | `label` ✅ | ✅ |
| `+3V3_SW` | Intra-block (3.3V Regulator) | `label` ✅ | ✅ |
| `GPIO2` | Intra-block (ESP32 block: U3 IO2 → R3) | `label` ✅ | ✅ |
| `LED_A` | Intra-block (ESP32 block: R3 → LED1) | `label` ✅ | ✅ |
| `CH340_V3` | Intra-block (USB/UART Bridge: U4 V3 → C7) | `label` ✅ | ✅ |
| `CC1`, `CC2` | Intra-block (USB/UART Bridge: J6 → R9/R10) | `label` ✅ | ✅ |
| `NTC_ADC` | Intra-block (ESP32 block: U3 IO32 → R4/NTC1) | `global_label` | ✅ Fixed in T002 — all three endpoints use `global_label` |

---

## 3. Implementation: What Was Done and Why

### 3.1 `global_label()` Method (lines 273–290 of `generate_project.py`)

**What:** The `global_label()` method emits KiCad 10 S-expression global label elements in the
correct format for format version `20260101`.

**Key format details:**
```
(global_label "<name>"
  (shape <shape>)
  (at <x> <y> <angle>)
  (fields_autoplaced yes)
  (effects (font (size 1.27 1.27)) (justify left|right))
  (uuid "...")
  (property "Intersheetrefs" "${INTERSHEET_REFS}"
    (at ...) (effects ... (hide yes))))
```

**Why `fields_autoplaced yes`:** Required by KiCad 10 to suppress a layout-dirty flag on every open.
Without it, KiCad marks the schematic as modified on first view even when nothing has changed.

**Why `Intersheetrefs` property:** KiCad 10 requires this property on every global label to populate
the cross-reference table. Omitting it causes a benign but noisy ERC warning.

**Why no `pin "~"` element:** KiCad 10 global labels do not have a `pin` child element. Emitting one
(as older KiCad versions did) causes a parse error on load.

**Why `justify left` (not `justify left bottom`):** The `bottom` baseline modifier is valid for
`label` elements but not for `global_label` elements in KiCad 10. Omitting it matches the reference
schematic and the KiCad 10 parser's expectations.

**Angle and justify logic (line 278):**
```python
justify = "right" if angle == 180 else "left"
```
Global labels on right-side pins face rightward (angle=0, justify=left). Labels on left-side pins
of components placed to the right (angle=180) face leftward (justify=right).

### 3.2 Inter-Block Signal Promotion (lines 694–893)

All eight cross-block signal groups were promoted to `global_label` in `build_schematic()`:

| Signal group | Generator call | Shape |
|---|---|---|
| Fan PWM outputs (IO25–IO14) | `s.global_label("FANx_PWM", *p["n"], shape="output")` | `output` |
| Fan TACH inputs (IO36/39/34/35) | `s.global_label("FANx_TACH", *p["n"], shape="input")` | `input` |
| EN pull-up circuit | `s.global_label("ESP_EN", ..., shape="input")` | `input` |
| BOOT pull-up circuit | `s.global_label("BOOT", ..., shape="passive")` | `passive` |
| UART bridge TX/RX | `s.global_label("ESP_TX/RX", ..., shape="input/output")` | directional |
| USB differential pair | `s.global_label("USB_DP/DN", ..., shape="bidirectional")` | `bidirectional` |

**Shape selection rationale:**
- `input` / `output` — used where the driving direction is unambiguous (ESP32 drives PWM, fans drive TACH)
- `passive` — used for BOOT (bidirectional: driven low by SW2, read by ESP32) to avoid ERC shape mismatch
- `bidirectional` — USB differential pair (half-duplex, direction switches at protocol level)

### 3.3 Isolated Ground Domains (lines 615–616, 630–641)

Two distinct ground nets are implemented:

| Net | Pin type | Placed on | Purpose |
|---|---|---|---|
| `GND_PRI` | `power_out` | U1 pin 6 (VOUT_N) | Primary-side return; isolated from secondary |
| `GND` | `power_out` | Secondary components (LM2596 GND, D1, ESP32, etc.) | SELV secondary return |

**Why `GND_PRI` uses `power_out`:** U1 Ag9905M drives its own return rail through the isolation
transformer. Making it `power_out` ensures KiCad's ERC recognises the rail as driven, suppressing
`power_pin_not_driven`. The `define_power()` call is:
```python
s.power("GND_PRI", *p["6"], pin_type="power_out")   # line 616
```
The `define_power()` method (line 165) registers the lib_symbol with the supplied `pin_type`, so the
lib_symbols section of the output `.kicad_sch` contains `GND_PRI` with `pin power_out line`.

**No bridge between domains:** The generator never connects a wire, label, or power symbol to both
`GND_PRI` and `GND`. The physical isolation at x = 38 mm (P-ISO-02) is mirrored in the net topology.

### 3.4 Section Header Style (lines 587–588, 624, 680, 789, 822)

All five functional block headers use:
```python
s.text("<Block Name>", x, y, size=2.54, bold=True, color=BLUE)  # BLUE = (0, 0, 255)
```

The `text()` method (line 320) renders:
```
(text "..." (at ...)
  (effects (font (color 0 0 255 1) (bold yes) (size 2.54 2.54))))
```

This matches the DMX_NODE reference exactly (blue RGB triple, bold, 2.54 mm). No ASCII decoration
(`===`, `---`, `***`) is present anywhere in the generator.

### 3.5 Power Symbol `pin_type` Defaults (lines 258, 165)

**`power()` method default changed to `power_out` (line 258):**
```python
def power(self, name, x, y, angle=0, pin_type="power_out"):
```
Previously defaulted to `power_in`, which caused KiCad ERC to flag every power rail as
`power_pin_not_driven` unless `PWR_FLAG` symbols were also placed. Changing the default to
`power_out` means each power symbol instance drives its rail, satisfying the ERC rule without
requiring additional `PWR_FLAG` symbols anywhere on the schematic.

**`define_power()` default also `power_in` → retained:** The lib_symbol registration in
`define_power()` (line 165) still defaults to `power_in` because a lib_symbol registered once as
`power_out` would conflict if a second placement passed `power_in`. In practice, every `power()`
call overrides this via `pin_type=` in the placement S-expression, so the lib_symbol's pin type
is overridden per-instance.

### 3.6 Ag9905M VPORT Pin Type: `passive` (lines 393–397)

The Ag9905M's four input ports (VPORT_A+, VPORT_A−, VPORT_B+, VPORT_B−) were previously defined
with `power_in` pin type. This caused four spurious `power_pin_not_driven` ERC errors because KiCad
expected a `power_out` source for each of these "power" pins — but they are actually transformer
primary winding inputs, not power rails.

Changing to `passive` (line 393–396) correctly models them as general-purpose pins with no power-rail
semantics, eliminating those four ERC errors:
```python
("VPORT_A+", "1", "passive"),
("VPORT_A-", "2", "passive"),
("VPORT_B+", "3", "passive"),
("VPORT_B-", "4", "passive"),
```

### 3.7 `pwr_flag()` Method: Exists but Not Called

The `pwr_flag()` method (lines 187–201) is implemented and correct but is **intentionally not called**
from `build_schematic()`. The decision to omit `PWR_FLAG` symbols is deliberate:

- P-SCH-04 (constitution §7A) explicitly states that the `power_out` default on every power symbol
  instance makes `PWR_FLAG` symbols unnecessary.
- Every power rail (`+12V`, `GND`, `+3V3`, `GND_PRI`) is driven by at least one symbol instance
  placed with `pin_type="power_out"`. This is equivalent to what `PWR_FLAG` would provide.
- The DMX_NODE reference places `PWR_FLAG` because it uses `power_in` defaults — a different design
  pattern. Our generator's `power_out` default achieves the same ERC outcome more concisely.

The method is retained in the codebase for future use if the power model ever changes.

---

## 4. Acceptance Criteria

Each criterion below is independently verifiable by a tester without modifying any source file.

### 4.1 ERC Result (P-TEST-01)

| Criterion | How to verify | Expected result |
|---|---|---|
| **Zero ERC errors** | Open `hardware/kicad/PoE-FanController.kicad_sch` in KiCad 10.0.3; run Inspect → Electrical Rules Checker | 0 errors |
| **Warnings are benign** | Review each warning in the ERC report | All warnings are `lib_symbol_mismatch` or `lib_symbol_issues`; no `power_pin_not_driven`, `pin_not_connected`, or `net_not_driven` |
| **ERC output committed** | Check `hardware/kicad/erc_output.json` in the repository | File present and reflects the current 0-error run (see §5.2 for gap) |

### 4.2 Global Labels in Generated Schematic

Run: `Select-String -Path hardware/kicad/PoE-FanController.kicad_sch -Pattern "global_label"`

| Expected global label | Min occurrences | Direction |
|---|---|---|
| `FAN1_PWM`, `FAN2_PWM`, `FAN3_PWM`, `FAN4_PWM` | 2 each (ESP32 + fan header side) | `output` on fan side |
| `FAN1_TACH`, `FAN2_TACH`, `FAN3_TACH`, `FAN4_TACH` | 3 each (ESP32 + fan header + pull-up) | `output` on fan side |
| `ESP_EN` | 3 (ESP32, R1, SW1, U4/RTS) | `input` |
| `BOOT` | 4 (ESP32, R2, SW2, U4/DTR) | `passive` |
| `ESP_TX` | 3 (ESP32, U4, J7) | directional |
| `ESP_RX` | 3 (ESP32, U4, J7) | directional |
| `USB_DP`, `USB_DN` | 2 each (J6 + U4) | `bidirectional` |

### 4.3 Ground Domain Isolation (P-SCH-02)

| Criterion | How to verify |
|---|---|
| `GND_PRI` present in schematic | `Select-String ... -Pattern "GND_PRI"` returns results |
| `GND_PRI` placed only once | `Select-String ... -Pattern 'symbol.*lib_id.*power:GND_PRI'` returns exactly 1 symbol instance |
| `GND_PRI` is `power_out` in lib_symbols | `Select-String ... -Pattern 'GND_PRI_1_1' -Context 0,3` shows `pin power_out line` |
| No wire bridges `GND_PRI` to `GND` | Verify no net name appears in both ground domains in KiCad's net inspector |

### 4.4 Section Header Style (P-SCH-03)

Run: `Select-String -Path hardware/kicad/PoE-FanController.kicad_sch -Pattern '"text"'`

All five headers must appear with:
- `(color 0 0 255 1)` — blue
- `(bold yes)`
- `(size 2.54 2.54)`
- Text: `"PoE Power Input"`, `"3.3V Regulator (LM2596)"`, `"ESP32-WROOM-32"`, `"Fan Headers (4× PWM)"`, `"USB / UART Bridge"`

### 4.5 Generator Re-runs Cleanly

```
python hardware/generate_project.py
```
Must exit with code 0, no Python exceptions, and overwrite `hardware/kicad/PoE-FanController.kicad_sch`
with content identical (structurally) to what KiCad 10.0.3 would accept without errors.

### 4.6 No Intra-Block Labels Misclassified as Cross-Block

The following nets must use `label` (NOT `global_label`) — verifiable by inspecting generator source:

| Net | Element type in `.kicad_sch` | Why local is correct |
|---|---|---|
| `POE_A+`, `POE_A-`, `POE_B+`, `POE_B-` | `label` | J1 and U1 both within PoE Input block (x=25–110) |
| `+3V3_SW` | `label` | LM2596 switch node: U2→D1→L1, all within 3.3V Regulator block |
| `GPIO2` | `label` | U3 IO2 → R3: both within ESP32 block |
| `LED_A` | `label` | R3 → LED1: both within ESP32 block |
| `CH340_V3` | `label` | U4 V3 → C7: both within USB/UART Bridge block |
| `CC1`, `CC2` | `label` | J6 CC pins → R9/R10: all within USB/UART Bridge block |

---

## 5. Remaining Gaps

### 5.1 ✅ NTC_ADC Label Inconsistency — Resolved in T002 (commit `599edfd`)

**Resolved:** All three NTC_ADC endpoints now use `global_label` consistently.
IO32 shape corrected to `input` (ESP32 reads the ADC voltage); R4 pin 2 and NTC1 pin 1
changed from plain `label` to `global_label` with `shape="output"` (passive divider drives node).
The shape-mismatch KiCad warning on this net was eliminated — ERC now shows 85 warnings (was 86).

**Changes made in `hardware/generate_project.py`:**
- Line 699: `shape="output"` → `shape="input"` on ESP32 IO32 endpoint
- Line 776: `s.label("NTC_ADC", ...)` → `s.global_label("NTC_ADC", ..., shape="output", angle=180)`
- Line 783: `s.label("NTC_ADC", ...)` → `s.global_label("NTC_ADC", ..., shape="output")`

**Verification:** `Select-String hardware/kicad/PoE-FanController.kicad_sch -Pattern "NTC_ADC"`
returns 3 lines, all containing `global_label`; zero plain `label` hits for this net.

### 5.2 ✅ `erc_output.json` Stale — Resolved in T001 and T003 (commits `bd6c99c`, `d9412d4`)

**Resolved:** `hardware/kicad/erc_output.json` has been regenerated as valid JSON using
`kicad-cli sch erc --format json`. The file shows **0 errors, 85 warnings** (dated 2026-06-06T23:05:08)
and is committed to `feature/25-schematic-readability`.

- T001 (`bd6c99c`): Initial JSON regeneration as baseline (0 errors, 86 warnings)
- T003 (`d9412d4`): Refreshed after NTC_ADC fix (0 errors, 85 warnings; shape-mismatch eliminated)

---

## 6. Testing Strategy

### 6.1 Automated (Static Analysis)

| Check | Command | Pass condition |
|---|---|---|
| Generator runs cleanly | `python hardware/generate_project.py` | Exit code 0, no exceptions |
| Global labels present | `Select-String PoE-FanController.kicad_sch -Pattern "global_label"` | ≥ 38 matches |
| GND_PRI present | `Select-String PoE-FanController.kicad_sch -Pattern "GND_PRI"` | ≥ 5 matches |
| No PWR_FLAG (design decision) | `Select-String PoE-FanController.kicad_sch -Pattern "PWR_FLAG"` | 0 matches |
| Blue headers present | `Select-String PoE-FanController.kicad_sch -Pattern "color 0 0 255"` | ≥ 5 matches |
| No ASCII decoration | `Select-String PoE-FanController.kicad_sch -Pattern "===\|---\|\*\*\*"` | 0 matches |

### 6.2 Manual KiCad Verification

1. Open `hardware/kicad/PoE-FanController.kicad_sch` in KiCad 10.0.3
2. Inspect → Electrical Rules Checker → Run → confirm **0 errors**
3. Highlight net `GND_PRI` (click net, press \`) — confirm it highlights only U1 pin 6; no secondary components highlight
4. Highlight net `GND` — confirm it does NOT include U1 pin 6
5. Highlight `NTC_ADC` — confirm IO32, R4, and NTC1 all highlight together (nets connected)
6. Visually confirm five blue bold section headers at top of each block

---

## 7. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| KiCad version drift invalidates format | Low | Medium | P-KI-01 locks KiCad to 10.0.3; generator pinned to `version 20260101` |
| `NTC_ADC` label/global_label mismatch creates open net on future KiCad versions | ~~Low~~ **Eliminated** | High | ✅ Fixed in T002 — all three endpoints now `global_label`; shape-mismatch warning removed |
| `erc_output.json` not updated before merge | ~~Medium~~ **Eliminated** | Medium | ✅ Resolved in T001/T003 — JSON format, 0 errors, committed to feature branch |
| `pwr_flag()` method unused → silent regression if `power()` default reverts | Low | High | P-SCH-04 documents the design decision; any change to `power()` default must re-evaluate ERC |

---

## 8. Constitution Compliance

| Principle | Requirement | How This Plan Satisfies It |
|---|---|---|
| **P-HW-05** | Schematic is generated, not hand-edited | All changes are in `generate_project.py`; `.kicad_sch` is a build artefact |
| **P-KI-04** | Generator script is the schematic source of truth | `build_schematic()` is the only place schematic content is defined |
| **P-KI-01** | KiCad 10.0.3 exclusively | Format version `20260101` locked in `render()` header |
| **P-TEST-01** | Zero ERC errors required | ✅ 0 errors — verified post-PR #24 and after T002 NTC_ADC fix |
| **P-TEST-02** | ERC output recorded in `erc_output.json` | ✅ Resolved in T001 and T003 — valid JSON, 0 errors, committed |
| **P-DEV-02** | ERC gate for hardware PRs | ✅ Satisfied — `erc_output.json` current and showing 0 errors |
| **P-SCH-01** | Global labels for all inter-block signals | All 8 inter-block signal groups use `global_label` (§2.2, §3.2) |
| **P-SCH-02** | Isolated ground domains | `GND_PRI` (power_out, U1 only) and `GND` (secondary) — never bridged (§3.3) |
| **P-SCH-03** | Blue bold 2.54 mm section headers | All 5 blocks: `text(..., size=2.54, bold=True, color=(0,0,255))` (§3.4) |
| **P-SCH-04** | Power symbol pin types | Default `power_out` eliminates `power_pin_not_driven` without PWR_FLAG (§3.5) |
| **P-SCH-05** | Component pin types in custom symbols | Ag9905M VPORT pins changed to `passive`; no spurious ERC errors (§3.6) |
| **P-ISO-02** | Isolation barrier at x = 38 mm | `GND_PRI` only on primary side; `GND` only on secondary side; no net bridges them |

---

## 9. References

| Resource | Location | Relevance |
|---|---|---|
| Schematic generator | `hardware/generate_project.py` | Source of truth for all schematic content |
| Generated schematic | `hardware/kicad/PoE-FanController.kicad_sch` | KiCad 10 output; verify acceptance criteria against this file |
| Constitution §7A | `docs/constitution.md` §7A | P-SCH-01 through P-SCH-05 govern all readability decisions |
| Constitution §8.1 | `docs/constitution.md` §8.1 | P-TEST-01/-02 govern ERC requirements |
| DMX_NODE reference | `docs/reference-samples/DMX_NODE/DMX_NODE.kicad_sch` | Source of best-practice patterns analysed in this feature |
| KiCad expert agent | `.github/agents/kicad.expert.agent.md` | KiCad 10.0.3 format rules, schematic readability section |
| ERC output | `hardware/kicad/erc_output.json` | ✅ Refreshed — 0 errors, 85 warnings (T001, T003) |
