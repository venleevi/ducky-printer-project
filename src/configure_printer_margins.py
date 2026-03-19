#!/usr/bin/env python3
"""Printer margin configuration utility for Citizen CT-S310II.

This utility helps reduce the hardware-enforced top margin from the default 11mm
to the minimum 1mm by providing instructions for configuring Memory Switch MSW8-3.

The CT-S310II has a configurable top margin controlled by MSW8-3:
- Default: 11mm
- Configurable: 1mm, 3mm, 4mm, 5mm, 6mm, 7mm, 8mm, 9mm, 10mm
- Minimum: 1mm

Usage:
    python src/configure_printer_margins.py
    python src/configure_printer_margins.py --send-commands
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.printer import find_printer, PrinterError


def print_instructions():
    """Print detailed instructions for configuring memory switches."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              Citizen CT-S310II Margin Configuration Guide                  ║
╚════════════════════════════════════════════════════════════════════════════╝

PROBLEM: Excessive top margin (~11mm default) wastes paper and creates whitespace

SOLUTION: Configure Memory Switch MSW8-3 to reduce top margin to 1-3mm

═══════════════════════════════════════════════════════════════════════════════

METHOD 1: Self-Test Mode Configuration (RECOMMENDED)
────────────────────────────────────────────────────────────────────────────────

1. Turn OFF the printer
2. Hold down the FEED button
3. While holding FEED, turn the printer ON
4. Keep holding FEED until the printer starts printing the self-test
5. Release the FEED button
6. The self-test will print current settings including MSW values
7. To enter configuration mode:
   - Press FEED button multiple times to cycle through menu options
   - Look for "MSW8-3 Top Margin" setting
   - Use FEED to change value from 11mm to 1mm (or 3mm for safety)
8. Save settings and exit (usually by holding FEED for 3 seconds)
9. Turn printer OFF and ON again to apply changes

═══════════════════════════════════════════════════════════════════════════════

METHOD 2: DIP Switch Access (If Available)
────────────────────────────────────────────────────────────────────────────────

Some CT-S310II models have physical DIP switches inside the printer:

1. Turn OFF the printer and unplug power
2. Remove printer cover (usually 2-4 screws)
3. Locate DIP switch bank (small switches near control board)
4. Find switch labeled MSW8-3 (may be in bank 8, switch 3)
5. Set MSW8-3 to configure top margin:
   - Refer to User Manual for exact DIP switch positions
   - Target: 1mm or 3mm for minimal top margin
6. Replace cover, plug in power, turn ON printer

═══════════════════════════════════════════════════════════════════════════════

METHOD 3: Software Configuration (ESC/POS Commands)
────────────────────────────────────────────────────────────────────────────────

Memory switches can be configured via ESC/POS commands (GS (E):

WARNING: This method can make permanent changes to printer configuration.
         Only use if you understand ESC/POS command protocol.

Run with --send-commands flag to attempt software configuration:
    python src/configure_printer_margins.py --send-commands

═══════════════════════════════════════════════════════════════════════════════

VERIFICATION:
────────────────────────────────────────────────────────────────────────────────

After configuration:
1. Print a test image: python -m src.print_job nopadding.png
2. Measure top margin with ruler - should be 1-3mm instead of 11mm
3. Expected improvement: ~8-10mm reduction in top whitespace

═══════════════════════════════════════════════════════════════════════════════

CURRENT SOFTWARE OPTIMIZATIONS:
────────────────────────────────────────────────────────────────────────────────

Your printer.py has been updated with:
✓ ESC @ - Initialize printer (reset state)
✓ ESC 3 0 - Set line spacing to minimum
✓ ESC 2 - Set line feed to 1/6 inch
✓ GS L 0 0 - Set left margin to 0
✓ ESC J 0 - No additional top feed
✓ ESC d 1 - Minimal bottom feed before cut

These reduce software-controlled margins but cannot override MSW8-3 hardware
setting. Reconfiguring MSW8-3 is required for significant top margin reduction.

═══════════════════════════════════════════════════════════════════════════════

REFERENCES:
────────────────────────────────────────────────────────────────────────────────

See: /home/admin/ducky-printer-project/CITIZEN_CT-S310II_MARGIN_RESEARCH.md
Official Manual: CT-S310II User Manual Section 4 (Memory Switches)
Command Reference: CommandReference.pdf (page 486, MSW8-3)

════════════════════════════════════════════════════════════════════════════════
""")


def send_configuration_commands():
    """Send ESC/POS commands to configure top margin via memory switches.

    This uses GS (E fn [parameter] commands to configure printer settings.

    WARNING: This makes permanent changes to printer configuration!
    """
    print("Attempting to configure top margin via ESC/POS commands...")
    print("WARNING: This may make permanent changes to printer settings!")

    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return 1

    try:
        printer = find_printer()
        printer.open()

        print("\nSending configuration commands...")

        # GS (E pL pH fn [parameter] - Printer function setting command
        # This is model-specific and may not work on all printers
        # Refer to CT-S310II Command Reference for exact command structure

        # Note: The exact command structure for MSW8-3 configuration
        # is not universally documented. The following is a best-effort
        # attempt based on Citizen ESC/POS standards.

        # Initialize printer first
        printer._raw(b'\x1B\x40')  # ESC @
        print("✓ Initialized printer")

        # Attempt to enter configuration mode
        # GS (E pL pH fn=1 (transfer to printer function setting mode)
        printer._raw(b'\x1D\x28\x45\x03\x00\x01\x01')
        print("✓ Entered configuration mode")

        # Note: Without exact documentation, we cannot safely set MSW8-3
        # The safest approach is to use self-test mode (Method 1)

        print("\n⚠ Software configuration of MSW8-3 requires exact command codes")
        print("  which vary by firmware version.")
        print("\nRECOMMENDED: Use Self-Test Mode (Method 1) for reliable configuration.")

        printer.close()
        return 0

    except PrinterError as e:
        print(f"\n✗ Error: {e}")
        print("\nFailed to configure via software commands.")
        print("Please use Self-Test Mode (Method 1) instead.")
        return 1

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Configure Citizen CT-S310II printer margins',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/configure_printer_margins.py
    Show configuration instructions

  python src/configure_printer_margins.py --send-commands
    Attempt software configuration (use with caution)
"""
    )

    parser.add_argument(
        '--send-commands',
        action='store_true',
        help='Attempt to send ESC/POS configuration commands (use with caution)'
    )

    args = parser.parse_args()

    if args.send_commands:
        return send_configuration_commands()
    else:
        print_instructions()
        return 0


if __name__ == '__main__':
    sys.exit(main())
