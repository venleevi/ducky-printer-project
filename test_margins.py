#!/usr/bin/env python3
"""Test script to verify margin improvements.

This script prints a test pattern to help measure top and bottom margins.
Use a ruler to measure the whitespace before and after the print.

Usage:
    python test_margins.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.printer import print_file, PrinterError


def main():
    """Print test pattern to measure margins."""
    print("=" * 70)
    print("MARGIN TEST - Printing test pattern")
    print("=" * 70)

    # Check if nopadding.png exists
    test_file = Path("/home/admin/ducky-printer-project/print_files/nopadding.png")
    if not test_file.exists():
        print(f"\n✗ Test file not found: {test_file}")
        print("\nPlease ensure nopadding.png exists in print_files/")
        return 1

    try:
        print("\n1. Printing test image (nopadding.png)...")
        print_file("nopadding.png", rotate=True)

        print("\n✓ Print complete!")
        print("\n" + "=" * 70)
        print("MEASUREMENT INSTRUCTIONS:")
        print("=" * 70)
        print("""
1. Take the printed receipt and place it on a flat surface
2. Use a ruler to measure:

   TOP MARGIN:
   - Measure from edge of paper to start of printed image
   - Expected BEFORE fix: ~11mm (hardware default)
   - Expected AFTER software optimization: ~11mm (still limited by MSW8-3)
   - Expected AFTER MSW8-3 reconfiguration: ~1-3mm

   BOTTOM MARGIN:
   - Measure from end of printed image to cut edge
   - Expected: ~13-15mm (hardware cutter position limit)
   - Minor improvement possible with software optimization

3. Record your measurements:
   - Top margin: _____ mm
   - Bottom margin: _____ mm
   - Total vertical whitespace: _____ mm

4. Compare to your previous measurements

═══════════════════════════════════════════════════════════════════════════════

NEXT STEPS:

If top margin is still ~11mm:
→ Run: python src/configure_printer_margins.py
→ Follow instructions to set MSW8-3 to 1mm or 3mm
→ Re-run this test after configuration

If top margin is now 1-3mm:
→ Success! MSW8-3 has been configured correctly
→ Software optimizations are working

═══════════════════════════════════════════════════════════════════════════════
""")

        return 0

    except PrinterError as e:
        print(f"\n✗ Printer error: {e}")
        return 1

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
