---
phase: 01-print-files-from-usb-folder
plan: 03
subsystem: CLI
tags: [cli, orchestration, error-handling, tdd]

dependency_graph:
  requires:
    - file_handler.read_file (01-01)
    - printer.print_text_file (01-02)
    - printer.PrinterError (01-02)
    - file_handler.FileError (01-01)
  provides:
    - print_job.main (CLI entry point)
    - print_job.parse_args (argument parser)
  affects:
    - Future automation scripts (provides exit codes for orchestration)

tech_stack:
  added:
    - argparse (stdlib) - command-line argument parsing
  patterns:
    - TDD (Test-Driven Development) - red/green/refactor cycle
    - Exit code communication (0=success, 1=error, 130=interrupted)
    - Error-first design (catch specific errors, provide clear messages)

key_files:
  created:
    - src/print_job.py (CLI entry point, 102 lines)
    - tests/test_print_job.py (CLI tests, 156 lines)
  modified: []

decisions:
  - id: EXIT_CODES
    summary: "Use standard Unix exit codes: 0 (success), 1 (error), 2 (bad args), 130 (interrupted)"
    rationale: "Standard conventions enable future automation scripts to handle errors correctly"
    alternatives: ["Custom exit codes", "Exception propagation"]

  - id: ERROR_OUTPUT
    summary: "Print all errors to stderr, success messages to stdout"
    rationale: "Follows Unix convention - allows callers to separate error logs from output"
    alternatives: ["All to stdout", "Structured JSON output"]

  - id: VERBOSE_FLAG
    summary: "Optional --verbose flag for success confirmation"
    rationale: "Silent by default (automation-friendly), verbose for manual testing"
    alternatives: ["Always verbose", "Logging to file"]

metrics:
  duration_seconds: 172
  duration_minutes: 2
  completed_date: "2026-03-13"
  tasks_completed: 2
  files_created: 2
  files_modified: 0
  tests_added: 9
  commits: 3
---

# Phase 1 Plan 3: CLI Integration Summary

**One-liner:** Command-line interface with argparse for orchestrating file-to-printer workflow with proper error handling and exit codes.

## What Was Built

Created `src/print_job.py` CLI entry point that:
- Parses command-line arguments (filename required, --folder and --verbose optional)
- Orchestrates file reading and printing via existing modules
- Handles errors with clear messages to stderr (FileError, PrinterError, KeyboardInterrupt)
- Returns appropriate exit codes (0=success, 1=error, 2=bad args, 130=interrupted)
- Supports verbose mode for manual testing

Implemented using TDD methodology:
1. RED: Created 9 failing tests covering argument parsing, orchestration, and error paths
2. GREEN: Implemented CLI to make all tests pass
3. REFACTOR: Not needed - implementation clean on first pass

## Test Coverage

**Added 9 tests in tests/test_print_job.py:**
- Argument parsing with various flag combinations
- Main entry point orchestration with mocked printer
- Error handling for FileError, PrinterError, KeyboardInterrupt
- Exit code verification
- Stdout/stderr output validation

**Full suite status:** 23/23 tests passing across all modules
- test_file_handler.py: 6 tests ✓
- test_printer.py: 8 tests ✓
- test_print_job.py: 9 tests ✓

## Deviations from Plan

None - plan executed exactly as written. All tasks completed successfully using TDD approach as specified.

## Integration Validation

Verified integration across modules:
- `print_job.py` imports FileError from `file_handler`
- `print_job.py` imports print_text_file and PrinterError from `printer`
- `printer.py` internally calls `file_handler.read_file()`
- Error propagation works correctly through the call chain

CLI executable via:
```bash
python3 -m src.print_job receipt.txt
python3 -m src.print_job receipt.txt --verbose
python3 -m src.print_job receipt.txt --folder /custom/path
```

## Success Criteria Verification

✅ src/print_job.py implements main() and parse_args() functions
✅ argparse configured with filename (required), --folder, --verbose arguments
✅ Imports and calls print_text_file() from printer module
✅ Error handling catches FileError and PrinterError with stderr output
✅ Exit codes follow standard conventions (0, 1, 2, 130)
✅ Verbose mode prints success message when --verbose flag used
✅ Test suite covers argument parsing and error handling paths
✅ Full test suite passes (all modules integrated correctly)
✅ Script executable via `python3 -m src.print_job <filename>`

## Key Implementation Details

**Argument Parser:**
- Required positional: filename
- Optional: --folder (default: /GEN26_BILLPRINTER)
- Optional: --verbose/-v flag
- Auto-generated help text with usage examples

**Error Handling Strategy:**
- Catch specific exceptions (FileError, PrinterError, KeyboardInterrupt)
- Print clear error messages to stderr
- Return appropriate exit codes for automation
- Generic Exception catch-all for unexpected errors

**TDD Benefits:**
- Tests written first ensured complete coverage
- Mocking strategy validated without requiring hardware
- Clear specification of expected behavior
- No refactoring needed - clean implementation on first pass

## Files Modified

### Created
- `src/print_job.py` - 102 lines
  - `parse_args()` - Command-line argument parsing
  - `main()` - Entry point with error handling
  - `if __name__ == '__main__'` - Direct execution support

- `tests/test_print_job.py` - 156 lines
  - 9 test functions covering all code paths
  - Uses pytest-mock for mocking printer operations
  - Validates stdout/stderr output with capsys fixture

## Self-Check

Verifying all claimed work exists:

```bash
# Check files exist
✓ /home/admin/ducky-printer-project/src/print_job.py exists (2.7K)
✓ /home/admin/ducky-printer-project/tests/test_print_job.py exists (4.3K)

# Check commits exist
✓ 5052650 test(01-03): add failing test for CLI entry point
✓ dae94ea feat(01-03): implement CLI entry point
✓ 2491daf chore(01-03): validate full test suite integration

# Verify tests pass
✓ 23/23 tests passing (pytest tests/ -v)

# Verify CLI executable
✓ python3 -m src.print_job --help works
```

## Self-Check: PASSED

All files, commits, and functionality verified successfully.
