"""Generate KiCad footprint for Waveshare ESP32-P4-POE-ETH GPIO header.

2x20 female pin socket, 2.54mm pin pitch, 15.38mm row-to-row spacing.

IMPORTANT: The 15.38mm row spacing is derived from:
  - Board width: 21.00 mm
  - Edge-to-pin-centre distance: 2.81 mm (from EACH long edge)
  - Row 1 (odd):  at y =  2.81 mm from top long edge of ESP32
  - Row 2 (even): at y = 18.19 mm from top long edge (= 21.00 - 2.81)
  - Row-to-row: 18.19 - 2.81 = 15.38 mm

The "2.81 mm" in the dimension drawing is the edge-to-pin distance, NOT the row pitch.

Board dimension source: docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-details-size-*.webp
PCB layout source:      docs/kb/Sample-PCB-Sketch.png
"""

import os

PITCH = 2.54
ROW_SPACING = 15.38  # = 21.00 - 2*2.81 mm
N_POS = 20  # 20 positions x 2 rows = 40 pins
PAD_SIZE = 1.7
DRILL = 1.0

row1_y = -ROW_SPACING / 2  # -7.69 mm
row2_y =  ROW_SPACING / 2  # +7.69 mm
x_start = -(N_POS - 1) / 2.0 * PITCH  # -24.13

cyd_x1 = x_start - PITCH / 2  # -25.4
cyd_x2 = -cyd_x1               # +25.4
cyd_y1 = row1_y - 1.5          # -9.19
cyd_y2 = row2_y + 1.5          # +9.19

lines = []
a = lines.append

a('(footprint "PinSocket_2x20_P2.54mm_P15.38mm_Vertical"')
a('  (version 20260206)')
a('  (generator "custom")')
a('  (generator_version "10.0")')
a('  (layer "F.Cu")')
a('  (descr "2x20 Female Pin Socket, 2.54mm pin pitch, 15.38mm row spacing - Waveshare ESP32-P4-POE-ETH (SKU 32088). Row1 at 2.81mm, Row2 at 18.19mm from board long edge.")')
a('  (tags "connector female socket 2x20 2.54mm 15.38mm waveshare esp32-p4 poe-eth sku32088")')
a('  (attr through_hole)')

a(f'  (fp_text reference "J" (at 0 {cyd_y1 - 1.0:.3f} 0) (layer "F.SilkS")')
a('    (effects (font (size 1.27 1.27) (thickness 0.15))))')
a(f'  (fp_text value "PinSocket_2x20_P2.54mm_P15.38mm_Vertical" (at 0 {cyd_y2 + 1.0:.3f} 0) (layer "F.Fab")')
a('    (effects (font (size 1.27 1.27) (thickness 0.15))))')

a(f'  (fp_rect (start {cyd_x1:.3f} {cyd_y1:.3f}) (end {cyd_x2:.3f} {cyd_y2:.3f})')
a('    (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))')

a(f'  (fp_rect (start {cyd_x1 - 0.25:.3f} {cyd_y1 - 0.25:.3f}) (end {cyd_x2 + 0.25:.3f} {cyd_y2 + 0.25:.3f})')
a('    (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))')

px = x_start
a(f'  (fp_line (start {px - 0.5:.3f} {row1_y - 1.2:.3f}) (end {px + 0.5:.3f} {row1_y - 1.2:.3f})')
a('    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
a(f'  (fp_line (start {px - 0.5:.3f} {row1_y - 1.2:.3f}) (end {px:.3f} {row1_y - 0.6:.3f})')
a('    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
a(f'  (fp_line (start {px + 0.5:.3f} {row1_y - 1.2:.3f}) (end {px:.3f} {row1_y - 0.6:.3f})')
a('    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')

uid = 1
for i in range(N_POS):
    x = x_start + i * PITCH
    odd_num  = 2 * i + 1
    even_num = 2 * i + 2

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
    "PinSocket_2x20_P2.54mm_P15.38mm_Vertical.kicad_mod"
)
out_path = os.path.normpath(out_path)
with open(out_path, "w", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

print(f"Written: {out_path}")
print(f"  Pads: 40  (2x20)")
print(f"  Pin pitch:   {PITCH} mm")
print(f"  Row spacing: {ROW_SPACING} mm  (= 21.00 - 2x2.81 mm)")
print(f"  Row 1 (odd)  y = {row1_y:.3f} mm  (2.81 mm from ESP32 long edge)")
print(f"  Row 2 (even) y = {row2_y:.3f} mm  (18.19 mm from same edge)")
print(f"  x span:  {x_start:.3f} .. {-x_start:.3f} mm  ({(N_POS-1)*PITCH:.2f} mm total)")