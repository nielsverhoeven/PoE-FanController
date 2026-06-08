"""
generator.components — build_schematic() for PoE FanController v0.3.

Carrier board design: custom PCB is a HAT for the Waveshare ESP32-P4-ETH
(SKU 32086) dev board.  All ESP32 peripherals (RMII Ethernet, USB-UART,
reset/boot buttons) are handled on the Waveshare board itself.

Carrier provides:
  - J1  RJ45 PoE power input (MDI secondary NC — power-only port)
  - U1  Ag9905M PoE+ PD module (→ 12V)
  - U2  LM2596S-5.0 buck regulator (12V → 5V)
  - D2  1N5822 back-feed protection Schottky (5V → +5V_HAT)
  - J8  2×20 HAT header connecting to Waveshare ESP32-P4-ETH
  - J2-J5 4-pin fan headers (12V PWM)
  - R5-R8 TACH pull-ups (3.3V from Waveshare via J8)
  - R4/NTC1 NTC temperature sensing
  - R3/LED1 status LED

Power chain:
  J1 RJ45 → Ag9905M → +12V
    → fans J2-J5 (12V)
    → U2 LM2596S-5.0 → +5V
      → D2 (1N5822) → +5V_HAT → J8 pins 2,4 → Waveshare board
        → (Waveshare LDO) → +3V3 → J8 pins 1,17 → carrier (pull-ups, NTC)

Pin position formula (angle=0):
  left  pin i: x = cx - hw - pin_len,  y = cy + hh - 1.27 - i*2.54
  right pin i: x = cx + hw + pin_len,  y = cy + hh - 1.27 - i*2.54
where hw = body_w/2, hh = body_h/2, pin_len = 2.54 mm
"""

from .schematic import Schematic
from .utils import G


def build_schematic():
    """Build and return the complete Schematic object for PoE-FanController."""
    s = Schematic()

    # -----------------------------------------------------------------------
    # Symbol definitions  (body_w, body_h MUST be multiples of G=2.54)
    # -----------------------------------------------------------------------

    # RJ45 with integrated PoE magnetics + MDI secondary exposure (Würth 615008144521)
    # OQ-03 RESOLVED 2026-06-07: Würth 615008144521 exposes PoE centre-tap pairs on
    # dedicated pins separate from MDI secondary winding outputs.  Left pins carry PoE
    # power centre-taps → Ag9905M (P-POE-02 topology unchanged).  Right pins carry MDI
    # secondary data pairs → LAN8720A via 49.9 Ω series resistors R11-R14.
    # PCB footprint: Custom:RJ45_Wuerth_615008144521 (stored in Custom.pretty/).
    # Using a custom footprint avoids lib_footprint_issues DRC violations — custom
    # footprints are not cross-checked against the KiCad standard library in either
    # 10.0.2 (Docker) or 10.0.3 (local). Geometry copied from Hanrun HR911105A which
    # has the same 8P8C THT horizontal body/pitch as the Würth 615008144521.
    s.define("Custom:RJ45_PoE_PHY", "J", "RJ45_PoE_PHY",
             "Custom:RJ45_Wuerth_615008144521",
             "https://www.we-online.com/en/components/products/WR-MJ/615008144521",
             body_w=15.24, body_h=12.70,
             pins_left=[
                 ("POE_A+", "PA+", "passive"),   # PoE mode A centre-tap +
                 ("POE_A-", "PA-", "passive"),   # PoE mode A centre-tap -
                 ("POE_B+", "PB+", "passive"),   # PoE mode B centre-tap +
                 ("POE_B-", "PB-", "passive"),   # PoE mode B centre-tap -
             ],
             pins_right=[
                 ("ETH_TD_P", "TDP", "passive"),  # MDI TX+ secondary winding
                 ("ETH_TD_N", "TDN", "passive"),  # MDI TX-
                 ("ETH_RD_P", "RDP", "passive"),  # MDI RX+
                 ("ETH_RD_N", "RDN", "passive"),  # MDI RX-
             ])

    # Ag9905M PoE+ PD module: 4 left (PoE input), 4 right (12V output)
    s.define("Custom:Ag9905M", "U", "Ag9905M",
             "Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical",
             "https://silvertel.com/images/datasheets/Ag9900-Datasheet.pdf",
             body_w=22.86, body_h=12.70,
             pins_left=[
                 ("VPORT_A+", "1", "passive"),
                 ("VPORT_A-", "2", "passive"),
                 ("VPORT_B+", "3", "passive"),
                 ("VPORT_B-", "4", "passive"),
             ],
             pins_right=[
                 ("VOUT_P", "5", "power_out"),
                 ("VOUT_N", "6", "power_out"),
                 ("/SD",    "7", "input"),
                 ("FLT",    "8", "output"),
             ])

    # LM2596-5.0: 3 left (IN, GND, /ON), 2 right (OUT, FB)
    s.define("Custom:LM2596-5.0", "U", "LM2596-5.0",
             "Package_TO_SOT_SMD:TO-263-5_TabPin3",
             "https://www.ti.com/lit/ds/symlink/lm2596.pdf",
             body_w=17.78, body_h=10.16,
             pins_left=[
                 ("IN",  "1", "power_in"),
                 ("GND", "3", "power_in"),
                 ("/ON", "5", "input"),
             ],
             pins_right=[
                 ("OUT", "2", "power_out"),
                 ("FB",  "4", "input"),
             ])

    # Waveshare ESP32-P4-ETH 2x20 HAT header (J8)
    # Pinout: Raspberry Pi Pico HAT-compatible (2.54mm pitch, 40 pins total)
    # Odd pads  (1,3,...,39) = left  column → pins_left  in top-to-bottom order
    # Even pads (2,4,...,40) = right column → pins_right in top-to-bottom order
    #
    # NOTE: GPIO28 (pad 35) = ETH_MDIO on Waveshare board — DO NOT drive from carrier.
    # POWER: pins 2,4 = +5V_HAT input from carrier (via D2 back-feed Schottky)
    #        pins 1,17 = +3V3 output from Waveshare's on-board LDO → carrier pull-ups
    # UART0 (GPIO38/39) is internal to Waveshare CH343P bridge — NOT on J8 header.
    # body_w = 10 * 2.54 = 25.4 mm, body_h = 20 * 2.54 = 50.8 mm
    s.define("Custom:J8_Waveshare", "J", "Waveshare_ESP32P4ETH",
             "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical",
             "https://www.waveshare.com/wiki/ESP32-P4-ETH",
             body_w=25.4, body_h=50.8,
             pins_left=[
                 # Odd pads: 1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39
                 ("+3V3_OUT",   "1",  "power_out"),    # 3.3V from Waveshare LDO
                 ("STATUS_LED", "3",  "bidirectional"), # GPIO2 — status LED
                 ("NC",         "5",  "no_connect"),    # GPIO3
                 ("FAN1_PWM",   "7",  "output"),        # GPIO4 LEDC CH0
                 ("GND",        "9",  "passive"),
                 ("FAN4_PWM",   "11", "output"),        # GPIO7 LEDC CH3
                 ("FAN2_TACH",  "13", "input"),         # GPIO9 tach input
                 ("FAN3_TACH",  "15", "input"),         # GPIO10 tach input
                 ("+3V3_OUT",   "17", "power_out"),     # 3.3V duplicate from Waveshare
                 ("NC",         "19", "no_connect"),    # GPIO13
                 ("NC",         "21", "no_connect"),    # GPIO14
                 ("NTC_ADC",    "23", "input"),         # GPIO16 ADC
                 ("GND",        "25", "passive"),
                 ("NC",         "27", "no_connect"),    # GPIO19
                 ("GND",        "29", "passive"),
                 ("NC",         "31", "no_connect"),    # GPIO22
                 ("GND",        "33", "passive"),
                 ("NC",         "35", "no_connect"),    # GPIO28 = ETH_MDIO (internal, NC)
                 ("NC",         "37", "no_connect"),    # GPIO29
                 ("NC",         "39", "no_connect"),    # VSYS
             ],
             pins_right=[
                 # Even pads: 2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40
                 # Pins 2,4 = +5V_HAT: use "passive" to avoid ERC power-driver error
                 # (D2 is a passive component — labels are used for connectivity)
                 ("+5V_HAT",    "2",  "passive"),       # 5V from carrier (via D2)
                 ("+5V_HAT",    "4",  "passive"),       # 5V duplicate
                 ("GND",        "6",  "passive"),
                 ("FAN2_PWM",   "8",  "output"),        # GPIO5 LEDC CH1
                 ("FAN3_PWM",   "10", "output"),        # GPIO6 LEDC CH2
                 ("FAN1_TACH",  "12", "input"),         # GPIO8 tach input
                 ("GND",        "14", "passive"),
                 ("FAN4_TACH",  "16", "input"),         # GPIO11 tach input
                 ("NC",         "18", "no_connect"),    # GPIO12
                 ("GND",        "20", "passive"),
                 ("NC",         "22", "no_connect"),    # GPIO15
                 ("NC",         "24", "no_connect"),    # GPIO17
                 ("NC",         "26", "no_connect"),    # GPIO18
                 ("NC",         "28", "no_connect"),    # GPIO20
                 ("NC",         "30", "no_connect"),    # GPIO21
                 ("NC",         "32", "no_connect"),    # GPIO26
                 ("NC",         "34", "no_connect"),    # GPIO27
                 ("NC",         "36", "no_connect"),    # 3V3_EN/RUN
                 ("GND",        "38", "passive"),
                 ("NC",         "40", "no_connect"),    # VBUS
             ])

    # 4-pin fan header (J2-J5)
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

    # Generic passive 2-terminal
    s.define("Custom:R", "R", "R",
             "Resistor_SMD:R_0402_1005Metric", "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("~", "1", "passive")],
             pins_right=[("~", "2", "passive")])

    s.define("Custom:C", "C", "C",
             "Capacitor_SMD:C_0402_1005Metric", "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("~", "1", "passive")],
             pins_right=[("~", "2", "passive")])

    s.define("Custom:L", "L", "L",
             "Inductor_THT:L_Axial_L11.0mm_D4.5mm_P15.24mm_Horizontal_Fastron_MECC", "~",
             body_w=7.62, body_h=2.54,
             pins_left=[("~", "1", "passive")],
             pins_right=[("~", "2", "passive")])

    s.define("Custom:D_Schottky", "D", "D_Schottky",
             "Diode_THT:D_DO-201AD_P12.70mm_Horizontal", "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("A", "1", "passive")],
             pins_right=[("K", "2", "passive")])

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
    # 2. Component placement
    #
    # All centres on 2.54 mm (G) grid. Using named variables for readability.
    # Diagram regions on A2 (594 × 420 mm):
    #   POE_IN  : x=25..110,  y=30..100
    #   BUCK    : x=25..175,  y=110..185
    #   FANS    : x=305..420, y=30..200
    #   J8_HAT  : x=25..200,  y=215..420
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # J1 – RJ45 with PoE magnetics — PoE POWER ONLY (MDI secondary NC)
    # Data path: Waveshare ESP32-P4-ETH's own RJ45 handles Ethernet data.
    # PSE switch port must be configured "force PoE" / "power regardless of link state"
    # because J1 MDI secondary is open-circuit → no 802.3 link visible on this port.
    # PCB footprint: Custom:RJ45_Wuerth_615008144521 (Custom.pretty/) — avoids
    # lib_footprint_issues DRC violations that standard library footprints cause.
    # -----------------------------------------------------------------------
    BLUE = (0, 0, 255)
    s.text("PoE Power Input", 25, 18, size=2.54, bold=True, color=BLUE)
    J1_CX, J1_CY = 38.1, 55.88          # 15*G, 22*G
    p = s.component("Custom:RJ45_PoE_PHY","J1","RJ45_PoE_PHY",
                    "Custom:RJ45_Wuerth_615008144521",
                    J1_CX, J1_CY)
    # PoE centre-tap pairs → Ag9905M (P-POE-02)
    s.label("POE_A+", *p["PA+"])
    s.label("POE_A-", *p["PA-"])
    s.label("POE_B+", *p["PB+"])
    s.label("POE_B-", *p["PB-"])
    # MDI secondary NC — Waveshare board uses its own RJ45 for Ethernet data
    s.no_connect(*p["TDP"])
    s.no_connect(*p["TDN"])
    s.no_connect(*p["RDP"])
    s.no_connect(*p["RDN"])

    # -----------------------------------------------------------------------
    # U1 – Ag9905M PoE+ PD module
    # -----------------------------------------------------------------------
    U1_CX, U1_CY = 96.52, 55.88         # 38*G, 22*G
    p = s.component("Custom:Ag9905M","U1","Ag9905M",
                    "Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical",
                    U1_CX, U1_CY)
    s.label("POE_A+", *p["1"])
    s.label("POE_A-", *p["2"])
    s.label("POE_B+", *p["3"])
    s.label("POE_B-", *p["4"])
    s.power("+12V",    *p["5"], pin_type="power_out")  # VOUT_P drives +12V rail
    s.power("GND_PRI", *p["6"], pin_type="power_out")  # VOUT_N = primary-side GND
    # /SD: leave as no_connect (internal pull-up keeps module on)
    s.no_connect(*p["7"])
    s.no_connect(*p["8"])                # FLT: not monitored in v0.1

    # -----------------------------------------------------------------------
    # U2 – LM2596S-5.0 step-down (12 V → 5 V for Waveshare ESP32-P4-ETH)
    # -----------------------------------------------------------------------
    s.text("5V Regulator (LM2596)", 25, 98, size=2.54, bold=True, color=BLUE)
    U2_CX, U2_CY = 73.66, 127.0         # 29*G, 50*G
    p = s.component("Custom:LM2596-5.0","U2","LM2596-5.0",
                    "Package_TO_SOT_SMD:TO-263-5_TabPin3",
                    U2_CX, U2_CY)
    s.power("+12V",  *p["1"])            # IN: draw from +12V rail
    s.power("GND",   *p["3"])            # GND (secondary side)
    s.power("GND",   *p["5"])            # /ON tied to GND = always enable
    s.label("+5V_SW", *p["2"], angle=180) # switch node output
    s.power("+5V",    *p["4"])           # FB connected to output rail (fixed 5.0V)

    # D1 – freewheeling Schottky (1N5822), anode = SW node, cathode = GND
    D1_CX, D1_CY = 108.0, 127.0
    p = s.component("Custom:D_Schottky","D1","1N5822",
                    "Diode_THT:D_DO-201AD_P12.70mm_Horizontal",
                    D1_CX, D1_CY)
    s.label("+5V_SW", *p["1"])           # anode
    s.power("GND",     *p["2"])          # cathode → GND (secondary)

    # L1 – 68 uH output inductor (SW → +5V)
    L1_CX, L1_CY = 127.0, 127.0
    p = s.component("Custom:L","L1","68uH",
                    "Inductor_THT:L_Axial_L11.0mm_D4.5mm_P15.24mm_Horizontal_Fastron_MECC",
                    L1_CX, L1_CY)
    s.label("+5V_SW", *p["1"])
    # +5V output: use power_out type to drive the +5V net
    s.power("+5V", *p["2"], pin_type="power_out")

    # C1 – 100 uF / 25 V input bulk cap
    C1_CX, C1_CY = 58.42, 142.24
    p = s.component("Custom:C","C1","100uF/25V",
                    "Capacitor_THT:C_Radial_D8.0mm_H11.5mm_P3.50mm",
                    C1_CX, C1_CY)
    s.power("+12V", *p["1"])             # also place +12V symbol here (drives net)
    s.power("GND",  *p["2"])

    # C2 – 100 uF / 16 V output bulk cap (5V rail — 16V rating for safety margin)
    C2_CX, C2_CY = 144.78, 142.24
    p = s.component("Custom:C","C2","100uF/16V",
                    "Capacitor_THT:C_Radial_D8.0mm_H11.5mm_P3.50mm",
                    C2_CX, C2_CY)
    s.power("+5V", *p["1"])
    s.power("GND",  *p["2"])

    # -----------------------------------------------------------------------
    # D2 – USB back-feed protection (1N5822)
    # Anode = +5V (from LM2596 output), Cathode = +5V_HAT (to J8 pins 2,4)
    # Prevents back-feeding PC USB host when Waveshare programmed via USB-C
    # while PoE is live. Vf ≈ 0.35V → +5V_HAT ≈ 4.65V at J8.
    # -----------------------------------------------------------------------
    D2_CX, D2_CY = 160.02, 127.0        # right of L1 (L1_CX=127), on +5V → +5V_HAT path
    p = s.component("Custom:D_Schottky","D2","1N5822",
                    "Diode_THT:D_DO-201AD_P12.70mm_Horizontal",
                    D2_CX, D2_CY)
    s.power("+5V",       *p["1"])        # anode ← +5V rail
    s.label("+5V_HAT",   *p["2"])        # cathode → +5V_HAT label → J8 pins 2,4

    # -----------------------------------------------------------------------
    # Status LED circuit (R3, LED1) — connected to STATUS_LED global label from J8
    # -----------------------------------------------------------------------
    R3_CX, R3_CY = 178.0, 220.0        # fixed position (U3 removed)
    p1 = s.component("Custom:R","R3","330R","Resistor_SMD:R_0402_1005Metric",
                     R3_CX, R3_CY)
    s.global_label("STATUS_LED", *p1["1"], shape="input")
    s.label("LED_A", *p1["2"])

    # LED1 – status LED
    LED1_CX = R3_CX + 3 * G
    LED1_CY = R3_CY
    p1 = s.component("Custom:LED","LED1","LED_GREEN","LED_THT:LED_D3.0mm",
                     LED1_CX, LED1_CY)
    s.label("LED_A", *p1["1"])
    s.power("GND",   *p1["2"])

    # -----------------------------------------------------------------------
    # NTC temperature sensor circuit (R4, NTC1) — NTC_ADC comes from J8
    # -----------------------------------------------------------------------
    R4_CX, R4_CY = 178.0, 240.0        # fixed position (below R3/LED1)
    p1 = s.component("Custom:R","R4","10k","Resistor_SMD:R_0402_1005Metric",
                     R4_CX, R4_CY)
    s.power("+3V3",    *p1["1"])         # +3V3 from J8 pins 1,17 (Waveshare LDO)
    s.global_label("NTC_ADC", *p1["2"], shape="output", angle=180)

    # NTC1 – thermistor (bottom half of divider)
    NTC1_CX, NTC1_CY = 178.0, R4_CY + 5 * G
    p1 = s.component("Custom:NTC","NTC1","NTC10K_B3950",
                     "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
                     NTC1_CX, NTC1_CY)
    s.global_label("NTC_ADC", *p1["1"], shape="output")
    s.power("GND",     *p1["2"])

    # -----------------------------------------------------------------------
    # Fan headers J2-J5 + TACH pull-up resistors R5-R8
    # -----------------------------------------------------------------------
    s.text("Fan Headers (4× PWM)", 305, 18, size=2.54, bold=True, color=BLUE)

    fan_data = [
        ("FAN1_PWM", "FAN1_TACH"),
        ("FAN2_PWM", "FAN2_TACH"),
        ("FAN3_PWM", "FAN3_TACH"),
        ("FAN4_PWM", "FAN4_TACH"),
    ]

    for i, (pwm_net, tach_net) in enumerate(fan_data):
        FJ_CX = 330.2    # 130*G
        FJ_CY = 35.56 + i * 40 * G   # well-spaced

        # Fan header
        p = s.component("Custom:Fan_Header", f"J{2+i}", f"FAN{i+1}",
                        "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
                        FJ_CX, FJ_CY)
        s.power("GND",    *p["1"])
        s.power("+12V",   *p["2"])
        s.global_label(tach_net, *p["3"], shape="output")
        s.global_label(pwm_net,  *p["4"], shape="input")

        # TACH pull-up resistor (R5-R8): +3V3 from J8 → TACH pin
        FR_CX = FJ_CX - 30 * G
        FR_CY = p["3"][1]   # same y as TACH pin
        pr = s.component("Custom:R", f"R{5+i}", "10k",
                         "Resistor_SMD:R_0402_1005Metric", FR_CX, FR_CY)
        s.power("+3V3",              *pr["1"])
        s.global_label(tach_net,     *pr["2"], shape="output")

    # -----------------------------------------------------------------------
    # J8 – Waveshare ESP32-P4-ETH Interface (2×20 HAT header)
    # Waveshare board mounts on top (HAT-style). J8 pins:
    #   Pins 2,4: +5V_HAT from LM2596S-5.0 via D2 → powers Waveshare board
    #   Pins 1,17: +3V3 from Waveshare's internal LDO → TACH pull-ups, NTC divider
    #   GPIO signals: FAN1-4 PWM/TACH (output/input), NTC_ADC, STATUS_LED
    # NOTE: GPIO28 (pad 35) = ETH_MDIO internal to Waveshare — not connected on carrier
    # NOTE: UART0 (GPIO38/39) is via Waveshare's CH343P USB-C — not on J8 header
    # -----------------------------------------------------------------------
    s.text("Waveshare ESP32-P4-ETH Interface (J8)", 25, 255, size=2.54, bold=True, color=BLUE)
    J8_CX, J8_CY = 101.6, 330.2         # 40*G, 130*G
    p = s.component("Custom:J8_Waveshare", "J8", "Waveshare_ESP32P4ETH",
                    "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical",
                    J8_CX, J8_CY)

    # Power rails — Waveshare 3.3V drives +3V3 net on carrier PCB
    s.power("+3V3", *p["1"],  pin_type="power_out")   # 3V3 from Waveshare LDO (pin 1)
    s.power("+3V3", *p["17"], pin_type="power_out")   # 3V3 duplicate (pin 17)

    # Power rails — carrier +5V_HAT goes into Waveshare via pins 2,4
    s.label("+5V_HAT", *p["2"])    # 5V input from carrier (via D2)
    s.label("+5V_HAT", *p["4"])    # 5V duplicate

    # GND connections for all GND pins on J8
    s.power("GND", *p["9"])
    s.power("GND", *p["25"])
    s.power("GND", *p["29"])
    s.power("GND", *p["33"])
    s.power("GND", *p["6"])
    s.power("GND", *p["14"])
    s.power("GND", *p["20"])
    s.power("GND", *p["38"])

    # Fan PWM outputs (from Waveshare GPIO → fan headers on carrier)
    s.global_label("FAN1_PWM",  *p["7"],  shape="output")
    s.global_label("FAN2_PWM",  *p["8"],  shape="output")
    s.global_label("FAN3_PWM",  *p["10"], shape="output")
    s.global_label("FAN4_PWM",  *p["11"], shape="output")

    # Fan TACH inputs (from fan headers on carrier → Waveshare GPIO)
    s.global_label("FAN1_TACH", *p["12"], shape="input")
    s.global_label("FAN2_TACH", *p["13"], shape="input")
    s.global_label("FAN3_TACH", *p["15"], shape="input")
    s.global_label("FAN4_TACH", *p["16"], shape="input")

    # Temperature ADC (from NTC circuit on carrier → Waveshare GPIO16)
    s.global_label("NTC_ADC",    *p["23"], shape="input")

    # Status LED (from Waveshare GPIO2 → LED circuit on carrier)
    s.global_label("STATUS_LED", *p["3"],  shape="output")

    return s
