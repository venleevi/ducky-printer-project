---
phase: 01-print-files-from-usb-folder
plan: 02
subsystem: printer-communication
tags: [printer, usb, escpos, thermal-printing, tdd]
dependency_graph:
  requires: [file-handler]
  provides: [printer-operations, usb-detection]
  affects: []
tech_stack:
  added: [pyusb, python-escpos]
  patterns: [per-job-lifecycle, class-based-usb-detection, tdd-workflow]
key_files:
  created:
    - tests/conftest.py
    - tests/test_printer.py
    - src/printer.py
  modified:
    - requirements.txt
decisions:
  - "Use USB class 7 detection instead of vendor/product IDs for printer portability"
  - "Per-job connection lifecycle (open-print-close) to prevent device busy errors"
  - "Minimal spacing: 1 blank line before content, 2 after, full paper cut"
  - "python-escpos text() method handles UTF-8 encoding automatically"
  - "Explicit pyusb dependency in requirements.txt for reliability"
metrics:
  duration_seconds: 244
  tasks_completed: 2
  tests_added: 8
  files_created: 3
  completed_date: "2026-03-13"
---

# Phase 1 Plan 2: Printer Communication Module Summary

**One-liner:** USB thermal printer communication with class-based auto-detection, per-job lifecycle management, and comprehensive test coverage using mocked hardware.

## What Was Built

Implemented core printer communication module (`src/printer.py`) with USB auto-detection, connection lifecycle management, and ESC/POS print operations. Created comprehensive test infrastructure with shared fixtures and 8 test cases covering all functionality without requiring physical hardware.

### Key Components

1. **Test Fixtures (`tests/conftest.py`):**
   - `mock_usb_device` - USB device with printer class 7 attributes
   - `mock_printer` - python-escpos Usb printer instance mock
   - `sample_text_content` - Multi-line UTF-8 receipt text
   - `temp_test_file` - Temporary file fixture with auto-cleanup

2. **Printer Module (`src/printer.py`):**
   - `PrinterError` - Custom exception for printer operations
   - `find_printer()` - USB class 7 auto-detection without hard-coded IDs
   - `print_text()` - Print text with per-job lifecycle and proper spacing
   - `print_text_file()` - Read file via file_handler and print content

3. **Test Suite (`tests/test_printer.py`):**
   - 8 comprehensive tests covering detection, printing, error handling
   - All tests use mocked USB hardware (no physical printer required)
   - TDD workflow: RED (failing tests), GREEN (implementation), verified

## Implementation Details

### USB Auto-Detection Strategy

Used USB device class 7 (printer class) matching instead of vendor/product IDs:
- Checks both device-level and interface-level class descriptors
- Works across multiple thermal printer models
- More robust to device changes and power cycles
- Implemented as custom match function passed to python-escpos

### Connection Lifecycle

Per-job lifecycle (open-print-close for each print operation):
- Opens connection at start of each print job
- Performs print sequence: feed(1) → text() → feed(2) → cut() → close()
- Always closes connection in finally block (even on errors)
- Prevents "device busy" errors after USB reconnects or power cycles

### Print Formatting

Minimal spacing and full paper cut:
- 1 blank line at top (clean start)
- Print content as-is (UTF-8 via python-escpos MagicEncode)
- 2 blank lines at bottom (separation)
- Full paper cut using ESC/POS command (mode='FULL')

### Error Handling

- USB errors caught and converted to `PrinterError` with descriptive messages
- Connection always closed in finally block to prevent resource leaks
- FileError from file_handler propagates to caller for proper error context

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Missing Dependency] pyusb not installed**
- **Found during:** Task 2 GREEN phase - tests failing with import error
- **Issue:** python-escpos dependency pyusb was not installed automatically
- **Fix:** Installed pyusb via pip, then explicitly added to requirements.txt
- **Files modified:** requirements.txt
- **Commit:** 70c7486

**2. [Rule 1 - Bug] Test USBError mocking broken**
- **Found during:** Task 2 GREEN phase - test failing with TypeError
- **Issue:** Test tried to set `__name__` on immutable Exception class
- **Fix:** Created proper USBError class in test and used it for mocking
- **Files modified:** tests/test_printer.py
- **Commit:** 5199285 (part of GREEN phase commit)

## Testing Coverage

All 8 tests passing without physical hardware:

1. ✅ find_printer() returns printer when USB class 7 device found
2. ✅ find_printer() raises PrinterError when no device found
3. ✅ print_text() executes correct operation sequence
4. ✅ print_text() adds 1 blank line before content
5. ✅ print_text() adds 2 blank lines after content
6. ✅ print_text() closes connection on USB error
7. ✅ Per-job lifecycle: each print opens and closes connection
8. ✅ print_text_file() reads file and prints content

## Integration Points

- **File Handler:** Imports `read_file()` from `src.file_handler` for UTF-8 file reading
- **USB Subsystem:** Uses `usb.core` for device detection via custom match function
- **ESC/POS Library:** Uses `escpos.printer.Usb` for printer communication and commands

## Files Modified

### Created
- `tests/conftest.py` (98 lines) - Shared test fixtures for printer testing
- `tests/test_printer.py` (151 lines) - Comprehensive test suite with 8 tests
- `src/printer.py` (155 lines) - Printer communication module with USB detection

### Modified
- `requirements.txt` - Added explicit pyusb>=1.0 dependency

## Success Criteria Verification

- ✅ src/printer.py exports find_printer(), print_text(), print_text_file(), PrinterError
- ✅ USB printer auto-detection uses class 7 matching (not hard-coded IDs)
- ✅ Per-job connection lifecycle: each print opens and closes connection
- ✅ Print operations include 1 blank line before, 2 after, full paper cut
- ✅ python-escpos text() method used for UTF-8 handling (not manual conversion)
- ✅ Error handling closes connection in finally block
- ✅ Test suite validates all behaviors with mocked USB hardware
- ✅ tests/conftest.py provides reusable fixtures for printer tests
- ✅ No direct dependency on physical printer for tests

## Next Steps

Plan 01-03 will integrate this printer module into a CLI entry point and create a comprehensive end-to-end test suite that validates the complete workflow from command-line arguments to print operations.

## Self-Check

Verifying all claimed files and commits exist:

### Files Check
- ✅ FOUND: tests/conftest.py
- ✅ FOUND: tests/test_printer.py
- ✅ FOUND: src/printer.py

### Commits Check
- ✅ FOUND: 9891c5f (feat: shared test fixtures)
- ✅ FOUND: 2f7f813 (test: failing tests for printer module)
- ✅ FOUND: 5199285 (feat: printer module implementation)
- ✅ FOUND: 70c7486 (fix: pyusb dependency)

## Self-Check: PASSED

All claimed files exist on disk and all commits are present in git history.
