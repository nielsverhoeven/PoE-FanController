# PoE FanController — Copilot Instructions

<!-- Updated: 2026-06-14 -->

## Project Overview

**Two-board stack.** The Waveshare ESP32-P4-POE-ETH (SKU 32088) is the main board — it handles PoE 802.3at, Ethernet (LAN8720A), ESP32-P4, USB-C, and RJ45. The custom **daughter board** (42 × 78 mm portrait PCB) sits beneath it and provides: 5V→12V boost, 4× PWM fan headers, TACH pull-ups, DHT11/DS18B20 sensor, and status LEDs.

---

## Build & Test Commands

```powershell
# Firmware build (always python -m platformio, never bare pio)
python -m platformio run -e esp32-p4-eth

# Firmware unit tests (native, no hardware needed)
python -m platformio test -e native

# Run a single test filter
python -m platformio test -e native --filter test_fan

# Schematic + BOM regeneration (NEVER edit .kicad_sch directly)
python hardware/generate_project.py

# Generator syntax check (fast, no KiCad needed)
python -m py_compile hardware/generator/components.py

# ERC
C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe sch erc --output hardware/kicad/erc_output.json hardware/kicad/PoE-FanController.kicad_sch

# DRC
C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe pcb drc --output hardware/kicad/drc_output.json hardware/kicad/PoE-FanController.kicad_pcb

# pcbnew Python API (for surgical PCB edits via script)
C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe <script.py>
```

---

## Architecture

### Schematic Generation Pipeline

`hardware/generator/components.py` → `generate_project.py` → `hardware/kicad/PoE-FanController.kicad_sch`

- **`components.py`** is the sole source of truth for all schematic content and wiring. All component changes go here.
- **`.kicad_sch` is auto-generated** — never edit it by hand. CI guards this with a sha256 check.
- **`.kicad_pcb` is KiCad GUI only** — scripts must never write to it (P-KI-07). Use pcbnew Python API for surgical edits when GUI is unavailable.

### Custom Footprints

All custom footprints live in `hardware/kicad/footprints/Custom.pretty/`. Referenced as `Custom:<name>` in schematics. The `fp-lib-table` in `hardware/kicad/` registers the library path.

**⚠️ Critical:** KiCad `.kicad_mod` files do NOT support `;` semicolons as comments — semicolons cause the entire footprint to be silently rejected by KiCad's parser (file becomes non-enumerable).

### Firmware

All GPIO constants are defined via `build_flags` in `platformio.ini` and declared in `firmware/include/pins.h`. No magic numbers in source — always use the named constants.

---

## Critical Conventions

### J8 Connector — Pin Numbering

The 2×20 header uses **consecutive column numbering**, not PICO-style alternating.

```
Row A (pins  1–20): x = 2.81 mm from left board edge  (bottom → top)
Row B (pins 21–40): x = 18.19 mm from left board edge (bottom → top)
Pin 40 = VBUS (+5V) — power input for boost module
Pin 36 = +3V3 — sensor VCC and pull-up source
GND pins: 3, 8, 13, 18 (Row A) | 23, 28, 33, 38 (Row B)
FORBIDDEN: pins 25, 26 = EMAC_RXD1/RXD0 — must remain NC
```

Fan signal assignments (PWM on lower pin, TACH on higher — swapped 2026-06-14):

| Pin | GPIO | Signal |
|-----|------|--------|
| 21 | GPIO48 | FAN4_PWM |
| 22 | GPIO47 | FAN4_TACH |
| 24 | GPIO46 | FAN3_PWM |
| 25 | GPIO33 | FAN3_TACH |
| 31 | GPIO23 | FAN2_PWM |
| 32 | GPIO22 | FAN2_TACH |
| 34 | GPIO21 | FAN1_PWM |
| 35 | GPIO20 | FAN1_TACH |

### Board Design Rules (from board setup — enforced as DRC errors)

| Rule | Value |
|---|---|
| Min copper clearance | 0.2 mm |
| Min copper-to-edge | **1.0 mm** (stricter than KiCad default) |
| Min track width | 0.4 mm (signal) / **1.0 mm** (power) |
| Min drill | 0.6 mm |
| Courtyard overlap | error |
| Tracks crossing | error |
| Shorts (different nets) | error |
| Dangling track | warning only |

### ERC/DRC Gates (CI)

- **ERC:** zero `severity=error` violations required
- **DRC:** zero `severity=error` violations required, zero unconnected items
- **Current baseline (fully routed, 2026-06-14):** 0 errors, 0 unconnected, 8 warnings (cosmetic: pth_inside_courtyard × 2, silk_overlap × 1, silk_over_copper × 2, silk_edge_clearance × 1, lib_footprint × 2)
- CI uses Docker `kicad/kicad:10.0.2`; local uses KiCad 10.0.3 — minor violation count differences are expected

### J8 PCB Placement (authoritative, updated 2026-06-14)

- Position: **(41.0, 40.77) mm**, rotation 90°
- Previous position (pre-reshuffle): ~~(10.50, 28.80) mm~~ — **do not use**

### Schematic Generator Conventions

```python
# Pin angle: 0 = label extends RIGHT (right-side pins); 180 = extends LEFT (left-side pins)
# Wrong angle renders labels inside component body

# Pin type for power symbols — always power_out to avoid ERC errors:
("OUT+", "3", "power_out")   # drives the +12V rail

# All pads must match footprint pad numbers exactly — KiCad matches by NUMBER not name
```

### Boost Module (U_BOOST — Amazon B07RKDB2VP)

Physical LM2587 48×23mm module. **Pin layout is 2×2 corners, not a 1×4 row:**
```
IN+  (top-left,  pad 1)    OUT+ (top-right,  pad 3)
IN-  (bottom-left, pad 2)  OUT- (bottom-right, pad 4)
```
Both INs on LEFT, both OUTs on RIGHT. Courtyard: 50×25mm.

---

## Windows Tool Rules

This project runs on **Windows**. Always use:

| ❌ Don't | ✅ Do |
|---|---|
| `pio run` | `python -m platformio run` |
| `head -N file` | `Get-Content file \| Select-Object -First N` |
| `cat file` | `Get-Content file` (or use `view` tool) |
| `grep` | Use the built-in `grep` tool (ripgrep) |
| `which` | `where.exe` |
| `kicad-cli` | `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe` |
| `gh auth login --web` | Ask user for `GH_TOKEN` env var instead (blocks shell interactively) |

---

## Feature Development Pipeline

New features follow 7 stages managed by the `orchestrator` agent:

1. GitHub issue enrichment
2. Feature planning (`docs/features/<name>/spec.md`)
3. Architecture validation (constitution check)
4. Task breakdown (`docs/features/<name>/tasks.md`)
5. **Implementation** (schematic → ERC → BOM → PCB → DRC)
6. Testing
7. Documentation

**Always complete stages 2–4 before starting stage 5.** Constitution lives at `docs/constitution.md`.

---

## Key Files

| File | Purpose |
|---|---|
| `docs/constitution.md` | Authoritative technology choices and design rules |
| `hardware/generator/components.py` | All schematic wiring — the only file to edit for hardware changes |
| `firmware/include/pins.h` | GPIO pin constants with J8 pin cross-references |
| `docs/kb/kicad-10-reference.md` | KiCad format, pcbnew API, ERC/DRC baselines, board rules |
| `docs/kb/component-library.md` | Full BOM with MPNs and KiCad footprints |
| `docs/kb/ESP32-P4-POE-ETH/` | Waveshare board reference, pin layout images |
| `docs/kb/DC-DC-boost-module.md` | LM2587 boost module specs, pin layout, physical dimensions |
| `.github/agents/copilot-instructions.md` | Extended agent-specific instructions (AgentDB, model routing) |

---

## Model Routing

| Task | Model |
|---|---|
| Exploration, GitHub CRUD, CI checks | `claude-haiku-4.5` |
| Architecture, complex implementation, feature planning | `claude-sonnet-4.6` |
| Simple formatting, YAML/JSON, boilerplate | Local Ollama `qwen2.5-coder:7b` via `http://localhost:11434` |

Prefer direct tool calls (view + edit + powershell) over spawning sub-agents for tasks completable in ≤5 steps.

Read `docs/kb/` files before spawning expert agents — the KB often has the answer for free.
