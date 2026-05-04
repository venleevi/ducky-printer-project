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
from pathlib import Path
from escpos.printer import Usb
from PIL import Image, ImageOps
from src.file_handler import read_file, resolve_filepath

# Thermal printer resolution: 72 pixels per cm (for 576px width on 8cm paper)
PIXELS_PER_CM = 72


class PrinterError(Exception):
    """Custom exception for printer operation errors."""
    pass


def find_printer():
    """Auto-detect USB thermal printer by device class (class 7).

    Uses USB class 7 (printer class) detection to find thermal printer
    without requiring hard-coded vendor/product IDs. This approach works
    across multiple printer models and is more robust to device changes.

    Explicitly specifies USB endpoints (in_ep=0x81, out_ep=0x02) which
    is required for some thermal printers like Citizen CT-S310IIEBK.

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
        # Create printer with explicit endpoints (required for some models)
        # in_ep=0x81 (bulk IN), out_ep=0x02 (bulk OUT)
        printer = Usb(
            usb_args={'custom_match': match_printer_class},
            in_ep=0x81,
            out_ep=0x02
        )
        return printer
    except Exception as e:
        raise PrinterError(f"No printer found: {e}")


def print_text(content: str) -> int:
    """Print text content with per-job connection lifecycle.

    Opens connection, prints content with spacing and paper cut, then closes.
    Connection is always closed even if errors occur (finally block).

    Print sequence:
    1. Open connection
    2. Print content (UTF-8 via python-escpos MagicEncode)
    3. Full paper cut (no spacing)
    4. Close connection

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

        # Print content (python-escpos handles UTF-8 encoding)
        printer.text(content)

        # Full paper cut (no spacing)
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


def print_text_file(filename: str, base_folder: str = "/home/admin/ducky-printer-project/print_files") -> int:
    """Read text file and print its content.

    Reads file via file_handler module (handles UTF-8 validation and errors),
    then prints content via print_text().

    Args:
        filename: Name of file to print (relative or absolute path)
        base_folder: Base folder for relative paths (default: /home/admin/ducky-printer-project/print_files)

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


def print_image(image_path: str, rotate: bool = True, scale_percent: int = 100, fit_width: bool = False, printer_width: int = 576, target_width_cm: float = 8.0, target_height_cm: float = 17.3) -> int:
    """Print image file with per-job connection lifecycle.

    Opens connection, prints image centered on receipt paper, then closes.
    Supports PNG, JPG, BMP formats via PIL/Pillow (python-escpos dependency).

    Print sequence:
    1. Open connection
    2. Optionally rotate image 90° clockwise (for wide images)
    3. Optionally scale image (fit to printer width, target dimensions, or manual percentage)
    4. Center image with white padding if target dimensions specified
    5. Print image (centered with padding when using target dimensions)
    6. Full paper cut (no spacing)
    7. Close connection

    Args:
        image_path: Full path to image file (PNG, JPG, BMP)
        rotate: If True, rotate image 90° clockwise for vertical printing (default: False)
        scale_percent: Scale image to percentage of original size (default: 100)
                       e.g., 25 = 25% (1/4 size), 50 = 50% (1/2 size)
                       Ignored if fit_width=True or target dimensions set
        fit_width: If True, automatically scale image to fit printer width (default: False)
                   Ignored if target dimensions set
        printer_width: Printer width in pixels for fit_width scaling (default: 576 for 80mm paper)
                       Common values: 384 (58mm), 576 (80mm)
        target_width_cm: Target width in centimeters (e.g., 8.0 for 8cm)
        target_height_cm: Target height in centimeters (e.g., 18.0 for 18cm)
                         If both set, image is scaled to fit and centered with white padding

    Returns:
        int: 0 on success

    Raises:
        PrinterError: If USB error occurs, printer unavailable, or image invalid

    Example:
        >>> print_image("/media/admin/KINGSTON/home/admin/ducky-printer-project/print_files/wish1.png")
        0

        >>> print_image("/media/admin/KINGSTON/home/admin/ducky-printer-project/print_files/wide.png", rotate=True)
        0

        >>> print_image("/media/admin/KINGSTON/home/admin/ducky-printer-project/print_files/large.png", fit_width=True)
        0

        >>> print_image("/media/admin/KINGSTON/home/admin/ducky-printer-project/print_files/wish1.png", rotate=True, target_width_cm=8, target_height_cm=18)
        0
    """
    printer = find_printer()
    temp_path = None

    try:
        # Open connection for this print job
        printer.open()

        # Reset printer and set line spacing to 0 to eliminate padding
        try:
            printer._raw(b'\x1B\x40')  # ESC @ - Initialize printer
            printer._raw(b'\x1B\x33\x00')  # ESC 3 n - Set line spacing to 0
        except:
            pass  # Ignore if not supported

        # Handle image transformations if requested
        actual_image_path = image_path
        if target_width_cm or target_height_cm or fit_width or scale_percent != 100 or rotate:
            # Load image
            img = Image.open(image_path)

            # Rotate first if needed (affects dimensions for scaling calculations)
            if rotate:
                img = img.rotate(-90, expand=True)  # -90 = clockwise

            # Trim white borders before scaling
            diff = ImageOps.invert(img.convert('RGB'))
            bbox = diff.getbbox()
            if bbox:
                img = img.crop(bbox)

            # Scale image based on target dimensions
            if target_width_cm and target_height_cm:
                # Convert cm to pixels
                target_width_px = int(target_width_cm * PIXELS_PER_CM)
                target_height_px = int(target_height_cm * PIXELS_PER_CM)

                # Scale image to fill exact target dimensions (may distort)
                img = img.resize((target_width_px, target_height_px), Image.LANCZOS)

            elif fit_width:
                # Automatically scale to fit printer width while maintaining aspect ratio
                scale_factor = printer_width / img.width
                new_width = printer_width
                new_height = int(img.height * scale_factor)
                img = img.resize((new_width, new_height), Image.LANCZOS)
            elif scale_percent != 100:
                # Manual percentage scaling
                scale_factor = scale_percent / 100.0
                new_width = int(img.width * scale_factor)
                new_height = int(img.height * scale_factor)
                img = img.resize((new_width, new_height), Image.LANCZOS)

            # Save to temp file with same extension
            temp_path = Path(image_path).parent / f".temp_processed_{Path(image_path).name}"
            img.save(temp_path)
            actual_image_path = str(temp_path)

        # Print image (python-escpos handles scaling and dithering)
        # center=False to avoid any centering padding
        # impl="bitImageColumn" is most compatible with thermal printers
        printer.image(actual_image_path, center=False, impl="bitImageColumn")

        # Full paper cut (no spacing)
        printer.cut(mode='FULL')

        return 0

    except usb.core.USBError as e:
        raise PrinterError(f"USB error: {e}")

    except Exception as e:
        raise PrinterError(f"Printer error: {e}")

    finally:
        # Clean up temp processed image if created
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass

        # Always close connection to prevent resource leaks
        try:
            printer.close()
        except:
            pass  # Ignore errors on close


def print_file(filename: str, base_folder: str = "/home/admin/ducky-printer-project/print_files", rotate: bool = True, scale_percent: int = 100, fit_width: bool = False, printer_width: int = 576, target_width_cm: float = 8.0, target_height_cm: float = 17.3) -> int:
    """Print file (text or image) based on file extension.

    Auto-detects file type by extension and routes to appropriate print function:
    - Text files (.txt): print_text_file()
    - Image files (.png, .jpg, .jpeg, .bmp): print_image()

    Args:
        filename: Name of file to print (relative or absolute path)
        base_folder: Base folder for relative paths (default: /home/admin/ducky-printer-project/print_files)
        rotate: If True, rotate images 90° clockwise for vertical printing (default: False)
        scale_percent: Scale images to percentage of original size (default: 100)
        fit_width: If True, automatically scale images to fit printer width (default: False)
        printer_width: Printer width in pixels for fit_width scaling (default: 576)
        target_width_cm: Target width in centimeters for images (e.g., 8.0)
        target_height_cm: Target height in centimeters for images (e.g., 18.0)

    Returns:
        int: 0 on success

    Raises:
        FileError: If file not found or not readable
        PrinterError: If printing fails
        ValueError: If file type not supported

    Example:
        >>> print_file("receipt.txt")
        0

        >>> print_file("wish1.png")
        0

        >>> print_file("wide.png", rotate=True, fit_width=True)
        0

        >>> print_file("wish1.png", rotate=True, target_width_cm=8, target_height_cm=18)
        0
    """
    # Resolve to full path
    file_path = resolve_filepath(filename, base_folder)

    # Check file exists
    if not file_path.exists():
        from src.file_handler import FileError
        raise FileError(f"File not found: {file_path}")

    # Determine file type by extension
    extension = file_path.suffix.lower()

    if extension == '.txt':
        # Text file - use text printing
        return print_text_file(filename, base_folder)

    elif extension in ['.png', '.jpg', '.jpeg', '.bmp']:
        # Image file - use image printing
        return print_image(str(file_path), rotate=rotate, scale_percent=scale_percent, fit_width=fit_width, printer_width=printer_width, target_width_cm=target_width_cm, target_height_cm=target_height_cm)

    else:
        # Unsupported file type
        raise ValueError(f"Unsupported file type: {extension}. Supported: .txt, .png, .jpg, .jpeg, .bmp")
