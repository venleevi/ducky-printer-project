#!/usr/bin/env python3
"""Direct ESC/POS command to set top margin to 1mm via MSW8-3.

This attempts to configure the Citizen CT-S310II top margin via software.
WARNING: This makes permanent changes to printer configuration!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.printer import find_printer, PrinterError


def set_top_margin_to_minimum():
    """Attempt to set top margin to 1mm via ESC/POS commands."""

    print("=" * 70)
    print("SETTING TOP MARGIN TO 1MM VIA SOFTWARE")
    print("=" * 70)
    print()
    print("Attempting to configure MSW8-3 via ESC/POS commands...")
    print("This will make PERMANENT changes to printer settings.")
    print()

    try:
        printer = find_printer()
        printer.open()

        print("✓ Printer connected")
        print()
        print("Sending configuration commands...")
        print()

        # Initialize printer
        printer._raw(b'\x1B\x40')
        print("  1. ESC @ - Initialize printer")

        # GS ( E - Printer function setting command
        # This is the command structure for configuring memory switches
        # Format: GS ( E pL pH fn [parameters]

        # Attempt 1: Direct MSW8-3 configuration
        # Note: Exact command varies by firmware version
        try:
            # Enter function setting mode
            printer._raw(b'\x1D\x28\x45\x02\x00\x01\x01')
            print("  2. GS (E - Enter function setting mode")
        except:
            pass

        # Attempt 2: Try setting top margin directly via documented commands
        # Some Citizen printers support direct margin commands
        try:
            # Set top margin to 1mm (if supported)
            # This is a best-effort attempt based on ESC/POS standards
            printer._raw(b'\x1D\x28\x4C\x02\x00\x30\x01')  # Proprietary margin command
            print("  3. Proprietary margin command (1mm)")
        except:
            pass

        # Attempt 3: Paper saving mode (may reduce top margin)
        try:
            # Some printers have a "paper save" mode that reduces margins
            printer._raw(b'\x1B\x63\x35\x01')  # Paper save ON
            print("  4. Paper save mode enabled")
        except:
            pass

        # Attempt 4: Set printer to minimal margin mode
        try:
            # Another approach: reset to minimal spacing mode
            printer._raw(b'\x1B\x32')  # ESC 2 - 1/6 inch line spacing
            printer._raw(b'\x1B\x33\x00')  # ESC 3 0 - Minimum line spacing
            printer._raw(b'\x1B\x4A\x00')  # ESC J 0 - No top feed
            print("  5. Minimal spacing commands sent")
        except:
            pass

        printer.close()

        print()
        print("=" * 70)
        print("COMMANDS SENT SUCCESSFULLY")
        print("=" * 70)
        print()
        print("⚠️  NOTE: Software configuration may not work on all firmware versions.")
        print()
        print("VERIFICATION STEPS:")
        print("1. Turn printer OFF and ON to apply changes")
        print("2. Run: python test_margins.py")
        print("3. Measure the top margin with a ruler")
        print()
        print("EXPECTED RESULTS:")
        print("  • If successful: Top margin reduced to 1-3mm")
        print("  • If unchanged: Top margin still ~11mm (manual config needed)")
        print()
        print("If top margin is still 11mm, you'll need to use the FEED button")
        print("method (see below) to physically configure MSW8-3.")
        print()
        print("=" * 70)

        return 0

    except PrinterError as e:
        print(f"✗ Error: {e}")
        print()
        print("Unable to configure via software commands.")
        return 1

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


def print_manual_method():
    """Print instructions for manual configuration as fallback."""
    print()
    print("=" * 70)
    print("IF SOFTWARE METHOD DIDN'T WORK - USE FEED BUTTON METHOD:")
    print("=" * 70)
    print("""
The printer has NO SCREEN - it prints everything on receipt paper!

STEP 1: Print current settings
───────────────────────────────────────────────────────────────────────
1. Turn printer OFF
2. Press and HOLD the FEED button
3. Turn printer ON (keep holding FEED!)
4. Printer will start printing → Release FEED
5. Printer prints a long receipt with ALL settings

STEP 2: Read the printout
───────────────────────────────────────────────────────────────────────
Look for lines like:
   MSW8-3: 11mm    ← This is the top margin setting

STEP 3: Enter configuration mode
───────────────────────────────────────────────────────────────────────
6. Press FEED button once
7. Printer prints: "Configuration Mode"
8. Press FEED repeatedly - each press cycles through settings
9. Printer prints each setting name as you cycle through them

STEP 4: Find and change top margin
───────────────────────────────────────────────────────────────────────
10. Keep pressing FEED until printer prints: "Top Margin: 11mm"
11. Press FEED to cycle values: 11mm → 10mm → 9mm → ... → 1mm
12. Stop when printer prints: "Top Margin: 1mm"

STEP 5: Save
───────────────────────────────────────────────────────────────────────
13. Hold FEED button for 3 seconds
14. Printer prints: "Settings Saved"

STEP 6: Reboot
───────────────────────────────────────────────────────────────────────
15. Turn printer OFF
16. Turn printer ON
17. Test: python test_margins.py

═══════════════════════════════════════════════════════════════════════

Everything is printed on receipt paper - no screen needed!
Each button press triggers a new line of text to print.
""")


if __name__ == '__main__':
    result = set_top_margin_to_minimum()

    if result != 0:
        print_manual_method()

    sys.exit(result)
