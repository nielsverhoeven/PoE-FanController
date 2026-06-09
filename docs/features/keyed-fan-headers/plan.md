# Technical Plan: Keyed Fan Headers (J2–J5)

**GitHub Issue:** #100 — Replace fan headers with keyed 4-pin female headers
**Spec:** `docs/features/keyed-fan-headers/spec.md`
**Branch:** `feature/100-keyed-fan-headers`
**Date:** 2026-06-09

---

## 1. Architecture Fit

J2–J5 are the four 4-wire Intel-spec PWM fan headers on the daughter board. They sit wholly in
the SELV secondary domain (P-ISO-01 through P-ISO-05 are not engaged), placed on the side board
edge (P-HW-03), and carry the +12 V, GND, TACH, and PWM nets that are defined in:

- **Schematic:** `hardware/generator/components.py` → `build_schematic()` → `Custom:Fan_Header`
  symbol definition and J2–J5 `component()` calls.
- **PCB:** `hardware/kicad/PoE-FanController.kicad_pcb` — four footprint instances maintained
  manually per P-KI-07.
- **Netlist import:** `hardware/generator/import_netlist.py` → `POWER_NETS` dict for GND/+12V
  pin assignments; TACH/PWM come from the exported netlist.

This feature touches **hardware only** — no firmware modules, no web UI, and no REST API
endpoints are modified. It satisfies the mandate of constitution principle P-HW-09 (amendment
v3.2.0), which requires keyed/polarised housings for all external cable connectors.

---

## 2. Footprint Selection — Resolved

### 2.1 What the issue requested vs. what is available

| Footprint ID | Status in KiCad 10.0.3 |
|---|---|
| `Connector_Molex:Molex_KK-254_22-23-2041_1x04_P2.54mm_Vertical` | **Not present** — no file with this name exists in `Connector_Molex.pretty` |
| `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` | **Present** — confirmed at `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\Connector_Molex.pretty\` |

### 2.2 Selected footprint

**`Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`**

Rationale:
- The KiCad footprint description reads: *"Molex KK-254 Interconnect System, old/engineering
  part number: AE-6410-04A, example for new part number: 22-27-2041, 4 Pins"*. The AE-6410-04A
  and 22-27-2041 are the same connector family as the 22-23-2041 specified in the issue; all are
  Molex KK-254 series, 1×4, 2.54 mm pitch, with a polarizing shroud.
- **Established project precedent:** J6 (DS18B20 probe connector) already uses
  `Connector_Molex:Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical` (the 3-pin sibling of the
  exact same family) — see `hardware/generator/components.py` line 214. Using the 4-pin version
  for J2–J5 is consistent with J6 and requires no new library entry.
- No custom footprint is required (NFR-05 satisfied).

### 2.3 Footprint dimensional data (measured from `.kicad_mod`)

| Property | Old: `PinHeader_1x04_P2.54mm_Vertical` | New: `Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` |
|---|---|---|
| Pad count | 4 | 4 |
| Pad pitch | 2.54 mm | 2.54 mm |
| Pad drill | 1.0 mm | 1.19 mm |
| Pad size | ~1.7 × 1.7 mm | 1.74 × 2.19 mm (pad 1: roundrect; pads 2–4: oval) |
| Courtyard X span | ~−1.0 to 8.6 mm | −1.77 to 9.39 mm (11.16 mm total) |
| Courtyard Y span | ~−1.0 to 1.0 mm | −3.42 to 3.38 mm (**6.8 mm total**) |
| Key indicator | None (unmarked pin 1 square pad only) | Shroud body + silk mark; pad 1 is roundrect |

> **Critical:** The Y-direction (perpendicular to the pin row) courtyard grows from ~2 mm to
> **6.8 mm** because of the polarising shroud body. At the current placement (rot=90°, so X
> and Y swap in board space), this growth is **in the board-interior direction**. With J2–J5
> at PCB x ≈ 58 mm and adjacent components (TACH pull-ups R5–R8, fan indicator resistors) at
> x ≈ 21–35 mm, there is approximately 20+ mm of clearance, making courtyard overlap unlikely.
> Placement must be verified in KiCad DRC after the swap (SC-07).

### 2.4 BOM amendment required

Constitution §2.2 currently locks J2–J5 as **Molex 47053-1000**. Changing to the KK-254 family
connector (`22-23-2041` or `22-27-2041`) requires a **MAJOR amendment** to §2.2 per the
constitution (§2.2: "Substitutions require a MAJOR amendment"). This amendment is mandated by
P-HW-09 (v3.2.0), which makes keyed connectors a constitutional requirement — the original
47053-1000 entry is retroactively non-compliant. The amendment must be completed and committed
before PCB Gerbers are submitted for fabrication.

**Recommended §2.2 update:**

| Ref | New Value / MPN | Package | Role |
|---|---|---|---|
| J2–J5 | Molex 22-23-2041 (KK-254, 4-pin keyed vertical header) | 1×4, 2.54 mm, through-hole | 12 V PWM fan headers — keyed, mating with standard 4-pin PC fan female housing (Molex 22-01-2042 or equivalent) |

---

## 3. Hardware Implementation Approach

### 3.1 Overview of changes

This feature requires changes in two places, executed in strict order:

```
[1] hardware/generator/components.py   ← schematic source of truth (P-KI-04 / P-HW-05)
        ↓  python hardware/generate_project.py
[2] hardware/kicad/PoE-FanController.kicad_sch   ← regenerated artefact (never edit directly)
        ↓  kicad-cli sch erc  (must pass with 0 violations)
[3] hardware/kicad/PoE-FanController.kicad_pcb   ← manual KiCad GUI edit only (P-KI-07)
        ↓  kicad-cli pcb drc  (must pass with 0 errors)
```

### 3.2 Schematic changes (generator package)

**File:** `hardware/generator/components.py`

**Change 1 — Symbol definition (line ~174):**
Update the `footprint` argument in the `Custom:Fan_Header` `s.define()` call.

```python
# BEFORE
s.define("Custom:Fan_Header", "J", "Fan_Header",
         "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "~",
         ...

# AFTER
s.define("Custom:Fan_Header", "J", "Fan_Header",
         "Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical",
         "https://www.molex.com/en-us/products/part-detail/22232041",
         ...
```

**Change 2 — Per-instance footprint override (line ~345–347):**
Update the `footprint` argument in each `s.component()` call for J2–J5 inside the `fan_data`
loop. Each call currently passes the old footprint string as a per-instance override, which
supersedes the symbol-level default.

```python
# BEFORE (inside the for loop, i = 0..3)
p = s.component("Custom:Fan_Header", f"J{2+i}", f"FAN{i+1}",
                "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
                FAN_CX, FJ_CY)

# AFTER
p = s.component("Custom:Fan_Header", f"J{2+i}", f"FAN{i+1}",
                "Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical",
                FAN_CX, FJ_CY)
```

> Note: Both the symbol-level `define()` footprint and the instance-level `component()` footprint
> must be updated. The `component()` call's footprint argument writes a per-instance `Footprint`
> property that KiCad uses for PCB cross-probing; the `define()` footprint is the default shown
> in the symbol editor. Keeping them in sync avoids silent mismatches.

**No other generator files require changes:**
- `hardware/generator/import_netlist.py` — `POWER_NETS` entries for J2–J5 use pin numbers 1 and 2
  (GND and +12V). These are unchanged; TACH/PWM come from the exported netlist. No edits needed.
- `hardware/generator/bom.py` — BOM generator picks up the footprint from the schematic; the
  updated footprint will automatically appear in the BOM output after regeneration.

**Regenerate the schematic:**
```
python hardware/generate_project.py
```
This overwrites `hardware/kicad/PoE-FanController.kicad_sch` with the updated footprint for all
four J2–J5 instances.

### 3.3 PCB changes (KiCad GUI — P-KI-07)

The `.kicad_pcb` file is maintained exclusively in the KiCad GUI. No script may write to it.

**Step-by-step:**

1. Open `hardware/kicad/PoE-FanController.kicad_pcb` in **KiCad 10.0.3**.
2. Run **Tools → Update PCB from Schematic (F8)**.
   - KiCad will detect the footprint change on J2–J5 and offer to update.
   - Accept all four footprint replacements.
   - The new `Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` footprints will be dropped at or
     near the existing J2–J5 positions.
3. **Re-place all four connectors:**
   - Target positions: J2 at (58, 10), J3 at (58, 22), J4 at (58, 34), J5 at (58, 46),
     all at rotation 90° (same as baseline).
   - After the footprint swap, verify that the shroud body (the F.CrtYd courtyard polygon,
     which extends 3.42 mm on one side and 3.38 mm on the other in the pin-perpendicular
     direction) does not overlap any adjacent component courtyard.
   - The key tab / shroud opening must face the board edge (toward larger X values, i.e., away
     from the interior components). At rotation 90°, pad 1 should be toward the top (lower Y)
     to match the standard fan-cable pin 1 (GND) assignment and the PCB silk orientation.
4. **Verify silk and fab layers** show pin 1 indicator on the correct side.
5. Save the PCB file.

> **Courtyard growth impact assessment:** At rot=90°, the footprint Y-courtyard (6.8 mm) maps
> to the board X-direction. The nearest interior components (TACH resistors R5–R8) are placed
> toward x ≈ 21–35 mm in board space; J2–J5 are at x ≈ 58 mm. The ~20+ mm gap means the
> additional ~1.4 mm of courtyard growth is very unlikely to cause conflicts, but DRC must
> confirm this (see §5).

### 3.4 Schematic changes — none beyond generator

Per P-HW-05 and P-KI-04, no direct edits to `.kicad_sch` are permitted. The file is regenerated
entirely from the generator. There are no new wires, labels, or power symbols required — only the
`Footprint` property value changes.

---

## 4. PoE / Power Considerations

None. This change is purely mechanical (footprint geometry). J2–J5 remain on the +12 V / GND
nets and carry the same maximum current (≤ 1.0 A total per P-HW-07 power track width). The power
budget in §5.2 of the constitution is unaffected. The SELV-only nature of the daughter board is
unchanged (P-ISO-01 through P-ISO-05 remain satisfied without any action).

---

## 5. Testing Strategy

### 5.1 Schematic ERC

After running `python hardware/generate_project.py`:

```
kicad-cli sch erc hardware/kicad/PoE-FanController.kicad_sch \
  --output hardware/kicad/erc_output.json \
  --format json --severity-error --severity-warning
```

**Pass criterion:** 0 ERC errors (P-TEST-01). The footprint-only change does not alter net
topology, so no new ERC issues are expected. The `erc_output.json` must be committed.

### 5.2 PCB DRC

After saving the updated PCB in KiCad GUI:

```
kicad-cli pcb drc hardware/kicad/PoE-FanController.kicad_pcb \
  --output hardware/kicad/drc_output.json \
  --format json --severity-error --severity-warning
```

**Pass criteria (P-TEST-03):**
- 0 DRC errors
- 0 unconnected items (the 71 ROUTING_PENDING ratsnest entries remain; these are categorised as
  unrouted, not as DRC errors — confirm they appear as "unconnected" ratsnest, not as DRC error
  violations in the JSON)
- DRC warning count must not exceed the 16-warning baseline recorded in `drc_current.json`
- Courtyard collision check: zero violations between J2–J5 and any adjacent footprint

The `drc_output.json` must be committed.

### 5.3 Manual placement check

After KiCad GUI placement:

- [ ] Inspect each of J2–J5 on F.Cu in 3D viewer: confirm shroud body is visible and key tab
      faces the board edge.
- [ ] Confirm no courtyard overlap markers (red DRC arrows) appear on screen.
- [ ] Confirm the spacing between J2–J5 is still visually consistent (12 mm centre-to-centre).
- [ ] Confirm silk-screen pin-1 indicator is on the correct side for each connector.

### 5.4 Hardware bring-up (post-fabrication)

- Attempt insertion of a 4-pin fan female housing in the correct orientation: must seat fully.
- Attempt insertion in the reverse orientation: shroud key must physically block insertion.
- Power on with one fan connected; verify expected TACH pulses and PWM response in firmware.
- No unit test changes required (no firmware logic changes).

---

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Courtyard overlap after swap** — Larger shroud body overlaps R5–R8 or indicator component courtyard | Low | Medium | Run DRC immediately after KiCad F8 update; if overlap occurs, shift J2–J5 slightly outward (+X direction) — side-edge placement gives room | 
| **KiCad F8 update not recognised** — Schematic UUID mismatch prevents automatic footprint update | Low | Medium | `import_netlist.py` runs `sync_pcb_paths.sync_paths()` to keep UUIDs aligned; if F8 still fails, delete old J2–J5 footprints and re-add from the updated netlist manually |
| **Wrong key-tab orientation after placement** — Shroud opens toward interior instead of board edge | Medium | Low | Visually verify in 3D viewer before saving; check that the pin-1 silk mark is on the board-edge side |
| **BOM amendment not completed before fabrication** — Gerbers submitted with stale §2.2 entry | Medium | High | Add a checklist item in the PR description; block merge to `main` until §2.2 MAJOR amendment is documented in `docs/constitution.md` |
| **Footprint not in KiCad's `fp-lib-table`** — `Connector_Molex` library not listed in the project's `fp-lib-table` | Low | High | Check `hardware/kicad/fp-lib-table`; if missing, add `(lib (name "Connector_Molex") (type "KiCad") (uri "${KICAD10_FOOTPRINT_DIR}/Connector_Molex.pretty") (options "") (descr ""))` |

---

## 7. Constitution Compliance

| Constitution Principle | How this plan satisfies it |
|---|---|
| **P-HW-02** — Single-sided placement (F.Cu only) | The `Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` footprint uses `*.Cu` + `*.Mask` pad layers (through-hole, both sides of copper, but component body on F.Cu only). Compliance unchanged from the existing pin header. |
| **P-HW-03** — Side-edge connector placement | J2–J5 remain at x ≈ 58 mm on the side edge. Placement positions are not changed by this plan. |
| **P-HW-05 / P-KI-04** — Generator is the schematic source of truth | All schematic changes are made in `hardware/generator/components.py` first; `.kicad_sch` is regenerated via `python hardware/generate_project.py`. Direct edits to `.kicad_sch` are forbidden and not performed. |
| **P-HW-06** — Grid discipline | Footprint origins remain on the existing PCB grid. No grid violations expected from a footprint swap. Schematic symbol origin is unchanged (only the `Footprint` property string changes). |
| **P-HW-09** — Keyed/polarised external connectors (v3.2.0 mandate) | **This feature directly satisfies P-HW-09** for J2–J5. The Molex KK-254 shroud physically prevents reverse insertion, meeting the requirement for a "mechanically keyed or polarized housing". |
| **P-KI-01** — KiCad 10.0.3 version lock | All KiCad GUI work must be performed in KiCad 10.0.3 locally. CI ERC/DRC runs in `kicad/kicad:10.0.2` (approved substitution per P-KI-01 PATCH). |
| **P-KI-05** — Custom symbols/footprints in-project | No custom footprint is required; the standard `Connector_Molex` library footprint is used. If the library is not in `fp-lib-table`, it is added — no file is created outside the project directory. |
| **P-KI-07** — PCB layout source of truth is KiCad GUI | No script writes to `.kicad_pcb`. All PCB changes are made interactively in KiCad 10.0.3 and committed as the resulting file. |
| **P-TEST-01** — Zero ERC errors | ERC is run after schematic regeneration; 0 violations required before any PCB work begins. |
| **P-TEST-03** — Zero DRC errors | DRC is run after PCB update; 0 errors required. Courtyard, clearance, unconnected net, and footprint validity checks are all included. |
| **P-TEST-02 / P-TEST-04** — ERC and DRC outputs recorded | `erc_output.json` and `drc_output.json` are updated and committed alongside the schematic and PCB changes. |
| **§2.2 BOM lock** — Substitutions require MAJOR amendment | The change from `47053-1000` to `22-23-2041` / `22-27-2041` is a BOM-locked substitution. A MAJOR amendment to `docs/constitution.md` §2.2 is required and must be completed before Gerbers are submitted. This amendment is mandated by P-HW-09 itself. |

---

## 8. Implementation Checklist

In recommended execution order:

- [ ] **1. Verify `fp-lib-table`** — Confirm `Connector_Molex` library is listed in
      `hardware/kicad/fp-lib-table`; add entry if missing.
- [ ] **2. Edit `components.py`** — Update `Custom:Fan_Header` symbol `define()` footprint and
      the J2–J5 loop `component()` footprint to
      `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`.
- [ ] **3. Regenerate schematic** — Run `python hardware/generate_project.py`; confirm no
      Python errors.
- [ ] **4. Run ERC** — `kicad-cli sch erc ...`; confirm 0 violations; commit `erc_output.json`.
- [ ] **5. Open PCB in KiCad** — Tools → Update PCB from Schematic (F8); accept J2–J5 updates.
- [ ] **6. Re-place connectors** — Confirm positions (58, 10/22/34/46) rot=90°; verify key tab
      faces board edge; verify no courtyard overlaps.
- [ ] **7. Run DRC** — `kicad-cli pcb drc ...`; confirm 0 errors; commit `drc_output.json`.
- [ ] **8. 3D view check** — Confirm shroud body visible, tab orientation correct.
- [ ] **9. MAJOR constitution amendment** — Update `docs/constitution.md` §2.2 J2–J5 BOM entry
      from `47053-1000` to `22-23-2041` (Molex KK-254 keyed header); document amendment version.
- [ ] **10. Commit all changes** — `components.py`, `.kicad_sch`, `.kicad_pcb`,
      `erc_output.json`, `drc_output.json`, `docs/constitution.md`, `docs/features/keyed-fan-headers/`.
- [ ] **11. Open PR** — Target `main`; reference issue #100 in PR description.
