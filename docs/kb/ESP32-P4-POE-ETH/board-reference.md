# ESP32-P4-POE-ETH Board Reference

<!-- Last updated: 2026-06-08 -->
<!-- Sources:
  - https://docs.waveshare.com/ESP32-P4-ETH (hardware description + SKU table)
  - https://github.com/waveshareteam/esp32-p4-platform (official Waveshare firmware examples)
  - https://github.com/waveshareteam/esp32-p4-platform/blob/main/examples/esp-idf/11_ethernetbasic/components/ethernet_init/Kconfig.projbuild
  - docs/kb/ESP32-P4-POE-ETH/ local files (datasheet PDFs)
-->

---

## 1. Product Identity

| Field | Value | Confidence |
|---|---|---|
| Product name | ESP32-P4-POE-ETH | 🟢 HIGH |
| SKU | **32088** | 🟢 HIGH — confirmed from docs.waveshare.com SKU table |
| SoC module | ESP32-P4NRW32 | 🟢 HIGH — confirmed from docs page hardware description |
| Flash | 32 MB Nor Flash | 🟢 HIGH |
| PSRAM | 32 MB (stacked in package) | 🟢 HIGH |
| Ethernet PHY | LAN8720A (100 Mbit RMII) | 🟢 HIGH |
| RJ45 | Single port — carries **both** PoE power + Ethernet data | 🟢 HIGH |
| USB-C | Type-C for power, programming, and debugging | 🟢 HIGH |
| BOOT/RST buttons | On-board | 🟢 HIGH |
| GPIO header | 2×20 (40 pins), 2.54 mm pitch, Raspberry Pi layout | 🟢 HIGH |
| Exposed GPIOs | **27 programmable GPIOs** on header (13 pins are power/GND) | 🟢 HIGH |
| TF card | SDIO 3.0 interface | 🟢 HIGH |
| Audio | SMD microphone + MX1.25 2P speaker connector | 🟢 HIGH |
| Camera | MIPI-CSI (2-lane), OV5647 compatible | 🟢 HIGH |
| Display | MIPI-DSI (2-lane), 5/7/8/10.1" screens | 🟢 HIGH |
| USB OTG | USB OTG 2.0 High Speed (4-pin connector) | 🟢 HIGH |

### SKU variants (same base board, different bundles)

| SKU | Variant | Notes |
|---|---|---|
| 32086 | ESP32-P4-ETH | **No PoE** — plain Ethernet only |
| 32087 | ESP32-P4-ETH-M | No PoE, M variant |
| **32088** | **ESP32-P4-POE-ETH** | **Our target** — onboard PoE module |
| 34247 | ESP32-P4-POE-ETH-NH | No header variant |
| 32089 | ESP32-P4-POE-ETH-KIT-A | Kit A (with accessories) |
| 32090 | ESP32-P4-POE-ETH-KIT-B | Kit B (with accessories) |

> ⚠️ **SKU 32086 vs 32088:** The project previously used SKU 32086 (no PoE). Issue #75 migrates
> to SKU 32088 (onboard PoE). Do not confuse them — only 32088 has the onboard PoE module.

---

## 2. EMAC / Ethernet PHY Pin Assignments

> 🟢 **HIGH CONFIDENCE** — extracted from official Waveshare ESP32-P4 platform examples
> Source: `Kconfig.projbuild` defaults in `examples/esp-idf/11_ethernetbasic/`
> GitHub: https://github.com/waveshareteam/esp32-p4-platform/blob/main/examples/esp-idf/11_ethernetbasic/components/ethernet_init/Kconfig.projbuild

| Signal | GPIO | Notes |
|---|---|---|
| EMAC_MDC | **GPIO31** | SMI clock — confirmed from Kconfig `default 31 if IDF_TARGET_ESP32P4` |
| EMAC_MDIO | **GPIO52** | SMI data — confirmed from Kconfig `default 52 if IDF_TARGET_ESP32P4` |
| PHY_RST | **GPIO51** | LAN8720A reset — confirmed from Kconfig `default 51 if IDF_TARGET_ESP32P4` |
| EMAC_RXD0 | GPIO32 | Fixed by IO_MUX — cannot be remapped |
| EMAC_RXD1 | GPIO33 | Fixed by IO_MUX — cannot be remapped |
| EMAC_CRS_DV | GPIO34 | Fixed by IO_MUX — cannot be remapped |
| EMAC_TXD0 | GPIO35 | Fixed by IO_MUX — cannot be remapped |
| EMAC_TXD1 | GPIO36 | Fixed by IO_MUX — cannot be remapped |
| EMAC_TX_EN | GPIO37 | Fixed by IO_MUX — cannot be remapped |
| EMAC_REF_CLK | GPIO50 | 50 MHz ref clock output from EMAC |

> ⚠️ **CRITICAL CORRECTION vs previous KB:** `esp32-p4-reference.md` incorrectly listed
> EMAC_MDIO as GPIO28. The correct value for Waveshare ESP32-P4 boards is **GPIO52**.
> GPIO28 is ETH_MDIO on the ESP32 classic (not ESP32-P4). Source: official Waveshare Kconfig.

**Forbidden GPIOs** (reserved for EMAC — cannot be used for fan/NTC/LED):
GPIO31, GPIO32–37, GPIO50, GPIO51, GPIO52

---

## 3. Board Dimensions

> 🟢 **HIGH CONFIDENCE** — confirmed from dimension drawing in `ESP32-P4-ETH-details-size-*.webp`

| Measurement | Value | Confidence |
|---|---|---|
| Length | **78.00 mm** | 🟢 HIGH — measured from dimension drawing |
| Width | **21.00 mm** | 🟢 HIGH — measured from dimension drawing |
| Pin pitch (within row) | **2.54 mm** | 🟢 HIGH — shown in dimension drawing |
| Edge-to-pin distance | **2.81 mm** from each long edge | 🟢 HIGH — shown in dimension drawing |
| **Row-to-row spacing** | **15.38 mm** (= 21.00 − 2×2.81) | 🟢 HIGH — calculated from confirmed edge distance |
| Row 1 centre (odd pins) | 2.81 mm from one long edge | 🟢 HIGH |
| Row 2 centre (even pins) | 18.19 mm from same long edge (= 2.81 mm from other edge) | 🟢 HIGH |
| First pin offset | **4.67 mm** from right short edge (in landscape orientation) | 🟢 HIGH — shown in dimension drawing |
| Mounting holes | 4× M2.5, Raspberry Pi HAT pattern | 🟡 MEDIUM |

> ⚠️ **Row spacing is 15.38 mm, NOT 2.81 mm.**
> The 2.81 mm dimension in the drawing is the **edge-to-pin-centre distance** (how far each row is from the board edge).
> The two rows are on OPPOSITE long edges: row 1 at 2.81 mm, row 2 at 21.00−2.81 = 18.19 mm from the same edge.
> Row-to-row pitch = 18.19 − 2.81 = **15.38 mm**.
> The KiCad footprint `PinSocket_2x20_P2.54mm_Vertical` AND `PinSocket_2x20_P2.54mm_P2.81mm_Vertical` are BOTH WRONG.
> Use: `Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical`
> (stored in `hardware/kicad/footprints/Custom.pretty/`)

**Daughter board implication (portrait layout — per `docs/kb/Sample-PCB-Sketch.png`):**
- Daughter board length (Y) = ESP32-P4-POE-ETH length = **≤78.00 mm** (board may not be longer)
- Daughter board width (X) ≥ **42.00 mm** (= 2× ESP32 width of 21 mm)
- ESP32-P4-POE-ETH occupies the **left column** (x = 0–21 mm), full height
- Fan headers (J2–J5) are in the **right column** (x > 21 mm), stacked vertically
- J8 connector spans Y = 4.67 mm to Y = 52.93 mm (20 pins × 2.54 mm = 48.26 mm span)

---

## 4. GPIO Header Pinout

> 🟡 **MEDIUM CONFIDENCE** — pinout table is an image on the docs page (not extractable as
> text). Table below compiled from: docs page description + ESP32-P4 TRM + Waveshare examples.
> **Verify against the schematic PDF in this folder before firmware commit.**

The header is 2×20 (40 pins), Raspberry Pi HAT layout:
- Odd pins (1,3,5,...,39): left column
- Even pins (2,4,6,...,40): right column
- Pin 1: top-left

### 4.1 Power pins (confirmed functional, positions TBC from schematic)

| Pin(s) | Signal | Voltage | Current limit | Confidence |
|---|---|---|---|---|
| 1, 17 | +3.3V | 3.3V | ~800 mA total (shared with board) | 🟡 MEDIUM |
| 2, 4 | **+5V** | **5V** | From PoE module — ~2–3A (TBC) | 🟡 MEDIUM |
| 6, 9, 14, 20, 25, 30, 34, 39 | GND | 0V | — | 🟢 HIGH (RPi standard) |

> ⚠️ **BLOCKING verification required:** Confirm exact +5V current available on header pins 2/4
> from the onboard PoE module. The daughter board U_BOOST (5V→12V) draws up to ~2A from these pins.
> Check schematic PDF `ESP32-P4-ETH-datasheet.pdf` in this folder.

### 4.2 GPIO signal assignments used by this project

| Physical Pin | GPIO | This project's use | Internal use on board | Confidence |
|---|---|---|---|---|
| 3 | GPIO2 | STATUS_LED | Possibly onboard LED — verify | 🟡 MEDIUM |
| 7 | GPIO4 | FAN1_PWM (LEDC CH0) | Free | 🟡 MEDIUM |
| 8 | GPIO5 | FAN2_PWM (LEDC CH1) | Free | 🟡 MEDIUM |
| 10 | GPIO6 | FAN3_PWM (LEDC CH2) | Free | 🟡 MEDIUM |
| 11 | GPIO7 | FAN4_PWM (LEDC CH3) | Free | 🟡 MEDIUM |
| 12 | GPIO8 | FAN1_TACH (GPIO IRQ) | Free | 🟡 MEDIUM |
| 13 | GPIO9 | FAN2_TACH (GPIO IRQ) | Free | 🟡 MEDIUM |
| 15 | GPIO10 | FAN3_TACH (GPIO IRQ) | Free | 🟡 MEDIUM |
| 16 | GPIO11 | FAN4_TACH (GPIO IRQ) | Free | 🟡 MEDIUM |
| 23 | GPIO16 | NTC_ADC (SAR ADC) | Free | 🟡 MEDIUM |

### 4.3 GPIOs NOT available on header (reserved internally)

| GPIO | Used for | Cannot be reassigned |
|---|---|---|
| GPIO28 | — | Listed in older docs as MDIO but **NOT confirmed for P4** |
| GPIO31 | EMAC_MDC | Fixed — internal PHY management |
| GPIO32 | EMAC_RXD0 | Fixed by IO_MUX |
| GPIO33 | EMAC_RXD1 | Fixed by IO_MUX |
| GPIO34 | EMAC_CRS_DV | Fixed by IO_MUX |
| GPIO35 | EMAC_TXD0 | Fixed by IO_MUX |
| GPIO36 | EMAC_TXD1 | Fixed by IO_MUX |
| GPIO37 | EMAC_TX_EN | Fixed by IO_MUX |
| GPIO38 | UART0_TX (USB-C debug) | Avoid |
| GPIO39 | UART0_RX (USB-C debug) | Avoid |
| GPIO50 | EMAC_REF_CLK (50 MHz) | Fixed |
| GPIO51 | LAN8720A PHY_RST | Internal |
| GPIO52 | EMAC_MDIO | Fixed — confirmed from Waveshare Kconfig |

---

## 5. PoE Specification

> 🟡 **MEDIUM CONFIDENCE** — from docs page description + power budget analysis.

| Parameter | Value | Confidence |
|---|---|---|
| PoE input standard | 802.3af/at (PD device) | 🟢 HIGH |
| PD class | Likely Class 4 (802.3at, 25.5W budget) | 🟡 MEDIUM — verify from schematic |
| PoE module output to header | **+5V** (most likely) | 🟡 MEDIUM — **must verify from schematic** |
| Board self-consumption | ~3–5W (ESP32-P4 + LAN8720A + PoE module overhead) | 🟡 MEDIUM |

### Power budget for daughter board (802.3at scenario)

| Item | Power |
|---|---|
| PSE total available | 25.5W |
| Cable loss (~10%) | −2.5W |
| PD module received | ~23W |
| Board self (ESP32-P4, PHY, regulators) | −3.5W |
| Available on +5V header rail | ~19.5W → **~3.9A at 5V** |
| U_BOOST efficiency (85%) | − |
| Available at +12V for fans | **~16.6W → ~1.38A at 12V** |
| 4 fans at 3W each | 12W |
| **Margin** | **4.6W** ✅ |

> ⚠️ **This budget is feasible ONLY with 802.3at (Class 4) PSE.**
> 802.3af-only PSE (12.95W total) cannot power 4 fans simultaneously.

---

## 6. Firmware Configuration (ESP-IDF)

Verified pin assignments from official Waveshare example defaults:

```c
// ETH PHY (LAN8720A via RMII)
#define ETH_PHY_TYPE        ETH_PHY_LAN8720
#define ETH_PHY_ADDR        1        // verify PHY address from schematic
#define ETH_MDC_GPIO        31       // confirmed from Waveshare Kconfig
#define ETH_MDIO_GPIO       52       // confirmed from Waveshare Kconfig (NOT 28!)
#define ETH_PHY_RST_GPIO    51       // confirmed from Waveshare Kconfig
#define ETH_CLK_MODE        ETH_CLOCK_GPIO50_OUT  // 50MHz REF_CLK from EMAC

// Fan control (daughter board — via J8 header)
#define FAN1_PWM_PIN    4
#define FAN2_PWM_PIN    5
#define FAN3_PWM_PIN    6
#define FAN4_PWM_PIN    7
#define FAN1_TACH_PIN   8
#define FAN2_TACH_PIN   9
#define FAN3_TACH_PIN   10
#define FAN4_TACH_PIN   11
#define NTC_ADC_PIN     16
#define STATUS_LED_PIN  2
```

### PlatformIO platformio.ini

```ini
[env:esp32-p4-poe-eth]
platform  = espressif32 @ >=6.9.0
board     = esp32-p4-poe-eth       ; custom manifest in firmware/boards/
board_dir = boards
framework = arduino

platform_packages =
  framework-arduinoespressif32 @ https://github.com/espressif/arduino-esp32.git#3.1.0

build_flags =
  -DARDUINO_USB_MODE=1
  -DBOARD_HAS_PSRAM
  ; EMAC — corrected from esp32-p4-reference.md
  -DETH_PHY_TYPE=ETH_PHY_LAN8720
  -DETH_PHY_ADDR=1
  -DETH_PHY_MDC=31
  -DETH_PHY_MDIO=52
  -DETH_PHY_RST=51
  -DETH_CLK_MODE=ETH_CLOCK_GPIO50_OUT
  ; Fan/NTC/LED on daughter board
  -DFAN1_PWM_PIN=4  -DFAN2_PWM_PIN=5  -DFAN3_PWM_PIN=6  -DFAN4_PWM_PIN=7
  -DFAN1_TACH_PIN=8 -DFAN2_TACH_PIN=9 -DFAN3_TACH_PIN=10 -DFAN4_TACH_PIN=11
  -DNTC_ADC_PIN=16
  -DSTATUS_LED_PIN=2
```

---

## 7. Development Toolchain

| Tool | Recommendation |
|---|---|
| Primary SDK | **ESP-IDF release/v5.4+** (official Waveshare recommendation) |
| Arduino | Limited support for ESP32-P4; use ESP-IDF for production |
| Official examples repo | https://github.com/waveshareteam/esp32-p4-platform |
| Arduino-ESP32 core | ≥ 3.1.0 required for ESP32-P4 Ethernet support |

---

## 8. Open Questions (Pending Verification)

| ID | Question | Blocking? | How to resolve |
|---|---|---|---|
| OQ-01 | ~~Exact board dimensions L × W mm~~ | ✅ RESOLVED: 78.00 × 21.00 mm | From dimension drawing |
| OQ-02 | Exact voltage and max current on header pins 2,4 (+5V?) | ✅ Yes (U_BOOST sizing) | Open schematic PDF in this folder |
| OQ-03 | PHY address (ADDR0/1 pins on LAN8720A) | Yes (firmware) | Open schematic PDF |
| OQ-04 | GPIO physical pin positions on 40-pin header (verify pin 3=GPIO2, etc.) | Yes (schematic) | Open pinout image from wiki or schematic PDF |
| OQ-05 | Whether GPIO2 drives onboard LED (conflict with STATUS_LED use) | Yes | Check schematic |
| OQ-06 | PoE PD class (af=Class 0-3, at=Class 4) | Yes (power budget) | Check schematic or PoE module datasheet |

---

## 9. Key Differences vs SKU 32086 (ESP32-P4-ETH, no PoE)

| Feature | SKU 32086 (old) | SKU 32088 (our target) |
|---|---|---|
| PoE | None (ext. power only) | Onboard PoE PD module |
| Cables needed | 1× power + 1× Ethernet | **1× PoE Ethernet** |
| Daughter board needs | Own J1 RJ45 + Ag9905M | **None** — PoE handled |
| Isolation barrier | On daughter/carrier board | Inside Waveshare board |
| Header +5V source | External regulator | Onboard PoE PD module |
| Fan power path | +5V header → U_BOOST → 12V | Same (U_BOOST still needed) |

---

## 10. Local Files in This Folder

| File | Contents |
|---|---|
| `esp32-p4_datasheet_en.pdf` | ESP32-P4 SoC datasheet (GPIO matrix, ADC specs, EMAC) |
| `esp32-p4_technical_reference_manual_en.pdf` | ESP32-P4 TRM (EMAC RMII fixed pins §EMAC) |
| `ESP32-P4-ETH-datasheet.pdf` | Waveshare board schematic/datasheet — **check for pin voltages** |
| `ESP32-P4-ETH-details-size-*.webp` | Board dimension drawing — **check for exact L×W mm** |
