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

# ── PROBE_LED routing now handled in left-zone signals section below ──────────
# (PROBE_LED moved from right column pin 21 to left column pin 7 in v0.6)
# ── PWM indicator LEDs (issue #175) ──────────────────────────────────────────
# R9-R12 at (53,10/22/34/46), D2-D5 at (62,10/22/34/46)
# R*.1 taps the FAN_PWM signal line; R*.2→D*.1 anode hop; D*.2→GND via pour
pwm_levels = {'FAN1_PWM':17.37,'FAN2_PWM':19.91,'FAN3_PWM':32.61,'FAN4_PWM':37.69}
r9x,r9y   = p('R9.1');  r92x,r92y  = p('R9.2')
r10x,r10y = p('R10.1'); r102x,r102y= p('R10.2')
r11x,r11y = p('R11.1'); r112x,r112y= p('R11.2')
r12x,r12y = p('R12.1'); r122x,r122y= p('R12.2')
d2x = p('D2.1')[0]; d3x = p('D3.1')[0]; d4x = p('D4.1')[0]; d5x = p('D5.1')[0]
# Stubs from R*.1 to PWM horizontal (vertical segment connecting to main PWM trace)
seg('FAN1_PWM', r9x, r9y,   r9x,  pwm_levels['FAN1_PWM'])
seg('FAN2_PWM', r10x,r10y,  r10x, pwm_levels['FAN2_PWM'])
seg('FAN3_PWM', r11x,r11y,  r11x, pwm_levels['FAN3_PWM'])
seg('FAN4_PWM', r12x,r12y,  r12x, pwm_levels['FAN4_PWM'])
# Anode connections R*.2 → D*.1
# FAN1: route via y=4 to avoid BOOST_SW vertical at x=62.1 (y=5-15)
seg('FAN1_PWM_A', r92x, r9y,   r92x, 4)        # R9.2 up to y=4 (above BOOST_SW)
seg('FAN1_PWM_A', r92x, 4,     d2x,  4)        # across to D2 x
seg('FAN1_PWM_A', d2x,  4,     d2x,  r9y)      # drop to D2.1 y
# FAN2-4: direct horizontal (BOOST_SW ends at y=15, these are at y=22,34,46)
seg('FAN2_PWM_A', r102x,r10y,  d3x, r10y)
seg('FAN3_PWM_A', r112x,r11y,  d4x, r11y)
seg('FAN4_PWM_A', r122x,r12y,  d5x, r12y)
print('PWM indicator LEDs done')

# ── Left-zone signals (F.Cu + B.Cu) ──────────────────────────────────────────
# New pin positions (v0.6 overhaul):
#   J8.17(17.81,12.29)=PWR_LED   J8.16(17.81,14.83)=PROG_LED
#   J8.14(17.81,19.91)=DHT11     J8.7(17.81,37.69)=PROBE_LED
#   J8.6(17.81,40.23)=DS18B20

# PWR_LED: J8.17(17.81,12.29) → R3.1(7,18) — via y=13.5 to stay above DHT11 at y=19.91
poly('PWR_LED',[(17.81,12.29),(5,12.29),(5,18),(7,18)])

# /LED_A: R3.2(14.62,18) → LED1.1(7,24) — via y=22 to avoid LED1.2(9.54,24)
poly('/LED_A',[(14.62,18),(14.62,22),(7,22),(7,24)])

# PROG_LED: J8.16(17.81,14.83) → R13.1(7,34) — use x=6 to avoid LED1.1(7,24)
poly('PROG_LED',[(17.81,14.83),(6,14.83),(6,34),(7,34)])

# /PROG_LED_A: R13.2(14.62,34) → LED2.1(7,40) — via y=38 to avoid LED2.2(9.54,40)
poly('/PROG_LED_A',[(14.62,34),(14.62,38),(7,38),(7,40)])

# PROBE_LED: J8.7(17.81,37.69) → R15.1(7,50) → LED6.1(7,44)
# Use B.Cu at x=4 to avoid crossing +3V3 F.Cu column at x=12 (y=14.83-50)
via('PROBE_LED', 17.81, 37.69)
poly('PROBE_LED',[(17.81,37.69),(4,37.69),(4,50)], SIG, B)  # B.Cu west then south
via('PROBE_LED', 4, 50)
seg('PROBE_LED', 4,50, 7,50)                                  # F.Cu short hop → R15.1
poly('/PROBE_LED_A',[(14.62,50),(14.62,42),(7,42),(7,44)])   # R15.2→LED6.1 via y=42 (via y=42 avoids LED6.2 at y=44)

# DHT11_DATA: J8.14(17.81,19.91) → HUM1.2(9.54,68) via B.Cu
seg('DHT11_DATA', 17.81,19.91, 17.81,19)
via('DHT11_DATA', 17.81, 19)
poly('DHT11_DATA',[(17.81,19),(8,19),(8,68),(9.54,68)], SIG, B)

# DS18B20_DATA: J8.6(17.81,40.23) → R14.2 → J6.2 via B.Cu at x=5.5
via('DS18B20_DATA', 17.81, 40.23)
poly('DS18B20_DATA',[(17.81,40.23),(5.5,40.23),(5.5,54)], SIG, B)
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
