import sys, math
sys.path.insert(0, r'C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin')
import pcbnew

PCB_PATH = r'C:\repos-github\PoE-FanController\hardware\kicad\PoE-FanController.kicad_pcb'
board = pcbnew.LoadBoard(PCB_PATH)
netinfo = board.GetNetInfo()

def mm(v):   return pcbnew.FromMM(float(v))
def tomm(v): return round(pcbnew.ToMM(v), 2)

netgnd = netinfo.GetNetItem('GND')

# Remove the offending GND vertical trace (45.19,28.5)->(45.19,21.75)
# that crosses +3V3 at y=26.83
removed = 0
for t in list(board.GetTracks()):
    if t.GetNetCode() != netgnd.GetNetCode(): continue
    w = tomm(t.GetWidth())
    if w < 0.9: continue
    sx,sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
    ex,ey = tomm(t.GetEnd().x),   tomm(t.GetEnd().y)
    # The bad vertical trace: x=45.19, y between 21.75 and 28.5
    if abs(sx-45.19)<0.1 and abs(ex-45.19)<0.1:
        board.Remove(t)
        removed += 1
        print(f'Removed GND trace ({sx},{sy})->({ex},{ey})')

print(f'Total removed: {removed}')

# Reroute: Pad2(37,28.5) -> right to (45.19,28.5) -> DOWN to (45.19,34.45) -> to GND bus
def add_track(net, x1, y1, x2, y2, w=1.0):
    seg = pcbnew.PCB_TRACK(board)
    seg.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    seg.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    seg.SetWidth(mm(w))
    seg.SetLayer(pcbnew.F_Cu)
    seg.SetNet(net)
    board.Add(seg)
    print(f'  Added GND ({x1},{y1})->({x2},{y2})')

# Route IN- GND downward to lower GND bus at y=34.45
add_track(netgnd, 37.0, 28.5, 45.19, 28.5)    # horizontal right
add_track(netgnd, 45.19, 28.5, 45.19, 34.45)   # down to GND bus (avoids +3V3 at y=26.83)

board.Save(PCB_PATH)
print('PCB saved.')
