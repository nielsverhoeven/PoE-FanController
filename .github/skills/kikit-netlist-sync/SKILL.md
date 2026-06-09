# Skill: kikit-netlist-sync

Synchronise net assignments from the KiCad schematic into the PCB file using
the pcbnew Python API. This is the scripted equivalent of **KiCad GUI →
Tools → Update PCB from Schematic (F8)**.

Use when the schematic has changed (e.g. a pin's net was reassigned in
`hardware/generator/components.py` and the schematic was regenerated) and the
PCB pads need to reflect those new net names.

**Trigger phrases:** "sync netlist", "update PCB from schematic", "netlist sync",
"apply netlist", "F8", "run netlist sync"

---

## Environment Constants

```powershell
$kicadPy  = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe"
$kicadCli = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
$pcb      = "C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb"
# NOTE: always forward slashes in $pcb — backslashes cause pcbnew unicode errors
```

---

## How It Works

KiCad's GUI "Update PCB from Schematic (F8)" performs three things:
1. Adds/removes footprints to match schematic component list
2. Updates net names on every pad to match the schematic netlist
3. Updates reference/value text on footprints

This skill handles **step 2 only** (net reassignment on existing pads) via
the pcbnew Python API. Use the implementer agent or KiCad GUI for steps 1 and 3
if footprints were added or removed.

---

## Step 1 — Audit current pad nets (before changing anything)

```powershell
& $kicadPy -c "
import sys; sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew
board = pcbnew.LoadBoard('$pcb')
board.BuildConnectivity()
# Print all pads for a given reference — change 'J8' as needed
ref = 'J8'
fp = board.FindFootprintByReference(ref)
if not fp:
    print(f'ERROR: {ref} not found')
else:
    for pad in sorted(fp.Pads(), key=lambda p: int(p.GetNumber()) if p.GetNumber().isdigit() else 0):
        print(f'  pad {pad.GetNumber():>3}: {pad.GetNetname()!r}')
" 2>&1
```

---

## Step 2 — Apply net reassignments

Replace the pad number / net name mappings in the script below with the
actual changes required. The example reflects issue #137 (pin 39→NC,
pin 40→+5V):

```powershell
& $kicadPy -c "
import sys; sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

PCB = '$pcb'
board = pcbnew.LoadBoard(PCB)
board.BuildConnectivity()

# --- Define reassignments: {pad_number: net_name} ---
# Use '' (empty string) for no-connect / unconnected
CHANGES = {
    'J8': {
        '39': '',      # was +5V (VSYS) -> unconnected
        '40': '+5V',   # was unconnected -> VBUS (5V source)
    }
}

for ref, pad_map in CHANGES.items():
    fp = board.FindFootprintByReference(ref)
    if not fp:
        print(f'ERROR: {ref} not found — skipping')
        continue
    for pad in fp.Pads():
        pn = pad.GetNumber()
        if pn not in pad_map:
            continue
        target_net_name = pad_map[pn]
        old_name = pad.GetNetname()
        net = board.FindNet(target_net_name)
        if net is None and target_net_name != '':
            print(f'ERROR: net {target_net_name!r} not found in PCB — run ERC/regenerate schematic first')
            continue
        pad.SetNet(net if net else board.FindNet(''))
        print(f'{ref} pad {pn}: {old_name!r} -> {target_net_name!r}')

board.BuildConnectivity()
board.Save(PCB)
print('Saved:', PCB)
" 2>&1
```

---

## Step 3 — Verify the change took effect

```powershell
& $kicadPy -c "
import sys; sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew
board = pcbnew.LoadBoard('$pcb')
board.BuildConnectivity()
fp = board.FindFootprintByReference('J8')
for pad in sorted(fp.Pads(), key=lambda p: int(p.GetNumber()) if p.GetNumber().isdigit() else 0):
    pn = pad.GetNumber()
    if pn in ['39', '40']:   # adjust to pads of interest
        print(f'  pad {pn}: {pad.GetNetname()!r}')
" 2>&1
```

---

## Step 4 — Run DRC to confirm no new errors

```powershell
cd C:\repos-github\PoE-FanController
& $kicadCli pcb drc `
  --output hardware/kicad/drc_result.rpt `
  hardware/kicad/PoE-FanController.kicad_pcb 2>&1 | Select-Object -Last 5

$drc = Get-Content hardware\kicad\drc_result.rpt
$errors  = ($drc | Select-String "severity=error").Count
$warnings= ($drc | Select-String "severity=warning").Count
Write-Host "DRC: $errors errors, $warnings warnings"
```

**Accept:** 0 errors. Silk warnings and unconnected items (pre-routing
ratsnest) are acceptable as long as the count does not increase vs the
baseline (0 errors, ≤16 silk warnings, 70 unconnected).

---

## Step 5 — Commit

```powershell
cd C:\repos-github\PoE-FanController
git add hardware/kicad/PoE-FanController.kicad_pcb hardware/kicad/drc_result.rpt
git commit -m "hw(pcb): sync netlist — <describe net changes>

DRC: 0 errors, N silk warnings, 70 unconnected (pre-existing ratsnest).

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

---

## When to Use This Skill vs Full F8 in GUI

| Scenario | Use this skill | Use KiCad GUI F8 |
|---|---|---|
| Only net assignments changed (pin→net mapping) | ✅ | optional |
| Footprints added or removed | ❌ | ✅ required |
| Component references/values changed | ❌ | ✅ required |
| Full schematic regenerated (`generate_project.py`) with only net changes | ✅ | optional |

---

## Quality Rules

- **Forward slashes only** in the PCB path passed to pcbnew.
- Always call `board.BuildConnectivity()` before **and** after net changes.
- Always call `board.Save(PCB)` — changes are in-memory until saved.
- If `board.FindNet(name)` returns `None` for a non-empty name, the net
  doesn't exist in the PCB yet — regenerate the schematic and recheck.
- Run DRC after every sync and report the delta vs baseline.
