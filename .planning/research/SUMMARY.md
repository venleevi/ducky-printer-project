# Project Research Summary

**Project:** Ducky Thermal Printer v0.2 - GPIO Print Trigger
**Domain:** Raspberry Pi GPIO-triggered thermal printing with YAML configuration and systemd service management
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project extends an existing Python thermal printer POC (v0.1, which prints files via CLI) to add physical button/switch-triggered random printing. The v0.2 milestone adds GPIO input handling via gpiozero 2.0.1 (the only viable GPIO library on Raspberry Pi OS Bookworm with kernel 6.6+), YAML-based configuration via PyYAML, random file selection from a source folder, and systemd service management for headless auto-start operation. The entire addition requires only two new pip packages (gpiozero, PyYAML) with approximately 20-30MB idle RAM overhead.

The recommended approach is strictly additive: four new Python modules (config.py, file_picker.py, trigger_handler.py, gpio_listener.py) compose with the existing v0.1 print pipeline without modifying any existing code. The architecture follows an event-driven pattern where gpiozero's Button class detects GPIO edge transitions, fires callbacks through a cooldown guard, picks a random printable file, and calls the existing `printer.print_file()` function. A trigger_handler module acts as an integration seam that future trigger sources (web interface in v0.3) can also use. Config is loaded once at startup from YAML with sensible defaults, and the daemon runs under systemd with automatic restart on failure.

The primary risk is GPIO button reliability with the lgpio backend on Pi 3B+. An open gpiozero issue (#1090) reports phantom triggers and missed presses with the LGPIOFactory. Mitigations include generous bounce_time (0.3s), application-level cooldown (5s default), and a fallback to polling-based GPIO reading if event callbacks prove unreliable. All other stack components (PyYAML, stdlib random, systemd) are high-confidence with well-documented patterns. The usblp kernel driver conflict is a known deployment pitfall that must be addressed via module blacklisting before the systemd service can operate reliably.

## Key Findings

### Recommended Stack

v0.2 adds two pip packages to the existing v0.1 foundation. gpiozero 2.0.1 is the only viable GPIO library on Bookworm (RPi.GPIO is broken on kernel 6.6+, pigpio requires a daemon, direct lgpio lacks high-level abstractions). PyYAML 6.0.2+ is the standard Python YAML library with confirmed Python 3.13 support. Everything else uses stdlib or system-level tooling.

**Core technologies:**
- **gpiozero 2.0.1**: GPIO button/switch event detection -- official Raspberry Pi Foundation recommendation, built-in Button class with debounce and callbacks
- **lgpio 0.2.2.0** (system apt package): Low-level GPIO backend for gpiozero on Bookworm -- must use system package via `--system-site-packages` venv, not the broken PyPI version
- **PyYAML >=6.0.2**: YAML configuration parsing -- always use `yaml.safe_load()`, never `yaml.load()`
- **systemd**: Auto-start daemon management -- native to Bookworm, handles restart-on-failure, logging via journald
- **stdlib random + pathlib**: Random file selection -- zero additional dependencies

**Critical stack constraint:** Virtual environments MUST use `--system-site-packages` to inherit the working system lgpio package. The PyPI lgpio (0.0.0.2) is broken.

### Expected Features

**Must have (table stakes):**
- YAML config loading with sensible defaults (works without editing config)
- Config validation at startup (fail fast with clear errors on headless Pi)
- GPIO button mode with software debounce (core use case: press button, get print)
- GPIO switch mode with configurable triggers (both/on_only/off_only transitions)
- Cooldown between activations (5s default, prevents paper waste)
- Random file selection from source folder (filtered by supported extensions)
- systemd auto-start on boot (headless operation is the whole point)
- Structured logging to journald (only debugging interface on headless Pi)
- Graceful shutdown on SIGTERM (clean GPIO release)

**Should have (add after v0.2 core is validated):**
- No-repeat random selection (avoid same file twice in a row)
- Default config generation on first run (commented example YAML)
- Config hot-reload via SIGHUP for non-hardware settings
- systemd watchdog integration

**Defer (v0.3+):**
- Visual confirmation LED (requires additional hardware)
- Web interface for print triggering (explicitly deferred per PROJECT.md)
- Print history/statistics
- Hold-to-print safety pattern

### Architecture Approach

The architecture is a clean layered design with strict dependency direction. Four new modules are added to the flat `src/` layout. `config.py` is the foundation with zero internal dependencies. `file_picker.py` handles directory scanning and random selection. `trigger_handler.py` orchestrates pick-and-print as an integration seam between event sources and the existing print pipeline. `gpio_listener.py` is the daemon entry point that sets up gpiozero callbacks, enforces cooldown, and blocks on `signal.pause()`. No existing v0.1 code is modified.

**Major components:**
1. **config.py** -- Load YAML with `safe_load()`, validate fields, return typed Config dataclass with defaults
2. **file_picker.py** -- List printable files by extension, `random.choice()` selection, handle empty folder gracefully
3. **trigger_handler.py** -- Orchestrate pick + print, catch PrinterError/FileError, return result dict (integration seam for future triggers)
4. **gpio_listener.py** -- gpiozero Button setup for button/switch mode, cooldown enforcement, `signal.pause()` daemon loop
5. **ducky-printer.service** -- systemd unit with GPIO device ordering, `SupplementaryGroups=gpio`, `KillSignal=SIGINT`

### Critical Pitfalls

1. **Script exits immediately without `signal.pause()`** -- gpiozero callbacks run in background threads; main thread must block indefinitely. Without this, the systemd service enters a crash-restart loop. Use `signal.pause()`, never `while True: time.sleep()`.

2. **usblp kernel driver claims USB printer** -- Linux auto-loads usblp on printer plug-in, blocking python-escpos raw USB access. Must blacklist usblp permanently via `/etc/modprobe.d/blacklist-usblp.conf` and create udev rules for permissions.

3. **Concurrent button presses causing multiple prints** -- Mechanical bounce (5-40ms) plus rapid intentional presses can fire multiple callbacks. Layer three defenses: gpiozero `bounce_time=0.3`, application-level cooldown (5s), and error handling around USB access.

4. **systemd environment differs from interactive shell** -- Missing modules, wrong paths, no venv activation. Specify full Python path in ExecStart, set WorkingDirectory, set `GPIOZERO_PIN_FACTORY=lgpio` environment variable explicitly.

5. **lgpio pin factory mismatch** -- gpiozero defaults to lgpio on Bookworm but fails if lgpio is not available (e.g., venv without `--system-site-packages`). Set pin factory explicitly in systemd service and ensure system lgpio package is installed.

## Implications for Roadmap

Based on research, the suggested phase structure follows the dependency graph identified in ARCHITECTURE.md. Each phase is independently testable without hardware (except the final phase).

### Phase 1: Configuration Foundation
**Rationale:** Zero external dependencies, pure Python. Every other module depends on config. Must be built first per dependency graph.
**Delivers:** `config.py` with `load_config()` returning Config dataclass, `config/config.yaml` with documented defaults, comprehensive test suite
**Addresses:** YAML config loading (P1), config validation (P1), sensible defaults (P1)
**Avoids:** Hardcoded values anti-pattern, `yaml.load()` security vulnerability, YAML boolean interpretation trap (`on`/`off` parsed as booleans)

### Phase 2: Random File Selection
**Rationale:** Pure Python (pathlib + random), no GPIO or printer hardware needed. Second leaf node in dependency graph.
**Delivers:** `file_picker.py` with `pick_random_file()` and `list_printable_files()`, test suite covering empty folder, single file, unsupported extensions, nonexistent folder
**Addresses:** Random file selection (P1), supported extension filtering
**Avoids:** `random.choice()` on empty list (IndexError crash), TOCTOU race on file deletion, .DS_Store/thumbs.db junk file selection

### Phase 3: Trigger Handler (Integration Seam)
**Rationale:** Creates the bridge between event sources and existing print pipeline. Testable via mocks without GPIO or printer hardware. Establishes the pattern that future web triggers will also use.
**Delivers:** `trigger_handler.py` with `handle_print_trigger(config)`, error handling for PrinterError/FileError, result dict format, test suite with mocked printer and file picker
**Addresses:** DRY integration point, error propagation without crashing daemon
**Avoids:** Direct printer access from callbacks, unhandled exceptions killing the daemon

### Phase 4: GPIO Listener
**Rationale:** Depends on all previous modules. GPIO mocking with `gpiozero.pins.mock.MockFactory` enables unit testing without hardware. This is the most complex phase due to gpiozero issue #1090 uncertainty.
**Delivers:** `gpio_listener.py` with button/switch mode, cooldown enforcement, `signal.pause()` daemon loop, test suite with MockFactory
**Addresses:** GPIO button mode (P1), GPIO switch mode (P1), cooldown (P1), dual-mode support, configurable switch triggers
**Avoids:** Script exits immediately (no signal.pause()), RPi.GPIO usage, polling-based GPIO (CPU waste), tight bounce_time values

### Phase 5: systemd Service and Deployment
**Rationale:** Pure deployment concern. All application code is testable before this phase. Requires actual Raspberry Pi hardware for validation.
**Delivers:** `systemd/ducky-printer.service` unit file, usblp blacklist configuration, installation documentation, logging verification
**Addresses:** Auto-start on boot (P1), logging to journald (P1), graceful shutdown (P1)
**Avoids:** systemd environment mismatch, usblp driver conflict, pin factory mismatch, missing GPIO device ordering (`After=dev-gpiochip0.device`)

### Phase Ordering Rationale

- **Config first** because every other module reads from it. Zero risk, pure Python, fast to build and test.
- **File picker second** because it is the other leaf dependency -- pure Python, no hardware, independently testable.
- **Trigger handler third** because it depends on file picker and existing printer code, and must be validated before GPIO wiring connects to it.
- **GPIO listener fourth** because it depends on config and trigger handler. This is where the gpiozero #1090 risk surfaces, so all downstream code should already be solid.
- **systemd last** because it is deployment infrastructure, not application logic. Testing requires real Pi hardware.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (GPIO Listener):** gpiozero issue #1090 (button reliability with LGPIOFactory on Pi 3B) is an open issue. May need to implement polling fallback if event callbacks are unreliable. Validate early on hardware.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Config):** Standard YAML + dataclass pattern. Well-documented, no unknowns.
- **Phase 2 (File Picker):** stdlib pathlib + random. Trivial.
- **Phase 3 (Trigger Handler):** Thin orchestration layer calling existing code. Pattern is clear.
- **Phase 5 (systemd):** Standard Linux service management. Documented templates available in STACK.md.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **MEDIUM-HIGH** | gpiozero is the only viable option but has open reliability issue #1090 on Pi 3B. PyYAML, stdlib, systemd are all HIGH confidence. |
| Features | **HIGH** | Feature set is well-scoped. Clear table stakes vs differentiators. All P1 features are low complexity. |
| Architecture | **HIGH** | Clean dependency graph, additive-only integration, no modifications to v0.1. Build order is unambiguous. |
| Pitfalls | **HIGH** | 8 critical pitfalls identified with specific prevention strategies and verification steps. All sourced from official docs and community reports. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **gpiozero button reliability on Pi 3B+ (issue #1090):** The lgpio backend may produce phantom triggers or miss presses. Generous bounce_time and application cooldown mitigate this, but hardware validation is essential. If callbacks are unreliable, fall back to polling `button.is_pressed` in a loop. This cannot be resolved through research alone -- it requires on-device testing.

- **lgpio in virtual environments:** The system lgpio package (0.2.2.0) works, but the PyPI version (0.0.0.2) is broken. The `--system-site-packages` workaround is documented but easy to forget. Consider adding a startup check that verifies lgpio version.

- **usblp blacklist persistence:** The kernel module blacklist must survive OS updates. Verify that `/etc/modprobe.d/blacklist-usblp.conf` persists across `apt upgrade` and potential kernel updates on Bookworm.

- **Switch initial state on daemon start:** When the daemon starts with a toggle switch already in the ON position, should it trigger a print? Research is unclear on the expected UX. Recommend: do NOT trigger on startup; only respond to transitions after the daemon is running.

## Sources

### Primary (HIGH confidence)
- [gpiozero 2.0.1 Documentation](https://gpiozero.readthedocs.io/en/stable/) -- Button API, pin factories, MockFactory, FAQ
- [gpiozero Input Devices API](https://gpiozero.readthedocs.io/en/stable/api_input.html) -- Button class, bounce_time, when_pressed/when_released
- [PyYAML PyPI](https://pypi.org/project/PyYAML/) -- Version compatibility, safe_load documentation
- [systemd.service man page](https://www.freedesktop.org/software/systemd/man/systemd.service.html) -- Service configuration, Type=simple, Restart behavior
- [PyYAML yaml.load() Deprecation](https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation) -- Security guidance

### Secondary (MEDIUM confidence)
- [gpiozero #1090: Button class broken with LGPIOFactory](https://github.com/gpiozero/gpiozero/issues/1090) -- Open issue affecting Pi 3B reliability
- [raspberrypi/linux #6037: GPIO.add_event_detect broken on kernel 6.6](https://github.com/raspberrypi/linux/issues/6037) -- Confirms RPi.GPIO is dead
- [lgpio in virtual environments](https://forums.raspberrypi.com/viewtopic.php?t=358841) -- Confirms --system-site-packages requirement
- [systemd service with GPIO permissions](https://forums.raspberrypi.com/viewtopic.php?p=2339274) -- Service file with gpiochip ordering
- [Raspberry Pi Forums - debouncing best practices](https://forums.raspberrypi.com/viewtopic.php?t=370376) -- Timing recommendations
- [USB printer Resource busy](https://github.com/pyusb/pyusb/issues/76) -- usblp conflict documentation

### Aggregated from Research Files
- STACK.md: 14 sources (official docs, PyPI, GitHub issues, community forums)
- FEATURES.md: 12 sources (API docs, tutorials, forums, configuration guides)
- ARCHITECTURE.md: 8 sources (official docs, existing codebase analysis, systemd patterns)
- PITFALLS.md: 18 sources (forums, GitHub issues, security advisories, troubleshooting guides)

**Total unique sources:** 45+ across all research files

---
*Research completed: 2026-03-19*
*Ready for roadmap: yes*
