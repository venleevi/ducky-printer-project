"""Random file selector with extension filtering.

Implements:
- FILE-01: Random selection from source folder
- FILE-02: Extension filtering (.txt, .png, .jpg, .jpeg, .bmp)
- FILE-03: Graceful empty folder handling with warning log
"""

from pathlib import Path
import random
import logging
from src.config.schema import PrinterConfig

logger = logging.getLogger(__name__)

# Supported file extensions (matches printer.py)
SUPPORTED_EXTENSIONS = {'.txt', '.png', '.jpg', '.jpeg', '.bmp'}


def select_random_printable_file(config: PrinterConfig) -> Path | None:
    """Select a random printable file from configured source folder.

    Requirements:
    - FILE-01: Random selection from source folder
    - FILE-02: Only supported file types (.txt, .png, .jpg, .jpeg, .bmp)
    - FILE-03: Empty folder logs warning, doesn't crash

    Args:
        config: PrinterConfig with source_folder field

    Returns:
        Path to randomly selected file, or None if no files available
    """
    # Extract and resolve source folder
    source_folder = config.source_folder
    if not source_folder.is_absolute():
        source_folder = source_folder.resolve()

    # Filter for supported files only
    printable_files = [
        f for f in source_folder.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    # Handle empty case (FILE-03)
    if not printable_files:
        logger.warning(
            f"No printable files found in {source_folder}. "
            f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
        return None

    # Random selection (FILE-01)
    return random.choice(printable_files)
