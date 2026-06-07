# PoE FanController Development Guidelines

<!-- Last updated: 2026-06-06 -->

## Project Overview

PoE-FanController is an open-hardware device that controls PWM fans using Power over Ethernet (PoE) as its sole power source. An ESP32 microcontroller monitors ambient temperature and adjusts fan speeds accordingly. All configuration is handled via a web interface hosted on the device itself.

## Technology Stack

### Hardware
- **PCB design**: KiCad 10.x (schematic + layout) — current install: **KiCad 10.0.3**
  - Schematic file format version: `20260101`
  - PCB file format version: `20260206`
  - Always use these version codes in generated `.kicad_sch` / `.kicad_pcb` files to avoid "older version" warnings
  - `kicad-cli` path: `C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe`
- **Microcontroller**: ESP32 (ESP-WROOM-32 or ESP32-S3 module)
- **Power input**: PoE 802.3af (15.4 W) / 802.3at (30 W) via dedicated PD controller IC
- **Fan outputs**: 4-wire PWM fans controlled via ESP32 LEDC peripheral (25 kHz)
- **Temperature sensing**: I2C sensors (BME280 / SHT3x) or 1-Wire (DS18B20)
- **PCB**: 2-layer, FR4, designed for standard fabrication (JLCPCB / PCBWay)

### Firmware
- **Build system**: PlatformIO (platformio.ini at repo root or `firmware/`)
- **Framework**: Arduino for ESP32 (espressif32 platform) — unless ESP-IDF is justified
- **Language**: C/C++ (C++17)
- **Web server**: ESPAsyncWebServer
- **File system**: LittleFS (web assets stored as SPIFFS/LittleFS partition)
- **Unit testing**: PlatformIO native environment with Unity test framework
- **OTA updates**: ArduinoOTA or ESP-IDF OTA

### Web Interface
- Plain HTML / CSS / JavaScript (no framework — must fit in ESP32 flash)
- Served from LittleFS; REST API provided by firmware
- Responsive, mobile-friendly

## Repository Structure

```text
hardware/
  kicad/
    PoE-FanController.kicad_sch   ← schematic
    PoE-FanController.kicad_pcb   ← PCB layout
    symbols/                       ← custom schematic symbols
    footprints/                    ← custom PCB footprints
  bom/                             ← bill of materials
  gerbers/                         ← fabrication outputs
firmware/
  platformio.ini
  src/
    main.cpp
    fan_control.cpp / fan_control.h
    temp_sensor.cpp / temp_sensor.h
    web_server.cpp / web_server.h
    config.cpp / config.h
  include/
  test/                            ← PlatformIO native unit tests
  data/                            ← LittleFS web assets
    index.html
    style.css
    app.js
docs/
  constitution.md                  ← authoritative technology choices
  architecture.md                  ← hardware + firmware architecture
  developer-setup.md
  features/
    <feature-name>/
      spec.md
      plan.md
      tasks.md
test-results/
```

## Build Commands

```powershell
# Firmware: build
pio run -e esp32dev

# Firmware: unit tests (native)
pio test -e native

# Firmware: upload to device
pio run -e esp32dev --target upload

# Firmware: upload filesystem (web assets)
pio run -e esp32dev --target uploadfs

# KiCad ERC (command-line, if kicad-cli available)
kicad-cli sch erc hardware/kicad/PoE-FanController.kicad_sch

# KiCad DRC
kicad-cli pcb drc hardware/kicad/PoE-FanController.kicad_pcb
```

## Code Style

- C/C++ firmware: follow Google C++ style guide conventions; use `.clang-format` if present
- All firmware functions must have Doxygen-style comments for public API
- No magic numbers — define constants with meaningful names in `config.h`
- Hardware: one KiCad project per board; one hierarchical sheet per major subsystem

## Critical Hardware Constraints

- **PoE isolation**: maintain ≥ 1.5 kV isolation between PoE input and low-voltage side
- **Creepage/clearance**: follow IEC 60950 / IEC 62368 for mains-adjacent voltages
- **EMC**: follow PoE PD controller reference design for layout and filtering
- **Thermal**: verify power dissipation for linear regulators and PoE PD controller

<!-- MANUAL ADDITIONS START -->

## Knowledge Base (KB) — Read Before Spending Cloud Credits

The `docs/kb/` directory contains pre-loaded domain facts for this project.
**Check these files before spawning any expert sub-agent or doing web searches.**

| File | Use for |
|---|---|
| `docs/kb/kicad-10-reference.md` | KiCad 10 format, ERC/DRC baselines, schematic conventions |
| `docs/kb/esp32-p4-reference.md` | RMII fixed pins, GPIO allocation, PlatformIO config, LEDC 3.x API |
| `docs/kb/poe-reference.md` | 802.3at class table, Ag9905M specs, power budget |
| `docs/kb/component-library.md` | All project MPNs, KiCad footprints, datasheet facts |
| `docs/kb/model-routing.md` | Which model/approach to use for each task type |
| `docs/kb/local-ai-setup.md` | Ollama installation and usage for free local inference |

**KB-First rule:** If the answer is in the KB, answer directly — no sub-agent, no web search.
After any expert consultation that produces a new verified fact, **update the KB file** and commit it.

## Model Routing — Use the Cheapest Appropriate Model

| Task complexity | Model choice |
|---|---|
| Simple: grep, edit, YAML validate, boilerplate from template | Local Ollama (`qwen2.5-coder:7b`) |
| Medium: GitHub API, file exploration, issue enrichment | Cloud Haiku (`claude-haiku-4.5`) |
| Complex: architecture, novel code, multi-domain reasoning | Cloud Sonnet (`claude-sonnet-4.6`) |

When calling the `task` tool for sub-agents, pass `model: "claude-haiku-4.5"` for:
- `explore` agents doing file/code searches
- `github.issues-manager` doing simple CRUD operations
- `github.action-manager` checking CI status

Keep `claude-sonnet-4.6` only for: `architect`, `implementer` (complex tasks), `feature.planner`, `rubber-duck`.

**Single biggest credit saver:** do direct tool calls (view + edit + powershell) instead of
spawning a sub-agent for tasks that take ≤ 5 tool calls.

<!-- MANUAL ADDITIONS END -->
