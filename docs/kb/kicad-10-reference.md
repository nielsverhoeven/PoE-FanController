# KiCad 10 Reference

<!-- Last updated: 2026-06-07 | Source: session experience + KiCad 10.0.3 -->
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
| Docker CI (KiCad 10.0.2) | 67 | 34 lib_footprint_issues + 28 solder_mask_bridge + 5 silk_edge_clearance |

**Docker is authoritative for CI.** Baseline in `hardware-check.yml` = 67.
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
- ESP32-P4-MINI-1U custom footprint: `ESP32-P4-MINI-1.kicad_mod` (must be authored from Espressif datasheet)
- LAN8720A: use standard `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` ✅

---

## 9. Generator Script

**Source of truth:** `hardware/generate_project.py`
- Regenerates `.kicad_sch` and `.kicad_pcb` from scratch
- Manual edits to KiCad files are **forbidden** (overwritten on next run)
- Run: `cd hardware && python3 generate_project.py`
- CI runs: `KICAD_FP_BASE=/usr/share/kicad/footprints python3 generate_project.py`
- Syntax check: `python -m py_compile hardware/generate_project.py`
