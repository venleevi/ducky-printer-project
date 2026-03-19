# Phase 1: Print files from USB folder - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Build core Python script to print files from `/GEN26_BILLPRINTER/` USB folder to Citizen CT-S310IIEBK thermal printer via USB. Script runs on-demand (not as daemon), accepts filename as argument, and outputs to printer. File management and triggering logic handled externally.

</domain>

<decisions>
## Implementation Decisions

### Printer Communication Library
- Use **python-escpos** - High-level thermal printer library with ESC/POS command support
- Auto-detect USB printer connection (no hard-coded vendor/product IDs)
- Reconnect per job (open connection, print, close) - more robust for power cycles and USB reconnects
- Reset printer and apply standard settings on each connection (codepage CP437, enable auto-status)

### File Handling Approach
- **On-demand execution** - Script runs once when triggered, prints specified file, then exits
- Accept specific filename via command-line argument (e.g., `python print.py receipt.txt`)
- Assume file is in `/GEN26_BILLPRINTER/` folder unless full path provided
- Leave files unchanged after printing - no deletion or moving (caller handles cleanup)
- Support **.txt files minimum** - check actual folder contents for other file types to support
- Future: External process will trigger script based on selected file

### Print Formatting
- **Raw text pass-through** - Print file content exactly as-is, no processing or reformatting
- Assume **UTF-8 encoding** for text files
- **Full cut** paper after each print job (activate CT-S310IIEBK auto-cutter)
- Minimal spacing - 1-2 blank lines at top and bottom for clean receipts

### Claude's Discretion
- Error handling strategy (retry logic, error messages, exit codes)
- Logging approach (file vs console vs both)
- Handling of missing files, printer offline, or corrupted files
- Paper width assumptions and character limit handling

</decisions>

<specifics>
## Specific Ideas

- User note: "For now print only on demand as a script. Later on a process will be created to trigger the printing process based on selected file"
- User note: "Check the contents of the folder. At least txt needs to be supported and any file types in given folder"
- Platform: Raspberry Pi 3B+ (ARM architecture) - ensure python-escpos compatible
- Printer model: Citizen CT-S310IIEBK with auto-cutter feature
- Target folder: `/GEN26_BILLPRINTER/` on USB-mounted stick

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- None - Fresh project with no existing Python code
- GSD framework available for workflow management

### Established Patterns
- Python-focused project (per .gitignore configuration)
- No established patterns yet - first code to be written

### Integration Points
- USB subsystem on Raspberry Pi (udev rules may be needed for printer permissions)
- File system access to USB stick mount point
- Command-line argument parsing (argparse or sys.argv)

</code_context>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope. Future trigger process mentioned but outside POC scope.

</deferred>

---

*Phase: 01-print-files-from-usb-folder*
*Context gathered: 2026-03-13*
