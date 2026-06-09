/**
 * @file config.cpp
 * @brief NVS-backed configuration store for PoE FanController.
 *
 * Uses the ESP32 Arduino Preferences library (thin wrapper over NVS).
 * Namespace: "fanctrl"  (max 15 chars per ESP-IDF NVS limit)
 *
 * curve_sensor key stores one of: "ntc" | "probe" | "max"
 * Default "ntc" on first boot (no regression from pre-probe firmware).
 */

#include <Arduino.h>
#include <Preferences.h>
#include "config.h"

// ---------------------------------------------------------------------------
// Internal constants
// ---------------------------------------------------------------------------
static const char* NVS_NAMESPACE     = "fanctrl";
static const char* KEY_CURVE_SENSOR  = "curve_sensor";
static const char* VAL_NTC           = "ntc";
static const char* VAL_PROBE         = "probe";
static const char* VAL_MAX           = "max";

static Preferences _prefs;

// ---------------------------------------------------------------------------
// config_init()
// ---------------------------------------------------------------------------
void config_init()
{
    // Open in read-write mode; creates namespace if it doesn't exist
    _prefs.begin(NVS_NAMESPACE, /*readOnly=*/false);
    Serial.println("[CFG] NVS namespace 'fanctrl' opened");
}

// ---------------------------------------------------------------------------
// config_get_curve_sensor()
// ---------------------------------------------------------------------------
curve_sensor_t config_get_curve_sensor()
{
    String val = _prefs.getString(KEY_CURVE_SENSOR, VAL_NTC);  // default "ntc"

    if (val == VAL_PROBE) return CURVE_SENSOR_PROBE;
    if (val == VAL_MAX)   return CURVE_SENSOR_MAX;
    return CURVE_SENSOR_NTC;  // default (also covers unknown/corrupt values)
}

// ---------------------------------------------------------------------------
// config_set_curve_sensor()
// ---------------------------------------------------------------------------
void config_set_curve_sensor(curve_sensor_t sensor)
{
    const char* val = VAL_NTC;
    switch (sensor) {
    case CURVE_SENSOR_PROBE: val = VAL_PROBE; break;
    case CURVE_SENSOR_MAX:   val = VAL_MAX;   break;
    default:                 val = VAL_NTC;   break;
    }
    _prefs.putString(KEY_CURVE_SENSOR, val);
    Serial.printf("[CFG] curve_sensor set to '%s'\n", val);
}
