#!/usr/bin/env python3
"""
hardware/fix_pcb_placement.py — Fix PCB placement issues for issue #97.

Problems fixed:
  1. J6 (Molex KK-254 3-pin probe connector) placed at (40,82) — 4mm below the
     board edge. Moved to (44, 68) — within board bounds.
  2. R14 (DS18B20 pull-up 4.7kΩ) placed at (25,82) — 4mm below board edge.
     Moved to (30, 72) — within board bounds.
  3. Fan headers J2-J5 arranged in a vertical column (x=50, y=12/30/48/66),
     consuming 60mm of the 78mm board height and leaving no room for J6.
     Reoriented to a horizontal row: rotated 90° and moved to the new right
     section (x=63, y=10/22/34/46). Pins now run horizontally (in X), not
     vertically (in Y).
  4. TACH pull-up resistors R5-R8 moved with their fan headers to (x=57,
     y=10/22/34/46) — kept adjacent to each fan header's TACH pin.
  5. Board outline widened from 56mm to 70mm to accommodate the horizontal
     fan section. Height remains 78mm.
  6. Off-board DS18B20_DATA traces (y>78) removed; re-routed for new positions.

Usage:
    C:\\Users\\Niels\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe hardware/fix_pcb_placement.py
"""

import sys
sys.path.insert(0, r'C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin')
import pcbnew

PCB = r'C:\repos-github\PoE-FanController\hardware\kicad\PoE-FanController.kicad_pcb'

BOARD_NEW_WIDTH_MM = 70.0   # widened from 56mm
TRACE_WIDTH_MM     = 0.25   # signal class (P-HW-07)

# Fan headers: (ref, new_cx_mm, new_cy_mm, rot_deg)
# Current: (50, 12/30/48/66) rot=0 — vertical column
# New:     (63, 10/22/34/46) rot=90 — horizontal row, pins run left-right in X
FAN_HEADER_MOVES = [
    ('J2', 63.0, 10.0, 90.0),
    ('J3', 63.0, 22.0, 90.0),
    ('J4', 63.0, 34.0, 90.0),
    ('J5', 63.0, 46.0, 90.0),
]

# TACH pull-up resistors: move alongside their fan headers
# Current: (35, 12/30/48/66). New: (57, 10/22/34/46)
# At (57, y) rot=0: pad1 (+3V3) at x=53.19, pad2 (TACH) at x=60.81
# Fan header TACH pin3 (at 90° rot, center 63, y) is at x=61.73 — short trace needed
TACH_RES_MOVES = [
    ('R5', 57.0, 10.0, 0.0),
    ('R6', 57.0, 22.0, 0.0),
    ('R7', 57.0, 34.0, 0.0),
    ('R8', 57.0, 46.0, 0.0),
]

# DS18B20 probe components: move from off-board to within board
# J6 anchor = pin1 (GND). pin2 (DATA) at cx+2.54, pin3 (+3V3) at cx+5.08
# R14 anchor = footprint center. pad1 (+3V3) at cx-3.81, pad2 (DATA) at cx+3.81
PROBE_MOVES = [
    ('J6',  44.0, 68.0, 0.0),
    ('R14', 30.0, 72.0, 0.0),
]

# New DS18B20_DATA trace: R14 pad2 → J6 pin2
# R14 center (30,72), R_Axial pad2 at center+3.81 = (33.81, 72)
# J6 anchor pin1 at (44,68), pin2 at (44+2.54, 68) = (46.54, 68)
# Route: (33.81, 72) → right to x=46.54 → up to y=68
NEW_ROUTES = [
    ('DS18B20_DATA', TRACE_WIDTH_MM, [
        (33.81, 72.0),
        (46.54, 72.0),
        (46.54, 68.0),
    ]),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fp_map(board):
    return {fp.GetReference(): fp for fp in board.GetFootprints()}


def move_footprint(board, ref, cx, cy, rot_deg):
    fps = fp_map(board)
    if ref not in fps:
        print(f'  WARNING: {ref} not found')
        return False
    fp = fps[ref]
    old_pos = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
    fp.SetOrientationDegrees(rot_deg)
    ox, oy = pcbnew.ToMM(old_pos.x), pcbnew.ToMM(old_pos.y)
    print(f'  {ref}: ({ox:.2f},{oy:.2f}) → ({cx:.2f},{cy:.2f}) rot={rot_deg}°')
    return True


def update_board_outline(board):
    """Widen the Edge.Cuts rect from 56mm to BOARD_NEW_WIDTH_MM."""
    for shape in board.GetDrawings():
        if shape.GetLayer() != pcbnew.Edge_Cuts:
            continue
        # Try SHAPE_T_RECT (int 4) or pcbnew.SHAPE_T.RECT
        try:
            shape_type = shape.GetShape()
            is_rect = (shape_type == pcbnew.SHAPE_T_RECT)
        except AttributeError:
            try:
                is_rect = (shape_type == 4)  # SHAPE_T_RECT = 4
            except Exception:
                is_rect = False
        if not is_rect:
            continue
        start = shape.GetStart()
        end   = shape.GetEnd()
        sx, sy = pcbnew.ToMM(start.x), pcbnew.ToMM(start.y)
        ex, ey = pcbnew.ToMM(end.x),   pcbnew.ToMM(end.y)
        print(f'  Current outline: ({sx},{sy}) → ({ex},{ey})')
        new_ex = sx + BOARD_NEW_WIDTH_MM
        shape.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(new_ex), pcbnew.FromMM(ey)))
        print(f'  Updated outline: ({sx},{sy}) → ({new_ex},{ey})')
        return True
    # Fallback: scan all shapes on Edge.Cuts for any that look like a board rect
    print('  WARNING: RECT shape not detected; scanning all Edge.Cuts shapes...')
    for shape in board.GetDrawings():
        if shape.GetLayer() != pcbnew.Edge_Cuts:
            continue
        try:
            start = shape.GetStart()
            end   = shape.GetEnd()
            sx, sy = pcbnew.ToMM(start.x), pcbnew.ToMM(start.y)
            ex, ey = pcbnew.ToMM(end.x),   pcbnew.ToMM(end.y)
            if abs(sx) < 1 and abs(sy) < 1 and ex > 40 and ey > 40:
                print(f'  Found candidate: ({sx},{sy}) → ({ex},{ey})')
                new_ex = sx + BOARD_NEW_WIDTH_MM
                shape.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(new_ex), pcbnew.FromMM(ey)))
                print(f'  Updated to ({sx},{sy}) → ({new_ex},{ey})')
                return True
        except Exception:
            continue
    print('  ERROR: board outline not updated')
    return False


def remove_off_board_traces(board, max_y_mm=78.0, max_x_mm=56.0):
    """Remove trace segments whose start or end is outside the original board bounds."""
    tracks = list(board.GetTracks())
    removed = 0
    for track in tracks:
        if not isinstance(track, pcbnew.PCB_TRACK):
            continue
        sy = pcbnew.ToMM(track.GetStart().y)
        ey = pcbnew.ToMM(track.GetEnd().y)
        if sy > max_y_mm or ey > max_y_mm:
            board.Remove(track)
            removed += 1
    print(f'  Removed {removed} off-board trace segments (y > {max_y_mm}mm)')


def get_or_create_net(board, name):
    n = board.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        print(f'  Created net: {name}')
    return n


def add_routes(board):
    for net_name, width_mm, points in NEW_ROUTES:
        net = get_or_create_net(board, net_name)
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            track = pcbnew.PCB_TRACK(board)
            track.SetLayer(pcbnew.F_Cu)
            track.SetNet(net)
            track.SetWidth(pcbnew.FromMM(width_mm))
            track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
            track.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
            board.Add(track)
            print(f'  Route [{net_name}] ({x1:.2f},{y1:.2f}) → ({x2:.2f},{y2:.2f})')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f'Loading: {PCB}')
    board = pcbnew.LoadBoard(PCB)
    board.BuildConnectivity()

    print('\n=== 1. Board outline ===')
    update_board_outline(board)

    print('\n=== 2. Fan headers → horizontal row ===')
    for ref, cx, cy, rot in FAN_HEADER_MOVES:
        move_footprint(board, ref, cx, cy, rot)

    print('\n=== 3. TACH pull-up resistors ===')
    for ref, cx, cy, rot in TACH_RES_MOVES:
        move_footprint(board, ref, cx, cy, rot)

    print('\n=== 4. DS18B20 probe components onto board ===')
    for ref, cx, cy, rot in PROBE_MOVES:
        move_footprint(board, ref, cx, cy, rot)

    print('\n=== 5. Remove off-board traces ===')
    remove_off_board_traces(board)

    print('\n=== 6. Add new DS18B20_DATA traces ===')
    add_routes(board)

    print('\nSaving...')
    board.BuildConnectivity()
    board.Save(PCB)
    print(f'Saved: {PCB}')

    # Verify
    board2 = pcbnew.LoadBoard(PCB)
    board2.BuildConnectivity()
    fps = {fp.GetReference(): fp for fp in board2.GetFootprints()}
    print('\n=== Verification ===')
    for ref in ['J2', 'J3', 'J4', 'J5', 'R5', 'R6', 'R7', 'R8', 'J6', 'R14']:
        if ref in fps:
            pos = fps[ref].GetPosition()
            x, y = round(pcbnew.ToMM(pos.x), 2), round(pcbnew.ToMM(pos.y), 2)
            rot  = round(fps[ref].GetOrientationDegrees(), 1)
            print(f'  {ref:5s}: ({x:6.2f}, {y:6.2f}) rot={rot}°')
    unconn = board2.GetConnectivity().GetUnconnectedCount(False)
    print(f'\nUnconnected ratsnest: {unconn}')
    print('Done.')


if __name__ == '__main__':
    main()
