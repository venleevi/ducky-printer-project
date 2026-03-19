---
phase: 01-print-files-from-usb-folder
plan: 04
subsystem: Hardware Verification
tags: [hardware, verification, thermal-printer, image-support]

dependency_graph:
  requires:
    - src/print_job.py (01-03)
    - src/printer.py (01-02)
    - src/file_handler.py (01-01)
  provides:
    - Verified hardware compatibility (Citizen CT-S310IIEBK)
    - Image printing capability (PNG, JPG, BMP)
    - Production-ready print script
  affects:
    - All future printing operations rely on verified hardware setup

tech_stack:
  added:
    - python-escpos image printing (via PIL/Pillow)
    - USB endpoint configuration (in_ep=0x81, out_ep=0x02)
  patterns:
    - Per-job connection lifecycle (open-print-close)
    - File type auto-detection (extension-based routing)
    - Hardware-specific USB endpoint configuration

key_files:
  created: []
  modified:
    - src/printer.py (+116 lines: print_image, print_file functions)
    - src/print_job.py (+20 lines: updated help text for image support)
    - tests/test_print_job.py (+20 lines: updated tests for print_file)

decisions:
  - id: IMAGE_SUPPORT
    summary: "Extended print script to support PNG/JPG/BMP images alongside text files"
    rationale: "Real-world folder contains PNG files (wish1.png, test_variation1.png) that need printing"
    alternatives: ["Text-only (reject images)", "Separate image print script"]

  - id: USB_ENDPOINTS
    summary: "Explicitly configure USB endpoints (in_ep=0x81, out_ep=0x02)"
    rationale: "Citizen CT-S310IIEBK requires explicit endpoint configuration to avoid 'Invalid endpoint address' error"
    alternatives: ["Auto-detect endpoints", "Try multiple endpoint combinations"]

  - id: API_CORRECTION
    summary: "Changed feed() to ln() for line feeds with python-escpos Usb class"
    rationale: "Usb printer objects use ln() method, not feed() - API documentation mismatch"
    alternatives: ["Use different escpos library", "Use raw ESC/POS commands"]

metrics:
  duration_seconds: 962
  duration_minutes: 16
  completed_date: "2026-03-13"
  tasks_completed: 2
  files_created: 0
  files_modified: 3
  commits: 2
---

# Phase 1 Plan 4: Hardware Verification Summary

**One-liner:** Verified thermal printer hardware with real Citizen CT-S310IIEBK printer, extended support for image files (PNG/JPG/BMP), fixed python-escpos API issues.

## What Was Built

Hardware verification completed with extended functionality:

**Task 1: Setup dependencies and USB permissions**
- System dependencies installed (libusb-1.0-0, python3-pip)
- Python dependencies installed (python-escpos, pytest, pytest-mock, pyusb, Pillow)
- USB permissions configured (user added to lp group)
- Printer detected successfully: Citizen Thermal Printer (ID 1d90:2060)

**Task 2: Hardware verification testing**
- Discovered real-world folder contains image files (PNG) alongside text
- Extended printer module to support image printing
- Fixed python-escpos API issues (feed→ln, explicit USB endpoints)
- Verified all functionality with real hardware printing

**Extended Support Added:**
- Original plan: Text files only (.txt)
- Extended: Text + images (.txt, .png, .jpg, .jpeg, .bmp)
- Added `print_image()` function using python-escpos image() method
- Added `print_file()` auto-detection function (routes by extension)
- Updated CLI help text to document image support

## Hardware Test Results

All verification tests PASSED:

**✓ Text file printing:**
- Created test-receipt.txt with UTF-8 café character
- Printed successfully with correct formatting
- Auto-cut worked (full paper cut)
- UTF-8 characters rendered correctly

**✓ Image file printing:**
- test_variation1.png: Printed successfully (centered, scaled for receipt width)
- wish1.png: Printed successfully (centered, scaled for receipt width)
- Both images printed with good quality on thermal paper

**✓ Error handling:**
- Missing file: Correct error message and exit code 1
- Printer offline: Detected USB error and returned exit code 1
- Unsupported file type: Clear error message for non-.txt/.png/.jpg files

**✓ Exit codes:**
- Success cases: Exit code 0
- Error cases: Exit code 1
- All as expected

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Added image printing support**
- **Found during:** Task 2 (hardware verification testing)
- **Issue:** Real USB folder (/media/admin/KINGSTON/GEN26_BILLPRINTER/) contains PNG files that need printing. Original implementation only supported text files.
- **Fix:** Extended printer module with print_image() function and print_file() dispatcher
- **Files modified:** src/printer.py (+116 lines), src/print_job.py (+20 lines), tests/test_print_job.py (+20 lines)
- **Commit:** 0608184 feat(01-04): add image printing support for PNG/JPG files

**2. [Rule 1 - Bug] Fixed python-escpos API usage**
- **Found during:** Task 2 (initial hardware print attempt)
- **Issue:** Code used feed() method but Usb printer objects don't have feed() - caused AttributeError
- **Fix:** Changed all feed() calls to ln() (correct API for Usb class)
- **Files modified:** src/printer.py (11 lines changed)
- **Commit:** 01aaf7b fix(01-04): correct python-escpos API and USB endpoints

**3. [Rule 1 - Bug] Added explicit USB endpoint configuration**
- **Found during:** Task 2 (hardware print attempt)
- **Issue:** "Invalid endpoint address" error with Citizen CT-S310IIEBK
- **Fix:** Added explicit in_ep=0x81, out_ep=0x02 to Usb() constructor
- **Files modified:** src/printer.py (20 lines changed)
- **Commit:** 01aaf7b fix(01-04): correct python-escpos API and USB endpoints

## Test Coverage

**Final test suite status:** 23/23 tests passing
- test_file_handler.py: 6 tests ✓
- test_printer.py: 8 tests ✓
- test_print_job.py: 9 tests ✓

**Updated tests:**
- Modified test_print_job.py to use new print_file() function
- All tests now route through print_file() dispatcher (matches CLI behavior)

## Success Criteria Verification

✅ System dependencies installed (libusb-1.0-0)
✅ Python dependencies installed (python-escpos, pytest)
✅ USB permissions configured for non-root access
✅ Printer auto-detected via USB class 7 matching
✅ Test receipt prints with correct content and formatting
✅ Paper cuts automatically after print job (full cut)
✅ UTF-8 text renders correctly (café character prints properly)
✅ Missing file error handled gracefully
✅ Printer offline error handled gracefully
✅ Exit codes correct (0=success, 1=error)
✅ Script ready for production use on Raspberry Pi
✅ **BONUS:** Image printing support for PNG/JPG/BMP files

## Key Implementation Details

**Hardware Configuration:**
- Printer: Citizen CT-S310IIEBK Thermal Receipt Printer
- USB ID: 1d90:2060
- Connection: USB bulk endpoints (IN=0x81, OUT=0x02)
- Permissions: User added to lp group (alternative to udev rules)

**Image Printing:**
- Uses python-escpos image() method with PIL/Pillow
- Automatic scaling to fit receipt paper width
- Centered alignment for professional appearance
- bitImageColumn implementation (most compatible with thermal printers)
- Same spacing and cut behavior as text printing

**File Type Routing:**
```python
def print_file(filename, base_folder):
    extension = file_path.suffix.lower()
    if extension == '.txt':
        return print_text_file(filename, base_folder)
    elif extension in ['.png', '.jpg', '.jpeg', '.bmp']:
        return print_image(str(file_path))
    else:
        raise ValueError(f"Unsupported file type: {extension}")
```

**API Corrections:**
- Before: `printer.feed(1)` → AttributeError
- After: `printer.ln(1)` → Works correctly
- Reason: Usb class API uses ln() not feed()

**USB Endpoint Configuration:**
- Before: `Usb(usb_args={'custom_match': match_printer_class})`
- After: `Usb(usb_args={'custom_match': match_printer_class}, in_ep=0x81, out_ep=0x02)`
- Reason: Some thermal printers require explicit endpoint specification

## Files Modified

### Modified (3 files)

**src/printer.py** (+116 lines)
- Added `print_image(image_path)` function for PNG/JPG/BMP printing
- Added `print_file(filename, base_folder)` dispatcher function
- Fixed API usage: feed() → ln()
- Added explicit USB endpoint configuration (in_ep, out_ep)

**src/print_job.py** (+20 lines)
- Updated help text to document image file support
- Updated epilog examples to show image printing
- Changed to call print_file() instead of print_text_file()
- Added ValueError exception handler for unsupported file types

**tests/test_print_job.py** (+20 lines)
- Updated mocks to use print_file instead of print_text_file
- All tests now route through print_file() dispatcher
- Tests still pass (23/23) with new architecture

## Production Readiness

The print script is now production-ready:
- ✅ Verified with real hardware (Citizen CT-S310IIEBK)
- ✅ USB permissions configured correctly
- ✅ Supports both text and image files
- ✅ Error handling tested and working
- ✅ UTF-8 character support confirmed
- ✅ Auto-cut working correctly
- ✅ Exit codes proper for automation
- ✅ All automated tests passing

**Ready for:**
- File monitoring automation (watch /GEN26_BILLPRINTER/ for new files)
- Batch printing operations
- Integration with upstream systems

## Self-Check

Verifying all claimed work exists:

```bash
# Check modified files exist and have expected content
✓ src/printer.py exists (8.0K, contains print_image and print_file functions)
✓ src/print_job.py exists (2.9K, updated help text)
✓ tests/test_print_job.py exists (4.3K, uses print_file mocking)

# Check commits exist
✓ 0608184 feat(01-04): add image printing support for PNG/JPG files
✓ 01aaf7b fix(01-04): correct python-escpos API and USB endpoints

# Verify functionality
✓ Test suite passes (23/23 tests)
✓ Hardware printing verified (text and images)
✓ Error handling verified (missing files, printer offline)
✓ Exit codes correct (0 for success, 1 for errors)

# Hardware verification
✓ Printer detected: Citizen Thermal Printer (ID 1d90:2060)
✓ Text printing working (test-receipt.txt)
✓ Image printing working (test_variation1.png, wish1.png)
✓ UTF-8 rendering working (café character prints correctly)
```

## Self-Check: PASSED

All files, commits, functionality, and hardware tests verified successfully.
