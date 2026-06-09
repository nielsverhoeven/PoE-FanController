#!/usr/bin/env python3
"""
hardware/add_ds18b20_pcb.py — Add DS18B20 temperature probe components to PCB.

Adds four new footprints (J6, R14, R15, LED6) for the DS18B20 probe feature (Issue #97).
Also reassigns nets for J8 pins 27 (DS18B20_DATA) and 28 (PROBE_LED).

Routes:
  - PROBE_LED_A: R15 pin2 → LED6 pin1 (2.38 mm horizontal, clear path)
  - DS18B20_DATA local: R14 pin2 → above J6 body → J6 pin2 (U-shape, clear)

Remaining signal/power routing (J8→R14, J8→R15, +3V3, GND) deferred to KiCad GUI.

Usage:
    C:\\Users\\Niels\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe hardware/add_ds18b20_pcb.py
"""

import sys
sys.path.insert(0, r'C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin')
import pcbnew

PCB = r'C:\repos-github\PoE-FanController\hardware\kicad\PoE-FanController.kicad_pcb'
KICAD_FP = r'C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints'

# ---------------------------------------------------------------------------
# Component definitions: (lib, footprint, ref, value, cx_mm, cy_mm, rot_deg)
# ---------------------------------------------------------------------------
NEW_COMPONENTS = [
    # R15 — 330Ω PROBE_LED current-limit resistor
    # pin1=(25,75)=PROBE_LED, pin2=(32.62,75)=PROBE_LED_A
    ("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     "R15", "330R", 25.0, 75.0, 0.0),

    # LED6 — 3mm green THT LED (probe health indicator)
    # pin1=(35,75)=PROBE_LED_A, pin2=(37.54,75)=GND
    ("LED_THT", "LED_D3.0mm",
     "LED6", "LED_GREEN", 35.0, 75.0, 0.0),

    # R14 — 4.7kΩ DS18B20_DATA pull-up to +3V3
    # pin1=(25,82)=+3V3, pin2=(32.62,82)=DS18B20_DATA
    ("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     "R14", "4k7", 25.0, 82.0, 0.0),

    # J6 — Molex KK-254 3-pin DS18B20 probe connector
    # pin1=(40,82)=GND, pin2=(42.54,82)=DS18B20_DATA, pin3=(45.08,82)=+3V3
    ("Connector_Molex", "Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical",
     "J6", "Molex_KK254_3pin", 40.0, 82.0, 0.0),
]

# ---------------------------------------------------------------------------
# Net assignments for new component pads AND J8 pin updates
# key = (ref, pad_number_str), value = net_name
# ---------------------------------------------------------------------------
NET_ASSIGNMENTS = {
    # J8 pin reassignments (previously NC, now GPIO19/GPIO20)
    ('J8', '27'): 'DS18B20_DATA',    # GPIO19 — 1-Wire DATA
    ('J8', '28'): 'PROBE_LED',       # GPIO20 — probe health LED

    # R15 (330Ω PROBE_LED current limit)
    ('R15', '1'): 'PROBE_LED',
    ('R15', '2'): '/PROBE_LED_A',

    # LED6 (3mm green status LED)
    ('LED6', '1'): '/PROBE_LED_A',
    ('LED6', '2'): 'GND',

    # R14 (4.7kΩ DS18B20_DATA pull-up)
    ('R14', '1'): '+3V3',
    ('R14', '2'): 'DS18B20_DATA',

    # J6 (Molex KK-254 3-pin probe connector)
    ('J6', '1'): 'GND',
    ('J6', '2'): 'DS18B20_DATA',
    ('J6', '3'): '+3V3',
}

# ---------------------------------------------------------------------------
# Routing traces: list of (net, width_mm, [(x1,y1),(x2,y2),...]) polylines
# Each consecutive pair of points defines a PCB_TRACK segment.
# ---------------------------------------------------------------------------
TRACE_WIDTH = 0.25  # mm — signal class (P-HW-07)

ROUTES = [
    # PROBE_LED_A: R15 pin2 (32.62,75) → LED6 pin1 (35,75)
    # Short 2.38mm horizontal, clear of all other pads. ✓
    ('/PROBE_LED_A', TRACE_WIDTH, [
        (32.62, 75.0),
        (35.0,  75.0),
    ]),

    # DS18B20_DATA local: R14 pin2 (32.62,82) → above J6 body → J6 pin2 (42.54,82)
    # Route goes UP to y=79 (above connector body), across, then DOWN to J6 pin2.
    # At y=79: clear of R15/LED6 (at y=75) above and J6 pads (at y=82) below. ✓
    ('DS18B20_DATA', TRACE_WIDTH, [
        (32.62, 82.0),   # R14 pin2
        (32.62, 79.0),   # up
        (42.54, 79.0),   # right, above J6 body (J6 pin1 at x=40, pin2 at x=42.54)
        (42.54, 82.0),   # down to J6 pin2
    ]),
]


def load_board():
    print(f'Loading PCB: {PCB}')
    board = pcbnew.LoadBoard(PCB)
    board.BuildConnectivity()
    return board


def get_or_create_net(board, name):
    n = board.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        print(f'  Created net: {name}')
    return n


def add_footprints(board):
    print('\nAdding new footprints...')
    fp_map = {fp.GetReference(): fp for fp in board.GetFootprints()}

    for lib, fp_name, ref, value, cx, cy, rot in NEW_COMPONENTS:
        if ref in fp_map:
            print(f'  SKIP: {ref} already in PCB')
            continue

        fp_path = f'{KICAD_FP}\\{lib}.pretty'
        try:
            fp = pcbnew.FootprintLoad(fp_path, fp_name)
        except Exception as e:
            print(f'  ERROR loading {lib}:{fp_name}: {e}')
            continue

        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetLayer(pcbnew.F_Cu)
        fp.SetPosition(pcbnew.VECTOR2I(
            pcbnew.FromMM(cx),
            pcbnew.FromMM(cy)
        ))
        if rot != 0.0:
            fp.SetOrientationDegrees(rot)

        board.Add(fp)
        pos = fp.GetPosition()
        px, py = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
        print(f'  Added: {ref} ({value}) at ({px:.2f},{py:.2f}) rot={rot}°')

    # Rebuild footprint map after adding new ones
    return {fp.GetReference(): fp for fp in board.GetFootprints()}


def assign_nets(board, fp_map):
    print('\nAssigning nets to pads...')
    assigned = 0
    skipped  = 0

    for (ref, pad_num), net_name in NET_ASSIGNMENTS.items():
        if ref not in fp_map:
            print(f'  WARNING: {ref} not in PCB — skipping net {net_name}')
            skipped += 1
            continue

        fp = fp_map[ref]
        pad = None
        for p in fp.Pads():
            if p.GetNumber() == pad_num:
                pad = p
                break

        if pad is None:
            print(f'  WARNING: {ref} pad {pad_num} not found')
            skipped += 1
            continue

        net = get_or_create_net(board, net_name)
        old_net = pad.GetNetname()
        pad.SetNet(net)
        print(f'  {ref}[{pad_num}]: {old_net!r} → {net_name!r}')
        assigned += 1

    print(f'  Assigned: {assigned}, Skipped: {skipped}')


def add_routes(board):
    print('\nAdding routing traces...')
    for net_name, width, points in ROUTES:
        net = get_or_create_net(board, net_name)
        width_iu = pcbnew.FromMM(width)

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            track = pcbnew.PCB_TRACK(board)
            track.SetLayer(pcbnew.F_Cu)
            track.SetNet(net)
            track.SetWidth(width_iu)
            track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
            track.SetEnd  (pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
            board.Add(track)
            print(f'  Route [{net_name}] ({x1:.2f},{y1:.2f})→({x2:.2f},{y2:.2f})')

    print(f'  Total new tracks: {len([p for _,_,pts in ROUTES for p in pts]) - len(ROUTES)}')


def verify(board):
    print('\nVerification:')
    board.BuildConnectivity()
    unconn = board.GetConnectivity().GetUnconnectedCount(False)
    tracks = list(board.GetTracks())
    fps    = list(board.GetFootprints())
    print(f'  Footprints: {len(fps)}')
    print(f'  Tracks: {len(tracks)}')
    print(f'  Unconnected ratsnest: {unconn}')

    # Verify new component pads have correct nets
    fp_map = {fp.GetReference(): fp for fp in fps}
    print('\n  New component pads:')
    for ref in ('R14', 'R15', 'LED6', 'J6'):
        if ref in fp_map:
            for pad in sorted(fp_map[ref].Pads(), key=lambda p: p.GetNumber()):
                pos = pad.GetPosition()
                print(f'    {ref}[{pad.GetNumber()}] '
                      f'({pcbnew.ToMM(pos.x):.2f},{pcbnew.ToMM(pos.y):.2f}) '
                      f'net={pad.GetNetname()}')


def main():
    board   = load_board()
    fp_map  = add_footprints(board)
    assign_nets(board, fp_map)
    add_routes(board)

    print('\nSaving PCB...')
    board.BuildConnectivity()
    board.Save(PCB)
    print(f'Saved: {PCB}')

    verify(board)
    print('\nDone.')


if __name__ == '__main__':
    main()
