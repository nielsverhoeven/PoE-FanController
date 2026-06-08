# PoE & Power Reference

<!-- Last updated: 2026-06-08 | Source: poe.expert consultation + constitution v1.2.0 + Issue #75 research -->
<!-- Verified against: IEEE 802.3at, Silvertel Ag9905M datasheet, esp32.expert/poe.expert Issue #75 analysis -->

---

## 1. PoE Standard Class Table

| Class | Standard | Max PD power | PSE output | Signature |
|---|---|---|---|---|
| 0 | 802.3af | 12.95 W | 15.4 W | 0–4 mA |
| 1 | 802.3af | 3.84 W | 4.0 W | 9–12 mA |
| 2 | 802.3af | 6.49 W | 7.0 W | 17–20 mA |
| 3 | 802.3af | 12.95 W | 15.4 W | 26–30 mA |
| **4** | **802.3at** | **25.5 W** | **30 W** | **36–44 mA** |
| 5 | 802.3bt | 40 W | 45 W | Type 3 |
| 6 | 802.3bt | 51 W | 60 W | Type 3 |

**This project: Class 4 (802.3at)**. No class change triggered by ESP32-P4 migration.

---

## 2. Ag9905M PoE Module (U1)

| Field | Value |
|---|---|
| MPN | Ag9905M (Silvertel) |
| Standard | 802.3at Class 4 |
| Output | 12 V nominal, 1.67 A max (20 W) |
| Isolation | Primary (PoE) to secondary (12 V): 1.5 kV minimum |
| Input voltage | 36–57 V (PSE output) |
| Package | 2×4 pin header, 2.54 mm pitch |
| Efficiency | ~85% typical |

**Pin types in schematic:** VPORT pins use `passive` (not `power_in`) — eliminates 4 ERC errors.

### Ag9905M Connections
```
Pin 1: VC    → 12V_POE (power output)
Pin 2: RTN   → GND_PRI (primary GND, isolated)
Pin 3: VPORT → PoE input (from J1 PoE pairs) — passive
Pin 4: VPORT → PoE input (from J1 PoE pairs) — passive
Pin 5: VOUT  → 12V_POE
Pin 6: VOUT_N → GND_PRI
Pin 7: VPORT → PoE input — passive
Pin 8: VPORT → PoE input — passive
```

---

## 3. Power Budget (v0.2 — ESP32-P4 + LAN8720A)

| Component | Voltage | Current | Power |
|---|---|---|---|
| U1 Ag9905M | 12 V in | — | 20 W available |
| U2 LM2596 efficiency | 12→3.3 V | — | ~85% |
| U3 ESP32-P4-MINI-1U | 3.3 V | ~300 mA peak | ~0.99 W |
| U4 CH340C | 3.3 V | ~20 mA | ~0.07 W |
| U5 LAN8720A | 3.3 V | ~70 mA | ~0.23 W |
| 4× fans (12 V) | 12 V | ≤1.0 A each | up to 12 W |
| NTC / passive | 3.3 V | <1 mA | negligible |
| **Total worst-case** | — | — | **~17.1 W** |
| **Margin vs Class 4** | — | — | **~8.4 W (33%)** |

**No PoE class change required** — well within Class 4 limits.

---

## 4. Isolation Rules (CRITICAL — safety)

- **≥ 1.5 kV isolation** between PoE primary side and secondary (SELV) side
- Primary GND: `GND_PRI` net (isolated, dangerous)
- Secondary GND: `GND` net (SELV, safe)
- These nets must **never** be connected — no copper continuity except through U1
- Minimum PCB creepage/clearance: follow IEC 62368-1 for 250 V working voltage class

---

## 5. EMC Guidance for Ethernet PHY

- **RMII REF_CLK (50 MHz):** keep trace ≤ 25 mm; add GND guard traces on both sides
- **MDI pairs (ETH_TD+/−, ETH_RD+/−):** route as 100 Ω differential pairs; match length within 5 mil
- **LAN8720A placement:** east of x=38 mm (Zone B); clear of PoE primary components
- **Decoupling:** 100 nF bypass caps within 1 mm of each VDD pin on U5
- **PHY is fully secondary-side** — no EMC isolation concern with PoE primary

---

## 6. LM2596S Buck Regulator (U2)

| Field | Value |
|---|---|
| MPN | LM2596S-3.3/NOPB (TI) |
| Package | D2PAK (TO-263-5) |
| Input | 12 V (from Ag9905M) |
| Output | 3.3 V fixed |
| Max current | 3 A |
| Inductor | L1: SRR5028-680Y 68 µH |
| Catch diode | D1: 1N5822 (3 A / 40 V Schottky) |
| Switch freq | 150 kHz typical |

---

## 7. SKU 32088 Power Architecture (Issue #75 — Daughter Board Design)

> Added: 2026-06-08 — from poe.expert + esp32.expert research for Issue #75 (ESP32-P4-POE-ETH redesign)

### 7.1 Architecture Overview

When the Waveshare ESP32-P4-POE-ETH (SKU 32088) is used as the main board, the PoE PD function moves entirely inside the Waveshare module. The daughter board (custom PCB) connects to the Waveshare 2×20 header and receives power from it.

```
[PoE switch — 802.3at Class 4 required]
       │  802.3at (37–57 V)
       ▼
  Waveshare ESP32-P4-POE-ETH (SKU 32088)
  │  Onboard PD module: PoE → 5V regulated
  │  (isolation is provided by the Waveshare board)
  └──► 2×20 header pin 2/4: +5V (likely — VERIFY)
            │
            ▼
       Daughter board (custom PCB, Issue #75)
       │  U_BOOST: 5V→12V boost converter
       │  (~85% efficiency, max ~1.3A at 12V from 802.3at budget)
       └──► J2–J5: 12V PWM fan headers (≤1.0A total / ≤12W)
```

### 7.2 Power Budget — Daughter Board (802.3at scenario)

| Stage | Value | Notes |
|---|---|---|
| 802.3at PD available | 25.5 W | Class 4, minimum PSE guarantee |
| PD module efficiency | ~85% | Isolated flyback inside Waveshare board |
| 5V available from PD | ~21.7 W | = 25.5 × 0.85 |
| Waveshare board self-use (ESP32-P4 + LAN8720A + USB) | ~3.5 W | Estimate — verify |
| Net available on 5V header pins | ~18.2 W | ≈ 3.64 A at 5V |
| Boost converter 5V→12V efficiency | ~85% | Typical for integrated switch boost |
| Available at 12V for fans | **~15.5 W** | ≈ 1.29 A at 12V |
| Fan load (max, all 4 fans) | ≤12.0 W | 1.0 A at 12V total (≤0.25 A per fan) |
| **Margin** | **~3.5 W (22%)** | Acceptable — wider than v2.0.0 Ag9905M margin |

> **Note on current spec:** The fan power budget is ≤1.0 A TOTAL for all 4 fans combined at 12V = ≤12W.
> This is ≤0.25 A per fan at 12V — consistent with standard 80–120mm PC fans (typical 0.1–0.25 A each).
> The poe.expert analysis using "1A per fan" was based on a mis-stated requirement; the correct spec is ≤1.0 A total.

### 7.3 Critical Requirement: 802.3at Mandatory

| Scenario | Fan budget at 12V | Verdict |
|---|---|---|
| 802.3at (Class 4) PSE | ~15.5W | ✅ Works with 3.5W margin |
| 802.3af (Class 3) PSE only | ~5.2W | ❌ Cannot power 12W fan load |

**The PSE (PoE switch/injector) MUST support 802.3at Class 4.** Document this as a system requirement in the installation guide.

### 7.4 5V→12V Boost Converter — Component Options

| MPN | Package | Vin | Vout | Iout | Notes |
|---|---|---|---|---|---|
| TI TPS61085 | SOT-23-6 | 2.7–5.5V | Adj | 1.5A | Small; 800kHz; adjust R divider for 12V |
| TI LM2587-12 | D2PAK-5 | 3.5–40V | 12V fixed | 2A | More current headroom; THT-friendly |
| XL6009E1 | SOP-8 | 3–32V | Adj | 4A | Wider margin; switch at 400kHz |

> Recommended: **TI LM2587-12** — fixed 12V output, 2A rating, familiar TO-263 footprint, well-characterized.
> Inductor: 68–100 µH, rated ≥1.5 A (e.g. Bourns SRR5028-100Y).
> Output cap: 100 µF, 25V, low-ESR electrolytic + 100nF ceramic.
> EMC: boost switching at ~100 kHz — keep well clear of 25 kHz fan PWM harmonics (25, 50, 75 kHz).

### 7.5 Isolation Note

With SKU 32088, the isolation barrier is internal to the Waveshare board (inside the PoE PD module). The daughter board operates entirely in the SELV domain. There is no primary-side circuitry on the daughter board — the isolation PCB slot (P-ISO-04) and x=38mm barrier rule (P-ISO-02) do NOT apply to the daughter board. The daughter board is a simpler, single-domain design.
