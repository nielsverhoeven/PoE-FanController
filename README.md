# PoE-FanController

A PoE 802.3at (25.5 W) powered quad-fan controller using the **Waveshare ESP32-P4-ETH**
development board (SKU 32086) mounted HAT-style on a custom carrier PCB.  The carrier
handles PoE power extraction and 12 V fan outputs; the Waveshare module integrates the
**ESP32-P4NRW32** SoC, **LAN8720A** Ethernet PHY (RMII), **CH343P** USB-UART bridge,
USB-C connector, and 32 MB flash + 32 MB PSRAM.  Provides wired Ethernet for reliable
data-centre and server-room deployments.

## Key components

| Ref | Part | Function |
|-----|------|----------|
| —   | Waveshare ESP32-P4-ETH (SKU 32086) | MCU module — ESP32-P4NRW32 dual-core RISC-V 400 MHz, LAN8720A PHY, CH343P USB bridge, 32 MB flash, 32 MB PSRAM |
| J8  | Sullins PREC020DAAN-RC / Würth 61304021821 | 2×20 HAT header — carrier PCB ↔ Waveshare module |
| U1  | Ag9905M (Silvertel) | PoE+ PD module — 802.3at Class 4, 12 V isolated output |
| U2  | LM2596S-5.0/NOPB (TI) | Buck regulator — 12 V → 5 V, 3 A |
| D2  | 1N5822 | USB back-feed protection Schottky — prevents back-feeding PC USB host when Waveshare is programmed via USB-C while PoE is live |
| J1  | Würth 615008144521 | Shielded RJ45 — PoE **power** input only; MDI secondary NC |

## Features

- 4 × 12 V PWM fan channels (25 kHz), GPIO4–7
- 4 × tachometer inputs (IRAM_ATTR ISR), GPIO8–11
- NTC thermistor ADC (GPIO16, 12-bit)
- HTTP OTA firmware update via POST `/api/v1/ota`
- Wired Ethernet via Waveshare's built-in LAN8720A (ETH.begin() / RMII)
- PoE 802.3at Class 4 power budget: ~18.9 W consumed; ~1.1 W margin against 20 W cap
- Programming and debug via Waveshare's USB-C connector (CH343P USB-UART bridge)

## Power supply

```
J1 RJ45 (PoE power only, MDI secondary NC)
  → U1 Ag9905M → +12 V
    → J2–J5  fan headers (12 V)
    → U2 LM2596S-5.0 → +5 V → D2 (back-feed) → +5V_HAT (~4.65 V)
      → J8 (2×20 HAT header) → Waveshare ESP32-P4-ETH
        → (internal Waveshare 3.3 V LDO) → +3V3 via J8 → TACH pull-ups, NTC divider
```

> **PSE note:** The PoE switch port connected to J1 must be set to **"force PoE"** mode
> (power regardless of link state), because J1's MDI secondary is NC and no 802.3 Ethernet
> link is visible on that port.  Ethernet data connectivity is provided by the Waveshare
> board's own built-in RJ45 on a separate cable.