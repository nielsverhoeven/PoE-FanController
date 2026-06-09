/**
 * @file probe.cpp
 * @brief DS18B20 external temperature probe implementation for PoE FanController.
 *
 * Uses OneWire + DallasTemperature libraries for 1-Wire communication.
 * Runs as a FreeRTOS task (priority 1, stack 2048 words).
 *
 * LED6 (GPIO20, PROBE_LED_PIN) blink pattern:
 *   PROBE_ABSENT  — LED off
 *   PROBE_READING — LED blinks 500 ms on / 500 ms off (non-blocking, millis-based)
 *   PROBE_OK      — LED steady on
 *
 * State machine cycle (~1 second total):
 *   1. Request conversion on 1-Wire bus.
 *   2. Wait 750 ms (12-bit resolution conversion time per DS18B20 datasheet).
 *   3. Read temperature; validate range [-55, +125] °C.
 *   4. Update cached value and state; drive LED accordingly.
 *   5. vTaskDelay 250 ms before next cycle.
 */

#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "pins.h"
#include "probe.h"

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
#define PROBE_TEMP_MIN     (-55.0f)   ///< DS18B20 minimum rated temperature
#define PROBE_TEMP_MAX     (125.0f)   ///< DS18B20 maximum rated temperature
#define PROBE_ABSENT_SENTINEL (-127.0f) ///< Returned when probe not present
#define PROBE_CONVERSION_MS  750      ///< 12-bit conversion time (ms)
#define PROBE_POLL_DELAY_MS  250      ///< Additional delay between cycles (ms)
#define PROBE_BLINK_PERIOD_MS 500     ///< LED blink half-period when READING (ms)
#define PROBE_TASK_STACK_WORDS 2048   ///< FreeRTOS stack size (words)
#define PROBE_TASK_PRIORITY    1      ///< FreeRTOS task priority

// ---------------------------------------------------------------------------
// Module-level state (written by probe task, read by public API)
// ---------------------------------------------------------------------------
static volatile probe_state_t _state    = PROBE_ABSENT;
static volatile float         _temp_c   = PROBE_ABSENT_SENTINEL;

// ---------------------------------------------------------------------------
// OneWire + DallasTemperature instances
// ---------------------------------------------------------------------------
static OneWire          _ow(DS18B20_DATA_PIN);
static DallasTemperature _sensors(&_ow);

// ---------------------------------------------------------------------------
// LED helper — non-blocking blink driven from probe task
// ---------------------------------------------------------------------------
static void update_led(probe_state_t state, unsigned long now_ms,
                        unsigned long* last_toggle_ms, bool* led_on)
{
    switch (state) {
    case PROBE_ABSENT:
        digitalWrite(PROBE_LED_PIN, LOW);
        *led_on = false;
        break;

    case PROBE_READING:
        // Non-blocking blink: toggle every PROBE_BLINK_PERIOD_MS ms
        if ((now_ms - *last_toggle_ms) >= PROBE_BLINK_PERIOD_MS) {
            *led_on = !(*led_on);
            digitalWrite(PROBE_LED_PIN, *led_on ? HIGH : LOW);
            *last_toggle_ms = now_ms;
        }
        break;

    case PROBE_OK:
        if (!(*led_on)) {
            digitalWrite(PROBE_LED_PIN, HIGH);
            *led_on = true;
        }
        break;
    }
}

// ---------------------------------------------------------------------------
// probe_task() — FreeRTOS task body
// ---------------------------------------------------------------------------
static void probe_task(void* /*arg*/)
{
    unsigned long last_toggle_ms = 0;
    bool          led_on         = false;

    _sensors.begin();

    for (;;) {
        unsigned long cycle_start = millis();

        // --- Detect sensor ---
        int count = _sensors.getDeviceCount();
        if (count == 0) {
            _state  = PROBE_ABSENT;
            _temp_c = PROBE_ABSENT_SENTINEL;
            update_led(PROBE_ABSENT, millis(), &last_toggle_ms, &led_on);
            vTaskDelay(pdMS_TO_TICKS(PROBE_CONVERSION_MS + PROBE_POLL_DELAY_MS));
            continue;
        }

        // --- Request temperature conversion ---
        _state = PROBE_READING;
        _sensors.requestTemperatures();

        // Blink LED during 750 ms conversion window (non-blocking)
        unsigned long conversion_end = cycle_start + PROBE_CONVERSION_MS;
        while (millis() < conversion_end) {
            update_led(PROBE_READING, millis(), &last_toggle_ms, &led_on);
            vTaskDelay(pdMS_TO_TICKS(50));
        }

        // --- Read result ---
        float raw = _sensors.getTempCByIndex(0);

        if (raw <= DEVICE_DISCONNECTED_C || raw < PROBE_TEMP_MIN || raw > PROBE_TEMP_MAX) {
            // Out of range or disconnected mid-cycle
            _state  = PROBE_ABSENT;
            _temp_c = PROBE_ABSENT_SENTINEL;
            update_led(PROBE_ABSENT, millis(), &last_toggle_ms, &led_on);
        } else {
            _temp_c = raw;
            _state  = PROBE_OK;
            update_led(PROBE_OK, millis(), &last_toggle_ms, &led_on);
        }

        vTaskDelay(pdMS_TO_TICKS(PROBE_POLL_DELAY_MS));
    }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

void probe_init()
{
    pinMode(PROBE_LED_PIN, OUTPUT);
    digitalWrite(PROBE_LED_PIN, LOW);

    xTaskCreate(
        probe_task,
        "probe_task",
        PROBE_TASK_STACK_WORDS,
        nullptr,
        PROBE_TASK_PRIORITY,
        nullptr
    );

    Serial.printf("[PROBE] DS18B20 probe init — GPIO%d (1-Wire), LED GPIO%d\n",
                  DS18B20_DATA_PIN, PROBE_LED_PIN);
}

float probe_get_temp_celsius()
{
    return _temp_c;
}

probe_state_t probe_get_state()
{
    return _state;
}
