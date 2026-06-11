# Widen board to 95mm, fix all placement conflicts, re-route
# Run: C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe hardware/fix_placement.py

import sys, math
sys.path.insert(0, 'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin/Lib/site-packages')
import pcbnew

PCB = 'hardware/kicad/PoE-FanController.kicad_pcb'
board = pcbnew.LoadBoard(PCB)

def mm(v): return pcbnew.FromMM(float(v))

# ── Step 1: Extend board outline right edge to x=94.025 if needed ────────────
for d in board.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        s = d.GetStart(); e = d.GetEnd()
        sx,sy = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
        ex,ey = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
        # Move any edge at x≈80 to x=94.025
        if abs(sx-80)<0.5: d.SetStart(pcbnew.VECTOR2I(mm(94.025), s.y))
        if abs(ex-80)<0.5: d.SetEnd  (pcbnew.VECTOR2I(mm(94.025), e.y))
print('Board outline checked')

# ── Step 2: Clear all tracks ──────────────────────────────────────────────────
for t in list(board.GetTracks()): board.Delete(t)

# ── Step 3: Reposition components ────────────────────────────────────────────
# Board: (11.975, 11.975) → (94.025, 90.025)  [82.05 × 78.05 mm]
# Top-left corner aligned with J8 row-A / column-1 corner.
# Positions recorded from PCB after user manual alignment on 2026-06-11.
# DO NOT change without user approval.

positions = {
    # ── Boost converter chain ──────────────────────────────────────────────────
    'L1':   (53.975,  16.670,    0.0),
    'C1':   (53.975,  23.475,  -90.0),
    'U1':   (71.675,  23.707,  180.0),
    'D1':   (71.975,  16.670,    0.0),
    'C2':   (84.675,  23.475,  -90.0),

    # ── TACH pull-up resistors ─────────────────────────────────────────────────
    'R5':   (61.975,  43.095,   90.0),
    'R6':   (61.975,  56.595,   90.0),
    'R7':   (61.975,  70.095,   90.0),
    'R8':   (61.975,  83.635,   90.0),

    # ── PWM indicator resistors ────────────────────────────────────────────────
    'R9':   (65.975,  35.475,  -90.0),
    'R10':  (65.975,  48.975,  -90.0),
    'R11':  (65.975,  62.475,  -90.0),
    'R12':  (65.975,  76.015,  -90.0),

    # ── PWM activity LEDs ──────────────────────────────────────────────────────
    'D2':   (71.120,  41.975,    0.0),
    'D3':   (71.120,  55.475,    0.0),
    'D4':   (71.120,  68.975,    0.0),
    'D5':   (71.120,  82.475,    0.0),

    # ── Fan headers ───────────────────────────────────────────────────────────
    'J2':   (82.475,  41.975,   90.0),
    'J3':   (82.475,  55.475,   90.0),
    'J4':   (82.475,  68.975,   90.0),
    'J5':   (82.475,  82.475,   90.0),

    # ── Left / sensor zone ────────────────────────────────────────────────────
    'R3':   (17.975,  18.475,  -90.0),
    'LED1': (18.000,  30.975,  -90.0),
    'R15':  (18.000,  39.475,  -90.0),
    'LED6': (17.975,  51.475,  -90.0),
    'R13':  (22.975,  18.475,  -90.0),
    'LED2': (22.975,  30.975,  -90.0),
    'R14':  (24.475,  55.095,   90.0),
    'J6':   (19.420,  61.995,    0.0),
    'HUM1': (21.935,  71.475,  180.0),

    # ── Logo / branding ───────────────────────────────────────────────────────
    'G***': (37.500,  77.500,    0.0),
}


for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref in positions:
        x, y, rot = positions[ref]
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.SetOrientationDegrees(rot)

board.Save(PCB)
board = pcbnew.LoadBoard(PCB)

# Dump final positions + bboxes to verify
print('\nFinal positions and bounding boxes:')
check_refs = ['C1','L1','D1','U1','C2','R9','R10','J2','J3','J4','J5']
for fp in board.GetFootprints():
    if fp.GetReference() in check_refs:
        bb = fp.GetBoundingBox()
        x1,y1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
        x2,y2 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
        pos = fp.GetPosition()
        print(f'  {fp.GetReference():5s} center=({pcbnew.ToMM(pos.x):.1f},{pcbnew.ToMM(pos.y):.1f}) '
              f'bbox=({x1:.1f},{y1:.1f})-({x2:.1f},{y2:.1f})')

print('\nDone. Run route_v5.py next.')
