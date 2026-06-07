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

    # ESP32-P4-MINI-1U-N16R8: 56 pads numbered 1-56 to match Custom:ESP32-P4-MINI-1 footprint.
    # Pin NUMBERS match footprint pad numbers so KiCad "Update PCB from Schematic" assigns nets.
    # Physical layout (Espressif ESP32-P4-MINI-1U, 25.4 × 19 mm, 1.27 mm pitch, best estimate —
    # VERIFY against Espressif ESP32-P4-MINI-1U Hardware Design Guide before fabrication):
    #   Bottom row left→right : pads  1-20
    #   Right  col  bot→top   : pads 21-28
    #   Top    row  right→left: pads 29-48
    #   Left   col  top→bot   : pads 49-56
    # Active signal assignments (OQ-01 RESOLVED 2026-06-07):
    #   RMII fixed IO_MUX: GPIO32-37 + GPIO50 (pads 37-42, 55)
    #   MDIO/MDC GPIO-matrix: GPIO28/GPIO31 (pads 33, 36)
    # body_h = 28 * G = 71.12 mm for 28 pins per side.
    s.define("Custom:ESP32-P4", "U", "ESP32-P4-MINI-1U",
             "Custom:ESP32-P4-MINI-1",
             "https://www.espressif.com/sites/default/files/documentation/esp32-p4_datasheet_en.pdf",
             body_w=30.48, body_h=71.12,
             pins_left=[
                 # Bottom row, pads 1-20 (left→right maps to top→bottom on left side)
                 ("GND",    "1",  "power_in"),       # pad 1  GND
                 ("GPIO0",  "2",  "input"),           # pad 2  BOOT strapping pin
                 ("NC",     "3",  "no_connect"),      # pad 3
                 ("GPIO2",  "4",  "bidirectional"),   # pad 4  1-Wire / status LED
                 ("NC",     "5",  "no_connect"),      # pad 5
                 ("GPIO4",  "6",  "output"),          # pad 6  FAN1_PWM  LEDC CH0
                 ("GPIO5",  "7",  "output"),          # pad 7  FAN2_PWM  LEDC CH1
                 ("GPIO6",  "8",  "output"),          # pad 8  FAN3_PWM  LEDC CH2
                 ("GPIO7",  "9",  "output"),          # pad 9  FAN4_PWM  LEDC CH3
                 ("GPIO8",  "10", "input"),           # pad 10 FAN1_TACH
                 ("GPIO9",  "11", "input"),           # pad 11 FAN2_TACH
                 ("GPIO10", "12", "input"),           # pad 12 FAN3_TACH
                 ("GPIO11", "13", "input"),           # pad 13 FAN4_TACH
                 ("NC",     "14", "no_connect"),      # pad 14
                 ("NC",     "15", "no_connect"),      # pad 15
                 ("NC",     "16", "no_connect"),      # pad 16
                 ("NC",     "17", "no_connect"),      # pad 17
                 ("GPIO16", "18", "input"),           # pad 18 NTC_ADC
                 ("NC",     "19", "no_connect"),      # pad 19
                 ("VDD",    "20", "power_in"),        # pad 20 VDD 3.3 V
                 # Left column, pads 49-56 (top→bottom)
                 ("NC",     "49", "no_connect"),      # pad 49
                 ("NC",     "50", "no_connect"),      # pad 50
                 ("NC",     "51", "no_connect"),      # pad 51
                 ("NC",     "52", "no_connect"),      # pad 52
                 ("NC",     "53", "no_connect"),      # pad 53
                 ("NC",     "54", "no_connect"),      # pad 54
                 ("GPIO50", "55", "output"),          # pad 55 EMAC_REF_CLK 50 MHz → PHY
                 ("EN",     "56", "input"),           # pad 56 chip enable
             ],
             pins_right=[
                 # Right column, pads 21-28 (bottom→top maps to top→bottom on right side)
                 ("NC",     "21", "no_connect"),      # pad 21
                 ("NC",     "22", "no_connect"),      # pad 22
                 ("NC",     "23", "no_connect"),      # pad 23
                 ("NC",     "24", "no_connect"),      # pad 24
                 ("NC",     "25", "no_connect"),      # pad 25
                 ("NC",     "26", "no_connect"),      # pad 26
                 ("NC",     "27", "no_connect"),      # pad 27
                 ("GND",    "28", "power_in"),        # pad 28 GND
                 # Top row, pads 29-48 (right→left maps to top→bottom on right side)
                 ("NC",     "29", "no_connect"),      # pad 29
                 ("NC",     "30", "no_connect"),      # pad 30
                 ("NC",     "31", "no_connect"),      # pad 31
                 ("NC",     "32", "no_connect"),      # pad 32
                 ("GPIO28", "33", "bidirectional"),   # pad 33 EMAC_MDIO (GPIO-matrix)
                 ("NC",     "34", "no_connect"),      # pad 34
                 ("NC",     "35", "no_connect"),      # pad 35
                 ("GPIO31", "36", "output"),          # pad 36 EMAC_MDC  (GPIO-matrix)
                 ("GPIO32", "37", "input"),           # pad 37 EMAC_RXD0 RMII fixed
                 ("GPIO33", "38", "input"),           # pad 38 EMAC_RXD1 RMII fixed
                 ("GPIO34", "39", "input"),           # pad 39 EMAC_CRS_DV RMII fixed
                 ("GPIO35", "40", "output"),          # pad 40 EMAC_TXD0 RMII fixed
                 ("GPIO36", "41", "output"),          # pad 41 EMAC_TXD1 RMII fixed
                 ("GPIO37", "42", "output"),          # pad 42 EMAC_TX_EN RMII fixed
                 ("GPIO38", "43", "output"),          # pad 43 UART0_TX IO_MUX default
                 ("GPIO39", "44", "input"),           # pad 44 UART0_RX IO_MUX default
                 ("NC",     "45", "no_connect"),      # pad 45
                 ("NC",     "46", "no_connect"),      # pad 46
                 ("NC",     "47", "no_connect"),      # pad 47
                 ("GND",    "48", "power_in"),        # pad 48 GND (top edge)
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

    # LAN8720A-CP-TR Ethernet PHY QFN-24+EP
    # Pin NUMBERS match QFN-24-1EP footprint pads 1-24 + EP(25).
    # Datasheet: DS00001913C (Microchip).
    # Left: RMII interface + MDI pairs + config/control pins.
    # Right: power supply pins (VDD33A, VDD33D, VDDIO, GND_LDO, GND_A, EP).
    # body_h = 19 * G = 48.26 mm for 19 left pins.
    # RBIAS (pin 4): external 6.04 kΩ to GND sets internal bias current.
    s.define("Custom:LAN8720A", "U", "LAN8720A-CP-TR",
             "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm",
             "https://ww1.microchip.com/downloads/en/DeviceDoc/00002165B.pdf",
             body_w=20.32, body_h=48.26,
             pins_left=[
                 ("TXEN",    "1",  "input"),         # TX_EN   ← ESP32 GPIO37
                 ("TXD1",    "2",  "input"),         # TXD[1]  ← ESP32 GPIO36
                 ("TXD0",    "3",  "input"),         # TXD[0]  ← ESP32 GPIO35
                 ("RBIAS",   "4",  "passive"),       # 6.04 kΩ to GND (sets bias)
                 ("RXD0",    "5",  "output"),        # RXD[0]  → ESP32 GPIO32
                 ("RXD1",    "6",  "output"),        # RXD[1]  → ESP32 GPIO33
                 ("CRS_DV",  "7",  "output"),        # CRS_DV  → ESP32 GPIO34
                 ("RXERR",   "8",  "output"),        # RX error (NC in this design)
                 ("CLKOUT",  "9",  "input"),         # REF_CLK ← ESP32 GPIO50 (ext clk mode)
                 ("nINTSEL", "10", "input"),         # pull to 3.3V (no interrupt)
                 ("LED2",    "11", "input"),         # MODE[1] pull to 3.3V → full-duplex
                 ("LED1",    "12", "input"),         # MODE[0] pull to 3.3V → 100BASE-TX
                 ("MDIO",    "13", "bidirectional"), # MDIO    ↔ ESP32 GPIO28
                 ("MDC",     "14", "input"),         # MDC     ← ESP32 GPIO31
                 ("nRST",    "15", "input"),         # active-low reset (tied to 3.3V)
                 ("TX+",     "20", "passive"),       # MDI TX+ → J1 via R11
                 ("TX-",     "21", "passive"),       # MDI TX- → J1 via R12
                 ("RX+",     "22", "passive"),       # MDI RX+ ← J1 via R13
                 ("RX-",     "23", "passive"),       # MDI RX- ← J1 via R14
             ],
             pins_right=[
                 ("VDD33A",  "17", "power_in"),      # Analog  3.3V supply
                 ("VDD33D",  "18", "power_in"),      # Digital 3.3V supply
                 ("VDDIO",   "19", "power_in"),      # I/O     3.3V supply
                 ("GND_LDO", "16", "power_in"),      # LDO GND
                 ("GND_A",   "24", "power_in"),      # Analog  GND
                 ("EP",      "25", "power_in"),      # Exposed pad GND
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

    # USB Type-C receptacle (GCT USB4085), full 20-pad footprint.
    # Pin NUMBERS match footprint pad names: A1, A4-A9, A12, B1, B4-B9, B12, SH.
    # body_h = 17 * G = 43.18 mm for 17 pins.
    # VBUS (A4, A9, B4, B9): not used in this design (powered from PoE); no_connect.
    # Duplicate GND pads (A12, B1, B12): connected to GND net.
    # Mirrored data pads (B6=D-, B7=D+): connected to same nets as A7/A6.
    # SBU (A8, B8): sideband use; no_connect in this design.
    s.define("Custom:USB_C", "J", "USB_C",
             "Connector_USB:USB_C_Receptacle_GCT_USB4085", "~",
             body_w=15.24, body_h=43.18,
             pins_left=[
                 ("GND",  "A1",  "passive"),        # Ground
                 ("VBUS", "A4",  "passive"),         # VBUS (no_connect — PoE-powered)
                 ("CC1",  "A5",  "passive"),         # CC1 configuration
                 ("D+",   "A6",  "bidirectional"),   # USB D+
                 ("D-",   "A7",  "bidirectional"),   # USB D-
                 ("SBU1", "A8",  "no_connect"),      # Sideband use 1 (NC)
                 ("VBUS", "A9",  "passive"),         # VBUS duplicate (NC)
                 ("GND",  "A12", "passive"),         # GND duplicate
                 ("GND",  "B1",  "passive"),         # GND duplicate
                 ("VBUS", "B4",  "passive"),         # VBUS duplicate (NC)
                 ("CC2",  "B5",  "passive"),         # CC2 configuration
                 ("D-",   "B6",  "bidirectional"),   # USB D- (mirror of A7)
                 ("D+",   "B7",  "bidirectional"),   # USB D+ (mirror of A6)
                 ("SBU2", "B8",  "no_connect"),      # Sideband use 2 (NC)
                 ("VBUS", "B9",  "passive"),         # VBUS duplicate (NC)
                 ("GND",  "B12", "passive"),         # GND duplicate
                 ("SHLD", "SH",  "passive"),         # Shield
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
    # U3 – ESP32-P4-MINI-1U (pin numbers now match footprint pads 1-56)
    # RMII fixed pins GPIO32-37 + GPIO50 verified against TRM §EMAC (OQ-01 closed)
    # NOTE: pad-to-GPIO mapping is best estimate from module layout; verify against
    #       Espressif ESP32-P4-MINI-1U Hardware Design Guide before fabrication.
    # -----------------------------------------------------------------------
    s.text("ESP32-P4", 155, 18, size=2.54, bold=True, color=BLUE)
    U3_CX, U3_CY = 218.44, 130.0        # 86*G — centre shifted down for taller body
    p = s.component("Custom:ESP32-P4","U3","ESP32-P4-MINI-1U",
                    "Custom:ESP32-P4-MINI-1",
                    U3_CX, U3_CY)

    # Power pins (pads 1, 20, 28, 48)
    s.power("GND",  *p["1"])             # pad 1  GND (bottom row)
    s.power("+3V3", *p["20"])            # pad 20 VDD
    s.power("GND",  *p["28"])            # pad 28 GND (right column)
    s.power("GND",  *p["48"])            # pad 48 GND (top row)

    # Left side — functional GPIO (pads 2, 4, 6-13, 18, 55, 56)
    s.global_label("BOOT",      *p["2"],  shape="passive")
    s.label("GPIO2",            *p["4"])                          # LED circuit local
    s.global_label("FAN1_PWM",  *p["6"],  shape="output")
    s.global_label("FAN2_PWM",  *p["7"],  shape="output")
    s.global_label("FAN3_PWM",  *p["8"],  shape="output")
    s.global_label("FAN4_PWM",  *p["9"],  shape="output")
    s.global_label("FAN1_TACH", *p["10"], shape="input")
    s.global_label("FAN2_TACH", *p["11"], shape="input")
    s.global_label("FAN3_TACH", *p["12"], shape="input")
    s.global_label("FAN4_TACH", *p["13"], shape="input")
    s.global_label("NTC_ADC",   *p["18"], shape="input")
    s.global_label("EMAC_REF_CLK", *p["55"], shape="output")     # GPIO50 on left col
    s.global_label("ESP_EN",    *p["56"], shape="input")          # EN on left col

    # Right side — RMII + UART + MDIO/MDC (pads 33, 36-44)
    s.global_label("ETH_MDIO",    *p["33"], shape="bidirectional", angle=180)
    s.global_label("ETH_MDC",     *p["36"], shape="output",        angle=180)
    s.global_label("EMAC_RXD0",   *p["37"], shape="input",         angle=180)
    s.global_label("EMAC_RXD1",   *p["38"], shape="input",         angle=180)
    s.global_label("EMAC_CRS_DV", *p["39"], shape="input",         angle=180)
    s.global_label("EMAC_TXD0",   *p["40"], shape="output",        angle=180)
    s.global_label("EMAC_TXD1",   *p["41"], shape="output",        angle=180)
    s.global_label("EMAC_TX_EN",  *p["42"], shape="output",        angle=180)
    s.global_label("ESP_TX",      *p["43"], shape="output",        angle=180)
    s.global_label("ESP_RX",      *p["44"], shape="input",         angle=180)

    # -----------------------------------------------------------------------
    # ESP32-P4 support: R1 (EN pull-up), SW1 (RESET), R2 (IO0 pull-up), SW2 (BOOT)
    # Pin references now use numeric pad numbers (pad 56=EN, pad 2=GPIO0, etc.)
    # -----------------------------------------------------------------------
    # R1 – 10k EN pull-up
    R1_CX, R1_CY = 178.0, p["56"][1]   # same y as EN pin (pad 56, left col)
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
    R2_CX, R2_CY = 178.0, p["2"][1]    # same y as GPIO0 pin (pad 2)
    p1 = s.component("Custom:R","R2","10k","Resistor_SMD:R_0402_1005Metric",
                     R2_CX, R2_CY)
    s.power("+3V3",           *p1["1"])
    s.global_label("BOOT",    *p1["2"], shape="passive")

    # SW2 – BOOT button (offset 8*G below SW1)
    SW2_CX, SW2_CY = 178.0, SW1_CY + 8 * G
    p1 = s.component("Custom:SW_Push","SW2","BOOT",
                     "Button_Switch_THT:SW_PUSH_6mm", SW2_CX, SW2_CY)
    s.global_label("BOOT", *p1["1"], shape="passive")
    s.power("GND",          *p1["2"])

    # R3 – 330R LED resistor (GPIO2 = pad 4)
    R3_CX, R3_CY = 178.0, p["4"][1]    # same y as GPIO2 pin (pad 4)
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

    # R4 – 10k NTC voltage divider top (GPIO16 = pad 18)
    R4_CX, R4_CY = 178.0, p["18"][1]   # same y as GPIO16 pin (pad 18)
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
    # Pin numbers now match QFN-24-1EP footprint pads 1-24 + EP(25).
    # New pins: RBIAS(4)→R15, RXERR(8)→NC, nINTSEL(10)/LED2(11)/LED1(12)→3V3,
    #           VDD33D(18)→3V3, GND_A(24)→GND.
    # -----------------------------------------------------------------------
    s.text("Ethernet PHY (LAN8720A)", 430, 18, size=2.54, bold=True, color=BLUE)
    U5_CX, U5_CY = 490.0, 109.22        # east of fan section; same y as U3 centre
    p5 = s.component("Custom:LAN8720A","U5","LAN8720A-CP-TR",
                     "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm",
                     U5_CX, U5_CY)

    # Power supplies (right side pins)
    s.power("+3V3", *p5["17"])           # VDD33A  (analog 3.3V)
    s.power("+3V3", *p5["18"])           # VDD33D  (digital 3.3V)
    s.power("+3V3", *p5["19"])           # VDDIO   (I/O 3.3V)
    s.power("GND",  *p5["16"])           # GND_LDO
    s.power("GND",  *p5["24"])           # GND_A
    s.power("GND",  *p5["25"])           # EP (exposed pad)

    # nRST — tie to +3V3 (PHY always released; optional external control deferred)
    s.power("+3V3", *p5["15"])

    # RXERR — no_connect in this design
    s.no_connect(*p5["8"])

    # Mode configuration: nINTSEL(10) + LED2/MODE[1](11) + LED1/MODE[0](12) → 3V3
    # MODE[1:0] = 11b → 100BASE-TX full-duplex auto-negotiation
    s.power("+3V3", *p5["10"])
    s.power("+3V3", *p5["11"])
    s.power("+3V3", *p5["12"])

    # RMII receive path (U5 drives → MCU receives)
    s.global_label("EMAC_RXD0",   *p5["5"],  shape="output")
    s.global_label("EMAC_RXD1",   *p5["6"],  shape="output")
    s.global_label("EMAC_CRS_DV", *p5["7"],  shape="output")

    # RMII transmit path (MCU drives → U5 receives)
    s.global_label("EMAC_TX_EN",  *p5["1"],  shape="input")
    s.global_label("EMAC_TXD1",   *p5["2"],  shape="input")
    s.global_label("EMAC_TXD0",   *p5["3"],  shape="input")

    # Reference clock (MCU GPIO50 → U5 CLKOUT/REF_CLK input)
    s.global_label("EMAC_REF_CLK",*p5["9"],  shape="input")

    # MDIO management bus
    s.global_label("ETH_MDIO",    *p5["13"], shape="bidirectional")
    s.global_label("ETH_MDC",     *p5["14"], shape="input")

    # MDI physical pairs (via R11-R14 termination resistors)
    s.global_label("ETH_TD_P", *p5["20"], shape="passive")
    s.global_label("ETH_TD_N", *p5["21"], shape="passive")
    s.global_label("ETH_RD_P", *p5["22"], shape="passive")
    s.global_label("ETH_RD_N", *p5["23"], shape="passive")

    # RBIAS (pin 4): 6.04 kΩ resistor to GND sets LAN8720A internal bias current
    R15_CX = 445.0
    R15_CY = p5["4"][1]
    pr15 = s.component("Custom:R","R15","6k04",
                       "Resistor_SMD:R_0402_1005Metric", R15_CX, R15_CY)
    s.label("RBIAS", *pr15["2"])         # right pin → toward U5 RBIAS
    s.power("GND",   *pr15["1"])         # left  pin → GND
    s.label("RBIAS", *p5["4"])

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
    # U5 decoupling caps: 3 × 100 nF near VDD pins + 1 × 10 µF bulk (C8-C11)
    # Pin references updated: VDD33A=17, VDDIO=19, GND_LDO=16, EP=25
    # -----------------------------------------------------------------------
    C8_CX, C8_CY   = 518.0, p5["17"][1]   # VDD33A decoupling
    p_cx = s.component("Custom:C","C8","100nF","Capacitor_SMD:C_0402_1005Metric",C8_CX,C8_CY)
    s.power("+3V3", *p_cx["1"]); s.power("GND", *p_cx["2"])

    C9_CX, C9_CY   = 518.0, p5["19"][1]   # VDDIO decoupling
    p_cx = s.component("Custom:C","C9","100nF","Capacitor_SMD:C_0402_1005Metric",C9_CX,C9_CY)
    s.power("+3V3", *p_cx["1"]); s.power("GND", *p_cx["2"])

    C10_CX, C10_CY  = 518.0, p5["16"][1]  # GND_LDO rail decoupling
    p_cx = s.component("Custom:C","C10","100nF","Capacitor_SMD:C_0402_1005Metric",C10_CX,C10_CY)
    s.power("+3V3", *p_cx["1"]); s.power("GND", *p_cx["2"])

    C11_CX, C11_CY  = 518.0, p5["25"][1]  # EP (bulk)
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
    # GND pads (all connected to GND net)
    s.power("GND",    *p["A1"])           # main GND
    s.power("GND",    *p["A12"])          # GND duplicate
    s.power("GND",    *p["B1"])           # GND duplicate
    s.power("GND",    *p["B12"])          # GND duplicate
    # VBUS pads (not used — PoE-powered; all no_connect)
    s.no_connect(*p["A4"])
    s.no_connect(*p["A9"])
    s.no_connect(*p["B4"])
    s.no_connect(*p["B9"])
    # CC pull-down resistors (R9/R10) via local labels
    s.label("CC1", *p["A5"])
    s.label("CC2", *p["B5"])
    # Data pairs A-side
    s.global_label("USB_DP", *p["A6"], shape="bidirectional")
    s.global_label("USB_DN", *p["A7"], shape="bidirectional")
    # Data pairs B-side (mirror — connect to same nets)
    s.global_label("USB_DN", *p["B6"], shape="bidirectional")
    s.global_label("USB_DP", *p["B7"], shape="bidirectional")
    # SBU (sideband use) — no_connect in this design
    s.no_connect(*p["A8"])
    s.no_connect(*p["B8"])
    # Shield — no_connect
    s.no_connect(*p["SH"])

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
