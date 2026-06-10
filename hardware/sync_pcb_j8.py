"""
T004: Sync PCB netlist from corrected schematic for J8 pad net assignments.

Changes from issue #148 pin corrections:
  Pad  2: was +5V (VBUS duplicate)     → now unconnected (NC, GPIO24/USB D-)
  Pad  4: was +5V (VBUS duplicate)     → now unconnected (NC, GPIO7/SDA)
  Pad 20: was GND                       → now unconnected (NC, GPIO54)
  Pad 25: was GND                       → now unconnected (NC, GPIO33/EMAC_RXD1 FORBIDDEN)
  Pad 26: was GND                       → now unconnected (NC, GPIO32/EMAC_RXD0 FORBIDDEN)
  Pad 30: was GND                       → now unconnected (NC, RUN reserved)
  Pad 33: was FAN2_PWM                  → now GND (physical GND pad)
  Pad 34: was GND                       → now FAN2_PWM (GPIO21)

Also updates footprint name from PinSocket_2x20_P2.54mm_P15.38mm_Vertical
to ESP32-P4-PoE-ETH-PinSocket.
"""

import sys
import os

# KiCad Python is at this path
KICAD_PYTHON = r"C:\Users\Niels\AppData\Local\Programs\KiCad\10.0\bin\python.exe"

import pcbnew

PCB_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__),
                            "kicad", "PoE-FanController.kicad_pcb"))

print(f"Loading PCB: {PCB_PATH}")
board = pcbnew.LoadBoard(PCB_PATH)

# Pad changes:
#   NC pads → empty net (unconnected)
NC_PADS = {"2", "4", "20", "25", "26", "30"}
# Reassigned signal pads:
# pad 33: was FAN2_PWM → GND
# pad 34: was GND → FAN2_PWM
REASSIGN = {
    "33": "GND",
    "34": "FAN2_PWM",
}

# Build a net name → NETINFO_ITEM lookup from the board
net_gnd = board.FindNet("GND")
net_fan2pwm = board.FindNet("FAN2_PWM")
net_empty = board.GetNetInfo().GetNetItem("")  # empty/unconnected net

print(f"GND net code: {net_gnd.GetNetCode() if net_gnd else 'NOT FOUND'}")
print(f"FAN2_PWM net code: {net_fan2pwm.GetNetCode() if net_fan2pwm else 'NOT FOUND'}")

if net_gnd is None:
    print("ERROR: GND net not found in PCB!")
    sys.exit(1)
if net_fan2pwm is None:
    print("ERROR: FAN2_PWM net not found in PCB!")
    sys.exit(1)

j8_fp = None
for fp in board.GetFootprints():
    if fp.GetReference() == "J8":
        j8_fp = fp
        break

if j8_fp is None:
    print("ERROR: J8 footprint not found in PCB!")
    sys.exit(1)

print(f"Found J8 footprint: {j8_fp.GetFPIDAsString()}")
print(f"  Current footprint value: {j8_fp.GetValue()}")

# Update footprint name if it still has the old name
old_fpid = j8_fp.GetFPIDAsString()
if "PinSocket_2x20" in old_fpid:
    new_lib_id = pcbnew.LIB_ID("Custom", "ESP32-P4-PoE-ETH-PinSocket")
    j8_fp.SetFPID(new_lib_id)
    print(f"  Updated footprint ID: {old_fpid} → {j8_fp.GetFPIDAsString()}")
else:
    print(f"  Footprint ID already correct: {old_fpid}")

# Update pad net assignments
changes = []
for pad in j8_fp.Pads():
    pnum = pad.GetNumber()
    current_net = pad.GetNetname()

    if pnum in NC_PADS:
        if current_net != "":
            pad.SetNet(board.GetNetInfo().GetNetItem(""))
            changes.append(f"  Pad {pnum}: {current_net} → (unconnected)")
    elif pnum in REASSIGN:
        target_net_name = REASSIGN[pnum]
        target_net = board.FindNet(target_net_name)
        if target_net is None:
            print(f"ERROR: Target net '{target_net_name}' for pad {pnum} not found!")
            sys.exit(1)
        if current_net != target_net_name:
            pad.SetNet(target_net)
            changes.append(f"  Pad {pnum}: {current_net} → {target_net_name}")

if changes:
    print("Net assignment changes:")
    for c in changes:
        print(c)
else:
    print("No net changes needed (already correct).")

print(f"\nSaving PCB to: {PCB_PATH}")
pcbnew.SaveBoard(PCB_PATH, board)
print("Done.")
