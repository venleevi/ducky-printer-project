#!/usr/bin/env python3
"""Read SW1-3 setting from printer to verify top margin configuration.

Queries the printer for current memory switch settings.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.printer import find_printer, PrinterError


def read_sw1_3():
    """Read SW1-3 (top margin) setting from printer."""

    print("=" * 70)
    print("READING SW1-3 SETTING FROM PRINTER")
    print("=" * 70)
    print()

    try:
        printer = find_printer()
        printer.open()

        print("✓ Printer connected")
        print()
        print("Querying memory switches...")
        print()

        # Method 1: Request printer status with memory switches
        try:
            # ESC u n - Transmit peripheral device status
            # This might include memory switch info on some models
            printer._raw(b'\x1B\x75\x00')
            print("  1. Sent status query command")
        except:
            pass

        # Method 2: GS ( E - Query memory switch settings
        try:
            # GS ( E pL pH fn=2 (query memory switch)
            # Request SW1 settings
            printer._raw(b'\x1D\x28\x45\x02\x00\x02\x01')
            print("  2. Sent SW1 query command")
        except:
            pass

        # Method 3: Request device ID (might include switch info)
        try:
            # GS I n - Request printer ID/status
            printer._raw(b'\x1D\x49\x00')
            print("  3. Sent device ID query")
        except:
            pass

        # Try to read response (if any)
        try:
            import usb.core
            # Try to read from input endpoint
            response = printer.device.read(0x81, 64, timeout=1000)
            if response:
                print()
                print("Response received:")
                print("  Raw bytes:", ' '.join(f'{b:02x}' for b in response))

                # Try to interpret as ASCII
                try:
                    text = bytes(response).decode('ascii', errors='ignore')
                    if text.strip():
                        print("  Text:", text)
                except:
                    pass
        except usb.core.USBError as e:
            print()
            print("  No response received (timeout or not supported)")
            print(f"  USB Error: {e}")
        except Exception as e:
            print()
            print(f"  Could not read response: {e}")

        printer.close()

        print()
        print("=" * 70)
        print("QUERY COMPLETE")
        print("=" * 70)
        print()
        print("⚠️  Note: Many thermal printers don't support reading memory")
        print("    switches via software. If no response, you need to:")
        print()
        print("ALTERNATIVE: Print self-test to see SW1-3 status")
        print("───────────────────────────────────────────────────────────────")
        print("1. Turn printer OFF")
        print("2. Hold FEED button")
        print("3. Turn printer ON (keep holding FEED)")
        print("4. Release when printer starts printing")
        print("5. Look at printout for:")
        print()
        print("   │ SW1 │ OFF │ OFF │ ??? │ OFF │ OFF │ OFF │ OFF │ OFF │")
        print("                       ↑")
        print("                    SW1-3")
        print()
        print("   If bit 3 = ON  → Success! Top margin is now 1mm")
        print("   If bit 3 = OFF → Need to use FEED button method")
        print()
        print("=" * 70)

        return 0

    except PrinterError as e:
        print(f"✗ Error: {e}")
        return 1

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(read_sw1_3())
