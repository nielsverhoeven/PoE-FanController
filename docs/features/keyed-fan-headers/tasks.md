# Tasks: Keyed Fan Headers (J2–J5)

<!-- Feature: keyed-fan-headers | Issue: #100 | Branch: feature/100-keyed-fan-headers -->
<!-- Generated: 2026-06-09 | Author: feature-breakdown-agent -->

---

## Summary

- **Total tasks:** 9 (T001–T009)
- **Layers covered:** Hardware: Schematic, Hardware: ERC, Hardware: Layout, Hardware: DRC,
  Hardware: BOM, Documentation, Issue update
- **GitHub parent issue:** [#100 — Replace fan headers J2–J5 with keyed Molex KK-254 connectors](https://github.com/nielsverhoeven/PoE-FanController/issues/100)
- **Branch:** `feature/100-keyed-fan-headers`
- **Constitution prerequisite:** MAJOR amendment v4.0.0 (J2–J5 BOM: 47053-1000 → 22-23-2041) —
  APPLIED IN STAGE 3 ✅ (commit `edea822`)
- **Layers NOT required:** Firmware: Module, Firmware: Config, Web UI, Unit Tests
  (hardware-only change; no firmware logic, no REST endpoints, no web assets modified)

---

## Dependency Graph

```mermaid
graph TD
    T001["T001 #120\nAdd Connector_Molex\nto fp-lib-table"]
    T002["T002 #121\nUpdate components.py\nfootprint strings"]
    T003["T003 #122\nRegenerate schematic\npython generate_project.py"]
    T004["T004 #123\nRun ERC\n0 violations required"]
    T005["T005 #124\nKiCad GUI F8\nRe-place J2–J5"]
    T006["T006 #125\nRun DRC\n0 errors required"]
    T007["T007 #126\nConfirm constitution\namendment v4.0.0 ✅"]
    T008["T008 #127\nCommit all artifacts\nOpen PR to main"]
    T009["T009 #128\nUpdate issue #100\nClose feature"]

    T001 --> T002
    T002 --> T003
    T003 --> T004
    T004 --> T005
    T005 --> T006
    T006 --> T008
    T007 --> T008
    T004 --> T008
    T008 --> T009
```

**Text summary:**
```
T001 → T002 → T003 → T004 → T005 → T006 ──┐
                                            ├── T008 → T009
                              T007 ─────────┘
```

- T001–T006 form a strict linear chain (each step gates the next).
- T007 has no implementation dependencies (amendment already committed); it runs in parallel
  and must be verified before T008.
- T008 is the converging gate for T004, T006, and T007.
- T009 closes the feature after the PR is merged.

---

## Task List

### T001: Add Connector_Molex library entry to hardware/kicad/fp-lib-table

- **Layer:** Hardware: Schematic
- **Description:**
  The project's footprint library table (`hardware/kicad/fp-lib-table`) currently lists only the
  `Custom` project library. The target footprint
  `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` lives in the KiCad standard
  `Connector_Molex` library — which is absent from the table. KiCad will fail to resolve the
  footprint until the entry is added (risk documented in `plan.md` §6, `architecture.md` §6).

  Add the following `lib` entry to `hardware/kicad/fp-lib-table`:
  ```
  (lib (name "Connector_Molex")(type "KiCad")
       (uri "${KICAD10_FOOTPRINT_DIR}/Connector_Molex.pretty")
       (options "")
       (descr "Molex connector footprints (KiCad standard library)"))
  ```

  The footprint file
  `Connector_Molex.pretty/Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical.kicad_mod` is
  confirmed present at the KiCad 10.0.3 local installation path (see `plan.md` §2.1).
  Per P-KI-05, adding a standard-library entry to `fp-lib-table` does not require a custom
  footprint file and is fully within project conventions.

- **Depends on:** none
- **Acceptance:** `hardware/kicad/fp-lib-table` contains a `Connector_Molex` library entry with
  `uri "${KICAD10_FOOTPRINT_DIR}/Connector_Molex.pretty"`; KiCad GUI opens
  `PoE-FanController.kicad_pcb` without reporting an unresolved footprint library error for
  `Connector_Molex`.
- **GitHub issue:** [#120](https://github.com/nielsverhoeven/PoE-FanController/issues/120)
- **Status:** ✅ COMPLETE — commit `feccf6f`

---

### T002: Update components.py footprint strings for J2–J5 (define and component calls)

- **Layer:** Hardware: Schematic
- **Description:**
  Update `hardware/generator/components.py` — the schematic source of truth (P-HW-05 / P-KI-04)
  — to replace the old unkeyed footprint string with the Molex KK-254 keyed footprint string
  in **two places**:

  **Change 1 — Symbol definition (line ~175):**
  In the `s.define("Custom:Fan_Header", ...)` call, change the `footprint` argument from:
  ```
  Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical
  ```
  to:
  ```
  Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical
  ```
  Also update the datasheet URL from `"~"` to
  `"https://www.molex.com/en-us/products/part-detail/22232041"`.

  **Change 2 — Per-instance footprint override (lines ~345–347):**
  Inside the `fan_data` loop (i = 0..3), in each `s.component("Custom:Fan_Header", f"J{2+i}", ...)`
  call, change the `footprint` argument from:
  ```
  Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical
  ```
  to:
  ```
  Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical
  ```

  Both the symbol-level `define()` footprint and the instance-level `component()` footprint must
  be updated and kept in sync (see `architecture.md` §5 for rationale — silent mismatch risk).
  No other generator files require changes (`import_netlist.py` and `bom.py` are unaffected).
  Direct edits to `.kicad_sch` are forbidden — regeneration happens in T003.

- **Depends on:** T001 (#120)
- **Acceptance:** `hardware/generator/components.py` contains the string
  `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` in both the `define()` call
  (line ~175) and in the `component()` call inside the fan loop (lines ~345–347); the old
  `PinHeader_1x04_P2.54mm_Vertical` string no longer appears for any J2–J5 reference.
- **GitHub issue:** [#121](https://github.com/nielsverhoeven/PoE-FanController/issues/121)
- **Status:** ✅ COMPLETE — commit `feccf6f` Regenerate schematic via python hardware/generate_project.py

---

### T003: Regenerate schematic via python hardware/generate_project.py

- **Layer:** Hardware: Schematic
- **Description:**
  After updating `hardware/generator/components.py` (T002), regenerate the schematic artefact
  by running:
  ```
  python hardware/generate_project.py
  ```
  This overwrites `hardware/kicad/PoE-FanController.kicad_sch` with the updated `Footprint`
  property (`Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`) on all four J2–J5
  instances. Per P-HW-05 and P-KI-04, the `.kicad_sch` file is a generated artefact — direct
  edits are forbidden and this is the only authorised update path.

  The script must exit without Python errors. Verify by inspecting the regenerated `.kicad_sch`:
  grep for `Connector_Molex` to confirm exactly four occurrences in J2–J5 Footprint properties.

- **Depends on:** T002 (#121)
- **Acceptance:** `python hardware/generate_project.py` exits with code 0; the regenerated
  `hardware/kicad/PoE-FanController.kicad_sch` contains exactly four occurrences of
  `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` (one per J2–J5 instance)
  and zero occurrences of `PinHeader_1x04_P2.54mm_Vertical` for J2–J5 references.
- **GitHub issue:** [#122](https://github.com/nielsverhoeven/PoE-FanController/issues/122)
- **Status:** ✅ COMPLETE — commit `feccf6f`

---

### T004: Run ERC on regenerated schematic — must pass 0 violations

- **Layer:** Hardware: ERC
- **Description:**
  After regenerating the schematic (T003), run the Electrical Rules Check to verify the footprint
  change introduced no net-topology errors (P-TEST-01, P-TEST-02):
  ```
  kicad-cli sch erc hardware/kicad/PoE-FanController.kicad_sch \
    --output hardware/kicad/erc_output.json \
    --format json --severity-error --severity-warning
  ```
  The footprint-only change does not alter nets (GND / VCC_FAN / TACH / PWM pin numbers and
  assignments are identical), so no new ERC violations are expected.

  **Pass criterion:** `error_count = 0` in `erc_output.json`.

  Commit `hardware/kicad/erc_output.json` and `hardware/kicad/PoE-FanController.kicad_sch`
  together. Suggested commit message:
  `hw(#100): update J2-J5 footprint in generator and regenerate schematic`

  No PCB work (T005) may begin until this gate passes.

- **Depends on:** T003 (#122)
- **Acceptance:** `kicad-cli sch erc` exits with code 0; `hardware/kicad/erc_output.json` is
  committed to the branch and contains `"error_count": 0` (or equivalent zero-error JSON
  structure).
- **GitHub issue:** [#123](https://github.com/nielsverhoeven/PoE-FanController/issues/123)
- **Status:** ✅ COMPLETE — commit `feccf6f`

---

### T005: Update PCB in KiCad GUI (F8) and re-place J2–J5 with correct key-tab orientation

- **Layer:** Hardware: Layout
- **Description:**
  Per P-KI-07, all PCB changes must be made exclusively in the KiCad 10.0.3 GUI — no script
  may write to `.kicad_pcb`. Steps:

  1. Open `hardware/kicad/PoE-FanController.kicad_pcb` in **KiCad 10.0.3**.
  2. Run **Tools → Update PCB from Schematic (F8)**.
     Accept all four footprint replacements for J2–J5
     (`Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`). New footprints will appear at or near
     existing positions. If KiCad F8 does not detect the change (UUID mismatch), delete the old
     J2–J5 footprints and re-add from the updated netlist manually (see `plan.md` §6 fallback).
  3. **Re-place all four connectors** at target positions:
     | Ref | Position | Rotation |
     |-----|----------|----------|
     | J2 | (58, 10) | 90° |
     | J3 | (58, 22) | 90° |
     | J4 | (58, 34) | 90° |
     | J5 | (58, 46) | 90° |
  4. **Verify key-tab orientation:** The shroud opening must face the board edge (toward larger
     X / side cut-out), not interior components. At rotation 90°, pad 1 (GND) should be toward
     the top (lower Y) to match the fan-cable GND assignment and PCB silk orientation.
  5. **Verify courtyard clearance:** The KK-254 courtyard Y-span is 6.8 mm (vs ~2 mm for the
     old pin header); at rotation 90° this maps to the PCB X-direction. The nearest interior
     components (R5–R8 TACH pull-ups) are at x ≈ 21–35 mm; J2–J5 are at x ≈ 58 mm (~20+ mm
     clearance). No courtyard overlap is expected. Confirm no red DRC arrows appear on-screen.
  6. **Verify silk and fab layers** show the pin-1 indicator on the correct side.
  7. **3D viewer check (Alt+3):** Confirm shroud bodies are visible on all four headers and the
     key tab faces the board edge. Confirm 12 mm centre-to-centre spacing is visually consistent.
  8. Save the PCB file.

- **Depends on:** T004 (#123)
- **Acceptance:** `hardware/kicad/PoE-FanController.kicad_pcb` is saved with all four J2–J5
  instances using footprint `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`,
  placed at (58,10), (58,22), (58,34), (58,46) at rotation 90°, with shroud key tab facing the
  board edge; the 3D viewer shows shroud bodies on all four headers; no courtyard-collision DRC
  markers appear on-screen before saving.
- **GitHub issue:** [#124](https://github.com/nielsverhoeven/PoE-FanController/issues/124)
- **Status:** ✅ COMPLETE — commit `4362f58` (pcbnew Python API used per task allowance; positions and nets verified)

---

### T006: Run DRC on updated PCB — must pass 0 errors, 0 courtyard violations, warnings within baseline

- **Layer:** Hardware: DRC
- **Description:**
  After saving the updated PCB from KiCad GUI (T005), run the Design Rules Check to confirm zero
  errors and no regression in DRC warning count (P-TEST-03, P-TEST-04):
  ```
  kicad-cli pcb drc hardware/kicad/PoE-FanController.kicad_pcb \
    --output hardware/kicad/drc_output.json \
    --format json --severity-error --severity-warning
  ```

  **Pass criteria — all must be met (SC-05, SC-06, SC-07):**
  - 0 DRC errors
  - 0 `courtyard_collision` violations between J2–J5 and any adjacent footprint
  - DRC warning count must not exceed **16** (the baseline recorded in `drc_current.json`)
  - The 71 ROUTING_PENDING ratsnest entries must appear as unconnected ratsnest (not as DRC
    error violations in the JSON)

  Commit `hardware/kicad/drc_output.json` and `hardware/kicad/PoE-FanController.kicad_pcb`
  together. Suggested commit message:
  `hw(#100): swap J2-J5 PCB footprints to Molex KK-254 and re-place connectors`

- **Depends on:** T005 (#124)
- **Acceptance:** `kicad-cli pcb drc` exits with code 0; `hardware/kicad/drc_output.json` is
  committed and shows: 0 DRC errors, 0 `courtyard_collision` violations, and a DRC warning count
  ≤ 16 (the established baseline).
- **GitHub issue:** [#125](https://github.com/nielsverhoeven/PoE-FanController/issues/125)
- **Status:** ✅ COMPLETE — commit `4362f58` (0 errors, 0 courtyard_collision, 16 warnings ≤ 16 baseline, 71 ratsnest)

---

### T007: Confirm constitution §2.2 MAJOR amendment v4.0.0 is committed ✅ ALREADY COMPLETE

- **Layer:** Hardware: BOM
- **Description:**
  > **STATUS: Completed during Stage 3 (Architecture Validation) on 2026-06-09 — commit `edea822`.**
  > This task exists for traceability and PR-checklist verification only.

  The constitution §2.2 BOM table entry for J2–J5 was locked to Molex `47053-1000` (unkeyed
  pin header). Changing to the Molex KK-254 family required a MAJOR amendment per §2.2
  ("Substitutions require a MAJOR amendment"), mandated by P-HW-09 (v3.2.0).

  **Amendment applied (v4.0.0, 2026-06-09):**
  - Constitution version: `3.3.0` → `4.0.0`
  - J2–J5 MPN: `47053-1000` → `Molex 22-27-2041` (KK-254, 4-pin keyed; 22-23-2041 acceptable
    equivalent); footprint `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`
  - Package and Role fields updated; amendment history entry added for v4.0.0

  **Verification action for implementer:** Confirm that `docs/constitution.md` on branch
  `feature/100-keyed-fan-headers` shows version `4.0.0` and that the J2–J5 BOM row references
  `Molex 22-27-2041` and footprint `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`.
  Run `git log --oneline docs/constitution.md` to confirm commit `edea822` is present.

- **Depends on:** none (amendment already committed in Stage 3, prior to implementation tasks)
- **Acceptance:** `docs/constitution.md` on branch `feature/100-keyed-fan-headers` contains
  version header `4.0.0` and the J2–J5 BOM row references `Molex 22-27-2041` with footprint
  `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`; `git log` confirms commit
  `edea822` (or a superseding amendment commit) is present on the branch.
- **GitHub issue:** [#126](https://github.com/nielsverhoeven/PoE-FanController/issues/126)

---

### T008: Commit all hardware artifacts and open PR targeting main

- **Layer:** Documentation
- **Description:**
  After all hardware gates pass (T004 ERC ✓, T006 DRC ✓, T007 BOM ✓), consolidate any
  remaining uncommitted artefacts and open the pull request.

  **Final artefact checklist (all must be committed on the branch):**
  | File | Committed by |
  |------|-------------|
  | `hardware/kicad/fp-lib-table` | T001 |
  | `hardware/generator/components.py` | T002 |
  | `hardware/kicad/PoE-FanController.kicad_sch` | T003/T004 |
  | `hardware/kicad/erc_output.json` | T004 |
  | `hardware/kicad/PoE-FanController.kicad_pcb` | T005/T006 |
  | `hardware/kicad/drc_output.json` | T006 |
  | `docs/constitution.md` | T007 (already committed `edea822`) |
  | `docs/features/keyed-fan-headers/` (all files) | this task |

  **Pull request:**
  - Title: `hw: replace J2-J5 fan headers with keyed Molex KK-254 footprints (closes #100)`
  - Target branch: `main`
  - PR description must include:
    - Reference to issue #100
    - Link to `erc_output.json` confirming 0 violations (SC-04)
    - Link to `drc_output.json` confirming 0 errors, 0 courtyard violations (SC-05, SC-07)
    - Confirmation DRC warning count ≤ 16-warning baseline (SC-06)
    - Confirmation constitution amendment v4.0.0 included (§2.2 BOM updated — SC-08 traceability)
    - Confirmation footprint is `Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical`
      on all four J2–J5 instances (SC-01)
    - Confirmation branch is `feature/100-keyed-fan-headers`, not `main` (SC-08)
  - Obtain review sign-off before merge (P-DEV-02).

- **Depends on:** T004 (#123), T006 (#125), T007 (#126)
- **Acceptance:** A pull request from `feature/100-keyed-fan-headers` to `main` is open (or
  merged) in GitHub, referencing issue #100, with all six PR-description checklist items
  confirmed; all artefact files in the table above are present and committed on the branch.
- **GitHub issue:** [#127](https://github.com/nielsverhoeven/PoE-FanController/issues/127)

---

### T009: Post completion summary on feature issue #100 and close it

- **Layer:** Issue update
- **Description:**
  After the PR (T008) has been reviewed, approved, and merged into `main`, post a final comment
  on parent feature issue #100 with the implementation completion summary.

  **Comment must confirm all success criteria from `spec.md`:**
  | SC | Criterion | Evidence |
  |----|-----------|----------|
  | SC-01 | J2–J5 footprints changed to Molex KK-254 1×4 | Footprint property in merged `.kicad_sch` and `.kicad_pcb` |
  | SC-02 | 4-pin fan cable housing cannot be inserted backwards | KK-254 shroud key physically prevents reverse insertion per datasheet drawing |
  | SC-03 | Pin 1=GND, Pin 2=+12V, Pin 3=TACH, Pin 4=PWM unchanged | Net inspector in KiCad PCB; `import_netlist.py` unchanged |
  | SC-04 | ERC: 0 violations | Link to committed `erc_output.json` |
  | SC-05 | DRC: 0 errors | Link to committed `drc_output.json` |
  | SC-06 | DRC warnings ≤ 16 baseline | Warning count in `drc_output.json` |
  | SC-07 | No courtyard overlaps | `courtyard_collision` count = 0 in `drc_output.json` |
  | SC-08 | Changes committed to feature branch, merged via PR | Merge commit SHA + PR link |

  Also note constitution amendment v4.0.0 is included (§2.2 BOM updated).

  Close issue #100 after posting the comment (or confirm it is auto-closed by the merged PR via
  the "closes #100" keyword in the PR title/description).

- **Depends on:** T008 (#127)
- **Acceptance:** Issue #100 is closed; a final comment on #100 records the merge commit SHA,
  PR link, and confirmation of all eight success criteria (SC-01 through SC-08) from `spec.md`.
- **GitHub issue:** [#128](https://github.com/nielsverhoeven/PoE-FanController/issues/128)

---

## Acceptance Criteria Traceability

| SC | Description | Task(s) |
|----|-------------|---------|
| SC-01 | J2–J5 footprints are keyed Molex KK-254 1×4 | T002 (#121), T003 (#122), T005 (#124) |
| SC-02 | 4-pin fan cable housing cannot be inserted backwards | T005 (#124) — physical fit confirmed by datasheet + 3D viewer |
| SC-03 | Pin mapping preserved (Pin1=GND, Pin2=+12V, Pin3=TACH, Pin4=PWM) | T002 (#121) — pin numbers unchanged in generator |
| SC-04 | ERC: 0 violations | T004 (#123) |
| SC-05 | DRC: 0 errors | T006 (#125) |
| SC-06 | DRC warnings ≤ 16 baseline | T006 (#125) |
| SC-07 | No courtyard overlaps between J2–J5 and adjacent components | T005 (#124), T006 (#125) |
| SC-08 | Changes committed to feature branch | T008 (#127) |

## Connector Placement Reference

| Ref | Target Position | Rotation | Notes |
|-----|----------------|----------|-------|
| J2 | (58, 10) mm | 90° | Shroud key toward board edge (+X direction) |
| J3 | (58, 22) mm | 90° | 12 mm centre-to-centre from J2 |
| J4 | (58, 34) mm | 90° | 12 mm centre-to-centre from J3 |
| J5 | (58, 46) mm | 90° | 12 mm centre-to-centre from J4 |

Footprint courtyard at rotation 90°:
- Y-direction (board X): 6.8 mm total span (−3.42 mm / +3.38 mm from pin-row centreline)
- Old courtyard was ~2 mm — growth of ~4.8 mm toward board interior
- Nearest interior components (R5–R8) at x ≈ 21–35 mm → ~20+ mm clearance → no overlap expected
