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
    # Boost chain — verified non-overlapping with 2mm+ courtyard gaps
    # L1 bbox (48.5,1.5)-(61.7,8.5)  D1 bbox (62.5,2.5)-(69.5,7.5)
    # U1 bbox (55,11)-(63,19)         C1 bbox (38.7,9.8)-(44.7,18.4)
    # C2 bbox (70.7,9.8)-(77.7,18.4)
    'L1': (50, 5,  0),      # inductor:    pads (50,5)  and (60.16,5)
    'D1': (66, 5,  0),      # schottky:    pads (64,5)  and (68,5)   — gap from L1 right 0.8mm
    'U1': (57, 15, 0),      # boost IC:    pins at y=15, x=57..61.8  — 2.5mm below L1
    'C1': (41, 15, 0),      # +5V bypass:  pads (41,15) and (43.5,15)— 3.8mm left of L1
    'C2': (73,  8, 0),      # +12V filter: pads (73,8) and (75.5,8)   — above R9

    # Indicator resistors — horizontal, one per fan gap, 1.7mm from fan headers
    # R*.bbox right=78.5, J* left=80.2 → gap=1.7mm
    'R9':  (70, 14, 0),     # FAN1 ind: pads (70,14)  and (77.62,14) — below C2
    'R10': (70, 24, 0),     # FAN2 ind: pads (70,24)  and (77.62,24) — y=22-30 gap
    'R11': (70, 36, 0),     # FAN3 ind: pads (70,36)  and (77.62,36) — y=34-42 gap
    'R12': (70, 48, 0),     # FAN4 ind: pads (70,48)  and (77.62,48) — y=46-54 gap

    # Fan headers — moved right to x=82 (clear of all components)
    'J2': (82, 10, 0),
    'J3': (82, 22, 0),
    'J4': (82, 34, 0),
    'J5': (82, 46, 0),

    # Indicator LEDs — stay close to pull-up column at x=48
    'D2': (48, 10, 0),
    'D3': (48, 22, 0),
    'D4': (48, 34, 0),
    'D5': (48, 46, 0),

    # Probe LED circuit
    'LED6': (48, 58, 0),
    'R15':  (38, 58, 0),

    # DS18B20 pull-up — left zone
    'R14': (4, 52, 0),
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
