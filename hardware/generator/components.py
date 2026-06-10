"""
generator.components — build_schematic() for PoE FanController v0.5.

Daughter board design: custom PCB is a daughter board that stacks underneath the
Waveshare ESP32-P4-POE-ETH (SKU 32088). The Waveshare board handles PoE PD,
Ethernet PHY, RJ45, and ESP32-P4 — all via a single 802.3at Ethernet cable.
No PoE circuitry on the daughter board (NFR-S-01: SELV-only domain).

The daughter board stacks below the Waveshare board via J8 (2x20 female PinSocket
header) that receives +5V and GPIO signals from the Waveshare board's male header.

Daughter board provides:
  - J8      2x20 female header (ESP32-P4-PoE-ETH-PinSocket) receiving +5V
            on pin 40 (VBUS) — pin 39 (VSYS) left NC (issue #137)
            and GPIO signals from Waveshare ESP32-P4-POE-ETH (SKU 32088)
   # U1 (formerly U_BOOST) — 5V->12V boost converter (TI LM2587-12, TO-220-3)
  - J2-J5   4-pin fan headers (12V PWM, side-edge placement)
  - R5-R8   TACH pull-up resistors (10kOhm to 3.3V from Waveshare via J8 pin 36)
  # R4/NTC1 NTC temperature sensing (10kOhm NTC + 10kOhm divider) — REMOVED (issue #135)
  # HUM1    DHT11 temperature+humidity breakout (3-pin, 3.3V, single-wire)
  - R3/LED1 status LED circuit (GPIO2 via J8 left pin 6)

Power chain:
  J8 pin 40 (VBUS) — +5V to U_BOOST VIN  (also pins 2, 4 — VBUS duplicates)
    # U1 (LM2587-12, 5V -> 12V boost converter)
      -> +12V rail -> fans J2-J5
  J8 pin 36 (+3V3 from Waveshare on-board LDO) — SOLE +3V3 source (issue #148)
    -> TACH pull-ups R5-R8
    -> DS18B20 pull-up R14
    -> DHT11 VCC (HUM1)

Schematic layout (A2 portrait, 420x594mm):
  Column A (x~91):   J8  Waveshare interface header (2x20, 50.8mm tall body)
  Column B (x~203):  U1 (LM2587-12) 5V->12V converter
  Column C (x~279):  TACH pull-up resistors R5-R8
  Column D (x~330):  Fan headers J2-J5

  Below col B/C (y~228): Status LED circuit (R3, LED1)
  Below col B/C (y~264): NTC temperature circuit (R4, NTC1)

  Fan spacing: 12xG = 30.48 mm between header centres.
  J8 centre at y=152.4 mm is vertically centred with fan section (J2-J5 span
  y=81..173 mm).

Label angle convention (KiCad global_label at position x,y):
  angle=0   -> label body extends RIGHT from (x,y) -> use for RIGHT-side pins
  angle=180 -> label body extends LEFT  from (x,y) -> use for LEFT-side pins

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

    # Schottky catch diode D1 — SS54, BOOST_SW node to +12V output rail.
    s.define("Custom:Diode_Schottky", "D", "SS54",
             "Diode_SMD:D_SMA",
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
    #   Row A (near edge, 2.81mm from long edge):  pins  1..20  (top → bottom)
    #   Row B (far edge, 18.19mm from same edge):  pins 21..40  (top → bottom)
    #
    # CORRECTED ASSIGNMENTS (issue #148 — architecture validation v4.2.0):
    #   Left col  (Row A, pins  1-20): +5V on 2,4; GND on 3,8,13,18,20;
    #             STATUS_LED/GPIO2 on pin 6; PROG_LED/GPIO15 on pin 14;
    #             DHT11_DATA/GPIO16 on pin 15; DS18B20_DATA/GPIO19 on pin 19.
    #             All others NC (GPIO25, EMAC_*, reserved).
    #   Right col (Row B, pins 21-40): ALL 8 fan signals here (GPIO20-23,26,27,46,47);
    #             PROBE_LED/GPIO48 on pin 21; +3V3 output on pin 36; +5V/VBUS on pin 40.
    #             FORBIDDEN: pins 25,26 = GPIO33/32 = EMAC_RXD1/RXD0 — left NC.
    #             Reserved: pin 37 = EN (chip-enable) — left NC.
    #
    # Row spacing: 15.38mm = 21.00mm board width - 2x2.81mm edge offsets (see P-HW-04)
    # body_w = 10 * 2.54 = 25.4 mm,  body_h = 20 * 2.54 = 50.8 mm
    s.define("Custom:J8_Waveshare", "J", "Waveshare_ESP32P4POEETH",
             "Custom:ESP32-P4-PoE-ETH-PinSocket",
             "https://www.waveshare.com/wiki/ESP32-P4-POE-ETH",
             body_w=25.4, body_h=50.8,
             pins_left=[
                 # Consecutive pins 1..20 — Row A (top-to-bottom)
                 ("NC",           "1",  "no_connect"),    # GPIO25 — NC (not used)
                 ("NC",           "2",  "no_connect"),    # GPIO24 — NC (USB D-)
                 ("GND",          "3",  "passive"),       # Physical GND
                 ("NC",           "4",  "no_connect"),    # GPIO7 — NC (SDA/I2C)
                 ("NC",           "5",  "no_connect"),    # GPIO8 — NC (SCL/I2C)
                 ("STATUS_LED",   "6",  "output"),        # GPIO2 — status LED output
                 ("NC",           "7",  "no_connect"),    # unassigned — NC
                 ("GND",          "8",  "passive"),       # Physical GND
                 ("NC",           "9",  "no_connect"),    # unassigned — NC
                 ("NC",           "10", "no_connect"),    # unassigned — NC
                 ("NC",           "11", "no_connect"),    # unassigned — NC
                 ("NC",           "12", "no_connect"),    # unassigned — NC
                 ("GND",          "13", "passive"),       # Physical GND
                 ("PROG_LED",     "14", "output"),        # GPIO15 — OTA/write LED
                 ("DHT11_DATA",   "15", "input"),         # GPIO16 — DHT11 single-wire
                 ("NC",           "16", "no_connect"),    # unassigned — NC
                 ("NC",           "17", "no_connect"),    # unassigned — NC
                 ("GND",          "18", "passive"),       # Physical GND
                 ("DS18B20_DATA", "19", "bidirectional"), # GPIO19 — 1-Wire data
                 ("NC",           "20", "no_connect"),    # GPIO54 — NC (not GND)
             ],
             pins_right=[
                 # Consecutive pins 21..40 — Row B (top-to-bottom)
                 ("PROBE_LED",    "21", "output"),        # GPIO48 — probe health LED
                 ("FAN4_TACH",    "22", "input"),         # GPIO47 — FAN4 tach IRQ
                 ("GND",          "23", "passive"),       # Physical GND
                 ("FAN3_TACH",    "24", "input"),         # GPIO46 — FAN3 tach IRQ
                 ("NC",           "25", "no_connect"),    # GPIO33/EMAC_RXD1 — FORBIDDEN by IO_MUX
                 ("NC",           "26", "no_connect"),    # GPIO32/EMAC_RXD0 — FORBIDDEN by IO_MUX
                 ("FAN4_PWM",     "27", "output"),        # GPIO27 — FAN4 LEDC CH3
                 ("GND",          "28", "passive"),       # Physical GND
                 ("FAN3_PWM",     "29", "output"),        # GPIO26 — FAN3 LEDC CH2
                 ("NC",           "30", "no_connect"),    # RUN = system control, reserved
                 ("FAN2_TACH",    "31", "input"),         # GPIO23 — FAN2 tach IRQ
                 ("FAN1_TACH",    "32", "input"),         # GPIO22 — FAN1 tach IRQ
                 ("GND",          "33", "passive"),       # Physical GND (was wrongly FAN2_PWM)
                 ("FAN2_PWM",     "34", "output"),        # GPIO21 — FAN2 LEDC CH1 (was wrongly GND)
                 ("FAN1_PWM",     "35", "output"),        # GPIO20 — FAN1 LEDC CH0
                 ("+3V3",         "36", "power_out"),     # +3V3 from Waveshare LDO — SOLE source (issue #148)
                 ("NC",           "37", "no_connect"),    # EN / chip-enable — RESERVED, do NOT use
                 ("GND",          "38", "passive"),       # Physical GND
                 ("NC",           "39", "no_connect"),    # VSYS — system regulated; do NOT use as 5V source (issue #137)
                 ("+5V",          "40", "power_out"),     # VBUS — 5V power source for daughter board
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

    # DHT11 breakout module — 3-pin 2.54 mm header (VCC / DATA / GND)
    # Replaces NTC1 + R4 voltage-divider (issue #135, constitution v4.1.0)
    # Pin 1: VCC (3.3 V), Pin 2: DATA (single-wire), Pin 3: GND
    s.define("Custom:DHT11_Breakout", "U", "DHT11_Breakout",
             "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
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
    #                    │
    #               U1 OUTPUT (pin 3)
    #               U1 FB    (pin 4) tied to OUTPUT (fixed 12V)
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
    s.label("BOOST_SW",  *pU1["4"], angle=0)                # right pin 4 — FB tied to OUTPUT
    s.power("GND",       *pU1["5"])                         # right pin 5 — OSC bypass to GND

    # D1 — catch diode: BOOST_SW (anode/pin 1) → +12V (cathode/pin 2)
    pD1 = s.component("Custom:Diode_Schottky", "D1", "SS54",
                      "Diode_SMD:D_SMA",
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
        ("FAN1_PWM", "FAN1_TACH"),
        ("FAN2_PWM", "FAN2_TACH"),
        ("FAN3_PWM", "FAN3_TACH"),
        ("FAN4_PWM", "FAN4_TACH"),
    ]

    for i, (pwm_net, tach_net) in enumerate(fan_data):
        FJ_CY = FAN_CY0 + i * FAN_STEP   # 81.28 / 111.76 / 142.24 / 172.72

        # Fan header — all pins left-side
        p = s.component("Custom:Fan_Header", f"J{2+i}", f"FAN{i+1}",
                        "Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical",
                        FAN_CX, FJ_CY)
        s.power("GND",  *p["1"])
        s.power("+12V", *p["2"])
        s.global_label(tach_net, *p["3"], shape="output", angle=180)  # left pin
        s.global_label(pwm_net,  *p["4"], shape="input",  angle=180)  # left pin

        # TACH pull-up R5-R8: +3V3 -> TACH net
        FR_CY = p["3"][1]   # same y as TACH pin of this fan header
        pr = s.component("Custom:R", f"R{5+i}", "10k",
                         "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                         TACH_RES_CX, FR_CY)
        s.power("+3V3",          *pr["1"])                           # left  pin
        s.global_label(tach_net, *pr["2"], shape="output")           # right pin -> angle=0

    # -----------------------------------------------------------------------
    # Per-fan power indicator LEDs (D2-D5 + R9-R12)
    # Passive circuit — no firmware needed.
    # +12V → R(1kΩ, 0402) → (FAN{n}_IND net) → D(LED_0805 red, anode) → GND
    # Indicates +12V power flow on each fan rail.
    # Schematic placement: to the RIGHT of fan headers (same row per fan)
    # -----------------------------------------------------------------------
    s.text("Per-fan Power Indicator LEDs  (passive)", 340, 64, size=2.54, bold=True, color=BLUE)

    FAN_IND_R_CX = 147*G   # 373.38 mm — indicator resistors
    FAN_IND_D_CX = 159*G   # 403.86 mm — indicator LEDs

    for i in range(4):
        FJ_CY   = FAN_CY0 + i * FAN_STEP
        ind_net = f"FAN{i+1}_IND"

        pr = s.component("Custom:R", f"R{9+i}", "1k",
                         "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                         FAN_IND_R_CX, FJ_CY)
        s.power("+12V",      *pr["1"])             # left  pin → +12V rail
        s.label(ind_net,     *pr["2"])             # right pin → local net to LED anode

        pd = s.component("Custom:LED_SMD", f"D{2+i}", "LED_GREEN",
                         "LED_THT:LED_D3.0mm",
                         FAN_IND_D_CX, FJ_CY)
        s.label(ind_net,     *pd["1"], angle=180)  # left  pin — anode
        s.power("GND",       *pd["2"])             # right pin — cathode → GND

    # -----------------------------------------------------------------------
    # STATUS_LED net: J8 pin 3 (GPIO2) -> R3 -> LED1 -> GND
    # R3 left pin: STATUS_LED (global_label, left-side -> angle=180)
    # R3 right pin -> local label LED_A -> LED1 left pin -> LED1 right: GND
    # -----------------------------------------------------------------------
    s.text("Status LED", 128, 215, size=2.54, bold=True, color=BLUE)
    p1 = s.component("Custom:R", "R3", "330R", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                     SMALL_CX, LED_CY)
    s.global_label("STATUS_LED", *p1["1"], shape="input", angle=180)  # left pin
    s.label("LED_A",             *p1["2"])                             # right pin

    p1 = s.component("Custom:LED", "LED1", "LED_GREEN", "LED_THT:LED_D3.0mm",
                     LARGE_CX, LED_CY)
    s.label("LED_A", *p1["1"], angle=180)   # left pin — label extends left to meet R3 label
    s.power("GND",   *p1["2"])              # right pin

    # -----------------------------------------------------------------------
    # PROG LED circuit: firmware-write / OTA activity indicator
    # GPIO15 (J8 pin 22) → PROG_LED net → R13 → PROG_LED_A → LED2 → GND
    # LED2 is an orange 3mm THT LED placed next to LED1 on the PCB.
    # -----------------------------------------------------------------------
    s.text("Prog LED (OTA)", 128, 233, size=2.54, bold=True, color=BLUE)
    p1 = s.component("Custom:R", "R13", "330R", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                     SMALL_CX, PROG_LED_CY)
    s.global_label("PROG_LED", *p1["1"], shape="input", angle=180)  # left pin
    s.label("PROG_LED_A",      *p1["2"])                             # right pin

    p1 = s.component("Custom:LED", "LED2", "LED_ORANGE", "LED_THT:LED_D3.0mm",
                     LARGE_CX, PROG_LED_CY)
    s.label("PROG_LED_A", *p1["1"], angle=180)  # left pin (anode)
    s.power("GND",        *p1["2"])             # right pin (cathode)

    # -----------------------------------------------------------------------
    # DHT11 temperature + humidity sensor (HUM1)
    # Replaces NTC1 + R4 voltage-divider (issue #135, constitution v4.1.0)
    # VCC → +3V3, DATA → DHT11_DATA (GPIO16 via J8 pin 23), GND → GND
    # -----------------------------------------------------------------------
    s.text("DHT11 Temp+Humidity Sensor (HUM1)", 128, 251, size=2.54, bold=True, color=BLUE)
    HUM1_CX = SMALL_CX + 7*G   # 175.26 — centre DHT11 in this area
    p1 = s.component("Custom:DHT11_Breakout", "HUM1", "DHT11_Breakout",
                     "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
                     HUM1_CX, DHT11_CY)
    s.power("+3V3",                *p1["1"])                              # VCC
    s.global_label("DHT11_DATA",   *p1["2"], shape="bidirectional")       # DATA
    s.power("GND",                 *p1["3"])                              # GND

    # -----------------------------------------------------------------------
    # DS18B20 Temperature Probe  (J6 / R14 / R15 / LED6)
    #
    # Probe connector J6 (Molex KK-254, 3-pin):
    #   Pin 1 → GND
    #   Pin 2 → DS18B20_DATA (1-Wire bus, GPIO19 via J8 left pin 27)
    #   Pin 3 → +3V3 (power supply to probe)
    #
    # R14 (4.7 kΩ): pull-up from DS18B20_DATA to +3V3 (required by 1-Wire spec)
    #   Left pin  → +3V3
    #   Right pin → DS18B20_DATA (global_label)
    #
    # Probe health indicator LED6 (green 3mm THT, Status_LED_5):
    #   GPIO20 (J8 right pin 28) → PROBE_LED net → R15 (330 Ω) → PROBE_LED_A → LED6 → GND
    # -----------------------------------------------------------------------
    s.text("DS18B20 Temperature Probe  (J6 / R14 / R15 / LED6)",
           128, 269, size=2.54, bold=True, color=BLUE)

    # R15 — 330 Ω current-limit for probe health LED6 (GPIO20 → LED6 anode)
    p1 = s.component("Custom:R", "R15", "330R",
                     "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                     SMALL_CX, PROBE_LED_CY)
    s.global_label("PROBE_LED", *p1["1"], shape="input", angle=180)  # left pin
    s.label("PROBE_LED_A",      *p1["2"])                             # right pin

    # LED6 — green 3mm THT, probe health indicator (Status_LED_5)
    p1 = s.component("Custom:LED", "LED6", "LED_GREEN",
                     "LED_THT:LED_D3.0mm",
                     LARGE_CX, PROBE_LED_CY)
    s.label("PROBE_LED_A", *p1["1"], angle=180)  # left pin (anode)
    s.power("GND",         *p1["2"])             # right pin (cathode)

    # R14 — 4.7 kΩ pull-up resistor DS18B20_DATA to +3V3
    p1 = s.component("Custom:R", "R14", "4k7",
                     "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
                     SMALL_CX, PROBE_SENSOR_CY)
    s.power("+3V3",                *p1["1"])                              # left  pin
    s.global_label("DS18B20_DATA", *p1["2"], shape="bidirectional")       # right pin

    # J6 — Molex KK-254 3-pin temp probe connector
    J6_CX = LARGE_CX + 8*G   # 213.36 — offset right of R14/LED6 column
    p1 = s.component("Custom:Conn_1x03", "J6", "Molex_KK254_3pin",
                     "Connector_Molex:Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical",
                     J6_CX, PROBE_SENSOR_CY)
    s.power("GND",                *p1["1"])                                   # pin 1 — GND
    s.global_label("DS18B20_DATA",*p1["2"], shape="bidirectional", angle=180) # pin 2 — DATA
    s.power("+3V3",               *p1["3"])                                   # pin 3 — +3V3

    # -----------------------------------------------------------------------
    # J8 — Waveshare ESP32-P4-POE-ETH Interface (2x20 female PinSocket)
    #
    # PIN LAYOUT (issue #133 fix): CONSECUTIVE column numbering.
    #   Row A (left  side of symbol): pins  1..20  top → bottom
    #   Row B (right side of symbol): pins 21..40  top → bottom
    #
    # CORRECTED ASSIGNMENTS (issue #148 — architecture validation v4.2.1):
    #
    # Power in from Waveshare:
    #   pin 40 (VBUS) -> +5V -> U_BOOST VIN
    #   pin 36 (+3V3) -> TACH pull-ups R5-R8, DS18B20 pull-up R14, DHT11 VCC
    #   pin 39 (VSYS) -> NC  (system regulated voltage — do NOT use as 5V source)
    #   GND: left col pins 3,8,13,18 + right col pins 23,28,33,38
    #
    # GPIO signals:
    #   Left col  (pins 1-20, angle=180): STATUS_LED/GPIO2(6), PROG_LED/GPIO15(14),
    #                                     DHT11_DATA/GPIO16(15), DS18B20_DATA/GPIO19(19)
    #   Right col (pins 21-40, angle=0):  PROBE_LED/GPIO48(21),
    #                                     FAN4_TACH/GPIO47(22), FAN3_TACH/GPIO46(24),
    #                                     FAN4_PWM/GPIO27(27),  FAN3_PWM/GPIO26(29),
    #                                     FAN2_TACH/GPIO23(31), FAN1_TACH/GPIO22(32),
    #                                     FAN2_PWM/GPIO21(34),  FAN1_PWM/GPIO20(35)
    #
    # NC pins (no_connect type — ERC suppressed, no wiring needed):
    #   Left: 1,2,4,5,7,9,10,11,12,16,17,20
    #   Right: 25,26,30,37,39
    # -----------------------------------------------------------------------
    s.text("Waveshare ESP32-P4-POE-ETH  Interface  (J8)",
           22, 112, size=2.54, bold=True, color=BLUE)
    p = s.component("Custom:J8_Waveshare", "J8", "Waveshare_ESP32P4POEETH",
                    "Custom:ESP32-P4-PoE-ETH-PinSocket",
                    J8_CX, J8_CY)

    # --- Row A (pins 1-20, left side) — use angle=180 for global_labels ---
    # pins 1,2,4,5,7,9-12,16,17,20: NC (no wiring needed — no_connect type suppresses ERC)
    s.power("GND", *p["3"])                                            # Physical GND
    # pin 5: NC
    s.global_label("STATUS_LED", *p["6"],  shape="output", angle=180)  # GPIO2
    # pin 7: NC
    s.power("GND", *p["8"])                                            # Physical GND
    # pins 9,10,11,12: NC
    s.power("GND", *p["13"])                                           # Physical GND
    s.global_label("PROG_LED",     *p["14"], shape="output",       angle=180)  # GPIO15
    s.global_label("DHT11_DATA",   *p["15"], shape="bidirectional",angle=180)  # GPIO16
    # pins 16,17: NC
    s.power("GND", *p["18"])                                           # Physical GND
    s.global_label("DS18B20_DATA", *p["19"], shape="bidirectional",angle=180)  # GPIO19
    # pin 20: NC (GPIO54 — not GND)

    # --- Row B (pins 21-40, right side) — use angle=0 for global_labels ---
    s.global_label("PROBE_LED",  *p["21"], shape="output")             # GPIO48 — probe health LED
    s.global_label("FAN4_TACH", *p["22"], shape="input")               # GPIO47 — FAN4 tach IRQ
    s.power("GND", *p["23"])                                            # Physical GND
    s.global_label("FAN3_TACH", *p["24"], shape="input")               # GPIO46 — FAN3 tach IRQ
    # pins 25,26: NC (GPIO33/EMAC_RXD1 and GPIO32/EMAC_RXD0 — FORBIDDEN by IO_MUX)
    s.global_label("FAN4_PWM",  *p["27"], shape="output")              # GPIO27 — FAN4 LEDC CH3
    s.power("GND", *p["28"])                                            # Physical GND
    s.global_label("FAN3_PWM",  *p["29"], shape="output")              # GPIO26 — FAN3 LEDC CH2
    # pin 30: NC (RUN = system control, reserved)
    s.global_label("FAN2_TACH", *p["31"], shape="input")               # GPIO23 — FAN2 tach IRQ
    s.global_label("FAN1_TACH", *p["32"], shape="input")               # GPIO22 — FAN1 tach IRQ
    s.power("GND", *p["33"])                                            # Physical GND (was wrongly FAN2_PWM)
    s.global_label("FAN2_PWM",  *p["34"], shape="output")              # GPIO21 — FAN2 LEDC CH1 (moved from 33→34)
    s.global_label("FAN1_PWM",  *p["35"], shape="output")              # GPIO20 — FAN1 LEDC CH0
    s.power("+3V3", *p["36"], pin_type="power_out")                    # +3V3 SOLE source (issue #148)
    # pin 37: NC (EN/chip-enable — RESERVED)
    s.power("GND", *p["38"])                                            # Physical GND
    # pin 39: NC (VSYS — do NOT use as 5V source)
    s.power("+5V", *p["40"], pin_type="power_out")                     # VBUS — 5V source for daughter board

    return s
