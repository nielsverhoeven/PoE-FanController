"""
generator.components — build_schematic() for PoE FanController v0.6.

Signal assignments (user-specified overhaul):
  Left column (pins 1-20, bottom→top on physical board):
    Pin 6  → DS18B20_DATA (GPIO2, 1-Wire probe data)
    Pin 10 → PROBE_LED    (GPIO5, probe health LED)
    Pin 11 → DHT11_DATA   (GPIO6, DHT11 single-wire)
    Pin 16 → PROG_LED     (GPIO17, OTA/write indicator)
    Pin 17 → PWR_LED      (GPIO18, power-on status LED)
    Pins 3,8,13,18 → GND
    All others → NC

  Right column (pins 21-40, bottom→top on physical board):
    Pin 21 → FAN4_PWM  (GPIO48)
    Pin 22 → FAN4_TACH (GPIO47)
    Pin 24 → FAN3_PWM  (GPIO46)
    Pin 25 → FAN3_TACH (GPIO33)
    Pin 31 → FAN2_PWM  (GPIO23)
    Pin 32 → FAN2_TACH (GPIO22)
    Pin 34 → FAN1_PWM  (GPIO21)
    Pin 35 → FAN1_TACH (GPIO20)
    Pin 36 → +3V3 (SOLE source for pull-ups and sensor VCC)
    Pin 40 → VBUS (+5V, boost converter input)
    Pins 23,28,33,38 → GND
    All others → NC

Power chain:
  J8 pin 40 (VBUS) — +5V to L1/U1 boost converter input
  U1 (LM2587-12) → +12V rail → J2-J5 fan headers VCC
  J8 pin 36 (+3V3) — pull-ups R5(FAN1), R7(FAN3), R8(FAN4); DS18B20 R14; DHT11 VCC
"""

from .schematic import Schematic
from .utils import G


def build_schematic():
    """Build and return the complete Schematic object for PoE-FanController daughter board."""
    s = Schematic()

    # -----------------------------------------------------------------------
    # Symbol definitions  (body_w, body_h MUST be multiples of G=2.54)
    # -----------------------------------------------------------------------

    # 5V->12V boost converter (TI LM2587-12 fixed 12V, TO-220-5).
    # Pin 1=GND, Pin 2=VIN, Pin 3=OUTPUT (SW switching node), Pin 4=FB, Pin 5=OSC.
    # For fixed-12V: FB tied to OUTPUT; OSC bypassed with cap to GND (see datasheet).
    # External circuit: +5V->L1->SW, SW->D1->+12V, C1:+5V/GND, C2:+12V/GND.
    s.define("Custom:Boost_Converter", "U", "LM2587-12",
             "Package_TO_SOT_THT:TO-220-5_Vertical",
             "https://www.ti.com/lit/ds/symlink/lm2587.pdf",
             body_w=10.16, body_h=12.70,
             pins_left=[
                 ("GND", "1", "power_in"),
                 ("VIN", "2", "power_in"),
             ],
             pins_right=[
                 ("OUTPUT", "3", "output"),
                 ("FB",     "4", "input"),
                 ("OSC",    "5", "input"),
             ])

    # Catch inductor L1 — 100 µH, connects +5V to BOOST_SW switching node.
    s.define("Custom:Inductor", "L", "100uH",
             "Inductor_THT:L_Axial_L7.0mm_D3.3mm_P10.16mm_Horizontal_Fastron_MICC",
             "~",
             body_w=7.62, body_h=2.54,
             pins_left=[("~",  "1", "passive")],
             pins_right=[("~", "2", "passive")])

    # Schottky catch diode D1 — 1N5822 (40V/3A, DO-27 axial through-hole),
    # BOOST_SW node to +12V output rail. Replaces SS54 SMA for hand-soldering.
    s.define("Custom:Diode_Schottky", "D", "1N5822",
             "Diode_THT:D_DO-27_P12.70mm_Horizontal",
             "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("A", "1", "passive")],
             pins_right=[("K", "2", "passive")])

    # Electrolytic bypass/filter capacitor — 100 µF / 25 V radial.
    # Used for C1 (+5V input bypass) and C2 (+12V output filter).
    s.define("Custom:Cap_Elec", "C", "100uF_25V",
             "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
             "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("~",  "1", "passive")],
             pins_right=[("~", "2", "passive")])

    # Waveshare ESP32-P4-POE-ETH (SKU 32088) 2x20 female interface header (J8).
    # Female PinSocket — daughter board sits below Waveshare board; Waveshare
    # 2x20 male header pins plug into this socket.
    #
    # CRITICAL: row spacing is 15.38mm (NOT standard 2.54mm).
    # Source: docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-details-size-*.webp
    # Board dimensions confirmed: 78.00 x 21.00 mm; pin pitch 2.54mm, row-to-row 15.38mm.
    # Custom footprint: Custom:ESP32-P4-PoE-ETH-PinSocket (in Custom.pretty)
    #
    # PIN LAYOUT (issue #133): CONSECUTIVE column numbering — NOT alternating/PICO style.
    #   Row A (near edge, 2.81mm from long edge):  pins  1..20  (bottom → top on physical board)
    #   Row B (far edge, 18.19mm from same edge):  pins 21..40  (bottom → top on physical board)
    #
    # CORRECTED ASSIGNMENTS (issue #148 — architecture validation v4.2.1):
    #   Left col  (Row A, pins  1-20): GND on 3,8,13,18;
    #             STATUS_LED/GPIO2 on pin 6; PROG_LED/GPIO15 on pin 14;
    #             DHT11_DATA/GPIO16 on pin 15; DS18B20_DATA/GPIO19 on pin 19.
    #             All others NC.
    #   Right col (Row B, pins 21-40): ALL 8 fan signals here (GPIO20-23,26,27,46,47);
    #             PROBE_LED/GPIO48 on pin 21; +3V3 output on pin 36; +5V/VBUS on pin 40.
    #             FORBIDDEN: pins 25,26 = GPIO33/32 = EMAC_RXD1/RXD0 — left NC.
    #             Reserved: pin 37 = EN, pin 30 = RUN — left NC.
    #
    # SIGNAL ASSIGNMENTS (user overhaul v0.6):
    #   Left col (pins 20→1, TOP→BOTTOM):
    #     Pin 17 → PWR_LED (GPIO18), Pin 16 → PROG_LED (GPIO17)
    #     Pin 14 → DHT11_DATA (GPIO15)
    #     Pin 7  → PROBE_LED (GPIO3),  Pin 6  → DS18B20_DATA (GPIO2)
    #     Pins 3,8,13,18 → GND; all others NC
    #   Right col (pins 40→21, TOP→BOTTOM):
    #     Pin 40 → +5V/VBUS, Pin 36 → +3V3
    #     Pin 34 → FAN1_TACH (GPIO21), Pin 32 → FAN2_PWM (GPIO22)
    #     Pin 27 → FAN3_PWM (GPIO27),  Pin 26 → FAN3_TACH (GPIO32) [EMAC—verify]
    #     Pin 22 → FAN4_PWM (GPIO47),  Pin 21 → FAN4_TACH (GPIO48)
    #     Pins 23,28,33,38 → GND; pins 25,30,37,39 → NC; others NC
    s.define("Custom:J8_Waveshare", "J", "Waveshare_ESP32P4POEETH",
             "Custom:ESP32-P4-PoE-ETH-PinSocket",
             "https://www.waveshare.com/wiki/ESP32-P4-POE-ETH",
             body_w=25.4, body_h=50.8,
             pins_left=[
                 # Pins 20..1, Row A — TOP → BOTTOM (matches physical board orientation)
                 ("NC",           "20", "no_connect"),    # GPIO54   — top-left
                 ("NC",           "19", "no_connect"),    # GPIO19   — NC (was DS18B20)
                 ("GND",          "18", "passive"),       # Physical GND
                 ("PWR_LED",      "17", "output"),        # GPIO18   — power-on status LED
                 ("PROG_LED",     "16", "output"),        # GPIO17   — OTA/write LED
                 ("NC",           "15", "no_connect"),    # GPIO16   — NC (was DHT11)
                 ("NC",           "14", "no_connect"),    # GPIO15   — NC (was DHT11)
                 ("GND",          "13", "passive"),       # Physical GND
                 ("NC",           "12", "no_connect"),    # GPIO14   — NC
                 ("DHT11_DATA",   "10", "input"),         # GPIO5    — DHT11 single-wire
                 ("PROBE_LED",    "11", "output"),        # GPIO6    — probe health LED
                 ("NC",           "9",  "no_connect"),    # GPIO4    — NC
                 ("GND",          "8",  "passive"),       # Physical GND
                 ("NC",           "7",  "no_connect"),    # GPIO3    — NC (was PROBE_LED)
                 ("DS18B20_DATA", "6",  "bidirectional"), # GPIO2    — 1-Wire probe data
                 ("NC",           "5",  "no_connect"),    # SCL/GPIO8 — NC
                 ("NC",           "4",  "no_connect"),    # SDA/GPIO7 — NC
                 ("GND",          "3",  "passive"),       # Physical GND
                 ("NC",           "2",  "no_connect"),    # DM/GPIO24 — NC
                 ("NC",           "1",  "no_connect"),    # DP/GPIO25 — bottom-left
             ],
             pins_right=[
                 # Pins 40..21, Row B — TOP → BOTTOM (matches physical board orientation)
                 ("+5V",          "40", "power_out"),     # VBUS     — top-right (+5V for boost)
                 ("NC",           "39", "no_connect"),    # VSYS     — do NOT use
                 ("GND",          "38", "passive"),       # Physical GND
                 ("NC",           "37", "no_connect"),    # EN       — chip-enable RESERVED
                 ("+3V3",         "36", "power_out"),     # +3V3     — SOLE 3.3V source
                 ("FAN1_TACH",    "34", "input"),          # GPIO21   — FAN1 tach IRQ
                 ("FAN1_PWM",     "35", "output"),        # GPIO20   — FAN1 speed control
                 ("GND",          "33", "passive"),       # Physical GND
                 ("FAN2_PWM",     "32", "output"),        # GPIO22   — FAN2 speed control
                 ("FAN2_TACH",    "31", "input"),         # GPIO23   — FAN2 tach IRQ
                 ("NC",           "30", "no_connect"),    # RUN      — system control RESERVED
                 ("NC",           "29", "no_connect"),    # GPIO26   — NC
                 ("GND",          "28", "passive"),       # Physical GND
                 ("FAN3_PWM",     "25", "output"),        # GPIO33   — FAN3 speed control
                 ("FAN3_TACH",    "24", "input"),         # GPIO46   — FAN3 tach IRQ
                 ("NC",           "27", "no_connect"),    # GPIO27   — NC (was FAN3_TACH)
                 ("NC",           "26", "no_connect"),    # GPIO32   — NC (was FAN3_PWM)
                 ("GND",          "23", "passive"),       # Physical GND
                 ("FAN4_PWM",     "22", "output"),        # GPIO47   — FAN4 speed control
                 ("FAN4_TACH",    "21", "input"),         # GPIO48   — FAN4 tach IRQ (bottom-right)
             ])

    # 4-pin fan header (J2-J5) — all pins on LEFT side (connector opens left)
    s.define("Custom:Fan_Header", "J", "Fan_Header",
             "Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical",
             "https://www.molex.com/en-us/products/part-detail/22232041",
             body_w=10.16, body_h=12.70,
             pins_left=[
                 ("GND",     "1", "passive"),
                 ("VCC_FAN", "2", "power_in"),
                 ("TACH",    "3", "output"),
                 ("PWM",     "4", "input"),
             ],
             pins_right=[])

    # Generic passive 2-terminal resistor (pin 1 left, pin 2 right)
    s.define("Custom:R", "R", "R",
             "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal", "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("~",  "1", "passive")],
             pins_right=[("~", "2", "passive")])

    s.define("Custom:LED", "LED", "LED",
             "LED_THT:LED_D3.0mm", "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("A",  "1", "passive")],
             pins_right=[("K", "2", "passive")])

    s.define("Custom:LED_SMD", "D", "LED_GREEN",
             "LED_THT:LED_D3.0mm", "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("A",  "1", "passive")],
             pins_right=[("K", "2", "passive")])

    # DHT11 sensor — custom 3-pin direct-solder footprint (VCC / DATA / GND)
    # Replaces NTC1 + R4 voltage-divider (issue #135, constitution v4.1.0)
    # Pin 1: VCC (3.3 V), Pin 2: DATA (single-wire), Pin 3: GND
    # Footprint: Custom:DHT11_Direct (generated by gen_footprint_dht11.py)
    s.define("Custom:DHT11_Direct", "U", "DHT11_Direct",
             "Custom:DHT11_Direct",
             "https://www.adafruit.com/product/386",
             body_w=10.16, body_h=7.62,
             pins_left=[
                 ("VCC",  "1", "power_in"),
                 ("DATA", "2", "bidirectional"),
                 ("GND",  "3", "power_in"),
             ],
             pins_right=[])

    # 3-pin Molex KK 254 connector — J6 DS18B20 temperature probe header
    # Pin 1: GND, Pin 2: DS18B20_DATA (1-Wire), Pin 3: +3V3 (power to probe)
    # Molex 22-01-3037 / KK-254 3-position housing
    s.define("Custom:Conn_1x03", "J", "Connector_1x03",
             "Connector_Molex:Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical",
             "https://www.molex.com/molex/products/part-detail/crimp_housings/0022013037",
             body_w=10.16, body_h=7.62,
             pins_left=[
                 ("GND",  "1", "passive"),
                 ("DATA", "2", "passive"),
                 ("VCC",  "3", "passive"),
             ],
             pins_right=[])

    # -----------------------------------------------------------------------
    # Component placement — all centres on G=2.54 mm grid
    #
    # Layout anchors:
    #   J8_CX/J8_CY    = (36G, 60G) = (91.44, 152.40) mm
    #   Boost subcircuit (row y=28G): C1@68G, L1@76G, U1@86G, D1@96G, C2@104G
    #   Bypass caps row  y=36G (below boost ICs)
    #   FAN_CX          = 130G      = 330.20             mm  (all fan headers)
    #   TACH_RES_CX     = 110G      = 279.40             mm  (TACH pull-up resistors)
    #   FAN_CY0         = 32G       = 81.28              mm  (J2 centre)
    #   FAN_STEP        = 12G       = 30.48              mm  (spacing J2->J3->J4->J5)
    #   LED_CY          = 90G       = 228.60             mm  (status LED row)
    #   PROG_LED_CY     = 97G       = 246.38             mm  (prog/OTA LED row, between status and NTC)
    #   NTC_CY          = 104G      = 264.16             mm  (NTC sensor row)
    #   SMALL_CX        = 62G       = 157.48             mm  (R3, R4, R13 left of LED/NTC pair)
    #   LARGE_CX        = 76G       = 193.04             mm  (LED1, LED2, NTC1 right of pair)
    #
    # Schematic spans x=22..350 mm, y=55..270 mm — fits well within A2 portrait.
    # -----------------------------------------------------------------------

    BLUE = (0, 0, 255)

    J8_CX,    J8_CY    = 36*G,  60*G   # (91.44, 152.40)
    FAN_CX              = 130*G         # 330.20
    TACH_RES_CX         = 110*G         # 279.40
    FAN_CY0             = 32*G          # 81.28 — J2
    FAN_STEP            = 12*G          # 30.48
    LED_CY              = 90*G          # 228.60
    PROG_LED_CY         = 97*G          # 246.38
    DHT11_CY            = 104*G         # 264.16 — DHT11 sensor row (replaces NTC)
    SMALL_CX            = 62*G          # 157.48 — R3 / R13 / R15
    LARGE_CX            = 76*G          # 193.04 — LED1 / LED2 / HUM1 / LED6
    PROBE_LED_CY        = 111*G         # 281.94 — probe health LED row (R15, LED6)
    PROBE_SENSOR_CY     = 119*G         # 302.26 — DS18B20 sensor row (R14, J6)

    # -----------------------------------------------------------------------
    # U1 — 5V->12V boost converter (LM2587-12) + external passives
    #
    # Correct boost topology:
    #   +5V ──[C1]── GND                  (input bypass cap)
    #   +5V ──[L1]──[BOOST_SW]──[D1]── +12V ──[C2]── GND  (boost path)
    #                    │                  │
    #               U1 OUTPUT (pin 3)   U1 FB (pin 4) senses +12V output
    #               U1 OSC   (pin 5) → 1 nF to GND (not shown, placed on PCB)
    #
    # Component layout in schematic (all on BOOST row y=28G..36G):
    #   C1   at (68G, 36G) — +5V input bypass
    #   L1   at (76G, 28G) — inductor from +5V to BOOST_SW
    #   U1   at (86G, 28G) — boost converter IC
    #   D1   at (94G, 28G) — catch diode BOOST_SW → +12V
    #   C2   at (102G, 36G) — +12V output filter
    # -----------------------------------------------------------------------
    BOOST_ROW_Y  = 28*G    # 71.12 mm — main boost row
    BYPASS_Y     = 36*G    # 91.44 mm — bypass caps below main row

    C1_CX  = 68*G          # 172.72 — input bypass cap
    L1_CX  = 76*G          # 193.04 — catch inductor
    U1_CX  = 86*G          # 218.44 — boost IC
    D1_CX  = 96*G          # 243.84 — catch diode
    C2_CX  = 104*G         # 264.16 — output filter cap

    s.text("5V -> 12V Boost  (U1 / LM2587-12)", 156, 55, size=2.54, bold=True, color=BLUE)

    # C1 — input bypass: +5V (pin 1) to GND (pin 2)
    pC1 = s.component("Custom:Cap_Elec", "C1", "100uF_25V",
                      "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
                      C1_CX, BYPASS_Y)
    s.power("+5V", *pC1["1"])
    s.power("GND", *pC1["2"])

    # L1 — catch inductor: +5V (pin 1) → BOOST_SW (pin 2)
    pL1 = s.component("Custom:Inductor", "L1", "100uH",
                      "Inductor_THT:L_Axial_L7.0mm_D3.3mm_P10.16mm_Horizontal_Fastron_MICC",
                      L1_CX, BOOST_ROW_Y)
    s.power("+5V",          *pL1["1"])
    s.label("BOOST_SW",     *pL1["2"])   # right pin → switching node

    # U1 — LM2587-12: GND(1) VIN(2) left; OUTPUT(3) FB(4) OSC(5) right
    pU1 = s.component("Custom:Boost_Converter", "U1", "LM2587-12",
                      "Package_TO_SOT_THT:TO-220-5_Vertical",
                      U1_CX, BOOST_ROW_Y)
    s.power("GND",       *pU1["1"])                         # left  pin 1 — GND
    s.power("+5V",       *pU1["2"])                         # left  pin 2 — VIN
    s.label("BOOST_SW",  *pU1["3"])                         # right pin 3 — OUTPUT/SW
    s.power("+12V",      *pU1["4"], pin_type="power_in")    # right pin 4 — FB senses +12V output
    s.power("GND",       *pU1["5"])                         # right pin 5 — OSC bypass to GND

    # D1 — catch diode: BOOST_SW (anode/pin 1) → +12V (cathode/pin 2)
    pD1 = s.component("Custom:Diode_Schottky", "D1", "1N5822",
                      "Diode_THT:D_DO-27_P12.70mm_Horizontal",
                      D1_CX, BOOST_ROW_Y)
    s.label("BOOST_SW",  *pD1["1"], angle=180)              # left  pin 1 — anode
    s.power("+12V",      *pD1["2"], pin_type="power_out")   # right pin 2 — cathode → +12V

    # C2 — output filter: +12V (pin 1) to GND (pin 2)
    pC2 = s.component("Custom:Cap_Elec", "C2", "100uF_25V",
                      "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
                      C2_CX, BYPASS_Y)
    s.power("+12V", *pC2["1"])
    s.power("GND",  *pC2["2"])

    # -----------------------------------------------------------------------
    # Fan headers J2-J5  +  TACH pull-up resistors R5-R8
    # All fan header pins are on the LEFT side of the symbol.
    # Labels on left-side pins use angle=180 (label extends LEFT, away from body).
    # TACH pull-up right pin is on the RIGHT side -> label uses angle=0.
    # -----------------------------------------------------------------------
    s.text("Fan Headers  (4x 12V PWM)", 240, 64, size=2.54, bold=True, color=BLUE)

    fan_data = [
        ("FAN1_PWM", "FAN1_TACH"),   # J2: PWM + TACH (full control)
        ("FAN2_PWM", "FAN2_TACH"),   # J3: PWM + TACH (R6 pull-up restored)
        ("FAN3_PWM", "FAN3_TACH"),   # J4: PWM + TACH (full control)
        ("FAN4_PWM", "FAN4_TACH"),   # J5: PWM + TACH (full control)
    ]

    for i, (pwm_net, tach_net) in enumerate(fan_data):
        FJ_CY = FAN_CY0 + i * FAN_STEP   # 81.28 / 111.76 / 142.24 / 172.72

        # Fan header — all pins left-side
        p = s.component("Custom:Fan_Header", f"J{2+i}", f"FAN{i+1}",
                        "Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical",
                        FAN_CX, FJ_CY)
        s.power("GND",  *p["1"])
        s.power("+12V", *p["2"])                                             # +12V from boost
        if tach_net == "NC":
            s.no_connect(*p["3"])                                            # no TACH monitoring
        else:
            s.global_label(tach_net, *p["3"], shape="output", angle=180)    # TACH signal
        if pwm_net == "NC":
            s.no_connect(*p["4"])                                            # no PWM = full speed
        else:
            s.global_label(pwm_net, *p["4"], shape="input", angle=180)      # PWM signal

        # TACH pull-up: only for fans that have TACH monitoring (R5=FAN1, R7=FAN3, R8=FAN4)
        # R6 (FAN2) omitted — FAN2 has no TACH
        if tach_net != "NC":
            res_idx = {0: 5, 1: 6, 2: 7, 3: 8}[i]   # fan 0→R5, 1→R6, 2→R7, 3→R8
            FR_CY = p["3"][1]
            pr = s.component("Custom:R", f"R{res_idx}", "10k",
                             "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                             TACH_RES_CX, FR_CY)
            s.power("+3V3",          *pr["1"])
            s.global_label(tach_net, *pr["2"], shape="output")

    # Per-fan passive indicator LEDs removed (cleanup v0.6 — reduces schematic noise)

    # -----------------------------------------------------------------------
    # PWM Fan Activity Indicator LEDs  (D2-D5 + R9-R12)  — issue #175
    #
    # Each LED is tapped directly on the FAN{n}_PWM signal line:
    #   FAN{n}_PWM ──[R 150Ω]──[LED anode]──[LED cathode]── GND
    #
    # LED brightness is proportional to PWM duty cycle:
    #   duty=100% → LED full brightness  (fan full speed)
    #   duty=50%  → LED medium brightness (fan half speed)
    #   duty=0%   → LED off              (fan stopped)
    #
    # Placement: schematically between TACH pull-ups and fan headers.
    #            On PCB: between J8 right column and fan headers.
    # -----------------------------------------------------------------------
    s.text("Fan PWM Activity LEDs  (D2-D5 / R9-R12)", 340, 64, size=2.54, bold=True, color=BLUE)

    PWM_LED_R_CX = 118*G   # 299.72 mm — resistors (between TACH column and fan headers)
    PWM_LED_D_CX = 124*G   # 314.96 mm — LEDs

    pwm_signals = ["FAN1_PWM", "FAN2_PWM", "FAN3_PWM", "FAN4_PWM"]
    for i, pwm_net in enumerate(pwm_signals):
        FJ_CY = FAN_CY0 + i * FAN_STEP
        led_anode_net = f"FAN{i+1}_PWM_A"

        # R9-R12: 150 Ω current-limit on PWM line
        pr = s.component("Custom:R", f"R{9+i}", "150R",
                         "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                         PWM_LED_R_CX, FJ_CY)
        s.global_label(pwm_net,     *pr["1"], shape="input",  angle=180)  # left  pin ← PWM signal
        s.label(led_anode_net,      *pr["2"])                              # right pin → LED anode

        # D2-D5: green 3mm THT activity LED
        pd = s.component("Custom:LED", f"D{2+i}", "LED_GREEN",
                         "LED_THT:LED_D3.0mm",
                         PWM_LED_D_CX, FJ_CY)
        s.label(led_anode_net,  *pd["1"], angle=180)  # left  pin — anode
        s.power("GND",          *pd["2"])             # right pin — cathode → GND

    # -----------------------------------------------------------------------
    # PWR_LED circuit: GPIO18 (J8 pin 17) → R3 → LED1 → GND
    # Power-on status indicator. Renamed from STATUS_LED.
    # -----------------------------------------------------------------------
    s.text("Power LED (PWR_LED)", 128, 215, size=2.54, bold=True, color=BLUE)
    p1 = s.component("Custom:R", "R3", "330R", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                     SMALL_CX, LED_CY)
    s.global_label("PWR_LED", *p1["1"], shape="input", angle=180)  # left pin
    s.label("LED_A",           *p1["2"])                             # right pin

    p1 = s.component("Custom:LED", "LED1", "LED_GREEN", "LED_THT:LED_D3.0mm",
                     LARGE_CX, LED_CY)
    s.label("LED_A", *p1["1"], angle=180)
    s.power("GND",   *p1["2"])

    # -----------------------------------------------------------------------
    # PROG LED: GPIO17 (J8 pin 16) → R13 → LED2 → GND
    # OTA / firmware-write activity indicator.
    # -----------------------------------------------------------------------
    s.text("Prog LED (OTA)", 128, 233, size=2.54, bold=True, color=BLUE)
    p1 = s.component("Custom:R", "R13", "330R", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                     SMALL_CX, PROG_LED_CY)
    s.global_label("PROG_LED", *p1["1"], shape="input", angle=180)
    s.label("PROG_LED_A",      *p1["2"])

    p1 = s.component("Custom:LED", "LED2", "LED_ORANGE", "LED_THT:LED_D3.0mm",
                     LARGE_CX, PROG_LED_CY)
    s.label("PROG_LED_A", *p1["1"], angle=180)
    s.power("GND",        *p1["2"])

    # -----------------------------------------------------------------------
    # DHT11 Temperature + Humidity Sensor (HUM1) — direct solder (3 pins)
    # No breakout module — solder DHT11 legs directly to the 3 PCB pads.
    # Pins: VCC (+3V3) | DATA (DHT11_DATA) | GND
    # Footprint: Custom:DHT11_Direct (generated by gen_footprint_dht11.py)
    # -----------------------------------------------------------------------
    s.text("DHT11 Temp+Humidity (HUM1 — direct solder)", 128, 251, size=2.54, bold=True, color=BLUE)
    HUM1_CX = SMALL_CX + 7*G
    p1 = s.component("Custom:DHT11_Direct", "HUM1", "DHT11_Direct",
                     "Custom:DHT11_Direct",
                     HUM1_CX, DHT11_CY)
    s.power("+3V3",                *p1["1"])
    s.global_label("DHT11_DATA",   *p1["2"], shape="bidirectional")
    s.power("GND",                 *p1["3"])

    # -----------------------------------------------------------------------
    # DS18B20 Temperature Probe + Probe Health LED  (J6 / R14 / R15 / LED6)
    #
    # DS18B20_DATA is GPIO2 (J8 left pin 6).
    # PROBE_LED    is GPIO3 (J8 left pin 7) — LED directly above J6 on PCB.
    #
    # J6 (Molex KK-254, 3-pin):  GND | DS18B20_DATA | +3V3
    # R14 (4.7kΩ): pull-up DS18B20_DATA → +3V3  (1-Wire spec)
    # R15 (330Ω) + LED6: PROBE_LED → LED → GND  (probe health indicator)
    # -----------------------------------------------------------------------
    s.text("DS18B20 Probe + Health LED  (J6 / R14 / R15 / LED6)",
           128, 269, size=2.54, bold=True, color=BLUE)

    # R14 — 4.7kΩ pull-up DS18B20_DATA to +3V3
    p1 = s.component("Custom:R", "R14", "4k7",
                     "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                     SMALL_CX, PROBE_SENSOR_CY)
    s.power("+3V3",                *p1["1"])
    s.global_label("DS18B20_DATA", *p1["2"], shape="bidirectional")

    # J6 — DS18B20 probe connector
    J6_CX = LARGE_CX + 8*G
    p1 = s.component("Custom:Conn_1x03", "J6", "Molex_KK254_3pin",
                     "Connector_Molex:Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical",
                     J6_CX, PROBE_SENSOR_CY)
    s.power("GND",                *p1["1"])
    s.global_label("DS18B20_DATA",*p1["2"], shape="bidirectional", angle=180)
    s.power("+3V3",               *p1["3"])

    # R15 + LED6 — probe health LED (PROBE_LED = GPIO3)
    # LED blinks when data is actively received from the DS18B20 probe
    # (firmware drives GPIO3 with a short pulse on each 1-Wire read cycle)
    p1 = s.component("Custom:R", "R15", "330R",
                     "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                     SMALL_CX, PROBE_LED_CY)
    s.global_label("PROBE_LED", *p1["1"], shape="input", angle=180)
    s.label("PROBE_LED_A",      *p1["2"])

    p1 = s.component("Custom:LED", "LED6", "LED_GREEN",
                     "LED_THT:LED_D3.0mm",
                     LARGE_CX, PROBE_LED_CY)
    s.label("PROBE_LED_A", *p1["1"], angle=180)
    s.power("GND",         *p1["2"])

    # -----------------------------------------------------------------------
    # J8 — Waveshare ESP32-P4-POE-ETH Interface (2x20 female PinSocket)
    # Signal assignments v0.6 — see module docstring for full table
    # -----------------------------------------------------------------------
    s.text("Waveshare ESP32-P4-POE-ETH  Interface  (J8)",
           22, 112, size=2.54, bold=True, color=BLUE)
    p = s.component("Custom:J8_Waveshare", "J8", "Waveshare_ESP32P4POEETH",
                    "Custom:ESP32-P4-PoE-ETH-PinSocket",
                    J8_CX, J8_CY)

    # --- Row A (pins 1-20, left side) — angle=180 for labels extending left ---
    s.power("GND",  *p["3"])
    s.power("GND",  *p["8"])
    s.power("GND",  *p["13"])
    s.global_label("DHT11_DATA",   *p["10"], shape="bidirectional", angle=180)  # GPIO5
    s.global_label("PROG_LED",     *p["16"], shape="output",        angle=180)  # GPIO17
    s.global_label("PWR_LED",      *p["17"], shape="output",        angle=180)  # GPIO18
    s.power("GND",  *p["18"])
    s.global_label("DS18B20_DATA", *p["6"],  shape="bidirectional", angle=180)  # GPIO2
    s.global_label("PROBE_LED",    *p["11"], shape="output",        angle=180)  # GPIO6

    # --- Row B (pins 21-40, right side) — angle=0 for labels extending right ---
    s.power("+5V",  *p["40"], pin_type="power_out")                            # VBUS → boost input
    s.power("GND",  *p["38"])
    s.power("+3V3", *p["36"], pin_type="power_out")                            # sole +3V3 source
    s.global_label("FAN1_PWM",   *p["35"], shape="output")                      # GPIO20 — FAN1 PWM
    s.global_label("FAN1_TACH",  *p["34"], shape="input")                        # GPIO21 — FAN1 tach
    s.power("GND",  *p["33"])
    s.global_label("FAN2_PWM",   *p["32"], shape="output")                      # GPIO22 — FAN2 PWM
    s.global_label("FAN2_TACH",  *p["31"], shape="input")                        # GPIO23 — FAN2 tach
    s.global_label("FAN3_PWM",   *p["25"], shape="output")                      # GPIO33 — FAN3 PWM
    s.global_label("FAN3_TACH",  *p["24"], shape="input")                        # GPIO46 — FAN3 tach
    s.power("GND",  *p["28"])
    s.global_label("FAN4_PWM",   *p["22"], shape="output")                      # GPIO47 — FAN4 PWM
    s.global_label("FAN4_TACH",  *p["21"], shape="input")                        # GPIO48 — FAN4 tach
    s.power("GND",  *p["23"])

    return s
