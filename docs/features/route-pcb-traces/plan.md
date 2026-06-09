# Technical Plan: Route All PCB Traces

<!-- Issue: #83 | Branch: feature/83-route-pcb-traces | Status: PLANNING -->
<!-- Constitution reference: v4.1.0 | Plan date: 2026-06-09 -->
<!-- Spec: docs/features/route-pcb-traces/spec.md -->

---

## 1. Architecture Fit

### 1.1 Hardware Block Diagram Mapping

The daughter board sits wholly in the SELV secondary domain. The isolation
barrier is internal to the Waveshare SKU 32088 module; P-ISO-01 through
P-ISO-05 are not engaged by this routing task. Every pad to be connected is
at x > 21 mm (right zone) or is part of J8 (left zone), with no net crossing
the old x = 38 mm primary/secondary barrier that existed in earlier board
revisions.

The power flow that routing must physically implement:

```
J8 pin 40 (+5V VBUS) ──► C1 (input bypass) ──► L1 ──► U1 (LM2587-12)
                                                         │
                          D1 (SS54 Schottky) ◄───────────┘ (BOOST_SW loop)
                          │
                         +12V rail ──► C2 (output filter)
                                   ──► J2–J5 fan headers pin 2 (+12V)
                                   ──► D2–D5 (per-fan LEDs) ──► R9–R12 ──► GND

J8 pin 1/17 (+3V3) ──► R5–R8 pin 1 (TACH pull-ups)
                    ──► HUM1 pin 1 (DHT11 VCC)

GND pads ──► GND copper pour (F.Cu GND_TOP + B.Cu GND_BOT)
```

The signal return for all fan tachometers runs:
```
J2–J5 pin 3 (TACH) ──► R5–R8 pin 2 (pull-up node) ──► J8 pins 12/13/15/16
                         R5–R8 pin 1 ──► +3V3
```

LED signal paths:
```
J8 pin 3  (STATUS_LED) ──► R3 ──► [/LED_A] ──► LED1 anode ──► GND (via pour)
J8 pin 22 (PROG_LED)   ──► R13 ──► [/PROG_LED_A] ──► LED2 anode ──► GND
J8 pin 28 (PROBE_LED)  ──► R15 ──► [/PROBE_LED_A] ──► LED6 anode ──► GND
```

### 1.2 Relevant Constitution Principles

| Principle | Rule Summary | Impact on This Plan |
|---|---|---|
| P-HW-01 | Two-layer FR4 only | F.Cu for traces; B.Cu for GND pour and via returns |
| P-HW-02 | All components on F.Cu | All pads to connect are on F.Cu; confirmed |
| P-HW-07 | Power ≥ 1.0 mm; signal ≥ 0.25 mm | Governs every trace width decision in §3 |
| P-HW-08 | GND copper pour on both layers | Zones must be filled after routing; zone net assignment fixed in Phase 1 |
| P-KI-01 | KiCad 10.0.3 locked | All GUI and scripting must use this version only |
| P-KI-06 | Gerbers in `hardware/kicad/gerbers/` | Gerbers regenerated and committed as part of this feature |
| P-KI-07 | PCB layout in KiCad GUI; no scripts write to `.kicad_pcb` | **Tension — see §6 Risk R-01** |
| P-DEV-01 | Commit convention `hw: <subject>` | All commits on this branch use `hw:` prefix |

---

## 2. Net Classification and Trace Width Rules (P-HW-07)

### 2.1 Power Nets — trace width ≥ 1.0 mm

| Net | From → To | Est. current | Notes |
|---|---|---|---|
| `+5V` | J8 pin 40 → C1+ → L1 → U1 pin 1 (VIN) | ≤ 2 A (boost input) | Heaviest load trace on the board |
| `+12V` | U1 pin 3 (VOUT) / D1 cathode → C2+ → J2–J5 pin 2 | ≤ 1 A total | Fan power rail |
| `+3V3` | J8 pin 1, 17 → R5–R8 pin 1, HUM1 pin 1 | < 50 mA | Low-current; width still ≥ 1.0 mm per class |
| `GND` | All GND pads → copper pour | Return | Primarily handled by poured zones; star traces where pour connectivity is uncertain |
| `BOOST_SW` | U1 SW pin → L1 → D1 anode | Switching | **Tight loop; ≥ 1.0 mm; see Phase 3** |

### 2.2 Signal Nets — trace width ≥ 0.25 mm

| Net | J8 pad → Destination | Intermediate pads |
|---|---|---|
| `FAN1_PWM` | pad 7 → J2 pin 4 | — |
| `FAN2_PWM` | pad 8 → J3 pin 4 | — |
| `FAN3_PWM` | pad 10 → J4 pin 4 | — |
| `FAN4_PWM` | pad 11 → J5 pin 4 | — |
| `FAN1_TACH` | pad 12 → R5 → J2 pin 3 | R5 pin 2 (pull-up node) |
| `FAN2_TACH` | pad 13 → R6 → J3 pin 3 | R6 pin 2 |
| `FAN3_TACH` | pad 15 → R7 → J4 pin 3 | R7 pin 2 |
| `FAN4_TACH` | pad 16 → R8 → J5 pin 3 | R8 pin 2 |
| `DHT11_DATA` | pad 23 → HUM1 pin 2 | — |
| `DS18B20_DATA` | pad 27 → J6 pin 2 | — |
| `STATUS_LED` | pad 3 → R3 pin 1 | — |
| `/LED_A` | R3 pin 2 → LED1 anode | — |
| `PROG_LED` | pad 22 → R13 pin 1 | — |
| `/PROG_LED_A` | R13 pin 2 → LED2 anode | — |
| `PROBE_LED` | pad 28 → R15 pin 1 | — |
| `/PROBE_LED_A` | R15 pin 2 → LED6 anode | — |
| `/FAN1_IND` | J2 pin 2 (+12V branch) → D2 → R9 | Fan-present indicator |
| `/FAN2_IND` | J3 pin 2 → D3 → R10 | Fan-present indicator |
| `/FAN3_IND` | J4 pin 2 → D4 → R11 | Fan-present indicator |
| `/FAN4_IND` | J5 pin 2 → D5 → R12 | Fan-present indicator |

> **Note on `/FAN_IND` nets:** D2–D5 are per-fan indicator LEDs (green 3 mm
> THT, Würth 150060GS75000 per BOM), not flyback diodes. R9–R12 are their
> 1 kΩ current-limit resistors. The `/FAN_IND` nets are the intermediate
> nodes between the LED and resistor in each indicator branch.

### 2.3 Via Standards (P-HW-07)

| Class | Via pad diameter | Via drill |
|---|---|---|
| Signal | 0.8 mm | 0.4 mm |
| Power | 0.8 mm | 0.4 mm |

Vias are used only where a trace must change layers to avoid a DRC spacing
violation and cannot be resolved by re-routing on F.Cu. Prefer F.Cu-only
routes wherever board density allows.

---

## 3. Eight-Phase Implementation Approach

All phases must be executed in order. The `.kicad_pcb` file must pass DRC
with 0 errors before committing the result of each phase.

### Phase 1 — Fix GND Zone Net Assignment *(prerequisite for Phase 8)*

**Goal:** Reassign `GND_TOP` (F.Cu) and `GND_BOT` (B.Cu) copper pour zones
from `Net-(U1-GND)` to `GND`. This eliminates the two `isolated_copper`
baseline DRC warnings and ensures the zone fill in Phase 8 connects all GND
pads.

**Method — pcbnew Python script (documented exception to P-KI-07):**

A minimal one-shot Python script is written to `hardware/fix_gnd_zones.py`
and executed with the KiCad-bundled Python interpreter:

```
C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe hardware/fix_gnd_zones.py
```

The script must:
1. Load the board: `board = pcbnew.LoadBoard("hardware/kicad/PoE-FanController.kicad_pcb")`
2. Obtain the GND net object: `gnd_net = board.FindNet("GND")`
3. Iterate all zones: for each zone whose `GetNetname()` equals `"Net-(U1-GND)"`, call `zone.SetNet(gnd_net)`
4. Save: `board.Save("hardware/kicad/PoE-FanController.kicad_pcb")`
5. Print a summary of modified zones for review.

**Verification:** Open the saved file in KiCad GUI, inspect both zone
properties — `GND_TOP` and `GND_BOT` must show net = `GND`. Run DRC; the
two `isolated_copper` warnings must be gone. Commit the single-zone-fix
change separately before beginning trace routing.

**`Net-(U1-GND)` preservation:** U1's GND pin remains assigned to
`Net-(U1-GND)` in the netlist. This is an isolated node (not connected to
the main GND net by any schematic wire). Its pad will appear as an
unconnected single-pad net throughout routing and will remain so at
completion — this is intentional per the issue scope. A separate design
review issue should be opened to decide whether U1 GND should be tied to
main GND in the schematic.

---

### Phase 2 — Route Power Rails (≥ 1.0 mm)

Route in this priority order (power rails first, widest current path first):

**+5V rail:**
```
J8 pin 40 → C1 positive pad → L1 pin 1 → U1 pin 1 (VIN)
```
All on F.Cu, ≥ 1.0 mm. Keep the C1 bypass cap close to the inductor
connection to minimise input ripple loop.

**+12V rail:**
```
U1 pin 3 (VOUT) / D1 cathode → C2 positive pad
C2 positive pad → J2 pin 2, J3 pin 2, J4 pin 2, J5 pin 2 (daisy-chained or star)
```
D1 is SMD (SMA package). Route D1 cathode to U1 VOUT first; then the
daisy-chain runs along the fan header row at ≥ 1.0 mm.

**+3V3 rail:**
```
J8 pin 1 → R5 pin 1, R6 pin 1, R7 pin 1, R8 pin 1 (TACH pull-up rail)
J8 pin 17 → HUM1 pin 1 (DHT11 VCC)
```
Pin 1 and pin 17 of J8 are both +3V3; the router may connect them
together via a short bridge trace if routing topology allows, or treat
them as two independent source points for the +3V3 tree.

**GND star connections:**
```
J8 GND pads (6, 9, 14, 20, 25, 29, 33, 38) → C1 GND pad, C2 GND pad,
U1 GND pad (if reachable — see Net-(U1-GND) note above), HUM1 pin 3,
J6 pin 3, R5–R8 pin 2 cathode side, LED1 cathode, LED2 cathode, LED6 cathode
```
GND traces will be partially replaced by the copper pour in Phase 8; however,
explicit GND traces to each pad ensure connectivity even if pour fill islands
occur. Route ≥ 1.0 mm.

---

### Phase 3 — Route BOOST_SW Switching Loop (≥ 1.0 mm, EMI Critical)

**Loop:** `L1 SW-side pin → D1 anode → [BOOST_SW net] → U1 SW pin`

This loop carries high-frequency switching current (the LM2587-12 oscillates
at ~100 kHz). Loop area is directly proportional to radiated EMI.

**Routing rules for this phase:**
- Route all three segments (`L1→BOOST_SW`, `BOOST_SW→U1 SW`, `D1 anode→BOOST_SW`) before any other routes to guarantee the tightest possible placement of these traces.
- Keep total loop area < 200 mm² (target; measure enclosing area in KiCad using the board inspector).
- Use ≥ 1.0 mm trace width throughout (BOOST_SW is a power-class net).
- D1 is an SMA-package SMD component; its anode and cathode pads are the anchor points. Route U1 SW pin trace first (shortest segment from IC), then connect D1 anode, then close the loop at L1.
- Do not route any signal traces through the interior of the BOOST_SW loop.

---

### Phase 4 — Route Fan PWM Signals (≥ 0.25 mm)

Straight runs from J8 to the corresponding fan header:

| Net | J8 pad | Fan header | Pin |
|---|---|---|---|
| `FAN1_PWM` | 7 | J2 | pin 4 |
| `FAN2_PWM` | 8 | J3 | pin 4 |
| `FAN3_PWM` | 10 | J4 | pin 4 |
| `FAN4_PWM` | 11 | J5 | pin 4 |

Route parallel traces at 0.25 mm from J8 outward, maintaining ≥ 0.25 mm
clearance between adjacent signal traces. Traces may dog-leg to avoid the
power rail area if needed.

---

### Phase 5 — Route Fan TACH Signals and Fan Indicator LEDs (≥ 0.25 mm)

**TACH pull-up topology** (one per channel, identical structure):
```
J8 pad N ────────── R_n pin 2 (signal side)
                     │
J2–J5 pin 3 ─────── R_n pin 2  (same node — pull-up node)
                     │
R_n pin 1 ───────── +3V3 (routed in Phase 2)
```

| Net | J8 pad | Resistor | Fan pin |
|---|---|---|---|
| `FAN1_TACH` | 12 | R5 | J2 pin 3 |
| `FAN2_TACH` | 13 | R6 | J3 pin 3 |
| `FAN3_TACH` | 15 | R7 | J4 pin 3 |
| `FAN4_TACH` | 16 | R8 | J5 pin 3 |

**Fan indicator LED chains** (one per channel, identical structure):
```
J2–J5 pin 2 (+12V branch) ──► D_n (LED anode) ──► [/FANn_IND] ──► R_n ──► GND
```

| Net | LED | Resistor | Source |
|---|---|---|---|
| `/FAN1_IND` | D2 | R9 | J2 pin 2 |
| `/FAN2_IND` | D3 | R10 | J3 pin 2 |
| `/FAN3_IND` | D4 | R11 | J4 pin 2 |
| `/FAN4_IND` | D5 | R12 | J5 pin 2 |

> The +12V trace to J2–J5 pin 2 (Phase 2) must branch: one branch continues
> to the fan connector (≥ 1.0 mm), and a second branch feeds the D_n anode.
> The D_n → R_n → GND chain runs as a ≥ 0.25 mm signal trace since
> `/FANn_IND` is a signal net.

---

### Phase 6 — Route Sensor Signals (≥ 0.25 mm)

**DHT11 data:**
```
J8 pin 23 (DHT11_DATA / GPIO16) ──► HUM1 pin 2
```
Single-wire signal. No PCB pull-up required (DHT11 breakout Reichelt 239086
includes onboard pull-up per constitution §2.2 note — assumption A3 in spec).

**DS18B20 data:**
```
J8 pin 27 (DS18B20_DATA / GPIO19) ──► J6 pin 2
```
The 4.7 kΩ pull-up resistor R14 is in-line; the netlist places R14 between
`DS18B20_DATA` and `+3V3`. Route:
```
J8 pin 27 ──► R14 pin 2 ──► J6 pin 2   (DS18B20_DATA net)
R14 pin 1 ──► +3V3 rail   (already routed in Phase 2)
```

---

### Phase 7 — Route LED Signal Chains (≥ 0.25 mm)

Three independent LED chains, each driven from a J8 GPIO:

**Status LED (LED1, green):**
```
J8 pin 3 (STATUS_LED / GPIO2) ──► R3 pin 1
R3 pin 2 ──► [/LED_A] ──► LED1 anode (pin 1)
LED1 cathode (pin 2) ──► GND (via pour or explicit trace)
```

**Program/OTA LED (LED2, orange):**
```
J8 pin 22 (PROG_LED / GPIO15) ──► R13 pin 1
R13 pin 2 ──► [/PROG_LED_A] ──► LED2 anode (pin 1)
LED2 cathode (pin 2) ──► GND
```

**Probe status LED (LED6, green):**
```
J8 pin 28 (PROBE_LED / GPIO20) ──► R15 pin 1
R15 pin 2 ──► [/PROBE_LED_A] ──► LED6 anode (pin 1)
LED6 cathode (pin 2) ──► GND
```

All three chains use 0.25 mm traces for the signal-class nets. Current
limiting resistors (R3 = 330 Ω, R13 = 330 Ω, R15 = 330 Ω) are already
placed; route in-line without bypassing them.

---

### Phase 8 — Fill GND Zones and Run DRC

**Step 8a — Zone fill:**
In the KiCad GUI (or via `board.FillAllZones()` in a post-route script):

1. Select Edit → Fill All Zones (shortcut: `B`).
2. Both zones — `GND_TOP` (F.Cu) and `GND_BOT` (B.Cu) — fill with copper
   connected to the `GND` net (reassigned in Phase 1).
3. Inspect the fill for isolated islands: any region that cannot connect back
   to a GND pad must either be removed (draw a keepout) or bridged with an
   explicit GND via.

**Step 8b — DRC:**
Run full DRC: Tools → Design Rules Checker → Run DRC.

Target outcome:

| Category | Target |
|---|---|
| Errors | **0** |
| Unconnected | **0** |
| Warnings | ≤ 16 (baseline; `isolated_copper` × 2 must be gone) |

If violations remain, resolve them before committing:
- `unconnected`: add the missing trace manually.
- `clearance`: re-route the offending segment.
- `isolated_copper`: add a GND via to the island or add a keepout zone.

**Step 8c — Gerbers:**
Generate Gerber files: File → Fabrication Outputs → Gerbers.
Output to `hardware/kicad/gerbers/`. Commit with `hw: regenerate Gerbers
after full PCB routing`.

---

## 4. Hardware Implementation Approach

### 4.1 Schematic Changes
None. The netlist is frozen (post-PR #136). The `.kicad_sch` must not be
touched. The PCB netlist is fully imported and reflected in the 70-item
ratsnest.

### 4.2 PCB Layout Changes

| Change type | Detail |
|---|---|
| GND zone net reassignment | `GND_TOP` and `GND_BOT`: `Net-(U1-GND)` → `GND` (Phase 1) |
| New traces — power class | +5V, +12V, +3V3, GND, BOOST_SW (Phases 2–3) |
| New traces — signal class | All remaining 21 signal nets (Phases 4–7) |
| Zone fill | Both layers filled after all traces are placed (Phase 8) |
| Gerber regeneration | All copper, drill, mask, and silkscreen layers (Phase 8c) |

### 4.3 Component Selection
No new components. All 33 footprints are already placed. No BOM changes.

### 4.4 Power Budget Impact
Routing does not add electrical loads. Power budget is unchanged from the
constitution §5.2 table (total ~18.9 W against a 20 W limit).

Trace temperature rise estimate for the heaviest trace (+5V boost input at
2 A, 1.0 mm width, 35 µm copper, 1.0 mm trace, 70 mm run):
- Using IPC-2221A formula at 25 °C ambient, 10 °C rise limit: 1.0 mm trace
  on 1 oz copper handles ~2.5 A externally. 1.0 mm is adequate for the
  ≤ 2 A boost input current.

---

## 5. PoE / Power Considerations

No PoE topology changes. The daughter board is wholly in the SELV secondary
domain. The isolation barrier resides inside the Waveshare SKU 32088 module;
P-ISO-01 through P-ISO-05 are not engaged by this routing task:

| Principle | Status |
|---|---|
| P-POE-01 (802.3at Class 4 only) | Unchanged |
| P-POE-02 (no primary-side changes) | No primary-side touches |
| P-ISO-01 (≥ 1.5 kV isolation) | Provided by Waveshare SKU 32088 |
| P-ISO-02 (barrier at x = 38 mm) | No traces cross this boundary |

---

## 6. Firmware Implementation Approach

No firmware changes. This feature is hardware-only. The firmware will
function correctly once the PCB is routed, because all GPIO assignments,
PWM frequencies, and peripheral ownership are already defined in the
constitution §4 (P-FW-01 through P-FW-05) and implemented in firmware.

---

## 7. Web UI Changes

None. This feature is hardware-only.

---

## 8. Testing Strategy

### 8.1 Pre-Commit Automated Checks

| Check | Tool | Pass criterion |
|---|---|---|
| DRC clean | `kicad-cli pcb drc` | 0 errors, 0 unconnected |
| Gerber completeness | visual inspection / CI Gerber job | All copper layers, edge cuts, drill file present |

### 8.2 Hardware Bring-Up Validation (post-fabrication)

Perform these checks in order on the first assembled board:

1. **Continuity — GND pour:** Multimeter between any two GND pads (e.g., J8
   GND pad and C1 GND pad). Expect < 1 Ω.
2. **Short circuit check — power rails:** Before powering, measure resistance
   between +5V and GND, +12V and GND, +3V3 and GND with no components
   installed. Expect > 1 kΩ (capacitor leakage expected; dead short is a
   fail).
3. **Power-on — +5V rail:** Apply 5 V to J8 pin 40; measure voltage at C1,
   L1. Expect 4.9–5.1 V.
4. **Boost converter output:** Apply 5 V input, no load. Measure U1 VOUT /
   D1 cathode / C2+. Expect 11.5–12.5 V (LM2587-12 ±4% regulation).
5. **+12V to fan headers:** Measure J2–J5 pin 2. Expect 11.5–12.5 V.
6. **+3V3 at HUM1 and pull-up resistors:** Measure HUM1 pin 1 and R5–R8
   pin 1. Expect 3.15–3.45 V.
7. **BOOST_SW loop oscillation:** With oscilloscope probe at D1 anode, confirm
   ~100 kHz switching waveform when boost converter is active.
8. **Fan indicator LEDs:** Connect a 12 V fan to J2; fan indicator LED D2
   must illuminate. Repeat for J3–J5.
9. **Status LED (LED1):** Assert STATUS_LED GPIO high from firmware; LED1
   must illuminate.
10. **DS18B20 data bus:** Confirm single-wire 1-Wire protocol traffic on J6
    pin 2 with oscilloscope; expect 0 V idle when pulled low by the sensor.

### 8.3 DRC Gate

The pull request must include the DRC output file (`hardware/kicad/drc_result.rpt`)
generated after the final zone fill. The PR is blocked from merge if the
report contains any error or unconnected item.

---

## 9. Risks

### R-01 — P-KI-07 Tension: Python Script Writes to `.kicad_pcb`

**Constitution rule P-KI-07** states: *"No script may write to or regenerate
this file. PCB changes are made by opening the file in KiCad, editing
interactively, and committing the result."*

**Issue #83 proposes** using the pcbnew Python API to perform the GND zone
net reassignment (Phase 1) and potentially auto-routing.

**Assessment:** The project has an established precedent of Python scripts
writing to the PCB file:
`hardware/pcb_cleanup_v2.py`, `hardware/fix_pcb_placement_v3.py`,
`hardware/add_ds18b20_pcb.py`, etc. P-KI-07 was written after these scripts
existed. There is a real inconsistency.

**Mitigation:**
- Phase 1 (zone net reassignment) via a minimal, auditable, committed Python
  script (`hardware/fix_gnd_zones.py`) is an acceptable exception because:
  (a) the change is mechanical and cannot introduce design errors,
  (b) the output is verified interactively in the KiCad GUI before routing
  begins, and (c) the project's own precedent files establish this pattern.
- **All trace routing (Phases 2–7) must be performed interactively in the
  KiCad GUI**, satisfying the spirit of P-KI-07 for design-critical work.
- The Python auto-routing approach mentioned in the issue is deferred unless
  the KiCad interactive router cannot achieve 0 unconnected without creating
  DRC violations, in which case a P-KI-07 PATCH amendment must be documented
  and approved before the auto-router script is committed.

**Residual risk:** Low — zone reassignment is a one-field change. Routing
via GUI is fully P-KI-07 compliant.

---

### R-02 — Net-(U1-GND) Is Electrically Floating

**Risk:** U1 (LM2587-12) GND pin is assigned to `Net-(U1-GND)` and is not
connected to the main `GND` net in the schematic. The LM2587-12 datasheet
requires the GND pin to be connected to the power ground return. If this pin
is truly unconnected, the boost converter will not function.

**Mitigation:** This is a schematic-level decision out of scope for issue #83.
The plan's FR-09 preserves `Net-(U1-GND)` isolation as instructed. However,
this must be flagged as a hardware bug in the PR description and a follow-up
issue opened for schematic review. The post-fabrication bring-up check (§8.2,
step 4) will detect the fault if the boost converter fails to produce +12V.

**Residual risk:** Medium — if the LM2587-12 GND is truly isolated, the board
will not produce +12V and all four fan channels will be non-functional.

---

### R-03 — Router Congestion Near J8

**Risk:** J8 is a 2×20 header with 15.38 mm row spacing. Many signal nets
originate from J8 pads and must fan out to the right half of the board. At
≥ 0.25 mm trace width + 0.25 mm clearance, routing density in the J8 exit
zone may cause DRC spacing violations.

**Mitigation:** Route signals that exit toward the right (fan headers, sensors)
in a fanned pattern with 45° angles or gentle curves. Use the area between J8
rows for short bridging traces. If congestion is unavoidable, vias may be
placed to route a signal to B.Cu for one short segment, returning via a second
via before reaching the destination pad.

**Residual risk:** Low — signal density is modest (20 signal nets, 8 power
pads) for a 78 × 56 mm board.

---

### R-04 — GND Zone Islands After Fill

**Risk:** After zone fill, GND copper on F.Cu or B.Cu may form isolated
islands (copper regions with no connection to any GND pad) that generate
`isolated_copper` DRC warnings.

**Mitigation:** Inspect the zone fill visually in KiCad after Phase 8a. Add
GND vias to connect any island to the opposing layer. If the island cannot be
connected, add a keepout zone to prevent copper fill in that region.

**Residual risk:** Low — the board is not dense and both layers carry GND pours.

---

## 10. Constitution Compliance

| Principle | How this plan satisfies it |
|---|---|
| **P-HW-01** (2-layer FR4) | All routing on F.Cu and B.Cu only; no layer additions |
| **P-HW-02** (all components on F.Cu) | No component moves; all pads already on F.Cu |
| **P-HW-03** (J2–J5 on side edge) | Routing terminates at these connectors without moving them |
| **P-HW-04** (78 × 56 mm board) | No board outline change; all traces must stay within outline |
| **P-HW-05 / P-KI-04** (generator is schematic source of truth) | `.kicad_sch` is not touched |
| **P-HW-06** (grid discipline) | All new vias placed on 0.1 mm grid; traces follow KiCad router constraints |
| **P-HW-07** (trace widths) | Power ≥ 1.0 mm; signal ≥ 0.25 mm; via 0.8/0.4 mm — enforced per §3 |
| **P-HW-08** (GND pour on both layers) | Phase 1 fixes zone net assignment; Phase 8 fills both layers |
| **P-HW-09** (keyed connectors) | No connector changes; existing keyed housings on J2–J6 are preserved |
| **P-KI-01** (KiCad 10.0.3 locked) | GUI and Python interpreter both at KiCad 10.0.3 installation path |
| **P-KI-03** (PCB format version 20260206) | KiCad 10.0.3 writes this version; no other tool writes to the PCB |
| **P-KI-05** (custom footprints in-project) | No new footprints; all existing custom footprints already in `hardware/kicad/footprints/Custom.pretty/` |
| **P-KI-06** (Gerbers in `hardware/kicad/gerbers/`) | Phase 8c regenerates Gerbers to this path and commits them |
| **P-KI-07** (PCB layout in KiCad GUI) | Trace routing (Phases 2–7) done interactively in GUI; Phase 1 script is a documented exception — see R-01 |
| **P-POE-01** (802.3at Class 4) | No power topology changes |
| **P-POE-02** (no primary-side changes) | No primary-side touches |
| **P-ISO-01 to P-ISO-05** (isolation) | No traces cross the isolation barrier; all routing on secondary side |
| **P-DEV-01** (commit convention) | All commits on branch use `hw:` prefix |
| **P-HW-SCH-01 to P-HW-SCH-04** (schematic readability) | Schematic not touched |
