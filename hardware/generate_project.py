"""
PoE FanController – KiCad 10 project generator (grid-correct, v3).

All coordinates are multiples of 1.27 mm (KiCad default schematic grid).
Symbol body sizes are chosen so that pin endpoints land on the 2.54 mm grid.
Component placements are on the 2.54 mm grid for maximum cleanliness.

Pin position formula (angle=0):
  left  pin i: x = cx - hw - pin_len,  y = cy + hh - 1.27 - i*2.54
  right pin i: x = cx + hw + pin_len,  y = cy + hh - 1.27 - i*2.54
where hw = body_w/2, hh = body_h/2, pin_len = 2.54 mm

Constraint: body_w and body_h must be multiples of 2.54 so that
  hw + pin_len = (n+2)*1.27 (always on 1.27 mm grid)
"""

import json, os, itertools, csv, re

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_uid_seq = itertools.count(1)
def _uuid():
    n = next(_uid_seq)
    return f"{n:08x}-{n:04x}-{n:04x}-{n:04x}-{n:012x}"

G  = 2.54   # grid unit (mm)
PL = 2.54   # pin length (mm)

# KiCad 10 footprint library base path.
# Override via KICAD_FP_BASE environment variable for CI / non-Windows systems.
# Linux default (KiCad installed via apt): /usr/share/kicad/footprints
KICAD_FP_BASE = os.environ.get(
    "KICAD_FP_BASE",
    r"C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints",
)

def snap(v):
    """Snap value to nearest 1.27 mm."""
    return round(round(v / 1.27) * 1.27, 6)

def _pt(x, y):
    return f"{snap(x):.4f} {snap(y):.4f}"

OUT_DIR  = os.path.join(os.path.dirname(__file__), "kicad")
PROJ     = "PoE-FanController"
SCH_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# ---------------------------------------------------------------------------
# .kicad_pro
# ---------------------------------------------------------------------------
def write_pro():
    pro = {
        "boards": [], "cvpcb": {"equivalence_files": []},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": f"{PROJ}.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [{"clearance": 0.2, "name": "Default", "track_width": 0.25,
                         "via_diameter": 0.8, "via_drill": 0.4}],
            "meta": {"version": 3}, "net_colors": {}, "netclass_assignments": {},
            "netclass_patterns": []},
        "schematic": {"annotate_start_num": 0, "bom_fmt_presets": [], "bom_presets": [],
                      "drawing": {"default_wire_thickness": 6, "default_text_size": 50},
                      "legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [], "text_variables": {}
    }
    p = os.path.join(OUT_DIR, f"{PROJ}.kicad_pro")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(pro, f, indent=2)
    print(f"  wrote {p}")


# ---------------------------------------------------------------------------
# Schematic class
# ---------------------------------------------------------------------------
class Schematic:
    def __init__(self):
        self._lib_syms  = []
        self._known     = set()
        self._meta      = {}   # lib_id → {body_w, body_h, pins_left, pins_right}
        self._elements  = []
        self._pwr_n     = itertools.count(1)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------
    def _prop(self, key, val, ax, ay, hidden=False, angle=0, size=1.27):
        h = "      (hide yes)\n" if hidden else ""
        return (
            f'    (property "{key}" "{val}"\n'
            f'      (at {_pt(ax,ay)} {angle})\n'
            + h +
            f'      (effects (font (size {size} {size}))))\n')

    def _emit_pin(self, x, y, angle, ptype, pname, pnum):
        return (
            f'        (pin {ptype} line\n'
            f'          (at {_pt(x,y)} {angle}) (length {PL:.4f})\n'
            f'          (name "{pname}" (effects (font (size 1.27 1.27))))\n'
            f'          (number "{pnum}" (effects (font (size 1.27 1.27)))))\n')

    # -----------------------------------------------------------------------
    # Define a custom lib symbol
    # -----------------------------------------------------------------------
    def define(self, lib_id, ref_prefix, default_val, footprint, datasheet,
               body_w, body_h, pins_left, pins_right,
               pins_top=None, pins_bottom=None):
        """
        Define a custom inline lib_symbol.
        body_w and body_h MUST be multiples of 2.54 mm.
        """
        assert body_w % G < 1e-9 or abs(body_w % G - G) < 1e-9, \
            f"body_w {body_w} must be a multiple of {G}"
        if lib_id in self._known:
            return
        self._known.add(lib_id)

        hw, hh = body_w / 2, body_h / 2
        sn = lib_id.split(":")[-1]  # short name for sub-symbol IDs

        self._meta[lib_id] = dict(body_w=body_w, body_h=body_h,
                                   pins_left=list(pins_left or []),
                                   pins_right=list(pins_right or []),
                                   pins_top=list(pins_top or []),
                                   pins_bottom=list(pins_bottom or []))

        lines = [
            f'    (symbol "{lib_id}"\n',
            f'      (pin_numbers (hide yes))\n',
            f'      (pin_names (offset 0.508))\n',
            f'      (exclude_from_sim no)\n',
            f'      (in_bom yes)\n',
            f'      (on_board yes)\n',
            self._prop("Reference", ref_prefix, 0, -(hh + 1.5)),
            self._prop("Value",     default_val, 0,  (hh + 1.5)),
            self._prop("Footprint", footprint,   0,   0, hidden=True),
            self._prop("Datasheet", datasheet,   0,   0, hidden=True),
            f'      (symbol "{sn}_0_1"\n',
            f'        (rectangle (start {-hw:.4f} {-hh:.4f}) (end {hw:.4f} {hh:.4f})\n',
            f'          (stroke (width 0) (type default))\n',
            f'          (fill (type background)))\n',
            f'      )\n',
            f'      (symbol "{sn}_1_1"\n',
        ]

        for i, (pname, pnum, ptype) in enumerate(pins_left or []):
            py = hh - G/2 - i * G
            lines.append(self._emit_pin(-hw - PL, py, 0, ptype, pname, pnum))

        for i, (pname, pnum, ptype) in enumerate(pins_right or []):
            py = hh - G/2 - i * G
            lines.append(self._emit_pin(hw + PL, py, 180, ptype, pname, pnum))

        for i, (pname, pnum, ptype) in enumerate(pins_top or []):
            px = -hw + G/2 + i * G
            lines.append(self._emit_pin(px, -(hh + PL), 270, ptype, pname, pnum))

        for i, (pname, pnum, ptype) in enumerate(pins_bottom or []):
            px = -hw + G/2 + i * G
            lines.append(self._emit_pin(px, hh + PL, 90, ptype, pname, pnum))

        lines += ['      )\n', '    )\n']
        self._lib_syms.append("".join(lines))

    def define_power(self, name, pin_type="power_in"):
        lib_id = f"power:{name}"
        if lib_id in self._known:
            return
        self._known.add(lib_id)
        self._lib_syms.append(
            f'    (symbol "{lib_id}"\n'
            f'      (pin_numbers (hide yes))\n'
            f'      (pin_names (offset 0) (hide yes))\n'
            f'      (exclude_from_sim no) (in_bom no) (on_board no)\n'
            + self._prop("Reference", "#PWR", 0, -3, hidden=True)
            + self._prop("Value",  name,      0,  3)
            + self._prop("Footprint", "", 0, 0, hidden=True)
            + self._prop("Datasheet", "", 0, 0, hidden=True)
            + f'      (symbol "{name}_0_1")\n'
            + f'      (symbol "{name}_1_1"\n'
            + f'        (pin {pin_type} line (at 0 0 270) (length 0)\n'
            + f'          (name "~" (effects (font (size 1.27 1.27))))\n'
            + f'          (number "1" (effects (font (size 1.27 1.27)))))\n'
            + f'      )\n'
            + f'    )\n')

    def pwr_flag(self, x, y):
        """PWR_FLAG: marks a net as driven (suppresses power_pin_not_driven ERC)."""
        self.define_power("PWR_FLAG", pin_type="power_out")
        ref = f"#PWR{next(self._pwr_n):03d}"
        self._elements.append(
            f'  (symbol (lib_id "power:PWR_FLAG") (at {_pt(x,y)} 0)\n'
            f'    (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
            f'    (fields_autoplaced yes) (uuid "{_uuid()}")\n'
            + self._prop("Reference", ref,        x, y+3, hidden=True)
            + self._prop("Value",     "PWR_FLAG", x, y-2)
            + self._prop("Footprint", "",         x, y,   hidden=True)
            + self._prop("Datasheet", "",         x, y,   hidden=True)
            + f'    (pin "1" (uuid "{_uuid()}"))\n'
            + f'    (instances (project "{PROJ}" (path "/" (reference "{ref}") (unit 1))))\n'
            + f'  )\n')

    # -----------------------------------------------------------------------
    # Pin position computation
    # -----------------------------------------------------------------------
    def pin_pos(self, lib_id, cx, cy, pin_num):
        """Return absolute (x, y) of the endpoint of pin 'pin_num'."""
        m = self._meta[lib_id]
        hw = m['body_w'] / 2
        hh = m['body_h'] / 2
        for i, (_, pnum, _) in enumerate(m['pins_left']):
            if pnum == pin_num:
                py = hh - G/2 - i * G
                return (snap(cx - hw - PL), snap(cy - py))
        for i, (_, pnum, _) in enumerate(m['pins_right']):
            if pnum == pin_num:
                py = hh - G/2 - i * G
                return (snap(cx + hw + PL), snap(cy - py))
        raise KeyError(f"Pin {pin_num} not found in {lib_id}")

    def all_pins(self, lib_id, cx, cy):
        """Return {pin_num: (x, y)} for all pins of component placed at (cx, cy)."""
        m = self._meta[lib_id]
        hw = m['body_w'] / 2
        hh = m['body_h'] / 2
        result = {}
        for i, (_, pnum, _) in enumerate(m['pins_left']):
            py = hh - G/2 - i * G
            result[pnum] = (snap(cx - hw - PL), snap(cy - py))
        for i, (_, pnum, _) in enumerate(m['pins_right']):
            py = hh - G/2 - i * G
            result[pnum] = (snap(cx + hw + PL), snap(cy - py))
        return result

    # -----------------------------------------------------------------------
    # Schematic elements
    # -----------------------------------------------------------------------
    def component(self, lib_id, ref, value, footprint, cx, cy, angle=0):
        cx = snap(cx)
        cy = snap(cy)
        all_p = self.all_pins(lib_id, cx, cy)
        pin_lines = "".join(
            f'    (pin "{pnum}" (uuid "{_uuid()}"))\n'
            for pnum in all_p)
        self._elements.append(
            f'  (symbol (lib_id "{lib_id}") (at {_pt(cx,cy)} {angle})\n'
            f'    (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
            f'    (uuid "{_uuid()}")\n'
            + self._prop("Reference", ref,       cx+1, cy-1.5)
            + self._prop("Value",     value,     cx+1, cy+1.5)
            + self._prop("Footprint", footprint, cx,   cy,   hidden=True)
            + self._prop("Datasheet", "~",       cx,   cy,   hidden=True)
            + pin_lines
            + f'    (instances (project "{PROJ}" (path "/" (reference "{ref}") (unit 1))))\n'
            + f'  )\n')
        return all_p  # return {pin_num: (x,y)} for caller to use

    def power(self, name, x, y, angle=0, pin_type="power_out"):
        self.define_power(name, pin_type=pin_type)
        ref = f"#PWR{next(self._pwr_n):03d}"
        self._elements.append(
            f'  (symbol (lib_id "power:{name}") (at {_pt(x,y)} {angle})\n'
            f'    (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
            f'    (fields_autoplaced yes) (uuid "{_uuid()}")\n'
            + self._prop("Reference", ref,  x, y+3, hidden=True)
            + self._prop("Value",     name, x, y-2)
            + self._prop("Footprint", "",   x, y,   hidden=True)
            + self._prop("Datasheet", "",   x, y,   hidden=True)
            + f'    (pin "1" (uuid "{_uuid()}"))\n'
            + f'    (instances (project "{PROJ}" (path "/" (reference "{ref}") (unit 1))))\n'
            + f'  )\n')

    def global_label(self, name, x, y, shape="bidirectional", angle=0):
        """Global net label — visible across the entire schematic; preferred for
        signals that cross between functional blocks (fan signals, UART, USB, etc.).
        shape: input | output | bidirectional | tri_state | passive
        """
        justify = "right" if angle == 180 else "left"
        iref_x = round(x + 2.54 * 3, 4)  # auto-placed intersheet ref offset
        self._elements.append(
            f'  (global_label "{name}"\n'
            f'    (shape {shape})\n'
            f'    (at {_pt(x,y)} {angle})\n'
            f'    (fields_autoplaced yes)\n'
            f'    (effects (font (size 1.27 1.27)) (justify {justify}))\n'
            f'    (uuid "{_uuid()}")\n'
            f'    (property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n'
            f'      (at {_pt(iref_x,y)} {angle})\n'
            f'      (effects (font (size 1.27 1.27)) (justify {justify}) (hide yes)))\n'
            f'  )\n')

    def label(self, name, x, y, angle=0):
        justify = "left" if angle != 180 else "right"
        self._elements.append(
            f'  (label "{name}" (at {_pt(x,y)} {angle})\n'
            f'    (effects (font (size 1.27 1.27)) (justify {justify} bottom))\n'
            f'    (uuid "{_uuid()}"))\n')

    def wlabel_l(self, name, px, py):
        """Wire stub from left-side pin endpoint leftward, then label."""
        wx = snap(px - G)
        self.wire(px, py, wx, py)
        self.label(name, wx, py, angle=0)

    def wlabel_r(self, name, px, py):
        """Wire stub from right-side pin endpoint rightward, then label."""
        wx = snap(px + G)
        self.wire(px, py, wx, py)
        self.label(name, wx, py, angle=180)

    def no_connect(self, x, y):
        self._elements.append(
            f'  (no_connect (at {_pt(x,y)}) (uuid "{_uuid()}"))\n')

    def wire(self, x1, y1, x2, y2):
        self._elements.append(
            f'  (wire (pts (xy {_pt(x1,y1)}) (xy {_pt(x2,y2)}))\n'
            f'    (stroke (width 0) (type default)) (uuid "{_uuid()}"))\n')

    def text(self, s, x, y, size=2.0, bold=False, color=None):
        """Place a text annotation.
        color: (r, g, b) tuple with values 0-255, e.g. (0, 0, 255) for blue.
        """
        font_parts = []
        if color:
            font_parts.append(f'(color {color[0]} {color[1]} {color[2]} 1)')
        if bold:
            font_parts.append('(bold yes)')
        font_parts.append(f'(size {size} {size})')
        font_str = " ".join(font_parts)
        self._elements.append(
            f'  (text "{s}" (at {_pt(x,y)} 0)\n'
            f'    (effects (font {font_str}))\n'
            f'    (uuid "{_uuid()}"))\n')

    # -----------------------------------------------------------------------
    def render(self):
        return (
            f'(kicad_sch\n'
            f'  (version 20260101)\n'
            f'  (generator "eeschema")\n'
            f'  (generator_version "10.0")\n'
            f'  (uuid "{SCH_UUID}")\n'
            f'  (paper "A2")\n'
            f'  (title_block\n'
            f'    (title "PoE FanController")\n'
            f'    (date "2026-06-06")\n'
            f'    (rev "v0.1")\n'
            f'    (comment 1 "4-channel PoE-powered PWM fan controller with ESP32")\n'
            f'    (comment 2 "Power: 802.3at PoE+ -> 12V (fans) + 3.3V (logic)")\n'
            f'  )\n'
            f'  (lib_symbols\n'
            + "".join(self._lib_syms)
            + f'  )\n\n'
            + "\n".join(self._elements)
            + f'\n  (sheet_instances (path "/" (page "1")))\n'
            f')\n')


# ---------------------------------------------------------------------------
# Build schematic
# ---------------------------------------------------------------------------
def build_schematic():
    s = Schematic()

    # -----------------------------------------------------------------------
    # Symbol definitions  (body_w, body_h MUST be multiples of G=2.54)
    # -----------------------------------------------------------------------

    # RJ45 with integrated PoE magnetics + MDI secondary exposure (Würth 615008144521)
    # OQ-03 RESOLVED 2026-06-07: Würth 615008144521 exposes PoE centre-tap pairs on
    # dedicated pins separate from MDI secondary winding outputs.  Left pins carry PoE
    # power centre-taps → Ag9905M (P-POE-02 topology unchanged).  Right pins carry MDI
    # secondary data pairs → LAN8720A via 49.9 Ω series resistors R11-R14.
    s.define("Custom:RJ45_PoE_PHY", "J", "RJ45_PoE_PHY",
             "Connector_RJ:RJ45_Amphenol_54602-x08_Horizontal",
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
    # TODO T009: Replace PCB footprint with Custom:Wuerth_615008144521 when authored.
    # -----------------------------------------------------------------------
    BLUE = (0, 0, 255)
    s.text("PoE Power Input", 25, 18, size=2.54, bold=True, color=BLUE)
    J1_CX, J1_CY = 38.1, 55.88          # 15*G, 22*G
    p = s.component("Custom:RJ45_PoE_PHY","J1","RJ45_PoE_PHY",
                    "Connector_RJ:RJ45_Amphenol_54602-x08_Horizontal",
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


# ---------------------------------------------------------------------------
# Footprint embedding helper — reads .kicad_mod and transforms it for PCB
# ---------------------------------------------------------------------------
def embed_footprint(lib_name, fp_name, ref, value, cx, cy, rot=0.0):
    """Read a footprint from the KiCad library and return it as a PCB footprint entry.

    Transforms the .kicad_mod format into the inline footprint format used by
    .kicad_pcb files: adds (at cx cy rot), (uuid ...), and updates Reference/Value.
    """
    fp_file = os.path.join(KICAD_FP_BASE, lib_name + ".pretty", fp_name + ".kicad_mod")
    content = open(fp_file, encoding="utf-8").read()

    uid = _uuid()
    rot_str = f" {rot:.1f}" if rot != 0.0 else ""

    # Transform the footprint header.
    # .kicad_mod starts with: (footprint "Name" (version N)(generator "X")(generator_version "Y")(layer "F.Cu") ...
    # .kicad_pcb needs:       (footprint "Lib:Name" (layer "F.Cu") (uuid "...") (at cx cy rot) ...
    # The regex handles the header regardless of whitespace/newlines between elements.
    transformed = re.sub(
        r'\(footprint\s+"[^"]+"\s*'
        r'(?:\(version\s+\d+\)\s*)?'
        r'(?:\(generator\s+"[^"]*"\)\s*)?'
        r'(?:\(generator_version\s+"[^"]*"\)\s*)?'
        r'\(layer\s+"F\.Cu"\)',
        f'(footprint "{lib_name}:{fp_name}" (layer "F.Cu") (uuid "{uid}") (at {cx:.3f} {cy:.3f}{rot_str})',
        content,
        count=1,
        flags=re.DOTALL,
    )

    # Update Reference and Value properties to actual designator and value.
    transformed = re.sub(
        r'(\(property\s+"Reference"\s+)"[^"]*"',
        rf'\g<1>"{ref}"',
        transformed,
        count=1,
    )
    transformed = re.sub(
        r'(\(property\s+"Value"\s+)"[^"]*"',
        rf'\g<1>"{value}"',
        transformed,
        count=1,
    )

    # Indent the footprint body by 2 spaces for readability in the PCB file.
    lines = transformed.splitlines()
    return "\n".join("  " + l if l.strip() else l for l in lines)


# ---------------------------------------------------------------------------
# Custom footprint base path (for project-local Custom.pretty/)
# ---------------------------------------------------------------------------
CUSTOM_FP_BASE = os.path.join(os.path.dirname(__file__), "kicad", "footprints")


def embed_custom_footprint(fp_name, ref, value, cx, cy, rot=0.0):
    """Embed a footprint from hardware/kicad/footprints/Custom.pretty/."""
    fp_file = os.path.join(CUSTOM_FP_BASE, "Custom.pretty", fp_name + ".kicad_mod")
    content = open(fp_file, encoding="utf-8").read()

    uid = _uuid()
    rot_str = f" {rot:.1f}" if rot != 0.0 else ""

    transformed = re.sub(
        r'\(footprint\s+"[^"]+"\s*'
        r'(?:\(version\s+\d+\)\s*)?'
        r'(?:\(generator\s+"[^"]*"\)\s*)?'
        r'(?:\(generator_version\s+"[^"]*"\)\s*)?'
        r'\(layer\s+"F\.Cu"\)',
        f'(footprint "Custom:{fp_name}" (layer "F.Cu") (uuid "{uid}") (at {cx:.3f} {cy:.3f}{rot_str})',
        content,
        count=1,
        flags=re.DOTALL,
    )
    transformed = re.sub(
        r'(\(fp_text\s+reference\s+)"[^"]*"',
        rf'\g<1>"{ref}"',
        transformed, count=1,
    )
    transformed = re.sub(
        r'(\(fp_text\s+value\s+)"[^"]*"',
        rf'\g<1>"{value}"',
        transformed, count=1,
    )
    lines = transformed.splitlines()
    return "\n".join("  " + l if l.strip() else l for l in lines)


# ---------------------------------------------------------------------------
# PCB skeleton (KiCad 10, 100×80 mm)
# ---------------------------------------------------------------------------
def write_pcb():
    W, H = 100.0, 80.0

    def uu():
        return _uuid()

    body = f"""(kicad_pcb
  (version 20260206)
  (generator "pcbnew")
  (generator_version "10.0")
  (general (thickness 1.6) (legacy_teardrops no))
  (paper "A4")
  (title_block (title "PoE FanController") (date "2026-06-06") (rev "v0.1"))
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (44 "Edge.Cuts" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user "B.Fabrication")
    (49 "F.Fab" user "F.Fabrication"))
  (setup
    (pad_to_mask_clearance 0.1)
    (allow_soldermask_bridges_in_footprints no)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (outputdirectory "../gerbers/")))
  (net 0 "")
  (net 1 "GND")
  (net 2 "+12V")
  (net 3 "+3V3")
  (net 4 "POE_A+")
  (net 5 "POE_A-")
  (net 6 "POE_B+")
  (net 7 "POE_B-")
  (net 8 "FAN1_PWM")
  (net 9 "FAN2_PWM")
  (net 10 "FAN3_PWM")
  (net 11 "FAN4_PWM")
  (net 12 "FAN1_TACH")
  (net 13 "FAN2_TACH")
  (net 14 "FAN3_TACH")
  (net 15 "FAN4_TACH")
  (net 16 "ESP_TX")
  (net 17 "ESP_RX")
  (net 18 "ESP_EN")
  (net 19 "BOOT")
  (net 20 "USB_DP")
  (net 21 "USB_DN")
  (net 22 "NTC_ADC")
  (net 23 "EMAC_RXD0")
  (net 24 "EMAC_RXD1")
  (net 25 "EMAC_CRS_DV")
  (net 26 "EMAC_TXD0")
  (net 27 "EMAC_TXD1")
  (net 28 "EMAC_TX_EN")
  (net 29 "EMAC_REF_CLK")
  (net 30 "ETH_MDIO")
  (net 31 "ETH_MDC")
  (net 32 "ETH_TD_P_IN")
  (net 33 "ETH_TD_N_IN")
  (net 34 "ETH_RD_P_IN")
  (net 35 "ETH_RD_N_IN")
  (net 36 "ETH_TD_P")
  (net 37 "ETH_TD_N")
  (net 38 "ETH_RD_P")
  (net 39 "ETH_RD_N")
  (gr_line (start 5 5) (end {W-5:.1f} 5)
    (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uu()}"))
  (gr_line (start {W-5:.1f} 5) (end {W-5:.1f} {H-5:.1f})
    (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uu()}"))
  (gr_line (start {W-5:.1f} {H-5:.1f}) (end 5 {H-5:.1f})
    (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uu()}"))
  (gr_line (start 5 {H-5:.1f}) (end 5 5)
    (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uu()}"))
  (gr_text "PoE FanController v0.2" (at {W/2:.1f} 3.5) (layer "F.SilkS") (uuid "{uu()}")
    (effects (font (size 1.5 1.5) (thickness 0.15))))
  (gr_text "ESP32-P4 | LAN8720A | PoE 802.3at | 4xPWM Fan" (at {W/2:.1f} {H-3:.1f}) (layer "F.SilkS") (uuid "{uu()}")
    (effects (font (size 1 1) (thickness 0.1))))
  (gr_line (start 38 5) (end 38 {H-5:.1f})
    (stroke (width 0.1) (type dash)) (layer "Cmts.User") (uuid "{uu()}"))
  (gr_text "PoE Primary Side" (at 20 8) (layer "Cmts.User") (uuid "{uu()}")
    (effects (font (size 1 1) (thickness 0.1))))
  (gr_text "SELV Secondary Side" (at 65 8) (layer "Cmts.User") (uuid "{uu()}")
    (effects (font (size 1 1) (thickness 0.1))))
  (gr_text "KEEP >= 3mm clearance across dashed line!" (at {W/2:.1f} 11) (layer "Cmts.User") (uuid "{uu()}")
    (effects (font (size 1.2 1.2) (thickness 0.12))))
  (zone (net 1) (net_name "GND") (layer "B.Cu") (uuid "{uu()}")
    (name "GND_BOT") (hatch edge 0.5) (priority 0)
    (connect_pads (clearance 0.3)) (min_thickness 0.25) (filled_areas_thickness no)
    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))
    (polygon (pts (xy 40 5) (xy {W-5:.1f} 5) (xy {W-5:.1f} {H-5:.1f}) (xy 40 {H-5:.1f}))))
  (zone (net 1) (net_name "GND") (layer "F.Cu") (uuid "{uu()}")
    (name "GND_TOP") (hatch edge 0.5) (priority 0)
    (connect_pads (clearance 0.3)) (min_thickness 0.25) (filled_areas_thickness no)
    (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))
    (polygon (pts (xy 40 5) (xy {W-5:.1f} 5) (xy {W-5:.1f} {H-5:.1f}) (xy 40 {H-5:.1f}))))
)
"""
    # -----------------------------------------------------------------------
    # Footprint placements — all connectors on top edge (y=5mm), per plan.md
    # Positions derived from footprint courtyard data + constitution P-HW-03.
    #
    # J1  RJ45   : rot=180 → port exits top edge; centre (20.0, 19.47)
    # J2–J5 fans : rot=0   → vertical; pin-1 row near top edge; cy=7.62
    # J6  USB-C  : rot=0   → port faces -Y (top edge); origin at (85.0, 6.06)
    # J7  debug  : rot=90  → pin row parallel to right board edge; (91.0, 35.0)
    #
    # IC / passive positions verified against courtyard extents:
    # U1 2x04 header   courtyard x[-1.77,4.31] y[-1.77,9.39]
    # U2 TO-263-5       courtyard x[-10.2,6.45] y[-5.65,5.65]
    # U3 ESP32-WROOM-32 T-shape courtyard: antenna x[-24,24] y[-30.74,-9.8]
    #                                       body    x[-9.75,9.75] y[-9.8,10.51]
    # L1 Axial P15.24   courtyard x[-1,16.24] y[-2.75,2.75]
    # D1 DO-201AD P12.7 courtyard x[-1,13.7]  y[-2.6,2.6]
    # C1/C2 Rad D8 P3.5 courtyard x[-2.5,6]   y[-4.25,4.25]
    # -----------------------------------------------------------------------
    fps = [
        # Connectors — top edge (primary side)
        embed_footprint("Connector_RJ", "RJ45_Amphenol_54602-x08_Horizontal",
                        "J1", "RJ45_PoE", 20.0, 19.47, rot=180.0),
        # Connectors — top edge (secondary side, x > 38 mm)
        embed_footprint("Connector_PinHeader_2.54mm", "PinHeader_1x04_P2.54mm_Vertical",
                        "J2", "Fan_Header", 46.1, 7.62),
        embed_footprint("Connector_PinHeader_2.54mm", "PinHeader_1x04_P2.54mm_Vertical",
                        "J3", "Fan_Header", 56.8, 7.62),
        embed_footprint("Connector_PinHeader_2.54mm", "PinHeader_1x04_P2.54mm_Vertical",
                        "J4", "Fan_Header", 67.4, 7.62),
        embed_footprint("Connector_PinHeader_2.54mm", "PinHeader_1x04_P2.54mm_Vertical",
                        "J5", "Fan_Header", 78.1, 7.62),
        embed_footprint("Connector_USB", "USB_C_Receptacle_GCT_USB4085",
                        "J6", "USB_C_2.0", 85.0, 6.06),
        # J7 — right board edge (documented exception, P-HW-03 v1.0.1)
        # At rot=90°, pins extend along +x. Pin 3 at x=88+5.08=93.08mm < board edge x=95mm ✓
        # y=50 clears U3 antenna keepout (y[22.26,43.2]) by 6.9mm ✓
        # and U4 body right (x=85.3) by 0.8mm ✓
        embed_footprint("Connector_PinHeader_2.54mm", "PinHeader_1x03_P2.54mm_Vertical",
                        "J7", "Debug_UART", 88.0, 50.0, rot=90.0),
        # Major ICs — primary side.
        # U1 at (21,32): courtyard y[30.23,41.39] — below J1 body (y<24), clear.
        embed_footprint("Connector_PinHeader_2.54mm", "PinHeader_2x04_P2.54mm_Vertical",
                        "U1", "Ag9905M", 21.0, 32.0),
        # U2 at (27,57): TO-263 courtyard x[16.8,33.45] y[51.35,62.65] — below L1 bottom (y=48.75) ✓
        embed_footprint("Package_TO_SOT_SMD", "TO-263-5_TabPin3",
                        "U2", "LM2596-3.3", 27.0, 57.0),
        # L1 at (8,46): pad2 at x=23.24; courtyard y[43.25,48.75] — above U2 top (y=51.35) ✓
        embed_footprint("Inductor_THT", "L_Axial_L11.0mm_D4.5mm_P15.24mm_Horizontal_Fastron_MECC",
                        "L1", "68uH", 8.0, 46.0),
        # D1 at (16,67): pad2 at x=28.7 < 38 ✓; left courtyard at x=15 vs C2 right x=13 → 2mm gap ✓
        embed_footprint("Diode_THT", "D_DO-201AD_P12.70mm_Horizontal",
                        "D1", "1N5822", 16.0, 67.0),
        # C1 at (8,32): courtyard x[5.5,14] — left of U1 (U1 left=19.23), no x overlap.
        embed_footprint("Capacitor_THT", "C_Radial_D8.0mm_H11.5mm_P3.50mm",
                        "C1", "100uF/25V", 8.0, 32.0),
        # C2 at (7,62): courtyard x[4.5,13] y[57.75,66.25] — clear of U2 (x>16.8) and D1 (y>64.4).
        embed_footprint("Capacitor_THT", "C_Radial_D8.0mm_H11.5mm_P3.50mm",
                        "C2", "100uF/10V", 7.0, 62.0),
        # U3 ESP32-P4-MINI-1U custom footprint (replaces ESP32-WROOM-32)
        # Centre at (65, 53) unchanged; custom LGA-56 footprint authored in T002.
        # OQ-06: U3 QFN footprint 25.4x19mm courtyard [51.2,78.8]x[42.4,63.6] —
        #   verified clear of U5 at (57,33), R11-14 at (40.5,26-35), C8-11 at (63-51,33-40)
        embed_custom_footprint("ESP32-P4-MINI-1",
                               "U3", "ESP32-P4-MINI-1U", 65.0, 53.0),
        embed_footprint("Package_SO", "SOIC-16_3.9x9.9mm_P1.27mm",
                        "U4", "CH340C", 87.0, 58.0),

        # U5 LAN8720A (QFN-24, 4×4 mm) — Zone B, east of x=38 ✓
        # Placement (57,33): courtyard [54.5,59.5]×[30.5,35.5]
        #   Clear of fan headers (y<18), Zone B passives (y>47), U3 (y>42) ✓
        embed_footprint("Package_DFN_QFN", "QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm",
                        "U5", "LAN8720A-CP-TR", 57.0, 33.0),

        # MDI termination resistors R11-R14 (49.9 Ω 0402) — Zone B near U5
        # x=40.5: [39,42] clear of isolation boundary (x=38+) and J2 (x=44.85+) ✓
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R11", "49R9", 40.5, 26.0),
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R12", "49R9", 40.5, 29.0),
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R13", "49R9", 40.5, 32.0),
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R14", "49R9", 40.5, 35.0),

        # U5 decoupling caps C8-C11 (100 nF ×3 + 10 µF bulk) — within 3 mm of U5 ✓
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric", "C8",  "100nF", 63.0, 33.0),
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric", "C9",  "100nF", 57.0, 38.5),
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric", "C10", "100nF", 51.0, 33.0),
        embed_footprint("Capacitor_SMD", "C_0805_2012Metric", "C11", "10uF/10V", 63.0, 36.5),

        # Zone A: TACH pull-up resistors between fan headers (y=19.5)
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R5", "10k", 51.5, 19.5),
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R6", "10k", 62.1, 19.5),
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R7", "10k", 72.8, 19.5),
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R8", "10k", 92.0, 19.5),

        # Zone B: I2C/GPIO pull-ups and bypass caps left of ESP32
        # C3-C6 moved to x=44 (was x=52) — ESP32-P4 left courtyard edge is x=51.2;
        # old WROOM was 38mm wide so caps were clear; new P4 is 25.4mm so they collide.
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R1", "10k", 45.0, 47.0),
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R2", "10k", 45.0, 50.0),
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R3", "330R", 45.0, 53.0),
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R4", "10k", 45.0, 56.0),
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric", "C3", "100nF", 44.0, 47.0),
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric", "C4", "100nF", 44.0, 50.0),
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric", "C5", "100nF", 44.0, 53.0),
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric", "C6", "100nF", 44.0, 56.0),

        # Zone C SMD: bypass cap for CH340C and USB-C CC pull-down resistors below U4
        # U4 moved to x=87 (was x=82): ESP32-P4 right courtyard edge is x=78.8;
        # SOIC-16 courtyard ~±3.4mm gives left edge 78.6 which overlapped at x=82 → now 83.6>78.8 ✓
        # C7 moved to y=65 (was y=63.5): ESP32-P4 bottom courtyard y=63.6; C7 now clear ✓
        embed_footprint("Capacitor_SMD", "C_0402_1005Metric", "C7", "100nF", 80.0, 65.0),
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R9", "5.1k", 83.0, 68.5),
        embed_footprint("Resistor_SMD", "R_0402_1005Metric", "R10", "5.1k", 83.0, 71.5),

        # Zone C THT: switches, status LED, NTC thermistor (corrected coords per architecture.md)
        embed_footprint("Button_Switch_THT", "SW_PUSH_6mm", "SW1", "SW_Reset", 44.0, 68.5),
        embed_footprint("Button_Switch_THT", "SW_PUSH_6mm", "SW2", "SW_Boot", 54.0, 68.5),
        embed_footprint("LED_THT", "LED_D3.0mm", "LED1", "LED_Green", 64.0, 68.5),
        embed_footprint("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", "NTC1", "NTC_10k", 70.0, 68.5),
    ]

    p = os.path.join(OUT_DIR, f"{PROJ}.kicad_pcb")
    with open(p, "w", encoding="utf-8") as f:
        # Write the board skeleton (everything up to the closing paren)
        f.write(body.rstrip().rstrip(")").rstrip())
        f.write("\n")
        # Embed all footprints
        for fp_str in fps:
            f.write(fp_str)
            f.write("\n")
        # Close the kicad_pcb
        f.write(")\n")
    print(f"  wrote {p}")


# ---------------------------------------------------------------------------
# BOM
# ---------------------------------------------------------------------------
def write_bom():
    rows = [
        ["Reference","Value","Footprint","Qty","Manufacturer","MPN","Description","Datasheet"],
        ["J1","RJ45_PoE","Connector_RJ:RJ45_Amphenol_54602-x08_Horizontal","1","Wuerth","615008144521","Shielded RJ45 with integrated magnetics","https://www.we-online.com/en/components/products/WR-MJ/615008144521"],
        ["U1","Ag9905M","Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical","1","Silvertel","Ag9905M","PoE+ 802.3at PD module, 12V 1.67A isolated","https://silvertel.com/images/datasheets/Ag9900-Datasheet.pdf"],
        ["U2","LM2596-3.3","Package_TO_SOT_SMD:TO-263-5_TabPin3","1","TI","LM2596S-3.3/NOPB","3A 150kHz buck regulator, 3.3V fixed, D2PAK","https://www.ti.com/lit/ds/symlink/lm2596.pdf"],
        ["U3","ESP32-P4-MINI-1U-N16R8","Custom:ESP32-P4-MINI-1","1","Espressif","ESP32-P4-MINI-1U-N16R8","ESP32-P4 MCU module 16MB flash/8MB PSRAM, RMII Ethernet","https://www.espressif.com/sites/default/files/documentation/esp32-p4-mini-1u_datasheet_en.pdf"],
        ["U5","LAN8720A-CP-TR","Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm","1","Microchip","LAN8720A-CP-TR","Ethernet PHY, RMII, QFN-24","https://ww1.microchip.com/downloads/en/DeviceDoc/00002165B.pdf"],
        ["R11,R12,R13,R14","49R9","Resistor_SMD:R_0402_1005Metric","4","Yageo","RC0402FR-0749R9L","49.9Ω 1% 0402 — MDI termination resistors","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf"],
        ["C8,C9,C10","100nF","Capacitor_SMD:C_0402_1005Metric","3","Samsung","CL05B104KO5NNNC","100nF 0402 16V X5R — LAN8720A VDD decoupling","https://www.samsungsem.com/global/product/passive-component/mlcc/CL05B104KO5NNNC.jsp"],
        ["C11","10uF/10V","Capacitor_SMD:C_0805_2012Metric","1","Samsung","CL21A106KAYNNNE","10µF 0805 10V X5R — LAN8720A bulk decoupling","https://www.samsungsem.com/global/product/passive-component/mlcc/CL21A106KAYNNNE.jsp"],
        ["U4","CH340C","Package_SO:SOIC-16_3.9x9.9mm_P1.27mm","1","WCH","CH340C","USB-UART bridge, internal oscillator","https://www.wch-ic.com/downloads/CH340DS1_PDF.html"],
        ["J2,J3,J4,J5","Fan_Header","Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical","4","Molex","47053-1000","4-pin 2.54mm 12V PWM fan header","~"],
        ["J6","USB_C_2.0","Connector_USB:USB_C_Receptacle_GCT_USB4085","1","GCT","USB4085-GF-A","USB Type-C receptacle, through-hole","~"],
        ["J7","Debug_UART","Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical","1","","","3-pin debug UART header","~"],
        ["L1","68uH","Inductor_THT:L_Axial_L11.0mm_D4.5mm_P15.24mm_Horizontal_Fastron_MECC","1","Bourns","SRR5028-680Y","68uH 3A shielded power inductor","~"],
        ["D1","1N5822","Diode_THT:D_DO-201AD_P12.70mm_Horizontal","1","ON Semi","1N5822","3A 40V Schottky diode","~"],
        ["C1","100uF/25V","Capacitor_THT:C_Radial_D8.0mm_H11.5mm_P3.50mm","1","","","LM2596 input bulk capacitor","~"],
        ["C2","100uF/10V","Capacitor_THT:C_Radial_D8.0mm_H11.5mm_P3.50mm","1","","","LM2596 output bulk capacitor","~"],
        ["C3,C4,C5,C6","100nF","Capacitor_SMD:C_0402_1005Metric","4","Samsung","CL05B104KO5NNNC","100nF 0402 16V X5R decoupling capacitors","https://www.samsungsem.com/global/product/passive-component/mlcc/CL05B104KO5NNNC.jsp"],
        ["C7","100nF","Capacitor_SMD:C_0402_1005Metric","1","Samsung","CL05B104KO5NNNC","100nF 0402 16V X5R — CH340C V3 decoupling","https://www.samsungsem.com/global/product/passive-component/mlcc/CL05B104KO5NNNC.jsp"],
        ["R1,R2,R4","10k","Resistor_SMD:R_0402_1005Metric","3","Yageo","RC0402FR-0710KL","10kΩ 0402 1% — EN, BOOT, NTC divider pull-up","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf"],
        ["R3","330R","Resistor_SMD:R_0402_1005Metric","1","Yageo","RC0402FR-07330RL","330Ω 0402 1% — status LED current limit","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf"],
        ["R5,R6,R7,R8","10k","Resistor_SMD:R_0402_1005Metric","4","Yageo","RC0402FR-0710KL","10kΩ 0402 1% — fan TACH pull-up resistors","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf"],
        ["R9,R10","5.1k","Resistor_SMD:R_0402_1005Metric","2","Yageo","RC0402FR-075K1L","5.1kΩ 0402 1% — USB-C CC pull-down resistors","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf"],
        ["LED1","LED_GREEN","LED_THT:LED_D3.0mm","1","Wurth","150060GS75000","Green 3mm THT LED, 565nm","https://www.we-online.com/en/components/products/LED/THROUGH_HOLE_LED/150060GS75000"],
        ["SW1","RESET","Button_Switch_THT:SW_PUSH_6mm","1","C&K","PTS636 SK43 SMTR LFS","6mm tactile pushbutton, THT, 4.3mm height","https://www.ckswitches.com/products/switches/product-details/Tactile/PTS636/"],
        ["SW2","BOOT","Button_Switch_THT:SW_PUSH_6mm","1","C&K","PTS636 SK43 SMTR LFS","6mm tactile pushbutton, THT, 4.3mm height","https://www.ckswitches.com/products/switches/product-details/Tactile/PTS636/"],
        ["NTC1","NTC10K_B3950","Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal","1","Murata","NCP15XH103F03RC","10kΩ NTC thermistor B=3380, axial THT","https://www.murata.com/en-us/products/productdetail?partid=NCP15XH103F03RC"],
    ]
    p = os.path.join(os.path.dirname(__file__), "bom", "bom.csv")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"  wrote {p}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    print("Project file...")
    write_pro()

    print("Building schematic...")
    sch = build_schematic()
    sp = os.path.join(OUT_DIR, f"{PROJ}.kicad_sch")
    with open(sp, "w", encoding="utf-8") as f:
        f.write(sch.render())
    print(f"  wrote {sp}")

    print("PCB skeleton...")
    write_pcb()

    print("BOM...")
    write_bom()

    print("\nDone. Run ERC with:")
    kicad_cli = r"C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
    print(f'  "{kicad_cli}" sch erc {sp}')
