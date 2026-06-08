# Feature: External DS18B20 Temperature Probe Support

<!-- Issue: #97 | Branch: feature/97-ds18b20-temperature-probe | Status: PLANNING -->
<!-- Constitution reference: v3.1.0 | Spec date: 2026-06-08 -->

---

## Overview

This feature adds a hardware-accessible external temperature sensing point to the PoE
FanController daughter board, using a DS18B20 1-Wire digital temperature sensor.
A 3-pin screw-terminal or JST connector (GND, DATA, VCC) is placed on the right edge
of the board alongside the existing four fan headers (J2–J5). A dedicated status LED
(Status_LED_5) mirrors the per-fan LED pattern and gives at-a-glance visibility of the
probe's connection state. Firmware scans the 1-Wire bus on startup, reads temperature
periodically, exposes the value on the existing `/api/v1/status` endpoint, and can use
it as an optional sensor source for fan curve control — supplementing the on-board NTC
thermistor (NTC1) that measures board temperature.

---

## User Stories

- As an operator, I want to connect a DS18B20 probe to measure intake or exhaust air
  temperature so that fan curves reflect actual airflow conditions rather than board
  temperature alone.
- As an operator, I want a status LED beside the probe connector so that I can confirm
  at a glance whether the probe is detected and reading normally, without needing a
  serial console.
- As a developer, I want the probe temperature exposed over the REST API so that
  external automation can consume it alongside fan RPM and duty data.
- As a developer, I want the 1-Wire implementation isolated in its own firmware module
  so that it can be tested independently and does not interfere with existing fan or
  NTC modules.

---

## Functional Requirements

1. **FR-01** — The daughter board shall provide a 3-pin connector (GND, DATA, VCC)
   accessible from the right board edge, sized to accept a standard DS18B20 pigtail
   or equivalent 3-wire probe.

2. **FR-02** — The DATA line of the connector shall be pulled up to +3.3V via a
   4.7 kΩ resistor on the daughter board (mandatory for DS18B20 1-Wire operation).

3. **FR-03** — A firmware-controlled status LED (Status_LED_5) shall be placed on
   the PCB adjacent to the probe connector, consistent in component type and
   current-limiting circuit with the existing per-fan status LEDs.

4. **FR-04** — The DATA line shall be routed to a dedicated, conflict-free GPIO on
   the ESP32-P4-POE-ETH via the J8 header.

5. **FR-05** — On startup the firmware shall scan the 1-Wire bus and attempt to
   locate a DS18B20 device.

6. **FR-06** — When a DS18B20 is detected, firmware shall initiate periodic
   (non-blocking) temperature conversions and read the result.

7. **FR-07** — When no DS18B20 is detected, the firmware shall report a sentinel
   value (e.g. `null` or `−127.0°C`) rather than a stale or fabricated reading.

8. **FR-08** — The Status_LED_5 shall be driven by firmware to indicate probe state:
   - **Off** — no probe detected on bus
   - **Slow blink (1 Hz)** — probe detected, conversion in progress or warming up
   - **Solid on** — probe detected, last reading valid

9. **FR-09** — The probe temperature shall be included in the `GET /api/v1/status`
   JSON response under a new `probe_temp_c` key (float, one decimal place, or `null`
   when no probe detected). This must not break existing API clients.

10. **FR-10** — The probe temperature shall be available as an optional fan curve
    sensor source. When selected as the active curve sensor, fan duty shall be
    calculated from probe temperature instead of (or in addition to) the NTC reading.

11. **FR-11** — The probe data path shall be non-blocking; 1-Wire bus operations
    must not stall the ESPAsyncWebServer callback task or the ETH stack.

12. **FR-12** — All new schematic symbols and PCB footprints shall be captured in the
    generator package (`hardware/generator/`) and pass ERC with zero errors.

13. **FR-13** — All new PCB components shall be placed on F.Cu (top layer) only
    and within the right zone (x > 21 mm), consistent with P-HW-02 and P-HW-04.

---

## Non-Functional Requirements

- **NFR-01 Power** — The DS18B20 in parasite-power mode draws ≤ 1.5 mA from the DATA
  line pull-up. In VCC-powered mode it draws ≤ 1.5 mA from +3.3V. Either is negligible
  against the existing 5.5% PoE power margin; no budget re-evaluation needed.
- **NFR-02 Timing** — DS18B20 temperature conversion takes up to 750 ms (12-bit mode).
  The firmware read cycle must not block for longer than a single FreeRTOS tick at any
  point; the full conversion must run asynchronously.
- **NFR-03 Accuracy** — DS18B20 specified accuracy ±0.5 °C (−10 to +85 °C). No
  firmware calibration correction is required in v1.
- **NFR-04 EMC** — The DATA trace from the probe connector to GPIO19 shall be kept
  short (< 50 mm on PCB) and routed away from the 25 kHz PWM traces (J2–J5) to
  minimise noise coupling.
- **NFR-05 Safety** — The DS18B20 probe is SELV-domain only; it must not be connected
  to the +12V fan rail. Connector pinout and silkscreen must unambiguously label GND,
  DATA, and VCC (3.3V).
- **NFR-06 Firmware size** — The DallasTemperature and OneWire libraries are compact;
  combined addition to flash is estimated < 10 kB, well within the 32 MB flash of the
  Waveshare board.
- **NFR-07 LittleFS budget** — No new web assets are strictly required; any UI changes
  (adding `probe_temp_c` display) must keep total LittleFS asset size ≤ 200 kB (P-UI-02).
- **NFR-08 ERC/DRC** — The schematic must achieve zero ERC errors and the PCB zero DRC
  errors post-implementation, per P-TEST-01 and P-TEST-03.

---

## Success Criteria

| ID | Criterion | Verification method |
|---|---|---|
| SC-01 | Probe connector present on schematic (ERC clean) and PCB (DRC clean) | `kicad-cli sch erc` + `kicad-cli pcb drc` — 0 errors |
| SC-02 | 4.7 kΩ pull-up resistor on DATA net visible in schematic | Schematic visual review; net continuity check |
| SC-03 | GPIO19 assigned in `pins.h` as `DS18B20_DATA_PIN`; no conflict with existing pins | Static analysis: `grep` pins.h for GPIO19 |
| SC-04 | GPIO20 assigned in `pins.h` as `PROBE_LED_PIN`; no conflict | Static analysis: `grep` pins.h for GPIO20 |
| SC-05 | Firmware detects a DS18B20 and reads a temperature in range −55 to +125 °C | Hardware bring-up: serial log shows `[PROBE] DS18B20 found, T=xx.x°C` |
| SC-06 | `GET /api/v1/status` includes `probe_temp_c` field (float or null) | `curl` against live device; JSON schema check |
| SC-07 | Status_LED_5 is OFF with no probe, BLINKING during read, SOLID when valid | Hardware bring-up: visual inspection |
| SC-08 | 1-Wire read task does not block ESPAsyncWebServer (HTTP requests succeed during conversion) | Stress test: poll `/api/v1/status` continuously while probe reads; no timeout |
| SC-09 | PlatformIO native unit tests pass (`pio test -e native`) | CI: `pio test -e native` exit code 0 |
| SC-10 | Power consumption increase < 10 mA at 3.3V rail | Bring-up: measure 3.3V rail current with/without probe |

---

## Out of Scope

- Multi-probe support (more than one DS18B20 on the bus) — single-probe design only in v1.
- Parasite power mode — VCC-powered mode only (3-pin connector provides dedicated VCC).
- DS18B20 address configuration via web UI — first detected address is used automatically.
- MQTT or other push protocols for temperature data — REST polling only in v1.
- Fan headers footprint change (forced-orientation 4-pin) — tracked separately in issue #99.
- DS18B20 parent feature scope beyond hardware + firmware — see issue #98.

---

## Assumptions

1. The DS18B20 probe is operated in VCC-powered mode (not parasite power); the 3-pin
   connector provides separate GND, DATA, and VCC (3.3V) pins.
2. Exactly one DS18B20 is connected at a time; the firmware targets the first discovered
   address without requiring ROM code configuration.
3. The DallasTemperature and OneWire Arduino libraries are compatible with arduino-esp32
   ≥ 3.x and the PlatformIO `espressif32` platform at the project-locked version.
4. GPIO19 and GPIO20 are general-purpose, output-capable, non-strapping GPIO lines on the
   ESP32-P4-POE-ETH (SKU 32088) routed to J8 pins 27 (left) and 28 (right) respectively,
   as documented in `hardware/generator/components.py`.
5. The existing PCB has sufficient right-zone space to place one additional connector and
   one LED + resistor pair within the 78 × 56 mm board outline without violating
   courtyard rules.
6. A constitution MINOR amendment is required to formally register GPIO19 and GPIO20 in
   the P-FW-02 peripheral ownership table before implementation begins.

---

## Open Questions

None. All ambiguities were resolved from the issue body, codebase, and hardware files.
