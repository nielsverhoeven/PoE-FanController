/**
 * @file probe.h
 * @brief DS18B20 external temperature probe API for PoE FanController.
 *
 * Hardware: DS18B20 connected via J6 (Molex KK-254 3-pin) to GPIO19 (1-Wire DATA).
 *   - R14 (4.7 kΩ) pull-up on PCB between DS18B20_DATA and +3V3.
 *   - LED6 (green, GPIO20 via R15 330 Ω) indicates probe health (Status_LED_5).
 *
 * State machine:
 *   PROBE_ABSENT  — no DS18B20 detected on 1-Wire bus
 *   PROBE_READING — conversion in progress (750 ms for 12-bit resolution)
 *   PROBE_OK      — valid temperature available
 *
 * Sentinel value: -127.0f indicates probe absent or out-of-range.
 */
#ifndef PROBE_H
#define PROBE_H

#include <stdint.h>

/** Probe operational state */
typedef enum {
    PROBE_ABSENT  = 0,  ///< No DS18B20 detected on 1-Wire bus
    PROBE_READING = 1,  ///< Temperature conversion in progress
    PROBE_OK      = 2   ///< Valid temperature cached and available
} probe_state_t;

/**
 * @brief Initialise the DS18B20 probe module and start background FreeRTOS task.
 *
 * Configures GPIO19 for 1-Wire (OneWire library) and GPIO20 as output for LED6.
 * Spawns a FreeRTOS task (priority 1, stack 2048 words) that polls the sensor
 * every ~1 second and drives LED6 according to probe state.
 *
 * Call from setup() after temp_init() and before web_init().
 */
void probe_init();

/**
 * @brief Return the most recently cached DS18B20 temperature in °C.
 *
 * Thread-safe (reads a cached float; written atomically by probe task).
 * Range guard: only values in [-55.0, +125.0] °C are accepted.
 *
 * @return Temperature in °C, or -127.0f if probe is absent or out-of-range.
 */
float probe_get_temp_celsius();

/**
 * @brief Return the current probe operational state.
 *
 * @return PROBE_ABSENT, PROBE_READING, or PROBE_OK.
 */
probe_state_t probe_get_state();

#endif /* PROBE_H */
