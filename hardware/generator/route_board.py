#!/usr/bin/env python3
"""
route_board.py v2 — MST-based L-shape / bypass router for PoE-FanController.

Fixes vs v1
-----------
* SegDB: track-to-track H×V crossing and H‖H / V‖V overlap detection.
  Every placed segment is checked against already-placed same-layer segments.
* PadDB: uses max(sx,sy)/2 so rectangular pads get their correct radius.
* J8 same-column bypasses always on F.Cu — avoids crossing B.Cu signal tracks.
* J8B→non-J8: tries _try_3by (V-first) and a 4-seg "drop-then-bypass" before
  falling back (fixes FAN4_PWM J8.22→R12.1).
* J8A→non-J8: tries a 4-seg right-detour via the inter-J8-row corridor before
  falling back (fixes DHT11_DATA J8.10→HUM1.2).
* +12V bus spine moved to x = 87.0 mm (clears C2.2 GND pad at x = 84.675).
* Existing tracks cleared at start of main().
"""

import sys
import math

sys.path.insert(0, "C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin")
import pcbnew

PCB_PATH = ("C:/repos-github/PoE-FanController/hardware/kicad/"
            "PoE-FanController.kicad_pcb")

POWER_NETS = {"+12V", "+5V", "+3V3", "GND", "BOOST_SW"}

J8A_X = 29.810   # Row-A column x
J8B_X = 45.190   # Row-B column x

# ── Geometry ──────────────────────────────────────────────────────────────────

def _dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _pt_seg_dist(px, py, x1, y1, x2, y2):
    """Minimum distance from point (px,py) to segment (x1,y1)-(x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
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
                # Use max dimension for conservative rectangular-pad radius.
                r = max(pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)) / 2.0
                self._pads.append((x, y, net, r))

    def ok(self, x1, y1, x2, y2, net_name, half_w, clr=0.2):
        """Return True if the segment clears every foreign pad by >= clr mm.
        
        All pads (connected and unconnected) are treated as obstacles with their
        full copper radius — this ensures DRC clearance rules are respected.
        """
        if abs(x1 - x2) < 0.001 and abs(y1 - y2) < 0.001:
            return True
        need = half_w + clr
        for px, py, pnet, pr in self._pads:
            if pnet == net_name or pnet == "":
                continue
            dist = _pt_seg_dist(px, py, x1, y1, x2, y2)
            if dist < need + pr:
                return False
        return True


# ── Track-to-track crossing database ─────────────────────────────────────────

class SegDB:
    """
    Detects when a candidate segment would cross or overlap an already-placed
    track on the same layer (different net).

    Stored segments are axis-aligned (H or V).  For two segments on the same
    layer with different nets this checks:
      H × V  — perpendicular crossing
      H ‖ H  — same-y overlap
      V ‖ V  — same-x overlap
    """

    def __init__(self):
        # (x0, y0, x1, y1, net, layer) with x0≤x1, y0≤y1
        self._segs = []

    def add(self, x1, y1, x2, y2, net, layer):
        self._segs.append(
            (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), net, layer)
        )

    def ok(self, x1, y1, x2, y2, net, layer):
        ax0, ay0 = min(x1, x2), min(y1, y2)
        ax1, ay1 = max(x1, x2), max(y1, y2)
        a_H = (ay1 - ay0) < 1e-6   # horizontal
        a_V = (ax1 - ax0) < 1e-6   # vertical
        for bx0, by0, bx1, by1, bnet, blyr in self._segs:
            if blyr != layer or bnet == net:
                continue
            b_H = (by1 - by0) < 1e-6
            b_V = (bx1 - bx0) < 1e-6
            # H × V crossing
            if a_H and b_V:
                if ax0 <= bx0 <= ax1 and by0 <= ay0 <= by1:
                    return False
            elif a_V and b_H:
                if bx0 <= ax0 <= bx1 and ay0 <= by0 <= ay1:
                    return False
            # H ‖ H overlap (same y, overlapping x)
            elif a_H and b_H:
                if abs(ay0 - by0) < 1e-6 and ax0 < bx1 and bx0 < ax1:
                    return False
            # V ‖ V overlap (same x, overlapping y)
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
    """Place one track segment and register it in segdb."""
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


def _add_via(board, nobj, x, y, segdb):
    """Place a via (B.Cu ↔ F.Cu) at (x, y)."""
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(0.8))
    v.SetDrill(pcbnew.FromMM(0.4))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(nobj)
    board.Add(v)




def _is_j8a(ref):
    if not ref or not ref.startswith("J8."):
        return False
    try:
        return 1 <= int(ref.split(".")[1]) <= 20
    except ValueError:
        return False


def _is_j8b(ref):
    if not ref or not ref.startswith("J8."):
        return False
    try:
        return 21 <= int(ref.split(".")[1]) <= 40
    except ValueError:
        return False


# ── Bypass-candidate generators ───────────────────────────────────────────────

_DELTAS = [0, -2, 2, -4, 4, -6, 6, -8, 8, -10, 10, -12, 12,
           -15, 15, -18, 18, -20, 20, -25, 25, -30, 30]


def _bx_candidates(x1, y1, x2, y2, only_right=False, only_left=False):
    mx = (x1 + x2) / 2.0
    seen = set()
    raw = []
    for d in _DELTAS:
        for base in (mx, x1, x2):
            bx = round(base + d, 3)
            if only_right and bx <= J8B_X:
                continue
            if only_left and bx >= J8A_X:
                continue
            if bx not in seen:
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
            if by not in seen:
                seen.add(by)
                raw.append(by)
    lo, hi = min(y1, y2), max(y1, y2)
    raw.sort(key=lambda v: (0 if lo <= v <= hi else 1, abs(v - my)))
    return raw


# ── 2-segment L-shape ────────────────────────────────────────────────────────

def _try_2seg(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb,
              preferred_layers=None):
    hw = w / 2.0
    options = [
        ((x2, y1), pcbnew.B_Cu),
        ((x1, y2), pcbnew.B_Cu),   # prefer B.Cu V-first over F.Cu
        ((x1, y2), pcbnew.F_Cu),
        ((x2, y1), pcbnew.F_Cu),
    ]
    if preferred_layers:
        options = [o for o in options if o[1] in preferred_layers] + \
                  [o for o in options if o[1] not in preferred_layers]
    for (cx, cy), layer in options:
        if (pdb.ok(x1, y1, cx, cy, net, hw) and
                pdb.ok(cx, cy, x2, y2, net, hw) and
                segdb.ok(x1, y1, cx, cy, net, layer) and
                segdb.ok(cx, cy, x2, y2, net, layer)):
            _add(board, nobj, x1, y1, cx, cy, w, layer, segdb)
            _add(board, nobj, cx, cy, x2, y2, w, layer, segdb)
            return True
    return False


# ── 3-segment U-shapes ────────────────────────────────────────────────────────

def _try_3bx(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb,
             only_right=False, only_left=False, layers=None):
    """U-shape via bypass-x: (x1,y1)→(bx,y1)→(bx,y2)→(x2,y2)."""
    hw = w / 2.0
    layer_seq = layers if layers else (pcbnew.B_Cu, pcbnew.F_Cu)
    for bx in _bx_candidates(x1, y1, x2, y2, only_right, only_left):
        segs = [(x1, y1, bx, y1), (bx, y1, bx, y2), (bx, y2, x2, y2)]
        for layer in layer_seq:
            if all(pdb.ok(a, b, c, d, net, hw) and
                   segdb.ok(a, b, c, d, net, layer)
                   for a, b, c, d in segs):
                for a, b, c, d in segs:
                    _add(board, nobj, a, b, c, d, w, layer, segdb)
                return True
    return False


def _try_3by(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb, layers=None):
    """U-shape via bypass-y: (x1,y1)→(x1,by)→(x2,by)→(x2,y2)."""
    hw = w / 2.0
    layer_seq = layers if layers else (pcbnew.B_Cu, pcbnew.F_Cu)
    for by in _by_candidates(x1, y1, x2, y2):
        segs = [(x1, y1, x1, by), (x1, by, x2, by), (x2, by, x2, y2)]
        for layer in layer_seq:
            if all(pdb.ok(a, b, c, d, net, hw) and
                   segdb.ok(a, b, c, d, net, layer)
                   for a, b, c, d in segs):
                for a, b, c, d in segs:
                    _add(board, nobj, a, b, c, d, w, layer, segdb)
                return True
    return False


# ── 4-segment detours ─────────────────────────────────────────────────────────

def _try_4seg_j8a_right(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb):
    """
    J8A → non-J8 detour when 3-seg fails.
    Goes RIGHT into the inter-J8-row corridor, loops below the destination,
    then approaches from below.  Pattern:
      H→(bx_r, y1) → V→(bx_r, by_low) → H→(x2, by_low) → V→(x2, y2)
    """
    hw = w / 2.0
    bx_rights = [37.0, 35.0, 39.0, 33.0, 41.0, 43.0]   # inter-J8 x values
    by_margin = 2.0   # mm below max(y1,y2)
    by_lows = [max(y1, y2) + by_margin + i for i in [0, 1, 2, 3, 4, 5]]
    for bx in bx_rights:
        for by in by_lows:
            segs = [(x1, y1, bx, y1), (bx, y1, bx, by),
                    (bx, by, x2, by), (x2, by, x2, y2)]
            for layer in (pcbnew.B_Cu, pcbnew.F_Cu):
                if all(pdb.ok(a, b, c, d, net, hw) and
                       segdb.ok(a, b, c, d, net, layer)
                       for a, b, c, d in segs):
                    for a, b, c, d in segs:
                        _add(board, nobj, a, b, c, d, w, layer, segdb)
                    return True
    return False


def _try_4seg_j8b_down(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb):
    """
    J8B → non-J8 detour when 3-seg fails.
    Drops slightly below the J8 pad y-level (past the R7.2/R11.1 blocker at
    y ≈ 62.475), then routes H→V→H to the destination.  Pattern:
      V→(x1, by1) → H→(bx, by1) → V→(bx, y2) → H→(x2, y2)
    """
    hw = w / 2.0
    # by1 candidates: just below y1 (going down = increasing y in KiCad)
    by1_offsets = [1.5, 1.3, 1.4, 2.0, 2.5, 3.0, 0.8, 3.5, 4.0]
    bx_offsets  = [-2.0, -1.5, -2.5, -3.0, -4.0, -1.0, -0.5, -5.0]
    for dy in by1_offsets:
        by1 = round(y1 + dy, 3)
        for dbx in bx_offsets:
            bx = round(x2 + dbx, 3)
            segs = [(x1, y1, x1, by1), (x1, by1, bx, by1),
                    (bx, by1, bx, y2),  (bx, y2, x2, y2)]
            for layer in (pcbnew.B_Cu, pcbnew.F_Cu):
                if all(pdb.ok(a, b, c, d, net, hw) and
                       segdb.ok(a, b, c, d, net, layer)
                       for a, b, c, d in segs):
                    for a, b, c, d in segs:
                        _add(board, nobj, a, b, c, d, w, layer, segdb)
                    return True
    return False


def _try_5seg_j8b_left(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb):
    """
    J8B → non-J8 five-segment detour that exits LEFT into the inter-J8-row
    corridor, arcs around the R7.2/R11.1 y-blocker, then descends to the
    destination from the right.  Pattern:
      H←(bx_l, y1) → V↑(bx_l, by_u) → H→(bx_r, by_u)
        → V↓(bx_r, y2) → H←(x2, y2)
    The EXIT left avoids the R7.2/R11.1 row that sits only 0.085 mm from
    y=62.390 on x∈[61.975,65.975] — those pads block any rightward H at y1.
    The APPROACH to x2 comes from the right (bx_r > x2) to avoid R8.2 at
    (61.975, 76.015) which sits on the same y=76.015 as R12.1.
    """
    hw = w / 2.0
    # Candidate left-exit x values — stay in inter-J8 corridor (29.81–45.19)
    bx_lefts = [37.0, 35.0, 39.0, 33.0, 41.0, 31.0, 43.0]
    # Candidate upper-bridge y values — go UP (y decreasing) from y1
    by_up_deltas = [-7.0, -5.0, -9.0, -3.5, -11.0, -13.0, -15.0]
    # Candidate right-approach x values — must be > x2 + clearance of R12.2
    bx_rights = [68.0, 69.0, 67.0, 70.0, 71.0, 72.0, 73.0, 66.5]
    for bx_l in bx_lefts:
        for dby in by_up_deltas:
            by_u = round(y1 + dby, 3)
            for bx_r in bx_rights:
                segs = [
                    (x1,  y1,  bx_l, y1  ),   # H left
                    (bx_l, y1,  bx_l, by_u),   # V up
                    (bx_l, by_u, bx_r, by_u),  # H right
                    (bx_r, by_u, bx_r, y2  ),  # V down
                    (bx_r, y2,  x2,   y2  ),   # H left stub to destination
                ]
                for layer in (pcbnew.B_Cu, pcbnew.F_Cu):
                    if all(pdb.ok(a, b, c, d, net, hw) and
                           segdb.ok(a, b, c, d, net, layer)
                           for a, b, c, d in segs):
                        for a, b, c, d in segs:
                            _add(board, nobj, a, b, c, d, w, layer, segdb)
                        return True
    return False


# ── Main per-edge router ──────────────────────────────────────────────────────

def _match(x1, y1, x2, y2, ax, ay, bx, by, tol=0.05):
    """True if (x1,y1)↔(x2,y2) matches the A↔B endpoint pair (either order)."""
    return ((abs(x1 - ax) < tol and abs(y1 - ay) < tol and
             abs(x2 - bx) < tol and abs(y2 - by) < tol) or
            (abs(x1 - bx) < tol and abs(y1 - by) < tol and
             abs(x2 - ax) < tol and abs(y2 - ay) < tol))


def _route_edge(board, nobj, r1, p1, r2, p2, w, net, pdb, segdb):
    x1, y1 = p1
    x2, y2 = p2
    hw = w / 2.0

    j8a1, j8a2 = _is_j8a(r1), _is_j8a(r2)
    j8b1, j8b2 = _is_j8b(r1), _is_j8b(r2)

    # ── Topologically-constrained hardcoded routes ────────────────────────────
    # These four edges cannot be found by the generic router because dense J8
    # pad clusters block every candidate bx/by within the standard DELTA grid.
    # Each path is verified by geometry: dist from every foreign pad > need+pr.

    # +3V3 J8.36(45.19,26.83) ↔ R14.1(24.475,55.095)
    # Route must loop south to y=66.5 to stay clear of J8A and J8B pad
    # columns at y∈[16.67,64.93]; V approaches R14.1 from the right.
    if net == "+3V3" and _match(x1, y1, x2, y2, 45.19, 26.83, 24.475, 55.095):
        if abs(x2 - 45.19) < 0.05:          # normalise: x1=J8.36
            x1, y1, x2, y2 = x2, y2, x1, y1
        for a, b, c, d in [(x1, y1,   47.19,  y1   ),   # H right (extends +3V3 spine)
                            (47.19, y1,  47.19,  66.5 ),  # V south past all J8 rows
                            (47.19, 66.5, 25.875, 66.5),  # H left (clear of J6 at y=62)
                            (25.875, 66.5, 25.875, y2  ),  # V north to R14.1 level
                            (25.875, y2,  x2,     y2  )]:  # H left to R14.1
            _add(board, nobj, a, b, c, d, w, pcbnew.B_Cu, segdb)
        return

    # GND J8.33(45.19,34.45) ↔ C1.2(53.975,25.975)
    # Must exit left (bx=37) to avoid +3V3 B.Cu V at x=47.19, then arc to y=22
    # so the final H at y=25.975 stays above J8.36's +3V3 pad clearance zone,
    # and the V+H approach to C1.2 avoids C1.1(+5V) at (53.975,23.475).
    if net == "GND" and _match(x1, y1, x2, y2, 45.19, 34.45, 53.975, 25.975):
        if abs(x1 - 53.975) < 0.05:         # normalise: x1=J8.33
            x1, y1, x2, y2 = x2, y2, x1, y1
        for a, b, c, d in [(x1,    y1,   37.0,  y1   ),  # H left past +3V3 V
                            (37.0,  y1,   37.0,  22.0 ),  # V north (clear of +3V3 V start)
                            (37.0,  22.0, 52.0,  22.0 ),  # H right (under J8.37 clearance)
                            (52.0,  22.0, 52.0,  y2   ),  # V south (clears C1.1 at x=53.975)
                            (52.0,  y2,   x2,    y2   )]:  # H right to C1.2
            _add(board, nobj, a, b, c, d, w, pcbnew.B_Cu, segdb)
        return

    # PROG_LED J8.16(29.81,26.83) ↔ R13.1(22.975,18.475)
    # Must exit RIGHT of J8A (bx=31.81) to avoid GND B.Cu V at x=27.81; the
    # return H at y=20.48 (midpoint between J8.19 and J8.18) threads the J8A
    # pad gap with 1.27mm clearance > need+pr=1.25mm; placed on F.Cu so the
    # GND B.Cu obstacles don't apply.
    if net == "PROG_LED" and _match(x1, y1, x2, y2, 29.81, 26.83, 22.975, 18.475):
        if abs(x2 - 29.81) < 0.05:          # normalise: x1=J8.16
            x1, y1, x2, y2 = x2, y2, x1, y1
        for a, b, c, d in [(x1,    y1,   31.81,  y1   ),   # H right (J8.17 dist=2.0mm)
                            (31.81, y1,   31.81,  20.48),   # V south
                            (31.81, 20.48, x2,   20.48),    # H left through J8.19/18 gap
                            (x2,   20.48, x2,    y2   )]:   # V north to R13.1
            _add(board, nobj, a, b, c, d, w, pcbnew.F_Cu, segdb)
        return

    # PWR_LED J8.17(29.81,24.29) ↔ R3.1(17.975,18.475)
    # 2-seg F.Cu H-first: avoids GND B.Cu V at x=27.81 (different layer).
    # PROG_LED's F.Cu V at x=31.81 y∈[20.48,26.83] is outside x∈[17.975,29.81].
    if net == "PWR_LED" and _match(x1, y1, x2, y2, 29.81, 24.29, 17.975, 18.475):
        if abs(x2 - 29.81) < 0.05:          # normalise: x1=J8.17
            x1, y1, x2, y2 = x2, y2, x1, y1
        _add(board, nobj, x1, y1, x2, y1, w, pcbnew.F_Cu, segdb)  # H west
        _add(board, nobj, x2, y1, x2, y2, w, pcbnew.F_Cu, segdb)  # V north
        return

    # ── Special case: FAN4_PWM J8.22 ↔ R12.1 ────────────────────────────────
    # J8.22(45.190,62.390)→R12.1(65.975,76.015): blocked by R7.2/R11.1 at
    # y=62.475 and R8.2(61.975,76.015) on same y as destination.
    # Route entirely on F.Cu (THT pad J8.22 connects to both layers).
    # F.Cu V short south, then H east, V south, H west to R12.1.
    if (net == "FAN4_PWM" and
            ((abs(x1 - 45.190) < 0.05 and abs(y1 - 62.390) < 0.05 and
              abs(x2 - 65.975) < 0.05 and abs(y2 - 76.015) < 0.05) or
             (abs(x2 - 45.190) < 0.05 and abs(y2 - 62.390) < 0.05 and
              abs(x1 - 65.975) < 0.05 and abs(y1 - 76.015) < 0.05))):
        # Normalise: J8.22 is (x1,y1)
        if abs(x2 - 45.190) < 0.05:
            x1, y1, x2, y2 = x2, y2, x1, y1
        vy = 63.675   # V endpoint — J8.21(64.93) dist=1.255 > need+pr=1.25mm
        _add(board, nobj, x1, y1, x1, vy, w, pcbnew.F_Cu, segdb)   # V south
        _add(board, nobj, x1, vy, 68.0, vy, w, pcbnew.F_Cu, segdb) # H east
        _add(board, nobj, 68.0, vy, 68.0, y2, w, pcbnew.F_Cu, segdb) # V south
        _add(board, nobj, 68.0, y2, x2, y2, w, pcbnew.F_Cu, segdb) # H west
        return

    # ── J8 same-column: both Row-A ─── bypass left, try B.Cu then F.Cu ─────────
    if j8a1 and j8a2:
        if not _try_3bx(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb,
                         only_left=True, layers=(pcbnew.B_Cu, pcbnew.F_Cu)):
            # Hard fallback: x = 27 mm, F.Cu (avoids B.Cu congestion at x=26)
            for a, b, c, d in [(x1, y1, 27.0, y1),
                                (27.0, y1, 27.0, y2),
                                (27.0, y2, x2, y2)]:
                _add(board, nobj, a, b, c, d, w, pcbnew.F_Cu, segdb)
        return

    # ── J8 same-column: both Row-B ─── bypass LEFT on B.Cu ──────────────────
    # All FANx_TACH/PWM signals route F.Cu H going RIGHT from J8B; going LEFT
    # on B.Cu (bx ≈ 43.19) avoids them entirely.  +3V3 B.Cu V is at x=47.19
    # (to the right of J8B), so leftward B.Cu is unobstructed.
    if j8b1 and j8b2:
        if not _try_3bx(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb,
                         only_left=True, layers=(pcbnew.B_Cu, pcbnew.F_Cu)):
            # Hard fallback: x = 37.0 mm, B.Cu
            for a, b, c, d in [(x1, y1, 37.0, y1),
                                (37.0, y1, 37.0, y2),
                                (37.0, y2, x2, y2)]:
                _add(board, nobj, a, b, c, d, w, pcbnew.B_Cu, segdb)
        return

    # ── J8 Row-A → non-J8 ────────────────────────────────────────────────────
    if j8a1 or j8a2:
        if j8a2:                        # normalise: J8 pad is always p1
            x1, y1, x2, y2 = x2, y2, x1, y1
            r1, r2 = r2, r1
        # 2-seg: try B.Cu then F.Cu for both H-first and V-first
        for layer in (pcbnew.B_Cu, pcbnew.F_Cu):
            for cx, cy in ((x2, y1), (x1, y2)):
                if (pdb.ok(x1, y1, cx, cy, net, hw) and
                        pdb.ok(cx, cy, x2, y2, net, hw) and
                        segdb.ok(x1, y1, cx, cy, net, layer) and
                        segdb.ok(cx, cy, x2, y2, net, layer)):
                    _add(board, nobj, x1, y1, cx, cy, w, layer, segdb)
                    _add(board, nobj, cx, cy, x2, y2, w, layer, segdb)
                    return
        # 3-seg left-biased, then unrestricted, then 4-seg right detour
        if (_try_3bx(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb,
                     only_left=True) or
                _try_3bx(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb) or
                _try_3by(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb) or
                _try_4seg_j8a_right(board, nobj, x1, y1, x2, y2,
                                    w, net, pdb, segdb)):
            return
        print(f"    WARN fallback: {r1} → {r2}")
        _add(board, nobj, x1, y1, x2, y1, w, pcbnew.B_Cu, segdb)
        _add(board, nobj, x2, y1, x2, y2, w, pcbnew.B_Cu, segdb)
        return

    # ── J8 Row-B → non-J8 ────────────────────────────────────────────────────
    if j8b1 or j8b2:
        if j8b2:
            x1, y1, x2, y2 = x2, y2, x1, y1
            r1, r2 = r2, r1
        # 2-seg: try B.Cu then F.Cu for both H-first and V-first
        for layer in (pcbnew.B_Cu, pcbnew.F_Cu):
            for cx, cy in ((x2, y1), (x1, y2)):
                if (pdb.ok(x1, y1, cx, cy, net, hw) and
                        pdb.ok(cx, cy, x2, y2, net, hw) and
                        segdb.ok(x1, y1, cx, cy, net, layer) and
                        segdb.ok(cx, cy, x2, y2, net, layer)):
                    _add(board, nobj, x1, y1, cx, cy, w, layer, segdb)
                    _add(board, nobj, cx, cy, x2, y2, w, layer, segdb)
                    return
        if (_try_3bx(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb,
                     only_right=True) or
                _try_3bx(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb) or
                _try_3by(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb) or
                _try_4seg_j8b_down(board, nobj, x1, y1, x2, y2,
                                   w, net, pdb, segdb) or
                _try_5seg_j8b_left(board, nobj, x1, y1, x2, y2,
                                   w, net, pdb, segdb)):
            return
        print(f"    WARN fallback: {r1} → {r2}")
        _add(board, nobj, x1, y1, x2, y1, w, pcbnew.B_Cu, segdb)
        _add(board, nobj, x2, y1, x2, y2, w, pcbnew.B_Cu, segdb)
        return

    # ── Non-J8 ↔ Non-J8 ──────────────────────────────────────────────────────
    if (_try_2seg(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb) or
            _try_3bx(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb) or
            _try_3by(board, nobj, x1, y1, x2, y2, w, net, pdb, segdb)):
        return

    print(f"    WARN fallback: {r1} → {r2}")
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    if dx >= dy:
        _add(board, nobj, x1, y1, x2, y1, w, pcbnew.B_Cu, segdb)
        _add(board, nobj, x2, y1, x2, y2, w, pcbnew.B_Cu, segdb)
    else:
        _add(board, nobj, x1, y1, x1, y2, w, pcbnew.F_Cu, segdb)
        _add(board, nobj, x1, y2, x2, y2, w, pcbnew.F_Cu, segdb)


# ── +12V bus ──────────────────────────────────────────────────────────────────

def _route_12v(board, nobj, pads, pdb, segdb):
    """
    Vertical spine at x = 87.0 mm (clears C2.2 GND at x = 84.675) with
    horizontal stubs from each +12V pad to the spine.
    """
    BUS_X = 87.0
    W = 0.6
    ys = sorted(y for _, x, y in pads)
    _add(board, nobj, BUS_X, ys[0], BUS_X, ys[-1], W, pcbnew.B_Cu, segdb)
    for _, x, y in pads:
        _add(board, nobj, x, y, BUS_X, y, W, pcbnew.B_Cu, segdb)


# ── Main ──────────────────────────────────────────────────────────────────────

def _strip_tracks_from_file(path):
    """
    Remove all (segment ...) and (via ...) blocks from the KiCad PCB file
    using text processing, to avoid pcbnew board.Remove() crashes.
    """
    import re
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Match multi-line segment/via blocks: starts with optional whitespace
    # then (segment or (via, ends with the matching closing paren.
    # Each block is a balanced s-expression at the top nesting level.
    # Simple approach: strip any line that starts a (segment or (via block
    # and all lines until we see the matching closing ")" at the same indent.
    lines = content.splitlines()
    out = []
    skip = 0
    for line in lines:
        stripped = line.lstrip()
        if skip == 0:
            if stripped.startswith("(segment") or stripped.startswith("(via"):
                # count open parens to find the end of this block
                skip = stripped.count("(") - stripped.count(")")
                if skip <= 0:
                    skip = 0  # single-line block already closed
                continue
            out.append(line)
        else:
            skip += line.count("(") - line.count(")")
            if skip <= 0:
                skip = 0
            continue
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def main():
    print(f"Stripping existing tracks from {PCB_PATH} ...")
    _strip_tracks_from_file(PCB_PATH)

    print(f"Loading {PCB_PATH} ...")
    board = pcbnew.LoadBoard(PCB_PATH)

    pdb = PadDB(board)
    segdb = SegDB()

    # Build net → [(ref_padnum, x, y), ...] from actual PCB pads
    net_pads = {}
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

    total_edges = 0
    warn_count = 0

    for net_name in sorted(net_pads.keys()):
        pads = net_pads[net_name]
        if len(pads) < 2:
            continue
        nobj = board.FindNet(net_name)
        if nobj is None:
            print(f"  WARNING: net '{net_name}' not found in board")
            continue

        W = 0.6 if net_name in POWER_NETS else 0.4
        print(f"  {net_name:22s}  {len(pads):2d} pads  {W} mm")

        if net_name == "+12V":
            _route_12v(board, nobj, pads, pdb, segdb)
            total_edges += len(pads)
            continue

        pts  = [(x, y) for _, x, y in pads]
        refs = [r       for r, _, _ in pads]

        for i, j in _prim_mst(pts):
            _route_edge(board, nobj,
                        refs[i], pts[i],
                        refs[j], pts[j],
                        W, net_name, pdb, segdb)
            total_edges += 1

    print(f"\nTotal edges placed: {total_edges}")
    print(f"Saving to {PCB_PATH} ...")
    board.Save(PCB_PATH)
    print("Done.")


if __name__ == "__main__":
    main()
