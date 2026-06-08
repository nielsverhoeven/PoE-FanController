# Technical Plan: External DS18B20 Temperature Probe Support

<!-- Issue: #97 | Branch: feature/97-ds18b20-temperature-probe | Status: PLANNING -->
<!-- Constitution reference: v3.1.0 | Plan date: 2026-06-08 -->

---

## Architecture Fit

### Hardware Block Diagram Mapping

The DS18B20 feature adds one new functional block to the right zone of the daughter board,
slotting alongside the existing FAN_1–FAN_4 column. The updated connector column becomes:

```
Right-edge column (x > 21 mm):
  ┌────────────────────────────────────────────┐
  │  J2  FAN_1  ←  FAN1_PWM / FAN1_TACH       │
  │  J3  FAN_2  ←  FAN2_PWM / FAN2_TACH       │
  │  J4  FAN_3  ←  FAN3_PWM / FAN3_TACH       │
  │  J5  FAN_4  ←  FAN4_PWM / FAN4_TACH       │
  │  J6  Temp_Probe ← DS18B20_DATA / +3V3/GND │  ← NEW
  └────────────────────────────────────────────┘
```

Each connector has an adjacent status LED. Existing fan connectors have +12V-powered
passive LEDs (D2–D5). The new probe connector has a firmware-driven LED (LED6 / Status_LED_5)
following the same physical pattern but driven from GPIO20 rather than the +12V rail.

### Firmware Module Structure (P-FW-01)

A new `probe` module is added alongside the existing four modules. Ownership boundaries
are strictly respected:

| Module | Responsibility | Change |
|---|---|---|
| `fan` | LEDC PWM, tach ISR, RPM | **No change** |
| `temp` | ADC, Steinhart-Hart NTC | **No change** |
| `probe` | 1-Wire bus scan, DS18B20 read, probe LED | **New** |
| `web` | Routes, JSON, LittleFS | Extended — add `probe_temp_c` to status response |
| `config` | NVS, defaults, schema | Extended — add probe sensor-select NVS key |
| `ota` | OTA handler | **No change** |
| `main` | Init order, task creation | Extended — call `probe_init()` |

### Constitution Principles Directly Invoked

| Principle | Relevance to This Feature |
|---|---|
| P-FW-01 — Module boundaries | `probe` module owns all 1-Wire logic; `web` module calls `probe_get_temp_celsius()` only |
| P-FW-02 — Peripheral ownership | GPIO19 and GPIO20 must be formally added to the peripheral table in a MINOR amendment |
| P-FW-04 — No blocking delays in async callbacks | DS18B20 750 ms conversion must run in a FreeRTOS task, not in a web handler |
| P-FW-05 — Safe defaults | On boot, probe state initialises to PROBE_ABSENT (not a stale temperature value) |
| P-HW-02 — Top-layer only | J6 connector and LED6 placed on F.Cu exclusively |
| P-HW-03 — Side-edge connectors | J6 placed on right edge, consistent with J2–J5 |
| P-HW-05 / P-KI-04 — Generator is schematic source | All schematic additions via `hardware/generator/components.py`; no hand-editing `.kicad_sch` |
| P-HW-07 — Track standards | 1-Wire DATA trace: 0.25 mm signal class; keep away from 12V/PWM traces |
| P-KI-05 — In-project symbols | No new custom symbol footprint required (screw terminal uses existing KiCad library) |
| P-SCH-01 — Global labels | `DS18B20_DATA` net uses a global label across schematic blocks |
| P-TEST-01/03 — Zero ERC/DRC | Must be verified before any PCB layout submission |
| P-UI-03 — REST conventions | `probe_temp_c` key follows existing temperature format (float, one decimal, or null) |
| P-CI-01 — CI gate | PR touching `hardware/` must pass automated ERC and DRC in CI |

---

## Hardware Implementation Approach

### Schematic Changes

All changes are made in `hardware/generator/components.py` (and supporting generator files).
The `.kicad_sch` is regenerated via `python hardware/generate_project.py`. No hand-editing
of `.kicad_sch` is permitted (P-HW-05, P-KI-04).

**New schematic elements:**

| Ref | Value / MPN | Symbol | Net connections |
|---|---|---|---|
| J6 | 3-pin screw terminal or JST (see Component Selection) | `Custom:Conn_3Pin` or KiCad std | Pin 1: GND; Pin 2: DS18B20_DATA; Pin 3: +3V3 |
| R14 | 4.7 kΩ THT | `Custom:R` (existing) | Between DS18B20_DATA and +3V3 |
| R15 | 330 Ω THT | `Custom:R` (existing) | In series with LED6 (GPIO20 → R15 → LED6 → GND) |
| LED6 | 3 mm green or amber THT LED | `Custom:LED` (existing) | Anode via R15 from GPIO20; cathode to GND |

**Generator additions:**
- Add `J6` to the fan column in `build_schematic()` with its own section header
  (P-SCH-03 compliant: bold, blue, 2.54 mm text)
- Add `DS18B20_DATA` global label (P-SCH-01) on J6 pin 2
- Add `PROBE_LED` global label on the GPIO20 net for LED6
- Update J8 symbol: change pin 27 (left) label from `NC` to `DS18B20_DATA`,
  type `bidirectional`; change pin 28 (right) label from `NC` to `PROBE_LED`, type `output`

### PCB Layout Changes

The PCB is modified in KiCad GUI (P-KI-07). Gerbers must be regenerated after layout.

**Placement (right zone, x > 21 mm):**
- J6 (probe connector): place below J5 (FAN_4 header) on the right edge, maintaining the
  same horizontal alignment and edge clearance as J2–J5.
- R14 (4.7 kΩ pull-up): place close to J6 pin 2 to minimise DATA trace antenna length.
- LED6 / R15 (probe status LED circuit): place immediately to the left of J6, mirroring
  the positional relationship of D2–D5 / R9–R12 relative to J2–J5.
- All components on F.Cu only (P-HW-02).

**Routing:**
- `DS18B20_DATA` trace: 0.25 mm signal class; route from J6 pin 2 via R14 to J8 left
  pin 27 (GPIO19); keep ≥ 1.5 mm from PWM and 12V traces.
- `PROBE_LED` trace: 0.25 mm signal class; route from J8 right pin 28 (GPIO20) via R15
  to LED6 anode.
- GND and +3V3 are picked up from nearby copper pour and 3.3V net respectively.

### Component Selection

| Ref | Part | MPN | Footprint | Rationale |
|---|---|---|---|---|
| J6 | 3-pin 2.54 mm pitch screw terminal | Phoenix Contact 1714977 (or Wurth 691102510003) | `TerminalBlock_Phoenix_PT-1,5mm_3-pin` | Allows fieldwiring of bare-wire DS18B20 pigtail; robust screw clamp; same pitch as other THT passives |
| R14 | 4.7 kΩ 1/4W 1% axial THT | Yageo MFR-25FBF52-4K70 | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` | 4.7 kΩ is the standard 1-Wire pull-up value; same family as R5–R8, R4 |
| R15 | 330 Ω 1/4W 1% axial THT | Yageo MFR-25FBF52-330R | same as R3, R13 | Limits LED6 current to ≈ 10 mA @ 3.3V; identical to existing LED current-limit resistors |
| LED6 | 3 mm green THT LED | Wurth 150060GS75000 | `LED_THT:LED_D3.0mm` | Consistent with LED1 (status) and LED2 (prog); all-green palette for board LEDs |

### Power Budget Impact

| Addition | Rail | Current | Power |
|---|---|---|---|
| DS18B20 VCC-mode max | +3.3V | ≤ 1.5 mA | ≤ 5.0 mW |
| LED6 (solid on, 10 mA) | +3.3V | 10 mA | 33 mW |
| **Total addition** | | **≤ 11.5 mA** | **≤ 38 mW** |

The existing 3.3V rail is supplied by the Waveshare board's internal LDO and is not budget-constrained
by the Ag9905M 20W limit (which governs the +12V rail). The +12V rail is unaffected.
The ≤ 38 mW addition is negligible; no budget re-evaluation required.

---

## PoE / Power Considerations

- **Power class:** No change — 802.3at Class 4 only (P-POE-01). The DS18B20 and LED6
  together consume < 50 mW; the 1.1 W PoE margin (§5.2) is unaffected.
- **Power rails:** No new rails. DS18B20 uses +3.3V (already present via J8 from the
  Waveshare board's internal LDO). DATA pull-up also ties to +3.3V.
- **Isolation:** No isolation impact. The DS18B20 probe is entirely in the SELV secondary
  domain. The probe connector is not adjacent to primary-side circuitry. Creepage and
  clearance rules (P-ISO-03) are not affected.

---

## Firmware Implementation Approach

### GPIO Pin Assignments (Prerequisite: MINOR Constitution Amendment)

| Signal | GPIO | J8 Header Pin | Current state in generator |
|---|---|---|---|
| DS18B20_DATA (1-Wire) | **GPIO19** | Left pin 27 | NC — available |
| PROBE_LED (Status_LED_5) | **GPIO20** | Right pin 28 | NC — available |

**Rationale:** GPIO19 and GPIO20 are the cleanest available GPIOs on the J8 header as confirmed
from `hardware/generator/components.py`. Neither is a strapping pin, neither conflicts with any
existing peripheral (fans, NTC, ETH RMII, ETH SMI, UART, status LEDs, OTA LED). They are
adjacent on the header (pins 27/28), simplifying PCB routing from J8 to J6/LED6.

A constitution MINOR amendment must update the P-FW-02 peripheral ownership table to formally
assign these GPIOs before implementation begins (P-DEV-04).

### New Module: `firmware/src/probe.cpp` + `firmware/include/probe.h`

```
probe_init()
  - pinMode(DS18B20_DATA_PIN, INPUT)  // 1-Wire idle state; pull-up is external (R14)
  - probe_led_init()                  // pinMode(PROBE_LED_PIN, OUTPUT); write LOW
  - Start probe_task() as FreeRTOS task (stack 2048, priority 1)

probe_task()  [FreeRTOS task, loops forever]
  - Scan 1-Wire bus: OneWire.reset() + search for DS18B20 ROM address
  - If not found: set _probe_state = PROBE_ABSENT; LED = OFF; delay 5s; retry
  - If found:
      a. Request conversion: DallasTemperature.requestTemperatures() — non-blocking call
      b. Delay FreeRTOS ticks (750 ms for 12-bit resolution) — task sleeps, not busy-wait
      c. Read result: DallasTemperature.getTempCByIndex(0)
      d. Validate range (−55 to +125 °C); set _probe_temp_c; set _probe_state = PROBE_OK
      e. LED = SOLID; delay 2s; repeat from (a)

probe_get_temp_celsius()  → float or sentinel (−127.0f = no probe)
probe_get_state()         → probe_state_t {PROBE_ABSENT, PROBE_READING, PROBE_OK}
```

**LED control** runs in the same `probe_task` using non-blocking millis-style toggling for
the blink pattern (PROBE_READING state), so it never calls `delay()` from within an
async callback (P-FW-04).

### `firmware/include/pins.h` Additions

```cpp
// DS18B20 1-Wire temperature probe (Issue #97)
#ifndef DS18B20_DATA_PIN
#define DS18B20_DATA_PIN  19  ///< GPIO19 — 1-Wire DATA, J8 left pin 27; 4.7kΩ pull-up on PCB (R14)
#endif
#ifndef PROBE_LED_PIN
#define PROBE_LED_PIN     20  ///< GPIO20 — Status_LED_5 (probe health); J8 right pin 28; 330Ω series R15
#endif
```

Mirror these in `platformio.ini` build flags for both `[env:esp32-p4-eth]` and `[env:native]`:

```ini
-DDS18B20_DATA_PIN=19
-DPROBE_LED_PIN=20
```

### Library Dependencies

Add to `platformio.ini` `lib_deps`:

```ini
paulstoffregen/OneWire @ ^2.3.8
milesburton/DallasTemperature @ ^3.11.0
```

Both libraries are stable, widely used with arduino-esp32, and do not conflict with the
existing `ESPAsyncWebServer` / `AsyncTCP` dependencies.

### `firmware/src/web.cpp` Extension

In `handle_status()`, add `probe_get_temp_celsius()` to the JSON document:

```cpp
// Forward declaration from probe module
float probe_get_temp_celsius();

// In handle_status():
float probe_t = probe_get_temp_celsius();
if (probe_t > -100.0f) {
    doc["probe_temp_c"] = (float)((int)(probe_t * 10)) / 10.0f;
} else {
    doc["probe_temp_c"] = nullptr;  // ArduinoJson null → JSON null
}
```

The existing `temp_c` field (NTC board sensor) is unchanged. The new `probe_temp_c` field
is always present in the response (either a float or JSON `null`), which is the cleanest
API contract for clients (P-UI-03).

### `firmware/src/main.cpp` Extension

Call `probe_init()` in `setup()` after `temp_init()` and before `web_init()`:

```cpp
// Forward declaration
void probe_init();

// In setup():
fan_init();
temp_init();
probe_init();   // ← New: starts 1-Wire scan task and probe LED
ota_init();
```

### Fan Curve Integration (config module)

Extend the NVS config schema with a `curve_sensor` key:

```
curve_sensor: "ntc" | "probe" | "max"  (default: "ntc")
```

- `"ntc"` — use NTC board temperature only (existing behaviour, no regression)
- `"probe"` — use DS18B20 probe temperature (falls back to NTC if probe absent)
- `"max"` — use whichever of NTC and probe reads higher (safest for thermal management)

The fan curve calculation (when implemented) reads `config_get_curve_sensor()` and selects
the appropriate temperature source. This is a minimal hook; the full fan curve feature may be
tracked separately.

---

## Web UI Changes

The web UI (`data/` assets, served from LittleFS) requires one addition:

- Display `probe_temp_c` on the status page alongside the existing `temp_c` reading.
- Show "—" or "No probe" when `probe_temp_c` is `null`.
- No new page or endpoint required.

Estimated asset size delta: < 500 bytes (one additional DOM element and a JS field read).
Total LittleFS budget remains well within 200 kB (P-UI-02).

---

## Testing Strategy

### PlatformIO Native Unit Tests (`pio test -e native`)

The `probe` module's hardware-dependent 1-Wire bus operations (OneWire, DallasTemperature)
cannot be run natively. However the following logic CAN and MUST be unit-tested natively:

| Test | File | What is tested |
|---|---|---|
| `test_probe_sentinel` | `test/test_probe/test_probe.cpp` | `probe_get_temp_celsius()` returns −127.0f when state is PROBE_ABSENT |
| `test_probe_json_null` | `test/test_probe/test_probe.cpp` | When probe absent, `probe_temp_c` serialises as JSON `null` (not a number) |
| `test_probe_json_float` | `test/test_probe/test_probe.cpp` | When probe present with T=42.0, serialises as `42.0` |
| `test_probe_range_guard` | `test/test_probe/test_probe.cpp` | Readings outside −55..125°C are rejected; sentinel returned |
| `test_pins_no_conflict` (extend existing) | `test/test_pins/test_pins.cpp` | GPIO19 and GPIO20 are not equal to any existing pin constant |

These tests run in the `native` environment (P-TEST-05) and must pass in CI (P-TEST-06).

### Hardware Bring-up Checks

Extend the §8.4 checklist with the following steps (to be run after the standard 10-step sequence):

| Step | Action | Expected result |
|---|---|---|
| 11 | Connect DS18B20 probe to J6 | Status_LED_5 transitions: OFF → BLINK → SOLID within ~2 s |
| 12 | `curl http://poe-fanctrl.local/api/v1/status` with probe connected | `probe_temp_c` is a float in range 0–85 °C |
| 13 | Disconnect probe | Status_LED_5 returns to OFF within 5 s; `probe_temp_c` becomes `null` |
| 14 | Verify DATA pull-up voltage | Measure J6 pin 2 with no probe: should read 3.3 V (confirms R14 is working) |
| 15 | HTTP request latency during conversion | Continuous `curl` loop shows no requests taking > 500 ms (confirms non-blocking path) |

### Manual Integration Tests

- Set `curve_sensor` to `"probe"` in NVS; confirm fan duty changes when warming the probe
  by hand (not a hard requirement for initial landing; documents expected behaviour).
- Verify STATUS_LED_5 blink pattern matches specification at each probe state transition.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| GPIO19/20 not actually available on SKU 32088 J8 header (OQ-03 still open in generator) | Low — components.py documents them as NC with GPIO number comments | High | Verify with oscilloscope or GPIO toggle test before schematic submission; have GPIO21/22 as fallback |
| OneWire / DallasTemperature library incompatible with arduino-esp32 3.x | Low — both libraries are actively maintained and widely used | Medium | Test compile (`pio run -e esp32-p4-eth`) on feature branch before hardware changes |
| PCB right zone has insufficient room for J6 + LED6/R15 below J5 | Low — board is 78 mm tall and only uses ~60 mm for fan section | Medium | Check courtyard clearance in KiCad before committing layout; J6 can be placed at the bottom edge |
| 1-Wire timing violations on ESP32-P4 at 400 MHz core | Low — OneWire library uses direct GPIO bit-banging with µs timing; works on all ESP32 variants | Low | Validate with scope on DATA line; slow conversion (12-bit) is most tolerant of timing variance |
| DS18B20 noise from 25 kHz PWM traces | Low — 4.7 kΩ pull-up provides strong signal; short DATA trace recommended | Low | Keep DATA trace ≥ 1.5 mm from PWM traces; add PCB note in `ROUTING_PENDING.md` |
| Constitution amendment not completed before implementation | — | High | Amendment is gating step (Phase 0) — block all hardware/firmware changes until ratified |

---

## Constitution Compliance

| Principle | How This Plan Satisfies It |
|---|---|
| §2.2 BOM-lock | J6, R14, R15, LED6 are new additions (not replacements of locked components); additions do not require a MAJOR amendment — only a MINOR amendment to register GPIO19/20 in P-FW-02 |
| §2.3 Firmware stack | OneWire + DallasTemperature are Arduino libraries compatible with the locked `espressif32` PlatformIO platform and arduino-esp32 ≥ 3.x framework |
| §2.4 Web UI | `probe_temp_c` key added to existing endpoint; no new page; plain HTML/JS delta < 500 bytes; LittleFS budget unaffected |
| P-HW-01 | PCB remains 2-layer FR4; no layer additions |
| P-HW-02 | J6, R14, R15, LED6 all placed on F.Cu only |
| P-HW-03 | J6 placed on right edge consistent with J2–J5 |
| P-HW-04 | All new components in right zone (x > 21 mm); board outline unchanged |
| P-HW-05 / P-KI-04 | Schematic changes made in generator package only; `.kicad_sch` regenerated |
| P-HW-06 | All new schematic elements placed on 2.54 mm grid |
| P-HW-07 | DATA trace routed as 0.25 mm signal class |
| P-HW-08 | No new ground domains; single GND pour unchanged |
| P-FW-01 | New `probe` module introduced with single responsibility; no cross-module internals access |
| P-FW-02 | GPIO19/20 formally registered in P-FW-02 table via MINOR amendment before implementation |
| P-FW-03 | PWM specification unchanged; probe module does not touch LEDC |
| P-FW-04 | DS18B20 750 ms conversion runs in a FreeRTOS task; no blocking in async callbacks |
| P-FW-05 | Probe state initialises to PROBE_ABSENT on boot; no stale temperature exposed |
| P-POE-01 | No power class change; addition is < 50 mW, within 1.1 W margin |
| P-POE-02 | No primary-side changes |
| P-ISO-01–05 | DS18B20 circuit is SELV-only; no signal crosses the isolation barrier |
| P-SCH-01 | `DS18B20_DATA` net uses a global label |
| P-SCH-02 | Single GND domain; no `GND_PRI` on daughter board |
| P-SCH-03 | New section header "DS18B20 Temperature Probe" added in generator |
| P-SCH-04/05 | New symbols use correct pin types (passive for resistor/LED, bidirectional for DATA) |
| P-TEST-01 | Zero ERC errors required; verified via `kicad-cli sch erc` in CI |
| P-TEST-03 | Zero DRC errors required; verified via `kicad-cli pcb drc` in CI |
| P-TEST-05 | Native unit tests cover probe sentinel, JSON serialisation, range guard, pin conflict |
| P-TEST-06 | All native tests must pass in CI on every PR |
| P-UI-01 | Web UI delta uses plain JS only; no frameworks |
| P-UI-02 | Asset delta < 500 bytes; total ≤ 200 kB |
| P-UI-03 | `probe_temp_c`: float (one decimal) or `null`; under `/api/v1/status` GET |
| P-UI-04 | No C-string web assets; changes go in `data/` directory |
| P-KI-01 | KiCad 10.0.3 for all local edits |
| P-KI-05 | No new custom footprints required (screw terminal from KiCad standard library; LED/R from existing custom set) |
| P-KI-07 | PCB layout modified in KiCad GUI; no script writes to `.kicad_pcb` |
| P-CI-01 | PR touching `hardware/` triggers ERC + DRC gate |
| P-DEV-01 | Commits use `hw:`, `feat:`, `test:` prefixes as appropriate |
| P-DEV-04 | MINOR constitution amendment drafted and committed before any implementation file changes |

---

## Implementation Phases

### Phase 0 — Constitution MINOR Amendment (Blocking prerequisite)

> **No schematic, PCB, or firmware files may change until this phase is complete.**

**Deliverable:** Updated `docs/constitution.md` with:
- GPIO19 (`DS18B20_DATA`) added to P-FW-02 peripheral ownership table, owner: `probe`
- GPIO20 (`PROBE_LED`) added to P-FW-02 peripheral ownership table, owner: `probe`
- Amendment version bumped (MINOR)

### Phase 1 — Library Validation

**Before touching hardware files**, confirm firmware compiles with the new libraries:

1. Add `paulstoffregen/OneWire` and `milesburton/DallasTemperature` to `platformio.ini`
2. Write a stub `probe.cpp` with `probe_init()` / `probe_get_temp_celsius()` that compiles
3. Run `pio run -e esp32-p4-eth` — confirm zero errors

**Deliverable:** Compiling firmware stub on the feature branch.

### Phase 2 — Schematic Update

1. Update `hardware/generator/components.py`:
   - Add J6 (probe connector), R14 (pull-up), R15 (LED resistor), LED6 symbols
   - Update J8 symbol: pin 27 → `DS18B20_DATA` (bidirectional), pin 28 → `PROBE_LED` (output)
   - Add global labels `DS18B20_DATA` and `PROBE_LED`
   - Add section header "DS18B20 Temperature Probe"
2. Run `python hardware/generate_project.py` to regenerate `.kicad_sch`
3. Run `kicad-cli sch erc` — must report zero errors
4. Update `hardware/kicad/erc_output.json`

**Deliverable:** Updated `.kicad_sch` and `erc_output.json` committed.

### Phase 3 — PCB Layout Update

1. Open `hardware/kicad/PoE-FanController.kicad_pcb` in KiCad 10.0.3
2. Import updated netlist from regenerated schematic
3. Place J6, R14, R15, LED6 in right zone below J5
4. Route `DS18B20_DATA`, `PROBE_LED`, `+3V3`, and `GND` connections
5. Update GND copper pour; run DRC — must report zero errors
6. Commit updated `.kicad_pcb` and `drc_result.rpt`

**Deliverable:** Updated PCB layout committed with zero DRC errors.

### Phase 4 — Firmware Implementation

1. Create `firmware/include/probe.h` (public API: `probe_init`, `probe_get_temp_celsius`, `probe_get_state`)
2. Create `firmware/src/probe.cpp` (full FreeRTOS task implementation)
3. Update `firmware/include/pins.h` (`DS18B20_DATA_PIN=19`, `PROBE_LED_PIN=20`)
4. Update `firmware/platformio.ini` (build flags, lib_deps)
5. Update `firmware/src/web.cpp` (`probe_temp_c` in status response)
6. Update `firmware/src/main.cpp` (`probe_init()` call in `setup()`)
7. Extend config module with `curve_sensor` NVS key

**Deliverable:** Full firmware implementation on feature branch.

### Phase 5 — Unit Tests

1. Create `firmware/test/test_probe/test_probe.cpp` with all five native test cases
2. Extend `firmware/test/test_pins/test_pins.cpp` with GPIO19/20 conflict checks
3. Run `pio test -e native` — must pass

**Deliverable:** All native tests passing.

### Phase 6 — Hardware Bring-up

1. Fabricate or hand-assemble updated PCB
2. Execute standard bring-up checklist (§8.4 steps 1–10) plus new steps 11–15
3. Log results

**Deliverable:** Bring-up log committed to `docs/` or PR comment.

### Phase 7 — Web UI Update

1. Add `probe_temp_c` display to `data/index.html` (or equivalent status page)
2. Verify total LittleFS asset size ≤ 200 kB
3. Upload with `pio run -e esp32-p4-eth --target uploadfs`

**Deliverable:** Updated web UI asset committed.

### Phase 8 — Pull Request and Gerber Export

1. Open PR against `main` on branch `feature/97-ds18b20-temperature-probe`
2. CI must pass: ERC (0 errors), DRC (0 errors), `pio test -e native` (all pass),
   `pio run -e esp32-p4-eth` (build clean)
3. After merge, trigger release workflow — DRC gate before Gerber export (P-CI-02)

---

## GPIO Pin Recommendation — Summary

> **Recommended 1-Wire DATA GPIO: GPIO19 (J8 left pin 27)**
>
> | Attribute | Value |
> |---|---|
> | GPIO number | 19 |
> | J8 header position | Left side, pin 27 |
> | Current state | NC (no_connect) in `hardware/generator/components.py` |
> | Strapping pin? | No |
> | Conflicts with existing peripherals? | None — confirmed against all entries in `firmware/include/pins.h` and `docs/constitution.md` §4 P-FW-02 |
> | Pull-up | External 4.7 kΩ resistor R14 on DATA net (required for 1-Wire) |
> | `pins.h` macro | `DS18B20_DATA_PIN 19` |
> | PlatformIO build flag | `-DDS18B20_DATA_PIN=19` |
>
> **Recommended Status_LED_5 GPIO: GPIO20 (J8 right pin 28)**
>
> | Attribute | Value |
> |---|---|
> | GPIO number | 20 |
> | J8 header position | Right side, pin 28 |
> | Current state | NC in `hardware/generator/components.py` |
> | Conflicts? | None |
> | `pins.h` macro | `PROBE_LED_PIN 20` |
> | PlatformIO build flag | `-DPROBE_LED_PIN=20` |
