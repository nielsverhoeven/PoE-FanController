# Architecture Note: Correct GPIO Pin Assignments (Issue #148)

> Feature: `correct-gpio-pin-assignments`
> Branch: `feature/148-correct-gpio-pin-assignments`
> Architect validation date: 2026-06-10 (re-validated 2026-06-10 — Stage 3 re-run)
> Constitution version at validation: **4.2.1** (v4.2.0 amended by this feature; v4.2.1 PATCH applied in Stage 3 re-run)
> Result: **APPROVED** — constitution amendments v4.2.0 (MINOR) and v4.2.1 (PATCH) applied; routing out of scope confirmed

---

## 1. Validation Scope

This note validates `docs/features/correct-gpio-pin-assignments/plan.md` against
`docs/constitution.md` and records all architecture decisions and expert findings for issue #148.

---

## 2. GPIO Capability Findings (esp32.expert consultation)

All checks performed against `docs/kb/ESP32-P4-POE-ETH/board-reference.md`,
`docs/kb/ESP32-P4-POE-ETH/pin-layout.md`, `docs/kb/esp32-p4-reference.md`,
and the ESP32-P4 Technical Reference Manual.

### 2.1 EMAC Conflict — GPIO32 and GPIO33

| GPIO | EMAC function | IO_MUX | Can be used for fan signals? |
|------|---------------|--------|------------------------------|
| GPIO32 | EMAC_RXD0 | **Fixed** (cannot be remapped) | ⛔ FORBIDDEN |
| GPIO33 | EMAC_RXD1 | **Fixed** (cannot be remapped) | ⛔ FORBIDDEN |

**Source:** `board-reference.md §2`, `esp32-p4-reference.md §2`, ESP32-P4 TRM §EMAC.

**Consequence for plan:** The issue #148 description incorrectly marks GPIO32/33 as usable.
The plan correctly identifies this and substitutes:
- FAN4_PWM → **GPIO27** (J8 pin 27) instead of GPIO33
- FAN3_TACH → **GPIO46** (J8 pin 24) instead of GPIO32

### 2.2 GPIO26 and GPIO27 — EMAC Safety

The forbidden EMAC set for the ESP32-P4-POE-ETH is:
**{GPIO31, GPIO32, GPIO33, GPIO34, GPIO35, GPIO36, GPIO37, GPIO50, GPIO51, GPIO52}**

GPIO26 and GPIO27 are **not** in this set and appear in the authoritative 40-pin header layout
(pins 29 and 27 respectively). ✅ **Safe for LEDC PWM.**

### 2.3 LEDC PWM Capability — GPIO20, GPIO21, GPIO26, GPIO27

The ESP32-P4 LEDC peripheral is routed to output pins exclusively via the **GPIO matrix**.
Any GPIO that is:
(a) not occupied by a fixed-function peripheral (EMAC, UART, strapping), and
(b) accessible on the header,

can be assigned to a LEDC channel. All four proposed PWM GPIOs satisfy both conditions:

| Signal | GPIO | J8 Pin | EMAC conflict? | Strapping pin? | LEDC capable? |
|--------|------|--------|----------------|----------------|---------------|
| FAN1_PWM | GPIO20 | 35 | ✅ No | ✅ No | ✅ YES |
| FAN2_PWM | GPIO21 | 34 | ✅ No | ✅ No | ✅ YES |
| FAN3_PWM | GPIO26 | 29 | ✅ No | ✅ No | ✅ YES |
| FAN4_PWM | GPIO27 | 27 | ✅ No | ✅ No | ✅ YES |

### 2.4 GPIO Interrupt / TACH Capability — GPIO22, GPIO23, GPIO46, GPIO47, GPIO48

All ESP32-P4 GPIOs that are connected to the GPIO matrix support edge-triggered and
level-triggered interrupts. The five proposed TACH/LED GPIOs:

| Signal | GPIO | J8 Pin | In authoritative table? | Forbidden list? | IRQ capable? |
|--------|------|--------|------------------------|-----------------|--------------|
| FAN1_TACH | GPIO22 | 32 | ✅ Yes (`pin-layout.md`) | ✅ No | ✅ YES |
| FAN2_TACH | GPIO23 | 31 | ✅ Yes (`pin-layout.md`) | ✅ No | ✅ YES |
| FAN3_TACH | GPIO46 | 24 | ✅ Yes (`board-reference.md §4`) | ✅ No | ✅ YES |
| FAN4_TACH | GPIO47 | 22 | ✅ Yes (`board-reference.md §4`) | ✅ No | ✅ YES |
| PROBE_LED  | GPIO48 | 21 | ✅ Yes (`board-reference.md §4`) | ✅ No | ✅ YES (output) |

> **Risk item from plan §7 resolved:** The plan flagged GPIO47/48 as "not confirmed usable in
> existing KB docs". They ARE listed in `board-reference.md §4` (full 40-pin table, pins 22 and 21)
> and are absent from the forbidden GPIO list in `board-reference.md §4.3`. Confirmed safe.

---

## 3. Constitution Compliance Check

| Constitution principle | Status | Notes |
|------------------------|--------|-------|
| **P-HW-05** — Schematic generated, not hand-edited | ✅ PASS | All changes in `hardware/generator/components.py`; `.kicad_sch` is a build artefact only |
| **P-HW-06** — Grid discipline | ✅ PASS | Symbol body geometry unchanged (25.4 × 50.8 mm); only pin names, types, and net wiring change; `snap()` enforces grid compliance |
| **P-HW-01/02** — Two-layer, top-side placement only | ✅ PASS | No layer or placement changes |
| **P-HW-04** — Board outline and J8 placement | ✅ PASS | J8 mechanical position unchanged; only pad nets change |
| **P-HW-09** — Polarised connectors | ✅ PASS | J8 is explicitly exempt (board-to-board); no new cable connectors added |
| **P-KI-01/02/03** — KiCad version and format locks | ✅ PASS | Generator emits same format tokens; no version upgrade |
| **P-KI-04** — Generator is schematic source of truth | ✅ PASS | Only `components.py` is modified; `.kicad_sch` is downstream artefact |
| **P-KI-07** — PCB is hand-edited in KiCad GUI | ✅ PASS | PCB updated via "Update PCB from Schematic" in KiCad; no script writes to `.kicad_pcb` |
| **P-TEST-01** — Zero ERC errors | ✅ REQUIRED | Plan mandates ERC run (T-02) after each generator iteration; blocking merge criterion |
| **P-TEST-03** — Zero DRC errors | ✅ REQUIRED | Plan mandates DRC run (T-05) after PCB netlist sync; blocking merge criterion |
| **P-FW-02** — Peripheral ownership documented | ⚠️ AMENDED | Table updated in constitution v4.2.0 (see §4 below) |
| **P-FW-03** — PWM 25 kHz / 8-bit | ✅ PASS | PWM specification unchanged; LEDC configuration unchanged except GPIO numbers |
| **P-SCH-01** — Global labels for inter-block signals | ✅ PASS | All signals continue to use `global_label` elements |
| **P-SCH-05** — Correct pin types | ✅ PASS | NC → `no_connect`; GND → `passive`; signal outputs/inputs/bidir correctly typed in updated lists |

---

## 4. Required Constitution Amendment

**Amendment version:** v4.2.0 (MINOR)
**Rationale for MINOR classification:** Updates table entries in P-FW-02 to correct GPIO
assignments and pin references; also corrects pre-existing EMAC MDIO entry (GPIO28→GPIO52).
No architectural principle is removed or redefined; no MAJOR technology choice changes.

### 4.1 Changes Applied to Constitution

The following edits were applied to `docs/constitution.md`:

**§2.3 Firmware table — DHT11 pin reference:** Corrected "J8 pin 23" → "J8 pin 15"
(pin 23 is physically GND; pin 15 = GPIO16 is the correct DHT11 DATA connection).

**§4 P-FW-02 Peripheral ownership table — complete replacement:**
- LEDC channels: GPIO4/5/6/7 → **GPIO20/21/26/27** with J8 right-column pin references
- GPIO interrupts (TACH): GPIO8/9/10/11 → **GPIO22/23/46/47** with J8 right-column pin references
- DHT11_DATA: J8 pin reference corrected from "pin 23" (GND) → **"left pin 15"** (GPIO16)
- STATUS_LED: J8 pin reference corrected from "left pin 3" (GND) → **"left pin 6"** (GPIO2)
- PROG_LED: J8 pin reference corrected from "right pin 22" (GND) → **"left pin 14"** (GPIO15)
- DS18B20_DATA: J8 pin reference corrected from "left pin 27" (GND) → **"left pin 19"** (GPIO19)
- PROBE_LED: GPIO corrected from GPIO20 (now FAN1_PWM) → **GPIO48** via J8 right pin 21
- Ethernet MAC/RMII: MDIO corrected from GPIO28 → **GPIO52** (ESP32-P4 Waveshare Kconfig confirmed; GPIO28 was ESP32-classic value)
- PHY_RST **GPIO51** added to Ethernet MAC row (previously absent)
- **I2C (SDA/SCL) reserved row removed** — GPIO21 now assigned to FAN2_PWM; GPIO22 now assigned to FAN1_TACH; I2C is no longer a candidate for these pins

---

## 5. J8 Signal-to-GPIO Map (Target State — post-amendment)

```
graph TB
    subgraph J8_Left ["J8 Left Column (x=2.81mm)"]
        P6["Pin 6 · GPIO2"]
        P14["Pin 14 · GPIO15"]
        P15["Pin 15 · GPIO16"]
        P19["Pin 19 · GPIO19"]
        PGND_L["Pins 3,8,13,18 · GND"]
    end

    subgraph J8_Right ["J8 Right Column (x=18.19mm)"]
        P21["Pin 21 · GPIO48"]
        P22["Pin 22 · GPIO47"]
        P24["Pin 24 · GPIO46"]
        P27["Pin 27 · GPIO27"]
        P29["Pin 29 · GPIO26"]
        P31["Pin 31 · GPIO23"]
        P32["Pin 32 · GPIO22"]
        P34["Pin 34 · GPIO21"]
        P35["Pin 35 · GPIO20"]
        P36["Pin 36 · 3V3"]
        P40["Pin 40 · VBUS/5V"]
        PGND_R["Pins 23,28,33,38 · GND"]
        PFBDN["Pins 25,26 · GPIO33/32 EMAC ⛔"]
    end

    P6  -->|STATUS_LED| LED1["R3 → LED1 (green)"]
    P14 -->|PROG_LED| LED2["R13 → LED2 (orange)"]
    P15 -->|DHT11_DATA| J9["J9 DHT11 connector"]
    P19 -->|DS18B20_DATA| J6["J6 + R14 4.7kΩ → probe"]

    P21 -->|PROBE_LED| LED6["R15 330Ω → LED6 (green)"]
    P22 -->|FAN4_TACH| J5T["J5 pin3 + R8 pull-up"]
    P24 -->|FAN3_TACH| J4T["J4 pin3 + R7 pull-up"]
    P27 -->|FAN4_PWM| J5P["J5 pin4"]
    P29 -->|FAN3_PWM| J4P["J4 pin4"]
    P31 -->|FAN2_TACH| J3T["J3 pin3 + R6 pull-up"]
    P32 -->|FAN1_TACH| J2T["J2 pin3 + R5 pull-up"]
    P34 -->|FAN2_PWM| J3P["J3 pin4"]
    P35 -->|FAN1_PWM| J2P["J2 pin4"]
    P36 -->|+3V3| PWR3V3["R5-R8 pull-ups · J9 VCC"]
    P40 -->|+5V| BOOST["U_BOOST 5V→12V"]
```

> Mermaid note: The `subgraph` wrapping allows the diagram to render in GitHub Markdown.
> Pins 25/26 (GPIO33/GPIO32) and 30 (RUN) are left as NC in the generator — correctly excluded.

---

## 6. PCB Impact Assessment

| Aspect | Impact |
|--------|--------|
| J8 footprint | **Unchanged** — same physical position, same pad coordinates; only pad net assignments change after "Update PCB from Schematic" |
| Fan traces | **All 8 fan signal traces must be rerouted.** Signals move from left column pads (x=2.81mm) to right column pads (x=18.19mm), which are physically closer to J2–J5 fan headers in the right zone (x>21mm). Net routing effort is reduced; trace lengths shorten by ~15mm per signal. |
| +3V3 routing | +3V3 source moves from pads 1/17 (left col, x=2.81mm) to pad 36 (right col, x=18.19mm). Pull-up resistors R5–R8 and J9 VCC must connect to pad 36 net instead. Expect airwires on R5–R8 pin 1 and J9 VCC after netlist sync. |
| Other signals | STATUS_LED, PROG_LED, DHT11_DATA, DS18B20_DATA GPIOs **unchanged** (GPIO2, 15, 16, 19) — only J8 pad numbers change. Existing traces from those left-column pads may become airwires requiring reroute. |

---

## 7. Testing Obligations (from plan §6, confirmed)

| Test | Blocking? | Description |
|------|-----------|-------------|
| T-01 | Pre-impl | Cross-check §2 pin table against authoritative board image before any file edit |
| T-02 | ✅ Merge-blocking | Zero ERC errors after `python hardware/generate_project.py` + `kicad-cli sch erc` |
| T-03 | Required | Net inspector spot-check per plan §6 T-03 table |
| T-04 | Required | Verify +3V3 net (pad 36) connects to R5–R8 pin 1 and J9 VCC |
| T-05 | ✅ Merge-blocking | Zero DRC **rule** violations after PCB netlist sync (routing is **out of scope** — airwires from re-assigned fan signals are expected and tracked separately; unconnected airwires are explicitly excluded from this gate per plan §Change 8) |
| T-06 | Required | Confirm P-FW-02 table diff matches constitution v4.2.0 values |

---

## 8. Verdict

**APPROVED WITH CHANGES**

The plan is architecturally sound. All proposed GPIO assignments are validated as safe and
capable on the ESP32-P4-POE-ETH. The plan correctly avoids the EMAC-forbidden GPIO32/33
and substitutes appropriate alternatives. The generator-only implementation path satisfies
P-HW-05 and P-KI-04. Constitution amendment v4.2.0 has been applied to `docs/constitution.md`.

**Merge conditions:**
1. ERC must report **zero errors** (T-02) — blocking
2. DRC must report **zero rule violations** after PCB netlist sync (T-05) — blocking. PCB re-routing is **out of scope** for this issue; unconnected airwires produced by the netlist sync are expected, tracked separately, and are NOT a DRC failure gate for this PR.
3. `erc_output.json` must be updated and committed alongside the schematic change
4. Firmware `platformio.ini` `build_flags` (FAN*_PIN, PROBE_LED_PIN) must be updated to
   new GPIO numbers in a follow-on firmware commit (tracked separately per spec §Out of Scope)

---

## 9. Stage 3 Re-validation — 2026-06-10

> Re-validation triggered by: issue #148 updated 2026-06-10 with scope changes and additional
> confirmed pin errors.
> Constitution version at re-validation: **4.2.1** (PATCH applied during this re-run — see below).
> Re-validation result: **APPROVED** (no new blocking issues found)

### 9.1 Scope Changes Validated

| Change | Architecture Assessment |
|--------|------------------------|
| **T4 "Route PCB Traces" — OUT OF SCOPE** | ✅ **CORRECT.** Routing is not required for schematic correctness or ERC compliance. DRC after netlist sync is still required (zero rule violations); unconnected airwires from the netlist sync are a routing concern tracked separately and are explicitly excluded from the DRC merge gate for this PR. `§7 T-05` and `§8 Merge condition 2` updated in this document to reflect this. |
| **New footprint rename (FR-12, T002):** `Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical` → `Custom:ESP32-P4-PoE-ETH-PinSocket` | ✅ **NO CONSTITUTION VIOLATION.** The rename is a purely cosmetic/identity change. Physical pad geometry, row-to-row spacing (15.38 mm), pad pitch (2.54 mm), pad numbering, and all mechanical constraints are **unchanged**. The new name is self-documenting and consistent with the project naming convention. No new footprint library source is introduced (custom footprint remains in `hardware/kicad/footprints/Custom.pretty/`). Satisfies P-KI-05 (custom footprints in-project). |

### 9.2 Additional Confirmed Pin Errors — Architecture Assessment

The following pin errors were confirmed by the 2026-06-10 audit. Each is validated against
`docs/kb/ESP32-P4-POE-ETH/pin-layout.md` (HIGH confidence source):

| Pin | Error | Physical type per pin-layout.md | Plan correction | Status |
|-----|-------|--------------------------------|-----------------|--------|
| 2 | Generator assigns `+5V (power_out)` | GPIO (DM/GPIO24) — not a power rail | NC (`no_connect`) | ✅ CORRECT per pin-layout.md line: "DM / GPIO24 \| GPIO" |
| 4 | Generator assigns `+5V (power_out)` | GPIO (SDA/GPIO7) — not a power rail | NC (`no_connect`) | ✅ CORRECT per pin-layout.md line: "SDA / GPIO7 \| GPIO" |
| 20 | Generator assigns `GND (passive)` | GPIO (GPIO54) — not GND | NC (`no_connect`) | ✅ CORRECT per pin-layout.md line: "GPIO54 \| GPIO" |
| 25 | Generator assigns `GND (passive)` | GPIO33 (EMAC_RXD1, forbidden) | NC (`no_connect`) | ✅ CORRECT — GPIO, not GND; EMAC-forbidden so NC is right choice |
| 26 | Generator assigns `GND (passive)` | GPIO32 (EMAC_RXD0, forbidden) | NC (`no_connect`) | ✅ CORRECT per pin-layout.md line: "GPIO32 \| GPIO" + board-reference.md §2 EMAC conflict |
| 30 | Generator assigns `GND (passive)` | RUN (system control) | NC (`no_connect`) | ✅ CORRECT per pin-layout.md line: "RUN \| System Control" |
| 33 | Generator assigns `FAN2_PWM` signal | **GND** (physical GND pad) | GND (`passive`) | ✅ CORRECT per pin-layout.md line: "GND \| Ground"; signal on physical GND = PCB short |
| 34 | Generator assigns `GND (passive)` | GPIO21 | FAN2_PWM (`output`) | ✅ CORRECT per pin-layout.md line: "GPIO21 \| GPIO"; FAN2_PWM correctly moves here from pin 33 |

All eight additional pin errors are consistent with `pin-layout.md` and are correctly
handled in the plan's target state (§3.1 table). No architectural concerns raised.

### 9.3 Footprint Rename — Constitution Compliance

The footprint rename was checked against all constitution principles:

| Principle | Impact | Status |
|-----------|--------|--------|
| **P-KI-05** — Custom footprints in-project | Rename stays within `Custom.pretty/`; no external library reference added | ✅ PASS |
| **P-HW-05** — Schematic generated | Rename applied in `components.py` and `gen_footprint_j8.py`; `.kicad_sch` is downstream artefact | ✅ PASS |
| **P-KI-07** — PCB is hand-edited | Footprint rename propagates to `.kicad_pcb` via "Update PCB from Schematic" (T004); no script writes to `.kicad_pcb` | ✅ PASS |
| **P-HW-04** — J8 placement constraints | Physical pad geometry, row spacing, and origin position **unchanged**; only the name string changes | ✅ PASS |
| **§2.2 BOM lock** — Footprint name entry | The footprint name in §2.2 is a BOM reference, not a component substitution. The **physical component is unchanged**. Rename does not trigger the MAJOR-amendment clause (which governs component substitutions, not identifier changes). | ✅ PASS |

**Constitution PATCH applied:** Amendment v4.2.1 (2026-06-10) updates:
- `§2.2` J8 BOM table: `Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical` → `Custom:ESP32-P4-PoE-ETH-PinSocket`
- `§3.1 P-HW-03` exception note: same old name → new name
- `§2.2` J8 Role description: stale "+5V (pins 2 & 4), +3.3V (pins 1 & 17)" language corrected to reflect Amendment v4.2.0 pin assignments (VBUS pin 40, +3V3 pin 36)
- `§10 Amendment History`: v4.2.1 entry added

### 9.4 DRC Gate — Clarification for Routing-Out-of-Scope

After the netlist sync ("Update PCB from Schematic"), the following are expected and **do not block merge**:
- Airwires (unconnected connections) on all 8 fan signal pads (FAN1–4 PWM and TACH), as signals move from left column pads to right column pads
- Airwires on +3V3 consumers (R5–R8 pin 1, HUM1 pin 1) as +3V3 source moves to pad 36

The DRC gate for this PR covers **rule violations only** (clearance, courtyard overlap, footprint validity). The unconnected-net count is tracked separately in the PR description and is a routing follow-on task.

### 9.5 Residual Observations (Non-Blocking)

The following items were observed during re-validation. They are **not blocking** for this PR but should be tracked as follow-on:

| Item | Location | Observation |
|------|----------|-------------|
| `§5.1` Power chain diagram | `docs/constitution.md` | Still shows `+3V3 back to carrier via J8 pin 1/17`. Pin 36 is the correct +3V3 source per Amendment v4.2.0. The §5.1 ASCII diagram was not updated in v4.2.0; needs a PATCH amendment (separate from footprint rename) |
| `§8.4` Bring-up checklist items 3, 6 | `docs/constitution.md` | Item 3 references "J8 pin 2 (after D2)" for +5V measurement; item 6 references "J8 pin 1" for +3.3V. Per Amendment v4.2.0 corrections, pin 40 (VBUS) is the +5V source and pin 36 is the +3V3 output. Checklist needs a PATCH amendment |
| `§2.2` DHT11 description | `docs/constitution.md` | Still says "J8 pin 23" (physically GND); Amendment v4.2.0 corrects this in §2.3 and P-FW-02 but the DHT11 BOM row Role text was not updated |
| `§2.2` verification warning | `docs/constitution.md` | Still says "+5V on pins 2 & 4" which is the old incorrect assignment; this warning is now superseded by Amendment v4.2.0 |

All four observations are documentation cleanup items only; none affect the correctness of the generator changes or the ERC/DRC gates.

---
