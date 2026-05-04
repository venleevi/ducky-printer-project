"""Print trigger handler with error resilience.

Implements GPIO-05 requirement: Printer failures log errors but do not crash
the listener service.

This module provides the integration point for GPIO listeners (Phase 5),
orchestrating file selection and printing with comprehensive error handling.
"""

import logging
from pathlib import Path
from src.config.schema import PrinterConfig
from src.file_selector import select_random_printable_file
from src.printer import print_file, PrinterError
from src.file_handler import FileError
from src.print_logger import log_print_event

logger = logging.getLogger(__name__)


def handle_print_trigger(config: PrinterConfig) -> bool:
    """Handle print trigger event with error resilience.

    Orchestrates file selection and printing with comprehensive error handling.
    All errors are logged but do not raise exceptions (GPIO-05 requirement).

    Requirements:
    - GPIO-05: Printer failures log errors but do not crash the listener service

    Error handling:
    - No files available: logs warning, returns False
    - PrinterError: logs error, returns False (no crash)
    - FileError: logs error, returns False (no crash)
    - ValueError: logs error, returns False (no crash)
    - Unexpected exceptions: logs with stack trace, returns False (no crash)

    Args:
        config: PrinterConfig with source_folder and other settings

    Returns:
        bool: True if print succeeded, False otherwise

    Example:
        >>> config = PrinterConfig(source_folder=Path("print_files"))
        >>> result = handle_print_trigger(config)
        >>> print(f"Success: {result}")
    """
    try:
        # Select random file from configured source folder
        file_path = select_random_printable_file(config)

        # Handle no files available (FILE-03 requirement)
        if file_path is None:
            logger.warning(f"No printable files available in {config.source_folder}")
            log_print_event(success=False, error_message="No printable files available")
            return False

        # Print file with default settings
        try:
            print_file(
                filename=str(file_path),
                base_folder=str(file_path.parent),
                rotate=True,
                target_width_cm=8.0,  # Full paper width (576px)
                target_height_cm=17.3  # 18cm total with ~0.7cm cut overhead
            )
            logger.info(f"Print triggered successfully: {file_path}")
            log_print_event(success=True, file_path=str(file_path))
            return True

        except PrinterError as e:
            # USB disconnected, device busy, etc. (GPIO-05)
            logger.error(f"Print failed: {e}")
            log_print_event(success=False, file_path=str(file_path), error_message=f"PrinterError: {e}")
            return False

        except FileError as e:
            # File read failed (GPIO-05)
            logger.error(f"File read failed: {e}")
            log_print_event(success=False, file_path=str(file_path), error_message=f"FileError: {e}")
            return False

        except ValueError as e:
            # Unsupported file type (GPIO-05)
            logger.error(f"Unsupported file type: {e}")
            log_print_event(success=False, file_path=str(file_path), error_message=f"ValueError: {e}")
            return False

    except Exception as e:
        # Catch-all for unexpected errors (GPIO-05 safety net)
        # Uses logger.exception to include stack trace for debugging
        logger.exception(f"Unexpected error in print trigger: {e}")
        log_print_event(success=False, error_message=f"Unexpected error: {e}")
        return False
