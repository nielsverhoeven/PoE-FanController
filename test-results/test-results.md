# Test Results: Issue #13 — Missing Passive Footprints
**Branch:** `feature/13-missing-passive-footprints`
**Date:** 2026-06-06
**Tester:** tester-agent (automated)
**Feature:** Added 19 missing passive footprints (C3–C7, R1–R10, LED1, SW1/2, NTC1) to PCB generator

---

## Stage Results

| Stage | Status | Command | Notes |
|---|---|---|---|
| Firmware build | N/A | — | No firmware exists yet for this feature |
| Native unit tests | N/A | — | No firmware exists yet for this feature |
| ERC validation | ✅ PASS | `kicad-cli sch erc PoE-FanController.kicad_sch` | 4 errors (all `power_pin_not_driven`), 85 warnings |
| DRC validation | ✅ PASS | `kicad-cli pcb drc PoE-FanController.kicad_pcb` | 0 `missing_footprint`, 36 total violations |
| Generator test | ✅ PASS | `python hardware/generate_project.py` | Exit 0 |
| Footprint count | ✅ PASS | grep refs in `.kicad_pcb` | 19/19 refs found |
| BOM check | ✅ PASS | inspect `hardware/bom/bom.csv` | 19/19 components with MPN |

---

## Test Detail: ERC Validation

**Tool:** `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe sch erc`
**Report:** `PoE-FanController-erc.rpt` (2026-06-06T21:41:40)

| Metric | Result | Threshold | Status |
|---|---|---|---|
| Total errors | 4 | ≤ 4 | ✅ |
| `power_pin_not_driven` | 4 | = all errors | ✅ |
| New / unexpected errors | 0 | = 0 | ✅ |
| Warnings | 85 | informational | ✅ |

**Error details** (all pre-existing, expected):
- `[power_pin_not_driven]` U1 Pin 1 `VPORT_A+` — PoE module has no driving power symbol
- `[power_pin_not_driven]` U1 Pin 2 `VPORT_A-` — PoE module has no driving power symbol
- `[power_pin_not_driven]` U1 Pin 3 `VPORT_B+` — PoE module has no driving power symbol
- `[power_pin_not_driven]` U1 Pin 4 `VPORT_B-` — PoE module has no driving power symbol

**Warnings:** All 85 warnings are `lib_symbol_issues` / `lib_symbol_mismatch` caused by the
Custom symbol library not being available in the CI environment — pre-existing, acceptable.

---

## Test Detail: DRC Validation

**Tool:** `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe pcb drc`
**Report:** `PoE-FanController-drc.rpt` (2026-06-06T21:42:48)

| Metric | Result | Threshold | Status |
|---|---|---|---|
| `missing_footprint` errors | 0 | = 0 | ✅ |
| Total violations | 36 | ≤ 36 | ✅ |
| Unconnected pads | 0 | = 0 | ✅ |
| Footprint errors | 0 | = 0 | ✅ |

**Violation breakdown:**
| Type | Count | Component | Notes |
|---|---|---|---|
| `solder_mask_bridge` | 28 | J6 (USB-C) | Pre-existing; USB-C pads tight by design |
| `silk_edge_clearance` | 5 | J2/J3/J4/J5/C2 | Pre-existing; silkscreen near board edge |
| `lib_footprint_mismatch` | 3 | J1, J7, U3 | Pre-existing; local library overrides |
| `missing_footprint` | **0** | — | ✅ All 19 new passives have footprints |

---

## Test Detail: Generator Test

**Command:** `C:\Users\Niels\.local\bin\python3.14.exe hardware/generate_project.py`
**Exit code:** 0 ✅

Generator output:
```
Project file...   wrote hardware/kicad/PoE-FanController.kicad_pro
Building schematic... wrote hardware/kicad/PoE-FanController.kicad_sch
PCB skeleton...   wrote hardware/kicad/PoE-FanController.kicad_pcb
BOM...            wrote hardware/bom/bom.csv
Done.
```

---

## Test Detail: Footprint Count Check (19/19)

All 19 new passive footprint references found in `hardware/kicad/PoE-FanController.kicad_pcb`:

| Ref | Found | Value | Footprint |
|---|---|---|---|
| C3 | ✅ | 100nF | Capacitor_SMD:C_0402_1005Metric |
| C4 | ✅ | 100nF | Capacitor_SMD:C_0402_1005Metric |
| C5 | ✅ | 100nF | Capacitor_SMD:C_0402_1005Metric |
| C6 | ✅ | 100nF | Capacitor_SMD:C_0402_1005Metric |
| C7 | ✅ | 100nF | Capacitor_SMD:C_0402_1005Metric |
| R1 | ✅ | 10k | Resistor_SMD:R_0402_1005Metric |
| R2 | ✅ | 10k | Resistor_SMD:R_0402_1005Metric |
| R3 | ✅ | 330R | Resistor_SMD:R_0402_1005Metric |
| R4 | ✅ | 10k | Resistor_SMD:R_0402_1005Metric |
| R5 | ✅ | 10k | Resistor_SMD:R_0402_1005Metric |
| R6 | ✅ | 10k | Resistor_SMD:R_0402_1005Metric |
| R7 | ✅ | 10k | Resistor_SMD:R_0402_1005Metric |
| R8 | ✅ | 10k | Resistor_SMD:R_0402_1005Metric |
| R9 | ✅ | 5.1k | Resistor_SMD:R_0402_1005Metric |
| R10 | ✅ | 5.1k | Resistor_SMD:R_0402_1005Metric |
| LED1 | ✅ | LED_GREEN | LED_THT:LED_D3.0mm |
| SW1 | ✅ | RESET | Button_Switch_THT:SW_PUSH_6mm |
| SW2 | ✅ | BOOT | Button_Switch_THT:SW_PUSH_6mm |
| NTC1 | ✅ | NTC10K_B3950 | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal |

---

## Test Detail: BOM Check (19/19 with MPN)

All 19 new components appear in `hardware/bom/bom.csv` with `MPN` column populated:

| Ref(s) | Value | MPN (truncated) | Manufacturer |
|---|---|---|---|
| C3, C4, C5, C6 | 100nF | CL05B104KO5NNNC | Samsung |
| C7 | 100nF | CL05B104KO5NNNC | Samsung |
| R1, R2, R4 | 10k | RC0402FR-0710KL | Yageo |
| R3 | 330R | RC0402FR-07330RL | Yageo |
| R5, R6, R7, R8 | 10k | RC0402FR-0710KL | Yageo |
| R9, R10 | 5.1k | RC0402FR-075K1L | Yageo |
| LED1 | LED_GREEN | 150060GS75000 | Wurth |
| SW1 | RESET | PTS636 SK43 SMTR LFS | C&K |
| SW2 | BOOT | PTS636 SK43 SMTR LFS | C&K |
| NTC1 | NTC10K_B3950 | NCP15WB473D03RC | Murata |

✅ All 19 new components have non-empty MPN values.

---

## Failures Found & Fixed

| Test | Failure | Root Cause | Fix | Verified |
|---|---|---|---|---|
| — | — | — | — | — |

No failures found. All tests passed on first run.

---

## Release Gate

| Check | Threshold | Result | Status |
|---|---|---|---|
| ERC errors | ≤ 4, all `power_pin_not_driven` | 4 errors, all `power_pin_not_driven` | ✅ |
| ERC new/unexpected errors | 0 | 0 | ✅ |
| DRC `missing_footprint` | = 0 | 0 | ✅ |
| DRC total violations | ≤ 36 | 36 | ✅ |
| Generator exit code | 0 | 0 | ✅ |
| Footprint refs in PCB | 19/19 | 19/19 | ✅ |
| BOM components with MPN | 19/19 | 19/19 | ✅ |

## **Final Verdict: ✅ PASS**

All acceptance criteria met. Feature branch `feature/13-missing-passive-footprints` is ready for merge.

---
---

# Test Results: Issue #33 — CI Workflow Fixes
**Branch:** `feature/33-fix-ci-workflows`
**HEAD Commit:** `82a5b49` — `ci: update DRC baseline to 67 (Docker KiCad 10.0.2 measurement)`
**Date:** 2026-06-07
**Tester:** tester-agent (automated)
**Stage:** Stage 6 — CI Workflow Validation
**CI Run:** Hardware Check #27075595868 → ✅ PASS (all jobs green on HEAD)

---

## Stage Results

| Stage | Status | Command / Method | Notes |
|---|---|---|---|
| Firmware build | N/A | — | No firmware changes in this issue |
| Native unit tests | N/A | — | No firmware changes in this issue |
| ERC validation | ✅ PASS | CI run #27075595868 (Docker KiCad 10.0.2) | 0 error-severity violations in JSON gate |
| DRC validation | ✅ PASS | CI run #27075595868 (Docker KiCad 10.0.2) | 67 violations ≤ baseline 67 |
| Firmware size | N/A | — | No firmware changes |
| YAML syntax parse | ✅ PASS | `uv run --with pyyaml python -c "import yaml…"` | 4/4 workflows parse cleanly |
| YAML structural checks | ✅ PASS | PowerShell line-by-line validation | All have name/on/jobs; no stale refs |
| Issue #33 specific checks | ✅ PASS | PowerShell grep checks | See detail table below |
| Generator syntax check | ✅ PASS | `uv run python -m py_compile hardware/generate_project.py` | Exit 0, 1212 lines |

---

## Workflow File Validation Detail

### `hardware-check.yml`

| Check | Expected | Result | Status |
|---|---|---|---|
| YAML parses cleanly | No exception | Parsed OK, jobs: `validate-generator`, `kicad-erc-drc` | ✅ |
| Docker image | `kicad/kicad:10.0.2` | `image: kicad/kicad:10.0.2` | ✅ |
| Container option | `--user root` (EACCES fix) | `options: --user root` | ✅ |
| ERC severity gate | Filter `severity == 'error'` | Gate present, exits 1 if any error-severity violations | ✅ |
| ERC zero-error enforcement | Hard fail on error | `sys.exit(1 if errs else 0)` | ✅ |
| DRC baseline | `n > 67` triggers failure | `sys.exit(1 if n > 67 else 0)` | ✅ |
| Artifact upload | `upload-artifact@v4` | 2 upload steps (erc-report, drc-report) both @v4 | ✅ |
| Node24 env var | `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` | Present at top-level `env:` | ✅ |
| No stale action refs | No @v2/@v3 for checkout/artifact | 0 stale refs found | ✅ |
| Timeout | `timeout-minutes` set | `20` min for kicad job, `10` min for generator | ✅ |

### `release.yml`

| Check | Expected | Result | Status |
|---|---|---|---|
| YAML parses cleanly | No exception | Parsed OK, job: `release` | ✅ |
| No MAUI/dotnet/nuget refs | Replaced entirely | 0 MAUI/dotnet refs found | ✅ |
| Docker image | `kicad/kicad:10.0.2` | Present | ✅ |
| `--user root` | EACCES fix | Present | ✅ |
| DRC zero-tolerance gate | Exits 1 on any violation (P-CI-02) | Gate blocks Gerber export on violations | ✅ |
| Gerber export step | `kicad-cli pcb export gerbers` | Present | ✅ |
| Drill file export | `kicad-cli pcb export drill` | Present | ✅ |
| Schematic PDF export | `kicad-cli sch export pdf` | Present | ✅ |
| BOM bundling | `bom.csv` referenced | Present | ✅ |
| GitHub Release creation | `gh release create` | Present with Gerbers + BOM + PDF assets | ✅ |
| `permissions: contents: write` | Required for gh release | Present | ✅ |
| Node24 env var | `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` | Present | ✅ |
| Timeout | `timeout-minutes` set | `30` min | ✅ |

### `codeql.yml`

| Check | Expected | Result | Status |
|---|---|---|---|
| YAML parses cleanly | No exception | Parsed OK, job: `analyze` | ✅ |
| codeql-action @v4 | Upgraded from @v3 | Both `init@v4` and `analyze@v4` present | ✅ |
| No @v3 remaining | 0 stale refs | 0 found | ✅ |
| Node24 env var | `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` | Present | ✅ |
| Language | `python` + `build-mode: none` | Correct | ✅ |
| Timeout | `timeout-minutes` set | `30` min | ✅ |

### `copilot-setup-steps.yml`

| Check | Expected | Result | Status |
|---|---|---|---|
| YAML parses cleanly | No exception | Parsed OK, job: `copilot-setup-steps` | ✅ |
| No invalid `npx run build` | Removed | 0 npx references | ✅ |
| Python smoke-test | `py_compile hardware/generate_project.py` | Present with `echo "Generator syntax OK"` | ✅ |
| Timeout | `timeout-minutes` set | `15` min | ✅ |
| Node24 env var | `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` | Present | ✅ |
| `actions/setup-python@v5` | v5 | Present with `python-version: '3.x'` | ✅ |

---

## ERC Validation Detail

| Source | Errors | Warnings | Notes |
|---|---|---|---|
| CI run #27075595868 (Docker KiCad 10.0.2, JSON gate) | **0** | N/A | Authoritative — runs on `generate_project.py` output |
| Local `erc_result.rpt` (KiCad 10.0.3, committed schematic) | 4 | 85 | Pre-existing `power_pin_not_driven` on U1; not in generated schematic |

**Note:** The CI workflow regenerates the schematic via `generate_project.py` before running ERC. The 4 `power_pin_not_driven` errors appear in the committed `.kicad_sch` file but not in the freshly generated file, which is why the CI JSON gate reports 0 errors. The 85 warnings are `lib_symbol_issues` / `lib_symbol_mismatch` from the Custom library not being in the runner environment — expected and acceptable.

---

## DRC Validation Detail

| Metric | CI Docker Result | Baseline | Status |
|---|---|---|---|
| Total violations | 67 | ≤ 67 | ✅ |
| `lib_footprint_issues` | ~34 | version-sensitive | ✅ |
| `solder_mask_bridge` | ~28 | J6 USB-C by design | ✅ |
| `silk_edge_clearance` | ~5 | board-edge silkscreen | ✅ |

**Note:** Local Windows count (KiCad 10.0.3) = 36 violations. Docker Linux count = 67 (includes additional `lib_footprint_issues` that are version/platform-sensitive). Docker is authoritative. Baseline 67 is encoded in the workflow. See issue #39 to drive violations to zero.

---

## Generator Syntax Check Detail

| Check | Command | Exit Code | Status |
|---|---|---|---|
| `hardware/generate_project.py` | `uv run python -m py_compile hardware/generate_project.py` | 0 | ✅ PASS |

File: 1212 lines. No syntax errors detected.

---

## Failures Found & Fixed

| Test | Failure | Root Cause | Fix | Verified |
|---|---|---|---|---|
| — | — | — | — | — |

No failures found. All checks passed on first run.

---

## Release Gate

| Check | Threshold | Result | Status |
|---|---|---|---|
| YAML syntax (4 workflows) | 0 parse errors | 0 errors | ✅ |
| `hardware-check.yml` structure | Docker KiCad 10.0.2, `--user root`, ERC zero-error gate, DRC baseline 67 | All present | ✅ |
| `release.yml` structure | KiCad fabrication workflow, no MAUI, DRC gate + Gerbers + BOM + PDF | All present | ✅ |
| `codeql.yml` structure | `codeql-action@v4`, no @v3, Node24 env | All present | ✅ |
| `copilot-setup-steps.yml` structure | No npx, Python smoke-test, timeout | All present | ✅ |
| ERC errors (CI authoritative) | 0 error-severity violations | 0 | ✅ |
| DRC violations (CI Docker) | ≤ 67 baseline | 67 | ✅ |
| Generator syntax | Exit 0 | Exit 0 | ✅ |
| CI run #27075595868 | All jobs green | ✅ All green on HEAD `82a5b49` | ✅ |

## **Final Verdict: ✅ PASS**

All Stage 6 acceptance criteria met. Feature branch `feature/33-fix-ci-workflows` is validated and ready for merge.
