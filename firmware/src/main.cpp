/**
 * @file main.cpp
 * @brief PoE FanController v0.3 — Waveshare ESP32-P4-POE-ETH HAT carrier board.
 *
 * Network: wired 100BASE-T via LAN8720A built into Waveshare board (SKU 32088).
 * Serial:  via Waveshare's CH343P USB bridge (USB-C on Waveshare board).
 * OTA:     HTTP POST /api/v1/ota (see ota.cpp).
 *
 * Startup sequence (P-FW-05 safe-boot):
 *   1. Set all fans to 100 % duty (FAN_PWM_SAFE_DEFAULT).
 *   2. Start Ethernet (ETH.begin — LAN8720A on Waveshare board).
 *   3. Wait for IP via ARDUINO_EVENT_ETH_GOT_IP.
 *   4. Load config from NVS; apply fan curves.
 *   5. Start web server.
 *
 * ETH PHY pins (confirmed from Waveshare Kconfig defaults):
 *   MDC=GPIO31, MDIO=GPIO52, RST=GPIO51, RMII fixed GPIO32-37+50.
 */

#include <Arduino.h>
#include <ETH.h>
#include <Update.h>
#include "pins.h"

// Forward declarations — defined in their respective modules
void fan_init();
void temp_init();
void probe_init();
void web_init();
void ota_init();
void ota_register(void* server);

// ---------------------------------------------------------------------------
// Ethernet event handler
// ---------------------------------------------------------------------------
static void on_eth_event(arduino_event_id_t event, arduino_event_info_t info)
{
    switch (event) {
    case ARDUINO_EVENT_ETH_START:
        Serial.println("[ETH] Started");
        ETH.setHostname("poe-fanctrl");
        break;
    case ARDUINO_EVENT_ETH_CONNECTED:
        Serial.println("[ETH] Link UP");
        break;
    case ARDUINO_EVENT_ETH_GOT_IP:
        Serial.printf("[ETH] IP: %s  speed: %u Mbps  %s-duplex\n",
                      ETH.localIP().toString().c_str(),
                      ETH.linkSpeed(),
                      ETH.fullDuplex() ? "full" : "half");
        break;
    case ARDUINO_EVENT_ETH_DISCONNECTED:
        Serial.println("[ETH] Link DOWN");
        break;
    case ARDUINO_EVENT_ETH_STOP:
        Serial.println("[ETH] Stopped");
        break;
    default:
        break;
    }
}

// ---------------------------------------------------------------------------
// setup()
// ---------------------------------------------------------------------------
void setup()
{
    Serial.begin(115200);
    Serial.println("\n[BOOT] PoE FanController v0.3 — Waveshare ESP32-P4-ETH");

    // P-FW-05: Set fans to 100% immediately, before config is loaded
    fan_init();
    temp_init();
    probe_init();  // DS18B20 external probe (GPIO19/GPIO20)
    ota_init();  // Initialise prog LED (GPIO15) — held LOW until OTA starts

    // Register Ethernet event handler
    Network.onEvent(on_eth_event);

    // Waveshare ESP32-P4-POE-ETH (SKU 32088) has LAN8720A built in.
    // RMII fixed pins GPIO32–37 + GPIO50 assigned automatically by ETH.begin().
    // MDC=GPIO31, MDIO=GPIO52, RST=GPIO51 — confirmed from Waveshare Kconfig.
    ETH.begin(
        ETH_PHY_LAN8720,         // PHY type
        ETH_PHY_ADDR,            // PHY address (set via build flag, default 1)
        ETH_PHY_MDC,             // MDC  pin — GPIO31
        ETH_PHY_MDIO,            // MDIO pin — GPIO52
        ETH_PHY_RST,             // RST  pin — GPIO51
        ETH_CLK_MODE             // ETH_CLOCK_GPIO50_OUT — 50 MHz from MCU
    );

    web_init();
}

// ---------------------------------------------------------------------------
// loop()
// ---------------------------------------------------------------------------
void loop()
{
    // All logic is event-driven or handled in FreeRTOS tasks.
    // No blocking calls here (P-FW-04).
    delay(10);
}
