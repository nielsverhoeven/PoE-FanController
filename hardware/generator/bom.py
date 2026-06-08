"""
generator.bom — write_bom() for PoE FanController v0.4 (daughter board for SKU 32088).

Writes hardware/bom/bom.csv with all components for the daughter board.

The Waveshare ESP32-P4-POE-ETH (SKU 32088) main board is purchased separately and
not listed here. It provides PoE PD, Ethernet PHY, RJ45, ESP32-P4, USB-C, and the
2×20 male header that mates with J8 on this daughter board.

Power chain: J8 pins 2,4 (+5V from Waveshare) → U_BOOST (5V→12V) → fans J2–J5.
"""

import csv
import os

from .utils import HW_DIR


def write_bom():
    """Write the bill of materials to hardware/bom/bom.csv."""
    rows = [
        ["Reference","Value","Footprint","Qty","Manufacturer","MPN","Description","Datasheet"],
        # Waveshare ESP32-P4-POE-ETH Interface (2×20 female PinSocket)
        ["J8","Waveshare_HAT","Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical","1","Sullins","PPPC202LFBN-RC","2×20 2.54mm female THT pin socket — daughter board ↔ Waveshare ESP32-P4-POE-ETH (SKU 32088) interface","https://www.waveshare.com/wiki/ESP32-P4-POE-ETH"],
        # 5V→12V Boost Converter
        ["U_BOOST","LM2587-12","Package_TO_SOT_THT:TO-220-3_Vertical","1","TI","LM2587T-12/NOPB","5V→12V fixed boost converter, TO-220-5, 1.5A — powers fan headers J2–J5","https://www.ti.com/lit/ds/symlink/lm2587.pdf"],
        # Fan Headers
        ["J2,J3,J4,J5","Fan_Header","Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical","4","Molex","47053-1000","4-pin 2.54mm 12V PWM fan header","~"],
        ["R5,R6,R7,R8","10k","Resistor_SMD:R_0402_1005Metric","4","Yageo","RC0402FR-0710KL","10kΩ 0402 1% — fan TACH pull-up resistors (3.3V from J8)","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf"],
        # Temperature Sensing
        ["R4","10k","Resistor_SMD:R_0402_1005Metric","1","Yageo","RC0402FR-0710KL","10kΩ 0402 1% — NTC divider pull-up (3.3V from J8)","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf"],
        ["NTC1","NTC10K_B3950","Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal","1","Murata","NCP15XH103F03RC","10kΩ NTC thermistor B=3380, axial THT","https://www.murata.com/en-us/products/productdetail?partid=NCP15XH103F03RC"],
        # Status LED
        ["R3","330R","Resistor_SMD:R_0402_1005Metric","1","Yageo","RC0402FR-07330RL","330Ω 0402 1% — status LED current limit","https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf"],
        ["LED1","LED_GREEN","LED_THT:LED_D3.0mm","1","Wurth","150060GS75000","Green 3mm THT LED, 565nm","https://www.we-online.com/en/components/products/LED/THROUGH_HOLE_LED/150060GS75000"],
    ]
    p = os.path.join(HW_DIR, "bom", "bom.csv")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"  wrote {p}")
