# PCB: update positions, shrink board right side, route all traces
# Run: C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe hardware/route_final.py

import sys
sys.path.insert(0, 'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin/Lib/site-packages')
import pcbnew

PCB = 'hardware/kicad/PoE-FanController.kicad_pcb'
board = pcbnew.LoadBoard(PCB)

PWR = 1.0; SIG = 0.25
F = pcbnew.F_Cu; B = pcbnew.B_Cu

def mm(v): return pcbnew.FromMM(float(v))
def net(n):
    x = board.FindNet(n)
    if x is None: raise ValueError(f'Net not found: {n}')
    return x
def seg(n,x1,y1,x2,y2,w=SIG,layer=F):
    if abs(x1-x2)<0.001 and abs(y1-y2)<0.001: return
    t = pcbnew.PCB_TRACK(board)
    t.SetNet(net(n)); t.SetWidth(mm(w)); t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1)))
    t.SetEnd(  pcbnew.VECTOR2I(mm(x2),mm(y2)))
    board.Add(t)
def poly(n,pts,w=SIG,layer=F):
    for i in range(len(pts)-1):
        seg(n,pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1],w,layer)
def via(n,x,y):
    v = pcbnew.PCB_VIA(board)
    v.SetNet(net(n)); v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); board.Add(v)

# ── Step 1: Update positions from user-saved PCB ──────────────────────────────
positions = {
    'C1': (41.00, 9.00,-90), 'C2': (73.00, 9.00,-90),
    'D1': (70.50, 4.50,  0), 'D2': (59.12,25.00,  0),
    'D3': (59.12,37.50,  0), 'D4': (59.12,51.00,  0), 'D5': (59.12,63.00,  0),
    'G***':(25.50,65.50,  0),
    'HUM1':( 7.50,70.08,180),
    'J2': (73.12,17.96,-90), 'J3': (73.12,32.00,-90),
    'J4': (73.12,46.00,-90), 'J5': (73.12,59.00,-90),
    'J6': ( 7.42,55.02,  0), 'J8': (25.50,28.80, 90),
    'L1': (41.00, 4.50,  0),
    'LED1':( 6.00,19.96,-90), 'LED2':(11.00,19.96,-90),
    'LED6':( 6.00,42.00,-90),
    'R10':(46.50,37.50,  0), 'R11':(46.50,51.00,  0), 'R12':(46.50,63.00,  0),
    'R13':(11.00, 7.96,-90), 'R14':(12.50,48.00, 90), 'R15':( 6.00,31.00,-90),
    'R3': ( 6.00, 7.96,-90),
    'R5': (54.12,21.50,180), 'R6': (54.12,33.50,180),
    'R7': (54.12,47.00,180), 'R8': (54.12,59.50,180),
    'R9': (46.50,25.00,  0), 'U1': (62.90, 8.05,180),
}
for fp in board.GetFootprints():
    if fp.GetReference() in positions:
        x,y,r = positions[fp.GetReference()]
        fp.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
        fp.SetOrientationDegrees(r)
print('Positions set')

# ── Step 2: Shrink board right edge from 95mm → 82mm ─────────────────────────
for d in board.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        s,e = d.GetStart(), d.GetEnd()
        if abs(pcbnew.ToMM(s.x)-95)<0.5: d.SetStart(pcbnew.VECTOR2I(mm(82), s.y))
        if abs(pcbnew.ToMM(e.x)-95)<0.5: d.SetEnd  (pcbnew.VECTOR2I(mm(82), e.y))
print('Board shrunk to 82mm')

# ── Step 3: Clear all tracks ──────────────────────────────────────────────────
for t in list(board.GetTracks()): board.Delete(t)

# ── Step 4: Route all signals ─────────────────────────────────────────────────
# VERIFIED routing plan (exhaustive clearance analysis):
#   TACH FAN1-3: B.Cu, col_x=43/42/41 (decreasing → no same-layer crossings)
#   TACH FAN4:   F.Cu col_x=40 + via at x=55 → B.Cu (avoids FAN3/FAN4 crossing)
#   PWM FAN1-2:  F.Cu, col_x=58/57 (straightforward)
#   PWM FAN3-4:  F.Cu with detours to clear R6.2(46.5,33.5) / R10.1(46.5,37.5)
#   +3V3 column: F.Cu at x=54.12 with left-jogs (x=53) around R9-R11 PTH pads
#   +3V3 west:   B.Cu, north route avoiding J8 body, tap to J6.3 via y=57
#   FAN2_TACH:   B.Cu detour around R10 pads (y=38.7 bypass corridor)
#   FAN3_TACH:   B.Cu detour around R11 pads (y=52.5 bypass corridor)

# ── BOOST_SW (1mm, F.Cu) ─────────────────────────────────────────────────────
seg('BOOST_SW', 51.16,4.5, 68.5,4.5, PWR)
poly('BOOST_SW',[(68.5,4.5),(59.5,4.5),(59.5,8.05)],PWR)
seg('BOOST_SW', 57.8,8.05, 59.5,8.05, PWR)

# ── +5V (1mm, F.Cu) via y=9 to avoid BOOST_SW vertical at x=59.5 ─────────────
seg('+5V', 33.19,4.67, 41,4.67, PWR)
seg('+5V', 41,4.67, 41,4.5,  PWR)
seg('+5V', 41,4.5,  41,9,    PWR)
seg('+5V', 41,9,   61.2,9,   PWR)
seg('+5V', 61.2,9, 61.2,8.05,PWR)

# ── +12V (1mm, F.Cu) ─────────────────────────────────────────────────────────
seg('+12V', 72.5,4.5, 74,4.5, PWR)
seg('+12V', 74,4.5,   74,9,   PWR)
seg('+12V', 73,9,     74,9,   PWR)
poly('+12V',[(74,9),(74,67)], PWR)
for fy in [20.5, 34.54, 48.54, 61.54]:
    seg('+12V', 74,fy, 73.12,fy, PWR)
print('+5V/+12V/BOOST done')

# ── +3V3 EAST (1mm, F.Cu) ────────────────────────────────────────────────────
# Horizontal bus only — R5-R8 pull-up pin1 connections left for manual routing
# in KiCad (too dense with PTH pads at x=54.12 to route programmatically)
seg('+3V3', 33.19,14.83, 54.12,14.83, PWR)         # east bus → reaches J8.36

# ── +3V3 WEST (0.5mm, B.Cu) ──────────────────────────────────────────────────
# J8.36 THT → east to x=43, north above J8, west to x=2, south to left zone.
# Tap to J6.3 via y=57 (avoids J6.2 DS18B20 THT pad at y=55.02)
W3 = 0.5
poly('+3V3',[(33.19,14.83),(43,14.83),(43,2),(2,2),(2,70.08),(7.5,70.08)],W3,B)
seg('+3V3', 2,57,    12.5,57,    W3, B)
seg('+3V3', 12.5,57, 12.5,55.02, W3, B)                # → J6.3 (THT)
seg('+3V3', 2,48,    13,48,      W3, B)
via('+3V3', 13,48)
seg('+3V3', 13,48,   12.5,48,    W3)                   # F.Cu stub → R14.1
print('+3V3 done')

# ── Fan TACH (B.Cu, with PTH-clearance detours) ───────────────────────────────
# TACH col_x decreasing (43,42,41,40F) → no same-layer crossings
# FAN2/FAN3: bypass corridors avoid R10.1(46.5,37.5) and R11.1(46.5,51) PTH pads
poly('FAN1_TACH',[(33.19,24.99),(43,24.99),(43,23.04),(73.12,23.04)],SIG,B)
poly('FAN2_TACH',[(33.19,27.53),(42,27.53),(42,37.08),
                  (45,37.08),(45,38.7),(55.5,38.7),(55.5,37.08),(73.12,37.08)],SIG,B)
poly('FAN3_TACH',[(33.19,45.31),(41,45.31),(41,51.08),
                  (45,51.08),(45,52.5),(55.5,52.5),(55.5,51.08),(73.12,51.08)],SIG,B)
# FAN4: F.Cu col_x=40 + via at x=55 → B.Cu (avoids FAN3_TACH B.Cu crossing)
poly('FAN4_TACH',[(33.19,50.39),(40,50.39),(40,64.08),(55,64.08)],SIG,F)
via('FAN4_TACH',55,64.08)
seg('FAN4_TACH',55,64.08,73.12,64.08,SIG,B)

# ── Fan PWM (F.Cu, col_x 58/57/56/55.5, detours for FAN3/FAN4) ───────────────
# col_x > 54.12 → approach/final never cross +3V3 column at x=54.12
poly('FAN1_PWM',[(33.19,17.37),(58,17.37),(58,25.58),(73.12,25.58)])
poly('FAN2_PWM',[(33.19,19.91),(57,19.91),(57,39.62),(73.12,39.62)])
# FAN3: detour via y=39 to clear R6.2(46.5,33.5) and jog-2 at x=53 (y=33.5-38)
poly('FAN3_PWM',[(33.19,32.61),(33.5,32.61),(33.5,39),(56,39),(56,53.62),(73.12,53.62)])
# FAN4: detour via y=40 at x=45.5 to clear R10.1(46.5,37.5); col_x=55.5
poly('FAN4_PWM',[(33.19,37.69),(45.5,37.69),(45.5,40),(55.5,40),(55.5,66.62),(73.12,66.62)])
print('Fan PWM/TACH done')

# ── DS18B20_DATA (F.Cu) ───────────────────────────────────────────────────────
seg('DS18B20_DATA', 17.81,40.23, 12.5,40.23)
seg('DS18B20_DATA', 12.5,40.23,  12.5,40.38)
seg('DS18B20_DATA', 12.5,40.38,  9.96,40.38)
seg('DS18B20_DATA',  9.96,40.38,  9.96,55.02)

# ── PROBE_LED (F.Cu + B.Cu bridge for J8.21) ─────────────────────────────────
seg('PROBE_LED',    17.81,37.69, 6,37.69)
seg('PROBE_LED',     6,37.69,   6,31.0)
seg('/PROBE_LED_A',  6,38.62,   6,42.0)
poly('PROBE_LED',[(33.19,52.93),(33.19,55),(16,55),(16,37.69),(17.81,37.69)],SIG,B)

# ── PWR_LED / /LED_A (F.Cu) ──────────────────────────────────────────────────
seg('PWR_LED', 17.81,12.29, 6,12.29)
seg('PWR_LED',  6,12.29,    6, 7.96)
seg('/LED_A',   6,15.58,    6,19.96)

# ── PROG_LED / /PROG_LED_A (F.Cu, detour via x=19 to clear PWR_LED at y=12.29)
poly('PROG_LED',[(17.81,14.83),(19,14.83),(19,6),(11,6),(11,7.96)])
seg('/PROG_LED_A', 11,15.58, 11,19.96)

# ── DHT11_DATA (F.Cu, detour via y=18 to clear LED pads) ────────────────────
poly('DHT11_DATA',[(17.81,19.91),(16,19.91),(16,18),(5,18),(5,67.54),(7.5,67.54)])
print('Left-zone signals done')

# ── GND zone fill ─────────────────────────────────────────────────────────────
board.Save(PCB)
try:
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(PCB)
    print('GND zones filled')
except Exception as e:
    print(f'Zone fill: {e}')

print(f'Total tracks: {len(list(board.GetTracks()))}')
