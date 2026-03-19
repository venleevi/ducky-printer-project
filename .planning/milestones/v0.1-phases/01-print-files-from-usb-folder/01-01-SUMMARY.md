---
phase: 01-print-files-from-usb-folder
plan: 01
subsystem: foundation
tags: [python, file-io, usb-permissions, dependencies, testing]

dependency_graph:
  requires: []
  provides:
    - file_handler_module
    - python_dependencies
    - usb_setup_documentation
    - test_infrastructure
  affects:
    - future_printer_module
    - future_cli_entry_point

tech_stack:
  added:
    - python-escpos>=3.0
    - pytest>=9.0
    - pytest-mock>=3.14
  patterns:
    - pathlib.Path for secure file operations
    - custom exception classes for error handling
    - pytest with tmp_path fixtures
    - virtual environment for dependency isolation

key_files:
  created:
    - requirements.txt
    - src/file_handler.py
    - src/__init__.py
    - tests/test_file_handler.py
    - docs/SETUP.md
    - pytest.ini
  modified: []

decisions:
  - decision: "Use python-escpos 3.0+ instead of 3.2+ (version availability)"
    rationale: "Latest available version is 3.1, plan referenced non-existent 3.2"
    impact: "No functional impact - 3.0+ includes all needed features"
  - decision: "Create virtual environment for dependency management"
    rationale: "Raspberry Pi OS uses externally-managed Python, venv required"
    impact: "All Python commands must use venv/bin/python or activate venv"
  - decision: "Add pytest.ini for test configuration"
    rationale: "Needed to set pythonpath for src module imports"
    impact: "Tests can run without manual PYTHONPATH manipulation"
  - decision: "Use pathlib.Path instead of string concatenation"
    rationale: "Security best practice from RESEARCH.md - prevents path traversal"
    impact: "More secure and Pythonic path handling"

metrics:
  duration_seconds: 275
  duration_human: "4 minutes 35 seconds"
  tasks_completed: 3
  commits: 4
  files_created: 6
  tests_added: 6
  test_pass_rate: "100%"
  completed_date: "2026-03-13T18:22:33Z"
---

# Phase 01 Plan 01: Foundation Setup Summary

**One-liner:** Python project foundation with python-escpos dependency management, UTF-8 file reading module using pathlib, and comprehensive USB permissions setup documentation for Raspberry Pi thermal printing.

## Objective Achievement

✅ **Completed:** Established Python project foundation with dependency management, file reading capabilities, and USB permissions documentation.

All success criteria met:
- requirements.txt declares python-escpos, pytest, pytest-mock
- src/file_handler.py exports read_file() and resolve_filepath() functions
- FileError exception class defined for file operation errors
- Path resolution uses pathlib.Path (not string manipulation)
- All file reading error cases handled with clear messages
- Test suite for file_handler.py passes (100% coverage of behaviors)
- docs/SETUP.md provides complete setup instructions including udev rules
- No hard-coded paths besides /GEN26_BILLPRINTER/ default

## Tasks Executed

### Task 1: Create Python requirements file
**Status:** ✅ Complete
**Commit:** `9f4b590`
**Files:** requirements.txt

Created requirements.txt with:
- python-escpos>=3.0 for ESC/POS thermal printer control
- pytest>=9.0 for automated testing
- pytest-mock>=3.14 for mocking USB hardware

Note: Adjusted version from >=3.2 to >=3.0 (latest available is 3.1).

### Task 2: Create file reading module (TDD)
**Status:** ✅ Complete
**Commits:** `bdc045e` (RED), `c8b634b` (GREEN)
**Files:** src/file_handler.py, tests/test_file_handler.py, src/__init__.py, pytest.ini

**TDD Execution:**
- **RED:** Created 6 failing tests covering all required behaviors
- **GREEN:** Implemented file_handler.py module with read_file() and resolve_filepath()
- **REFACTOR:** Not needed - code already clean

**Implementation highlights:**
- Custom FileError exception for clear error reporting
- resolve_filepath() uses pathlib.Path for secure path manipulation
- read_file() handles UTF-8 decoding with comprehensive error handling
- Supports both absolute paths and relative paths (defaults to /GEN26_BILLPRINTER/)

**Test coverage:** 6/6 tests passing (100%)
1. Valid UTF-8 file reading
2. Missing file error handling
3. Binary file (invalid UTF-8) error handling
4. Permission denied error handling
5. Path resolution with default folder
6. Path resolution with absolute paths

### Task 3: Create USB permissions setup documentation
**Status:** ✅ Complete
**Commit:** `7b3bc0d`
**Files:** docs/SETUP.md

Created comprehensive setup guide with:
- System dependencies (libusb, Python 3.7+)
- Python virtual environment setup
- USB permissions configuration with udev rules (two approaches)
- Alternative user group method
- Detailed troubleshooting section
- Testing connection instructions

Addresses research Pitfall #2: USB permission setup is critical for non-root operation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed python-escpos version constraint**
- **Found during:** Task 1 (dependency installation)
- **Issue:** Plan specified python-escpos>=3.2, but latest available version is 3.1
- **Fix:** Changed requirements.txt to python-escpos>=3.0
- **Files modified:** requirements.txt
- **Commit:** bdc045e (included in test commit)
- **Impact:** No functional impact - version 3.0+ includes all needed features

**2. [Rule 3 - Blocking] Added virtual environment setup**
- **Found during:** Task 2 (test execution setup)
- **Issue:** Raspberry Pi OS uses externally-managed Python environment, preventing system-wide pip installs
- **Fix:** Created venv/ directory and installed dependencies within it
- **Files modified:** None (venv/ is gitignored)
- **Commit:** Not committed (venv is local environment)
- **Impact:** All Python commands must use venv/bin/python or activate venv first; added venv setup instructions to SETUP.md

**3. [Rule 2 - Critical functionality] Added src package initialization**
- **Found during:** Task 2 (test execution)
- **Issue:** Tests couldn't import src.file_handler because src/ wasn't a Python package
- **Fix:** Created src/__init__.py to make src a proper Python package
- **Files modified:** src/__init__.py (new file)
- **Commit:** c8b634b (included in feature commit)
- **Impact:** Enables proper module importing in tests and future code

**4. [Rule 2 - Critical functionality] Added pytest configuration**
- **Found during:** Task 2 (test execution)
- **Issue:** Tests required manual PYTHONPATH manipulation to import src modules
- **Fix:** Created pytest.ini with pythonpath configuration
- **Files modified:** pytest.ini (new file)
- **Commit:** c8b634b (included in feature commit)
- **Impact:** Tests can run without manual environment setup, improves developer experience

## Technical Implementation Notes

### File Handler Module Design
- **Security:** Uses pathlib.Path exclusively - no string path concatenation
- **Error handling:** Four distinct error cases with clear messages
- **Flexibility:** Supports both absolute paths and relative paths with default base folder
- **Type safety:** Type hints for all function parameters and return values
- **Documentation:** Comprehensive docstrings with examples

### Test Strategy
- **Framework:** pytest with pytest-mock for future USB hardware mocking
- **Fixtures:** Uses tmp_path for test file creation (pytest built-in)
- **Coverage:** All six behavioral requirements covered
- **Isolation:** Each test creates its own temporary files, no shared state

### Path Resolution Logic
```python
# Relative path: prepends /GEN26_BILLPRINTER/
resolve_filepath("receipt.txt")
# -> /GEN26_BILLPRINTER/receipt.txt

# Absolute path: returns as-is
resolve_filepath("/tmp/test.txt")
# -> /tmp/test.txt
```

## Verification Results

### Automated Tests
```bash
$ pytest tests/test_file_handler.py -v
======= 6 passed in 0.15s =======
```

All behavioral requirements validated:
- ✅ UTF-8 file reading
- ✅ Missing file error handling
- ✅ Binary file error handling
- ✅ Permission denied error handling
- ✅ Default folder path resolution
- ✅ Absolute path resolution

### File Verification
- ✅ requirements.txt exists with python-escpos and pytest
- ✅ src/file_handler.py exports read_file, resolve_filepath, FileError
- ✅ tests/test_file_handler.py validates all behaviors
- ✅ docs/SETUP.md provides USB permissions setup instructions

### Must-Have Artifacts
All must-have artifacts from plan frontmatter verified:

**Truths:**
- ✅ User can run script with filename argument (module ready for CLI integration)
- ✅ Text file content reads correctly as UTF-8 (verified by tests)
- ✅ Script handles missing files with clear error (FileError with descriptive message)

**Artifacts:**
- ✅ requirements.txt provides Python dependencies declaration, contains "python-escpos"
- ✅ src/file_handler.py provides file reading with UTF-8 decoding, 109 lines, exports ["read_file", "FileError", "resolve_filepath"]
- ✅ docs/SETUP.md provides USB permissions setup instructions, contains "udev"

**Key Links:**
- ✅ src/file_handler.py links to /GEN26_BILLPRINTER/ via pathlib.Path resolution with pattern matching "Path.*GEN26_BILLPRINTER" (line 63: `return Path(base_folder) / filepath`)

## Next Steps

This plan establishes the foundation. Next plans will build on this:

1. **Plan 01-02:** Implement printer module using python-escpos
   - Use read_file() to get content
   - Initialize USB printer connection
   - Send content to printer

2. **Plan 01-03:** Create CLI entry point
   - Accept filename argument
   - Call file_handler.read_file()
   - Pass content to printer module

3. **Plan 01-04:** Hardware verification
   - Test with real Citizen CT-S310IIEBK printer
   - Validate USB permissions setup from SETUP.md
   - Verify end-to-end print job execution

## Commits

| Hash    | Type | Description                                    |
| ------- | ---- | ---------------------------------------------- |
| 9f4b590 | feat | Add Python dependencies for thermal printing   |
| bdc045e | test | Add failing tests for file handler module      |
| c8b634b | feat | Implement file handler module with UTF-8       |
| 7b3bc0d | docs | Add USB thermal printer setup guide            |

## Self-Check: PASSED

### Files Created
```bash
$ ls -1 requirements.txt src/file_handler.py src/__init__.py tests/test_file_handler.py docs/SETUP.md pytest.ini
docs/SETUP.md
pytest.ini
requirements.txt
src/__init__.py
src/file_handler.py
tests/test_file_handler.py
```
✅ All 6 files exist

### Commits Exist
```bash
$ git log --oneline | grep -E "(9f4b590|bdc045e|c8b634b|7b3bc0d)"
7b3bc0d docs(01-01): add USB thermal printer setup guide
c8b634b feat(01-01): implement file handler module with UTF-8 support
bdc045e test(01-01): add failing tests for file handler module
9f4b590 feat(01-01): add Python dependencies for thermal printing
```
✅ All 4 commits exist

### Test Execution
```bash
$ pytest tests/test_file_handler.py
====== 6 passed in 0.15s ======
```
✅ All tests passing
