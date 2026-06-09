/**
 * @file web.cpp
 * @brief Web server and REST API for PoE FanController v0.2.
 *
 * Network: Wired Ethernet (ETH.localIP() — not WiFi.localIP()).
 * OTA endpoint registered via ota_register() (no ArduinoOTA).
 * REST API paths (P-UI-01):
 *   GET  /api/v1/status     — system status (IP, temp, fan speeds)
 *   POST /api/v1/fan/{n}    — set fan duty (body: {"duty":128})
 *   POST /api/v1/ota        — firmware update (binary upload)
 */

#include <Arduino.h>
#include <ETH.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include "pins.h"

// Forward declarations from other modules
float temp_read_celsius();
uint32_t fan_get_rpm(uint8_t idx);
uint8_t  fan_get_duty(uint8_t idx);
void     fan_set_duty(uint8_t idx, uint8_t duty);
void     ota_register(AsyncWebServer* server);
float    probe_get_temp_celsius();
int      probe_get_state();   // probe_state_t, cast to int for forward decl

static AsyncWebServer _server(80);

// ---------------------------------------------------------------------------
// Status endpoint: GET /api/v1/status
// ---------------------------------------------------------------------------
static void handle_status(AsyncWebServerRequest* request)
{
    JsonDocument doc;
    doc["ip"]        = ETH.localIP().toString();   // Ethernet IP (not WiFi)
    doc["link_mbps"] = ETH.linkSpeed();
    doc["full_duplex"] = ETH.fullDuplex();
    doc["temp_c"]    = (float)((int)(temp_read_celsius() * 10)) / 10.0f;

    // DS18B20 external probe — null if absent (-127.0f sentinel), float otherwise
    float probe_t = probe_get_temp_celsius();
    if (probe_t <= -126.0f) {
        doc["probe_temp_c"] = nullptr;  // JSON null — probe absent
    } else {
        doc["probe_temp_c"] = (float)((int)(probe_t * 10)) / 10.0f;  // 1 decimal
    }

    JsonArray fans = doc["fans"].to<JsonArray>();
    for (int i = 0; i < 4; i++) {
        JsonObject fan = fans.add<JsonObject>();
        fan["duty"] = fan_get_duty(i);
        fan["rpm"]  = fan_get_rpm(i);
    }

    String body;
    serializeJson(doc, body);
    request->send(200, "application/json", body);
}

// ---------------------------------------------------------------------------
// Fan control: POST /api/v1/fan/{n}   body: {"duty":0-255}
// ---------------------------------------------------------------------------
static void handle_fan_set(AsyncWebServerRequest* request, uint8_t* data,
                            size_t len, size_t index, size_t total)
{
    String param = request->pathArg(0);
    int fan_idx  = param.toInt();
    if (fan_idx < 0 || fan_idx > 3) {
        request->send(400, "text/plain", "Bad fan index (0-3)");
        return;
    }

    JsonDocument doc;
    if (deserializeJson(doc, data, len)) {
        request->send(400, "text/plain", "Bad JSON");
        return;
    }

    int duty = doc["duty"] | -1;
    if (duty < 0 || duty > 255) {
        request->send(400, "text/plain", "duty must be 0-255");
        return;
    }

    fan_set_duty((uint8_t)fan_idx, (uint8_t)duty);
    request->send(200, "text/plain", "OK");
}

// ---------------------------------------------------------------------------
// web_init() — build and start the server
// ---------------------------------------------------------------------------
void web_init()
{
    _server.on("/api/v1/status", HTTP_GET, handle_status);

    _server.on(
        "^\\/api\\/v1\\/fan\\/([0-3])$",
        HTTP_POST,
        [](AsyncWebServerRequest* r) {},  // final response sent in body handler
        nullptr,
        handle_fan_set
    );

    // OTA upload endpoint (defined in ota.cpp)
    ota_register(&_server);

    // Serve static web UI from LittleFS (data/ directory)
    // DefaultFile and static handler will be added when data/ is populated
    _server.onNotFound([](AsyncWebServerRequest* request) {
        request->send(404, "text/plain", "Not found");
    });

    _server.begin();

    Serial.printf("[WEB] Server started — http://%s/\n",
                  ETH.localIP().toString().c_str());
}
