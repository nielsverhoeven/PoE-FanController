# PoE-FanController

A PoE 802.3at (25.5 W) powered quad-fan controller using the **ESP32-P4** MCU with onboard
**LAN8720A** Ethernet PHY (RMII). Replaces WiFi with wired Ethernet for reliable data-centre
and server-room deployments.

## Key components

| Ref | Part | Function |
|-----|------|----------|
| U3  | ESP32-P4-MINI-1U-N16R8 | Main MCU — dual-core RISC-V 400 MHz, 16 MB flash, 8 MB PSRAM |
| U5  | LAN8720A-CP-TR | Ethernet PHY — 10/100BASE-T, RMII, QFN-24 |
| U1  | Ag9905M | PoE+ PD module — 802.3at Class 4, 12 V isolated output |
| U2  | LM2596-3.3 | Buck regulator — 12 V → 3.3 V, 3 A |
| J1  | Würth 615008144521 | Shielded RJ45 with integrated magnetics |

## Features

- 4 × 12 V PWM fan channels (25 kHz), GPIO4–7
- 4 × tachometer inputs (IRAM_ATTR ISR), GPIO8–11
- NTC thermistor ADC (GPIO16, 12-bit)
- HTTP OTA firmware update via POST `/api/v1/ota`
- Wired Ethernet (ETH.begin() / RMII fixed pins GPIO32–37 + GPIO50)
- PoE 802.3at power budget: 12.95 W available after conversion losses