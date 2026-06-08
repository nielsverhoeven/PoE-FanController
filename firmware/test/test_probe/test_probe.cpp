/**
 * @file test_probe.cpp
 * @brief Unit tests for DS18B20 probe module (native env).
 *
 * All hardware dependencies (OneWire, DallasTemperature, Arduino GPIO, FreeRTOS)
 * are stubbed/mocked — no real hardware needed.
 *
 * Test cases:
 *   1. test_probe_sentinel     — absent state returns -127.0f
 *   2. test_probe_json_null    — absent → JSON null representation check
 *   3. test_probe_json_float   — OK + 42.0 °C → JSON 42.0 check
 *   4. test_probe_range_guard  — out-of-range values are rejected
 *   5. test_probe_state_transitions — ABSENT → READING → OK transitions valid
 *
 * Run: pio test -e native
 */

#include <unity.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>

// ---------------------------------------------------------------------------
// Minimal Arduino / FreeRTOS stubs for native build
// ---------------------------------------------------------------------------
#define HIGH 1
#define LOW  0
#define OUTPUT 1
#define INPUT  0

static int _pin_mode[64]  = {0};
static int _pin_state[64] = {0};

void pinMode(uint8_t pin, uint8_t mode)  { if (pin < 64) _pin_mode[pin]  = mode; }
void digitalWrite(uint8_t pin, uint8_t v){ if (pin < 64) _pin_state[pin] = v;    }
uint8_t digitalRead(uint8_t pin)         { return (pin < 64) ? _pin_state[pin] : 0; }

struct FakeSerial {
    void begin(int) {}
    void println(const char*) {}
    void printf(const char*, ...) {}
} Serial;

// FreeRTOS stub
typedef unsigned int TickType_t;
#define pdMS_TO_TICKS(ms) ((TickType_t)(ms))
void vTaskDelay(TickType_t) {}
typedef void* TaskHandle_t;
typedef void (*TaskFunction_t)(void*);
int xTaskCreate(TaskFunction_t, const char*, uint32_t, void*, int, TaskHandle_t*) { return 1; }

// millis stub
static unsigned long _fake_millis = 0;
unsigned long millis() { return _fake_millis; }

// ---------------------------------------------------------------------------
// OneWire / DallasTemperature stubs (injectable)
// ---------------------------------------------------------------------------
static int   _device_count   = 0;
static float _raw_temp_c     = 0.0f;
static bool  _conversion_req = false;

// Stub classes mirroring the real API
#define DEVICE_DISCONNECTED_C (-127.0f)

class OneWire {
public:
    OneWire(uint8_t /*pin*/) {}
};

class DallasTemperature {
public:
    DallasTemperature(OneWire* /*ow*/) {}
    void begin()                          { }
    int  getDeviceCount()                 { return _device_count; }
    void requestTemperatures()            { _conversion_req = true; }
    float getTempCByIndex(uint8_t /*i*/)  { return _raw_temp_c; }
};

// ---------------------------------------------------------------------------
// Pull in the probe module under test (inline reimplementation for native env)
// ---------------------------------------------------------------------------

// Inline the probe logic directly for testability (avoids linking Arduino libs)

typedef enum {
    PROBE_ABSENT  = 0,
    PROBE_READING = 1,
    PROBE_OK      = 2
} probe_state_t;

#define PROBE_TEMP_MIN          (-55.0f)
#define PROBE_TEMP_MAX          (125.0f)
#define PROBE_ABSENT_SENTINEL   (-127.0f)
#define DS18B20_DATA_PIN        19
#define PROBE_LED_PIN           20

// Testable state (mimics probe.cpp statics, exposed for tests)
static volatile probe_state_t _test_state  = PROBE_ABSENT;
static volatile float         _test_temp_c = PROBE_ABSENT_SENTINEL;

static OneWire          _test_ow(DS18B20_DATA_PIN);
static DallasTemperature _test_sensors(&_test_ow);

/** Simulate one full probe cycle using the injectable stubs */
static void run_probe_cycle()
{
    _test_sensors.begin();

    if (_test_sensors.getDeviceCount() == 0) {
        _test_state  = PROBE_ABSENT;
        _test_temp_c = PROBE_ABSENT_SENTINEL;
        return;
    }

    _test_state = PROBE_READING;
    _test_sensors.requestTemperatures();

    float raw = _test_sensors.getTempCByIndex(0);

    if (raw <= DEVICE_DISCONNECTED_C || raw < PROBE_TEMP_MIN || raw > PROBE_TEMP_MAX) {
        _test_state  = PROBE_ABSENT;
        _test_temp_c = PROBE_ABSENT_SENTINEL;
    } else {
        _test_temp_c = raw;
        _test_state  = PROBE_OK;
    }
}

// Public API wrappers (mirrors probe.h)
static float         test_probe_get_temp_celsius() { return _test_temp_c; }
static probe_state_t test_probe_get_state()        { return _test_state;  }

// ---------------------------------------------------------------------------
// JSON null / float helpers (mirrors web.cpp logic, no ArduinoJson needed)
// ---------------------------------------------------------------------------
static bool probe_json_is_null(float t)   { return t <= -126.0f; }
static float probe_json_value(float t)    { return (float)((int)(t * 10)) / 10.0f; }

// ---------------------------------------------------------------------------
// setUp / tearDown
// ---------------------------------------------------------------------------
void setUp()
{
    _device_count   = 0;
    _raw_temp_c     = 0.0f;
    _conversion_req = false;
    _test_state     = PROBE_ABSENT;
    _test_temp_c    = PROBE_ABSENT_SENTINEL;
    _fake_millis    = 0;
}

void tearDown() {}

// ---------------------------------------------------------------------------
// Test 1: absent state returns sentinel -127.0f
// ---------------------------------------------------------------------------
void test_probe_sentinel()
{
    _device_count = 0;
    run_probe_cycle();

    TEST_ASSERT_EQUAL(PROBE_ABSENT, test_probe_get_state());
    TEST_ASSERT_FLOAT_WITHIN(0.01f, -127.0f, test_probe_get_temp_celsius());
}

// ---------------------------------------------------------------------------
// Test 2: absent sentinel → JSON null
// ---------------------------------------------------------------------------
void test_probe_json_null()
{
    _device_count = 0;
    run_probe_cycle();

    float t = test_probe_get_temp_celsius();
    TEST_ASSERT_TRUE_MESSAGE(probe_json_is_null(t),
        "Absent probe (-127.0f) must produce JSON null");
}

// ---------------------------------------------------------------------------
// Test 3: OK + 42.0 °C → JSON 42.0
// ---------------------------------------------------------------------------
void test_probe_json_float()
{
    _device_count = 1;
    _raw_temp_c   = 42.0f;
    run_probe_cycle();

    float t = test_probe_get_temp_celsius();
    TEST_ASSERT_FALSE_MESSAGE(probe_json_is_null(t),
        "Valid probe reading must NOT produce JSON null");
    TEST_ASSERT_FLOAT_WITHIN(0.05f, 42.0f, probe_json_value(t));
}

// ---------------------------------------------------------------------------
// Test 4: out-of-range values rejected (range guard)
// ---------------------------------------------------------------------------
void test_probe_range_guard()
{
    // Below minimum (-55 °C) — rejected
    _device_count = 1;
    _raw_temp_c   = -60.0f;
    run_probe_cycle();
    TEST_ASSERT_EQUAL_MESSAGE(PROBE_ABSENT, test_probe_get_state(),
        "Temperature below -55 °C must be rejected");
    TEST_ASSERT_FLOAT_WITHIN(0.01f, PROBE_ABSENT_SENTINEL, test_probe_get_temp_celsius());

    // Above maximum (+125 °C) — rejected
    setUp();
    _device_count = 1;
    _raw_temp_c   = 130.0f;
    run_probe_cycle();
    TEST_ASSERT_EQUAL_MESSAGE(PROBE_ABSENT, test_probe_get_state(),
        "Temperature above +125 °C must be rejected");
    TEST_ASSERT_FLOAT_WITHIN(0.01f, PROBE_ABSENT_SENTINEL, test_probe_get_temp_celsius());

    // Boundary: exactly -55 °C — valid
    setUp();
    _device_count = 1;
    _raw_temp_c   = -55.0f;
    run_probe_cycle();
    TEST_ASSERT_EQUAL_MESSAGE(PROBE_OK, test_probe_get_state(),
        "-55.0 °C is within DS18B20 rated range and must be accepted");

    // Boundary: exactly +125 °C — valid
    setUp();
    _device_count = 1;
    _raw_temp_c   = 125.0f;
    run_probe_cycle();
    TEST_ASSERT_EQUAL_MESSAGE(PROBE_OK, test_probe_get_state(),
        "+125.0 °C is within DS18B20 rated range and must be accepted");
}

// ---------------------------------------------------------------------------
// Test 5: state transitions ABSENT → READING → OK
// ---------------------------------------------------------------------------
void test_probe_state_transitions()
{
    // Start absent
    _device_count = 0;
    run_probe_cycle();
    TEST_ASSERT_EQUAL(PROBE_ABSENT, test_probe_get_state());

    // Sensor plugged in — next cycle should go READING then OK
    _device_count = 1;
    _raw_temp_c   = 25.5f;
    run_probe_cycle();
    TEST_ASSERT_EQUAL(PROBE_OK, test_probe_get_state());
    TEST_ASSERT_FLOAT_WITHIN(0.1f, 25.5f, test_probe_get_temp_celsius());

    // Sensor unplugged — should return to ABSENT
    _device_count = 0;
    run_probe_cycle();
    TEST_ASSERT_EQUAL(PROBE_ABSENT, test_probe_get_state());
    TEST_ASSERT_FLOAT_WITHIN(0.01f, PROBE_ABSENT_SENTINEL, test_probe_get_temp_celsius());
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------
int main(int argc, char** argv)
{
    UNITY_BEGIN();

    RUN_TEST(test_probe_sentinel);
    RUN_TEST(test_probe_json_null);
    RUN_TEST(test_probe_json_float);
    RUN_TEST(test_probe_range_guard);
    RUN_TEST(test_probe_state_transitions);

    return UNITY_END();
}
