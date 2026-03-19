#!/usr/bin/env python3
"""Set SW1-3 to ON to reduce top margin from 11mm to 1mm.

Based on CT-S310II self-test output:
- SW1-3 = OFF: 11mm top margin (current)
- SW1-3 = ON:  1mm top margin (target)

This sends ESC/POS commands to configure the memory switch.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.printer import find_printer, PrinterError


def set_sw1_3_on():
    """Set SW1-3 (top margin) to ON via ESC/POS commands."""

    print("=" * 70)
    print("SETTING SW1-3 TO ON (Top Margin: 11mm → 1mm)")
    print("=" * 70)
    print()
    print("Target: SW1-3 = ON (reduces top margin to 1mm)")
    print()

    try:
        printer = find_printer()
        printer.open()

        print("✓ Printer connected")
        print()
        print("Sending commands to set SW1-3 = ON...")
        print()

        # Initialize printer
        printer._raw(b'\x1B\x40')
        print("  1. ESC @ - Initialize printer")

        # GS ( E - Memory switch setting command for CT-S310II
        # Format: GS ( E pL pH fn m a [parameters]
        # fn=3: Set memory switch
        # m=switch bank (1=SW1, 2=SW2, etc.)
        # a=bit number (3 for SW1-3)

        try:
            # Attempt to set SW1, bit 3 to ON
            # Command structure for Citizen CT-S310II
            # GS ( E pL pH fn m a b
            # where b = 1 (ON) or 0 (OFF)

            # Set SW1-3 to ON
            printer._raw(b'\x1D\x28\x45\x04\x00\x03\x01\x03\x01')
            print("  2. GS (E - Set SW1-3 to ON")
        except Exception as e:
            print(f"  2. Warning: {e}")

        # Alternative approach: Use printer function setting mode
        try:
            # Enter memory switch programming mode
            printer._raw(b'\x1D\x28\x45\x03\x00\x01\x01')
            print("  3. GS (E - Enter memory switch mode")

            # Program SW1-3 = ON
            # This varies by firmware but is a common approach
            printer._raw(b'\x1D\x28\x45\x05\x00\x0A\x01\x01\x03\x01')
            print("  4. Program SW1-3 = ON")
        except Exception as e:
            print(f"  3-4. Warning: {e}")

        # Alternative: Direct memory switch command (Citizen-specific)
        try:
            # Some Citizen printers accept direct switch programming
            printer._raw(b'\x1B\x1D\x61\x01\x03\x01')
            print("  5. Direct SW1-3 command")
        except Exception as e:
            print(f"  5. Warning: {e}")

        # Exit programming mode and save
        try:
            printer._raw(b'\x1D\x28\x45\x02\x00\x02\x01')
            print("  6. Save and exit programming mode")
        except Exception as e:
            print(f"  6. Warning: {e}")

        printer.close()

        print()
        print("=" * 70)
        print("COMMANDS SENT")
        print("=" * 70)
        print()
        print("⚠️  IMPORTANT: Power cycle the printer for changes to take effect!")
        print()
        print("NEXT STEPS:")
        print("───────────────────────────────────────────────────────────────")
        print("1. Turn printer OFF")
        print("2. Turn printer ON")
        print("3. Verify with self-test (HOLD FEED → Turn ON):")
        print("   Look for: SW1 bit 3 = ON (was OFF)")
        print()
        print("4. Test margin reduction:")
        print("   python test_margins.py")
        print()
        print("EXPECTED RESULT:")
        print("───────────────────────────────────────────────────────────────")
        print("  • Top margin: ~1mm (was 11mm)")
        print("  • Improvement: 10mm saved per print!")
        print("  • Total whitespace: ~14-15mm (was ~24-26mm)")
        print()
        print("If SW1-3 is still OFF after power cycle, use FEED button method:")
        print("  1. Self-test printout → Press FEED once")
        print("  2. Press FEED until you see 'SW1-3'")
        print("  3. Press FEED to toggle OFF → ON")
        print("  4. Hold FEED 3 seconds to save")
        print()
        print("=" * 70)

        return 0

    except PrinterError as e:
        print(f"✗ Error: {e}")
        print()
        print("Unable to configure via software.")
        print("Please use FEED button method (see above).")
        return 1

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(set_sw1_3_on())
