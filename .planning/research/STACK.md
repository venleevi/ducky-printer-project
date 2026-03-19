# Technology Stack — v0.2 GPIO Print Trigger

**Project:** Ducky Thermal Printer POC
**Milestone:** v0.2 - GPIO Print Trigger
**Researched:** 2026-03-19
**Platform:** Raspberry Pi 3B+ (ARM, Bookworm OS, kernel 6.6)
**Existing Stack:** Python 3.13.5, python-escpos 3.0+, pyusb 1.0+

## Executive Summary

**New capabilities:** GPIO button/switch trigger, YAML configuration, random file selection, systemd auto-start
**Stack additions:** gpiozero 2.0.1 (GPIO), PyYAML 6.0.2+ (config), stdlib only for file selection
**Philosophy:** Minimal additions -- two new pip packages, zero new system services
**Confidence:** MEDIUM-HIGH (gpiozero has a known open issue with lgpio button reliability on Pi 3B; mitigations documented)

---

## Existing Stack (DO NOT MODIFY)

| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| Python | 3.13.5 | Runtime | Validated v0.1 |
| python-escpos | >=3.0 | USB thermal printer ESC/POS commands | Validated v0.1 |
| pyusb | >=1.0 | USB communication backend | Validated v0.1 |
| pytest | >=9.0 | Test framework | Validated v0.1 |
| pytest-mock | >=3.14 | Test mocking | Validated v0.1 |

---

## New Stack Components

### GPIO Button/Switch Handling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **gpiozero** | 2.0.1 | GPIO input device abstraction | Official Raspberry Pi Foundation library. High-level API with `Button` class, built-in `when_pressed`/`when_released` callbacks, software debounce via `bounce_time`. Replaces deprecated RPi.GPIO. |
| **lgpio** (backend) | 0.2.2.0 (system) | Low-level GPIO access | Required backend for gpiozero on Bookworm. Pre-installed via `python3-lgpio` apt package. Talks to `/dev/gpiochip0` kernel interface. |

**Why gpiozero over alternatives:**

- RPi.GPIO is broken on kernel 6.6+ (current Bookworm default). `GPIO.add_event_detect()` raises `RuntimeError: Failed to add edge detection` due to removal of downstream GPIO sysfs patch. ([GitHub raspberrypi/linux #6037](https://github.com/raspberrypi/linux/issues/6037))
- gpiozero is the official Raspberry Pi recommendation for 2024+. RPi Ltd has stated they "never supported" RPi.GPIO. ([gpiozero docs](https://gpiozero.readthedocs.io/en/stable/))
- pigpio requires a running daemon (`pigpiod`), adding unnecessary complexity for a simple button input.
- Direct lgpio usage is too low-level for button debounce/callback patterns that gpiozero provides out of the box.

**Known issue -- IMPORTANT:**
gpiozero issue [#1090](https://github.com/gpiozero/gpiozero/issues/1090) (OPEN as of 2026-03-19): Button events with `LGPIOFactory` (the default on Bookworm) are sometimes unreliable on Pi 3B, with phantom triggers and missed presses. The issue was filed against Pi 400 and Pi 3B.

**Mitigations for issue #1090:**
1. Use generous `bounce_time` (0.1-0.3s) instead of tight values (0.05s)
2. Implement application-level cooldown (5s default per PROJECT.md) which masks any phantom triggers
3. Add software debounce in the callback itself as a safety net
4. If lgpio proves unreliable in testing, fall back to polling `button.is_pressed` in a loop (less elegant but fully reliable)
5. The RPiGPIOFactory fallback is NOT viable on kernel 6.6+ because RPi.GPIO edge detection is broken

**Confidence:** MEDIUM -- gpiozero is the right choice (only viable option), but button reliability with lgpio on Pi 3B needs validation during implementation.

**Integration with existing code:**
```python
from gpiozero import Button
from signal import pause

def on_trigger():
    # Call existing print pipeline
    from src.printer import print_file
    print_file(random_filename, source_folder)

button = Button(17, bounce_time=0.3, pull_up=True)
button.when_pressed = on_trigger
pause()  # Keep process alive for callbacks
```

**Switch mode (toggle) support:**
```python
# For switch/toggle mode: detect both transitions
button = Button(17, bounce_time=0.3, pull_up=True)
button.when_pressed = on_switch_on    # Switch flipped to ON
button.when_released = on_switch_off  # Switch flipped to OFF
```

### YAML Configuration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **PyYAML** | >=6.0.2 | YAML config file parsing | De facto standard Python YAML library. MIT licensed. Python 3.13 support confirmed in 6.0.2+. `safe_load()` prevents arbitrary code execution. Human-friendly format for Pi users editing config on-device via nano/vim. |

**Why PyYAML:**
- Only mature YAML library for Python. 6.0.2 added Python 3.13 support, 6.0.3 added Python 3.14 support. ([PyYAML PyPI](https://pypi.org/project/PyYAML/))
- `yaml.safe_load()` is the correct function -- never use `yaml.load()` which allows arbitrary code execution. ([PyYAML deprecation wiki](https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation))
- YAML chosen over JSON (no comments, less human-readable) and INI (no nested structures, weaker typing). This aligns with PROJECT.md key decision.
- Zero dependencies -- PyYAML is self-contained.

**Why NOT alternatives:**
- `tomllib` (stdlib in 3.11+): Read-only, TOML less familiar to Pi hobbyists than YAML.
- `strictyaml`: Adds type validation but is an extra dependency with smaller community.
- `ruamel.yaml`: More features than needed, heavier, and preserves comments (unnecessary for this use case).
- JSON: No comments. Users editing config on a headless Pi need inline documentation.

**Confidence:** HIGH -- PyYAML is battle-tested, well-maintained, fully compatible.

**Integration pattern:**
```python
import yaml
from pathlib import Path

DEFAULT_CONFIG = {
    "gpio_pin": 17,
    "trigger_mode": "button",       # "button" or "switch"
    "switch_trigger": "both",       # "both", "on_only", "off_only"
    "cooldown_seconds": 5,
    "bounce_time": 0.3,
    "source_folder": "/home/admin/ducky-printer-project/print_files",
}

def load_config(path: Path) -> dict:
    with open(path, "r") as f:
        user_config = yaml.safe_load(f) or {}
    config = {**DEFAULT_CONFIG, **user_config}
    return config
```

### Random File Selection

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **random** (stdlib) | built-in | Random file selection | `random.choice()` for uniform random selection from file list. No external dependency needed. |
| **pathlib** (stdlib) | built-in | File system operations | `Path.glob()` for listing files by extension pattern. Modern, clean API. Already implicit in python-escpos usage patterns. |

**No new packages required.** The stdlib `random` module with `os`/`pathlib` for directory listing covers this completely.

**Why NOT alternatives:**
- `secrets.choice()`: Cryptographic randomness unnecessary for file selection.
- Weighted random: Over-engineered. Uniform random is the expected behavior.

**Confidence:** HIGH -- stdlib, zero risk.

**Integration pattern:**
```python
import random
from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".png", ".jpg", ".jpeg", ".bmp"}

def pick_random_file(folder: str) -> Path:
    source = Path(folder)
    files = [f for f in source.iterdir()
             if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]
    if not files:
        raise FileNotFoundError(f"No printable files in {folder}")
    return random.choice(files)
```

### systemd Service

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **systemd** | system | Auto-start on boot, process management | Native to Raspberry Pi OS Bookworm. Handles restart-on-failure, logging (journalctl), boot ordering. Zero Python dependencies. |

**No Python packages required.** systemd is configured via a `.service` unit file only.

**Why systemd over alternatives:**
- `crontab @reboot`: No process management, no restart-on-failure, no logging integration.
- `rc.local`: Deprecated on modern Debian/Bookworm systems.
- `supervisor`: Extra dependency when systemd is already available and standard.
- `screen`/`tmux`: Manual, not automatic, requires SSH.

**Confidence:** HIGH -- standard Linux service management, well-documented for Pi.

**Critical configuration for GPIO access:**
```ini
[Unit]
Description=Ducky Thermal Printer GPIO Trigger
Wants=dev-gpiochip0.device
After=dev-gpiochip0.device multi-user.target
ConditionPathExists=/dev/gpiochip0

[Service]
Type=simple
User=admin
SupplementaryGroups=gpio
Environment=GPIOZERO_PIN_FACTORY=lgpio
ExecStart=/usr/bin/python3 -m src.gpio_listener
WorkingDirectory=/home/admin/ducky-printer-project
Restart=on-failure
RestartSec=5
KillSignal=SIGINT
PrivateDevices=no

[Install]
WantedBy=multi-user.target
```

**Key details:**
- `Wants=dev-gpiochip0.device` + `After=dev-gpiochip0.device`: Ensures GPIO hardware is available before starting. Without this, the service may start before `/dev/gpiochip0` exists and crash.
- `SupplementaryGroups=gpio`: Grants GPIO device access without running as root.
- `PrivateDevices=no`: Required so the service can access `/dev/gpiochip0` and `/dev/gpiomem`.
- `Environment=GPIOZERO_PIN_FACTORY=lgpio`: Explicit pin factory selection.
- `KillSignal=SIGINT`: Sends Ctrl+C to Python for graceful `signal.pause()` exit.
- `Restart=on-failure` + `RestartSec=5`: Auto-restart on crash with 5s delay.
- `Type=simple`: Correct for a long-running `signal.pause()` process.

---

## Installation

### System Dependencies (one-time, likely already present)
```bash
# lgpio (pre-installed on Bookworm, verify)
dpkg -l | grep python3-lgpio || sudo apt-get install -y python3-lgpio
```

### Python Packages (add to requirements.txt)
```
# GPIO control library (official Raspberry Pi recommendation)
gpiozero>=2.0.1

# YAML configuration file parsing
PyYAML>=6.0.2
```

### Virtual Environment Setup
```bash
# CRITICAL: Use --system-site-packages to inherit system lgpio
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**WARNING:** Creating a venv WITHOUT `--system-site-packages` will cause lgpio to be missing or install a broken PyPI version (0.0.0.2 instead of the working system 0.2.2.0). This causes `PinFactoryFallback` errors. ([Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=358841))

### systemd Service Setup
```bash
sudo cp ducky-printer.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/ducky-printer.service
sudo systemctl daemon-reload
sudo systemctl enable ducky-printer.service
sudo systemctl start ducky-printer.service
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| GPIO | gpiozero 2.0.1 | RPi.GPIO | Edge detection broken on kernel 6.6+ (current Bookworm). Dead project. |
| GPIO | gpiozero 2.0.1 | pigpio | Requires daemon process. Overkill for single button. |
| GPIO | gpiozero 2.0.1 | rpi-lgpio | Drop-in RPi.GPIO replacement using lgpio. Works, but lower-level API than gpiozero. No built-in Button class. |
| GPIO | gpiozero 2.0.1 | Direct lgpio | No debounce, no callback helpers, manual pin management. |
| Config | PyYAML 6.0.2+ | tomllib (stdlib) | Read-only (no write). TOML less familiar to Pi hobbyists. |
| Config | PyYAML 6.0.2+ | JSON | No comments. Users need inline docs when editing on headless Pi. |
| Config | PyYAML 6.0.2+ | INI/configparser | No nested structures, weak typing, no list support. |
| Config | PyYAML 6.0.2+ | strictyaml | Extra dependency, smaller community, unnecessary for simple config. |
| File select | random (stdlib) | secrets | Cryptographic randomness unnecessary. |
| Service | systemd | crontab @reboot | No restart-on-failure, no logging, no process management. |
| Service | systemd | supervisor | Extra dependency when systemd is native. |

---

## Anti-Patterns to Avoid

### Do NOT: Use RPi.GPIO on kernel 6.6+
**Why:** `GPIO.add_event_detect()` raises RuntimeError. The GPIO sysfs interface it depends on was removed from the kernel.
**Instead:** Use gpiozero with lgpio backend.

### Do NOT: Create venv without --system-site-packages
**Why:** lgpio on PyPI (0.0.0.2) is broken. The working version (0.2.2.0) is installed via apt as `python3-lgpio`.
**Instead:** Always use `python3 -m venv --system-site-packages`.

### Do NOT: Use yaml.load() (without safe_load)
**Why:** Allows arbitrary Python code execution from YAML files. Equivalent to `pickle.load()` in terms of security risk.
**Instead:** Always use `yaml.safe_load()`.

### Do NOT: Use tight bounce_time values (< 0.1s)
**Why:** lgpio debounce works differently from RPi.GPIO. It waits for the signal to be STABLE for the specified duration, rather than suppressing edges within a window. Combined with issue #1090, tight values increase phantom trigger risk.
**Instead:** Start with `bounce_time=0.3` and add application-level cooldown.

### Do NOT: Run the systemd service as root
**Why:** Unnecessary privilege escalation. GPIO access is available via the `gpio` group.
**Instead:** Run as the application user with `SupplementaryGroups=gpio`.

### Do NOT: Skip the `After=dev-gpiochip0.device` in systemd
**Why:** The service may start before the GPIO device node exists, causing immediate crash + restart loop.
**Instead:** Use `Wants=dev-gpiochip0.device` and `After=dev-gpiochip0.device`.

### Do NOT: Use signal.pause() without SIGINT handling
**Why:** systemd sends SIGTERM by default, but Python `signal.pause()` responds to SIGINT (Ctrl+C). Without `KillSignal=SIGINT` in the service file, shutdown may not be clean.
**Instead:** Set `KillSignal=SIGINT` in the systemd unit, or handle SIGTERM explicitly in Python.

---

## Resource Footprint

| Component | Memory (MB) | CPU (idle) | Notes |
|-----------|-------------|------------|-------|
| gpiozero + lgpio | <1 | <1% | Event-driven via `signal.pause()`, sleeps between events |
| PyYAML | <1 | 0% | One-time load at startup, then GC'd |
| Python process | ~20-30 | <1% | Main loop is `signal.pause()`, nearly zero CPU |
| **Total NEW** | ~20-30 | <2% | Negligible on Pi 3B+ (1GB RAM, quad-core) |

**v0.1 baseline:** python-escpos + USB overhead ~20-40MB (per-job, not persistent)
**v0.2 persistent process:** ~20-30MB idle, spikes to ~50-70MB during print job

---

## Configuration Recommendations

### GPIO Pin Selection
- **Default:** GPIO 17 (physical pin 11) -- general purpose, no special function
- **Avoid:** GPIO 2/3 (I2C), GPIO 14/15 (UART), GPIO 7-11 (SPI)
- **Pull resistor:** Use internal pull-up (`pull_up=True`, gpiozero default) with button/switch grounding the pin
- **Wiring:** Button connects GPIO pin to GND. No external resistor needed.

### Debounce Strategy (layered)
1. **Hardware:** Optional 0.1uF capacitor across button terminals
2. **gpiozero:** `bounce_time=0.3` (300ms -- generous for reliability)
3. **Application:** 5-second cooldown between print activations (per PROJECT.md requirement)

### Config File Location
- **Path:** `/home/admin/ducky-printer-project/config.yaml`
- **Fallback:** Hardcoded defaults if file missing or malformed
- **Permissions:** Readable by application user, writable for editing

---

## Version Compatibility Matrix

| Component | Min Python | Tested Python | Raspberry Pi OS | Kernel | Notes |
|-----------|------------|---------------|-----------------|--------|-------|
| gpiozero 2.0.1 | 3.9 | 3.13 | Bookworm | 6.6+ | Pre-installed on Bookworm desktop |
| PyYAML 6.0.2 | 3.8 | 3.13 | Any | Any | Pure Python fallback if C ext fails |
| lgpio 0.2.2.0 | 3.9 | 3.13 | Bookworm | 6.6+ | System apt package only |
| systemd | - | - | Bookworm | Any | Native, always available |

**Current project:** Python 3.13.5 -- all components compatible.

---

## Migration Path (v0.1 to v0.2)

### No Breaking Changes
- Existing `src/printer.py`, `src/file_handler.py`, `src/print_job.py` **unchanged**
- python-escpos integration **untouched**
- CLI interface (`python3 -m src.print_job <filename>`) **preserved**

### Additive Changes
```
ducky-printer-project/
  src/
    printer.py           # Existing (no changes)
    file_handler.py      # Existing (no changes)
    print_job.py         # Existing (no changes)
    config.py            # NEW: YAML config loading with defaults
    gpio_listener.py     # NEW: GPIO event loop with signal.pause()
    file_selector.py     # NEW: Random file selection from folder
  config.yaml            # NEW: User-editable configuration
  ducky-printer.service  # NEW: systemd unit file
```

### New requirements.txt additions
```
gpiozero>=2.0.1
PyYAML>=6.0.2
```

---

## Testing Considerations

### GPIO Testing (without hardware)
- Mock `gpiozero.Button` in unit tests using `pytest-mock`
- Test callback registration, debounce timing, cooldown logic
- gpiozero provides `MockFactory` for testing: `from gpiozero.pins.mock import MockFactory`

### YAML Config Testing
- Test default values when config file missing
- Test partial config (user overrides subset of defaults)
- Test invalid YAML (malformed file) gracefully returns defaults
- Test type validation (wrong types in config values)

### File Selection Testing
- Test empty folder raises appropriate error
- Test folder with non-printable files only
- Test randomness (statistical distribution over many calls)
- Test file extension filtering (case insensitive)

### systemd Testing (on device)
- `sudo systemctl status ducky-printer` -- verify running
- `sudo journalctl -u ducky-printer -f` -- live log tailing
- Kill process, verify auto-restart after 5s
- Reboot, verify auto-start

---

## Sources

### Official Documentation
- [gpiozero 2.0.1 Documentation](https://gpiozero.readthedocs.io/en/stable/) -- HIGH confidence
- [gpiozero Input Devices API](https://gpiozero.readthedocs.io/en/stable/api_input.html) -- HIGH confidence
- [gpiozero Pin Factories API](https://gpiozero.readthedocs.io/en/stable/api_pins.html) -- HIGH confidence
- [gpiozero FAQ](https://gpiozero.readthedocs.io/en/stable/faq.html) -- HIGH confidence
- [PyYAML PyPI](https://pypi.org/project/PyYAML/) -- HIGH confidence

### Known Issues (verified)
- [gpiozero #1090: Button class broken with LGPIOFactory](https://github.com/gpiozero/gpiozero/issues/1090) -- OPEN, affects Pi 3B
- [raspberrypi/linux #6037: GPIO.add_event_detect broken on kernel 6.6](https://github.com/raspberrypi/linux/issues/6037) -- Confirms RPi.GPIO is dead
- [PyYAML yaml.load() Deprecation](https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation) -- Security guidance

### Community Resources
- [lgpio in virtual environments](https://forums.raspberrypi.com/viewtopic.php?t=358841) -- Confirms --system-site-packages requirement
- [systemd service with GPIO permissions](https://forums.raspberrypi.com/viewtopic.php?p=2339274) -- Service file template with gpiochip ordering
- [RPi.GPIO broken on Bookworm kernel 6.6](https://forums.raspberrypi.com/viewtopic.php?t=372507) -- Confirms edge detection failure
- [rpi-lgpio as RPi.GPIO replacement](https://rpi-lgpio.readthedocs.io/en/latest/differences.html) -- Alternative if needed

---

## Confidence Assessment

| Area | Confidence | Rationale |
|------|------------|-----------|
| GPIO (gpiozero) | **MEDIUM** | Correct library choice (only viable option), but open issue #1090 means button reliability on Pi 3B needs validation. Mitigations documented. |
| YAML (PyYAML) | **HIGH** | Battle-tested, Python 3.13 compatible, no known issues. |
| File selection (stdlib) | **HIGH** | Standard library, zero risk. |
| systemd service | **HIGH** | Well-documented pattern, community-verified GPIO ordering config. |
| Virtual env + lgpio | **MEDIUM-HIGH** | Requires `--system-site-packages` workaround. Well-documented but easy to get wrong. |
| Overall | **MEDIUM-HIGH** | GPIO reliability is the only open question. Everything else is straightforward. |

---

## Decision Summary

**For v0.2 milestone, add two new pip packages:**

1. **gpiozero >=2.0.1** -- GPIO button/switch events (official recommendation, only viable option on kernel 6.6+)
2. **PyYAML >=6.0.2** -- YAML configuration loading

**Use stdlib for:**
- `random.choice()` for file selection
- `pathlib.Path` for file system operations
- `signal.pause()` for main event loop

**Use system-level:**
- `lgpio` 0.2.2.0 via `python3-lgpio` apt package (GPIO backend)
- `systemd` for service management

**Total new pip dependencies:** 2 packages
**Total new RAM footprint:** ~20-30MB idle
**Integration:** Zero breaking changes to existing v0.1 code

**Critical validation needed:** GPIO button reliability with lgpio on Pi 3B+ (issue #1090). Plan fallback to polling-based approach if event callbacks prove unreliable.
