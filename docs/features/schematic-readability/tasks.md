# Tasks: SCH — Improve Schematic Readability to Match DMX_NODE Reference Style

## Summary

- **Total tasks:** 5
- **Layers covered:** Hardware: ERC, Hardware: Schematic (generator), Documentation, Issue update
- **GitHub parent issue:** #25
- **Branch:** `feature/25-schematic-readability`
- **Core implementation status:** Complete (merged via PR #24 into `main`)
- **Remaining scope:** Two gaps identified post-merge; all other acceptance criteria already satisfied on `main`

### What is already done (no tasks needed)
| Criterion | Status |
|---|---|
| `global_label()` method with correct KiCad 10 format | ✅ merged in PR #24 |
| Global labels on all inter-block signals (FAN1-4 PWM/TACH, ESP_EN, BOOT, ESP_TX, ESP_RX, USB_DP, USB_DN) | ✅ merged in PR #24 |
| `GND_PRI` / `GND` isolated ground domains | ✅ merged in PR #24 |
| Blue bold 2.54 mm section headers on all 5 blocks | ✅ merged in PR #24 |
| `power()` default pin_type = `power_out` | ✅ merged in PR #24 |
| Ag9905M VPORT pins changed to `passive` | ✅ merged in PR #24 |
| ERC: 0 errors, 86 warnings (on current `.kicad_sch`) | ✅ verified post-PR #24 |
| Constitution §7A added (P-SCH-01 through P-SCH-05) | ✅ merged in PR #24 |
| `kicad.expert.agent.md` updated | ✅ merged in PR #24 |

---

## Dependency Graph

```
T001 (ERC: regenerate erc_output.json)
  └── T002 (SCH: fix NTC_ADC label inconsistency in generator)
        └── T003 (ERC: re-run ERC after NTC_ADC fix)
              └── T004 (Docs: mark gaps resolved in plan.md)
                    └── T005 (Issue: final status update on #25)
```

All tasks are strictly sequential. T001 has no dependencies and can start immediately.

---

## Task List

### T001: Regenerate erc_output.json to reflect post-PR-#24 ERC state

- **Layer:** Hardware: ERC
- **Description:** The committed `hardware/kicad/erc_output.json` is a plain-text ERC report
  from before PR #24 landed. It records the pre-improvement state and is not valid JSON.
  Per P-TEST-02 and P-DEV-02, this file must be a current JSON-format ERC report showing 0 errors
  and must be committed before this PR can merge.

  Steps:
  1. Run `python hardware/generate_project.py` to produce the latest `.kicad_sch`
  2. Run `kicad-cli sch erc hardware/kicad/PoE-FanController.kicad_sch --output hardware/kicad/erc_output.json --format json`
  3. Confirm `error_count` field is `0` in the output file
  4. Commit `hardware/kicad/erc_output.json` with message `hw: regenerate erc_output.json — 0 errors post-PR-#24 (#25)`

  > **Note:** Do not run T002 changes before this commit; T001 must capture the current
  > generator state as a baseline before the NTC_ADC fix is applied.

- **Depends on:** none
- **Acceptance:** `hardware/kicad/erc_output.json` is committed to `feature/25-schematic-readability`,
  is valid JSON, and its `error_count` (or equivalent top-level field) equals `0`.
- **GitHub issue:** #27

---

### T002: Fix NTC_ADC label inconsistency in generate_project.py

- **Layer:** Hardware: Schematic (generator)
- **Description:** Three edits to `hardware/generate_project.py` are required to make the `NTC_ADC`
  net use `global_label` consistently on all three endpoints, and to correct the semantically wrong
  `shape="output"` on the ESP32 IO32 pin (the ESP32 reads the ADC voltage — it does not drive it):

  | Location | Current | Change to |
  |---|---|---|
  | Line 699 (ESP32 IO32) | `global_label("NTC_ADC", ..., shape="output")` | `shape="input"` |
  | Line 776 (R4 pin 2) | `s.label("NTC_ADC", *p1["2"])` | `s.global_label("NTC_ADC", *p1["2"], shape="output", angle=180)` |
  | Line 783 (NTC1 pin 1) | `s.label("NTC_ADC", *p1["1"])` | `s.global_label("NTC_ADC", *p1["1"], shape="output")` |

  After edits, re-run `python hardware/generate_project.py` to regenerate `.kicad_sch`.
  Commit both `hardware/generate_project.py` and `hardware/kicad/PoE-FanController.kicad_sch`
  with message `hw: fix NTC_ADC global_label shape and consistency on R4/NTC1 (#25)`.

  Rationale: The NTC thermistor voltage divider drives the NTC_ADC net; the ESP32 IO32 pin
  reads it. `shape="input"` on IO32 and `shape="output"` on R4/NTC1 correctly models the
  signal direction and eliminates any KiCad shape-mismatch warning on this net.

- **Depends on:** T001
- **Acceptance:** `Select-String hardware/kicad/PoE-FanController.kicad_sch -Pattern "NTC_ADC"`
  returns only `global_label` occurrences (zero plain `label` hits for `NTC_ADC`); the IO32 instance
  has `(shape input)` and the R4/NTC1 instances have `(shape output)`.
- **GitHub issue:** #28

---

### T003: Re-run ERC after NTC_ADC fix; commit refreshed erc_output.json

- **Layer:** Hardware: ERC
- **Description:** The `.kicad_sch` was regenerated in T002 (NTC_ADC endpoints changed from plain
  `label` to `global_label`). Per P-TEST-02, the ERC report must be refreshed after every schematic
  change and the result committed. This task verifies the fix introduces no new ERC errors.

  Steps:
  1. Confirm `python hardware/generate_project.py` exits with code 0 (no exceptions)
  2. Run `kicad-cli sch erc hardware/kicad/PoE-FanController.kicad_sch --output hardware/kicad/erc_output.json --format json`
  3. Confirm `error_count` is still `0`
  4. Commit the refreshed `hardware/kicad/erc_output.json` with message
     `hw: refresh erc_output.json after NTC_ADC global_label fix (#25)`

- **Depends on:** T002
- **Acceptance:** `erc_output.json` in the repository post-dates the T002 commit; it is valid JSON;
  `error_count` equals `0`; the file timestamp is newer than the T002 `.kicad_sch` commit.
- **GitHub issue:** #29

---

### T004: Mark resolved gaps in plan.md

- **Layer:** Documentation
- **Description:** Update `docs/features/schematic-readability/plan.md` §5 to reflect that both
  remaining gaps have been closed:

  - §5.1 (NTC_ADC inconsistency): Replace ⚠️ status with ✅ and note "Resolved in T002 —
    all three NTC_ADC endpoints now use `global_label`; IO32 shape corrected to `input`."
  - §5.2 (stale erc_output.json): Replace ⚠️ status with ✅ and note "Resolved in T001 and T003 —
    `erc_output.json` regenerated as valid JSON with 0 errors."

  Commit `docs/features/schematic-readability/plan.md` with message
  `docs: mark NTC_ADC and erc_output.json gaps resolved in schematic-readability plan (#25)`.

- **Depends on:** T003
- **Acceptance:** `plan.md` §5.1 and §5.2 both contain a ✅ "Resolved" line; no ⚠️ markers
  remain in §5; the commit message references issue #25.
- **GitHub issue:** #30

---

### T005: Post final status comment on issue #25 and link closing PR

- **Layer:** Issue update
- **Description:** After all tasks are complete and the feature branch is ready for PR, post a
  closing comment on GitHub issue #25 that confirms every acceptance criterion from `plan.md` §4
  is satisfied:

  ```
  ✅ global_label count ≥ 14 in generated .kicad_sch
  ✅ GND_PRI appears in schematic (placed once on U1 pin 6; no bridge to GND)
  ✅ All 5 section headers: color 0 0 255, bold yes, size 2.54 2.54
  ✅ ERC: 0 errors (erc_output.json current and committed)
  ✅ NTC_ADC uses global_label on all three endpoints (IO32 shape=input; R4/NTC1 shape=output)
  ✅ No docs/reference-samples/DMX_NODE in the git tree (excluded via .gitignore)
  ```

  Open a pull request from `feature/25-schematic-readability` → `main` and reference issue #25
  in the PR description so that merge closes the issue automatically.

- **Depends on:** T004
- **Acceptance:** Issue #25 has a comment listing all six acceptance criteria with ✅ status;
  a PR from `feature/25-schematic-readability` into `main` is open and references "Closes #25".
- **GitHub issue:** #31
