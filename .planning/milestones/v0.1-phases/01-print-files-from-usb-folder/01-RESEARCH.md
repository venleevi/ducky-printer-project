# Phase 1: Print files from USB folder - Research

**Researched:** 2026-03-13
**Domain:** Python thermal printing with ESC/POS via USB on Raspberry Pi
**Confidence:** MEDIUM-HIGH

## Summary

Phase 1 implements a command-line Python script to print files from `/GEN26_BILLPRINTER/` USB folder to a Citizen CT-S310IIEBK thermal printer via USB. The script uses **python-escpos** library for ESC/POS communication, auto-detects the USB printer, reads text files with UTF-8 encoding, and performs full paper cuts after printing. The script is designed for on-demand execution (not as a daemon), accepting a filename argument and exiting after printing.

The Citizen CT-S310IIEBK is an 80mm thermal receipt printer (203 dpi, 160mm/sec) with built-in auto-cutter, USB/Serial interfaces, and full ESC/POS compatibility. The printer supports standard ESC/POS commands for text printing, paper cutting, and configuration.

**Primary recommendation:** Use python-escpos 3.x with USB auto-detection via printer class matching, implement per-job connection lifecycle (open-print-close), handle UTF-8 text via the library's MagicEncode helper, use argparse for CLI argument parsing, and implement proper USB permission setup via udev rules. Focus initial implementation on .txt file support, then extend to other formats found in the USB folder.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Printer Communication Library:**
- Use **python-escpos** - High-level thermal printer library with ESC/POS command support
- Auto-detect USB printer connection (no hard-coded vendor/product IDs)
- Reconnect per job (open connection, print, close) - more robust for power cycles and USB reconnects
- Reset printer and apply standard settings on each connection (codepage CP437, enable auto-status)

**File Handling Approach:**
- **On-demand execution** - Script runs once when triggered, prints specified file, then exits
- Accept specific filename via command-line argument (e.g., `python print.py receipt.txt`)
- Assume file is in `/GEN26_BILLPRINTER/` folder unless full path provided
- Leave files unchanged after printing - no deletion or moving (caller handles cleanup)
- Support **.txt files minimum** - check actual folder contents for other file types to support
- Future: External process will trigger script based on selected file

**Print Formatting:**
- **Raw text pass-through** - Print file content exactly as-is, no processing or reformatting
- Assume **UTF-8 encoding** for text files
- **Full cut** paper after each print job (activate CT-S310IIEBK auto-cutter)
- Minimal spacing - 1-2 blank lines at top and bottom for clean receipts

### Claude's Discretion

- Error handling strategy (retry logic, error messages, exit codes)
- Logging approach (file vs console vs both)
- Handling of missing files, printer offline, or corrupted files
- Paper width assumptions and character limit handling

### Deferred Ideas (OUT OF SCOPE)

None - discussion stayed within phase scope. Future trigger process mentioned but outside POC scope.
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-escpos | 3.x (latest: 3.2+) | ESC/POS thermal printer control | De facto standard Python library for ESC/POS printers, actively maintained, comprehensive feature set, supports USB/Serial/Network |
| pyusb | 1.2.x+ | USB device communication (python-escpos dependency) | Standard Python USB library using libusb, required for USB printer detection and communication |
| Pillow (PIL) | 10.x+ | Image processing (python-escpos dependency) | Required by python-escpos for image printing capabilities, even if not immediately used |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| argparse | stdlib | Command-line argument parsing | Built-in, modern, auto-generates help, type validation |
| pathlib | stdlib | Path manipulation | Safer than string concatenation, cross-platform compatibility |
| logging | stdlib | Structured logging | Better than print() for production scripts, configurable output levels |

### System Dependencies
| Package | Purpose | Installation |
|---------|---------|--------------|
| libusb-1.0-0 | USB device access library | `sudo apt-get install libusb-1.0-0` |
| udev | USB device permissions | Pre-installed on Raspberry Pi OS |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-escpos | python-printer-escpos | Older fork, less maintained, different API - stick with python-escpos |
| python-escpos | PyESCPOS | Lower-level, less hardware abstraction - python-escpos is more user-friendly |
| argparse | click/typer | Third-party dependencies for simple single-command script - argparse sufficient |

**Installation:**
```bash
# System dependencies (Raspberry Pi OS)
sudo apt-get update
sudo apt-get install -y libusb-1.0-0

# Python packages
pip install python-escpos
# Dependencies (pyusb, Pillow) installed automatically
```

## Architecture Patterns

### Recommended Project Structure
```
ducky-printer-project/
├── src/
│   ├── print_job.py         # Main script - CLI entry point
│   ├── printer.py           # Printer connection and operations
│   └── file_handler.py      # File reading and validation
├── tests/
│   ├── test_print_job.py    # CLI argument handling tests
│   ├── test_printer.py      # Printer operations tests (mocked)
│   └── test_file_handler.py # File operations tests
├── requirements.txt         # Python dependencies
└── README.md                # Setup and usage instructions
```

### Pattern 1: CLI Script with Argparse
**What:** Single-purpose command-line script with structured argument parsing
**When to use:** On-demand execution scripts that accept parameters

**Example:**
```python
# Source: argparse best practices 2026
import argparse
import sys
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description='Print files from USB folder to thermal printer',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'filename',
        type=str,
        help='File to print (e.g., receipt.txt)'
    )
    parser.add_argument(
        '--folder',
        type=Path,
        default=Path('/GEN26_BILLPRINTER'),
        help='Base folder path (default: /GEN26_BILLPRINTER)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    return parser.parse_args()

def main():
    args = parse_args()
    # Implementation...

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

### Pattern 2: Per-Job Connection Lifecycle
**What:** Open connection, perform operation, close connection - no persistent state
**When to use:** Scripts that run once per job, need robustness against power cycles

**Example:**
```python
# Source: python-escpos documentation patterns
from escpos.printer import Usb
import usb.core

def print_file(filepath, content):
    """Print file with per-job connection lifecycle."""
    printer = None
    try:
        # Auto-detect USB printer by class (class 7 = printer)
        def match_printer(device):
            if device.bDeviceClass == 7:
                return True
            for cfg in device:
                for intf in cfg:
                    if intf.bInterfaceClass == 7:
                        return True
            return False

        printer = Usb(usb_args={'custom_match': match_printer})
        printer.open()

        # Reset and configure printer
        # Note: python-escpos handles encoding via MagicEncode
        printer.text(content)
        printer.feed(2)  # 2 blank lines
        printer.cut(mode='FULL')  # Full paper cut

        printer.close()
        return 0

    except usb.core.USBError as e:
        if printer:
            printer.close()
        raise PrinterError(f"USB error: {e}")
    except Exception as e:
        if printer:
            printer.close()
        raise
```

### Pattern 3: Exit Code Communication
**What:** Use standard exit codes to communicate script status
**When to use:** CLI scripts that may be called by other processes

**Exit codes:**
- `0` - Success
- `1` - General error (file not found, printer error, etc.)
- `2` - Invalid command-line arguments (argparse default)
- `130` - Script interrupted (SIGINT/Ctrl+C)

### Anti-Patterns to Avoid

- **Hard-coded vendor/product IDs:** USB IDs can change between printer models or revisions. Use class-based matching or device enumeration instead.
- **Persistent connections:** Keeping USB printer connection open between jobs leads to "device busy" errors after power cycles. Always open-print-close.
- **Direct UTF-8 to printer:** Thermal printers use legacy codepages (CP437, etc.), not UTF-8. Let python-escpos handle encoding via MagicEncode.
- **Silent failures:** Always provide clear error messages and appropriate exit codes for automation and debugging.
- **String path manipulation:** Use `pathlib.Path` for path operations to avoid security issues and cross-platform bugs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| USB printer detection | Custom pyusb scanning and filtering | python-escpos Usb class with custom_match | Handles endpoint detection, interface claiming, error recovery |
| ESC/POS command encoding | Raw byte sequences for printer commands | python-escpos methods (text(), cut(), feed()) | Commands vary by printer model, library handles compatibility |
| Character encoding | Manual codepage conversion | python-escpos MagicEncode (automatic) | Complex mapping between UTF-8 and printer codepages, library handles automatically |
| USB permissions | chmod/chown on device files | udev rules | Device files are recreated on reconnect, udev rules persist |
| Retry logic for USB | Custom retry loops with sleep | Let caller handle retries, fail fast with clear errors | Script is single-job, caller can implement retry policy |

**Key insight:** Thermal printers have significant complexity hidden beneath simple "print text" operations. ESC/POS commands, USB endpoint discovery, codepage handling, and auto-cutter commands all have edge cases that python-escpos already handles. Use the library's abstractions rather than dropping to raw pyusb or byte sequences.

## Common Pitfalls

### Pitfall 1: UTF-8 Character Encoding Issues
**What goes wrong:** Printing UTF-8 text directly produces garbage characters or CharCodeError exceptions for special characters (accents, symbols, non-Latin scripts).

**Why it happens:** Thermal printers use legacy codepages (CP437, CP850, etc.) from the DOS era, not modern UTF-8. Direct UTF-8 bytes are interpreted as codepage characters, producing wrong output.

**How to avoid:** Let python-escpos handle encoding automatically via MagicEncode. The library automatically switches codepages to encode Unicode characters based on printer capabilities. For unsupported characters, fall back to rendering text as an image if needed (future enhancement).

**Warning signs:** Special characters print as boxes, question marks, or wrong symbols; CharCodeError exceptions; foreign language text unreadable.

### Pitfall 2: USB Permission Denied Errors
**What goes wrong:** Script fails with "Permission denied" or "Access denied" USB errors, even though printer works with other tools.

**Why it happens:** By default, USB devices are owned by root. Python script running as regular user cannot access the device.

**How to avoid:**
1. Create udev rule in `/etc/udev/rules.d/99-thermal-printer.rules`:
   ```
   SUBSYSTEM=="usb", ATTR{idVendor}=="XXXX", ATTR{idProduct}=="YYYY", MODE="0666"
   ```
   (Replace XXXX/YYYY with actual vendor/product IDs from `lsusb`)
2. Alternative: Add user to `lp` (line printer) group: `sudo usermod -aG lp $USER`
3. Reload udev: `sudo udevadm control --reload-rules && sudo udevadm trigger`
4. Reconnect printer (unplug/replug USB)

**Warning signs:** USBError with "Access denied", script works with sudo but not as regular user, permissions error in logs.

### Pitfall 3: Invalid Endpoint Address Error
**What goes wrong:** Script crashes with "ValueError: Invalid endpoint address 0x1" when initializing USB connection.

**Why it happens:** python-escpos defaults for in_ep/out_ep don't match printer's actual USB endpoints. Different printer models use different endpoint addresses.

**How to avoid:** Explicitly set endpoints when creating Usb object:
```python
printer = Usb(
    usb_args={'custom_match': match_printer},
    in_ep=0x82,   # Common: 0x81, 0x82
    out_ep=0x01   # Common: 0x01, 0x02
)
```
Use `lsusb -v` to find actual endpoint addresses for the specific printer model.

**Warning signs:** ValueError mentioning endpoint address, connection failures with valid vendor/product IDs, works on some systems but not others.

### Pitfall 4: Printer State Persists Between Jobs
**What goes wrong:** Second print job has wrong formatting (alignment, font size) even though script sets it correctly. Print output varies based on previous jobs.

**Why it happens:** Thermal printers maintain state (alignment, character size, codepage) between jobs unless explicitly reset. Previous job's settings affect next job.

**How to avoid:** Always reset printer state at start of each job. However, python-escpos doesn't have an explicit reset() method in current versions. As workaround:
1. Set all formatting explicitly (don't rely on defaults)
2. Consider sending ESC @ (initialize printer) command via `_raw()` method
3. Document assumption that printer starts in default state

**Warning signs:** Inconsistent output between runs, formatting depends on previous jobs, printer "remembers" settings.

### Pitfall 5: Paper Width Character Limit Assumptions
**What goes wrong:** Text gets cut off mid-line or wrapped unexpectedly because lines exceed printer's character width.

**Why it happens:** 80mm thermal printers typically support 48 characters per line in normal font, but this varies by font size, printer model, and character width settings.

**How to avoid:**
1. For Phase 1 (raw text pass-through), document that files should be pre-formatted for 48 characters/line
2. Don't auto-wrap or truncate in script - print exactly as provided
3. Future enhancement: Add line length validation or auto-wrapping as separate feature

**Warning signs:** Lines wrap unexpectedly, text cut off at right edge, receipt looks poorly formatted.

### Pitfall 6: File Reading Without Error Handling
**What goes wrong:** Script crashes with unhandled exceptions when file doesn't exist, is binary, has wrong encoding, or is unreadable.

**Why it happens:** Filesystem operations and file decoding can fail in many ways. Python's default exception handling isn't user-friendly for CLI scripts.

**How to avoid:** Wrap file operations in try/except with clear error messages:
```python
def read_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileError(f"File not found: {filepath}")
    except UnicodeDecodeError:
        raise FileError(f"File is not valid UTF-8 text: {filepath}")
    except PermissionError:
        raise FileError(f"Permission denied reading file: {filepath}")
    except Exception as e:
        raise FileError(f"Error reading file {filepath}: {e}")
```

**Warning signs:** Cryptic Python tracebacks, script crashes instead of exiting gracefully, no indication of what went wrong.

### Pitfall 7: Raspberry Pi ARM Compatibility Issues
**What goes wrong:** python-escpos or dependencies fail to install or crash with "Illegal instruction" on Raspberry Pi, especially older models.

**Why it happens:** Some binary dependencies (PIL/Pillow) may not have ARM builds or require compilation. Raspberry Pi Zero (ARMv6) has known compatibility issues.

**How to avoid:**
1. Use Raspberry Pi 3B+ or newer (ARMv7/ARMv8) - better binary package support
2. Install system packages before pip: `sudo apt-get install python3-pil libusb-1.0-0`
3. Use OS-provided packages when available: `sudo apt-get install python3-usb`
4. Test installation on actual hardware early

**Warning signs:** "Illegal instruction" errors, segfaults, pip installation failures, missing binary packages.

## Code Examples

Verified patterns from official sources:

### USB Printer Auto-Detection Without Vendor ID
```python
# Source: python-escpos USB documentation + pyusb custom_match pattern
from escpos.printer import Usb
import usb.core

def find_and_connect_printer():
    """Auto-detect USB thermal printer by device class."""

    # Match function: finds devices with printer class (7)
    def match_printer_class(device):
        # Check device-level class
        if device.bDeviceClass == 7:
            return True
        # Check interface descriptors
        try:
            for cfg in device:
                for intf in cfg:
                    if intf.bInterfaceClass == 7:
                        return True
        except:
            pass
        return False

    # Create printer with custom match function
    printer = Usb(usb_args={'custom_match': match_printer_class})
    return printer
```

### Full Print Job Flow
```python
# Source: python-escpos usage patterns
from escpos.printer import Usb
from pathlib import Path

def print_text_file(filename, base_folder='/GEN26_BILLPRINTER'):
    """Complete print job: read file, connect printer, print, cleanup."""

    # Build file path
    filepath = Path(base_folder) / filename

    # Read file
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        raise FileError(f"File not found: {filepath}")
    except UnicodeDecodeError:
        raise FileError(f"File is not valid UTF-8: {filepath}")

    # Connect to printer
    printer = find_and_connect_printer()

    try:
        printer.open()

        # Add top spacing (1-2 blank lines)
        printer.feed(1)

        # Print content (python-escpos handles encoding)
        printer.text(content)

        # Add bottom spacing
        printer.feed(2)

        # Full paper cut
        printer.cut(mode='FULL')

        printer.close()
        return 0

    except Exception as e:
        if printer:
            try:
                printer.close()
            except:
                pass
        raise PrinterError(f"Printer error: {e}")
```

### Error-Handling CLI Entry Point
```python
# Source: Python argparse + exit code best practices
import sys
import argparse
from pathlib import Path

class PrinterError(Exception):
    """Printer communication errors."""
    pass

class FileError(Exception):
    """File reading/validation errors."""
    pass

def parse_args():
    parser = argparse.ArgumentParser(
        description='Print text files to thermal receipt printer',
        epilog='Example: python print_job.py receipt.txt'
    )
    parser.add_argument('filename', help='File to print (in /GEN26_BILLPRINTER/)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    return parser.parse_args()

def main():
    args = parse_args()

    try:
        print_text_file(args.filename)
        if args.verbose:
            print(f"Successfully printed: {args.filename}")
        return 0

    except FileError as e:
        print(f"File error: {e}", file=sys.stderr)
        return 1
    except PrinterError as e:
        print(f"Printer error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

### udev Rule for USB Printer Permissions
```bash
# Source: Raspberry Pi USB permissions best practices
# File: /etc/udev/rules.d/99-thermal-printer.rules

# Find vendor/product ID with: lsusb
# Example output: Bus 001 Device 005: ID 2730:0fff Citizen Systems

# Generic rule for all printers (by USB class)
SUBSYSTEM=="usb", ATTR{bInterfaceClass}=="07", MODE="0666"

# Or specific rule for Citizen CT-S310IIEBK
# SUBSYSTEM=="usb", ATTR{idVendor}=="2730", ATTR{idProduct}=="0fff", MODE="0666"

# Apply rules:
# sudo udevadm control --reload-rules && sudo udevadm trigger
# Then reconnect printer
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-printer-escpos fork | python-escpos (maintained) | ~2016-2017 | Use python-escpos from PyPI, not older forks |
| Manual vendor/product ID lookup | USB class-based detection or enumeration | Ongoing | More robust across printer models |
| Manual codepage conversion | MagicEncode auto-detection | python-escpos 2.x+ | Automatic UTF-8 to codepage mapping |
| argparse.error() override | exit_on_error=False parameter | Python 3.9+ (2020) | Cleaner error handling without subclassing |
| apt-get python-usb | pip install pyusb | Modern practice | pip provides newer versions than OS packages |

**Deprecated/outdated:**
- **python-printer-escpos**: Older fork, use python-escpos instead
- **escpos library (not python-escpos)**: Different project, less maintained
- **Direct ESC/POS byte sequences**: Use python-escpos methods, not raw `\x1b` commands
- **Python 2.x**: python-escpos 3.x requires Python 3.x (3.7+)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x (latest 2026) |
| Config file | none — see Wave 0 gaps |
| Quick run command | `pytest tests/ -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PRINT-01 | Accept filename via command-line argument | unit | `pytest tests/test_print_job.py::test_parse_args -x` | ❌ Wave 0 |
| PRINT-02 | Read file from /GEN26_BILLPRINTER/ folder | unit | `pytest tests/test_file_handler.py::test_read_file -x` | ❌ Wave 0 |
| PRINT-03 | Auto-detect USB printer without hard-coded IDs | unit (mocked) | `pytest tests/test_printer.py::test_auto_detect -x` | ❌ Wave 0 |
| PRINT-04 | Open printer connection, print, close per job | integration (mocked) | `pytest tests/test_printer.py::test_connection_lifecycle -x` | ❌ Wave 0 |
| PRINT-05 | Print UTF-8 text content exactly as-is | integration (mocked) | `pytest tests/test_printer.py::test_print_text -x` | ❌ Wave 0 |
| PRINT-06 | Full paper cut after print | integration (mocked) | `pytest tests/test_printer.py::test_full_cut -x` | ❌ Wave 0 |
| PRINT-07 | Handle file not found errors gracefully | unit | `pytest tests/test_file_handler.py::test_file_not_found -x` | ❌ Wave 0 |
| PRINT-08 | Handle printer offline/USB errors gracefully | unit (mocked) | `pytest tests/test_printer.py::test_usb_error -x` | ❌ Wave 0 |
| PRINT-09 | Return appropriate exit codes (0=success, 1=error, 2=bad args) | integration | `pytest tests/test_print_job.py::test_exit_codes -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x` (stop on first failure, ~5-10 seconds)
- **Per wave merge:** `pytest tests/ -v` (full suite with verbose output, ~30 seconds)
- **Phase gate:** Full suite green + manual print test with actual hardware before `/gsd:verify-work`

### Wave 0 Gaps

The project currently has no test infrastructure. Wave 0 must establish:

- [ ] `tests/test_print_job.py` — covers PRINT-01, PRINT-09 (CLI argument parsing, main entry point, exit codes)
- [ ] `tests/test_file_handler.py` — covers PRINT-02, PRINT-07 (file reading, UTF-8 decoding, error cases)
- [ ] `tests/test_printer.py` — covers PRINT-03, PRINT-04, PRINT-05, PRINT-06, PRINT-08 (printer operations with mocked USB)
- [ ] `tests/conftest.py` — shared fixtures (mock printer, temp files, sample text content)
- [ ] Framework install: `pip install pytest pytest-mock` — if not detected in requirements.txt
- [ ] `pytest.ini` or `pyproject.toml` — basic pytest configuration (test discovery, output format)

**Mocking Strategy:** Use `pytest-mock` or `unittest.mock` to mock pyusb/python-escpos USB operations. Test business logic without requiring physical printer hardware. Reserve actual hardware testing for manual verification at phase gate.

## Open Questions

1. **Citizen CT-S310IIEBK specific vendor/product ID**
   - What we know: Citizen printers typically use vendor ID 0x2730, but specific product ID varies by model
   - What's unclear: Exact USB IDs for CT-S310IIEBK variant (vs CT-S310II or CT-S310)
   - Recommendation: Use class-based auto-detection (class 7) as specified in user constraints, avoiding hard-coded IDs. If class detection fails, fall back to `lsusb` output on actual hardware for specific IDs.

2. **Additional file types beyond .txt**
   - What we know: User requested checking folder contents and supporting "any file types in given folder" with .txt as minimum
   - What's unclear: USB folder not currently mounted, can't check actual file types present
   - Recommendation: Implement .txt support in Phase 1 as specified. Add .png/.jpg image support if found during testing (python-escpos supports via `image()` method). Document supported types in help text.

3. **Raspberry Pi 3B+ specific configuration**
   - What we know: Project targets Raspberry Pi 3B+ (ARMv8), python-escpos generally compatible
   - What's unclear: Whether OS packages vs pip installation is better for this specific hardware
   - Recommendation: Start with pip install (standard practice), fall back to `apt-get install python3-escpos python3-usb python3-pil` if pip has issues. Test installation on actual hardware in Wave 0.

4. **Printer reset/initialization commands**
   - What we know: User specified "reset printer and apply standard settings on each connection (codepage CP437, enable auto-status)"
   - What's unclear: python-escpos doesn't expose explicit reset() method in current API
   - Recommendation: Investigate sending ESC @ (initialize) command via `_raw()` method, or rely on per-job connection lifecycle to reset state. May require reading printer manufacturer's command reference to implement full initialization sequence.

5. **Logging vs console output**
   - What we know: User left logging approach to Claude's discretion
   - What's unclear: Whether automated triggering process (future) needs structured logs or just exit codes
   - Recommendation: Phase 1 uses simple console output (print to stderr for errors, stdout for verbose success). Add file logging in later phase when trigger process is implemented, if needed for debugging automated runs.

## Sources

### Primary (HIGH confidence)
- [python-escpos official documentation](https://python-escpos.readthedocs.io/) - API reference, usage patterns, methods
- [python-escpos GitHub repository](https://github.com/python-escpos/python-escpos) - Source code, issue tracking, examples
- [Citizen CT-S310II Command Reference PDF](https://www.citizen-systems.com/resource/support/POS/Generic_Printer_Files/Command_Reference/CommandReference.pdf) - ESC/POS commands
- [Citizen CT-S310II User Manual](https://www.citizen-systems.com/resource/support/POS/Manuals/User_Manuals/CT-S310II_Manual_EN.pdf) - Hardware specifications
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html) - Official stdlib docs (updated 2026-03-13)

### Secondary (MEDIUM confidence)
- [Raspberry Pi USB permissions forums](https://forums.raspberrypi.com/viewtopic.php?t=186839) - Community udev rules guidance
- [python-escpos Raspberry Pi documentation](https://python-escpos.readthedocs.io/en/latest/user/raspi.html) - Platform-specific setup
- [pytest documentation 2026](https://docs.pytest.org/) - Testing framework
- [Real Python SystemExit guide](https://realpython.com/ref/builtin-exceptions/systemexit/) - Exit code patterns
- [Raspberry Pi testing with pytest](https://woteq.com/how-to-test-python-applications-running-on-raspberry-pi-with-pytest/) - Hardware mocking strategies

### Tertiary (LOW confidence - requires validation)
- Web search results for UTF-8/codepage issues - Multiple GitHub issues reported, but workarounds vary
- Web search results for endpoint address errors - Documented by users, but specific solutions hardware-dependent
- Thermal paper character width standards - Industry conventions, but printer-specific settings may override

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - python-escpos is established standard, well-documented, actively maintained
- Architecture: MEDIUM-HIGH - Patterns verified from official docs, but Citizen-specific profiles not found in python-escpos database
- Pitfalls: MEDIUM - Based on GitHub issues and forum posts (not official docs), but widely reported and consistent across sources
- Raspberry Pi compatibility: MEDIUM - Generally works, but ARMv6 (Pi Zero) has known issues; Pi 3B+ should be fine
- Testing approach: HIGH - pytest is standard, mocking strategies well-documented

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (30 days - stable domain, python-escpos updates infrequent)

**Notes:**
- USB folder `/GEN26_BILLPRINTER/` not currently mounted, couldn't verify actual file types present
- Citizen CT-S310IIEBK specific USB IDs not verified (will need `lsusb` output from actual hardware)
- python-escpos reset() method investigation incomplete - may need deeper dive into raw command sending
- Printer profile for CT-S310 not found in python-escpos database - may need generic ESC/POS profile or custom profile creation
