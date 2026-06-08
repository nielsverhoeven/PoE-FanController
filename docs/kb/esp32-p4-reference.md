# ESP32-P4 Reference

<!-- Last updated: 2026-06-08 | Source: esp32.expert consultation + architecture.md | GPIO2 corrected: feature/40-replace-esp32-with-esp32-p4 -->
<!-- Verified against: Espressif ESP32-P4 TRM, arduino-esp32 3.x docs, Waveshare official examples repo (SKU 32088 EMAC pins corrected 2026-06-08) -->
<!-- IMPORTANT: For full board-specific reference including dimensions, pinout, and PoE specs see docs/kb/ESP32-P4-POE-ETH/board-reference.md -->

---

## 1. Module Selection

| Field | Value |
|---|---|
| MPN | `ESP32-P4-MINI-1U-N16R8` |
| Package | LGA-56 castellation (module) |
| Core | Dual-core RISC-V HP (up to 400 MHz) + LP core |
| Flash | 16 MB (internal) |
| PSRAM | 8 MB |
| WiFi | **NONE** (by design — wired Ethernet only) |
| Bluetooth | **NONE** |
| Ethernet MAC | Built-in EMAC; requires external PHY |
| USB | Native USB OTG (deferred to future amendment; CH340C retained for v0.2) |

---

## 2. RMII Fixed Pin Assignments (VERIFIED — cannot be remapped)

> ⚠️ Verified from official Waveshare ESP32-P4 platform examples Kconfig.
> Source: https://github.com/waveshareteam/esp32-p4-platform/blob/main/examples/esp-idf/11_ethernetbasic/components/ethernet_init/Kconfig.projbuild

| Signal | GPIO | Direction | Notes |
|---|---|---|---|
| EMAC_RXD0 | GPIO32 | Input | Fixed by IO_MUX |
| EMAC_RXD1 | GPIO33 | Input | Fixed by IO_MUX |
| EMAC_CRS_DV | GPIO34 | Input | Carrier Sense / Data Valid |
| EMAC_TXD0 | GPIO35 | Output | Fixed by IO_MUX |
| EMAC_TXD1 | GPIO36 | Output | Fixed by IO_MUX |
| EMAC_TX_EN | GPIO37 | Output | Fixed by IO_MUX |
| EMAC_REF_CLK | GPIO50 | Output | 50 MHz REF_CLK to PHY |
| EMAC_MDIO | **GPIO52** | Bidirectional | **Corrected 2026-06-08** — was GPIO28 (ESP32 classic value, incorrect for P4) |
| EMAC_MDC | GPIO31 | Output | Confirmed from Waveshare Kconfig |
| PHY_RST | GPIO51 | Output | LAN8720A reset — confirmed from Waveshare Kconfig |

**Critical constraint:** GPIO31, GPIO32–37, GPIO50, GPIO51, GPIO52 cannot be used for any other function.

---

## 3. GPIO Allocation (Conflict-Validated)

| Signal | GPIO | Peripheral | Notes |
|---|---|---|---|
| FAN1_PWM | GPIO4 | LEDC | PWM output |
| FAN2_PWM | GPIO5 | LEDC | PWM output |
| FAN3_PWM | GPIO6 | LEDC | PWM output |
| FAN4_PWM | GPIO7 | LEDC | PWM output |
| FAN1_TACH | GPIO8 | GPIO interrupt | Tach input |
| FAN2_TACH | GPIO9 | GPIO interrupt | Tach input |
| FAN3_TACH | GPIO10 | GPIO interrupt | Tach input |
| FAN4_TACH | GPIO11 | GPIO interrupt | Tach input |
| NTC_ADC | GPIO16 | ADC | NTC thermistor (Steinhart-Hart) |
| STATUS_LED | GPIO2 | Output | Status LED via R3 330 Ω (active HIGH) |
| DS18B20_DATA | GPIO19 | 1-Wire | External temperature probe DATA line (4.7 kΩ pull-up to 3.3 V on daughter board) |
| PROBE_LED | GPIO20 | Output | Status_LED_5 — probe connector status LED (off=absent, blink=reading, solid=valid) |
| UART0_TX | GPIO38 | UART0 | To CH340C; IO_MUX default |
| UART0_RX | GPIO39 | UART0 | From CH340C; IO_MUX default |
| EMAC_MDIO | GPIO52 | EMAC | PHY management data — **corrected from GPIO28** |
| EMAC_MDC | GPIO31 | EMAC | PHY management clock |
| PHY_RST | GPIO51 | Output | LAN8720A hardware reset |
| BOOT | GPIO0 | Strapping | Pull low to enter download mode |
| EN | EN pin | — | Module enable (active-high) |

**Forbidden GPIOs (RMII + ETH management):** GPIO31, GPIO32–37, GPIO50, GPIO51, GPIO52 — reserved for EMAC, must not be reassigned.

> **Note on per-fan indicator LEDs (D2–D5):** The per-fan power LEDs are passive, +12V-rail-driven
> (R→LED→GND, no GPIO). Only Status_LED_5 (probe) is firmware-driven via GPIO20.

---

## 4. PlatformIO Configuration

```ini
[env:esp32-p4]
platform = espressif32 @ >=6.9.0
board     = esp32-p4-mini-1u    ; custom manifest in firmware/boards/
board_dir = boards
framework = arduino

; arduino-esp32 ≥ 3.1.0 required for ESP32-P4 + ETH.h support
platform_packages =
  framework-arduinoespressif32 @ https://github.com/espressif/arduino-esp32.git#3.1.0

build_flags =
  -DARDUINO_USB_MODE=1
  -DBOARD_HAS_PSRAM
  ; GPIO pin assignments
  -DFAN1_PWM_PIN=4
  -DFAN2_PWM_PIN=5
  -DFAN3_PWM_PIN=6
  -DFAN4_PWM_PIN=7
  -DFAN1_TACH_PIN=8
  -DFAN2_TACH_PIN=9
  -DFAN3_TACH_PIN=10
  -DFAN4_TACH_PIN=11
  -DNTC_ADC_PIN=16
  -DSTATUS_LED_PIN=2
  -DDS18B20_DATA_PIN=19
  -DPROBE_LED_PIN=20
  ; RMII config for ETH.h — corrected MDIO=52, added PHY_RST=51
  -DETH_PHY_TYPE=ETH_PHY_LAN8720
  -DETH_PHY_ADDR=1
  -DETH_PHY_MDC=31
  -DETH_PHY_MDIO=52
  -DETH_PHY_RST=51
  -DETH_CLK_MODE=ETH_CLOCK_GPIO50_OUT
```

> **OQ-04 resolved (feature/40):** Custom board manifest `firmware/boards/esp32-p4-mini-1u.json`
> was created for the 16 MB flash variant (N16R8). `esp32-p4-function-ev-board` is the upstream
> base; the custom manifest overrides `flash_size` to 16 MB and `connectivity` to `["ethernet"]`.

---

## 5. ETH.h Initialization (arduino-esp32 ≥ 3.x)

```cpp
#include <ETH.h>

void setup() {
  // LAN8720A on RMII with REF_CLK output from GPIO50
  // Pin assignments verified from Waveshare esp32-p4-platform Kconfig (2026-06-08)
  ETH.begin(
    ETH_PHY_LAN8720,        // PHY type
    1,                       // PHY address (verify from schematic)
    31,                      // MDC pin (GPIO31)
    52,                      // MDIO pin (GPIO52 — NOT GPIO28)
    51,                      // PHY reset pin (GPIO51)
    ETH_CLOCK_GPIO50_OUT    // REF_CLK output from EMAC
  );
}
```

---

## 6. HTTP OTA (replaces ArduinoOTA WiFi)

```cpp
// POST /api/v1/ota with firmware binary
server.on("/api/v1/ota", HTTP_POST,
  [](AsyncWebServerRequest *request) {
    request->send(Update.hasError() ? 500 : 200);
    if (!Update.hasError()) ESP.restart();
  },
  [](AsyncWebServerRequest *request, String filename,
     size_t index, uint8_t *data, size_t len, bool final) {
    if (!index) Update.begin(UPDATE_SIZE_UNKNOWN);
    Update.write(data, len);
    if (final) Update.end(true);
  }
);
```

---

## 7. LEDC API Changes (arduino-esp32 3.x)

arduino-esp32 3.x changed the LEDC API:
```cpp
// OLD (2.x):
ledcSetup(channel, freq, resolution);
ledcAttachPin(pin, channel);
ledcWrite(channel, duty);

// NEW (3.x):
ledcAttach(pin, freq, resolution);  // pin IS the channel reference
ledcWrite(pin, duty);
ledcDetach(pin);
```

---

## 8. ESPAsyncWebServer on ESP32-P4

Use the maintained fork — original repo is unmaintained for IDF 5.x:
- `mathieucarbou/ESPAsyncWebServer` (ESP32-P4 + IDF 5.x compatible)
- `mathieucarbou/AsyncTCP` ≥ 3.x (IDF 5.x fork)

> ⚠️ OQ-05: Compatibility under arduino-esp32 3.x on ESP32-P4 must be tested by implementer.

---

## 9. Waveshare ESP32-P4-POE-ETH (SKU 32088) Board Specs

> ⚠️ **Confidence level:** MEDIUM — compiled from training-data corpus; live wiki verification required before PCB commitment.
> Live URL to verify: https://www.waveshare.com/wiki/ESP32-P4-POE-ETH → Resources tab → Schematic PDF

> **CRITICAL DISTINCTION:** SKU 32088 (ESP32-P4-**POE**-ETH) is different from SKU 32086 (ESP32-P4-ETH, no onboard PoE).
> The v2.0.0 carrier board was designed for SKU 32086. Issue #75 redesigns for SKU 32088.

### 9.1 Board Identity

| Field | Value | Confidence |
|---|---|---|
| SKU / Model | ESP32-P4-POE-ETH (SKU 32088) | 🟢 HIGH |
| SoC module | ESP32-P4NRW32 (same as SKU 32086) | 🟢 HIGH |
| Flash | 32 MB | 🟢 HIGH |
| PSRAM | 32 MB | 🟢 HIGH |
| Ethernet PHY | LAN8720A (same as SKU 32086) | 🟢 HIGH |
| RJ45 | Integrated — carries **both** PoE power + Ethernet data | 🟢 HIGH |
| USB-C | Yes — for firmware flash/debug; fallback power when no PoE | 🟢 HIGH |
| BOOT/RST buttons | On-board | 🟢 HIGH |
| GPIO header | 2×20 (40 pins), 2.54 mm pitch, PICO-2×20 layout | 🟢 HIGH |

### 9.2 Board Dimensions (MUST VERIFY)

| Measurement | Value | Confidence | Verification action |
|---|---|---|---|
| Length (L) | **≈ 85.6 mm** | 🟡 MEDIUM | Check wiki "Dimensions" section |
| Width (W) | **≈ 56 mm** | 🟡 MEDIUM | Check wiki "Dimensions" section |
| Mounting holes | 4× M2.5 | 🟡 MEDIUM | Check mechanical drawing |

**Daughter board implication:** Daughter board matches SKU 32088 in LENGTH; wider in WIDTH to place fan headers on the side edge (exact width TBD from architecture decision).

### 9.3 Header Voltage — CRITICAL DESIGN DECISION

| Pin(s) | Signal | Voltage | Notes |
|---|---|---|---|
| 1, 17 | 3.3V | 3.3V | From onboard LDO; safe for pull-ups and NTC divider |
| **39** | **5V (VSYS)** | **5V** | PoE module output — main 5V rail — confirmed from schematic |
| **40** | **5V (VBUS)** | **5V** | USB 5V — confirmed from schematic |
| 6, 9, 14, 20, 25, 30, 34, 38 | GND | 0V | Secondary common GND |
| All others | GPIO (3.3V logic) | 3.3V | ESP32-P4 GPIO signals |

> ✅ **Verified:** +5V is on header pins 39 (VSYS) and 40 (VBUS), confirmed from Waveshare
> schematic Interface section. **Pins 2 and 4 are NOT power pins on this board.**
> Daughter board boost converter must source from pin 39 (VSYS).

### 9.4 Header Pinout — GPIO Assignments (Unverified)

> 🔴 LOW CONFIDENCE — GPIO-to-physical-pin mapping reconstructed from ESP32-P4 constraints.
> **Verify against Waveshare pinout diagram before firmware work.**

| Physical Pin | GPIO | Function in This Project | Notes |
|---|---|---|---|
| 3 | GPIO2 | STATUS_LED | Common for Waveshare onboard LED |
| 7 | GPIO4 | FAN1_PWM | LEDC CH0 |
| 8 | GPIO5 | FAN2_PWM | LEDC CH1 |
| 10 | GPIO6 | FAN3_PWM | LEDC CH2 |
| 11 | GPIO7 | FAN4_PWM | LEDC CH3 |
| 12 | GPIO8 | FAN1_TACH | GPIO interrupt |
| 13 | GPIO9 | FAN2_TACH | GPIO interrupt |
| 15 | GPIO10 | FAN3_TACH | GPIO interrupt |
| 16 | GPIO11 | FAN4_TACH | GPIO interrupt |
| 23 | GPIO16 | NTC_ADC | SAR ADC |

**Definitively NOT on header** (internal, EMAC/UART fixed):
GPIO28 (EMAC_MDIO), GPIO31 (EMAC_MDC), GPIO32–37 (RMII), GPIO38 (UART TX), GPIO39 (UART RX), GPIO50 (REF_CLK).

### 9.5 Power Available on 5V Header Rail (Analysis)

| Scenario | PD available | Board self-use | Net on header | At 12V after 85% boost | Fan budget (≤12W) |
|---|---|---|---|---|---|
| 802.3af (Class 3) | 12.95 W | ~3.5 W | ~9.45 W → ~7.1W (5V rail) | ~6.0 W | ❌ Insufficient |
| **802.3at (Class 4)** | **25.5 W** | **~3.5 W** | **~22 W → ~16.4W (5V rail)** | **~13.9 W** | **✅ Feasible (1.9W margin)** |

> ⚠️ **The daughter board 12V fan design is ONLY feasible with 802.3at PSE.**
> The PSE (PoE switch) MUST be 802.3at Class 4. 802.3af-only switches will not work.
> Verify SKU 32088's onboard PD module supports 802.3at Class 4 (from wiki/schematic).

### 9.6 Key Differences vs SKU 32086

| Attribute | SKU 32086 (v2.0.0 current) | SKU 32088 (Issue #75 target) |
|---|---|---|
| PoE power | **Carrier board** Ag9905M | **Onboard** PD module |
| RJ45 cables needed | **2** (power + data separate) | **1** (combined PoE + data) |
| Header pins 2/4 | 5V (from carrier LM2596) | 5V (from onboard PD, likely) |
| 12V rail for fans | On carrier board | **Not on header** → needs boost converter on daughter board |
| Fan power available | 20W (Ag9905M 1.67A × 12V) | ~13.9W (after boost, 802.3at only) |
| Isolation location | Carrier PCB (Ag9905M) | Inside Waveshare board |
