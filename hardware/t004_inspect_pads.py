"""
T004: Route all PCB traces on the corrected J8 right-column layout.

Queries current pad positions for routing reference.
"""
import sys
sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

PCB = r'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb'

board = pcbnew.LoadBoard(PCB)

# Collect all pads by (ref, padnum) -> (net, x_mm, y_mm)
pad_info = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        pos = pad.GetCenter()
        x_mm = pcbnew.ToMM(pos.x)
        y_mm = pcbnew.ToMM(pos.y)
        net = pad.GetNetname()
        pad_info[(ref, pad.GetNumber())] = (net, round(x_mm, 3), round(y_mm, 3))

# Print relevant pads
interesting = ["J8", "J2", "J3", "J4", "J5", "J6", "J9", "R3", "R5", "R6", "R7", "R8",
               "R13", "R14", "R15", "LED1", "LED2", "LED6", "L1", "D1", "U1", "C1", "C2",
               "HUM1"]

for ref in interesting:
    pads = [(k, v) for k, v in pad_info.items() if k[0] == ref]
    pads.sort(key=lambda x: int(x[0][1]) if x[0][1].isdigit() else 0)
    if pads:
        print(f"\n{ref}:")
        for (r, num), (net, x, y) in pads:
            print(f"  pad {num:>3}: net={net:<20} x={x:>7.3f} y={y:>7.3f}")
