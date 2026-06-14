/**
 * @file temp.cpp
 * @brief DHT22 temperature + humidity sensing for PoE FanController.
 *
 * Replaces DHT11 (2026-06-14). Same pinout, same library, sensor type changed to DHT22.
 * Uses GPIO5 (J8 pin 10) as the DHT22 single-wire data line.
 * Library: Adafruit DHT sensor library (adafruit/DHT sensor library@^1.4.6).
 */

#include <Arduino.h>
#include <DHT.h>
#include "pins.h"

static DHT _dht(DHT11_DATA_PIN, DHT22);

static float _temp_celsius  = 25.0f;  ///< last valid temperature reading
static float _humidity_pct  = 50.0f;  ///< last valid humidity reading

// ---------------------------------------------------------------------------
// temp_init() — configure DHT11 sensor
// ---------------------------------------------------------------------------
void temp_init()
{
    _dht.begin();
    Serial.printf("[TEMP] DHT22 initialised on GPIO%d\n", DHT11_DATA_PIN);
}

// ---------------------------------------------------------------------------
// temp_read_celsius() — read DHT11 and return temperature in °C
// Returns cached value on read failure (NaN guard).
// ---------------------------------------------------------------------------
float temp_read_celsius()
{
    float t = _dht.readTemperature();
    if (!isnan(t)) {
        _temp_celsius = t;
    }
    // Also refresh humidity while we have the bus
    float h = _dht.readHumidity();
    if (!isnan(h)) {
        _humidity_pct = h;
    }
    return _temp_celsius;
}

// ---------------------------------------------------------------------------
// temp_get_cached() — return last computed temperature (safe from any context)
// ---------------------------------------------------------------------------
float temp_get_cached()
{
    return _temp_celsius;
}

// ---------------------------------------------------------------------------
// temp_get_humidity() — return last valid relative humidity in % (0–100)
// ---------------------------------------------------------------------------
float temp_get_humidity()
{
    return _humidity_pct;
}

