#!/usr/bin/env python3
"""
hardware/fix_pcb_alignment.py — Align all right-side components to a uniform 5-row grid.

Layout (matching PoE_FanController.drawio.png):
  Rows at y = 10, 22, 34, 46, 58  (12 mm spacing)
  Col 1 x=25: R5-R8 (TACH pull-ups), R14 (DS18B20 pull-up)   — analogous
  Col 2 x=36: R9-R12 (LED resistors), R15 (LED6 resistor)     — analogous
  Col 3 x=48: D2-D5 (status LEDs),    LED6 (probe status LED) — analogous
  Col 4 x=58: J2-J5 (fan headers),    J6 (probe connector)    — analogous

Fan headers J2-J5 are already correct at (58, 10/22/34/46) rot=90 — kept as-is.

Tracks removed (all now dangling after moves):
  DS18B20_DATA segments (old v2/v3 routes)
  PROBE_LED_A segment (R15→LED6, old positions)

Tracks NOT re-added — leave routing to KiCad GUI (ROUTING_PENDING convention).

Usage:
    C:\\Users\\Niels\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe hardware/fix_pcb_alignment.py
"""

import sys
sys.path.insert(0, r'C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin')
import pcbnew

PCB = r'C:\repos-github\PoE-FanController\hardware\kicad\PoE-FanController.kicad_pcb'

# Row Y values (mm)
ROWS = [10.0, 22.0, 34.0, 46.0, 58.0]

# Component moves: { ref: (x, y, rot) }
MOVES = {
    # Fan headers — already correct, listed for documentation only
    # 'J2': (58.0, 10.0, 90.0),
    # 'J3': (58.0, 22.0, 90.0),
    # 'J4': (58.0, 34.0, 90.0),
    # 'J5': (58.0, 46.0, 90.0),

    # Row 5 probe connector — left-align with J2-J5 at x=58
    'J6':   (58.0, 58.0,  0.0),

    # Status LEDs — col 3 x=48, one per row
    'D2':   (48.0, 10.0,  0.0),
    'D3':   (48.0, 22.0,  0.0),
    'D4':   (48.0, 34.0,  0.0),
    'D5':   (48.0, 46.0,  0.0),
    'LED6': (48.0, 58.0,  0.0),  # DS18B20 probe status LED

    # LED current-limiting resistors — col 2 x=36, one per row
    'R9':   (36.0, 10.0,  0.0),
    'R10':  (36.0, 22.0,  0.0),
    'R11':  (36.0, 34.0,  0.0),
    'R12':  (36.0, 46.0,  0.0),
    'R15':  (36.0, 58.0,  0.0),  # LED6 current-limiting resistor

    # Pull-up resistors — col 1 x=25, one per row
    'R5':   (25.0, 10.0,  0.0),  # FAN1 TACH pull-up
    'R6':   (25.0, 22.0,  0.0),  # FAN2 TACH pull-up
    'R7':   (25.0, 34.0,  0.0),  # FAN3 TACH pull-up
    'R8':   (25.0, 46.0,  0.0),  # FAN4 TACH pull-up
    'R14':  (25.0, 58.0,  0.0),  # DS18B20 data pull-up
}


def move(fps, ref, x, y, rot):
    if ref not in fps:
        print(f'  WARNING: {ref} not found, skipping')
        return
    fp = fps[ref]
    old_pos = fp.GetPosition()
    ox, oy = pcbnew.ToMM(old_pos.x), pcbnew.ToMM(old_pos.y)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    fp.SetOrientationDegrees(rot)
    print(f'  {ref}: ({ox:.2f},{oy:.2f}) rot={fp.GetOrientationDegrees():.0f} -> ({x},{y}) rot={rot:.0f}')


def remove_all_tracks(board):
    tracks = list(board.GetTracks())
    for t in tracks:
        board.Remove(t)
    print(f'  Removed {len(tracks)} existing track segment(s)')


def main():
    print(f'Loading: {PCB}')
    board = pcbnew.LoadBoard(PCB)
    board.BuildConnectivity()

    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

    print('\n=== 1. Move components to aligned grid ===')
    for ref, (x, y, rot) in MOVES.items():
        move(fps, ref, x, y, rot)

    print('\n=== 2. Remove existing copper tracks (all are/will be dangling) ===')
    remove_all_tracks(board)
    print('  Note: DS18B20_DATA and PROBE_LED_A routing left to KiCad GUI (ROUTING_PENDING)')

    print('\nSaving...')
    board.BuildConnectivity()
    board.Save(PCB)
    print(f'Saved: {PCB}')
    print('Done.')


if __name__ == '__main__':
    main()
