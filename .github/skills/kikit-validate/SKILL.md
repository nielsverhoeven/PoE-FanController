---
name: kikit-validate
description: >
  Validate the PoE FanController schematic (ERC) and PCB (DRC) using kicad-cli.
  Reports violation counts, classifies errors, and gates further work on a clean
  result. Use when asked to 'run DRC', 'run ERC', 'validate PCB', 'validate
  schematic', 'check for errors', 'DRC status', or 'ERC status'.
  NOTE: kikit drc crashes on KiCad 10.0 (access violation) — always use
  kicad-cli for validation in this project.
allowed-tools: shell
---

## Purpose

Provide a fast, reliable pass/fail verdict on the current state of the
schematic and PCB so that agents and users know whether it is safe to proceed
to routing, Gerber export, or CI.

---

## Environment Constants

```powershell
$kicadCli = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
$kikit    = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\Scripts\kikit.exe"
$repo     = "C:\repos-github\PoE-FanController"
$sch      = "hardware\kicad\PoE-FanController.kicad_sch"
$pcb      = "hardware\kicad\PoE-FanController.kicad_pcb"
```

> ⚠️ **DO NOT use `kikit drc run`** — it crashes with an access violation in
> `pcbnew.WriteDRCReport()` on KiCad 10.0. The `kicad-cli` path is stable.

---

## Step 1 — Run ERC (Electrical Rules Check on schematic)

```powershell
cd $repo
& $kicadCli sch erc `
  --output hardware/kicad/erc_result.rpt `
  hardware/kicad/PoE-FanController.kicad_sch 2>&1
```

Parse the result:
```powershell
$erc = Get-Content hardware\kicad\erc_result.rpt -ErrorAction SilentlyContinue
$erc | Select-String "violation|error|warning" | Select-Object -First 20
```

**Interpret:**
- `violations: 0` → ✅ ERC passed — safe to proceed
- Any `severity=error` → ❌ ERC failed — must fix before PCB changes or routing

Known acceptable ERC warnings for this project (schematic v3.1.0):
- None currently known — aim for 0 violations.

---

## Step 2 — Run DRC (Design Rule Check on PCB)

```powershell
cd $repo
& $kicadCli pcb drc `
  --output hardware/kicad/drc_result.rpt `
  hardware/kicad/PoE-FanController.kicad_pcb 2>&1
```

Parse violations:
```powershell
$drc = Get-Content hardware\kicad\drc_result.rpt -ErrorAction SilentlyContinue
$errors   = ($drc | Select-String "severity=error").Count
$warnings = ($drc | Select-String "severity=warning").Count
$unconn   = ($drc | Select-String "unconnected").Count
Write-Host "DRC: $errors errors, $warnings warnings, $unconn unconnected items"
```

**Interpret:**
- `0 errors, 0 unconnected` → ✅ DRC passed
- Any `severity=error` → ❌ DRC failed
- `unconnected > 0` → ❌ routing incomplete
- `warnings` (silk overlap) → ⚠️ cosmetic only, acceptable

---

## Step 3 — Check Net Assignment (routing prerequisite)

If DRC shows unconnected items, first confirm whether nets are loaded:

```powershell
$kicadPy = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe"
& $kicadPy -c "
import sys; sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew
board = pcbnew.LoadBoard('C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb')
board.BuildConnectivity()
nets = [str(n) for n in board.GetNetInfo().NetsByName().keys() if n]
print('Signal nets:', len(nets), '->', sorted(nets)[:10])
print('Unconnected:', board.GetConnectivity().GetUnconnectedCount(False))
"
```

**If signal nets are missing (empty list or only GND):**
→ Netlist not imported. User must open KiCad GUI → Tools → Update PCB from
  Schematic (F8) → Apply. This cannot be scripted — report this requirement.

---

## Step 4 — DRC Baseline Comparison

Compare against the known baseline established in board v3.1.0:

| Metric | Baseline (pre-routing) | After routing |
|---|---|---|
| ERC violations | 0 | 0 |
| DRC errors | 0 | 0 |
| DRC silk warnings | 4 | ≤ 4 |
| Unconnected | 0* | 0 |

*0 unconnected before routing because nets were not imported yet (no ratsnest).

If any metric exceeds the baseline, escalate with the specific violation list.

---

## Step 5 — Report

After running both ERC and DRC, produce a compact report:

```markdown
## Validation Report — PoE-FanController v3.1.0

| Check | Status | Details |
|---|---|---|
| ERC (schematic) | ✅ / ❌ | N violations |
| DRC (PCB errors) | ✅ / ❌ | N errors |
| DRC (silk warnings) | ⚠️ / ✅ | N warnings (cosmetic) |
| Unconnected nets | ✅ / ❌ | N items |
| Net assignment | ✅ / ⚠️ | Nets loaded / missing (needs F8) |

### Overall Gate
✅ READY / ❌ NOT READY — describe blocking issue
```

---

## Step 6 — Commit Report Files

```powershell
cd $repo
git add hardware/kicad/erc_result.rpt hardware/kicad/drc_result.rpt
git commit -m "hw(validation): ERC + DRC report — <0 errors / N violations>

ERC: 0 violations. DRC: 0 errors, N silk warnings, 0 unconnected.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push origin feature/75-esp32-p4-poe-eth-daughterboard
```

---

## Quality Rules

- **Never use `kikit drc run`** on KiCad 10.0 — it crashes (access violation
  in `pcbnew.WriteDRCReport()`). Use `kicad-cli pcb drc` exclusively.
- ERC must pass (0 violations) before any PCB routing work begins.
- DRC must pass (0 errors, 0 unconnected) before Gerber export.
- Silk warnings are cosmetic and do not block routing or export.
- Always report baseline vs current counts — delta matters more than absolutes.
- If `kicad-cli` is not on PATH, use the full path in $kicadCli above.
