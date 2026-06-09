#!/usr/bin/env python3
"""
hardware/fix_pcb_placement_v3.py — Final placement micro-adjustments.

Issues:
  1. J6 at (44,68): R8 right pad at (42.62,66) is inside J6's courtyard → pth_inside_courtyard
     FIX: move J6 to (46,70) — clears R8 pad (x=42.62 < 44.5 = new courtyard left edge) ✓
  2. DS18B20_DATA trace must be updated: J6 pin2 moves from (46.54,68) to (48.54,70)
     FIX: remove old trace segments, add new route ending at (48.54,70)

Usage:
    C:\\Users\\Niels\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe hardware/fix_pcb_placement_v3.py
"""

import sys
sys.path.insert(0, r'C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin')
import pcbnew

PCB = r'C:\repos-github\PoE-FanController\hardware\kicad\PoE-FanController.kicad_pcb'
TRACE_WIDTH_MM = 0.25

# J6: (44,68) → (46,70)
#   anchor=pin1 at new pos: pin1=(46,70), pin2=(48.54,70), pin3=(51.08,70)
#   courtyard X: ~44.5 to 52.6mm   (R8 right pad at 42.62 → CLEAR)
#   courtyard Y: ~66.5 to 73.5mm   (D5 LED at y=62 courtyard ends at 63.5 → CLEAR)
J6_OLD = (44.0, 68.0)
J6_NEW = (46.0, 70.0)

# Old DS18B20_DATA trace segments (ending at old J6 pin2 = 46.54, 68)
OLD_DS18B20_SEGS = [
    ((37.62, 72.0), (46.54, 72.0)),
    ((46.54, 72.0), (46.54, 68.0)),
]

# New DS18B20_DATA trace: R14 pad2 (37.62,72) → J6 pin2 new pos (48.54,70)
NEW_DS18B20_SEGS = [
    (37.62, 72.0),
    (48.54, 72.0),
    (48.54, 70.0),
]


def coords_match(pcb_vec, xy, tol=0.02):
    return abs(pcbnew.ToMM(pcb_vec.x) - xy[0]) < tol and abs(pcbnew.ToMM(pcb_vec.y) - xy[1]) < tol


def main():
    print(f'Loading: {PCB}')
    board = pcbnew.LoadBoard(PCB)
    board.BuildConnectivity()

    # Move J6
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    if 'J6' in fps:
        j6 = fps['J6']
        j6.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(J6_NEW[0]), pcbnew.FromMM(J6_NEW[1])))
        print(f'Moved J6: {J6_OLD} -> {J6_NEW}')
    else:
        print('WARNING: J6 not found')

    # Remove old DS18B20_DATA trace segments
    removed = 0
    for track in list(board.GetTracks()):
        if not isinstance(track, pcbnew.PCB_TRACK):
            continue
        s, e = track.GetStart(), track.GetEnd()
        for (x1, y1), (x2, y2) in OLD_DS18B20_SEGS:
            if ((coords_match(s, (x1, y1)) and coords_match(e, (x2, y2))) or
                    (coords_match(s, (x2, y2)) and coords_match(e, (x1, y1)))):
                board.Remove(track)
                removed += 1
                break
    print(f'Removed {removed} old DS18B20_DATA segments')

    # Add new DS18B20_DATA trace
    net = board.FindNet('DS18B20_DATA')
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, 'DS18B20_DATA')
        board.Add(net)
    for i in range(len(NEW_DS18B20_SEGS) - 1):
        x1, y1 = NEW_DS18B20_SEGS[i]
        x2, y2 = NEW_DS18B20_SEGS[i + 1]
        track = pcbnew.PCB_TRACK(board)
        track.SetLayer(pcbnew.F_Cu)
        track.SetNet(net)
        track.SetWidth(pcbnew.FromMM(TRACE_WIDTH_MM))
        track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        track.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
        board.Add(track)
        print(f'  Route DS18B20_DATA ({x1:.2f},{y1:.2f}) -> ({x2:.2f},{y2:.2f})')

    print('Saving...')
    board.BuildConnectivity()
    board.Save(PCB)
    print(f'Saved: {PCB}')
    print('Done.')


if __name__ == '__main__':
    main()
