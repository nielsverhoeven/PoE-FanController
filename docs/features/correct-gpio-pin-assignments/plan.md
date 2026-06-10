# Technical Plan: Correct GPIO Pin Assignments for J8 (ESP32-P4-POE-ETH)

> Issue: [#148](https://github.com/nielsverhoeven/PoE-FanController/issues/148)
> Branch: `feature/148-correct-gpio-pin-assignments`
> Status: Planning — **RE-RUN v2 (2026-06-10): scope updated per issue comment**
> Spec: `docs/features/correct-gpio-pin-assignments/spec.md`

---

## ⚠️ Scope Change Notice (2026-06-10)

The issue was updated on 2026-06-10 with a validated pin audit and the following changes to scope:

| Change | Detail |
|--------|--------|
| **T4 (Route PCB Traces) — OUT OF SCOPE** | Routing is explicitly excluded from this issue. Netlist sync is in scope; re-routing existing and new traces is not. |
| **New: Footprint rename (T002)** | `Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical` → `Custom:ESP32-P4-PoE-ETH-PinSocket` across all generator files and the `.kicad_mod` file. |
| **Additional pin errors found** | Pins 2, 4, 26, and 33 had different wrong assignments than originally captured (see §1.3 below). |

---

## 1. Problem Summary

The generator in `hardware/generator/components.py` has three independent classes of error for the
J8 symbol definition and its wiring block.

### Class A — Signal on a physical GND or power pin (CRITICAL — will cause PCB short)

| J8 Pin | Physical function | Current net in generator |
|--------|------------------|--------------------------|
| 1 | GPIO25 (USB D+) | +3V3 ← power symbol on a GPIO pin |
| 3 | **GND** | STATUS_LED ← signal on a GND pin |
| 6 | GPIO2 | GND ← GND symbol on a GPIO pin |
| 8 | **GND** | FAN2_PWM ← signal on a GND pin |
| 9 | GPIO4 | GND ← GND symbol on a GPIO pin |
| 13 | **GND** | FAN2_TACH ← signal on a GND pin |
| 14 | GPIO15 | GND ← GND symbol on a GPIO pin |
| 17 | GPIO18 | +3V3 ← power symbol on a GPIO pin |
| 23 | **GND** | DHT11_DATA ← signal on a GND pin |
| 28 | **GND** | PROBE_LED ← signal on a GND pin |
| 33 | **GND** | FAN2_PWM ← signal on physical GND pad ⚠️ **NEW** |
| 34 | GPIO21 | GND ← GND symbol on a GPIO pin |

### Class B — Wrong power symbol on a GPIO pin (CRITICAL — incorrect schematic semantics)

Discovered by the 2026-06-10 pin audit against `docs/kb/ESP32-P4-POE-ETH/pin-layout.md`:

| J8 Pin | Physical function | Current net in generator | Correct net |
|--------|------------------|--------------------------|-------------|
| 2 | DM / GPIO24 (USB D−) | **+5V** (power_out) | NC (no_connect) — USB D-, not a power pin |
| 4 | SDA / GPIO7 (I²C Data) | **+5V** (power_out) | NC (no_connect) — I²C SDA, not a power pin |
| 20 | GPIO54 | **GND** (passive) | NC (no_connect) — valid GPIO, not GND |
| 25 | GPIO33 (EMAC_RXD1) | **GND** (passive) | NC (no_connect) — EMAC forbidden, not GND |
| 26 | GPIO32 (EMAC_RXD0) | **GND** (passive) | NC (no_connect) — EMAC forbidden, not GND ⚠️ **NEW** |
| 30 | RUN (system control) | **GND** (passive) | NC (no_connect) — reserved control pin |

> **Note on pins 2 and 4:** The original plan assumed these were already NC in `components.py`.
> The 2026-06-10 audit confirmed they are currently assigned `+5V (power_out)` — a critical error
> that misrepresents these GPIO lines as a power rail.

> **Note on pin 26:** The original plan assumed GPIO32/EMAC_RXD0 was already NC. The audit
> confirmed it is currently assigned GND — incorrect because it is a GPIO (albeit EMAC-forbidden).

> **Note on pin 33:** The original plan assumed pin 33 was NC → GND. The audit confirmed it
> currently carries `FAN2_PWM` — a signal on a physical GND pad, which is a Class A PCB-shorting error.

### Class C — Signal on wrong GPIO (firmware mismatch — will cause wrong MCU pin to be driven)

| J8 Pin | Physical GPIO | Current net | Expected GPIO | Source |
|--------|--------------|-------------|---------------|--------|
| 7 | GPIO3 | FAN1_PWM | GPIO4 (LEDC CH0) | constitution P-FW-02 |
| 10 | GPIO5 | FAN3_PWM | GPIO6 (LEDC CH2) | constitution P-FW-02 |
| 11 | GPIO6 | FAN4_PWM | GPIO7 (LEDC CH3) | constitution P-FW-02 |
| 12 | GPIO14 | FAN1_TACH | GPIO8 (IRQ) | constitution P-FW-02 |
| 15 | GPIO16 | FAN3_TACH | GPIO10 (IRQ) | constitution P-FW-02 |
| 16 | GPIO17 | FAN4_TACH | GPIO11 (IRQ) | constitution P-FW-02 |

> **Note on Class C:** The fan signal GPIOs in the current constitution (GPIO4–11) were themselves
> derived from the old (incorrect) pin layout. This fix moves all fan signals to the right column —
> where physical proximity to J2–J5 fan headers minimises PCB trace length — adopting GPIO20–27,
> 46, 47 which are confirmed available on the right column. This requires a **constitution
> amendment** to P-FW-02 before merge (see §7).

---

## 2. Authoritative Physical Pin Layout

**Source:** `docs/kb/ESP32-P4-POE-ETH/pin-layout.md` — verified from the Waveshare board silkscreen
image `ESP32-P4-ETH-details-inter-d78f8087f1a1597badd3a1d077c4c057.webp`. HIGH confidence.

### Left Column — J8 Pins 1–20 (x = 2.81 mm from left board edge)

| J8 Pin | y (mm) | Physical signal | GPIO# | Available? |
|--------|--------|----------------|-------|-----------|
| 1 | 52.93 | DP / GPIO25 | 25 | ✅ (USB D+, not used) |
| 2 | 50.39 | DM / GPIO24 | 24 | ✅ (USB D−, not used) |
| 3 | 47.85 | **GND** | — | ❌ |
| 4 | 45.31 | SDA / GPIO7 | 7 | ✅ (I²C SDA, unassigned) |
| 5 | 42.77 | SCL / GPIO8 | 8 | ✅ (I²C SCL, unassigned) |
| 6 | 40.23 | GPIO2 | 2 | ✅ → STATUS_LED |
| 7 | 37.69 | GPIO3 | 3 | ✅ (unassigned) |
| 8 | 35.15 | **GND** | — | ❌ |
| 9 | 32.61 | GPIO4 | 4 | ✅ (unassigned) |
| 10 | 30.07 | GPIO5 | 5 | ✅ (unassigned) |
| 11 | 27.53 | GPIO6 | 6 | ✅ (unassigned) |
| 12 | 24.99 | GPIO14 | 14 | ✅ (unassigned) |
| 13 | 22.45 | **GND** | — | ❌ |
| 14 | 19.91 | GPIO15 | 15 | ✅ → PROG_LED |
| 15 | 17.37 | GPIO16 | 16 | ✅ → DHT11_DATA |
| 16 | 14.83 | GPIO17 | 17 | ✅ (unassigned) |
| 17 | 12.29 | GPIO18 | 18 | ✅ (unassigned) |
| 18 | 9.75 | **GND** | — | ❌ |
| 19 | 7.21 | GPIO19 | 19 | ✅ → DS18B20_DATA |
| 20 | 4.67 | GPIO54 | 54 | ✅ (unassigned) |

### Right Column — J8 Pins 21–40 (x = 18.19 mm from left board edge)

| J8 Pin | y (mm) | Physical signal | GPIO# | Available? |
|--------|--------|----------------|-------|-----------|
| 21 | 52.93 | GPIO48 | 48 | ✅ → PROBE_LED |
| 22 | 50.39 | GPIO47 | 47 | ✅ → FAN4_TACH |
| 23 | 47.85 | **GND** | — | ❌ |
| 24 | 45.31 | GPIO46 | 46 | ✅ → FAN3_TACH |
| 25 | 42.77 | GPIO33 | 33 | ⛔ EMAC_RXD1 — forbidden |
| 26 | 40.23 | GPIO32 | 32 | ⛔ EMAC_RXD0 — forbidden |
| 27 | 37.69 | GPIO27 | 27 | ✅ → FAN4_PWM |
| 28 | 35.15 | **GND** | — | ❌ |
| 29 | 32.61 | GPIO26 | 26 | ✅ → FAN3_PWM |
| 30 | 30.07 | **RUN** (module EN) | — | ❌ reserved |
| 31 | 27.53 | GPIO23 | 23 | ✅ → FAN2_TACH |
| 32 | 24.99 | GPIO22 | 22 | ✅ → FAN1_TACH |
| 33 | 22.45 | **GND** | — | ❌ |
| 34 | 19.91 | GPIO21 | 21 | ✅ → FAN2_PWM |
| 35 | 17.37 | GPIO20 | 20 | ✅ → FAN1_PWM |
| 36 | 14.83 | **3V3 output** | — | ❌ power (source of +3V3) |
| 37 | 12.29 | **EN** (module reset) | — | ❌ reserved |
| 38 | 9.75 | **GND** | — | ❌ |
| 39 | 7.21 | **VSYS** | — | ❌ power (do not draw current) |
| 40 | 4.67 | **VBUS (5V)** | — | ❌ power (5V daughter board source) |

> ⛔ **EMAC conflict (pins 25 & 26):** GPIO32 and GPIO33 are internally wired to the LAN8720A PHY
> (EMAC_RXD0, EMAC_RXD1) via the ESP32-P4 IO_MUX and are driven by the EMAC peripheral at all
> times. Even though they appear on the J8 header, they **cannot** be used as general GPIO outputs
> or inputs by the daughter board. The issue #148 description marks them as "✅ signal" — this is
> incorrect and must not be acted upon. Confirmed by `docs/kb/ESP32-P4-POE-ETH/board-reference.md §2`
> and `docs/constitution.md P-FW-02`.  
> **Resolution:** FAN4_PWM uses GPIO27 (pin 27) and FAN3_TACH uses GPIO46 (pin 24) instead.

---

## 3. Complete Corrected Signal-to-Pin Mapping

### 3.1 Complete J8 Net Assignment Table

This table defines the **target state** for the generator. Every J8 pin is listed.

**Left column — `pins_left` in `s.define("Custom:J8_Waveshare", ...)`, wired in Row A block:**

| J8 Pin | Physical | Target Net | Pin Type | Change from current |
|--------|----------|------------|----------|---------------------|
| 1 | GPIO25 | NC | no_connect | +3V3 → NC ⚠️ |
| 2 | GPIO24 | NC | no_connect | **+5V → NC** ⚠️ NEW |
| 3 | GND | GND | passive | STATUS_LED → GND ⚠️ |
| 4 | GPIO7 | NC | no_connect | **+5V → NC** ⚠️ NEW |
| 5 | GPIO8 | NC | no_connect | unchanged |
| 6 | GPIO2 | STATUS_LED | output | GND → STATUS_LED ⚠️ |
| 7 | GPIO3 | NC | no_connect | FAN1_PWM → NC ⚠️ |
| 8 | GND | GND | passive | FAN2_PWM → GND ⚠️ |
| 9 | GPIO4 | NC | no_connect | GND → NC ⚠️ |
| 10 | GPIO5 | NC | no_connect | FAN3_PWM → NC ⚠️ |
| 11 | GPIO6 | NC | no_connect | FAN4_PWM → NC ⚠️ |
| 12 | GPIO14 | NC | no_connect | FAN1_TACH → NC ⚠️ |
| 13 | GND | GND | passive | FAN2_TACH → GND ⚠️ |
| 14 | GPIO15 | PROG_LED | output | GND → PROG_LED ⚠️ |
| 15 | GPIO16 | DHT11_DATA | input | FAN3_TACH → DHT11_DATA ⚠️ |
| 16 | GPIO17 | NC | no_connect | FAN4_TACH → NC ⚠️ |
| 17 | GPIO18 | NC | no_connect | +3V3 → NC ⚠️ |
| 18 | GND | GND | passive | NC → GND ⚠️ |
| 19 | GPIO19 | DS18B20_DATA | bidirectional | NC → DS18B20_DATA ⚠️ |
| 20 | GPIO54 | NC | no_connect | **GND → NC** ⚠️ |

**Right column — `pins_right` in `s.define("Custom:J8_Waveshare", ...)`, wired in Row B block:**

| J8 Pin | Physical | Target Net | Pin Type | Change from current |
|--------|----------|------------|----------|---------------------|
| 21 | GPIO48 | PROBE_LED | output | NC → PROBE_LED ⚠️ |
| 22 | GPIO47 | FAN4_TACH | input | PROG_LED → FAN4_TACH ⚠️ |
| 23 | GND | GND | passive | DHT11_DATA → GND ⚠️ |
| 24 | GPIO46 | FAN3_TACH | input | NC → FAN3_TACH ⚠️ |
| 25 | GPIO33 (EMAC) | NC | no_connect | **GND → NC** ⚠️ |
| 26 | GPIO32 (EMAC) | NC | no_connect | **GND → NC** ⚠️ NEW |
| 27 | GPIO27 | FAN4_PWM | output | DS18B20_DATA → FAN4_PWM ⚠️ |
| 28 | GND | GND | passive | PROBE_LED → GND ⚠️ |
| 29 | GPIO26 | FAN3_PWM | output | NC → FAN3_PWM ⚠️ |
| 30 | RUN | NC | no_connect | **GND → NC** ⚠️ |
| 31 | GPIO23 | FAN2_TACH | input | NC → FAN2_TACH ⚠️ |
| 32 | GPIO22 | FAN1_TACH | input | NC → FAN1_TACH ⚠️ |
| 33 | GND | GND | passive | **FAN2_PWM → GND** ⚠️ NEW |
| 34 | GPIO21 | FAN2_PWM | output | **GND → FAN2_PWM** ⚠️ |
| 35 | GPIO20 | FAN1_PWM | output | NC → FAN1_PWM ⚠️ |
| 36 | 3V3 | +3V3 | power_out | NC → +3V3 ⚠️ |
| 37 | EN | NC | no_connect | NC → NC (unchanged) |
| 38 | GND | GND | passive | GND → GND (unchanged) |
| 39 | VSYS | NC | no_connect | NC → NC (unchanged) |
| 40 | VBUS | +5V | power_out | +5V → +5V (unchanged) |

### 3.2 Firmware GPIO Impact (new vs. current)

| Signal | Current GPIO (constitution) | New GPIO (this fix) | Δ |
|--------|-----------------------------|---------------------|---|
| STATUS_LED | GPIO2 | GPIO2 | ← unchanged (pin moves: 3→6) |
| PROG_LED | GPIO15 | GPIO15 | ← unchanged (pin moves: 22→14) |
| DHT11_DATA | GPIO16 | GPIO16 | ← unchanged (pin moves: 23→15) |
| DS18B20_DATA | GPIO19 | GPIO19 | ← unchanged (pin moves: 27→19) |
| PROBE_LED | **GPIO20** | **GPIO48** | ← GPIO changes |
| FAN1_PWM | GPIO4 | **GPIO20** | ← GPIO changes |
| FAN2_PWM | GPIO5 | **GPIO21** | ← GPIO changes |
| FAN3_PWM | GPIO6 | **GPIO26** | ← GPIO changes |
| FAN4_PWM | GPIO7 | **GPIO27** | ← GPIO changes |
| FAN1_TACH | GPIO8 | **GPIO22** | ← GPIO changes |
| FAN2_TACH | GPIO9 | **GPIO23** | ← GPIO changes |
| FAN3_TACH | GPIO10 | **GPIO46** | ← GPIO changes |
| FAN4_TACH | GPIO11 | **GPIO47** | ← GPIO changes |

> **Note:** GPIO9–11 (current FAN2–4 TACH) and GPIO7–8 (current FAN4 PWM / FAN1 TACH) do not
> appear on J8 at all (GPIO7/8 appear as SDA/SCL at pins 4/5 and have no TACH wiring). GPIO9,
> 10, 11 are entirely absent from the 40-pin header. The current firmware cannot function correctly
> with these assignments.

---

## 4. Architecture Fit

### 4.1 Constitution Principles

| Constitution principle | How this plan satisfies it |
|------------------------|---------------------------|
| **P-HW-05** — Schematic generated, not hand-edited | All changes are implemented exclusively in `hardware/generator/components.py`. The `.kicad_sch` is rebuilt by running `python hardware/generate_project.py`. No hand-editing of the schematic. |
| **P-HW-06** — Grid discipline | Symbol geometry (`body_w=25.4 mm`, `body_h=50.8 mm`) is unchanged. Only pin name strings, pin type strings, and net-wiring calls change. The `snap()` function in the generator enforces grid compliance on all wire endpoints. |
| **P-KI-04** — Generator is schematic source of truth | `components.py` is the sole authoritative source. The diff in the generated `.kicad_sch` is a downstream artefact of the generator changes. |
| **P-KI-07** — PCB is hand-edited in KiCad GUI | The `.kicad_pcb` is updated via "Update PCB from Schematic" in KiCad after schematic regeneration; no script touches the PCB file. |
| **P-HW-04** — Board outline / J8 placement | J8 mechanical placement (left edge, 78 mm span, 15.38 mm row-to-row) is unchanged. Only nets on pads change. |
| **P-HW-09** — Polarised connectors | J8 is explicitly exempt (board-to-board mating connector). |
| **P-TEST-01** — Zero ERC errors | The corrected schematic must pass ERC before the PR is merged. |
| **P-TEST-03** — Zero DRC errors | The PCB must pass DRC after netlist sync and re-routing. |
| **P-FW-02** — Peripheral ownership | The table in §P-FW-02 must be amended to record the new GPIO numbers (Change 5 below). |
| **P-SCH-01** — Global labels for inter-block signals | All fan, LED, and sensor signals continue to use `global_label` elements as they do now. |
| **P-SCH-05** — Correct pin types | NC pins use `no_connect`, GND pins use `passive`, signal output pins use `output`, bidirectional pins use `bidirectional`. Updated in `pins_left` / `pins_right` definition. |

### 4.2 PCB Layout Impact

The signal re-assignment moves all eight fan signals from the left column (x = 2.81 mm) to the
right column (x = 18.19 mm). The fan headers J2–J5 are in the right zone of the daughter board
(x > 21 mm). This **shortens** the PCB traces from J8 to J2–J5 by approximately 15–16 mm per
trace, reducing routing congestion and improving signal integrity. The PCB netlist sync will produce
airwires on all previously routed fan signal pads; all fan traces must be rerouted after the sync.

---

## 5. Hardware Implementation Approach

### Change 1 — `hardware/generator/components.py`: Fix `pins_left` in symbol definition

**Location:** `s.define("Custom:J8_Waveshare", ...)` call (~line 128 of `components.py`).

Replace the current `pins_left` list with:

```python
pins_left=[
    # Consecutive pins 1..20 — Row A (top-to-bottom in symbol = bottom→top on physical board)
    # Source: docs/kb/ESP32-P4-POE-ETH/pin-layout.md (HIGH confidence, verified from board image)
    ("NC",           "1",  "no_connect"),  # GPIO25 (USB D+) — not used by daughter board
    ("NC",           "2",  "no_connect"),  # GPIO24 (USB D−) — not used
    ("GND",          "3",  "passive"),     # Physical GND
    ("NC",           "4",  "no_connect"),  # GPIO7  (SDA) — not used
    ("NC",           "5",  "no_connect"),  # GPIO8  (SCL) — not used
    ("STATUS_LED",   "6",  "output"),      # GPIO2  → STATUS_LED
    ("NC",           "7",  "no_connect"),  # GPIO3  — not used
    ("GND",          "8",  "passive"),     # Physical GND
    ("NC",           "9",  "no_connect"),  # GPIO4  — not used (available)
    ("NC",           "10", "no_connect"),  # GPIO5  — not used (available)
    ("NC",           "11", "no_connect"),  # GPIO6  — not used (available)
    ("NC",           "12", "no_connect"),  # GPIO14 — not used
    ("GND",          "13", "passive"),     # Physical GND
    ("PROG_LED",     "14", "output"),      # GPIO15 → PROG_LED (OTA/write indicator)
    ("DHT11_DATA",   "15", "input"),       # GPIO16 → DHT11 single-wire DATA
    ("NC",           "16", "no_connect"),  # GPIO17 — not used
    ("NC",           "17", "no_connect"),  # GPIO18 — not used
    ("GND",          "18", "passive"),     # Physical GND
    ("DS18B20_DATA", "19", "bidirectional"), # GPIO19 → 1-Wire temp probe DATA
    ("NC",           "20", "no_connect"),  # GPIO54 — not used
],
```

### Change 2 — `hardware/generator/components.py`: Fix `pins_right` in symbol definition

Replace the current `pins_right` list with:

```python
pins_right=[
    # Consecutive pins 21..40 — Row B (top-to-bottom in symbol = bottom→top on physical board)
    # Source: docs/kb/ESP32-P4-POE-ETH/pin-layout.md (HIGH confidence, verified from board image)
    ("PROBE_LED",    "21", "output"),      # GPIO48  → PROBE_LED (probe health indicator)
    ("FAN4_TACH",    "22", "input"),       # GPIO47  → FAN4 tachometer input
    ("GND",          "23", "passive"),     # Physical GND
    ("FAN3_TACH",    "24", "input"),       # GPIO46  → FAN3 tachometer input
    ("NC",           "25", "no_connect"),  # GPIO33  — EMAC_RXD1: FORBIDDEN — do not use
    ("NC",           "26", "no_connect"),  # GPIO32  — EMAC_RXD0: FORBIDDEN — do not use
    ("FAN4_PWM",     "27", "output"),      # GPIO27  → FAN4 PWM output (LEDC CH3)
    ("GND",          "28", "passive"),     # Physical GND
    ("FAN3_PWM",     "29", "output"),      # GPIO26  → FAN3 PWM output (LEDC CH2)
    ("NC",           "30", "no_connect"),  # RUN (chip enable) — RESERVED — do not use
    ("FAN2_TACH",    "31", "input"),       # GPIO23  → FAN2 tachometer input
    ("FAN1_TACH",    "32", "input"),       # GPIO22  → FAN1 tachometer input
    ("GND",          "33", "passive"),     # Physical GND
    ("FAN2_PWM",     "34", "output"),      # GPIO21  → FAN2 PWM output (LEDC CH1)
    ("FAN1_PWM",     "35", "output"),      # GPIO20  → FAN1 PWM output (LEDC CH0)
    ("+3V3",         "36", "power_out"),   # 3.3 V output — sole +3V3 source on J8
    ("NC",           "37", "no_connect"),  # EN (module reset) — RESERVED
    ("GND",          "38", "passive"),     # Physical GND
    ("NC",           "39", "no_connect"),  # VSYS — do NOT draw current (issue #137)
    ("+5V",          "40", "power_out"),   # VBUS — 5V source for daughter board (confirmed OQ-02)
],
```

### Change 3 — `hardware/generator/components.py`: Fix J8 wiring block

**Location:** The `p = s.component("Custom:J8_Waveshare", ...)` block and its subsequent signal
wiring (~lines 522–563 of `components.py`).

Replace the wiring block entirely with:

```python
# --- Row A (pins 1-20, left side) — use angle=180 for global_labels ---
# pins 1,2,4,5,7,9,10,11,12,16,17,20: NC (handled by pin type in define())
s.power("GND",               *p["3"])                                    # physical GND
s.global_label("STATUS_LED", *p["6"],  shape="output", angle=180)       # GPIO2
s.power("GND",               *p["8"])                                    # physical GND
s.power("GND",               *p["13"])                                   # physical GND
s.global_label("PROG_LED",   *p["14"], shape="output", angle=180)       # GPIO15
s.global_label("DHT11_DATA", *p["15"], shape="input",  angle=180)       # GPIO16
s.power("GND",               *p["18"])                                   # physical GND
s.global_label("DS18B20_DATA", *p["19"], shape="bidirectional", angle=180)  # GPIO19

# --- Row B (pins 21-40, right side) — use angle=0 for global_labels ---
# pins 25,26,30,37,39: NC (handled by pin type in define())
s.global_label("PROBE_LED",  *p["21"], shape="output")                  # GPIO48
s.global_label("FAN4_TACH",  *p["22"], shape="input")                   # GPIO47
s.power("GND",               *p["23"])                                   # physical GND
s.global_label("FAN3_TACH",  *p["24"], shape="input")                   # GPIO46
s.global_label("FAN4_PWM",   *p["27"], shape="output")                  # GPIO27
s.power("GND",               *p["28"])                                   # physical GND
s.global_label("FAN3_PWM",   *p["29"], shape="output")                  # GPIO26
s.global_label("FAN2_TACH",  *p["31"], shape="input")                   # GPIO23
s.global_label("FAN1_TACH",  *p["32"], shape="input")                   # GPIO22
s.power("GND",               *p["33"])                                   # physical GND
s.global_label("FAN2_PWM",   *p["34"], shape="output")                  # GPIO21
s.global_label("FAN1_PWM",   *p["35"], shape="output")                  # GPIO20
s.power("+3V3",              *p["36"], pin_type="power_out")             # 3V3 sole source on J8
s.power("GND",               *p["38"])                                   # physical GND
s.power("+5V",               *p["40"], pin_type="power_out")             # VBUS — 5V source
```

> **+3V3 wiring note:** Because +3V3 now comes from pin 36 (right column) instead of pins 1 and 17
> (left column), the wires from `p["36"]` to the TACH pull-up resistors (R5–R8) and the DHT11 VCC
> net will route across the schematic. If the layout becomes hard to read, the generator may
> introduce a short wire stub + label (e.g. `s.wlabel_r("+3V3", *p["36"])`) and rely on the power
> symbol net propagation to connect R5–R8 and HUM1 via name-matching. Both approaches are ERC-clean.

### Change 4 — Rename J8 footprint (NEW — T002)

**Scope added 2026-06-10.** The footprint must be renamed from:
- **Old:** `Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical`
- **New:** `Custom:ESP32-P4-PoE-ETH-PinSocket`

Apply the rename in all of the following locations:

| File | Change |
|------|--------|
| `hardware/generator/components.py` | Update the `footprint=` argument in the `s.define("Custom:J8_Waveshare", ...)` call and any `s.component(...)` call referencing the old name |
| `hardware/generator/gen_footprint_j8.py` | Update the footprint name string at the top of the generated `.kicad_mod` output |
| `hardware/kicad/footprints/Custom.pretty/` | Rename `PinSocket_2x20_P2.54mm_P15.38mm_Vertical.kicad_mod` → `ESP32-P4-PoE-ETH-PinSocket.kicad_mod` and update the `(footprint "Custom:ESP32-P4-PoE-ETH-PinSocket" ...)` header inside the file |
| `hardware/bom/bom.py` (if present) | Update any string referencing the old footprint name |

> The rename propagates automatically to `.kicad_sch` and `.kicad_pcb` when the schematic is
> regenerated (T003) and the PCB netlist is synced (T004). No hand-editing of those files is
> required.

### Change 5 — Regenerate schematic (T003)

```bash
cd hardware
python generate_project.py
```

This writes `hardware/kicad/PoE-FanController.kicad_sch`. Run after Changes 1–4 are complete.
Immediately follow with ERC (gate: 0 errors):

```bash
kicad-cli sch erc hardware/kicad/PoE-FanController.kicad_sch \
  --output hardware/kicad/erc_output.json
```

### Change 6 — Amend `docs/constitution.md` P-FW-02 peripheral ownership table

Update the peripheral ownership table for the `fan` and `probe` modules:

| ESP32 Peripheral | Owner module | Old pins | New pins |
|-----------------|--------------|----------|---------|
| LEDC channels 0–3 | `fan` | GPIO4 (FAN1), GPIO5 (FAN2), GPIO6 (FAN3), GPIO7 (FAN4) | **GPIO20 (FAN1), GPIO21 (FAN2), GPIO26 (FAN3), GPIO27 (FAN4)** |
| GPIO interrupts (TACH) | `fan` | GPIO8, GPIO9, GPIO10, GPIO11 | **GPIO22, GPIO23, GPIO46, GPIO47** |
| GPIO output (probe status LED) | `probe` | GPIO20 (PROBE_LED) | **GPIO48 (PROBE_LED)** |
| GPIO digital input (STATUS_LED) | `main` | GPIO2 — Via J8 **left** pin 3 | GPIO2 — Via J8 **left** pin 6 |
| GPIO output (OTA activity LED) | `ota` | GPIO15 — Via J8 **right** pin 22 | GPIO15 — Via J8 **left** pin 14 |
| GPIO digital input (DHT11) | `temp` | GPIO16 — Via J8 **right** pin 23 | GPIO16 — Via J8 **left** pin 15 |
| 1-Wire bus (DS18B20) | `probe` | GPIO19 — Via J8 **left** pin 27 | GPIO19 — Via J8 **left** pin 19 |

Also update the J8 BOM entry in §2.2 to reflect the new footprint name
`Custom:ESP32-P4-PoE-ETH-PinSocket`.

### Change 7 — PCB netlist sync (T004)

Open `hardware/kicad/PoE-FanController.kicad_pcb` in KiCad GUI:

1. **Inspect → Board Statistics** — note current connected/unconnected counts for baseline.
2. **Tools → Update PCB from Schematic** — accept all changes (new net assignments, renamed
   footprint reference propagation).
3. **Inspect → Net Inspector** — verify FAN1_PWM net is on J8 pad 35 and fan header J2 pin 4;
   FAN1_TACH on pad 32 and J2 pin 3; etc.

> **⛔ Routing is OUT OF SCOPE for this issue.** After the netlist sync, airwires will appear on
> previously-routed fan signal pads. These are expected and will remain unrouted. PCB re-routing
> is a separate follow-on task.

### Change 8 — DRC (T005)

After PCB netlist sync (Change 7), run DRC from the KiCad PCB editor:

- Target: zero DRC rule violations.
- Unconnected airwires from the routing gap are expected and are **not** a DRC failure (they are
  "unconnected" violations, separately gated by the PR checklist).
- Pre-existing solder-mask-bridge suppressions are excluded.

---

## 6. Task Summary and Testing Strategy

### Task Map

| Task | Description | Gate |
|------|-------------|------|
| **T001** | Fix all J8 pin assignments in `components.py` (define block + wiring block) | Code review: every pin matches §3.1 table |
| **T002** | Rename footprint from `Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical` to `Custom:ESP32-P4-PoE-ETH-PinSocket` in all files | No references to old name remain in repo |
| **T003** | Regenerate schematic via `python hardware/generate_project.py` + run ERC | **ERC = 0 errors** (blocking) |
| **T004** | Sync PCB netlist from corrected schematic via "Update PCB from Schematic" | Net Inspector spot-check passes |
| **T005** | Run DRC and verify clean | **DRC = 0 rule violations** (blocking) |
| **T006** | Update `docs/constitution.md` P-FW-02 + BOM entry + close issue | Diff review passes |

> ⛔ **"Route PCB Traces" is NOT a task in this issue.** Airwires produced by the netlist sync are
> expected and are tracked as a separate follow-on. This scope boundary was confirmed in the
> 2026-06-10 issue update.

---

### T-01 — Pre-implementation: cross-check against authoritative image

Before editing any file, open
`docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-details-inter-d78f8087f1a1597badd3a1d077c4c057.webp` and
verify the following against §2 tables:

| Check | Expected |
|-------|----------|
| Pin 2 (left col) | DM / GPIO24 — NOT a 5V power rail |
| Pin 4 (left col) | SDA / GPIO7 — NOT a 5V power rail |
| Pin 3 (left col) | GND label |
| Pin 6 (left col) | GPIO2 label |
| Pin 23 (right col) | GND label |
| Pin 26 (right col) | GPIO32 label — EMAC, NOT GND |
| Pin 28 (right col) | GND label |
| Pin 33 (right col) | GND label — NOT a signal pad |
| Pin 34 (right col) | GPIO21 label |
| Pin 35 (right col) | GPIO20 label |
| Pin 36 (right col) | 3V3 label |
| Pin 40 (right col) | VBUS label |

### T-02 — Generator self-test: ERC after each change

After Changes 1–4 (T001 + T002), run:
```bash
cd hardware && python generate_project.py
kicad-cli sch erc hardware/kicad/PoE-FanController.kicad_sch --output hardware/kicad/erc_output.json
```
Target: zero errors. Any ERC error indicates a pin-type mismatch, floating net, or footprint
reference inconsistency.

### T-03 — Net membership spot-check (post-generation)

Open the generated `.kicad_sch` in KiCad. Use **Inspect → Net Inspector** to verify:

| Net | Must include | Must NOT include |
|-----|-------------|-----------------|
| GND | J8 pads 3, 8, 13, 18, 23, 28, 33, 38 | J8 pads 2, 4, 20, 25, 26, 30 |
| +3V3 | J8 pad 36 | J8 pads 1, 17 |
| +5V | J8 pad 40 | J8 pads 2, 4 |
| STATUS_LED | J8 pad 6, R3 pin 1 | J8 pad 3 |
| FAN1_PWM | J8 pad 35, J2 pin 4 | J8 pads 7, 8 |
| FAN2_PWM | J8 pad 34, J3 pin 4 | J8 pad 33 |
| FAN3_PWM | J8 pad 29, J4 pin 4 | J8 pads 10 |
| FAN4_PWM | J8 pad 27, J5 pin 4 | J8 pads 11 |
| FAN1_TACH | J8 pad 32, J2 pin 3, R5 pin 2 | J8 pad 12 |
| FAN2_TACH | J8 pad 31, J3 pin 3, R6 pin 2 | J8 pad 13 |
| FAN3_TACH | J8 pad 24, J4 pin 3, R7 pin 2 | J8 pad 15 |
| FAN4_TACH | J8 pad 22, J5 pin 3, R8 pin 2 | J8 pad 16 |
| PROG_LED | J8 pad 14, R13 pin 1 | J8 pad 22 |
| DHT11_DATA | J8 pad 15, HUM1 pin 2 | J8 pad 23 |
| DS18B20_DATA | J8 pad 19, R14 pin 2, J6 pin 2 | J8 pad 27 |
| PROBE_LED | J8 pad 21, R15 pin 1 | J8 pad 28 |

### T-04 — TACH pull-up power path

Verify that the +3V3 net (sourced from J8 pad 36) is connected to:
- R5 pin 1, R6 pin 1, R7 pin 1, R8 pin 1 (TACH pull-ups)
- HUM1 pin 1 (DHT11 VCC)

### T-05 — PCB DRC after netlist sync

After PCB netlist sync (T004):
- Run DRC from KiCad PCB editor.
- Zero DRC rule violations (clearance, footprint courtyard, etc.).
- Unconnected airwires (from out-of-scope routing) are noted but do not block this issue.
- Pre-existing solder-mask-bridge suppressions are excluded.

### T-06 — Footprint rename verification

Confirm no reference to `PinSocket_2x20_P2.54mm_P15.38mm_Vertical` remains in:
```bash
git grep "PinSocket_2x20" -- hardware/
```
Expected: zero matches.

### T-07 — Constitution amendment diff review

Confirm that `docs/constitution.md` P-FW-02 table shows:
- LEDC channels: GPIO20, 21, 26, 27
- TACH interrupts: GPIO22, 23, 46, 47
- PROBE_LED: GPIO48
- J8 pin references corrected for STATUS_LED (pin 6), PROG_LED (pin 14), DHT11 (pin 15), DS18B20 (pin 19)
- J8 BOM entry (§2.2) reflects new footprint name `Custom:ESP32-P4-PoE-ETH-PinSocket`

---

## 7. Risks

| Risk | Likelihood | Severity | Mitigation |
|------|-----------|----------|-----------|
| Issue #148 description marks GPIO32/33 (EMAC) as usable — acting on this would drive EMAC signals with fan PWM | HIGH (if not caught) | CRITICAL — ethernet failure + possible GPIO contention | Plan explicitly uses GPIO27/GPIO46 instead; EMAC conflict noted in §2 and confirmed from board-reference.md §2 and constitution P-FW-02 |
| Pins 2 and 4 were `+5V` in components.py — KiCad treats this as a power source on a USB D± line | HIGH (already confirmed) | HIGH — ERC "power pin not driven" or net conflict | T001 correction changes these to `no_connect`; ERC gate (T003) enforces this |
| Pin 33 carries FAN2_PWM in components.py — signal wire short-circuits to physical GND pad | HIGH (already confirmed) | CRITICAL — PCB short if routed | T001 correction moves FAN2_PWM to pin 34 (GPIO21) and makes pin 33 `GND (passive)` |
| Footprint rename (`PinSocket_...` → `ESP32-P4-PoE-ETH-PinSocket`) may leave orphaned footprint reference in `.kicad_pcb` if netlist sync is not performed after rename | MEDIUM | MEDIUM — DRC "footprint not found" error | T004 netlist sync resolves this; T002 must be completed before T003/T004 |
| GPIO47/48 not confirmed usable in existing KB docs | LOW — only GPIO31, 32–37, 50–52 are listed as forbidden | MEDIUM | Consult `esp32.expert` before merge; GPIO47/48 are not in the forbidden list and appear freely on J8 at pins 22/21 |
| PCB has existing routed fan traces from left-column J8 pads; after netlist sync those traces become unrouted airwires | HIGH | LOW — routing work needed, no net-topology error | Expected consequence; routing is explicitly out of scope for this issue; tracked as follow-on |
| `s.power("+3V3", *p["36"], pin_type="power_out")` conflicts with existing +3V3 power_out from another source (ERC: multiple power-out drivers on same net) | LOW | LOW | Use `pin_type="power_in"` if ERC reports conflict |
| Symbol pin count or ordering change shifts all subsequent pin y-positions in the generator, misaligning wire stubs from neighbouring blocks | MEDIUM | MEDIUM — wires land at wrong coordinates → ERC disconnected stubs | Run ERC immediately after every regeneration (T003 gate) |
| Constitution amendment to P-FW-02 may conflict with in-progress firmware work in a parallel branch | LOW | LOW | Coordinate with firmware author before merge; no firmware source files exist yet per project status |

---

## 8. Constitution Compliance

| Principle | How satisfied |
|-----------|--------------|
| **P-HW-05** — Schematic generated, never hand-edited | All changes in `components.py` and `gen_footprint_j8.py`; `.kicad_sch` is a build artefact of `generate_project.py`. |
| **P-HW-06** — Grid discipline | Symbol body unchanged (25.4 × 50.8 mm). `snap()` enforces grid on all wire endpoints. Only net name strings, pin type strings, and the footprint name string change. |
| **P-HW-01/02** — Two-layer, top-side placement | No layer or component placement changes. |
| **P-HW-04** — Board outline | J8 physical position unchanged. Only pad nets and footprint name change. |
| **P-HW-09** — Polarised connectors | J8 explicitly exempt; no change. |
| **P-KI-01/02/03** — File format locks | Generator emits the same format version tokens; no format upgrade. |
| **P-KI-04** — Generator is schematic source of truth | Plan modifies only `components.py` and `gen_footprint_j8.py`. |
| **P-KI-07** — PCB is hand-edited | PCB updated via KiCad GUI only; no script writes to `.kicad_pcb`. |
| **P-TEST-01** — Zero ERC errors | ERC run after regeneration (T003); blocking criterion for merge. |
| **P-TEST-03** — Zero DRC errors | DRC run after netlist sync (T005); blocking criterion for merge. |
| **P-FW-02** — Peripheral ownership documented | Constitution amendment (Change 6) updates GPIO table; new values match physical pin layout and avoid all EMAC-forbidden GPIOs. |
| **P-SCH-01** — Global labels | All inter-block signals continue to use `global_label` elements. |
| **P-SCH-03** — Section header style | Section header text calls in components.py are unchanged. |
| **P-SCH-05** — Correct pin types | NC pins → `no_connect`; GND pins → `passive`; signal output/input/bidir correctly assigned per updated lists. Pins 2, 4 corrected from `power_out` to `no_connect`. |

---

## 9. References

| Resource | Location |
|----------|----------|
| GitHub issue #148 | https://github.com/nielsverhoeven/PoE-FanController/issues/148 |
| Authoritative J8 pinout (verified image) | `docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-details-inter-*.webp` |
| KB pin layout reference | `docs/kb/ESP32-P4-POE-ETH/pin-layout.md` |
| KB board reference (§2 forbidden GPIOs, §4.1 power pins) | `docs/kb/ESP32-P4-POE-ETH/board-reference.md` |
| Generator component definitions + wiring | `hardware/generator/components.py` |
| Generator schematic builder | `hardware/generator/schematic.py` |
| Project constitution (P-HW-05, P-FW-02, P-TEST-01/03) | `docs/constitution.md` |
| Feature spec | `docs/features/correct-gpio-pin-assignments/spec.md` |
| Previous pin-layout fix (issue #133) | `docs/features/esp32-p4-eth-pin-layout/plan.md` |
