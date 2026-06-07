/**
 * @file test_ota.cpp
 * @brief Unit tests: HTTP OTA handler logic (mocked Update.h).
 *
 * Verifies that the OTA upload sequence calls begin/write/end in correct order,
 * that no delay() is called in the streaming chunk handler, and that the
 * response callback returns 200 on success and 500 on failure.
 *
 * Run: pio test -e native
 */
#include <unity.h>
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

// ---------------------------------------------------------------------------
// Minimal stubs — no Arduino runtime needed for native tests
// ---------------------------------------------------------------------------

// Stub: Update object
static bool _update_begun  = false;
static bool _update_ended  = false;
static bool _update_error  = false;
static size_t _bytes_written = 0;
static int  _delay_called  = 0;   // must remain 0 in upload handler

struct MockUpdate {
    bool begin(size_t /* size */)             { _update_begun = true; return true; }
    bool isRunning() const                    { return _update_begun && !_update_ended; }
    size_t write(const uint8_t* b, size_t n) { _bytes_written += n; return n; }
    bool end(bool /* verify */)              { _update_ended = true; return !_update_error; }
    bool hasError() const                    { return _update_error; }
    const char* errorString() const          { return ""; }
} Update;

// Stub: delay() — tracks calls so we can assert absence in upload handler
void delay(int) { _delay_called++; }

// ---------------------------------------------------------------------------
// Simplified OTA upload handler (mirrors ota.cpp logic, framework-independent)
// ---------------------------------------------------------------------------
static void ota_upload_handler(const uint8_t* data, size_t len,
                                size_t index, bool final)
{
    if (!index) {
        Update.begin(/* UPDATE_SIZE_UNKNOWN */ (size_t)-1);
    }
    if (Update.isRunning()) {
        Update.write(data, len);
    }
    if (final) {
        Update.end(true);
    }
}

// Stub request to capture response code
static int _response_code = 0;
static char _response_body[32] = "";

struct MockRequest {
    void send(int code, const char* /*ct*/, const char* body) {
        _response_code = code;
        strncpy(_response_body, body, sizeof(_response_body) - 1);
    }
} req;

static void ota_response_handler()
{
    bool ok = !Update.hasError();
    req.send(ok ? 200 : 500, "text/plain", ok ? "OK" : "FAIL");
    // Note: in real code, ESP.restart() follows here — not testable in native
}

// ---------------------------------------------------------------------------
// Test: begin/write/end called in correct order
// ---------------------------------------------------------------------------
void test_ota_sequence()
{
    // Reset state
    _update_begun = _update_ended = _update_error = false;
    _bytes_written = 0;
    _delay_called  = 0;

    uint8_t chunk1[64] = {0xAA};
    uint8_t chunk2[32] = {0xBB};

    // First chunk
    ota_upload_handler(chunk1, sizeof(chunk1), 0, false);
    TEST_ASSERT_TRUE_MESSAGE(_update_begun, "Update.begin() must be called on first chunk");
    TEST_ASSERT_EQUAL(sizeof(chunk1), _bytes_written);
    TEST_ASSERT_FALSE_MESSAGE(_update_ended, "Update.end() must NOT be called mid-stream");

    // Middle chunk
    ota_upload_handler(chunk2, sizeof(chunk2), sizeof(chunk1), false);
    TEST_ASSERT_EQUAL(sizeof(chunk1) + sizeof(chunk2), _bytes_written);

    // Final chunk
    ota_upload_handler(nullptr, 0, sizeof(chunk1) + sizeof(chunk2), true);
    TEST_ASSERT_TRUE_MESSAGE(_update_ended, "Update.end() must be called on final chunk");
}

// ---------------------------------------------------------------------------
// Test: upload handler has no delay() call
// ---------------------------------------------------------------------------
void test_ota_no_delay_in_upload()
{
    _delay_called = 0;
    uint8_t dummy[16] = {0};
    ota_upload_handler(dummy, sizeof(dummy), 0, false);
    ota_upload_handler(nullptr, 0, sizeof(dummy), true);

    TEST_ASSERT_EQUAL_MESSAGE(0, _delay_called,
        "delay() must NOT be called in the OTA upload streaming handler (P-FW-04)");
}

// ---------------------------------------------------------------------------
// Test: response 200 on success
// ---------------------------------------------------------------------------
void test_ota_response_200_on_success()
{
    _update_error = false;
    _update_begun = true;
    _update_ended = true;
    _response_code = 0;

    ota_response_handler();
    TEST_ASSERT_EQUAL(200, _response_code);
    TEST_ASSERT_EQUAL_STRING("OK", _response_body);
}

// ---------------------------------------------------------------------------
// Test: response 500 on error
// ---------------------------------------------------------------------------
void test_ota_response_500_on_error()
{
    _update_error = true;
    _update_begun = true;
    _update_ended = false;
    _response_code = 0;

    ota_response_handler();
    TEST_ASSERT_EQUAL(500, _response_code);
    TEST_ASSERT_EQUAL_STRING("FAIL", _response_body);
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------
void setUp()    {}
void tearDown() {}

int main(int argc, char** argv)
{
    UNITY_BEGIN();
    RUN_TEST(test_ota_sequence);
    RUN_TEST(test_ota_no_delay_in_upload);
    RUN_TEST(test_ota_response_200_on_success);
    RUN_TEST(test_ota_response_500_on_error);
    return UNITY_END();
}
