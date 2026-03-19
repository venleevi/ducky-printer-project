# Phase 3: File Selection - Research

**Researched:** 2026-03-19
**Domain:** Python file system operations, random selection, directory scanning
**Confidence:** HIGH

## Summary

Phase 3 implements a random file picker that selects printable files from a configured source folder. The domain is well-understood in Python's standard library ecosystem with mature, stable patterns.

The core task involves three operations: (1) scanning a directory for files with supported extensions (.txt, .png, .jpg, .bmp), (2) selecting a random file from the filtered list, and (3) handling edge cases gracefully (empty folders, no matching files). Python's pathlib module (Python 3.4+) provides the modern standard for filesystem operations, and the random module's choice() function handles selection.

This phase integrates with existing v0.1 print pipeline (which already handles .txt, .png, .jpg, .bmp files) and v0.2 Phase 2 configuration system (which provides source_folder path). No new dependencies are required — all functionality exists in Python's standard library.

**Primary recommendation:** Use pathlib.Path.iterdir() with list comprehension for extension filtering, random.choice() for selection, and pre-check for empty lists to avoid exceptions. Follow existing project logging patterns (logging.getLogger(__name__)) for warning messages.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FILE-01 | System picks a random file from the configured source folder on each activation | Python random.choice() with pathlib.Path iteration — standard library, zero dependencies |
| FILE-02 | System filters to supported file types (.txt, .png, .jpg, .bmp) | pathlib.Path.suffix filtering with list comprehension — efficient single-pass scan |
| FILE-03 | Empty source folder logs warning instead of crashing | Pre-check list before random.choice() + logging.getLogger(__name__).warning() — follows existing project pattern |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pathlib | stdlib (Python 3.4+) | File system path operations | Modern Python standard, replaces os.path, cross-platform, object-oriented |
| random | stdlib | Random selection from sequences | Python standard library since 1.5.2, proven randomness for non-cryptographic use |
| logging | stdlib | Structured warning messages | Python standard logging framework, project already uses in config watcher |

### Supporting
None required — all functionality in Python standard library.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pathlib.iterdir() | glob.glob() | glob returns strings not Path objects, less type-safe |
| pathlib.iterdir() | os.listdir() | os.listdir returns strings, pathlib is more Pythonic (PEP 428) |
| random.choice() | random.sample(list, 1) | sample is for multiple items, choice is semantically correct for single selection |
| Pre-check empty list | Try-except IndexError | LBYL (look before you leap) is faster and clearer when empty folders are expected behavior |

**Installation:**
None required — all standard library.

**Version verification:**
Python 3.13.5 confirmed in project environment. All referenced modules are stdlib, no version constraints needed.

## Architecture Patterns

### Recommended Project Structure
```
src/
├── file_selector.py     # New module for random file selection
└── config/              # Existing (provides source_folder path)
```

### Pattern 1: Extension Filtering with pathlib
**What:** Use Path.iterdir() with list comprehension to filter by file suffix
**When to use:** Filtering for specific file extensions in a single directory (non-recursive)
**Example:**
```python
# Based on: https://docs.python.org/3/library/pathlib.html
from pathlib import Path

SUPPORTED_EXTENSIONS = {'.txt', '.png', '.jpg', '.bmp'}

def get_printable_files(folder: Path) -> list[Path]:
    """Return all printable files from folder (non-recursive).

    Args:
        folder: Directory path to scan

    Returns:
        List of Path objects for files with supported extensions
    """
    return [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
```

**Why this pattern:**
- `.iterdir()` is faster than glob for simple directory listing (no pattern matching overhead)
- `.is_file()` excludes directories, symlinks to directories, and other non-file entries
- `.suffix.lower()` handles mixed-case extensions (.TXT, .Txt, .txt)
- List comprehension is single-pass and efficient
- Returns Path objects (not strings) for type safety and downstream use

**Source:** [pathlib — Object-oriented filesystem paths](https://docs.python.org/3/library/pathlib.html)

### Pattern 2: Safe Random Selection
**What:** Pre-check sequence before calling random.choice() to avoid IndexError
**When to use:** When empty sequences are expected/valid (not exceptional)
**Example:**
```python
# Based on: https://note.nkmk.me/en/python-random-choice-sample-choices/
import random
import logging

logger = logging.getLogger(__name__)

def select_random_file(files: list[Path]) -> Path | None:
    """Select a random file from the list, or None if empty.

    Args:
        files: List of file paths to choose from

    Returns:
        Randomly selected Path, or None if list is empty
    """
    if not files:
        logger.warning("No files available for selection")
        return None

    return random.choice(files)
```

**Why this pattern:**
- LBYL (look before you leap) is appropriate when empty lists are expected behavior
- Faster than try-except for non-exceptional cases
- Returns None for explicit null handling (caller can decide behavior)
- logging.warning() matches project pattern (seen in config watcher)

**Source:** [Random Sampling from a List in Python](https://note.nkmk.me/en/python-random-choice-sample-choices/)

### Pattern 3: Integration with Existing Config
**What:** Read source_folder from PrinterConfig, convert relative paths to absolute
**When to use:** Phase depends on Phase 2 config system
**Example:**
```python
from pathlib import Path
from src.config.schema import PrinterConfig

def resolve_source_folder(config: PrinterConfig) -> Path:
    """Resolve source_folder to absolute path.

    Args:
        config: PrinterConfig with source_folder field

    Returns:
        Absolute Path to source folder
    """
    path = config.source_folder

    # Convert relative to absolute (relative to project root or cwd)
    if not path.is_absolute():
        path = path.resolve()

    return path
```

**Why this pattern:**
- Config schema stores Path objects (already type-safe)
- .resolve() converts relative to absolute, resolves symlinks
- Handles both absolute and relative paths from config
- Consistent with existing file_handler.resolve_filepath() pattern

### Anti-Patterns to Avoid
- **Using glob with multiple calls for each extension:** Inefficient compared to iterdir() + suffix check
- **Recursive directory scanning (rglob):** Requirements specify configured source folder only, not subdirectories
- **String-based path manipulation:** Use pathlib Path objects throughout for cross-platform compatibility
- **Catching IndexError from random.choice():** Empty folder is expected behavior, not exceptional — use pre-check
- **Hardcoding file extensions:** Use constant or reference printer.py SUPPORTED_EXTENSIONS for DRY

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Random selection | Custom random index generation | random.choice() | Handles edge cases (empty sequences), cryptographically random not needed, stdlib tested |
| Path operations | String concatenation with "/" | pathlib.Path | Cross-platform (Windows vs Unix), handles . and .., type-safe |
| File extension matching | Regex or string splitting | Path.suffix property | Handles edge cases (no extension, multiple dots), case normalization with .lower() |
| Directory validation | Manual os.path.exists() + os.path.isdir() | Config schema validator | Phase 2 already validates source_folder exists and is directory |

**Key insight:** Python's standard library has mature, tested solutions for all file selection operations. The project already uses pathlib (file_handler.py) and logging (config watcher). Consistency with existing patterns reduces cognitive load and testing surface.

## Common Pitfalls

### Pitfall 1: Case-Sensitive Extension Matching
**What goes wrong:** User saves "photo.JPG" but only ".jpg" is checked, file is ignored
**Why it happens:** File systems may be case-sensitive (Linux) or case-insensitive (Windows/macOS), but Python string comparison is always case-sensitive
**How to avoid:** Always normalize with .suffix.lower() before comparison
**Warning signs:** Test files work but user files don't, platform-specific failures

**Code example:**
```python
# WRONG: Case-sensitive
if f.suffix in {'.txt', '.png', '.jpg', '.bmp'}:  # Misses .TXT, .PNG, etc.

# RIGHT: Case-insensitive
if f.suffix.lower() in {'.txt', '.png', '.jpg', '.bmp'}:
```

### Pitfall 2: Including Directories in File List
**What goes wrong:** Folder named "test.txt" included in file list, causes errors when trying to print
**Why it happens:** iterdir() returns all directory entries, not just files
**How to avoid:** Always filter with .is_file() check
**Warning signs:** Unexpected errors when printing, failures on specific "files"

**Code example:**
```python
# WRONG: Includes directories
files = [f for f in folder.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS]

# RIGHT: Files only
files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]
```

### Pitfall 3: .jpg vs .jpeg Extension Handling
**What goes wrong:** Only .jpg in filter set, user's .jpeg files ignored
**Why it happens:** JPEG standard allows both .jpg and .jpeg extensions, both are common
**How to avoid:** Include both in supported extensions set
**Warning signs:** Some photos work, others don't (check file extensions)

**Code example:**
```python
# INCOMPLETE: Missing .jpeg
SUPPORTED_EXTENSIONS = {'.txt', '.png', '.jpg', '.bmp'}

# COMPLETE: Both JPEG variants
SUPPORTED_EXTENSIONS = {'.txt', '.png', '.jpg', '.jpeg', '.bmp'}
```

**Note:** Existing printer.py already handles .jpeg (line 346), so file selector must match.

### Pitfall 4: Relative Path Resolution Ambiguity
**What goes wrong:** Config specifies "print_files" but code looks in wrong directory (current working directory vs project root)
**Why it happens:** Path.resolve() resolves relative to current working directory, which changes based on how script is invoked
**How to avoid:** Document assumptions, or resolve relative to known anchor (config file location, project root)
**Warning signs:** Works when run from project root, fails when run from elsewhere

**Code example:**
```python
# AMBIGUOUS: Depends on cwd
path = Path("print_files").resolve()  # Where is cwd?

# CLEAR: Explicit anchor (example - project root)
project_root = Path(__file__).parent.parent.parent
path = (project_root / "print_files").resolve()
```

**Project context:** Existing file_handler.py uses hardcoded base_folder="/home/admin/ducky-printer-project/print_files". Phase 3 should align with this pattern or establish new convention.

### Pitfall 5: random.choice() IndexError on Empty List
**What goes wrong:** random.choice([]) raises IndexError, crashes the daemon
**Why it happens:** random.choice() expects non-empty sequence, empty folder is valid state
**How to avoid:** Pre-check with if not files before calling random.choice()
**Warning signs:** Crashes when print_files folder is empty or has no supported files

**Code example:**
```python
# WRONG: Crashes on empty
selected = random.choice(files)  # IndexError: Cannot choose from an empty sequence

# RIGHT: Graceful handling
if not files:
    logger.warning("No printable files in folder")
    return None
selected = random.choice(files)
```

## Code Examples

Verified patterns from official sources and existing project code:

### List Files with Extension Filter
```python
# Source: https://docs.python.org/3/library/pathlib.html
from pathlib import Path

SUPPORTED_EXTENSIONS = {'.txt', '.png', '.jpg', '.jpeg', '.bmp'}

def get_printable_files(folder: Path) -> list[Path]:
    """Return list of printable files from folder.

    Only includes regular files (not directories) with supported extensions.
    Case-insensitive extension matching.

    Args:
        folder: Directory to scan

    Returns:
        List of Path objects for matching files
    """
    return [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
```

### Safe Random Selection with Logging
```python
# Source: Project pattern from src/config/watcher.py
import random
import logging

logger = logging.getLogger(__name__)

def select_random_file(files: list[Path]) -> Path | None:
    """Select random file from list, or None if empty.

    Logs warning if no files available (FILE-03 requirement).

    Args:
        files: List of file paths

    Returns:
        Random Path or None
    """
    if not files:
        logger.warning("No printable files available for selection")
        return None

    return random.choice(files)
```

### Complete File Selector Module
```python
# Integration: Combines patterns above with config integration
from pathlib import Path
import random
import logging
from src.config.schema import PrinterConfig

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.txt', '.png', '.jpg', '.jpeg', '.bmp'}

def select_random_printable_file(config: PrinterConfig) -> Path | None:
    """Select a random printable file from configured source folder.

    Requirements:
    - FILE-01: Random selection from source folder
    - FILE-02: Only supported file types (.txt, .png, .jpg, .bmp)
    - FILE-03: Empty folder logs warning, doesn't crash

    Args:
        config: PrinterConfig with source_folder field

    Returns:
        Path to randomly selected file, or None if no files available
    """
    folder = config.source_folder

    # Resolve relative paths to absolute
    if not folder.is_absolute():
        folder = folder.resolve()

    # Scan for printable files
    files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    # Select random file (or None if empty)
    if not files:
        logger.warning(
            f"No printable files found in {folder} "
            f"(supported: {', '.join(SUPPORTED_EXTENSIONS)})"
        )
        return None

    return random.choice(files)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| os.path module | pathlib.Path | Python 3.4 (PEP 428) | pathlib is now standard for modern Python, object-oriented API |
| glob.glob() for filtering | Path.iterdir() + comprehension | pathlib introduction | iterdir() more efficient for simple filters, returns Path objects |
| Try-except for empty choice | Pre-check with if not list | Community best practice | LBYL preferred when empty is expected, not exceptional |

**Deprecated/outdated:**
- **os.path string manipulation:** Use pathlib.Path for all new code (existing project already uses pathlib)
- **glob.glob() for simple filtering:** Use iterdir() when not using wildcards (faster, cleaner)

**Current state (2026):**
- pathlib is mature and stable (12+ years old)
- random.choice() unchanged since Python 2.x, well-understood
- Python 3.10+ type hints (list[Path], Path | None) for better static analysis

## Open Questions

1. **Should file selection be deterministic for testing?**
   - What we know: random.choice() is non-deterministic, makes testing harder
   - What's unclear: Do we need repeatable selection for integration tests?
   - Recommendation: Accept random.seed() in function for test control, or mock random.choice() in tests (existing project uses pytest-mock)

2. **Should we support .jpeg extension?**
   - What we know: Requirements specify .jpg, printer.py supports .jpeg (line 346)
   - What's unclear: Is .jpeg intentionally supported or accidental?
   - Recommendation: Support .jpeg for consistency with existing printer.py implementation

3. **How should relative paths in source_folder be resolved?**
   - What we know: Config schema allows Path("print_files") default, needs resolution to absolute
   - What's unclear: Relative to what anchor? (cwd, project root, config file location)
   - Recommendation: Use Path.resolve() which resolves to cwd, document assumption, or resolve relative to project root if cwd varies in production

## Validation Architecture

> Validation architecture enabled (workflow.nyquist_validation not set to false in .planning/config.json)

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0+ |
| Config file | /home/admin/ducky-printer-project/pytest.ini |
| Quick run command | `pytest tests/test_file_selector.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FILE-01 | Random file selection from folder | unit | `pytest tests/test_file_selector.py::test_select_random_file_from_folder -x` | ❌ Wave 0 |
| FILE-01 | Each call can return different file (randomness) | unit | `pytest tests/test_file_selector.py::test_selection_is_random -x` | ❌ Wave 0 |
| FILE-02 | Only .txt files included | unit | `pytest tests/test_file_selector.py::test_filters_txt_files -x` | ❌ Wave 0 |
| FILE-02 | Only .png files included | unit | `pytest tests/test_file_selector.py::test_filters_png_files -x` | ❌ Wave 0 |
| FILE-02 | Only .jpg files included | unit | `pytest tests/test_file_selector.py::test_filters_jpg_files -x` | ❌ Wave 0 |
| FILE-02 | Only .bmp files included | unit | `pytest tests/test_file_selector.py::test_filters_bmp_files -x` | ❌ Wave 0 |
| FILE-02 | .jpeg extension also supported | unit | `pytest tests/test_file_selector.py::test_filters_jpeg_files -x` | ❌ Wave 0 |
| FILE-02 | Case-insensitive extension matching (.TXT, .PNG) | unit | `pytest tests/test_file_selector.py::test_case_insensitive_extensions -x` | ❌ Wave 0 |
| FILE-02 | Unsupported extensions excluded (.pdf, .doc) | unit | `pytest tests/test_file_selector.py::test_excludes_unsupported_extensions -x` | ❌ Wave 0 |
| FILE-02 | Directories excluded even if named like file | unit | `pytest tests/test_file_selector.py::test_excludes_directories -x` | ❌ Wave 0 |
| FILE-03 | Empty folder returns None | unit | `pytest tests/test_file_selector.py::test_empty_folder_returns_none -x` | ❌ Wave 0 |
| FILE-03 | Empty folder logs warning message | unit | `pytest tests/test_file_selector.py::test_empty_folder_logs_warning -x` | ❌ Wave 0 |
| FILE-03 | Folder with only unsupported files returns None | unit | `pytest tests/test_file_selector.py::test_no_supported_files_returns_none -x` | ❌ Wave 0 |
| FILE-03 | Folder with only unsupported files logs warning | unit | `pytest tests/test_file_selector.py::test_no_supported_files_logs_warning -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_file_selector.py -x` (fail fast on new file selector tests)
- **Per wave merge:** `pytest tests/ -v` (full suite to ensure no regressions in existing modules)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_file_selector.py` — covers FILE-01, FILE-02, FILE-03 (all phase requirements)
- [ ] Shared fixture in `tests/conftest.py` — temporary folder with mixed file types for testing

*All other test infrastructure exists:*
- pytest.ini configured
- conftest.py with shared fixtures
- pytest-mock for mocking random.choice() if needed for deterministic tests

## Sources

### Primary (HIGH confidence)
- [pathlib — Object-oriented filesystem paths](https://docs.python.org/3/library/pathlib.html) - Python 3.13 official docs, Path.iterdir(), Path.suffix, Path.is_file()
- [random — Generate pseudo-random numbers](https://docs.python.org/3/library/random.html) - Python 3.13 official docs, random.choice()
- [logging — Logging facility for Python](https://docs.python.org/3/library/logging.html) - Python 3.13 official docs, logging.getLogger()
- Existing project code: src/file_handler.py (pathlib usage), src/config/watcher.py (logging pattern), src/printer.py (supported extensions .txt, .png, .jpg, .jpeg, .bmp)

### Secondary (MEDIUM confidence)
- [Python's pathlib Module: Taming the File System – Real Python](https://realpython.com/python-pathlib/) - Verified with official docs, comprehensive pathlib tutorial
- [Random Sampling from a List in Python: random.choice, sample, choices](https://note.nkmk.me/en/python-random-choice-sample-choices/) - Verified with official docs, usage patterns
- [10 Best Practices for Logging in Python | Better Stack Community](https://betterstack.com/community/guides/logging/python/python-logging-best-practices/) - Verified project uses logging.getLogger(__name__) pattern
- [How to Get a List of All Files in a Directory With Python – Real Python](https://realpython.com/get-all-files-in-directory-python/) - Verified with official docs, iterdir() best practices

### Tertiary (LOW confidence)
- [Using Python to Select and Load a Random File - Accadius](https://www.accadius.com/using-python-to-select-and-load-a-random-file/) - Community blog, general pattern confirmed by official docs
- [Python - Loop through files of certain extensions - GeeksforGeeks](https://www.geeksforgeeks.org/python/python-loop-through-files-of-certain-extensions/) - Community tutorial, patterns verified elsewhere

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib, Python 3.4+ stable, existing project uses pathlib and logging
- Architecture: HIGH - Official Python docs, verified in existing project code (file_handler.py, config watcher)
- Pitfalls: HIGH - Documented in official docs, community consensus, observed in existing code patterns

**Research date:** 2026-03-19
**Valid until:** ~60 days (stable stdlib APIs, no fast-moving dependencies)
