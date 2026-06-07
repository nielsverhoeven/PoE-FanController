# PoE FanController – Hardware Design Notes

<!-- Last updated: 2026-06-07 | Updated: feature/33-fix-ci-workflows -->

## Overview
A PoE 802.3at (PoE+) powered device that controls up to 4 PWM fans via an
ESP32-WROOM-32 microcontroller and exposes a web-based configuration interface.

## Block Diagram
```
[Ethernet cable / PoE+]
       │
   ┌───▼────────────────┐
   │  J1  RJ45 + magnetics │  ← Shielded, PoE-capable
   └───┬────────────────┘
       │ 37–57 V DC (PoE pair)
   ┌───▼────────────────┐
   │  U1  Ag9905M module │  ← PoE PD negotiation + isolated flyback
   └───┬────────────────┘
       │ 12 V, 1.67 A (20 W)
       ├──────────────────────────────► J2-J5  Fan headers (12 V PWM)
       │
   ┌───▼────────────────┐
   │  U2  LM2596-3.3    │  ← 12 V → 3.3 V, 3 A step-down
   └───┬────────────────┘
       │ 3.3 V
       ├──── U3 ESP32-WROOM-32
       ├──── U4 CH340C
       └──── Logic decoupling caps
```

## Power Budget (802.3at PoE+ = 25.5 W at PD)

| Consumer          | Voltage | Current  | Power  |
|-------------------|---------|----------|--------|
| 4 × 12 V fan (max)| 12 V   | 4×0.25 A | 12 W   |
| ESP32 (peak WiFi) | 3.3 V   | 0.35 A   | 1.15 W |
| CH340C + logic    | 3.3 V   | 0.10 A   | 0.33 W |
| LM2596 losses     | –       | –        | ~1.5 W |
| Ag9905M losses    | –       | –        | ~2.0 W |
| **Total**         |         |          |**~17 W**|

Available margin: 25.5 − 17 = 8.5 W.  Safe for 802.3at Class 4.

## ESP32 GPIO Allocation

| GPIO   | Function         | Direction | Notes                          |
|--------|------------------|-----------|--------------------------------|
| GPIO0  | BOOT             | Input     | Pull-up R2; BOOT button SW2    |
| GPIO2  | Status LED       | Output    | Active HIGH, R3 330 Ω          |
| GPIO4  | (reserved)       | –         | 1-Wire or I2C SDA alternative  |
| GPIO14 | FAN4 PWM         | Output    | LEDC channel 3, 25 kHz         |
| GPIO21 | I2C SDA (future) | I/O       | Not populated on v0.1          |
| GPIO22 | I2C SCL (future) | I/O       | Not populated on v0.1          |
| GPIO25 | FAN1 PWM         | Output    | LEDC channel 0, 25 kHz         |
| GPIO26 | FAN2 PWM         | Output    | LEDC channel 1, 25 kHz         |
| GPIO27 | FAN3 PWM         | Output    | LEDC channel 2, 25 kHz         |
| GPIO32 | NTC ADC          | ADC Input | 12-bit ADC, voltage divider    |
| GPIO34 | FAN1 TACH        | Input     | Input-only pin, pull-up R5     |
| GPIO35 | FAN2 TACH        | Input     | Input-only pin, pull-up R6     |
| GPIO36 | FAN3 TACH        | Input     | Input-only pin, pull-up R7     |
| GPIO39 | FAN4 TACH        | Input     | Input-only pin, pull-up R8     |
| GPIO1  | TXD0 (UART0)     | Output    | To CH340C RXD                  |
| GPIO3  | RXD0 (UART0)     | Input     | From CH340C TXD                |
| EN     | Reset            | Input     | Pull-up R1; RESET button SW1   |

## Safety & Isolation Requirements (CRITICAL)

- **Minimum creepage across isolation barrier (J1↔U1 output)**: 3.0 mm
- **Minimum clearance**: 3.0 mm
- **Hipot test**: 1.5 kV AC for 60 s across isolation barrier
- **Slot**: Consider adding a PCB slot between primary (PoE) and secondary sides
- The dashed line in the PCB comment layer marks the isolation barrier at x = 38 mm
- **Never route secondary-side signals across the isolation barrier without the Ag9905M module**

## Fan Header Pinout (J2–J5, all identical)

| Pin | Signal   | Notes                              |
|-----|----------|------------------------------------|
| 1   | GND      | Ground                             |
| 2   | +12V     | Fan supply (12 V from Ag9905M)     |
| 3   | TACH     | Tachometer output from fan, 10k pull-up to 3.3V |
| 4   | PWM      | 25 kHz PWM input from ESP32 LEDC  |

Standard PC fan pinout (Intel spec). Compatible with 4-wire 12V PWM fans.

## PCB Design Guidelines

- **Layer stack**: 2-layer FR4, 1.6 mm, 1 oz Cu
- **Track widths**: Signal = 0.25 mm; Power (+12V, GND) = 1.0 mm
- **Via**: 0.8 mm diameter, 0.4 mm drill
- **Ground pour**: Both layers (GND). Split at isolation barrier.
- **Component placement priority**:
  1. **All external connectors on top board edge** (y = 5 mm, per constitution P-HW-03):
     | Ref | Part | Centre X | Side | Notes |
     |-----|------|----------|------|-------|
     | J1 | RJ45 Amphenol 54602 | 20.0 mm | Primary (x < 38 mm) | rot=180°, port exits top edge |
     | J2 | Fan header 1×4 | 46.1 mm | Secondary | Courtyard left ≥ 41.0 mm (3 mm creepage) |
     | J3 | Fan header 1×4 | 56.8 mm | Secondary | |
     | J4 | Fan header 1×4 | 67.4 mm | Secondary | |
     | J5 | Fan header 1×4 | 78.1 mm | Secondary | |
     | J6 | USB-C GCT USB4085 | 85.0 mm | Secondary | Port faces top edge (rot=0°) |
     | J7 | Debug UART 1×3 | 91.0 mm | Right edge | Documented exception P-HW-03 v1.0.1; rot=90° |
  2. U1 (Ag9905M) close to J1, primary-side power traces (≈ x=20, y=40)
  3. Isolation gap/slot at x=38 mm, y=10–70 mm, 1.0 mm wide (P-ISO-04)
  4. U2 (LM2596) + L1 + D1 grouped together, primary side (≈ x=15–32, y=55–62)
  5. U3 (ESP32) on secondary side (≈ x=65, y=42)
  6. U4 (CH340C) near J6 on secondary side (≈ x=82, y=58)
  7. Passive components — 19 footprints placed across three zones (see **Passive Component Placement Zones** below)

## Passive Component Placement Zones

All 19 passive footprints were added in feature #13 (`feature/13-missing-passive-footprints`).
Coordinates below are the PCB origin (cx, cy) passed to `embed_footprint()` in
`hardware/generate_project.py` — the single source of truth for all placements.
All components sit on `F.Cu` only (P-HW-02 ✓). All centres are east of x=38 mm (P-ISO-02 ✓).

### Zone A — Between fan headers (y ≈ 19.5 mm)

| Ref | cx (mm) | cy (mm) | Package | Value | Function |
|-----|---------|---------|---------|-------|----------|
| R5 | 51.5 | 19.5 | 0402 | 10 kΩ | FAN1 TACH pull-up (→ GPIO34) |
| R6 | 62.1 | 19.5 | 0402 | 10 kΩ | FAN2 TACH pull-up (→ GPIO35) |
| R7 | 72.8 | 19.5 | 0402 | 10 kΩ | FAN3 TACH pull-up (→ GPIO36) |
| R8 | 92.0 | 19.5 | 0402 | 10 kΩ | FAN4 TACH pull-up (→ GPIO39) |

### Zone B — Left of ESP32 body (x = 45–52 mm, y = 47–56 mm)

| Ref | cx (mm) | cy (mm) | Package | Value | Function |
|-----|---------|---------|---------|-------|----------|
| R1 | 45.0 | 47.0 | 0402 | 10 kΩ | ESP32 EN pull-up |
| R2 | 45.0 | 50.0 | 0402 | 10 kΩ | ESP32 BOOT (GPIO0) pull-up |
| R3 | 45.0 | 53.0 | 0402 | 330 Ω | Status LED current limit |
| R4 | 45.0 | 56.0 | 0402 | 10 kΩ | NTC voltage divider (top half) |
| C3 | 52.0 | 47.0 | 0402 | 100 nF | +3V3 decoupling — U3 |
| C4 | 52.0 | 50.0 | 0402 | 100 nF | +3V3 decoupling — U3 |
| C5 | 52.0 | 53.0 | 0402 | 100 nF | +3V3 decoupling — U3 |
| C6 | 52.0 | 56.0 | 0402 | 100 nF | +3V3 decoupling — U3 |

### Zone C — Below ESP32 / U4 (y = 63.5–71.5 mm)

| Ref | cx (mm) | cy (mm) | Package | Value | Function |
|-----|---------|---------|---------|-------|----------|
| C7 | 76.0 | 63.5 | 0402 | 100 nF | CH340C V3 pin decoupling |
| R9 | 83.0 | 68.5 | 0402 | 5.1 kΩ | USB-C CC1 pull-down (→ GND) |
| R10 | 83.0 | 71.5 | 0402 | 5.1 kΩ | USB-C CC2 pull-down (→ GND) |
| SW1 | 44.0 | 68.5 | 6mm THT | — | RESET button; origin = Pad 1 (leftmost pad) at x=44.0 mm; left pad edge x=43.0 mm → 5.0 mm gap to isolation barrier (P-ISO-03 ✓) |
| SW2 | 54.0 | 68.5 | 6mm THT | — | BOOT button; courtyard left x=52.5; gap to SW1 courtyard right (52.0 mm) = 0.5 mm ✓ |
| LED1 | 64.0 | 68.5 | 3mm THT | Green | Status LED; origin = anode (Pad 1) |
| NTC1 | 70.0 | 68.5 | Axial THT | 10 kΩ NTC | NTC thermistor; 10.16 mm pitch; courtyard right x=81.21 mm; gap to R9 left (82.07 mm) = 0.86 mm ✓ |

> **THT courtyard note:** `SW_PUSH_6mm`, `LED_D3.0mm`, and `R_Axial_DIN0207_…_Horizontal`
> footprints have their KiCad origin at **Pad 1, not the geometric centre**.
> The (cx, cy) values above are origin positions, not bounding-box centres.
> THT courtyard bottoms all land at y = 74.5 mm — 0.5 mm from the board edge (y = 75 mm).
> See `docs/features/pcb-passive-footprints/architecture.md` §4–5 for the full courtyard
> derivation and corrected-vs-plan-md comparison.

### DRC status after feature #13

| Check | Result |
|-------|--------|
| `missing_footprint` violations | **0** |
| `courtyard_collision` violations | **0** |
| Total DRC violations | **36** (all `solder_mask_bridge` on J6 USB-C — pre-existing, unrelated to this feature) |
| All footprints on F.Cu | ✓ |
| All centres east of isolation barrier (x = 38 mm) | ✓ (nearest: SW1 at cx = 44.0 mm) |

DRC report: `PoE-FanController-drc.rpt` (repository root).

---

## Schematic Conventions

These conventions are enforced by `hardware/generate_project.py` and codified in constitution §7A
(P-SCH-01 – P-SCH-05). The generator is the single source of truth for the schematic; the
`.kicad_sch` file is a build artefact and must never be edited by hand (P-HW-05, P-KI-04).

### Global labels vs. local labels

Any signal that crosses between two of the five functional blocks MUST use `global_label()`.
Purely intra-block connections use `label()`.

| Signal type | Method | Example nets |
|---|---|---|
| Inter-block | `global_label()` | `FAN1_PWM`, `FAN1_TACH`, `ESP_TX`, `ESP_RX`, `USB_DP`, `USB_DN`, `NTC_ADC`, `ESP_EN`, `BOOT` |
| Intra-block | `label()` | `POE_A+`, `POE_A-`, `GPIO2`, `LED_A`, `CH340_V3`, `+3V3_SW`, `CC1`, `CC2` |

The `global_label()` method emits a KiCad 10 S-expression with `fields_autoplaced yes` and an
`Intersheetrefs` property carrying `${INTERSHEET_REFS}`, matching the KiCad 10 reference-project
format. The schematic currently contains **41 global labels**.

Label `shape` follows signal direction at the point of connection:

| Shape | Meaning | Example in this schematic |
|---|---|---|
| `input` | This end receives the signal | `ESP32.IO32` receiving `NTC_ADC`; `ESP32.EN` receiving `ESP_EN` |
| `output` | This end drives the signal | `Fan_Header.TACH` driving `FAN1_TACH`; `R4` driving `NTC_ADC` |
| `bidirectional` | Both drive and receive | `USB_DP`, `USB_DN` |
| `passive` | No defined direction | `BOOT` (pulled-up by R2, driven by CH340C DTR, consumed by ESP32 IO0) |

### Ground domain separation

Two ground nets exist in the schematic and are **never connected** to each other, either in the
schematic or on the PCB:

| Net | Defined on | Side | Function |
|---|---|---|---|
| `GND_PRI` | U1 VOUT_N (pin 6), `pin_type="power_out"` | Primary (PoE) | Return path for PoE input currents only |
| `GND` | U2 GND (pin 3) and all secondary components | Secondary (SELV) | Return path for 12 V fans and 3.3 V logic |

The isolation barrier is at x = 38 mm on the PCB (P-ISO-02). The copper pour on both layers is
split at this line (P-HW-08). No PCB trace, pad, via, or pour may cross it.

### Section header style

Each functional block opens with a plain-text annotation placed by the `text()` method:

```python
BLUE = (0, 0, 255)
s.text("PoE Power Input", 25, 18, size=2.54, bold=True, color=BLUE)
```

The five section headers in the current schematic:

| Header text | Components |
|---|---|
| `PoE Power Input` | J1 (RJ45), U1 (Ag9905M) |
| `3.3V Regulator (LM2596)` | U2, D1, L1, C1–C6 |
| `ESP32-WROOM-32` | U3, R1–R4, SW1–SW2, LED1, NTC1 |
| `Fan Headers (4× PWM)` | J2–J5, R5–R8 |
| `USB / UART Bridge` | J6, J7, U4 (CH340C), R9–R10, C7 |

Requirements (P-SCH-03): `bold=True`, `size=2.54` mm, `color=(0,0,255)` (blue).
No ASCII-art decoration (`===`, `---`, `***`) is permitted.

### Power symbol pin types

The `power()` method in the generator defaults to `pin_type="power_out"`:

```python
def power(self, name, x, y, angle=0, pin_type="power_out"):
    self.define_power(name, pin_type=pin_type)
```

Every `#PWR` symbol placed by `power()` — whether a rail source or a power consumer (decoupling
cap, pull-up, ground return) — is therefore defined as `power_out`. This eliminates all
`power_pin_not_driven` ERC errors without needing separate `PWR_FLAG` symbols (P-SCH-04).

The three key rail driver calls that are also explicitly marked `power_out`:

| Call in `generate_project.py` | Net driven |
|---|---|
| `s.power("+12V",    *p["5"], pin_type="power_out")` — U1 VOUT_P | `+12V` rail |
| `s.power("GND_PRI", *p["6"], pin_type="power_out")` — U1 VOUT_N | `GND_PRI` rail |
| `s.power("+3V3",    *p["2"], pin_type="power_out")` — L1 pin 2 | `+3V3` rail |

**Ag9905M VPORT pins:** U1 input pins (VPORT_A±, VPORT_B±) use `passive` in the custom symbol
definition (not `power_in`). Using `power_in` on these pins previously caused spurious
`power_pin_not_driven` ERC errors because no schematic element drives the PoE pair nets — they
are driven externally by the Ethernet PSE. Changing to `passive` removes those errors (P-SCH-05).

### ERC status

Authoritative ERC run: KiCad 10.0.3, `hardware/kicad/erc_output.json`, 2026-06-06T23:14:29.

| Metric | Result |
|---|---|
| **Errors** | **0** |
| **Warnings** | **85** |

All 85 warnings fall into two categories, both benign:

**`lib_symbol_issues` — "symbol library 'Custom' not included"**
All components are defined inline in `generate_project.py` using `Custom:*` lib IDs. The `Custom`
library is not registered in `PoE-FanController.kicad_pro` because it does not exist on disk;
all symbol definitions are embedded directly in the generated `.kicad_sch` file. KiCad cannot
find the external library and flags each component. This is expected and correct by design
(P-HW-05, P-KI-04).

**`lib_symbol_mismatch` — "symbol 'X' doesn't match copy in library 'power'"**
Inline power symbols (`GND`, `+12V`, `+3V3`, `GND_PRI`) are generated with `pin_type="power_out"`,
whereas the KiCad stock `power` library defines those same names with `pin_type="power_in"`.
KiCad detects the mismatch. Benign: the deviation is intentional (P-SCH-04) and is precisely
what suppresses `power_pin_not_driven` ERC errors project-wide.

Four check types are suppressed in the project-level ERC configuration:

| Suppressed check | Reason |
|---|---|
| `single_global_label` | Precautionary suppress; all 41 global labels appear at ≥ 2 locations |
| `four_way_junction` | No 4-way wire junctions exist in the schematic |
| `simulation_model_issue` | No SPICE models are attached |
| `footprint_filter` | Custom footprint assignments do not match KiCad library filter strings |

---

## Bill of Materials Summary

Full BOM (with Qty, Manufacturer, MPN, Datasheet links) is generated by `python hardware/generate_project.py`
into `hardware/bom/bom.csv`. Key component selections:

### Major ICs and Connectors (BOM-locked per constitution §2.2)

| Ref | Value / MPN | Package | Role |
|-----|-------------|---------|------|
| U1 | Silvertel Ag9905M | 2×4 pin header 2.54 mm | PoE+ 802.3at PD module, 12 V / 1.67 A isolated |
| U2 | TI LM2596S-3.3/NOPB | D2PAK (TO-263-5) | 3.3 V 3 A fixed buck regulator |
| U3 | Espressif ESP32-WROOM-32D | RF module | Main MCU, WiFi, 4 MB flash |
| U4 | WCH CH340C | SOIC-16 | USB-UART bridge (no external crystal) |
| J1 | Würth 615008144521 | RJ45 horizontal | PoE input with integrated magnetics |
| J2–J5 | Molex 47053-1000 | 4-pin 2.54 mm | 12 V PWM fan headers |
| J6 | GCT USB4085-GF-A | USB-C through-hole | USB-C debug / programming |
| L1 | Bourns SRR5028-680Y | Axial THT | 68 µH buck inductor |
| D1 | ON Semi 1N5822 | DO-201AD THT | 3 A Schottky catch diode |

### Passives Added in Feature #13 (not BOM-locked — equivalents acceptable if value/package match)

| Refs | Qty | Value | Package | MPN | Notes |
|------|-----|-------|---------|-----|-------|
| C3, C4, C5, C6, C7 | 5 | 100 nF | 0402 | Samsung CL05B104KO5NNNC | +3V3 / V3 decoupling, X5R 16 V |
| R1, R2, R4, R5, R6, R7, R8 | 7 | 10 kΩ | 0402 | Yageo RC0402FR-0710KL | EN, BOOT, NTC divider, TACH pull-ups |
| R3 | 1 | 330 Ω | 0402 | Yageo RC0402FR-07330RL | Status LED current limit |
| R9, R10 | 2 | 5.1 kΩ | 0402 | Yageo RC0402FR-075K1L | USB-C CC1/CC2 pull-down resistors |
| LED1 | 1 | Green 3 mm | THT Ø3 mm | Würth 150060GS75000 | Status LED, 565 nm, active HIGH via R3 |
| SW1 | 1 | RESET | 6 mm THT | C&K PTS636 SK43 SMTR LFS | ESP32 EN reset button |
| SW2 | 1 | BOOT | 6 mm THT | C&K PTS636 SK43 SMTR LFS | ESP32 GPIO0 boot-mode button |
| NTC1 | 1 | 10 kΩ NTC | Axial THT P10.16 mm | Murata NCP15XH103F03RC | Temperature sensing (B = 3380 K, GPIO32 ADC) |

---

## Firmware Overview

- **Framework**: Arduino for ESP32 (PlatformIO)
- **Fan PWM**: ESP32 LEDC peripheral, 25 kHz, 8-bit resolution
- **TACH**: GPIO interrupt counting or PCNT peripheral, Hz → RPM
- **Temperature**: ADC + Steinhart-Hart equation for NTC
- **Web interface**: ESPAsyncWebServer + LittleFS (static HTML/CSS/JS)
- **Configuration persistence**: NVS (Non-Volatile Storage)
- **OTA**: ArduinoOTA over local WiFi

## CI / Automated Checks

Full workflow documentation is in [`docs/ci.md`](../docs/ci.md). This section summarises what CI enforces on hardware files.

### Workflows that act on `hardware/`

| Workflow | Trigger | Gate |
|---|---|---|
| **Hardware Check (ERC + DRC)** | `push` / `pull_request` touching `hardware/**` | Generator syntax; ERC zero errors; DRC ≤ 67 violations (Docker baseline) |
| **KiCad Hardware Release** | `v*.*.*` tag | DRC zero tolerance, then Gerbers + BOM + schematic PDF → GitHub Release |

### KiCad Docker image

Both hardware workflows run `kicad-cli` inside `kicad/kicad:10.0.2` with `--user root`. The development toolchain is locked to KiCad 10.0.3 (P-KI-01); the Docker image uses 10.0.2 because no 10.0.3 image was published on Docker Hub as of 2026-05-09 (P-KI-01 PATCH amendment, constitution v1.1.0).

### DRC baseline

The PR gate allows up to **67 violations** in the Docker/Linux environment (breakdown: 34 `lib_footprint_issues`, 28 `solder_mask_bridge` on J6, 5 `silk_edge_clearance`). Issue #39 tracks driving this to zero. The release workflow uses a **zero-tolerance threshold** regardless of the PR baseline (P-CI-02).

### ERC gate

ERC errors (severity `"error"`) cause an immediate hard failure. Warnings are logged but do not block merge. The current schematic must have zero ERC errors (P-TEST-01).

---

## Bring-up Procedure

1. **No-load power test**: Connect PoE+ switch. Measure Ag9905M output (expect 12.0 ± 0.3 V).
2. **Secondary rail**: Measure LM2596 output (expect 3.30 ± 0.05 V).
3. **UART test**: Connect USB-C. CH340C should enumerate. Open serial at 115200 baud.
4. **Flash firmware**: `pio run -e esp32dev --target upload` via CH340C.
5. **Fan test**: Connect one fan to J2. Command 50% duty cycle from firmware/web UI.
6. **Full load test**: Connect all 4 fans at 100%, run for 10 min. Check temperatures.
