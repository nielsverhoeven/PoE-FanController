"""
generator.components — build_schematic() for PoE FanController v0.5.

Daughter board design: custom PCB is a daughter board that stacks underneath the
Waveshare ESP32-P4-POE-ETH (SKU 32088). The Waveshare board handles PoE PD,
Ethernet PHY, RJ45, and ESP32-P4 — all via a single 802.3at Ethernet cable.
No PoE circuitry on the daughter board (NFR-S-01: SELV-only domain).

The daughter board stacks below the Waveshare board via J8 (2x20 female PinSocket
header) that receives +5V and GPIO signals from the Waveshare board's male header.

Daughter board provides:
  - J8      2x20 female header (PinSocket_2x20_P2.54mm_Vertical) receiving +5V
            and GPIO signals from Waveshare ESP32-P4-POE-ETH (SKU 32088)
   # U1 (formerly U_BOOST) — 5V->12V boost converter (TI LM2587-12, TO-220-3)
  - J2-J5   4-pin fan headers (12V PWM, side-edge placement)
  - R5-R8   TACH pull-up resistors (10kOhm to 3.3V from Waveshare via J8)
  - R4/NTC1 NTC temperature sensing (10kOhm NTC + 10kOhm divider)
  - R3/LED1 status LED circuit (GPIO2 via J8)

Power chain:
  J8 pins 2,4 (+5V from Waveshare ESP32-P4-POE-ETH PoE PD module)
    # U1 (LM2587-12, 5V -> 12V boost converter)
      -> +12V rail -> fans J2-J5
  J8 pins 1,17 (+3V3 from Waveshare on-board LDO)
    -> TACH pull-ups R5-R8
    -> NTC voltage divider R4

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
    # CRITICAL: row spacing is 2.81mm (NOT standard 2.54mm).
    # Source: docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-details-size-*.webp
    # Board dimensions confirmed: 78.00 x 21.00 mm; pin pitch 2.54mm, row pitch 2.81mm.
    # Custom footprint: Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical (in Custom.pretty)
    #
    # OQ-02 PENDING: Confirm +5V on pins 2,4 from Waveshare SKU 32088 schematic.
    # OQ-03 PENDING: Confirm GPIO4-7/8-11/16/2 positions on SKU 32088 header.
    # Row spacing: 15.38mm = 21.00mm board width - 2x2.81mm edge offsets (see P-HW-04)
    # body_w = 10 * 2.54 = 25.4 mm,  body_h = 20 * 2.54 = 50.8 mm
    s.define("Custom:J8_Waveshare", "J", "Waveshare_ESP32P4POEETH",
             "Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical",
             "https://www.waveshare.com/wiki/ESP32-P4-POE-ETH",
             body_w=25.4, body_h=50.8,
             pins_left=[
                 # Odd pads 1,3,5,...,39  (top-to-bottom)
                 ("+3V3",      "1",  "power_out"),     # 3.3V from Waveshare LDO
                 ("LED",       "3",  "bidirectional"), # GPIO2 - status LED
                 ("NC",        "5",  "no_connect"),    # GPIO3
                 ("FAN1_PWM",  "7",  "output"),        # GPIO4 LEDC CH0
                 ("GND",       "9",  "passive"),
                 ("FAN4_PWM",  "11", "output"),        # GPIO7 LEDC CH3
                 ("FAN2_TACH", "13", "input"),         # GPIO9 tach input
                 ("FAN3_TACH", "15", "input"),         # GPIO10 tach input
                 ("+3V3",      "17", "power_out"),     # 3.3V duplicate
                 ("NC",        "19", "no_connect"),    # GPIO13
                 ("NC",        "21", "no_connect"),    # GPIO14
                 ("NTC_ADC",   "23", "input"),         # GPIO16 ADC
                 ("GND",       "25", "passive"),
                 ("NC",        "27", "no_connect"),    # GPIO19
                 ("GND",       "29", "passive"),
                 ("NC",        "31", "no_connect"),    # GPIO22
                 ("GND",       "33", "passive"),
                 ("NC",        "35", "no_connect"),    # GPIO28 ETH_MDIO (NC)
                 ("NC",        "37", "no_connect"),    # GPIO29
                 ("NC",        "39", "no_connect"),    # VSYS
             ],
             pins_right=[
                 # Even pads 2,4,6,...,40  (top-to-bottom)
                 ("+5V",       "2",  "power_out"),     # +5V from Waveshare PoE PD
                 ("+5V",       "4",  "power_out"),     # +5V duplicate
                 ("GND",       "6",  "passive"),
                 ("FAN2_PWM",  "8",  "output"),        # GPIO5 LEDC CH1
                 ("FAN3_PWM",  "10", "output"),        # GPIO6 LEDC CH2
                 ("FAN1_TACH", "12", "input"),         # GPIO8 tach input
                 ("GND",       "14", "passive"),
                 ("FAN4_TACH", "16", "input"),         # GPIO11 tach input
                 ("NC",        "18", "no_connect"),    # GPIO12
                 ("GND",       "20", "passive"),
                 ("NC",        "22", "no_connect"),    # GPIO15
                 ("NC",        "24", "no_connect"),    # GPIO17
                 ("NC",        "26", "no_connect"),    # GPIO18
                 ("NC",        "28", "no_connect"),    # GPIO20
                 ("NC",        "30", "no_connect"),    # GPIO21
                 ("NC",        "32", "no_connect"),    # GPIO26
                 ("NC",        "34", "no_connect"),    # GPIO27
                 ("NC",        "36", "no_connect"),    # 3V3_EN/RUN
                 ("GND",       "38", "passive"),
                 ("NC",        "40", "no_connect"),    # VBUS
             ])

    # 4-pin fan header (J2-J5) — all pins on LEFT side (connector opens left)
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

    # Generic passive 2-terminal resistor (pin 1 left, pin 2 right)
    s.define("Custom:R", "R", "R",
             "Resistor_SMD:R_0402_1005Metric", "~",
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

    s.define("Custom:NTC", "NTC", "NTC_10K",
             "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("1",  "1", "passive")],
             pins_right=[("2", "2", "passive")])

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
    #   NTC_CY          = 104G      = 264.16             mm  (NTC sensor row)
    #   SMALL_CX        = 62G       = 157.48             mm  (R3, R4 left of LED/NTC pair)
    #   LARGE_CX        = 76G       = 193.04             mm  (LED1, NTC1 right of pair)
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
    NTC_CY              = 104*G         # 264.16
    SMALL_CX            = 62*G          # 157.48 — R3 / R4
    LARGE_CX            = 76*G          # 193.04 — LED1 / NTC1

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
                        "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
                        FAN_CX, FJ_CY)
        s.power("GND",  *p["1"])
        s.power("+12V", *p["2"])
        s.global_label(tach_net, *p["3"], shape="output", angle=180)  # left pin
        s.global_label(pwm_net,  *p["4"], shape="input",  angle=180)  # left pin

        # TACH pull-up R5-R8: +3V3 -> TACH net
        FR_CY = p["3"][1]   # same y as TACH pin of this fan header
        pr = s.component("Custom:R", f"R{5+i}", "10k",
                         "Resistor_SMD:R_0402_1005Metric",
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
                         "Resistor_SMD:R_0402_1005Metric",
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
    p1 = s.component("Custom:R", "R3", "330R", "Resistor_SMD:R_0402_1005Metric",
                     SMALL_CX, LED_CY)
    s.global_label("STATUS_LED", *p1["1"], shape="input", angle=180)  # left pin
    s.label("LED_A",             *p1["2"])                             # right pin

    p1 = s.component("Custom:LED", "LED1", "LED_GREEN", "LED_THT:LED_D3.0mm",
                     LARGE_CX, LED_CY)
    s.label("LED_A", *p1["1"], angle=180)   # left pin — label extends left to meet R3 label
    s.power("GND",   *p1["2"])              # right pin

    # -----------------------------------------------------------------------
    # NTC temperature sensor voltage divider (R4 + NTC1)
    # +3V3 -> R4 -> NTC_ADC node -> NTC1 -> GND
    # Both sides of the node are labelled NTC_ADC (global_label) so the net is
    # visible at both R4 (right pin) and NTC1 (left pin).
    # -----------------------------------------------------------------------
    s.text("NTC Temperature Sensor", 128, 251, size=2.54, bold=True, color=BLUE)
    p1 = s.component("Custom:R", "R4", "10k", "Resistor_SMD:R_0402_1005Metric",
                     SMALL_CX, NTC_CY)
    s.power("+3V3",            *p1["1"])                              # left  pin
    s.global_label("NTC_ADC", *p1["2"], shape="output")              # right pin -> angle=0

    p1 = s.component("Custom:NTC", "NTC1", "NTC10K_B3950",
                     "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
                     LARGE_CX, NTC_CY)
    s.global_label("NTC_ADC", *p1["1"], shape="output", angle=180)   # left  pin
    s.power("GND",            *p1["2"])                               # right pin

    # -----------------------------------------------------------------------
    # J8 — Waveshare ESP32-P4-POE-ETH Interface (2x20 female PinSocket)
    #
    # Power in from Waveshare (right pins, angle=0):
    #   pins 2,4 -> +5V -> U_BOOST VIN
    #   pins 6,14,20,38 + left pins 9,25,29,33 -> GND
    #   pins 1,17 (left) -> +3V3 -> TACH pull-ups + NTC divider
    #
    # GPIO signals:
    #   Left side (odd, angle=180): FAN1_PWM(7), FAN4_PWM(11),
    #                               FAN2_TACH(13), FAN3_TACH(15),
    #                               NTC_ADC(23), STATUS_LED(3)
    #   Right side (even, angle=0): FAN2_PWM(8), FAN3_PWM(10),
    #                               FAN1_TACH(12), FAN4_TACH(16)
    #
    # NC pins: symbol type "no_connect" suppresses ERC — no explicit markers needed.
    # -----------------------------------------------------------------------
    s.text("Waveshare ESP32-P4-POE-ETH  Interface  (J8)",
           22, 112, size=2.54, bold=True, color=BLUE)
    p = s.component("Custom:J8_Waveshare", "J8", "Waveshare_ESP32P4POEETH",
                    "Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical",
                    J8_CX, J8_CY)

    # --- Left pins (odd) — use angle=180 for global_labels ---
    s.power("+3V3", *p["1"],  pin_type="power_out")                   # +3V3 output
    s.global_label("STATUS_LED", *p["3"],  shape="output", angle=180) # GPIO2
    # pin 5: NC (symbol type no_connect)
    s.global_label("FAN1_PWM",  *p["7"],  shape="output", angle=180)  # GPIO4
    s.power("GND", *p["9"])
    s.global_label("FAN4_PWM",  *p["11"], shape="output", angle=180)  # GPIO7
    s.global_label("FAN2_TACH", *p["13"], shape="input",  angle=180)  # GPIO9
    s.global_label("FAN3_TACH", *p["15"], shape="input",  angle=180)  # GPIO10
    s.power("+3V3", *p["17"], pin_type="power_out")                   # +3V3 duplicate
    # pins 19,21: NC
    s.global_label("NTC_ADC",   *p["23"], shape="input",  angle=180)  # GPIO16
    s.power("GND", *p["25"])
    # pin 27: NC
    s.power("GND", *p["29"])
    # pin 31: NC
    s.power("GND", *p["33"])
    # pins 35,37,39: NC

    # --- Right pins (even) — use angle=0 for global_labels ---
    s.power("+5V", *p["2"])                                           # +5V from Waveshare PoE
    s.power("+5V", *p["4"])                                           # +5V duplicate
    s.power("GND", *p["6"])
    s.global_label("FAN2_PWM",  *p["8"],  shape="output")             # GPIO5
    s.global_label("FAN3_PWM",  *p["10"], shape="output")             # GPIO6
    s.global_label("FAN1_TACH", *p["12"], shape="input")              # GPIO8
    s.power("GND", *p["14"])
    s.global_label("FAN4_TACH", *p["16"], shape="input")              # GPIO11
    # pin 18: NC
    s.power("GND", *p["20"])
    # pins 22,24,26,28,30,32,34,36: NC
    s.power("GND", *p["38"])
    # pin 40: NC

    return s
