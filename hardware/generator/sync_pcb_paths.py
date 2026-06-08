"""
sync_pcb_paths.py — Set PCB footprint paths from schematic component UUIDs.

KiCad's "Update PCB from Schematic" (F8) matches schematic symbols to PCB
footprints via the footprint's 'path' attribute (/{symbol_uuid}).  When
footprints are placed programmatically (via pcbnew API) without a path,
KiCad treats them as new/unplaced components and prompts the user to place
them manually.

This script:
  1. Parses the schematic to extract {reference: uuid} for every real component.
  2. Matches each PCB footprint by reference designator.
  3. Sets the footprint path to /{uuid} so F8 recognises it as already-placed.

After running this script, "Update PCB from Schematic (F8)" will:
  - Update existing footprint net/value data in-place (no placement prompt).
  - Only prompt for NEW schematic components not yet in the PCB.

Usage:
    python hardware/generator/sync_pcb_paths.py

Part of issue #77 fix.
"""

import sys, re

sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

SCH = 'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_sch'
PCB = 'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb'


def extract_schematic_uuids(sch_path: str) -> dict[str, str]:
    """Return {reference: uuid} for every non-power component in the schematic."""
    with open(sch_path, 'r', encoding='utf-8') as f:
        text = f.read()

    results = {}
    # Match component symbol blocks (skip power: symbols)
    for m in re.finditer(r'\(symbol \(lib_id "(?!power:)([^"]+)"\)', text):
        start = m.start()
        depth, i = 0, start
        while i < len(text):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        block = text[start:i + 1]
        uuid_m = re.search(r'\(uuid "([^"]+)"\)', block)
        ref_m  = re.search(r'\(property "Reference" "([^"]+)"', block)
        if uuid_m and ref_m:
            results[ref_m.group(1)] = uuid_m.group(1)
    return results


def sync_paths(sch_path: str = SCH, pcb_path: str = PCB) -> None:
    print("Extracting schematic UUIDs …")
    ref_to_uuid = extract_schematic_uuids(sch_path)
    for ref, uuid in sorted(ref_to_uuid.items()):
        print(f"  {ref:12} -> {uuid}")

    print(f"\nLoading PCB: {pcb_path}")
    board = pcbnew.LoadBoard(pcb_path)

    matched   = []
    unmatched = []

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in ref_to_uuid:
            uuid = ref_to_uuid[ref]
            path = pcbnew.KIID_PATH()
            path.push_back(pcbnew.KIID(uuid))
            fp.SetPath(path)
            matched.append(ref)
        else:
            unmatched.append(ref)

    print(f"\nPaths set:   {len(matched)}  ({', '.join(sorted(matched))})")
    if unmatched:
        print(f"No UUID found: {', '.join(sorted(unmatched))}  (not in schematic?)")

    board.BuildConnectivity()
    board.Save(pcb_path)
    print(f"\nSaved: {pcb_path}")

    # Verify
    board2 = pcbnew.LoadBoard(pcb_path)
    print("\nVerification:")
    for fp in board2.GetFootprints():
        path_str = fp.GetPath().AsString()
        status = "✓" if path_str else "✗ EMPTY"
        print(f"  {fp.GetReference():12} path={path_str!r}  {status}")


if __name__ == '__main__':
    sync_paths()
