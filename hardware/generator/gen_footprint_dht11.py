"""Generate KiCad footprint for DHT11 temperature + humidity sensor (direct solder).

3 through-hole pads at 2.54 mm pitch representing:
  Pin 1 — VCC  (+3.3 V)
  Pin 2 — DATA (single-wire)
  Pin 3 — GND

DHT11 body outline (typical sensor dimensions):
  Width:  15.5 mm  (x-axis)
  Height: 12.0 mm  (y-axis, above the pins)
  Depth:   6.7 mm  (z, informational only)

Pad: 1.7 mm circle, 1.0 mm drill.  Pin 1 uses a square pad for polarity marking.
"""

import os

PITCH    = 2.54          # mm — pin-to-pin spacing
PAD_SIZE = 1.7           # mm — pad diameter
DRILL    = 1.0           # mm — drill diameter

# Body dimensions (DHT11 typical)
BODY_W   = 15.5          # mm
BODY_H   = 12.0          # mm

# Pad row: centred at x=0, y=0.  Pads at x = -2.54, 0, +2.54
pad_xs   = [-PITCH, 0.0, PITCH]  # VCC, DATA, GND

# Body outline sits above the pads (negative y direction in KiCad schematic coords)
body_x1  = -BODY_W / 2
body_x2  =  BODY_W / 2
body_y1  = -(BODY_H + 1.0)   # top of body
body_y2  = -1.0               # bottom of body (1 mm above pad row)

# Courtyard = body + 0.25 mm expansion
cyd_x1   = body_x1 - 0.25
cyd_x2   = body_x2 + 0.25
cyd_y1   = body_y1 - 0.25
cyd_y2   = PAD_SIZE / 2 + 0.5   # extend below pads

lines = []
a = lines.append

a('(footprint "DHT11_Direct"')
a('  (version 20260206)')
a('  (generator "custom")')
a('  (layer "F.Cu")')
a('  (descr "DHT11 temperature + humidity sensor, direct solder, 3 pins 2.54mm pitch. Pin 1=VCC, Pin 2=DATA, Pin 3=GND.")')
a('  (tags "DHT11 sensor temperature humidity direct-solder 3-pin 2.54mm")')
a('  (attr through_hole)')

# Reference and value text
a(f'  (fp_text reference "HUM" (at 0 {body_y1 - 1.5:.3f}) (layer "F.SilkS")')
a('    (effects (font (size 1.27 1.27) (thickness 0.15))))')
a(f'  (fp_text value "DHT11_Direct" (at 0 {cyd_y2 + 1.0:.3f}) (layer "F.Fab")')
a('    (effects (font (size 1.27 1.27) (thickness 0.15))))')

# Body outline — F.Fab
a(f'  (fp_rect (start {body_x1:.3f} {body_y1:.3f}) (end {body_x2:.3f} {body_y2:.3f})')
a('    (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))')

# Silkscreen outline — offset inward by 0.11 mm from F.Fab to distinguish layers
silk_x1  = body_x1 + 0.11
silk_x2  = body_x2 - 0.11
silk_y1  = body_y1 + 0.11
silk_y2  = body_y2 - 0.11
a(f'  (fp_rect (start {silk_x1:.3f} {silk_y1:.3f}) (end {silk_x2:.3f} {silk_y2:.3f})')
a('    (stroke (width 0.12) (type solid)) (fill none) (layer "F.SilkS"))')

# Pin 1 marker — small triangle on silkscreen at pad 1 location
p1x = pad_xs[0]
a(f'  (fp_line (start {p1x - 0.5:.3f} {-PAD_SIZE:.3f}) (end {p1x + 0.5:.3f} {-PAD_SIZE:.3f})')
a('    (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')

# Courtyard — F.CrtYd
a(f'  (fp_rect (start {cyd_x1:.3f} {cyd_y1:.3f}) (end {cyd_x2:.3f} {cyd_y2:.3f})')
a('    (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))')

# Pin labels on F.Fab
# Pin label text removed — fp_text user requires UUID in KiCad 10 and causes load failure

# Pads
for i, px in enumerate(pad_xs):
    pad_num = i + 1
    shape   = "rect" if pad_num == 1 else "circle"
    a(f'  (pad "{pad_num}" thru_hole {shape} (at {px:.3f} 0.000)'
      f' (size {PAD_SIZE} {PAD_SIZE}) (drill {DRILL})'
      f' (layers "*.Cu" "*.Mask")'
      f' (uuid "d480000{pad_num}-0000-0000-0000-00000000000{pad_num}"))')

a(')')

out_path = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "..", "kicad", "footprints", "Custom.pretty",
    "DHT11_Direct.kicad_mod"
))

with open(out_path, "w", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

print(f"Written: {out_path}")
print(f"  Pads: 3 (Pin1=VCC square, Pin2=DATA circle, Pin3=GND circle)")
print(f"  Pitch:     {PITCH} mm")
print(f"  Pad size:  {PAD_SIZE} mm  /  Drill: {DRILL} mm")
print(f"  Body:      {BODY_W} mm × {BODY_H} mm")
