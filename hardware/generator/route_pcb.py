# FINAL PCB routing — clean component layout + simplified routing
# Key insight: +3V3 can run under ESP32 (x=15-36mm) on F.Cu
# +12V inter-fan bus at x=66 (outside PWM range x=33-65.62)
# TACH on B.Cu to avoid crossing F.Cu fan PWM traces

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
def seg(n, x1,y1,x2,y2, w=SIG, layer=F):
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
    v.SetNet(net(n)); v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); board.Add(v)

# ── STEP 0: Reposition components (no overlaps, clean zones) ─────────────────
moves = {
    # Boost converter chain — top-right zone, clear of each other
    'L1':  (37, 2),    # inductor: pads (37,2) and (47.16,2)
    'D1':  (52, 3),    # diode:    pads (50,3) and (54,3)
    'C1':  (34, 7),    # +5V bypass: pads (34,7) and (36.5,7)
    'C2':  (56, 4),    # +12V filter: pads (56,4) and (58.5,4)
    # TACH pull-ups — spread vertically between fan headers, x=46
    'R5':  (46, 16),   # FAN1_TACH: pads (46,16) and (53.62,16)
    'R6':  (46, 28),   # FAN2_TACH: pads (46,28) and (53.62,28)
    'R7':  (46, 38),   # FAN3_TACH: pads (46,38) and (53.62,38)
    'R8':  (46, 48),   # FAN4_TACH: pads (46,48) and (53.62,48)
    # Fan indicator resistors — x=53, between fan headers
    'R9':  (53,  7),   # FAN1 ind: pads (53,7) and (60.62,7)
    'R10': (53, 19),   # FAN2 ind: pads (53,19) and (60.62,19)
    'R11': (53, 30),   # FAN3 ind: pads (53,30) and (60.62,30)
    'R12': (53, 43),   # FAN4 ind: pads (53,43) and (60.62,43)
    # Probe LED resistor — below fan area
    'R15': (38, 58),   # PROBE_LED: pads (38,58) and (45.62,58)
    # DS18B20 pull-up — left zone, away from J6 pads
    'R14': (4, 52),    # pads (4,52) and (11.62,52)
}
for fp in board.GetFootprints():
    if fp.GetReference() in moves:
        x,y = moves[fp.GetReference()]
        fp.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))

board.Save(PCB)
board = pcbnew.LoadBoard(PCB)  # reload to get fresh pad positions

# ── Pad lookup ────────────────────────────────────────────────────────────────
pads = {}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        pos = pad.GetPosition()
        pads[f'{fp.GetReference()}.{pad.GetNumber()}'] = (
            pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y), pad.GetNetname())
def p(k): return pads[k][:2]

print('Key pads after reposition:')
for k in ['L1.1','L1.2','D1.1','D1.2','C1.1','C2.1',
          'R5.1','R5.2','R6.1','R6.2','R7.1','R7.2','R8.1','R8.2',
          'R9.1','R9.2','R14.1','R14.2','R15.1','R15.2']:
    print(f'  {k}: {pads[k]}')

# ── BOOST_SW: L1.2 → D1.1 → U1.3/U1.4 (tight loop, avoid crossing D1.2) ─────
# L1.2(47.16,2) BOOST_SW  D1.1(50,3) BOOST_SW  U1.3(45.4,6) U1.4(47.1,6)
poly('BOOST_SW', [(47.16,2),(47.16,5),(45.4,5),(45.4,6)], PWR)  # L1.2→U1.3
seg ('BOOST_SW', 45.4,5, 47.1,5, PWR)                           # lateral link
seg ('BOOST_SW', 47.1,5, 47.1,6, PWR)                           # → U1.4
seg ('BOOST_SW', 50,3,   50,5,   PWR)                           # D1.1 tap up
seg ('BOOST_SW', 50,5,   47.1,5, PWR)                           # join loop

# ── +5V: J8.40 → L1.1, U1.2, C1.1 ──────────────────────────────────────────
# J8.40 at (33.19,4.67)  L1.1(37,2)  U1.2(43.7,6)  C1.1(34,7)
poly('+5V', [(33.19,4.67),(37,4.67),(37,2)], PWR)           # → L1.1
poly('+5V', [(37,4.67),(43.7,4.67),(43.7,6)], PWR)          # → U1.2
poly('+5V', [(37,4.67),(34,4.67),(34,7)], PWR)              # → C1.1

# ── +12V: D1.2 → C2.1 → J2-J5 pin2 via x=66 (outside PWM range) ─────────────
# D1.2(54,3) C2.1(56,4)  J2.2(60.54,10)..J5.2(60.54,46)
seg ('+12V', 54,3, 56,3, PWR)                               # D1.2 → C2.1 area
seg ('+12V', 56,3, 56,4, PWR)                               # → C2.1
# Route +12V at x=66 (outside fan PWM span 33-65.62) to each fan header
poly('+12V', [(56,3),(66,3),(66,47)], PWR)                   # x=66 bus extends to y=47
# Route +12V stubs OUTSIDE the FAN PWM vertical range at x=65.62:
# FAN1_PWM vertical: x=65.62, y=10→17.37 → approach J2.2 from y=9 (above y=10)
# FAN2_PWM vertical: x=65.62, y=19.91→22 → approach J3.2 from y=23 (below y=22)
# FAN3_PWM vertical: x=65.62, y=32.61→34 → approach J4.2 from y=35
# FAN4_PWM vertical: x=65.62, y=37.69→46 → approach J5.2 from y=47
seg ('+12V', 66,9,  60.54,9,  PWR); seg('+12V', 60.54,9,  60.54,10, PWR)  # J2.2
seg ('+12V', 66,23, 60.54,23, PWR); seg('+12V', 60.54,23, 60.54,22, PWR)  # J3.2
seg ('+12V', 66,35, 60.54,35, PWR); seg('+12V', 60.54,35, 60.54,34, PWR)  # J4.2
seg ('+12V', 66,47, 60.54,47, PWR); seg('+12V', 60.54,47, 60.54,46, PWR)  # J5.2
# Indicator resistor +12V stubs (at y values clear of PWM)
seg ('+12V', 53,3,   53,7,  PWR)                            # → R9.1(53,7) from north (avoids crossing R9.2 at y=7)
seg ('+12V', 66,19,  53,19, PWR)                            # → R10.1
seg ('+12V', 66,30,  53,30, PWR)                            # → R11.1
seg ('+12V', 66,43,  53,43, PWR)                            # → R12.1
print('+12V done')

# ── +3V3: J8.36 → R5-R8 (right zone) + left-zone via ESP32 ──────────────────
# J8.36 at (33.19,14.83).  Route RIGHT to pull-ups, LEFT (under ESP32) to sensors.
# Right zone: stubs to R5.1(46,16), R6.1(46,28), R7.1(46,38), R8.1(46,48)
seg ('+3V3', 33.19,14.83, 46,14.83, PWR)                   # main +3V3 east run
seg ('+3V3', 46,14.83,    46,16,    PWR)                    # → R5.1
seg ('+3V3', 46,16,       46,28,    PWR)                    # R5.1→R6.1 column
seg ('+3V3', 46,28,       46,38,    PWR)                    # R6.1→R7.1
seg ('+3V3', 46,38,       46,48,    PWR)                    # R7.1→R8.1
# Left zone via ESP32 zone (allowed — flat trace under module):
seg ('+3V3', 33.19,14.83, 12,14.83, PWR)                   # west run to left zone
seg ('+3V3', 12,14.83,    12,50,    PWR)                    # south column at x=12 (stop at y=50)
seg ('+3V3', 12,50,       4,50,     PWR)                    # west at y=50 → R14.1 approach
seg ('+3V3', 4,50,        4,52,     PWR)                    # → R14.1(4,52)
seg ('+3V3', 12,50,       13,50,    PWR)                    # east jog to x=13 for J6.3/HUM1 branch
seg ('+3V3', 13,50,       13,56,    PWR)                    # south to J6.3 level
seg ('+3V3', 13,56,       12.08,56, PWR)                    # → J6.3
seg ('+3V3', 13,56,       13,60,    PWR)                    # south for HUM1
seg ('+3V3', 13,60,       7,60,     PWR)                    # west
seg ('+3V3', 7,60,        7,68,     PWR)                    # → HUM1.1
print('+3V3 done')

# ── Fan PWM (F.Cu, 0.25mm) ────────────────────────────────────────────────────
poly('FAN1_PWM', [(33.19,17.37),(65.62,17.37),(65.62,10)])
poly('FAN2_PWM', [(33.19,19.91),(65.62,19.91),(65.62,22)])
poly('FAN3_PWM', [(33.19,32.61),(65.62,32.61),(65.62,34)])
poly('FAN4_PWM', [(33.19,37.69),(65.62,37.69),(65.62,46)])
print('Fan PWM done')

# ── Fan TACH: F.Cu stub from J8, B.Cu under PWM, F.Cu to fan header ──────────
# +3V3 side of pull-up already connected above.
# TACH side: J8.32/31/24/22 → R5.2/R6.2/R7.2/R8.2 → J2.3/J3.3/J4.3/J5.3
# Use B.Cu for vertical runs that cross F.Cu fan PWM horizontals.
# Approach fan header pin3 from above (y < fan_y) at x=63.08.

def tach(j8net, j8x,j8y, rpad2x,rpad2y, fanx,fany, bcu_y, xchan):
    """Route one TACH signal: J8 pad → pull-up R.pin2 → fan header pin3.
    After R5-R8 rotation 180°: pin2(TACH) at x=38.38, pin1(+3V3) at x=46.
    B.Cu stub from xchan to rpad2x(38.38) clears +3V3 THT at x=46.
    bcu_y must be >1mm clear of fan GND pin1 annular ring.
    """
    seg(j8net, j8x,j8y, xchan,j8y)                         # F.Cu stub from J8
    via(j8net, xchan, j8y)
    seg(j8net, xchan,j8y, xchan,rpad2y, SIG, B)            # B.Cu up to pull-up y
    seg(j8net, xchan,rpad2y, rpad2x,rpad2y, SIG, B)        # B.Cu stub → R.pin2
    seg(j8net, xchan,rpad2y, xchan,bcu_y, SIG, B)          # B.Cu continue up
    seg(j8net, xchan,bcu_y, fanx,bcu_y, SIG, B)            # B.Cu → fan approach
    via(j8net, fanx, bcu_y)
    seg(j8net, fanx,bcu_y, fanx,fany)                       # F.Cu drop to fan pin3

# Use actual rpad2x after 180° rotation (pin2/TACH at x=38.38)
tach('FAN1_TACH', 33.19,24.99, 38.38,16, 63.08,10, bcu_y=8,  xchan=35)
tach('FAN2_TACH', 33.19,27.53, 38.38,28, 63.08,22, bcu_y=20, xchan=36)
tach('FAN3_TACH', 33.19,45.31, 38.38,38, 63.08,34, bcu_y=32, xchan=37)
tach('FAN4_TACH', 33.19,50.39, 38.38,48, 63.08,46, bcu_y=44, xchan=38)
print('Fan TACH done')

# ── PROBE_LED ─────────────────────────────────────────────────────────────────
# J8.21(33.19,52.93) → R15.1(38,58) → R15.2(45.62,58) → LED6.1(48,58)
r15_1x,r15_1y = p('R15.1'); r15_2x,r15_2y = p('R15.2')
poly('PROBE_LED',    [(33.19,52.93),(r15_1x,52.93),(r15_1x,r15_1y)])
seg ('/PROBE_LED_A', r15_2x,r15_2y, 48,r15_2y)

# ── Fan indicator LEDs (F.Cu) ─────────────────────────────────────────────────
# R9.2→D2.1, R10.2→D3.1, R11.2→D4.1, R12.2→D5.1
r92x = p('R9.2')[0];  poly('/FAN1_IND', [(r92x,7),(48,10)])    # diagonal to D2.1(48,10)
r102x= p('R10.2')[0]; poly('/FAN2_IND', [(r102x,19),(r102x,20.5),(48,20.5),(48,22)])
r112x= p('R11.2')[0]; poly('/FAN3_IND', [(r112x,30),(r112x,31.5),(48,31.5),(48,34)])
r122x= p('R12.2')[0]; poly('/FAN4_IND', [(r122x,43),(r122x,44),(48,44),(48,46)])

# ── Left-zone signals (all on F.Cu, routing under ESP32 where needed) ─────────
# STATUS_LED: go via y=41.5 to clear LED2.1(7,40) /PROG_LED_A pad annular ring
poly('STATUS_LED', [(17.81,40.23),(17.81,41.5),(7,41.5),(5,41.5),(5,18),(7,18)])

# /LED_A: R3.2(14.62,18) → LED1.1(7,24) — via y=22 to avoid LED1.2(9.54,24) GND pad
poly('/LED_A', [(14.62,18),(14.62,22),(7,22),(7,24)])

# PROG_LED: use x=6 vertical to avoid LED1.1(7,24) THT pad
poly('PROG_LED', [(17.81,19.91),(6,19.91),(6,34),(7,34)])

# /PROG_LED_A: R13.2(14.62,34) → LED2.1(7,40) — via y=38 to avoid LED2.2(9.54,40) GND pad
poly('/PROG_LED_A', [(14.62,34),(14.62,38),(7,38),(7,40)])

# DHT11_DATA: route UP from J8.15 to y=16 on F.Cu, then via to B.Cu at y=16
# (y=16 clears R3.2 THT annular ring which extends to y=17.15)
seg ('DHT11_DATA', 17.81,17.37, 17.81,16)                  # F.Cu: J8.15 up to y=16
via('DHT11_DATA', 17.81, 16)
poly('DHT11_DATA', [(17.81,16),(8,16),(8,68),(9.54,68)], SIG, B)  # B.Cu: left then south

# DS18B20_DATA: B.Cu at x=5.5, via at y=54 (clears R14.1(4,52) annular ring)
via('DS18B20_DATA', 17.81, 7.21)
poly('DS18B20_DATA', [(17.81,7.21),(5.5,7.21),(5.5,54)], SIG, B)
via('DS18B20_DATA', 5.5, 54)
poly('DS18B20_DATA', [(5.5,54),(11.62,54),(11.62,52)])      # → R14.2 from y=54
poly('DS18B20_DATA', [(11.62,52),(11.62,56),(9.54,56)])     # → J6.2
print('Left-zone signals done')

# ── Save and fill zones ───────────────────────────────────────────────────────
board.Save(PCB)
try:
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(PCB)
    print('GND zones filled')
except Exception as e:
    print(f'Zone fill: {e}')

print(f'Total tracks: {len(list(board.GetTracks()))}')
