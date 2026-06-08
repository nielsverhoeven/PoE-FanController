/**
 * @file pins.h
 * @brief GPIO pin constants for PoE FanController v0.3 (Waveshare ESP32-P4-POE-ETH)
 *
 * MCU: ESP32-P4NRW32 on Waveshare ESP32-P4-POE-ETH board (SKU 32088)
 * Connected to custom carrier PCB via 2×20 HAT header (J8).
 *
 * GPIO4–11, GPIO16, GPIO2, GPIO15 are available on Waveshare's 2×20 header.
 * RMII fixed pins GPIO32–37 + GPIO50 are handled internally by Waveshare's LAN8720A.
 * MDC/MDIO/RST: GPIO31/GPIO52/GPIO51 — internal to Waveshare board (not on J8 header).
 * UART0: GPIO38 (TX), GPIO39 (RX) — via Waveshare's CH343P USB-C (not on J8 header).
 *
 * ETH PHY pin source: Waveshare official esp32-p4-platform Kconfig defaults
 *   github.com/waveshareteam/esp32-p4-platform — examples/esp-idf/11_ethernetbasic
 */
#pragma once

// ---------------------------------------------------------------------------
// Fan PWM outputs — LEDC (25 kHz, 8-bit resolution)
// arduino-esp32 3.x API: ledcAttach(pin, freq, bits) / ledcWrite(pin, duty)
// ---------------------------------------------------------------------------
#ifndef FAN1_PWM_PIN
#define FAN1_PWM_PIN  4   ///< GPIO4  LEDC CH0
#endif
#ifndef FAN2_PWM_PIN
#define FAN2_PWM_PIN  5   ///< GPIO5  LEDC CH1
#endif
#ifndef FAN3_PWM_PIN
#define FAN3_PWM_PIN  6   ///< GPIO6  LEDC CH2
#endif
#ifndef FAN4_PWM_PIN
#define FAN4_PWM_PIN  7   ///< GPIO7  LEDC CH3
#endif

// ---------------------------------------------------------------------------
// Fan tachometer inputs — GPIO interrupt (open-drain, pull-up required)
// ---------------------------------------------------------------------------
#ifndef FAN1_TACH_PIN
#define FAN1_TACH_PIN  8   ///< GPIO8
#endif
#ifndef FAN2_TACH_PIN
#define FAN2_TACH_PIN  9   ///< GPIO9
#endif
#ifndef FAN3_TACH_PIN
#define FAN3_TACH_PIN  10  ///< GPIO10
#endif
#ifndef FAN4_TACH_PIN
#define FAN4_TACH_PIN  11  ///< GPIO11
#endif

// ---------------------------------------------------------------------------
// Analog / temperature
// ---------------------------------------------------------------------------
#ifndef NTC_ADC_PIN
#define NTC_ADC_PIN   16  ///< GPIO16 ADC1 — NTC thermistor voltage divider
#endif

// ---------------------------------------------------------------------------
// Status / control
// ---------------------------------------------------------------------------
#ifndef STATUS_LED_PIN
#define STATUS_LED_PIN  2  ///< GPIO2  — green status LED via 330 Ω (R3 / LED1)
#endif
#ifndef PROG_LED_PIN
#define PROG_LED_PIN   15  ///< GPIO15 — orange OTA/prog LED via 330 Ω (R13 / LED2); J8 pin 22
#endif
#ifndef BOOT_PIN
#define BOOT_PIN        0  ///< GPIO0 — strapping / BOOT button
#endif

// ---------------------------------------------------------------------------
// Ethernet management (MDC/MDIO/RST — confirmed from Waveshare Kconfig defaults)
// Source: github.com/waveshareteam/esp32-p4-platform Kconfig.projbuild
// ---------------------------------------------------------------------------
#ifndef ETH_MDC_PIN
#define ETH_MDC_PIN   31  ///< GPIO31 EMAC_MDC  (SMI clock to LAN8720A)
#endif
#ifndef ETH_MDIO_PIN
#define ETH_MDIO_PIN  52  ///< GPIO52 EMAC_MDIO (SMI bidirectional data)
#endif
#ifndef ETH_PHY_RST_PIN
#define ETH_PHY_RST_PIN 51  ///< GPIO51 LAN8720A PHY reset (active-low)
#endif

// ---------------------------------------------------------------------------
// RMII fixed IO_MUX pins — DO NOT REASSIGN (ESP32-P4 TRM §EMAC)
// These are configured automatically by ETH.begin() — no #define needed for
// runtime use. Listed here for documentation and static analysis only.
// ---------------------------------------------------------------------------
// #define EMAC_RXD0_PIN     32   // Input  — fixed by IO_MUX
// #define EMAC_RXD1_PIN     33   // Input  — fixed by IO_MUX
// #define EMAC_CRS_DV_PIN   34   // Input  — fixed by IO_MUX
// #define EMAC_TXD0_PIN     35   // Output — fixed by IO_MUX
// #define EMAC_TXD1_PIN     36   // Output — fixed by IO_MUX
// #define EMAC_TX_EN_PIN    37   // Output — fixed by IO_MUX
// #define EMAC_REF_CLK_PIN  50   // Output — 50 MHz to LAN8720A REFCLK

// ---------------------------------------------------------------------------
// DS18B20 external temperature probe — 1-Wire bus + status LED
// ---------------------------------------------------------------------------
#ifndef DS18B20_DATA_PIN
#define DS18B20_DATA_PIN  19  ///< GPIO19 — 1-Wire DATA, J8 left pin 27; 4.7kΩ pull-up R14 on PCB
#endif
#ifndef PROBE_LED_PIN
#define PROBE_LED_PIN     20  ///< GPIO20 — Status_LED_5 (probe health), J8 right pin 28; 330Ω series R15
#endif

// ---------------------------------------------------------------------------
// Fan PWM parameters
// ---------------------------------------------------------------------------
#define FAN_PWM_FREQ_HZ    25000  ///< 25 kHz (P-FW-03)
#define FAN_PWM_RESOLUTION     8  ///< 8-bit (0–255)
#define FAN_PWM_SAFE_DEFAULT 255  ///< 100% on boot until config loaded (P-FW-05)

// ---------------------------------------------------------------------------
// NTC thermistor (Steinhart-Hart)
// ---------------------------------------------------------------------------
#define NTC_SERIES_OHM   10000   ///< R4 = 10 kΩ pull-up
#define NTC_NOMINAL_OHM  10000   ///< NTC1 nominal resistance at 25 °C
#define NTC_BETA         3950    ///< B-constant (NCP15XH103F03RC)
#define NTC_NOMINAL_TEMP 25.0f   ///< °C nominal temperature
