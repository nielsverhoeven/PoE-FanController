# Technical Plan: Replace ESP32-WROOM-32D with ESP32-P4

<!-- Issue: #40 | Branch: feature/40-replace-esp32-with-esp32-p4 | Status: PLANNING -->
<!-- Constitution reference: v1.1.0 | Plan date: 2026-06-07 -->

---

## 1. Architecture Fit

This change replaces **U3 (ESP32-WROOM-32D)** — the main MCU — with an **ESP32-P4** module,
transitioning the device's network connectivity from WiFi to wired 10/100BASE-T Ethernet. It
directly touches three of the five functional schematic blocks defined in `generate_project.py`
and the `docs/constitution.md` firmware architecture:

| Schematic block | Impact |
|---|---|
| `ESP32-WROOM-32` block | **Full replacement** — new symbol, footprint, GPIO re-map, section header rename |
| `USB / UART Bridge` block | **Evaluation required** — CH340C may become redundant if P4 native USB is used |
| `PoE Power Input` block | **New sub-block** — Ethernet data signals currently unused; must be routed to PHY |
| `3.3V Regulator (LM2596)` | **Power budget update only** — regulator is adequate; no topology change |
| `Fan Headers (4× PWM)` | **Net rename only** — FAN{1-4}_PWM and FAN{1-4}_TACH reconnect to new GPIO numbers |

**Constitution principles directly invoked:**

| Principle | Relevance |
|---|---|
| §2.2 BOM-lock + §9 MAJOR amendment | U3 is BOM-locked; amendment must precede all implementation |
| P-HW-05 / P-KI-04 | All schematic changes via `generate_project.py`; no hand-editing `.kicad_sch` |
| P-KI-05 | New `Custom:ESP32-P4` symbol and footprint must be in-project |
| P-SCH-01/02/03/04/05 | Global labels, ground domain separation, section headers, power pin types |
| P-ISO-02/05 | All new components must remain east of x = 38 mm; no secondary signal crosses barrier |
| P-TEST-01 / P-CI-01 | Zero ERC errors; CI must enforce ERC on every PR touching `hardware/` |
| P-POE-02 | Primary-side circuitry (J1, U1) must not be restructured; PHY is secondary-side |
| P-FW-01/02 | Firmware modules and peripheral ownership table must be updated in constitution §4 |

---

## 2. Phase 0 — Constitution MAJOR Amendment (Prerequisite)

> **This phase blocks all implementation. No schematic, PCB, or firmware files may change until
> the amendment is ratified by the architect.**

Per constitution §9 (P-DEV-04), any BOM-locked component substitution requires a documented
MAJOR amendment with expert consultation before work begins.

### 2.1 Decisions That Must Be Resolved in Phase 0

The following decisions must be made and recorded in the amendment **before** any implementation
work begins. Recommended positions are provided below as starting points for the expert review.

#### Decision 0-A: Target Module MPN

**Recommended:** `ESP32-P4-MINI-1U-N16R8` (Espressif Systems)

| Attribute | Value |
|---|---|
| Core | RISC-V HP dual-core @ 400 MHz + LP core @ 40 MHz |
| Flash | 16 MB (N16 variant) |
| PSRAM | 8 MB (R8 variant) |
| Package | LGA (Land-Grid Array), 25.4 × 19.0 × 3.1 mm PCB module |
| WiFi | **None** |
| Bluetooth | **None** |
| Ethernet MAC | Built-in 10/100 EMAC with RMII interface |
| USB | Native USB OTG (USB 2.0 FS/HS) |
| Supply voltage | 3.3 V (compatible with existing LM2596S-3.3 rail) |
| PlatformIO board ID | `esp32-p4-function-ev-board` (Phase 0 must confirm final board def) |

> **Assembly note:** The ESP32-P4-MINI-1U is a castellation-edge LGA module (not BGA die), making
> it suitable for standard SMT assembly with paste and reflow — comparable complexity to the
> WROOM-32D. A custom footprint is required (see §2.2 BOM-lock amendment and Phase 1).
>
> **Alternative:** If the MINI-1U proves to be unavailable at procurement time, the `ESP32-P4-MINI-1`
> (non-U variant, no external antenna connector) is the fallback. The amendment must record which
> variant is procured.

#### Decision 0-B: Ethernet PHY MPN

**Recommended:** `LAN8720A-CP-TR` (Microchip Technology), QFN-24 package

| Attribute | Value |
|---|---|
| Interface | RMII (Reduced Media-Independent Interface) |
| Speed | 10/100BASE-T |
| Supply | 3.3 V (single-rail, compatible with existing +3V3) |
| Package | QFN-24, 4 × 4 mm |
| REF_CLK | 50 MHz; sourced from ESP32-P4 REF_CLK output (GPIO50 on P4 EVB reference) |
| MDIO/MDC | Management interface to ESP32-P4 |
| KiCad footprint | `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` (standard library) |
| Magnetics | Uses existing J1 (Würth 615008144521) integrated magnetics on secondary data side |
| BOM-lock requirement | **Yes** — new entry in constitution §2.2 MAJOR amendment |

> **Rationale for LAN8720A:** This is the same PHY family used by the official Espressif
> ESP32-Ethernet-Kit (LAN8720A); the `esp-idf` ETH driver for RMII+LAN8720 is mature and tested.
> The `arduino-esp32` 3.x Ethernet library (`ETH.h`) directly supports it via
> `ETH.begin(ETH_PHY_LAN8720, ...)`.
>
> **Alternative:** `DP83848IVV` (TI, QFP-32) — larger footprint but well-characterised; use if
> LAN8720A supply is constrained.

#### Decision 0-C: CH340C Disposition

**Recommended for v0.2: Retain CH340C (U4).**

Rationale: The ESP32-P4 native USB OTG is functional but the `esptool.py` auto-reset circuit
(DTR → EN, RTS → BOOT) is already implemented for CH340C. Retaining U4 avoids a second BOM
amendment. The CH340C stays as the programming/debug interface; the J6 USB-C port is unchanged.

The native USB OTG capability of the P4 can be exploited in a future minor amendment once the
RMII + firmware stack is validated.

> If the architect decides to remove CH340C: that requires a separate MAJOR amendment (U4 is
> BOM-locked in §2.2). This plan does **not** cover CH340C removal.

#### Decision 0-D: OTA Strategy

**Recommended:** HTTP OTA over wired Ethernet using `esp_https_ota` (IDF) / `Update.h` (Arduino).

The `ArduinoOTA` library (mDNS + UDP over WiFi) must be removed. Replacement:
- Firmware exposes `POST /api/v1/ota` endpoint accepting a binary upload
- The `web` module (P-FW-01) handles the upload; calls `Update.begin()` / `Update.write()` /
  `Update.end()` from `Update.h`
- UART fallback via CH340C / J6 remains available at all times via `esptool.py`
- This requires a constitution §2.3 amendment to the OTA row

#### Decision 0-E: PlatformIO Board Definition

**Recommended board:** `esp32-p4-function-ev-board`

This is the closest available PlatformIO board definition for the ESP32-P4 as of arduino-esp32 v3.x
(IDF 5.3). A custom board manifest (`boards/esp32-p4-mini-1.json`) may be needed in the firmware
repository if the MINI-1U variant requires different flash/PSRAM configuration.

- **Platform:** `espressif32` at version ≥ 6.9.0 (first release supporting `esp32p4` target)
- **Framework:** `arduino` with `arduino-esp32` ≥ 3.1.0

> Arduino-esp32 3.x uses IDF 5.3+ and provides `ETH.h` with Ethernet MAC+PHY support.
> Confirm exact minimum version during Phase 0 research.

### 2.2 Amendment Procedure

1. **Draft the amendment text** in `docs/constitution.md` §10 (Amendment History):
   - Version bump: `1.1.0` → `2.0.0` (MAJOR)
   - Update §2.2 table: replace U3 row; add PHY (U5) row
   - Update §2.3 firmware table: board, framework version, OTA row, web server row
   - Update §4 P-FW-02 peripheral ownership table: new GPIO assignments, EMAC entry, remove WiFi
   - Update §5.2 power budget table (see §8 of this plan)
   - Add EMAC/Ethernet section to §5 if appropriate

2. **Expert consultations required** (per P-DEV-04):
   - `hw.expert` — for U3 and U5 BOM changes, footprint, power budget
   - `fw.expert` — for PlatformIO target, arduino-esp32 version, RMII driver, OTA strategy
   - `poe.expert` — to confirm PHY placement does not violate P-POE-02 (PHY is secondary-side, ✓)

3. **Commit the ratified amendment** to `docs/constitution.md` **before** any other file in this
   feature branch changes.

---

## 3. Phase 1 — Component Selection Research

> Prerequisite: Phase 0 approved.
> Output: Confirmed MPNs, confirmed PlatformIO support, confirmed footprint strategy.

### 3.1 ESP32-P4 Module Research Checklist

- [ ] Download and review ESP32-P4-MINI-1 datasheet; extract exact pin list and pad numbers
- [ ] Confirm RMII pin assignments (fixed vs GPIO-matrix) from ESP32-P4 TRM Chapter on EMAC
- [ ] Confirm all required strapping pins and boot-mode configuration (GPIO0 equivalent)
- [ ] Confirm ADC channel available for NTC (ADC1 or ADC2; note ADC2 is not usable during WiFi
      on ESP32 — not an issue here since P4 has no WiFi, but confirm ADC2 availability)
- [ ] Extract footprint courtyard dimensions; determine if PCB placement at U3 position (65, 53 mm)
      needs adjustment given P4-MINI-1 dimensions vs WROOM-32D
- [ ] Verify no KiCad standard-library footprint exists; plan custom footprint in
      `hardware/kicad/footprints/` (P-KI-05)
- [ ] Confirm the module has castellation/LGA edges suitable for the `embed_footprint()` approach
      used by `generate_project.py` (requires a `.kicad_mod` file to be authored and committed)

### 3.2 LAN8720A Research Checklist

- [ ] Download LAN8720A datasheet; extract RMII pin table
- [ ] Confirm 50 MHz REF_CLK sourcing: P4 output → PHY (preferred) vs external oscillator
- [ ] Confirm `arduino-esp32` `ETH.h` API call: `ETH.begin(ETH_PHY_LAN8720, PHY_ADDR, MDC_PIN, MDIO_PIN, PWR_PIN, ETH_CLOCK_GPIO_OUT_1)`
- [ ] Identify required decoupling network: typically 100 nF × 4 on each VDD pin + 10 µF bulk
- [ ] Confirm crystal/oscillator is **not** required when using ESP32-P4 as REF_CLK source
- [ ] Verify standard KiCad footprint `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm`
      matches LAN8720A-CP-TR land pattern
- [ ] Identify required termination resistors on MDI± lines (typically 49.9 Ω series per line)

### 3.3 PlatformIO Support Verification

- [ ] Install `espressif32` platform ≥ 6.9.0 in a local PlatformIO environment
- [ ] Confirm `esp32-p4-function-ev-board` board definition compiles a minimal Arduino sketch
- [ ] Test `ETH.h` include and basic link-up with LAN8720A driver stub
- [ ] Confirm LEDC API (`ledcSetup`, `ledcWrite`) is available and functional on P4 under arduino-esp32 3.x
- [ ] Confirm ADC API (`analogRead`) and `analogSetPinAttenuation` are functional on target GPIO
- [ ] Confirm `LittleFS.h` is available and supported on P4 in arduino-esp32 3.x
- [ ] Confirm `Update.h` is available for HTTP OTA on P4

---

## 4. Phase 2 — Schematic Changes in `generate_project.py`

> Prerequisite: Phase 0 and Phase 1 complete; MPNs confirmed; footprint files present.
> All changes are made **only** in `hardware/generate_project.py`. The `.kicad_sch` file is a
> build artifact and must never be edited directly (P-HW-05, P-KI-04).

### 4.1 New Symbol Definitions

Add the following `s.define(...)` calls in the symbol definition block (before `build_schematic`
placements, following the existing pattern):

#### 4.1.1 `Custom:ESP32-P4` Symbol

Replace the `Custom:ESP32-WROOM-32` definition (lines 422–468) with a new
`Custom:ESP32-P4` definition. The pin list must be derived from the ESP32-P4-MINI-1 datasheet.

Key structural requirements:
- `body_w` and `body_h` must be multiples of 2.54 mm (G)
- All pin endpoints must land on 2.54 mm grid (P-HW-06)
- `pin_type` must use the most restrictive correct type per P-SCH-05:
  - Power: `power_in` / `power_out` on VDD / GND pins
  - GPIO (bidirectional): `bidirectional`
  - ADC-only inputs: `input`
  - UART TX: `output`; UART RX: `input`
  - EN, BOOT strapping: `input`
- Use `passive` only for GND pads and truly direction-ambiguous pins (matching WROOM-32D convention)
- Footprint reference: `Custom:ESP32-P4-MINI-1` (in-project, see Phase 3)
- Datasheet URL: Espressif ESP32-P4-MINI-1 datasheet URL

**Proposed RMII-required pins** (to be verified against ESP32-P4 TRM; pin numbers are P4-MINI-1
module pad numbers, not GPIO numbers):

| Symbol pin name | Direction | Notes |
|---|---|---|
| `VDD3P3` (×2) | `power_in` | 3.3 V supply |
| `GND` (×N) | `passive` | Ground return |
| `EN` | `input` | Hardware reset, active-low |
| `BOOT` | `input` | Strapping pin, GPIO0 equivalent |
| `TXD0` | `output` | UART0 TX → CH340C |
| `RXD0` | `input` | UART0 RX ← CH340C |
| `FAN1_PWM` | `bidirectional` | GPIO assigned in Phase 2.3 |
| `FAN2_PWM` | `bidirectional` | GPIO assigned in Phase 2.3 |
| `FAN3_PWM` | `bidirectional` | GPIO assigned in Phase 2.3 |
| `FAN4_PWM` | `bidirectional` | GPIO assigned in Phase 2.3 |
| `FAN1_TACH` | `input` | GPIO assigned in Phase 2.3 |
| `FAN2_TACH` | `input` | GPIO assigned in Phase 2.3 |
| `FAN3_TACH` | `input` | GPIO assigned in Phase 2.3 |
| `FAN4_TACH` | `input` | GPIO assigned in Phase 2.3 |
| `NTC_ADC` | `input` | ADC input GPIO |
| `GPIO_LED` | `bidirectional` | Status LED |
| `RMII_TXD0` | `output` | EMAC RMII TX data 0 → PHY |
| `RMII_TXD1` | `output` | EMAC RMII TX data 1 → PHY |
| `RMII_TX_EN` | `output` | EMAC RMII TX enable → PHY |
| `RMII_RXD0` | `input` | EMAC RMII RX data 0 ← PHY |
| `RMII_RXD1` | `input` | EMAC RMII RX data 1 ← PHY |
| `RMII_CRS_DV` | `input` | EMAC RMII carrier sense ← PHY |
| `RMII_REF_CLK` | `output` | 50 MHz clock to PHY |
| `ETH_MDC` | `output` | MDIO clock |
| `ETH_MDIO` | `bidirectional` | MDIO data |
| NC (remaining) | `no_connect` | All unused pins must be marked |

#### 4.1.2 `Custom:LAN8720A` Symbol

Add a new symbol definition for the Ethernet PHY (U5). Suggested structure:

```
pins_left (interface to ESP32-P4 EMAC via RMII):
  TXD0, TXD1, TX_EN      — output (from PHY perspective: data it transmits)
  RXD0, RXD1, CRS_DV     — input  (data PHY receives)
  MDC, MDIO               — input/bidirectional
  REFCLK                  — input  (50 MHz from P4)
  nINT/REFCLKO            — output

pins_right (interface to RJ45 magnetics):
  TXP, TXN                — bidirectional (to MDI+ / MDI-)
  RXP, RXN                — bidirectional (from MDI+ / MDI-)
  RBIAS                   — passive (bias resistor)
  VDD (×4)                — power_in
  GND (×4 + exposed pad)  — passive
  nRST                    — input
  REGOUT                  — passive (internal LDO output, decouple)
  LED                     — output (optional: link/activity LED)
```

Footprint: `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm`
Datasheet URL: Microchip LAN8720A datasheet URL

### 4.2 J1 RJ45 Symbol Update

The current `Custom:RJ45_PoE` symbol (lines 372–385) treats all 8 pins as PoE power pairs
consumed entirely by the Ag9905M. This is incorrect for a design with an Ethernet PHY:
the RJ45 magnetics (integrated in Würth 615008144521) have **two secondary sides**:
- **PoE extraction side:** picked up by Ag9905M via the centre-tap of the primary winding
- **Data signal side:** differential pairs on the secondary winding → PHY MDI inputs

**Required symbol update:**

Replace `Custom:RJ45_PoE` with a revised `Custom:RJ45_PoE_PHY` symbol that exposes both sides:

```
pins_left (port side — primary, connects internally to RJ45 socket):
  P1, P2  — passive (mode-A pair +, pins 1 & 2 on RJ45)
  P3, P6  — passive (mode-A pair –, pins 3 & 6)
  P4, P5  — passive (mode-B pair +, pins 4 & 5)
  P7, P8  — passive (mode-B pair –, pins 7 & 8)

pins_right (secondary / magnetics output side):
  TD+, TD-  — bidirectional (transmit differential pair → PHY RX)
  RD+, RD-  — bidirectional (receive differential pair → PHY TX)
  CT1, CT2  — passive (centre-tap connections for PoE; connect to Ag9905M VPORT via PoE bypass caps)
```

> **Important:** The Würth 615008144521 datasheet must be consulted to identify the exact pin
> numbering for secondary MDI outputs and centre-tap access. The Ag9905M connects to the PoE
> power extracted via the centre-taps — the current schematic abstracts this away; with a PHY
> present the abstraction must be explicit.

**Wiring changes to J1:**
- `POE_A+` / `POE_A-` / `POE_B+` / `POE_B-` labels remain → Ag9905M (unchanged, P-POE-02 ✓)
- New global labels `ETH_TD+`, `ETH_TD-`, `ETH_RD+`, `ETH_RD-` connect secondary side → LAN8720A MDI

### 4.3 GPIO Re-mapping

The following table shows current ESP32-WROOM-32D assignments and proposed ESP32-P4 replacements.
GPIO numbers are proposals pending verification against the ESP32-P4 TRM. Strapping pins and
RMII-fixed pins must not be used for other functions.

| Signal net | ESP32 GPIO (current) | ESP32-P4 proposed GPIO | Notes |
|---|---|---|---|
| `FAN1_PWM` | GPIO25 | GPIO4 | LEDC capable; not strapping |
| `FAN2_PWM` | GPIO26 | GPIO5 | LEDC capable |
| `FAN3_PWM` | GPIO27 | GPIO6 | LEDC capable |
| `FAN4_PWM` | GPIO14 | GPIO7 | LEDC capable |
| `FAN1_TACH` | GPIO34 (input-only) | GPIO8 | General input; interrupt capable |
| `FAN2_TACH` | GPIO35 (input-only) | GPIO9 | General input; interrupt capable |
| `FAN3_TACH` | GPIO36 (input-only) | GPIO10 | General input; interrupt capable |
| `FAN4_TACH` | GPIO39 (input-only) | GPIO11 | General input; interrupt capable |
| `NTC_ADC` | GPIO32 / ADC1 CH4 | GPIO16 | ADC1 channel (avoid ADC2 if possible) |
| Status LED | GPIO2 | GPIO2 | Retain if GPIO2 is available on P4 |
| `BOOT` | GPIO0 | GPIO0 | P4 strapping pin equivalent |
| `ESP_EN` | EN | EN | Hardware reset; retained |
| `ESP_TX` (UART0) | GPIO1 | GPIO37 (or UART0 default) | Confirm P4 UART0 pin |
| `ESP_RX` (UART0) | GPIO3 | GPIO38 (or UART0 default) | Confirm P4 UART0 pin |
| `RMII_TXD0` | — (new) | GPIO39 | EMAC fixed pin — verify TRM |
| `RMII_TXD1` | — (new) | GPIO40 | EMAC fixed pin — verify TRM |
| `RMII_TX_EN` | — (new) | GPIO41 | EMAC fixed pin — verify TRM |
| `RMII_RXD0` | — (new) | GPIO42 | EMAC fixed pin — verify TRM |
| `RMII_RXD1` | — (new) | GPIO43 | EMAC fixed pin — verify TRM |
| `RMII_CRS_DV` | — (new) | GPIO44 | EMAC fixed pin — verify TRM |
| `RMII_REF_CLK` | — (new) | GPIO50 | P4 clock output to PHY |
| `ETH_MDC` | — (new) | GPIO31 | GPIO-matrix assignable |
| `ETH_MDIO` | — (new) | GPIO32 | GPIO-matrix assignable |

> **Critical:** The ESP32-P4 EMAC RMII interface uses partially fixed pin assignments (similar to
> ESP32). These cannot be freely reassigned on the GPIO matrix. The final GPIO numbers in this
> table MUST be verified against Chapter "Ethernet" in the ESP32-P4 Technical Reference Manual
> before the schematic is committed. Any discrepancy invalidates the schematic.

### 4.4 New Schematic Wiring

#### 4.4.1 ESP32-P4 Component Placement

Replace the U3 placement block (lines 678–893 approximately) with:

```python
# U3 – ESP32-P4-MINI-1
s.text("ESP32-P4", 155, 18, size=2.54, bold=True, color=BLUE)
U3_CX, U3_CY = <confirmed from footprint dimensions>
p = s.component("Custom:ESP32-P4", "U3", "ESP32-P4-MINI-1U-N16R8",
                "Custom:ESP32-P4-MINI-1", U3_CX, U3_CY)
```

All existing global label connections (`FAN1_PWM`, `FAN1_TACH`, … `NTC_ADC`, `BOOT`, `ESP_EN`,
`ESP_TX`, `ESP_RX`) must be reconnected to the new pin names/numbers using the mapping in §4.3.

New global labels for RMII:
```python
s.global_label("ETH_TXD0",   *p["RMII_TXD0"],  shape="output")
s.global_label("ETH_TXD1",   *p["RMII_TXD1"],  shape="output")
s.global_label("ETH_TX_EN",  *p["RMII_TX_EN"], shape="output")
s.global_label("ETH_RXD0",   *p["RMII_RXD0"],  shape="input")
s.global_label("ETH_RXD1",   *p["RMII_RXD1"],  shape="input")
s.global_label("ETH_CRS_DV", *p["RMII_CRS_DV"],shape="input")
s.global_label("ETH_REF_CLK",*p["RMII_REF_CLK"],shape="output")
s.global_label("ETH_MDC",    *p["ETH_MDC"],    shape="output")
s.global_label("ETH_MDIO",   *p["ETH_MDIO"],   shape="bidirectional")
```

#### 4.4.2 LAN8720A (U5) Component Placement

Add a new schematic sub-block. Suggested placement on the A2 schematic sheet: right-hand side of
the ESP32 block (or a separate region at x > 300, y = 200–320 in schematic coordinates), away from
fan headers.

RMII interface wiring (global labels matching §4.4.1):
```python
s.global_label("ETH_TXD0",   *p5["TXD0"],   shape="input")
s.global_label("ETH_TXD1",   *p5["TXD1"],   shape="input")
s.global_label("ETH_TX_EN",  *p5["TX_EN"],  shape="input")
s.global_label("ETH_RXD0",   *p5["RXD0"],   shape="output")
s.global_label("ETH_RXD1",   *p5["RXD1"],   shape="output")
s.global_label("ETH_CRS_DV", *p5["CRS_DV"], shape="output")
s.global_label("ETH_REF_CLK",*p5["REFCLK"], shape="input")
s.global_label("ETH_MDC",    *p5["MDC"],    shape="input")
s.global_label("ETH_MDIO",   *p5["MDIO"],   shape="bidirectional")
```

MDI interface wiring (to J1 secondary side via global labels):
```python
s.global_label("ETH_TD+", *p5["TXP"], shape="bidirectional")
s.global_label("ETH_TD-", *p5["TXN"], shape="bidirectional")
s.global_label("ETH_RD+", *p5["RXP"], shape="bidirectional")
s.global_label("ETH_RD-", *p5["RXN"], shape="bidirectional")
```

Power decoupling for U5 (new components U5_C1 through U5_C4 — assign next available ref):
```python
# 4 × 100 nF decoupling caps on VDD pins, placed adjacent to U5
# 1 × 10 µF bulk cap on VDD
s.power("+3V3", *p5["VDD1"])
s.power("+3V3", *p5["VDD2"])
s.power("+3V3", *p5["VDD3"])
s.power("GND",  *p5["GND"])
s.power("GND",  *p5["EP"])   # exposed pad — must connect to GND
```

RBIAS resistor (10.0 kΩ ±1%, 0402):
```python
# R_RBIAS — 10k ±1% to GND (sets internal bias current)
p_rb = s.component("Custom:R", "R_RBIAS", "10k_1%", "Resistor_SMD:R_0402_1005Metric", ...)
s.label("PHY_RBIAS", *p_rb["1"])
s.power("GND",       *p_rb["2"])
s.label("PHY_RBIAS", *p5["RBIAS"])
```

nRST line (controlled by GPIO or tied HIGH via pull-up):
```python
# PHY_nRST — pull-up to +3V3; optionally connected to an ESP32-P4 GPIO for software reset
p_rr = s.component("Custom:R", "R_PHYRST", "10k", "Resistor_SMD:R_0402_1005Metric", ...)
s.power("+3V3",        *p_rr["1"])
s.global_label("PHY_nRST", *p_rr["2"], shape="passive")
s.global_label("PHY_nRST", *p5["nRST"], shape="input")
```

#### 4.4.3 J1 RJ45 Update

Add the following new global labels for the secondary (data) side of J1:
```python
s.global_label("ETH_TD+", *p["TD+"], shape="bidirectional")
s.global_label("ETH_TD-", *p["TD-"], shape="bidirectional")
s.global_label("ETH_RD+", *p["RD+"], shape="bidirectional")
s.global_label("ETH_RD-", *p["RD-"], shape="bidirectional")
```

#### 4.4.4 PCB Net Table Update

The `write_pcb()` function in `generate_project.py` (line ~987) must have new nets appended:
```python
(net 23 "ETH_TXD0")
(net 24 "ETH_TXD1")
(net 25 "ETH_TX_EN")
(net 26 "ETH_RXD0")
(net 27 "ETH_RXD1")
(net 28 "ETH_CRS_DV")
(net 29 "ETH_REF_CLK")
(net 30 "ETH_MDC")
(net 31 "ETH_MDIO")
(net 32 "ETH_TD+")
(net 33 "ETH_TD-")
(net 34 "ETH_RD+")
(net 35 "ETH_RD-")
(net 36 "PHY_nRST")
```

#### 4.4.5 WiFi Removal Checklist

The following must be confirmed **absent** from the updated schematic:

- [ ] No `Custom:ESP32-WROOM-32` symbol definition
- [ ] No `RF_Module:ESP32-WROOM-32` footprint reference
- [ ] No antenna matching network (the WROOM-32D has no external matching, so nothing to remove)
- [ ] No WiFi-related nets (there were none — WiFi was internal to the module)
- [ ] PCB silk-screen line 1019 updated: `"ESP32 | PoE 802.3at | 4xPWM Fan"` →
      `"ESP32-P4 | PoE 802.3at | 4xPWM Fan | 100BASE-T Ethernet"`
- [ ] Schematic title block comment (line 349) updated:
      `"4-channel PoE-powered PWM fan controller with ESP32"` →
      `"4-channel PoE-powered PWM fan controller with ESP32-P4 + Ethernet"`

### 4.5 ERC Compliance (P-SCH-05 / P-TEST-01)

After generator changes:
1. Run `python hardware/generate_project.py` — must complete without Python errors
2. Run `kicad-cli sch erc hardware/kicad/PoE-FanController.kicad_sch --output hardware/kicad/erc_output.json --exit-code-violations`
3. Verify: **0 ERC errors** (severity `"error"`). Warnings for `lib_symbol_issues` and `lib_symbol_mismatch` are expected and acceptable (same category as existing 85 warnings).
4. Commit updated `hardware/kicad/erc_output.json`.

---

## 5. Phase 3 — PCB Layout Updates

> Prerequisite: Phase 2 complete; ERC passes.
> The PCB is also generated by `generate_project.py` (`write_pcb()` function). All PCB
> placements are in `embed_footprint()` calls. No hand-editing of `.kicad_pcb`.

### 5.1 U3 Footprint Replacement

Remove the `embed_footprint("RF_Module", "ESP32-WROOM-32", "U3", ...)` call (line 1102).

Replace with:
```python
embed_footprint("Custom", "ESP32-P4-MINI-1",
                "U3", "ESP32-P4-MINI-1U-N16R8", U3_CX, U3_CY)
```

The `ESP32-P4-MINI-1.kicad_mod` file must be present in `hardware/kicad/footprints/Custom.pretty/`
before this call is made. The footprint must:
- Place all pads on `F.Cu` only (P-HW-02)
- Have origin at the geometric centre (or at pad 1 if LGA convention differs — document choice)
- Not extend west of x = 38 mm in its placed position (P-ISO-02)
- Have courtyard on `F.CrtYd` only
- Use the correct pad dimensions from the ESP32-P4-MINI-1 datasheet (module castellation pitch)

**Courtyard considerations:** The ESP32-WROOM-32D has a T-shaped courtyard due to the antenna
overhang. The P4-MINI-1 (if using PCB trace or no-antenna LGA) may have a simpler rectangular
courtyard. The existing U3 placement at (65, 53 mm) must be validated against the new courtyard;
passive component zone B (R1–R4, C3–C6 at x = 45–52, y = 47–56) must remain clear.

### 5.2 U5 (LAN8720A) Footprint Placement

Add to `write_pcb()` footprint list:
```python
# U5 LAN8720A — placed east of U3, west of U4, secondary side (x > 38mm)
# Suggested: cx=57, cy=42 — left of U3; verify no courtyard collision with Zone B passives
embed_footprint("Package_DFN_QFN", "QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm",
                "U5", "LAN8720A", <cx>, <cy>)
```

Placement constraints:
- Must remain east of x = 38 mm (P-ISO-02 / P-ISO-05)
- Must be on F.Cu only (P-HW-02)
- QFN-24 courtyard is approximately 5 × 5 mm; must not collide with U3, U4, Zone B, or Zone C
  passive components
- Place as close to U3 RMII pins as physically possible to minimise RMII trace lengths
  (RMII signals run at 50 MHz — short, matched traces reduce EMI)

### 5.3 PHY Decoupling Capacitor Placements

Add `embed_footprint()` calls for:
- 4 × 100 nF / 0402 decoupling caps (C8–C11) placed immediately adjacent to U5 VDD pins
- 1 × 10 µF / 0805 bulk cap (C12) near U5 VDD pin
- 1 × 100 nF / 0402 for REGOUT pin (C13)
- RBIAS resistor (R_RBIAS, 0402) near RBIAS pin of U5
- PHY_nRST pull-up resistor (R_PHYRST, 0402)

All must satisfy P-HW-02 (F.Cu), P-ISO-02 (x > 38 mm).

### 5.4 MDI Termination Resistors

Add 4 × 49.9 Ω (1%) / 0402 series resistors on the MDI lines (TD+, TD−, RD+, RD−) between U5
and J1 secondary pins. Placement: as close to U5 MDI pins as possible to minimise stub length.

### 5.5 PCB Layout Guidelines for New Signals

The following guidelines apply during the manual PCB routing step (after `generate_project.py`
produces the `.kicad_pcb` with correct footprint positions):

| Signal group | Routing requirement |
|---|---|
| RMII data (6 signals) | Length-match to within ±5 mm; 0.25 mm width; minimise vias |
| RMII REF_CLK | Route away from sensitive nets; consider 0.25 mm width |
| MDI pairs (TD±, RD±) | Differential pairs; 100 Ω differential impedance; minimum length |
| MDIO/MDC | Non-critical; standard 0.25 mm signal width |
| PHY VDD decoupling | Caps placed within 1 mm of VDD pins; direct connection, no stubs |

> **Note:** All the above nets are secondary-side signals (P-ISO-05); none may cross x = 38 mm.

### 5.6 DRC Baseline Update

After Phase 3, the DRC baseline in `.github/workflows/hardware-check.yml` must be reviewed:
- New footprints (U5, decoupling caps, termination resistors) may change the `lib_footprint_issues`
  count (currently 34 in Docker CI)
- The `solder_mask_bridge` count (28 on J6) should be unchanged
- Any new DRC violations must be individually assessed before being added to the PR-gate baseline

---

## 6. Phase 4 — Firmware Changes

> Prerequisite: Phase 2 complete (GPIO assignments finalised).
> Firmware changes may proceed in parallel with Phase 3 PCB layout.

### 6.1 `platformio.ini`

Create `platformio.ini` in the repository root (it does not currently exist):

```ini
; PoE FanController firmware — PlatformIO build configuration
; Constitution reference: §2.3 (v2.0.0 after MAJOR amendment)
; Target: ESP32-P4-MINI-1U-N16R8

[env:esp32-p4]
platform  = espressif32 @ >=6.9.0
board     = esp32-p4-function-ev-board
framework = arduino

; Arduino-esp32 3.x with IDF 5.3+ required for ESP32-P4 support
platform_packages =
    framework-arduinoespressif32 @ >=3.1.0

; Board flash size override (16 MB flash on MINI-1U N16 variant)
board_build.flash_size = 16MB
board_build.partitions = default_16MB.csv

; LittleFS file system image
board_build.filesystem = littlefs

; Build flags
build_flags =
    -D ARDUINO_ESP32_P4_MINI
    -D CONFIG_ETH_USE_ESP32_EMAC=1
    -D CONFIG_ETH_PHY_LAN8720=1
    ; GPIO assignments (from Phase 2.3 — update when finalised)
    -D FAN1_PWM_PIN=4
    -D FAN2_PWM_PIN=5
    -D FAN3_PWM_PIN=6
    -D FAN4_PWM_PIN=7
    -D FAN1_TACH_PIN=8
    -D FAN2_TACH_PIN=9
    -D FAN3_TACH_PIN=10
    -D FAN4_TACH_PIN=11
    -D NTC_ADC_PIN=16
    -D STATUS_LED_PIN=2
    -D ETH_MDC_PIN=31
    -D ETH_MDIO_PIN=32
    -D ETH_PHY_ADDR=0
    -D ETH_CLK_MODE=ETH_CLOCK_GPIO_OUT_1

; Native unit test environment (business logic only; no hardware peripherals)
[env:native]
platform = native
build_flags =
    -D UNIT_TEST
    -std=c++17
test_framework = unity
```

### 6.2 Module Changes by Firmware Module

#### `main` module

- **Remove:** `WiFi.begin()`, `WiFi.waitForConnectResult()`, WiFi SSID/password config
- **Add:** `ETH.begin(ETH_PHY_LAN8720, ETH_PHY_ADDR, ETH_MDC_PIN, ETH_MDIO_PIN, -1, ETH_CLK_MODE)`
- **Add:** Ethernet link-up event handler (`ETH_EVENT` → `ARDUINO_EVENT_ETH_GOT_IP`)
- **Update:** `BOOT` pin initialisation — use P4 equivalent strapping pin
- **Update:** `ESP_EN` / reset button — confirm P4 reset net name

#### `ota` module

- **Remove:** `ArduinoOTA` header and all `ArduinoOTA.*` calls
- **Remove:** mDNS dependency (`ESPmDNS.h`)
- **Add:** HTTP OTA endpoint handler:
  ```cpp
  // POST /api/v1/ota — accepts firmware binary; streams to Update partition
  server.on("/api/v1/ota", HTTP_POST, [](AsyncWebServerRequest *req){
      req->send(Update.hasError() ? 500 : 200, "text/plain",
                Update.hasError() ? "OTA FAILED" : "OK");
  }, [](AsyncWebServerRequest *req, String fn, size_t idx, uint8_t *data, size_t len, bool final){
      if (!idx) Update.begin((ESP.getFreeSketchSpace() - 0x1000) & 0xFFFFF000);
      Update.write(data, len);
      if (final) Update.end(true);
  });
  ```
- **Retain:** UART OTA fallback via CH340C / `esptool.py` is always available

#### `web` module

- **No library change required:** `ESPAsyncWebServer` works over Ethernet TCP the same as over
  WiFi TCP — it depends on the underlying TCP/IP stack, not the physical interface. Once
  `ETH.begin()` is called and a link-up event fires, `server.begin()` works identically.
- **Update:** Any references to `WiFi.localIP()` → `ETH.localIP()`
- **Update:** Web UI status page to show Ethernet link speed/status instead of WiFi SSID/RSSI

#### `fan` module

- **Update:** GPIO pin constants (`FAN1_PWM_PIN`, etc.) to use `build_flags` defines from
  `platformio.ini` (§6.1)
- **LEDC API:** arduino-esp32 3.x changed LEDC API. Use new-style:
  ```cpp
  ledcAttach(FAN1_PWM_PIN, 25000, 8);   // pin, freq Hz, resolution bits
  ledcWrite(FAN1_PWM_PIN, duty);
  ```
  rather than deprecated `ledcSetup()` / `ledcAttachPin()` from 2.x

#### `temp` module

- **Update:** `NTC_ADC_PIN` constant to use `build_flags` define
- **Confirm:** `analogRead(NTC_ADC_PIN)` and `analogSetPinAttenuation()` available on P4 GPIO16
  under arduino-esp32 3.x

#### `config` module

- **No change expected** — NVS API is unchanged in arduino-esp32 3.x

### 6.3 Constitution §4 Firmware Peripheral Ownership Update

The following rows in constitution §4 P-FW-02 must be updated in the MAJOR amendment:

| ESP32-P4 Peripheral | Owner module | New Pins |
|---|---|---|
| LEDC channels 0–3 | `fan` | GPIO4 (FAN1), GPIO5 (FAN2), GPIO6 (FAN3), GPIO7 (FAN4) |
| GPIO interrupts (TACH) | `fan` | GPIO8, GPIO9, GPIO10, GPIO11 |
| ADC (channel TBD) | `temp` | GPIO16 (NTC) |
| UART0 | `main` / debug | GPIO37 (TXD0), GPIO38 (RXD0) — confirm P4 UART0 defaults |
| GPIO output | `main` | GPIO2 (status LED) |
| GPIO input | `main` | GPIO0 (BOOT), EN (RESET) |
| LittleFS | `web`, `config` | — |
| NVS | `config` | — |
| **EMAC (Ethernet MAC)** | **`web`, `ota`** | **RMII pins (see §4.3)** |
| ~~WiFi / TCP stack~~ | ~~`web`, `ota`~~ | ~~removed~~ |
| I2C (SDA/SCL) | reserved | TBD (not populated v0.2) |

---

## 7. Phase 5 — Testing and CI Validation

### 7.1 Hardware Bring-up Checklist (v0.2 Board)

The following sequence replaces the v0.1 bring-up procedure in `hardware/DESIGN.md`:

1. **No-load PoE test:** Connect 802.3at PoE+ switch. Measure Ag9905M output at J2 pin 2:
   expect **12.0 ± 0.3 V DC**.
2. **3.3 V rail test:** Measure LM2596 output: expect **3.30 ± 0.05 V DC**.
3. **USB-UART enumeration:** Connect J6 USB-C → CH340C must enumerate as serial device (COM port
   or `/dev/ttyUSB0`). Open at 115200 baud.
4. **Firmware flash:** `pio run -e esp32-p4 --target upload` via CH340C. Confirm no flash errors.
5. **Ethernet link-up:** Connect J1 to 802.3at PoE+ switch (same port as PoE). Confirm:
   - LINK LED on switch port goes active
   - Firmware UART log shows `ETH MAC Address`, `ETH Connected`, `ETH Got IP` events
   - `ETH.localIP()` returns a valid DHCP address
6. **Web UI access:** Open `http://<ip>` in a browser. Confirm the fan controller UI loads.
7. **Fan PWM test:** Connect one fan to J2. Command 50% duty cycle via web UI. Confirm audible
   speed change and valid TACH reading.
8. **HTTP OTA test:** Upload a test firmware binary via `POST /api/v1/ota`. Confirm device
   reboots and runs the new firmware.
9. **Full-load thermal test:** All 4 fans at 100% duty for 10 minutes. Measure:
   - U2 LM2596 temperature (expect < 85 °C)
   - U5 LAN8720A temperature (expect < 70 °C)
   - U3 ESP32-P4 temperature (expect < 75 °C)

### 7.2 PlatformIO Native Unit Tests (P-TEST-05)

The following test modules must be present and pass via `pio test -e native`:

| Test file | Functions under test |
|---|---|
| `test_temp.cpp` | Steinhart-Hart calculation for NTC10K B=3950 |
| `test_fan.cpp` | RPM calculation from TACH pulse count; duty clamping 0–100% |
| `test_config.cpp` | JSON config parsing; default value injection; schema validation |
| `test_web_api.cpp` | JSON serialisation of fan status and temperature response |

Hardware-dependent code (LEDC, ADC, ETH, GPIO) is mocked or excluded from native tests.

### 7.3 CI Gate Validation (P-CI-01)

The `hardware-check.yml` workflow must be confirmed passing on the branch with all Phase 2–3
changes. Required gates:

| Check | Tool | Pass condition |
|---|---|---|
| Generator syntax | `python -m py_compile hardware/generate_project.py` | Exit 0 |
| Generator execution | `python hardware/generate_project.py` | Exit 0, files written |
| ERC | `kicad-cli sch erc` in `kicad/kicad:10.0.2` Docker | **0 errors** (severity `"error"`) |
| DRC | `kicad-cli pcb drc` in `kicad/kicad:10.0.2` Docker | ≤ updated baseline violations |
| Firmware build | `pio run -e esp32-p4` | Exit 0 |
| Native unit tests | `pio test -e native` | All tests pass |

### 7.4 ERC Validation Approach

When verifying ERC compliance for the new `Custom:ESP32-P4` and `Custom:LAN8720A` symbols,
the following ERC patterns are expected (consistent with existing 85 warnings):

- **Expected warnings (benign):** `lib_symbol_issues` ("Custom library not found") for each new
  `Custom:*` symbol — acceptable per P-KI-05 design decision
- **Expected warnings (benign):** `lib_symbol_mismatch` for power symbols if `+3V3` / `GND`
  are redefined as `power_out` — acceptable per P-SCH-04
- **Must not appear:** Any `pin_not_connected` on RMII or MDI pins — all must be connected or
  explicitly `no_connect`
- **Must not appear:** `power_pin_not_driven` — all power nets must have a `power_out` driver

---

## 8. Power Budget

### 8.1 Current Budget (v0.1 with ESP32-WROOM-32D)

| Consumer | Rail | Max current | Max power |
|---|---|---|---|
| 4 × PWM fan (max) | 12 V | 4 × 0.25 A = 1.0 A | 12.0 W |
| ESP32-WROOM-32D (WiFi TX peak) | 3.3 V | 0.35 A | 1.15 W |
| CH340C + logic | 3.3 V | 0.10 A | 0.33 W |
| LM2596 losses (est.) | — | — | ~1.5 W |
| Ag9905M losses (est.) | — | — | ~2.0 W |
| **Total** | | | **~17.0 W** |
| **802.3at Class 4 budget** | | | **25.5 W** |
| **Margin** | | | **~8.5 W** |

### 8.2 Proposed Budget (v0.2 with ESP32-P4 + LAN8720A)

| Consumer | Rail | Max current | Max power | Notes |
|---|---|---|---|---|
| 4 × PWM fan (max) | 12 V | 4 × 0.25 A = 1.0 A | 12.0 W | Unchanged |
| ESP32-P4-MINI-1 (active, no WiFi) | 3.3 V | 0.30 A | 0.99 W | P4 TRM §Power; verify datasheet |
| LAN8720A PHY (100BASE-T active) | 3.3 V | 0.07 A | 0.23 W | LAN8720A datasheet §Electrical |
| CH340C + logic | 3.3 V | 0.10 A | 0.33 W | Unchanged |
| LM2596 losses (est.) | — | — | ~1.5 W | Unchanged |
| Ag9905M losses (est.) | — | — | ~2.0 W | Unchanged |
| **Total (proposed)** | | | **~17.1 W** | |
| **802.3at Class 4 budget** | | | **25.5 W** | |
| **Margin (proposed)** | | | **~8.4 W** | |

> **Key observations:**
> - Removing the WiFi radio saves ~0.16 W (peak) — WiFi TX peak was 0.35 A vs ~0.30 A for P4 CPU
> - Adding the LAN8720A costs ~0.23 W
> - Net impact is approximately neutral (+0.07 W total) — well within the 8+ W available margin
> - The 3.3 V / 3 A LM2596 rail is not stressed: total 3.3 V load = 0.47 A (proposed) vs 0.45 A
>   (current), both far below the 3 A rating
> - Power class remains **802.3at Class 4** — no change to PoE classification

### 8.3 Budget Validation

The power budget figures above use datasheet maximums. Actual values must be confirmed during
Phase 1 research (§3.1, §3.2) from:
- ESP32-P4 TRM / datasheet "Electrical Characteristics" → `IDD` at 3.3 V, max CPU load
- LAN8720A datasheet "DC Electrical Characteristics" → `IVDD` at 3.3 V, link active

---

## 9. Risk Register

| ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | **BGA / LGA assembly risk** — ESP32-P4-MINI-1U is an LGA module; paste printing and reflow are more demanding than SOIC/THT. First-article assembly may have cold joints. | Medium | High | Use a PCB assembly service with LGA experience; specify no-clean flux; X-ray inspect first article; order at least 3 boards for rework. |
| R-02 | **No ESP32-P4 module footprint in KiCad standard library** — custom `.kicad_mod` must be authored. Errors in pad pitch cause unrouteable PCB. | High | High | Author footprint directly from Espressif MINI-1U recommended land pattern PDF; peer-review against datasheet before committing; validate with DRC courtyard checks. |
| R-03 | **RMII pin constraints** — ESP32-P4 EMAC may have partially fixed RMII pin assignments not fully exposed on the MINI-1U module. If required RMII pins are NC on the module, the design is blocked. | Medium | Critical | Verify in Phase 1 by cross-referencing ESP32-P4 TRM Chapter "Ethernet" with MINI-1U module datasheet pin-out table. Select alternate GPIO or alternate module if any RMII pin is not available. |
| R-04 | **PlatformIO support maturity** — arduino-esp32 3.x ESP32-P4 support was released recently; ETH.h, LEDC, ADC, and LittleFS may have outstanding bugs on P4 target. | Medium | High | Pin to a known-stable arduino-esp32 release during Phase 1; run a minimal firmware smoke test on ESP32-P4 Function EV Board before committing to custom hardware; track Espressif GitHub issues for P4. |
| R-05 | **LAN8720A availability** — the LAN8720A is a mature but aging part; supply may be constrained. | Low | Medium | Order from authorised distributors (Mouser, DigiKey); identify DP83848IVV (TI) as a pin-compatible alternative; confirm both are available before PCB fabrication. |
| R-06 | **J1 RJ45 schematic rework complexity** — the current schematic treats all 8 RJ45 pins as PoE-only; adding PHY data-path signals requires a symbol redesign that could introduce ERC errors. | Medium | Medium | Consult Würth 615008144521 datasheet for the exact secondary pin positions before rewriting the J1 symbol; run ERC in Docker immediately after Phase 2 changes. |
| R-07 | **PCB area pressure** — adding U5 (LAN8720A, ~5×5 mm courtyard) and its decoupling (6–8 caps, 4 termination resistors) onto a fixed 90×70 mm board may require rebalancing the secondary-side layout. | Medium | Medium | Model U5 courtyard in a scratch layout before committing; evaluate whether Zone B passive components need shifting; board outline cannot change (P-HW-04). |
| R-08 | **DRC baseline shift** — new footprints (U5, passives) may introduce new DRC violations beyond the PR-gate baseline (currently 67). | Medium | Low | Re-measure DRC after Phase 3; update the baseline in `hardware-check.yml` with a documented rationale for each new item; zero-tolerance release gate still applies (P-CI-02). |
| R-09 | **ESPAsyncWebServer compatibility on P4** — the library must be tested under arduino-esp32 3.x / IDF 5.3+ on ESP32-P4. The `AsyncTCP` dependency may need updating. | Medium | Medium | Pin to a known-compatible AsyncTCP version; test on EV Board before custom hardware; consider `ESP Async WebServer` community fork (maintained for IDF 5.x). |
| R-10 | **PoE data + power on shared RJ45** — while the RJ45 Würth 615008144521 has integrated magnetics, the centre-tap PoE topology must be verified to not degrade Ethernet signal integrity at 100BASE-T. | Low | Medium | Review IEEE 802.3af/at PoE coexistence requirements; confirm Würth datasheet shows compatible mode A topology; validate with an Ethernet analyser at bring-up. |

---

## 10. Constitution Compliance Summary

| Constitution principle | How this plan satisfies it |
|---|---|
| **§2.2 BOM-lock + §9 MAJOR amendment** | Phase 0 is a hard prerequisite; no schematic file changes until amendment is ratified and committed. Amendment covers U3 replacement, U5 addition, and all §2.3 firmware changes. |
| **P-HW-02 Single-sided placement** | All new components (U3-P4, U5, decoupling) placed on F.Cu only. |
| **P-HW-04 Fixed board outline** | No Edge.Cuts changes proposed; U5 placement verified to fit within current secondary-side area. |
| **P-HW-05 / P-KI-04 Generator is source of truth** | All schematic and PCB changes are made in `generate_project.py`. `.kicad_sch` and `.kicad_pcb` remain build artifacts. |
| **P-KI-05 Custom symbols/footprints in-project** | `Custom:ESP32-P4` symbol in-generator; `ESP32-P4-MINI-1.kicad_mod` in `hardware/kicad/footprints/Custom.pretty/`. |
| **P-SCH-01 Global labels for inter-block signals** | All new RMII and MDI signals use `global_label()` with correct shapes. |
| **P-SCH-02 Ground domain separation** | PHY `GND` pin connects to secondary `GND` only; no new primary-side components; `GND_PRI` domain unchanged. |
| **P-SCH-03 Section header style** | New "ESP32-P4" section header uses `bold=True`, `size=2.54`, `color=BLUE`. |
| **P-SCH-04 Power symbol pin types** | No new power rail drivers introduced; existing `+3V3` and `GND` power symbols apply to U5 and new passives. |
| **P-SCH-05 Custom symbol pin types** | ESP32-P4 and LAN8720A symbols use correct restrictive pin types; no `power_in` on non-power pins. |
| **P-ISO-02/05 Isolation barrier** | All new components (U3, U5, passives) placed east of x = 38 mm. No new traces cross isolation barrier. |
| **P-POE-02 No primary-side changes** | J1 and U1 are unchanged in topology; only secondary-side data pins of J1 are newly wired. |
| **P-TEST-01 Zero ERC errors** | Phase 2 includes mandatory ERC run; CI gate enforces this on every PR. |
| **P-CI-01 ERC/DRC in CI** | Existing `hardware-check.yml` workflow covers new files; DRC baseline updated with rationale. |
| **P-CI-02 Release DRC gate** | Zero-tolerance release DRC gate is unchanged; new violations must be resolved before any tagged release. |
| **P-FW-01 Module boundaries** | New Ethernet init goes into `main`; OTA handler into `ota`; `ETH.localIP()` into `web`; fan/temp module changes are pin-number only. |
| **P-FW-02 Peripheral ownership** | EMAC owned by `web`/`ota`; all other peripheral owners unchanged except GPIO pin reassignment. |
| **P-FW-03 PWM 25 kHz** | LEDC configuration is unchanged; only the GPIO pin numbers change. |
| **P-FW-04 No blocking in async callbacks** | OTA handler uses streaming write pattern; no `delay()` in handler. |
| **P-FW-05 Safe boot default** | Fan PWM initialised to 100% before config load — unchanged behaviour. |
| **P-UI-01/02/03/04** | Web UI changes are cosmetic (Ethernet status vs WiFi); no new assets; REST API unchanged. |

---

## 11. Acceptance Criteria

All of the following must be satisfied before this feature may be merged to `main`:

### Schematic / ERC
- [ ] **AC-01:** `docs/constitution.md` contains a ratified `v2.0.0` MAJOR amendment documenting the ESP32-P4-MINI-1U-N16R8 MPN, LAN8720A-CP-TR MPN, rationale, and expert consultations.
- [ ] **AC-02:** `hardware/generate_project.py` contains no reference to `Custom:ESP32-WROOM-32` or `RF_Module:ESP32-WROOM-32` in the U3 placement block.
- [ ] **AC-03:** `Custom:ESP32-P4` symbol is defined in `generate_project.py` with pin types conforming to P-SCH-05; all RMII and GPIO pins have correct directionality.
- [ ] **AC-04:** `Custom:LAN8720A` symbol is defined in `generate_project.py` with correct RMII, MDI, and power pin types.
- [ ] **AC-05:** Running `python hardware/generate_project.py` produces `.kicad_sch` and `.kicad_pcb` without Python errors.
- [ ] **AC-06:** `kicad-cli sch erc` reports **0 violations with severity "error"**. Result committed to `hardware/kicad/erc_output.json`.
- [ ] **AC-07:** All signal nets (`FAN1_PWM`…`FAN4_PWM`, `FAN1_TACH`…`FAN4_TACH`, `NTC_ADC`, `BOOT`, `ESP_EN`, `ESP_TX`, `ESP_RX`) and all new Ethernet nets (`ETH_TXD0`…`ETH_MDIO`, `ETH_TD+`…`ETH_RD-`) are connected in the schematic with zero unconnected stubs.
- [ ] **AC-08:** No WiFi-related schematic elements (antenna matching network, WiFi-only nets) appear anywhere in the generated schematic.

### PCB / DRC
- [ ] **AC-09:** `ESP32-P4-MINI-1.kicad_mod` custom footprint is committed to `hardware/kicad/footprints/Custom.pretty/`; all pads are on F.Cu; origin matches generator call.
- [ ] **AC-10:** U5 (LAN8720A) PCB footprint uses the standard KiCad QFN-24 footprint; placement is east of x = 38 mm on F.Cu.
- [ ] **AC-11:** `kicad-cli pcb drc` reports ≤ updated baseline violation count (zero courtyard collisions, zero unconnected nets in secondary domain, zero isolation-barrier crossings).

### Firmware / PlatformIO
- [ ] **AC-12:** `platformio.ini` exists in the repository root with a valid `[env:esp32-p4]` section; `pio run -e esp32-p4` completes without errors.
- [ ] **AC-13:** `pio test -e native` passes all unit tests (Steinhart-Hart, RPM calc, duty clamping, JSON serialisation).
- [ ] **AC-14:** Firmware does not reference `WiFi.h`, `ArduinoOTA.h`, or `ESPmDNS.h`.
- [ ] **AC-15:** Firmware references `ETH.h`; `ETH.begin()` is called with LAN8720A configuration constants.
- [ ] **AC-16:** HTTP OTA endpoint `POST /api/v1/ota` is implemented in the `ota` module using `Update.h`.

### CI
- [ ] **AC-17:** `hardware-check.yml` CI workflow passes on the feature branch (ERC 0 errors; DRC ≤ baseline; generator syntax check passes).
- [ ] **AC-18:** Firmware CI build job (if present) passes for `env:esp32-p4` target.

### Documentation
- [ ] **AC-19:** `hardware/DESIGN.md` §ESP32 GPIO Allocation table is updated to ESP32-P4 pin assignments; old GPIO34/35/36/39 rows are replaced.
- [ ] **AC-20:** `hardware/DESIGN.md` §Power Budget table is updated to reflect ESP32-P4 + LAN8720A consumption; WiFi peak row removed.
- [ ] **AC-21:** `hardware/DESIGN.md` §Bring-up Procedure updated to include Ethernet link-up and HTTP OTA steps.
- [ ] **AC-22:** Constitution §5.2 power budget matches the proposed budget in §8.2 of this plan.

---

## 12. Open Questions

The following items require resolution during Phase 0 / Phase 1 research before implementation
can proceed. These are **blocking** items — implementation must not begin until each is answered.

| ID | Question | Owner | Blocking phase |
|---|---|---|---|
| OQ-01 | What are the exact RMII pin assignments for ESP32-P4-MINI-1U-N16R8? Which are fixed (non-routable on GPIO matrix) vs flexible? | hw.expert (Phase 1) | Phase 2 |
| OQ-02 | Is `ETH_PHY_LAN8720` available in the `arduino-esp32` 3.x `ETH.h` for ESP32-P4, or does it require IDF-native `esp_eth`? | fw.expert (Phase 1) | Phase 4 |
| OQ-03 | Does the Würth 615008144521 expose the secondary winding MDI outputs as explicit pins in the recommended PCB land pattern, or does the schematic treat the full RJ45 as a black box? Confirm the pin mapping for secondary data vs PoE centre-tap. | hw.expert (Phase 1) | Phase 2 |
| OQ-04 | What is the exact PlatformIO board identifier for the ESP32-P4-MINI-1U variant, and what is the minimum `espressif32` platform version that includes it? | fw.expert (Phase 1) | Phase 4 |
| OQ-05 | Does `ESPAsyncWebServer` (+ `AsyncTCP`) compile and function correctly under arduino-esp32 3.x on ESP32-P4? Which fork/version is recommended? | fw.expert (Phase 1) | Phase 4 |
| OQ-06 | Is there a courtyard collision between the proposed U5 LAN8720A placement and the existing Zone B passive components (R1–R4, C3–C6 at x = 45–52, y = 47–56)? | hw.expert (Phase 3) | Phase 3 |

---

*Plan authored by: Feature Planner Agent*
*Date: 2026-06-07*
*Issue: #40 — MCU: replace ESP32-WROOM-32D with ESP32-P4*
*Branch: `feature/40-replace-esp32-with-esp32-p4`*
*Constitution version at time of planning: v1.1.0*
