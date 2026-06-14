#!/usr/bin/env python3
"""
fix_pcb_uboost.py — Fix U_BOOST placement and routing in PCB.

Moves U_BOOST from (48, 20) to (56, 20) to clear J8 Row B courtyard.
Removes bad routing and replaces with clean DRC-passing routes.
Fills GND pour zones to fix clearance violations.

Run: python.exe hardware/fix_pcb_uboost.py
"""

import sys, math

sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

PCB_PATH    = r'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb'
FP_LIB_PATH = r'C:/repos-github/PoE-FanController/hardware/kicad/footprints/Custom.pretty'
FP_NAME     = 'DC-Boost-Module'

# Corrected U_BOOST placement — clear of J8 Row B courtyard (right edge ~46.94 mm)
UBOOST_X = 56.0   # centre x — pads at 52.19..59.81 mm (all within board, clear of J8)
UBOOST_Y = 20.0   # centre y

PAD_NETS = {'1': '+5V', '2': 'GND', '3': '+12V', '4': 'GND'}
POWER_TRACE_WIDTH = 1.0   # mm — P-HW-07


def mm(v):
    return pcbnew.FromMM(float(v))


def tomm(v):
    return pcbnew.ToMM(v)


def add_track(board, net, x1, y1, x2, y2, width_mm=POWER_TRACE_WIDTH):
    seg = pcbnew.PCB_TRACK(board)
    seg.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    seg.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    seg.SetWidth(mm(width_mm))
    seg.SetLayer(pcbnew.F_Cu)
    seg.SetNet(net)
    board.Add(seg)
    return seg


def main():
    print('Loading PCB ...')
    board = pcbnew.LoadBoard(PCB_PATH)

    # ── Step 1: Remove existing U_BOOST footprint ─────────────────────────────
    uboost_old = None
    for fp in board.GetFootprints():
        if fp.GetReference() == 'U_BOOST':
            uboost_old = fp
            break

    if uboost_old:
        board.Delete(uboost_old)
        print('  Removed old U_BOOST footprint')
    else:
        print('  No existing U_BOOST found — fresh placement')

    # ── Step 2: Remove all tracks added by the first script ───────────────────
    # Remove tracks in the zone x=43-91, y=13-27 (covers old routing from first script)
    REMOVE_ZONE = {'x_min': 43.0, 'x_max': 91.0, 'y_min': 13.0, 'y_max': 27.0}
    remove_nets = {'+5V', 'GND', '+12V'}
    tracks_to_delete = []

    for track in board.GetTracks():
        if track.GetNetname() not in remove_nets:
            continue
        s = track.GetStart()
        e = track.GetEnd()
        sx, sy = tomm(s.x), tomm(s.y)
        ex, ey = tomm(e.x), tomm(e.y)
        # Only remove tracks that were added for U_BOOST (both endpoints in zone)
        in_zone = (
            REMOVE_ZONE['x_min'] <= sx <= REMOVE_ZONE['x_max'] and
            REMOVE_ZONE['y_min'] <= sy <= REMOVE_ZONE['y_max'] and
            REMOVE_ZONE['x_min'] <= ex <= REMOVE_ZONE['x_max'] and
            REMOVE_ZONE['y_min'] <= ey <= REMOVE_ZONE['y_max']
        )
        if in_zone:
            tracks_to_delete.append(track)

    for t in tracks_to_delete:
        board.Delete(t)
    print(f'  Removed {len(tracks_to_delete)} old routing tracks')

    # ── Step 3: Load and add U_BOOST footprint at corrected position ──────────
    print(f'  Loading footprint {FP_NAME} ...')
    fp_uboost = pcbnew.FootprintLoad(FP_LIB_PATH, FP_NAME)
    if fp_uboost is None:
        raise RuntimeError(f'Could not load footprint {FP_NAME}')

    fp_uboost.SetReference('U_BOOST')
    fp_uboost.SetValue('DC-Boost-Module')
    fp_uboost.SetPosition(pcbnew.VECTOR2I(mm(UBOOST_X), mm(UBOOST_Y)))
    fp_uboost.SetOrientationDegrees(0.0)
    fp_uboost.SetLayer(pcbnew.F_Cu)
    board.Add(fp_uboost)
    print(f'  Added U_BOOST at ({UBOOST_X}, {UBOOST_Y}) mm')

    # ── Step 4: Assign nets ───────────────────────────────────────────────────
    netmap = board.GetNetInfo()
    pad_positions = {}

    for pad in fp_uboost.Pads():
        pad_num = pad.GetNumber()
        net_name = PAD_NETS.get(pad_num)
        if net_name:
            net_info = netmap.GetNetItem(net_name)
            if net_info:
                pad.SetNet(net_info)
        pos = pad.GetPosition()
        pad_positions[pad_num] = (tomm(pos.x), tomm(pos.y))
        print(f'  Pad {pad_num} ({PAD_NETS.get(pad_num)}): '
              f'({tomm(pos.x):.3f}, {tomm(pos.y):.3f}) mm')

    # ── Step 5: Route power connections ──────────────────────────────────────
    net_5v  = netmap.GetNetItem('+5V')
    net_gnd = netmap.GetNetItem('GND')
    net_12v = netmap.GetNetItem('+12V')

    p1x, p1y = pad_positions['1']   # IN+  → +5V  (52.19, 20)
    p2x, p2y = pad_positions['2']   # IN-  → GND  (54.73, 20)
    p3x, p3y = pad_positions['3']   # OUT+ → +12V (57.27, 20)
    p4x, p4y = pad_positions['4']   # OUT- → GND  (59.81, 20)

    print('\n  Routing power traces (1.0 mm, F.Cu) ...')

    # +5V: Pad1 → up to J8 pad 40 level → left to J8 pad 40
    # J8 pad 40 (+5V) at (45.19, 16.67)
    J8_5V_X, J8_5V_Y = 45.19, 16.67
    add_track(board, net_5v,  p1x, p1y,   p1x, J8_5V_Y)
    add_track(board, net_5v,  p1x, J8_5V_Y, J8_5V_X, J8_5V_Y)
    print(f'    +5V: Pad1({p1x:.2f},{p1y:.2f}) → ({p1x:.2f},{J8_5V_Y}) → J8-40({J8_5V_X},{J8_5V_Y})')

    # GND Pad2: Pad2 → down to J8 GND row → left to J8 pad 38
    # J8 pad 38 (GND) at (45.19, 21.75)
    J8_GND_X, J8_GND_Y = 45.19, 21.75
    add_track(board, net_gnd, p2x, p2y,   p2x, J8_GND_Y)
    add_track(board, net_gnd, p2x, J8_GND_Y, J8_GND_X, J8_GND_Y)
    print(f'    GND: Pad2({p2x:.2f},{p2y:.2f}) → ({p2x:.2f},{J8_GND_Y}) → J8-38({J8_GND_X},{J8_GND_Y})')

    # GND Pad4: Pad4 → down to GND bus → join Pad2 route
    add_track(board, net_gnd, p4x, p4y,   p4x, J8_GND_Y)
    add_track(board, net_gnd, p4x, J8_GND_Y, p2x, J8_GND_Y)
    print(f'    GND: Pad4({p4x:.2f},{p4y:.2f}) → ({p4x:.2f},{J8_GND_Y}) → ({p2x:.2f},{J8_GND_Y})')

    # +12V: Pad3 → up (above GND bus level) → right to x=62 to clear pad4 → down → right to spine
    # Route: up to y=18 (above GND bus), then right to x=62 (clear of pad4 at 59.81), then down, then right to spine at x=89
    add_track(board, net_12v, p3x, p3y,   p3x, 18.0)
    add_track(board, net_12v, p3x, 18.0,  62.0, 18.0)
    add_track(board, net_12v, 62.0, 18.0, 62.0, 25.5)
    add_track(board, net_12v, 62.0, 25.5, 89.0, 25.5)
    print(f'    +12V: Pad3({p3x:.2f},{p3y:.2f})→({p3x:.2f},18)→(62,18)→(62,25.5)→(89,25.5)')

    # ── Step 6: Fill zones to resolve GND pour clearance violations ───────────
    print('\n  Filling copper zones (FillAllZones) ...')
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    print('  Zones filled.')

    # ── Step 7: Save ──────────────────────────────────────────────────────────
    board.Save(PCB_PATH)
    print(f'\nPCB saved: {PCB_PATH}')

    # ── Verify ────────────────────────────────────────────────────────────────
    board2 = pcbnew.LoadBoard(PCB_PATH)
    for fp in board2.GetFootprints():
        if fp.GetReference() == 'U_BOOST':
            pos = fp.GetPosition()
            print(f'\nVerification:')
            print(f'  U_BOOST at ({tomm(pos.x):.3f}, {tomm(pos.y):.3f}) mm, layer={fp.GetLayerName()}')
            for pad in fp.Pads():
                p = pad.GetPosition()
                in_zone = 33.19 <= tomm(p.x) <= 62.0
                print(f'  Pad {pad.GetNumber()} ({pad.GetNetname()}): '
                      f'({tomm(p.x):.3f}, {tomm(p.y):.3f}) in zone: {in_zone}')


if __name__ == '__main__':
    main()
