#!/usr/bin/env python3
"""
hardware/fix_pcb_alignment_v2.py — Fix critical conflicts from alignment script.

The alignment script put R5-R8 at x=25, which collides with existing power-circuit
components (R3, R4, C1) and status LEDs (LED1, LED2) in that column.
It also put R14 at (25,58), directly on top of LED1.

Fixes:
  R5-R8: restore to original Y-staggered positions at x=35 (generator-validated safe)
  R14:   move from (25,58) to (35,55) — clear of LED1/LED2 at y=58, clear of R7 at y=48
  R10:   shift from (36,22) to (37,26) — avoid C2 at (40,18) whose courtyard bottom is ~y=21.5

All other components (D2-D5, LED6, J6, R9, R11, R12, R15, J2-J5) stay as placed by
fix_pcb_alignment.py.

Usage:
    C:\\Users\\Niels\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe hardware/fix_pcb_alignment_v2.py
"""

import sys
sys.path.insert(0, r'C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin')
import pcbnew

PCB = r'C:\repos-github\PoE-FanController\hardware\kicad\PoE-FanController.kicad_pcb'

MOVES = {
    # TACH pull-up resistors — restore to original Y-staggered positions (x=35, verified safe)
    'R5':  (35.0, 12.0, 0.0),
    'R6':  (35.0, 30.0, 0.0),
    'R7':  (35.0, 48.0, 0.0),
    'R8':  (35.0, 66.0, 0.0),

    # DS18B20 data pull-up — clear of LED1 at (25,58) and LED2 at (31,58)
    # At (35,55): courtyard X=33.5-44.1, Y=53.5-56.5 — clear of LED2 right edge (~33.5) and R15 top (56.5)
    'R14': (35.0, 55.0, 0.0),

    # LED resistor for D3/FAN2 — shift right/down to avoid C2 at (40,18) courtyard bottom ~y=21.5
    # At (37,26): courtyard X=35.5-46.1, Y=24.5-27.5 — 3mm clear of C2 bottom
    'R10': (37.0, 26.0, 0.0),
}


def main():
    print(f'Loading: {PCB}')
    board = pcbnew.LoadBoard(PCB)
    board.BuildConnectivity()

    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

    print('\n=== Fix critical placement conflicts ===')
    for ref, (x, y, rot) in MOVES.items():
        if ref not in fps:
            print(f'  WARNING: {ref} not found')
            continue
        fp = fps[ref]
        old = fp.GetPosition()
        ox, oy = pcbnew.ToMM(old.x), pcbnew.ToMM(old.y)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        fp.SetOrientationDegrees(rot)
        print(f'  {ref}: ({ox:.2f},{oy:.2f}) -> ({x},{y})')

    print('\nSaving...')
    board.BuildConnectivity()
    board.Save(PCB)
    print(f'Saved: {PCB}')
    print('Done.')


if __name__ == '__main__':
    main()
