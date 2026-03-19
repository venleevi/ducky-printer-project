"""Tests for print logging functionality."""

import sqlite3
import pytest
from pathlib import Path
from src.print_logger import log_print_event, DB_PATH, _init_database


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Create temporary database for testing."""
    test_db = tmp_path / "test_print_log.db"
    monkeypatch.setattr("src.print_logger.DB_PATH", test_db)
    return test_db


def test_init_database_creates_table(temp_db):
    """Test that database initialization creates the print_log table."""
    _init_database()

    assert temp_db.exists()

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Check table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='print_log'"
    )
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == "print_log"

    # Check table schema
    cursor.execute("PRAGMA table_info(print_log)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    assert "id" in columns
    assert "timestamp" in columns
    assert "success" in columns
    assert "file_path" in columns
    assert "error_message" in columns

    conn.close()


def test_log_successful_print(temp_db):
    """Test logging a successful print event."""
    log_print_event(success=True, file_path="/path/to/file.png")

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM print_log")
    row = cursor.fetchone()

    assert row is not None
    assert row[2] == 1  # success = 1
    assert row[3] == "/path/to/file.png"  # file_path
    assert row[4] is None  # error_message = NULL

    conn.close()


def test_log_failed_print(temp_db):
    """Test logging a failed print event."""
    log_print_event(
        success=False,
        file_path="/path/to/file.png",
        error_message="Printer not found"
    )

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM print_log")
    row = cursor.fetchone()

    assert row is not None
    assert row[2] == 0  # success = 0
    assert row[3] == "/path/to/file.png"  # file_path
    assert row[4] == "Printer not found"  # error_message

    conn.close()


def test_log_multiple_events(temp_db):
    """Test logging multiple print events."""
    log_print_event(success=True, file_path="/path/1.png")
    log_print_event(success=False, error_message="No files")
    log_print_event(success=True, file_path="/path/2.png")

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM print_log")
    count = cursor.fetchone()[0]
    assert count == 3

    cursor.execute("SELECT COUNT(*) FROM print_log WHERE success = 1")
    success_count = cursor.fetchone()[0]
    assert success_count == 2

    cursor.execute("SELECT COUNT(*) FROM print_log WHERE success = 0")
    failure_count = cursor.fetchone()[0]
    assert failure_count == 1

    conn.close()


def test_log_event_with_minimal_data(temp_db):
    """Test logging with only required success parameter."""
    log_print_event(success=False)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM print_log")
    row = cursor.fetchone()

    assert row is not None
    assert row[2] == 0  # success = 0
    assert row[3] is None  # file_path = NULL
    assert row[4] is None  # error_message = NULL

    conn.close()


def test_timestamp_format(temp_db):
    """Test that timestamps are in ISO 8601 format."""
    log_print_event(success=True)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("SELECT timestamp FROM print_log")
    timestamp = cursor.fetchone()[0]

    # Verify ISO 8601 format (YYYY-MM-DDTHH:MM:SS.ffffff)
    assert "T" in timestamp
    assert len(timestamp) >= 19  # At minimum YYYY-MM-DDTHH:MM:SS

    conn.close()
