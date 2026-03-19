"""Shared pytest fixtures for printer tests.

This module provides reusable fixtures for testing printer functionality
without requiring physical hardware.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def mock_usb_device():
    """Returns mock USB device object with printer class attributes.

    Creates a mock USB device configured as a thermal printer (class 7).
    Used for testing USB device detection logic.

    Returns:
        MagicMock: USB device with bDeviceClass=7 and bInterfaceClass=7
    """
    device = MagicMock()
    device.bDeviceClass = 7  # USB printer class

    # Mock configuration and interface for class detection
    mock_interface = MagicMock()
    mock_interface.bInterfaceClass = 7

    mock_config = MagicMock()
    mock_config.__iter__ = MagicMock(return_value=iter([mock_interface]))

    device.__iter__ = MagicMock(return_value=iter([mock_config]))

    return device


@pytest.fixture
def mock_printer():
    """Returns mock python-escpos Usb printer instance.

    Creates a mock printer object that tracks method calls for verification.
    All printer methods (open, close, text, feed, cut) are mocked.

    Returns:
        MagicMock: Printer instance with mocked communication methods
    """
    printer = MagicMock()
    printer.open = MagicMock()
    printer.close = MagicMock()
    printer.text = MagicMock()
    printer.feed = MagicMock()
    printer.cut = MagicMock()

    return printer


@pytest.fixture
def sample_text_content():
    """Returns sample receipt text with mixed ASCII and UTF-8 characters.

    Provides realistic receipt content for testing text printing and
    UTF-8 encoding validation.

    Returns:
        str: Multi-line receipt text with special characters
    """
    return """Customer Receipt
==================
Item 1: Coffee ☕        $3.50
Item 2: Croissant 🥐     $2.75
Item 3: Café Latte      $4.25
------------------
Subtotal:              $10.50
Tax (8%):               $0.84
------------------
Total:                 $11.34

Thank you! Merci! 谢谢!
"""


@pytest.fixture
def temp_test_file(tmp_path, sample_text_content):
    """Creates temporary text file with sample content.

    Uses pytest's tmp_path fixture to create a temporary file that's
    automatically cleaned up after the test. File is UTF-8 encoded.

    Args:
        tmp_path: Pytest fixture providing temporary directory
        sample_text_content: Fixture providing sample receipt text

    Returns:
        Path: Path object to the temporary file
    """
    test_file = tmp_path / "test_receipt.txt"
    test_file.write_text(sample_text_content, encoding='utf-8')
    return test_file


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Creates temporary directory for config source_folder tests.

    Provides a clean temporary directory that exists for testing
    source_folder path validation.

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        Path: Path object to the temporary directory
    """
    return tmp_path
