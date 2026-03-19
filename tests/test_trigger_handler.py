"""Tests for print trigger handler.

Requirement: GPIO-05 - Printer failures log errors but do not crash the listener service

Test coverage:
1. Success path returns True and logs success
2. No files available returns False and logs warning
3. PrinterError returns False and logs error (no crash)
4. FileError returns False and logs error (no crash)
5. Generic exception returns False and logs with stack trace (no crash)
6. Path to string conversion verified
7. Default print settings verified
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, call
from src.trigger_handler import handle_print_trigger
from src.config.schema import PrinterConfig
from src.printer import PrinterError
from src.file_handler import FileError


class TestHandlePrintTriggerSuccess:
    """Test successful print trigger execution."""

    def test_success_path_returns_true_and_logs_success(self, tmp_path, caplog):
        """Given valid config with files, when triggered, then prints and returns True."""
        # Arrange
        config = PrinterConfig(source_folder=tmp_path)
        test_file = tmp_path / "test.txt"

        with patch('src.trigger_handler.select_random_printable_file') as mock_select, \
             patch('src.trigger_handler.print_file') as mock_print:
            mock_select.return_value = test_file
            mock_print.return_value = 0

            # Act
            with caplog.at_level('INFO', logger='src.trigger_handler'):
                result = handle_print_trigger(config)

            # Assert
            assert result is True
            mock_select.assert_called_once_with(config)
            mock_print.assert_called_once()
            assert f"Print triggered successfully: {test_file}" in caplog.text

    def test_converts_path_to_string_for_print_file(self, tmp_path):
        """Verify Path object is converted to string when calling print_file."""
        # Arrange
        config = PrinterConfig(source_folder=tmp_path)
        test_file = Path("/home/admin/test.png")

        with patch('src.trigger_handler.select_random_printable_file') as mock_select, \
             patch('src.trigger_handler.print_file') as mock_print:
            mock_select.return_value = test_file
            mock_print.return_value = 0

            # Act
            handle_print_trigger(config)

            # Assert
            # First positional arg should be string, not Path
            call_args = mock_print.call_args
            assert isinstance(call_args[1]['filename'], str)
            assert call_args[1]['filename'] == str(test_file)

    def test_uses_default_print_settings(self, tmp_path):
        """Verify default print settings are passed to print_file."""
        # Arrange
        config = PrinterConfig(source_folder=tmp_path)
        test_file = tmp_path / "test.png"

        with patch('src.trigger_handler.select_random_printable_file') as mock_select, \
             patch('src.trigger_handler.print_file') as mock_print:
            mock_select.return_value = test_file
            mock_print.return_value = 0

            # Act
            handle_print_trigger(config)

            # Assert
            mock_print.assert_called_once_with(
                filename=str(test_file),
                base_folder=str(test_file.parent),
                rotate=True,
                target_width_cm=8.0,
                target_height_cm=18.0
            )


class TestHandlePrintTriggerNoFiles:
    """Test behavior when no printable files available."""

    def test_no_files_returns_false_and_logs_warning(self, tmp_path, caplog):
        """Given empty source folder, when triggered, then returns False and logs warning."""
        # Arrange
        config = PrinterConfig(source_folder=tmp_path)

        with patch('src.trigger_handler.select_random_printable_file') as mock_select, \
             patch('src.trigger_handler.print_file') as mock_print:
            mock_select.return_value = None  # No files available

            # Act
            with caplog.at_level('WARNING', logger='src.trigger_handler'):
                result = handle_print_trigger(config)

            # Assert
            assert result is False
            mock_select.assert_called_once_with(config)
            mock_print.assert_not_called()  # Should not attempt to print
            assert f"No printable files available in {tmp_path}" in caplog.text


class TestHandlePrintTriggerPrinterErrors:
    """Test error handling for printer failures (GPIO-05 requirement)."""

    def test_printer_error_returns_false_and_logs_error(self, tmp_path, caplog):
        """Given PrinterError, when triggered, then returns False and logs error (no crash)."""
        # Arrange
        config = PrinterConfig(source_folder=tmp_path)
        test_file = tmp_path / "test.txt"
        error_msg = "USB error: [Errno 19] No such device"

        with patch('src.trigger_handler.select_random_printable_file') as mock_select, \
             patch('src.trigger_handler.print_file') as mock_print:
            mock_select.return_value = test_file
            mock_print.side_effect = PrinterError(error_msg)

            # Act
            with caplog.at_level('ERROR', logger='src.trigger_handler'):
                result = handle_print_trigger(config)

            # Assert - GPIO-05: Does NOT crash, returns False
            assert result is False
            assert f"Print failed: {error_msg}" in caplog.text

    def test_file_error_returns_false_and_logs_error(self, tmp_path, caplog):
        """Given FileError, when triggered, then returns False and logs error (no crash)."""
        # Arrange
        config = PrinterConfig(source_folder=tmp_path)
        test_file = tmp_path / "test.txt"
        error_msg = "File not readable"

        with patch('src.trigger_handler.select_random_printable_file') as mock_select, \
             patch('src.trigger_handler.print_file') as mock_print:
            mock_select.return_value = test_file
            mock_print.side_effect = FileError(error_msg)

            # Act
            with caplog.at_level('ERROR', logger='src.trigger_handler'):
                result = handle_print_trigger(config)

            # Assert - GPIO-05: Does NOT crash, returns False
            assert result is False
            assert f"File read failed: {error_msg}" in caplog.text

    def test_value_error_returns_false_and_logs_error(self, tmp_path, caplog):
        """Given ValueError (unsupported file type), then returns False and logs error."""
        # Arrange
        config = PrinterConfig(source_folder=tmp_path)
        test_file = tmp_path / "test.pdf"
        error_msg = "Unsupported file type: .pdf"

        with patch('src.trigger_handler.select_random_printable_file') as mock_select, \
             patch('src.trigger_handler.print_file') as mock_print:
            mock_select.return_value = test_file
            mock_print.side_effect = ValueError(error_msg)

            # Act
            with caplog.at_level('ERROR', logger='src.trigger_handler'):
                result = handle_print_trigger(config)

            # Assert - GPIO-05: Does NOT crash, returns False
            assert result is False
            assert f"Unsupported file type: {error_msg}" in caplog.text


class TestHandlePrintTriggerFileSelectionErrors:
    """Test error handling for file selection failures."""

    def test_file_selection_error_returns_false_and_logs_error(self, tmp_path, caplog):
        """Given file selection error, when triggered, then returns False and logs error."""
        # Arrange
        config = PrinterConfig(source_folder=tmp_path)
        error_msg = "Folder does not exist"

        with patch('src.trigger_handler.select_random_printable_file') as mock_select, \
             patch('src.trigger_handler.print_file') as mock_print:
            mock_select.side_effect = FileNotFoundError(error_msg)

            # Act
            with caplog.at_level('ERROR', logger='src.trigger_handler'):
                result = handle_print_trigger(config)

            # Assert - GPIO-05: Does NOT crash, returns False
            assert result is False
            mock_print.assert_not_called()
            assert "Unexpected error in print trigger" in caplog.text


class TestHandlePrintTriggerUnexpectedErrors:
    """Test generic exception handling (GPIO-05 safety net)."""

    def test_unexpected_error_returns_false_and_logs_exception(self, tmp_path, caplog):
        """Given unexpected exception, when triggered, then returns False with stack trace."""
        # Arrange
        config = PrinterConfig(source_folder=tmp_path)
        error_msg = "Unexpected database error"

        with patch('src.trigger_handler.select_random_printable_file') as mock_select:
            mock_select.side_effect = RuntimeError(error_msg)

            # Act
            with caplog.at_level('ERROR', logger='src.trigger_handler'):
                result = handle_print_trigger(config)

            # Assert - GPIO-05: Does NOT crash, returns False
            assert result is False
            assert "Unexpected error in print trigger" in caplog.text
            assert error_msg in caplog.text
