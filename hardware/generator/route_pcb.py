# CORRECTED routing — all known shorts fixed
# Run: C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe hardware/route_corrected.py

import sys
sys.path.insert(0, 'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin/Lib/site-packages')
import pcbnew

PCB = 'hardware/kicad/PoE-FanController.kicad_pcb'
board = pcbnew.LoadBoard(PCB)
for t in list(board.GetTracks()): board.Delete(t)

PWR = 1.0; SIG = 0.25
F = pcbnew.F_Cu; B = pcbnew.B_Cu

def mm(v): return pcbnew.FromMM(v)
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

def poly(n, pts, w=SIG, layer=F):
    for i in range(len(pts)-1):
        seg(n, pts[i][0],pts[i][1], pts[i+1][0],pts[i+1][1], w, layer)

def via(n, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetNet(net(n))
    v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    board.Add(v)

# ── Pad lookup ────────────────────────────────────────────────────────────────
pads = {}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        pos = pad.GetPosition()
        pads[f'{fp.GetReference()}.{pad.GetNumber()}'] = (
            pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y))
def p(k): return pads[k]

# Verify key positions
r52x,r52y = p('R5.2'); r62x,r62y = p('R6.2')
r72x,r72y = p('R7.2'); r82x,r82y = p('R8.2')
r14_2x, r14_2y = p('R14.2')
print(f'R5.2={r52x,r52y}  R6.2={r62x,r62y}  R7.2={r72x,r72y}  R8.2={r82x,r82y}')
print(f'R14.2={r14_2x,r14_2y}')

# ── BOOST_SW: route AROUND D1.2 cathode (goes up to y=5, avoids x=50 at y=2.5) ──
# D1.1(46,2.5)=BOOST_SW  D1.2(50,2.5)=+12V  L1.2(52.16,2.5)=BOOST_SW
# U1.3(45.4,6)  U1.4(47.1,6) both BOOST_SW
poly('BOOST_SW',[(52.16,2.5),(52.16,5),(45.4,5),(45.4,6)], w=PWR)  # L1.2→U1.3
seg ('BOOST_SW', 45.4,5, 47.1,5, PWR)                              # horizontal link
seg ('BOOST_SW', 47.1,5, 47.1,6, PWR)                              # → U1.4
seg ('BOOST_SW', 46,5,   46,2.5,  PWR)                             # → D1.1

# ── +5V ───────────────────────────────────────────────────────────────────────
poly('+5V',[(33.19,4.67),(42,4.67),(42,2.5)], w=PWR)              # → L1.1
poly('+5V',[(42,4.67),(43.7,4.67),(43.7,6)], w=PWR)               # → U1.2
poly('+5V',[(42,4.67),(41,4.67),(41,14),(42,14)], w=PWR)           # → C1.1

# ── +12V (B.Cu spine) ────────────────────────────────────────────────────────
# D1.2(50,2.5) via → B.Cu spine at x=40, stubs to fan headers (THT auto-connects)
via('+12V', 50, 2.5)
poly('+12V',[(50,2.5),(50,1),(40,1),(40,10)], w=PWR, layer=B)  # D1.2 → spine (y=1 avoids L1.1 at y=2.5)
seg ('+12V', 40,10, 40,46, PWR, B)                                 # spine
poly('+12V',[(36,10),(60.54,10)], w=PWR, layer=B)                  # J2.2 + R9.1
seg ('+12V', 40,22, 60.54,22, PWR, B)                              # J3.2
seg ('+12V', 40,34, 60.54,34, PWR, B)                              # J4.2
seg ('+12V', 40,46, 60.54,46, PWR, B)                              # J5.2
seg ('+12V', 38.5,26, 40,26, PWR, B)                                 # R10.1 (moved to x=38.5)
seg ('+12V', 38.5,34, 40,34, PWR, B)                                 # R11.1
seg ('+12V', 38.5,46, 40,46, PWR, B)                                 # R12.1

# ── +3V3 (B.Cu column at x=36.5, avoids F.Cu PWM horizontal traces) ─────────
via('+3V3', 33.19, 14.83)
seg ('+3V3', 33.19,14.83, 36.5,14.83, PWR, B)
seg ('+3V3', 36.5,14.83,  36.5,54,    PWR, B)                     # column to y=54
seg ('+3V3', 36.5,56,     8,56,        PWR, B)                     # → R14.1(8,56)
via('+3V3', 8, 56)                                                 # up to F.Cu
# F.Cu: R14.1→J6.3 and R14.1→HUM1.1 (avoid J6.1 GND at (7,56))
seg ('+3V3', 8,56, 12.08,56, PWR)                                  # → J6.3
poly('+3V3',[(8,56),(8,58),(7,58),(7,68)], w=PWR)                  # → HUM1.1

# ── Fan PWM (F.Cu, simple L-shapes) ─────────────────────────────────────────
poly('FAN1_PWM',[(33.19,17.37),(65.62,17.37),(65.62,10)])
poly('FAN2_PWM',[(33.19,19.91),(65.62,19.91),(65.62,22)])
poly('FAN3_PWM',[(33.19,32.61),(65.62,32.61),(65.62,34)])
poly('FAN4_PWM',[(33.19,37.69),(65.62,37.69),(65.62,46)])

# ── Fan TACH: F.Cu stub to pull-up, then B.Cu to avoid crossing PWM ──────────
# FAN1_TACH: J8.32(33.19,24.99) → R5.2(44.12,25) → B.Cu → J2.3(63.08,10)
seg('FAN1_TACH', 33.19,24.99, r52x,24.99)
seg('FAN1_TACH', r52x,24.99,  r52x,r52y)
via('FAN1_TACH', r52x, r52y)
poly('FAN1_TACH',[(r52x,r52y),(r52x,12),(63.08,12)], layer=B)
via('FAN1_TACH', 63.08, 12)
seg('FAN1_TACH', 63.08,12, 63.08,10)

# FAN2_TACH: J8.31(33.19,27.53) → R6.2(44.12,28) → B.Cu → J3.3(63.08,22)
seg('FAN2_TACH', 33.19,27.53, r62x,27.53)
seg('FAN2_TACH', r62x,27.53,  r62x,r62y)
via('FAN2_TACH', r62x, r62y)
poly('FAN2_TACH',[(r62x,r62y),(43.12,r62y),(43.12,24),(63.08,24)], layer=B)
via('FAN2_TACH', 63.08, 24)
seg('FAN2_TACH', 63.08,24, 63.08,22)

# FAN3_TACH: J8.24(33.19,45.31) → R7.2(44.12,45) → B.Cu → J4.3(63.08,34)
seg('FAN3_TACH', 33.19,45.31, r72x,45.31)
seg('FAN3_TACH', r72x,45.31,  r72x,r72y)
via('FAN3_TACH', r72x, r72y)
poly('FAN3_TACH',[(r72x,r72y),(r72x,36),(63.08,36)], layer=B)
via('FAN3_TACH', 63.08, 36)
seg('FAN3_TACH', 63.08,36, 63.08,34)

# FAN4_TACH: J8.22(33.19,50.39) → R8.2(44.12,50) → B.Cu → J5.3(63.08,46)
seg('FAN4_TACH', 33.19,50.39, r82x,50.39)
seg('FAN4_TACH', r82x,50.39,  43.12,50.39)
seg('FAN4_TACH', 43.12,50.39, 43.12,r82y)
via('FAN4_TACH', 43.12, r82y)
poly('FAN4_TACH',[(43.12,r82y),(43.12,48),(63.08,48)], layer=B)
via('FAN4_TACH', 63.08, 48)
seg('FAN4_TACH', 63.08,48, 63.08,46)

# ── PROBE_LED chain ───────────────────────────────────────────────────────────
r15_1x,r15_1y = p('R15.1'); r15_2x,r15_2y = p('R15.2')
poly('PROBE_LED',  [(33.19,52.93),(r15_1x,52.93),(r15_1x,r15_1y)])
seg ('/PROBE_LED_A', r15_2x,r15_2y, 48,r15_2y)                    # → LED6.1

# ── Fan indicator LEDs (F.Cu) — approach ABOVE LED anodes to avoid GND pads ──
r92x = p('R9.2')[0]
seg ('/FAN1_IND', r92x,10, 48,10)
r102x = p('R10.2')[0]
poly('/FAN2_IND',[(r102x,26),(r102x,22),(48,22)])
r112x = p('R11.2')[0]
seg ('/FAN3_IND', r112x,34, 48,34)
r122x = p('R12.2')[0]
seg ('/FAN4_IND', r122x,46, 48,46)

# ── Left-zone signals (F.Cu) ─────────────────────────────────────────────────
# STATUS_LED: J8.6(17.81,40.23) → R3.1(7,18)
# Go to y=41 first (below /PROG_LED_A end at y=40) to avoid y=40.23 vs y=40 clearance
poly('STATUS_LED',[(17.81,40.23),(17.81,41),(13,41),(13,16),(7,16),(7,18)])

# /LED_A: R3.2(14.62,18) → LED1.1(7,24)
# Approach at y=22 then drop to y=24 to avoid LED1.2 GND pad at (9.54,24)
poly('/LED_A',[(14.62,18),(14.62,22),(7,22),(7,24)])

# PROG_LED: J8.14(17.81,19.91) → R13.1(7,34)
poly('PROG_LED',[(17.81,19.91),(14,19.91),(14,34),(7,34)])

# /PROG_LED_A: R13.2(14.62,34) → LED2.1(7,40)
# Approach at y=38 then drop to y=40 to avoid LED2.2 GND pad at (9.54,40)
poly('/PROG_LED_A',[(14.62,34),(14.62,38),(7,38),(7,40)])

# DHT11_DATA: J8.15(17.81,17.37) → HUM1.2(9.54,68)
# Use B.Cu at x=8.5 (not 9.54) to avoid LED1.2(9.54,24) and LED2.2(9.54,40) GND pads
via('DHT11_DATA', 17.81, 17.37)
poly('DHT11_DATA',[(17.81,17.37),(7.5,17.37),(7.5,68),(9.54,68)], layer=B)  # x=7.5 avoids +3V3 B.Cu at y=56 (x=8→36.5)

# DS18B20_DATA: J8.19(17.81,7.21) → R14.2(15.62,56) → J6.2(9.54,56)
# F.Cu via x=15.62 channel; approach J6.2 from above (y=58) to avoid J6.3(+3V3) at y=56
poly('DS18B20_DATA',[(17.81,7.21),(r14_2x,7.21),(r14_2x,r14_2y)])
poly('DS18B20_DATA',[(r14_2x,r14_2y),(r14_2x,58),(9.54,58),(9.54,56)])

# ── Save + fill GND zones ─────────────────────────────────────────────────────
board.Save(PCB)
try:
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(PCB)
    print('Zones filled')
except Exception as e:
    print(f'Zone fill: {e}')

print(f'Total tracks: {len(list(board.GetTracks()))}')
print('Run DRC: kicad-cli.exe pcb drc --output hardware/kicad/drc_output.json hardware/kicad/PoE-FanController.kicad_pcb')
