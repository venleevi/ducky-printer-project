"""CLI entry point for thermal printer job execution.

This module provides the command-line interface for printing files from the
/GEN26_BILLPRINTER/ folder (or custom path) to a USB thermal printer.

Supports text files (.txt) and image files (.png, .jpg, .jpeg, .bmp).

Usage:
    python print_job.py receipt.txt
    python print_job.py wish1.png --verbose
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
        help='File to print (.txt, .png, .jpg, .jpeg, .bmp). Assumes /GEN26_BILLPRINTER/ unless full path.'
    )

    parser.add_argument(
        '--folder',
        type=str,
        default='/GEN26_BILLPRINTER',
        help='Base folder path (default: /GEN26_BILLPRINTER)'
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
        print_file(args.filename, args.folder)

        if args.verbose:
            print(f"Successfully printed: {args.filename}")

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
