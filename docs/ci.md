<!-- Last updated: 2026-06-07 | Updated by: feature/33-fix-ci-workflows -->

# CI / Automated Checks

This document describes the four GitHub Actions workflows in `.github/workflows/`, what each checks, and how to interpret failures.

For constitution principles that govern these workflows see [`docs/constitution.md`](constitution.md) §8.5 (P-CI-01, P-CI-02) and §7 (P-KI-01 and its CI Docker image PATCH amendment).

---

## Workflow Summary

| Workflow file | Name | Trigger | Purpose |
|---|---|---|---|
| `hardware-check.yml` | Hardware Check (ERC + DRC) | `push` / `pull_request` on `hardware/**` or the workflow file itself | Validates the schematic generator and runs KiCad ERC + DRC inside a Docker container |
| `release.yml` | KiCad Hardware Release | `push` on `v*.*.*` tags; `workflow_dispatch` | DRC-gates then exports Gerbers, drill files, BOM CSV, and schematic PDF; publishes a GitHub Release |
| `codeql.yml` | CodeQL | `push` to `main`; all PRs; weekly schedule (Monday 04:00 UTC) | Static security analysis of Python source (`hardware/generate_project.py`) |
| `copilot-setup-steps.yml` | Copilot Setup Steps | `workflow_dispatch`; `push` / `pull_request` on the file itself | Bootstraps a Copilot agent environment and validates the generator script syntax |

All four workflows set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` at the `env:` level as a bridge measure through the GitHub Actions mandatory Node.js 24 migration deadline (2026-06-16). See [Node.js 24 migration](#nodejs-24-migration) below.

---

## Workflow Details

### `hardware-check.yml` — Hardware Check (ERC + DRC)

**Trigger:** Any `push` or `pull_request` that touches `hardware/**` or the workflow file itself.

**Jobs:**

#### `validate-generator` (timeout: 10 min)

Runs on `ubuntu-latest`. Checks out the repository, installs Python 3.12, and runs:

```
python -m py_compile hardware/generate_project.py
```

This confirms the generator script has no syntax errors before the KiCad container job starts.

#### `kicad-erc-drc` (timeout: 20 min)

Runs inside the official KiCad Docker container:

```yaml
container:
  image: kicad/kicad:10.0.2
  options: --user root
```

> **Version note:** The project's locked development tool is KiCad 10.0.3 (P-KI-01). The CI container uses `kicad/kicad:10.0.2` because no `10.0.3` image was published on Docker Hub as of 2026-05-09. This is permitted by the P-KI-01 PATCH amendment (constitution v1.1.0). `--user root` is required to avoid an EACCES permission error when the container writes output files.

**Steps (in order):**

1. **Run PCB generator** — executes `KICAD_FP_BASE=/usr/share/kicad/footprints python3 generate_project.py` inside `hardware/`. Any non-zero exit fails the job immediately (no `|| true` suppression).

2. **Run ERC** — invokes `kicad-cli sch erc … --format json`. The KiCad CLI may exit non-zero even for warnings; the raw exit code is captured with `|| true` so the JSON output is always written.

3. **Check ERC results (zero errors enforced)** — a Python one-liner reads `hardware/kicad/erc_output.json`, counts violations with `severity == "error"`, and calls `sys.exit(1)` if any are found. Warnings do not block the job.

4. **Run DRC** — invokes `kicad-cli pcb drc … --format json --exit-code-violations || true` to guarantee JSON output regardless of violation count.

5. **Check DRC violation count (baseline 67)** — a Python one-liner reads `hardware/kicad/drc_output.json` and exits with code 1 if the total violation count exceeds **67**. The baseline of 67 was measured in the `kicad/kicad:10.0.2` Docker/Linux environment and breaks down as:
   - 34 `lib_footprint_issues` (version-sensitive, dependent on Docker image's bundled library)
   - 28 `solder_mask_bridge` on J6 USB-C (pre-existing, component-level)
   - 5 `silk_edge_clearance`

   The local Windows KiCad 10.0.3 count is 36 (no `lib_footprint_issues`); Docker is the authoritative gate. A follow-up issue (#39) tracks driving this count to zero (P-TEST-03).

6. **Upload ERC report** (`if: always()`) — uploads `hardware/kicad/erc_output.json` as the `erc-report` artifact.

7. **Upload DRC report** (`if: always()`) — uploads `hardware/kicad/drc_output.json` as the `drc-report` artifact. The `if: always()` condition ensures reports are preserved even when a preceding step fails.

**Interpreting failures:**

| Failure step | Likely cause | Action |
|---|---|---|
| `validate-generator` / Syntax check | Python syntax error in `hardware/generate_project.py` | Fix the syntax error in the generator script |
| `kicad-erc-drc` / Run PCB generator | Generator runtime error (bad net, missing component) | Run `python hardware/generate_project.py` locally and fix the error |
| `kicad-erc-drc` / Check ERC results | One or more ERC errors (severity=error) in the schematic | Download the `erc-report` artifact and inspect errors; fix in generator |
| `kicad-erc-drc` / Check DRC violation count | More than 67 DRC violations in the Docker environment | Download the `drc-report` artifact; new violations must be resolved before merge |

---

### `release.yml` — KiCad Hardware Release

**Trigger:** `push` on tags matching `v*.*.*`; or `workflow_dispatch` (requires a `tag` input, e.g. `v0.1.0`).

**Job: `release`** (timeout: 30 min)

Runs inside the same Docker container as `hardware-check.yml`:

```yaml
container:
  image: kicad/kicad:10.0.2
  options: --user root
```

`permissions: contents: write` is required so the job can publish a GitHub Release.

**Steps (in order):**

1. **Checkout** — full repository checkout.

2. **Generate KiCad files** — runs `KICAD_FP_BASE=/usr/share/kicad/footprints python3 generate_project.py` inside `hardware/`. Hard-fails on any error.

3. **DRC gate (zero tolerance) — P-CI-02** — runs `kicad-cli pcb drc … --format json --exit-code-violations`. A Python inline script reads the output and calls `sys.exit(1)` if `violations` is non-empty. **This gate uses a threshold of zero — no violations are permitted, regardless of the 67-violation PR baseline.** Gerber export is blocked until this step exits with code 0. This enforces P-CI-02 and P-TEST-04.

4. **Export Gerbers** — `kicad-cli pcb export gerbers … --output hardware/gerbers/`.

5. **Export drill files** — `kicad-cli pcb export drill … --format excellon --output hardware/gerbers/`.

6. **Export schematic PDF** — `kicad-cli sch export pdf … --output hardware/PoE-FanController-schematic.pdf`.

7. **Bundle release assets** — zips Gerbers and copies BOM CSV with the tag name embedded in the filename.

8. **Create GitHub Release** — uses the `gh release create` CLI (pre-installed on GitHub-hosted runners) to publish the release, attaching the Gerber ZIP, BOM CSV, and schematic PDF. No third-party JavaScript action is used.

**Interpreting failures:**

| Failure step | Likely cause | Action |
|---|---|---|
| Generate KiCad files | Generator error on the tagged commit | Fix before re-tagging |
| DRC gate | PCB has ≥ 1 DRC violation in the Docker environment | Resolve all DRC violations in the PCB, regenerate, and re-tag |
| Export Gerbers / drill / PDF | `kicad-cli` error (file path, missing layer) | Check the step log; verify file paths in the workflow |
| Create GitHub Release | Tag already has a release, or `GH_TOKEN` lacks `contents: write` | Delete the existing release, or check repository permissions |

> **Release vs. PR gate:** The release DRC gate uses **zero tolerance**. A PR may merge with up to 67 DRC violations (the tracked baseline); a tag-triggered release will be blocked until all violations are resolved. This is intentional (P-CI-02).

---

### `codeql.yml` — CodeQL

**Trigger:** `push` to `main`; all `pull_request` events; weekly schedule (Mondays 04:00 UTC).

**Job: `analyze`** (timeout: 30 min, `ubuntu-latest`)

Runs GitHub's CodeQL static analysis on Python source code (language: `python`, build-mode: `none`). The primary target is `hardware/generate_project.py`.

**Permissions required:** `security-events: write`, `packages: read`, `actions: read`, `contents: read`.

Results are uploaded to GitHub's Security → Code Scanning dashboard. Findings appear as alerts on the repository.

**Interpreting failures:** A job failure (not a CodeQL finding) means the CodeQL action itself errored — check the runner log. CodeQL findings do not fail the job; they appear as security alerts. A finding on `hardware/generate_project.py` should be investigated and resolved or marked as dismissed with a rationale.

**Action versions:** `github/codeql-action/init@v4` and `github/codeql-action/analyze@v4` (upgraded from @v3 in this feature — @v3 is deprecated with a hard removal deadline of 2026-06-16).

---

### `copilot-setup-steps.yml` — Copilot Setup Steps

**Trigger:** `workflow_dispatch`; `push` or `pull_request` on the workflow file itself.

**Job: `copilot-setup-steps`** (timeout: 15 min, `ubuntu-latest`)

This workflow is a bootstrap hint for GitHub Copilot agents working on this repository. It does not constitute a CI gate for PRs.

**Steps:**

1. `actions/checkout@v4`
2. `actions/setup-python@v5` with `python-version: '3.x'`
3. **Validate hardware generator (Python smoke-test):** `python -m py_compile hardware/generate_project.py`

This confirms Python is available and the generator script is syntactically valid in the agent environment. There are no npm, Node.js, or browser-automation steps — the project has no `package.json` and no JavaScript build pipeline (P-UI-01).

**Interpreting failures:** A failure here means the generator script has a Python syntax error, or `actions/setup-python` failed to install Python. This does not block PRs but should be investigated if Copilot agent tasks are failing to initialise.

---

## Node.js 24 Migration

GitHub Actions is migrating all JavaScript-based actions to run on Node.js 24 with a hard enforcement date of **2026-06-16**. The environment variable:

```yaml
env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"
```

is set at the top-level `env:` block in all four workflow files as a bridge measure. This forces all JavaScript actions on the runner to use the Node.js 24 runtime immediately, before GitHub enforces it globally. The `codeql-action` was upgraded from `@v3` → `@v4` in this feature to meet this deadline (feature/33-fix-ci-workflows, issue #33).

Once GitHub enforces Node.js 24 globally (after 2026-06-16), this environment variable becomes a no-op and may be removed.

---

## DRC Baseline — Known Violations

The `hardware-check.yml` PR gate allows up to **67 DRC violations** (Docker/Linux count). These are pre-existing and tracked in issue [#39](https://github.com/nielsverhoeven/PoE-FanController/issues/39):

| Category | Count | Note |
|---|---|---|
| `lib_footprint_issues` | 34 | Version-sensitive; present in Docker (`kicad/kicad:10.0.2`) only |
| `solder_mask_bridge` | 28 | Pre-existing on J6 USB-C pads |
| `silk_edge_clearance` | 5 | Pre-existing |
| **Total** | **67** | Docker authoritative; local Windows 10.0.3 shows 36 |

Any PR that causes the violation count to exceed 67 will be blocked. The release workflow uses a zero-tolerance threshold independent of this baseline (P-CI-02).

---

## Related Documents

- [`docs/constitution.md`](constitution.md) — P-CI-01, P-CI-02, P-KI-01 (and PATCH amendment), P-TEST-01 through P-TEST-04
- [`hardware/DESIGN.md`](../hardware/DESIGN.md) — DRC status history per feature; hardware bring-up procedure
- [`docs/features/ci-fixes/architecture.md`](features/ci-fixes/architecture.md) — architect review of CI design decisions for issue #33
