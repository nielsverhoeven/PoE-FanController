# PoE & Power Reference

<!-- Last updated: 2026-06-07 | Source: poe.expert consultation + constitution v1.2.0 -->
<!-- Verified against: IEEE 802.3at, Silvertel Ag9905M datasheet -->

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
