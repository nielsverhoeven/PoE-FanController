---
name: github-action-runs-manager
description: >
  Inspect, analyse, and report on GitHub Actions workflow runs for the current
  repository. Fetch run lists, drill into job details, retrieve failure logs,
  identify root causes, and summarise CI health for a given PR, branch, or
  commit. Use when asked to 'check CI', 'why did the action fail', 'get run logs',
  'investigate failures', 'CI status for PR', or 'recent run results'.
allowed-tools: shell
---

## Purpose

Give a precise, evidence-based diagnosis of GitHub Actions run results so that
the calling agent (or user) can understand what failed, why, and what needs to
be fixed — without having to manually browse the GitHub UI.

---

## Step 1 — Locate the GitHub CLI and Repository

```powershell
# Find gh
& "C:\Program Files\GitHub CLI\gh.exe" auth status   # Windows
# or: gh auth status

# Resolve repo
git remote get-url origin   # strip .git suffix → owner/repo
```

---

## Step 2 — List Recent Runs

### For a specific workflow:
```
gh run list --repo <owner/repo> --workflow <workflow-id> --limit <N>
```

### For a specific PR:
```
gh pr checks <pr-number> --repo <owner/repo>
```

### For a specific branch:
```
gh run list --repo <owner/repo> --branch <branch-name> --limit 20
```

### For the most recent commit on the current branch:
```
$sha = git rev-parse HEAD
gh run list --repo <owner/repo> --commit $sha
```

Present results as a table:

| Run ID | Workflow | Branch | Event | Status | Duration | Age |
|---|---|---|---|---|---|---|

Use these status symbols:
- ✅ `completed / success`
- ❌ `completed / failure`
- ⏱️ `in_progress`
- ⏭️ `skipped`
- 💀 `timed_out`
- 🚫 `cancelled`

---

## Step 3 — Inspect a Single Run

```
gh run view <run-id> --repo <owner/repo>
```

Extract:
- Overall status
- Job list with individual statuses and durations
- Any annotations (warnings, errors)
- Triggered by: push / pull_request / schedule / workflow_dispatch

Identify the **first failing job** — that is almost always the root cause; later
jobs may fail as a cascade.

---

## Step 4 — Retrieve Failure Logs

### Full log of a failed run (filtered to errors only):
```
gh run view <run-id> --repo <owner/repo> --log-failed
```

### Full log of a specific job:
```
gh run view --job <job-id> --repo <owner/repo> --log
```

When logs are very long, extract the most informative section:
- Search for `##[error]`, `ERROR`, `FAILED`, `exit code`, `Exception`, `timed out`
- Show the 20 lines before and after each error marker
- For timeout failures, look for the last meaningful log line before the kill

---

## Step 5 — Root Cause Classification

Classify every failure into one of these categories:

| Category | Symptoms | Typical Fix |
|---|---|---|
| **Timeout** | Duration = 6h0m, "exceeded maximum execution time" | Add `timeout-minutes`, fix hung process (infinite loop, stuck build) |
| **Build failure** | Compiler error, missing dependency, PlatformIO build error | Fix source code or dependency config |
| **Test failure** | Unit test assertion failed, exit code 1 from test runner | Fix failing test or the code under test |
| **ERC failure** | KiCad ERC reports errors in schematic | Fix schematic errors; run kicad-cli sch erc locally to reproduce |
| **DRC failure** | KiCad DRC reports violations in PCB layout | Fix layout violations; run kicad-cli pcb drc locally to reproduce |
| **Environment missing** | Tool not found (kicad-cli, pio), SDK missing | Provision the tool in CI environment or mark as `not-applicable` |
| **Flaky / intermittent** | Same test passes in other runs, no code change | Add retry logic or investigate race condition |
| **Workflow misconfiguration** | Wrong branch filter, missing secret, bad YAML | Fix the workflow YAML |
| **Deprecated action** | Node.js deprecation warning, forced upgrade | Bump action versions |
| **Artifact / path missing** | "No files were found with the provided path" | Fix artifact path in workflow YAML |
| **Firmware size over budget** | Flash or RAM usage exceeds partition limits | Optimize code size or increase partition budget in `platformio.ini` |

> **Note**: For firmware build failures, check the full PlatformIO build log for the first error — subsequent errors are often cascading from the root cause.

---

## Step 6 — PR / Commit CI Health Check

When called to validate a specific PR or recent commit:

1. Fetch all runs for the PR branch or commit SHA.
2. For each workflow that ran:
   - Record: status, duration, job results
3. Produce a **CI Health Report**:

```markdown
## CI Health Report — PR #<N> / commit <sha>

| Workflow | Status | Duration | Root Cause (if failed) |
|---|---|---|---|
| Firmware CI | ✅ pass | 1m47s | — |
| Hardware Check | ✅ pass | 0m32s | — |
| CodeQL | ✅ pass | 3m12s | — |

### Failed Runs — Detail

#### Firmware CI — build job
**Classification**: Build failure
**Evidence**: `error: 'FanControl' does not name a type`
**Recommended fix**: Fix the missing include or class definition in the firmware source.

### Overall Gate
❌ NOT READY — 1 required workflow failing. Fix before merge.
```

---

## Step 7 — Re-trigger a Run

If a failure is transient (flaky, infra issue) and a re-run is appropriate:

```
gh run rerun <run-id> --repo <owner/repo>               # rerun all jobs
gh run rerun <run-id> --repo <owner/repo> --failed-only  # rerun only failed jobs
```

Only suggest a re-run when the failure classification is **Flaky / intermittent**
or **Environment missing** (transient infra). For all other categories, a fix
is required before re-running.

---

## Quality Rules

- Always classify failures — never report "it failed" without a root cause category.
- Distinguish between the **first failing job** (root cause) and **cascade failures**
  (jobs that failed because an earlier job failed).
- When a run timed out at 6 hours, always check whether `timeout-minutes` is set
  in the workflow YAML and flag it if missing.
- Never suggest a re-run for a build or test failure — those require a fix.
- Include the run URL in every report so the user can navigate directly to GitHub.
