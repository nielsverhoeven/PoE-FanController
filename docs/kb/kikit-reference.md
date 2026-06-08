# KiKit Reference

<!-- Last updated: 2026-06-08 (session 3) | KiKit 1.8.0 + KiCad 10.0.3 -->
<!-- Source: live testing on this machine + https://github.com/yaqwsx/KiKit -->

---

## 1. Installation

KiKit 1.8.0 is installed in **KiCad's Python environment** (not system Python).

| Item | Value |
|---|---|
| Version | **1.8.0** |
| CLI executable | `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\Scripts\kikit.exe` |
| Python module | `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\Lib\site-packages\kikit\` |
| KiCad Python | `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe` |

> ⚠️ `kikit` is NOT on the system PATH. Always use the full path to `kikit.exe` above,
> or run via KiCad Python: `& "C:\...\KiCad\10.0\bin\Scripts\kikit.exe" <command>`

---

## 2. What KiKit CAN Do (for this project)

### 2.1 Gerber Export
```powershell
$kikit = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\Scripts\kikit.exe"
& $kikit export gerber hardware/kicad/PoE-FanController.kicad_pcb hardware/gerbers/
```
Alternative to `kicad-cli pcb export gerbers`. Exports all standard Gerber layers.

### 2.2 Manufacturing Data Export (JLCPCB / PCBWay)
```powershell
# JLCPCB — produces Gerbers + drill + BOM + centroid in one bundle
& $kikit fab jlcpcb hardware/kicad/PoE-FanController.kicad_pcb jlcpcb-output/

# PCBWay
& $kikit fab pcbway hardware/kicad/PoE-FanController.kicad_pcb pcbway-output/
```
**Very useful for production** — generates exactly the files each fab house needs.

### 2.3 Silkscreen / Reference Visibility
```powershell
# Hide all references matching pattern
& $kikit modify references --hide "J*" hardware/kicad/PoE-FanController.kicad_pcb output.kicad_pcb

# Show values
& $kikit modify values --show hardware/kicad/PoE-FanController.kicad_pcb output.kicad_pcb
```

### 2.4 Panelization (future — for production runs)
```powershell
& $kikit panelize --help
```
Creates panelized boards for batch fabrication. Not needed for single-unit prototypes.

### 2.5 Stencil Generation (future)
```powershell
& $kikit stencil create hardware/kicad/PoE-FanController.kicad_pcb output/
```
Generates solder paste stencil files.

### 2.6 S-expression File Manipulation (advanced)
KiKit includes a `sexpr` module for direct parsing of `.kicad_sch` / `.kicad_pcb` files:
```python
from kikit.sexpr import parseSexprF, findNode, SExpr
with open('hardware/kicad/PoE-FanController.kicad_pcb', 'r') as f:
    tree = parseSexprF(f)
# Navigate and modify tree nodes, then write back
```
Useful for surgical file edits without loading the full pcbnew board object.

---

## 3. What KiKit CANNOT Do (important limitations)

| Capability | Status | Alternative |
|---|---|---|
| **Trace routing / autorouting** | ❌ Not in KiKit | KiCad GUI interactive router; or pcbnew PCB_TRACK API (see §5) |
| **DRC** | ❌ **Crashes on KiCad 10.0** (API incompatibility — `WriteDRCReport` signature changed) | Use `kicad-cli pcb drc` |
| Schematic editing | ❌ `eeschema` module is KiCad 5/6 format only — incompatible with v7+ `.kicad_sch` | Use our `hardware/generator/` package |
| Component placement | ❌ (only ref/value visibility, not position) | Use pcbnew Python API |
| ERC | ❌ Not provided | Use `kicad-cli sch erc` |

### KiKit DRC crash (KiCad 10.0 incompatibility)
```
Windows fatal exception: access violation
pcbnew.py line 9949: WriteDRCReport(aBoard, aFileName, aUnits, aReportAllTrackErrors)
TypeError: in method 'WriteDRCReport', argument 4 of type 'bool'
```
**Root cause:** KiCad 10.0 changed `pcbnew.WriteDRCReport()` signature. KiKit 1.8.0 was
written for KiCad 7/8. The DRC command crashes with an access violation.
**Fix:** Always use `kicad-cli pcb drc` for DRC — it is reliable.

---

## 4. KiKit CLI Quick Reference

```powershell
$kikit = "C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\Scripts\kikit.exe"

# Show all commands
& $kikit --help

# DRC (BROKEN on KiCad 10 — use kicad-cli instead)
# & $kikit drc run --level warning --useMm hardware/kicad/...

# Gerber export
& $kikit export gerber BOARDFILE [OUTPUTDIR]

# Fab house bundles
& $kikit fab jlcpcb BOARDFILE OUTPUTDIR
& $kikit fab pcbway BOARDFILE OUTPUTDIR

# Panelize
& $kikit panelize --help

# Stencil
& $kikit stencil create BOARDFILE OUTPUTDIR

# Modify silkscreen
& $kikit modify references --hide "PATTERN" BOARDFILE OUTPUTFILE
& $kikit modify values --show BOARDFILE OUTPUTFILE
```

---

## 5. Trace Routing — Programmatic Approach (pcbnew API)

KiKit does NOT route traces. Options for programmatic routing:

### Option A: pcbnew PCB_TRACK API (manual, surgical)
```python
import sys
sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

board = pcbnew.LoadBoard('C:/path/to/PoE-FanController.kicad_pcb')
board.BuildConnectivity()

def mm(x): return pcbnew.FromMM(x)

# Create a trace segment
track = pcbnew.PCB_TRACK(board)
track.SetLayer(pcbnew.F_Cu)
track.SetWidth(mm(0.25))  # 0.25mm signal trace
track.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
track.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
track.SetNet(board.FindNet('NET_NAME'))  # assign to net
board.Add(track)

board.BuildConnectivity()
board.Save('C:/path/to/PoE-FanController.kicad_pcb')
```

### ⚠️ CRITICAL PREREQUISITE: Netlist must be imported first
The PCB currently has **0 net assignments** (only GND net found — all others missing).
Before routing can begin:
1. Open `PoE-FanController.kicad_pcb` in KiCad GUI
2. Run **Tools → Update PCB from Schematic** (F8)
3. This imports the netlist (+5V, +12V, FAN1_PWM, FAN1_TACH, etc.) from the schematic
4. After import, the ratsnest (unrouted connections) will be visible
5. THEN scripted routing or interactive routing can begin

Without this step, `board.FindNet('FAN1_PWM')` returns `None` and traces cannot be assigned to nets.

### Option B: FreeRouting autorouter
1. Export DSN (Specctra session) from KiCad: **File → Export → Specctra DSN**
2. Run FreeRouting: https://github.com/freerouting/freerouting
3. Import back the routed `.ses` file: **File → Import → Specctra Session**
Not scripted, but handles complex routing automatically.

### Option C: KiCad Interactive Router (recommended)
Open the PCB in KiCad GUI and use the interactive router (X key). Supports push-and-shove.
This is the most reliable method for a 42×78mm board with 12 signal nets.

---

## 6. Recommended Workflow for This Project

| Task | Tool | Notes |
|---|---|---|
| Schematic regeneration | `python hardware/generate_project.py` | Always use this — never edit .kicad_sch |
| ERC | `kicad-cli sch erc ...` | 0 errors baseline |
| PCB component placement | pcbnew Python API | surgical, use forward slashes |
| **Netlist import** | **KiCad GUI: F8 (Update PCB from Schematic)** | **Must do before routing** |
| **Trace routing** | **KiCad GUI interactive router** | **Only option for complex routing** |
| DRC | `kicad-cli pcb drc ...` | 4 silk warnings baseline |
| Gerber export | `kikit fab jlcpcb ...` | OR `kicad-cli pcb export gerbers` |
| Manufacturing bundle | `kikit fab jlcpcb/pcbway ...` | Best for sending to fab |

---

## 7. KiKit Module Reference

| Module | Purpose | Works on KiCad 10? |
|---|---|---|
| `kikit.drc` | Programmatic DRC | ❌ Crashes (WriteDRCReport API mismatch) |
| `kikit.eeschema` | Schematic parsing | ❌ KiCad 5/6 format only |
| `kikit.sexpr` | S-expression parser | ✅ Works — useful for file surgery |
| `kikit.panelize` | Board panelization | ✅ (untested for this project) |
| `kikit.export` | Gerber/DXF export | ✅ |
| `kikit.fab` | Fab house bundles | ✅ |
| `kikit.stencil` | Paste stencil | ✅ |
| `kikit.modify` | Ref/value visibility | ✅ |
| `kikit.pcbnew_utils` | pcbnew helpers | ✅ (thin wrappers) |
| `kikit.substrate` | Board geometry | ✅ |
