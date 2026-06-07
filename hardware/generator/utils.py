"""
Shared utilities, constants, and the .kicad_pro writer.

Extracted from hardware/generate_project.py (pure mechanical refactor — no logic changes).
"""

import json
import os
import itertools

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_uid_seq = itertools.count(1)


def _uuid():
    n = next(_uid_seq)
    return f"{n:08x}-{n:04x}-{n:04x}-{n:04x}-{n:012x}"


G  = 2.54   # grid unit (mm)
PL = 2.54   # pin length (mm)

# KiCad 10 footprint library base path.
# Override via KICAD_FP_BASE environment variable for CI / non-Windows systems.
# Linux default (KiCad installed via apt): /usr/share/kicad/footprints
KICAD_FP_BASE = os.environ.get(
    "KICAD_FP_BASE",
    r"C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints",
)


def snap(v):
    """Snap value to nearest 1.27 mm."""
    return round(round(v / 1.27) * 1.27, 6)


def _pt(x, y):
    return f"{snap(x):.4f} {snap(y):.4f}"


# hardware/ directory — two levels up from this file (hardware/generator/utils.py)
_HARDWARE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR  = os.path.join(_HARDWARE_DIR, "kicad")
PROJ     = "PoE-FanController"
SCH_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


# ---------------------------------------------------------------------------
# .kicad_pro
# ---------------------------------------------------------------------------
def write_pro():
    pro = {
        "boards": [], "cvpcb": {"equivalence_files": []},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": f"{PROJ}.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [{"clearance": 0.2, "name": "Default", "track_width": 0.25,
                         "via_diameter": 0.8, "via_drill": 0.4}],
            "meta": {"version": 3}, "net_colors": {}, "netclass_assignments": {},
            "netclass_patterns": []},
        "schematic": {"annotate_start_num": 0, "bom_fmt_presets": [], "bom_presets": [],
                      "drawing": {"default_wire_thickness": 6, "default_text_size": 50},
                      "legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [], "text_variables": {}
    }
    p = os.path.join(OUT_DIR, f"{PROJ}.kicad_pro")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(pro, f, indent=2)
    print(f"  wrote {p}")
