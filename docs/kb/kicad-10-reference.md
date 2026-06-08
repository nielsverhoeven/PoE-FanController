# KiCad 10 Reference

<!-- Last updated: 2026-06-07 (session 2) | Source: session experience + KiCad 10.0.3 -->
<!-- Verified against: KiCad 10.0.3 (Windows), kicad/kicad:10.0.2 (Docker/Linux) -->

---

## 1. File Format Versions (use these exactly)

```
kicad_sch  → version 20260101   generator_version "10.0"
kicad_pcb  → version 20260206   generator_version "10.0"
```
Mismatched versions cause "older version" warnings in KiCad GUI.

---

## 2. Global Label S-expression (VERIFIED — use this exact format)

```sexp
(global_label "SIGNAL_NAME"
  (shape input|output|bidirectional|passive)
  (at X Y ANGLE)
  (fields_autoplaced yes)
  (effects (font (size 1.27 1.27)) (justify left))
  (uuid "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
  (property "Intersheetrefs" "${INTERSHEET_REFS}"
    (at X Y ANGLE)
    (effects (font (size 1.27 1.27)) (justify left) (hide yes)))
)
```

### CRITICAL rules — violations cause schematic load failure
- **NO** `(pin "~" ...)` element inside global_label
- **NO** `(justify left bottom)` — `bottom` is invalid on global_label (valid only on `label`)
- **MUST** have `fields_autoplaced yes`
- **MUST** have `Intersheetrefs` property

### Shape selection
| Signal direction | shape |
|---|---|
| Signal source / driver | `output` |
| Signal receiver / sink | `input` |
| Bidirectional bus | `bidirectional` |
| Power / GND | `passive` |

---

## 3. Power Symbol S-expression (VERIFIED)

```sexp
(symbol "POWER_NET" (power) (pin_names (offset 0)) (in_bom no) (on_board no)
  (property "Reference" "#PWR" (at 0 -3 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (property "Value" "POWER_NET" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
  (symbol "POWER_NET_0_1"
    (pin power_out line (at 0 -3.81 90) (length 0)
      (name "~" (effects (font (size 0 0))))
      (number "1" (effects (font (size 0 0)))))
  )
)
```
- Use `pin_type="power_out"` as default — eliminates `power_pin_not_driven` ERC errors
- GND power symbols: use `power_in` type (receives GND net)
- `define_power()` in generate_project.py registers a lib_sym once — call order matters

---

## 4. ERC Results — Known Baselines

| Environment | Tool version | ERC errors | ERC warnings | Notes |
|---|---|---|---|---|
| Windows local | KiCad 10.0.3 | 0 | 85–86 | `lib_symbol_issues` warnings are benign |
| Docker CI | kicad/kicad:10.0.2 | 0 | ~120 | More warnings due to version differences |

**Gate:** ERC must exit with 0 severity=`error` violations. Warnings are acceptable.

### Known benign ERC warnings
- `lib_symbol_mismatch` / `lib_symbol_issues` — custom symbols differ from KiCad stdlib version
- `pin_not_connected` on VPORT pins of Ag9905M — by design (PoE module abstraction)
- `power_pin_not_driven` — eliminated by using `pin_type="power_out"` on power symbols

---

## 5. DRC Results — Known Baselines

| Environment | Violations | Breakdown |
|---|---|---|
| Windows local (KiCad 10.0.3) | 36 | 28 solder_mask_bridge (J6) + 5 silk_edge_clearance + 2 lib_footprint_mismatch (J1,J7) + 1 lib_footprint_issues (U3 Custom) |
| Docker CI (KiCad 10.0.2) | 76 | 43 lib_footprint_issues + 28 solder_mask_bridge + 5 silk_edge_clearance |

**Docker is authoritative for CI.** Baseline in `hardware-check.yml` = 76.

### Why lib_footprint_issues count = number of BOM components (CRITICAL to understand)

Docker's `fp-lib-table` does NOT list any standard footprint library. Every footprint in the PCB
generates exactly **1 `lib_footprint_issues` violation** with description:
`"The current configuration does not include the footprint library 'X'"`

**Rule:** Adding N new BOM components adds N to the Docker DRC violation count.
- ESP32-P4 migration added 9 new components (U5, R11–R14, C8–C11): baseline 67 → 76
- Always update the baseline in `hardware-check.yml` when adding new BOM components
- **Fix tracked in issue #39:** Add `fp-lib-table` pointing to Docker paths → eliminates all violations

DRC must not exceed baseline. Driving to zero is tracked in issue #39.

### Critical: Docker generator must succeed

If `generate_project.py` crashes in Docker (e.g. footprint not in Docker's library), DRC runs
on the **committed** (Windows-generated) PCB instead. The 10.0.3-embedded footprints differ from
10.0.2 → many more `lib_footprint_issues` than the 34 baseline (typically 43+ for feature branches
adding new components). **Always use footprints confirmed in Docker 10.0.2** for PCB `embed_footprint`
calls to ensure the generator succeeds and Docker DRC uses the freshly-generated PCB.

### Footprints confirmed in Docker kicad/kicad:10.0.2

**Safe (confirmed):**
- `Connector_RJ:RJ45_Hanrun_HR911105A_Horizontal` ✅
- `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` ✅
- `Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical` ✅
- `Resistor_SMD:R_0402_1005Metric` ✅
- `Capacitor_SMD:C_0402_1005Metric` ✅
- `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` ✅

**Avoid (may not exist in 10.0.2):**
- `Connector_RJ:RJ45_Amphenol_54602-x08_Horizontal` ⚠️ (present in 10.0.3 local, uncertain in Docker)

### 0402 component placement constraints (verified against DRC)

R_0402 and C_0402 footprints:
- Courtyard half-width (X): 0.86 mm
- Pad half-width (X): ~0.52 mm (pad2 right edge ≈ center+0.48, pad1 left edge ≈ center-0.51)

Minimum X spacing between adjacent 0402s at same Y:
- Centre-to-centre ≥ 2.0 mm to avoid courtyard overlap
- Centre-to-centre ≥ 1.2 mm to avoid copper clearance violation (0.2 mm required)
- Practical rule: use ≥ 2.0 mm centre-to-centre for any co-planar 0402 pair

---

## 6. kicad-cli Commands (Docker)

```bash
# ERC — do NOT use --exit-code-violations (exits non-zero for warnings)
kicad-cli sch erc hardware/kicad/PoE-FanController.kicad_sch \
  --output hardware/kicad/erc_output.json --format json || true

# DRC — use || true; let Python gate enforce baseline
kicad-cli pcb drc hardware/kicad/PoE-FanController.kicad_pcb \
  --output hardware/kicad/drc_output.json --format json --exit-code-violations || true
```

**Local Windows path:** `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe`

---

## 7. Schematic Conventions (P-SCH-01 through P-SCH-05)

| Rule | Description |
|---|---|
| P-SCH-01 | All inter-block signals use `global_label` (never plain wire crossing) |
| P-SCH-02 | Section headers: blue bold 2.54mm text, no ASCII decoration |
| P-SCH-03 | Primary side GND = `GND_PRI`; secondary (SELV) side = `GND` |
| P-SCH-04 | Power symbols must drive their net (`pin_type="power_out"`) |
| P-SCH-05 | Component pin types: match signal direction (`input`/`output`/`passive`) |

---

## 8. Custom Footprint Location

```
hardware/kicad/footprints/Custom.pretty/
```
- ESP32-P4-MINI-1U custom footprint: `ESP32-P4-MINI-1.kicad_mod` — 56 pads, see §10 for pin mapping
- LAN8720A: use standard `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` ✅
- RJ45: `Custom:RJ45_Wuerth_615008144521` — custom footprint in Custom.pretty

### fp-lib-table — REQUIRED for custom footprints

Every KiCad project must have `hardware/kicad/fp-lib-table` to register Custom.pretty.
**Without it, any `Custom:` footprint generates "Cannot add XN (footprint not found)" in Update PCB.**

```sexp
(fp_lib_table
  (version 7)
  (lib (name "Custom")(type "KiCad")(uri "${KIPRJMOD}/footprints/Custom.pretty")(options "")(descr "Custom project footprints")))
```

`${KIPRJMOD}` resolves to the directory containing the `.kicad_pro` file (i.e. `hardware/kicad/`).

---

## 9. Symbol Pin Number ↔ Footprint Pad Number — CRITICAL RULE

**KiCad matches symbol pins to footprint pads by NUMBER, not by name.**

When you run "Update PCB from Schematic":
- KiCad looks at each footprint pad number (e.g. `"1"`, `"TXEN"`, `"A1"`)
- It searches the symbol for a pin whose **number** (second field in the pin tuple) matches exactly
- **If no match: "No net found for component X pad Y (no pin Y in symbol)"** → pad gets no net → chip is non-functional on PCB

### Consequences of mismatch
- Using functional names as pin numbers (e.g. `"G4"`, `"TXEN"`) when the footprint uses `"1"`, `"2"` etc. → ALL pads unconnected
- Every chip shows 100% of pads as "no net" — board is completely non-functional
- The generator MUST use the actual pad numbers from the footprint as the symbol's pin number field

### Rule for generator
In `s.define(...)` calls:
```python
# WRONG — functional name as pin number:
("GPIO4", "G4", "output")    # pin name="GPIO4", pin number="G4"

# CORRECT — actual footprint pad number:
("GPIO4", "6", "output")     # pin name="GPIO4", pin number="6" (matches footprint pad "6")
```

### Handling multi-pad chips (all pads must be in symbol)
- Every footprint pad must have a matching symbol pin
- Unused pads: add as `("NC", "pad_number", "no_connect")` — no wire needed, prevents warnings
- Multiple GND pads: each must have a unique pin number, can share net via schematic wires

---

## 10. Generator Script

**Source of truth:** `hardware/generate_project.py` (thin wrapper over `hardware/generator/` package)
- Regenerates `.kicad_sch` and `bom.csv` only — **never writes `.kicad_pcb`** (P-KI-07)
- Run: `cd hardware && python3 generate_project.py`
- CI runs: `KICAD_FP_BASE=/usr/share/kicad/footprints python3 generate_project.py`
- Syntax check: `python -m py_compile hardware/generate_project.py`

### Generator package structure
```
hardware/
  generate_project.py     # thin entry point (≤40 lines)
  generator/
    __init__.py           # re-exports build_schematic, write_bom
    utils.py              # constants, _uuid, snap, _pt, write_pro
    schematic.py          # class Schematic (S-expression builder)
    components.py         # build_schematic() — ALL component placement logic
    pcb_utils.py          # embed_footprint(), embed_custom_footprint() (P-KI-07 compliant)
    bom.py                # write_bom()
```

---

## 11. ESP32-P4-MINI-1U Physical Pad Mapping (BEST ESTIMATE — verify vs Espressif HW Design Guide)

The custom `ESP32-P4-MINI-1.kicad_mod` footprint has 56 pads numbered 1–56:

| Physical position | Pads | Assigned signals |
|---|---|---|
| Bottom row, left→right | 1–20 | 1=GND, 2=GPIO0, 3=NC, 4=GPIO2, 5=NC, 6–13=GPIO4–11, 14–17=NC, 18=GPIO16, 19=NC, 20=VDD |
| Right column, bottom→top | 21–28 | 21–27=NC, 28=GND |
| Top row, right→left | 29–48 | 29–32=NC, 33=GPIO28, 34–35=NC, 36=GPIO31, 37=GPIO32, 38=GPIO33, 39=GPIO34, 40=GPIO35, 41=GPIO36, 42=GPIO37, 43=GPIO38, 44=GPIO39, 45–47=NC, 48=GND |
| Left column, top→bottom | 49–56 | 49–54=NC, 55=GPIO50, 56=EN |

⚠️ **This mapping is a generator best-estimate.** Verify against Espressif ESP32-P4-MINI-1U Hardware Design Guide before PCB fabrication.

---

## 12. LAN8720A QFN-24 Pin Numbering (VERIFIED — Microchip DS00001913C)

| Pin | Signal | Notes |
|---|---|---|
| 1 | TXEN | TX enable (input from MAC) |
| 2 | TXD[1] | TX data bit 1 |
| 3 | TXD[0] | TX data bit 0 |
| **4** | **RBIAS** | **Requires 6.04 kΩ to GND — MANDATORY for operation** |
| 5 | RXD[0] | RX data bit 0 |
| 6 | RXD[1] | RX data bit 1 |
| 7 | CRS_DV | Carrier sense / data valid |
| 8 | RXERR | RX error (can be NC in simple designs) |
| 9 | CLKOUT | 50 MHz REF_CLK output → ESP32-P4 GPIO50 |
| 10 | nINTSEL | Pull to 3.3V (no interrupt in our design) |
| 11 | LED2/nINTSEL | Pull to 3.3V → MODE[1]=1 (100BASE-TX full-duplex) |
| 12 | LED1/REGOFF | Pull to 3.3V → MODE[0]=1 |
| 13 | MDIO | Management data I/O |
| 14 | MDC | Management data clock |
| 15 | nRST | Active-low reset |
| 16 | GND | LDO ground |
| 17 | VDD33A | Analog 3.3V supply |
| 18 | VDD33D | Digital 3.3V supply |
| 19 | VDDIO | I/O 3.3V supply |
| 20 | MDIP (TX+) | MDI transmit positive |
| 21 | MDIN (TX−) | MDI transmit negative |
| 22 | MDIP (RX+) | MDI receive positive |
| 23 | MDIN (RX−) | MDI receive negative |
| 24 | GND | Analog ground |
| EP (25) | GND | Exposed pad (must connect to GND plane) |

### Missing RBIAS — design-critical
Without RBIAS (6.04 kΩ from pin 4 to GND), the LAN8720A internal current reference is broken and the chip will not operate. Currently implemented as **R15** in the schematic.

---

## 13. USB-C GCT USB4085 Pad Numbering

All pads in the `Connector_USB:USB_C_Receptacle_GCT_USB4085` footprint must be in the symbol:

| Pad | Signal | Notes |
|---|---|---|
| A1, A12, B1, B12 | GND | 4× GND pads — all must connect to GND net |
| A4, A9, B4, B9 | VBUS | 4× VBUS pads — all must connect to VBUS net |
| A5 | CC1 | Configuration channel 1 |
| A6, B7 | D+ | USB data positive (both sides) |
| A7, B6 | D− | USB data negative (both sides) |
| A8, B8 | SBU1/SBU2 | Sideband use — NC in USB 2.0 only designs |
| B5 | CC2 | Configuration channel 2 |
| SH | Shield | Connect to GND or chassis |

---

## 14. CI Docker Constraints

### `git diff` does not work inside kicad/kicad:10.0.2 container
The Docker container has no git repo context. `git diff --exit-code` exits with:
`"Not a git repository. Use --no-index to compare two paths outside a working tree"`

**Fix:** Use `sha256sum` for file integrity checks in CI:
```yaml
- name: Store PCB checksum (P-KI-07 guard baseline)
  run: sha256sum hardware/kicad/PoE-FanController.kicad_pcb > /tmp/pcb_before.sha256

- name: Guard — kicad_pcb must not be modified by generator (P-KI-07)
  run: |
    sha256sum --check /tmp/pcb_before.sha256 || \
      (echo "ERROR: P-KI-07 violation — kicad_pcb modified by generator" && exit 1)
```

### DRC baseline formula (Docker authoritative)
`baseline = count(unique footprints in BOM)`  — one `lib_footprint_issues` per footprint in Docker  
Current baseline: **76** (post ESP32-P4 migration + RBIAS R15 = 77 if R15 adds a new footprint type)
Update `hardware-check.yml` whenever new BOM components are added.

---

## 15. pcbnew Python API — Surgical PCB Edits (Windows)

Use when the KiCad GUI is not available but targeted changes are needed (board resize, component repositioning). Always prefer KiCad GUI for routing.

```python
import sys
sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

board = pcbnew.LoadBoard('C:/path/to/PoE-FanController.kicad_pcb')

# Coordinates in nanometres — always use FromMM()
def mm(x): return pcbnew.FromMM(x)

# Replace Edge.Cuts with new board outline
for d in list(board.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts:
        board.Delete(d)

seg = pcbnew.PCB_SHAPE(board)
seg.SetShape(pcbnew.SHAPE_T_RECT)
seg.SetStart(pcbnew.VECTOR2I(mm(0), mm(0)))
seg.SetEnd(pcbnew.VECTOR2I(mm(42), mm(78)))
seg.SetLayer(pcbnew.Edge_Cuts)
seg.SetWidth(mm(0.05))
board.Add(seg)

# Move a footprint
fp = board.FindFootprintByReference('J8')
fp.SetPosition(pcbnew.VECTOR2I(mm(10.50), mm(28.80)))
fp.SetOrientationDegrees(90)   # 90° rotation for J8 (runs along board height)

# ALWAYS call both before saving
board.BuildConnectivity()
board.Save('C:/path/to/PoE-FanController.kicad_pcb')
```

### Critical gotchas
- **Forward slashes only in file paths** — backslashes cause unicode errors in pcbnew
- `board.BuildConnectivity()` is mandatory before `board.Save()`
- `SetOrientationDegrees(90)` — positive angle = CCW in KiCad's coordinate system
- For J8 (2×20, 15.38mm row spacing, runs vertically): place at (10.50, 28.80)mm, rotate 90°

---

## 16. Custom Footprint Generation Pattern

When a connector has non-standard row spacing (e.g. J8's 15.38mm), generate the `.kicad_mod` file programmatically.

**Template:** see `hardware/generator/gen_footprint_j8.py`

Key parameters for `PinSocket_2x20_P2.54mm_P15.38mm_Vertical`:
```python
PITCH = 2.54          # pin-to-pin within a row
ROW_SPACING = 15.38   # between the two rows (= 21.00 - 2*2.81 for Waveshare ESP32-P4-POE-ETH)
N_POS = 20            # positions per row (40 pads total)
PAD_SIZE = 1.7        # pad diameter (mm)
DRILL = 1.0           # drill diameter (mm)

row1_y = -ROW_SPACING / 2  # -7.69 mm
row2_y =  ROW_SPACING / 2  # +7.69 mm
x_start = -(N_POS - 1) / 2.0 * PITCH  # -24.13 mm (centre at x=0)
```

Pad numbering convention:
- Odd pads (1,3,5,...,39): row 1 at `y = row1_y`
- Even pads (2,4,6,...,40): row 2 at `y = row2_y`
- Pin 1 and pin 2 use `shape="rect"` (orientation marker); all others `shape="circle"`

Always output with `newline="\n"` (not Windows CRLF) and add to `Custom.pretty/`.

### J8 PCB placement (daughter board constitution v3.1.0)
- Footprint: `Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical`
- PCB origin: X=10.50mm, Y=28.80mm (centre between rows, centre of pin span)
- Rotation: 90° (so pin span runs along board Y=4.67..52.93mm)
- After 90° rotation: row1 at X=2.81mm, row2 at X=18.19mm from board left edge ✓

---

## 17. DRC Baseline — Current (v3.1.0, daughter board, 0 routing)

| Environment | Violations | Breakdown |
|---|---|---|
| Windows local KiCad 10.0.3 | **4** | 2× silk_overlap (title text near J5), 2× silk_over_copper (J8 pin-1 marker clipped by mask) |
| All violations | **severity=warning** | 0 errors, 0 unconnected — safe to proceed |

**CI threshold:** ≤5 violations (set in `.github/workflows/hardware-check.yml`)
