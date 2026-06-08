/**
 * @file test_pins.cpp
 * @brief Unit tests: GPIO pin constant correctness and collision check.
 *
 * Verifies all 13 GPIO constants from architecture.md §4 match expected values,
 * and that no two functions share the same GPIO number.
 *
 * Run: pio test -e native
 */
#include <unity.h>
#include "pins.h"

// ---------------------------------------------------------------------------
// Individual constant checks
// ---------------------------------------------------------------------------
void test_fan_pwm_pins()
{
    TEST_ASSERT_EQUAL(4,  FAN1_PWM_PIN);
    TEST_ASSERT_EQUAL(5,  FAN2_PWM_PIN);
    TEST_ASSERT_EQUAL(6,  FAN3_PWM_PIN);
    TEST_ASSERT_EQUAL(7,  FAN4_PWM_PIN);
}

void test_fan_tach_pins()
{
    TEST_ASSERT_EQUAL(8,  FAN1_TACH_PIN);
    TEST_ASSERT_EQUAL(9,  FAN2_TACH_PIN);
    TEST_ASSERT_EQUAL(10, FAN3_TACH_PIN);
    TEST_ASSERT_EQUAL(11, FAN4_TACH_PIN);
}

void test_adc_and_misc_pins()
{
    TEST_ASSERT_EQUAL(16, NTC_ADC_PIN);
    TEST_ASSERT_EQUAL(2,  STATUS_LED_PIN);
    TEST_ASSERT_EQUAL(15, PROG_LED_PIN);
    TEST_ASSERT_EQUAL(0,  BOOT_PIN);
}

void test_eth_management_pins()
{
    TEST_ASSERT_EQUAL(52, ETH_MDIO_PIN);
    TEST_ASSERT_EQUAL(31, ETH_MDC_PIN);
    TEST_ASSERT_EQUAL(51, ETH_PHY_RST_PIN);
}

// ---------------------------------------------------------------------------
// No-collision check: all 13 defined pins must be unique
// ---------------------------------------------------------------------------
void test_no_gpio_collisions()
{
    const int pins[] = {
        FAN1_PWM_PIN,  FAN2_PWM_PIN,  FAN3_PWM_PIN,  FAN4_PWM_PIN,
        FAN1_TACH_PIN, FAN2_TACH_PIN, FAN3_TACH_PIN, FAN4_TACH_PIN,
        NTC_ADC_PIN,   STATUS_LED_PIN, PROG_LED_PIN,  BOOT_PIN,
        ETH_MDIO_PIN,  ETH_MDC_PIN,   ETH_PHY_RST_PIN,
    };
    const int N = sizeof(pins) / sizeof(pins[0]);

    for (int i = 0; i < N; i++) {
        for (int j = i + 1; j < N; j++) {
            TEST_ASSERT_NOT_EQUAL_MESSAGE(pins[i], pins[j],
                "GPIO collision detected between two pin constants");
        }
    }
}

// ---------------------------------------------------------------------------
// RMII forbidden zone: none of the defined pins may fall in GPIO32-37 or GPIO50
// (those are fixed RMII pins, must never be reassigned)
// ---------------------------------------------------------------------------
void test_no_rmii_collision()
{
    const int rmii_fixed[] = { 32, 33, 34, 35, 36, 37, 50 };
    const int user_pins[]  = {
        FAN1_PWM_PIN,  FAN2_PWM_PIN,  FAN3_PWM_PIN,  FAN4_PWM_PIN,
        FAN1_TACH_PIN, FAN2_TACH_PIN, FAN3_TACH_PIN, FAN4_TACH_PIN,
        NTC_ADC_PIN,   STATUS_LED_PIN, PROG_LED_PIN,  BOOT_PIN,
        ETH_MDIO_PIN,  ETH_MDC_PIN,   ETH_PHY_RST_PIN,
    };

    for (int u = 0; u < (int)(sizeof(user_pins)/sizeof(user_pins[0])); u++) {
        for (int r = 0; r < (int)(sizeof(rmii_fixed)/sizeof(rmii_fixed[0])); r++) {
            TEST_ASSERT_NOT_EQUAL_MESSAGE(user_pins[u], rmii_fixed[r],
                "User GPIO conflicts with RMII fixed IO_MUX pin");
        }
    }
}

// ---------------------------------------------------------------------------
// PWM parameter checks
// ---------------------------------------------------------------------------
void test_fan_pwm_params()
{
    TEST_ASSERT_EQUAL(25000, FAN_PWM_FREQ_HZ);
    TEST_ASSERT_EQUAL(8,     FAN_PWM_RESOLUTION);
    TEST_ASSERT_EQUAL(255,   FAN_PWM_SAFE_DEFAULT);
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------
void setUp()    {}
void tearDown() {}

int main(int argc, char** argv)
{
    UNITY_BEGIN();

    RUN_TEST(test_fan_pwm_pins);
    RUN_TEST(test_fan_tach_pins);
    RUN_TEST(test_adc_and_misc_pins);
    RUN_TEST(test_eth_management_pins);
    RUN_TEST(test_no_gpio_collisions);
    RUN_TEST(test_no_rmii_collision);
    RUN_TEST(test_fan_pwm_params);

    return UNITY_END();
}
