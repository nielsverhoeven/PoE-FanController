"""
PCB cleanup script -- ESP32-P4-ETH carrier board transition.

Removes orphaned footprints from the pre-Waveshare ESP32-P4-MINI-1U design
and adds J8 (2x20 2.54mm pin header) for the ESP32-P4-ETH GPIO interface.

Run with KiCad bundled Python:
  kicad-python hardware/pcb_cleanup.py

P-KI-07 exception: surgical footprint management via pcbnew API only.
Does not touch traces, zones, or net topology.
"""

import pcbnew, sys, os

PCB_PATH = os.path.join(os.path.dirname(__file__),
                        "kicad", "PoE-FanController.kicad_pcb")

CONNECTOR_LIB = (r"C:/Users/Niels/AppData/Local/Programs/KiCad/10.0"
                 r"/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty")

# Components removed from schematic — orphaned on PCB
TO_REMOVE = ["U3", "U4", "U5", "J6", "SW1", "SW2",
             "R9", "R10", "R11", "R12", "R13", "R14",
             "C8", "C9", "C10", "C11"]

# J8: 2×20 2.54mm vertical pin header — interface to Waveshare ESP32-P4-ETH
J8_FOOTPRINT = "PinHeader_2x20_P2.54mm_Vertical"
# Place at ~(65, 40) mm — secondary side (x>38mm), clear of fan headers and PoE
J8_X_MM = 65.0
J8_Y_MM = 40.0


def main():
    print(f"Loading PCB: {PCB_PATH}")
    board = pcbnew.LoadBoard(PCB_PATH)

    # ── Remove orphaned footprints ──────────────────────────────────────────
    removed = []
    not_found = []
    for ref in TO_REMOVE:
        fp = board.FindFootprintByReference(ref)
        if fp:
            board.Delete(fp)
            removed.append(ref)
        else:
            not_found.append(ref)

    print(f"Removed  ({len(removed)}): {', '.join(removed)}")
    if not_found:
        print(f"Not found (already gone): {', '.join(not_found)}")

    # ── Add J8 ─────────────────────────────────────────────────────────────
    fp_path = os.path.join(CONNECTOR_LIB, f"{J8_FOOTPRINT}.kicad_mod")
    if not os.path.exists(fp_path):
        print(f"ERROR: footprint file not found: {fp_path}", file=sys.stderr)
        sys.exit(1)

    j8 = pcbnew.FootprintLoad(CONNECTOR_LIB, J8_FOOTPRINT)
    if j8 is None:
        print("ERROR: FootprintLoad returned None", file=sys.stderr)
        sys.exit(1)

    j8.SetReference("J8")
    j8.SetValue("ESP32-P4-ETH_Header")
    j8.SetPosition(pcbnew.VECTOR2I(
        pcbnew.FromMM(J8_X_MM),
        pcbnew.FromMM(J8_Y_MM)
    ))
    # Place on F.Cu (top layer, P-HW-02)
    j8.SetLayer(pcbnew.F_Cu)

    board.Add(j8)
    print(f"Added J8 ({J8_FOOTPRINT}) at ({J8_X_MM}, {J8_Y_MM}) mm on F.Cu")

    # ── Refresh ratsnest & save ─────────────────────────────────────────────
    board.BuildConnectivity()
    pcbnew.Refresh()
    board.Save(PCB_PATH)
    print(f"Saved: {PCB_PATH}")
    print("Done. Open in KiCad GUI to:")
    print("  1. Fine-tune J8 position and orientation")
    print("  2. Route connections from J8 to power/signal pads")
    print("  3. Run Zone Refill")


if __name__ == "__main__":
    main()
