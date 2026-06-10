# Technical Plan: Route All PCB Traces

<!-- Issue: #83 | Branch: feature/148-correct-gpio-pin-assignments | Status: PLANNING -->
<!-- Constitution reference: v4.2.1 | Plan date: 2026-06-10 -->
<!-- Spec: docs/features/route-pcb-traces/spec.md -->

---

## 1. Architecture Fit

### 1.1 Current Board State (Post-Issue #148)

Before routing can begin, the current PCB state must be understood:

| Item | State |
|---|---|
| DRC `shorting_items` | **35** (all from old pre-#148 signal traces) |
| DRC `solder_mask_bridge` | **125** (all from old pre-#148 signal traces) |
| GND copper pour zones | **Already correctly assigned to `GND` net** (fixed in #148) |
| Legacy signal traces | Must be deleted as Phase 0 before any new routing |
| Post-deletion state | All nets unconnected (pure airwire / ratsnest board) |

### 1.2 Hardware Block Diagram Mapping

The daughter board sits wholly in the SELV secondary domain. The isolation
barrier is internal to the Waveshare SKU 32088 module; P-ISO-01 through
P-ISO-05 are not engaged by this routing task.

J8 geometry (from constitution P-HW-04, updated for new ESP32 x=15–36mm layout):
- Row A (pads 1–20): PCB x = 17.81 mm — signals route LEFT (x < 17.81 mm)
- Row B (pads 21–40): PCB x = 33.19 mm — signals route RIGHT (x > 33.19 mm)
- J8 centre at PCB position (25.50, 28.80) mm, rotated 90 degrees
- Left component zone: x = 0–17.81 mm (J9, LED1+R3, LED2+R13, J6)
- Right component zone: x = 33.19–56 mm (J2–J5, R5–R8, U1, L1, D1, C1, C2, LED6+R15, D2–D5)

Corrected power flow that routing must physically implement:

    J8 pad 40 (+5V VBUS) --> C1 (input bypass) --> L1 --> U1 (boost converter)
                                                            |
                             D1 (SS54 Schottky) <----------+ (BOOST_SW loop)
                             |
                            +12V rail --> C2 (output filter)
                                      --> J2-J5 fan headers pin 2 (+12V)
                                      --> D2-D5 (per-fan LEDs) --> R9-R12 --> GND

    J8 pad 36 (+3V3) --> R5-R8 pin 1 (TACH pull-ups)
                     --> J9 pin 1 (DHT11 VCC)
                     --> R14 pin 1 (DS18B20 pull-up)

    GND pads (Row A: 3,8,13,18 | Row B: 23,28,33,38) --> GND copper pour

### 1.3 Authoritative J8 Pad-to-Net Mapping (from Issue #148)

**Row B, pads 21–40 (PCB x = 33.19 mm) — route RIGHT toward fan headers:**

| Pad | Net | GPIO | Notes |
|-----|-----|------|-------|
| 21 | PROBE_LED | GPIO48 | --> R15 --> LED6 |
| 22 | FAN4_TACH | GPIO47 | Via R8 pull-up |
| 23 | GND | — | Physical GND |
| 24 | FAN3_TACH | GPIO46 | Via R7 pull-up |
| 25 | NC | GPIO33 | **EMAC FORBIDDEN — never route** |
| 26 | NC | GPIO32 | **EMAC FORBIDDEN — never route** |
| 27 | FAN4_PWM | GPIO27 | --> J5 pin 4 |
| 28 | GND | — | Physical GND |
| 29 | FAN3_PWM | GPIO26 | --> J4 pin 4 |
| 30 | NC | RUN | Reserved — no route |
| 31 | FAN2_TACH | GPIO23 | Via R6 pull-up |
| 32 | FAN1_TACH | GPIO22 | Via R5 pull-up |
| 33 | GND | — | Physical GND |
| 34 | FAN2_PWM | GPIO21 | --> J3 pin 4 |
| 35 | FAN1_PWM | GPIO20 | --> J2 pin 4 |
| 36 | +3V3 | — | Sole 3.3V source on J8 |
| 37 | NC | EN | Reserved — no route |
| 38 | GND | — | Physical GND |
| 39 | NC | VSYS | No route |
| 40 | +5V | VBUS | Sole 5V source on J8 |

**Row A, pads 1–20 (PCB x = 17.81 mm) — route LEFT toward left-zone components:**

| Pad | Net | GPIO | Notes |
|-----|-----|------|-------|
| 3 | GND | — | Physical GND |
| 6 | STATUS_LED | GPIO2 | --> R3 --> LED1 |
| 8 | GND | — | Physical GND |
| 13 | GND | — | Physical GND |
| 14 | PROG_LED | GPIO15 | --> R13 --> LED2 |
| 15 | DHT11_DATA | GPIO16 | --> J9 pin 2 |
| 18 | GND | — | Physical GND |
| 19 | DS18B20_DATA | GPIO19 | --> R14 pin 2 --> J6 pin 2 |
| All others | NC | — | No route |

### 1.4 Intentional NC Pads — Never Route

| J8 Pad | GPIO | Reason |
|--------|------|--------|
| 25 | GPIO33 | EMAC RXD1 — Ethernet MAC, permanently reserved |
| 26 | GPIO32 | EMAC RXD0 — Ethernet MAC, permanently reserved |
| 30 | RUN | System RUN control pin |
| 37 | EN | System enable pin |
| 39 | VSYS | System voltage reference |

### 1.5 Relevant Constitution Principles

| Principle | Rule Summary | Impact on This Plan |
|---|---|---|
| P-HW-01 | Two-layer FR4 only | F.Cu for traces; B.Cu for GND pour and via returns |
| P-HW-02 | All components on F.Cu | All pads to connect are on F.Cu; confirmed |
| P-HW-04 | 78 x 56 mm board, portrait layout | J8 Row A at x=17.81mm, Row B at x=33.19mm; ESP32 at x=15–36mm; left zone x=0–17.81mm; right zone x=33.19–56mm |
| P-HW-07 | Power >= 1.0 mm; signal >= 0.25 mm | Governs every trace width decision in §3 |
| P-HW-08 | GND copper pour on both layers | Zones already assigned to GND (issue #148); fill in Phase 8 |
| P-KI-01 | KiCad 10.0.3 locked | All GUI and scripting must use this version only |
| P-KI-06 | Gerbers in `hardware/kicad/gerbers/` | Gerbers regenerated and committed in Phase 8c |
| P-KI-07 | PCB layout in KiCad GUI; no scripts write to `.kicad_pcb` | Phase 0 script is a documented exception — see §9 Risk R-01 |
| P-DEV-01 | Commit convention `hw: <subject>` | All commits on this branch use `hw:` prefix |

---

## 2. Net Classification and Trace Width Rules (P-HW-07)

### 2.1 Power Nets — trace width >= 1.0 mm

| Net | From --> To | Notes |
|---|---|---|
| `+5V` | J8 pad 40 --> C1+ --> L1 --> U1 VIN | Boost input; heaviest current path |
| `+12V` | D1 cathode --> C2+ --> J2-J5 pin 2 | Fan power rail |
| `+3V3` | J8 pad 36 --> R5-R8 pin 1, J9 pin 1, R14 pin 1 | Single source; low-current but power class |
| `GND` | All GND pads --> copper pour | Primarily handled by poured zones |
| `BOOST_SW` | U1 SW pin --> L1 --> D1 anode | Switching loop; tight route; >= 1.0 mm |

### 2.2 Signal Nets — trace width >= 0.25 mm

| Net | Path |
|---|---|
| `FAN1_PWM` | J8 pad 35 --> J2 pin 4 |
| `FAN2_PWM` | J8 pad 34 --> J3 pin 4 |
| `FAN3_PWM` | J8 pad 29 --> J4 pin 4 |
| `FAN4_PWM` | J8 pad 27 --> J5 pin 4 |
| `FAN1_TACH` | J8 pad 32 --> R5 pin 2 --> J2 pin 3; R5 pin 1 --> +3V3 |
| `FAN2_TACH` | J8 pad 31 --> R6 pin 2 --> J3 pin 3; R6 pin 1 --> +3V3 |
| `FAN3_TACH` | J8 pad 24 --> R7 pin 2 --> J4 pin 3; R7 pin 1 --> +3V3 |
| `FAN4_TACH` | J8 pad 22 --> R8 pin 2 --> J5 pin 3; R8 pin 1 --> +3V3 |
| `PROBE_LED` | J8 pad 21 --> R15 pin 1 |
| `/PROBE_LED_A` | R15 pin 2 --> LED6 anode |
| `STATUS_LED` | J8 pad 6 --> R3 pin 1 |
| `/LED_A` | R3 pin 2 --> LED1 anode |
| `PROG_LED` | J8 pad 14 --> R13 pin 1 |
| `/PROG_LED_A` | R13 pin 2 --> LED2 anode |
| `DHT11_DATA` | J8 pad 15 --> J9 pin 2 |
| `DS18B20_DATA` | J8 pad 19 --> R14 pin 2 --> J6 pin 2 |
| `/FAN1_IND` | J2 pin 2 --> D2 anode; D2 cathode --> R9 --> GND |
| `/FAN2_IND` | J3 pin 2 --> D3 anode; D3 cathode --> R10 --> GND |
| `/FAN3_IND` | J4 pin 2 --> D4 anode; D4 cathode --> R11 --> GND |
| `/FAN4_IND` | J5 pin 2 --> D5 anode; D5 cathode --> R12 --> GND |

> **Note on `/FAN_IND` nets:** D2–D5 are per-fan indicator LEDs. The `/FANn_IND`
> net is the intermediate node between each LED and its current-limit resistor
> (R9–R12, 1 kOhm each). The +12V trace branches at J2–J5 pin 2: one branch
> (>= 1.0 mm power class) continues to the fan, a second branch (>= 0.25 mm)
> feeds each D_n anode.

### 2.3 Via Standards (P-HW-07)

| Class | Via pad diameter | Via drill |
|---|---|---|
| Signal | 0.8 mm | 0.4 mm |
| Power | 0.8 mm | 0.4 mm |

Vias are used only where a trace must change layers to avoid a DRC spacing
violation and cannot be resolved by re-routing on F.Cu. Prefer F.Cu-only
routes wherever board density allows.

---

## 3. Ten-Phase Implementation Approach

All phases must be executed in order. The `.kicad_pcb` file must pass DRC
with 0 errors at the relevant gate before committing the result of each phase.

---

### Phase 0 — Delete All Existing Signal Traces *(CRITICAL PREREQUISITE)*

**Goal:** Remove all legacy traces created against the pre-#148 (incorrect)
pad-to-net mapping. These are the sole cause of the 35 DRC `shorting_items`
and 125 `solder_mask_bridge` violations.

**Method — pcbnew Python script (documented exception to P-KI-07):**

Script path: `hardware/delete_old_traces.py`

Execute with the KiCad-bundled Python interpreter:

    C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe hardware/delete_old_traces.py

The script must:
1. Load the board: `board = pcbnew.LoadBoard("hardware/kicad/PoE-FanController.kicad_pcb")`
2. Collect all `PCB_TRACK` and `PCB_ARC` items from `board.GetTracks()`
3. Remove each track: `board.Remove(track)` — does not touch zones or footprints
4. Save: `board.Save("hardware/kicad/PoE-FanController.kicad_pcb")`
5. Print count of removed tracks for review

**Verification:** Open the saved file in KiCad GUI. Confirm all traces are gone
(board shows airwires/ratsnest only). Run DRC — the 35 `shorting_items` and
125 `solder_mask_bridge` violations must be gone. Commit this single-purpose
change separately before Phase 1.

**GND zones unchanged:** The Phase 0 script must NOT touch zone objects.
Both GND zones remain correctly assigned to `GND` net (per issue #148).

---

### Phase 1 — Reposition J8 Footprint and Move J6 to Left Zone *(CRITICAL PREREQUISITE — must precede ALL routing)*

**Goal:** Align PCB component positions with the new ESP32 x = 15 mm layout
so that every signal's source pad (J8 Row A or Row B) is physically adjacent
to its destination component, enabling zero-crossing trace routing.

**Actions (KiCad GUI — P-KI-07):**

1. **Move J8 footprint centre** from (10.50, 28.80) mm to **(25.50, 28.80) mm**.
   - This shifts Row A pads from x = 2.81 mm → **x = 17.81 mm**
   - This shifts Row B pads from x = 18.19 mm → **x = 33.19 mm**
   - In KiCad GUI: select J8 footprint → Properties → set X to 25.50 mm
     (or use `E` → Position X field); Y and rotation are unchanged.

2. **Move J6 (DS18B20 connector)** from its current right-side position to the
   **left zone (x < 17.81 mm)**, near J9 and LED2+R13.
   - DS18B20_DATA (GPIO19) is a Row A signal; placing J6 left keeps the trace
     entirely in x ≤ 17.81 mm (FR-10, FR-12).

3. **Verify left-zone components** — all of the following must be within
   x = 0–17.81 mm: J9 (DHT11 connector), LED1+R3 (STATUS_LED chain),
   LED2+R13 (PROG_LED chain), J6 (DS18B20 connector).

4. **Verify right-zone components** — all of the following must be within
   x = 33.19–56 mm: J2–J5 (fan headers), R5–R8 (TACH pull-ups), U1, L1, D1,
   C1, C2 (boost converter chain), LED6+R15 (PROBE_LED chain), D2–D5 (fan
   indicator LEDs).

**Acceptance gate:**
- J8 Row A pads at x ≈ 17.81 mm (verify in KiCad footprint properties)
- J8 Row B pads at x ≈ 33.19 mm
- J6 positioned in left zone (x < 17.81 mm)
- DRC shows 0 courtyard violations introduced by repositioning
- Isolated git commit (e.g. `hw: reposition J8 to x=25.50mm and move J6 to left zone`)

---

### Phase 2 — Route BOOST_SW Switching Loop *(EMI Critical)*

**Net:** `BOOST_SW` — the loop `L1 SW-side pin → D1 anode → U1 SW pin`

**Zone:** RIGHT (all components in x = 33.19–56 mm)

This loop carries high-frequency switching current (~100 kHz). Loop area is
directly proportional to radiated EMI. Route this before all other traces to
guarantee the tightest possible copper geometry.

**Routing rules:**
- Route all three segments (`L1 → BOOST_SW`, `BOOST_SW → U1 SW`,
  `D1 anode → BOOST_SW`) before any other routes.
- Keep total enclosed loop area < 200 mm² (measure in KiCad board inspector).
- Use >= 1.0 mm trace width throughout (BOOST_SW is a power-class net).
- D1 is an SMA-package SMD component; route U1 SW pin first (shortest
  segment from IC), then connect D1 anode, then close the loop at L1.
- No signal traces may pass through the interior of the BOOST_SW loop.

**Acceptance:** BOOST_SW loop fully routed; trace width ≥ 1.0 mm; enclosed
loop area < 200 mm²; isolated git commit.

---

### Phase 3 — Route Power Rails (>= 1.0 mm)

Route in current priority order (heaviest first):

**+5V rail (RIGHT zone):**
```
J8 pad 40 --> C1 positive pad --> L1 pin 1 --> U1 VIN
```
Keep C1 bypass cap close to the inductor to minimise input ripple loop area.

**+12V rail (RIGHT zone):**
```
D1 cathode --> C2 positive pad
C2 positive pad --> J2 pin 2, J3 pin 2, J4 pin 2, J5 pin 2 (daisy-chain or star)
```

**+3V3 rail:**
```
J8 pad 36 --> R5 pin 1, R6 pin 1, R7 pin 1, R8 pin 1  (RIGHT zone — TACH pull-ups)
J8 pad 36 --> R14 pin 1 (DS18B20 pull-up; R14 may sit near left zone boundary)
```
Note: +3V3 is a power rail (not a signal), so it is exempt from the
zero-crossing trace constraint in FR-10. Keep the +3V3 tree as short as
possible regardless of zone boundary.

**GND connections (>= 1.0 mm):**
```
J8 Row A GND pads (3, 8, 13, 18) --> GND pour / C1 GND / J9 pin 3 / LED cathodes
J8 Row B GND pads (23, 28, 33, 38) --> GND pour / C2 GND / J6 pin 3 / U1 GND area
```
GND traces partially replaced by copper pour in Phase 8, but explicit traces
ensure connectivity even if pour islands occur.

**Acceptance:** All power rail ratsnest cleared; trace widths ≥ 1.0 mm;
isolated git commit.

---

### Phase 4 — Route Fan PWM Signals (>= 0.25 mm)

Straight runs from Row B of J8 (x = 33.19 mm) rightward to fan headers
(x ≈ 46–56 mm):

| Net | J8 pad | Fan header | Pin |
|---|---|---|---|
| `FAN1_PWM` | 35 | J2 | pin 4 |
| `FAN2_PWM` | 34 | J3 | pin 4 |
| `FAN3_PWM` | 29 | J4 | pin 4 |
| `FAN4_PWM` | 27 | J5 | pin 4 |

Route parallel traces at 0.25 mm. Maintain >= 0.25 mm clearance between
adjacent signal traces. Dog-leg to avoid the BOOST_SW loop region if needed.

**Acceptance:** All 4 FAN_PWM ratsnest cleared; trace width ≥ 0.25 mm; all
traces remain in x ≥ 33.19 mm.

---

### Phase 5 — Route Fan TACH Signals + R5–R8 Pull-ups (>= 0.25 mm)

**Pull-up topology** (identical for all four channels):

    J8 pad N -------- R_n pin 2 (signal / pull-up node)
                       |
    J2-J5 pin 3 ------ R_n pin 2   (same node)
                       |
    R_n pin 1 -------- +3V3 (routed in Phase 3)

| Net | J8 pad | Resistor | Fan header | Pin |
|---|---|---|---|---|
| `FAN1_TACH` | 32 | R5 | J2 | pin 3 |
| `FAN2_TACH` | 31 | R6 | J3 | pin 3 |
| `FAN3_TACH` | 24 | R7 | J4 | pin 3 |
| `FAN4_TACH` | 22 | R8 | J5 | pin 3 |

**Acceptance:** All 4 FAN_TACH nets connected; R5–R8 both pads connected;
all traces in x ≥ 33.19 mm.

---

### Phase 6 — Route Right-Side LED Chains (>= 0.25 mm)

**PROBE_LED (GPIO48 — Row B, RIGHT zone):**
```
J8 pad 21 (PROBE_LED / GPIO48) --> R15 pin 1
R15 pin 2 --> [/PROBE_LED_A] --> LED6 anode (pin 1)
LED6 cathode (pin 2) --> GND (via pour or explicit trace)
```

**Fan indicator LED chains (passive — +12V rail driven, RIGHT zone):**

Four identical per-channel indicator chains:

```
J2-J5 pin 2 (+12V branch) --> D_n anode --> [/FANn_IND] --> R_n --> GND
```

| Net | LED | Resistor | Fan header |
|---|---|---|---|
| `/FAN1_IND` | D2 | R9 | J2 pin 2 |
| `/FAN2_IND` | D3 | R10 | J3 pin 2 |
| `/FAN3_IND` | D4 | R11 | J4 pin 2 |
| `/FAN4_IND` | D5 | R12 | J5 pin 2 |

The +12V trace to each J_n pin 2 (from Phase 3) must branch: one segment
continues to the fan connector at >= 1.0 mm (power class), and a separate
branch at >= 0.25 mm feeds D_n anode. The D_n → R_n → GND chain is a
signal-class net.

**Acceptance:** PROBE_LED net connected; D2–D5 chains connected; all traces
in x ≥ 33.19 mm.

---

### Phase 7 — Route Left-Side Signals (>= 0.25 mm)

All signals originate from Row A of J8 (x = 17.81 mm) and route leftward
into the left zone (x < 17.81 mm). No trace in this phase may cross the
ESP32 footprint boundary (FR-10).

**Status LED (LED1, green):**
```
J8 pad 6 (STATUS_LED / GPIO2) --> R3 pin 1
R3 pin 2 --> [/LED_A] --> LED1 anode (pin 1)
LED1 cathode (pin 2) --> GND
```

**Program/OTA LED (LED2, orange):**
```
J8 pad 14 (PROG_LED / GPIO15) --> R13 pin 1
R13 pin 2 --> [/PROG_LED_A] --> LED2 anode (pin 1)
LED2 cathode (pin 2) --> GND
```

**DHT11 data:**
```
J8 pad 15 (DHT11_DATA / GPIO16) --> J9 pin 2
```
Single-wire signal. No PCB pull-up required — DHT11 breakout (Reichelt
239086) includes onboard pull-up per constitution §2.2.

**DS18B20 data:**
```
J8 pad 19 (DS18B20_DATA / GPIO19) --> R14 pin 2 --> J6 pin 2
R14 pin 1 --> +3V3 (routed in Phase 3)
```
R14 is the 4.7 kΩ DS18B20 pull-up; route in-line, do not bypass it. J6 is
in the left zone after Phase 1, so the full signal path stays at x ≤ 17.81 mm.

**Acceptance:** All 4 left-side signal nets (STATUS_LED, PROG_LED, DHT11_DATA,
DS18B20_DATA) connected; no trace crosses ESP32 footprint boundary
(x = 15–36 mm); isolated git commit.

---

### Phase 8 — Fill GND Zones and Run DRC *(Convergence Gate)*

**Step 8a — Zone fill:**
In the KiCad GUI (Edit → Fill All Zones, shortcut: `B`):
1. Both zones — `GND_TOP` (F.Cu) and `GND_BOT` (B.Cu) — fill with copper
   connected to the `GND` net (already correctly assigned per issue #148).
2. Inspect for isolated islands: any region not connected back to a GND pad
   must be bridged with an explicit GND via or removed with a keepout zone.

**Step 8b — DRC:**
Run full DRC: Tools → Design Rules Checker → Run DRC.

Target outcome:

| Category | Target |
|---|---|
| Errors | **0** |
| Unconnected | **0** (NC pads 25, 26, 30, 37, 39 intentionally excluded) |
| Shorting items | **0** (all eliminated in Phase 0) |
| Solder mask bridge | **0** (all eliminated in Phase 0) |

Verify J8 pads 25, 26, 30, 37, and 39 have zero connected tracks in the
`.kicad_pcb` file.

If violations remain, resolve before committing:
- `unconnected`: add the missing trace manually.
- `clearance`: re-route the offending segment.
- `isolated_copper`: add GND via or keepout zone.

**Step 8c — Gerbers:**
Generate Gerber files: File → Fabrication Outputs → Gerbers.
Output to `hardware/kicad/gerbers/`. Commit updated `.kicad_pcb` and Gerbers
together with message: `hw: regenerate Gerbers after full PCB routing`

---

## 4. Hardware Implementation Approach

### 4.1 Schematic Changes
None. The netlist is frozen after issue #148. The `.kicad_sch` must not be
touched.

### 4.2 PCB Layout Changes

| Change type | Detail |
|---|---|
| Delete legacy traces | All existing signal/power traces (Phase 0) — removes 35 shorts |
| Reposition J8 footprint | Move centre from (10.50, 28.80) to (25.50, 28.80) mm (Phase 1) |
| Relocate J6 to left zone | Move DS18B20 connector from right side to x < 17.81 mm (Phase 1) |
| New traces — power class | `+5V`, `+12V`, `+3V3`, `GND`, `BOOST_SW` (Phases 2–3) |
| New traces — signal class | All signal nets using corrected pad numbers (Phases 4–7) |
| Zone fill | Both layers filled after all traces are placed (Phase 8) |
| Gerber regeneration | All copper, drill, mask, and silkscreen layers (Phase 8c) |

### 4.3 Component Selection
No new components. All 33 footprints are already placed. No BOM changes.
Two footprint positions are updated in Phase 1 (J8 and J6); no component
values, packages, or netlists change.

### 4.4 Power Budget Impact
Routing does not add electrical loads. Power budget is unchanged from the
constitution §5.2 table. Trace temperature rise at the heaviest path (+5V
boost input, <= 2 A, 1.0 mm width, 35 µm copper) is within the IPC-2221A
spec at 25 °C ambient with a <= 10 °C rise target.

---

## 5. PoE / Power Considerations

No PoE topology changes. The daughter board is wholly in the SELV secondary
domain. The isolation barrier resides inside the Waveshare SKU 32088 module.

| Principle | Status |
|---|---|
| P-POE-01 (802.3at Class 4 only) | Unchanged |
| P-POE-02 (no primary-side changes) | No primary-side touches |
| P-ISO-01 (>= 1.5 kV isolation) | Provided by Waveshare SKU 32088 |
| P-ISO-02 through P-ISO-05 | Not engaged — all routing on secondary (SELV) side |

---

## 6. Firmware Implementation Approach

No firmware changes. This feature is hardware-only. All GPIO assignments are
defined in the constitution §4 and already implemented in firmware. The
corrected J8 pad-to-GPIO mapping (issue #148) does not change the GPIO
numbers — only the physical pad locations on the connector were corrected.

---

## 7. Web UI Changes

None. This feature is hardware-only.

---

## 8. Testing Strategy

### 8.1 Pre-Commit Automated Checks

| Check | Tool | Pass criterion |
|---|---|---|
| Legacy traces deleted | KiCad DRC / `kicad-cli` | 0 `shorting_items`, 0 `solder_mask_bridge` after Phase 0 |
| DRC clean | `kicad-cli pcb drc` | 0 errors, 0 unconnected after Phase 8 |
| NC pads unrouted | `.kicad_pcb` XML inspection | Pads 25, 26, 30, 37, 39 have zero track endpoints |
| Trace widths | `.kicad_pcb` XML inspection | Power nets >= 1.0 mm; signal nets >= 0.25 mm |
| Gerber completeness | Visual inspection | All copper layers, edge cuts, drill file present |

### 8.2 Hardware Bring-Up Validation (post-fabrication)

Perform these checks in order on the first assembled board:

1. **Continuity — GND pour:** Multimeter between any two GND pads. Expect < 1 Ohm.
2. **Short circuit check:** Before powering, measure +5V<-->GND, +12V<-->GND,
   +3V3<-->GND. Expect > 1 kOhm (capacitor leakage expected; dead short = fail).
3. **Power-on +5V:** Apply 5 V to J8 pad 40; measure at C1, L1. Expect 4.9–5.1 V.
4. **Boost converter output:** Measure D1 cathode / C2+. Expect 11.5–12.5 V.
5. **+12V to fan headers:** Measure J2–J5 pin 2. Expect 11.5–12.5 V.
6. **+3V3 at J9 and pull-up resistors:** Measure J9 pin 1 and R5–R8 pin 1.
   Expect 3.15–3.45 V.
7. **BOOST_SW oscillation:** Oscilloscope at D1 anode; confirm ~100 kHz switching.
8. **Fan indicator LEDs:** Connect 12 V fan to J2; D2 must illuminate. Repeat J3–J5.
9. **Status LED (LED1):** Assert STATUS_LED GPIO high from firmware; LED1 must illuminate.
10. **DS18B20 data bus:** Confirm 1-Wire protocol traffic on J6 pin 2 with oscilloscope.

### 8.3 DRC Gate

The pull request must include the DRC output file (`hardware/kicad/drc_result.rpt`)
generated after the final zone fill. The PR is blocked from merge if the
report contains any error or unconnected item.

---

## 9. Risks

### R-01 — P-KI-07 Tension: Python Script Writes to `.kicad_pcb`

**Constitution rule P-KI-07** states that PCB layout must be done in the
KiCad GUI; no scripts may write to `.kicad_pcb`.

**Scope:** Phase 0 uses a minimal Python script to delete all legacy tracks.
This is a mechanical bulk deletion (not a design decision), is fully auditable,
and follows the project's established precedent (`hardware/pcb_cleanup_v2.py`,
`hardware/fix_pcb_placement_v3.py`, etc.).

**Mitigation:** All trace routing (Phases 2–7) is performed interactively in
the KiCad GUI, satisfying the spirit of P-KI-07 for design-critical work. The
Phase 0 script is a documented exception, committed separately and
code-reviewed. A P-KI-07 PATCH amendment must be documented if auto-routing
scripts are used for Phases 2–7.

**Residual risk:** Low — track deletion is fully reversible via `git checkout`.

---

### R-02 — Router Congestion Near J8

**Risk:** J8 is a 2×20 header with 15.38 mm row spacing. After Phase 1
repositioning, Row A pads are at x = 17.81 mm and Row B pads are at
x = 33.19 mm. The 15.38 mm gap between rows now sits over the ESP32 footprint
(x = 17.81–33.19 mm) and is free of routing — which is the design intent of
the zero-crossing constraint. Congestion risk is reduced compared to the old
layout, since each row's signals route exclusively into the adjacent zone.

**Mitigation:** Route Row B signals rightward in a fanned pattern with 45°
angles. Route Row A signals leftward. Use vias to route short B.Cu segments if
congestion is unavoidable on F.Cu within a zone.

**Residual risk:** Low — signal density is modest (20 signal nets, 8 power
pads) for a 78 × 56 mm board, and the two routing zones are now well-separated.

---

### R-03 — GND Zone Islands After Fill

**Risk:** After zone fill, GND copper on F.Cu or B.Cu may form isolated
islands that generate `isolated_copper` DRC warnings.

**Mitigation:** Inspect zone fill visually in KiCad after Phase 8a. Add GND
vias to connect any island to the opposing layer. If an island cannot be
connected, add a keepout zone to prevent copper fill in that region.

**Residual risk:** Low — the board is not dense and both layers carry GND pours.

---

### R-04 — EMAC Pad Accidental Connection

**Risk:** J8 pads 25 (GPIO33 EMAC) and 26 (GPIO32 EMAC) are reserved for the
Ethernet MAC. Accidentally routing traces to these pads would cause Ethernet
failures at runtime.

**Mitigation:** FR-09 (spec) explicitly prohibits routing to pads 25, 26, 30,
37, 39. The NC-pad check in §8.1 verifies absence of tracks. The KiCad
interactive router will show no ratsnest airwire to these pads if the netlist
correctly marks them NC (confirmed by issue #148).

**Residual risk:** Low if DRC gate is enforced.

---

## 10. Constitution Compliance

| Principle | How this plan satisfies it |
|---|---|
| **P-HW-01** (2-layer FR4) | All routing on F.Cu and B.Cu only; no layer additions |
| **P-HW-02** (all components on F.Cu) | J8 and J6 are repositioned in Phase 1 (position changes only; both remain on F.Cu); all other pads already on F.Cu |
| **P-HW-03** (J2–J5 on side edge) | Routing terminates at these connectors without moving them |
| **P-HW-04** (78 x 56 mm board) | No board outline change; J8 repositioned to centre (25.50, 28.80) mm; Row A at x=17.81mm, Row B at x=33.19mm |
| **P-HW-05 / P-KI-04** (generator is schematic source of truth) | `.kicad_sch` is not touched |
| **P-HW-06** (grid discipline) | All new vias on 0.1 mm grid; traces follow KiCad router constraints |
| **P-HW-07** (trace widths) | Power >= 1.0 mm; signal >= 0.25 mm; via 0.8/0.4 mm — enforced per §3 |
| **P-HW-08** (GND pour on both layers) | GND zone net assignment already correct (issue #148); Phase 8 fills both layers |
| **P-HW-09** (keyed connectors) | No connector changes; existing keyed housings on J2–J6 and J9 preserved |
| **P-KI-01** (KiCad 10.0.3 locked) | GUI and Python interpreter at KiCad 10.0.3 installation path |
| **P-KI-03** (PCB format version 20260206) | KiCad 10.0.3 writes this version; no other tool writes to the PCB |
| **P-KI-05** (custom footprints in-project) | No new footprints; `Custom:ESP32-P4-PoE-ETH-PinSocket` already in `hardware/kicad/footprints/Custom.pretty/` |
| **P-KI-06** (Gerbers in `hardware/kicad/gerbers/`) | Phase 8c regenerates Gerbers to this path and commits them |
| **P-KI-07** (PCB layout in KiCad GUI) | Phase 1 repositioning and trace routing (Phases 2–7) done interactively in GUI; Phase 0 script is a documented exception — see R-01 |
| **P-POE-01** (802.3at Class 4) | No power topology changes |
| **P-POE-02** (no primary-side changes) | No primary-side touches |
| **P-ISO-01 to P-ISO-05** (isolation) | No traces cross the isolation barrier; all routing on secondary (SELV) side |
| **P-DEV-01** (commit convention) | All commits on branch use `hw:` prefix |

---

## 11. Acceptance Criteria

- [ ] All legacy invalid signal traces deleted (Phase 0 complete; git commit separate)
- [ ] J8 footprint repositioned to centre (25.50, 28.80) mm; Row A at x=17.81mm, Row B at x=33.19mm (Phase 1 complete; git commit separate)
- [ ] J6 (DS18B20 connector) repositioned to left zone (x < 17.81 mm) (Phase 1)
- [ ] DRC: 0 `shorting_items` after Phase 0
- [ ] DRC: 0 `solder_mask_bridge` after Phase 0
- [ ] All nets routed in Phases 2–7 using the authoritative pad table from issue #148
- [ ] 0 unconnected items (pads 25, 26, 30, 37, 39 intentionally NC — excluded)
- [ ] DRC: 0 rule violations (shorts, clearance) after Phase 8
- [ ] All power traces >= 1.0 mm: `+5V`, `+12V`, `+3V3`, `GND`, `BOOST_SW`
- [ ] All signal traces >= 0.25 mm
- [ ] J8 pads 25, 26, 30, 37, 39 have zero connected tracks in the PCB file
- [ ] BOOST_SW loop (L1 --> U1 --> D1) enclosed area < 200 mm²
- [ ] Zero signal traces cross the ESP32 footprint boundary (x = 15–36 mm)
- [ ] All Row A GPIO traces at x ≤ 17.81 mm; all Row B GPIO traces at x ≥ 33.19 mm
- [ ] Both GND zones filled; no isolated copper islands
- [ ] Gerber files in `hardware/kicad/gerbers/` committed on branch
- [ ] DRC report `hardware/kicad/drc_result.rpt` attached to PR
