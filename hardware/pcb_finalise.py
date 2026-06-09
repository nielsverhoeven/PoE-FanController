#!/usr/bin/env python3
"""
hardware/pcb_finalise.py — Route missing traces, clean silkscreen, fill zones.

Steps:
  1. Route DS18B20_DATA: R14 pad2 (43.62,55) ---> J6 pad2 (60.54,58)
     Route: (43.62,55) -> (60.54,55) -> (60.54,58)  [L-shape below row 5]
  2. Route /PROBE_LED_A: R15 pad2 (43.62,58) -> LED6 pad1 (48.00,58)
     Route: straight horizontal at y=58
  3. Silkscreen cleanup:
     - Hide VALUE text for all small passives and indicator LEDs
     - Reposition REFERENCE text for row-area components to avoid silk_overlap
  4. Fill zones (GND + +3V3 copper pours)

Usage:
    C:\\Users\\Niels\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe hardware/pcb_finalise.py
"""

import sys
sys.path.insert(0, r'C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin')
import pcbnew

PCB = r'C:\repos-github\PoE-FanController\hardware\kicad\PoE-FanController.kicad_pcb'
TRACE_W = pcbnew.FromMM(0.25)


# ─── helper ────────────────────────────────────────────────────────────────────

def add_track(board, net_name, x1, y1, x2, y2, layer=pcbnew.F_Cu):
    net = board.FindNet(net_name)
    if net is None:
        print(f'  WARNING: net {net_name} not found')
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetLayer(layer)
    t.SetNet(net)
    t.SetWidth(TRACE_W)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    board.Add(t)
    print(f'  [{net_name}] ({x1},{y1}) -> ({x2},{y2})')


def mm(v):
    return pcbnew.ToMM(v)


# ─── silkscreen layout ─────────────────────────────────────────────────────────

# Components whose VALUE text should be hidden (small passives, indicators)
HIDE_VALUE = {
    'D2','D3','D4','D5','LED6',
    'R5','R6','R7','R8','R9','R10','R11','R12','R13','R14','R15',
    'C1','C2','L1',
}

# Absolute reference text positions (x, y, angle_deg)
# Places refs so they don't pile on top of each other.
# Fan connectors: ref 3.5mm above anchor
# Status LEDs: ref 3.5mm above anchor
# LED resistors: ref 3mm below anchor
# TACH resistors: ref 2mm below anchor (they sit between rows)
REF_POSITIONS = {
    # Row 1  y=10
    'J2':  (58.0,  6.5, 0),
    'D2':  (48.0,  6.5, 0),
    'R9':  (36.0, 13.5, 0),
    'R5':  (35.0, 17.5, 0),
    # Row 2  y=22
    'J3':  (58.0, 18.5, 0),
    'D3':  (48.0, 18.5, 0),
    'R10': (37.0, 29.5, 0),   # offset y=26 -> 29.5
    'R6':  (35.0, 27.5, 0),
    # Row 3  y=34
    'J4':  (58.0, 30.5, 0),
    'D4':  (48.0, 30.5, 0),
    'R11': (36.0, 37.5, 0),
    'R7':  (35.0, 46.5, 0),
    # Row 4  y=46
    'J5':  (58.0, 42.5, 0),
    'D5':  (48.0, 42.5, 0),
    'R12': (36.0, 49.5, 0),
    'R8':  (35.0, 63.5, 0),
    # Row 5  y=58
    'J6':  (58.0, 54.5, 0),
    'LED6':(48.0, 54.5, 0),
    'R15': (36.0, 61.5, 0),
    'R14': (36.0, 58.5, 0),   # at (36,55); ref 3.5 below
}

TEXT_SIZE = pcbnew.FromMM(0.8)
TEXT_THICK = pcbnew.FromMM(0.12)


def apply_silk(fps):
    # Hide value text for noise-heavy components
    for ref, fp in fps.items():
        if ref in HIDE_VALUE:
            fp.Value().SetVisible(False)

    # Reposition reference text for row-area components
    for ref, (rx, ry, angle) in REF_POSITIONS.items():
        if ref not in fps:
            continue
        fp = fps[ref]
        t = fp.Reference()
        t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(rx), pcbnew.FromMM(ry)))
        t.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
        t.SetTextSize(pcbnew.VECTOR2I(TEXT_SIZE, TEXT_SIZE))
        t.SetTextThickness(TEXT_THICK)
        t.SetVisible(True)


# ─── main ──────────────────────────────────────────────────────────────────────

def main():
    print(f'Loading: {PCB}')
    board = pcbnew.LoadBoard(PCB)
    board.BuildConnectivity()

    # Step 1 — Route DS18B20_DATA
    print('\n=== 1. Route DS18B20_DATA ===')
    add_track(board, 'DS18B20_DATA', 43.62, 55.0, 60.54, 55.0)   # horizontal
    add_track(board, 'DS18B20_DATA', 60.54, 55.0, 60.54, 58.0)   # vertical to J6 pad2

    # Step 2 — Route /PROBE_LED_A
    print('\n=== 2. Route /PROBE_LED_A ===')
    add_track(board, '/PROBE_LED_A', 43.62, 58.0, 48.0, 58.0)    # horizontal to LED6 pad1

    # Step 3 — Silkscreen cleanup
    print('\n=== 3. Silkscreen cleanup ===')
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    apply_silk(fps)
    print(f'  Value text hidden for: {sorted(HIDE_VALUE)}')
    print(f'  Reference text repositioned for {len(REF_POSITIONS)} components')

    # Step 4 — Zone fill
    print('\n=== 4. Zone fill ===')
    zones = list(board.Zones())
    print(f'  Found {len(zones)} zone(s): {[z.GetNetname() for z in zones]}')
    board.BuildConnectivity()
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    print('  Zones filled.')

    print('\nSaving...')
    board.Save(PCB)
    print(f'Saved: {PCB}')
    print('Done.')


if __name__ == '__main__':
    main()
