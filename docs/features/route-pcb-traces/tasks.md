# Tasks: Route All PCB Traces

<!-- Feature: route-pcb-traces | Issue: #83 | Branch: feature/83-route-pcb-traces -->
<!-- Generated: 2026-06-09 | Author: feature-breakdown-agent -->

---

## Summary

- **Total tasks:** 9 (T001–T009)
- **Layers covered:** Hardware: Layout, Hardware: DRC, Documentation, Issue update
- **GitHub parent issue:** [#83 — hw(pcb): route all PCB traces (51 unconnected ratsnest)](https://github.com/nielsverhoeven/PoE-FanController/issues/83)
- **Branch:** eature/83-route-pcb-traces
- **Constitution prerequisite:** v4.1.0 (locked; no amendments required)
- **Layers NOT required:** Hardware: Schematic, Hardware: ERC, Hardware: BOM, Firmware: Module, Firmware: Config, Web UI, Unit Tests
  (hardware layout-only change; no schematic edits, no netlist changes, no firmware logic)

---

## Dependency Graph

\\\mermaid
graph TD
    T001["T001\nFix GND Zone\nNet Assignment"]
    T002["T002\nRoute Power Rails\n≥1.0mm"]
    T003["T003\nRoute BOOST_SW\nSwitching Loop"]
    T004["T004\nRoute Fan PWM\nSignals"]
    T005["T005\nRoute Fan TACH &\nIndicator LEDs"]
    T006["T006\nRoute Sensor\nSignals"]
    T007["T007\nRoute LED Signal\nChains"]
    T008["T008\nFill GND Zones\n& Run DRC"]
    T009["T009\nRegenerate Gerbers\n& Documentation"]

    T001 --> T002
    T002 --> T003
    T002 --> T004
    T002 --> T005
    T002 --> T006
    T002 --> T007
    T003 --> T008
    T004 --> T008
    T005 --> T008
    T006 --> T008
    T007 --> T008
    T008 --> T009
\\\

**Text summary:**
\\\
T001 → T002 ─┬─ T003 ─┐
             ├─ T004 ─┤
             ├─ T005 ─┼─ T008 → T009
             ├─ T006 ─┤
             └─ T007 ─┘
\\\

- T001 (GND zone fix) is a prerequisite with no dependencies; it gates T002.
- T002 (power rails) completes before the four signal routing tasks (T003–T007) can start.
- T003–T007 can execute in parallel (all depend only on T002).
- T008 (zone fill + DRC) is the converging gate; all preceding tasks must be complete.
- T009 (Gerbers + documentation) closes the feature.

---

## Task List

### T001: Fix GND Zone Net Assignment

- **Layer:** Hardware: Layout
- **Description:**
  Create and execute a Python script to reassign the two GND copper pour zones from the isolated
  \Net-(U1-GND)\ net to the main \GND\ net. This is a documented exception to P-KI-07 (pcbnew
  scripts forbidden) because no trace routing touches these zones — only their net assignment is
  corrected. The script must be saved to \hardware/fix_gnd_zones.py\ and executed via the KiCad
  bundled Python interpreter:

  \\\
  C:\\Users\\Niels\\AppData\\Local\\Programs\\KiCad\\10.0\\bin\\python.exe hardware/fix_gnd_zones.py
  \\\

  **Script requirements:**
  - Load board: \oard = pcbnew.LoadBoard("hardware/kicad/PoE-FanController.kicad_pcb")\
  - Find GND net: \gnd_net = board.FindNet("GND")\
  - Iterate all zones; for each zone where \GetNetname() == "Net-(U1-GND)"\, call \zone.SetNet(gnd_net)\
  - Save: \oard.Save("hardware/kicad/PoE-FanController.kicad_pcb")\
  - Print summary of modified zones

  **Verification:**
  Open the modified \.kicad_pcb\ in KiCad GUI, inspect both \GND_TOP\ (F.Cu) and \GND_BOT\ (B.Cu)
  zone properties — both must show \
et "GND"\ (not \
et "Net-(U1-GND)"\). Run DRC; the two
  \isolated_copper\ baseline warnings must be eliminated. Commit only this change before routing begins.

  **Constraints:**
  - U1's GND pin (\Net-(U1-GND)\) remains isolated in the netlist — NO routed connection to main GND is permitted.
  - Only zone \
et\ assignments are changed; the component pin netlist is untouched.

- **Depends on:** none
- **Acceptance:** 
  DRC report shows 0 isolated_copper warnings for zones; `GND_TOP` and `GND_BOT` both display
  `net "GND"` in zone properties; script committed to `hardware/fix_gnd_zones.py`.
- **GitHub issue:** [#139](https://github.com/nielsverhoeven/PoE-FanController/issues/139)

---

### T002: Route Power Rails (≥1.0 mm)

- **Layer:** Hardware: Layout
- **Description:**
  Route all power distribution rails with ≥1.0 mm trace width on F.Cu. All pads are at component positions;
  all traces run on the front copper layer. Route in priority order:

  **+5V rail (heaviest load — ≤ 2 A boost input):**
  \\\
  J8 pin 40 → C1 positive pad → L1 pin 1 → U1 pin 1 (VIN)
  \\\
  Keep C1 bypass cap close to L1 connection to minimize input ripple loop.

  **+12V rail (fan power — ≤ 1 A total):**
  \\\
  U1 pin 3 (VOUT) / D1 cathode → C2 positive pad
  C2 positive pad → J2 pin 2 → J3 pin 2 → J4 pin 2 → J5 pin 2 (daisy-chain to fan headers)
  \\\
  D1 is SMD (SMA package); route D1 cathode first, then continue the daisy-chain to all fan headers.
  This rail will branch in Phase 5 to feed the per-fan indicator LED diodes.

  **+3V3 rail (low-current — < 50 mA):**
  \\\
  J8 pin 1 → R5 pin 1, R6 pin 1, R7 pin 1, R8 pin 1 (TACH pull-up rail)
  J8 pin 17 → HUM1 pin 1 (DHT11 VCC)
  \\\
  J8 pins 1 and 17 are both +3V3; may be bridged together or routed as separate distribution trees.

  **GND star connections (power return paths — ≥1.0 mm):**
  \\\
  J8 GND pads (6, 9, 14, 20, 25, 29, 33, 38) → C1 GND, C2 GND, HUM1 pin 3, J6 pin 3,
  R5–R8 pin 2 (pull-up cathode side), LED1 cathode, LED2 cathode, LED6 cathode
  \\\
  GND traces will be partially replaced by the copper pour in Phase 8; explicit traces ensure
  connectivity independent of pour fill topology.

  **Method:**
  Use KiCad interactive router (Ctrl+E from a trace endpoint, or Route → Route Tracks). All traces
  on F.Cu only. Set trace width to 1.0 mm (or wider if netclass allows). Use vias (0.8 mm pad /
  0.4 mm drill) only where necessary to avoid DRC spacing violations (prefer F.Cu-only routes).

- **Depends on:** T001
- **Acceptance:**
  All five power nets (+5V, +12V, +3V3, GND, BOOST_SW partial) have continuous routed paths from
  source to all destination pads; every segment ≥1.0 mm wide on F.Cu; DRC still reports 0 errors
  (ratsnest count reduced from 70 to approximately 40).
- **GitHub issue:** [#140](https://github.com/nielsverhoeven/PoE-FanController/issues/140)

---

### T003: Route BOOST_SW Switching Loop (≥1.0 mm, Tight EMI Loop)

- **Layer:** Hardware: Layout
- **Description:**
  Route the high-frequency switching node (BOOST_SW) connecting the boost converter IC, inductor,
  and diode. This loop carries ~100 kHz switching current; loop area directly affects radiated EMI.

  **Loop topology:**
  \\\
  L1 switching pin → BOOST_SW node → D1 anode → [back to] BOOST_SW node → [back to] U1 SW pin
  \\\

  **Routing rules — critical for EMI compliance:**
  - Total enclosed loop area must be < 200 mm² (measure in KiCad PCB editor Inspect tool after routing).
  - All traces ≥1.0 mm wide (BOOST_SW is a power-class net per FR-03 and P-HW-07).
  - Route on F.Cu only; no via insertion unless unavoidable.
  - **Do NOT route any signal traces through the interior of the BOOST_SW loop.**
  - Use the tightest possible geometry; minimize any dogleg or detour.

  **Recommended sequence (to ensure shortest segments):**
  1. Route U1 SW pin first (shortest segment from IC to the loop).
  2. Connect D1 anode to the BOOST_SW node via tight trace.
  3. Connect L1 switching pin to close the loop (complete the three-segment circuit).

  **Verification:**
  After routing, measure loop area using KiCad Inspect tool (place a rectangle around the loop and
  record area in mm²). If area ≥ 200 mm², re-route with tighter geometry before moving to Phase 4.

- **Depends on:** T002
- **Acceptance:**
  BOOST_SW node (L1 → D1 → U1 SW) is fully routed with ≥1.0 mm traces; enclosed loop area measures
  < 200 mm² in KiCad Inspect; no signal traces pass through the loop interior; DRC still 0 errors.
- **GitHub issue:** [#141](https://github.com/nielsverhoeven/PoE-FanController/issues/141)

---

### T004: Route Fan PWM Signals (≥0.25 mm)

- **Layer:** Hardware: Layout
- **Description:**
  Route the four fan PWM control signals from the ESP32-P4 (via J8) to the respective fan headers.
  These are logic-level signals (0–3.3V digital); trace width ≥0.25 mm per signal net class (FR-04).

  **Routing table:**

  | Net | J8 pad | Destination | Trace width |
  |---|---|---|---|
  | FAN1_PWM | 7 | J2 pin 4 | ≥0.25 mm |
  | FAN2_PWM | 8 | J3 pin 4 | ≥0.25 mm |
  | FAN3_PWM | 10 | J4 pin 4 | ≥0.25 mm |
  | FAN4_PWM | 11 | J5 pin 4 | ≥0.25 mm |

  **Routing constraints:**
  - Parallel traces at ≥0.25 mm width; maintain ≥0.25 mm clearance between adjacent signal traces.
  - Traces may dog-leg to avoid the +12V power rail area if needed (F.Cu routing only).
  - No via insertion required (all pads on F.Cu).
  - Route as independent traces (no daisy-chaining required).

  **Method:**
  Use KiCad interactive router. Set net to route, set trace width to 0.25 mm, and draw each signal
  path from J8 to the target fan header pin. If spacing is tight near J8 or the fan headers, carefully
  position traces to maintain clearance margins.

- **Depends on:** T002
- **Acceptance:**
  All four FAN*_PWM nets are fully routed from J8 source pad to J2–J5 pin 4 destinations; every trace
  ≥0.25 mm wide on F.Cu; no unrouted ratsnest for these nets; DRC still 0 errors.
- **GitHub issue:** [#142](https://github.com/nielsverhoeven/PoE-FanController/issues/142)

---

### T005: Route Fan TACH Signals and Indicator LED Chains (≥0.25 mm)

- **Layer:** Hardware: Layout
- **Description:**
  Route two interconnected signal structures for all four fan channels:

  **1. Fan TACH pull-up topology** (one per channel; identical structure):
  \\\
  J8 pad N ─────────── R_n pin 2 (signal side)
                         │
  J2–J5 pin 3 ─────── R_n pin 2  (same node — pull-up node, where TACH signal is pulled to +3V3)
                         │
  R_n pin 1 ───────── +3V3 (already routed in T002)
  \\\

  | Net | J8 pad | Resistor | Fan TACH pin |
  |---|---|---|---|
  | FAN1_TACH | 12 | R5 | J2 pin 3 |
  | FAN2_TACH | 13 | R6 | J3 pin 3 |
  | FAN3_TACH | 15 | R7 | J4 pin 3 |
  | FAN4_TACH | 16 | R8 | J5 pin 3 |

  Route the two signal segments in series: J8 pad → R_n pin 2 → J2–J5 pin 3. All three points
  are electrically the same node (pulled up to +3V3 via R_n pin 1, already connected in T002).

  **2. Fan indicator LED chains** (one per channel; identical structure):
  \\\
  J2–J5 pin 2 (+12V branch) ──► D_n (LED anode) ──► [/FANn_IND] ──► R_n ──► GND (copper pour in T008)
  \\\

  | Net | LED | Current-limit resistor | Source (fan header) |
  |---|---|---|---|
  | /FAN1_IND | D2 | R9 | J2 pin 2 |
  | /FAN2_IND | D3 | R10 | J3 pin 2 |
  | /FAN3_IND | D4 | R11 | J4 pin 2 |
  | /FAN4_IND | D5 | R12 | J5 pin 2 |

  The +12V rail routes to each fan header in T002; branch a 0.25 mm signal trace from J2 pin 2
  to D2 anode, then continue D2 cathode (via /FAN1_IND net) → R9 → GND (GND connection via pour
  in T008; may use explicit GND trace if needed).

  **Routing method:**
  1. Draw FAN*_TACH traces (J8 → R_n pin 2 → J*_pin 3) as continuous signal paths, ≥0.25 mm.
  2. Branch the +12V rail at each fan header (J2–J5 pin 2) to the respective LED diode anode.
  3. Route each /FAN*_IND net from LED cathode → R_n (current-limit resistor) → GND.
  4. All traces on F.Cu; no vias required for signal routing.

- **Depends on:** T002
- **Acceptance:**
  All eight nets (four FAN*_TACH + four /FAN*_IND) are fully routed; every segment ≥0.25 mm wide
  on F.Cu; no unrouted ratsnest for these nets; DRC still 0 errors; indicator LED chains connected
  end-to-end.
- **GitHub issue:** [#143](https://github.com/nielsverhoeven/PoE-FanController/issues/143)

---

### T006: Route Sensor Signals (≥0.25 mm)

- **Layer:** Hardware: Layout
- **Description:**
  Route the two sensor data signals connecting the daughter board to external temperature and humidity
  sensors. Both are single-wire digital signals operating at 3.3V logic levels.

  **DHT11 temperature + humidity sensor:**
  \\\
  J8 pin 23 (DHT11_DATA / GPIO16) ──► HUM1 pin 2
  \\\
  Single-wire signal. The Reichelt 239086 DHT11 breakout module includes an onboard pull-up resistor
  per constitution §2.2 (Assumption A3 in spec); no additional PCB pull-up required. Route directly
  from J8 pin 23 to HUM1 pin 2 (connector for external DHT11 module).

  **DS18B20 digital temperature sensor:**
  \\\
  J8 pin 27 (DS18B20_DATA / GPIO19) ──► R14 pin 2 ──► J6 pin 2
  \\\
  The DS18B20 requires a 4.7 kΩ pull-up resistor (R14) already placed on the PCB. Route from J8 pin 27
  to R14 pin 2 (signal side of the resistor), then from R14 pin 2 to J6 pin 2 (connector for external
  DS18B20 probe). R14 pin 1 is already connected to +3V3 in T002.

  **Routing constraints:**
  - Both traces ≥0.25 mm wide (signal net class per FR-04).
  - Both on F.Cu; no vias required.
  - Keep traces away from high-current power rails to minimize noise coupling.

- **Depends on:** T002
- **Acceptance:**
  Both DHT11_DATA and DS18B20_DATA nets are fully routed from source (J8 pins 23, 27) to destination
  connectors (HUM1 pin 2, J6 pin 2); every trace ≥0.25 mm wide on F.Cu; no unrouted ratsnest for these
  nets; DRC still 0 errors.
- **GitHub issue:** [#144](https://github.com/nielsverhoeven/PoE-FanController/issues/144)

---

### T007: Route LED Signal Chains (≥0.25 mm)

- **Layer:** Hardware: Layout
- **Description:**
  Route three independent LED indicator chains, each driven by a separate GPIO from the ESP32-P4. All
  are current-limited via series resistors already placed on the PCB.

  **Status LED chain (green LED1):**
  \\\
  J8 pin 3 (STATUS_LED / GPIO2) ──► R3 pin 1
  R3 pin 2 ──► [/LED_A] ──► LED1 anode (pin 1)
  LED1 cathode (pin 2) ──► GND (via copper pour in T008, or explicit trace)
  \\\

  **Program/OTA LED chain (orange LED2):**
  \\\
  J8 pin 22 (PROG_LED / GPIO15) ──► R13 pin 1
  R13 pin 2 ──► [/PROG_LED_A] ──► LED2 anode (pin 1)
  LED2 cathode (pin 2) ──► GND
  \\\

  **Probe status LED chain (green LED6):**
  \\\
  J8 pin 28 (PROBE_LED / GPIO20) ──► R15 pin 1
  R15 pin 2 ──► [/PROBE_LED_A] ──► LED6 anode (pin 1)
  LED6 cathode (pin 2) ──► GND
  \\\

  **Current-limit resistor values:**
  - R3 = 330 Ω (LED1 series resistor)
  - R13 = 330 Ω (LED2 series resistor)
  - R15 = 330 Ω (LED6 series resistor)

  **Routing constraints:**
  - All signal traces (/LED_A, /PROG_LED_A, /PROBE_LED_A) ≥0.25 mm wide (signal net class).
  - Route in-line without bypassing the current-limit resistors (R3, R13, R15).
  - All on F.Cu; no vias required.
  - Connect LED cathodes to GND; may use GND copper pour (T008) or explicit GND trace if needed.

  **Routing sequence:**
  1. Draw GPIO signal trace from J8 pin to resistor pin 1 (GPIO drive side).
  2. Draw resistor pin 2 to LED anode trace (the /LED_A net).
  3. Connect LED cathode to GND (explicit trace or rely on pour).

- **Depends on:** T002
- **Acceptance:**
  All three LED chains (STATUS_LED, PROG_LED, PROBE_LED) are fully routed from GPIO source (J8) through
  resistors to LED anodes; all /LED_A nets are routed; LED cathodes connected to GND; every trace
  ≥0.25 mm wide on F.Cu; no unrouted ratsnest for these nets; DRC still 0 errors.
- **GitHub issue:** [#145](https://github.com/nielsverhoeven/PoE-FanController/issues/145)

---

### T008: Fill GND Zones and Run DRC

- **Layer:** Hardware: DRC
- **Description:**
  After all trace routing (T003–T007) is complete, fill the two GND copper pour zones and execute
  a full design rule check to verify the board is DRC-clean.

  **Step 8a — Zone fill:**
  In KiCad GUI, select Edit → Fill All Zones (shortcut: **B**).

  The two zones — GND_TOP (F.Cu) and GND_BOT (B.Cu) — should fill with copper connected to the GND
  net (reassigned from \Net-(U1-GND)\ in T001). Visually inspect the fill result:

  - **Check for isolated islands:** Any region that cannot trace a path back to a GND pad (via other
    zones, vias, or routed traces) must either be (a) removed by drawing a keepout polygon, or (b)
    bridged to GND via an explicit via or trace.
  - **Check for unintended copper shorting:** Ensure no zone copper inadvertently shorts signal nets.
  - **Verify layer coverage:** F.Cu zone should not overlap B.Cu pads unless connected via vias.

  **Step 8b — DRC execution:**
  Run Tools → Design Rules Checker → Run DRC (or command-line: \kicad-cli pcb drc hardware/kicad/PoE-FanController.kicad_pcb\).

  **Target outcome:**

  | Category | Target |
  |---|---|
  | **Errors** | **0** |
  | **Unconnected** | **0** |
  | **Warnings** | ≤ 16 baseline; two \isolated_copper\ warnings must be gone |

  **Resolution of violations (if any):**
  - **Unconnected:** Add the missing trace manually (go back to T002–T007 if a routed net was missed).
  - **Spacing violations:** Adjust trace width or position if a 0.25 mm trace conflicts with a 1.0 mm
    power trace; re-run DRC.
  - **Via issues:** If DRC flags via spacing, remove or reposition the via.

  Do NOT commit until DRC shows 0 errors and 0 unconnected.

- **Depends on:** T003, T004, T005, T006, T007 (all routing complete)
- **Acceptance:**
  DRC report displays **0 errors**, **0 unconnected**, and ≤ 16 warnings (baseline; the two
  `isolated_copper` warnings from T001 must NOT appear); both GND zones visibly filled and connected
  to GND pads; board visually complete with all ratsnest cleared from PCB editor.
- **GitHub issue:** [#146](https://github.com/nielsverhoeven/PoE-FanController/issues/146)

---

### T009: Regenerate Gerbers and Update Documentation

- **Layer:** Documentation
- **Description:**
  After DRC passes (T008), regenerate Gerber and drill files, and update the feature documentation
  with final task status and issue links.

  **Step 9a — Regenerate Gerber files:**
  In KiCad GUI, select File → Fabrication Outputs → Gerbers (or use \kicad-cli pcb export gerbers ...\).
  Output directory: \hardware/kicad/gerbers/\ (per FR-10 and P-KI-06).

  Exported files should include:
  - \PoE-FanController-F_Cu.gbr\ (front copper with all routed traces)
  - \PoE-FanController-B_Cu.gbr\ (back copper with GND pour)
  - \PoE-FanController-F_SilkS.gbr\ (front silk layer)
  - \PoE-FanController-B_SilkS.gbr\ (back silk layer)
  - \PoE-FanController-F_Mask.gbr\ (front solder mask)
  - \PoE-FanController-B_Mask.gbr\ (back solder mask)
  - \PoE-FanController-Edge_Cuts.gbr\ (board edge)
  - \PoE-FanController.drl\ (drill file)

  Verify Gerber files are newer than the routed \.kicad_pcb\ file (timestamp check).

  **Step 9b — Commit artifacts:**
  - Commit the routed \.kicad_pcb\ file with message: \hw: route all PCB traces — all nets routed, 0 DRC errors\
  - Commit Gerber files (directory \hardware/kicad/gerbers/\) with message: \hw: regenerate Gerbers after PCB routing\

  **Step 9c — Update tasks.md:**
  Replace all GitHub issue placeholders (\(to be filled by github.issues-manager)\) with actual issue
  links (\[#NNN](https://github.com/nielsverhoeven/PoE-FanController/issues/NNN)\). Update the
  Dependency Graph section if any tasks were split or re-sequenced. Commit \	asks.md\ with message:
  \docs: finalize tasks.md with GitHub issue numbers for #83\.

  **Step 9d — Push and open PR:**
  Push all commits to the remote \eature/83-route-pcb-traces\ branch. Open a pull request to \main\
  with the title: \hw: route all PCB traces — [#83]\. Include a summary of:
  - All nets routed (70 ratsnest items cleared).
  - DRC: 0 errors, 0 unconnected.
  - GND zones reassigned and filled.
  - Gerber files regenerated and included.

- **Depends on:** T008
- **Acceptance:**
  Gerber files exist in `hardware/kicad/gerbers/` and are dated after the routed `.kicad_pcb`; all
  task issue numbers appear in `tasks.md` as hyperlinks; commits are pushed to the remote branch;
  PR is opened and ready for review.
- **GitHub issue:** [#147](https://github.com/nielsverhoeven/PoE-FanController/issues/147)

---

## Checklist for Reviewers

Before merging the PR, verify:

- [ ] T001: GND zone net reassignment script (\hardware/fix_gnd_zones.py\) committed and working.
- [ ] T002–T007: All ratsnest items cleared; traces visible in PCB editor; layer constraints observed.
- [ ] T003: BOOST_SW loop area measured < 200 mm² (documented in PR comment).
- [ ] T004–T007: Signal traces ≥0.25 mm; power traces ≥1.0 mm (visual or XML inspection).
- [ ] T008: DRC clean: **0 errors**, **0 unconnected**.
- [ ] T009: Gerber files present and dated correctly; \	asks.md\ updated with issue links.
- [ ] Commit history clean: no merge commits; squash or rebase if needed.
- [ ] PR description includes summary of changes and DRC result.

---

## Reference Documents

- **Feature Spec:** \docs/features/route-pcb-traces/spec.md\
- **Technical Plan:** \docs/features/route-pcb-traces/plan.md\
- **Constitution v4.1.0:** \docs/constitution.md\ (P-HW-07, P-KI-06, P-KI-07, P-DEV-01)
- **PCB File:** \hardware/kicad/PoE-FanController.kicad_pcb\ (feature baseline)
- **GND Zone Script:** \hardware/fix_gnd_zones.py\ (to be created in T001)
