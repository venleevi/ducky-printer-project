"""CLI entry point for thermal printer job execution.

This module provides the command-line interface for printing files from the
/home/admin/ducky-printer-project/print_files/ folder (or custom path) to a USB thermal printer.

Supports text files (.txt) and image files (.png, .jpg, .jpeg, .bmp).

Usage:
    python print_job.py receipt.txt
    python print_job.py wish1.png --verbose
    python print_job.py wish1.png --rotate --width 8 --height 18
    python print_job.py wide_image.png --rotate --fit
    python print_job.py large_image.png --fit
    python print_job.py large_image.png --scale 25
    python print_job.py receipt.txt --folder /custom/path

Exit codes:
    0: Success
    1: Error (file not found, printer error, etc.)
    2: Invalid command-line arguments (argparse default)
    130: Interrupted (Ctrl+C)
"""

import sys
import argparse
from src.file_handler import FileError
from src.printer import print_file, PrinterError


def parse_args(args=None):
    """Parse command-line arguments.

    Args:
        args: Argument list to parse (defaults to sys.argv if None)

    Returns:
        argparse.Namespace: Parsed arguments with attributes:
            - filename (str): File to print
            - folder (str): Base folder path
            - verbose (bool): Enable verbose output

    Raises:
        SystemExit: If arguments are invalid (argparse default behavior)
    """
    parser = argparse.ArgumentParser(
        description='Print text or image files to thermal receipt printer',
        epilog='Examples:\n  python print_job.py receipt.txt\n  python print_job.py wish1.png --verbose',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'filename',
        type=str,
        help='File to print (.txt, .png, .jpg, .jpeg, .bmp). Assumes /home/admin/ducky-printer-project/print_files/ unless full path.'
    )

    parser.add_argument(
        '--folder',
        type=str,
        default='/home/admin/ducky-printer-project/print_files',
        help='Base folder path (default: /home/admin/ducky-printer-project/print_files)'
    )

    parser.add_argument(
        '--rotate', '-r',
        action='store_true',
        help='Rotate image 90° clockwise for vertical printing (useful for wide images)'
    )

    parser.add_argument(
        '--scale', '-s',
        type=int,
        default=100,
        metavar='PERCENT',
        help='Scale image to percentage of original size (default: 100). E.g., 25 = 1/4 size, 50 = 1/2 size. Ignored if --fit is used.'
    )

    parser.add_argument(
        '--fit', '-f',
        action='store_true',
        help='Automatically scale image to fit printer width (maintains aspect ratio)'
    )

    parser.add_argument(
        '--printer-width',
        type=int,
        default=576,
        metavar='PIXELS',
        help='Printer width in pixels for --fit scaling (default: 576 for 80mm paper). Common: 384 (58mm), 576 (80mm)'
    )

    parser.add_argument(
        '--width',
        type=float,
        metavar='CM',
        help='Target print width in centimeters (e.g., 8.0 for 8cm). Use with --height to set exact dimensions.'
    )

    parser.add_argument(
        '--height',
        type=float,
        metavar='CM',
        help='Target print height in centimeters (e.g., 18.0 for 18cm). Use with --width to set exact dimensions.'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args(args)


def main():
    """Main entry point - orchestrate print job.

    Returns:
        int: Exit code (0=success, 1=error, 130=interrupted)
    """
    args = parse_args()

    try:
        # Print file using printer module (auto-detects text vs image)
        print_file(
            args.filename,
            args.folder,
            rotate=args.rotate,
            scale_percent=args.scale,
            fit_width=args.fit,
            printer_width=args.printer_width,
            target_width_cm=args.width,
            target_height_cm=args.height
        )

        if args.verbose:
            rotation_msg = " (rotated 90°)" if args.rotate else ""
            if args.width and args.height:
                scale_msg = f" (scaled to fit {args.width}cm × {args.height}cm)"
            elif args.fit:
                scale_msg = f" (fitted to {args.printer_width}px width)"
            elif args.scale != 100:
                scale_msg = f" (scaled to {args.scale}%)"
            else:
                scale_msg = ""
            print(f"Successfully printed: {args.filename}{rotation_msg}{scale_msg}")

        return 0

    except FileError as e:
        print(f"File error: {e}", file=sys.stderr)
        return 1

    except PrinterError as e:
        print(f"Printer error: {e}", file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"File type error: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
