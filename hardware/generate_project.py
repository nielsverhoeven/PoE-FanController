#!/usr/bin/env python3
"""Entry point: regenerate KiCad schematic and BOM from source.

Implementation lives in hardware/generator/ (split into focused modules).
This file is intentionally thin (<=30 lines of logic).

P-KI-07: This script does NOT write hardware/kicad/PoE-FanController.kicad_pcb.
         The PCB file is maintained exclusively via the KiCad GUI.
"""

import sys
import os
from pathlib import Path

# Allow running as: python generate_project.py from hardware/ dir
sys.path.insert(0, str(Path(__file__).parent))

from generator.utils import write_pro, OUT_DIR, PROJ  # noqa: E402
from generator import build_schematic, write_bom       # noqa: E402

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    print("Project file...")
    write_pro()

    print("Building schematic...")
    sch = build_schematic()
    sp = os.path.join(OUT_DIR, f"{PROJ}.kicad_sch")
    with open(sp, "w", encoding="utf-8") as f:
        f.write(sch.render())
    print(f"  wrote {sp}")

    print("BOM...")
    write_bom()

    print("Done.")
