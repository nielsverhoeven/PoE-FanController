"""Generate KiCad footprint for Waveshare ESP32-P4-POE-ETH GPIO header.

2x20 female pin socket, 2.54mm pin pitch, 2.81mm row-to-row spacing.
Board dimension source: docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-details-size-*.webp
"""

import os

PITCH = 2.54
ROW_SPACING = 2.81
N_POS = 20  # 20 positions x 2 rows = 40 pins
PAD_SIZE = 1.7
DRILL = 1.0

row1_y = -ROW_SPACING / 2  # -1.405
row2_y =  ROW_SPACING / 2  # +1.405
x_start = -(N_POS - 1) / 2.0 * PITCH  # -24.13

cyd_x1 = x_start - PITCH / 2  # -25.4
cyd_x2 = -cyd_x1               # +25.4
cyd_y1 = row1_y - 1.5          # -2.905
cyd_y2 = row2_y + 1.5          # +2.905

lines = []
a = lines.append

a('(footprint "PinSocket_2x20_P2.54mm_P2.81mm_Vertical"')
a('  (version 20260206)')
a('  (generator "custom")')
a('  (generator_version "10.0")')
a('  (layer "F.Cu")')
a('  (descr "2x20 Female Pin Socket, 2.54mm pitch, 2.81mm row spacing - Waveshare ESP32-P4-POE-ETH GPIO header")')
a('  (tags "connector female socket 2x20 2.54mm 2.81mm waveshare esp32-p4 poe-eth")')
a('  (attr through_hole)')

# Reference / value
a(f'  (fp_text reference "J" (at 0 {cyd_y1 - 1.0:.3f} 0) (layer "F.SilkS")')
a('    (effects (font (size 1.27 1.27) (thickness 0.15))))')
a(f'  (fp_text value "PinSocket_2x20_P2.54mm_P2.81mm_Vertical" (at 0 {cyd_y2 + 1.0:.3f} 0) (layer "F.Fab")')
a('    (effects (font (size 1.27 1.27) (thickness 0.15))))')

# Fab outline
a(f'  (fp_rect (start {cyd_x1:.3f} {cyd_y1:.3f}) (end {cyd_x2:.3f} {cyd_y2:.3f})')
a('    (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))')

# Courtyard (0.25mm clearance)
a(f'  (fp_rect (start {cyd_x1 - 0.25:.3f} {cyd_y1 - 0.25:.3f}) (end {cyd_x2 + 0.25:.3f} {cyd_y2 + 0.25:.3f})')
a('    (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))')

# Pin 1 marker triangle on silkscreen
px = x_start
a(f'  (fp_line (start {px - 0.5:.3f} {row1_y - 1.2:.3f}) (end {px + 0.5:.3f} {row1_y - 1.2:.3f})')
a('    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
a(f'  (fp_line (start {px - 0.5:.3f} {row1_y - 1.2:.3f}) (end {px:.3f} {row1_y - 0.6:.3f})')
a('    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
a(f'  (fp_line (start {px + 0.5:.3f} {row1_y - 1.2:.3f}) (end {px:.3f} {row1_y - 0.6:.3f})')
a('    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')

# Pads
uid = 1
for i in range(N_POS):
    x = x_start + i * PITCH
    odd_num  = 2 * i + 1   # 1, 3, 5, ..., 39
    even_num = 2 * i + 2   # 2, 4, 6, ..., 40

    shape1 = "rect" if odd_num == 1 else "circle"
    a(f'  (pad "{odd_num}" thru_hole {shape1} (at {x:.3f} {row1_y:.3f}) '
      f'(size {PAD_SIZE} {PAD_SIZE}) (drill {DRILL}) '
      f'(layers "*.Cu" "*.Mask") '
      f'(uuid "{uid:08x}-0000-0000-0000-{uid:012x}"))')
    uid += 1

    shape2 = "rect" if even_num == 2 else "circle"
    a(f'  (pad "{even_num}" thru_hole {shape2} (at {x:.3f} {row2_y:.3f}) '
      f'(size {PAD_SIZE} {PAD_SIZE}) (drill {DRILL}) '
      f'(layers "*.Cu" "*.Mask") '
      f'(uuid "{uid:08x}-0000-0000-0000-{uid:012x}"))')
    uid += 1

a(')')

out_path = os.path.join(
    os.path.dirname(__file__),
    "..", "kicad", "footprints", "Custom.pretty",
    "PinSocket_2x20_P2.54mm_P2.81mm_Vertical.kicad_mod"
)
out_path = os.path.normpath(out_path)
with open(out_path, "w", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

print(f"Written: {out_path}")
print(f"  Pads: 40  (2x20)")
print(f"  Pin pitch:   {PITCH} mm")
print(f"  Row spacing: {ROW_SPACING} mm")
print(f"  Row 1 (odd)  y = {row1_y:.3f} mm")
print(f"  Row 2 (even) y = {row2_y:.3f} mm")
print(f"  x range: {x_start:.3f} .. {-x_start:.3f} mm")
