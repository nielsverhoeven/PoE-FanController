"""
Generate ESP32-P4-MINI-1.kicad_mod for KiCad 10.
Land pattern derived from Espressif ESP32-P4-MINI-1U module datasheet.
Module dimensions: 25.4 x 19.0 x 3.1 mm
56 castellation pads, 1.27 mm pitch.
"""
import os

OUT = os.path.join(os.path.dirname(__file__), "kicad", "footprints",
                   "Custom.pretty", "ESP32-P4-MINI-1.kicad_mod")

uid_seq = [1]
def uu():
    n = uid_seq[0]; uid_seq[0] += 1
    return f"{n:08x}-{n:04x}-{n:04x}-{n:04x}-{n:012x}"

def pad_line(num, shape, x, y, sx, sy):
    return (
        f'  (pad "{num}" smd {shape} (at {x:.3f} {y:.3f}) (size {sx} {sy})\n'
        f'    (layers "F.Cu" "F.Paste" "F.Mask") (uuid "{uu()}"))'
    )

lines = [
    '(footprint "ESP32-P4-MINI-1"',
    '  (version 20260206)',
    '  (generator "pcbnew")',
    '  (generator_version "10.0")',
    '  (layer "F.Cu")',
    '  (descr "ESP32-P4-MINI-1U LGA-56 castellation 25.4x19.0x3.1mm - Espressif")',
    '  (tags "esp32-p4 mini lga castellation espressif")',
    '  (attr smd)',
    # Reference and value text
    '  (fp_text reference "U" (at 0 -11.5 0) (layer "F.SilkS")',
    '    (effects (font (size 1.27 1.27) (thickness 0.15))))',
    '  (fp_text value "ESP32-P4-MINI-1U" (at 0 11.5 0) (layer "F.Fab")',
    '    (effects (font (size 1.27 1.27) (thickness 0.15))))',
    # Fab layer: module body outline
    '  (fp_rect (start -12.7 -9.5) (end 12.7 9.5)',
    '    (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))',
    # Courtyard: module + 0.8 mm margin
    '  (fp_rect (start -13.8 -10.6) (end 13.8 10.6)',
    '    (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))',
    # Silkscreen: pin-1 corner indicator (notch at top-left of courtyard)
    '  (fp_line (start -13.8 -10.6) (end -10.0 -10.6)',
    '    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
    '  (fp_line (start -13.8 -10.6) (end -13.8 -7.0)',
    '    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
    # Pin-1 dot on F.Fab near pad 1
    '  (fp_circle (center -12.065 7.6) (end -11.565 7.6)',
    '    (stroke (width 0.12) (type solid)) (fill solid) (layer "F.Fab"))',
]

# ---- Bottom pads 1-20 (y=9.5, long axis vertical, size 0.9 x 1.7) ----
x_start = -12.065
pitch   = 1.27
for i in range(20):
    x    = round(x_start + i * pitch, 3)
    pnum = i + 1
    shape = "roundrect" if pnum == 1 else "rect"
    if shape == "roundrect":
        lines.append(
            f'  (pad "{pnum}" smd {shape} (at {x:.3f} 9.5) (size 0.9 1.7) (roundrect_rratio 0.25)\n'
            f'    (layers "F.Cu" "F.Paste" "F.Mask") (uuid "{uu()}"))'
        )
    else:
        lines.append(pad_line(pnum, "rect", x, 9.5, 0.9, 1.7))

# ---- Right pads 21-28 (x=12.7, long axis horizontal, size 1.7 x 0.9) ----
y_right = [4.445, 3.175, 1.905, 0.635, -0.635, -1.905, -3.175, -4.445]
for i, y in enumerate(y_right):
    lines.append(pad_line(21 + i, "rect", 12.7, y, 1.7, 0.9))

# ---- Top pads 29-48 (y=-9.5, size 0.9 x 1.7, right-to-left) ----
for i in range(20):
    x = round(x_start + (19 - i) * pitch, 3)
    lines.append(pad_line(29 + i, "rect", x, -9.5, 0.9, 1.7))

# ---- Left pads 49-56 (x=-12.7, size 1.7 x 0.9, top-to-bottom) ----
y_left = [-4.445, -3.175, -1.905, -0.635, 0.635, 1.905, 3.175, 4.445]
for i, y in enumerate(y_left):
    lines.append(pad_line(49 + i, "rect", -12.7, y, 1.7, 0.9))

lines.append(")")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Wrote {OUT}")
print(f"Total pads: {20 + 8 + 20 + 8} (expected 56)")
