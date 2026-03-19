#!/usr/bin/env python3
"""View print logs from SQLite database.

Displays print history with timestamps, success/failure status, and error details.

Usage:
    python view_print_logs.py           # Show all logs
    python view_print_logs.py --last 10  # Show last 10 entries
    python view_print_logs.py --failed   # Show only failed prints
"""

import argparse
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "print_log.db"


def format_timestamp(iso_timestamp):
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_timestamp


def view_logs(limit=None, failed_only=False):
    """View print logs from database.

    Args:
        limit: Maximum number of entries to show (None = all)
        failed_only: If True, only show failed prints
    """
    if not DB_PATH.exists():
        print(f"No database found at {DB_PATH}")
        print("No print events have been logged yet.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Build query
        query = "SELECT id, timestamp, success, file_path, error_message FROM print_log"

        if failed_only:
            query += " WHERE success = 0"

        query += " ORDER BY id DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            print("No print events found.")
            return

        # Display header
        print("\n" + "=" * 100)
        print(f"{'ID':<6} {'Timestamp':<20} {'Status':<10} {'File':<40} {'Error':<20}")
        print("=" * 100)

        # Display rows
        for row in rows:
            row_id, timestamp, success, file_path, error_message = row
            status = "✓ SUCCESS" if success else "✗ FAILED"
            formatted_time = format_timestamp(timestamp)
            file_display = (file_path or "")[:40] if file_path else ""
            error_display = (error_message or "")[:20] if error_message else ""

            print(f"{row_id:<6} {formatted_time:<20} {status:<10} {file_display:<40} {error_display:<20}")

        print("=" * 100)
        print(f"\nTotal entries: {len(rows)}")

        # Show statistics
        cursor.execute("SELECT COUNT(*) FROM print_log WHERE success = 1")
        success_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM print_log WHERE success = 0")
        failure_count = cursor.fetchone()[0]

        total_count = success_count + failure_count
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        print(f"Success: {success_count} | Failed: {failure_count} | Success Rate: {success_rate:.1f}%\n")

        conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="View print logs from SQLite database"
    )
    parser.add_argument(
        "--last",
        type=int,
        metavar="N",
        help="Show only the last N entries"
    )
    parser.add_argument(
        "--failed",
        action="store_true",
        help="Show only failed print attempts"
    )

    args = parser.parse_args()

    view_logs(limit=args.last, failed_only=args.failed)


if __name__ == "__main__":
    main()
