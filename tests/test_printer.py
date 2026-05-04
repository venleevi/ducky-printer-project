"""Tests for printer communication module.

Tests printer USB auto-detection, connection lifecycle, and print operations
using mocked hardware to avoid dependency on physical printer.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path


# Import the module we'll be testing (will fail initially)
from src.printer import find_printer, print_text, print_text_file, PrinterError


class TestFindPrinter:
    """Tests for USB printer auto-detection."""

    def test_find_printer_with_class_7_device_returns_printer(self, mock_usb_device, mocker):
        """Test that find_printer() returns printer instance when USB class 7 device found."""
        # Mock the Usb printer constructor
        mock_printer = MagicMock()
        mock_usb_class = mocker.patch('src.printer.Usb', return_value=mock_printer)

        result = find_printer()

        # Should have called Usb with custom_match parameter
        mock_usb_class.assert_called_once()
        call_kwargs = mock_usb_class.call_args[1]
        assert 'usb_args' in call_kwargs
        assert 'custom_match' in call_kwargs['usb_args']

        # Should return the printer instance
        assert result == mock_printer

    def test_find_printer_with_no_device_raises_printer_error(self, mocker):
        """Test that find_printer() raises PrinterError when no printer found."""
        # Mock Usb to raise exception (no device found)
        mocker.patch('src.printer.Usb', side_effect=Exception("No USB device found"))

        with pytest.raises(PrinterError) as exc_info:
            find_printer()

        assert "No USB printer found" in str(exc_info.value)


class TestPrintText:
    """Tests for print_text() function."""

    def test_print_text_executes_correct_sequence(self, mock_printer, mocker):
        """Test print_text() opens connection, sends text, cuts, and closes."""
        mocker.patch('src.printer.find_printer', return_value=mock_printer)

        content = "Test receipt content"
        result = print_text(content)

        # Verify correct call sequence
        assert mock_printer.open.call_count == 1
        assert mock_printer.text.call_count == 1
        assert mock_printer.cut.call_count == 1
        assert mock_printer.close.call_count == 1

        # Verify method arguments
        mock_printer.text.assert_called_with(content)

        # Verify cut mode
        mock_printer.cut.assert_called_with(mode='FULL')

        # Should return 0 on success
        assert result == 0

    def test_print_text_closes_connection_on_usb_error(self, mock_printer, mocker):
        """Test print_text() closes connection and raises PrinterError on USB error."""
        mocker.patch('src.printer.find_printer', return_value=mock_printer)

        # Create a proper USBError exception class
        class USBError(Exception):
            pass

        # Mock usb.core module with USBError
        mock_usb_module = mocker.MagicMock()
        mock_usb_module.USBError = USBError
        mocker.patch('src.printer.usb.core', mock_usb_module)

        # Make text() raise USB error
        usb_error = USBError("USB communication error")
        mock_printer.text.side_effect = usb_error

        with pytest.raises(PrinterError) as exc_info:
            print_text("Test")

        # Should still close connection despite error
        assert mock_printer.close.call_count == 1
        assert "error" in str(exc_info.value).lower()

    def test_per_job_lifecycle_each_print_opens_and_closes(self, mock_printer, mocker):
        """Test that each print_text() call opens and closes connection (per-job lifecycle)."""
        mocker.patch('src.printer.find_printer', return_value=mock_printer)

        # Call print_text twice
        print_text("First job")
        print_text("Second job")

        # Should have opened and closed twice (once per job)
        assert mock_printer.open.call_count == 2
        assert mock_printer.close.call_count == 2


class TestPrintTextFile:
    """Tests for print_text_file() function."""

    def test_print_text_file_reads_file_and_prints_content(
        self, mock_printer, temp_test_file, sample_text_content, mocker
    ):
        """Test print_text_file() reads file via file_handler and prints content."""
        mocker.patch('src.printer.find_printer', return_value=mock_printer)

        # Mock the read_file function to return sample content
        mock_read_file = mocker.patch('src.printer.read_file', return_value=sample_text_content)

        result = print_text_file("receipt.txt", "/test/folder")

        # Should have called read_file with correct arguments
        mock_read_file.assert_called_once_with("receipt.txt", "/test/folder")

        # Should have printed the content
        mock_printer.text.assert_called_with(sample_text_content)

        # Should return 0 on success
        assert result == 0
