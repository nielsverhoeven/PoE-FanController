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

import json, os, itertools, csv

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_uid_seq = itertools.count(1)
def _uuid():
    n = next(_uid_seq)
    return f"{n:08x}-{n:04x}-{n:04x}-{n:04x}-{n:012x}"

G  = 2.54   # grid unit (mm)
PL = 2.54   # pin length (mm)

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

    def power(self, name, x, y, angle=0, pin_type="power_in"):
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

    def text(self, s, x, y, size=2.0):
        self._elements.append(
            f'  (text "{s}" (at {_pt(x,y)} 0)\n'
            f'    (effects (font (size {size} {size})))\n'
            f'    (uuid "{_uuid()}"))\n')

    # -----------------------------------------------------------------------
    def render(self):
        return (
            f'(kicad_sch\n'
            f'  (version 20250610)\n'
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

    # RJ45 with PoE: 9 left (Ethernet), 4 right (PoE taps)
    s.define("Custom:RJ45_PoE", "J", "RJ45_PoE",
             "Connector_RJ45:RJ45_Shielded_Horizontal_Amphenol_54602", "~",
             body_w=15.24, body_h=22.86,
             pins_left=[
                 ("DA+",    "1",  "bidirectional"),
                 ("DA-",    "2",  "bidirectional"),
                 ("DB+",    "3",  "bidirectional"),
                 ("DB-",    "4",  "bidirectional"),
                 ("DC+",    "5",  "bidirectional"),
                 ("DC-",    "6",  "bidirectional"),
                 ("DD+",    "7",  "bidirectional"),
                 ("DD-",    "8",  "bidirectional"),
                 ("SHIELD", "9",  "passive"),
             ],
             pins_right=[
                 ("POE_A+", "10", "passive"),
                 ("POE_A-", "11", "passive"),
                 ("POE_B+", "12", "passive"),
                 ("POE_B-", "13", "passive"),
             ])

    # Ag9905M PoE+ PD module: 4 left (PoE input), 4 right (12V output)
    s.define("Custom:Ag9905M", "U", "Ag9905M",
             "Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical",
             "https://silvertel.com/images/datasheets/Ag9900-Datasheet.pdf",
             body_w=22.86, body_h=12.70,
             pins_left=[
                 ("VPORT_A+", "1", "power_in"),
                 ("VPORT_A-", "2", "power_in"),
                 ("VPORT_B+", "3", "power_in"),
                 ("VPORT_B-", "4", "power_in"),
             ],
             pins_right=[
                 ("VOUT_P", "5", "power_out"),
                 ("VOUT_N", "6", "power_out"),
                 ("/SD",    "7", "input"),
                 ("FLT",    "8", "output"),
             ])

    # LM2596-3.3: 3 left (IN, GND, /ON), 2 right (OUT, FB)
    s.define("Custom:LM2596-3.3", "U", "LM2596-3.3",
             "Package_TO_SOT_THT:TO-263-5_TabDown",
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

    # ESP32-WROOM-32: 14 left + 14 right = 28 pins
    s.define("Custom:ESP32-WROOM-32", "U", "ESP32-WROOM-32",
             "RF_Module:ESP32-WROOM-32",
             "https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf",
             body_w=30.48, body_h=35.56,
             pins_left=[
                 ("GND",    "1",  "power_in"),
                 ("3V3",    "2",  "power_in"),
                 ("EN",     "3",  "input"),
                 ("GPIO0",  "4",  "bidirectional"),
                 ("GPIO2",  "5",  "bidirectional"),
                 ("GPIO4",  "6",  "bidirectional"),
                 ("TXD0",   "7",  "output"),
                 ("RXD0",   "8",  "input"),
                 ("GPIO14", "9",  "bidirectional"),
                 ("GPIO32", "10", "bidirectional"),
                 ("GPIO34", "11", "input"),
                 ("GPIO35", "12", "input"),
                 ("GPIO36", "13", "input"),
                 ("GPIO39", "14", "input"),
             ],
             pins_right=[
                 ("GND",    "15", "power_in"),
                 ("GPIO25", "16", "bidirectional"),
                 ("GPIO26", "17", "bidirectional"),
                 ("GPIO27", "18", "bidirectional"),
                 ("GPIO12", "19", "bidirectional"),
                 ("GPIO13", "20", "bidirectional"),
                 ("GPIO15", "21", "bidirectional"),
                 ("GPIO16", "22", "bidirectional"),
                 ("GPIO17", "23", "bidirectional"),
                 ("GPIO18", "24", "bidirectional"),
                 ("GPIO19", "25", "bidirectional"),
                 ("GPIO21", "26", "bidirectional"),
                 ("GPIO22", "27", "bidirectional"),
                 ("GPIO23", "28", "bidirectional"),
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

    # USB Type-C receptacle (simplified, 7 key signals)
    s.define("Custom:USB_C", "J", "USB_C",
             "Connector_USB:USB_C_Receptacle_GCT_USB4135_FlipMountable", "~",
             body_w=15.24, body_h=20.32,
             pins_left=[
                 ("GND",  "A1", "passive"),
                 ("VBUS", "A4", "power_in"),
                 ("CC1",  "A5", "passive"),
                 ("D+",   "A6", "bidirectional"),
                 ("D-",   "A7", "bidirectional"),
                 ("CC2",  "B5", "passive"),
                 ("SHLD", "S1", "passive"),
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
             "Inductor_THT:L_Axial_L10.0mm_D4.5mm_P15.24mm", "~",
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
    s.text("=== PoE Power Input ===", 25, 20)
    J1_CX, J1_CY = 38.1, 55.88          # 15*G, 22*G
    p = s.component("Custom:RJ45_PoE","J1","RJ45_PoE",
                    "Connector_RJ45:RJ45_Shielded_Horizontal_Amphenol_54602",
                    J1_CX, J1_CY)
    # Left pins: Ethernet pairs → no connect (the Ag9905M has integrated magnetics)
    for pn in ["1","2","3","4","5","6","7","8","9"]:
        s.no_connect(*p[pn])
    # Right pins: PoE differential pairs to Ag9905M (label at right-side pin tip)
    s.label("POE_A+", *p["10"], angle=180)
    s.label("POE_A-", *p["11"], angle=180)
    s.label("POE_B+", *p["12"], angle=180)
    s.label("POE_B-", *p["13"], angle=180)

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
    s.power("GND",     *p["6"], pin_type="power_out")  # VOUT_N = system GND driver
    # /SD: leave as no_connect (internal pull-up keeps module on)
    s.no_connect(*p["7"])
    s.no_connect(*p["8"])                # FLT: not monitored in v0.1

    # -----------------------------------------------------------------------
    # U2 – LM2596-3.3 step-down (12 V → 3.3 V)
    # -----------------------------------------------------------------------
    s.text("=== 3.3V Regulator (LM2596) ===", 25, 100)
    U2_CX, U2_CY = 73.66, 127.0         # 29*G, 50*G
    p = s.component("Custom:LM2596-3.3","U2","LM2596-3.3",
                    "Package_TO_SOT_THT:TO-263-5_TabDown",
                    U2_CX, U2_CY)
    s.power("+12V",  *p["1"])            # IN: draw from +12V rail
    s.power("GND",   *p["3"])            # GND
    s.power("GND",   *p["5"])            # /ON tied to GND = always enable
    s.label("+3V3_SW", *p["2"], angle=180)  # switch node output
    s.power("+3V3",    *p["4"])                  # FB connected to output rail (fixed 3.3V)

    # D1 – freewheeling Schottky (1N5822), anode = SW node, cathode = GND
    D1_CX, D1_CY = 108.0, 127.0
    p = s.component("Custom:D_Schottky","D1","1N5822",
                    "Diode_THT:D_DO-201AD_P12.70mm_Horizontal",
                    D1_CX, D1_CY)
    s.label("+3V3_SW", *p["1"])          # anode
    s.power("GND",     *p["2"])          # cathode → GND

    # L1 – 68 uH output inductor (SW → +3V3)
    L1_CX, L1_CY = 127.0, 127.0
    p = s.component("Custom:L","L1","68uH",
                    "Inductor_THT:L_Axial_L10.0mm_D4.5mm_P15.24mm",
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
    s.text("=== ESP32-WROOM-32 ===", 155, 20)
    U3_CX, U3_CY = 218.44, 109.22       # 86*G, 43*G
    p = s.component("Custom:ESP32-WROOM-32","U3","ESP32-WROOM-32",
                    "RF_Module:ESP32-WROOM-32",
                    U3_CX, U3_CY)
    # Power
    s.power("GND",   *p["1"])
    s.power("+3V3",  *p["2"])
    s.power("GND",   *p["15"])

    # Signal labels on left-side pins
    s.label("ESP_EN",    *p["3"])
    s.label("BOOT",      *p["4"])
    s.label("GPIO2",     *p["5"])
    s.no_connect(        *p["6"])        # GPIO4 reserved
    s.label("ESP_TX",    *p["7"])
    s.label("ESP_RX",    *p["8"])
    s.label("FAN4_PWM",  *p["9"])        # GPIO14
    s.label("NTC_ADC",   *p["10"])       # GPIO32
    s.label("FAN1_TACH", *p["11"])       # GPIO34
    s.label("FAN2_TACH", *p["12"])       # GPIO35
    s.label("FAN3_TACH", *p["13"])       # GPIO36
    s.label("FAN4_TACH", *p["14"])       # GPIO39

    # Right side signal labels
    s.label("FAN1_PWM", *p["16"])        # GPIO25
    s.label("FAN2_PWM", *p["17"])        # GPIO26
    s.label("FAN3_PWM", *p["18"])        # GPIO27

    # No-connect unused right-side GPIOs for now
    for pn in ["19","20","21","22","23","24","25","26","27","28"]:
        s.no_connect(*p[pn])

    # -----------------------------------------------------------------------
    # ESP32 support: R1 (EN pull-up), SW1 (RESET), R2 (IO0 pull-up), SW2 (BOOT)
    # -----------------------------------------------------------------------
    # R1 – 10k EN pull-up
    R1_CX, R1_CY = 178.0, p["3"][1]   # same y as EN pin
    p1 = s.component("Custom:R","R1","10k","Resistor_SMD:R_0402_1005Metric",
                     R1_CX, R1_CY)
    s.power("+3V3",   *p1["1"])
    s.label("ESP_EN", *p1["2"])

    # SW1 – RESET button
    SW1_CX, SW1_CY = 178.0, R1_CY + 5 * G
    p1 = s.component("Custom:SW_Push","SW1","RESET",
                     "Button_Switch_THT:SW_PUSH_6mm", SW1_CX, SW1_CY)
    s.label("ESP_EN", *p1["1"])
    s.power("GND",    *p1["2"])

    # R2 – 10k GPIO0 pull-up
    R2_CX, R2_CY = 178.0, p["4"][1]   # same y as GPIO0 pin (boot pin)
    p1 = s.component("Custom:R","R2","10k","Resistor_SMD:R_0402_1005Metric",
                     R2_CX, R2_CY)
    s.power("+3V3", *p1["1"])
    s.label("BOOT", *p1["2"])

    # SW2 – BOOT button  (placed 10*G below SW1 to avoid pin coordinate collision)
    SW2_CX, SW2_CY = 178.0, SW1_CY + 10 * G
    p1 = s.component("Custom:SW_Push","SW2","BOOT",
                     "Button_Switch_THT:SW_PUSH_6mm", SW2_CX, SW2_CY)
    s.label("BOOT", *p1["1"])
    s.power("GND",  *p1["2"])

    # R3 – 330R LED resistor
    R3_CX, R3_CY = 178.0, p["5"][1]   # same y as GPIO2
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

    # R4 – 10k NTC voltage divider (top half)
    R4_CX, R4_CY = 178.0, p["10"][1]   # same y as GPIO32
    p1 = s.component("Custom:R","R4","10k","Resistor_SMD:R_0402_1005Metric",
                     R4_CX, R4_CY)
    s.power("+3V3",    *p1["1"])
    s.label("NTC_ADC", *p1["2"])

    # NTC1 – thermistor (bottom half of divider)
    NTC1_CX, NTC1_CY = 178.0, R4_CY + 5 * G
    p1 = s.component("Custom:NTC","NTC1","NTC10K_B3950",
                     "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
                     NTC1_CX, NTC1_CY)
    s.label("NTC_ADC", *p1["1"])
    s.power("GND",     *p1["2"])

    # -----------------------------------------------------------------------
    # Fan headers J2-J5 + TACH pull-up resistors R5-R8
    # -----------------------------------------------------------------------
    s.text("=== Fan Headers (4x PWM) ===", 305, 20)

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
        s.label(tach_net, *p["3"])
        s.label(pwm_net,  *p["4"])

        # TACH pull-up resistor (R5-R8): +3V3 → TACH pin
        FR_CX = FJ_CX - 30 * G
        FR_CY = p["3"][1]   # same y as TACH pin
        pr = s.component("Custom:R", f"R{5+i}", "10k",
                         "Resistor_SMD:R_0402_1005Metric", FR_CX, FR_CY)
        s.power("+3V3",   *pr["1"])
        s.label(tach_net, *pr["2"])

    # -----------------------------------------------------------------------
    # USB Type-C connector (J6) + CC resistors R9/R10
    # -----------------------------------------------------------------------
    s.text("=== USB / UART Bridge ===", 25, 205)
    J6_CX, J6_CY = 55.88, 264.16        # 22*G, 104*G
    p = s.component("Custom:USB_C","J6","USB_C_2.0",
                    "Connector_USB:USB_C_Receptacle_GCT_USB4135_FlipMountable",
                    J6_CX, J6_CY)
    s.power("GND",   *p["A1"])
    s.no_connect(*p["A4"])               # VBUS – not used (bus-powered from PoE)
    s.label("USB_DP", *p["A6"])
    s.label("USB_DN", *p["A7"])
    # CC1 / CC2 pull-down to GND (no_connect placeholder – connect via R9/R10)
    s.label("CC1", *p["A5"])
    s.label("CC2", *p["B5"])
    s.no_connect(*p["S1"])               # shield

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
    s.label("ESP_RX", *p["2"])           # TXD → ESP RXD0
    s.label("ESP_TX", *p["3"])           # RXD ← ESP TXD0
    s.label("CH340_V3", *p["4"])         # V3: internal 3.3V, decouple with C7
    s.label("USB_DP",   *p["5"])
    s.label("USB_DN",   *p["6"])
    s.no_connect(*p["7"])                # XI (no crystal)
    s.no_connect(*p["8"])                # XO
    s.power("+3V3",   *p["16"])          # VCC
    s.label("BOOT",   *p["15"], angle=180)  # DTR → GPIO0 auto-boot
    s.label("ESP_EN", *p["14"], angle=180)  # RTS → EN auto-reset
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
    s.power("GND",    *p["1"])
    s.label("ESP_TX", *p["2"])
    s.label("ESP_RX", *p["3"])

    return s


# ---------------------------------------------------------------------------
# PCB skeleton (KiCad 10, 100×80 mm)
# ---------------------------------------------------------------------------
def write_pcb():
    W, H = 100.0, 80.0

    def uu():
        return _uuid()

    body = f"""(kicad_pcb
  (version 20250610)
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
  (gr_line (start 5 5) (end {W-5:.1f} 5)
    (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uu()}"))
  (gr_line (start {W-5:.1f} 5) (end {W-5:.1f} {H-5:.1f})
    (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uu()}"))
  (gr_line (start {W-5:.1f} {H-5:.1f}) (end 5 {H-5:.1f})
    (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uu()}"))
  (gr_line (start 5 {H-5:.1f}) (end 5 5)
    (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uu()}"))
  (gr_text "PoE FanController v0.1" (at {W/2:.1f} 3.5) (layer "F.SilkS") (uuid "{uu()}")
    (effects (font (size 1.5 1.5) (thickness 0.15))))
  (gr_text "ESP32 | PoE 802.3at | 4xPWM Fan" (at {W/2:.1f} {H-3:.1f}) (layer "F.SilkS") (uuid "{uu()}")
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
    p = os.path.join(OUT_DIR, f"{PROJ}.kicad_pcb")
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"  wrote {p}")


# ---------------------------------------------------------------------------
# BOM
# ---------------------------------------------------------------------------
def write_bom():
    rows = [
        ["Reference","Value","Footprint","Qty","Manufacturer","MPN","Description","Datasheet"],
        ["J1","RJ45_PoE","Connector_RJ45:RJ45_Shielded_Horizontal_Amphenol_54602","1","Wuerth","615008144521","Shielded RJ45 with integrated magnetics","https://www.we-online.com/en/components/products/WR-MJ/615008144521"],
        ["U1","Ag9905M","Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical","1","Silvertel","Ag9905M","PoE+ 802.3at PD module, 12V 1.67A isolated","https://silvertel.com/images/datasheets/Ag9900-Datasheet.pdf"],
        ["U2","LM2596-3.3","Package_TO_SOT_THT:TO-263-5_TabDown","1","TI","LM2596T-3.3/NOPB","3A 150kHz buck regulator, 3.3V fixed","https://www.ti.com/lit/ds/symlink/lm2596.pdf"],
        ["U3","ESP32-WROOM-32","RF_Module:ESP32-WROOM-32","1","Espressif","ESP32-WROOM-32D","ESP32 dual-core WiFi+BT module, 4MB flash","https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf"],
        ["U4","CH340C","Package_SO:SOIC-16_3.9x9.9mm_P1.27mm","1","WCH","CH340C","USB-UART bridge, internal oscillator","https://www.wch-ic.com/downloads/CH340DS1_PDF.html"],
        ["J2,J3,J4,J5","Fan_Header","Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical","4","Molex","47053-1000","4-pin 2.54mm 12V PWM fan header","~"],
        ["J6","USB_C_2.0","Connector_USB:USB_C_Receptacle_GCT_USB4135_FlipMountable","1","GCT","USB4135-GF-A","USB Type-C receptacle, flip mount","~"],
        ["J7","Debug_UART","Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical","1","","","3-pin debug UART header","~"],
        ["L1","68uH","Inductor_THT:L_Axial_L10.0mm_D4.5mm_P15.24mm","1","Bourns","SRR5028-680Y","68uH 3A shielded power inductor","~"],
        ["D1","1N5822","Diode_THT:D_DO-201AD_P12.70mm_Horizontal","1","ON Semi","1N5822","3A 40V Schottky diode","~"],
        ["C1","100uF/25V","Capacitor_THT:C_Radial_D8.0mm_H11.5mm_P3.50mm","1","","","LM2596 input bulk capacitor","~"],
        ["C2","100uF/10V","Capacitor_THT:C_Radial_D8.0mm_H11.5mm_P3.50mm","1","","","LM2596 output bulk capacitor","~"],
        ["C3,C4,C5,C6","100nF","Capacitor_SMD:C_0402_1005Metric","4","","","3.3V decoupling capacitors","~"],
        ["C7","100nF","Capacitor_SMD:C_0402_1005Metric","1","","","CH340C V3 decoupling","~"],
        ["R1,R2","10k","Resistor_SMD:R_0402_1005Metric","2","","","EN and GPIO0 pull-up resistors","~"],
        ["R3","330R","Resistor_SMD:R_0402_1005Metric","1","","","Status LED series resistor","~"],
        ["R4","10k","Resistor_SMD:R_0402_1005Metric","1","","","NTC voltage divider resistor","~"],
        ["R5,R6,R7,R8","10k","Resistor_SMD:R_0402_1005Metric","4","","","Fan TACH pull-up resistors","~"],
        ["R9,R10","5.1k","Resistor_SMD:R_0402_1005Metric","2","","","USB-C CC pull-down resistors","~"],
        ["LED1","LED_GREEN","LED_THT:LED_D3.0mm","1","","","Green status LED","~"],
        ["SW1","RESET","Button_Switch_THT:SW_PUSH_6mm","1","","","Tactile reset button","~"],
        ["SW2","BOOT","Button_Switch_THT:SW_PUSH_6mm","1","","","Tactile boot button","~"],
        ["NTC1","NTC10K_B3950","Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal","1","","","10k NTC thermistor B=3950","~"],
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
