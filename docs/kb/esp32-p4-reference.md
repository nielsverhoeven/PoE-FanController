# ESP32-P4 Reference

<!-- Last updated: 2026-06-07 | Source: esp32.expert consultation + architecture.md | GPIO2 corrected: feature/40-replace-esp32-with-esp32-p4 -->
<!-- Verified against: Espressif ESP32-P4 TRM, arduino-esp32 3.x docs -->

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

> ⚠️ OQ-01: Implementer MUST cross-verify against ESP32-P4 TRM §EMAC Table "EMAC Signal Overview" before schematic work.

| Signal | GPIO | Direction | Notes |
|---|---|---|---|
| EMAC_RXD0 | GPIO32 | Input | Fixed by IO_MUX |
| EMAC_RXD1 | GPIO33 | Input | Fixed by IO_MUX |
| EMAC_CRS_DV | GPIO34 | Input | Carrier Sense / Data Valid |
| EMAC_TXD0 | GPIO35 | Output | Fixed by IO_MUX |
| EMAC_TXD1 | GPIO36 | Output | Fixed by IO_MUX |
| EMAC_TX_EN | GPIO37 | Output | Fixed by IO_MUX |
| EMAC_REF_CLK | GPIO50 | Output | 50 MHz REF_CLK to PHY |
| EMAC_MDIO | GPIO28 | Bidirectional | Flexible (MDIO data) |
| EMAC_MDC | GPIO31 | Output | Flexible (MDIO clock) |

**Critical constraint:** GPIO32–37 and GPIO50 cannot be used for any other function.

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
| UART0_TX | GPIO38 | UART0 | To CH340C; IO_MUX default |
| UART0_RX | GPIO39 | UART0 | From CH340C; IO_MUX default |
| EMAC_MDIO | GPIO28 | EMAC | PHY management data |
| EMAC_MDC | GPIO31 | EMAC | PHY management clock |
| BOOT | GPIO0 | Strapping | Pull low to enter download mode |
| EN | EN pin | — | Module enable (active-high) |

**Forbidden GPIOs (RMII):** GPIO32–37, GPIO50 — reserved for EMAC, must not be reassigned.

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
  ; RMII config for ETH.h
  -DETH_PHY_TYPE=ETH_PHY_LAN8720
  -DETH_PHY_ADDR=0
  -DETH_PHY_MDC=31
  -DETH_PHY_MDIO=28
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
  ETH.begin(
    ETH_PHY_LAN8720,  // PHY type
    0,                 // PHY address (ADDR0/ADDR1 pins on LAN8720A)
    ETH_PHY_MDC,      // MDC pin (GPIO31)
    ETH_PHY_MDIO,     // MDIO pin (GPIO28)
    -1,                // PHY power pin (-1 = not used)
    ETH_CLOCK_GPIO50_OUT  // REF_CLK output from EMAC
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
