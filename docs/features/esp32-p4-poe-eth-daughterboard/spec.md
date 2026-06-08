# Feature: Redesign — Switch to ESP32-P4-POE-ETH + Daughter Board with Side-Accessible Fan Headers

<!-- Issue: #75 | Branch: feature/75-esp32-p4-poe-eth-daughterboard | Status: PLANNING -->
<!-- Constitution reference: v2.0.0 | Spec date: 2026-06-08 -->
<!-- Supersedes: Issue #62 (ESP32-P4-ETH carrier board approach) -->

---

## Overview

The current custom PCB (v2.0.0) is a carrier/HAT board for the Waveshare **ESP32-P4-ETH** (SKU
32086), which has **no onboard PoE**. That design requires two cables (one PoE power cable to J1,
one separate Ethernet data cable to the Waveshare board's own RJ45) and carries discrete PoE PD
components (U1 Ag9905M, J1 RJ45) on the carrier PCB.

This feature replaces that two-board-plus-two-cable arrangement with a simpler architecture:

- **Main board (off-the-shelf):** Waveshare **ESP32-P4-POE-ETH** (SKU 32088), which integrates
  PoE PD, Ethernet PHY, RJ45, ESP32-P4, USB-C, and BOOT/RST buttons on one module. A single
  802.3at Ethernet cable provides both power and data.
- **Daughter board (custom PCB):** A new, minimal PCB that stacks onto the SKU 32088 via a 2×20
  female header (J8). It boosts the 5 V from the header to 12 V for fans, routes PWM/TACH/NTC
  signals, and exposes four 4-pin fan headers on the **side edge** of the board — enabling a
  clean enclosure design with a single cut-out for fan cables.

The result is a simpler BOM, a single cable installation, and cleaner mechanical integration.

---

## User Stories

- As an **installer**, I want to plug a single 802.3at PoE Ethernet cable into the unit so that
  I do not need a separate power injector or a second cable.
- As an **installer**, I want all four fan connectors accessible from one side of the enclosure
  so that I can route cables without removing the lid or accessing multiple faces.
- As a **hardware maintainer**, I want the PoE PD circuitry on the off-the-shelf Waveshare board
  so that the custom PCB is simpler, cheaper to manufacture, and easier to assemble.
- As a **firmware developer**, I want GPIO assignments and the ESP32-P4 module to remain unchanged
  so that the existing firmware requires no modification for the hardware redesign.
- As a **system administrator**, I want the device to work reliably with 802.3at (PoE+) switches
  so that I know the power class requirement before purchasing infrastructure.

---

## Functional Requirements

1. **FR-01 — Single-cable PoE+Ethernet input.** The assembled unit (main board + daughter board)
   shall require exactly one 802.3at Ethernet cable for both network connectivity and power. No
   additional power injector or DC power supply connection is required during normal operation.

2. **FR-02 — Four 12 V PWM fan headers.** The daughter board shall expose four 4-pin 12 V PWM fan
   headers (J2–J5), each compatible with the Intel 4-wire fan specification (25 kHz PWM,
   open-drain TACH).

3. **FR-03 — Side-edge connector placement.** Fan headers J2–J5 shall be placed on the side edge
   of the daughter board (the edge perpendicular to the 2×20 header axis) so that cables can be
   accessed through a single enclosure cut-out.

4. **FR-04 — 12 V fan power via boost conversion.** The daughter board shall include a 5 V → 12 V
   boost converter (U_BOOST) that derives 12 V from the 5 V rail on the 2×20 header. The boost
   converter shall supply at least 1.3 A at 12 V (16 W) to satisfy the fan budget with margin.

5. **FR-05 — 802.3at (Class 4) requirement documented.** The design shall document that the PSE
   (PoE switch or injector) must support 802.3at Class 4 (≥ 30 W at port). 802.3af-only PSEs
   are explicitly not supported.

6. **FR-06 — Temperature sensing preserved.** The daughter board shall include NTC1 (10 kΩ,
   B = 3950 K) and voltage-divider resistor R4, connected to the NTC_ADC signal (GPIO16) via J8.

7. **FR-07 — TACH pull-ups preserved.** The daughter board shall include R5–R8 (TACH pull-up
   resistors, 10 kΩ to 3.3 V), one per fan header.

8. **FR-08 — Status LED preserved.** The daughter board shall include LED1 (status LED) and
   current-limiting resistor R3, driven by STATUS_LED (GPIO2) via J8.

9. **FR-09 — GPIO compatibility.** Daughter board signal assignments (PWM, TACH, NTC, LED) shall
   use the same GPIO numbers as the v2.0.0 design (GPIO4–7 PWM, GPIO8–11 TACH, GPIO16 NTC,
   GPIO2 LED) so that no firmware changes are required.

10. **FR-10 — Schematic generator updated.** The hardware generator (`hardware/generator/`) shall
    be updated to reflect the new architecture: old power components removed, new boost converter
    added, J8 role updated to female receiver.

11. **FR-11 — PCB updated.** The KiCad PCB file (`hardware/kicad/PoE-FanController.kicad_pcb`)
    shall be updated to reflect the new board outline, component placement, and routing.

12. **FR-12 — BOM updated.** `hardware/bom/bom.csv` shall be updated to remove deleted components
    and add the boost converter and any new passives.

13. **FR-13 — Constitution amended.** `docs/constitution.md` shall receive a MAJOR amendment
    (v3.0.0) recording all architectural changes before any implementation work begins.

---

## Non-Functional Requirements

### Power

- **NFR-P-01 — Fan power budget.** Total 12 V fan load shall not exceed 12 W (≤ 1.0 A at 12 V
  combined across all four headers, ≤ 0.25 A per header).
- **NFR-P-02 — Power margin.** At 802.3at Class 4 (25.5 W PD), the design shall maintain a
  minimum 15 % power margin above the worst-case total load (fans + Waveshare board self-use +
  conversion losses).
- **NFR-P-03 — Boost converter efficiency.** The 5 V → 12 V boost converter shall operate at
  ≥ 85 % efficiency at the rated load point.
- **NFR-P-04 — No 802.3af support.** The system is explicitly not required to operate on
  802.3af (Class 0–3) PSEs. Attempting operation on an 802.3af-only PSE may result in
  insufficient fan power; this is an accepted, documented limitation.

### Safety and Isolation

- **NFR-S-01 — SELV-only daughter board.** The daughter board shall operate entirely within the
  SELV (Safety Extra-Low Voltage) domain. No primary-side PoE circuitry shall be present on the
  daughter board. Isolation is entirely inside the Waveshare SKU 32088 board.
- **NFR-S-02 — Single ground domain.** The daughter board uses a single `GND` net. The
  `GND_PRI` / isolation barrier rules (P-ISO-02 through P-ISO-05) do not apply to the daughter
  board; there is no isolation slot and no x = 38 mm barrier on the new PCB.

### Electrical

- **NFR-E-01 — 12 V trace width.** All 12 V power traces on the daughter board shall be ≥ 1.0 mm
  wide (per P-HW-07).
- **NFR-E-02 — Signal trace width.** All signal traces (PWM, TACH, NTC, LED) shall be ≥ 0.25 mm
  wide (per P-HW-07).
- **NFR-E-03 — GND pour.** Both F.Cu and B.Cu shall carry a GND copper pour (per P-HW-08, with
  the isolation-split clause not applicable as there is only one ground domain).

### Mechanical

- **NFR-M-01 — Board length.** The daughter board length (axis along which the 2×20 header runs)
  shall match the Waveshare SKU 32088 board length (≈ 85.6 mm — exact value to be confirmed per
  OQ-01).
- **NFR-M-02 — Board width.** The daughter board width shall be sufficient to accommodate
  side-edge fan headers while keeping all components within the board outline. Exact width is
  TBD pending OQ-01 resolution but expected to be wider than SKU 32088 (≈ 56 mm).
- **NFR-M-03 — Two-layer FR4.** The daughter board uses exactly two copper layers, 1.6 mm FR4,
  1 oz copper (per P-HW-01).
- **NFR-M-04 — Single-sided placement.** All components shall be on F.Cu only (per P-HW-02).
- **NFR-M-05 — Side-edge fan access.** Fan header J2–J5 bodies and mating connector plug
  clearances shall be fully accessible from outside the enclosure through a single side cut-out.

### Firmware

- **NFR-F-01 — No firmware changes required.** The hardware redesign shall not require any change
  to existing firmware modules. GPIO assignments, peripheral ownership, and firmware build
  configuration remain unchanged.

---

## Success Criteria

- **SC-01** — `python hardware/generate_project.py` exits 0 and produces a KiCad schematic
  containing boost converter U_BOOST, female J8, and fan headers J2–J5, with no ERC errors.
- **SC-02** — ERC report (`hardware/kicad/erc_output.json`) shows **0 errors**.
- **SC-03** — KiCad PCB file has zero footprints for J1, U1, U2, D1, D2, L1, C1, C2.
- **SC-04** — Fan headers J2–J5 are placed on the side edge of the PCB (confirmed via visual
  inspection in KiCad GUI and DRC courtyard check).
- **SC-05** — DRC reports ≤ 5 violations (target 0); zero unconnected nets.
- **SC-06** — `hardware/bom/bom.csv` does not list J1, U1, U2, D1, D2, L1, C1, C2; does list
  U_BOOST (boost converter) and updated J8 (female connector).
- **SC-07** — `docs/constitution.md` contains amendment record v3.0.0 before any schematic or
  PCB file is modified.
- **SC-08** — Waveshare SKU 32088 board dimensions (L × W mm) and 2×20 header voltage are
  verified from the Waveshare wiki and recorded in `docs/kb/esp32-p4-reference.md` before PCB
  outline is committed.
- **SC-09** — Power budget analysis confirms ≥ 15 % margin at 802.3at with the chosen boost
  converter, using verified (not estimated) self-use figures for SKU 32088.
- **SC-10** — Hardware bring-up checklist (§8.4 of constitution) is updated for the new
  assembly sequence and recorded in `docs/constitution.md` v3.0.0.

---

## Out of Scope

- **Firmware changes** — GPIO assignments and peripheral ownership are unchanged; no firmware
  modification is in scope for this feature.
- **Web UI changes** — No new endpoints, pages, or controls are required.
- **Enclosure design** — Physical enclosure CAD/drawing is not part of this feature; only the
  PCB mechanical constraints that enable a future enclosure are defined here.
- **802.3af compatibility** — Designing a fallback power path for 802.3af-only PSEs is out of
  scope. The limitation is documented (FR-05) but not mitigated in hardware.
- **Gerber export** — Gerber generation is a release-gate step (P-CI-02) and is out of scope
  until DRC reaches zero violations.
- **USB-C power fallback** — The Waveshare SKU 32088 board's USB-C port provides programming
  access but is not designed as a primary power path; no USB power validation is in scope.

---

## Assumptions

- **A-01** — The Waveshare ESP32-P4-POE-ETH (SKU 32088) 2×20 header pins 2 and 4 carry **+5 V**
  (regulated, from the onboard PoE PD module). This is MEDIUM confidence and must be verified
  (see OQ-01) before PCB commitment.
- **A-02** — The Waveshare SKU 32088 board self-consumption is approximately 3.5 W under typical
  load (ESP32-P4 + LAN8720A active). This must be verified under load before the power margin
  is finalised.
- **A-03** — The Waveshare SKU 32088 2×20 header follows Raspberry Pi HAT mechanical layout,
  with the same GPIO-to-pin mapping as documented in `docs/kb/esp32-p4-reference.md §9.4`.
  This is LOW confidence and must be verified against the Waveshare schematic PDF (see OQ-02).
- **A-04** — Fan headers J2–J5 use the same 4-pin 2.54 mm Molex 47053-1000 footprint (vertical
  through-hole) unless side-mount connectors are selected during PCB layout (see OQ-03).
- **A-05** — The TI LM2587-12 (or equivalent fixed-12V boost converter) is available and
  meets dimensional constraints for the daughter board. Component selection is confirmed in the
  technical plan but final MPN is subject to availability verification.
- **A-06** — The daughter board mounts **below** the Waveshare main board (Waveshare sits on
  top, daughter board underneath), with J8 female header on the daughter board facing up.

---

## Open Questions

> All items below are marked as requiring live verification from the Waveshare wiki before PCB
> fabrication files are committed.

- **OQ-01 (BLOCKING — PCB outline):** Confirm exact board dimensions (L × W mm) of the
  Waveshare ESP32-P4-POE-ETH (SKU 32088) from the mechanical drawing on the wiki.
  URL: https://www.waveshare.com/wiki/ESP32-P4-POE-ETH → Resources tab → mechanical drawing.
  *Blocks: board outline in Edge.Cuts (T4), daughter board width specification (NFR-M-01/02).*

- **OQ-02 (BLOCKING — schematic/firmware):** Confirm that the SKU 32088 2×20 header pins 2 & 4
  carry +5 V (not 12 V, not raw PoE, not 3.3 V) from the Waveshare schematic PDF.
  URL: https://www.waveshare.com/wiki/ESP32-P4-POE-ETH → Resources tab → schematic PDF.
  *Blocks: boost converter input spec (T2), power budget finalisation (NFR-P-01/02).*

- **OQ-03 (BLOCKING — schematic/firmware):** Confirm that GPIO4–7 (PWM) and GPIO8–11 (TACH)
  and GPIO16 (NTC) and GPIO2 (LED) are available on the SKU 32088 2×20 header and at the
  physical pin positions documented in `docs/kb/esp32-p4-reference.md §9.4`.
  *Blocks: J8 net assignments in generator (T2), firmware GPIO defines (P-FW-02).*

- **OQ-04 (DESIGN CHOICE — connectors):** Confirm choice of vertical vs. right-angle (side-mount)
  fan header connectors for J2–J5. Vertical connectors require the daughter board to be wide
  enough that the connector body clears the enclosure edge. Right-angle connectors reduce required
  width. Decision needed before PCB layout (T4).
  *Blocks: PCB width specification, connector MPN finalisation (BOM T7).*

- **OQ-05 (DESIGN CHOICE — boost converter MPN):** Confirm final boost converter selection
  (TI LM2587-12 vs. TI TPS61085 vs. XL6009E1) based on package availability, footprint
  constraints, and PCB area budget. The TI LM2587-12 is the recommended starting point
  (see `docs/kb/poe-reference.md §7.4`).
  *Blocks: boost converter footprint in generator (T2), BOM entry (T7).*
