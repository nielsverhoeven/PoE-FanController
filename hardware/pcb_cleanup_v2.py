#!/usr/bin/env python3
"""
hardware/pcb_cleanup_v2.py — PCB cleanup for Issue #75 daughter board redesign.

Removes old PoE power chain footprints (U1, U2, D1, L1, C1-C7, R1, R2, J7, REF**)
from the PCB, repositions fan headers J2-J5 to the right side edge of the board,
and resizes the board outline to match the Waveshare ESP32-P4-POE-ETH (SKU 32088)
board dimensions (~100 mm wide × 85.6 mm tall).

Kept footprints: J2, J3, J4, J5, J8, R3, R4, R5, R6, R7, R8, LED1, NTC1

Usage (KiCad Python interpreter):
    C:\\Users\\Niels\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe hardware/pcb_cleanup_v2.py

NOTE: After running this script, open PoE-FanController.kicad_pcb in KiCad GUI and:
  1. Run "Update PCB from Schematic" to add U_BOOST footprint
  2. Place U_BOOST manually
  3. Route all nets
  4. Run DRC to verify zero violations
"""

import sys
sys.path.insert(0, r'C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin')
import pcbnew

PCB_PATH = r'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb'

# -------------------------------------------------------------------------
# Footprints to REMOVE (old PoE power chain — no longer on daughter board)
# -------------------------------------------------------------------------
REFS_TO_REMOVE = {
    'U1',                             # Ag9905M PoE+ PD module
    'U2',                             # LM2596S-5.0 buck regulator (12V→5V)
    'D1',                             # 1N5822 freewheeling Schottky (LM2596)
    'L1',                             # 68uH buck inductor
    'C1', 'C2',                       # LM2596 input/output bulk caps
    'C3', 'C4', 'C5', 'C6', 'C7',   # decoupling caps from old power chain
    'R1', 'R2',                       # orphaned resistors from old design
    'J7',                              # orphaned connector from old design
    'REF**',                          # fabrication reference placeholder
}

# Footprints to KEEP (daughter board components)
REFS_TO_KEEP = {
    'J2', 'J3', 'J4', 'J5',          # 4-pin fan headers (12V PWM)
    'J8',                              # 2×20 female interface header (Waveshare)
    'R3', 'R4',                       # status LED resistor + NTC divider resistor
    'R5', 'R6', 'R7', 'R8',          # TACH pull-up resistors
    'LED1',                            # status LED
    'NTC1',                            # NTC thermistor
}

# -------------------------------------------------------------------------
# Board geometry (all in mm)
# -------------------------------------------------------------------------
BOARD_ORIGIN_X = 5.0     # board left edge X (keep same as existing)
BOARD_ORIGIN_Y = 5.0     # board top edge Y (keep same as existing)
BOARD_W        = 100.0   # board width  (X): wide enough for side-edge fan headers
BOARD_H        = 85.6    # board height (Y): matches Waveshare SKU 32088 board length

# Fan header placement: on the right side of the board
# J2-J5 are placed in a column near the right edge, spaced 18mm apart vertically
FAN_X         = BOARD_ORIGIN_X + BOARD_W - 8.0   # fan header centre X (8mm from right edge)
FAN_Y_START   = BOARD_ORIGIN_Y + 12.0            # first fan header centre Y
FAN_Y_SPACING = 18.0                              # spacing between fan header centres

# -------------------------------------------------------------------------
# Load board
# -------------------------------------------------------------------------
print(f'Loading: {PCB_PATH}')
board = pcbnew.LoadBoard(PCB_PATH)

bb = board.GetBoardEdgesBoundingBox()
print(f'Current board: x={pcbnew.ToMM(bb.GetX()):.1f} y={pcbnew.ToMM(bb.GetY()):.1f} '
      f'w={pcbnew.ToMM(bb.GetWidth()):.1f} h={pcbnew.ToMM(bb.GetHeight()):.1f} mm')

# -------------------------------------------------------------------------
# Step 1: Remove old power chain footprints
# -------------------------------------------------------------------------
print('\nStep 1: Removing old power chain footprints...')
all_fps = list(board.GetFootprints())
removed = []
kept = []
unexpected = []

for fp in all_fps:
    ref = fp.GetReference()
    if ref in REFS_TO_REMOVE:
        board.Remove(fp)
        removed.append(ref)
        print(f'  Removed: {ref} ({fp.GetValue()})')
    elif ref in REFS_TO_KEEP:
        kept.append(ref)
    else:
        unexpected.append(ref)
        print(f'  WARNING: unexpected ref "{ref}" — leaving in place')

print(f'  Removed {len(removed)} footprints: {sorted(removed)}')
print(f'  Kept    {len(kept)} footprints:    {sorted(kept)}')

# -------------------------------------------------------------------------
# Step 2: Move fan headers J2-J5 to right side edge
# -------------------------------------------------------------------------
print('\nStep 2: Moving fan headers J2-J5 to right side edge...')
fan_refs = ['J2', 'J3', 'J4', 'J5']
fp_map = {fp.GetReference(): fp for fp in board.GetFootprints()}

for i, ref in enumerate(fan_refs):
    if ref in fp_map:
        fp = fp_map[ref]
        new_x_mm = FAN_X
        new_y_mm = FAN_Y_START + i * FAN_Y_SPACING
        fp.SetX(pcbnew.FromMM(new_x_mm))
        fp.SetY(pcbnew.FromMM(new_y_mm))
        fp.SetOrientationDegrees(0)
        print(f'  {ref}: moved to ({new_x_mm:.1f}, {new_y_mm:.1f}) mm')
    else:
        print(f'  WARNING: {ref} not found in PCB')

# -------------------------------------------------------------------------
# Step 3: Resize board outline to 100 × 85.6 mm
# -------------------------------------------------------------------------
print('\nStep 3: Resizing board outline...')
edge_layer = pcbnew.Edge_Cuts

# Remove existing Edge.Cuts drawings
removed_edges = 0
for d in list(board.GetDrawings()):
    if d.GetLayer() == edge_layer:
        board.Remove(d)
        removed_edges += 1
print(f'  Removed {removed_edges} existing Edge.Cuts segments')

# Draw new rectangular outline
corners = [
    (BOARD_ORIGIN_X,            BOARD_ORIGIN_Y),
    (BOARD_ORIGIN_X + BOARD_W,  BOARD_ORIGIN_Y),
    (BOARD_ORIGIN_X + BOARD_W,  BOARD_ORIGIN_Y + BOARD_H),
    (BOARD_ORIGIN_X,            BOARD_ORIGIN_Y + BOARD_H),
]
for j in range(4):
    x1, y1 = corners[j]
    x2, y2 = corners[(j + 1) % 4]
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetLayer(edge_layer)
    seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    seg.SetWidth(pcbnew.FromMM(0.05))
    board.Add(seg)
print(f'  New board outline: {BOARD_W} × {BOARD_H} mm '
      f'at origin ({BOARD_ORIGIN_X}, {BOARD_ORIGIN_Y}) mm')

# -------------------------------------------------------------------------
# Step 4: Save
# -------------------------------------------------------------------------
print('\nStep 4: Building connectivity and saving...')
board.BuildConnectivity()
pcbnew.Refresh()
board.Save(board.GetFileName())
print(f'  Saved: {PCB_PATH}')

bb2 = board.GetBoardEdgesBoundingBox()
print(f'\nNew board: x={pcbnew.ToMM(bb2.GetX()):.1f} y={pcbnew.ToMM(bb2.GetY()):.1f} '
      f'w={pcbnew.ToMM(bb2.GetWidth()):.1f} h={pcbnew.ToMM(bb2.GetHeight()):.1f} mm')
print('\nDone.')
print('\nNEXT STEPS:')
print('  1. Open PoE-FanController.kicad_pcb in KiCad GUI')
print('  2. Tools → Update PCB from Schematic → to add U_BOOST footprint')
print('  3. Place U_BOOST between J8 and the fan headers')
print('  4. Route all nets (+5V, +12V, GND, PWM[1-4], TACH[1-4], TEMP, STATUS_LED)')
print('  5. Run DRC and verify zero violations')
