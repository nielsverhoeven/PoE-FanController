# Component Library

<!-- Last updated: 2026-06-08 (session 3) | Source: constitution v3.1.0, BOM, expert consultations -->
<!-- All MPNs are BOM-locked unless noted. Changes require MAJOR or MINOR amendment. -->

---

## Current BOM — Daughter Board (v3.1.0)

The custom PCB is now a **daughter board** for the Waveshare ESP32-P4-POE-ETH (SKU 32088).
PoE, Ethernet, ESP32, USB-C are all on the Waveshare board. The daughter board is SELV-only.

| Ref | MPN / Value | Manufacturer | Package | KiCad Footprint | Role |
|---|---|---|---|---|---|
| **J8** | Female 2×20 pin socket, 2.54mm pitch, **15.38mm row spacing** | — | THT | `Custom:PinSocket_2x20_P2.54mm_P15.38mm_Vertical` | Daughter board ↔ Waveshare ESP32-P4-POE-ETH interface; row spacing = 21mm board − 2×2.81mm edge offsets |
| **U_BOOST** | LM2587-12 (fixed 12V) | TI | TO-220-3 Vertical | `Package_TO_SOT_THT:TO-220-3_Vertical` | 5V→12V boost converter for fan rail |
| **J2–J5** | 47053-1000 | Molex | 4-pin 2.54mm | `Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical` | 4-wire 12V PWM fan headers — on right zone of daughter board |
| **R3** | 330Ω | — | 0402 SMD | `Resistor_SMD:R_0402_1005Metric` | LED current limit |
| **R4** | 10kΩ | — | 0402 SMD | `Resistor_SMD:R_0402_1005Metric` | NTC voltage divider (top resistor) |
| **R5–R8** | 10kΩ | — | 0402 SMD | `Resistor_SMD:R_0402_1005Metric` | TACH pull-ups to +3.3V |
| **LED1** | Green LED | — | LED_D3.0mm THT | `LED_THT:LED_D3.0mm` | Status LED (GPIO2 via J8) |
| **NTC1** | 10kΩ B=3950 NTC | — | Axial THT | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | Temperature sensing |

---

## Passive Components

| Ref | Value | Role | Notes |
|---|---|---|---|
| R1 | 10 kΩ | NTC pull-up | Top of voltage divider to 3.3 V |
| R2 | 10 kΩ | Reset pull-up | ESP32-P4 EN pin |
| R3 | 10 kΩ | BOOT pull-up | GPIO0 default HIGH |
| R4 | 10 kΩ NTC (B=3950) | NTC thermistor | Bottom of voltage divider |
| **R15** | **6.04 kΩ (RC0402FR-076K04L)** | **LAN8720A RBIAS** | **MANDATORY — sets PHY internal bias current; PHY non-functional without it** |
| C1 | 100 µF / 16 V | Bulk decoupling | After LM2596 output |
| C2 | 100 nF | Local bypass | 3.3 V rail, near U3 |
| C3–C6 | 100 nF | Fan header bypass | One per fan header |
| NTC1 | 10 kΩ NTC (B=3950) | Temperature sensing | In series with R4 |

---

## LAN8720A Mandatory Support Components (design-critical)

All required or PHY will not function:

| Signal | Ref | Value | Connection | Notes |
|---|---|---|---|---|
| RBIAS (pin 4) | R15 | 6.04 kΩ | pin 4 → GND | Sets internal bias current — **non-negotiable** |
| LED1 (pin 12) | pull-up | 10 kΩ | pin 12 → 3.3V | MODE[0]=1 → 100BASE-TX auto-negotiate |
| LED2 (pin 11) | pull-up | 10 kΩ | pin 11 → 3.3V | MODE[1]=1 → full-duplex |
| nINTSEL (pin 10) | pull-up | 10 kΩ | pin 10 → 3.3V | Disables interrupt output |

---

## KiCad Footprint Notes

### Custom footprints (in `hardware/kicad/footprints/Custom.pretty/`)
- **ESP32-P4-MINI-1U** — must be authored from Espressif MINI-1U datasheet land pattern
  - Land pattern: 56-pad LGA castellation; castellation pitch TBD from datasheet
  - Courtyard: ~18 × 25.5 mm (verify from module drawing)
- **Ag9905M** — 2×4 pin header, 2.54 mm pitch (standard THT)
- **Würth 615008144521** — RJ45 with PoE magnetics; MDI secondary winding pin numbers **must be verified from datasheet (OQ-03)**

### Standard library footprints (no custom file needed)
- LAN8720A: `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm` ✅ confirmed
- LM2596S: `Package_TO_SOT_SMD:TO-263-5` (D2PAK standard)
- 1N5822: `Diode_THT:D_DO-201AD_P12.70mm_Horizontal`

---

## Datasheet Quick Facts

### Ag9905M
- Datasheet: https://silvertel.com/images/datasheets/Ag9900-Datasheet.pdf
- PoE pairs: pins 3, 4, 7, 8 (VPORT — connect to J1 data pairs 1-2 and 3-6)
- Output: pins 1 (VC/12V), 2 (RTN/GND_PRI), 5 (VOUT), 6 (VOUT_N/GND_PRI)

### LAN8720A
- Datasheet: https://ww1.microchip.com/downloads/en/DeviceDoc/8720a.pdf
- RMII interface: RXD[1:0], CRS_DV, TXD[1:0], TX_EN, REF_CLK (50 MHz input)
- MDI interface: TX+/TX−/RX+/RX− (connect to J1 secondary winding MDI pairs)
- PHY address: set by ADDR0/ADDR1 pins (default 0x00 when both pulled low)
- REF_CLK: can be sourced from ESP32-P4 GPIO50 (EMAC_REF_CLK output)
- Power: 3.3 V single rail (~70 mA typical)
- NRESET: active-low; tie via RC or drive from GPIO

### ESP32-P4-MINI-1U-N16R8
- Datasheet: https://www.espressif.com/sites/default/files/documentation/esp32-p4_datasheet_en.pdf
- TRM: https://www.espressif.com/sites/default/files/documentation/esp32-p4_technical_reference_manual_en.pdf
- EMAC chapter in TRM: verify RMII fixed GPIO table (OQ-01 — critical)
