# Technical Plan: PCB Layout — Place All External Connectors on One Board Edge

**GitHub Issue:** #1 — "PCB layout: place all external connectors on one board edge"
**Feature path:** `docs/features/pcb-connector-edge/`
**Status:** Planning (v0.1 PCB — no footprints placed yet)
**Date:** 2026-06-06

---

## 1. Problem Statement and Goals

The v0.1 PCB currently carries placement guidance in `hardware/DESIGN.md` that assigns connectors to
three different board edges:

| Connector | Old guidance | Problem |
|-----------|-------------|---------|
| J1 RJ45 | Left edge (implied by horizontal footprint) | Cables exit a different face from fans |
| J2–J5 fan headers | Right edge | Perpendicular to J1 — conflicts with enclosure |
| J6 USB-C + U4 | Bottom edge | Third face — incompatible with panel mounting |

The result makes clean cable management and panel/enclosure mounting impossible.

**Goal:** Place every user-facing external connector — J1 (RJ45 PoE input), J2–J5 (4-wire fan
headers), and J6 (USB-C) — on the **top board edge at y = 5 mm**, spanning the full 90 mm board
width. This is the only edge that crosses both the primary (x < 38 mm) and secondary (x > 38 mm)
isolation domains, and therefore the only edge that can satisfy both the one-edge requirement and
the isolation constraint simultaneously.

J7 (3-pin debug UART header) is a non-user-facing programming/debug convenience connector. It is
placed on the **right board edge** (x = 95 mm), which is a documented exception to the
one-edge rule (see §8, Out of Scope and Exceptions).

---

## 2. Constraints (from `docs/constitution.md`)

| Ref | Rule | Value |
|-----|------|-------|
| P-HW-02 | Single-sided placement | All components on F.Cu top layer only |
| P-HW-03 | Single board-edge connector rule | All external connectors on top edge, y ≈ 5 mm |
| P-HW-04 | Fixed board outline | 90 × 70 mm, Edge.Cuts must not move |
| P-ISO-02 | Isolation barrier position | x = 38 mm; no copper may cross it |
| P-ISO-03 | Minimum creepage and clearance | ≥ 3.0 mm across isolation barrier |
| P-ISO-04 | PCB slot at barrier | Routed slot at x = 38 mm recommended |
| P-TEST-03 | Zero DRC errors | Clearance, unconnected nets, courtyard, footprint validity |
| P-KI-01 | KiCad version | 10.0.3 exclusively |
| §2.2 | BOM lock | Substitutions require MAJOR amendment |

The ground-pour zones defined in `PoE-FanController.kicad_pcb` (lines 73–82) already start at
x = 40 mm, leaving a 2 mm copper-free buffer around the barrier. Connector placement must not
introduce copper closer than 3.0 mm to x = 38 mm on either side.

---

## 3. Component Placement Zones Diagram (ASCII)

Board outline: x = 5 → 95 mm, y = 5 → 75 mm (90 × 70 mm, Edge.Cuts).
Top edge: y = 5 mm. Isolation barrier: x = 38 mm.

```
x=5          x=38                                                    x=95
 │            │ ISOLATION BARRIER (3 mm creepage each side)           │
 ▼            ▼                                                        ▼
┌─────────────┬──────────────────────────────────────────────────────┐  y=5  (TOP EDGE)
│             │                                                       │
│  PRIMARY    │  S E L V   S E C O N D A R Y   S I D E               │
│  PoE SIDE   │                                                       │
│  x=5..38    │  x=38..95                                            │
│  (33 mm)    │  (57 mm)                                             │
│             │                                                       │
│  [J1 RJ45]  │  [J2] [J3] [J4] [J5]  [J6]           [J7]→         │
│  ←21.3mm→  │  ←10.16→ each         ←9mm→      (right edge)       │
│             │                                                       │
│  [U1 Ag9905M]                                                       │
│             │  [U2 LM2596] [L1] [D1]                               │
│             │               [U3 ESP32]                             │
│             │               [U4 CH340C]                            │
└─────────────┴──────────────────────────────────────────────────────┘  y=75 (BOTTOM EDGE)
 x=5         x=38                                                    x=95

Legend:
  [Jn]  = connector footprint placed flush with top edge (y=5 mm)
  →     = J7 exits right edge (x=95 mm), secondary side only
  ├─── = isolation barrier; no copper within 3 mm either side
```

### Domain membership summary

| Connector | Domain | Board edge | Isolation zone |
|-----------|--------|-----------|----------------|
| J1 (RJ45) | Primary (PoE) | Top | x < 35 mm (≥ 3 mm from barrier) |
| J2–J5 (fan) | Secondary (SELV) | Top | x > 41 mm (≥ 3 mm from barrier) |
| J6 (USB-C) | Secondary (SELV) | Top | x > 41 mm |
| J7 (UART) | Secondary (SELV) | **Right** (exception) | y = 30–50 mm |

---

## 4. Top-Edge Spacing Analysis

### 4.1 Coordinate system

- Board left wall: x = 5 mm; board right wall: x = 95 mm
- Isolation barrier: x = 38 mm
- Minimum copper stand-off from barrier: 3.0 mm (P-ISO-03)
- Primary usable zone: x = 5 mm → x = 35 mm (barrier − 3 mm)
- Secondary usable zone: x = 41 mm (barrier + 3 mm) → x = 94.5 mm (0.5 mm from right wall)

### 4.2 Connector body widths

"Body width" = the footprint's lateral extent along the X axis when oriented to exit the top edge.
For pin headers this equals (pin count − 1) × pitch + 2 × 1.27 mm end-pad overhang.

| Ref | Footprint | Body width |
|-----|-----------|-----------|
| J1 | `RJ45_Amphenol_54602-x08_Horizontal` | 21.3 mm |
| J2–J5 | `PinHeader_1x04_P2.54mm_Vertical` | 10.16 mm each |
| J6 | `USB_C_Receptacle_GCT_USB4085` | 9.0 mm |
| J7 | `PinHeader_1x03_P2.54mm_Vertical` | 7.62 mm |

### 4.3 Primary-side fit check (J1)

```
Primary zone width:   35 − 5 = 30 mm usable (≥ 3 mm from barrier, ≥ 0 mm from left wall)
J1 body width:        21.3 mm
Centering margin:     (30 − 21.3) / 2 = 4.35 mm each side  ✓
J1 center X:          5 + 4.35 + 10.65 = 20.0 mm
J1 left edge copper:  20.0 − 10.65 = 9.35 mm  (> 5 mm board wall)  ✓
J1 right edge copper: 20.0 + 10.65 = 30.65 mm  (< 35 mm limit)     ✓
Gap to barrier:        38 − 30.65 = 7.35 mm  (> 3.0 mm P-ISO-03)   ✓
```

### 4.4 Secondary-side fit check (J2–J5 + J6)

Target: pack four fan headers and one USB-C receptacle between x = 41 mm and x = 94.5 mm (53.5 mm
of rail), with 0.5 mm inter-courtyard gaps (no DRC courtyard collision, practical assembly
clearance for vertical headers connected from above).

```
Calculation (left-edge → right-edge, step by step):

  Start x = 41.0 mm  (3.0 mm clearance from barrier)

  J2:  left=41.00   center=46.08   right=51.16   [10.16 mm body]
  gap: 0.5 mm
  J3:  left=51.66   center=56.74   right=61.82   [10.16 mm body]
  gap: 0.5 mm
  J4:  left=62.32   center=67.40   right=72.48   [10.16 mm body]
  gap: 0.5 mm
  J5:  left=72.98   center=78.06   right=83.14   [10.16 mm body]
  gap: 0.5 mm
  J6:  left=83.64   center=88.14   right=92.64   [9.00 mm body]

  Right edge of J6:  92.64 mm
  Board right wall:  95.0 mm
  Copper-to-edge clearance: 95.0 − 92.64 = 2.36 mm  (> 0.5 mm minimum)  ✓

  Total rail consumed: 92.64 − 41.0 = 51.64 mm
  Total rail available:                53.5 mm
  Margin:                               1.86 mm  ✓
```

### 4.5 Proposed X centre positions (to be implemented in KiCad)

Snap to 0.1 mm grid for clarity; exact placement on 0.1 mm grid or finer per P-HW-06.

| Ref | X centre (mm) | Y (body flush with top edge) | Notes |
|-----|--------------|------------------------------|-------|
| J1  | 20.0 | y ≈ 5 + (depth/2) | Rotate 90° CW so port faces +Y (up/out) |
| J2  | 46.1 | y ≈ 5 + (depth/2) | Vertical; pin 1 nearest barrier |
| J3  | 56.8 | y ≈ 5 + (depth/2) | Vertical |
| J4  | 67.4 | y ≈ 5 + (depth/2) | Vertical |
| J5  | 78.1 | y ≈ 5 + (depth/2) | Vertical |
| J6  | 88.1 | y ≈ 5 + (depth/2) | Through-hole; verify edge clearance per §5.3 |
| J7  | x = 95 (right edge) | y ≈ 40.0 | Right edge, horizontal, secondary side only |

> **Note on Y depth:** Each footprint must be positioned so its mating face (or port opening) is
> flush with or slightly proud of the y = 5 mm Edge.Cuts line. The exact Y centre of the footprint
> origin depends on the footprint's internal courtyard / mating-face reference; verify in KiCad's
> footprint editor before placing.

### 4.6 Why J7 cannot fit on the top edge

```
Secondary rail available:       53.5 mm
J2–J5 + J6 total (with gaps):  51.64 mm
Remaining for J7:                1.86 mm
J7 body width:                   7.62 mm
Shortfall:                       5.76 mm  ✗
```

J7 does not fit. It is a 3-pin debug UART header used only during development and is not present on
the production label or panel-mount face. Relocating it to the right board edge is the correct
trade-off; the constitution's P-HW-03 lists J1, J2–J5, J6 as the connectors subject to the
one-edge rule (§3.1: "All external connectors (J1, J2–J5, J6)"). J7 is not named in P-HW-03.

---

## 5. BOM Change Decision: Vertical vs. Right-Angle Fan Headers

### 5.1 Options

| Option | Footprint | MPN | Assembly impact | Cable exit direction |
|--------|-----------|-----|-----------------|---------------------|
| **A — Keep vertical (recommended)** | `PinHeader_1x04_P2.54mm_Vertical` | Molex 47053-1000 *(current BOM)* | No change | Cables exit upward, fold over board edge |
| B — Right-angle | `PinHeader_1x04_P2.54mm_Horizontal` | Molex 22-27-2041 or equivalent | BOM change required | Cables exit horizontally from board top edge |

### 5.2 Decision: Option A — Retain vertical headers

**Rationale:**

1. **Constitution constraint (§2.2, §9 P-DEV-04):** Molex 47053-1000 is a locked BOM component.
   Substituting a right-angle variant is a MAJOR amendment requiring `kicad.expert` consultation
   and a documented constitution revision before work begins. No such amendment has been filed.

2. **Functional equivalence:** Vertical headers placed flush with the top board edge allow cables
   to exit perpendicular to the PCB plane (upward), then fold horizontally toward the enclosure
   panel opening. Standard 4-wire fan cables have sufficient flexibility for this routing. This is
   a widely used technique in embedded fan-controller boards.

3. **Footprint depth savings:** Vertical headers are shallower in the Y direction (~2.5 mm body
   depth) vs. right-angle headers (~6–8 mm). This preserves more board area for internal
   components on the secondary side.

4. **Spacing:** The spacing analysis in §4.4 was performed using vertical-header body widths.
   Right-angle headers have the same X-axis footprint but require additional Y clearance; no
   replanning is needed if the decision is later reversed.

**If right-angle headers are desired in a future revision:** File a constitution amendment citing
§2.2, obtain `kicad.expert` sign-off, update `bom.csv` (MPN + footprint), update
`hardware/generate_project.py` if the footprint is referenced there, and rerun the spacing
analysis to confirm Y-depth clearance.

---

## 6. Implementation Steps

Steps must be executed in this order. No step may begin until the preceding step's acceptance
gate is met.

### Step 1 — Update `hardware/DESIGN.md` placement guidelines (docs change, no KiCad)

**Owner:** Hardware designer
**Gate:** PR review

- Remove the three-edge placement guidance from the "Component placement priority" list.
- Replace with the single-edge placement table from §4.5 of this plan.
- Add a note that J7 is the sole documented exception, placed on the right edge.
- Add a row noting that vertical fan headers (Molex 47053-1000) are retained and documenting
  the cable-folding requirement for fan cables.

### Step 2 — Verify ERC is zero before any PCB placement work

**Owner:** Hardware designer
**Gate:** Zero ERC errors in `hardware/kicad/erc_output.json` (P-TEST-01)

```
python hardware/generate_project.py
# Open PoE-FanController.kicad_sch in KiCad → Tools → Electrical Rules Checker
# Save output to hardware/kicad/erc_output.json
# Assert: "error_count": 0
```

No PCB footprint placement begins until this gate is confirmed.

### Step 3 — Place J1 (RJ45) on primary top edge

**Owner:** Hardware designer (KiCad PCB editor)

1. Load `hardware/kicad/PoE-FanController.kicad_pcb` in KiCad 10.0.3 (P-KI-01).
2. Add footprint `Connector_RJ:RJ45_Amphenol_54602-x08_Horizontal`.
3. **Rotate 90° clockwise** so the RJ45 port opening faces the +Y direction (upward, out of the
   top board edge).
4. Position footprint origin at **(x = 20.0 mm, y = adjusted so mating face is flush with
   y = 5 mm Edge.Cuts)**. Verify in 3D viewer that the port opening aligns with or slightly
   overhangs the board edge.
5. Check the retaining/locking tab: the tab projects ≈ 3 mm in the cable-insertion direction.
   After rotation, this tab must not extend beyond y = 5 mm (into the board-cut zone). Adjust
   Y position if needed so the tab falls inside the board outline.
6. Confirm: right-most copper of J1 ≤ x = 35 mm (≥ 3 mm clearance from barrier). Expected
   right copper edge: 20.0 + 10.65 = 30.65 mm — 7.35 mm clearance. ✓
7. Assign nets: POE_A+, POE_A−, POE_B+, POE_B− to the RJ45 differential pairs; GND to shield.

### Step 4 — Place J2–J5 (fan headers) on secondary top edge

**Owner:** Hardware designer

1. Place four instances of `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical`.
2. Orient so pin row runs along X axis (headers face upward, cables fold toward enclosure).
3. Use X centre positions from §4.5:

   | Ref | X centre | Pin 1 side |
   |-----|----------|------------|
   | J2  | 46.1 mm  | toward barrier (lower X) |
   | J3  | 56.8 mm  | toward barrier |
   | J4  | 67.4 mm  | toward barrier |
   | J5  | 78.1 mm  | toward barrier |

4. Y position: body flush with y = 5 mm Edge.Cuts (mating end of pins at or just above board edge).
5. Assign nets per `hardware/DESIGN.md` Fan Header Pinout: GND, +12V, TACH, PWM (pins 1–4).
6. Verify minimum X of J2 pin 1 pad: 41.0 mm − pad_overhang > 41.0 mm ≥ 38 + 3.0 mm. ✓

### Step 5 — Place J6 (USB-C) on secondary top edge

**Owner:** Hardware designer

1. Place footprint `Connector_USB:USB_C_Receptacle_GCT_USB4085`.
2. X centre: **88.1 mm**. Y: mating face flush with y = 5 mm Edge.Cuts.
3. **Edge clearance verification for through-hole pads:** The GCT USB4085-GF-A datasheet specifies
   minimum board-edge distance from the nearest mounting/through-hole pad centre. Confirm that no
   through-hole drill centre is closer than 0.5 mm to the Edge.Cuts line (KiCad DRC will flag
   violations). Adjust Y inward if needed; the mating face may overhang the board edge by up to
   1 mm without structural risk on a 1.6 mm FR4 board.
4. Assign nets: USB_DP, USB_DN, GND, and CC pull-down resistor nets (R9, R10).
5. Check courtyard gap to J5 right edge: 83.64 − 83.14 = 0.50 mm. DRC will pass (no overlap). ✓

### Step 6 — Place J7 (debug UART) on right board edge

**Owner:** Hardware designer

1. Place footprint `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical`.
2. **Rotate** so the pin row runs along Y axis and the connector exits the right board edge
   (x = 95 mm), or use a right-angle variant for horizontal cable exit at x = 95 mm.
   *(Right-angle for J7 is a debug-only header — no BOM amendment needed as it is not a locked
   BOM line; J7 is listed without MPN in `bom.csv`. A right-angle 3-pin 2.54 mm header is
   acceptable.)*
3. Position: x ≈ 94.5 mm (mating face flush with x = 95 mm wall), y centre ≈ 40 mm
   (vertical mid-point of secondary zone).
4. Assign nets: ESP_TX (GPIO1), ESP_RX (GPIO3), GND.
5. Confirm this connector is entirely within the secondary domain (x > 38 mm). ✓

### Step 7 — Add PCB isolation slot

**Owner:** Hardware designer

Per P-ISO-04: add a routed slot along x = 38 mm between the primary and secondary copper pours.
Recommended slot: 1.0 mm wide, spanning from y = 10 mm to y = 70 mm (leaving 5 mm keepout from
each board edge to avoid mechanical weakness). The slot increases creepage distance beyond the
copper gap at zero cost.

```
KiCad: Place → Add Rule Area (type = "Routed Slot")
  OR: Add a graphic line on Edge.Cuts layer with slot width parameter = 1.0 mm at x=38 mm
```

Verify the slot does not intersect any through-hole drill, via, or pad annular ring.

### Step 8 — Run DRC and resolve all errors

**Owner:** Hardware designer
**Gate:** Zero DRC errors (P-TEST-03)

DRC must be configured with:

| Check | Setting |
|-------|---------|
| General clearance | 0.2 mm (signal), 1.0 mm (power, for track width enforcement) |
| Isolation barrier clearance | 3.0 mm between primary netclass and secondary netclass |
| Courtyard collision | Enabled |
| Unconnected nets | Enabled (must be zero) |
| Board edge clearance | 0.3 mm minimum from copper to Edge.Cuts |

Expected DRC result: **0 errors, 0 unconnected nets.**

DRC report must be saved and committed alongside the PCB file (P-DEV-02).

### Step 9 — Gerber review

**Owner:** Hardware designer

1. Generate Gerbers to `hardware/gerbers/` (P-KI-06).
2. Open Gerbers in KiCad's Gerber viewer (or gerbv).
3. Confirm in F.Cu layer: J1, J2–J5, J6 pads visible at the top board edge.
4. Confirm in Edge.Cuts layer: board outline intact; isolation slot visible at x = 38 mm.
5. Confirm in drill file: all through-holes for J1, J2–J5, J6, J7 present with correct diameters.
6. Commit Gerbers.

### Step 10 — Update `hardware/DESIGN.md`

**Owner:** Hardware designer

Replace the placement priority list (items 1, 6, 7 — currently contradictory) with the final
connector positions as implemented. Add a note confirming:
- Fan header footprint: **Molex 47053-1000 (vertical)** — cable management note included.
- J7 exception documented.
- Isolation slot at x = 38 mm confirmed.

---

## 7. Acceptance Criteria

Each criterion maps to a constitution rule or a DRC-verifiable check.

| # | Criterion | Verifiable by | Ref |
|---|-----------|---------------|-----|
| AC-1 | J1 (RJ45), J2–J5 (fan headers), and J6 (USB-C) are all placed on the top board edge (y = 5 mm) in `PoE-FanController.kicad_pcb` | KiCad PCB editor — visual + footprint properties | P-HW-03 |
| AC-2 | No external connector pads or mating faces appear on the left, right, or bottom board edges (J7 on right edge is the sole documented exception) | KiCad PCB editor — visual inspection | P-HW-03 |
| AC-3 | All footprints are placed on F.Cu (top layer); no pads or courtyards on B.Cu | DRC courtyard check; footprint layer property | P-HW-02 |
| AC-4 | J1 copper pads remain at x ≤ 35 mm (≥ 3.0 mm from barrier); J2 copper pads begin at x ≥ 41 mm (≥ 3.0 mm from barrier) | DRC isolation-barrier clearance rule (3.0 mm between primary and secondary netclasses) | P-ISO-03 |
| AC-5 | KiCad DRC reports **zero errors** and **zero unconnected nets** after all connectors are placed and routed | DRC report | P-TEST-03 |
| AC-6 | Isolation slot at x = 38 mm is present in Edge.Cuts between y = 10 mm and y = 70 mm | Gerber viewer — Edge.Cuts layer | P-ISO-04 |
| AC-7 | Courtyard of J6 right edge ≤ x = 92.7 mm (≥ 2.3 mm from board right wall) | DRC board-edge clearance check | P-TEST-03 |
| AC-8 | Fan header BOM entry in `bom.csv` remains Molex 47053-1000 with `PinHeader_1x04_P2.54mm_Vertical` footprint (no unilateral BOM change) | Git diff of `bom.csv` | §2.2, §9 P-DEV-04 |
| AC-9 | `hardware/DESIGN.md` placement priority list is updated to reflect top-edge assignment and J7 right-edge exception | PR review | P-DEV-01 |
| AC-10 | J7 assigned to right board edge (x = 95 mm); body entirely within secondary domain (x > 38 mm); documented exception noted in `DESIGN.md` | KiCad PCB editor; DESIGN.md text | P-HW-03 exception |
| AC-11 | Gerbers regenerated and committed to `hardware/gerbers/` showing top-edge connector positions | Git history; Gerber file timestamps | P-KI-06 |

---

## 8. Out of Scope and Exceptions

- **Firmware changes:** Connector edge assignment has zero firmware impact.
- **Schematic netlist changes:** This is a PCB layout and BOM task only. `hardware/generate_project.py` is not modified (no new components, no net changes).
- **Internal component placement** (U1–U4, passives, L1, D1, SW1/SW2, LED1, NTC1): Governed by a separate placement plan; not addressed here.
- **Right-angle fan header substitution:** Deferred; requires a MAJOR constitution amendment. Vertical headers are retained.
- **J7 top-edge placement:** Explicitly excluded due to 5.76 mm shortfall on secondary top-edge rail. J7 is placed on the right board edge. This is a documented, intentional exception to P-HW-03 (J7 is not listed in P-HW-03's scope — that rule names J1, J2–J5, J6 only).

---

## 9. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | J6 USB-C through-hole pads too close to y=5 mm board edge (DRC edge-clearance error) | Medium | Medium | Adjust J6 Y position inward; mating face may overhang ≤1 mm. Verify against GCT USB4085 datasheet minimum board-edge distance before placement. |
| R2 | J1 RJ45 locking tab overhangs Edge.Cuts after 90° rotation | Medium | Low | Shift J1 Y position inward until tab clears y=5 mm. Verify in KiCad 3D viewer. The body depth of ~15.7 mm means the footprint origin sits well inside the board. |
| R3 | Courtyard collision between adjacent fan headers (J2–J5) in KiCad DRC | Low | Low | 0.5 mm inter-body gap is within courtyard clearance norm. Widen to 1.0 mm (reduces secondary-side margin from 1.86 mm to −0.14 mm — tight; adjust J6 position to compensate or use 0.5 mm gaps). |
| R4 | Ground pour zones (currently starting at x=40 mm per kicad_pcb lines 73–82) expose a 2 mm copper-free strip near the barrier; DRC may flag if traces need to cross this area | Low | Medium | Route all traces outside the x=38–40 mm keepout. The 2 mm buffer is a deliberate pour boundary; signal traces are narrow enough to route around it. |
| R5 | BOM pressure to switch to right-angle fan headers (from enclosure team or mechanical review) | Medium | Medium | File a constitution amendment before any footprint change. The spacing analysis in §4.4 uses vertical-header widths; right-angle headers have the same X width but larger Y depth — recheck Y clearance if amendment is approved. |

---

## 10. Constitution Compliance

| Constitution principle | How this plan satisfies it |
|------------------------|---------------------------|
| **P-HW-02** (single-sided placement) | All connector footprints specified for F.Cu top layer. B.Cu is reserved for traces and pours only. |
| **P-HW-03** (single board-edge connector rule, top edge) | J1, J2–J5, J6 all assigned to top edge (y = 5 mm). J7 is not in P-HW-03's named connector list; its right-edge exception is explicitly documented. |
| **P-HW-04** (fixed board outline) | No Edge.Cuts changes. The isolation slot (§6, Step 7) is an interior slot within the existing outline, not an outline change. |
| **P-HW-06** (grid discipline) | Proposed X centres are on 0.1 mm grid; implementation must use 0.1 mm or finer per KiCad PCB grid setting. |
| **P-ISO-02** (barrier at x=38 mm) | No copper crosses x=38 mm. J1 copper stops at x≈30.65 mm; J2 copper starts at x≈41 mm. |
| **P-ISO-03** (≥3.0 mm creepage/clearance) | J1 right copper edge to barrier: 7.35 mm. J2 left copper edge to barrier: 3.0 mm. Both ≥ 3.0 mm. DRC isolation-barrier rule enforces this. |
| **P-ISO-04** (PCB slot at barrier) | Routed slot at x=38 mm specified in Step 7. |
| **P-TEST-01** (zero ERC before layout) | Step 2 gates PCB work on a confirmed zero-ERC schematic. |
| **P-TEST-03** (zero DRC after layout) | Step 8 requires DRC to pass with zero errors and zero unconnected nets before Gerber export. |
| **P-TEST-04** (DRC before Gerber export) | Step 8 precedes Step 9 in the implementation sequence. |
| **P-KI-01** (KiCad 10.0.3) | All PCB work uses KiCad 10.0.3; no other version is permitted. |
| **P-KI-06** (Gerbers in `hardware/gerbers/`) | Step 9 regenerates Gerbers to the specified directory. |
| **P-DEV-01** (commit convention) | All commits for this feature use prefix `hw:`. |
| **P-DEV-02** (ERC/DRC gate for hardware PRs) | PR must include updated `erc_output.json` and DRC report as merge preconditions. |
| **P-DEV-03** (no direct commits to main) | All changes via pull request. |
| **§2.2** (BOM lock — Molex 47053-1000) | Vertical headers retained; no BOM change. Right-angle option deferred to a future amendment. |

---

## 11. References

| Resource | Path / URL |
|----------|-----------|
| Board outline and isolation barrier | `hardware/kicad/PoE-FanController.kicad_pcb` lines 53–82 |
| Ground pour zones | `hardware/kicad/PoE-FanController.kicad_pcb` lines 73–82 |
| BOM — connector entries | `hardware/bom/bom.csv` rows J1, J2–J5, J6, J7 |
| Placement guidelines (to be updated) | `hardware/DESIGN.md` §PCB Design Guidelines, items 1, 6, 7 |
| Isolation and safety rules | `hardware/DESIGN.md` §Safety & Isolation Requirements |
| Fan header pinout | `hardware/DESIGN.md` §Fan Header Pinout (J2–J5) |
| Constitution — hardware principles | `docs/constitution.md` §3 (P-HW-01 – P-HW-08) |
| Constitution — isolation rules | `docs/constitution.md` §5.4 (P-ISO-01 – P-ISO-05) |
| Constitution — testing standards | `docs/constitution.md` §8 (P-TEST-01 – P-TEST-04) |
| Würth 615008144521 datasheet | https://www.we-online.com/en/components/products/WR-MJ/615008144521 |
| GCT USB4085-GF-A datasheet | https://gct.co/connector/usb4085 |
| GitHub issue | https://github.com/nielsverhoeven/PoE-FanController/issues/1 |
