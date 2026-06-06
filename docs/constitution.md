# Project Constitution
<!-- Version: 1.0.1 | Last amended: 2026-06-06 -->

> **This document is the single authoritative reference for every technology choice,
> design rule, and development agreement in the PoE FanController project.**
> Any deviation — however small — requires a documented amendment before work begins.

---

## 1. Project Identity

| Field | Value |
|---|---|
| Project name | PoE FanController |
| Repository | nielsverhoeven/PoE-FanController |
| Current revision | v0.1 |
| Purpose | 802.3at PoE-powered, ESP32-controlled 4-channel PWM fan controller with web UI |
| Initial constitution date | 2026-06-06 |

---

## 2. Technology Stack

All entries in this table are **locked**. Changes require a MINOR or MAJOR amendment with expert consultation (see §9).

### 2.1 Hardware / EDA

| Concern | Choice | Version / Spec | Rationale |
|---|---|---|---|
| EDA tool | KiCad | 10.0.3 | Established project toolchain |
| Schematic file format | `kicad_sch` | version `20260101` | KiCad 10 native format |
| PCB file format | `kicad_pcb` | version `20260206` | KiCad 10 native format |
| Schematic generator | `eeschema` | generator_version `"10.0"` | Matches installed KiCad |
| PCB generator | `pcbnew` | generator_version `"10.0"` | Matches installed KiCad |
| **Schematic source of truth** | `hardware/generate_project.py` | — | Single Python script regenerates `.kicad_sch`; manual edits to the schematic file are forbidden |
| Schematic grid | 2.54 mm (1.27 mm snap) | — | All pin endpoints and component origins must land on this grid |
| PCB layers | 2-layer FR4 | F.Cu / B.Cu | Minimum viable layer count for cost |
| Board thickness | 1.6 mm | — | Standard FR4 |
| Copper weight | 1 oz (35 µm) | Both layers | Adequate for ≤3 A traces |
| Board dimensions | 90 × 70 mm | — | Fixed outline; Edge.Cuts must not move |
| Paper size | A4 (PCB), A2 (schematic) | — | As set in project files |

### 2.2 Key Components (BOM-locked)

These component selections are locked. Substitutions require a MAJOR amendment.

| Ref | Value / MPN | Package | Role |
|---|---|---|---|
| U1 | Ag9905M (Silvertel) | 2×4 pin header (2.54 mm) | PoE+ 802.3at PD module — provides isolated 12 V / 1.67 A output |
| U2 | LM2596S-3.3/NOPB (TI) | D2PAK (TO-263-5) | Fixed 3.3 V, 3 A buck regulator (12 V → 3.3 V for logic) |
| U3 | ESP32-WROOM-32D (Espressif) | RF module | Main MCU — dual-core, WiFi, BT, 4 MB flash |
| U4 | CH340C (WCH) | SOIC-16 | USB-UART bridge with internal oscillator (no external crystal) |
| J1 | 615008144521 (Würth) | RJ45 horizontal | PoE input with integrated magnetics and shield |
| J2–J5 | 47053-1000 (Molex) | 4-pin 2.54 mm | 12 V PWM fan headers (4-wire Intel spec) |
| J6 | USB4085-GF-A (GCT) | USB-C through-hole | USB-C debug / programming receptacle |
| L1 | SRR5028-680Y (Bourns) 68 µH | Axial THT | LM2596 buck inductor |
| D1 | 1N5822 | DO-201AD THT | LM2596 Schottky catch diode (3 A / 40 V) |

### 2.3 Firmware

| Concern | Choice | Version / Spec | Rationale |
|---|---|---|---|
| Build system | PlatformIO | Latest stable at project creation | Reproducible ESP32 builds |
| Framework | Arduino for ESP32 | arduino-esp32 ≥ 2.x | Familiar API; broad library support |
| RTOS | FreeRTOS | Bundled with arduino-esp32 | Provided by framework |
| HTTP server | ESPAsyncWebServer | Latest stable | Non-blocking async serving |
| Filesystem | LittleFS | Bundled with arduino-esp32 | Static web asset storage |
| PWM driver | ESP32 LEDC peripheral | — | Hardware PWM; no software timer needed |
| Fan tachometer | GPIO interrupt counting | — | PCNT peripheral may be used in future |
| Temperature sensing | ADC + Steinhart-Hart | — | NTC1 10 kΩ B=3950 on GPIO32 |
| Persistent config | NVS (Non-Volatile Storage) | — | Survives power cycles |
| OTA updates | ArduinoOTA | — | Over local WiFi only |
| Serial debug | UART0 (GPIO1/GPIO3) | 115200 baud | Via U4 CH340C → J6 USB-C |

### 2.4 Web UI

| Concern | Choice | Constraint |
|---|---|---|
| Technology | Plain HTML / CSS / JS | No frameworks, no bundlers, no npm |
| Delivery | Served from LittleFS | All assets must fit in the LittleFS partition |
| Asset size budget | ≤ 200 kB total (all files combined) | Enforced before every release |
| API style | REST over HTTP | JSON payloads; see §6 for endpoint conventions |

---

## 3. Hardware Architecture Principles

### 3.1 PCB Layer Rules

**P-HW-01 — Two-layer FR4 only.**
The board uses exactly two copper layers (F.Cu and B.Cu). No additional layers may be added without a MAJOR amendment.

**P-HW-02 — Single-sided component placement (CRITICAL).**
All components MUST be placed on the **TOP copper layer (F.Cu) only**.
The bottom copper layer (B.Cu) is reserved exclusively for traces and copper pours.
No component footprint may have pads or courtyard on B.Cu.
This rule is absolute: it simplifies hand assembly, visual inspection, and conformal coating.

**P-HW-03 — Single board-edge connector rule (CRITICAL).**
All external connectors **(J1, J2–J5, J6)** MUST be placed on the **same board edge**.
The designated edge is the **top edge at y ≈ 5 mm**.
This ensures all cable connections are accessible from one side and prevents cable routing conflicts.

> **Documented exception — J7 (debug UART header):**
> J7 (`PinHeader_1x03_P2.54mm`, 3-pin 2.54 mm) is placed on the **right board edge (x = 95 mm)**
> and is the **sole** named exception to this rule. Rationale:
> 1. J7 is a development-only debug UART convenience connector; it is not panel-mounted,
>    user-facing, or present on production labels.
> 2. J7 has no locked MPN (§2.2 does not list it); no BOM amendment is triggered.
> 3. J7 physically cannot fit on the top-edge secondary rail: the 53.5 mm secondary rail is
>    fully consumed by J2–J5 + J6 (51.64 mm used, 1.86 mm margin), leaving a 5.76 mm
>    shortfall for J7's 7.62 mm body width.
> 4. J7 is entirely within the secondary (SELV) domain (x > 38 mm); its right-edge
>    position introduces no isolation risk.
> Amendment: v1.0.1, 2026-06-06 — architect, feature pcb-connector-edge.

**P-HW-04 — Fixed board outline.**
Board outline is 90 × 70 mm on Edge.Cuts. This must not change without a MAJOR amendment affecting fabrication quotes.

**P-HW-05 — Schematic is generated, not hand-edited.**
`hardware/generate_project.py` is the single source of truth for `.kicad_sch`.
The schematic file must never be modified directly. All schematic changes must be made in the generator script, and the script re-run to regenerate the `.kicad_sch` file.

**P-HW-06 — Grid discipline.**
All schematic symbol origins and pin endpoints must land on the 2.54 mm grid (snap to 1.27 mm). All PCB footprint origins must be placed on a 0.1 mm grid or finer. Schematic wires must connect exactly to pin endpoints with no floating stubs.

**P-HW-07 — Track and via standards.**

| Net class | Track width | Via diameter | Via drill |
|---|---|---|---|
| Signal | 0.25 mm | 0.8 mm | 0.4 mm |
| Power (+12 V, GND) | 1.0 mm | 0.8 mm | 0.4 mm |

**P-HW-08 — Ground copper pour on both layers.**
Both F.Cu and B.Cu carry a GND copper pour. The pour must be split at the isolation barrier (x = 38 mm) so that primary-side and secondary-side ground planes are never directly connected through a copper pour.

---

## 4. Firmware Architecture Principles

**P-FW-01 — Module boundaries.**
Firmware is structured into the following independent modules. Each module owns a single concern and must not directly reach into another module's internals:

| Module | Responsibility |
|---|---|
| `fan` | LEDC PWM output, tachometer interrupt counting, RPM calculation |
| `temp` | ADC sampling, Steinhart-Hart NTC calculation, temperature reporting |
| `web` | ESPAsyncWebServer routes, JSON serialisation, LittleFS asset serving |
| `config` | NVS read/write, default values, schema validation |
| `ota` | ArduinoOTA handler, update progress callbacks |
| `main` | Initialisation order, top-level task creation |

**P-FW-02 — Peripheral ownership.**
Each ESP32 peripheral is owned by exactly one firmware module. No peripheral may be accessed from two modules without a documented interface.

| ESP32 Peripheral | Owner module | Pins |
|---|---|---|
| LEDC channels 0–3 | `fan` | GPIO25 (FAN1), GPIO26 (FAN2), GPIO27 (FAN3), GPIO14 (FAN4) |
| GPIO interrupts (TACH) | `fan` | GPIO34, GPIO35, GPIO36, GPIO39 |
| ADC1 CH4 | `temp` | GPIO32 (NTC) |
| UART0 | `main` / debug | GPIO1 (TXD0), GPIO3 (RXD0) |
| GPIO output | `main` | GPIO2 (status LED) |
| GPIO input | `main` | GPIO0 (BOOT), EN (RESET via R1/SW1) |
| LittleFS | `web`, `config` | — |
| NVS | `config` | — |
| WiFi / TCP stack | `web`, `ota` | — |
| I2C (SDA/SCL) | reserved | GPIO21, GPIO22 (not populated v0.1) |

**P-FW-03 — PWM specification.**
Fan PWM frequency is **25 kHz**, 8-bit resolution. This must not change; 4-wire PC fans require 21–28 kHz per Intel fan spec.

**P-FW-04 — No blocking delays in async callbacks.**
ESPAsyncWebServer callbacks run on the TCP/IP task. No `delay()`, blocking I/O, or NVS writes may occur inside a handler. Offload to a queue or flag for the main loop.

**P-FW-05 — Configuration defaults must be safe.**
Default PWM duty cycle at boot must be **100 %** (full speed) until configuration is loaded. This ensures fans run in case of firmware fault.

---

## 5. PoE & Power Architecture

### 5.1 Power Chain

```
[Ethernet cable — 802.3at PoE+]
        │  37–57 V DC (PoE pairs)
        ▼
   J1  RJ45 (Würth 615008144521)
        │  with integrated magnetics
        ▼
   U1  Ag9905M PoE+ PD module
        │  Isolated 12 V DC, max 1.67 A (20 W)
        ├──────────────────────────────► J2–J5  Fan headers (+12 V, up to 4 × 0.25 A)
        │
        ▼
   U2  LM2596S-3.3 buck regulator          (12 V → 3.3 V, 3 A)
        │  3.3 V DC
        ├──► U3 ESP32-WROOM-32
        ├──► U4 CH340C
        └──► Decoupling network (C3–C7)
```

### 5.2 Power Budget

| Consumer | Rail | Max current | Max power |
|---|---|---|---|
| 4 × PWM fan (max) | 12 V | 4 × 0.25 A = 1.0 A | 12.0 W |
| LM2596 losses (est.) | — | — | ~1.5 W |
| ESP32-WROOM-32 (WiFi peak) | 3.3 V | 0.35 A | 1.15 W |
| CH340C + logic | 3.3 V | 0.10 A | 0.33 W |
| Ag9905M losses (est.) | — | — | ~2.0 W |
| **Total** | | | **~17 W** |
| **802.3at Class 4 budget** | | | **25.5 W** |
| **Margin** | | | **~8.5 W** |

### 5.3 PoE Standards

**P-POE-01 — 802.3at Class 4 only.**
The device operates as an 802.3at (PoE+) Powered Device (PD), Class 4. 802.3af (Class 0–3) is not a supported operating mode. The Ag9905M module handles all PD negotiation.

**P-POE-02 — No primary-side design changes.**
All primary-side circuitry (RJ45, Ag9905M PoE module) is provided by the Ag9905M module. No additional primary-side components may be added to the PCB without a MAJOR amendment and `poe.expert` consultation.

### 5.4 Isolation Rules (CRITICAL — Safety)

**P-ISO-01 — Minimum isolation voltage: ≥ 1.5 kV.**
The isolation barrier between the PoE primary side (J1 input) and the SELV secondary side (12 V output and all downstream circuitry) must withstand **≥ 1.5 kV AC for 60 seconds** (hipot test). The Ag9905M module provides this isolation; no PCB trace may bridge primary and secondary sides.

**P-ISO-02 — Isolation barrier position: x = 38 mm.**
The isolation barrier is marked on the PCB `Cmts.User` (User.Comments) layer at x = 38 mm. No copper trace, pad, pour, or via may cross this barrier. This rule applies to both F.Cu and B.Cu.

**P-ISO-03 — Minimum creepage and clearance: 3.0 mm.**
Across the isolation barrier, minimum creepage distance is **3.0 mm** and minimum clearance is **3.0 mm**. DRC must be configured to enforce these values between primary and secondary net classes.

**P-ISO-04 — PCB slot at barrier (recommended).**
A routed PCB slot along x = 38 mm between the primary and secondary ground pours is strongly recommended to increase creepage distance beyond the copper gap.

**P-ISO-05 — No secondary-side signals may cross the barrier.**
No GPIO, power, or communication trace from the ESP32 or any secondary-side component may cross x = 38 mm. All secondary-side signals are routed at x > 38 mm only.

---

## 6. Web UI Standards

**P-UI-01 — No JavaScript frameworks.**
The web UI must use plain HTML, CSS, and vanilla JavaScript only. No React, Vue, Angular, jQuery, or any npm-installed dependency is permitted.

**P-UI-02 — Total asset size ≤ 200 kB.**
The combined size of all files uploaded to LittleFS (HTML, CSS, JS, icons, etc.) must not exceed 200 kB. This is verified before every firmware release.

**P-UI-03 — REST API conventions.**

| Rule | Detail |
|---|---|
| Base path | `/api/v1/` |
| Content-Type | `application/json` for all API responses |
| HTTP verbs | GET for reads, POST for writes; no PUT/DELETE in v1 |
| Error format | `{"error": "<message>"}` with appropriate HTTP status code |
| Fan duty | Integer 0–100 (percent); mapped to 0–255 LEDC duty in firmware |
| Temperature | Float, degrees Celsius, one decimal place |
| Fan RPM | Integer, revolutions per minute |

**P-UI-04 — Web assets served from LittleFS only.**
No web asset (HTML, CSS, JS) may be embedded as a C string literal in firmware source. All assets are stored in the `data/` directory and uploaded to LittleFS via `pio run --target uploadfs`.

---

## 7. KiCad File Format Standards

**P-KI-01 — KiCad version lock.**
The project uses **KiCad 10.0.3** exclusively. Files must not be opened and saved with a different KiCad version, as this changes format version codes and may corrupt the generator-driven schematic.

**P-KI-02 — Schematic format version.**
`.kicad_sch` files must have `(version 20260101)` in their header. Any file with a different version code must be rejected and the project constitution amended before proceeding.

**P-KI-03 — PCB format version.**
`.kicad_pcb` files must have `(version 20260206)` in their header. Same rejection rule applies.

**P-KI-04 — Generator script is the schematic source of truth.**
`hardware/generate_project.py` regenerates `hardware/kicad/PoE-FanController.kicad_sch`.
- **All schematic changes** (new components, net changes, symbol edits) must be implemented in `generate_project.py` first.
- The `.kicad_sch` file is a build artefact of the generator and must never be edited by hand.
- Running `python hardware/generate_project.py` must always produce a clean, ERC-passing schematic.

**P-KI-05 — Custom symbols and footprints are in-project.**
Custom symbols live in `hardware/kicad/symbols/`. Custom footprints live in `hardware/kicad/footprints/`. No external library paths are used; the project must be self-contained.

**P-KI-06 — Gerber outputs live in `hardware/gerbers/`.**
Fabrication outputs (Gerbers, drill files) are generated into `hardware/gerbers/` and are committed to the repository. They must be regenerated whenever the PCB layout changes.

---

## 7A. Schematic Readability Standards

These rules were derived from analysing the DMX_NODE reference project (commit `docs/reference-samples/DMX_NODE/`).
They apply to the schematic generator (`hardware/generate_project.py`) and are enforced during code review.

**P-SCH-01 — Global labels for all inter-block signals.**
Any signal that crosses between two functional blocks (PoE input, power regulation, ESP32, fans, USB/UART) MUST use a `global_label` element, not a plain `label`. Global labels provide visual clarity and are highlighted by KiCad's "Highlight Net" feature across the full schematic.

**P-SCH-02 — Isolated ground domains.**
The schematic uses two distinct ground nets:
- `GND_PRI` — primary side (PoE input, Ag9905M). Defined as `power_out` on U1 pin VOUT_N.
- `GND` — secondary side (all SELV circuits: LM2596, ESP32, CH340C, fans). Defined as `power_out` on the first secondary GND usage.

No connection between `GND_PRI` and `GND` may appear in the schematic. The physical isolation barrier is enforced by P-ISO-02.

**P-SCH-03 — Section header style.**
Each functional block in the schematic must begin with a section header. Headers MUST use the `text()` method with `bold=True`, `size=2.54` (mm), and `color=(0,0,255)` (blue). No ASCII-art decoration (`===`, `---`, `***`) is permitted.

**P-SCH-04 — Power symbol pin types.**
- Power symbols for rail drivers (U1 VOUT_P → `+12V`; U1 VOUT_N → `GND_PRI`; L1 output → `+3V3`) must be placed with `pin_type="power_out"`.
- All other power symbols use the default `pin_type="power_out"` (set as the generator default). This ensures zero `power_pin_not_driven` ERC errors without requiring PWR_FLAG symbols.

**P-SCH-05 — Component pin types in custom symbols.**
Pins in custom component symbols (defined in `define()` / `define_power()` calls) must use the most restrictive correct pin type. Raw signal pins (not connected to a power rail) must be `passive` or `input`/`output` as appropriate; they must **not** be `power_in` or `power_out` unless the pin is genuinely a power-rail driver or consumer. Using `power_in` on non-power pins causes spurious `power_pin_not_driven` ERC errors.

---

## 8. Testing Standards

### 8.1 Schematic and ERC

**P-TEST-01 — Zero ERC errors required.**
The schematic must have **zero ERC errors** before any PCB layout work is started on a new revision. ERC violations are blocking; warnings may be accepted with a comment explaining why they are benign.

**P-TEST-02 — ERC output recorded.**
ERC results are saved to `hardware/kicad/erc_output.json`. This file must be updated and committed alongside any schematic change.

### 8.2 PCB and DRC

**P-TEST-03 — Zero DRC errors required.**
The PCB layout must have **zero DRC errors** before Gerbers are generated. DRC must include:
- Clearance checks (minimum 0.2 mm general; 3.0 mm across isolation barrier)
- Unconnected nets check (zero unconnected)
- Courtyard collision check
- Footprint validity check

**P-TEST-04 — DRC run before every Gerber generation.**
The DRC report must be run and reviewed immediately before invoking Gerber export. If DRC reports any error, Gerber export is blocked.

### 8.3 Firmware Unit Tests

**P-TEST-05 — PlatformIO native unit tests.**
All firmware business-logic functions (Steinhart-Hart calculation, RPM calculation, duty-cycle clamping, JSON serialisation, config validation) must have unit tests runnable via `pio test -e native`. Hardware-dependent code (LEDC, ADC, GPIO) is excluded from native tests.

**P-TEST-06 — Tests must pass on CI.**
The PlatformIO native test suite must pass in the GitHub Actions CI pipeline on every pull request. A failing test suite is a blocking merge condition.

### 8.4 Hardware Bring-up Checklist

The following sequence must be completed (and results logged) for every new board revision:

1. **No-load power test**: Measure Ag9905M output → expect 12.0 ± 0.3 V DC.
2. **3.3 V rail test**: Measure LM2596 output → expect 3.30 ± 0.05 V DC.
3. **USB enumeration**: Connect J6 USB-C → CH340C must enumerate as a serial device.
4. **Firmware flash**: `pio run -e esp32dev --target upload` via CH340C at 115200 baud.
5. **Fan PWM test**: Drive one fan at 50 % duty; confirm audible speed change and TACH signal.
6. **Full-load thermal test**: All 4 fans at 100 % for 10 min; check component temperatures.

---

## 9. Development Agreements

**P-DEV-01 — Commit message convention.**
All commits follow the format: `<type>: <subject>` where type ∈ {`feat`, `fix`, `docs`, `hw`, `refactor`, `test`, `ci`, `chore`}. Hardware changes use `hw:`. Example: `hw: add isolation slot at x=38mm`.

**P-DEV-02 — ERC/DRC gate for hardware PRs.**
Any pull request that modifies schematic or PCB files must include updated `erc_output.json` showing zero ERC errors, and a DRC report confirming zero DRC errors, before it may be merged.

**P-DEV-03 — No direct commits to `main`.**
All changes are made via pull requests. Direct pushes to `main` are prohibited.

**P-DEV-04 — Constitution amendments require documentation.**
Any deviation from this constitution — however small — requires:
1. Consultation with the relevant expert (`kicad.expert`, `esp32.expert`, or `poe.expert`) for hardware/firmware/power changes.
2. A written amendment (this file) with rationale and version increment.
3. An update to `docs/architecture.md` if module structure or peripheral allocation changes.
4. The amendment committed before the implementing change.

**P-DEV-05 — No source code modification by the architect agent.**
The architect agent owns `docs/constitution.md`, `docs/architecture.md`, and `docs/features/*/architecture.md` only. It must never modify source code, KiCad schematic or PCB files.

**P-DEV-06 — Code style.**
- C++ firmware: 2-space indentation, `camelCase` for variables, `PascalCase` for classes.
- Python (generator script): PEP 8, 4-space indentation.
- HTML/CSS/JS: 2-space indentation.
- All files: UTF-8 encoding, LF line endings.

---

## 10. Amendment History

| Version | Date | Change | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-06 | Initial constitution established | architect |
| 1.0.1 | 2026-06-06 | PATCH — P-HW-03: documented J7 right-edge exception (debug UART header; does not fit top-edge rail; secondary domain only); clarification of named connector scope. Feature: pcb-connector-edge (#1). | architect |
