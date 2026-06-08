"""
generator.schematic — Schematic class: S-expression builder for KiCad 10 schematics.

All public methods append S-expression fragments to internal buffers; call
render() to produce the complete .kicad_sch text.
"""

import itertools

from .utils import _uuid, _pt, snap, G, PL, PROJ, SCH_UUID


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
