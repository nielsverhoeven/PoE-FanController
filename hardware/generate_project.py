#!/usr/bin/env python3
"""Entry point: regenerate KiCad schematic and BOM. Does NOT touch .kicad_pcb (P-KI-07)."""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from generator.utils import write_pro, OUT_DIR, PROJ
from generator import build_schematic, write_bom

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    write_pro()
    sch = build_schematic()
    with open(os.path.join(OUT_DIR, f"{PROJ}.kicad_sch"), "w", encoding="utf-8") as f:
        f.write(sch.render())
    write_bom()
    print("Done.")
