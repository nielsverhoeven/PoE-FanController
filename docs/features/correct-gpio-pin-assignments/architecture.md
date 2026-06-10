# Architecture Note: Correct GPIO Pin Assignments (Issue #148)

> Feature: `correct-gpio-pin-assignments`
> Branch: `feature/148-correct-gpio-pin-assignments`
> Architect validation date: 2026-06-10
> Constitution version at validation: **4.2.0** (amended by this feature)
> Result: **APPROVED WITH CHANGES** — constitution amendment v4.2.0 applied

---

## 1. Validation Scope

This note validates `docs/features/correct-gpio-pin-assignments/plan.md` against
`docs/constitution.md` and records all architecture decisions and expert findings for issue #148.

---

## 2. GPIO Capability Findings (esp32.expert consultation)

All checks performed against `docs/kb/ESP32-P4-POE-ETH/board-reference.md`,
`docs/kb/ESP32-P4-POE-ETH/pin-layout.md`, `docs/kb/esp32-p4-reference.md`,
and the ESP32-P4 Technical Reference Manual.

### 2.1 EMAC Conflict — GPIO32 and GPIO33

| GPIO | EMAC function | IO_MUX | Can be used for fan signals? |
|------|---------------|--------|------------------------------|
| GPIO32 | EMAC_RXD0 | **Fixed** (cannot be remapped) | ⛔ FORBIDDEN |
| GPIO33 | EMAC_RXD1 | **Fixed** (cannot be remapped) | ⛔ FORBIDDEN |

**Source:** `board-reference.md §2`, `esp32-p4-reference.md §2`, ESP32-P4 TRM §EMAC.

**Consequence for plan:** The issue #148 description incorrectly marks GPIO32/33 as usable.
The plan correctly identifies this and substitutes:
- FAN4_PWM → **GPIO27** (J8 pin 27) instead of GPIO33
- FAN3_TACH → **GPIO46** (J8 pin 24) instead of GPIO32

### 2.2 GPIO26 and GPIO27 — EMAC Safety

The forbidden EMAC set for the ESP32-P4-POE-ETH is:
**{GPIO31, GPIO32, GPIO33, GPIO34, GPIO35, GPIO36, GPIO37, GPIO50, GPIO51, GPIO52}**

GPIO26 and GPIO27 are **not** in this set and appear in the authoritative 40-pin header layout
(pins 29 and 27 respectively). ✅ **Safe for LEDC PWM.**

### 2.3 LEDC PWM Capability — GPIO20, GPIO21, GPIO26, GPIO27

The ESP32-P4 LEDC peripheral is routed to output pins exclusively via the **GPIO matrix**.
Any GPIO that is:
(a) not occupied by a fixed-function peripheral (EMAC, UART, strapping), and
(b) accessible on the header,

can be assigned to a LEDC channel. All four proposed PWM GPIOs satisfy both conditions:

| Signal | GPIO | J8 Pin | EMAC conflict? | Strapping pin? | LEDC capable? |
|--------|------|--------|----------------|----------------|---------------|
| FAN1_PWM | GPIO20 | 35 | ✅ No | ✅ No | ✅ YES |
| FAN2_PWM | GPIO21 | 34 | ✅ No | ✅ No | ✅ YES |
| FAN3_PWM | GPIO26 | 29 | ✅ No | ✅ No | ✅ YES |
| FAN4_PWM | GPIO27 | 27 | ✅ No | ✅ No | ✅ YES |

### 2.4 GPIO Interrupt / TACH Capability — GPIO22, GPIO23, GPIO46, GPIO47, GPIO48

All ESP32-P4 GPIOs that are connected to the GPIO matrix support edge-triggered and
level-triggered interrupts. The five proposed TACH/LED GPIOs:

| Signal | GPIO | J8 Pin | In authoritative table? | Forbidden list? | IRQ capable? |
|--------|------|--------|------------------------|-----------------|--------------|
| FAN1_TACH | GPIO22 | 32 | ✅ Yes (`pin-layout.md`) | ✅ No | ✅ YES |
| FAN2_TACH | GPIO23 | 31 | ✅ Yes (`pin-layout.md`) | ✅ No | ✅ YES |
| FAN3_TACH | GPIO46 | 24 | ✅ Yes (`board-reference.md §4`) | ✅ No | ✅ YES |
| FAN4_TACH | GPIO47 | 22 | ✅ Yes (`board-reference.md §4`) | ✅ No | ✅ YES |
| PROBE_LED  | GPIO48 | 21 | ✅ Yes (`board-reference.md §4`) | ✅ No | ✅ YES (output) |

> **Risk item from plan §7 resolved:** The plan flagged GPIO47/48 as "not confirmed usable in
> existing KB docs". They ARE listed in `board-reference.md §4` (full 40-pin table, pins 22 and 21)
> and are absent from the forbidden GPIO list in `board-reference.md §4.3`. Confirmed safe.

---

## 3. Constitution Compliance Check

| Constitution principle | Status | Notes |
|------------------------|--------|-------|
| **P-HW-05** — Schematic generated, not hand-edited | ✅ PASS | All changes in `hardware/generator/components.py`; `.kicad_sch` is a build artefact only |
| **P-HW-06** — Grid discipline | ✅ PASS | Symbol body geometry unchanged (25.4 × 50.8 mm); only pin names, types, and net wiring change; `snap()` enforces grid compliance |
| **P-HW-01/02** — Two-layer, top-side placement only | ✅ PASS | No layer or placement changes |
| **P-HW-04** — Board outline and J8 placement | ✅ PASS | J8 mechanical position unchanged; only pad nets change |
| **P-HW-09** — Polarised connectors | ✅ PASS | J8 is explicitly exempt (board-to-board); no new cable connectors added |
| **P-KI-01/02/03** — KiCad version and format locks | ✅ PASS | Generator emits same format tokens; no version upgrade |
| **P-KI-04** — Generator is schematic source of truth | ✅ PASS | Only `components.py` is modified; `.kicad_sch` is downstream artefact |
| **P-KI-07** — PCB is hand-edited in KiCad GUI | ✅ PASS | PCB updated via "Update PCB from Schematic" in KiCad; no script writes to `.kicad_pcb` |
| **P-TEST-01** — Zero ERC errors | ✅ REQUIRED | Plan mandates ERC run (T-02) after each generator iteration; blocking merge criterion |
| **P-TEST-03** — Zero DRC errors | ✅ REQUIRED | Plan mandates DRC run (T-05) after PCB netlist sync; blocking merge criterion |
| **P-FW-02** — Peripheral ownership documented | ⚠️ AMENDED | Table updated in constitution v4.2.0 (see §4 below) |
| **P-FW-03** — PWM 25 kHz / 8-bit | ✅ PASS | PWM specification unchanged; LEDC configuration unchanged except GPIO numbers |
| **P-SCH-01** — Global labels for inter-block signals | ✅ PASS | All signals continue to use `global_label` elements |
| **P-SCH-05** — Correct pin types | ✅ PASS | NC → `no_connect`; GND → `passive`; signal outputs/inputs/bidir correctly typed in updated lists |

---

## 4. Required Constitution Amendment

**Amendment version:** v4.2.0 (MINOR)
**Rationale for MINOR classification:** Updates table entries in P-FW-02 to correct GPIO
assignments and pin references; also corrects pre-existing EMAC MDIO entry (GPIO28→GPIO52).
No architectural principle is removed or redefined; no MAJOR technology choice changes.

### 4.1 Changes Applied to Constitution

The following edits were applied to `docs/constitution.md`:

**§2.3 Firmware table — DHT11 pin reference:** Corrected "J8 pin 23" → "J8 pin 15"
(pin 23 is physically GND; pin 15 = GPIO16 is the correct DHT11 DATA connection).

**§4 P-FW-02 Peripheral ownership table — complete replacement:**
- LEDC channels: GPIO4/5/6/7 → **GPIO20/21/26/27** with J8 right-column pin references
- GPIO interrupts (TACH): GPIO8/9/10/11 → **GPIO22/23/46/47** with J8 right-column pin references
- DHT11_DATA: J8 pin reference corrected from "pin 23" (GND) → **"left pin 15"** (GPIO16)
- STATUS_LED: J8 pin reference corrected from "left pin 3" (GND) → **"left pin 6"** (GPIO2)
- PROG_LED: J8 pin reference corrected from "right pin 22" (GND) → **"left pin 14"** (GPIO15)
- DS18B20_DATA: J8 pin reference corrected from "left pin 27" (GND) → **"left pin 19"** (GPIO19)
- PROBE_LED: GPIO corrected from GPIO20 (now FAN1_PWM) → **GPIO48** via J8 right pin 21
- Ethernet MAC/RMII: MDIO corrected from GPIO28 → **GPIO52** (ESP32-P4 Waveshare Kconfig confirmed; GPIO28 was ESP32-classic value)
- PHY_RST **GPIO51** added to Ethernet MAC row (previously absent)
- **I2C (SDA/SCL) reserved row removed** — GPIO21 now assigned to FAN2_PWM; GPIO22 now assigned to FAN1_TACH; I2C is no longer a candidate for these pins

---

## 5. J8 Signal-to-GPIO Map (Target State — post-amendment)

```
graph TB
    subgraph J8_Left ["J8 Left Column (x=2.81mm)"]
        P6["Pin 6 · GPIO2"]
        P14["Pin 14 · GPIO15"]
        P15["Pin 15 · GPIO16"]
        P19["Pin 19 · GPIO19"]
        PGND_L["Pins 3,8,13,18 · GND"]
    end

    subgraph J8_Right ["J8 Right Column (x=18.19mm)"]
        P21["Pin 21 · GPIO48"]
        P22["Pin 22 · GPIO47"]
        P24["Pin 24 · GPIO46"]
        P27["Pin 27 · GPIO27"]
        P29["Pin 29 · GPIO26"]
        P31["Pin 31 · GPIO23"]
        P32["Pin 32 · GPIO22"]
        P34["Pin 34 · GPIO21"]
        P35["Pin 35 · GPIO20"]
        P36["Pin 36 · 3V3"]
        P40["Pin 40 · VBUS/5V"]
        PGND_R["Pins 23,28,33,38 · GND"]
        PFBDN["Pins 25,26 · GPIO33/32 EMAC ⛔"]
    end

    P6  -->|STATUS_LED| LED1["R3 → LED1 (green)"]
    P14 -->|PROG_LED| LED2["R13 → LED2 (orange)"]
    P15 -->|DHT11_DATA| J9["J9 DHT11 connector"]
    P19 -->|DS18B20_DATA| J6["J6 + R14 4.7kΩ → probe"]

    P21 -->|PROBE_LED| LED6["R15 330Ω → LED6 (green)"]
    P22 -->|FAN4_TACH| J5T["J5 pin3 + R8 pull-up"]
    P24 -->|FAN3_TACH| J4T["J4 pin3 + R7 pull-up"]
    P27 -->|FAN4_PWM| J5P["J5 pin4"]
    P29 -->|FAN3_PWM| J4P["J4 pin4"]
    P31 -->|FAN2_TACH| J3T["J3 pin3 + R6 pull-up"]
    P32 -->|FAN1_TACH| J2T["J2 pin3 + R5 pull-up"]
    P34 -->|FAN2_PWM| J3P["J3 pin4"]
    P35 -->|FAN1_PWM| J2P["J2 pin4"]
    P36 -->|+3V3| PWR3V3["R5-R8 pull-ups · J9 VCC"]
    P40 -->|+5V| BOOST["U_BOOST 5V→12V"]
```

> Mermaid note: The `subgraph` wrapping allows the diagram to render in GitHub Markdown.
> Pins 25/26 (GPIO33/GPIO32) and 30 (RUN) are left as NC in the generator — correctly excluded.

---

## 6. PCB Impact Assessment

| Aspect | Impact |
|--------|--------|
| J8 footprint | **Unchanged** — same physical position, same pad coordinates; only pad net assignments change after "Update PCB from Schematic" |
| Fan traces | **All 8 fan signal traces must be rerouted.** Signals move from left column pads (x=2.81mm) to right column pads (x=18.19mm), which are physically closer to J2–J5 fan headers in the right zone (x>21mm). Net routing effort is reduced; trace lengths shorten by ~15mm per signal. |
| +3V3 routing | +3V3 source moves from pads 1/17 (left col, x=2.81mm) to pad 36 (right col, x=18.19mm). Pull-up resistors R5–R8 and J9 VCC must connect to pad 36 net instead. Expect airwires on R5–R8 pin 1 and J9 VCC after netlist sync. |
| Other signals | STATUS_LED, PROG_LED, DHT11_DATA, DS18B20_DATA GPIOs **unchanged** (GPIO2, 15, 16, 19) — only J8 pad numbers change. Existing traces from those left-column pads may become airwires requiring reroute. |

---

## 7. Testing Obligations (from plan §6, confirmed)

| Test | Blocking? | Description |
|------|-----------|-------------|
| T-01 | Pre-impl | Cross-check §2 pin table against authoritative board image before any file edit |
| T-02 | ✅ Merge-blocking | Zero ERC errors after `python hardware/generate_project.py` + `kicad-cli sch erc` |
| T-03 | Required | Net inspector spot-check per plan §6 T-03 table |
| T-04 | Required | Verify +3V3 net (pad 36) connects to R5–R8 pin 1 and J9 VCC |
| T-05 | ✅ Merge-blocking | Zero DRC errors after PCB netlist sync + re-routing |
| T-06 | Required | Confirm P-FW-02 table diff matches constitution v4.2.0 values |

---

## 8. Verdict

**APPROVED WITH CHANGES**

The plan is architecturally sound. All proposed GPIO assignments are validated as safe and
capable on the ESP32-P4-POE-ETH. The plan correctly avoids the EMAC-forbidden GPIO32/33
and substitutes appropriate alternatives. The generator-only implementation path satisfies
P-HW-05 and P-KI-04. Constitution amendment v4.2.0 has been applied to `docs/constitution.md`.

**Merge conditions:**
1. ERC must report **zero errors** (T-02) — blocking
2. DRC must report **zero errors** after PCB netlist sync and re-routing (T-05) — blocking
3. `erc_output.json` must be updated and committed alongside the schematic change
4. Firmware `platformio.ini` `build_flags` (FAN*_PIN, PROBE_LED_PIN) must be updated to
   new GPIO numbers in a follow-on firmware commit (tracked separately per spec §Out of Scope)
