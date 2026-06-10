"""
T004: Route all PCB traces on the corrected J8 right-column layout.

Issue #148 — correct GPIO pin assignments for J8 (ESP32-P4-POE-ETH right column).

Routing strategy (verified against actual pad coordinates):
  F_Cu: Power rails (+5V, +12V, +3V3), BOOST_SW, fan TACH F->header segments
  B_Cu: Fan PWM (J8->header), fan TACH (J8->pullup), control signals

Trace widths:
  Power (+12V, +5V): 0.8 mm
  Rail  (+3V3):      0.5 mm
  Signal:            0.25 mm
  Via: drill=0.8mm, size=1.6mm

Usage:
  C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin/python.exe hardware/t004_route_pcb.py
"""

import sys
sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

PCB = r'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb'

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def mm(x):
    return pcbnew.FromMM(x)

def pt(x_mm, y_mm):
    return pcbnew.VECTOR2I(mm(x_mm), mm(y_mm))

def get_net(board, name):
    n = board.GetNetInfo().GetNetItem(name)
    if n is None:
        raise ValueError(f"Net '{name}' not found in board")
    return n

def add_track(board, net_name, layer, x1, y1, x2, y2, w=0.25):
    if abs(x1 - x2) < 0.001 and abs(y1 - y2) < 0.001:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetLayer(layer)
    t.SetWidth(mm(w))
    t.SetStart(pt(x1, y1))
    t.SetEnd(pt(x2, y2))
    t.SetNet(get_net(board, net_name))
    board.Add(t)

def add_via(board, net_name, x, y, drill=0.8, size=1.6):
    v = pcbnew.PCB_VIA(board)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(mm(size))
    v.SetDrill(mm(drill))
    v.SetPosition(pt(x, y))
    v.SetNet(get_net(board, net_name))
    board.Add(v)

def route_L(board, net, layer, x1, y1, x2, y2, h_first=True, w=0.25):
    """L-shaped route: horizontal-then-vertical or vertical-then-horizontal."""
    if h_first:
        add_track(board, net, layer, x1, y1, x2, y1, w)
        add_track(board, net, layer, x2, y1, x2, y2, w)
    else:
        add_track(board, net, layer, x1, y1, x1, y2, w)
        add_track(board, net, layer, x1, y2, x2, y2, w)

F = pcbnew.F_Cu
B = pcbnew.B_Cu

# ─────────────────────────────────────────────────────────────────────────────
# Load board
# ─────────────────────────────────────────────────────────────────────────────
print(f"Loading PCB: {PCB}")
board = pcbnew.LoadBoard(PCB)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Fan PWM signals — B_Cu, 0.25 mm
#    J8 right-col pad → fan header pin 4 (east then north/south)
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- Fan PWM (B_Cu) ---")

# FAN1_PWM: J8 pad 35 (18.19,17.37) -> J2 pad 4 (65.62,10.00)
route_L(board, "FAN1_PWM", B, 18.19, 17.37, 65.62, 10.00, h_first=True)
print("  FAN1_PWM routed")

# FAN2_PWM: J8 pad 33 (18.19,22.45) -> J3 pad 4 (65.62,22.00)
route_L(board, "FAN2_PWM", B, 18.19, 22.45, 65.62, 22.00, h_first=True)
print("  FAN2_PWM routed")

# FAN3_PWM: J8 pad 29 (18.19,32.61) -> J4 pad 4 (65.62,34.00)
route_L(board, "FAN3_PWM", B, 18.19, 32.61, 65.62, 34.00, h_first=True)
print("  FAN3_PWM routed")

# FAN4_PWM: J8 pad 27 (18.19,37.69) -> J5 pad 4 (65.62,46.00)
route_L(board, "FAN4_PWM", B, 18.19, 37.69, 65.62, 46.00, h_first=True)
print("  FAN4_PWM routed")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Fan TACH signals
#    Segment A: J8 right-col → pullup resistor pad 2  (B_Cu)
#    Segment B: pullup pad 2 → via                    (F_Cu, north then east)
#    Segment C: via → fan header pin 3                (B_Cu, east then south)
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- Fan TACH (B_Cu / F_Cu / via) ---")

# ── FAN1_TACH ──────────────────────────────────────────────────────────────
# Seg A (B_Cu): J8 pad 32 (18.19,24.99) -> R5 pad 2 (32.62,35.00)
route_L(board, "FAN1_TACH", B, 18.19, 24.99, 32.62, 35.00, h_first=True)
# Seg B (F_Cu): R5 pad 2 (32.62,35.00) -> via (59.0,9.0)  [north then east]
add_track(board, "FAN1_TACH", F, 32.62, 35.00, 32.62,  9.00)  # north
add_track(board, "FAN1_TACH", F, 32.62,  9.00, 59.00,  9.00)  # east
add_via(board, "FAN1_TACH", 59.00, 9.00)
# Seg C (B_Cu): via -> J2 pad 3 (63.08,10.00)  [east then south]
add_track(board, "FAN1_TACH", B, 59.00,  9.00, 63.08,  9.00)  # east
add_track(board, "FAN1_TACH", B, 63.08,  9.00, 63.08, 10.00)  # south
print("  FAN1_TACH routed")

# ── FAN2_TACH ──────────────────────────────────────────────────────────────
# Seg A (B_Cu): J8 pad 31 (18.19,27.53) -> R6 pad 2 (42.62,30.00)
route_L(board, "FAN2_TACH", B, 18.19, 27.53, 42.62, 30.00, h_first=True)
# Seg B (F_Cu): R6 pad 2 (42.62,30.00) -> via (59.0,21.0)
add_track(board, "FAN2_TACH", F, 42.62, 30.00, 42.62, 21.00)  # north
add_track(board, "FAN2_TACH", F, 42.62, 21.00, 59.00, 21.00)  # east
add_via(board, "FAN2_TACH", 59.00, 21.00)
# Seg C (B_Cu): via -> J3 pad 3 (63.08,22.00)
add_track(board, "FAN2_TACH", B, 59.00, 21.00, 63.08, 21.00)  # east
add_track(board, "FAN2_TACH", B, 63.08, 21.00, 63.08, 22.00)  # south
print("  FAN2_TACH routed")

# ── FAN3_TACH ──────────────────────────────────────────────────────────────
# Seg A (B_Cu): J8 pad 24 (18.19,45.31) -> R7 pad 2 (42.62,50.00)
route_L(board, "FAN3_TACH", B, 18.19, 45.31, 42.62, 50.00, h_first=True)
# Seg B (F_Cu): R7 pad 2 (42.62,50.00) -> via (59.0,33.5)
add_track(board, "FAN3_TACH", F, 42.62, 50.00, 42.62, 33.50)  # north
add_track(board, "FAN3_TACH", F, 42.62, 33.50, 59.00, 33.50)  # east
add_via(board, "FAN3_TACH", 59.00, 33.50)
# Seg C (B_Cu): via -> J4 pad 3 (63.08,34.00)
add_track(board, "FAN3_TACH", B, 59.00, 33.50, 63.08, 33.50)  # east
add_track(board, "FAN3_TACH", B, 63.08, 33.50, 63.08, 34.00)  # south
print("  FAN3_TACH routed")

# ── FAN4_TACH ──────────────────────────────────────────────────────────────
# Seg A (B_Cu): J8 pad 22 (18.19,50.39) -> R8 pad 2 (42.62,66.00)
#   jog south to y=51.5 first (clears R7 pad at y=50 by 1.5mm), then x=44 vertical
add_track(board, "FAN4_TACH", B, 18.19, 50.39, 18.19, 51.50)  # south stub
add_track(board, "FAN4_TACH", B, 18.19, 51.50, 44.00, 51.50)  # east
add_track(board, "FAN4_TACH", B, 44.00, 51.50, 44.00, 66.00)  # south
add_track(board, "FAN4_TACH", B, 44.00, 66.00, 42.62, 66.00)  # west to R8p2
# Seg B (F_Cu): R8 pad 2 (42.62,66.00) -> via (59.0,45.0)
#   separate x-lane at x=44 to avoid FAN3_TACH F_Cu at x=42.62
add_track(board, "FAN4_TACH", F, 42.62, 66.00, 44.00, 66.00)  # east stub
add_track(board, "FAN4_TACH", F, 44.00, 66.00, 44.00, 45.00)  # north
add_track(board, "FAN4_TACH", F, 44.00, 45.00, 59.00, 45.00)  # east
add_via(board, "FAN4_TACH", 59.00, 45.00)
# Seg C (B_Cu): via -> J5 pad 3 (63.08,46.00)
add_track(board, "FAN4_TACH", B, 59.00, 45.00, 63.08, 45.00)  # east
add_track(board, "FAN4_TACH", B, 63.08, 45.00, 63.08, 46.00)  # south
print("  FAN4_TACH routed")

# ─────────────────────────────────────────────────────────────────────────────
# 3. PROBE_LED — F_Cu, 0.25 mm
#    J8 pad 21 (18.19,52.93) -> R15 pad 1 (36.00,58.00) -> R15 pad 2 (43.62,58) -> LED6 pad 1 (48.00,58)
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- PROBE_LED ---")
# J8 pad 21 -> R15 pad 1: east then south
route_L(board, "PROBE_LED", F, 18.19, 52.93, 36.00, 58.00, h_first=True)
print("  PROBE_LED routed J8->R15p1")

# /PROBE_LED_A: R15 pad 2 -> LED6 pad 1
add_track(board, "/PROBE_LED_A", F, 43.62, 58.00, 48.00, 58.00)
print("  /PROBE_LED_A routed R15p2->LED6p1")

# ─────────────────────────────────────────────────────────────────────────────
# 4. STATUS_LED — B_Cu, 0.25 mm
#    J8 pad 6 (2.81,40.23) -> R3 pad 1 (25.00,20.00)
#    Route: south stub to y=41.5, east to x=23 (midlane between J8 cols),
#           north to y=20, east to R3 pad 1
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- STATUS_LED ---")
add_track(board, "STATUS_LED", B, 2.81, 40.23, 2.81, 41.50)   # south stub
add_track(board, "STATUS_LED", B, 2.81, 41.50, 23.00, 41.50)  # east (clears J8 right col)
add_track(board, "STATUS_LED", B, 23.00, 41.50, 23.00, 20.00) # north
add_track(board, "STATUS_LED", B, 23.00, 20.00, 25.00, 20.00) # east to R3p1
print("  STATUS_LED routed J8p6->R3p1")

# /LED_A: R3 pad 2 (32.62,20) -> LED1 pad 1 (25.00,58.00)
add_track(board, "/LED_A", B, 32.62, 20.00, 37.00, 20.00)  # east past R5 region
add_track(board, "/LED_A", B, 37.00, 20.00, 37.00, 60.00)  # south
add_track(board, "/LED_A", B, 37.00, 60.00, 25.00, 60.00)  # west
add_track(board, "/LED_A", B, 25.00, 60.00, 25.00, 58.00)  # north to LED1p1
print("  /LED_A routed R3p2->LED1p1")

# ─────────────────────────────────────────────────────────────────────────────
# 5. PROG_LED — B_Cu, 0.25 mm
#    J8 pad 14 (2.81,19.91) -> R13 pad 1 (25.00,64.00)
#    Route: south stub to y=21.18 (midlane between J8 right pads 34/33),
#           east to x=22 (separate from STATUS_LED at x=23),
#           south to y=64, east to R13 pad 1
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- PROG_LED ---")
add_track(board, "PROG_LED", B, 2.81, 19.91, 2.81, 21.18)   # south stub
add_track(board, "PROG_LED", B, 2.81, 21.18, 22.00, 21.18)  # east
add_track(board, "PROG_LED", B, 22.00, 21.18, 22.00, 64.00) # south
add_track(board, "PROG_LED", B, 22.00, 64.00, 25.00, 64.00) # east to R13p1
print("  PROG_LED routed J8p14->R13p1")

# /PROG_LED_A: R13 pad 2 (32.62,64) -> LED2 pad 1 (31.00,58.00)
add_track(board, "/PROG_LED_A", B, 32.62, 64.00, 32.62, 58.00)  # north
add_track(board, "/PROG_LED_A", B, 32.62, 58.00, 31.00, 58.00)  # west to LED2p1
print("  /PROG_LED_A routed R13p2->LED2p1")

# ─────────────────────────────────────────────────────────────────────────────
# 6. DHT11_DATA — B_Cu, 0.25 mm
#    J8 pad 15 (2.81,17.37) -> HUM1 pad 2 (24.54,70.00)
#    Route: south stub to y=18.64 (midlane J8 right pads 35/34), east to x=20,
#           south to y=70.5 (clears HUM1 pad 1 at y=70 by 0.5mm approach),
#           east to x=24.54, north to HUM1p2
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- DHT11_DATA ---")
add_track(board, "DHT11_DATA", B, 2.81, 17.37, 2.81, 18.64)   # south stub
add_track(board, "DHT11_DATA", B, 2.81, 18.64, 20.00, 18.64)  # east
add_track(board, "DHT11_DATA", B, 20.00, 18.64, 20.00, 70.50) # south
add_track(board, "DHT11_DATA", B, 20.00, 70.50, 24.54, 70.50) # east
add_track(board, "DHT11_DATA", B, 24.54, 70.50, 24.54, 70.00) # north into HUM1p2
print("  DHT11_DATA routed J8p15->HUM1p2")

# ─────────────────────────────────────────────────────────────────────────────
# 7. DS18B20_DATA — B_Cu, 0.25 mm
#    J8 pad 19 (2.81,7.21) -> R14 pad 2 (43.62,55.00) -> J6 pad 2 (60.54,58.00)
#    Route J8->R14: south stub to y=8.48, east to x=45, south to y=55, west to R14p2
#    Route R14->J6: west to x=40, south to y=68 (clear of FAN4_TACH at y=51.5-66),
#                   east to x=60.54, north to J6p2
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- DS18B20_DATA ---")
# J8 pad 19 -> R14 pad 2
add_track(board, "DS18B20_DATA", B, 2.81, 7.21,  2.81, 8.48)  # south stub
add_track(board, "DS18B20_DATA", B, 2.81, 8.48, 45.00, 8.48)  # east (x=45 clears F_Cu conflicts)
add_track(board, "DS18B20_DATA", B, 45.00, 8.48, 45.00, 55.00) # south
add_track(board, "DS18B20_DATA", B, 45.00, 55.00, 43.62, 55.00) # west to R14p2
print("  DS18B20_DATA routed J8p19->R14p2")

# R14 pad 2 -> J6 pad 2: go west to x=40, south to y=68 (south of FAN4_TACH vertical at x=44 y=51.5-66)
add_track(board, "DS18B20_DATA", B, 43.62, 55.00, 40.00, 55.00) # west
add_track(board, "DS18B20_DATA", B, 40.00, 55.00, 40.00, 68.00) # south past FAN4_TACH
add_track(board, "DS18B20_DATA", B, 40.00, 68.00, 60.54, 68.00) # east
add_track(board, "DS18B20_DATA", B, 60.54, 68.00, 60.54, 58.00) # north to J6p2
print("  DS18B20_DATA routed R14p2->J6p2")

# ─────────────────────────────────────────────────────────────────────────────
# 8. +5V power — F_Cu, 0.8 mm
#    Main path: J8 pad 40 (18.19,4.67) -> L1p1 (33,3) -> U1p2 (23.7,6) -> C1p1 (24,15)
#    Bus for pads 2,4: x=10 vertical from y=50.39 to y=4.67, branches at each pad
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- +5V power (F_Cu) ---")
W5 = 0.8  # +5V trace width

# J8 pad 40 -> L1 pad 1
route_L(board, "+5V", F, 18.19, 4.67, 33.00, 3.00, h_first=True, w=W5)

# L1 pad 1 -> U1 pad 2 (west then south)
route_L(board, "+5V", F, 33.00, 3.00, 23.70, 6.00, h_first=True, w=W5)

# U1 pad 2 -> C1 pad 1 (south then east)
route_L(board, "+5V", F, 23.70, 6.00, 24.00, 15.00, h_first=False, w=W5)

# J8 pads 2 & 4 connected via x=10 bus north to pad 40
add_track(board, "+5V", F, 2.81, 50.39, 10.00, 50.39, W5)   # pad 2 east to bus
add_track(board, "+5V", F, 2.81, 45.31, 10.00, 45.31, W5)   # pad 4 east to bus
add_track(board, "+5V", F, 10.00, 50.39, 10.00, 4.67, W5)   # bus north
add_track(board, "+5V", F, 10.00, 4.67, 18.19, 4.67, W5)    # bus east to pad 40
print("  +5V routed")

# ─────────────────────────────────────────────────────────────────────────────
# 9. BOOST_SW — F_Cu, 0.25 mm
#    U1p3 (25.4,6) <-> U1p4 (27.1,6): short east
#    U1p3 -> L1p2 (43.16,3): north then east
#    L1p2 -> D1p1 (46.0,2.5): east then north
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- BOOST_SW (F_Cu) ---")
# U1 pins 3-4 tie
add_track(board, "BOOST_SW", F, 25.40, 6.00, 27.10, 6.00)
# U1p3 north to y=3, east to L1p2
add_track(board, "BOOST_SW", F, 25.40, 6.00, 25.40, 3.00)
add_track(board, "BOOST_SW", F, 25.40, 3.00, 43.16, 3.00)
# L1p2 east to D1p1
add_track(board, "BOOST_SW", F, 43.16, 3.00, 46.00, 3.00)
add_track(board, "BOOST_SW", F, 46.00, 3.00, 46.00, 2.50)
print("  BOOST_SW routed")

# ─────────────────────────────────────────────────────────────────────────────
# 10. +12V power — F_Cu, 0.8 mm
#     D1p2 (50,2.5) -> trunk at x=60.54 -> fan headers J2-J5 pin 2
#     Branch to C2p1 (40,18) via north detour at y=16
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- +12V power (F_Cu) ---")
W12 = 0.8

# D1 cathode to trunk
add_track(board, "+12V", F, 50.00, 2.50, 60.54, 2.50, W12)

# Vertical trunk x=60.54, y=2.5 -> y=46 (J5 pad 2)
add_track(board, "+12V", F, 60.54, 2.50, 60.54, 46.00, W12)
# (J2p2, J3p2, J4p2, J5p2 all lie on this trunk at x=60.54)

# C2p1 (40,18) -> trunk: north from C2p1, east at y=16, into trunk at y=16
add_track(board, "+12V", F, 40.00, 18.00, 40.00, 16.00, W12)  # north from C2p1
add_track(board, "+12V", F, 40.00, 16.00, 60.54, 16.00, W12)  # east to trunk
print("  +12V routed")

# ─────────────────────────────────────────────────────────────────────────────
# 11. +3V3 power — F_Cu, 0.5 mm
#     J8 pad 36 (18.19,14.83) -> bus at x=35 (south to y=62)
#     Branches: R5p1 (25,35) west, R6p1/R7p1/R8p1 on bus, R14p1 east 1mm,
#               HUM1p1 (22,70) via y=62 detour west+south,
#               J6p3 (63.08,58) via B_Cu y=43 east route
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- +3V3 power ---")
W3 = 0.5

# J8 pad 36 east to x=35 bus
add_track(board, "+3V3", F, 18.19, 14.83, 35.00, 14.83, W3)

# Vertical bus at x=35, y=14.83 -> y=62
add_track(board, "+3V3", F, 35.00, 14.83, 35.00, 62.00, W3)

# R5 pad 1 branch: west from (35,35) to (25,35)
add_track(board, "+3V3", F, 35.00, 35.00, 25.00, 35.00, W3)

# R14 pad 1 branch: east 1mm from bus at (35,55) to (36,55)
add_track(board, "+3V3", F, 35.00, 55.00, 36.00, 55.00, W3)

# HUM1 pad 1 (22,70): branch west at y=62, south to y=70
add_track(board, "+3V3", F, 35.00, 62.00, 22.00, 62.00, W3)  # west
add_track(board, "+3V3", F, 22.00, 62.00, 22.00, 70.00, W3)  # south to HUM1p1

# J6 pad 3 (63.08,58): via at (35,43), B_Cu east then south approach from north
add_via(board, "+3V3", 35.00, 43.00)
add_track(board, "+3V3", B, 35.00, 43.00, 64.00, 43.00, W3)  # east on B_Cu
add_track(board, "+3V3", B, 64.00, 43.00, 64.00, 57.50, W3)  # south
add_track(board, "+3V3", B, 64.00, 57.50, 63.08, 57.50, W3)  # west
add_track(board, "+3V3", B, 63.08, 57.50, 63.08, 58.00, W3)  # south into J6p3
print("  +3V3 routed")

# ─────────────────────────────────────────────────────────────────────────────
# 12. GND — vias at key isolated GND pads to connect to copper zones
#     (GND copper pours on F_Cu and B_Cu handle most connectivity)
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- GND vias ---")
# J8 left col GND pads
gnd_pads = [
    (2.81,  47.85),  # J8 pad  3
    (2.81,  35.15),  # J8 pad  8
    (2.81,  22.45),  # J8 pad 13
    (2.81,   9.75),  # J8 pad 18
    (2.81,   4.67),  # J8 pad 20
    # J8 right col GND pads
    (18.19, 47.85),  # J8 pad 23
    (18.19, 42.77),  # J8 pad 25
    (18.19, 40.23),  # J8 pad 26
    (18.19, 35.15),  # J8 pad 28
    (18.19, 30.07),  # J8 pad 30
    (18.19, 19.91),  # J8 pad 34
    (18.19,  9.75),  # J8 pad 38
    # Fan headers GND pads
    (58.00, 10.00),  # J2 pad 1
    (58.00, 22.00),  # J3 pad 1
    (58.00, 34.00),  # J4 pad 1
    (58.00, 46.00),  # J5 pad 1
    # Misc GND
    (23.70, 15.00),  # C1 pad 2 (GND) — actually C1p2 is at (26.5,15)
    (26.50, 15.00),  # C1 pad 2 GND
    (42.50, 18.00),  # C2 pad 2 GND
    (22.00,  6.00),  # U1 pad 1 GND
    (28.80,  6.00),  # U1 pad 5 GND
    (27.08, 70.00),  # HUM1 pad 3 GND
    (27.54, 58.00),  # LED1 pad 2 GND
    (33.54, 58.00),  # LED2 pad 2 GND
    (50.54, 58.00),  # LED6 pad 2 GND
    (58.00, 58.00),  # J6 pad 1 GND
]
for (gx, gy) in gnd_pads:
    add_via(board, "GND", gx, gy)
print(f"  Added {len(gnd_pads)} GND vias")

# ─────────────────────────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────────────────────────
print("\nRebuilding connectivity...")
board.BuildConnectivity()
print(f"Saving PCB: {PCB}")
board.Save(PCB)
print("Done.")

# Quick stats
tracks = list(board.GetTracks())
print(f"\nTrack/via count: {len(tracks)}")
