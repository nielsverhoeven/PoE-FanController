"""
PCB footprint embedding utilities.

embed_footprint() reads a .kicad_mod file from the KiCad library and transforms
it into an inline footprint entry suitable for use in a .kicad_pcb file.

NOTE (P-KI-07): The .kicad_pcb file is KiCad GUI territory.  These utilities
are provided for reference / future tooling only.  The generate_project.py
entry point does NOT call write_pcb() — that function has been removed.

Extracted from hardware/generate_project.py (pure mechanical refactor — no logic changes).
"""

import os
import re
from .utils import KICAD_FP_BASE, _uuid

# Base path for any custom footprints stored in the project repository.
CUSTOM_FP_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "kicad", "footprints",
)


# ---------------------------------------------------------------------------
# Footprint embedding helper — reads .kicad_mod and transforms it for PCB
# ---------------------------------------------------------------------------
def embed_footprint(lib_name, fp_name, ref, value, cx, cy, rot=0.0):
    """Read a footprint from the KiCad library and return it as a PCB footprint entry.

    Transforms the .kicad_mod format into the inline footprint format used by
    .kicad_pcb files: adds (at cx cy rot), (uuid ...), and updates Reference/Value.
    """
    fp_file = os.path.join(KICAD_FP_BASE, lib_name + ".pretty", fp_name + ".kicad_mod")
    content = open(fp_file, encoding="utf-8").read()

    uid = _uuid()
    rot_str = f" {rot:.1f}" if rot != 0.0 else ""

    # Transform the footprint header.
    # .kicad_mod starts with: (footprint "Name" (version N)(generator "X")(generator_version "Y")(layer "F.Cu") ...
    # .kicad_pcb needs:       (footprint "Lib:Name" (layer "F.Cu") (uuid "...") (at cx cy rot) ...
    # The regex handles the header regardless of whitespace/newlines between elements.
    transformed = re.sub(
        r'\(footprint\s+"[^"]+"\s*'
        r'(?:\(version\s+\d+\)\s*)?'
        r'(?:\(generator\s+"[^"]*"\)\s*)?'
        r'(?:\(generator_version\s+"[^"]*"\)\s*)?'
        r'\(layer\s+"F\.Cu"\)',
        f'(footprint "{lib_name}:{fp_name}" (layer "F.Cu") (uuid "{uid}") (at {cx:.3f} {cy:.3f}{rot_str})',
        content,
        count=1,
        flags=re.DOTALL,
    )

    # Update Reference and Value properties to actual designator and value.
    transformed = re.sub(
        r'(\(property\s+"Reference"\s+)"[^"]*"',
        rf'\g<1>"{ref}"',
        transformed,
        count=1,
    )
    transformed = re.sub(
        r'(\(property\s+"Value"\s+)"[^"]*"',
        rf'\g<1>"{value}"',
        transformed,
        count=1,
    )

    # Indent the footprint body by 2 spaces for readability in the PCB file.
    lines = transformed.splitlines()
    return "\n".join("  " + l if l.strip() else l for l in lines)


def embed_custom_footprint(fp_name, ref, value, cx, cy, rot=0.0):
    """Embed a footprint from the project-local custom footprint library.

    Custom footprints are stored under hardware/kicad/footprints/<fp_name>.kicad_mod.
    Uses CUSTOM_FP_BASE as the library root.
    """
    fp_file = os.path.join(CUSTOM_FP_BASE, fp_name + ".kicad_mod")
    content = open(fp_file, encoding="utf-8").read()

    uid = _uuid()
    rot_str = f" {rot:.1f}" if rot != 0.0 else ""

    transformed = re.sub(
        r'\(footprint\s+"[^"]+"\s*'
        r'(?:\(version\s+\d+\)\s*)?'
        r'(?:\(generator\s+"[^"]*"\)\s*)?'
        r'(?:\(generator_version\s+"[^"]*"\)\s*)?'
        r'\(layer\s+"F\.Cu"\)',
        f'(footprint "Custom:{fp_name}" (layer "F.Cu") (uuid "{uid}") (at {cx:.3f} {cy:.3f}{rot_str})',
        content,
        count=1,
        flags=re.DOTALL,
    )

    transformed = re.sub(
        r'(\(property\s+"Reference"\s+)"[^"]*"',
        rf'\g<1>"{ref}"',
        transformed,
        count=1,
    )
    transformed = re.sub(
        r'(\(property\s+"Value"\s+)"[^"]*"',
        rf'\g<1>"{value}"',
        transformed,
        count=1,
    )

    lines = transformed.splitlines()
    return "\n".join("  " + l if l.strip() else l for l in lines)
