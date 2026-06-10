# Widen board to 95mm, fix all placement conflicts, re-route
# Run: C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe hardware/fix_placement.py

import sys, math
sys.path.insert(0, 'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin/Lib/site-packages')
import pcbnew

PCB = 'hardware/kicad/PoE-FanController.kicad_pcb'
board = pcbnew.LoadBoard(PCB)

def mm(v): return pcbnew.FromMM(float(v))

# ── Step 1: Extend board outline from 70mm → 95mm in X ───────────────────────
for d in board.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        s = d.GetStart(); e = d.GetEnd()
        sx,sy = pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)
        ex,ey = pcbnew.ToMM(e.x), pcbnew.ToMM(e.y)
        # Move any edge at x=70 to x=95
        if abs(sx-70)<0.5: d.SetStart(pcbnew.VECTOR2I(mm(95), s.y))
        if abs(ex-70)<0.5: d.SetEnd  (pcbnew.VECTOR2I(mm(95), e.y))
print('Board extended to 95mm')

# ── Step 2: Clear all tracks ──────────────────────────────────────────────────
for t in list(board.GetTracks()): board.Delete(t)

# ── Step 3: Reposition components — no-overlap layout ────────────────────────
# Board: 95mm(X) × 78mm(Y)  J8: Row A at x=17.81mm, Row B at x=33.19mm
#
# Zone layout (right of ESP32 at x=36.7mm):
#   x=37-55  : C1(bypass), L1(inductor) — boost input side
#   x=55-70  : D1(schottky), U1(boost IC), C2(output) — boost output side
#   x=70-78  : R9-R12 indicator resistors (rotated 90° for narrow x-footprint)
#   x=80-95  : J2-J5 fan headers (right side access)
#   (pull-ups R5-R8 stay at x=46, y=16/28/38/48)

positions = {
    # ── User-verified positions (read from PCB 2026-06-10, after manual placement) ──
    # DO NOT change without user approval
    #
    # Boost converter chain
    'L1':   (41.00,  4.50,    0),
    'D1':   (70.50,  4.50,    0),
    'U1':   (62.90,  8.05,  180),
    'C1':   (41.00,  9.00,  -90),
    'C2':   (73.00,  9.00,  -90),

    # PWM indicator resistors
    'R9':   (46.50, 25.00,    0),
    'R10':  (46.50, 37.50,    0),
    'R11':  (46.50, 51.00,    0),
    'R12':  (46.50, 63.00,    0),

    # PWM activity LEDs
    'D2':   (59.12, 25.00,    0),
    'D3':   (59.12, 37.50,    0),
    'D4':   (59.12, 51.00,    0),
    'D5':   (59.12, 63.00,    0),

    # Fan headers
    'J2':   (73.12, 17.96,  -90),
    'J3':   (73.12, 32.00,  -90),
    'J4':   (73.12, 46.00,  -90),
    'J5':   (73.12, 59.00,  -90),

    # TACH pull-up resistors
    'R5':   (54.12, 21.50,  180),
    'R6':   (54.12, 33.50,  180),
    'R7':   (54.12, 47.00,  180),
    'R8':   (54.12, 59.50,  180),

    # Left zone
    'HUM1': ( 7.00, 68.00,   90),
    'J6':   ( 7.00, 56.00,    0),
    'R14':  ( 4.00, 52.00,    0),
    'LED1': ( 6.00, 19.96,  -90),
    'R3':   ( 6.00,  7.96,  -90),
    'LED2': (11.00, 19.96,  -90),
    'R13':  (11.00,  7.96,  -90),
    'LED6': ( 7.00, 44.00,    0),
    'R15':  ( 7.00, 50.00,    0),
    'G***': (25.50, 65.50,    0),
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
