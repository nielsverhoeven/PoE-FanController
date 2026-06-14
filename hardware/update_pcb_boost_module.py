#!/usr/bin/env python3
"""
update_pcb_boost_module.py — T006 PCB Update: Replace discrete boost stage with U_BOOST module.

Executed with KiCad's Python (pcbnew) to:
  1. Delete footprints: U1, L1, D1, C1, C2 and their associated traces
  2. Delete BOOST_SW net tracks (net no longer exists)
  3. Add Custom:DC-Boost-Module as U_BOOST at PCB position (48, 20) mm
  4. Assign nets: Pad1=+5V, Pad2=GND, Pad3=+12V, Pad4=GND
  5. Route 4 power traces (width=1.0mm, F.Cu) from U_BOOST pads to power buses
  6. Save PCB

Run: python.exe hardware/update_pcb_boost_module.py
"""

import sys, math

sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

PCB_PATH    = r'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb'
FP_LIB_PATH = r'C:/repos-github/PoE-FanController/hardware/kicad/footprints/Custom.pretty'
FP_NAME     = 'DC-Boost-Module'

# U_BOOST placement (centre of the 4-pin header) — in x=33.19..56mm zone (NFR-05)
UBOOST_X = 48.0   # mm — centre x of the 4-pin header
UBOOST_Y = 20.0   # mm — centre y

# Pad offsets from centre (2.54mm pitch, single-row)
PAD_OFFSETS = {
    '1': (-3.81, 0.0),   # IN+  → +5V
    '2': (-1.27, 0.0),   # IN-  → GND
    '3': ( 1.27, 0.0),   # OUT+ → +12V
    '4': ( 3.81, 0.0),   # OUT- → GND
}
PAD_NETS = {'1': '+5V', '2': 'GND', '3': '+12V', '4': 'GND'}

POWER_TRACE_WIDTH = 1.0   # mm — P-HW-07

# Zone to clear: old boost components were in this box
ZONE_X_MIN = 50.0   # mm
ZONE_Y_MAX = 27.0   # mm (keep board top margin)

TOLERANCE  = 0.6    # mm — pad endpoint matching tolerance


def mm(v):
    return pcbnew.FromMM(float(v))


def tomm(v):
    return pcbnew.ToMM(v)


def near(a, b, tol=TOLERANCE):
    return math.hypot(tomm(a.x) - tomm(b.x), tomm(a.y) - tomm(b.y)) < tol


def add_track(board, net, x1, y1, x2, y2, width_mm=POWER_TRACE_WIDTH):
    """Add a straight PCB track segment on F.Cu."""
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

    # ── Step 1: Identify deleted component pads ──────────────────────────────
    REMOVE_REFS = {'U1', 'L1', 'D1', 'C1', 'C2'}
    deleted_pad_positions = []   # list of VECTOR2I
    footprints_to_delete  = []

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in REMOVE_REFS:
            for pad in fp.Pads():
                deleted_pad_positions.append(pad.GetPosition())
            footprints_to_delete.append(fp)

    print(f'  Found {len(footprints_to_delete)} footprints to remove: '
          f'{[f.GetReference() for f in footprints_to_delete]}')

    # ── Step 2: Delete associated tracks ─────────────────────────────────────
    tracks_to_delete = []
    for track in board.GetTracks():
        s = track.GetStart()
        e = track.GetEnd()

        # Rule A: BOOST_SW net — all tracks
        if track.GetNetname() == 'BOOST_SW':
            tracks_to_delete.append(track)
            continue

        # Rule B: both endpoints in old-boost zone (x>50mm, y<27mm)
        in_zone = (
            tomm(s.x) > ZONE_X_MIN and tomm(s.y) < ZONE_Y_MAX and
            tomm(e.x) > ZONE_X_MIN and tomm(e.y) < ZONE_Y_MAX
        )
        if in_zone:
            tracks_to_delete.append(track)
            continue

        # Rule C: at least one endpoint within tolerance of a deleted pad
        for pad_pos in deleted_pad_positions:
            if near(s, pad_pos) or near(e, pad_pos):
                tracks_to_delete.append(track)
                break

    # De-duplicate
    seen = set()
    unique_delete = []
    for t in tracks_to_delete:
        if id(t) not in seen:
            seen.add(id(t))
            unique_delete.append(t)

    print(f'  Deleting {len(unique_delete)} track segments')
    for t in unique_delete:
        board.Delete(t)

    # ── Step 3: Delete footprints ─────────────────────────────────────────────
    for fp in footprints_to_delete:
        board.Delete(fp)
    print('  Deleted footprints: U1, L1, D1, C1, C2')

    # ── Step 4: Load and add U_BOOST footprint ────────────────────────────────
    print(f'  Loading footprint Custom:{FP_NAME} ...')
    fp_uboost = pcbnew.FootprintLoad(FP_LIB_PATH, FP_NAME)
    if fp_uboost is None:
        raise RuntimeError(f'Could not load footprint {FP_NAME} from {FP_LIB_PATH}')

    fp_uboost.SetReference('U_BOOST')
    fp_uboost.SetValue('DC-Boost-Module')
    fp_uboost.SetPosition(pcbnew.VECTOR2I(mm(UBOOST_X), mm(UBOOST_Y)))
    fp_uboost.SetOrientationDegrees(0.0)
    fp_uboost.SetLayer(pcbnew.F_Cu)

    board.Add(fp_uboost)
    print(f'  Added U_BOOST at ({UBOOST_X}, {UBOOST_Y}) mm')

    # ── Step 5: Assign nets to pads ──────────────────────────────────────────
    netmap = board.GetNetInfo()
    pad_positions = {}

    for pad in fp_uboost.Pads():
        pad_num = pad.GetNumber()
        net_name = PAD_NETS.get(pad_num)
        if net_name:
            net_info = netmap.GetNetItem(net_name)
            if net_info:
                pad.SetNet(net_info)
                print(f'  U_BOOST pad {pad_num} → {net_name}')
            else:
                print(f'  WARNING: net {net_name} not found in board')
        # Record actual pad position (after placement)
        pos = pad.GetPosition()
        pad_positions[pad_num] = (tomm(pos.x), tomm(pos.y))
        print(f'    Pad {pad_num} at ({tomm(pos.x):.3f}, {tomm(pos.y):.3f}) mm')

    # ── Step 6: Route power connections (F.Cu, 1.0mm width) ──────────────────
    netmap = board.GetNetInfo()
    net_5v  = netmap.GetNetItem('+5V')
    net_gnd = netmap.GetNetItem('GND')
    net_12v = netmap.GetNetItem('+12V')

    p1x, p1y = pad_positions['1']   # IN+  → +5V
    p2x, p2y = pad_positions['2']   # IN-  → GND
    p3x, p3y = pad_positions['3']   # OUT+ → +12V
    p4x, p4y = pad_positions['4']   # OUT- → GND

    print('\n  Routing power traces (1.0 mm, F.Cu) ...')

    # J8 pad 40 (+5V) at (45.19, 16.67)
    # Route: Pad1 → (p1x, 16.67) → (45.19, 16.67)
    J8_5V_X, J8_5V_Y = 45.19, 16.67
    add_track(board, net_5v,  p1x, p1y, p1x, J8_5V_Y)
    add_track(board, net_5v,  p1x, J8_5V_Y, J8_5V_X, J8_5V_Y)
    print(f'    +5V: Pad1({p1x:.2f},{p1y:.2f}) → ({p1x:.2f},{J8_5V_Y:.2f}) → J8-40({J8_5V_X},{J8_5V_Y})')

    # J8 pad 38 (GND) at (45.19, 21.75)
    # Route Pad2 GND: Pad2 → (p2x, 21.75) → (45.19, 21.75)
    J8_GND_X, J8_GND_Y = 45.19, 21.75
    add_track(board, net_gnd, p2x, p2y, p2x, J8_GND_Y)
    add_track(board, net_gnd, p2x, J8_GND_Y, J8_GND_X, J8_GND_Y)
    print(f'    GND: Pad2({p2x:.2f},{p2y:.2f}) → ({p2x:.2f},{J8_GND_Y:.2f}) → J8-38({J8_GND_X},{J8_GND_Y})')

    # Route Pad4 GND: Pad4 → (p4x, 21.75) → (p2x, 21.75) [join Pad2 GND route]
    add_track(board, net_gnd, p4x, p4y, p4x, J8_GND_Y)
    add_track(board, net_gnd, p4x, J8_GND_Y, p2x, J8_GND_Y)
    print(f'    GND: Pad4({p4x:.2f},{p4y:.2f}) → ({p4x:.2f},{J8_GND_Y:.2f}) → ({p2x:.2f},{J8_GND_Y:.2f})')

    # +12V spine at x=89.0 starts at (89.00, 25.50) → fan headers
    # Route Pad3 +12V: Pad3 → (p3x, 25.50) → (89.00, 25.50)
    SPINE_X, SPINE_Y = 89.0, 25.5
    add_track(board, net_12v, p3x, p3y, p3x, SPINE_Y)
    add_track(board, net_12v, p3x, SPINE_Y, SPINE_X, SPINE_Y)
    print(f'    +12V: Pad3({p3x:.2f},{p3y:.2f}) → ({p3x:.2f},{SPINE_Y:.2f}) → spine({SPINE_X},{SPINE_Y})')

    # ── Step 7: Save ──────────────────────────────────────────────────────────
    board.Save(PCB_PATH)
    print(f'\nPCB saved to {PCB_PATH}')
    print('Done. U_BOOST footprint placed and routed.')

    # ── Verify ────────────────────────────────────────────────────────────────
    board2 = pcbnew.LoadBoard(PCB_PATH)
    found_uboost = any(fp.GetReference() == 'U_BOOST' for fp in board2.GetFootprints())
    found_old    = any(fp.GetReference() in REMOVE_REFS for fp in board2.GetFootprints())
    print(f'\nVerification:')
    print(f'  U_BOOST present: {found_uboost}')
    print(f'  Old boost refs present: {found_old}')


if __name__ == '__main__':
    main()
