# Feature Research

**Domain:** GPIO print trigger with config system, random file selection, and systemd service on Raspberry Pi
**Researched:** 2026-03-19
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| GPIO button debouncing | Physical buttons bounce mechanically; without debounce a single press fires multiple prints | LOW | gpiozero `Button(pin, bounce_time=0.05)` handles this. Known issue: bounce_time can drop edge events with RPi.GPIO backend. Use default lgpio backend on Pi 3B+ to avoid. 50ms is safe starting point. |
| Software pull-up/pull-down resistor configuration | GPIO pins float when unconnected; reads garbage without defined pull state | LOW | gpiozero `Button(pin, pull_up=True)` is the default. Connect button between GPIO pin and GND. No external resistor needed. Avoid GPIO2/GPIO3 (have permanent physical pull-ups). |
| Cooldown between activations | Prevents accidental rapid-fire prints that waste paper and jam printer | LOW | Application-level timer (not debounce). Track last print timestamp, reject activations within cooldown window. Default 5 seconds per PROJECT.md spec. |
| Config file with sensible defaults | Users should not need to edit config to get started; first run should work | LOW | YAML file with all fields having defaults. Parse with `yaml.safe_load()`, merge with defaults dict. Missing file = use all defaults. |
| Config validation at startup | Invalid config (wrong pin number, bad path) should fail fast with clear error, not crash mid-operation | MEDIUM | Validate types, ranges (valid GPIO pins 2-27), path existence, enum values (mode: button/switch). Report all errors at once, not one at a time. |
| Random file selection from folder | Core value proposition: press button, get random print. Must actually be random, not sequential or repeating | LOW | `random.choice(list(Path(folder).glob('*')))` filtered by supported extensions (.txt, .png, .jpg, .jpeg, .bmp). Handle empty folder gracefully. |
| systemd auto-start on boot | Headless Pi must work after power-on without SSH or keyboard | LOW | Service file in `/etc/systemd/system/`. Use `Type=simple`, `Restart=on-failure`, `After=multi-user.target`. Straightforward configuration. |
| Graceful shutdown on SIGTERM | systemd sends SIGTERM on `systemctl stop`; service must release GPIO cleanly | LOW | gpiozero handles GPIO cleanup automatically on exit. Catch SIGTERM with signal handler to log shutdown. `signal.pause()` in main loop naturally exits on signal. |
| Structured logging to journald | No screen attached; logs are the only debugging interface | LOW | Use Python `logging` module. systemd captures stdout/stderr automatically. Use `python3 -u` flag in ExecStart to disable output buffering. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Dual input mode (button AND switch) | Same hardware, two use cases: momentary press for on-demand prints, toggle switch for "print on flip" installations | MEDIUM | Button mode: `when_pressed` callback. Switch mode: `when_activated`/`when_deactivated` callbacks with configurable trigger (both transitions, on_only, off_only). Same gpiozero `Button` class works for both. |
| Configurable switch transition triggers | Switch users may want print on flip-on, flip-off, or both directions | LOW | Config option `trigger_on: both/on_only/off_only`. In switch mode, check config before printing in `when_activated`/`when_deactivated` handlers. |
| No-repeat random selection | Avoids printing the same file twice in a row when folder has multiple files | LOW | Track last printed file, re-roll if same. Only matters when folder has 2+ files. With 1 file, always print it. |
| Config file hot-reload on SIGHUP | Change config without restarting service; send `systemctl reload` or `kill -HUP` | MEDIUM | Re-read and re-validate YAML on SIGHUP. Re-initialize GPIO if pin changed. Lower priority than getting basics working. |
| Default config generation | First run creates a commented example config if none exists | LOW | Write default YAML with comments explaining each option. Users see what is configurable without reading docs. |
| systemd watchdog integration | systemd detects if service hangs and restarts it automatically | LOW | Add `WatchdogSec=30` to service file. Periodically call `sd_notify("WATCHDOG=1")` from Python via `systemd.daemon` or simple socket write. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Config hot-reload for GPIO pin changes | Convenience of not restarting service | Changing GPIO pin at runtime requires closing old pin, opening new one. Risk of pin conflicts, partial state. gpiozero cleanup on pin change can be unreliable. | Require service restart for pin changes. Hot-reload only for non-hardware settings (cooldown, source_folder). |
| Multiple GPIO pins for different actions | Different buttons for different file types or folders | GPIO pin scarcity on Pi 3B+; wiring complexity; confusing UX for a "press button, get random print" device | Single button/switch. Use config to set source folder. |
| TOML or INI config instead of YAML | Some users prefer other formats | Adding format options splits testing surface. YAML is the most human-friendly for the key-value-with-nesting pattern this config needs. PyYAML is the only dependency needed. | Stick with YAML. It is already decided in PROJECT.md. |
| Pydantic for config validation | Type-safe, auto-coercion, great error messages | Adds a significant dependency (pydantic + typing-extensions) to a minimal Pi project. PyYAML + manual validation with dataclasses is sufficient for 6 config fields. | Use Python dataclasses with explicit validation. Keeps dependencies minimal per project constraint. |
| File watching (inotify) on source folder | Auto-detect new files added to print folder | Adds inotify dependency. Source folder changes are rare (USB stick swap). Over-engineering for the use case. | Re-scan folder on each activation. Simple, no extra dependencies, always fresh. |
| Print queue for rapid button presses | Queue prints instead of rejecting during cooldown | Thermal printers are serial devices. Queue builds up if printer is slow. Paper waste risk. Cooldown exists specifically to prevent this. | Reject during cooldown. Log the rejection. User learns the rhythm. |
| Environment variable overrides for config | Twelve-factor app pattern | This is a single-purpose embedded device, not a cloud service. ENV vars are harder to inspect than a YAML file for Pi users. | YAML file is the single source of truth. CLI args could override for testing. |
| Weighted random selection | Some files print more often than others | Adds config complexity (weights per file). Users would need to maintain a mapping of filenames to weights. | Equal probability. If users want more of one file, they can duplicate it in the folder. |

## Feature Dependencies

```
[YAML Config System]
    +-- parsed at startup
    +-- provides settings to all other components
    |
    +-------> [GPIO Listener]
    |             +-- needs: pin number, mode (button/switch), cooldown, bounce_time
    |             +-- needs: trigger_on setting for switch mode
    |             |
    |             +-------> [Random File Selector]
    |             |             +-- needs: source_folder path from config
    |             |             +-- needs: supported file extensions (hardcoded, matches v0.1)
    |             |             |
    |             |             +-------> [Existing Print Pipeline]
    |             |                           +-- src.printer.print_file()
    |             |                           +-- already built in v0.1
    |             |
    |             +-------> [Cooldown Manager]
    |                           +-- needs: cooldown_seconds from config
    |                           +-- gates print activation
    |
    +-------> [systemd Service]
                  +-- needs: ExecStart path, User, WorkingDirectory
                  +-- manages lifecycle of GPIO Listener
                  +-- captures logs via journald
```

### Dependency Notes

- **Config must load before GPIO init:** GPIO pin number comes from config. Config parsing and validation is the first thing that runs.
- **GPIO Listener depends on Config:** Cannot set up Button without knowing which pin, which mode, what bounce_time.
- **Random File Selector is stateless:** Called on each activation. Scans folder fresh each time. No dependency on GPIO library itself.
- **Print Pipeline is unchanged:** `src.printer.print_file()` is called with the selected filename. Same interface as CLI. No modifications to v0.1 code.
- **systemd is deployment concern:** Does not affect application code. Service file references the Python entry point. Orthogonal to feature implementation.
- **Cooldown is application-level:** Not a gpiozero feature. Simple timestamp check wrapping the print trigger callback.

## MVP Definition

### Launch With (v0.2)

Minimum viable milestone -- physical button triggers random print, runs as service.

- [ ] **YAML config loading with defaults** -- Foundation for all other features. Without config, everything is hardcoded.
- [ ] **Config validation at startup** -- Fail fast with clear errors. Essential for headless debugging.
- [ ] **GPIO button mode with debounce** -- Core use case. Press button, get print.
- [ ] **GPIO switch mode with configurable triggers** -- Second input mode per spec. Same GPIO library, different callback wiring.
- [ ] **Cooldown between activations** -- Prevents paper waste and printer abuse.
- [ ] **Random file selection from source folder** -- Core value: "random file prints." Not a specific file.
- [ ] **systemd service file** -- Auto-start on boot. Headless operation is the whole point.
- [ ] **Logging to journald** -- Only way to debug on headless Pi.

### Add After Validation (v0.2.x)

Features to add once core is working and tested on hardware.

- [ ] **No-repeat random selection** -- Only matters once users notice duplicates. Trivial to add.
- [ ] **Default config generation on first run** -- Nice onboarding. Not blocking for users who can create config manually.
- [ ] **Config hot-reload for non-hardware settings** -- SIGHUP reloads cooldown, source_folder without service restart.
- [ ] **systemd watchdog** -- Safety net for hangs. Add after confirming basic service stability.

### Future Consideration (v0.3+)

Features to defer until GPIO trigger system is stable.

- [ ] **Visual confirmation LED** -- Physical feedback. Requires additional GPIO pin, wiring, and LED hardware.
- [ ] **Hold-to-print pattern** -- Prevents accidental prints. Add if users report accidental triggers.
- [ ] **Web interface for print triggering** -- Explicitly deferred per PROJECT.md scope decision.
- [ ] **Print history/statistics** -- Track what was printed, when, how triggered.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| YAML config with defaults | HIGH | LOW | P1 |
| Config validation | HIGH | LOW | P1 |
| GPIO button mode + debounce | HIGH | LOW | P1 |
| GPIO switch mode | HIGH | LOW | P1 |
| Cooldown between activations | HIGH | LOW | P1 |
| Random file selection | HIGH | LOW | P1 |
| systemd service file | HIGH | LOW | P1 |
| Logging to journald | HIGH | LOW | P1 |
| Configurable switch triggers (both/on/off) | MEDIUM | LOW | P1 |
| No-repeat random | LOW | LOW | P2 |
| Default config generation | MEDIUM | LOW | P2 |
| Config hot-reload (SIGHUP) | LOW | MEDIUM | P2 |
| systemd watchdog | LOW | LOW | P2 |
| Visual LED feedback | MEDIUM | MEDIUM | P3 |
| Hold-to-print safety | LOW | MEDIUM | P3 |
| Web interface | HIGH | HIGH | P3 (deferred) |

**Priority key:**
- P1: Must have for v0.2 launch
- P2: Should have, add when proven stable
- P3: Future consideration, explicitly out of scope for v0.2

## Implementation Patterns

### GPIO Button Mode

```python
from gpiozero import Button
from signal import pause

button = Button(
    pin=config.gpio_pin,     # e.g., 17
    pull_up=True,             # Connect button between pin and GND
    bounce_time=0.05,         # 50ms software debounce
)

def on_press():
    if not cooldown_active():
        file = select_random_file(config.source_folder)
        print_file(file)
        reset_cooldown()

button.when_pressed = on_press
pause()  # Keeps script alive for event detection
```

**Key points:**
- `pull_up=True` (default): wire button between GPIO pin and GND. No external resistor needed.
- `bounce_time=0.05`: 50ms is safe for most mechanical buttons. Known issue: setting bounce_time too high (>100ms) can drop events with some backends.
- `signal.pause()`: blocks main thread, keeps callbacks alive. Properly handles SIGTERM for clean shutdown.
- gpiozero handles GPIO cleanup automatically on exit.

### GPIO Switch Mode

```python
from gpiozero import Button  # Button class works for switches too
from signal import pause

switch = Button(
    pin=config.gpio_pin,
    pull_up=True,
    bounce_time=0.1,          # Switches may need longer debounce
)

def on_activate():
    """Switch flipped to ON position."""
    if config.trigger_on in ('both', 'on_only'):
        if not cooldown_active():
            trigger_print()

def on_deactivate():
    """Switch flipped to OFF position."""
    if config.trigger_on in ('both', 'off_only'):
        if not cooldown_active():
            trigger_print()

switch.when_pressed = on_activate      # when_activated alias
switch.when_released = on_deactivate   # when_deactivated alias
pause()
```

**Key points:**
- Same `Button` class works for toggle switches. gpiozero has no separate Switch class.
- `when_pressed` fires on inactive-to-active transition (switch flipped on).
- `when_released` fires on active-to-inactive transition (switch flipped off).
- `trigger_on` config controls which transitions actually print.

### YAML Configuration Pattern

```yaml
# /etc/ducky-printer/config.yaml
gpio:
  pin: 17                    # BCM pin number (2-27, avoid 2,3,14,15)
  mode: button               # button or switch
  trigger_on: both           # both, on_only, off_only (switch mode only)
  bounce_time: 0.05          # seconds, 0.01-0.3 range

print:
  source_folder: /home/admin/ducky-printer-project/print_files
  cooldown: 5                # seconds between activations
```

**Loading with defaults pattern (no Pydantic):**

```python
import yaml
from dataclasses import dataclass, field

@dataclass
class GpioConfig:
    pin: int = 17
    mode: str = 'button'        # 'button' or 'switch'
    trigger_on: str = 'both'    # 'both', 'on_only', 'off_only'
    bounce_time: float = 0.05

@dataclass
class PrintConfig:
    source_folder: str = '/home/admin/ducky-printer-project/print_files'
    cooldown: int = 5

def load_config(path):
    defaults = {'gpio': GpioConfig(), 'print': PrintConfig()}
    try:
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return defaults  # Use all defaults if no config file
    # Merge raw into defaults, validate, return
```

**Key points:**
- `yaml.safe_load()` always -- never `yaml.load()` (security risk: arbitrary code execution).
- Dataclasses provide typed defaults without external dependencies.
- Missing config file is not an error; use defaults.
- Validate after loading: pin range, mode enum, path existence, cooldown > 0.

### Random File Selection

```python
import random
from pathlib import Path

SUPPORTED_EXTENSIONS = {'.txt', '.png', '.jpg', '.jpeg', '.bmp'}

def select_random_file(folder: str) -> Path:
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise FileError(f"Source folder not found: {folder}")

    files = [
        f for f in folder_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        raise FileError(f"No printable files in: {folder}")

    return random.choice(files)
```

**Key points:**
- Re-scan folder on every activation. No caching. Picks up new files immediately.
- Filter by supported extensions matching v0.1 capabilities.
- `iterdir()` is more efficient than `glob('*')` when filtering in code anyway.
- Handle empty folder explicitly. This will happen and needs a clear error.

### systemd Service File

```ini
# /etc/systemd/system/ducky-printer.service
[Unit]
Description=Ducky Printer GPIO trigger service
After=multi-user.target

[Service]
Type=simple
User=admin
Group=admin
SupplementaryGroups=gpio
WorkingDirectory=/home/admin/ducky-printer-project
ExecStart=/usr/bin/python3 -u -m src.gpio_listener
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Key points:**
- Place in `/etc/systemd/system/` (user-managed), not `/lib/systemd/system/` (package-managed).
- `python3 -u` disables output buffering so logs appear in journald immediately.
- `User=admin` runs as the project user, not root. `SupplementaryGroups=gpio` grants GPIO access.
- `Restart=on-failure` with `RestartSec=5` recovers from crashes without tight restart loops.
- `After=multi-user.target` ensures basic system is up. No network dependency needed.
- `Type=simple` is correct for a long-running `signal.pause()` process.

## Complexity Assessment

### LOW Complexity (1-2 hours each)
- YAML config loading with `safe_load()` + dataclass defaults
- Config validation (type checks, range checks, enum checks)
- GPIO button mode with `when_pressed` callback
- GPIO switch mode with `when_activated`/`when_deactivated`
- Cooldown timer (timestamp comparison)
- Random file selection with `pathlib` + `random.choice`
- systemd service file (static configuration)
- Logging setup with Python `logging` module

### MEDIUM Complexity (3-6 hours each)
- Dual mode support (button/switch) with runtime mode selection
- Config hot-reload on SIGHUP
- Integration testing on actual Pi hardware with real button
- systemd watchdog integration

### HIGH Complexity (deferred)
- Web interface (Flask + WiFi AP setup) -- explicitly out of scope
- Configuration web panel -- out of scope
- Multiple GPIO pin support -- anti-feature

## Dependencies on Existing v0.1 Functionality

### Direct Dependencies
- **`src.printer.print_file(filename, folder, ...)`** -- Called by random file selector after choosing a file. This is the only integration point with v0.1.
- **`src.file_handler.resolve_filepath()`** -- May be reused for path resolution, or random selector handles paths directly.
- **Supported file extensions** -- Must match what v0.1's `print_file()` accepts: .txt, .png, .jpg, .jpeg, .bmp.

### Integration Approach
- **Import, don't subprocess:** Call `src.printer.print_file()` directly as a Python function. Avoids subprocess overhead and gives direct access to exceptions.
- **Per-job USB lifecycle:** v0.1 already opens and closes USB connection per print. This is correct for GPIO-triggered prints too -- no connection pooling needed.
- **Error propagation:** Catch `PrinterError` and `FileError` from v0.1 in the GPIO callback. Log the error. Do not crash the service.

### No Changes Required to v0.1
- Print pipeline remains as-is
- USB detection unchanged
- File handling unchanged
- Error types unchanged

**Design principle:** New code wraps v0.1 print_file(). GPIO listener and config are new modules that compose with, not modify, existing code.

## Sources

### GPIO and gpiozero
- [gpiozero API - Input Devices (v2.0.1)](https://gpiozero.readthedocs.io/en/stable/api_input.html)
- [gpiozero Basic Recipes](https://gpiozero.readthedocs.io/en/stable/recipes.html)
- [gpiozero FAQ - Keeping scripts running, systemd](https://gpiozero.readthedocs.io/en/stable/faq.html)
- [gpiozero Migration from RPi.GPIO](https://gpiozero.readthedocs.io/en/stable/migrating_from_rpigpio.html)
- [Software debounce drops edge events - Issue #1039](https://github.com/gpiozero/gpiozero/issues/1039)
- [Debouncing best practices - Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=370376)
- [GPIO trouble when running as systemd service](https://forums.raspberrypi.com/viewtopic.php?p=2339274)

### systemd Service Configuration
- [Ultimate guide to systemd autostart on Raspberry Pi](https://www.thedigitalpictureframe.com/ultimate-guide-systemd-autostart-scripts-raspberry-pi/)
- [Auto Start Python Script on Raspberry Pi](https://linuxconfig.org/how-to-autostart-python-script-on-raspberry-pi)
- [How to Autorun Python on Boot Using systemd](https://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/)

### YAML Configuration
- [Best practices for Python configuration management 2025](https://toxigon.com/best-practices-for-python-configuration-management)
- [Working with YAML Files in Python - Better Stack](https://betterstack.com/community/guides/scaling-python/yaml-files-in-python/)
- [PyYAML on PyPI](https://pypi.org/project/PyYAML/)

### Random File Selection
- [Python: Best way to choose a random file from a directory](https://gist.github.com/3811448)
- [pathlib - Python Official Documentation](https://docs.python.org/3/library/pathlib.html)

---
*Feature research for: GPIO print trigger with config, random selection, and systemd service*
*Researched: 2026-03-19*
