---
name: update-ratnests
description: >
  Update PCB ratsnest (pad-to-net assignments) after a schematic net change.
  Covers the complete workflow: fix components.py → regenerate schematic →
  export netlist → import nets into PCB → verify. Use when asked to
  'update ratnests', 'sync nets to PCB', 'apply schematic changes to PCB',
  'ratsnest is wrong', or after any pin/net reassignment in components.py.
allowed-tools: shell
---

## Purpose

After any net assignment change in `hardware/generator/components.py`
(e.g. swapping which J8 pin carries DHT11_DATA, PROBE_LED, FAN1_PWM, etc.),
the PCB pad-to-net table must be resynchronised so the ratsnest reflects the
new wiring. This skill documents the authoritative four-step workflow.

---

## Environment Constants

```powershell
$kicadPy  = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe"
$kicadCli = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
$repo     = "C:\repos-github\PoE-FanController"
$sch      = "$repo\hardware\kicad\PoE-FanController.kicad_sch"
$pcb      = "C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb"
$netlist  = "$repo\hardware\kicad\netlist.kicad_net"
# NOTE: always use forward slashes in $pcb — backslashes cause pcbnew unicode errors
```

---

## Step 1 — Edit `components.py`

Change the net name(s) on the affected J8 pins in the `s.define("Custom:J8_Waveshare", ...)`
block **and** update the corresponding `s.global_label(...)` call(s) in the placement
section at the bottom of `build_schematic()`.

**Always update both locations or the symbol pin and the schematic wire will disagree.**

Example — swap DHT11_DATA and PROBE_LED between J8 pins 10 and 11:

```python
# In s.define(...) pins_left list:
("DHT11_DATA",   "10", "input"),         # GPIO5  — DHT11 single-wire
("PROBE_LED",    "11", "output"),        # GPIO6  — probe health LED

# In global_label placement:
s.global_label("DHT11_DATA", *p["10"], shape="bidirectional", angle=180)
s.global_label("PROBE_LED",  *p["11"], shape="output",        angle=180)
```

Also update `firmware/include/pins.h` and `firmware/test/test_pins/test_pins.cpp`
when GPIO numbers change alongside the net reassignment.

---

## Step 2 — Regenerate Schematic

```powershell
cd $repo
python hardware/generate_project.py
```

Expected output: `wrote PoE-FanController.kicad_pro` and `wrote bom.csv` — no errors.

---

## Step 3 — Export Fresh Netlist

```powershell
& $kicadCli sch export netlist `
  --output "$repo\hardware\kicad\netlist.kicad_net" `
  "$repo\hardware\kicad\PoE-FanController.kicad_sch" 2>&1
```

Expected: exit code 0, no output (kicad-cli is silent on success).

---

## Step 4 — Import Nets into PCB

### Option A — Full import (recommended when multiple pads changed)

```powershell
& $kicadPy "$repo\hardware\generator\import_netlist.py" 2>&1
```

Expected output includes:
- `Signal nets from netlist: N pad-net entries`
- `Assigned: N`
- `Saved PCB: ...`
- `Unconnected ratsnest items: N`

> If `import_netlist.py` shows a warning about `sync_pcb_paths` at the end,
> ignore it — the nets are already saved before that step runs.

### Option B — Surgical patch (when only 1–3 pads need changing)

Use when the schematic was already imported and only a small targeted swap is needed:

```powershell
& $kicadPy -c "
import sys; sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

PCB = '$pcb'
board = pcbnew.LoadBoard(PCB)
board.BuildConnectivity()

CHANGES = {
    'J8': {
        '10': 'DHT11_DATA',   # example: was PROBE_LED -> now DHT11_DATA
        '11': 'PROBE_LED',    # example: was DHT11_DATA -> now PROBE_LED
    }
}

for ref, pad_map in CHANGES.items():
    fp = board.FindFootprintByReference(ref)
    if not fp:
        print(f'ERROR: {ref} not found'); continue
    for pad in fp.Pads():
        pn = pad.GetNumber()
        if pn not in pad_map: continue
        target = pad_map[pn]
        net = board.FindNet(target)
        if net is None and target:
            print(f'ERROR: net {target!r} not in PCB — run Step 2-3 first'); continue
        old = pad.GetNetname()
        pad.SetNet(net if net else board.FindNet(''))
        print(f'{ref} pad {pn}: {old!r} -> {target!r}')

board.BuildConnectivity()
board.Save(PCB)
print('Saved:', PCB)
" 2>&1
```

---

## Step 5 — Verify

```powershell
& $kicadPy -c "
import sys; sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew
board = pcbnew.LoadBoard('$pcb')
board.BuildConnectivity()
fp = board.FindFootprintByReference('J8')
for pad in sorted(fp.Pads(), key=lambda p: int(p.GetNumber()) if p.GetNumber().isdigit() else 0):
    pn = pad.GetNumber()
    net = pad.GetNetname()
    if net and net not in ('', 'unconnected'):
        print(f'  J8 pad {pn:>3}: {net}')
print('Unconnected:', board.GetConnectivity().GetUnconnectedCount(False))
" 2>&1
```

Check that the swapped pads show the correct net names. Unconnected count should
be stable (no increase vs baseline).

---

## Step 6 — Run DRC

```powershell
cd $repo
& $kicadCli pcb drc `
  --output hardware/kicad/drc_result.rpt `
  hardware/kicad/PoE-FanController.kicad_pcb 2>&1 | Select-Object -Last 3

$drc = Get-Content hardware\kicad\drc_result.rpt
$errors   = ($drc | Select-String "severity=error").Count
$warnings = ($drc | Select-String "severity=warning").Count
Write-Host "DRC: $errors errors, $warnings warnings"
```

Accept: 0 errors. Warnings are cosmetic.

---

## Step 7 — Update `import_netlist.py` POWER_NETS (if needed)

If the changed net is a **power net** (GND, +3V3, +5V, +12V) or one not exported
by the KiCad netlist (e.g. DS18B20_DATA, PROBE_LED on J8), update the `POWER_NETS`
dict in `hardware/generator/import_netlist.py` to match. Signal nets (FAN*_PWM,
FAN*_TACH, DHT11_DATA, etc.) come from the netlist automatically and do not need
a POWER_NETS entry.

---

## Decision Table

| How many pads changed? | Nets already in PCB? | Use |
|---|---|---|
| Many (full schematic regen) | No | Steps 1–4A–5–6 |
| Few (1–3 specific pads) | Yes | Step 4B only, then 5–6 |
| POWER_NETS involved | — | Also do Step 7 |

---

## Quality Rules

- Always call `board.BuildConnectivity()` **before and after** net changes.
- Always call `board.Save(PCB)` — changes are in-memory until saved.
- Always use **forward slashes** in the PCB path passed to pcbnew.
- If `board.FindNet(name)` returns `None`, the net doesn't exist in the PCB yet —
  run Steps 2–3 first (schematic regen + netlist export), then retry.
- DRC must show 0 errors after every ratsnest update.
- Commit the updated PCB and DRC report together.

---

## Commit Template

```powershell
cd $repo
git add hardware/kicad/PoE-FanController.kicad_pcb hardware/kicad/drc_result.rpt
git commit -m "hw(pcb): update ratsnest — <describe net changes>

Updated pad-to-net assignments for J8 pad(s) <N>: <old_net> -> <new_net>.
DRC: 0 errors, N warnings (cosmetic).

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```
