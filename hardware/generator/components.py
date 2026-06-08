"""
generator.components — build_schematic() for PoE FanController v0.4.

Daughter board design: custom PCB is a daughter board that stacks underneath the
Waveshare ESP32-P4-POE-ETH (SKU 32088). The Waveshare board handles PoE PD,
Ethernet PHY, RJ45, and ESP32-P4 — all via a single 802.3at Ethernet cable.
No PoE circuitry on the daughter board (NFR-S-01: SELV-only domain).

The daughter board stacks below the Waveshare board via J8 (2×20 female PinSocket
header) that receives +5V and GPIO signals from the Waveshare board's male header.

Daughter board provides:
  - J8      2×20 female header (PinSocket_2x20_P2.54mm_Vertical) receiving +5V
            and GPIO signals from Waveshare ESP32-P4-POE-ETH (SKU 32088)
  - U_BOOST 5V→12V boost converter (TI LM2587-12, TO-220-3)
  - J2–J5   4-pin fan headers (12V PWM, side-edge placement)
  - R5–R8   TACH pull-up resistors (10kΩ to 3.3V from Waveshare via J8)
  - R4/NTC1 NTC temperature sensing (10kΩ NTC + 10kΩ divider)
  - R3/LED1 status LED circuit (GPIO2 via J8)

Power chain:
  J8 pins 2,4 (+5V from Waveshare ESP32-P4-POE-ETH PoE PD module)
    → U_BOOST (TI LM2587-12, 5V → 12V boost converter)
      → +12V rail → fans J2–J5
  J8 pins 1,17 (+3V3 from Waveshare on-board LDO)
    → TACH pull-ups R5–R8
    → NTC voltage divider R4

NOTE — OQ-02 PENDING: Confirm +5V on J8 pins 2,4 from Waveshare SKU 32088 schematic.
NOTE — OQ-03 PENDING: Confirm GPIO4-7/8-11/16/2 positions on SKU 32088 header.

Pin position formula (angle=0):
  left  pin i: x = cx - hw - pin_len,  y = cy + hh - 1.27 - i*2.54
  right pin i: x = cx + hw + pin_len,  y = cy + hh - 1.27 - i*2.54
where hw = body_w/2, hh = body_h/2, pin_len = 2.54 mm
"""

from .schematic import Schematic
from .utils import G


def build_schematic():
    """Build and return the complete Schematic object for PoE-FanController daughter board."""
    s = Schematic()

    # -----------------------------------------------------------------------
    # Symbol definitions  (body_w, body_h MUST be multiples of G=2.54)
    # -----------------------------------------------------------------------

    # 5V→12V boost converter (TI LM2587-12, or equivalent fixed-12V boost)
    # Generic 3-terminal representation: VIN/GND (left), VOUT (right).
    # Real circuit needs external catch diode + inductor + output cap (on PCB).
    # Footprint: TO-220-3_Vertical — update to actual package when MPN confirmed.
    s.define("Custom:Boost_Converter", "U", "LM2587-12",
             "Package_TO_SOT_THT:TO-220-3_Vertical",
             "https://www.ti.com/lit/ds/symlink/lm2587.pdf",
             body_w=10.16, body_h=7.62,
             pins_left=[
                 ("VIN",  "1", "power_in"),
                 ("GND",  "2", "power_in"),
             ],
             pins_right=[
                 ("VOUT", "3", "power_out"),
             ])

    # Waveshare ESP32-P4-POE-ETH (SKU 32088) 2×20 female interface header (J8).
    # Female PinSocket — daughter board sits below Waveshare board; Waveshare male
    # header pins plug into J8 socket.
    # OQ-02 PENDING: Confirm +5V on pins 2,4 from Waveshare SKU 32088 schematic PDF.
    # OQ-03 PENDING: Confirm GPIO4-7/8-11/16/2 on SKU 32088 header at stated positions.
    # body_w = 10 * 2.54 = 25.4 mm, body_h = 20 * 2.54 = 50.8 mm
    s.define("Custom:J8_Waveshare", "J", "Waveshare_ESP32P4POEETH",
             "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical",
             "https://www.waveshare.com/wiki/ESP32-P4-POE-ETH",
             body_w=25.4, body_h=50.8,
             pins_left=[
                 # Odd pads: 1,3,5,...,39  (top-to-bottom)
                 ("+3V3_OUT",   "1",  "power_out"),     # 3.3V from Waveshare LDO
                 ("STATUS_LED", "3",  "bidirectional"),  # GPIO2 — status LED
                 ("NC",         "5",  "no_connect"),     # GPIO3
                 ("FAN1_PWM",   "7",  "output"),         # GPIO4 LEDC CH0
                 ("GND",        "9",  "passive"),
                 ("FAN4_PWM",   "11", "output"),         # GPIO7 LEDC CH3
                 ("FAN2_TACH",  "13", "input"),          # GPIO9 tach input
                 ("FAN3_TACH",  "15", "input"),          # GPIO10 tach input
                 ("+3V3_OUT",   "17", "power_out"),      # 3.3V duplicate from Waveshare
                 ("NC",         "19", "no_connect"),     # GPIO13
                 ("NC",         "21", "no_connect"),     # GPIO14
                 ("NTC_ADC",    "23", "input"),          # GPIO16 ADC
                 ("GND",        "25", "passive"),
                 ("NC",         "27", "no_connect"),     # GPIO19
                 ("GND",        "29", "passive"),
                 ("NC",         "31", "no_connect"),     # GPIO22
                 ("GND",        "33", "passive"),
                 ("NC",         "35", "no_connect"),     # GPIO28 ETH_MDIO (NC on header)
                 ("NC",         "37", "no_connect"),     # GPIO29
                 ("NC",         "39", "no_connect"),     # VSYS
             ],
             pins_right=[
                 # Even pads: 2,4,6,...,40  (top-to-bottom)
                 # Pins 2,4: +5V from Waveshare PoE PD module → U_BOOST input
                 ("+5V_IN",  "2",  "power_out"),         # +5V from Waveshare
                 ("+5V_IN",  "4",  "power_out"),         # +5V duplicate
                 ("GND",     "6",  "passive"),
                 ("FAN2_PWM",   "8",  "output"),         # GPIO5 LEDC CH1
                 ("FAN3_PWM",   "10", "output"),         # GPIO6 LEDC CH2
                 ("FAN1_TACH",  "12", "input"),          # GPIO8 tach input
                 ("GND",        "14", "passive"),
                 ("FAN4_TACH",  "16", "input"),          # GPIO11 tach input
                 ("NC",         "18", "no_connect"),     # GPIO12
                 ("GND",        "20", "passive"),
                 ("NC",         "22", "no_connect"),     # GPIO15
                 ("NC",         "24", "no_connect"),     # GPIO17
                 ("NC",         "26", "no_connect"),     # GPIO18
                 ("NC",         "28", "no_connect"),     # GPIO20
                 ("NC",         "30", "no_connect"),     # GPIO21
                 ("NC",         "32", "no_connect"),     # GPIO26
                 ("NC",         "34", "no_connect"),     # GPIO27
                 ("NC",         "36", "no_connect"),     # 3V3_EN/RUN
                 ("GND",        "38", "passive"),
                 ("NC",         "40", "no_connect"),     # VBUS
             ])

    # 4-pin fan header (J2–J5)
    s.define("Custom:Fan_Header", "J", "Fan_Header",
             "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "~",
             body_w=10.16, body_h=12.70,
             pins_left=[
                 ("GND",     "1", "passive"),
                 ("VCC_FAN", "2", "power_in"),
                 ("TACH",    "3", "output"),
                 ("PWM",     "4", "input"),
             ],
             pins_right=[])

    # Generic passive 2-terminal resistor
    s.define("Custom:R", "R", "R",
             "Resistor_SMD:R_0402_1005Metric", "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("~", "1", "passive")],
             pins_right=[("~", "2", "passive")])

    s.define("Custom:LED", "LED", "LED",
             "LED_THT:LED_D3.0mm", "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("A", "1", "passive")],
             pins_right=[("K", "2", "passive")])

    s.define("Custom:NTC", "NTC", "NTC_10K",
             "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("1", "1", "passive")],
             pins_right=[("2", "2", "passive")])

    # -----------------------------------------------------------------------
    # Component placement
    #
    # All centres on 2.54 mm (G) grid.  Functional block regions on A2 sheet:
    #   BOOST   : x=170..250,  y=60..100   — 5V→12V converter
    #   FANS    : x=300..420,  y=25..320   — fan headers J2–J5 + TACH pull-ups
    #   LED_NTC : x=130..230,  y=190..280  — status LED + NTC temperature circuit
    #   J8_IFACE: x=25..200,   y=290..410  — Waveshare interface header
    #
    # Spacing rule (T3): functional blocks ≥ 30 mm apart (edge to edge).
    # -----------------------------------------------------------------------

    BLUE = (0, 0, 255)

    # -----------------------------------------------------------------------
    # U_BOOST – 5V→12V boost converter (TI LM2587-12)
    # Input: +5V from J8 pins 2,4 (Waveshare PoE PD module)
    # Output: +12V rail → fan headers J2–J5
    # -----------------------------------------------------------------------
    s.text("5V→12V Boost Converter (U_BOOST)", 155, 48, size=2.54, bold=True, color=BLUE)
    BOOST_CX, BOOST_CY = 205.74, 76.2      # 81*G, 30*G
    p = s.component("Custom:Boost_Converter", "U_BOOST", "LM2587-12",
                    "Package_TO_SOT_THT:TO-220-3_Vertical",
                    BOOST_CX, BOOST_CY)
    # VIN (pin 1, left): connect to +5V rail supplied by J8
    s.power("+5V",  *p["1"])
    # GND (pin 2, left): connect to GND
    s.power("GND",  *p["2"])
    # VOUT (pin 3, right): drives +12V rail for all fans
    s.power("+12V", *p["3"], pin_type="power_out")

    # -----------------------------------------------------------------------
    # Status LED circuit (R3, LED1) — STATUS_LED signal from J8 pin 3 (GPIO2)
    # Spaced ≥ 30 mm below U_BOOST block (BOOST bottom ≈ 80mm, LED top ≈ 198mm)
    # -----------------------------------------------------------------------
    s.text("Status LED", 130, 188, size=2.54, bold=True, color=BLUE)
    R3_CX, R3_CY = 167.64, 205.74      # 66*G, 81*G
    p1 = s.component("Custom:R", "R3", "330R", "Resistor_SMD:R_0402_1005Metric",
                     R3_CX, R3_CY)
    s.global_label("STATUS_LED", *p1["1"], shape="input")
    s.label("LED_A", *p1["2"])

    LED1_CX = R3_CX + 3 * G
    LED1_CY = R3_CY
    p1 = s.component("Custom:LED", "LED1", "LED_GREEN", "LED_THT:LED_D3.0mm",
                     LED1_CX, LED1_CY)
    s.label("LED_A", *p1["1"])
    s.power("GND",   *p1["2"])

    # -----------------------------------------------------------------------
    # NTC temperature sensor circuit (R4, NTC1) — NTC_ADC from J8 pin 23 (GPIO16)
    # Spaced ≥ 30 mm below Status LED block (LED bottom ≈ 207mm, NTC top ≈ 240mm)
    # -----------------------------------------------------------------------
    s.text("NTC Temperature Sensor", 130, 238, size=2.54, bold=True, color=BLUE)
    R4_CX, R4_CY = 167.64, 254.0       # 66*G, 100*G
    p1 = s.component("Custom:R", "R4", "10k", "Resistor_SMD:R_0402_1005Metric",
                     R4_CX, R4_CY)
    s.power("+3V3",    *p1["1"])        # +3V3 from J8 pins 1,17 (Waveshare LDO)
    s.global_label("NTC_ADC", *p1["2"], shape="output", angle=180)

    NTC1_CX, NTC1_CY = 167.64, R4_CY + 5 * G
    p1 = s.component("Custom:NTC", "NTC1", "NTC10K_B3950",
                     "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
                     NTC1_CX, NTC1_CY)
    s.global_label("NTC_ADC", *p1["1"], shape="output")
    s.power("GND",     *p1["2"])

    # -----------------------------------------------------------------------
    # Fan headers J2–J5 + TACH pull-up resistors R5–R8
    # Side-edge placement (FR-03): fan headers on right edge of board.
    # Spaced ≥ 30 mm from J8 block (J8 right edge ≈ 114mm, TACH pull-ups at 254mm)
    # -----------------------------------------------------------------------
    s.text("Fan Headers (4× 12V PWM)", 300, 18, size=2.54, bold=True, color=BLUE)

    fan_data = [
        ("FAN1_PWM", "FAN1_TACH"),
        ("FAN2_PWM", "FAN2_TACH"),
        ("FAN3_PWM", "FAN3_TACH"),
        ("FAN4_PWM", "FAN4_TACH"),
    ]

    for i, (pwm_net, tach_net) in enumerate(fan_data):
        FJ_CX = 381.0    # 150*G — right section
        FJ_CY = 35.56 + i * 40 * G   # well-spaced vertically (≥30mm gap between headers)

        # Fan header
        p = s.component("Custom:Fan_Header", f"J{2+i}", f"FAN{i+1}",
                        "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
                        FJ_CX, FJ_CY)
        s.power("GND",   *p["1"])
        s.power("+12V",  *p["2"])
        s.global_label(tach_net, *p["3"], shape="output")
        s.global_label(pwm_net,  *p["4"], shape="input")

        # TACH pull-up resistor (R5–R8): +3V3 from J8 → TACH pin
        FR_CX = FJ_CX - 30 * G
        FR_CY = p["3"][1]   # same y as TACH pin
        pr = s.component("Custom:R", f"R{5+i}", "10k",
                         "Resistor_SMD:R_0402_1005Metric", FR_CX, FR_CY)
        s.power("+3V3",          *pr["1"])
        s.global_label(tach_net, *pr["2"], shape="output")

    # -----------------------------------------------------------------------
    # J8 – Waveshare ESP32-P4-POE-ETH Interface (2×20 female PinSocket)
    # Waveshare board (SKU 32088) sits on top; its 2×20 male pins plug into J8.
    # J8 pins 2,4: +5V from Waveshare PoE PD → U_BOOST VIN (FR-04)
    # J8 pins 1,17: +3V3 from Waveshare LDO → TACH pull-ups + NTC divider
    # GPIO signals: FAN1-4 PWM/TACH (output/input), NTC_ADC, STATUS_LED (FR-09)
    # NOTE: GPIO28 (pin 35) = ETH_MDIO internal to Waveshare — not connected here
    # NOTE: UART0 (GPIO38/39) via Waveshare CH343P USB-C — not on J8 header
    # -----------------------------------------------------------------------
    s.text("Waveshare ESP32-P4-POE-ETH Interface (J8)", 25, 278, size=2.54, bold=True, color=BLUE)
    J8_CX, J8_CY = 101.6, 355.6        # 40*G, 140*G — lower section
    p = s.component("Custom:J8_Waveshare", "J8", "Waveshare_ESP32P4POEETH",
                    "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical",
                    J8_CX, J8_CY)

    # Power rails — Waveshare +3V3 LDO drives +3V3 net on daughter board
    s.power("+3V3", *p["1"],  pin_type="power_out")   # 3V3 from Waveshare LDO (pin 1)
    s.power("+3V3", *p["17"], pin_type="power_out")   # 3V3 duplicate (pin 17)

    # Power rails — +5V from Waveshare PoE PD module enters via pins 2,4 → U_BOOST
    s.power("+5V", *p["2"])     # +5V from Waveshare (drives +5V net)
    s.power("+5V", *p["4"])     # +5V duplicate

    # GND connections for all GND pins on J8
    s.power("GND", *p["6"])
    s.power("GND", *p["9"])
    s.power("GND", *p["14"])
    s.power("GND", *p["20"])
    s.power("GND", *p["25"])
    s.power("GND", *p["29"])
    s.power("GND", *p["33"])
    s.power("GND", *p["38"])

    # Fan PWM outputs (from Waveshare GPIO → fan headers on daughter board)
    s.global_label("FAN1_PWM",  *p["7"],  shape="output")
    s.global_label("FAN2_PWM",  *p["8"],  shape="output")
    s.global_label("FAN3_PWM",  *p["10"], shape="output")
    s.global_label("FAN4_PWM",  *p["11"], shape="output")

    # Fan TACH inputs (from fan headers on daughter board → Waveshare GPIO)
    s.global_label("FAN1_TACH", *p["12"], shape="input")
    s.global_label("FAN2_TACH", *p["13"], shape="input")
    s.global_label("FAN3_TACH", *p["15"], shape="input")
    s.global_label("FAN4_TACH", *p["16"], shape="input")

    # Temperature ADC (from NTC circuit on daughter board → Waveshare GPIO16)
    s.global_label("NTC_ADC",    *p["23"], shape="input")

    # Status LED (from Waveshare GPIO2 → LED circuit on daughter board)
    s.global_label("STATUS_LED", *p["3"],  shape="output")

    return s
