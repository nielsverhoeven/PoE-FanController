import sys, math
sys.path.insert(0, r'C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin')
import pcbnew

PCB_PATH = r'C:\repos-github\PoE-FanController\hardware\kicad\PoE-FanController.kicad_pcb'
board = pcbnew.LoadBoard(PCB_PATH)
netinfo = board.GetNetInfo()

def tomm(v): return round(pcbnew.ToMM(v), 2)

# Find tracks on +5V, GND, +12V nets and report their endpoints
for net_name in ['+5V', 'GND', '+12V']:
    net = netinfo.GetNetItem(net_name)
    if not net: continue
    net_code = net.GetNetCode()
    tracks = [t for t in board.GetTracks() if t.GetNetCode() == net_code]
    print(f"\n{net_name} tracks ({len(tracks)} total):")
    for t in sorted(tracks, key=lambda t: pcbnew.ToMM(t.GetStart().x)):
        sx,sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
        ex,ey = tomm(t.GetEnd().x),   tomm(t.GetEnd().y)
        w = tomm(t.GetWidth())
        print(f"  ({sx},{sy})->({ex},{ey}) w={w}")
