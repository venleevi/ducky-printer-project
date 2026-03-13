"""Tests for print_job CLI entry point module.

Tests cover:
- Command-line argument parsing (argparse)
- Main entry point orchestration
- Error handling and exit codes
- Output to stdout/stderr
"""

import sys
import pytest
from unittest.mock import patch, MagicMock
from src.file_handler import FileError
from src.printer import PrinterError


def test_parse_args_with_filename_only():
    """Test parse_args with just filename argument."""
    from src.print_job import parse_args

    args = parse_args(["receipt.txt"])

    assert args.filename == "receipt.txt"
    assert args.folder == "/GEN26_BILLPRINTER"
    assert args.verbose is False


def test_parse_args_with_verbose_flag():
    """Test parse_args with --verbose flag."""
    from src.print_job import parse_args

    args = parse_args(["receipt.txt", "--verbose"])

    assert args.filename == "receipt.txt"
    assert args.verbose is True


def test_parse_args_with_custom_folder():
    """Test parse_args with custom --folder argument."""
    from src.print_job import parse_args

    args = parse_args(["receipt.txt", "--folder", "/custom/path"])

    assert args.filename == "receipt.txt"
    assert args.folder == "/custom/path"


def test_parse_args_missing_filename():
    """Test parse_args raises SystemExit when filename is missing."""
    from src.print_job import parse_args

    with pytest.raises(SystemExit):
        parse_args([])


def test_main_with_valid_file(mocker, capsys):
    """Test main() returns 0 on successful print."""
    from src.print_job import main

    # Mock print_file to simulate successful print
    mock_print = mocker.patch('src.print_job.print_file', return_value=0)

    # Mock sys.argv for argument parsing
    mocker.patch('sys.argv', ['print_job.py', 'receipt.txt'])

    result = main()

    assert result == 0
    mock_print.assert_called_once_with('receipt.txt', '/GEN26_BILLPRINTER')


def test_main_with_file_error(mocker, capsys):
    """Test main() returns 1 and prints error to stderr on FileError."""
    from src.print_job import main

    # Mock print_file to raise FileError
    mock_print = mocker.patch(
        'src.print_job.print_file',
        side_effect=FileError("File not found: /GEN26_BILLPRINTER/missing.txt")
    )

    # Mock sys.argv
    mocker.patch('sys.argv', ['print_job.py', 'missing.txt'])

    result = main()

    assert result == 1

    # Check stderr output
    captured = capsys.readouterr()
    assert "File error:" in captured.err
    assert "File not found" in captured.err


def test_main_with_printer_error(mocker, capsys):
    """Test main() returns 1 and prints error to stderr on PrinterError."""
    from src.print_job import main

    # Mock print_file to raise PrinterError
    mock_print = mocker.patch(
        'src.print_job.print_file',
        side_effect=PrinterError("No printer found")
    )

    # Mock sys.argv
    mocker.patch('sys.argv', ['print_job.py', 'receipt.txt'])

    result = main()

    assert result == 1

    # Check stderr output
    captured = capsys.readouterr()
    assert "Printer error:" in captured.err
    assert "No printer found" in captured.err


def test_main_with_keyboard_interrupt(mocker, capsys):
    """Test main() returns 130 and prints 'Interrupted' on KeyboardInterrupt."""
    from src.print_job import main

    # Mock print_file to raise KeyboardInterrupt
    mock_print = mocker.patch(
        'src.print_job.print_file',
        side_effect=KeyboardInterrupt()
    )

    # Mock sys.argv
    mocker.patch('sys.argv', ['print_job.py', 'receipt.txt'])

    result = main()

    assert result == 130

    # Check stderr output
    captured = capsys.readouterr()
    assert "Interrupted" in captured.err


def test_main_with_verbose_flag(mocker, capsys):
    """Test main() with --verbose prints success message to stdout."""
    from src.print_job import main

    # Mock print_file to simulate successful print
    mock_print = mocker.patch('src.print_job.print_file', return_value=0)

    # Mock sys.argv with --verbose
    mocker.patch('sys.argv', ['print_job.py', 'receipt.txt', '--verbose'])

    result = main()

    assert result == 0

    # Check stdout output
    captured = capsys.readouterr()
    assert "Successfully printed: receipt.txt" in captured.out
