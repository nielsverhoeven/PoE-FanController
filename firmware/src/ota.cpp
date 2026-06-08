/**
 * @file ota.cpp
 * @brief HTTP OTA update handler for PoE FanController v0.2.
 *
 * Replaces ArduinoOTA (WiFi UDP) with HTTP POST /api/v1/ota over wired Ethernet.
 * Uses ESPAsyncWebServer streaming upload pattern — no delay() in callbacks (P-FW-04).
 *
 * LED2 (orange, GPIO15 / PROG_LED_PIN) flickers during firmware write:
 *   - Toggles on every chunk write to give visual feedback.
 *   - Held HIGH while update is running, driven LOW on completion/error.
 *
 * Client usage:
 *   curl -X POST http://<device-ip>/api/v1/ota --data-binary @firmware.bin
 *   HTTP 200 "OK"  → update applied, device rebooting
 *   HTTP 500 "FAIL" → update failed (check serial log)
 */

#include <Arduino.h>
#include <Update.h>
#include <ESPAsyncWebServer.h>
#include "pins.h"

// ---------------------------------------------------------------------------
// Internal upload callback — no blocking, no delay() (P-FW-04)
// ---------------------------------------------------------------------------
static void handle_ota_upload(AsyncWebServerRequest* request,
                               const String& filename,
                               size_t index,
                               uint8_t* data,
                               size_t len,
                               bool final)
{
    if (!index) {
        Serial.printf("[OTA] Start: %s  size: %u bytes\n",
                      filename.c_str(), request->contentLength());
        digitalWrite(PROG_LED_PIN, HIGH);   // LED on: OTA starting
        if (!Update.begin(UPDATE_SIZE_UNKNOWN)) {
            Serial.printf("[OTA] begin() error: %s\n", Update.errorString());
        }
    }

    if (Update.isRunning()) {
        // Toggle LED on each chunk to produce flicker effect
        digitalWrite(PROG_LED_PIN, !digitalRead(PROG_LED_PIN));
        if (Update.write(data, len) != len) {
            Serial.printf("[OTA] write() error: %s\n", Update.errorString());
        }
    }

    if (final) {
        if (!Update.end(true)) {
            Serial.printf("[OTA] end() error: %s\n", Update.errorString());
            digitalWrite(PROG_LED_PIN, LOW);   // LED off: failed
        } else {
            Serial.println("[OTA] Complete — rebooting");
            digitalWrite(PROG_LED_PIN, HIGH);  // LED steady: success, about to reboot
        }
    }
}

// ---------------------------------------------------------------------------
// ota_init() — initialise GPIO and register route; call from setup()
// ---------------------------------------------------------------------------
void ota_init()
{
    pinMode(PROG_LED_PIN, OUTPUT);
    digitalWrite(PROG_LED_PIN, LOW);  // off at boot
}

// ---------------------------------------------------------------------------
// ota_register() — call from web_init() after server is created
// ---------------------------------------------------------------------------
void ota_register(AsyncWebServer* server)
{
    server->on(
        "/api/v1/ota",
        HTTP_POST,
        // Response handler (called after upload finishes)
        [](AsyncWebServerRequest* request) {
            bool ok = !Update.hasError();
            request->send(ok ? 200 : 500,
                          "text/plain",
                          ok ? "OK" : "FAIL");
            if (ok) {
                // Short delay to ensure response is sent before reboot
                // Acceptable here: single post-OTA path, not in hot loop (P-FW-04)
                delay(100);
                ESP.restart();
            }
        },
        // Upload handler (called for each chunk)
        handle_ota_upload
    );

    Serial.println("[OTA] POST /api/v1/ota registered");
}
