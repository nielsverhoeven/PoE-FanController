---
name: kikit-export
description: >
  Export manufacturing files for the PoE FanController PCB using KiKit 1.8.0.
  Generates Gerbers, drill files, and complete fabrication bundles for JLCPCB
  or PCBWay in one command. Use when asked to 'export gerbers', 'generate fab
  files', 'prepare for JLCPCB', 'prepare for PCBWay', 'export manufacturing
  data', or 'generate production files'.
allowed-tools: shell
---

## Purpose

Produce all files needed to order PCBs from a fabrication house, using KiKit's
`fab` command which bundles Gerbers, drill files, BOM, and component placement
into the exact format each fab house requires.

---

## Environment Constants

```powershell
$kikit  = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\Scripts\kikit.exe"
$kicadCli = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
$pcb    = "hardware\kicad\PoE-FanController.kicad_pcb"
$repo   = "C:\repos-github\PoE-FanController"
```

Verify KiKit is accessible before proceeding:
```powershell
& $kikit --version   # expect: kikit, version 1.8.0
```

---

## Step 1 — Run DRC Gate (zero errors required before export)

Never export Gerbers from a board with DRC errors. Run DRC first:

```powershell
cd $repo
& $kicadCli pcb drc `
  --output hardware/kicad/drc_output.json `
  hardware/kicad/PoE-FanController.kicad_pcb 2>&1
```

Parse the result:
```powershell
Get-Content hardware\kicad\drc_result.rpt | Select-String "violations|unconnected"
```

**Gate:** If any `severity=error` violations exist → STOP. Report the violations
and tell the user to fix them before exporting. Silk warnings are acceptable.

Current known baseline (pre-routing): 4 silk warnings, 0 errors, 0 unconnected.

---

## Step 2A — Fab Bundle for JLCPCB (recommended)

```powershell
cd $repo
$outDir = "hardware\gerbers\jlcpcb"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

& $kikit fab jlcpcb `
  hardware/kicad/PoE-FanController.kicad_pcb `
  $outDir
```

This generates:
- `*.gbr` Gerber layers (F.Cu, B.Cu, F.Mask, B.Mask, F.SilkS, B.SilkS, Edge.Cuts)
- `*.drl` Excellon drill file
- `*-BOM.csv` component BOM in JLCPCB format
- `*-CPL.csv` component placement list for JLCPCB SMT assembly

---

## Step 2B — Fab Bundle for PCBWay

```powershell
cd $repo
$outDir = "hardware\gerbers\pcbway"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

& $kikit fab pcbway `
  hardware/kicad/PoE-FanController.kicad_pcb `
  $outDir
```

---

## Step 2C — Plain Gerbers Only (no fab-specific formatting)

```powershell
cd $repo
$outDir = "hardware\gerbers\generic"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

& $kikit export gerber `
  hardware/kicad/PoE-FanController.kicad_pcb `
  $outDir
```

---

## Step 3 — Verify Output

```powershell
Get-ChildItem $outDir | Select-Object Name, Length | Format-Table
```

Expected files (JLCPCB example):
- `PoE-FanController-F_Cu.gbr`
- `PoE-FanController-B_Cu.gbr`
- `PoE-FanController-F_Mask.gbr`
- `PoE-FanController-B_Mask.gbr`
- `PoE-FanController-F_SilkS.gbr`
- `PoE-FanController-Edge_Cuts.gbr`
- `PoE-FanController.drl`
- `PoE-FanController-BOM.csv`
- `PoE-FanController-CPL.csv`

If any expected file is missing, report which one and suggest re-running.

---

## Step 4 — Commit the Gerbers

```powershell
cd $repo
git add hardware/gerbers/
git commit -m "hw(gerbers): regenerate fab files for <JLCPCB|PCBWay>

DRC: 0 errors before export.
Board: PoE-FanController daughter board v3.1.0 (42x78mm)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

---

## Quality Rules

- **Never export without a passing DRC gate** (0 severity=error violations).
- Always use the full KiKit path — `kikit` is not on the system PATH.
- If KiKit crashes (e.g. during JLCPCB BOM generation due to missing field),
  fall back to `kicad-cli pcb export gerbers` for plain Gerbers.
- Report the output directory path and file count to the user after export.
- Commit Gerbers to the repository so they are version-controlled alongside the PCB.
