"""
import_netlist.py — Import net assignments from exported schematic netlist into KiCad PCB.
Equivalent to KiCad GUI "Tools > Update PCB from Schematic (F8)" net assignment step.

Handles both signal nets (from kicad-cli netlist export) and power nets
(GND, +5V, +12V, +3V3) which are not always exported due to annotation quirks.

Usage: python import_netlist.py
"""
import sys, re

sys.path.insert(0, r'C:/Users/Niels/AppData/Local/Programs/KiCad/10.0/bin')
import pcbnew

PCB     = 'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_pcb'
NETLIST = 'C:/repos-github/PoE-FanController/hardware/kicad/netlist.kicad_net'

# ── Power net assignments (sourced directly from components.py schematic def) ──
# NC pins on J8: 5,18,19,21,22,24,26,27,28,30,31,32,34,35,36,37,39,40 — left with no net
POWER_NETS = {
    # J8 — Waveshare ESP32-P4-POE-ETH header
    ('J8', '1'):  '+3V3',  # 3.3V from Waveshare LDO
    ('J8', '2'):  '+5V',   # +5V from Waveshare PoE PD
    ('J8', '4'):  '+5V',   # +5V duplicate
    ('J8', '6'):  'GND',
    ('J8', '9'):  'GND',
    ('J8', '14'): 'GND',
    ('J8', '17'): '+3V3',  # 3.3V duplicate
    ('J8', '20'): 'GND',
    ('J8', '25'): 'GND',
    ('J8', '29'): 'GND',
    ('J8', '33'): 'GND',
    ('J8', '38'): 'GND',
    # Fan headers J2-J5
    ('J2', '1'): 'GND',    ('J2', '2'): '+12V',
    ('J3', '1'): 'GND',    ('J3', '2'): '+12V',
    ('J4', '1'): 'GND',    ('J4', '2'): '+12V',
    ('J5', '1'): 'GND',    ('J5', '2'): '+12V',
    # TACH pull-up resistors R5-R8: left pin → +3V3
    ('R5', '1'): '+3V3',
    ('R6', '1'): '+3V3',
    ('R7', '1'): '+3V3',
    ('R8', '1'): '+3V3',
    # NTC voltage divider: R4 left pin → +3V3
    ('R4', '1'): '+3V3',
    # Status LED: LED1 cathode → GND
    ('LED1', '2'): 'GND',
    # NTC thermistor: NTC1 bottom → GND
    ('NTC1', '2'): 'GND',
    # U1: 5V→12V boost converter (TI LM2587-12, TO-220-5_Vertical)
    # Pin 1=GND, Pin 2=VIN(+5V), Pin 3=OUTPUT/SW, Pin 4=FB(tied to OUTPUT), Pin 5=OSC/GND
    ('U1', '1'): 'GND',       # GND
    ('U1', '2'): '+5V',       # VIN
    ('U1', '3'): 'BOOST_SW',  # OUTPUT / switching node
    ('U1', '4'): 'BOOST_SW',  # FB tied to OUTPUT (fixed 12V)
    ('U1', '5'): 'GND',       # OSC bypass to GND
    # L1: catch inductor — +5V → BOOST_SW
    ('L1', '1'): '+5V',
    ('L1', '2'): 'BOOST_SW',
    # D1: Schottky catch diode — BOOST_SW anode → +12V cathode
    ('D1', '1'): 'BOOST_SW',
    ('D1', '2'): '+12V',
    # C1: input bypass cap — +5V / GND
    ('C1', '1'): '+5V',
    ('C1', '2'): 'GND',
    # C2: output filter cap — +12V / GND
    ('C2', '1'): '+12V',
    ('C2', '2'): 'GND',
}

# ── Step 1: Parse netlist → {(ref, pin): net_name} ──────────────────────────

def parse_netlist(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    pad_net = {}   # {(ref, pin_number): net_name}
    net_names = {} # {net_name: set_of_(ref,pin)}

    # Locate the (nets ...) block and compact whitespace (netlist is pretty-printed)
    start = text.find('(nets')
    if start < 0:
        raise ValueError("No (nets ...) section found in netlist")
    nets_text = ' '.join(text[start:].split())  # collapse all whitespace to single spaces

    # Each net block: (net (code "N") (name "NAME") (class "...") (node (ref "R") (pin "P") ...) ...)
    net_name_re  = re.compile(r'\(name "([^"]+)"\)')
    node_re      = re.compile(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)')

    # Walk parentheses to split into individual (net ...) blocks
    # Use '(net ' (not '(nets') to distinguish net entries from wrapper
    MARKER = '(net '
    i = 0
    while i < len(nets_text):
        if nets_text[i:i+5] == MARKER:
            depth = 0
            j = i
            while j < len(nets_text):
                if nets_text[j] == '(':
                    depth += 1
                elif nets_text[j] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            block = nets_text[i:j+1]

            name_m = net_name_re.search(block)
            if name_m:
                net_name = name_m.group(1)
                for node_m in node_re.finditer(block):
                    ref = node_m.group(1)
                    pin = node_m.group(2)
                    pad_net[(ref, pin)] = net_name

            i = j + 1
        else:
            i += 1

    return pad_net

print("Parsing netlist …")
pad_net = parse_netlist(NETLIST)
print(f"  Signal nets from netlist: {len(pad_net)} pad-net entries")

# Merge power nets (not exported by kicad-cli due to annotation quirks)
overlap = {k for k in POWER_NETS if k in pad_net}
if overlap:
    print(f"  WARNING: {len(overlap)} power net entries overlap with signal nets: {overlap}")
pad_net.update(POWER_NETS)
print(f"  Total pad-net entries after merging power nets: {len(pad_net)}")

# ── Step 2: Load PCB and create/resolve nets ─────────────────────────────────

print("\nLoading PCB …")
board = pcbnew.LoadBoard(PCB)
board.BuildConnectivity()

net_info = board.GetNetInfo()

def get_or_create_net(name):
    n = board.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
    return n

# Pre-create all nets
all_nets = set(pad_net.values())
print(f"\nCreating {len(all_nets)} nets: {sorted(all_nets)}")
for net_name in all_nets:
    get_or_create_net(net_name)

# ── Step 3: Assign nets to pads ──────────────────────────────────────────────

print("\nAssigning nets to pads …")
assigned   = 0
unresolved = 0
skipped    = 0

for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        pin = pad.GetNumber()
        key = (ref, pin)
        if key in pad_net:
            net = get_or_create_net(pad_net[key])
            pad.SetNet(net)
            assigned += 1
        else:
            # Pad has no net in netlist — leave as no-connect
            skipped += 1

print(f"  Assigned: {assigned}")
print(f"  No netlist entry (unconnected/NC): {skipped}")

# ── Step 4: Rebuild connectivity and save ────────────────────────────────────

board.BuildConnectivity()
board.Save(PCB)
print(f"\nSaved PCB: {PCB}")

# ── Step 5: Verify ───────────────────────────────────────────────────────────
board2 = pcbnew.LoadBoard(PCB)
board2.BuildConnectivity()
nets2 = [str(n) for n in board2.GetNetInfo().NetsByName().keys() if n]
unconn = board2.GetConnectivity().GetUnconnectedCount(False)
print(f"\nVerification:")
print(f"  Signal nets in PCB: {len(nets2)}")
print(f"  Nets: {sorted(nets2)}")
print(f"  Unconnected ratsnest items: {unconn}")

# ── Step 6: Sync footprint paths from schematic UUIDs (issue #77) ────────────
# Sets /{uuid} path on every footprint so KiCad F8 "Update PCB from Schematic"
# recognises all components as already-placed and never prompts for manual placement.
print("\nSyncing footprint paths from schematic UUIDs …")
SCH = 'C:/repos-github/PoE-FanController/hardware/kicad/PoE-FanController.kicad_sch'
sys.path.insert(0, r'C:/repos-github/PoE-FanController/hardware/generator')
import sync_pcb_paths
sync_pcb_paths.sync_paths(SCH, PCB)
print("Done — all footprints now have schematic UUID paths set.")
