# UPDATED routing — 95mm board, fan headers at x=82, new boost component positions
# Run: C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe hardware/route_v6.py

import sys
sys.path.insert(0, 'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin/Lib/site-packages')
import pcbnew

PCB = 'hardware/kicad/PoE-FanController.kicad_pcb'
board = pcbnew.LoadBoard(PCB)
for t in list(board.GetTracks()): board.Delete(t)

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

# Pad lookup
pads={}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        pos=pad.GetPosition()
        pads[f'{fp.GetReference()}.{pad.GetNumber()}']=(
            pcbnew.ToMM(pos.x),pcbnew.ToMM(pos.y),pad.GetNetname())
def p(k): return pads[k][:2]

# Key positions (verify after placement)
print('Key pads:')
for k in ['L1.1','L1.2','D1.1','D1.2','U1.2','U1.3','U1.4','C1.1','C2.1',
          'R5.1','R5.2','J2.2','J2.3','J2.4']:
    if k in pads: print(f'  {k}: {pads[k]}')

# ── BOOST_SW (F.Cu, 1mm): L1.2→D1.1→U1.3/U1.4 ───────────────────────────────
# L1.2(60.16,5) D1.1(64,5) U1.3(60.4,15) U1.4(62.1,15)
l12x,l12y = p('L1.2'); d11x,d11y = p('D1.1')
u13x,u13y = p('U1.3'); u14x,u14y = p('U1.4')
seg('BOOST_SW', l12x,l12y, d11x,d11y, PWR)                 # L1.2→D1.1 horizontal
seg('BOOST_SW', d11x,d11y, u14x,d11y, PWR)                 # D1.1 west to U1.4 x
seg('BOOST_SW', u14x,d11y, u14x,u14y, PWR)                 # down to U1.4
seg('BOOST_SW', u13x,u13y, u14x,u14y, PWR)                 # U1.3→U1.4

# ── +5V (F.Cu, 1mm): J8.40→L1.1, U1.2, C1.1 ─────────────────────────────────
j840x,j840y = p('J8.40'); l11x,l11y = p('L1.1')
u12x,u12y = p('U1.2');   c11x,c11y = p('C1.1')
poly('+5V',[(j840x,j840y),(l11x,j840y),(l11x,l11y)], PWR)  # →L1.1
poly('+5V',[(l11x,j840y),(c11x,j840y),(c11x,c11y)], PWR)   # →C1.1 (via y=j840y)
poly('+5V',[(l11x,l11y),(l11x,9),(u12x,9),(u12x,u12y)], PWR) # →U1.2 (below L1)

# ── +12V (F.Cu, 1mm): D1.2→C2.1→x=91 bus→fan header pin2 ──────────────────
d12x,d12y = p('D1.2'); c21x,c21y = p('C2.1')
poly('+12V',[(d12x,d12y),(c21x,d12y),(c21x,c21y)], PWR)    # D1.2→C2.1
poly('+12V',[(d12x,d12y),(d12x,3),(91,3),(91,48)], PWR)     # D1.2 up to y=3, east, south bus
seg ('+12V', 73,3, 73,c21y, PWR)                            # stub south to C2.1(73,8)
# Stubs to fan header pin2 (x=84.54) at y values clear of TACH vias and FAN PWM:
# J2.2: y=12 (below TACH drop y=8-10, above PWM y=17.37)
# J3.2: y=25 (below TACH drop y=18-22, above PWM y=32.61)
# J4.2: y=35 (below TACH drop y=32-34, above PWM y=37.69)
# J5.2: y=48 (below TACH drop y=44-46)
for ys,yf in [(12,10),(25,22),(35,34),(48,46)]:
    seg('+12V', 91,ys, 84.54,ys, PWR)
    seg('+12V', 84.54,ys, 84.54,yf, PWR)
# Indicator resistor +12V stubs (at y clear of TACH vias at y=8,18,32,44)
r91x,r91y = p('R9.1');   seg('+12V', 91,r91y,  r91x,r91y,  PWR)  # y=14
r101x,r101y = p('R10.1'); seg('+12V', 91,r101y, r101x,r101y, PWR)  # y=24
r111x,r111y = p('R11.1'); seg('+12V', 91,r111y, r111x,r111y, PWR)  # y=36
r121x,r121y = p('R12.1'); seg('+12V', 91,r121y, r121x,r121y, PWR)  # y=48
print('+12V done')

# ── +3V3 (F.Cu, 1mm): J8.36→R5-R8 + left zone via ESP32 ─────────────────────
j836x,j836y = p('J8.36')
# East to R5-R8 pull-ups (pin1 at x=46)
seg('+3V3', j836x,j836y, 46,j836y, PWR)                    # east run to x=46
seg('+3V3', 46,j836y, 46,16, PWR)                          # south to R5.1(46,16)
poly('+3V3',[(46,16),(46,48)], PWR)                         # column R5→R8
# West under ESP32 to left zone
seg('+3V3', j836x,j836y, 12,j836y, PWR)                    # west under ESP32
seg('+3V3', 12,j836y, 12,50, PWR)                          # south column at x=12
seg('+3V3', 12,50, 4,50, PWR)                              # →R14.1 approach
seg('+3V3', 4,50, 4,52, PWR)                               # →R14.1(4,52)
seg('+3V3', 12,50, 13,50, PWR)                             # east to x=13 branch
seg('+3V3', 13,50, 13,56, PWR)                             # →J6.3 level
seg('+3V3', 13,56, 12.08,56, PWR)                          # →J6.3
seg('+3V3', 13,56, 13,60, PWR)                             # →HUM1 branch
seg('+3V3', 13,60, 7,60, PWR)
seg('+3V3', 7,60, 7,68, PWR)                               # →HUM1.1
print('+3V3 done')

# ── Fan PWM (F.Cu, 0.25mm) — x=89.62 is new fan pin4 x ──────────────────────
poly('FAN1_PWM',[(33.19,17.37),(89.62,17.37),(89.62,10)])
poly('FAN2_PWM',[(33.19,19.91),(89.62,19.91),(89.62,22)])
poly('FAN3_PWM',[(33.19,32.61),(89.62,32.61),(89.62,34)])
poly('FAN4_PWM',[(33.19,37.69),(89.62,37.69),(89.62,46)])
print('Fan PWM done')

# ── Fan TACH (B.Cu to avoid crossing F.Cu PWM) ───────────────────────────────
# After R5-R8 rotation 180°: pin2(TACH) at x=38.38, pin1(+3V3) at x=46
# Fan header pin3 now at x=87.08 (moved from 63.08)
def tach(j8net,j8x,j8y, rpad2x,rpad2y, fanx,fany, bcu_y, xchan):
    seg(j8net, j8x,j8y, xchan,j8y)                         # F.Cu stub from J8
    via(j8net, xchan, j8y)
    seg(j8net, xchan,j8y, xchan,rpad2y, SIG, B)            # B.Cu up to pull-up y
    seg(j8net, xchan,rpad2y, rpad2x,rpad2y, SIG, B)        # →R.pin2
    seg(j8net, xchan,rpad2y, xchan,bcu_y, SIG, B)          # continue up
    seg(j8net, xchan,bcu_y, fanx,bcu_y, SIG, B)            # →fan x column
    via(j8net, fanx, bcu_y)
    seg(j8net, fanx,bcu_y, fanx,fany)                       # F.Cu drop to pin3

tach('FAN1_TACH', 33.19,24.99, 38.38,16, 87.08,10, bcu_y=8,  xchan=35)
tach('FAN2_TACH', 33.19,27.53, 38.38,28, 87.08,22, bcu_y=18, xchan=36)  # bcu_y=18 clears PWM at y=19.91
tach('FAN3_TACH', 33.19,45.31, 38.38,38, 87.08,34, bcu_y=32, xchan=37)
tach('FAN4_TACH', 33.19,50.39, 38.38,48, 87.08,46, bcu_y=44, xchan=38)
print('Fan TACH done')

# ── PROBE_LED ─────────────────────────────────────────────────────────────────
r151x,r151y = p('R15.1'); r152x,r152y = p('R15.2')
poly('PROBE_LED',   [(33.19,52.93),(r151x,52.93),(r151x,r151y)])
seg('/PROBE_LED_A', r152x,r152y, 48,r152y)

# ── Fan indicator LEDs (F.Cu) ─────────────────────────────────────────────────
# R9-R12 at (70,14/24/36/48). R9.2 → D2.1(48,10), etc.
r92x,r92y = p('R9.2')
poly('/FAN1_IND', [(r92x,r92y),(r92x,10),(48,10)])
r102x,r102y = p('R10.2')
poly('/FAN2_IND', [(r102x,r102y),(r102x,22.5),(48,22.5),(48,22)])
r112x,r112y = p('R11.2')
poly('/FAN3_IND', [(r112x,r112y),(r112x,34.5),(48,34.5),(48,34)])
r122x,r122y = p('R12.2')
poly('/FAN4_IND', [(r122x,r122y),(r122x,46.5),(48,46.5),(48,46)])
print('Indicator LEDs done')

# ── Left-zone signals (F.Cu + B.Cu) ──────────────────────────────────────────
# STATUS_LED: J8.6(17.81,40.23) → R3.1(7,18) — route via y=41.5 to clear LED2
poly('STATUS_LED',[(17.81,40.23),(17.81,41.5),(7,41.5),(5,41.5),(5,18),(7,18)])

# /LED_A: via y=22 to avoid LED1.2(9.54,24) GND pad
poly('/LED_A',[(14.62,18),(14.62,22),(7,22),(7,24)])

# PROG_LED: x=6 vertical avoids LED1.1(7,24) THT pad
poly('PROG_LED',[(17.81,19.91),(6,19.91),(6,34),(7,34)])

# /PROG_LED_A: via y=38 to avoid LED2.2(9.54,40) GND pad
poly('/PROG_LED_A',[(14.62,34),(14.62,38),(7,38),(7,40)])

# DHT11_DATA: F.Cu up to y=16, via to B.Cu at y=16 (clears R3.2 annular ring)
seg('DHT11_DATA', 17.81,17.37, 17.81,16)
via('DHT11_DATA', 17.81, 16)
poly('DHT11_DATA',[(17.81,16),(8,16),(8,68),(9.54,68)], SIG, B)

# DS18B20_DATA: B.Cu at x=5.5, via at y=54 (clears R14.1 annular ring)
via('DS18B20_DATA', 17.81, 7.21)
poly('DS18B20_DATA',[(17.81,7.21),(5.5,7.21),(5.5,54)], SIG, B)
via('DS18B20_DATA', 5.5, 54)
poly('DS18B20_DATA',[(5.5,54),(11.62,54),(11.62,52)])
poly('DS18B20_DATA',[(11.62,52),(11.62,56),(9.54,56)])
print('Left-zone signals done')

# ── Save + fill zones ─────────────────────────────────────────────────────────
board.Save(PCB)
try:
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(PCB)
    print('GND zones filled')
except Exception as e:
    print(f'Zone fill: {e}')

print(f'Total tracks: {len(list(board.GetTracks()))}')
