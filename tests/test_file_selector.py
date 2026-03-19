"""Tests for random file selector with extension filtering.

Test coverage for:
- FILE-01: Random selection from source folder
- FILE-02: Extension filtering (.txt, .png, .jpg, .jpeg, .bmp)
- FILE-03: Empty folder handling
"""

import pytest
from pathlib import Path
from src.file_selector import select_random_printable_file, SUPPORTED_EXTENSIONS
from src.config.schema import PrinterConfig


# FILE-01: Random selection tests


def test_selects_from_available_files(tmp_path):
    """Given folder with supported files, returns one of them."""
    # Create test files
    (tmp_path / "file1.txt").write_text("test")
    (tmp_path / "file2.png").write_bytes(b"fake png")
    (tmp_path / "file3.jpg").write_bytes(b"fake jpg")

    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)

    assert result is not None
    assert result.name in {"file1.txt", "file2.png", "file3.jpg"}
    assert result.parent == tmp_path


def test_randomness_over_multiple_calls(tmp_path):
    """Multiple calls can return different files (proves randomness)."""
    # Create 5 test files to increase probability of different results
    for i in range(5):
        (tmp_path / f"file{i}.txt").write_text(f"content {i}")

    config = PrinterConfig(source_folder=tmp_path)
    results = {select_random_printable_file(config).name for _ in range(20)}

    # With 20 calls on 5 files, we should get at least 2 different files
    assert len(results) > 1, "Expected randomness, but got same file every time"


def test_uses_uniform_random_distribution(tmp_path, monkeypatch):
    """Selection uses random.choice for uniform distribution."""
    import random

    # Create test files
    (tmp_path / "file1.txt").write_text("test")
    (tmp_path / "file2.txt").write_text("test")

    # Mock random.choice to verify it's called
    choice_called = False
    original_choice = random.choice

    def mock_choice(seq):
        nonlocal choice_called
        choice_called = True
        return original_choice(seq)

    monkeypatch.setattr(random, "choice", mock_choice)

    config = PrinterConfig(source_folder=tmp_path)
    select_random_printable_file(config)

    assert choice_called, "Expected random.choice to be called"


# FILE-02: Extension filtering tests


def test_includes_txt_files(tmp_path):
    """Includes .txt files in selection."""
    (tmp_path / "test.txt").write_text("content")
    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)
    assert result.name == "test.txt"


def test_includes_png_files(tmp_path):
    """Includes .png files in selection."""
    (tmp_path / "test.png").write_bytes(b"fake png")
    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)
    assert result.name == "test.png"


def test_includes_jpg_files(tmp_path):
    """Includes .jpg files in selection."""
    (tmp_path / "test.jpg").write_bytes(b"fake jpg")
    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)
    assert result.name == "test.jpg"


def test_includes_jpeg_files(tmp_path):
    """Includes .jpeg files in selection."""
    (tmp_path / "test.jpeg").write_bytes(b"fake jpeg")
    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)
    assert result.name == "test.jpeg"


def test_includes_bmp_files(tmp_path):
    """Includes .bmp files in selection."""
    (tmp_path / "test.bmp").write_bytes(b"fake bmp")
    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)
    assert result.name == "test.bmp"


def test_case_insensitive_extensions(tmp_path):
    """Matches .TXT, .PNG, .Txt, etc."""
    (tmp_path / "file1.TXT").write_text("content")
    (tmp_path / "file2.PNG").write_bytes(b"fake")
    (tmp_path / "file3.Txt").write_text("content")

    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)

    assert result is not None
    assert result.suffix.lower() in {".txt", ".png"}


def test_excludes_unsupported_extensions(tmp_path):
    """Excludes .pdf, .doc, .mp3."""
    (tmp_path / "file.pdf").write_bytes(b"pdf")
    (tmp_path / "file.doc").write_bytes(b"doc")
    (tmp_path / "file.mp3").write_bytes(b"mp3")

    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)

    assert result is None


def test_excludes_directories(tmp_path):
    """Directories excluded even if named like files."""
    # Create a directory with .txt in the name
    (tmp_path / "test.txt").mkdir()

    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)

    assert result is None


# FILE-03: Empty folder tests


def test_empty_folder_returns_none(tmp_path):
    """Empty folder (no files at all) returns None."""
    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)
    assert result is None


def test_folder_with_only_unsupported_returns_none(tmp_path):
    """Folder with only unsupported files returns None."""
    (tmp_path / "file.pdf").write_bytes(b"pdf")
    (tmp_path / "file.zip").write_bytes(b"zip")

    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)

    assert result is None


def test_empty_folder_logs_warning(tmp_path, caplog):
    """Warning includes path and supported extensions."""
    import logging
    caplog.set_level(logging.WARNING)

    config = PrinterConfig(source_folder=tmp_path)
    select_random_printable_file(config)

    assert len(caplog.records) == 1
    warning = caplog.records[0]
    assert warning.levelname == "WARNING"
    assert str(tmp_path) in warning.message
    assert ".txt" in warning.message or "Supported extensions" in warning.message


# Integration tests


def test_reads_source_folder_from_config(tmp_path):
    """Accepts PrinterConfig and reads source_folder field."""
    (tmp_path / "test.txt").write_text("content")

    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)

    assert result is not None
    assert result.parent == tmp_path


def test_returns_path_objects_not_strings(tmp_path):
    """Returns pathlib.Path, not str."""
    (tmp_path / "test.txt").write_text("content")

    config = PrinterConfig(source_folder=tmp_path)
    result = select_random_printable_file(config)

    assert isinstance(result, Path)
    assert not isinstance(result, str)
