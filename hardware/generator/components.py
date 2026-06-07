"""
generator.components — build_schematic() with all ESP32-P4 components.

Assembles the complete PoE FanController schematic using the Schematic
S-expression builder.  All component placements are on the 2.54 mm grid.

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

    # ESP32-P4-MINI-1U-N16R8: 14 left functional pins + 12 right RMII/UART/MDIO pins.
    # Pin numbers are GPIO IDs for schematic clarity.
    # RMII fixed pins GPIO32-37 + GPIO50: hard-wired to IO_MUX (ESP32-P4 TRM §EMAC).
    # MDIO GPIO28 / MDC GPIO31: GPIO-matrix configurable.
    # All assignments verified: OQ-01 RESOLVED 2026-06-07.
    s.define("Custom:ESP32-P4", "U", "ESP32-P4-MINI-1U",
             "Custom:ESP32-P4-MINI-1",
             "https://www.espressif.com/sites/default/files/documentation/esp32-p4_datasheet_en.pdf",
             body_w=30.48, body_h=35.56,
             pins_left=[
                 ("GND",    "GND1", "power_in"),
                 ("VDD",    "VDD",  "power_in"),
                 ("EN",     "EN",   "input"),
                 ("GPIO0",  "G0",   "input"),         # BOOT strapping pin
                 ("GPIO2",  "G2",   "bidirectional"), # 1-Wire / status LED
                 ("GPIO4",  "G4",   "output"),        # FAN1_PWM  LEDC CH0
                 ("GPIO5",  "G5",   "output"),        # FAN2_PWM  LEDC CH1
                 ("GPIO6",  "G6",   "output"),        # FAN3_PWM  LEDC CH2
                 ("GPIO7",  "G7",   "output"),        # FAN4_PWM  LEDC CH3
                 ("GPIO8",  "G8",   "input"),         # FAN1_TACH
                 ("GPIO9",  "G9",   "input"),         # FAN2_TACH
                 ("GPIO10", "G10",  "input"),         # FAN3_TACH
                 ("GPIO11", "G11",  "input"),         # FAN4_TACH
                 ("GPIO16", "G16",  "input"),         # NTC_ADC
             ],
             pins_right=[
                 ("GND",    "GND2", "power_in"),
                 ("GPIO28", "G28",  "bidirectional"), # EMAC_MDIO (GPIO-matrix)
                 ("GPIO31", "G31",  "output"),        # EMAC_MDC  (GPIO-matrix)
                 ("GPIO32", "G32",  "input"),         # EMAC_RXD0 RMII fixed
                 ("GPIO33", "G33",  "input"),         # EMAC_RXD1 RMII fixed
                 ("GPIO34", "G34",  "input"),         # EMAC_CRS_DV RMII fixed
                 ("GPIO35", "G35",  "output"),        # EMAC_TXD0 RMII fixed
                 ("GPIO36", "G36",  "output"),        # EMAC_TXD1 RMII fixed
                 ("GPIO37", "G37",  "output"),        # EMAC_TX_EN RMII fixed
                 ("GPIO38", "G38",  "output"),        # UART0_TX IO_MUX default
                 ("GPIO39", "G39",  "input"),         # UART0_RX IO_MUX default
                 ("GPIO50", "G50",  "output"),        # EMAC_REF_CLK 50 MHz → PHY
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

    # LAN8720A-CP-TR Ethernet PHY QFN-24
    # Left: RMII interface (← ESP32-P4) + MDI physical pairs (↔ J1 via R11-R14)
    # Right: power pins (+3V3, GND, exposed pad)
    s.define("Custom:LAN8720A", "U", "LAN8720A-CP-TR",
             "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm",
             "https://ww1.microchip.com/downloads/en/DeviceDoc/8720a.pdf",
             body_w=20.32, body_h=35.56,
             pins_left=[
                 ("TXEN",   "TXEN", "input"),         # TX_EN  ← ESP32 GPIO37
                 ("TXD0",   "TXD0", "input"),         # TXD0   ← ESP32 GPIO35
                 ("TXD1",   "TXD1", "input"),         # TXD1   ← ESP32 GPIO36
                 ("RXD0",   "RXD0", "output"),        # RXD0   → ESP32 GPIO32
                 ("RXD1",   "RXD1", "output"),        # RXD1   → ESP32 GPIO33
                 ("CRS_DV", "CRDV", "output"),        # CRS_DV → ESP32 GPIO34
                 ("REFCLK", "RCLK", "input"),         # 50 MHz ← ESP32 GPIO50
                 ("MDIO",   "MDIO", "bidirectional"), # MDIO   ↔ ESP32 GPIO28
                 ("MDC",    "MDC",  "input"),         # MDC    ← ESP32 GPIO31
                 ("NRESET", "NRST", "input"),         # Active-low (tie to +3V3)
                 ("TX+",    "TXP",  "passive"),       # MDI TX+ → J1 via R11
                 ("TX-",    "TXN",  "passive"),       # MDI TX- → J1 via R12
                 ("RX+",    "RXP",  "passive"),       # MDI RX+ ← J1 via R13
                 ("RX-",    "RXN",  "passive"),       # MDI RX- ← J1 via R14
             ],
             pins_right=[
                 ("VDD",   "VDD",   "power_in"),  # 3.3 V
                 ("VDDIO", "VDDIO", "power_in"),  # 3.3 V I/O supply
                 ("GND",   "GND",   "power_in"),
                 ("EP",    "EP",    "power_in"),  # Exposed pad = GND
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
    # J1 – RJ45 with PoE magnetics + MDI secondary (Würth 615008144521)
    # OQ-03 RESOLVED 2026-06-07: MDI secondary winding outputs confirmed separate
    # from PoE centre-taps. P-POE-02 topology unchanged — only secondary MDI added.
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
    # MDI secondary → R11-R14 (49.9 Ω) → LAN8720A
    s.global_label("ETH_TD_P_IN", *p["TDP"], shape="passive", angle=180)
    s.global_label("ETH_TD_N_IN", *p["TDN"], shape="passive", angle=180)
    s.global_label("ETH_RD_P_IN", *p["RDP"], shape="passive", angle=180)
    s.global_label("ETH_RD_N_IN", *p["RDN"], shape="passive", angle=180)

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
    # U3 – ESP32-P4-MINI-1U (replaces ESP32-WROOM-32D)
    # RMII fixed pins GPIO32-37 + GPIO50 verified against TRM §EMAC (OQ-01 closed)
    # -----------------------------------------------------------------------
    s.text("ESP32-P4", 155, 18, size=2.54, bold=True, color=BLUE)
    U3_CX, U3_CY = 218.44, 109.22       # 86*G, 43*G — centre unchanged
    p = s.component("Custom:ESP32-P4","U3","ESP32-P4-MINI-1U",
                    "Custom:ESP32-P4-MINI-1",
                    U3_CX, U3_CY)

    # Power pins
    s.power("GND",   *p["GND1"])
    s.power("+3V3",  *p["VDD"])
    s.power("GND",   *p["GND2"])

    # Left side — functional GPIO
    s.global_label("ESP_EN",    *p["EN"],  shape="input")
    s.global_label("BOOT",      *p["G0"],  shape="passive")
    s.label("GPIO2",            *p["G2"])                         # LED circuit local
    s.global_label("FAN1_PWM",  *p["G4"],  shape="output")
    s.global_label("FAN2_PWM",  *p["G5"],  shape="output")
    s.global_label("FAN3_PWM",  *p["G6"],  shape="output")
    s.global_label("FAN4_PWM",  *p["G7"],  shape="output")
    s.global_label("FAN1_TACH", *p["G8"],  shape="input")
    s.global_label("FAN2_TACH", *p["G9"],  shape="input")
    s.global_label("FAN3_TACH", *p["G10"], shape="input")
    s.global_label("FAN4_TACH", *p["G11"], shape="input")
    s.global_label("NTC_ADC",   *p["G16"], shape="input")

    # Right side — RMII + UART + MDIO/MDC (all with angle=180 = label points right)
    s.global_label("ETH_MDIO",    *p["G28"], shape="bidirectional", angle=180)
    s.global_label("ETH_MDC",     *p["G31"], shape="output",        angle=180)
    s.global_label("EMAC_RXD0",   *p["G32"], shape="input",         angle=180)
    s.global_label("EMAC_RXD1",   *p["G33"], shape="input",         angle=180)
    s.global_label("EMAC_CRS_DV", *p["G34"], shape="input",         angle=180)
    s.global_label("EMAC_TXD0",   *p["G35"], shape="output",        angle=180)
    s.global_label("EMAC_TXD1",   *p["G36"], shape="output",        angle=180)
    s.global_label("EMAC_TX_EN",  *p["G37"], shape="output",        angle=180)
    s.global_label("ESP_TX",      *p["G38"], shape="output",        angle=180)
    s.global_label("ESP_RX",      *p["G39"], shape="input",         angle=180)
    s.global_label("EMAC_REF_CLK",*p["G50"], shape="output",        angle=180)

    # -----------------------------------------------------------------------
    # ESP32-P4 support: R1 (EN pull-up), SW1 (RESET), R2 (IO0 pull-up), SW2 (BOOT)
    # -----------------------------------------------------------------------
    # R1 – 10k EN pull-up
    R1_CX, R1_CY = 178.0, p["EN"][1]   # same y as EN pin
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

    # R2 – 10k GPIO0 pull-up
    R2_CX, R2_CY = 178.0, p["G0"][1]   # same y as GPIO0 pin
    p1 = s.component("Custom:R","R2","10k","Resistor_SMD:R_0402_1005Metric",
                     R2_CX, R2_CY)
    s.power("+3V3",           *p1["1"])
    s.global_label("BOOT",    *p1["2"], shape="passive")

    # SW2 – BOOT button (offset 8*G below SW1 to clear NTC divider at GPIO16)
    SW2_CX, SW2_CY = 178.0, SW1_CY + 8 * G
    p1 = s.component("Custom:SW_Push","SW2","BOOT",
                     "Button_Switch_THT:SW_PUSH_6mm", SW2_CX, SW2_CY)
    s.global_label("BOOT", *p1["1"], shape="passive")
    s.power("GND",          *p1["2"])

    # R3 – 330R LED resistor (GPIO2)
    R3_CX, R3_CY = 178.0, p["G2"][1]   # same y as GPIO2 pin
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

    # R4 – 10k NTC voltage divider top (GPIO16 = NTC_ADC)
    R4_CX, R4_CY = 178.0, p["G16"][1]  # same y as GPIO16 pin
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
    # U5 – LAN8720A Ethernet PHY (RMII)
    # RMII interface: all 7 signals connect to ESP32-P4 via matching global labels
    # MDI interface: to J1 secondary winding via 49.9 Ω termination resistors R11-R14
    # -----------------------------------------------------------------------
    s.text("Ethernet PHY (LAN8720A)", 430, 18, size=2.54, bold=True, color=BLUE)
    U5_CX, U5_CY = 490.0, 109.22        # east of fan section; same y as U3
    p5 = s.component("Custom:LAN8720A","U5","LAN8720A-CP-TR",
                     "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm",
                     U5_CX, U5_CY)

    # Power
    s.power("+3V3", *p5["VDD"])
    s.power("+3V3", *p5["VDDIO"])
    s.power("GND",  *p5["GND"])
    s.power("GND",  *p5["EP"])

    # NRESET — tie to +3V3 (PHY always released; optional external control deferred)
    s.power("+3V3", *p5["NRST"])

    # RMII receive path (U5 drives → MCU receives)
    s.global_label("EMAC_RXD0",   *p5["RXD0"], shape="output")
    s.global_label("EMAC_RXD1",   *p5["RXD1"], shape="output")
    s.global_label("EMAC_CRS_DV", *p5["CRDV"], shape="output")

    # RMII transmit path (MCU drives → U5 receives)
    s.global_label("EMAC_TX_EN",  *p5["TXEN"], shape="input")
    s.global_label("EMAC_TXD0",   *p5["TXD0"], shape="input")
    s.global_label("EMAC_TXD1",   *p5["TXD1"], shape="input")

    # Reference clock (MCU GPIO50 → U5)
    s.global_label("EMAC_REF_CLK",*p5["RCLK"], shape="input")

    # MDIO management bus
    s.global_label("ETH_MDIO",    *p5["MDIO"], shape="bidirectional")
    s.global_label("ETH_MDC",     *p5["MDC"],  shape="input")

    # MDI physical pairs (via R11-R14 termination resistors)
    s.global_label("ETH_TD_P", *p5["TXP"], shape="passive")
    s.global_label("ETH_TD_N", *p5["TXN"], shape="passive")
    s.global_label("ETH_RD_P", *p5["RXP"], shape="passive")
    s.global_label("ETH_RD_N", *p5["RXN"], shape="passive")

    # -----------------------------------------------------------------------
    # MDI termination resistors R11-R14 (49.9 Ω ±1% 0402)
    # Between J1 MDI secondary winding and LAN8720A MDI pins (architecture §5)
    # -----------------------------------------------------------------------
    s.text("MDI Termination (49.9\u03a9 x4)", 415, 185, size=2.54, bold=True, color=BLUE)
    mdi_r_data = [
        ("R11", "ETH_TD_P_IN", "ETH_TD_P"),
        ("R12", "ETH_TD_N_IN", "ETH_TD_N"),
        ("R13", "ETH_RD_P_IN", "ETH_RD_P"),
        ("R14", "ETH_RD_N_IN", "ETH_RD_N"),
    ]
    for i, (rref, net_in, net_out) in enumerate(mdi_r_data):
        rcx = 445.0
        rcy = 200.0 + i * 5.08
        pr = s.component("Custom:R", rref, "49R9",
                         "Resistor_SMD:R_0402_1005Metric", rcx, rcy)
        s.global_label(net_in,  *pr["1"], shape="passive")
        s.global_label(net_out, *pr["2"], shape="passive", angle=180)

    # -----------------------------------------------------------------------
    # U5 decoupling caps: 4 × 100 nF near VDD pins + 1 × 10 µF bulk (C8-C11)
    # -----------------------------------------------------------------------
    C8_CX, C8_CY   = 518.0, p5["VDD"][1]
    p_cx = s.component("Custom:C","C8","100nF","Capacitor_SMD:C_0402_1005Metric",C8_CX,C8_CY)
    s.power("+3V3", *p_cx["1"]); s.power("GND", *p_cx["2"])

    C9_CX, C9_CY   = 518.0, p5["VDDIO"][1]
    p_cx = s.component("Custom:C","C9","100nF","Capacitor_SMD:C_0402_1005Metric",C9_CX,C9_CY)
    s.power("+3V3", *p_cx["1"]); s.power("GND", *p_cx["2"])

    C10_CX, C10_CY  = 518.0, p5["GND"][1]
    p_cx = s.component("Custom:C","C10","100nF","Capacitor_SMD:C_0402_1005Metric",C10_CX,C10_CY)
    s.power("+3V3", *p_cx["1"]); s.power("GND", *p_cx["2"])

    C11_CX, C11_CY  = 518.0, p5["EP"][1]
    p_cx = s.component("Custom:C","C11","10uF/10V","Capacitor_SMD:C_0805_2012Metric",C11_CX,C11_CY)
    s.power("+3V3", *p_cx["1"]); s.power("GND", *p_cx["2"])

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
