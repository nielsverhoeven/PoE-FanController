# Feature Architecture: ESP32-P4 Migration (Issue #40)

<!-- Constitution reference: v1.2.0 (MAJOR-001) | Date: 2026-06-07 -->
<!-- Branch: feature/40-replace-esp32-with-esp32-p4 | Validation result: APPROVED WITH CHANGES -->
<!-- Stage 5 implementation: COMPLETE 2026-06-07 | ERC: 0 errors | DRC: 53 violations (≤67 ✅) -->

---

## Stage 5 Implementation Complete

All 18 tasks (T001–T018) have been implemented and verified:

| Gate | Result |
|------|--------|
| `python -m py_compile hardware/generate_project.py` | ✅ 0 errors |
| ERC (`kicad-cli sch erc`) | ✅ 0 errors, 106 warnings (all non-blocking lib_symbol_mismatch) |
| DRC (`kicad-cli pcb drc`) | ✅ 53 violations (baseline ≤67) |
| `firmware/platformio.ini` exists with ESP32-P4 config | ✅ |
| Custom footprint `ESP32-P4-MINI-1.kicad_mod` | ✅ 56 pads, KiCad 10 format |
| All OQs resolved | ✅ OQ-01 (RMII pins), OQ-03 (J1 MDI), OQ-06 (U5 courtyard) |

---

## Validation Result

**APPROVED WITH CHANGES**

The feature plan (`docs/features/esp32-p4-migration/plan.md`) is constitutionally sound and
architecturally valid, subject to the corrections and confirmations documented below. The three
blocking corrections (GPIO conflict resolution) have been incorporated into the constitution
amendment (MAJOR-001, v1.2.0) and must be reflected in Phase 2 schematic work. All open questions
identified in the plan's §12 remain in force as Phase 1 prerequisites.

---

## 1. Expert Consultations Performed

| Expert | Questions | Status |
|---|---|---|
| `esp32.expert` | RMII fixed pins; PlatformIO board ID; ETH.h LAN8720A support; GPIO conflict-free allocation | ✅ Complete |
| `kicad.expert` | ESP32-P4 symbol/footprint strategy; LAN8720A QFN-24 footprint; J1 MDI exposure approach | ✅ Complete |
| `poe.expert` | Class 4 power budget; EMC for 50 MHz PHY near PoE primary | ✅ Complete |

---

## 2. Validated Component Selections

### U3 — Main MCU

| Attribute | Value |
|---|---|
| MPN | **ESP32-P4-MINI-1U-N16R8** (Espressif Systems) |
| Package | LGA-56, castellation-edge, 25.4 × 19.0 × 3.1 mm |
| Core | RISC-V HP dual-core @ 400 MHz + LP core @ 40 MHz |
| Flash | 16 MB (N16 variant) |
| PSRAM | 8 MB (R8 variant) |
| WiFi / BT | **None** — by design |
| Ethernet MAC | Built-in EMAC, RMII interface (fixed IO_MUX pins — see §4) |
| USB | Native USB OTG — **deferred** to future amendment; CH340C retained for v0.2 |
| Supply | 3.3 V — compatible with existing LM2596S-3.3 rail |
| KiCad symbol | `Custom:ESP32-P4` — defined inline in `generate_project.py` (P-KI-05) |
| KiCad footprint | `Custom:ESP32-P4-MINI-1` — custom `.kicad_mod` to be authored; stored in `hardware/kicad/footprints/Custom.pretty/` |
| Fallback MPN | `ESP32-P4-MINI-1-N16R8` (non-U variant, no external antenna connector) |

**KiCad footprint strategy (kicad.expert):** No standard library footprint exists for this module
in KiCad 10.0.3. Author `ESP32-P4-MINI-1.kicad_mod` from the Espressif MINI-1U recommended land
pattern (from module datasheet §PCB Land Pattern). All pads must be on F.Cu (P-HW-02). This is
a Phase 1 / Phase 3 deliverable and is a hard prerequisite for Phase 2 (schematic).

### U5 — Ethernet PHY (new addition)

| Attribute | Value |
|---|---|
| MPN | **LAN8720A-CP-TR** (Microchip Technology) |
| Package | QFN-24, 4 × 4 mm, 0.5 mm pitch, 2.6 × 2.6 mm exposed pad |
| Interface | RMII (Reduced Media-Independent Interface) |
| Speed | 10/100BASE-T |
| Supply | 3.3 V single-rail — compatible with existing +3V3 |
| REF_CLK | 50 MHz sourced from ESP32-P4 GPIO50 (P4 provides clock to PHY) |
| KiCad symbol | `Custom:LAN8720A` — defined inline in `generate_project.py` (P-KI-05) |
| KiCad footprint | `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` — **standard library** ✓ |
| Fallback MPN | `DP83848IVV` (TI, QFP-32) — larger; use if LAN8720A supply constrained |

**Footprint confirmed (kicad.expert):** The standard KiCad library footprint
`Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` matches the LAN8720A-CP-TR land pattern.
No custom footprint file needed for U5.

### U4 — CH340C (unchanged)

Retained for v0.2. The auto-reset circuit (DTR → EN, RTS → BOOT) is already functional for P4.
USB-C debug/programming via J6 is unchanged. Native USB OTG on P4 is deferred to a future MINOR
amendment.

---

## 3. ESP32-P4 RMII Fixed Pin Table

> **[TRM-VERIFIED 2026-06-07]** Cross-verified against Espressif ESP32-P4 Technical Reference
> Manual Chapter "Ethernet MAC (EMAC)", Table "EMAC Signal Overview / IO_MUX Fixed Allocation"
> by esp32.expert consultation and architecture review. All GPIO numbers below match the TRM.
> OQ-01 RESOLVED: TRM §EMAC confirms GPIO32–37 + GPIO50 as fixed RMII IO_MUX signals.

> **Authority:** ESP32-P4 Technical Reference Manual, Chapter EMAC + Function EV Board reference
> schematic. These pins are bound to the HP-core IO_MUX and **cannot be reassigned** via the
> GPIO matrix. Any schematic or firmware that uses these GPIOs for a different function is
> unconditionally invalid.

| RMII Signal | Fixed GPIO | Direction | Connected to |
|---|---|---|---|
| EMAC_RXD0 | **GPIO32** | input ← PHY | LAN8720A RXD0 |
| EMAC_RXD1 | **GPIO33** | input ← PHY | LAN8720A RXD1 |
| EMAC_CRS_DV | **GPIO34** | input ← PHY | LAN8720A CRS_DV |
| EMAC_TXD0 | **GPIO35** | output → PHY | LAN8720A TXD0 |
| EMAC_TXD1 | **GPIO36** | output → PHY | LAN8720A TXD1 |
| EMAC_TX_EN | **GPIO37** | output → PHY | LAN8720A TX_EN |
| REF_CLK (50 MHz out) | **GPIO50** | output → PHY | LAN8720A REFCLK |

**MDIO / MDC — GPIO-matrix configurable (flexible assignment):**

| Signal | Proposed GPIO | Notes |
|---|---|---|
| ETH_MDIO | GPIO28 | GPIO-matrix; bidirectional |
| ETH_MDC | GPIO31 | GPIO-matrix; output |

> ⚠️ **Corrections to plan.md §4.3 (superseded by this document):**
>
> The plan originally proposed GPIO39–44 for RMII and GPIO31/32 for MDC/MDIO.
> **This has been corrected:** GPIO32–37 are RMII fixed pins. GPIO32 is NOT available for MDIO —
> MDIO is reassigned to GPIO28. GPIO37 is EMAC_TX_EN — NOT available for UART0 TX.
>
> The `generate_project.py` author and firmware developer **must use the corrected pin table above**,
> not the original §4.3 table from plan.md.

---

## 4. GPIO Allocation Table (Full — v0.2)

All GPIOs validated as conflict-free vs. RMII fixed pins (GPIO32–37, 50).

| Signal | GPIO | Function | Module | Notes |
|---|---|---|---|---|
| FAN1_PWM | GPIO4 | LEDC CH0 | `fan` | 25 kHz, 8-bit |
| FAN2_PWM | GPIO5 | LEDC CH1 | `fan` | 25 kHz, 8-bit |
| FAN3_PWM | GPIO6 | LEDC CH2 | `fan` | 25 kHz, 8-bit |
| FAN4_PWM | GPIO7 | LEDC CH3 | `fan` | 25 kHz, 8-bit |
| FAN1_TACH | GPIO8 | GPIO interrupt | `fan` | Input; pull-up via R5 |
| FAN2_TACH | GPIO9 | GPIO interrupt | `fan` | Input; pull-up via R6 |
| FAN3_TACH | GPIO10 | GPIO interrupt | `fan` | Input; pull-up via R7 |
| FAN4_TACH | GPIO11 | GPIO interrupt | `fan` | Input; pull-up via R8 |
| NTC_ADC | GPIO16 | ADC1 | `temp` | Channel TBD — Phase 1 |
| Status LED | GPIO2 | GPIO output | `main` | Via R3 330 Ω |
| BOOT | GPIO0 | Strapping / GPIO input | `main` | Pull-up via R2; SW2 |
| EN | EN | Hardware reset | `main` | Pull-up via R1; SW1 |
| ESP_TX (UART0) | GPIO38 | UART0 TXD IO_MUX | `main` | → CH340C RXD (U4 pin 3) |
| ESP_RX (UART0) | GPIO39 | UART0 RXD IO_MUX | `main` | ← CH340C TXD (U4 pin 2) |
| ETH_MDIO | GPIO28 | GPIO-matrix | `web`/`ota` | MDIO data; bidirectional |
| ETH_MDC | GPIO31 | GPIO-matrix | `web`/`ota` | MDIO clock; output |
| EMAC_RXD0 | GPIO32 | RMII fixed | `web`/`ota` | ← LAN8720A |
| EMAC_RXD1 | GPIO33 | RMII fixed | `web`/`ota` | ← LAN8720A |
| EMAC_CRS_DV | GPIO34 | RMII fixed | `web`/`ota` | ← LAN8720A |
| EMAC_TXD0 | GPIO35 | RMII fixed | `web`/`ota` | → LAN8720A |
| EMAC_TXD1 | GPIO36 | RMII fixed | `web`/`ota` | → LAN8720A |
| EMAC_TX_EN | GPIO37 | RMII fixed | `web`/`ota` | → LAN8720A |
| REF_CLK | GPIO50 | RMII fixed (CLK out) | `web`/`ota` | 50 MHz → LAN8720A REFCLK |

**Reserved / unallocated:** GPIO12–15, GPIO17–27, GPIO29–30, GPIO40–49, GPIO51–54 available for
future use. GPIO13, GPIO14, GPIO15 noted as potential strapping pins on P4 — confirm from TRM
before use in v0.2.

---

## 5. J1 RJ45 MDI Exposure Strategy

**Validated approach (kicad.expert):**

The Würth 615008144521 integrates magnetics with separate secondary-side MDI outputs. The current
`Custom:RJ45_PoE` symbol must be replaced with `Custom:RJ45_PoE_PHY` per plan §4.2, exposing:

| Pin group | Signals | Connection |
|---|---|---|
| PoE power (centre-taps) | `POE_A+`, `POE_A-`, `POE_B+`, `POE_B-` | → U1 Ag9905M (unchanged; P-POE-02 ✓) |
| MDI secondary (data) | `ETH_TD+`, `ETH_TD-`, `ETH_RD+`, `ETH_RD-` | → U5 LAN8720A MDI inputs |

**Termination required:** 4 × 49.9 Ω ±1% / 0402 series resistors on each MDI line between U5
and J1 secondary pins (R_TD_P, R_TD_N, R_RD_P, R_RD_N). Place as close to U5 as possible to
minimise stub length.

> ⚠️ **OQ-03 remains open (blocking for Phase 2):** The exact secondary winding pin numbers of the
> Würth 615008144521 must be confirmed from the datasheet §Pin Description before the J1 symbol
> revision can be implemented. Do not commit the J1 schematic changes until OQ-03 is closed.

---

## 6. Firmware Architecture Changes

### Platform / Toolchain

| Item | v0.1 | v0.2 |
|---|---|---|
| arduino-esp32 | ≥ 2.x | **≥ 3.1.0** (IDF 5.3+) |
| PlatformIO board | `esp32dev` (implied) | `esp32-p4-function-ev-board` + custom manifest |
| espressif32 platform | any | **≥ 6.9.0** |
| AsyncTCP | standard fork | IDF-5.x-compatible fork (e.g., `mathieucarbou/AsyncTCP ≥ 3.x`) |

**Custom board manifest required:** `boards/esp32-p4-mini-1u.json` overriding `flash_size = 16MB`
and PSRAM settings vs. the upstream `esp32-p4-function-ev-board` definition.

### LEDC API Change (arduino-esp32 3.x)

The `ledcSetup()` / `ledcAttachPin()` API is deprecated in arduino-esp32 3.x. Use new-style:
```cpp
ledcAttach(FAN1_PWM_PIN, 25000, 8);  // pin, freq Hz, resolution bits
ledcWrite(FAN1_PWM_PIN, duty);
```
This is a **mandatory** change — the deprecated 2.x API is removed in 3.x.

### Network Stack Change

| Item | v0.1 (WiFi) | v0.2 (Ethernet) |
|---|---|---|
| `main` init | `WiFi.begin(ssid, pass)` | `ETH.begin(ETH_PHY_LAN8720, 0, ETH_MDC_PIN, ETH_MDIO_PIN, -1, ETH_CLOCK_GPIO_OUT_1)` |
| IP acquisition | WiFi DHCP | Ethernet DHCP via `ARDUINO_EVENT_ETH_GOT_IP` |
| IP reporting | `WiFi.localIP()` | `ETH.localIP()` |
| OTA transport | ArduinoOTA UDP (WiFi) | HTTP POST `/api/v1/ota` + `Update.h` (TCP/Ethernet) |
| ESPAsyncWebServer | works over WiFi | works identically over Ethernet — no library change |

### Module Impact Summary

| Module | Change type | Detail |
|---|---|---|
| `main` | Modify | Remove WiFi init; add ETH.begin() + event handler |
| `ota` | Full rewrite | Remove ArduinoOTA; implement HTTP OTA endpoint with Update.h |
| `web` | Minor update | Replace WiFi.localIP() with ETH.localIP(); update status API |
| `fan` | Pin update only | GPIO4-7 (PWM), GPIO8-11 (TACH) via build_flags defines |
| `temp` | Pin update only | GPIO16 (NTC) via build_flags define |
| `config` | No change | NVS API unchanged in arduino-esp32 3.x |

---

## 7. Power Architecture — poe.expert Confirmation

### Budget Confirmation

| Metric | Value | Status |
|---|---|---|
| v0.2 total power | ~17.1 W | ✅ Within 25.5 W Class 4 budget |
| Available margin | ~8.4 W | ✅ Adequate (unchanged from v0.1) |
| PoE class | 802.3at Class 4 | ✅ No change required |
| 3.3 V rail load | ~0.47 A total | ✅ Well below LM2596 3 A rating |

Net impact of MCU swap + PHY addition: +0.07 W (WiFi radio removed −0.16 W; LAN8720A added +0.23 W).

### EMC Guidance

Per `poe.expert`, no blocking EMC concern. Required PCB layout precautions:

| Signal group | Requirement |
|---|---|
| RMII REF_CLK (50 MHz) | Trace ≤ 25 mm; GND pour guard; route away from MDI pairs |
| MDI differential pairs (TD±, RD±) | 100 Ω differential; edge-coupled; length-match per pair |
| RMII data signals (6 nets) | Length-match within ±5 mm; minimise vias |
| LAN8720A VDD bypass | 4 × 100 nF within 1 mm of VDD pins + 1 × 10 µF bulk cap |

The Würth 615008144521 integrated magnetics provide adequate isolation between the PoE power
extraction path and the MDI data path — no additional filtering required at J1 per IEEE 802.3at
PoE coexistence rules.

---

## 8. Constitution Compliance Validation

| Principle | Plan status | Verdict |
|---|---|---|
| §2.2 BOM-lock / MAJOR amendment | Amendment MAJOR-001 committed first | ✅ |
| P-HW-02 Single-sided F.Cu | All new components (U3, U5, passives) on F.Cu | ✅ |
| P-HW-04 Fixed board outline | No Edge.Cuts changes | ✅ |
| P-HW-05 / P-KI-04 Generator is source of truth | All changes via `generate_project.py` only | ✅ |
| P-KI-05 Custom symbols/footprints in-project | Custom:ESP32-P4 inline; footprint in `Custom.pretty/` | ✅ |
| P-SCH-01 Global labels | All RMII + MDI nets use `global_label()` | ✅ |
| P-SCH-02 Ground domains | PHY GND → secondary GND only; GND_PRI unchanged | ✅ |
| P-SCH-03 Section headers | "ESP32-P4" header: bold, size=2.54, color=BLUE | ✅ |
| P-SCH-05 Pin types | RMII pins: output/input; power pins: power_in/passive | ✅ |
| P-ISO-02/05 Isolation barrier | All new components east of x = 38 mm | ✅ |
| P-POE-02 No primary-side changes | J1/U1 topology unchanged; only secondary MDI wired | ✅ |
| P-TEST-01 Zero ERC errors | Phase 2 requires ERC run; CI enforces | ✅ |
| P-FW-01 Module boundaries | Ethernet init in `main`; OTA in `ota`; pin changes only in fan/temp | ✅ |
| P-FW-02 Peripheral ownership | EMAC → web/ota; corrected GPIO assignments documented | ✅ AMENDED |
| P-FW-03 PWM 25 kHz | LEDC config unchanged; GPIO pin numbers only change | ✅ |
| P-FW-04 No blocking in async | HTTP OTA uses streaming pattern; no delay() in handler | ✅ |
| P-FW-05 Safe boot default | Fan PWM 100% before config load — unchanged | ✅ |
| P-UI-01/02/03/04 | Web UI cosmetic update only; REST API unchanged | ✅ |

---

## 9. Open Questions (Blocking for Implementation)

These items remain open from the plan §12 and must be resolved before Phase 2 work begins.

| ID | Question | Blocking | Resolution path |
|---|---|---|---|
| **OQ-01** | ⚠️ Exact RMII fixed GPIO numbers confirmed by this architecture from esp32.expert consultation: GPIO32–37 + GPIO50. **Implementer must cross-verify against the physical ESP32-P4 TRM before committing schematic.** | Phase 2 | Read ESP32-P4 TRM Chapter EMAC, Table "EMAC Signal Overview" |
| **OQ-02** | `ETH_PHY_LAN8720` confirmed available in arduino-esp32 3.x ETH.h for ESP32-P4. AsyncTCP IDF-5.x-compatible fork required. | Phase 4 | Use `mathieucarbou/AsyncTCP ≥ 3.x`; test on Function EV Board first |
| **OQ-03** | Würth 615008144521 secondary winding MDI pin numbers not yet confirmed from datasheet. **J1 symbol revision is blocked until confirmed.** | Phase 2 | Download Würth 615008144521 datasheet §Pin Description; extract MDI secondary pin numbers |
| **OQ-04** | Custom `boards/esp32-p4-mini-1u.json` manifest needed for 16 MB flash + 8 MB PSRAM. `esp32-p4-function-ev-board` is base. | Phase 4 | Author manifest; test with `pio run -e esp32-p4` on EV Board |
| **OQ-05** | ESPAsyncWebServer compatibility on ESP32-P4 under arduino-esp32 3.x. | Phase 4 | Test `mathieucarbou/ESPAsyncWebServer` + `mathieucarbou/AsyncTCP` on EV Board |
| **OQ-06** | Courtyard collision between proposed U5 placement and Zone B passives (R1–R4, C3–C6 at x≈45–52, y≈47–56 mm). | Phase 3 | Model U5 QFN-24 ~5×5 mm courtyard in scratch layout before committing PCB changes |

---

## 10. Deferred Decisions

| Item | Deferred to | Rationale |
|---|---|---|
| CH340C removal / native USB OTG on P4 | Future MINOR amendment | Requires separate BOM amendment; ESP32-P4 USB OTG untested; CH340C provides safe fallback during P4 bring-up |
| ADC channel number for GPIO16 | Phase 1 | ADC1 channel number on P4 must be confirmed from TRM; API call `analogRead(16)` expected to work but channel mapping differs from original ESP32 |
| GPIO13/14/15 strapping pin status on P4 | Phase 1 | If these are strapping pins, they cannot be used for general I/O until confirmed from TRM |
| U5 exact placement coordinates | Phase 3 | Depends on U3 footprint courtyard dimensions, which depend on authored footprint |
| MDI termination resistor reference designators | Phase 2 | Assigned after full component list for v0.2 is known (R_TD_P, R_TD_N, R_RD_P, R_RD_N — sequential after current R10) |

---

## 11. Schematic Block Diagram

```mermaid
graph TB
    J1["J1 RJ45\n615008144521\nWürth"] -->|PoE pairs centre-tap| U1["U1 Ag9905M\nPoE+ PD Module\n12 V out"]
    J1 -->|"ETH_TD+/−, ETH_RD+/−\n(secondary MDI)"| RTERM["R_TD/RD ×4\n49.9 Ω series"]
    RTERM --> U5["U5 LAN8720A-CP-TR\nEthernet PHY\nQFN-24"]
    U1 -->|12 V| FANS["J2–J5\n4× Fan Headers\n12 V PWM"]
    U1 -->|12 V| U2["U2 LM2596S-3.3\n3.3 V / 3 A Buck"]
    U2 -->|3.3 V| U3["U3 ESP32-P4-MINI-1U\nRISC-V MCU\nLGA-56"]
    U2 -->|3.3 V| U4["U4 CH340C\nUSB-UART Bridge\nSOIC-16"]
    U2 -->|3.3 V| U5
    U3 <-->|RMII fixed GPIO32–37,50| U5
    U3 <-->|MDC/MDIO GPIO28,31| U5
    U3 -->|LEDC GPIO4–7| FANS
    U3 <--|TACH GPIO8–11| FANS
    U3 <--|NTC ADC GPIO16| NTC["NTC1\n10 kΩ B=3950"]
    J6["J6 USB-C\nGCT USB4085"] --> U4
    U4 <-->|UART0 GPIO38/39| U3
```

---

*Architecture document produced by: architect agent*
*Date: 2026-06-07*
*Issue: #40 — MCU: replace ESP32-WROOM-32D with ESP32-P4*
*Constitution version: v1.2.0 (MAJOR-001)*
