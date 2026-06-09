"""T001 — Fix GND Zone Net Assignment and extend zone to full board."""
import sys
sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

PCB = 'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb'
board = pcbnew.LoadBoard(PCB)
board.BuildConnectivity()

def mm(x): return pcbnew.FromMM(x)

gnd_net = board.FindNet('GND')
if gnd_net is None:
    raise ValueError("GND net not found!")
print(f"GND net code: {gnd_net.GetNetCode()}")

# Fix zone nets and extend boundaries to full board
# Board is 70x78mm; extend zones to cover x=-1 to 71, y=-1 to 79 (with margin)
BX0, BY0, BX1, BY1 = -1.0, -1.0, 71.0, 79.0

fixed = 0
for i, zone in enumerate(board.Zones()):
    old_net = zone.GetNetname()
    zone.SetNet(gnd_net)
    layer_id = zone.GetLayer()
    print(f"Zone {i}: layer={layer_id} net {old_net!r} -> GND")

    # Replace outline with full-board rectangle
    outline = zone.Outline()
    outline.RemoveAllContours()
    outline.NewOutline()
    outline.Append(mm(BX0), mm(BY0))
    outline.Append(mm(BX1), mm(BY0))
    outline.Append(mm(BX1), mm(BY1))
    outline.Append(mm(BX0), mm(BY1))
    fixed += 1

print(f"Fixed {fixed} zones → GND, extended to ({BX0},{BY0})–({BX1},{BY1}) mm")

board.BuildConnectivity()
board.Save(PCB)
print("Saved:", PCB)
