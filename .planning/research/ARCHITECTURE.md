# Architecture Research

**Domain:** GPIO Print Trigger Integration for Thermal Printer
**Researched:** 2026-03-19
**Confidence:** HIGH

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                   Service Layer (systemd)                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  ducky-printer.service  (auto-start, restart on failure)   │   │
│  └────────────────────────────┬───────────────────────────────┘   │
│                               ↓                                   │
├──────────────────────────────────────────────────────────────────┤
│                   Application Entry Point                        │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  gpio_listener.py (main loop with signal.pause())          │   │
│  │  • Reads config at startup                                 │   │
│  │  • Creates Button (momentary) or sets up switch callbacks  │   │
│  │  • Enforces cooldown between activations                   │   │
│  └────────────────────────────┬───────────────────────────────┘   │
│                               ↓ (callback on GPIO event)          │
├──────────────────────────────────────────────────────────────────┤
│                   New Integration Modules (v0.2)                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  config.py       │  │  file_picker.py  │  │  trigger_       │  │
│  │  Load YAML       │  │  Random file     │  │  handler.py     │  │
│  │  Validate keys   │  │  selection from  │  │  Orchestrate    │  │
│  │  Type-safe       │  │  source folder   │  │  pick + print   │  │
│  │  access          │  │  Filter by ext   │  │  Return status  │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                     │                     │           │
├───────────┴─────────────────────┴─────────────────────┴──────────┤
│                   Existing Print Pipeline (v0.1 - UNCHANGED)     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  print_file()   │  │  print_image()   │  │  print_text()  │  │
│  │  (dispatcher)   │  │  (USB + PIL)     │  │  (USB ESC/POS) │  │
│  └────────┬────────┘  └─────────┬────────┘  └────────┬───────┘  │
│           └─────────────────────┴─────────────────────┘           │
│                               ↓                                   │
│                    USB Printer Communication                      │
│                    find_printer() → open() → print → close()     │
└──────────────────────────────────────────────────────────────────┘
                               ↓
                    Citizen CT-S310IIEBK (USB)
```

## Component Responsibilities

| Component | Responsibility | Status |
|-----------|----------------|--------|
| **config.py** | Load and validate YAML config; provide typed access to settings (pin, mode, cooldown, source_folder) | NEW |
| **file_picker.py** | List printable files in source folder; select one at random; filter by supported extensions | NEW |
| **trigger_handler.py** | Orchestrate a print job: pick random file, call existing `print_file()`, return success/failure dict | NEW |
| **gpio_listener.py** | Set up gpiozero Button/callbacks for button or switch mode; enforce cooldown; run as long-lived daemon | NEW |
| **ducky-printer.service** | systemd unit file for auto-start on boot, restart on crash | NEW |
| **printer.py** | USB printer communication (auto-detect, connect, print, close) | UNCHANGED |
| **file_handler.py** | File reading and path resolution | UNCHANGED |
| **print_job.py** | CLI entry point | UNCHANGED |

## Recommended Project Structure

```
src/
├── __init__.py              # [v0.1] Package init (UNCHANGED)
├── print_job.py             # [v0.1] CLI entry point (UNCHANGED)
├── printer.py               # [v0.1] USB printer communication (UNCHANGED)
├── file_handler.py          # [v0.1] File reading (UNCHANGED)
├── config.py                # [v0.2] NEW - YAML config loader
├── file_picker.py           # [v0.2] NEW - Random file selection
├── trigger_handler.py       # [v0.2] NEW - Shared print trigger orchestration
└── gpio_listener.py         # [v0.2] NEW - GPIO daemon entry point

config/
└── config.yaml              # [v0.2] NEW - Default configuration file

systemd/
└── ducky-printer.service    # [v0.2] NEW - systemd service unit

tests/
├── conftest.py              # [v0.1] Shared fixtures (EXTEND with config fixtures)
├── test_file_handler.py     # [v0.1] (UNCHANGED)
├── test_print_job.py        # [v0.1] (UNCHANGED)
├── test_printer.py          # [v0.1] (UNCHANGED)
├── test_config.py           # [v0.2] NEW - Config loading tests
├── test_file_picker.py      # [v0.2] NEW - File selection tests
├── test_trigger_handler.py  # [v0.2] NEW - Trigger handler tests
└── test_gpio_listener.py    # [v0.2] NEW - GPIO listener tests (mocked gpiozero)
```

### Structure Rationale

- **Flat `src/` layout preserved:** Existing v0.1 uses flat module structure. No reason to introduce packages for 4 new files.
- **`config/` directory at project root:** Separates runtime config from code. Standard Linux convention.
- **`systemd/` directory at project root:** Service files are deployment artifacts, not code. Keeps them findable.
- **v0.1 files are UNCHANGED:** All new code is additive. The integration point is calling `printer.print_file()`.

## Architectural Patterns

### Pattern 1: Event-Driven GPIO with Cooldown Guard

**What:** gpiozero Button detects GPIO events and fires callbacks. A time-based cooldown guard prevents rapid re-triggering (debounce handles electrical noise, cooldown handles intentional rapid presses).

**When to use:** Physical input triggers that should not fire faster than a configurable rate.

**Trade-offs:**
- **Pros:** gpiozero handles threading and debounce internally; cooldown is simple timestamp check
- **Cons:** Cooldown state lives in the daemon process; restarting the service resets it (acceptable)

**Example:**
```python
# src/gpio_listener.py (button mode sketch)
import time
import logging
from gpiozero import Button
from signal import pause
from src.config import load_config
from src.trigger_handler import handle_print_trigger

config = load_config()
last_trigger_time = 0.0

def on_activated():
    global last_trigger_time
    now = time.monotonic()
    cooldown = config.cooldown_seconds
    if now - last_trigger_time < cooldown:
        logging.info(f"Cooldown active ({cooldown}s), ignoring")
        return
    last_trigger_time = now
    result = handle_print_trigger(config)
    logging.info(f"Print result: {result}")

button = Button(
    config.gpio_pin,
    pull_up=True,
    bounce_time=0.1  # 100ms hardware debounce
)
button.when_pressed = on_activated

pause()  # Keep daemon alive
```

### Pattern 2: Dual-Mode GPIO (Button vs Switch)

**What:** Config specifies `mode: button` or `mode: switch`. Button mode uses `when_pressed` only. Switch mode uses `when_pressed` and/or `when_released` depending on `switch_trigger` setting (`both`, `on_only`, `off_only`).

**When to use:** When the same GPIO pin may be connected to either a momentary push button or a toggle switch, and the user should configure which via YAML.

**Trade-offs:**
- **Pros:** Single codebase supports both hardware configurations; no code change needed when swapping button for switch
- **Cons:** Slightly more complex GPIO setup logic; must document clearly

**Example:**
```python
# In gpio_listener.py setup
button = Button(config.gpio_pin, pull_up=True, bounce_time=0.1)

if config.gpio_mode == "button":
    button.when_pressed = on_activated
elif config.gpio_mode == "switch":
    trigger = config.switch_trigger  # "both", "on_only", "off_only"
    if trigger in ("both", "on_only"):
        button.when_pressed = on_activated
    if trigger in ("both", "off_only"):
        button.when_released = on_activated
```

### Pattern 3: Trigger Handler as Integration Seam

**What:** A thin orchestration module (`trigger_handler.py`) sits between event sources (GPIO today, web later) and the existing print pipeline. It picks a file, calls `printer.print_file()`, and returns a result dict.

**When to use:** When multiple event sources need to trigger the same action, and that action involves multi-step orchestration (pick file, resolve path, call printer).

**Trade-offs:**
- **Pros:** Testable in isolation (mock `print_file` and `pick_random_file`); future web trigger calls same function; single place for print options logic
- **Cons:** One layer of indirection (but justified by testability and future extensibility)

**Example:**
```python
# src/trigger_handler.py
from src.config import Config
from src.file_picker import pick_random_file
from src.printer import print_file, PrinterError
from src.file_handler import FileError

def handle_print_trigger(config: Config) -> dict:
    """Pick random file and print it. Returns status dict."""
    try:
        filename = pick_random_file(config.source_folder)
        if filename is None:
            return {"success": False, "message": "No printable files found"}

        print_file(
            filename,
            config.source_folder,
            rotate=config.print_rotate,
            fit_width=config.print_fit_width,
            printer_width=config.print_printer_width,
        )
        return {"success": True, "message": f"Printed: {filename}"}

    except (PrinterError, FileError) as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {e}"}
```

## Data Flow

### GPIO Button Press to Print Output

```
1. Physical button press (GPIO pin goes LOW)
       ↓
2. gpiozero Button detects edge (internal thread)
   - bounce_time=0.1 filters electrical noise
       ↓
3. when_pressed callback fires (gpiozero callback thread)
       ↓
4. Cooldown check (time.monotonic() comparison)
   - If within cooldown: log + return (no print)
   - If past cooldown: proceed
       ↓
5. handle_print_trigger(config) called
       ↓
6. pick_random_file(source_folder)
   - List files matching extensions [.txt, .png, .jpg, .jpeg, .bmp]
   - random.choice() to select one
       ↓
7. printer.print_file(filename, source_folder, **print_options)
   - resolve_filepath() → full path
   - Detect extension → route to print_text_file() or print_image()
       ↓
8. find_printer() → USB class 7 detection
       ↓
9. printer.open() → printer.text()/printer.image() → printer.cut() → printer.close()
       ↓
10. USB ESC/POS commands → Citizen CT-S310IIEBK → thermal output
       ↓
11. Result dict returned up the call stack
       ↓
12. gpio_listener logs success/failure
```

### Switch Mode Data Flow (Differences from Button)

```
Toggle switch flipped ON (GPIO goes LOW)
    ↓
when_pressed fires → same flow as button (steps 4-12)

Toggle switch flipped OFF (GPIO goes HIGH)
    ↓
when_released fires → same flow as button (steps 4-12)
(only if switch_trigger is "both" or "off_only")
```

### Configuration Loading Flow

```
systemd starts ducky-printer.service
    ↓
gpio_listener.py imports and calls load_config()
    ↓
Reads config/config.yaml from project root
    ↓
Validates required keys present (gpio_pin, mode, source_folder)
    ↓
Returns Config object (dataclass or typed dict)
    ↓
Config passed to on_activated callback via closure
    ↓
No hot-reload: restart service to pick up config changes
```

## Integration Points

### New Code to Existing Code Integration

| New Module | Calls | In Existing Module | How |
|------------|-------|--------------------|-----|
| `trigger_handler.py` | `print_file()` | `printer.py` | Direct function import; passes filename, source_folder, and print options |
| `trigger_handler.py` | `PrinterError`, `FileError` | `printer.py`, `file_handler.py` | Catches exceptions, converts to result dict |
| `file_picker.py` | `resolve_filepath()` | `file_handler.py` | Optional: could use for path validation, but `Path.glob()` is simpler for listing |
| `gpio_listener.py` | None | None | Only calls trigger_handler; no direct dependency on v0.1 modules |

### Key Constraint: No Modifications to v0.1 Code

The existing `printer.print_file()` signature already supports everything needed:

```python
# Existing signature (printer.py line 293)
def print_file(filename, base_folder, rotate=False, scale_percent=100,
               fit_width=False, printer_width=576,
               target_width_cm=None, target_height_cm=None)
```

The trigger handler calls this directly. No changes required.

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **gpio_listener -> trigger_handler** | Direct function call | Same process; callback thread calls handler |
| **trigger_handler -> file_picker** | Direct function call | Returns filename string |
| **trigger_handler -> printer** | Direct function call | Imports `print_file` from `printer.py` |
| **config -> all modules** | Config object passed as parameter | Loaded once at startup, passed via closure |

## Configuration Design

### YAML Schema

```yaml
# config/config.yaml

# GPIO settings
gpio:
  pin: 17              # BCM pin number (physical pin 11)
  mode: button          # "button" (momentary) or "switch" (toggle)
  switch_trigger: both  # "both", "on_only", "off_only" (only used when mode=switch)

# Print trigger settings
trigger:
  cooldown_seconds: 5   # Minimum seconds between activations
  source_folder: /home/admin/ducky-printer-project/print_files

# Print options (passed to printer.print_file())
print_options:
  rotate: false
  fit_width: true
  printer_width: 576    # 576 for 80mm paper, 384 for 58mm
  # target_width_cm and target_height_cm are optional overrides
```

### Config Module Design

Use a dataclass or simple class for typed access rather than raw dict traversal. This catches missing keys at load time rather than at print time.

```python
# src/config.py
import yaml
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    gpio_pin: int
    gpio_mode: str           # "button" or "switch"
    switch_trigger: str      # "both", "on_only", "off_only"
    cooldown_seconds: float
    source_folder: str
    print_rotate: bool
    print_fit_width: bool
    print_printer_width: int
    print_target_width_cm: float | None
    print_target_height_cm: float | None

def load_config(config_path: str = None) -> Config:
    """Load config from YAML file, validate, return Config dataclass."""
    if config_path is None:
        # Default: config/config.yaml relative to project root
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    with open(config_path, 'r') as f:
        raw = yaml.safe_load(f)

    # Extract with defaults
    gpio = raw.get('gpio', {})
    trigger = raw.get('trigger', {})
    opts = raw.get('print_options', {})

    return Config(
        gpio_pin=gpio['pin'],  # Required, no default
        gpio_mode=gpio.get('mode', 'button'),
        switch_trigger=gpio.get('switch_trigger', 'both'),
        cooldown_seconds=trigger.get('cooldown_seconds', 5),
        source_folder=trigger.get('source_folder',
            '/home/admin/ducky-printer-project/print_files'),
        print_rotate=opts.get('rotate', False),
        print_fit_width=opts.get('fit_width', True),
        print_printer_width=opts.get('printer_width', 576),
        print_target_width_cm=opts.get('target_width_cm'),
        print_target_height_cm=opts.get('target_height_cm'),
    )
```

## systemd Service Integration

### Single Service (Not Two)

Since v0.2 is GPIO-only (web deferred), there is only one service:

```ini
# systemd/ducky-printer.service
[Unit]
Description=Ducky Thermal Printer GPIO Listener
After=local-fs.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/admin/ducky-printer-project
ExecStart=/usr/bin/python3 -m src.gpio_listener
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Why `User=root`:** GPIO access on Raspberry Pi requires root or gpio group membership. Running as root is simplest for a dedicated appliance. Alternative: add user to `gpio` group and run as `admin`.

**Why `After=local-fs.target`:** No network needed for GPIO printing. Only needs filesystem mounted (for config and print files).

**Why `-m src.gpio_listener`:** Uses Python module syntax consistent with existing `python3 -m src.print_job` pattern.

## Build Order and Dependencies

### Dependency Graph

```
                    ┌──────────────┐
                    │  config.py   │  ← No dependencies on other new modules
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
     ┌──────────────┐ ┌──────────────┐  │
     │ file_picker  │ │ trigger_     │  │
     │   .py        │ │ handler.py   │←─┘ (uses config + file_picker + printer.py)
     └──────┬───────┘ └──────┬───────┘
            │                │
            └────────┬───────┘
                     ↓
            ┌──────────────────┐
            │ gpio_listener.py │  ← Uses config + trigger_handler
            └──────────────────┘
                     ↓
            ┌──────────────────┐
            │ systemd service  │  ← Deployment artifact wrapping gpio_listener
            └──────────────────┘
```

### Recommended Build Order

**Phase 1: Configuration Foundation**
- Build `config.py` with `load_config()` returning `Config` dataclass
- Create `config/config.yaml` with documented defaults
- Write `test_config.py`: valid config, missing keys, bad values, defaults
- **Why first:** Zero external dependencies. Pure Python. Every other module depends on it.

**Phase 2: Random File Selection**
- Build `file_picker.py` with `pick_random_file(source_folder)` and `list_printable_files(source_folder)`
- Write `test_file_picker.py`: empty folder, single file, multiple files, unsupported extensions filtered, nonexistent folder
- **Why second:** Also pure Python (pathlib + random). No GPIO or printer hardware needed. Independent testability.

**Phase 3: Trigger Handler (Integration Seam)**
- Build `trigger_handler.py` with `handle_print_trigger(config)`
- Write `test_trigger_handler.py`: mock `printer.print_file()` and `pick_random_file()`, verify correct params passed, verify error handling
- **Why third:** This is the integration point. By building it before GPIO, you can test the full pick-and-print logic without hardware.

**Phase 4: GPIO Listener**
- Build `gpio_listener.py` with button/switch mode setup, cooldown enforcement
- Write `test_gpio_listener.py`: mock gpiozero Button, simulate press events, verify cooldown works, verify switch mode callbacks
- **Why fourth:** Depends on all previous modules. GPIO mocking with `gpiozero.Device.pin_factory = MockFactory` enables testing without hardware.

**Phase 5: systemd Service**
- Create `systemd/ducky-printer.service` unit file
- Write install/uninstall script or document manual steps
- Test on actual Raspberry Pi: enable, start, verify auto-start on boot, verify restart on crash
- **Why last:** Pure deployment concern. All code is testable before this phase. Hardware-only validation.

### Testing Strategy Per Phase

| Phase | Test Type | Hardware Needed | Mock Strategy |
|-------|-----------|-----------------|---------------|
| Config | Unit | No | Sample YAML files via tmp_path |
| File Picker | Unit | No | tmp_path with test files |
| Trigger Handler | Unit | No | Mock `print_file()`, `pick_random_file()` |
| GPIO Listener | Unit + Manual | Mock for unit, Pi for manual | `gpiozero.Device.pin_factory = MockFactory` |
| systemd | Manual | Yes (Raspberry Pi) | N/A |

## Anti-Patterns

### Anti-Pattern 1: Modifying Existing v0.1 Modules

**What people do:** Add GPIO or config logic into `printer.py`, `file_handler.py`, or `print_job.py`.
**Why it's wrong:** Breaks single responsibility. Makes v0.1 CLI mode dependent on config system. Risks breaking 23 existing tests.
**Do this instead:** New modules call existing functions as a library. Zero changes to v0.1.

### Anti-Pattern 2: Persistent USB Connection

**What people do:** Open USB connection once at daemon start, reuse for all prints.
**Why it's wrong:** USB devices enter busy state after power cycles. This is exactly why v0.1 uses per-job lifecycle (documented as key decision in PROJECT.md).
**Do this instead:** Let `printer.print_file()` handle its own connection lifecycle per call.

### Anti-Pattern 3: Hot-Reloading Config in a GPIO Daemon

**What people do:** Watch config file for changes, reload on the fly.
**Why it's wrong:** Adds complexity (file watchers, thread safety for config access, partial state during reload). For an embedded appliance, `systemctl restart ducky-printer` is the expected config reload mechanism.
**Do this instead:** Load config once at startup. Document that service restart applies config changes.

### Anti-Pattern 4: Using RPi.GPIO Instead of gpiozero

**What people do:** Use the lower-level `RPi.GPIO` library directly.
**Why it's wrong:** Requires manual cleanup (`GPIO.cleanup()`), manual threading for callbacks, manual debounce logic, no mock pin factory for testing.
**Do this instead:** Use gpiozero. It provides `Button` class with built-in debounce, callback threading, mock factories, and a cleaner API.

### Anti-Pattern 5: Threading Lock for Print Serialization

**What people do:** Add `threading.Lock()` around print calls to prevent concurrent USB access.
**Why it's wrong:** Unnecessary complexity. The per-job connection lifecycle in `printer.py` means each call opens its own USB handle. The USB kernel driver serializes access. With a single GPIO trigger source and cooldown, concurrent prints are already prevented.
**Do this instead:** Rely on cooldown to space out triggers. Per-job USB connections handle the rare case of overlapping calls naturally.

### Anti-Pattern 6: Putting Config in Python Code

**What people do:** Define pin numbers, paths, and options as constants in Python source files.
**Why it's wrong:** Users must edit Python to change settings. Error-prone on a headless Raspberry Pi. YAML is human-friendly and editable with `nano`.
**Do this instead:** All user-configurable values go in `config/config.yaml`. Python code reads the YAML.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **1 button, 1 printer, casual use** | Current architecture is exactly right. No changes needed. |
| **Adding web trigger later (v0.3)** | Web server module calls same `handle_print_trigger()`. Add print queue if concerned about concurrent GPIO + web triggers. |
| **Multiple print files with weighted selection** | Extend `file_picker.py` with weight config. Config-driven, no architecture change. |
| **Multiple printers** | Out of scope per PROJECT.md. Would require `find_printer()` to accept vendor/product filter. |

### Scaling Priorities

1. **Not a concern for v0.2:** Single button, single printer, cooldown-gated. The architecture cannot be stressed.
2. **Future web trigger:** The trigger_handler abstraction exists specifically to support this without architectural changes.

## Sources

### Official Documentation
- [gpiozero Button API and Recipes](https://gpiozero.readthedocs.io/en/stable/recipes.html) -- button/switch patterns, when_pressed/when_released callbacks, bounce_time, MockFactory
- [gpiozero Input Devices source](https://gpiozero.readthedocs.io/en/stable/_modules/gpiozero/input_devices.html) -- Button internals, threading model
- [systemd.service man page](https://www.freedesktop.org/software/systemd/man/systemd.service.html) -- Type=simple, Restart, After dependencies
- [PyYAML safe_load](https://pyyaml.org/wiki/PyYAMLDocumentation) -- YAML loading best practices

### Existing Codebase (Verified by Reading Source)
- `src/printer.py` -- `print_file()` signature at line 293, per-job connection lifecycle, `PrinterError` exception
- `src/file_handler.py` -- `resolve_filepath()`, `FileError` exception, UTF-8 validation
- `src/print_job.py` -- CLI entry point, argument parsing (shows all print_file kwargs)
- `tests/conftest.py` -- Existing test fixtures (mock_printer, mock_usb_device, temp_test_file)

---
*Architecture research for: GPIO Print Trigger Integration (v0.2)*
*Researched: 2026-03-19*
