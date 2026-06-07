/**
 * @file fan.cpp
 * @brief Fan PWM and tachometer module for PoE FanController v0.2.
 *
 * Uses arduino-esp32 3.x LEDC API:
 *   ledcAttach(pin, freq, resolution)  — binds pin to LEDC channel
 *   ledcWrite(pin, duty)               — sets duty cycle
 *   ledcDetach(pin)                    — releases pin
 *
 * NOT: ledcSetup() / ledcAttachPin() — deprecated in 3.x, removed in 4.x.
 */

#include <Arduino.h>
#include "pins.h"

// ---------------------------------------------------------------------------
// Internal state
// ---------------------------------------------------------------------------
static uint8_t _duty[4] = {
    FAN_PWM_SAFE_DEFAULT,
    FAN_PWM_SAFE_DEFAULT,
    FAN_PWM_SAFE_DEFAULT,
    FAN_PWM_SAFE_DEFAULT,
};

static const uint8_t PWM_PINS[4] = {
    FAN1_PWM_PIN, FAN2_PWM_PIN, FAN3_PWM_PIN, FAN4_PWM_PIN,
};

static const uint8_t TACH_PINS[4] = {
    FAN1_TACH_PIN, FAN2_TACH_PIN, FAN3_TACH_PIN, FAN4_TACH_PIN,
};

// Tachometer pulse counters (incremented in ISR, read in task context)
static volatile uint32_t _tach_pulses[4] = {0, 0, 0, 0};

// ---------------------------------------------------------------------------
// ISR stubs — one per fan (no lambda captures in ISR)
// ---------------------------------------------------------------------------
static void IRAM_ATTR isr_fan0() { _tach_pulses[0]++; }
static void IRAM_ATTR isr_fan1() { _tach_pulses[1]++; }
static void IRAM_ATTR isr_fan2() { _tach_pulses[2]++; }
static void IRAM_ATTR isr_fan3() { _tach_pulses[3]++; }

static void (* const ISR_TABLE[4])() = { isr_fan0, isr_fan1, isr_fan2, isr_fan3 };

// ---------------------------------------------------------------------------
// fan_init() — called from setup() BEFORE config load (P-FW-05 safe default)
// ---------------------------------------------------------------------------
void fan_init()
{
    for (int i = 0; i < 4; i++) {
        // PWM output — arduino-esp32 3.x API (P-FW-03: 25 kHz, 8-bit)
        ledcAttach(PWM_PINS[i], FAN_PWM_FREQ_HZ, FAN_PWM_RESOLUTION);
        ledcWrite(PWM_PINS[i], FAN_PWM_SAFE_DEFAULT);  // 100 % on boot

        // Tachometer input with internal pull-up
        pinMode(TACH_PINS[i], INPUT_PULLUP);
        attachInterrupt(digitalPinToInterrupt(TACH_PINS[i]),
                        ISR_TABLE[i], FALLING);
    }
    Serial.println("[FAN] Initialised — all fans at 100%");
}

// ---------------------------------------------------------------------------
// fan_set_duty() — set duty 0–255 for fan index 0–3
// ---------------------------------------------------------------------------
void fan_set_duty(uint8_t fan_idx, uint8_t duty)
{
    if (fan_idx >= 4) return;
    _duty[fan_idx] = duty;
    ledcWrite(PWM_PINS[fan_idx], duty);
}

// ---------------------------------------------------------------------------
// fan_get_duty() — return current duty 0–255
// ---------------------------------------------------------------------------
uint8_t fan_get_duty(uint8_t fan_idx)
{
    if (fan_idx >= 4) return 0;
    return _duty[fan_idx];
}

// ---------------------------------------------------------------------------
// fan_get_rpm() — return estimated RPM from tachometer pulses
//   Call every 1 second; fans typically emit 2 pulses per revolution.
// ---------------------------------------------------------------------------
uint32_t fan_get_rpm(uint8_t fan_idx)
{
    if (fan_idx >= 4) return 0;
    // Snapshot and clear pulse counter (read in task context = safe)
    uint32_t pulses = _tach_pulses[fan_idx];
    _tach_pulses[fan_idx] = 0;
    return (pulses * 60) / 2;  // 2 pulses per rev, sampled over 1 s
}
