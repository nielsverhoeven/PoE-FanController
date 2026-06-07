/**
 * @file ota.cpp
 * @brief HTTP OTA update handler for PoE FanController v0.2.
 *
 * Replaces ArduinoOTA (WiFi UDP) with HTTP POST /api/v1/ota over wired Ethernet.
 * Uses ESPAsyncWebServer streaming upload pattern — no delay() in callbacks (P-FW-04).
 *
 * Client usage:
 *   curl -X POST http://<device-ip>/api/v1/ota --data-binary @firmware.bin
 *   HTTP 200 "OK"  → update applied, device rebooting
 *   HTTP 500 "FAIL" → update failed (check serial log)
 */

#include <Arduino.h>
#include <Update.h>
#include <ESPAsyncWebServer.h>

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
        if (!Update.begin(UPDATE_SIZE_UNKNOWN)) {
            Serial.printf("[OTA] begin() error: %s\n", Update.errorString());
        }
    }

    if (Update.isRunning()) {
        if (Update.write(data, len) != len) {
            Serial.printf("[OTA] write() error: %s\n", Update.errorString());
        }
    }

    if (final) {
        if (!Update.end(true)) {
            Serial.printf("[OTA] end() error: %s\n", Update.errorString());
        } else {
            Serial.println("[OTA] Complete — rebooting");
        }
    }
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
