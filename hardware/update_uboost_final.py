#!/usr/bin/env python3
"""
update_uboost_final.py — Fix U_BOOST: replace old linear footprint with
corrected 2×2 corner layout.

Strategy
--------
The footprint was corrected from a 1×4 linear row (4 pads at y=20, x=52-60)
to a 2×2 corner layout (pads at four corners ±21mm X, ±8.5mm Y).

The board has J8 (2×20 pin header) at x=28–47mm, and fan headers at x=82mm.
Geometric constraints make it impossible to fit the 50mm-wide module entirely
to the right of J8 without exceeding the board edge. Solution:
  - Footprint courtyard shrunk to ±22mm X, ±9.5mm Y (44×19mm) — still 1mm
    clearance from every pad edge.
  - Placed at origin (70, 23) rotated 180° so:
      Pad 1 (IN+  /+5V):  (49, 14.5)  ← left-top,  close to J8[40]+5V
      Pad 2 (IN−  /GND):  (91, 14.5)  ← right-top
      Pad 3 (OUT+ /+12V): (49, 31.5)  ← left-bottom
      Pad 4 (OUT− /GND):  (91, 31.5)  ← right-bottom
  - Courtyard: x=[48,92], y=[13.5,32.5] — clears J8 right at 46.94mm.

Routing (all 1.0mm, F.Cu):
  +5V:  Pad1(49,14.5)→(45.19,14.5)→(45.19,16.67)[J8-40 +5V]
  GND:  Pad2(91,14.5)→(91,21.75)→(45.19,21.75)[J8-38 GND]
        Pad4(91,31.5)→(91,21.75)  [T-join]
  +12V: Pad3(49,31.5)→(49,39.44)→(82.47,39.44)[J2-2 +12V]
        (existing 0.4mm spine J2→J3→J4→J5 is preserved)

Run: C:\\Users\\Niels\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe hardware/update_uboost_final.py
"""

import sys
import math

sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

PCB_PATH    = r'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb'
FP_LIB_PATH = r'C:/repos-github/PoE-FanController/hardware/kicad/footprints/Custom.pretty'
FP_NAME     = 'DC-Boost-Module'

# Placement: origin and rotation
UBOOST_X   = 70.0   # mm — module centre X
UBOOST_Y   = 23.0   # mm — module centre Y
UBOOST_ROT = 180.0  # degrees — 180° so left column = IN+/OUT+, right = GND/GND

# Expected pad positions after 180° rotation (for verification)
# Pad offsets in footprint coords: 1=(+21,+8.5) 2=(-21,+8.5) 3=(+21,-8.5) 4=(-21,-8.5)
# After 180° rotation: multiply each offset by -1
# Pad1(+5V):  origin + (-21, -8.5) = (49, 14.5)
# Pad2(GND):  origin + (+21, -8.5) = (91, 14.5)
# Pad3(+12V): origin + (-21, +8.5) = (49, 31.5)
# Pad4(GND):  origin + (+21, +8.5) = (91, 31.5)

PAD_NETS = {'1': '+5V', '2': 'GND', '3': '+12V', '4': 'GND'}

POWER_WIDTH = 1.0  # mm — power trace minimum width (P-HW-07)

# ── Helpers ──────────────────────────────────────────────────────────────────

def mm(v):
    return pcbnew.FromMM(float(v))


def tomm(v):
    return pcbnew.ToMM(v)


def near(a, b, tol=0.05):
    """Return True if two VECTOR2I are within tol mm of each other."""
    return math.hypot(tomm(a.x) - tomm(b.x), tomm(a.y) - tomm(b.y)) < tol


def add_track(board, net, x1, y1, x2, y2, width_mm=POWER_WIDTH):
    """Add a straight PCB track on F.Cu."""
    seg = pcbnew.PCB_TRACK(board)
    seg.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    seg.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    seg.SetWidth(mm(width_mm))
    seg.SetLayer(pcbnew.F_Cu)
    seg.SetNet(net)
    board.Add(seg)
    return seg


def pt_near(track, x, y, tol=0.05):
    """True if either endpoint of a track is within tol mm of (x,y)."""
    p = pcbnew.VECTOR2I(mm(x), mm(y))
    return near(track.GetStart(), p, tol) or near(track.GetEnd(), p, tol)


# ── Step 0: Load ─────────────────────────────────────────────────────────────

print('Loading PCB …')
board = pcbnew.LoadBoard(PCB_PATH)

# ── Step 1: Remove old U_BOOST footprint ─────────────────────────────────────

old_uboost = None
for fp in board.GetFootprints():
    if fp.GetReference() == 'U_BOOST':
        old_uboost = fp
        break

if old_uboost:
    board.Delete(old_uboost)
    print('  Deleted old U_BOOST footprint (linear-pad variant)')
else:
    print('  No existing U_BOOST found — fresh placement')

# ── Step 2: Remove old U_BOOST routing tracks ─────────────────────────────────
#
# Two groups to remove:
#   A) All 1.0mm power tracks (GND/+5V/+12V) whose BOTH endpoints fall inside
#      the bounding box of the old linear footprint routing region.
#   B) The 0.4mm bridge track that linked the old +12V spine at y=25.5 to the
#      fan header junction at y=38.0 on x=89mm.  Without the spine, that
#      bridge's upper endpoint is dangling — delete it.

OLD_ROUTING_BOX = dict(x_min=43.0, x_max=90.0, y_min=10.0, y_max=30.0)
BRIDGE_POINT_A  = (89.0, 25.5)   # top end of bridge (spine side)
BRIDGE_POINT_B  = (89.0, 38.0)   # bot end of bridge (fan junction side)

def in_old_box(track):
    """Both endpoints inside old routing bounding box."""
    sx, sy = tomm(track.GetStart().x), tomm(track.GetStart().y)
    ex, ey = tomm(track.GetEnd().x),   tomm(track.GetEnd().y)
    b = OLD_ROUTING_BOX
    return (b['x_min'] <= sx <= b['x_max'] and b['y_min'] <= sy <= b['y_max'] and
            b['x_min'] <= ex <= b['x_max'] and b['y_min'] <= ey <= b['y_max'])


def is_bridge(track):
    """Detect the old spine-to-fan-junction bridge track."""
    if track.GetNetname() != '+12V':
        return False
    return ((pt_near(track, *BRIDGE_POINT_A) and pt_near(track, *BRIDGE_POINT_B)) or
            (pt_near(track, *BRIDGE_POINT_B) and pt_near(track, *BRIDGE_POINT_A)))


tracks_to_delete = []
for t in board.GetTracks():
    net = t.GetNetname()
    w   = tomm(t.GetWidth())
    # Group A: 1mm power tracks in old region
    if w >= 0.99 and net in {'+5V', 'GND', '+12V'} and in_old_box(t):
        tracks_to_delete.append(t)
        continue
    # Group B: bridge track
    if is_bridge(t):
        tracks_to_delete.append(t)

# De-duplicate
seen = set()
unique_del = []
for t in tracks_to_delete:
    if id(t) not in seen:
        seen.add(id(t))
        unique_del.append(t)

print(f'  Deleting {len(unique_del)} old routing tracks')
for t in unique_del:
    print(f'    [{t.GetNetname()}] '
          f'({tomm(t.GetStart().x):.2f},{tomm(t.GetStart().y):.2f})'
          f'→({tomm(t.GetEnd().x):.2f},{tomm(t.GetEnd().y):.2f})'
          f' w={tomm(t.GetWidth()):.2f}mm')
    board.Delete(t)

# ── Step 3: Load and place corrected U_BOOST footprint ───────────────────────

print(f'  Loading footprint {FP_NAME} from {FP_LIB_PATH} …')
fp_uboost = pcbnew.FootprintLoad(FP_LIB_PATH, FP_NAME)
if fp_uboost is None:
    raise RuntimeError(f'Could not load footprint {FP_NAME}')

fp_uboost.SetReference('U_BOOST')
fp_uboost.SetValue('DC-Boost-Module')
fp_uboost.SetPosition(pcbnew.VECTOR2I(mm(UBOOST_X), mm(UBOOST_Y)))
fp_uboost.SetOrientationDegrees(UBOOST_ROT)
fp_uboost.SetLayer(pcbnew.F_Cu)

board.Add(fp_uboost)
print(f'  Added U_BOOST at ({UBOOST_X}, {UBOOST_Y}) mm, rotated {UBOOST_ROT}°')

# ── Step 4: Assign nets to pads ──────────────────────────────────────────────

netmap = board.GetNetInfo()
pad_positions = {}

for pad in fp_uboost.Pads():
    pad_num  = pad.GetNumber()
    net_name = PAD_NETS.get(pad_num)
    if net_name:
        net_info = netmap.GetNetItem(net_name)
        if net_info:
            pad.SetNet(net_info)
        else:
            print(f'  WARNING: net {net_name} not found in board — pad {pad_num} unassigned')
    pos = pad.GetPosition()
    pad_positions[pad_num] = (tomm(pos.x), tomm(pos.y))
    print(f'  Pad {pad_num} ({net_name}) → ({tomm(pos.x):.3f}, {tomm(pos.y):.3f}) mm')

# Verify expected positions
expected = {
    '1': (49.0, 14.5), '2': (91.0, 14.5),
    '3': (49.0, 31.5), '4': (91.0, 31.5),
}
for num, (ex, ey) in expected.items():
    ax, ay = pad_positions[num]
    err = math.hypot(ax - ex, ay - ey)
    status = 'OK' if err < 0.1 else f'WARNING off by {err:.3f}mm'
    print(f'  Pad {num}: expected ({ex},{ey}), actual ({ax:.3f},{ay:.3f}) — {status}')

# ── Step 5: Route power connections (1.0 mm, F.Cu) ───────────────────────────

net_5v  = netmap.GetNetItem('+5V')
net_gnd = netmap.GetNetItem('GND')
net_12v = netmap.GetNetItem('+12V')

p1x, p1y = pad_positions['1']   # IN+  / +5V   (49, 14.5)
p2x, p2y = pad_positions['2']   # IN−  / GND   (91, 14.5)
p3x, p3y = pad_positions['3']   # OUT+ / +12V  (49, 31.5)
p4x, p4y = pad_positions['4']   # OUT− / GND   (91, 31.5)

print('\n  Routing power traces (1.0 mm, F.Cu) …')

# +5V: Pad1 → (45.19, p1y) → J8[40] at (45.19, 16.67)
J8_5V_X, J8_5V_Y = 45.19, 16.67
add_track(board, net_5v, p1x, p1y, J8_5V_X, p1y)       # horizontal to J8 column
add_track(board, net_5v, J8_5V_X, p1y, J8_5V_X, J8_5V_Y)  # vertical down to J8[40]
print(f'  +5V:  Pad1({p1x:.2f},{p1y:.2f})→({J8_5V_X},{p1y:.2f})→J8-40({J8_5V_X},{J8_5V_Y})')

# GND: Pad2 (91,14.5) → (91,21.75) → (45.19,21.75) J8[38]
#      Pad4 (91,31.5) → (91,21.75)  [T-join]
J8_GND_X, J8_GND_Y = 45.19, 21.75
GND_JUNC_X = p2x                                  # x=91 (same column for both GND pads)
GND_JUNC_Y = J8_GND_Y                             # y=21.75 junction
add_track(board, net_gnd, p2x, p2y, GND_JUNC_X, GND_JUNC_Y)  # Pad2 down to junction
add_track(board, net_gnd, p4x, p4y, GND_JUNC_X, GND_JUNC_Y)  # Pad4 up to junction
add_track(board, net_gnd, GND_JUNC_X, GND_JUNC_Y, J8_GND_X, J8_GND_Y)  # junction → J8[38]
print(f'  GND:  Pad2({p2x:.2f},{p2y:.2f})→({GND_JUNC_X},{GND_JUNC_Y})→J8-38({J8_GND_X},{J8_GND_Y})')
print(f'  GND:  Pad4({p4x:.2f},{p4y:.2f})→({GND_JUNC_X},{GND_JUNC_Y}) [T-join]')

# +12V: Pad3 (49,31.5) → (49,39.44) → (82.47,39.44) J2[2]
# This connects to the existing 0.4mm fan-distribution spine at J2[2].
J2_12V_X, J2_12V_Y = 82.47, 39.44
add_track(board, net_12v, p3x, p3y, p3x, J2_12V_Y)        # vertical down to J2 row
add_track(board, net_12v, p3x, J2_12V_Y, J2_12V_X, J2_12V_Y)  # horizontal to J2[2]
print(f'  +12V: Pad3({p3x:.2f},{p3y:.2f})→({p3x:.2f},{J2_12V_Y})→J2-2({J2_12V_X},{J2_12V_Y})')

# ── Step 6: Fill copper zones ─────────────────────────────────────────────────

print('\n  Filling copper zones …')
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
print('  Done.')

# ── Step 7: Save ─────────────────────────────────────────────────────────────

board.Save(PCB_PATH)
print(f'\nPCB saved → {PCB_PATH}')

# ── Step 8: Verify by reloading ───────────────────────────────────────────────

board2 = pcbnew.LoadBoard(PCB_PATH)
fp_check = None
for fp in board2.GetFootprints():
    if fp.GetReference() == 'U_BOOST':
        fp_check = fp
        break

print('\n=== Verification ===')
if fp_check:
    pos = fp_check.GetPosition()
    print(f'  U_BOOST at ({tomm(pos.x):.3f}, {tomm(pos.y):.3f}) mm, '
          f'rotation={fp_check.GetOrientationDegrees():.1f}°, '
          f'layer={fp_check.GetLayerName()}')
    for pad in fp_check.Pads():
        p = pad.GetPosition()
        print(f'  Pad {pad.GetNumber()} ({pad.GetNetname()}): '
              f'({tomm(p.x):.3f}, {tomm(p.y):.3f}) mm')
    # Check courtyard
    crtyd = []
    for g in fp_check.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            try:
                s, e = g.GetStart(), g.GetEnd()
                crtyd.append((tomm(s.x), tomm(s.y), tomm(e.x), tomm(e.y)))
            except Exception:
                pass
    if crtyd:
        xs = [c[0] for c in crtyd] + [c[2] for c in crtyd]
        ys = [c[1] for c in crtyd] + [c[3] for c in crtyd]
        print(f'  Courtyard X=[{min(xs):.2f}, {max(xs):.2f}] '
              f'Y=[{min(ys):.2f}, {max(ys):.2f}]')
        ok = min(xs) > 46.94
        print(f'  Courtyard clears J8 right edge (46.94): {"OK" if ok else "FAIL"}')
else:
    print('  ERROR: U_BOOST not found in saved PCB!')

# Count new power tracks
pwr_tracks = [t for t in board2.GetTracks()
              if t.GetNetname() in {'+5V', 'GND', '+12V'}
              and tomm(t.GetWidth()) >= 0.99]
print(f'  Power tracks (≥1mm): {len(pwr_tracks)}')
for t in pwr_tracks:
    s, e = t.GetStart(), t.GetEnd()
    print(f'    [{t.GetNetname()}] ({tomm(s.x):.2f},{tomm(s.y):.2f})'
          f'→({tomm(e.x):.2f},{tomm(e.y):.2f})')

print('\nDone — run kicad-cli pcb drc to verify.')
