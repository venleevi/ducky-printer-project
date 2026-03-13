"""Tests for file_handler module."""

import pytest
from pathlib import Path
from src.file_handler import read_file, resolve_filepath, FileError


def test_read_file_with_valid_utf8_file(tmp_path):
    """Test 1: read_file with valid UTF-8 file returns content as string."""
    test_file = tmp_path / "test.txt"
    test_content = "Hello, thermal printer!\nLine 2 with UTF-8: café ☕"
    test_file.write_text(test_content, encoding="utf-8")

    result = read_file(str(test_file))

    assert result == test_content
    assert isinstance(result, str)


def test_read_file_missing_file_raises_error(tmp_path):
    """Test 2: read_file with missing file raises FileError with 'File not found' message."""
    missing_file = tmp_path / "missing.txt"

    with pytest.raises(FileError) as exc_info:
        read_file(str(missing_file))

    assert "File not found" in str(exc_info.value)


def test_read_file_with_binary_file_raises_error(tmp_path):
    """Test 3: read_file with binary file raises FileError with 'not valid UTF-8' message."""
    binary_file = tmp_path / "binary.dat"
    # Write invalid UTF-8 bytes
    binary_file.write_bytes(b'\x80\x81\x82\x83')

    with pytest.raises(FileError) as exc_info:
        read_file(str(binary_file))

    assert "not valid UTF-8" in str(exc_info.value)


def test_read_file_with_permission_denied_raises_error(tmp_path):
    """Test 4: read_file with permission denied raises FileError with 'Permission denied' message."""
    restricted_file = tmp_path / "restricted.txt"
    restricted_file.write_text("content", encoding="utf-8")
    # Remove all read permissions
    restricted_file.chmod(0o000)

    try:
        with pytest.raises(FileError) as exc_info:
            read_file(str(restricted_file))

        assert "Permission denied" in str(exc_info.value)
    finally:
        # Restore permissions for cleanup
        restricted_file.chmod(0o644)


def test_resolve_filepath_with_default_folder():
    """Test 5: resolve_filepath with relative filename returns /GEN26_BILLPRINTER/filename path."""
    result = resolve_filepath("receipt.txt")

    assert isinstance(result, Path)
    assert str(result) == "/GEN26_BILLPRINTER/receipt.txt"


def test_resolve_filepath_with_absolute_path():
    """Test 6: resolve_filepath with absolute path returns path as-is without prepending base folder."""
    result = resolve_filepath("/full/path.txt")

    assert isinstance(result, Path)
    assert str(result) == "/full/path.txt"
    assert "GEN26_BILLPRINTER" not in str(result)
