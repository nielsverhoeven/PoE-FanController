# Feature: Correct GPIO Pin Assignments for J8 (ESP32-P4-POE-ETH Right Column)

> Issue: [#148](https://github.com/nielsverhoeven/PoE-FanController/issues/148)
> Branch: `feature/148-correct-gpio-pin-assignments`
> Status: Planning

---

## Overview

The schematic generator (`hardware/generator/components.py`) assigns signal nets to J8 pins that
do not match the physical pin functions of the Waveshare ESP32-P4-POE-ETH (SKU 32088). Several pins
that are physically GND, power rails, or EMAC-reserved GPIOs carry signal nets in the schematic,
and several signal pins (GPIO2, GPIO15–16, GPIO19) are labelled as GND or power rails. This feature
corrects every J8 pin assignment — in both columns — so that the generated schematic is
electrically consistent with the physical module, produces zero ERC errors, and enables correct PCB
routing and firmware operation.

---

## User Stories

- As a **hardware designer**, I want every J8 pin in the schematic to carry the net that matches its
  physical function on the ESP32-P4-POE-ETH so that the PCB layout connects to the correct copper.
- As a **firmware developer**, I want the fan PWM and TACH GPIO numbers in the schematic to reflect
  GPIOs that are actually available and routed through J8 so that my firmware pin definitions match
  the hardware.
- As a **reviewer**, I want the KiCad ERC to report zero errors after the correction so that I can
  trust the schematic as a correct starting point for PCB routing.

---

## Functional Requirements

1. **FR-01** — No signal net (PWM, TACH, STATUS_LED, PROG_LED, PROBE_LED, DHT11_DATA,
   DS18B20_DATA) shall be assigned to a J8 pin whose physical function on the ESP32-P4-POE-ETH is
   GND, a power rail (3V3, VSYS, VBUS), or a reserved control pin (EN, RUN).

2. **FR-02** — No power symbol (+3V3, +5V, GND) shall be placed on a J8 pin whose physical function
   is a general-purpose GPIO.

3. **FR-03** — The +3V3 power rail shall be sourced from J8 pin 36 (physical: 3V3 output from
   Waveshare LDO), which is the only pin confirmed to supply 3.3 V to the daughter board via the
   header.

4. **FR-04** — The eight fan signals (FAN1–4 PWM and FAN1–4 TACH) shall be assigned exclusively to
   right-column (pins 21–40) GPIO pins that are physically accessible and not reserved for EMAC
   (forbidden GPIOs: 31, 32–37, 50–52).

5. **FR-05** — Signal assignments shall use only GPIO numbers that appear in the physical right-
   column pin layout confirmed from the authoritative board image
   (`docs/kb/ESP32-P4-POE-ETH/pin-layout.md`), excluding EMAC-forbidden GPIOs.

6. **FR-06** — STATUS_LED, PROG_LED, DHT11_DATA, and DS18B20_DATA shall be assigned to left-column
   (pins 1–20) GPIO pins whose physical numbers match the GPIO expected by each signal (GPIO2, 15,
   16, 19 respectively).

7. **FR-07** — PROBE_LED shall be assigned to a valid right-column GPIO pin that is not already
   consumed by a fan signal and is not EMAC-reserved.

8. **FR-08** — All changes to the J8 symbol definition and wiring shall be made exclusively in
   `hardware/generator/components.py`; the `.kicad_sch` file must never be edited by hand
   (P-HW-05 / P-KI-04).

9. **FR-09** — After running `python hardware/generate_project.py`, the regenerated schematic shall
   produce zero KiCad ERC errors.

10. **FR-10** — The corrected pin-to-GPIO mapping shall be documented in the generator source as
    inline comments on each pin entry.

11. **FR-11** — The constitution (`docs/constitution.md` §P-FW-02 peripheral ownership table) shall
    be updated to reflect the new GPIO numbers for all fan signals and for PROBE_LED.

---

## Non-Functional Requirements

- **NFR-01** — All schematic changes must be implemented exclusively through the generator package
  (P-HW-05); no hand-editing of `.kicad_sch`.
- **NFR-02** — The corrected schematic must comply with KiCad 10.0.3 format (P-KI-01/02).
- **NFR-03** — All symbol origins and pin endpoints must remain on the 2.54 mm schematic grid
  (P-HW-06); only net labels and pin types change, not physical symbol geometry.
- **NFR-04** — The PCB must be updated via "Update PCB from Schematic" in KiCad GUI after schematic
  regeneration; no script may write to `.kicad_pcb` (P-KI-07).
- **NFR-05** — After PCB netlist sync and any required re-routing, DRC must report zero errors
  (P-TEST-03); pre-existing solder-mask-bridge suppressions are excluded.

---

## Success Criteria

| ID | Criterion | How to verify |
|----|-----------|---------------|
| SC-01 | No J8 pin in the regenerated schematic carries a signal net on a physical GND pin (3, 8, 13, 18, 23, 28, 33, 38) | KiCad net inspector — no signal nets on those pad numbers |
| SC-02 | No J8 pin carries a signal net on a physical power/reserved pin (36, 37, 39, 40, 30) | KiCad net inspector |
| SC-03 | No power symbol (+3V3, GND, +5V) is placed on physical GPIO pins 1, 2, 4–7, 9–12, 14–17, 19–22, 24–27, 29, 31, 32, 34, 35 | Diff of generated `.kicad_sch` pin assignments |
| SC-04 | +3V3 rail is connected to J8 pad 36 only (not pads 1 or 17) | Net inspector: +3V3 net contains J8 pad 36 |
| SC-05 | All eight fan signals use right-column GPIO pins: FAN1_PWM=GPIO20, FAN2_PWM=GPIO21, FAN3_PWM=GPIO26, FAN4_PWM=GPIO27, FAN1_TACH=GPIO22, FAN2_TACH=GPIO23, FAN3_TACH=GPIO46, FAN4_TACH=GPIO47 | Net inspector pin list for each signal |
| SC-06 | STATUS_LED on J8 pad 6 (GPIO2); PROG_LED on pad 14 (GPIO15); DHT11_DATA on pad 15 (GPIO16); DS18B20_DATA on pad 19 (GPIO19); PROBE_LED on pad 21 (GPIO48) | Net inspector |
| SC-07 | ERC reports 0 errors after `python hardware/generate_project.py` | `kicad-cli sch erc` output |
| SC-08 | DRC reports 0 errors after PCB netlist sync | KiCad DRC dialog |
| SC-09 | `docs/constitution.md` P-FW-02 table updated with new GPIO assignments for FAN1–4 PWM/TACH and PROBE_LED | Diff review |
| SC-10 | The `.kicad_sch` file is not modified by any hand-edit; it is produced exclusively by running `python hardware/generate_project.py` (the file's `(generator "eeschema")` header is intact and the git diff shows only the build artefact changed, not `components.py` → `.kicad_sch` in isolation) | Git diff review: no direct `.kicad_sch` edits |
| SC-11 | Every pin entry in the updated `pins_left` / `pins_right` lists in `components.py` has an inline comment identifying the physical signal name (e.g. `# GPIO20`, `# Physical GND`, `# EMAC_RXD1: FORBIDDEN`) | Code review of `components.py` diff |

---

## Out of Scope

- Changes to left-column pin **numbers** 1–20 in the generator symbol `pins_left` list definition
  (pin position indices are already correct from issue #133 fix; only nets and pin-type annotations
  change where they are wrong).
- Firmware source code changes (updating `#define FAN1_PWM_PIN` constants etc.) — these are a
  downstream consequence tracked separately.
- PCB re-routing of fan traces — this is a PCB layout task following the netlist sync.
- Changes to J8 footprint pad coordinates or the custom
  `PinSocket_2x20_P2.54mm_P15.38mm_Vertical.kicad_mod` footprint (pad numbering was already fixed
  in issue #133; physical coordinates are unchanged).
- Adding any new components to the schematic or PCB.

---

## Assumptions

- The authoritative physical pin layout is the verified image
  `docs/kb/ESP32-P4-POE-ETH/ESP32-P4-ETH-details-inter-*.webp`, as documented in
  `docs/kb/ESP32-P4-POE-ETH/pin-layout.md`. This source is treated as HIGH confidence.
- GPIO32 and GPIO33 (J8 pins 26 and 25) are EMAC-reserved (EMAC_RXD0 and EMAC_RXD1) per
  `docs/kb/ESP32-P4-POE-ETH/board-reference.md §2` and `docs/constitution.md P-FW-02`. They appear
  on J8 but cannot be used as general GPIO by the daughter board.
- J8 pin 30 (physical: RUN/chip-enable) is reserved and must not carry any daughter-board signal.
- GPIO47 and GPIO48 (J8 pins 22, 21) are not listed as forbidden in `board-reference.md §4.3` and
  are available for general use.
- The 3.3 V power supply to the daughter board (for TACH pull-ups R5–R8 and DHT11 VCC) is sourced
  from J8 pin 36 (+3V3). The current generator's incorrect assignment of +3V3 to pins 1 (GPIO25)
  and 17 (GPIO18) is part of this bug and must be corrected.
- Fan signal GPIO assignments will change from the values in the current constitution (GPIO4–11) to
  new values (GPIO20–23, 26, 27, 46, 47). A constitution amendment is required to make this change
  official before implementation is merged.
- PROBE_LED GPIO changes from GPIO20 (current constitution) to GPIO48 because GPIO20 is now
  assigned to FAN1_PWM.

---

## Open Questions

None — all [NEEDS CLARIFICATION] items were resolved by reading pin-layout.md, board-reference.md,
constitution.md, and the authoritative board image. The EMAC-conflict with GPIO32/33 is noted in
the plan and must be reviewed by `esp32.expert` before the constitution amendment is signed off.
