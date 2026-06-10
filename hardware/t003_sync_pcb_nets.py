"""
T003: Sync PCB J8 pad net assignments and clear all stale tracks.

Issue #148 — correct GPIO pin assignments for J8 (ESP32-P4-POE-ETH right column).
After the schematic generator was updated (T001) and ERC verified (T002), this script:
  1. Clears ALL existing tracks and vias (they are invalid for the new pin assignments)
  2. Reassigns J8 pad nets to match the corrected schematic netlist
  3. Ensures all required nets exist in the board
  4. Rebuilds connectivity
  5. Saves the PCB file

Usage:
    C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin/python.exe hardware/t003_sync_pcb_nets.py
"""

import sys
sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

PCB = r'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb'

# Net assignments for J8 pads — corrected (issue #148, architecture validation v4.2.0)
# Pad number string -> net name ("" = NC/unconnected)
J8_NETS = {
    # Left column: pins 1-20
    "1":  "",             # NC (GPIO25)
    "2":  "+5V",          # VBUS duplicate
    "3":  "GND",          # Physical GND
    "4":  "+5V",          # VBUS duplicate
    "5":  "",             # NC
    "6":  "STATUS_LED",   # GPIO2 — status LED
    "7":  "",             # NC
    "8":  "GND",          # Physical GND
    "9":  "",             # NC
    "10": "",             # NC
    "11": "",             # NC
    "12": "",             # NC
    "13": "GND",          # Physical GND
    "14": "PROG_LED",     # GPIO15 — OTA/write LED
    "15": "DHT11_DATA",   # GPIO16 — DHT11 single-wire
    "16": "",             # NC
    "17": "",             # NC
    "18": "GND",          # Physical GND
    "19": "DS18B20_DATA", # GPIO19 — 1-Wire data
    "20": "GND",          # Physical GND
    # Right column: pins 21-40
    "21": "PROBE_LED",    # GPIO48 — probe health LED
    "22": "FAN4_TACH",    # GPIO47 — FAN4 tach IRQ
    "23": "GND",          # Physical GND
    "24": "FAN3_TACH",    # GPIO46 — FAN3 tach IRQ
    "25": "GND",          # Physical GND
    "26": "GND",          # Physical GND
    "27": "FAN4_PWM",     # GPIO27 — FAN4 LEDC CH3
    "28": "GND",          # Physical GND
    "29": "FAN3_PWM",     # GPIO26 — FAN3 LEDC CH2
    "30": "GND",          # Physical GND
    "31": "FAN2_TACH",    # GPIO23 — FAN2 tach IRQ
    "32": "FAN1_TACH",    # GPIO22 — FAN1 tach IRQ
    "33": "FAN2_PWM",     # GPIO21 — FAN2 LEDC CH1
    "34": "GND",          # Physical GND
    "35": "FAN1_PWM",     # GPIO20 — FAN1 LEDC CH0
    "36": "+3V3",         # +3V3 from Waveshare LDO — SOLE source (issue #148)
    "37": "",             # NC (EN/chip-enable — RESERVED)
    "38": "GND",          # Physical GND
    "39": "",             # NC (VSYS — do NOT use as 5V source)
    "40": "+5V",          # VBUS — 5V power source
}

def main():
    print(f"Loading PCB: {PCB}")
    board = pcbnew.LoadBoard(PCB)
    netinfo = board.GetNetInfo()

    # ---------------------------------------------------------------
    # Step 1: Delete ALL tracks and vias
    # ---------------------------------------------------------------
    tracks = list(board.GetTracks())
    print(f"\nStep 1: Removing {len(tracks)} tracks/vias...")
    for track in tracks:
        board.Remove(track)
    print(f"  Done. Tracks remaining: {len(list(board.GetTracks()))}")

    # ---------------------------------------------------------------
    # Step 2: Ensure all required nets exist in the board
    # ---------------------------------------------------------------
    required_nets = sorted(set(n for n in J8_NETS.values() if n))
    print(f"\nStep 2: Ensuring nets exist: {required_nets}")
    for net_name in required_nets:
        existing = netinfo.GetNetItem(net_name)
        if existing is None or existing.GetNetCode() == 0:
            new_net = pcbnew.NETINFO_ITEM(board, net_name)
            board.Add(new_net)
            print(f"  Created net: {net_name}")
        else:
            print(f"  Exists:      {net_name} (code {existing.GetNetCode()})")

    # Refresh netinfo after adding nets
    board.BuildConnectivity()
    netinfo = board.GetNetInfo()

    # ---------------------------------------------------------------
    # Step 3: Find J8 footprint and assign pad nets
    # ---------------------------------------------------------------
    j8 = None
    for fp in board.GetFootprints():
        if fp.GetReference() == "J8":
            j8 = fp
            break

    if j8 is None:
        print("\nERROR: J8 footprint not found in PCB!")
        sys.exit(1)

    print(f"\nStep 3: Assigning J8 pad nets ({len(list(j8.Pads()))} pads)...")
    assigned = 0
    nc_count = 0
    for pad in j8.Pads():
        pad_num = pad.GetNumber()
        net_name = J8_NETS.get(pad_num, "")
        if net_name:
            net = netinfo.GetNetItem(net_name)
            if net and net.GetNetCode() != 0:
                pad.SetNet(net)
                print(f"  J8 pad {pad_num:>3} -> {net_name}")
                assigned += 1
            else:
                print(f"  WARNING: Net '{net_name}' not found for pad {pad_num}")
        else:
            # NC pad: set to unconnected (netcode 0)
            pad.SetNetCode(0)
            print(f"  J8 pad {pad_num:>3} -> (NC)")
            nc_count += 1

    print(f"\n  Assigned: {assigned} pads with nets")
    print(f"  NC:       {nc_count} pads")

    # ---------------------------------------------------------------
    # Step 4: Rebuild connectivity and save
    # ---------------------------------------------------------------
    print("\nStep 4: Rebuilding connectivity...")
    board.BuildConnectivity()

    print(f"Saving PCB: {PCB}")
    board.Save(PCB)
    print("Done.")

    # ---------------------------------------------------------------
    # Step 5: Verification — reload and check
    # ---------------------------------------------------------------
    print("\nVerification (reloading PCB)...")
    board2 = pcbnew.LoadBoard(PCB)
    j8_v = None
    for fp in board2.GetFootprints():
        if fp.GetReference() == "J8":
            j8_v = fp
            break
    if j8_v:
        print("J8 pad assignments after save:")
        for pad in sorted(j8_v.Pads(), key=lambda p: int(p.GetNumber())):
            net = pad.GetNet()
            net_name = net.GetNetname() if net else "(no net)"
            print(f"  J8 pad {pad.GetNumber():>3}: {net_name}")
    
    track_count = len(list(board2.GetTracks()))
    print(f"\nTrack count after save: {track_count}")


if __name__ == "__main__":
    main()
