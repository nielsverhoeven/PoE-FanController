# Feature: Split Generator into Package; Transition PCB to KiCad GUI

> Issue: [#62](https://github.com/nielsverhoeven/PoE-FanController/issues/62)
> Branch: `feature/62-split-generator-kicad-gui-pcb`

---

## Overview

`hardware/generate_project.py` is a 1,212-line monolithic script that simultaneously generates the
KiCad schematic (`.kicad_sch`), PCB layout skeleton (`.kicad_pcb`), and BOM (`bom.csv`). The PCB
generation function (`write_pcb()`) only places components — it cannot route traces — and overwrites
the file on every run, destroying any manual routing work. This feature (a) splits the monolith into
a structured `hardware/generator/` Python package with clear module boundaries, and (b) permanently
removes `write_pcb()`, promoting the committed `.kicad_pcb` to a KiCad GUI source of truth that no
script may ever overwrite.

---

## User Stories

- As a **hardware engineer**, I want schematic changes to live in focused Python modules so that the
  1,200-line monolith no longer needs to be navigated in full for every edit.
- As a **hardware engineer**, I want the PCB file to survive generator runs intact so that manual
  routing work is never silently destroyed.
- As a **CI maintainer**, I want the syntax check to cover every generator module so that a Python
  error in any module fails fast, not only when the entry point is imported.
- As a **reviewer**, I want `generate_project.py` to be a thin, obviously-correct entry point so
  that I can understand the full generation pipeline at a glance.

---

## Functional Requirements

1. **FR-01 — Package structure.** A `hardware/generator/` Python package must exist containing:
   `__init__.py`, `utils.py`, `schematic.py`, `components.py`, `pcb_utils.py`, and `bom.py`.
   Each module must contain only the code described in the architecture section; cross-module
   responsibility leakage is not permitted.

2. **FR-02 — Thin entry point.** `hardware/generate_project.py` must import from the
   `generator` package and delegate all work to it. The file must contain no business logic
   beyond invoking `generator` functions and writing output files.

3. **FR-03 — Schematic output unchanged.** Running `python3 generate_project.py` must produce a
   `.kicad_sch` file whose ERC result is zero errors — identical gate to the pre-refactor baseline.

4. **FR-04 — BOM output unchanged.** Running `python3 generate_project.py` must produce
   `hardware/bom/bom.csv` with content identical to the pre-refactor output.

5. **FR-05 — PCB file not written.** Running `python3 generate_project.py` must not create or
   modify `hardware/kicad/PoE-FanController.kicad_pcb`. The `write_pcb()` function must not exist
   anywhere under `hardware/generator/`.

6. **FR-06 — Package importable.** `from generator import build_schematic, write_bom` must succeed
   when executed from the `hardware/` directory with no import errors.

7. **FR-07 — Acyclic import graph.** The package dependency chain must follow:
   `components.py → pcb_utils.py → schematic.py → utils.py`. No circular imports.

8. **FR-08 — CI generator step scoped to schematic.** The `kicad-erc-drc` job step named
   "Run PCB generator" must be renamed to "Regenerate schematic" to reflect its new scope. A
   subsequent step must verify that `.kicad_pcb` was not modified by the generator.

9. **FR-09 — CI syntax check covers package.** The `validate-generator` job's
   `python -m py_compile` step must check every `hardware/generator/*.py` module individually,
   not only `hardware/generate_project.py`.

10. **FR-10 — Constitution amended.** Before the refactor lands on `main`, the constitution must
    be updated to: (a) scope P-HW-05 and P-KI-04 to `.kicad_sch` only, (b) update the §2.1
    "Schematic source of truth" row to reference the package entry point, (c) add a new policy
    (P-KI-07) naming `.kicad_pcb` as KiCad GUI territory, and (d) update the §7A preamble.

---

## Non-Functional Requirements

- **NFR-01 — Zero behaviour regression.** The refactor is a mechanical code reorganisation. No
  schematic logic, BOM data, or file-path contract may change.
- **NFR-02 — Python 3.10+ compatibility.** All modules must run under CPython 3.10 or later
  (the minimum version available in the `ubuntu-latest` CI runner via `actions/setup-python@v5`).
- **NFR-03 — PEP 8 compliance.** All new and moved code must satisfy PEP 8 style
  (as per P-DEV-06 in the constitution).
- **NFR-04 — No new dependencies.** The package may not introduce any third-party dependencies
  beyond what `generate_project.py` already imports (`json`, `os`, `itertools`, `csv`, `re`).
- **NFR-05 — CI runtime unchanged.** The refactor must not increase the `validate-generator`
  or `kicad-erc-drc` job wall-clock time by more than 10 seconds.

---

## Success Criteria

| ID | Criterion | Verification method |
|---|---|---|
| SC-01 | `hardware/generator/` exists with all six required modules | `ls hardware/generator/` |
| SC-02 | `generate_project.py` is ≤ 30 lines (thin wrapper) | `wc -l hardware/generate_project.py` |
| SC-03 | `from generator import build_schematic, write_bom` succeeds from `hardware/` | `python3 -c "from generator import build_schematic, write_bom"` in CI |
| SC-04 | ERC reports zero errors after running the refactored generator | CI `kicad-erc-drc` job passes |
| SC-05 | `git diff --exit-code hardware/kicad/PoE-FanController.kicad_pcb` exits 0 after generator run | CI guard step exits 0 |
| SC-06 | `grep -r "def write_pcb" hardware/generator/` returns empty | CI or code review |
| SC-07 | DRC violation count does not exceed 67 (Docker baseline) | CI `kicad-erc-drc` job passes |
| SC-08 | All `hardware/generator/*.py` modules pass `python -m py_compile` | CI `validate-generator` job |
| SC-09 | Constitution contains P-KI-07 and updated P-KI-04, P-HW-05, §2.1, §7A | Code review of `docs/constitution.md` |
| SC-10 | `bom/bom.csv` content is byte-for-byte identical to pre-refactor output | `diff` against saved baseline |

---

## Out of Scope

- Routing the PCB (must be done manually in KiCad GUI — no script or agent should auto-route).
- Changes to the schematic component set, netlist, or symbol definitions.
- Firmware, web UI, or any file outside `hardware/` and `.github/workflows/hardware-check.yml`.
- Gerber regeneration (governed by P-KI-06 — separate release workflow).
- Absorbing `gen_esp32p4_footprint.py` into the package (file does not exist in the current tree;
  if it appears in future it should be evaluated separately).

---

## Assumptions

- The KiCad footprint library path (`KICAD_FP_BASE`) is still passed via environment variable;
  the package inherits this from `utils.py` unchanged.
- The committed `hardware/kicad/PoE-FanController.kicad_pcb` is stable and passes DRC at the
  67-violation Docker baseline before this refactor begins.
- No other scripts or tools import from `hardware/generate_project.py` directly (it is not a
  library module); only the `__main__` interface is exercised externally.
- The CI `ubuntu-latest` runner will find the `generator` package via the `cd hardware` working
  directory set before `python3 generate_project.py` is invoked.

---

## Open Questions

_None. All ambiguities resolved in the issue and context provided by the calling agent._
