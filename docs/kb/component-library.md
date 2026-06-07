# Component Library

<!-- Last updated: 2026-06-07 (session 2) | Source: constitution v1.3.0, BOM, expert consultations -->
<!-- All MPNs are BOM-locked unless noted. Changes require MAJOR or MINOR amendment. -->

---

## BOM-Locked Components

| Ref | MPN | Manufacturer | Package | KiCad Symbol | KiCad Footprint | Amendment required |
|---|---|---|---|---|---|---|
| U1 | Ag9905M | Silvertel | 2×4 pin header 2.54 mm | Custom:Ag9905M | Custom:Ag9905M | MAJOR |
| U2 | LM2596S-3.3/NOPB | TI | D2PAK (TO-263-5) | Custom:LM2596S | Package_TO_SOT_SMD:TO-263-5 | MAJOR |
| U3 | ESP32-P4-MINI-1U-N16R8 | Espressif | LGA-56 castellation | Custom:ESP32-P4-MINI-1U | Custom:ESP32-P4-MINI-1 (must author) | MAJOR |
| U4 | CH340C | WCH | SOIC-16 | Custom:CH340C | Package_SO:SOIC-16_3.9x9.9mm_P1.27mm | MAJOR |
| U5 | LAN8720A-CP-TR | Microchip | QFN-24 | Custom:LAN8720A | Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm ✅ | MAJOR |
| J1 | 615008144521 | Würth | RJ45 horizontal | Custom:RJ45_PoE_PHY | Custom:Wuerth_615008144521 | MAJOR |
| J2–J5 | 47053-1000 | Molex | 4-pin 2.54 mm | Custom:FAN_HEADER | Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical | MAJOR |
| J6 | USB4085-GF-A | GCT | USB-C THT | Custom:USB_C | Custom:GCT_USB4085 | MAJOR |
| L1 | SRR5028-680Y | Bourns | Axial THT 68 µH | Custom:L_SRR5028 | Inductor_THT:L_Axial_L13.0mm_D6.0mm_P20.32mm | MAJOR |
| D1 | 1N5822 | Various | DO-201AD THT | Device:D_Schottky | Diode_THT:D_DO-201AD_P12.70mm_Horizontal | MAJOR |

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
