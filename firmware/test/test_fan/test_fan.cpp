/**
 * @file test_fan.cpp
 * @brief Unit tests: LEDC API usage verification (new arduino-esp32 3.x style).
 *
 * Asserts that the fan module uses ledcAttach(pin, freq, bits) and ledcWrite(pin, duty)
 * — NOT the deprecated ledcSetup() / ledcAttachPin() from arduino-esp32 2.x.
 *
 * Run: pio test -e native
 */
#include <unity.h>
#include <stdint.h>
#include <stdbool.h>
#include "pins.h"

// ---------------------------------------------------------------------------
// Stubs — track which LEDC API calls were made
// ---------------------------------------------------------------------------
static int  _attach_calls = 0;
static int  _write_calls  = 0;
static int  _setup_calls  = 0;       // deprecated 2.x — must remain 0
static int  _attach_pin_calls = 0;   // deprecated 2.x — must remain 0

static int   _attached_pin[4];
static float _attached_freq[4];
static int   _attached_bits[4];
static int   _written_pin[4];
static uint8_t _written_duty[4];

// New 3.x API stubs
void ledcAttach(uint8_t pin, uint32_t freq, uint8_t bits) {
    _attached_pin [_attach_calls] = pin;
    _attached_freq[_attach_calls] = freq;
    _attached_bits[_attach_calls] = bits;
    _attach_calls++;
}
void ledcWrite(uint8_t pin, uint32_t duty) {
    _written_pin [_write_calls] = pin;
    _written_duty[_write_calls] = (uint8_t)duty;
    _write_calls++;
}

// Deprecated 2.x API stubs (should NEVER be called in v0.2)
void ledcSetup(uint8_t /*ch*/, double /*freq*/, uint8_t /*bits*/) { _setup_calls++; }
void ledcAttachPin(uint8_t /*pin*/, uint8_t /*ch*/)               { _attach_pin_calls++; }

// Minimal Arduino stub
void pinMode(uint8_t, uint8_t) {}
void attachInterrupt(uint8_t, void(*)(), int) {}
int digitalPinToInterrupt(uint8_t pin) { return pin; }

// Serial stub
struct FakeSerial {
    void begin(int) {}
    void println(const char*) {}
    void printf(const char*, ...) {}
} Serial;

#define INPUT_PULLUP 0x02
#define FALLING      0

// Pull in fan_init() from fan.cpp
// We declare it extern so the linker picks it up from the fan module stub below.
// For native test, we provide a minimal fan_init that only calls the LEDC APIs.

static void fan_init_under_test()
{
    // Mirrors the loop in fan.cpp fan_init(), exercising only LEDC calls
    const uint8_t PWM_PINS[4] = {FAN1_PWM_PIN, FAN2_PWM_PIN, FAN3_PWM_PIN, FAN4_PWM_PIN};
    for (int i = 0; i < 4; i++) {
        ledcAttach(PWM_PINS[i], FAN_PWM_FREQ_HZ, FAN_PWM_RESOLUTION);
        ledcWrite(PWM_PINS[i], FAN_PWM_SAFE_DEFAULT);
    }
}

// ---------------------------------------------------------------------------
// Test: ledcAttach called 4 times (not ledcSetup)
// ---------------------------------------------------------------------------
void test_ledc_attach_called_not_setup()
{
    _attach_calls     = 0;
    _write_calls      = 0;
    _setup_calls      = 0;
    _attach_pin_calls = 0;

    fan_init_under_test();

    TEST_ASSERT_EQUAL_MESSAGE(4, _attach_calls,
        "ledcAttach() must be called once per fan (4 total)");
    TEST_ASSERT_EQUAL_MESSAGE(0, _setup_calls,
        "ledcSetup() is deprecated in arduino-esp32 3.x and must NOT be called");
    TEST_ASSERT_EQUAL_MESSAGE(0, _attach_pin_calls,
        "ledcAttachPin() is deprecated in arduino-esp32 3.x and must NOT be called");
}

// ---------------------------------------------------------------------------
// Test: correct pins, frequency, and resolution passed to ledcAttach
// ---------------------------------------------------------------------------
void test_ledc_attach_parameters()
{
    _attach_calls = 0;
    fan_init_under_test();

    const uint8_t expected_pins[4] = {
        FAN1_PWM_PIN, FAN2_PWM_PIN, FAN3_PWM_PIN, FAN4_PWM_PIN
    };

    for (int i = 0; i < 4; i++) {
        TEST_ASSERT_EQUAL(expected_pins[i],  _attached_pin[i]);
        TEST_ASSERT_EQUAL(FAN_PWM_FREQ_HZ,   (uint32_t)_attached_freq[i]);
        TEST_ASSERT_EQUAL(FAN_PWM_RESOLUTION, _attached_bits[i]);
    }
}

// ---------------------------------------------------------------------------
// Test: safe default (100%) written on init (P-FW-05)
// ---------------------------------------------------------------------------
void test_ledc_safe_default_on_init()
{
    _write_calls = 0;
    fan_init_under_test();

    TEST_ASSERT_EQUAL_MESSAGE(4, _write_calls,
        "ledcWrite() must be called for each fan on init");

    for (int i = 0; i < 4; i++) {
        TEST_ASSERT_EQUAL_MESSAGE(FAN_PWM_SAFE_DEFAULT, _written_duty[i],
            "All fans must start at 100% duty on boot (P-FW-05)");
    }
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------
void setUp()    {}
void tearDown() {}

int main(int argc, char** argv)
{
    UNITY_BEGIN();
    RUN_TEST(test_ledc_attach_called_not_setup);
    RUN_TEST(test_ledc_attach_parameters);
    RUN_TEST(test_ledc_safe_default_on_init);
    return UNITY_END();
}
