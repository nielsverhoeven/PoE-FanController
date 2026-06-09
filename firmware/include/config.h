/**
 * @file config.h
 * @brief NVS-backed configuration store for PoE FanController.
 *
 * Keys are persisted in the "fanctrl" NVS namespace.
 * All getters return defaults on first boot (no prior NVS entry).
 *
 * NVS key: "curve_sensor"
 *   Type   : string
 *   Values : "ntc"   — use onboard NTC thermistor (default)
 *             "probe" — use DS18B20 external probe (GPIO19)
 *             "max"   — use whichever sensor reports highest temperature
 *   Default: "ntc"   — no regression on first boot
 */
#pragma once

#include <stdint.h>

/** Sensor selection for fan curve temperature input */
typedef enum {
    CURVE_SENSOR_NTC   = 0,  ///< Onboard NTC thermistor (GPIO16 ADC) — default
    CURVE_SENSOR_PROBE = 1,  ///< DS18B20 external probe (GPIO19 1-Wire)
    CURVE_SENSOR_MAX   = 2   ///< Maximum of NTC and probe readings
} curve_sensor_t;

/**
 * @brief Initialise the config module (open NVS namespace).
 * Call once from setup() before reading any config values.
 */
void config_init();

/**
 * @brief Get the curve sensor selection from NVS.
 * @return CURVE_SENSOR_NTC (default), CURVE_SENSOR_PROBE, or CURVE_SENSOR_MAX.
 */
curve_sensor_t config_get_curve_sensor();

/**
 * @brief Persist the curve sensor selection to NVS.
 * @param sensor  One of CURVE_SENSOR_NTC, CURVE_SENSOR_PROBE, CURVE_SENSOR_MAX.
 */
void config_set_curve_sensor(curve_sensor_t sensor);
