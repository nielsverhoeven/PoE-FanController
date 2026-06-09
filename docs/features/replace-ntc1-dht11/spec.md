# Feature: Replace NTC1 Thermistor with DHT11 Temperature + Humidity Sensor

<!-- Issue: #135 | Branch: feature/135-replace-ntc1-dht11-sensor | Status: PLANNING -->
<!-- Constitution reference: v4.0.0 | Spec date: 2026-06-09 -->

---

## Overview

This feature replaces the on-board NTC1 thermistor (10 kΩ B=3950) and its associated
voltage-divider resistor (R4) with a DHT11 digital temperature + humidity breakout module
(Reichelt product 239086; 3-pin 2.54 mm through-hole: VCC / DATA / GND).  The ADC-based
Steinhart-Hart temperature path is retired; a single-wire digital protocol driver takes its
place on the same GPIO (GPIO16 / J8 pin 23).  The upgrade adds relative-humidity measurement
as a new sensor channel alongside the already-present DS18B20 external probe, enabling
humidity-aware fan control algorithms in future firmware work.  This feature requires a MINOR
constitution amendment (§2.2 BOM, §2.3 firmware table, and P-FW-02 peripheral table) before
any implementation work begins.

---

## User Stories

- As an operator, I want the fan controller to report both ambient temperature and relative
  humidity via the REST API so that I can build humidity-aware automation on top of it.
- As an operator, I want to use a low-cost breakout module rather than a bare thermistor so
  that no external calibration or Steinhart-Hart coefficient management is required.
- As a developer, I want humidity data in the `/api/v1/status` JSON payload so that
  dashboards and scripts can consume it without additional endpoints.
- As a developer, I want the NTC ADC path entirely removed from firmware so that the ADC
  peripheral on GPIO16 is freed and the code surface is simplified.
- As a developer, I want clear separation between the on-board DHT11 driver and the existing
  DS18B20 external probe module so that each can be tested independently.

---

## Functional Requirements

1. **FR-01** — The NTC1 thermistor (Murata NCP15XH103F03RC) shall be removed from the
   daughter board BOM and PCB.

2. **FR-02** — The R4 resistor (10 kΩ NTC voltage-divider pull-up) shall be removed from
   the daughter board BOM and PCB.

3. **FR-03** — The daughter board shall provide a polarized 3-pin keyed connector (J9,
   Molex KK-254 / 22-01-3037, 2.54 mm pitch) on the right board edge for cable-connecting
   a DHT11 breakout module; pin order shall be: Pin 1 → GND, Pin 2 → DHT11_DATA, Pin 3 →
   +3V3 (consistent with J6 DS18B20 probe connector).  This connector is subject to P-HW-09
   (polarized latching housing mandatory for external cable connectors).

4. **FR-04** — The schematic net formerly named `NTC_ADC` on J8 pin 23 shall be renamed
   `DHT11_DATA`; all schematic labels and generator code using `NTC_ADC` for this GPIO shall
   be updated accordingly.

5. **FR-05** — The firmware `temp` module shall be rewritten to drive the DHT11 single-wire
   protocol on GPIO16 (`DHT11_DATA_PIN`).  The ADC read and Steinhart-Hart calculation shall
   be completely removed.

6. **FR-06** — The firmware shall perform periodic (non-blocking) DHT11 reads at an interval
   of no less than 2 seconds, storing the result in module-static variables.

7. **FR-07** — The firmware shall expose `temp_read_celsius()` (board temperature from DHT11)
   and a new `temp_read_humidity_pct()` function (relative humidity) for consumption by the
   `web` module.

8. **FR-08** — On a DHT11 read error the firmware shall retain and return the last valid
   reading for up to 10 consecutive failures before substituting a sentinel value (–999.0f
   for temperature, –1.0f for humidity).

9. **FR-09** — The `GET /api/v1/status` JSON response shall include a `humidity_pct` field
   (float, one decimal place, or `null` on sensor fault) alongside the existing `temp_c`
   field.

10. **FR-10** — The pin constant `NTC_ADC_PIN` in `firmware/include/pins.h` shall be renamed
    to `DHT11_DATA_PIN` (retaining the value `16`).  All NTC-specific constants
    (`NTC_SERIES_OHM`, `NTC_NOMINAL_OHM`, `NTC_BETA`, `NTC_NOMINAL_TEMP`) shall be removed.

11. **FR-11** — The constitution (§2.2, §2.3, and P-FW-02) shall be amended before any
    schematic, PCB, or firmware changes are committed to the branch.

---

## Non-Functional Requirements

1. **NFR-01 — Temperature accuracy.** DHT11 temperature accuracy is ±2 °C.  This is
   acceptable for fan-speed control decisions.  No further calibration is required.

2. **NFR-02 — Humidity accuracy.** DHT11 relative-humidity accuracy is ±5 % RH (20–80 % RH
   range, 25 °C).  This is sufficient for the targeted use case.

3. **NFR-03 — Supply voltage.** DHT11 VCC is 3.0–5.5 V.  The 3.3 V rail supplied via J8 is
   within spec.

4. **NFR-04 — Pull-up.** DHT11 DATA requires a 4.7–10 kΩ pull-up to VCC.  The Reichelt 239086
   breakout module is assumed to include this resistor onboard (see Assumptions §A-01).
   No additional pull-up resistor shall be placed on the daughter board PCB unless the
   datasheet confirms the breakout lacks one.

5. **NFR-05 — Power budget.** DHT11 active current ≤ 2.5 mA at 3.3 V (< 10 mW).  This is
   negligible versus the 1.1 W PoE budget margin documented in §5.2.  No re-evaluation is
   required.

6. **NFR-06 — Read timing.** DHT11 minimum inter-read interval is 1 second.  Firmware must
   enforce a minimum of 2 seconds to include margin.

7. **NFR-07 — DHT11 read latency.** A single DHT11 read takes approximately 2 ms.  This must
   not occur inside an ESPAsyncWebServer callback (P-FW-04); reads shall be offloaded to a
   FreeRTOS timer or dedicated task.

8. **NFR-08 — LittleFS budget.** No new web assets are added; the 200 kB LittleFS budget
   (P-UI-02) is unaffected.

9. **NFR-09 — PCB rule compliance.** Replacement footprint must be placed on F.Cu only
   (P-HW-02), must produce zero DRC errors (P-TEST-03), and must not violate courtyard
   clearances.

---

## Success Criteria

| ID | Criterion | Verifiable by |
|---|---|---|
| SC-01 | Schematic regenerates with zero ERC errors after NTC1/R4 removal and DHT11 connector addition | `python hardware/generate_project.py` + `kicad-cli sch erc` |
| SC-02 | PCB layout passes DRC with zero errors after footprint replacement | `kicad-cli pcb drc` |
| SC-03 | `hardware/bom/bom.csv` contains no NTC1 or R4 row; contains one DHT11 breakout row | Inspect bom.csv |
| SC-04 | `firmware/include/pins.h` contains `DHT11_DATA_PIN = 16` and no `NTC_ADC_PIN` or NTC constants | Code review |
| SC-05 | `firmware/src/temp.cpp` contains no ADC read or Steinhart-Hart logic | Code review |
| SC-06 | `GET /api/v1/status` response JSON includes `temp_c` (from DHT11) and `humidity_pct` | Integration test via HTTP on physical board |
| SC-07 | DHT11 temperature reading falls within ±3 °C of a calibrated reference thermometer | Manual bring-up test |
| SC-08 | DHT11 humidity reading falls within ±8 % RH of a reference hygrometer | Manual bring-up test |
| SC-09 | Constitution amendment (§2.2, §2.3, P-FW-02) committed before any hardware/firmware changes | Git log inspection |
| SC-10 | CI pipeline (ERC, DRC, PlatformIO native tests) passes on the feature PR | GitHub Actions |

---

## Out of Scope

- Fan curve algorithm changes based on humidity data (addressed separately if needed).
- Humidity-based thresholds in NVS configuration schema.
- Any changes to the DS18B20 external probe (`probe` module) or its connector J6.
- Physical DHT11 sensor calibration or factory offset correction.
- I2C or SPI alternative temperature/humidity sensors.

---

## Assumptions

| ID | Assumption |
|---|---|
| A-01 | The Reichelt 239086 DHT11 breakout includes a DATA pull-up resistor (typically 10 kΩ) onboard. **Must be verified against the module datasheet / PCB silkscreen before PCB layout is finalised (constitution §2.2 DHT11 note).** If no onboard pull-up exists, a 10 kΩ resistor must be added to the daughter board PCB between DHT11_DATA and +3V3, and that resistor must be locked in §2.2 via a further PATCH amendment before routing. |
| A-02 | GPIO16 is available as a digital I/O pin on ESP32-P4 with no ADC dependency once the ADC path is removed; it is not a strapping pin and is not used by EMAC or UART. |
| A-03 | The DHT11 firmware library is TBD and must be confirmed with `esp32.expert` before Stage 4 implementation.  Constitution §2.3 recommends `adafruit/DHT sensor library` or an equivalent arduino-esp32 ≥ 3.x compatible library. |
| A-04 | The DHT11 breakout module connects to J9 via a 3-pin cable assembly (crimped Molex KK-254 female housing, same as DS18B20 probe cable to J6). |

---

## Open Questions

_None. All ambiguities have been resolved or captured as verifiable assumptions above._
