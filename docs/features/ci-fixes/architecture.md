# Feature Architecture: CI Fixes (Issue #33)

<!-- Validated by: architect agent | Date: 2026-06-06 | Constitution version: 1.0.1 -->

## Validation Result

> **APPROVED WITH CHANGES**
>
> The plan is architecturally sound in intent and direction, but contains **two blocking
> issues** that must be resolved before implementation begins, plus **one significant
> concern** requiring explicit acknowledgment in the PR. Three constitution amendments
> are also proposed to close CI-related gaps identified during this review.

---

## Scope Confirmation

This feature modifies only `.github/workflows/*.yml` files and `docs/features/ci-fixes/`.
No `.kicad_sch`, `.kicad_pcb`, `hardware/generate_project.py`, or firmware source files
are changed. Expert consultations with `kicad.expert`, `esp32.expert`, and `poe.expert`
are therefore not required for this feature's implementation changes.

The architecture review is confined to:
1. Whether the proposed CI strategy correctly enforces constitution principles.
2. Whether any CI-specific choices conflict with or are absent from the constitution.

---

## Validation by Section

### 1. KiCad Docker Approach (P1 fix) — `kicad/kicad:10.0.2`

#### 1a. Version mismatch — BLOCKING ❌

**Constitution principle:** P-KI-01 — "The project uses **KiCad 10.0.3** exclusively."

**Finding:** The plan proposes `kicad/kicad:10.0.2` for both `hardware-check.yml` and
`release.yml`. This is KiCad **10.0.2**, not 10.0.3. The plan's compliance table
attempts to paper over this by stating the image "matches the project's format versions
(20260101 / 20260206)," but format version compatibility is not the same as KiCad version
compliance. P-KI-01 is unambiguous: the tool version is locked at 10.0.3.

**Why this matters beyond format codes:**
- `kicad-cli` behaviour (ERC rule sets, DRC constraint evaluation, footprint resolution)
  may differ between 10.0.2 and 10.0.3. A green CI gate on 10.0.2 is not evidence that
  the schematic/PCB is clean under 10.0.3 (the developer's actual tool).
- Files written by the 10.0.3 developer environment may contain features or internal
  representations that 10.0.2's CLI handles differently in headless mode.

**Resolution required (choose one):**

| Option | Action |
|---|---|
| **A (preferred)** | Confirm whether `kicad/kicad:10.0.3` exists on Docker Hub. If it does, use it. Check `docker pull kicad/kicad:10.0.3` or the Docker Hub tags page. |
| **B (if 10.0.3 is unavailable)** | Propose a MINOR constitution amendment to P-KI-01 that explicitly carves out CI containers: "CI jobs must use the latest available `kicad/kicad:10.0.x` Docker image. If a 10.0.3 image is unavailable, the closest preceding patch is acceptable for read-only CI operations (ERC/DRC does not write back to files)." Rationale must be recorded in Amendment History. |
| **C (fallback)** | Use the floating `kicad/kicad:10.0` tag and document that it tracks the latest 10.0.x release. Less reproducible than a pinned tag but avoids the 10.0.2-specific mismatch. |

**This issue must be resolved before implementation begins.**

---

#### 1b. Docker-based CI approach — APPROVED ✅

The Docker container approach is consistent with the project's philosophy of reproducible,
self-contained builds (implied by §2 "All entries are locked" and P-KI-01's rationale
"Established project toolchain"). Docker containers are the industry-standard solution
for pinned-tool CI when a package registry (PPA) is unavailable or unreliable. The
approach eliminates the PPA failure mode entirely and is architecturally preferable to
any apt-based fallback.

---

#### 1c. ERC/DRC in CI — APPROVED WITH CONCERN ⚠️

P-TEST-01 requires zero ERC errors. P-TEST-03 requires zero DRC errors.

The plan correctly:
- Removes the `|| true` suppression from the generator step.
- Adds an explicit ERC error-count check (hard fail on ≥ 1 error).
- Retains a `missing_footprint` hard failure for DRC.
- Fixes artifact uploads with `if: always()`.

**Concern — DRC threshold of 36 violations (see §3 below):** The plan retains the DRC
check `if [ "$VIOLATIONS" -gt 36 ]; then exit 1; fi`, allowing up to 36 DRC violations
before failing. P-TEST-03 requires **zero** DRC errors. This threshold contradicts the
constitution and requires explicit acknowledgment. See §3 for full analysis.

---

### 2. New `release.yml` Structure

#### 2a. Trigger strategy (tag + `workflow_dispatch`) — APPROVED ✅

Tag-based triggering on `v[0-9]+.[0-9]+.[0-9]+` with `workflow_dispatch` is the
conventional and architecturally correct approach for release automation. No constitution
principle constrains trigger strategy; this is implementation detail.

---

#### 2b. Running `generate_project.py` before Gerber export — APPROVED ✅

P-KI-04 mandates that `hardware/generate_project.py` is the schematic source of truth.
Running the generator before any KiCad CLI invocation correctly ensures the schematic
artefact is in a known-good state at release time. This is consistent with the
`hardware-check.yml` pattern and is the correct approach.

---

#### 2c. Gerber export — `release.yml` vs. P-KI-06 — APPROVED (no conflict) ✅

P-KI-06 states: "Gerber outputs live in `hardware/gerbers/` and are committed to the
repository. They must be regenerated whenever the PCB layout changes."

**Current state:** `hardware/gerbers/` contains only `.gitkeep` — no Gerbers have been
committed yet.

**Conflict analysis:** There is no conflict. The release workflow exports Gerbers into
`hardware/gerbers/` within the CI runner's workspace and packages them into the release
ZIP. It does not commit them back to the repository — they are ephemeral CI artefacts.

The two coexist cleanly:
- **Committed Gerbers (P-KI-06):** Developer-committed Gerbers serve as the repo-level
  reference; they must be kept in sync with PCB changes and reviewed in PRs.
- **Release ZIP Gerbers:** Generated fresh from the tagged commit at release time,
  ensuring the published fabrication package exactly matches the tagged state.

No amendment to P-KI-06 is required. However, see §4 for a proposed new CI principle
that formalises this workflow.

---

#### 2d. DRC before Gerber export — BLOCKING ❌

**Constitution principle:** P-TEST-04 — "The DRC report must be run and reviewed
immediately before invoking Gerber export. If DRC reports any error, Gerber export is
blocked."

**Finding:** The proposed `release.yml` YAML in plan §2 Phase 2 does **not include a
DRC step** before the `Export Gerbers` step. The plan acknowledges this gap in its own
Risk R2 section and in the implementation checklist (`Add DRC step before Gerber export`)
— but the concrete YAML omits the step.

This is a constitution violation. Releasing a fabrication package without a DRC gate
is exactly the scenario P-TEST-04 is designed to prevent: a designer tags a release
from a branch that passed the PR gate days ago, but a subsequent commit introduced a DRC
violation that was never caught.

**Resolution required:** The `release.yml` implementation MUST include a DRC step
immediately before the `Export Gerbers` step, structured as follows:

```yaml
      - name: Run DRC (gate before Gerber export)
        run: |
          kicad-cli pcb drc \
            hardware/kicad/PoE-FanController.kicad_pcb \
            --output hardware/kicad/drc_result.rpt \
            --schematic-parity
          echo "=== DRC Report ===" && cat hardware/kicad/drc_result.rpt
          VIOLATIONS=$(grep -c '^\[' hardware/kicad/drc_result.rpt || true)
          if [ "$VIOLATIONS" -gt 0 ]; then
            echo "❌ RELEASE BLOCKED: $VIOLATIONS DRC violation(s) detected"
            exit 1
          fi
          echo "✅ DRC clean — proceeding to Gerber export"
```

Note that the threshold in the release workflow must be **zero** (consistent with
P-TEST-03 and P-TEST-04), even if `hardware-check.yml` temporarily uses a non-zero
threshold. The release gate must be the strictest gate. See §3 for the threshold issue.

**This issue must be resolved before implementation begins.**

---

#### 2e. `softprops/action-gh-release@v2` vs. `gh` CLI — APPROVED ✅ (with preference)

The plan correctly identifies R4 (softprops Node.js 20 runtime risk) and recommends the
`gh release create` CLI alternative. Architecturally, the `gh` CLI approach is preferred:

- No JavaScript action dependency → no Node.js runtime version risk.
- Pre-installed on all GitHub-hosted Ubuntu runners.
- The plan's CLI alternative YAML is complete and correct.

The implementation should use the `gh release create` CLI form, not `softprops/action-gh-release@v2`,
to avoid the June 16 deadline risk.

---

### 3. DRC Violation Threshold — SIGNIFICANT CONCERN ⚠️

**Constitution principle:** P-TEST-03 — "Zero DRC errors required."

**Finding:** Both the existing `hardware-check.yml` and the plan's proposed replacement
retain the check `if [ "$VIOLATIONS" -gt 36 ]`, meaning up to 36 DRC violations are
silently accepted. This is a significant deviation from P-TEST-03, which is unambiguous.

The plan provides no explanation for the 36-violation baseline. Possible explanations:
- The PCB currently has known DRC issues (unconnected nets, clearance violations) that
  have not yet been resolved.
- The `grep -c '^\['` pattern is counting informational or advisory DRC entries (not
  just hard errors) that the KiCad DRC report format includes for certain rule classes.
- The threshold was copied from a prior state of `hardware-check.yml` without
  re-evaluation.

**This concern is NOT a blocking issue for this feature** (CI fixes), because the PCB's
DRC state is pre-existing and outside this feature's scope. However, the following is
required:

1. **The `release.yml` DRC gate must use zero tolerance** (threshold 0), not 36.
   The release path is the highest-criticality gate in the pipeline.

2. **The plan must document the 36-violation baseline explicitly.** The plan should
   state: "The current PCB has N known DRC violations of category X. These are tracked
   as [issue/label]. The CI gate uses threshold 36 as a temporary baseline until
   [issue] is resolved." This acknowledgment is necessary for the PR to merge.

3. **A follow-up issue should be opened** to drive the DRC violation count to zero,
   at which point the threshold in `hardware-check.yml` must be lowered to 0 and
   a note added to P-TEST-03 confirming CI enforcement.

---

### 4. `copilot-setup-steps.yml` Replacement — APPROVED ✅

**Constitution principle:** P-UI-01 — "No frameworks, no bundlers, no npm."

The plan's interpretation of P-UI-01 for the CI setup step is correct. The existing
workflow's Node.js section (`npm ci`, `npx playwright install`, `npx run build`) is
entirely inconsistent with this project's technology stack. The project has no
`package.json`, no `package-lock.json`, and no JavaScript build pipeline — `npm ci`
would fail on the first run.

The replacement (`python -m py_compile hardware/generate_project.py`) is appropriate:
- It validates that the generator script is syntactically valid Python.
- It confirms Python is available in the Copilot agent's environment.
- It is fast (< 1 second) and has no network dependency.

**One architectural gap:** The copilot-setup-steps workflow does not set up KiCad.
For a Copilot agent working on hardware tasks (schematic changes, ERC fixes), not having
`kicad-cli` available may limit its ability to validate changes. However, this is a
feature gap, not an architectural violation — the Copilot setup steps file is
specifically a bootstrap hint for the agent, not a full CI gate. Extending it with a
KiCad container reference is a future enhancement, not a requirement for this PR.

The `timeout-minutes: 15` addition (fixing P4b) is correct and necessary.

---

### 5. Node.js 24 Migration (P3) — APPROVED ✅

No architecture principles govern action runtime versions. The migration from
`codeql@v3` to `codeql@v4` is a maintenance action with a hard deadline (June 16, 2026).
The Phase 0 stopgap (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`) is a valid bridge measure.
The plan correctly identifies all affected action pins.

Architectural note: The preference for explicit SHA pins for reproducibility (mentioned
in the plan) is architecturally desirable but not constitutionally mandated. This is
left to implementer discretion.

---

## Constitution Gap Analysis

The following CI-related principles are absent from `docs/constitution.md`. These are
flagged for the **orchestrator to action as constitution amendments** — the architect
agent does not write amendments unilaterally per P-DEV-04.

### Gap 1 — No CI enforcement mandate for ERC/DRC on hardware PRs

**Current state:** P-TEST-01 through P-TEST-04 describe ERC/DRC quality requirements,
and P-DEV-02 requires updated ERC/DRC results in PRs. However, no principle explicitly
mandates that CI must *automatically enforce* these gates.

**Proposed amendment (MINOR, new principle P-CI-01):**

> **P-CI-01 — ERC/DRC gates must be enforced in CI.**
> Any pull request that modifies files under `hardware/` must pass a CI job that:
> (a) runs `hardware/generate_project.py` without error suppression,
> (b) runs `kicad-cli sch erc` and fails hard on ≥ 1 ERC error, and
> (c) runs `kicad-cli pcb drc` and fails hard on ≥ 1 DRC violation.
> A CI job using a KiCad Docker container is the approved mechanism; no PPA-based
> installation is permitted. Silently skipping ERC/DRC (e.g., via `|| true` fallbacks
> or conditional `if: kicad_available` guards) is prohibited.

---

### Gap 2 — No principle governing the release workflow and Gerber export

**Current state:** P-KI-06 covers committed Gerbers. P-TEST-04 covers DRC before
Gerber export. Neither addresses the CI release workflow or its structure.

**Proposed amendment (MINOR, new principle P-CI-02):**

> **P-CI-02 — Release workflow must DRC-gate Gerber export.**
> The CI release workflow (triggered on `v*.*.*` tags) must:
> (a) regenerate the schematic via `hardware/generate_project.py`,
> (b) run `kicad-cli pcb drc` and fail with exit code 1 on any violation (zero-tolerance),
> (c) only proceed to Gerber/drill export after a clean DRC,
> (d) bundle Gerbers, drill files, BOM CSV, and schematic PDF into a single versioned ZIP,
> (e) publish the ZIP as a GitHub Release asset.
> The release runner must use the same KiCad Docker image as the `hardware-check.yml` gate.

---

### Gap 3 — No principle governing KiCad CI tooling version

**Current state:** P-KI-01 locks the KiCad version to 10.0.3 for development. It is
silent on CI containers, where the exact patch version may not match an available Docker image.

**Proposed amendment (PATCH, clarification to P-KI-01):**

> **P-KI-01 — KiCad version lock (clarified).**
> The project uses **KiCad 10.0.3** for all development work. CI jobs must use the
> `kicad/kicad` official Docker image pinned to a 10.0.x patch tag. The pinned tag must
> match the project's development version (currently `10.0.3`). If the exact patch image
> is unavailable on Docker Hub, the closest available patch is acceptable for read-only
> CI operations (ERC/DRC does not write back to `.kicad_sch` or `.kicad_pcb` files) —
> this exception requires a note in the workflow YAML comment and must be resolved when
> the correct image becomes available.

---

## Summary of Findings

### Blocking Issues (must resolve before implementation)

| # | Issue | Location in plan | Resolution |
|---|---|---|---|
| **B1** | `kicad/kicad:10.0.2` violates P-KI-01 (KiCad 10.0.3 required) | §2 Phase 3, Phase 2; §3 table P-KI-01 row | Check if `kicad/kicad:10.0.3` exists; use it, or document constitutional basis for 10.0.2 via PATCH amendment (see Gap 3 proposal). |
| **B2** | `release.yml` proposed YAML omits DRC step before Gerber export, violating P-TEST-04 | §2 Phase 2 YAML; §3 table P-TEST-04 row; Risk R2 | Add zero-tolerance DRC step immediately before `Export Gerbers` step in `release.yml`. |

### Significant Concerns (must be acknowledged in PR)

| # | Concern | Resolution |
|---|---|---|
| **C1** | DRC threshold of 36 violations in `hardware-check.yml` contradicts P-TEST-03 | Document the baseline violation count and categories in the PR description; open a follow-up issue to drive count to zero; use zero threshold in `release.yml`. |

### Approved Without Change

| Area | Verdict |
|---|---|
| Docker container approach (replacing PPA) | ✅ Architecturally correct |
| `release.yml` trigger strategy (tag + dispatch) | ✅ Correct |
| Running `generate_project.py` before KiCad CLI | ✅ Consistent with P-KI-04 |
| P-KI-06 vs. release Gerber export — no conflict | ✅ Coexistence confirmed |
| `copilot-setup-steps.yml` — Node.js removal per P-UI-01 | ✅ Correct interpretation |
| `copilot-setup-steps.yml` — Python smoke-test replacement | ✅ Appropriate |
| `timeout-minutes` additions | ✅ Correct hardening |
| `if: always()` on artifact uploads | ✅ Correct hardening |
| Node.js 24 migration (`codeql@v3` → `@v4`, stopgap variable) | ✅ Correct |
| `gh release create` CLI preference over `softprops` | ✅ Preferred |
| ERC zero-error hard-fail check (new explicit step) | ✅ Satisfies P-TEST-01 |
| `|| true` removal from generator step | ✅ Satisfies P-KI-04 / P-TEST gate integrity |

---

## Proposed Constitution Amendments (for orchestrator to action)

The following amendments are flagged for the orchestrator. They do not block this
feature's implementation but should be applied concurrently or immediately after.

| Amendment | Type | Principle affected | Priority |
|---|---|---|---|
| Gap 3: Clarify P-KI-01 for CI Docker container patch versioning | PATCH | P-KI-01 | **HIGH** — required to unblock B1 |
| Gap 1: Add P-CI-01 (ERC/DRC CI gate mandate) | MINOR | (new) | MEDIUM — formalises what this PR implements |
| Gap 2: Add P-CI-02 (release workflow DRC-gate mandate) | MINOR | (new) | MEDIUM — formalises what this PR implements |

---

## Pre-Implementation Checklist for Implementer

Before writing a single line of workflow YAML, confirm:

- [ ] **B1:** Check Docker Hub for `kicad/kicad:10.0.3`. If it exists, use it in all
      workflow files. If not, await the PATCH amendment to P-KI-01 from the orchestrator.
- [ ] **B2:** Add DRC step (zero-tolerance) to `release.yml` YAML before `Export Gerbers`.
- [ ] **C1:** Confirm the number and categories of current DRC violations in `hardware-check.yml`
      baseline (the "36" figure); document them in the PR description and open a follow-up issue.
- [ ] All 12 acceptance criteria from plan §5 remain valid and should be verified after implementation.
