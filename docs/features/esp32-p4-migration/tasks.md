# Tasks: ESP32-P4 Migration (MCU: replace ESP32-WROOM-32D with ESP32-P4)

## Summary

- **Total tasks:** 18
- **Layers covered:** Documentation, Hardware: Schematic, Hardware: ERC, Hardware: Layout, Hardware: DRC, Hardware: BOM, Firmware: Config, Firmware: Module, Unit Tests, Issue update
- **GitHub parent issue:** #40
- **Branch:** `feature/40-replace-esp32-with-esp32-p4`
- **Constitution version:** v1.2.0 (MAJOR-001 — already ratified; no further amendment needed)
- **Architecture document:** `docs/features/esp32-p4-migration/architecture.md`

---

## Dependency Graph

```
T001 (Doc: Verify RMII fixed pins against TRM) ─────────────┐
T002 (HW-SCH: Author ESP32-P4-MINI-1U custom footprint) ────┤
T012 (FW-CFG: Update platformio.ini for ESP32-P4) ──────────┤
                                                             │
              T001 + T002 ──► T003 (HW-SCH: Replace U3 in generator)
              T001 ──────────► T004 (HW-SCH: Add U5 LAN8720A in generator)
              T001 ──────────► T005 (HW-SCH: Redesign J1 RJ45 symbol)
                                                             │
              T003 + T004 + T005 ──► T006 (HW-SCH: Add global labels)
                                         │
                                         ▼
                                   T007 (HW-ERC: Run ERC — 0 errors)
                                    │         │
                           ┌────────┘         └────────┐
                           ▼                           ▼
                 T008 (HW-PCB: Place U5)    T009 (HW-PCB: J1 PCB footprint)
                           │                           │
                           └──────────┬────────────────┘
                                      ▼
                             T010 (HW-PCB: Route RMII + MDI traces)
                                      │
                                      ▼
                             T011 (HW-DRC: Run DRC ≤67 violations)
                                      │
              T007 ─────────────────► T015 (HW-BOM: Update BOM for U3/U5/Rnew)
              T001 + T012 ──────────► T013 (FW-MOD: Replace WiFi with Ethernet)
              T001 + T012 ──────────► T014 (FW-MOD: Update GPIO pin constants)
              T013 + T014 ─────────► T016 (UT: Firmware unit tests)
                                      │
              T011 + T015 + T016 ───► T017 (DOC: Update documentation)
                                      │
                                      ▼
                             T018 (ISSUE: Final status update on #40)
```

### Critical Path

**Hardware path (longest):**
`T001 → T003 → T006 → T007 → T008 → T010 → T011 → T017 → T018` (9 tasks)

**Firmware path (parallel, not on critical path):**
`T001 → T013 → T016 → T017 → T018` (5 tasks)

**Tasks that can start immediately (no dependencies):**
T001, T002, T012

---

## Task List

---

### T001: Verify RMII fixed GPIO assignments against ESP32-P4 TRM [#42]

- **Layer:** Documentation
- **Description:** Cross-verify the GPIO32–37 + GPIO50 RMII pin table documented in
  `docs/features/esp32-p4-migration/architecture.md §3` against the physical ESP32-P4
  Technical Reference Manual Chapter EMAC, Table "EMAC Signal Overview". This is a
  read-and-compare task — no schematic files are changed here.

  Steps:
  1. Download or open the ESP32-P4 TRM (available from Espressif docs portal).
  2. Locate Chapter EMAC → "EMAC Signal Overview" / "IO_MUX Fixed Allocation" table.
  3. Compare each signal (EMAC_RXD0, EMAC_RXD1, EMAC_CRS_DV, EMAC_TXD0, EMAC_TXD1,
     EMAC_TX_EN, REF_CLK) against the architecture.md §3 table.
  4. If all match: add a ✅ `[TRM-VERIFIED yyyy-mm-dd]` annotation to the architecture.md §3
     table header and commit.
  5. If any GPIO number differs: update `docs/features/esp32-p4-migration/architecture.md`
     with the corrected numbers, add a ⚠️ `[CORRECTION APPLIED yyyy-mm-dd]` note, and
     comment on this issue listing which GPIOs changed — this will cascade changes to T003,
     T004, T013, T014.

  Commit message: `docs: verify RMII fixed-pin table against ESP32-P4 TRM §EMAC (#40)`

  > ⚠️ **OQ-01 (CRITICAL):** This task closes OQ-01. All downstream tasks (T003, T004,
  > T013, T014) are gated on this task because a pin number error would require their
  > full rework. Do not begin T003, T004, T013, or T014 until this task is ✅ closed.

- **Depends on:** none
- **Acceptance:** `docs/features/esp32-p4-migration/architecture.md` §3 contains a
  `[TRM-VERIFIED]` or `[CORRECTION APPLIED]` annotation with a date, and a commit exists
  on the branch that updates this file.
- **GitHub issue:** #42

---

### T002: Author ESP32-P4-MINI-1U custom KiCad footprint [#43]

- **Layer:** Hardware: Schematic
- **Description:** Create the file
  `hardware/kicad/footprints/Custom.pretty/ESP32-P4-MINI-1.kicad_mod` containing the
  LGA-56 castellation-edge land pattern for the ESP32-P4-MINI-1U module, derived from
  the Espressif MINI-1U datasheet §PCB Land Pattern.

  Requirements (per architecture.md §2 + P-HW-02 + P-KI-05):
  - All 56 pads on F.Cu only (P-HW-02 — single-sided placement)
  - Pad geometry (size, drill, courtyard) must match Espressif recommended land pattern
  - Courtyard must enclose the full module body (25.4 × 19.0 mm) plus keep-out margin
  - Fab layer silkscreen must show module outline and pin-1 indicator
  - `(generator "pcbnew")` and `(generator_version "10.0")` headers for KiCad 10 compatibility
  - Stored in `hardware/kicad/footprints/Custom.pretty/` per P-KI-05

  Validation: Open the file in KiCad 10 Footprint Editor and run footprint validation
  (Inspect → Design Rules Checker on footprint). Zero errors required.

  Commit message: `hw: add ESP32-P4-MINI-1 custom LGA-56 footprint to Custom.pretty (#40)`

  > **Note:** This is a prerequisite for T003. The `generate_project.py` U3 symbol
  > references `Custom:ESP32-P4-MINI-1` — the footprint file must exist before the
  > generated schematic/PCB can be opened in KiCad without missing-footprint errors.

- **Depends on:** none
- **Acceptance:** File `hardware/kicad/footprints/Custom.pretty/ESP32-P4-MINI-1.kicad_mod`
  exists in the repository, is valid KiCad 10 `.kicad_mod` format, and KiCad Footprint
  Editor reports zero validation errors when the file is loaded.
- **GitHub issue:** #43

---

### T003: Replace U3 symbol and footprint in generate_project.py [#45]

- **Layer:** Hardware: Schematic
- **Description:** Edit `hardware/generate_project.py` to replace the existing
  `ESP32-WROOM-32D` symbol block with a `Custom:ESP32-P4-MINI-1U` symbol block. All pin
  definitions must use the verified GPIO table from architecture.md §4 (closed after T001).

  Changes required:
  1. Remove the `ESP32-WROOM-32D` symbol definition (all pins, pin types, net connections).
  2. Add a new `Custom:ESP32-P4` symbol with:
     - All RMII fixed pins: GPIO32–37, GPIO50 (directions per architecture.md §3)
     - MDIO/MDC: GPIO28, GPIO31
     - PWM outputs: GPIO4–7 (LEDC)
     - TACH inputs: GPIO8–11
     - NTC ADC: GPIO16
     - 1-Wire / Status LED: GPIO2
     - BOOT strapping: GPIO0
     - UART0: GPIO38 (TX), GPIO39 (RX)
     - EN pin (hardware reset)
     - 3.3 V power pins, GND pins
  3. Set footprint to `Custom:ESP32-P4-MINI-1` (file authored in T002).
  4. Remove all WiFi / Bluetooth net references (no antenna, no RF nets).
  5. Update the schematic section header to `"ESP32-P4"` (bold, size=2.54, color=BLUE,
     per P-SCH-03).
  6. Re-run `python hardware/generate_project.py` and confirm it exits with code 0.

  Commit both `hardware/generate_project.py` and the regenerated
  `hardware/kicad/PoE-FanController.kicad_sch`.

  Commit message: `hw: replace ESP32-WROOM-32D with ESP32-P4-MINI-1U in generator (#40)`

  > **Note:** Use only the GPIO assignments from the T001-verified architecture.md table.
  > Do not use the original plan.md §4.3 table — it contains superseded GPIO numbers.

- **Depends on:** T001, T002
- **Acceptance:** `python -m py_compile hardware/generate_project.py` exits with code 0;
  `Select-String hardware/generate_project.py -Pattern "WROOM"` returns no matches;
  `Select-String hardware/generate_project.py -Pattern "ESP32-P4"` returns at least one match.
- **GitHub issue:** #45

---

### T004: Add U5 LAN8720A symbol and nets in generate_project.py [#46]

- **Layer:** Hardware: Schematic
- **Description:** Edit `hardware/generate_project.py` to add the new `Custom:LAN8720A`
  symbol for U5 (Ethernet PHY) with full RMII, MDI, and power pin connectivity.

  Changes required:
  1. Add a `Custom:LAN8720A` symbol definition with all 24 QFN pins:
     - RMII receive: RXD0, RXD1, CRS_DV (inputs from ESP32-P4 GPIO32–34)
     - RMII transmit: TXD0, TXD1, TX_EN (outputs to ESP32-P4 GPIO35–37)
     - REF_CLK: 50 MHz input from ESP32-P4 GPIO50
     - MDIO, MDC (GPIO28, GPIO31)
     - MDI: TD+, TD−, RD+, RD− (from J1 via 49.9 Ω series resistors)
     - VDD, VDDIO, GND (including exposed pad = GND)
  2. Set footprint to `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm`
     (standard KiCad library — no custom footprint needed for U5).
  3. Wire all RMII nets to the corresponding ESP32-P4 (U3) pins using matching net names.
  4. Add 4 × 100 nF decoupling capacitor symbols on U5 VDD pins + 1 × 10 µF bulk cap
     (reference designators to be assigned sequentially after the last existing cap).
  5. Re-run `python hardware/generate_project.py` and confirm exit code 0.

  Commit message: `hw: add U5 LAN8720A PHY symbol and RMII net connections in generator (#40)`

  > **Note:** Use only the verified GPIO numbers from architecture.md §3 (closed T001).
  > RMII fixed pins are GPIO32–37 + GPIO50. MDIO = GPIO28, MDC = GPIO31.

- **Depends on:** T001
- **Acceptance:** `python -m py_compile hardware/generate_project.py` exits code 0;
  `Select-String hardware/generate_project.py -Pattern "LAN8720A"` returns at least one match;
  RMII net names appear in both U3 and U5 symbol definitions.
- **GitHub issue:** #46

---

### T005: Redesign J1 RJ45 symbol to expose MDI pairs in generate_project.py [#47]

- **Layer:** Hardware: Schematic
- **Description:** Edit `hardware/generate_project.py` to replace the existing
  `Custom:RJ45_PoE` symbol for J1 with `Custom:RJ45_PoE_PHY` that exposes both the PoE
  power centre-tap pairs (to U1 Ag9905M — unchanged) and the MDI secondary winding data
  pairs (to U5 LAN8720A via termination resistors).

  Changes required:
  1. Rename the J1 symbol from `Custom:RJ45_PoE` to `Custom:RJ45_PoE_PHY`.
  2. Retain all existing PoE pair pins: `POE_A+`, `POE_A−`, `POE_B+`, `POE_B−`
     (connected to U1 — P-POE-02 prohibits any change to the primary side topology).
  3. Add MDI secondary winding pins: `ETH_TD+`, `ETH_TD−`, `ETH_RD+`, `ETH_RD−`.
  4. Add 4 × 49.9 Ω ±1% / 0402 series resistors (R_TD_P, R_TD_N, R_RD_P, R_RD_N)
     between J1 MDI secondary pins and U5 MDI inputs. Assign reference designators
     sequentially after the last existing resistor.
  5. Re-run generator and confirm exit code 0.

  Commit message: `hw: replace J1 RJ45_PoE with RJ45_PoE_PHY exposing MDI pairs (#40)`

  > ⚠️ **OQ-03 (BLOCKING):** The exact secondary winding pin numbers for the Würth
  > 615008144521 must be confirmed from the datasheet §Pin Description before this task
  > can be committed. Download the Würth 615008144521 datasheet, locate the secondary
  > MDI output pin numbers, and record them in this issue as a comment before implementing.
  > Do not commit J1 schematic changes until OQ-03 is explicitly closed in this issue.

- **Depends on:** T001
- **Acceptance:** `python -m py_compile hardware/generate_project.py` exits code 0;
  `Select-String hardware/generate_project.py -Pattern "RJ45_PoE_PHY"` returns a match;
  `Select-String hardware/generate_project.py -Pattern "ETH_TD"` returns matches for TD+ and TD−;
  `Select-String hardware/generate_project.py -Pattern "ETH_RD"` returns matches for RD+ and RD−.
- **GitHub issue:** #47

---

### T006: Add global labels for all RMII and MDI signals in generate_project.py [#48]

- **Layer:** Hardware: Schematic
- **Description:** Edit `hardware/generate_project.py` to add `global_label()` entries for
  every inter-block RMII and MDI net, per P-SCH-01 (all inter-block signals must use global
  labels). This task applies after T003, T004, and T005 have defined all new symbols and
  nets, to ensure every cross-block net is properly labelled.

  Signals requiring global labels (total 13 nets):
  - **RMII (7):** `EMAC_RXD0`, `EMAC_RXD1`, `EMAC_CRS_DV`, `EMAC_TXD0`, `EMAC_TXD1`,
    `EMAC_TX_EN`, `EMAC_REF_CLK`
  - **MDI (4):** `ETH_TD+`, `ETH_TD−`, `ETH_RD+`, `ETH_RD−`
  - **MDIO bus (2):** `ETH_MDIO`, `ETH_MDC`

  Requirements (per P-SCH-01 and architecture.md §8):
  - Each net must use `global_label()` at both endpoints (MCU side and PHY side / J1 side).
  - Label shapes must reflect signal direction: `input` for MCU-receive signals, `output`
    for MCU-transmit signals, `bidirectional` for MDIO.
  - Labels must land on the 2.54 mm grid (P-HW-06).
  - Re-run generator after edits; confirm exit code 0.

  Commit message: `hw: add global labels for RMII and MDI inter-block nets in generator (#40)`

- **Depends on:** T003, T004, T005
- **Acceptance:** `Select-String hardware/generate_project.py -Pattern "global_label"` returns
  at least 13 new matches covering all RMII and MDI signal names; generator runs without error.
- **GitHub issue:** #48

---

### T007: Run ERC and achieve 0 errors [#49]

- **Layer:** Hardware: ERC
- **Description:** After all schematic tasks (T003–T006) are complete, regenerate the
  schematic and run the Electrical Rules Check. Fix any ERC violations introduced by the
  ESP32-P4 migration. Commit the refreshed `erc_output.json`.

  Steps:
  1. Run `python hardware/generate_project.py` — must exit with code 0.
  2. Run:
     ```
     kicad-cli sch erc hardware/kicad/PoE-FanController.kicad_sch \
       --output hardware/kicad/erc_output.json --format json
     ```
  3. Inspect `erc_output.json` — `error_count` must equal `0` (warnings acceptable).
  4. If errors exist: identify each violation, fix in `generate_project.py`, re-run generator,
     re-run ERC, repeat until 0 errors.
  5. Commit `hardware/kicad/erc_output.json` (and any generator fixes).

  Commit message: `hw: run ERC after ESP32-P4 schematic migration — 0 errors (#40)`

  Common ERC issues to watch for:
  - Unconnected RMII pins if any signal was missed in T006
  - Power pin type mismatches on U5 VDD vs. 3.3 V power symbol
  - Missing PWR_FLAG on newly added power nets

- **Depends on:** T006
- **Acceptance:** `hardware/kicad/erc_output.json` is committed, is valid JSON, and its
  `error_count` field equals `0`. The file timestamp is newer than the T006 commit.
- **GitHub issue:** #49

---

### T008: Add U5 LAN8720A placement to PCB layout in generate_project.py [#50]

- **Layer:** Hardware: Layout
- **Description:** Edit the PCB-generation section of `hardware/generate_project.py` to
  place the LAN8720A (U5) footprint on the PCB. Add all required decoupling capacitors
  to the PCB as well.

  Requirements (per architecture.md §7 EMC + P-HW-02 + P-ISO-02):
  - U5 must be placed on F.Cu only (P-HW-02).
  - U5 must be east of x = 38 mm (secondary domain, P-ISO-02/05).
  - Target placement: as close to J1 MDI secondary pins as routing allows, to minimise
    MDI stub length.
  - 4 × 100 nF bypass caps within 1 mm of U5 VDD pins; 1 × 10 µF bulk cap within 3 mm.
  - Check courtyard of QFN-24 (approx. 5 × 5 mm) against existing Zone B passives
    (R1–R4, C3–C6 at x ≈ 45–52, y ≈ 47–56 mm) and adjust placement if collision exists.
  - Re-run generator; confirm exit code 0.

  Commit message: `hw: place U5 LAN8720A and decoupling caps in PCB layout (#40)`

  > ⚠️ **OQ-06:** Before committing, manually verify the chosen (x, y) coordinates for U5
  > produce no courtyard overlap with existing Zone B components. Record the final
  > placement coordinates in a comment on this issue.

- **Depends on:** T007, T002
- **Acceptance:** `python -m py_compile hardware/generate_project.py` exits code 0;
  U5 footprint (`QFN-24-1EP_4x4mm`) appears in the PCB section of the generator at
  coordinates east of x = 38 mm; no courtyard violations are introduced (verified by
  visual inspection or KiCad DRC).
- **GitHub issue:** #50

---

### T009: Verify and update J1 PCB footprint for Würth 615008144521 MDI access [#51]

- **Layer:** Hardware: Layout
- **Description:** Confirm that the PCB footprint assigned to J1 in the PCB generation
  section of `hardware/generate_project.py` correctly represents the Würth 615008144521
  with MDI secondary winding pins accessible for routing. Update if needed.

  Steps:
  1. Open the Würth 615008144521 datasheet §PCB Footprint / Recommended Land Pattern.
  2. Compare the existing J1 footprint in the generator against the datasheet.
  3. Confirm that MDI secondary winding pads (ETH_TD+/−, ETH_RD+/−) are present as
     distinct, routable pads on the footprint.
  4. If footprint is correct: add a comment in the generator noting "Verified vs. Würth
     615008144521 datasheet [date]".
  5. If footprint is incorrect or missing MDI pads: author or update the footprint file in
     `hardware/kicad/footprints/Custom.pretty/` and update the generator reference.
  6. Re-run generator; confirm exit code 0.

  Commit message: `hw: verify/update J1 footprint for Würth 615008144521 MDI secondary pins (#40)`

  > ⚠️ **OQ-03 linkage:** The same Würth 615008144521 datasheet needed to close OQ-03
  > in T005 also provides the PCB footprint. Coordinate with T005 implementer.

- **Depends on:** T007
- **Acceptance:** The J1 footprint in the PCB generator has been verified against the
  Würth 615008144521 datasheet; a confirmation comment is present in the generator source;
  `python -m py_compile hardware/generate_project.py` exits code 0.
- **GitHub issue:** #51

---

### T010: Add RMII and MDI trace stubs to PCB generator [#52]

- **Layer:** Hardware: Layout
- **Description:** Edit the PCB-generation section of `hardware/generate_project.py` to
  add trace stubs for all RMII and MDI nets, per the EMC requirements in architecture.md §7.

  Trace requirements:
  | Net group | Spec |
  |---|---|
  | RMII REF_CLK (GPIO50) | ≤ 25 mm trace length; GND guard trace on both sides |
  | RMII data (6 nets: RXD0/1, CRS_DV, TXD0/1, TX_EN) | Length-match within ±5 mm; minimise vias |
  | MDI differential pairs (TD+/−, RD+/−) | 100 Ω differential, edge-coupled; length-match per pair |
  | MDI termination resistors (R_TD_P/N, R_RD_P/N) | Place < 2 mm from U5 MDI pins |

  All traces on Signal net class (0.25 mm width per P-HW-07) except MDI pairs which use
  differential pair rules (see constitution §3.1 P-HW-07).
  All new traces on F.Cu only (P-HW-02).

  Commit message: `hw: add RMII and MDI trace stubs with EMC constraints in PCB generator (#40)`

- **Depends on:** T008, T009
- **Acceptance:** `python -m py_compile hardware/generate_project.py` exits code 0;
  trace entries for all 13 RMII/MDI net names appear in the PCB generator section;
  REF_CLK trace stub length does not exceed 25 mm.
- **GitHub issue:** #52

---

### T011: Run DRC and validate violation count does not exceed baseline [#53]

- **Layer:** Hardware: DRC
- **Description:** After all PCB tasks (T008–T010) are complete, regenerate the PCB and
  run the Design Rules Check. Confirm that no new violations have been introduced by the
  ESP32-P4 PCB changes (baseline: 67 violations on `main` before this feature).

  Steps:
  1. Run `python hardware/generate_project.py` — must exit with code 0.
  2. Run:
     ```
     kicad-cli pcb drc hardware/kicad/PoE-FanController.kicad_pcb \
       --output hardware/kicad/drc_output.json --format json
     ```
  3. Count total violations in `drc_output.json`.
  4. Confirm count ≤ 67 (baseline) AND that no violation refers to a net, pad, or
     courtyard introduced by the ESP32-P4 migration tasks.
  5. Commit `hardware/kicad/drc_output.json`.

  Commit message: `hw: run DRC after ESP32-P4 PCB layout — ≤67 violations (#40)`

  > **Escalation path:** If new violations > 0 are introduced by migration tasks, fix them
  > in the PCB generator before committing. Do not accept a higher baseline violation count
  > as a result of this feature.

- **Depends on:** T010
- **Acceptance:** `hardware/kicad/drc_output.json` is committed; total violation count is
  ≤ 67; no violation description references `ESP32-P4`, `LAN8720A`, `EMAC`, `MDI`, or
  the new resistor reference designators.
- **GitHub issue:** #53

---

### T012: Update platformio.ini for ESP32-P4 board and framework [#54]

- **Layer:** Firmware: Config
- **Description:** Edit `platformio.ini` (and author the custom board manifest if required)
  to target the ESP32-P4-MINI-1U-N16R8.

  Changes required:
  1. Set `board = esp32-p4-function-ev-board` (upstream base board).
  2. Set `platform = espressif32 @ >=6.9.0`.
  3. Set `framework = arduino`.
  4. Add `platform_packages = framework-arduinoespressif32 @ >=3.1.0` to pin
     arduino-esp32 ≥ 3.1.0.
  5. Author `boards/esp32-p4-mini-1u.json` custom manifest overriding:
     - `flash_size = 16MB` (N16 variant)
     - PSRAM: 8 MB (R8 variant settings)
     - `build.mcu = esp32p4`
  6. Update `board` in `platformio.ini` to point to the custom manifest:
     `board = esp32-p4-mini-1u` (with `board_dir = boards/`).
  7. Run `pio run` (or `pio run --dry-run`) to validate the configuration resolves without
     toolchain error.

  Commit message: `fw: update platformio.ini and add ESP32-P4 custom board manifest (#40)`

  > ⚠️ **OQ-04:** The exact JSON schema for the custom board manifest must match the
  > PlatformIO espressif32 platform's board JSON schema. Reference
  > `esp32-p4-function-ev-board.json` in the espressif32 platform package as a template.
  > Record the final manifest path and any schema deviations as a comment on this issue.

  > ⚠️ **OQ-05 linkage:** ESPAsyncWebServer fork compatibility (T013) depends on the
  > platform version set here. Ensure the `lib_deps` in T013 are consistent with the
  > arduino-esp32 3.x version pinned in this task.

- **Depends on:** none
- **Acceptance:** `platformio.ini` references `espressif32 @ >=6.9.0` and `arduino-esp32 >=3.1.0`;
  `boards/esp32-p4-mini-1u.json` exists; `pio run` exits without "board not found" or
  toolchain resolution errors.
- **GitHub issue:** #54

---

### T013: Replace WiFi initialisation with Ethernet in firmware [#55]

- **Layer:** Firmware: Module
- **Description:** Modify the firmware source files to remove all WiFi-specific code and
  replace it with wired Ethernet via `ETH.h` (LAN8720A RMII), and replace ArduinoOTA with
  the HTTP OTA endpoint. Changes span four modules per architecture.md §6.

  **`src/main.cpp` (or `main.ino`):**
  - Remove `#include <WiFi.h>`, `WiFi.begin()`, WiFi event handlers.
  - Add `#include <ETH.h>`.
  - Add `ETH.begin(ETH_PHY_LAN8720, 0, ETH_MDC_PIN, ETH_MDIO_PIN, -1, ETH_CLOCK_GPIO_OUT_1)`
    using pin constants from T014.
  - Add `ARDUINO_EVENT_ETH_GOT_IP` event handler that logs `ETH.localIP()`.
  - Remove `#include <ArduinoOTA.h>` and `ArduinoOTA.begin()` / `ArduinoOTA.handle()`.

  **`src/ota.cpp` (full rewrite):**
  - Remove UDP ArduinoOTA logic.
  - Implement `POST /api/v1/ota` handler using `Update.h` streaming pattern:
    ```cpp
    server.on("/api/v1/ota", HTTP_POST, [](AsyncWebServerRequest *r){
        r->send(200, "text/plain", Update.hasError() ? "FAIL" : "OK");
        ESP.restart();
    }, handleOtaUpload);
    ```
  - The upload callback must use `Update.write(data, len)` with no `delay()` calls (P-FW-04).

  **`src/web.cpp`:**
  - Replace `WiFi.localIP()` with `ETH.localIP()` in status API response.
  - Update any network status fields (SSID, RSSI → not applicable; replace with link speed,
    duplex from `ETH.linkSpeed()` / `ETH.fullDuplex()`).

  **`src/fan.cpp`:**
  - Update LEDC API from deprecated 2.x style to arduino-esp32 3.x style:
    ```cpp
    // Replace: ledcSetup(ch, 25000, 8); ledcAttachPin(pin, ch);
    // With:    ledcAttach(pin, 25000, 8);
    ledcAttach(FAN1_PWM_PIN, 25000, 8);
    ledcWrite(FAN1_PWM_PIN, duty);
    ```

  **`platformio.ini` lib_deps:**
  - Replace `ESPAsyncWebServer` with `mathieucarbou/ESPAsyncWebServer @ ^3.x`
  - Replace `AsyncTCP` with `mathieucarbou/AsyncTCP @ ^3.x` (IDF 5.x compatible)

  Commit message: `fw: replace WiFi+ArduinoOTA with Ethernet+HTTP-OTA; update LEDC API (#40)`

  > ⚠️ **OQ-05 (CRITICAL):** Before merging, verify that `mathieucarbou/ESPAsyncWebServer`
  > and `mathieucarbou/AsyncTCP` compile and serve requests correctly on ESP32-P4 under
  > arduino-esp32 3.x. Test on a Function EV Board or document compilation evidence in
  > a comment on this issue. If incompatible, raise a new issue before merging this task.

- **Depends on:** T001, T012
- **Acceptance:** `pio run` (or `pio ci`) exits with code 0 and produces a binary;
  no `WiFi.h` or `ArduinoOTA.h` includes remain in `src/`;
  `src/ota.cpp` contains `POST /api/v1/ota` and `Update.write`;
  `src/fan.cpp` uses `ledcAttach()` (not `ledcSetup()`).
- **GitHub issue:** #55

---

### T014: Update GPIO pin constants to ESP32-P4 allocation [#56]

- **Layer:** Firmware: Module
- **Description:** Update all GPIO `#define` / `const` pin assignments in firmware headers
  or `platformio.ini` build flags to match the ESP32-P4 GPIO allocation from
  architecture.md §4. Remove any reference to old ESP32-WROOM-32D GPIO numbers.

  All constants to define (using `build_flags` in `platformio.ini` or a central `pins.h`):

  | Constant | GPIO | Note |
  |---|---|---|
  | `FAN1_PWM_PIN` | 4 | LEDC CH0 |
  | `FAN2_PWM_PIN` | 5 | LEDC CH1 |
  | `FAN3_PWM_PIN` | 6 | LEDC CH2 |
  | `FAN4_PWM_PIN` | 7 | LEDC CH3 |
  | `FAN1_TACH_PIN` | 8 | GPIO interrupt |
  | `FAN2_TACH_PIN` | 9 | GPIO interrupt |
  | `FAN3_TACH_PIN` | 10 | GPIO interrupt |
  | `FAN4_TACH_PIN` | 11 | GPIO interrupt |
  | `NTC_ADC_PIN` | 16 | ADC1 |
  | `STATUS_LED_PIN` | 2 | GPIO output |
  | `BOOT_PIN` | 0 | Strapping input |
  | `ETH_MDC_PIN` | 31 | GPIO-matrix |
  | `ETH_MDIO_PIN` | 28 | GPIO-matrix |

  RMII fixed pins (GPIO32–37, GPIO50) are handled automatically by `ETH.begin()` and do
  not need `#define` constants — document this assumption in a code comment.

  Scan all `src/` files for hardcoded GPIO numbers from the old ESP32-WROOM-32D layout
  and replace with the new constants. Remove any GPIO numbers that were WiFi-related and
  are no longer used.

  Commit message: `fw: update all GPIO pin constants to ESP32-P4 allocation (#40)`

  > **Note:** Use only the verified GPIO numbers from architecture.md §4 (T001 must be
  > complete). If T001 results in a correction to the pin table, update this task's
  > constants accordingly before committing.

- **Depends on:** T001, T012
- **Acceptance:** A grep of `src/` for the old WROOM GPIO numbers (e.g., the original
  WiFi/UART pin numbers) returns zero matches; all 13 constants above are defined in
  `pins.h` or `platformio.ini` build flags; `pio run` exits code 0.
- **GitHub issue:** #56

---

### T015: Update Bill of Materials for U3 replacement and U5/resistors addition [#57]

- **Layer:** Hardware: BOM
- **Description:** Update all BOM-tracking artifacts to reflect the v0.2 component changes:
  U3 replaced, U5 added, and 4 × MDI termination resistors added.

  Changes to make:
  1. **`docs/constitution.md` §2.2 BOM table** — already updated by MAJOR-001 amendment;
     verify U3 = `ESP32-P4-MINI-1U-N16R8` and U5 = `LAN8720A-CP-TR` are present. No edit
     needed if already correct.
  2. **`hardware/generate_project.py` BOM comments** (if any) — confirm U3 MPN, U5 MPN,
     and the 4 × 49.9 Ω 0402 series resistors (R_TD_P, R_TD_N, R_RD_P, R_RD_N) are
     listed with correct MPNs or value/footprint if MPN is TBD.
  3. **Create or update `hardware/bom.csv`** (if this file exists in the repository) with
     the new component rows:

     | Ref | Value | MPN | Footprint | Qty |
     |---|---|---|---|---|
     | U3 | ESP32-P4-MINI-1U-N16R8 | ESP32-P4-MINI-1U-N16R8 | Custom:ESP32-P4-MINI-1 | 1 |
     | U5 | LAN8720A-CP-TR | LAN8720A-CP-TR | QFN-24-1EP_4x4mm | 1 |
     | R_TD_P, R_TD_N, R_RD_P, R_RD_N | 49.9 Ω 1% 0402 | (TBD at procurement) | R_0402 | 4 |

  4. Remove the `ESP32-WROOM-32D` BOM row if present in any BOM file.

  Commit message: `hw: update BOM for U3→ESP32-P4-MINI-1U, U5 LAN8720A, MDI resistors (#40)`

- **Depends on:** T007
- **Acceptance:** `docs/constitution.md` §2.2 lists `ESP32-P4-MINI-1U-N16R8` for U3 and
  `LAN8720A-CP-TR` for U5; no reference to `ESP32-WROOM-32D` remains in any BOM file;
  the 4 MDI termination resistors are listed in the generator or BOM file.
- **GitHub issue:** #57

---

### T016: Write firmware unit tests for Ethernet init, OTA handler, and GPIO constants [#58]

- **Layer:** Unit Tests
- **Description:** Author unit tests covering the three firmware areas modified by this
  migration: Ethernet initialisation, HTTP OTA handler, and GPIO pin constant correctness.
  Tests must live in `test/` per PlatformIO conventions and run via `pio test`.

  **Test file: `test/test_pins/test_pins.cpp`**
  - Assert all 13 GPIO constants from T014 match expected values:
    ```cpp
    TEST_ASSERT_EQUAL(4,  FAN1_PWM_PIN);
    TEST_ASSERT_EQUAL(5,  FAN2_PWM_PIN);
    // ... all 13 constants
    TEST_ASSERT_EQUAL(28, ETH_MDIO_PIN);
    TEST_ASSERT_EQUAL(31, ETH_MDC_PIN);
    ```
  - Assert no two different functions share the same GPIO number (collision check).

  **Test file: `test/test_ota/test_ota.cpp`**
  - Mock `Update.h` to verify the OTA handler calls `Update.begin()`, `Update.write()`,
    and `Update.end()` in the correct sequence.
  - Verify the handler returns HTTP 200 with `"OK"` on success and `"FAIL"` on error.
  - Verify no `delay()` is called within the handler (static analysis or mock assertion).

  **Test file: `test/test_fan/test_fan.cpp`**
  - Verify that PWM setup uses `ledcAttach(pin, 25000, 8)` (3-arg new API) and NOT
    `ledcSetup()` (deprecated 2.x API) — mock or stub the LEDC peripheral.

  Run: `pio test -e native` (for host-based tests) or `pio test -e esp32-p4-mini-1u`
  on target hardware.

  Commit message: `test: add unit tests for pin constants, OTA handler, and LEDC API (#40)`

- **Depends on:** T013, T014
- **Acceptance:** `pio test` exits code 0 with all three test suites passing;
  test files exist at the paths listed above; the GPIO collision check asserts no duplicates
  across the 13 defined constants.
- **GitHub issue:** #58

---

### T017: Update feature documentation and architecture diagram [#59]

- **Layer:** Documentation
- **Description:** Update all documentation artifacts to reflect the completed ESP32-P4
  migration. This task runs after hardware (T011), BOM (T015), and firmware tests (T016)
  are all complete.

  Changes required:
  1. **`docs/features/esp32-p4-migration/architecture.md`** — add a "Implementation
     Complete" section at the top noting which OQs were closed, which were deferred, and
     the final verified RMII pin table (already amended in T001).
  2. **`docs/constitution.md` §4 Firmware Architecture / §2.2 BOM** — verify all entries
     match the implemented state (no further amendment needed per MAJOR-001, but spot-check
     peripheral ownership table in §4 P-FW-02 against the actual firmware module structure).
  3. **`README.md`** — update the "Hardware" and "Firmware" sections to describe:
     - MCU: ESP32-P4-MINI-1U-N16R8 (RISC-V dual-core)
     - Ethernet PHY: LAN8720A-CP-TR (RMII)
     - Network: wired 100BASE-T (no WiFi)
     - OTA: HTTP POST `/api/v1/ota`
  4. **`docs/features/esp32-p4-migration/plan.md`** — mark status header from `PLANNING`
     to `IMPLEMENTED` and add a reference to the merged PR number.
  5. **`docs/architecture.md`** (top-level, if it exists) — update the hardware block
     diagram to show ESP32-P4 + LAN8720A + revised J1 topology.

  Commit message: `docs: update README, architecture, and plan.md for ESP32-P4 migration (#40)`

- **Depends on:** T011, T015, T016
- **Acceptance:** `README.md` contains "ESP32-P4" and "LAN8720A"; `plan.md` status header
  reads `IMPLEMENTED`; `architecture.md` contains `[TRM-VERIFIED]` annotation (from T001);
  no document still refers to "ESP32-WROOM-32D" as the current MCU.
- **GitHub issue:** #59

---

### T018: Post final status update on issue #40 and open closing PR [#60]

- **Layer:** Issue update
- **Description:** After all tasks (T001–T017) are complete and the branch is ready for
  review, post a closing comment on GitHub issue #40 confirming every acceptance criterion
  from the feature plan is satisfied, then open the pull request.

  Comment must confirm:
  ```
  ✅ T001: RMII GPIO32–37+GPIO50 verified against ESP32-P4 TRM §EMAC
  ✅ T002: ESP32-P4-MINI-1 custom LGA-56 footprint committed to Custom.pretty/
  ✅ T003: U3 ESP32-WROOM-32D replaced by ESP32-P4-MINI-1U in generate_project.py
  ✅ T004: U5 LAN8720A added to schematic with full RMII + MDI + power nets
  ✅ T005: J1 redesigned as RJ45_PoE_PHY exposing MDI pairs (OQ-03 closed)
  ✅ T006: Global labels for all 13 RMII/MDI inter-block nets
  ✅ T007: ERC 0 errors (erc_output.json committed)
  ✅ T008: U5 placed on PCB — F.Cu, east of x=38 mm, no courtyard violations
  ✅ T009: J1 PCB footprint verified against Würth 615008144521 datasheet
  ✅ T010: RMII + MDI trace stubs with EMC constraints committed
  ✅ T011: DRC ≤67 violations, 0 new violations from migration (drc_output.json committed)
  ✅ T012: platformio.ini updated; custom boards/esp32-p4-mini-1u.json authored
  ✅ T013: WiFi/ArduinoOTA removed; ETH.begin() + HTTP POST /api/v1/ota implemented
  ✅ T014: All GPIO constants updated to ESP32-P4 allocation
  ✅ T015: BOM updated — U3 ESP32-P4-MINI-1U, U5 LAN8720A, 4× MDI resistors
  ✅ T016: Unit tests pass — pin constants, OTA handler, LEDC API
  ✅ T017: README, plan.md, architecture.md updated
  ```

  Open a pull request from `feature/40-replace-esp32-with-esp32-p4` → `main` with
  description "Closes #40".

- **Depends on:** T017
- **Acceptance:** Issue #40 has a comment listing all 17 ✅ criteria above; a PR from
  `feature/40-replace-esp32-with-esp32-p4` into `main` is open and its description
  contains "Closes #40".
- **GitHub issue:** #60
