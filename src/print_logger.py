"""Print event logging to SQLite database.

Records each print trigger event with timestamp and outcome.
Database is stored in the project root directory.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Database location in project root
DB_PATH = Path(__file__).parent.parent / "print_log.db"


def _init_database():
    """Initialize SQLite database and create print_log table if needed.

    Table schema:
        - id: Auto-incrementing primary key
        - timestamp: ISO 8601 timestamp of print event
        - success: Boolean (1=success, 0=failure)
        - file_path: Path to file that was printed (or attempted)
        - error_message: Error details if print failed (NULL if success)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS print_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                success INTEGER NOT NULL,
                file_path TEXT,
                error_message TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.debug(f"Database initialized at {DB_PATH}")

    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def log_print_event(
    success: bool,
    file_path: Optional[str] = None,
    error_message: Optional[str] = None
):
    """Log a print event to the SQLite database.

    Args:
        success: True if print succeeded, False if failed
        file_path: Path to the file that was printed (optional)
        error_message: Error details if print failed (optional)

    Example:
        >>> log_print_event(True, "/path/to/file.png")
        >>> log_print_event(False, error_message="Printer not found")
    """
    try:
        # Ensure database exists
        _init_database()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO print_log (timestamp, success, file_path, error_message)
            VALUES (?, ?, ?, ?)
            """,
            (timestamp, 1 if success else 0, file_path, error_message)
        )

        conn.commit()
        conn.close()

        logger.debug(f"Logged print event: success={success}, file={file_path}")

    except sqlite3.Error as e:
        # Don't crash on logging failures - just log the error
        logger.error(f"Failed to log print event to database: {e}")
