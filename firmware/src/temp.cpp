/**
 * @file temp.cpp
 * @brief NTC thermistor temperature sensing for PoE FanController v0.2.
 *
 * Uses GPIO16 (ADC1) — verified conflict-free with RMII fixed pins (OQ-01 resolved).
 * Steinhart-Hart simplified B-parameter equation:
 *   1/T = 1/T0 + (1/B) * ln(R/R0)
 */

#include <Arduino.h>
#include "pins.h"

#define ADC_RESOLUTION   12       ///< 12-bit ADC (0–4095)
#define ADC_VREF_MV    3300       ///< 3.3 V reference (mV)
#define KELVIN_OFFSET  273.15f

static float _temp_celsius = 25.0f;

// ---------------------------------------------------------------------------
// temp_init() — configure ADC pin
// ---------------------------------------------------------------------------
void temp_init()
{
    pinMode(NTC_ADC_PIN, INPUT);
    analogReadResolution(ADC_RESOLUTION);
    Serial.println("[TEMP] NTC ADC initialised on GPIO" STRINGIFY(NTC_ADC_PIN));
}

// ---------------------------------------------------------------------------
// temp_read_celsius() — read NTC and compute temperature
// ---------------------------------------------------------------------------
float temp_read_celsius()
{
    int raw = analogRead(NTC_ADC_PIN);
    if (raw <= 0 || raw >= 4095) return _temp_celsius;  // guard rail

    // Voltage divider: V_out = V_ref * R_ntc / (R_series + R_ntc)
    // R_ntc = R_series * raw / (ADC_MAX - raw)
    float r_ntc = NTC_SERIES_OHM * (float)raw / (float)(4095 - raw);

    // Steinhart-Hart B-parameter equation
    float t_inv = 1.0f / (NTC_NOMINAL_TEMP + KELVIN_OFFSET)
                + (1.0f / (float)NTC_BETA) * logf(r_ntc / (float)NTC_NOMINAL_OHM);
    _temp_celsius = (1.0f / t_inv) - KELVIN_OFFSET;

    return _temp_celsius;
}

// ---------------------------------------------------------------------------
// temp_get_cached() — return last computed value (safe to call from ISR context)
// ---------------------------------------------------------------------------
float temp_get_cached()
{
    return _temp_celsius;
}
