/**
 * @file main.cpp
 * @brief PoE FanController v0.2 — ESP32-P4 + LAN8720A Ethernet entry point.
 *
 * Network: wired 100BASE-T via LAN8720A RMII PHY (no WiFi — ESP32-P4 has none).
 * OTA:     HTTP POST /api/v1/ota (see ota.cpp — replaces ArduinoOTA).
 *
 * Startup sequence (P-FW-05 safe-boot):
 *   1. Set all fans to 100 % duty (FAN_PWM_SAFE_DEFAULT).
 *   2. Start Ethernet (ETH.begin).
 *   3. Wait for IP via ARDUINO_EVENT_ETH_GOT_IP.
 *   4. Load config from NVS; apply fan curves.
 *   5. Start web server.
 */

#include <Arduino.h>
#include <ETH.h>
#include <Update.h>
#include "pins.h"

// Forward declarations — defined in their respective modules
void fan_init();
void temp_init();
void web_init();
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
    Serial.println("\n[BOOT] PoE FanController v0.2 — ESP32-P4");

    // P-FW-05: Set fans to 100% immediately, before config is loaded
    fan_init();
    temp_init();

    // Register Ethernet event handler
    Network.onEvent(on_eth_event);

    // LAN8720A on RMII — GPIO50 provides 50 MHz REF_CLK to PHY.
    // RMII fixed pins GPIO32–37 + GPIO50 are assigned automatically by ETH.begin().
    // MDC = GPIO31, MDIO = GPIO28 (GPIO-matrix configurable).
    ETH.begin(
        ETH_PHY_LAN8720,         // PHY type
        ETH_PHY_ADDR,            // PHY address 0 (ADDR0/ADDR1 tied low on LAN8720A)
        ETH_PHY_MDC,             // MDC  pin (GPIO31) — from build_flags
        ETH_PHY_MDIO,            // MDIO pin (GPIO28) — from build_flags
        -1,                      // PHY power pin (-1 = not used)
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
