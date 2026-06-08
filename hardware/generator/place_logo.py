"""
place_logo.py — Ensure the NV-Home-Lab logo footprint is placed in the PCB.

The logo (Logos:nv-homelab-logo-negative-15mm) is NOT in the schematic and
has no nets, so it is invisible to kicad-cli netlist export and import_netlist.py.
This script guarantees the footprint is present at the correct board position
after any PCB regeneration step.

Target position: (10.5, 65.5) — bottom-left corner, clear of all components.
Footprint library: hardware/kicad/footprints/Logos.pretty/

Usage: python place_logo.py          (run after import_netlist.py if needed)
       python place_logo.py --check   (exit 0 if present, 1 if missing)
"""
import sys, re

REPO      = 'C:/repos-github/PoE-FanController'
PCB       = f'{REPO}/hardware/kicad/PoE-FanController.kicad_pcb'
MOD       = f'{REPO}/hardware/kicad/footprints/Logos.pretty/nv-homelab-logo-negative-15mm.kicad_mod'
LOGO_REF  = 'Logos:nv-homelab-logo-negative-15mm'
LOGO_AT   = (10.5, 65.5)
LOGO_UUID = 'c83c7609-bdc2-4bfe-a66b-7f33c54c15f8'

CHECK_ONLY = '--check' in sys.argv


def logo_block_in_pcb(text: str) -> tuple[int, int] | None:
    """Return (start_char, end_char) of existing logo footprint block, or None."""
    marker = f'(footprint "{LOGO_REF}"'
    idx = text.find(marker)
    if idx < 0:
        return None
    depth = 0
    i = idx
    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return (idx, i + 1)
        i += 1
    return None


def build_pcb_footprint(mod_text: str) -> str:
    """
    Convert a .kicad_mod footprint definition into a PCB footprint instance
    with the correct library reference, position, and UUID.
    """
    # Strip the bare footprint name and replace with fully-qualified library ref + PCB attrs
    mod_text = mod_text.strip()
    # Remove the opening line ("(footprint "nv-homelab-logo-negative-15mm"")
    # and inject the library-qualified name + position + uuid
    first_nl = mod_text.index('\n')
    rest = mod_text[first_nl:]  # everything after the first line

    # Remove version/generator lines (not used in PCB instances)
    rest = re.sub(r'\n\s*\(version [^\)]+\)', '', rest)
    rest = re.sub(r'\n\s*\(generator [^\)]+\)', '', rest)
    rest = re.sub(r'\n\s*\(generator_version [^\)]+\)', '', rest)

    block = (
        f'\t(footprint "{LOGO_REF}"\n'
        f'\t\t(layer "F.Cu")\n'
        f'\t\t(uuid "{LOGO_UUID}")\n'
        f'\t\t(at {LOGO_AT[0]} {LOGO_AT[1]})\n'
        + rest.rstrip()
        + '\n\t)'
    )
    return block


print(f"Checking PCB for logo footprint ({LOGO_REF}) …")

with open(PCB, 'r', encoding='utf-8') as f:
    pcb_text = f.read()

span = logo_block_in_pcb(pcb_text)

if span is not None:
    # Verify position
    block = pcb_text[span[0]:span[1]]
    at_match = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)', block)
    if at_match:
        x, y = float(at_match.group(1)), float(at_match.group(2))
        if abs(x - LOGO_AT[0]) < 0.01 and abs(y - LOGO_AT[1]) < 0.01:
            print(f"  ✓ Logo present at ({x}, {y}) — no changes needed.")
            sys.exit(0)
        else:
            print(f"  ⚠ Logo found but at wrong position ({x}, {y}), correcting to {LOGO_AT} …")
    else:
        print("  ⚠ Logo found but position unreadable — re-inserting …")

    if CHECK_ONLY:
        print("  [--check] Wrong position. Exiting with error.")
        sys.exit(1)

    # Remove existing block and re-insert at correct position
    pcb_text = pcb_text[:span[0]] + pcb_text[span[1]:]
else:
    if CHECK_ONLY:
        print("  [--check] Logo missing. Exiting with error.")
        sys.exit(1)
    print("  Logo not found — inserting from library …")

# Build and inject the footprint block before the closing ')' of the board
with open(MOD, 'r', encoding='utf-8') as f:
    mod_text = f.read()

logo_fp = build_pcb_footprint(mod_text)

# Insert before the very last ')' (closes the kicad_pcb block)
insert_at = pcb_text.rfind('\n)')
if insert_at < 0:
    raise RuntimeError("Could not find closing ')' of kicad_pcb block")

pcb_text = pcb_text[:insert_at] + '\n' + logo_fp + pcb_text[insert_at:]

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(pcb_text)

print(f"  ✓ Logo inserted at {LOGO_AT} and PCB saved.")
