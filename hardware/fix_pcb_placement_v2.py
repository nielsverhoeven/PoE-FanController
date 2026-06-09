#!/usr/bin/env python3
"""
hardware/fix_pcb_placement_v2.py — Correct placement issues found in DRC after fix_pcb_placement.py.

Issues found:
  1. J2-J5 at x=63 rot=90: rightmost pad (GND, anchor+7.62) at x=70.62 → outside board edge
     FIX: move fan headers from x=63 to x=58 so all pads stay within 70mm board
  2. R5-R8 at (57, 10/22/34/46): right pad (TACH) at x=60.81 is 0.92mm from J2-J5's +12V pad
     FIX: move TACH pull-up resistors back to safe (35, 12/30/48/66) — original Y positions
  3. DS18B20_DATA trace starts at (33.81,72) — wrong, R14 anchor=pad1 so pad2 is at (37.62,72)
     FIX: remove wrong trace segments, add correct trace from R14 pad2 (37.62,72) → J6 pin2 (46.54,68)

Usage:
    C:\\Users\\Niels\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe hardware/fix_pcb_placement_v2.py
"""

import sys
sys.path.insert(0, r'C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin')
import pcbnew

PCB = r'C:\repos-github\PoE-FanController\hardware\kicad\PoE-FanController.kicad_pcb'

TRACE_WIDTH_MM = 0.25  # signal class (P-HW-07)

# Fan headers: move from x=63 (pads overshoot 70mm edge) to x=58
# At x=58 rot=90 with anchor=pad1: pad4 at x=58+7.62=65.62mm < 70mm ✓
FAN_HEADER_MOVES = [
    ('J2', 58.0, 10.0, 90.0),
    ('J3', 58.0, 22.0, 90.0),
    ('J4', 58.0, 34.0, 90.0),
    ('J5', 58.0, 46.0, 90.0),
]

# TACH pull-up resistors: move back to original Y positions at x=35
# These are in the main board area and connect via schematic nets (not proximity traces)
TACH_RES_MOVES = [
    ('R5', 35.0, 12.0, 0.0),
    ('R6', 35.0, 30.0, 0.0),
    ('R7', 35.0, 48.0, 0.0),
    ('R8', 35.0, 66.0, 0.0),
]

# DS18B20_DATA trace corrections:
#   R14 at (30, 72) with anchor=pad1: pad1=(30,72), pad2=(37.62,72)
#   J6  at (44, 68) with anchor=pin1: pin1=(44,68), pin2=(46.54,68)
#   Route: pad2(37.62,72) → right to x=46.54 → up to pin2(46.54,68)
NEW_ROUTES = [
    ('DS18B20_DATA', TRACE_WIDTH_MM, [
        (37.62, 72.0),
        (46.54, 72.0),
        (46.54, 68.0),
    ]),
]

# Coordinates of the WRONG trace segments added by fix_pcb_placement.py (to remove)
WRONG_TRACE_COORDS = [
    # These were added with wrong start point (33.81 instead of 37.62)
    ((33.81, 72.0), (46.54, 72.0)),
    ((46.54, 72.0), (46.54, 68.0)),
]


def fp_map(board):
    return {fp.GetReference(): fp for fp in board.GetFootprints()}


def move_footprint(board, ref, cx, cy, rot_deg):
    fps = fp_map(board)
    if ref not in fps:
        print(f'  WARNING: {ref} not found')
        return False
    fp = fps[ref]
    old = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
    fp.SetOrientationDegrees(rot_deg)
    ox, oy = round(pcbnew.ToMM(old.x), 2), round(pcbnew.ToMM(old.y), 2)
    print(f'  {ref}: ({ox},{oy}) -> ({cx},{cy}) rot={rot_deg}')
    return True


def coords_match(a, b, tol=0.01):
    """Return True if two (x,y) pcbnew coordinates match within tol mm."""
    return (abs(pcbnew.ToMM(a.x) - b[0]) < tol and
            abs(pcbnew.ToMM(a.y) - b[1]) < tol)


def remove_wrong_traces(board):
    """Remove the incorrectly-routed DS18B20_DATA trace segments from fix v1."""
    tracks = list(board.GetTracks())
    removed = 0
    for track in tracks:
        if not isinstance(track, pcbnew.PCB_TRACK):
            continue
        s = track.GetStart()
        e = track.GetEnd()
        for (x1, y1), (x2, y2) in WRONG_TRACE_COORDS:
            if ((coords_match(s, (x1, y1)) and coords_match(e, (x2, y2))) or
                    (coords_match(s, (x2, y2)) and coords_match(e, (x1, y1)))):
                board.Remove(track)
                removed += 1
                break
    print(f'  Removed {removed} wrong DS18B20_DATA trace segments')


def get_or_create_net(board, name):
    n = board.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
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
            print(f'  Route [{net_name}] ({x1:.2f},{y1:.2f}) -> ({x2:.2f},{y2:.2f})')


def main():
    print(f'Loading: {PCB}')
    board = pcbnew.LoadBoard(PCB)
    board.BuildConnectivity()

    print('\n=== 1. Fan headers: move to x=58 (away from 70mm edge) ===')
    for ref, cx, cy, rot in FAN_HEADER_MOVES:
        move_footprint(board, ref, cx, cy, rot)

    print('\n=== 2. TACH pull-up resistors: restore to original Y positions ===')
    for ref, cx, cy, rot in TACH_RES_MOVES:
        move_footprint(board, ref, cx, cy, rot)

    print('\n=== 3. Remove wrong DS18B20_DATA traces ===')
    remove_wrong_traces(board)

    print('\n=== 4. Add correct DS18B20_DATA traces ===')
    add_routes(board)

    print('\nSaving...')
    board.BuildConnectivity()
    board.Save(PCB)
    print(f'Saved: {PCB}')
    print('Done.')


if __name__ == '__main__':
    main()
