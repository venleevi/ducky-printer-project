"""Printer communication module for USB thermal printer.

This module provides USB printer auto-detection using device class matching,
per-job connection lifecycle, and ESC/POS print operations via python-escpos.

Security notes:
- Per-job connection lifecycle (open-print-close) prevents device busy errors
- Class-based USB detection works across multiple printer models
- All USB errors are caught and converted to PrinterError
- Connection always closed in finally block to prevent resource leaks
"""

import usb.core
from escpos.printer import Usb
from src.file_handler import read_file


class PrinterError(Exception):
    """Custom exception for printer operation errors."""
    pass


def find_printer():
    """Auto-detect USB thermal printer by device class (class 7).

    Uses USB class 7 (printer class) detection to find thermal printer
    without requiring hard-coded vendor/product IDs. This approach works
    across multiple printer models and is more robust to device changes.

    Returns:
        Usb: python-escpos printer instance ready for operations

    Raises:
        PrinterError: If no printer found or USB error occurs

    Example:
        >>> printer = find_printer()
        >>> printer.open()
    """
    def match_printer_class(device):
        """Check if USB device is a printer (class 7)."""
        # Check device-level class
        if device.bDeviceClass == 7:
            return True

        # Check interface-level class descriptors
        try:
            for cfg in device:
                for intf in cfg:
                    if intf.bInterfaceClass == 7:
                        return True
        except:
            pass

        return False

    try:
        printer = Usb(usb_args={'custom_match': match_printer_class})
        return printer
    except Exception as e:
        raise PrinterError(f"No printer found: {e}")


def print_text(content: str) -> int:
    """Print text content with per-job connection lifecycle.

    Opens connection, prints content with spacing and paper cut, then closes.
    Connection is always closed even if errors occur (finally block).

    Print sequence:
    1. Open connection
    2. Feed 1 blank line (top spacing)
    3. Print content (UTF-8 via python-escpos MagicEncode)
    4. Feed 2 blank lines (bottom spacing)
    5. Full paper cut
    6. Close connection

    Args:
        content: Text content to print (UTF-8 string)

    Returns:
        int: 0 on success

    Raises:
        PrinterError: If USB error occurs or printer unavailable

    Example:
        >>> print_text("Customer Receipt\\nTotal: $10.50")
        0
    """
    printer = find_printer()

    try:
        # Open connection for this print job
        printer.open()

        # Add 1 blank line at top
        printer.feed(1)

        # Print content (python-escpos handles UTF-8 encoding)
        printer.text(content)

        # Add 2 blank lines at bottom
        printer.feed(2)

        # Full paper cut
        printer.cut(mode='FULL')

        return 0

    except usb.core.USBError as e:
        raise PrinterError(f"USB error: {e}")

    except Exception as e:
        raise PrinterError(f"Printer error: {e}")

    finally:
        # Always close connection to prevent resource leaks
        try:
            printer.close()
        except:
            pass  # Ignore errors on close


def print_text_file(filename: str, base_folder: str = "/GEN26_BILLPRINTER") -> int:
    """Read text file and print its content.

    Reads file via file_handler module (handles UTF-8 validation and errors),
    then prints content via print_text().

    Args:
        filename: Name of file to print (relative or absolute path)
        base_folder: Base folder for relative paths (default: /GEN26_BILLPRINTER)

    Returns:
        int: 0 on success

    Raises:
        FileError: If file cannot be read (from file_handler module)
        PrinterError: If printing fails (from print_text function)

    Example:
        >>> print_text_file("receipt.txt")
        0

        >>> print_text_file("/tmp/test.txt")
        0
    """
    # Read file content (FileError propagates to caller)
    content = read_file(filename, base_folder)

    # Print content (PrinterError propagates to caller)
    return print_text(content)
