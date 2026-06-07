"""
build_schematic(): places all components for the PoE FanController.

Extracted from hardware/generate_project.py (pure mechanical refactor — no logic changes).
"""

from .schematic import Schematic
from .utils import G


# ---------------------------------------------------------------------------
# Build schematic
# ---------------------------------------------------------------------------
def build_schematic():
    s = Schematic()

    # -----------------------------------------------------------------------
    # Symbol definitions  (body_w, body_h MUST be multiples of G=2.54)
    # -----------------------------------------------------------------------

    # RJ45: 8-pin Amphenol 54602 (pads 1-8 match footprint exactly)
    # PoE pairs share the physical Ethernet conductors (mode A: 1,2/3,6; mode B: 4,5/7,8)
    s.define("Custom:RJ45_PoE", "J", "RJ45_PoE",
             "Connector_RJ:RJ45_Amphenol_54602-x08_Horizontal", "~",
             body_w=15.24, body_h=22.86,
             pins_left=[
                 ("P1",  "1", "passive"),   # PoE mode A pair: +
                 ("P2",  "2", "passive"),   # PoE mode A pair: +
                 ("P3",  "3", "passive"),   # PoE mode A pair: –
                 ("P4",  "4", "passive"),   # PoE mode B pair: +
                 ("P5",  "5", "passive"),   # PoE mode B pair: +
                 ("P6",  "6", "passive"),   # PoE mode A pair: –
                 ("P7",  "7", "passive"),   # PoE mode B pair: –
                 ("P8",  "8", "passive"),   # PoE mode B pair: –
             ],
             pins_right=[])

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

    # LM2596-3.3: 3 left (IN, GND, /ON), 2 right (OUT, FB)
    s.define("Custom:LM2596-3.3", "U", "LM2596-3.3",
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

    # ESP32-WROOM-32: 19 left (pads 1-19) + 20 right (pads 20-39, incl. exposed GND pad)
    # Pin numbers match RF_Module:ESP32-WROOM-32 footprint pads exactly.
    s.define("Custom:ESP32-WROOM-32", "U", "ESP32-WROOM-32",
             "RF_Module:ESP32-WROOM-32",
             "https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf",
             body_w=30.48, body_h=50.80,
             pins_left=[
                 ("GND",       "1",  "power_in"),
                 ("VDD",       "2",  "power_in"),
                 ("EN",        "3",  "input"),
                 ("SENSOR_VP", "4",  "input"),       # GPIO36
                 ("SENSOR_VN", "5",  "input"),       # GPIO39
                 ("IO34",      "6",  "input"),
                 ("IO35",      "7",  "input"),
                 ("IO32",      "8",  "bidirectional"),
                 ("IO33",      "9",  "bidirectional"),
                 ("IO25",      "10", "bidirectional"),
                 ("IO26",      "11", "bidirectional"),
                 ("IO27",      "12", "bidirectional"),
                 ("IO14",      "13", "bidirectional"),
                 ("IO12",      "14", "bidirectional"),
                 ("GND",       "15", "passive"),
                 ("IO13",      "16", "bidirectional"),
                 ("SHD/SD2",   "17", "bidirectional"),
                 ("SWP/SD3",   "18", "bidirectional"),
                 ("SCS/CMD",   "19", "bidirectional"),
             ],
             pins_right=[
                 ("SCK/CLK",   "20", "bidirectional"),
                 ("SDO/SD0",   "21", "bidirectional"),
                 ("SDI/SD1",   "22", "bidirectional"),
                 ("IO15",      "23", "bidirectional"),
                 ("IO2",       "24", "bidirectional"),
                 ("IO0",       "25", "bidirectional"),
                 ("IO4",       "26", "bidirectional"),
                 ("IO16",      "27", "bidirectional"),
                 ("IO17",      "28", "bidirectional"),
                 ("IO5",       "29", "bidirectional"),
                 ("IO18",      "30", "bidirectional"),
                 ("IO19",      "31", "bidirectional"),
                 ("NC",        "32", "no_connect"),
                 ("IO21",      "33", "bidirectional"),
                 ("RXD0/IO3",  "34", "bidirectional"),
                 ("TXD0/IO1",  "35", "bidirectional"),
                 ("IO22",      "36", "bidirectional"),
                 ("IO23",      "37", "bidirectional"),
                 ("GND",       "38", "passive"),
                 ("GND_PAD",   "39", "passive"),     # exposed bottom GND pad
             ])

    # CH340C: 8 left, 8 right
    s.define("Custom:CH340C", "U", "CH340C",
             "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
             "https://www.wch-ic.com/downloads/CH340DS1_PDF.html",
             body_w=22.86, body_h=22.86,
             pins_left=[
                 ("GND", "1",  "power_in"),
                 ("TXD", "2",  "output"),
                 ("RXD", "3",  "input"),
                 ("V3",  "4",  "power_out"),
                 ("UD+", "5",  "bidirectional"),
                 ("UD-", "6",  "bidirectional"),
                 ("XI",  "7",  "input"),
                 ("XO",  "8",  "output"),
             ],
             pins_right=[
                 ("VCC", "16", "power_in"),
                 ("DTR", "15", "output"),
                 ("RTS", "14", "output"),
                 ("CTS", "13", "input"),
                 ("DSR", "12", "output"),
                 ("RI",  "11", "output"),
                 ("DCD", "10", "input"),
                 ("CKO", "9",  "output"),
             ])

    # 4-pin fan header
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

    # USB Type-C receptacle (GCT USB4085 full-featured, 20-pin)
    s.define("Custom:USB_C", "J", "USB_C",
             "Connector_USB:USB_C_Receptacle_GCT_USB4085", "~",
             body_w=15.24, body_h=20.32,
             pins_left=[
                 ("GND",  "A1", "passive"),
                 ("VBUS", "A4", "power_in"),
                 ("CC1",  "A5", "passive"),
                 ("D+",   "A6", "bidirectional"),
                 ("D-",   "A7", "bidirectional"),
                 ("CC2",  "B5", "passive"),
                 ("SHLD", "SH", "passive"),
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

    s.define("Custom:SW_Push", "SW", "SW_Push",
             "Button_Switch_THT:SW_PUSH_6mm", "~",
             body_w=7.62, body_h=5.08,
             pins_left=[("1", "1", "passive"), ("2", "2", "passive")],
             pins_right=[])

    s.define("Custom:NTC", "NTC", "NTC_10K",
             "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", "~",
             body_w=5.08, body_h=2.54,
             pins_left=[("1", "1", "passive")],
             pins_right=[("2", "2", "passive")])

    s.define("Custom:Header3", "J", "Header_3pin",
             "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", "~",
             body_w=7.62, body_h=10.16,
             pins_left=[("GND","1","passive"),("TX","2","passive"),("RX","3","passive")],
             pins_right=[])

    # -----------------------------------------------------------------------
    # 2. Component placement
    #
    # All centres on 2.54 mm (G) grid. Using named variables for readability.
    # Diagram regions on A2 (594 × 420 mm):
    #   POE_IN  : x=25..110,  y=30..100
    #   BUCK    : x=25..145,  y=110..185
    #   ESP32   : x=155..295, y=30..210
    #   FANS    : x=305..420, y=30..200
    #   USB_UART: x=25..195,  y=215..385
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # J1 – RJ45 with PoE
    # -----------------------------------------------------------------------
    BLUE = (0, 0, 255)
    s.text("PoE Power Input", 25, 18, size=2.54, bold=True, color=BLUE)
    J1_CX, J1_CY = 38.1, 55.88          # 15*G, 22*G
    p = s.component("Custom:RJ45_PoE","J1","RJ45_PoE",
                    "Connector_RJ:RJ45_Amphenol_54602-x08_Horizontal",
                    J1_CX, J1_CY)
    # Pins 1,2 = mode-A pair (+); pins 3,6 = mode-A pair (–)
    # Pins 4,5 = mode-B pair (+); pins 7,8 = mode-B pair (–)
    s.label("POE_A+", *p["1"])
    s.label("POE_A+", *p["2"])
    s.label("POE_A-", *p["3"])
    s.label("POE_B+", *p["4"])
    s.label("POE_B+", *p["5"])
    s.label("POE_A-", *p["6"])
    s.label("POE_B-", *p["7"])
    s.label("POE_B-", *p["8"])

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
    # U2 – LM2596-3.3 step-down (12 V → 3.3 V)
    # -----------------------------------------------------------------------
    s.text("3.3V Regulator (LM2596)", 25, 98, size=2.54, bold=True, color=BLUE)
    U2_CX, U2_CY = 73.66, 127.0         # 29*G, 50*G
    p = s.component("Custom:LM2596-3.3","U2","LM2596-3.3",
                    "Package_TO_SOT_SMD:TO-263-5_TabPin3",
                    U2_CX, U2_CY)
    s.power("+12V",  *p["1"])            # IN: draw from +12V rail
    s.power("GND",   *p["3"])            # GND (secondary side)
    s.power("GND",   *p["5"])            # /ON tied to GND = always enable
    s.label("+3V3_SW", *p["2"], angle=180)  # switch node output
    s.power("+3V3",    *p["4"])                  # FB connected to output rail (fixed 3.3V)

    # D1 – freewheeling Schottky (1N5822), anode = SW node, cathode = GND
    D1_CX, D1_CY = 108.0, 127.0
    p = s.component("Custom:D_Schottky","D1","1N5822",
                    "Diode_THT:D_DO-201AD_P12.70mm_Horizontal",
                    D1_CX, D1_CY)
    s.label("+3V3_SW", *p["1"])          # anode
    s.power("GND",     *p["2"])          # cathode → GND (secondary)

    # L1 – 68 uH output inductor (SW → +3V3)
    L1_CX, L1_CY = 127.0, 127.0
    p = s.component("Custom:L","L1","68uH",
                    "Inductor_THT:L_Axial_L11.0mm_D4.5mm_P15.24mm_Horizontal_Fastron_MECC",
                    L1_CX, L1_CY)
    s.label("+3V3_SW", *p["1"])
    # +3V3 output: use power_out type to drive the +3V3 net (suppresses ERC warning)
    s.power("+3V3", *p["2"], pin_type="power_out")

    # C1 – 100 uF / 25 V input bulk cap
    C1_CX, C1_CY = 58.42, 142.24
    p = s.component("Custom:C","C1","100uF/25V",
                    "Capacitor_THT:C_Radial_D8.0mm_H11.5mm_P3.50mm",
                    C1_CX, C1_CY)
    s.power("+12V", *p["1"])             # also place +12V symbol here (drives net)
    s.power("GND",  *p["2"])

    # C2 – 100 uF / 10 V output bulk cap
    C2_CX, C2_CY = 144.78, 142.24
    p = s.component("Custom:C","C2","100uF/10V",
                    "Capacitor_THT:C_Radial_D8.0mm_H11.5mm_P3.50mm",
                    C2_CX, C2_CY)
    s.power("+3V3", *p["1"])
    s.power("GND",  *p["2"])

    # C3-C6 – 100nF decoupling caps on 3.3V rail (placed near ESP32)
    for i in range(4):
        cx = 147.32 + i * G * 3
        cy = 160.02
        p = s.component("Custom:C", f"C{3+i}", "100nF",
                        "Capacitor_SMD:C_0402_1005Metric", cx, cy)
        s.power("+3V3", *p["1"])
        s.power("GND",  *p["2"])

    # -----------------------------------------------------------------------
    # U3 – ESP32-WROOM-32
    # -----------------------------------------------------------------------
    s.text("ESP32-WROOM-32", 155, 18, size=2.54, bold=True, color=BLUE)
    U3_CX, U3_CY = 218.44, 109.22       # 86*G, 43*G
    p = s.component("Custom:ESP32-WROOM-32","U3","ESP32-WROOM-32",
                    "RF_Module:ESP32-WROOM-32",
                    U3_CX, U3_CY)
    # Power pins
    s.power("GND",   *p["1"])            # pad 1 = GND (left, top)
    s.power("+3V3",  *p["2"])            # pad 2 = VDD
    s.power("GND",   *p["15"])           # pad 15 = GND (mid-left)
    s.power("GND",   *p["38"])           # pad 38 = GND (right, bottom)
    s.power("GND",   *p["39"])           # pad 39 = exposed bottom GND pad

    # Signal pins – left side (pads 3-19)
    # EN/BOOT use global labels — driven by R1/SW1 and R2/SW2 respectively
    s.global_label("ESP_EN",    *p["3"],  shape="input")
    s.global_label("FAN3_TACH", *p["4"],  shape="input")  # SENSOR_VP = GPIO36
    s.global_label("FAN4_TACH", *p["5"],  shape="input")  # SENSOR_VN = GPIO39
    s.global_label("FAN1_TACH", *p["6"],  shape="input")  # IO34
    s.global_label("FAN2_TACH", *p["7"],  shape="input")  # IO35
    s.global_label("NTC_ADC",   *p["8"],  shape="input")  # IO32 — reads ADC voltage
    s.no_connect(               *p["9"])                   # IO33
    s.global_label("FAN1_PWM",  *p["10"], shape="output") # IO25
    s.global_label("FAN2_PWM",  *p["11"], shape="output") # IO26
    s.global_label("FAN3_PWM",  *p["12"], shape="output") # IO27
    s.global_label("FAN4_PWM",  *p["13"], shape="output") # IO14
    s.no_connect(               *p["14"])                  # IO12
    for pn in ["16","17","18","19"]:
        s.no_connect(*p[pn])             # IO13, SD2, SD3, CMD (flash interface)

    # Signal pins – right side (pads 20-37)
    for pn in ["20","21","22"]:
        s.no_connect(*p[pn])             # CLK, SD0, SD1 (flash interface)
    s.no_connect(*p["23"])               # IO15
    s.label("GPIO2",   *p["24"], angle=180)  # IO2 → status LED (local — same block)
    s.global_label("BOOT",    *p["25"], shape="passive", angle=180)  # IO0 → BOOT button
    s.no_connect(*p["26"])               # IO4
    for pn in ["27","28","29","30","31"]:
        s.no_connect(*p[pn])             # IO16, IO17, IO5, IO18, IO19
    s.no_connect(*p["32"])               # NC (module internal)
    s.no_connect(*p["33"])               # IO21
    s.global_label("ESP_RX",  *p["34"], shape="input",  angle=180)  # RXD0
    s.global_label("ESP_TX",  *p["35"], shape="output", angle=180)  # TXD0
    s.no_connect(*p["36"])               # IO22
    s.no_connect(*p["37"])               # IO23

    # -----------------------------------------------------------------------
    # ESP32 support: R1 (EN pull-up), SW1 (RESET), R2 (IO0 pull-up), SW2 (BOOT)
    # -----------------------------------------------------------------------
    # R1 – 10k EN pull-up (pad 3 is left-side)
    R1_CX, R1_CY = 178.0, p["3"][1]   # same y as EN pin
    p1 = s.component("Custom:R","R1","10k","Resistor_SMD:R_0402_1005Metric",
                     R1_CX, R1_CY)
    s.power("+3V3",             *p1["1"])
    s.global_label("ESP_EN",    *p1["2"], shape="input")

    # SW1 – RESET button
    SW1_CX, SW1_CY = 178.0, R1_CY + 5 * G
    p1 = s.component("Custom:SW_Push","SW1","RESET",
                     "Button_Switch_THT:SW_PUSH_6mm", SW1_CX, SW1_CY)
    s.global_label("ESP_EN", *p1["1"], shape="input")
    s.power("GND",            *p1["2"])

    # R2 – 10k IO0 pull-up (pad 25 is right-side)
    R2_CX, R2_CY = 178.0, p["25"][1]  # same y as IO0 pin
    p1 = s.component("Custom:R","R2","10k","Resistor_SMD:R_0402_1005Metric",
                     R2_CX, R2_CY)
    s.power("+3V3",           *p1["1"])
    s.global_label("BOOT",    *p1["2"], shape="passive")

    # SW2 – BOOT button  (placed 10*G below SW1 to avoid pin coordinate collision)
    SW2_CX, SW2_CY = 178.0, SW1_CY + 10 * G
    p1 = s.component("Custom:SW_Push","SW2","BOOT",
                     "Button_Switch_THT:SW_PUSH_6mm", SW2_CX, SW2_CY)
    s.global_label("BOOT", *p1["1"], shape="passive")
    s.power("GND",          *p1["2"])

    # R3 – 330R LED resistor (pad 24 = IO2)
    R3_CX, R3_CY = 178.0, p["24"][1]  # same y as IO2 pin
    p1 = s.component("Custom:R","R3","330R","Resistor_SMD:R_0402_1005Metric",
                     R3_CX, R3_CY)
    s.label("GPIO2", *p1["1"])
    s.label("LED_A", *p1["2"])

    # LED1 – status LED
    LED1_CX = R3_CX + 3 * G
    LED1_CY = R3_CY
    p1 = s.component("Custom:LED","LED1","LED_GREEN","LED_THT:LED_D3.0mm",
                     LED1_CX, LED1_CY)
    s.label("LED_A", *p1["1"])
    s.power("GND",   *p1["2"])

    # R4 – 10k NTC voltage divider (top half, pad 8 = IO32)
    R4_CX, R4_CY = 178.0, p["8"][1]   # same y as IO32 pin
    p1 = s.component("Custom:R","R4","10k","Resistor_SMD:R_0402_1005Metric",
                     R4_CX, R4_CY)
    s.power("+3V3",    *p1["1"])
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

        # TACH pull-up resistor (R5-R8): +3V3 → TACH pin
        FR_CX = FJ_CX - 30 * G
        FR_CY = p["3"][1]   # same y as TACH pin
        pr = s.component("Custom:R", f"R{5+i}", "10k",
                         "Resistor_SMD:R_0402_1005Metric", FR_CX, FR_CY)
        s.power("+3V3",              *pr["1"])
        s.global_label(tach_net,     *pr["2"], shape="output")

    # -----------------------------------------------------------------------
    # USB Type-C connector (J6) + CC resistors R9/R10
    # -----------------------------------------------------------------------
    s.text("USB / UART Bridge", 25, 203, size=2.54, bold=True, color=BLUE)
    J6_CX, J6_CY = 55.88, 264.16        # 22*G, 104*G
    p = s.component("Custom:USB_C","J6","USB_C_2.0",
                    "Connector_USB:USB_C_Receptacle_GCT_USB4085",
                    J6_CX, J6_CY)
    s.power("GND",    *p["A1"])
    s.no_connect(*p["A4"])               # VBUS – not used (bus-powered from PoE)
    s.global_label("USB_DP", *p["A6"], shape="bidirectional")
    s.global_label("USB_DN", *p["A7"], shape="bidirectional")
    # CC1 / CC2 pull-down to GND (5.1k resistors R9/R10)
    s.label("CC1", *p["A5"])
    s.label("CC2", *p["B5"])
    s.no_connect(*p["SH"])               # shield

    # R9 – CC1 pull-down (5.1k to GND)
    R9_CX = J6_CX - 5 * G
    R9_CY = J6_CY + 8 * G
    p9 = s.component("Custom:R","R9","5.1k","Resistor_SMD:R_0402_1005Metric",
                     R9_CX, R9_CY)
    s.label("CC1",  *p9["1"])
    s.power("GND",  *p9["2"])

    # R10 – CC2 pull-down
    R10_CX = R9_CX + 4 * G
    R10_CY = R9_CY
    p10 = s.component("Custom:R","R10","5.1k","Resistor_SMD:R_0402_1005Metric",
                      R10_CX, R10_CY)
    s.label("CC2",  *p10["1"])
    s.power("GND",  *p10["2"])

    # -----------------------------------------------------------------------
    # U4 – CH340C USB-UART bridge
    # -----------------------------------------------------------------------
    U4_CX, U4_CY = 127.0, 264.16        # 50*G, 104*G
    p = s.component("Custom:CH340C","U4","CH340C",
                    "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
                    U4_CX, U4_CY)
    s.power("GND",    *p["1"])           # GND
    s.global_label("ESP_RX", *p["2"], shape="output") # TXD → ESP RXD0
    s.global_label("ESP_TX", *p["3"], shape="input")  # RXD ← ESP TXD0
    s.label("CH340_V3", *p["4"])         # V3: internal 3.3V, decouple with C7
    s.global_label("USB_DP",   *p["5"], shape="bidirectional")
    s.global_label("USB_DN",   *p["6"], shape="bidirectional")
    s.no_connect(*p["7"])                # XI (no crystal)
    s.no_connect(*p["8"])                # XO
    s.power("+3V3",   *p["16"])          # VCC
    s.global_label("BOOT",   *p["15"], shape="passive",  angle=180)  # DTR → GPIO0 auto-boot
    s.global_label("ESP_EN", *p["14"], shape="input",    angle=180)  # RTS → EN auto-reset
    s.no_connect(*p["13"])               # CTS
    s.no_connect(*p["12"])               # DSR
    s.no_connect(*p["11"])               # RI
    s.no_connect(*p["10"])               # DCD
    s.no_connect(*p["9"])                # CKO

    # C7 – V3 decoupling cap (100nF)
    C7_CX = U4_CX - 10 * G
    C7_CY = p["4"][1]
    p7 = s.component("Custom:C","C7","100nF",
                     "Capacitor_SMD:C_0402_1005Metric", C7_CX, C7_CY)
    s.label("CH340_V3", *p7["1"])
    s.power("GND",       *p7["2"])

    # -----------------------------------------------------------------------
    # J7 – Debug UART header (GND, TX, RX)
    # -----------------------------------------------------------------------
    J7_CX, J7_CY = 172.72, 264.16        # 68*G, 104*G
    p = s.component("Custom:Header3","J7","Debug_UART",
                    "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
                    J7_CX, J7_CY)
    s.power("GND",              *p["1"])
    s.global_label("ESP_TX",    *p["2"], shape="input")
    s.global_label("ESP_RX",    *p["3"], shape="output")

    return s
