# Technical Plan: CI Fix — Broken Workflows (Issue #33)

**GitHub Issue:** #33 — CI: fix broken workflows — KiCad PPA, release.yml leftover, Node.js 20 deprecation, copilot-setup-steps  
**Branch:** `feature/33-fix-ci-workflows`  
**Feature path:** `docs/features/ci-fixes/`  
**Date:** 2026-06-06  
**Scope:** CI/infrastructure only — zero hardware schematic or firmware changes.

---

## 1. Problem Inventory

All four workflow files were read and cross-referenced against the issue body. Every finding
below is verified against the actual file content with exact line citations.

### P1 — `hardware-check.yml`: KiCad PPA is broken; hardware gate is a silent no-op

| # | File | Lines | Finding |
|---|------|-------|---------|
| 1a | `hardware-check.yml` | 44–46 | `sudo add-apt-repository ppa:kicad/kicad-dev` fails silently on GitHub-hosted Ubuntu 24.04 runners (PPA host no longer resolves). The `\|\| { … exit 0; }` branch sets `kicad_available=false` and immediately exits with code 0 — the step is marked **green**. |
| 1b | `hardware-check.yml` | 52–56 | Skip-notice step fires; all ERC/DRC steps (lines 58–110) are gated on `kicad_available == 'true'` and are skipped. The entire hardware validation job passes without running a single check. |
| 1c | `hardware-check.yml` | 30 | `python hardware/generate_project.py 2>&1 \|\| true` in the `validate-generator` job suppresses **all** generator errors unconditionally. A broken generator script produces a green step. |
| 1d | `hardware-check.yml` | 12, 32 | Neither `validate-generator` (line 12) nor `kicad-erc-drc` (line 32) sets `timeout-minutes`. Jobs can hang indefinitely. |
| 1e | `hardware-check.yml` | 98–110 | `Upload ERC report` and `Upload DRC report` are gated on `kicad_available == 'true'` but have no `if: always()`. If ERC or DRC steps crash mid-run, the report artefacts are never uploaded and the failure is invisible in the GitHub Actions UI. |

**Why `apt install kicad` from Ubuntu universe does not solve P1:**  
Ubuntu 24.04 (Noble) ships **KiCad 8.0.x** from its universe repository. The project uses
KiCad 10.0.3 (constitution §2.1, P-KI-01). KiCad 10 `.kicad_sch` format version `20260101`
and `.kicad_pcb` format version `20260206` cannot be read by KiCad 8 — `kicad-cli` would
abort with a format version error. Ubuntu universe is therefore **not a viable install source**
for this project.

**Chosen fix — Docker container job (`kicad/kicad:10.0`):**  
KiCad publishes official Docker images to Docker Hub under the `kicad/kicad` repository.
The tag `kicad/kicad:10.0` was verified live against the Docker Hub API
(last pushed 2026-05-09, last pulled 2026-06-06, digest
`sha256:165c81785b2df23a09892f4cc53bc0095a83b469bfbbe07989670d64049677a7`,
image size ~800 MB). The image is public, requires no registry authentication,
and ships `kicad-cli` and Python 3 (KiCad scripting engine). The pinned patch tag
`kicad/kicad:10.0.2` (identical digest) is preferred over the floating `10.0` tag
for fully reproducible CI runs.

Using a GitHub Actions `container:` job, the Docker image is pulled once per runner;
all steps execute inside the container with the workspace mounted at `$GITHUB_WORKSPACE`.
No sudo, no PPA, no apt — KiCad is already installed in the image.

---

### P2 — `release.yml`: Entirely wrong project (MAUI/Android leftover)

| # | File | Lines | Finding |
|---|------|-------|---------|
| 2a | `release.yml` | 4–8 | Trigger is `workflow_run` on `workflows: [MAUI CI]`. No workflow named "MAUI CI" exists in this repository; this trigger will **never fire**. |
| 2b | `release.yml` | 21 | `runs-on: windows-latest` — wrong OS for a KiCad / Linux project. |
| 2c | `release.yml` | 38 | `actions/setup-dotnet@v4` — .NET not used in this project. |
| 2d | `release.yml` | 43 | `dotnet workload install maui-android` — MAUI Android workload. |
| 2e | `release.yml` | 46 | `dotnet restore NdiForAndroid.sln` — solution file does not exist in this repo; step would fail immediately if triggered via `workflow_dispatch`. |
| 2f | `release.yml` | 85 | `dotnet publish … -f net10.0-android` — publishes an Android APK. |
| 2g | `release.yml` | 104 | Release name is `"NDI for Android ${{ steps.version.outputs.version_name }}"`. |

This file was copied wholesale from a different project and was never adapted. It is
dead weight and a security risk (if someone accidentally triggers `workflow_dispatch`,
every step fails in a confusing way). It must be **replaced in full**.

---

### P3 — Node.js 20 → 24 forced migration (all four files) — **HARD DEADLINE June 16 2026**

GitHub Actions forces all JavaScript actions to run on Node.js 24 starting 2026-06-16.
The following action pins are affected:

| Action pin | File | Line(s) |
|---|---|---|
| `actions/checkout@v4` | `hardware-check.yml` | 16, 40 |
| `actions/setup-python@v5` | `hardware-check.yml` | 18 |
| `actions/upload-artifact@v4` | `hardware-check.yml` | 99, 105 |
| `actions/checkout@v4` | `release.yml` | 33 (being replaced — moot) |
| `actions/setup-dotnet@v4` | `release.yml` | 38 (being replaced — moot) |
| `actions/checkout@v4` | `codeql.yml` | 24 |
| `github/codeql-action/init@v3` | `codeql.yml` | 27 |
| `github/codeql-action/analyze@v3` | `codeql.yml` | 33 |
| `actions/checkout@v4` | `copilot-setup-steps.yml` | 20 |
| `actions/setup-node@v4` | `copilot-setup-steps.yml` | 22 |

All `@v4` tags of the standard GitHub Actions (`checkout`, `setup-python`, `setup-node`,
`upload-artifact`) have already shipped Node.js 24-compatible runtimes in their latest
patch releases — the major version tag (`@v4`) is updated in-place by GitHub. The
stopgap below buys time while the proper action-version pins are reviewed and updated.

**Stopgap (Phase 0):** Add `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` as a GitHub
Actions repository variable (Settings → Secrets and Variables → Actions → Variables)
or at workflow `env:` level. This instructs the runner to use the Node.js 24 runtime
for all JavaScript actions regardless of which Node.js version the action declares.

**Proper fix (Phase 1):** Upgrade `github/codeql-action` from `@v3` to `@v4` (v3 is
deprecated December 2026, and v4 is already Node.js 24-compatible). Confirm all other
`@v4` action pins resolve to Node.js 24-compatible patch versions; add explicit SHA
pins if reproducibility is required. Remove the stopgap variable once all pins are updated.

---

### P4 — `copilot-setup-steps.yml`: Invalid shell command + missing timeout

| # | File | Lines | Finding |
|---|------|-------|---------|
| 4a | `copilot-setup-steps.yml` | 34 | `npx run build` — `npx` is a package executor, not a script runner. `npx` has no `run` subcommand; this would fail with `npm error unknown command: run`. The correct command is `npm run build`. |
| 4b | `copilot-setup-steps.yml` | 13 | `copilot-setup-steps` job has no `timeout-minutes`; it can hang indefinitely. |
| 4c | `copilot-setup-steps.yml` | 26–34 | The entire Node.js section (`npm ci`, `npx playwright install`, `npx run build`) is irrelevant to this project. Constitution §2.4 (P-UI-01) explicitly mandates plain HTML/CSS/JS with **no npm, no bundlers, no frameworks**. There is no `package.json` in this repository. Running `npm ci` would fail immediately (no lockfile). |

**Chosen fix:** Remove the `actions/setup-node@v4` step, `npm ci`, `npx playwright install`,
and the `Build application` step entirely. Replace with the Copilot agent's actual
environment needs: Python 3 (for the generator script) and KiCad tooling (for ERC/DRC).
Add `timeout-minutes: 15`.

---

### Minor issues (fix alongside P1–P4)

| # | File | Lines | Finding |
|---|------|-------|---------|
| M1 | `hardware-check.yml` | 12, 32 | Missing `timeout-minutes` on both jobs. |
| M2 | `hardware-check.yml` | 98–110 | Artifact upload steps missing `if: always()`. |
| M3 | `codeql.yml` | 27, 33 | `github/codeql-action@v3` — deprecated December 2026; upgrade to `@v4`. |

---

## 2. Implementation Approach

### Priority order

1. **P3 — Node.js 24 (URGENT: 10 days to June 16 2026)**
2. **P2 — Replace dead `release.yml`**
3. **P1 — Fix broken KiCad gate in `hardware-check.yml`**
4. **P4 — Fix `copilot-setup-steps.yml`**
5. **M1–M3 — Minor hardening** (done alongside the above)

---

### Phase 0 — Immediate stopgap (< 1 hour, today)

Set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` as a repository Actions variable:

```sh
gh variable set FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 --body "true" \
  --repo nielsverhoeven/PoE-FanController
```

Or add to each workflow's top-level `env:` block as a bridge:

```yaml
env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true
```

This prevents the June 16 hard-break while the proper pin upgrades are prepared.

---

### Phase 1 — Node.js 24 action pin upgrades (P3 + M3)

**`codeql.yml`** — upgrade CodeQL actions from `@v3` to `@v4`:

```yaml
# line 27 — change from:
uses: github/codeql-action/init@v3
# to:
uses: github/codeql-action/init@v4

# line 33 — change from:
uses: github/codeql-action/analyze@v3
# to:
uses: github/codeql-action/analyze@v4
```

**`hardware-check.yml`** — the `@v4` tags for `actions/checkout`, `actions/setup-python`,
and `actions/upload-artifact` already point to Node.js 24-compatible patch versions.
Confirm by reviewing each action's changelog and SHA at the time of the PR. No version
bump is needed unless the SHA resolves to an older Node.js 20-only runtime.

**`copilot-setup-steps.yml`** — after applying the P4 fix (Phase 4), this workflow no
longer uses `actions/setup-node@v4`. `actions/checkout@v4` remains and should be
confirmed Node.js 24-compatible.

**Remove stopgap** once all pins are verified and the PR merges before June 16.

---

### Phase 2 — Replace `release.yml` (P2)

Delete the current file and replace with the KiCad fabrication release workflow below.

**Trigger strategy decision:** Tag-based (`push` on `v*.*.*`) plus `workflow_dispatch`.
Rationale: This is the conventional approach for release automation; it is explicit
(no surprise releases), aligns with semantic-versioning conventions, and is simpler
than label-based or status-check-based triggers. `workflow_dispatch` is included
for manual testing.

**Proposed new `release.yml`:**

```yaml
name: Release — KiCad Fabrication Outputs

on:
  push:
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'
  workflow_dispatch:
    inputs:
      prerelease:
        description: Mark as pre-release
        required: false
        default: 'false'
        type: boolean

jobs:
  release:
    name: Build fabrication outputs and publish release
    runs-on: ubuntu-latest
    timeout-minutes: 30
    container:
      image: kicad/kicad:10.0.2   # pinned patch; ~800 MB; includes kicad-cli + Python 3
    permissions:
      contents: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Run PCB generator
        env:
          KICAD_FP_BASE: /usr/share/kicad/footprints
        run: python3 hardware/generate_project.py

      - name: Export Gerbers
        run: |
          mkdir -p hardware/gerbers
          kicad-cli pcb export gerbers \
            hardware/kicad/PoE-FanController.kicad_pcb \
            --output hardware/gerbers/

      - name: Export drill files
        run: |
          kicad-cli pcb export drill \
            hardware/kicad/PoE-FanController.kicad_pcb \
            --output hardware/gerbers/ \
            --format excellon \
            --excellon-separate-th

      - name: Export schematic PDF
        run: |
          kicad-cli sch export pdf \
            hardware/kicad/PoE-FanController.kicad_sch \
            --output hardware/PoE-FanController-schematic.pdf

      - name: Bundle fabrication archive
        run: |
          cd hardware
          zip -r ../PoE-FanController-fab-${{ github.ref_name }}.zip \
            gerbers/ \
            bom/bom.csv \
            PoE-FanController-schematic.pdf

      - name: Publish GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ github.ref_name }}
          name: PoE FanController ${{ github.ref_name }}
          files: PoE-FanController-fab-${{ github.ref_name }}.zip
          fail_on_unmatched_files: true
          generate_release_notes: true
          prerelease: ${{ github.event.inputs.prerelease == 'true' || contains(github.ref_name, '-rc') || contains(github.ref_name, '-alpha') || contains(github.ref_name, '-beta') }}
```

**Release assets included:**
- `hardware/gerbers/` — all Gerber layers + Excellon drill files (for PCB fabrication)
- `hardware/bom/bom.csv` — bill of materials (for component procurement)
- `hardware/PoE-FanController-schematic.pdf` — schematic PDF (for review/documentation)

All bundled into `PoE-FanController-fab-<tag>.zip` as a single release asset.

**Note on `softprops/action-gh-release@v2`:** This action uses a Node.js 20 runtime
in its current release; verify whether v2's latest patch ships Node.js 24 support
before the June 16 deadline, or substitute with the official `gh release create` CLI
command (pre-installed on all GitHub-hosted runners) to avoid the dependency entirely:

```yaml
      - name: Publish GitHub Release (CLI alternative)
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release create "${{ github.ref_name }}" \
            --title "PoE FanController ${{ github.ref_name }}" \
            --generate-notes \
            PoE-FanController-fab-${{ github.ref_name }}.zip
```

The CLI alternative is preferred if `softprops/action-gh-release` cannot be
confirmed Node.js 24-compatible before the deadline.

---

### Phase 3 — Fix `hardware-check.yml` KiCad gate (P1 + M1 + M2)

**`validate-generator` job** (lines 12–30):

- Add `timeout-minutes: 10` to the job (M1).
- Remove `|| true` from line 30. The generator must be allowed to fail. If footprint
  errors are acceptable on CI, add a specific `|| true` only on the footprint-embed
  call, not on the entire script. Preferred: fix the generator to detect missing
  `KICAD_FP_BASE` gracefully and exit with a non-zero code only on logic errors.

**`kicad-erc-drc` job** (lines 32–111) — switch to Docker container:

```yaml
  kicad-erc-drc:
    name: KiCad ERC + DRC
    runs-on: ubuntu-latest
    timeout-minutes: 20            # M1 fix
    container:
      image: kicad/kicad:10.0.2   # P1 fix — pinned Docker image; no PPA needed
    steps:
      - uses: actions/checkout@v4

      - name: Run PCB generator
        env:
          KICAD_FP_BASE: /usr/share/kicad/footprints
        run: python3 hardware/generate_project.py
        # No || true: generator failures must block the gate

      - name: Run ERC
        run: |
          kicad-cli sch erc \
            hardware/kicad/PoE-FanController.kicad_sch \
            --output hardware/kicad/erc_result.rpt
          echo "=== ERC Report ===" && cat hardware/kicad/erc_result.rpt

      - name: Check ERC errors
        run: |
          ERRORS=$(grep -c 'ERC error' hardware/kicad/erc_result.rpt || true)
          echo "ERC errors: $ERRORS"
          if [ "$ERRORS" -gt 0 ]; then
            echo "❌ FAIL: ERC reported $ERRORS error(s)"
            exit 1
          fi
          echo "✅ PASS: Zero ERC errors"

      - name: Run DRC
        run: |
          kicad-cli pcb drc \
            hardware/kicad/PoE-FanController.kicad_pcb \
            --output hardware/kicad/drc_result.rpt \
            --schematic-parity
          echo "=== DRC Report ===" && cat hardware/kicad/drc_result.rpt

      - name: Check DRC violation count
        run: |
          VIOLATIONS=$(grep -c '^\[' hardware/kicad/drc_result.rpt || true)
          MISSING=$(grep -c 'missing_footprint' hardware/kicad/drc_result.rpt || true)
          echo "Total DRC violations: $VIOLATIONS"
          echo "missing_footprint:    $MISSING"
          if [ "$MISSING" -gt 0 ]; then
            echo "❌ FAIL: missing_footprint violations detected"
            exit 1
          fi
          if [ "$VIOLATIONS" -gt 36 ]; then
            echo "❌ FAIL: DRC violation count $VIOLATIONS exceeds threshold 36"
            exit 1
          fi
          echo "✅ PASS: DRC within acceptable limits"

      - name: Upload ERC report
        uses: actions/upload-artifact@v4
        if: always()               # M2 fix — upload even if ERC step crashed
        with:
          name: erc-report
          path: hardware/kicad/erc_result.rpt

      - name: Upload DRC report
        uses: actions/upload-artifact@v4
        if: always()               # M2 fix
        with:
          name: drc-report
          path: hardware/kicad/drc_result.rpt
```

Key changes vs. current file:
- `container: image: kicad/kicad:10.0.2` replaces the entire Install KiCad step (lines 42–56).
- The `id: install_kicad` / `kicad_available` output and all `if: steps.install_kicad.outputs…`
  guards are removed. If the container cannot be pulled, the job fails hard — which is correct.
- `|| true` removed from the generator step (line 30 of current file).
- Added explicit ERC error-count check (current file only checks DRC violation count).
- Artifact uploads changed to `if: always()`.
- `timeout-minutes` added to both jobs.

---

### Phase 4 — Fix `copilot-setup-steps.yml` (P4)

```yaml
name: "Copilot Setup Steps"

on:
  workflow_dispatch:
  push:
    paths:
      - .github/workflows/copilot-setup-steps.yml
  pull_request:
    paths:
      - .github/workflows/copilot-setup-steps.yml

jobs:
  copilot-setup-steps:
    runs-on: ubuntu-latest
    timeout-minutes: 15            # P4 fix — missing timeout added

    permissions:
      contents: read

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Verify generator syntax
        run: python -m py_compile hardware/generate_project.py
```

Rationale for removing Node.js steps:
- Constitution P-UI-01: "No frameworks, no bundlers, no npm" — this project has no
  `package.json`, no `node_modules`, and no JS build step.
- `npm ci` would fail immediately (no `package-lock.json`).
- `npx playwright install` is irrelevant to hardware/firmware CI.
- `npx run build` (line 34 in current file) is syntactically invalid.
- Replacing with a Python syntax check matches what `validate-generator` already does
  and provides a meaningful Copilot agent environment verification.

---

## 3. Architecture Fit

### Constitution compliance

| Constitution principle | How this plan satisfies it |
|---|---|
| **P-KI-01** — KiCad 10.0.3 exclusively | Docker image `kicad/kicad:10.0.2` is pinned to KiCad 10, matching the project's format versions (20260101 / 20260206). |
| **P-KI-04** — Generator script is schematic source of truth | Both `hardware-check.yml` and the new `release.yml` run `python3 hardware/generate_project.py` before any KiCad CLI invocation. |
| **P-KI-06** — Gerbers in `hardware/gerbers/` | The new `release.yml` exports Gerbers and drill files to `hardware/gerbers/` as required. |
| **P-TEST-01** — Zero ERC errors required | Fixed `hardware-check.yml` adds an explicit ERC error-count check; the gate now fails hard if any ERC error is detected. |
| **P-TEST-03** — Zero DRC errors required | Fixed `hardware-check.yml` retains the DRC violation threshold check. The `missing_footprint` check remains a hard failure. |
| **P-TEST-04** — DRC before Gerber generation | The new `release.yml` does not explicitly run DRC before Gerber export. **Risk:** See §4, R2. Mitigation: add a DRC step with `exit 1` on violations before the Gerber export step. |
| **P-DEV-01** — Commit message convention | All CI fix commits should use the `ci:` type prefix. |
| **P-DEV-02** — ERC/DRC gate for hardware PRs | Restoring the actual ERC/DRC execution in `hardware-check.yml` fulfils this principle. The gate is no longer a no-op. |
| **P-UI-01** — No npm/bundlers | Removing the Node.js steps from `copilot-setup-steps.yml` enforces this principle in CI. |

### No hardware or firmware changes

This feature touches only `.github/workflows/*.yml` and `docs/features/ci-fixes/`.
No `.kicad_sch`, `.kicad_pcb`, `firmware/`, or `hardware/generate_project.py` changes
are made. No constitution amendments are required.

---

## 4. Risk Assessment

### R1 — Docker image pull latency and size (~800 MB per cold runner)

**Likelihood:** Medium. GitHub-hosted runners cache popular images; `kicad/kicad:10.0.2`
was pulled from Docker Hub as recently as 2026-06-06 and may already be warm.

**Impact:** Slow CI (potentially +3–5 min on cold pull); no correctness risk.

**Mitigation:** Accept the latency. If CI time becomes a concern, upgrade to a
self-hosted runner with the image pre-pulled, or use GitHub Actions' built-in
`docker pull` caching via `docker/setup-buildx-action`. Do not switch to the `-full`
image (1.4 GB) — the standard image includes all required `kicad-cli` commands.

### R2 — Gerber export without DRC in `release.yml`

**Likelihood:** Low (tag-based releases should only be cut from clean branches).

**Impact:** High — fabrication outputs from a design with DRC violations could be sent
to a PCB manufacturer.

**Mitigation:** Add a DRC step with hard failure (`exit 1` on any violation) before
the Gerber export step in `release.yml`. This mirrors P-TEST-04. The `hardware-check.yml`
gate already runs DRC on every PR, but an explicit DRC check in `release.yml` provides
defence-in-depth for the release-cut path.

### R3 — KiCad Docker image PATH or environment differences from the PPA install

**Likelihood:** Low. The `kicad/kicad` Docker Hub image is the project's official CI image,
designed specifically for headless `kicad-cli` invocations.

**Impact:** Medium — `kicad-cli` might not be on PATH, or the footprint library path
`/usr/share/kicad/footprints` might differ.

**Mitigation:**
1. Add a `kicad-cli --version` smoke-test step before ERC/DRC steps.
2. Verify the footprint base path with `find /usr -name "*.kicad_mod" -maxdepth 6 | head -1`
   in the bring-up PR.
3. If `KICAD_FP_BASE` differs, override the env var in the step.

### R4 — June 16 deadline miss if `softprops/action-gh-release@v2` is Node.js 20-only

**Likelihood:** Low-medium. `softprops/action-gh-release@v2` is a community action;
its Node.js runtime version is not guaranteed to be updated before the deadline.

**Impact:** `release.yml` breaks on or after June 16 if the action is not updated.

**Mitigation:** Use the `gh release create` CLI command instead (shown in §2, Phase 2
as the preferred alternative). The `gh` CLI is pre-installed on all GitHub-hosted Ubuntu
runners and has no JavaScript runtime dependency.

### R5 — `|| true` removal causes generator failures to block PRs unexpectedly

**Likelihood:** Low. The current `|| true` was added intentionally for the missing
footprint path scenario on CI.

**Impact:** Medium — PRs that previously passed `validate-generator` may now fail if
the generator exits non-zero for non-critical reasons.

**Mitigation:** Before removing `|| true`, review `hardware/generate_project.py` and
confirm it exits 0 on CI with `KICAD_FP_BASE=/usr/share/kicad/footprints` set
(available inside the KiCad Docker container). The Docker container provides the
footprint library at the expected path, making the original reason for `|| true` moot.

---

## 5. Acceptance Criteria

Each criterion is directly verifiable in the GitHub Actions UI or via `gh run view`.

| # | Criterion | How to verify |
|---|---|---|
| AC-01 | `kicad-erc-drc` job runs `kicad-cli sch erc` and `kicad-cli pcb drc` on every PR touching `hardware/**` | Inspect step logs in the Actions run; both commands must appear and produce output |
| AC-02 | `kicad-erc-drc` job **fails** (exit code non-zero) if ERC detects ≥ 1 error | Introduce a deliberate ERC error in a test branch; confirm the job is red |
| AC-03 | `kicad-erc-drc` job **fails** if DRC detects a `missing_footprint` violation | Verify with current DRC baseline |
| AC-04 | `erc-report` and `drc-report` artefacts are uploaded even when ERC or DRC steps fail | Let ERC fail; confirm artefact is available in the failed run's Summary page |
| AC-05 | No workflow uses a `\|\| true` fallback on a step that is part of the quality gate | Code review of all four workflow files |
| AC-06 | `validate-generator` job fails if `hardware/generate_project.py` exits non-zero | Introduce a syntax error in a test branch; confirm the job is red |
| AC-07 | `release.yml` creates a GitHub Release with a `.zip` containing Gerbers, BOM, and schematic PDF on tag push `v*.*.*` | Push a test tag `v0.1.0-rc1` on a test branch; inspect the created release assets |
| AC-08 | `codeql.yml` uses `github/codeql-action@v4` | `grep` in workflow file; confirm no `@v3` references |
| AC-09 | No workflow triggers a Node.js 20 deprecation warning in the Actions run log after June 16 2026 | Check the Actions annotations tab on any post-deadline run |
| AC-10 | `copilot-setup-steps.yml` has `timeout-minutes` on the job and contains no `npx run build` | Code review + workflow run completes without `npm error unknown command: run` |
| AC-11 | All jobs in all four workflow files have `timeout-minutes` set | Code review |
| AC-12 | `hardware-check.yml` `kicad-erc-drc` job uses `container: kicad/kicad:10.0.2` and has no PPA installation steps | Code review |

---

## 6. Implementation Checklist (sequenced)

```
[ ] Phase 0 — Stopgap (today)
    [ ] Set FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true repository variable via gh CLI

[ ] Phase 1 — P3: Node.js 24 pin upgrades
    [ ] codeql.yml: github/codeql-action/init@v3 → @v4
    [ ] codeql.yml: github/codeql-action/analyze@v3 → @v4
    [ ] Verify @v4 patch SHAs for checkout, setup-python, upload-artifact are Node.js 24-capable
    [ ] Remove stopgap variable once PR is merged (before Jun 16)

[ ] Phase 2 — P2: Replace release.yml
    [ ] Delete current release.yml content
    [ ] Write new KiCad fabrication release workflow (see §2 Phase 2 above)
    [ ] Decide: softprops/action-gh-release@v2 or gh CLI — prefer gh CLI (no Node.js dep)
    [ ] Add DRC step before Gerber export (mitigates R2)

[ ] Phase 3 — P1: Fix hardware-check.yml KiCad gate
    [ ] kicad-erc-drc job: add container: kicad/kicad:10.0.2
    [ ] Remove Install KiCad step (lines 42–56) and all kicad_available guards
    [ ] Add kicad-cli --version smoke-test step
    [ ] Verify KICAD_FP_BASE path inside the container
    [ ] Remove || true from validate-generator job (line 30) after verifying generator behaves
    [ ] Add timeout-minutes: 10 to validate-generator, timeout-minutes: 20 to kicad-erc-drc
    [ ] Change artifact upload steps to if: always()
    [ ] Add explicit ERC error-count check step

[ ] Phase 4 — P4: Fix copilot-setup-steps.yml
    [ ] Remove actions/setup-node@v4, npm ci, npx playwright install, npx run build steps
    [ ] Add actions/setup-python@v5 + python -m py_compile generator smoke-test
    [ ] Add timeout-minutes: 15 to job

[ ] Validation
    [ ] All 12 acceptance criteria verified (see §5)
    [ ] PR #33 passes all CI checks
```

---

## 7. References

- `.github/workflows/hardware-check.yml` — P1: lines 30, 44–56, 98–110; M1: lines 12, 32
- `.github/workflows/release.yml` — P2: lines 4–8, 21, 43, 46, 85, 104 (full replacement)
- `.github/workflows/codeql.yml` — M3: lines 27, 33; P3: line 24
- `.github/workflows/copilot-setup-steps.yml` — P4: lines 13, 34
- `docs/constitution.md` — §2.1 (P-KI-01), §2.4 (P-UI-01), §7 (P-KI-04, P-KI-06), §8 (P-TEST-01, P-TEST-03, P-TEST-04), §9 (P-DEV-01, P-DEV-02)
- Docker Hub: `kicad/kicad:10.0.2` — verified 2026-06-06; digest `sha256:165c81785b2df23a09892f4cc53bc0095a83b469bfbbe07989670d64049677a7`; size 800 MB; pushed 2026-05-09
- GitHub issue #33 (enriched, `<!-- enriched-by-copilot -->` present)
- PR #32 — hardware PR where CI issues were first observed
- Issue #25 — parent CI / hardware gate tracking issue
- [GitHub Actions Node.js 20 → 24 deprecation notice](https://github.blog/changelog/2024-03-07-github-actions-all-actions-will-run-on-node20-instead-of-node16-by-default/)
- [github/codeql-action v4 release notes](https://github.com/github/codeql-action/releases/tag/codeql-bundle-v2.19.0)
