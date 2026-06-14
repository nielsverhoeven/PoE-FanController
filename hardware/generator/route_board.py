#!/usr/bin/env python3
"""
route_board.py v4 — Single-layer F.Cu router for PoE-FanController.

ALL tracks are placed on F.Cu only.  No vias.  No hardcoded net-specific
routes.

Routing strategy
----------------
1. Power nets (GND, +12V, +5V, +3V3, BOOST_SW) are routed FIRST so that
   their segments are registered in SegDB before any signal net is attempted.
   - GND   : horizontal bus at y = GND_BUS_Y  + V stubs from every GND pad.
   - +12V  : vertical spine  at x = V12_BUS_X + H stubs from every +12V pad.
   - +5V   : horizontal bus  at y = V5_BUS_Y  + V stubs from every +5V pad.
   - +3V3  : vertical spine  at x = V3V3_BUS_X+ H stubs from every +3V3 pad.
   - BOOST_SW : MST + bypass.

2. Signal nets: MST (Prim) + per-edge routing that tries, in order:
     2-seg L → 3-seg bypass-x (U) → 3-seg bypass-y (U) → 4-seg detour.
   If all attempts fail the edge is logged as UNROUTED and NO track is placed.
   An unrouted ratsnest is always preferable to a tracks_crossing DRC error on
   a single-copper-layer board.

All routing functions gate EVERY segment placement through:
  • pdb.ok()  — pad-to-track clearance (≥ 0.2 mm gap to foreign copper)
  • segdb.ok()— track-to-track crossing check (axis-aligned H × V detection)
"""

import sys
import math

sys.path.insert(0, "C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin")
import pcbnew

PCB_PATH = ("C:/repos-github/PoE-FanController/hardware/kicad/"
            "PoE-FanController.kicad_pcb")

POWER_NETS = {"+12V", "+5V", "+3V3", "GND"}

# Single routing layer — never changes
ROUTE_LAYER = pcbnew.F_Cu

# Board routing limits (mm).  Board origin ≈ (11.975, 11.975), ~82 × 78 mm.
# Stay ≥ 1.0 mm from every edge.
BRD_X1, BRD_X2 = 13.0, 92.5
BRD_Y1, BRD_Y2 = 13.0, 88.5

# Power bus / spine positions (all well within edge-clearance rules)
GND_BUS_Y   = 88.0   # GND  horizontal bus near bottom edge
V12_BUS_X   = 91.0   # +12V vertical spine near right edge
V5_BUS_Y    = 13.5   # +5V  horizontal bus near top edge
V3V3_BUS_X  = 13.5   # +3V3 vertical spine near left edge

# ── Geometry ──────────────────────────────────────────────────────────────────

def _dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _pt_seg_dist(px, py, x1, y1, x2, y2):
    """Minimum distance from point (px,py) to segment (x1,y1)–(x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0,
                     ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


# ── Pad clearance database ────────────────────────────────────────────────────

class PadDB:
    """Every pad's (x, y, net, copper_radius) for pad-to-track clearance."""

    def __init__(self, board):
        self._pads = []
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                pos = pad.GetPosition()
                x = pcbnew.ToMM(pos.x)
                y = pcbnew.ToMM(pos.y)
                net = pad.GetNetname()
                sz = pad.GetSize()
                r = max(pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)) / 2.0
                self._pads.append((x, y, net, r))

    def ok(self, x1, y1, x2, y2, net_name, half_w, clr=0.2):
        """True if segment clears every foreign pad by ≥ clr mm."""
        if abs(x1 - x2) < 0.001 and abs(y1 - y2) < 0.001:
            return True
        need = half_w + clr
        for px, py, pnet, pr in self._pads:
            if pnet == net_name or pnet == "":
                continue
            if _pt_seg_dist(px, py, x1, y1, x2, y2) < need + pr:
                return False
        return True


# ── Track-to-track crossing database ─────────────────────────────────────────

class SegDB:
    """
    Axis-aligned (H or V) segment crossing / overlap detector.

    Rules for two segments on the same layer with different nets:
      H × V  — perpendicular crossing
      H ‖ H  — same-y overlap (collinear)
      V ‖ V  — same-x overlap (collinear)
    """

    def __init__(self):
        self._segs = []   # (x0, y0, x1, y1, net, layer)  x0≤x1, y0≤y1

    def add(self, x1, y1, x2, y2, net, layer):
        self._segs.append(
            (min(x1, x2), min(y1, y2),
             max(x1, x2), max(y1, y2), net, layer))

    def ok(self, x1, y1, x2, y2, net, layer):
        ax0, ay0 = min(x1, x2), min(y1, y2)
        ax1, ay1 = max(x1, x2), max(y1, y2)
        a_H = (ay1 - ay0) < 1e-6
        a_V = (ax1 - ax0) < 1e-6
        for bx0, by0, bx1, by1, bnet, blyr in self._segs:
            if blyr != layer or bnet == net:
                continue
            b_H = (by1 - by0) < 1e-6
            b_V = (bx1 - bx0) < 1e-6
            # H × V crossing
            if a_H and b_V:
                if ax0 < bx0 < ax1 and by0 < ay0 < by1:
                    return False
            elif a_V and b_H:
                if bx0 < ax0 < bx1 and ay0 < by0 < ay1:
                    return False
            # Collinear overlap
            elif a_H and b_H:
                if abs(ay0 - by0) < 1e-6 and ax0 < bx1 and bx0 < ax1:
                    return False
            elif a_V and b_V:
                if abs(ax0 - bx0) < 1e-6 and ay0 < by1 and by0 < ay1:
                    return False
        return True


# ── MST (Prim) ────────────────────────────────────────────────────────────────

def _prim_mst(pts):
    n = len(pts)
    if n <= 1:
        return []
    INF = float("inf")
    in_tree = [False] * n
    md = [INF] * n
    par = [-1] * n
    md[0] = 0.0
    edges = []
    for _ in range(n):
        u = min((i for i in range(n) if not in_tree[i]), key=lambda i: md[i])
        in_tree[u] = True
        if par[u] >= 0:
            edges.append((par[u], u))
        for v in range(n):
            if not in_tree[v]:
                d = _dist(pts[u], pts[v])
                if d < md[v]:
                    md[v] = d
                    par[v] = u
    return edges


# ── PCB track helper ──────────────────────────────────────────────────────────

def _add(board, nobj, x1, y1, x2, y2, w, layer, segdb):
    """Place one F.Cu track segment and register it in segdb."""
    if abs(x1 - x2) < 0.001 and abs(y1 - y2) < 0.001:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(layer)
    t.SetNet(nobj)
    board.Add(t)
    segdb.add(x1, y1, x2, y2, nobj.GetNetname(), layer)


# ── Bypass-candidate generators ───────────────────────────────────────────────

# Relative offsets tried around the midpoint and both endpoints
_DELTAS = [
    0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5,
    -6, 6, -8, 8, -10, 10, -12, 12, -15, 15,
    -18, 18, -20, 20, -25, 25, -30, 30,
    -35, 35, -40, 40, -50, 50, -60, 60, -70, 70,
]

# Fixed board-region waypoints always included in candidate lists
_BX_FIXED = [13.5, 15.0, 20.0, 25.0, 30.0, 37.0, 45.0,
             55.0, 65.0, 75.0, 85.0, 88.0, 90.0, 91.0]
_BY_FIXED = [13.5, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0,
             50.0, 60.0, 70.0, 78.0, 82.0, 85.0, 88.0]


def _bx_candidates(x1, y1, x2, y2):
    mx = (x1 + x2) / 2.0
    seen = set()
    raw = []
    for d in _DELTAS:
        for base in (mx, x1, x2):
            bx = round(base + d, 3)
            if BRD_X1 <= bx <= BRD_X2 and bx not in seen:
                seen.add(bx)
                raw.append(bx)
    for bx in _BX_FIXED:
        if bx not in seen and BRD_X1 <= bx <= BRD_X2:
            seen.add(bx)
            raw.append(bx)
    lo, hi = min(x1, x2), max(x1, x2)
    raw.sort(key=lambda v: (0 if lo <= v <= hi else 1, abs(v - mx)))
    return raw


def _by_candidates(x1, y1, x2, y2):
    my = (y1 + y2) / 2.0
    seen = set()
    raw = []
    for d in _DELTAS:
        for base in (my, y1, y2):
            by = round(base + d, 3)
            if BRD_Y1 <= by <= BRD_Y2 and by not in seen:
                seen.add(by)
                raw.append(by)
    for by in _BY_FIXED:
        if by not in seen and BRD_Y1 <= by <= BRD_Y2:
            seen.add(by)
            raw.append(by)
    lo, hi = min(y1, y2), max(y1, y2)
    raw.sort(key=lambda v: (0 if lo <= v <= hi else 1, abs(v - my)))
    return raw


# ── Routing primitives (all on ROUTE_LAYER = F.Cu only) ──────────────────────

def _segs_ok(segs, net, hw, pdb, segdb):
    """Return True if every segment in *segs* passes both pdb and segdb."""
    return all(
        pdb.ok(a, b, c, d, net, hw) and segdb.ok(a, b, c, d, net, ROUTE_LAYER)
        for a, b, c, d in segs
    )


def _place_segs(board, nobj, segs, w, segdb):
    for a, b, c, d in segs:
        _add(board, nobj, a, b, c, d, w, ROUTE_LAYER, segdb)


def _try_2seg(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb):
    """2-segment L-shape — H-first and V-first."""
    hw = w / 2.0
    for cx, cy in ((x2, y1), (x1, y2)):
        segs = [(x1, y1, cx, cy), (cx, cy, x2, y2)]
        if _segs_ok(segs, net, hw, pdb, segdb):
            _place_segs(board, nobj, segs, w, segdb)
            return True
    return False


def _try_3bx(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb):
    """3-seg U via bypass-x: (x1,y1)→(bx,y1)→(bx,y2)→(x2,y2)."""
    hw = w / 2.0
    for bx in _bx_candidates(x1, y1, x2, y2):
        segs = [(x1, y1, bx, y1), (bx, y1, bx, y2), (bx, y2, x2, y2)]
        if _segs_ok(segs, net, hw, pdb, segdb):
            _place_segs(board, nobj, segs, w, segdb)
            return True
    return False


def _try_3by(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb):
    """3-seg U via bypass-y: (x1,y1)→(x1,by)→(x2,by)→(x2,y2)."""
    hw = w / 2.0
    for by in _by_candidates(x1, y1, x2, y2):
        segs = [(x1, y1, x1, by), (x1, by, x2, by), (x2, by, x2, y2)]
        if _segs_ok(segs, net, hw, pdb, segdb):
            _place_segs(board, nobj, segs, w, segdb)
            return True
    return False


def _try_4seg(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb):
    """4-segment detour — H-V-H-V and V-H-V-H patterns.

    Caps candidate lists at 40 each to bound runtime.
    """
    hw = w / 2.0
    bxs = _bx_candidates(x1, y1, x2, y2)[:40]
    bys = _by_candidates(x1, y1, x2, y2)[:40]

    # H-V-H-V: (x1,y1)→(bx,y1)→(bx,by)→(x2,by)→(x2,y2)
    for bx in bxs:
        for by in bys:
            segs = [(x1, y1, bx, y1), (bx, y1, bx, by),
                    (bx, by, x2, by), (x2, by, x2, y2)]
            if _segs_ok(segs, net, hw, pdb, segdb):
                _place_segs(board, nobj, segs, w, segdb)
                return True

    # V-H-V-H: (x1,y1)→(x1,by)→(bx,by)→(bx,y2)→(x2,y2)
    for by in bys:
        for bx in bxs:
            segs = [(x1, y1, x1, by), (x1, by, bx, by),
                    (bx, by, bx, y2), (bx, y2, x2, y2)]
            if _segs_ok(segs, net, hw, pdb, segdb):
                _place_segs(board, nobj, segs, w, segdb)
                return True

    return False


# ── Power bus / spine routing ─────────────────────────────────────────────────

def _stub_to_h_bus(board, nobj, net, px, py, bus_y, w, pdb, segdb):
    """
    Connect pad at (px, py) to a horizontal bus at y = bus_y.
    Tries direct V-stub, then 3-seg bypass via an offset x.
    """
    if abs(py - bus_y) < 0.001:
        return True   # pad already on bus level

    hw = w / 2.0

    # Direct vertical stub
    if (pdb.ok(px, py, px, bus_y, net, hw) and
            segdb.ok(px, py, px, bus_y, net, ROUTE_LAYER)):
        _add(board, nobj, px, py, px, bus_y, w, ROUTE_LAYER, segdb)
        return True

    # 3-seg via offset x: (px,py)→(ox,py)→(ox,bus_y)→(px,bus_y)
    for ox in _bx_candidates(px, py, px, bus_y):
        segs = [(px, py, ox, py), (ox, py, ox, bus_y), (ox, bus_y, px, bus_y)]
        if _segs_ok(segs, net, hw, pdb, segdb):
            _place_segs(board, nobj, segs, w, segdb)
            return True

    return False


def _stub_to_v_bus(board, nobj, net, px, py, bus_x, w, pdb, segdb):
    """
    Connect pad at (px, py) to a vertical bus at x = bus_x.
    Tries direct H-stub, then 3-seg bypass via an offset y.
    """
    if abs(px - bus_x) < 0.001:
        return True   # pad already on bus line

    hw = w / 2.0

    # Direct horizontal stub
    if (pdb.ok(px, py, bus_x, py, net, hw) and
            segdb.ok(px, py, bus_x, py, net, ROUTE_LAYER)):
        _add(board, nobj, px, py, bus_x, py, w, ROUTE_LAYER, segdb)
        return True

    # 3-seg via offset y: (px,py)→(px,oy)→(bus_x,oy)→(bus_x,py)
    for oy in _by_candidates(px, py, bus_x, py):
        segs = [(px, py, px, oy), (px, oy, bus_x, oy), (bus_x, oy, bus_x, py)]
        if _segs_ok(segs, net, hw, pdb, segdb):
            _place_segs(board, nobj, segs, w, segdb)
            return True

    return False


def _route_power_h_bus(board, nobj, net, pads, bus_y, w, pdb, segdb):
    """
    Route a power net using a horizontal bus at y = bus_y.

    1. Place the bus from x_min to x_max of all pad x-coordinates (checked).
    2. Route a stub from each pad to the bus level (checked).
    3. Connect each stub's bus-level endpoint to the next one with a short
       horizontal segment (checked).
    """
    hw = w / 2.0
    sorted_pads = sorted(pads, key=lambda p: p[1])   # sort by x
    xs = [px for _, px, _ in sorted_pads]

    # Place bus segments between consecutive x-positions (checked individually)
    bus_points = []
    for i in range(len(xs) - 1):
        sx1, sx2 = xs[i], xs[i + 1]
        if (pdb.ok(sx1, bus_y, sx2, bus_y, net, hw) and
                segdb.ok(sx1, bus_y, sx2, bus_y, net, ROUTE_LAYER)):
            _add(board, nobj, sx1, bus_y, sx2, bus_y, w, ROUTE_LAYER, segdb)
        else:
            print(f"    WARN bus segment blocked: {net} x=[{sx1:.2f},{sx2:.2f}] y={bus_y}")
        bus_points.extend([sx1, sx2])

    # Place stubs
    unrouted = 0
    for _, px, py in sorted_pads:
        ok = _stub_to_h_bus(board, nobj, net, px, py, bus_y, w, pdb, segdb)
        if not ok:
            print(f"    UNROUTED stub: {net} ({px:.3f},{py:.3f}) → y={bus_y}")
            unrouted += 1
    return unrouted


def _route_power_v_bus(board, nobj, net, pads, bus_x, w, pdb, segdb):
    """
    Route a power net using a vertical bus at x = bus_x.

    1. Place the spine from y_min to y_max of all pad y-coordinates (checked).
    2. Route a stub from each pad to the spine (checked).
    3. Connect each stub's spine-level endpoint vertically as needed.
    """
    hw = w / 2.0
    sorted_pads = sorted(pads, key=lambda p: p[2])   # sort by y
    ys = [py for _, _, py in sorted_pads]

    # Place spine segments between consecutive y-positions (checked)
    for i in range(len(ys) - 1):
        sy1, sy2 = ys[i], ys[i + 1]
        if (pdb.ok(bus_x, sy1, bus_x, sy2, net, hw) and
                segdb.ok(bus_x, sy1, bus_x, sy2, net, ROUTE_LAYER)):
            _add(board, nobj, bus_x, sy1, bus_x, sy2, w, ROUTE_LAYER, segdb)
        else:
            print(f"    WARN spine segment blocked: {net} x={bus_x} y=[{sy1:.2f},{sy2:.2f}]")

    # Place stubs
    unrouted = 0
    for _, px, py in sorted_pads:
        ok = _stub_to_v_bus(board, nobj, net, px, py, bus_x, w, pdb, segdb)
        if not ok:
            print(f"    UNROUTED stub: {net} ({px:.3f},{py:.3f}) → x={bus_x}")
            unrouted += 1
    return unrouted


# ── Main per-edge router ──────────────────────────────────────────────────────

def _route_edge(board, nobj, r1, p1, r2, p2, w, net, pdb, segdb):
    """
    Route one MST edge using progressively more complex bypass shapes.

    Returns True if routed, False if left UNROUTED.
    No track is placed when returning False — unrouted is better than crossing.
    """
    x1, y1 = p1
    x2, y2 = p2

    if (_try_2seg(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb) or
            _try_3bx(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb) or
            _try_3by(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb) or
            _try_4seg(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb)):
        return True

    print(f"    UNROUTED: {r1}({x1:.3f},{y1:.3f}) ↔ {r2}({x2:.3f},{y2:.3f})")
    return False


# ── Track stripper ────────────────────────────────────────────────────────────

def _strip_tracks_from_file(path):
    """
    Remove all (segment …) and (via …) s-expression blocks from the PCB file
    using text processing, avoiding pcbnew board.Remove() crashes.
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    out = []
    skip = 0
    for line in lines:
        stripped = line.lstrip()
        if skip == 0:
            if stripped.startswith("(segment") or stripped.startswith("(via"):
                skip = stripped.count("(") - stripped.count(")")
                if skip <= 0:
                    skip = 0
                continue
            out.append(line)
        else:
            skip += line.count("(") - line.count(")")
            if skip <= 0:
                skip = 0
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Stripping existing tracks from {PCB_PATH} …")
    _strip_tracks_from_file(PCB_PATH)

    print(f"Loading {PCB_PATH} …")
    board = pcbnew.LoadBoard(PCB_PATH)

    pdb   = PadDB(board)
    segdb = SegDB()

    # ── Collect pad positions per net ──────────────────────────────────────────
    net_pads = {}   # net_name → [(ref.pad, x, y), …]
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            pos = pad.GetPosition()
            x = pcbnew.ToMM(pos.x)
            y = pcbnew.ToMM(pos.y)
            net = pad.GetNetname()
            if net == "" or net.startswith("unconnected"):
                continue
            key = f"{ref}.{pad.GetNumber()}"
            net_pads.setdefault(net, []).append((key, x, y))

    total_routed   = 0
    total_unrouted = 0
    W_PWR = 0.6
    W_SIG = 0.4

    # ── 1. Power nets — spine / bus routing ───────────────────────────────────
    # Order matters: GND first (largest net, sets baseline density),
    # then the others.  Each net's segments are in segdb before the next starts.
    power_spine_order = [
        ("GND",   "h_bus", GND_BUS_Y),
        ("+12V",  "v_bus", V12_BUS_X),
        ("+5V",   "h_bus", V5_BUS_Y),
        ("+3V3",  "v_bus", V3V3_BUS_X),
    ]

    for net_name, kind, coord in power_spine_order:
        if net_name not in net_pads:
            continue
        pads = net_pads[net_name]
        nobj = board.FindNet(net_name)
        if nobj is None:
            print(f"  WARNING: net '{net_name}' not found in board netlist")
            continue
        print(f"  {net_name:22s}  {len(pads):2d} pads  {W_PWR} mm  "
              f"[{'H-bus' if kind == 'h_bus' else 'V-spine'}]")
        if kind == "h_bus":
            u = _route_power_h_bus(board, nobj, net_name, pads, coord,
                                   W_PWR, pdb, segdb)
        else:
            u = _route_power_v_bus(board, nobj, net_name, pads, coord,
                                   W_PWR, pdb, segdb)
        total_unrouted += u

    # BOOST_SW — MST + bypass (too few pads / geometry varies)
    if "BOOST_SW" in net_pads:
        pads  = net_pads["BOOST_SW"]
        nobj  = board.FindNet("BOOST_SW")
        if nobj and len(pads) >= 2:
            print(f"  {'BOOST_SW':22s}  {len(pads):2d} pads  {W_PWR} mm  [MST]")
            pts  = [(x, y) for _, x, y in pads]
            refs = [r       for r, _, _ in pads]
            for i, j in _prim_mst(pts):
                ok = _route_edge(board, nobj,
                                 refs[i], pts[i], refs[j], pts[j],
                                 W_PWR, "BOOST_SW", pdb, segdb)
                if ok:
                    total_routed += 1
                else:
                    total_unrouted += 1

    # ── 2. Signal nets — MST + bypass routing ────────────────────────────────
    for net_name in sorted(net_pads.keys()):
        if net_name in POWER_NETS:
            continue
        pads = net_pads[net_name]
        if len(pads) < 2:
            continue
        nobj = board.FindNet(net_name)
        if nobj is None:
            print(f"  WARNING: net '{net_name}' not found in board netlist")
            continue
        print(f"  {net_name:22s}  {len(pads):2d} pads  {W_SIG} mm")
        pts  = [(x, y) for _, x, y in pads]
        refs = [r       for r, _, _ in pads]
        for i, j in _prim_mst(pts):
            ok = _route_edge(board, nobj,
                             refs[i], pts[i], refs[j], pts[j],
                             W_SIG, net_name, pdb, segdb)
            if ok:
                total_routed += 1
            else:
                total_unrouted += 1

    print(f"\n{'─'*55}")
    print(f"  Edges routed   : {total_routed}")
    print(f"  Edges unrouted : {total_unrouted}")
    print(f"{'─'*55}")
    print(f"Saving to {PCB_PATH} …")
    board.Save(PCB_PATH)
    print("Done.")


if __name__ == "__main__":
    main()
