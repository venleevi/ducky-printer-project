"""File handler module for reading text files from USB stick folder.

This module provides functionality to read text files with UTF-8 encoding
from the /home/admin/ducky-printer-project/print_files/ folder (default) or from absolute paths.

Security notes:
- Uses pathlib.Path for secure path manipulation (no string concatenation)
- Provides clear error messages for all failure modes
- Validates UTF-8 encoding to prevent binary data processing
"""

from pathlib import Path
from typing import Union


class FileError(Exception):
    """Custom exception for file operation errors."""
    pass


def resolve_filepath(
    filename: str,
    base_folder: str = "/home/admin/ducky-printer-project/print_files"
) -> Path:
    """Resolve a filename to a full Path object.

    If the filename is an absolute path, returns it as-is.
    If it's a relative filename, prepends the base_folder.

    Args:
        filename: The filename or path to resolve
        base_folder: The base folder to use for relative paths (default: /home/admin/ducky-printer-project/print_files)

    Returns:
        Path object representing the full file path

    Examples:
        >>> resolve_filepath("receipt.txt")
        PosixPath('/home/admin/ducky-printer-project/print_files/receipt.txt')

        >>> resolve_filepath("/full/path/receipt.txt")
        PosixPath('/full/path/receipt.txt')
    """
    filepath = Path(filename)

    # If the path is absolute, return it as-is
    if filepath.is_absolute():
        return filepath

    # Otherwise, prepend the base folder
    return Path(base_folder) / filepath


def read_file(
    filename: str,
    base_folder: str = "/home/admin/ducky-printer-project/print_files"
) -> str:
    """Read a text file with UTF-8 encoding.

    Reads the content of a file, automatically resolving the full path
    based on whether the filename is absolute or relative.

    Args:
        filename: The filename or path to read
        base_folder: The base folder to use for relative paths (default: /home/admin/ducky-printer-project/print_files)

    Returns:
        The file content as a UTF-8 decoded string

    Raises:
        FileError: If the file cannot be read for any reason:
            - File not found
            - File is not valid UTF-8
            - Permission denied
            - Other I/O errors

    Examples:
        >>> content = read_file("receipt.txt")
        >>> print(content)
        Customer Receipt
        ...

        >>> content = read_file("/tmp/test.txt")
    """
    filepath = resolve_filepath(filename, base_folder)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    except FileNotFoundError:
        raise FileError(f"File not found: {filepath}")

    except UnicodeDecodeError:
        raise FileError(f"File is not valid UTF-8: {filepath}")

    except PermissionError:
        raise FileError(f"Permission denied reading file: {filepath}")

    except Exception as e:
        raise FileError(f"Error reading file {filepath}: {e}")
