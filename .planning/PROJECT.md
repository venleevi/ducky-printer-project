# Thermal Printer POC

**Platform:** Raspberry Pi 3B+
**Printer:** Citizen CT-S310IIEBK (USB)
**Language:** Python

## Current State

**Version:** v0.1.0 (POC) — shipped 2026-03-13

**What's Built:**
- Command-line print script for text and image files
- USB thermal printer auto-detection and communication
- File reading from USB stick folder (`/GEN26_BILLPRINTER/`)
- Hardware-verified with Citizen CT-S310IIEBK printer

**Tech Stack:**
- Python 3.13 with python-escpos library
- 969 lines of code (src + tests)
- 23 automated tests (100% passing)
- USB class 7 detection for printer portability

**Known Issues:**
- 3/23 tests have mock mismatches (feed vs ln) — functionality works, tests need updating

## Vision

Proof of concept for automated thermal receipt printing from files stored on a USB stick. The system should detect print jobs in the `/GEN26_BILLPRINTER/` folder and print them on demand using the connected thermal printer.

## Success Criteria

### Validated (v0.1.0)

- ✅ Successfully communicate with Citizen CT-S310IIEBK via USB — verified with real hardware
- ✅ Read files from USB stick folder `/GEN26_BILLPRINTER/` — supports text (.txt) and images (.png, .jpg, .bmp)
- ✅ Print file contents to thermal printer — UTF-8 text and images both working
- ✅ Handle basic error cases (printer offline, no files, etc.) — clear error messages, proper exit codes

### Next Milestone Goals

*(To be defined in next milestone planning)*

## Key Decisions

| Decision | Rationale | Outcome | Status |
|----------|-----------|---------|--------|
| USB class 7 detection instead of vendor/product IDs | Works across multiple printer models | Citizen CT-S310IIEBK detected successfully | ✓ Good |
| Per-job connection lifecycle (open-print-close) | Prevents device busy errors after power cycles | No connection issues observed | ✓ Good |
| Extended to support images (PNG/JPG/BMP) | Real USB folder contained image files needing printing | Both text and images print successfully | ✓ Good |
| Explicit USB endpoints (in_ep=0x81, out_ep=0x02) | Required for Citizen CT-S310IIEBK compatibility | Fixed "Invalid endpoint address" error | ✓ Good |
| File type auto-detection by extension | Simple routing for text vs images | Clean separation of concerns | ✓ Good |

## Constraints

- Must run on Raspberry Pi 3B+ (ARM architecture)
- Python-based solution
- USB connectivity only

---

*Last updated: 2026-03-13 after v0.1 milestone*
