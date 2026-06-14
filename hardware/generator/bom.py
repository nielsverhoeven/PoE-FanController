"""
generator.bom — write_bom() for PoE FanController v0.6 (daughter board for SKU 32088).

Writes hardware/bom/bom.csv with all components for the daughter board.

The Waveshare ESP32-P4-POE-ETH (SKU 32088) main board is purchased separately and
not listed here. It provides PoE PD, Ethernet PHY, RJ45, ESP32-P4, USB-C, and the
2×20 male header that mates with J8 on this daughter board.

Power chain: J8 pin 40 (+5V from Waveshare VBUS) → U_BOOST (LM2587 DC-DC boost module, 5A, 92%) → fans J2–J5.
"""

import csv
import os

from .utils import HW_DIR


def write_bom():
    """Write the bill of materials to hardware/bom/bom.csv."""
    rows = [
        ["Reference","Value","Footprint","Qty","Manufacturer","MPN","Description","Datasheet"],
        # Waveshare ESP32-P4-POE-ETH Interface (2×20 female PinSocket)
        ["J8","Waveshare_HAT","Custom:ESP32-P4-PoE-ETH-PinSocket","1","Sullins","PPPC202LFBN-RC","2×20 2.54mm female THT pin socket — daughter board ↔ Waveshare ESP32-P4-POE-ETH (SKU 32088) interface","https://www.waveshare.com/wiki/ESP32-P4-POE-ETH"],
        # 5V→12V Boost Module (replaces discrete U1/L1/D1/C1/C2 boost stage)
        ["U_BOOST","DC-Boost-Module","Custom:DC-Boost-Module","1","Amazon.nl","B07RKDB2VP","DC-DC step-up boost converter module (LM2587), 5V→12V, 5A max, 92% efficiency — powers fan +12V rail. 4-pin 2.54mm THT daughter board header.","https://www.ti.com/lit/ds/symlink/lm2587.pdf"],
        # Fan Headers
        ["J2,J3,J4,J5","Fan_Header","Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical","4","Molex","47053-1000","4-pin 2.54mm 12V PWM fan header","~"],
        ["R5,R6,R7,R8","10k","Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal","4","Yageo","MFR-25FBF52-10K0","10kΩ 1/4W 1% axial THT — fan TACH pull-up resistors (3.3V from J8)","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-MFR_51.pdf"],
        # Per-fan Power Indicator LEDs (passive: +12V → R → LED → GND)
        ["R9,R10,R11,R12","1k","Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal","4","Yageo","MFR-25FBF52-1K00","1kΩ 1/4W 1% axial THT — per-fan LED current limiting resistors","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-MFR_51.pdf"],
        ["D2,D3,D4,D5","LED_GREEN","LED_THT:LED_D3.0mm","4","Wurth","150060GS75000","Green 3mm THT LED, 565nm — per-fan power indicator (lights when +12V on fan header)","https://www.we-online.com/en/components/products/LED/THROUGH_HOLE_LED/150060GS75000"],
        # Temperature + Humidity Sensing (DHT11 breakout — replaces NTC1 + R4, issue #135)
        ["HUM1","DHT11_Breakout","Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical","1","Aosong","DHT11","DHT11 temperature+humidity breakout, 3-pin 3.3V single-wire — J8 pin 23 (GPIO16)","https://www.adafruit.com/product/386"],
        # Status LED (GPIO-driven)
        ["R3","330R","Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal","1","Yageo","MFR-25FBF52-330R","330Ω 1/4W 1% axial THT — status LED current limit","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-MFR_51.pdf"],
        ["LED1","LED_GREEN","LED_THT:LED_D3.0mm","1","Wurth","150060GS75000","Green 3mm THT LED, 565nm — GPIO status indicator","https://www.we-online.com/en/components/products/LED/THROUGH_HOLE_LED/150060GS75000"],
        # Prog / OTA LED (GPIO15-driven, flickers during firmware write)
        ["R13","330R","Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal","1","Yageo","MFR-25FBF52-330R","330Ω 1/4W 1% axial THT — prog LED current limit","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-MFR_51.pdf"],
        ["LED2","LED_ORANGE","LED_THT:LED_D3.0mm","1","Wurth","150060AS75000","Orange 3mm THT LED, 605nm — firmware-write / OTA activity indicator","https://www.we-online.com/en/components/products/LED/THROUGH_HOLE_LED/150060AS75000"],
    ]
    p = os.path.join(HW_DIR, "bom", "bom.csv")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"  wrote {p}")
