# Pitfalls Research

**Domain:** Adding GPIO button/switch triggers, YAML config, systemd service, and random file selection to existing Python USB thermal printer system on Raspberry Pi 3B+
**Researched:** 2026-03-19
**Confidence:** HIGH

Research verified against gpiozero 2.0.1 official documentation, Pi forum community reports, PyYAML security advisories, and systemd documentation. Focused exclusively on v0.2 milestone scope (no web interface, no WiFi AP).

---

## Critical Pitfalls

### Pitfall 1: Script Exits Immediately Without signal.pause()

**What goes wrong:**
The GPIO listener script starts, registers `when_pressed` callbacks, then immediately exits because there is nothing keeping the main thread alive. When run as a systemd service, systemd reports the service as failed or keeps restarting it in a tight loop.

**Why it happens:**
gpiozero's `when_pressed` callbacks run in background threads. The main thread finishes executing, Python exits, GPIO pins are released, and the daemon thread dies. Developers test interactively with `python -i script.py` (which keeps the REPL alive) and never notice the problem until deploying as a service.

**How to avoid:**
- End the main script with `signal.pause()` from Python's `signal` module -- this blocks the main thread indefinitely while still allowing signal handling (SIGTERM for clean shutdown)
- Use `Type=simple` in the systemd service file (the default), which expects the ExecStart process to remain running
- Never use `while True: time.sleep(1)` as a keepalive -- it wastes CPU and does not handle signals cleanly

**Warning signs:**
- systemd shows service as `inactive (dead)` immediately after starting
- Service restart loop in `journalctl -u your-service`
- Works in interactive terminal but not as a service

**Phase to address:**
GPIO listener implementation -- this is the core daemon loop pattern and must be correct from the first working version.

---

### Pitfall 2: Using RPi.GPIO Instead of gpiozero on Pi 3B+

**What goes wrong:**
Code written with RPi.GPIO works today on Pi 3B+ but is a dead end. RPi.GPIO is deprecated, will not work on Pi 5, and accesses hardware registers directly (bypassing the Linux kernel GPIO interface), which can cause conflicts with other GPIO consumers. Its debounce handling (`bouncetime` parameter) is also notoriously unreliable -- it sometimes fires callbacks while the switch is still bouncing.

**Why it happens:**
The majority of Raspberry Pi GPIO tutorials (2014-2022) use RPi.GPIO. Developers copy older examples without checking current recommendations. RPi.GPIO still works on Pi 3B+, so there is no immediate error.

**How to avoid:**
- Use gpiozero (v2.0+) with lgpio backend -- this is the officially recommended stack as of Raspberry Pi OS Bookworm
- gpiozero's `Button` class provides built-in debounce (`bounce_time` parameter in seconds), pull-up configuration, and both `when_pressed` callback and `wait_for_press` blocking patterns
- If on Bullseye (older OS), gpiozero falls back to RPi.GPIO backend transparently -- the API stays the same
- Set `GPIOZERO_PIN_FACTORY=lgpio` environment variable in the systemd service to avoid ambiguous fallback behavior

**Warning signs:**
- `import RPi.GPIO` in any source file
- Warnings about deprecated libraries in logs
- GPIO code that uses `GPIO.setmode()`, `GPIO.setup()`, `GPIO.add_event_detect()` directly

**Phase to address:**
GPIO listener implementation -- choose the right library from day one.

---

### Pitfall 3: USB Printer "Device Busy" from usblp Kernel Driver Conflict

**What goes wrong:**
python-escpos fails with `[Errno 16] Resource busy` or `[Errno 13] Access denied` because the Linux `usblp` kernel module has already claimed the USB printer interface. The existing v0.1 CLI works with `sudo` but the systemd service fails, or works intermittently.

**Why it happens:**
When a USB printer is plugged in, the Linux kernel automatically loads the `usblp` driver and claims the USB interface. python-escpos (via pyusb/libusb) needs raw USB access to the same interface, causing a conflict. This is the single most common issue reported on the Raspberry Pi Forums for python-escpos.

**How to avoid:**
- Blacklist the `usblp` kernel module permanently:
  ```
  echo "blacklist usblp" | sudo tee /etc/modprobe.d/blacklist-usblp.conf
  sudo modprobe -r usblp
  ```
- Create a udev rule for the Citizen CT-S310IIEBK to set permissions:
  ```
  SUBSYSTEM=="usb", ATTRS{idVendor}=="2730", ATTRS{idProduct}=="0fff", MODE="0666"
  ```
  (Verify actual vendor/product IDs with `lsusb`)
- The existing codebase uses class-7 auto-detection which makes it harder to create targeted udev rules -- consider adding a udev rule that matches USB printer class generically
- Document the `usblp` blacklist as a required setup step

**Warning signs:**
- `USBError: [Errno 16] Resource busy` in logs
- `dmesg | grep usblp` shows the kernel driver claiming the device
- Works with `sudo` but not as regular user
- Works after `sudo modprobe -r usblp` but fails after reboot

**Phase to address:**
systemd service / deployment phase -- must be resolved before the service can run reliably on boot.

---

### Pitfall 4: Concurrent Button Presses Triggering Multiple Print Jobs

**What goes wrong:**
User presses the button once but 2-5 print jobs execute. Or user presses the button during an active print job and the second job collides with the first, causing USB errors or corrupted output.

**Why it happens:**
Two separate issues compound:
1. **Mechanical switch bounce:** Physical contacts bounce for 5-40ms, generating multiple edge transitions. Even gpiozero's `bounce_time` may not fully eliminate this for cheap switches.
2. **No cooldown enforcement:** Without a cooldown timer, rapid legitimate presses or bounce-triggered callbacks all result in print jobs. The existing printer code uses per-job open-print-close lifecycle, but two overlapping jobs will both try to open the USB device.

**How to avoid:**
- Use gpiozero's `Button(pin, bounce_time=0.3)` for hardware-level debounce (300ms is a safe default for most switches)
- Implement application-level cooldown using a timestamp check: reject any trigger within N seconds of the last accepted trigger (configurable via YAML, default 5 seconds per PROJECT.md)
- Use a `threading.Lock` or boolean flag around the print execution path to prevent overlapping jobs
- The existing per-job USB lifecycle (open-print-close) in `printer.py` is correct and must be preserved -- just gate entry to it

**Warning signs:**
- Multiple identical print jobs in quick succession
- `USBError` or `PrinterError` in logs shortly after a button press
- Print output garbled or cut short

**Phase to address:**
GPIO listener implementation -- cooldown and debounce are core requirements listed in PROJECT.md.

---

### Pitfall 5: PyYAML yaml.load() Arbitrary Code Execution

**What goes wrong:**
Using `yaml.load()` instead of `yaml.safe_load()` allows arbitrary Python object instantiation from YAML files. A malicious or malformed config file can execute arbitrary code on the Pi.

**Why it happens:**
PyYAML's `yaml.load()` has been unsafe since 2006 (CVE-2017-18342, CVE-2020-14343). Even `FullLoader` (the default since PyYAML 5.1) has known RCE exploits. Many tutorials and Stack Overflow examples still show `yaml.load()` without specifying a safe loader.

**How to avoid:**
- Always use `yaml.safe_load()` -- never `yaml.load()`, never `yaml.load(data, Loader=yaml.FullLoader)`
- For writing YAML: use `yaml.safe_dump()` correspondingly
- `safe_load` supports all the YAML types needed for config (strings, numbers, booleans, lists, dicts) -- no functionality is lost for a config file
- Add a linting rule or code review check for any bare `yaml.load()` calls

**Warning signs:**
- Any use of `yaml.load()` without `Loader=yaml.SafeLoader` in the codebase
- PyYAML deprecation warnings in logs

**Phase to address:**
Configuration system implementation -- get this right in the first line of YAML-handling code.

---

### Pitfall 6: random.choice() on Empty Directory

**What goes wrong:**
`random.choice(os.listdir(path))` raises `IndexError` when the source folder is empty or contains no printable files. The service crashes or enters a restart loop.

**Why it happens:**
Developers test with files present and never test the empty-directory case. The source folder might be empty on first boot, after a USB drive is removed, or if file extensions don't match supported types. Additionally, there is a TOCTOU race condition: a file can be deleted between listing and opening.

**How to avoid:**
- Filter the file list to supported extensions (.txt, .png, .jpg, .jpeg, .bmp) before selecting
- Check that the filtered list is non-empty before calling `random.choice()`; if empty, log a warning and return gracefully (do not crash)
- Wrap the file-open operation in a try/except to handle the race condition where a file disappears after listing
- Consider what happens when the same file is selected repeatedly in a small folder -- document whether this is acceptable behavior or if a "no repeat" mechanism is needed

**Warning signs:**
- `IndexError: Cannot choose from an empty sequence` in logs
- Service crashes when source folder is empty
- Service crashes intermittently when files are being added/removed from the folder

**Phase to address:**
Random file selection implementation -- validate before selecting and handle all edge cases.

---

### Pitfall 7: systemd Service Environment Differs from Interactive Shell

**What goes wrong:**
The Python script works perfectly when run manually (`python3 -m src.print_job`) but fails under systemd with `ModuleNotFoundError`, wrong file paths, or permission errors.

**Why it happens:**
systemd services run with a minimal environment: no user shell profile, no PATH customizations, no virtual environment activation, and potentially a different working directory. If python-escpos or other packages are installed in a user's local site-packages (pip install --user) or a venv, systemd's Python cannot find them.

**How to avoid:**
- Specify the full path to the Python interpreter in `ExecStart` (e.g., `/usr/bin/python3` or the venv python)
- Set `WorkingDirectory=` in the service file to the project root
- Set `Environment=` for any needed variables (PATH, PYTHONPATH, GPIOZERO_PIN_FACTORY)
- If using a virtual environment, use the venv's Python directly: `ExecStart=/path/to/venv/bin/python3 ...`
- Install system-wide packages with `sudo pip3 install` (or `apt install python3-pyyaml python3-gpiozero`) to avoid user-local-only installs
- Test the exact ExecStart command manually with `sudo -u <service-user> env -i /bin/bash -c '<ExecStart command>'` to simulate the minimal environment

**Warning signs:**
- `ModuleNotFoundError` in `journalctl -u your-service`
- `FileNotFoundError` for config files using relative paths
- Service works with `sudo python3 script.py` but not via systemd

**Phase to address:**
systemd service implementation -- test in simulated minimal environment before writing the service file.

---

### Pitfall 8: GPIO Pin Factory Mismatch on Different OS Versions

**What goes wrong:**
gpiozero fails to initialize with errors like `BadPinFactory`, `No module named 'lgpio'`, or `.lgd-nfy` permission errors. The script works on one Pi but not another, or works after a fresh install but breaks after an OS update.

**Why it happens:**
gpiozero 2.0 defaults to lgpio as the pin factory on Bookworm, but falls back to RPi.GPIO on Bullseye. If lgpio is not installed (e.g., in a virtual environment that does not inherit system packages), gpiozero either falls back silently to a different backend or crashes. The lgpio library needs read/write access to `/dev/gpiochip0`, which may not be available to non-root users without proper group membership.

**How to avoid:**
- Explicitly set the pin factory in the systemd service: `Environment=GPIOZERO_PIN_FACTORY=lgpio`
- Ensure lgpio is installed: `sudo apt install python3-lgpio` (system package, not pip)
- Add the service user to the `gpio` group: `sudo usermod -a -G gpio <user>`
- If running as root (for USB access), this is less of an issue, but still set the pin factory explicitly for predictability
- Document the minimum OS version and required system packages

**Warning signs:**
- `BadPinFactory` exception on startup
- `No module named 'lgpio'` error
- GPIO works as root but not as service user
- `PinFactoryFallback` warning in logs

**Phase to address:**
GPIO listener implementation -- verify pin factory works in the target environment before building on it.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Running systemd service as root | Avoids all USB/GPIO permission issues | Security risk, files created as root, harder to debug | Acceptable for v0.2 single-purpose appliance if documented. Add udev rules in future milestone. |
| No config file validation | Faster to implement, fewer lines of code | Typos in config cause cryptic runtime errors hours later | Never -- validate on startup, fail fast with clear error messages |
| Hardcoding default config values in multiple places | Quick to start | Values drift between code and example config, confusing behavior | Never -- single source of truth for defaults, either in code or in a default config file |
| Using `time.sleep()` loop instead of `signal.pause()` | More intuitive for beginners | Wastes CPU, does not handle SIGTERM cleanly, complicates shutdown | Never -- signal.pause() is simpler and correct |
| Polling GPIO instead of edge detection | No threading complexity | Burns CPU continuously, higher latency, drains battery (if applicable) | Never for a daemon -- edge detection with callbacks is the correct pattern |
| No logging, only print() | Works in terminal | No diagnostics when running as systemd service (print goes nowhere useful without stdout redirect) | Never -- use Python logging module from the start |
| Catching bare Exception everywhere | Prevents crashes | Hides bugs, masks the actual error type | Only at the outermost daemon loop as a last resort; use specific exceptions internally |

---

## Integration Gotchas

Common mistakes when connecting GPIO triggers to the existing printer system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| GPIO callback to printer | Calling `print_file()` directly inside `when_pressed` callback | Call print function from the callback but wrap with cooldown check and lock; keep callback fast |
| YAML config to GPIO setup | Reading config at import time (module level) | Load config explicitly in main(), pass values to GPIO setup functions |
| systemd to Python script | Using `python3 script.py` without full paths | Use absolute paths for interpreter, script, config file, and working directory |
| Config file location | Relative path like `config.yaml` | Absolute path or path relative to a known base (WorkingDirectory in systemd) |
| Random selection to print_file() | Passing just the filename without the folder | Use `os.path.join(source_folder, selected_file)` or pass both as the existing API expects |
| Switch mode (on/off) | Treating switch like a button (edge detect only) | Read initial state on startup, then respond to edges; handle both transitions per config |
| Printer error in callback | Letting PrinterError propagate and crash the daemon | Catch PrinterError in callback, log it, continue listening for next trigger |
| YAML boolean gotchas | Using `on`/`off`/`yes`/`no` as string values | YAML interprets these as booleans; quote them: `mode: "on_only"` or use different terminology |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Re-scanning directory on every button press | Noticeable delay before printing starts | Cache file list, refresh on configurable interval or use a simple timer | Source folder with 1000+ files |
| Opening/closing USB on every print | 200-500ms overhead per job | Acceptable with per-job lifecycle (existing pattern); do not try to keep connection open -- it causes more problems than it solves | Not a real issue at expected usage rate |
| Loading large images synchronously in callback | Button feels unresponsive, 2-5 second delay | Acceptable for thermal printer use case; user expects some delay. Log timing for diagnostics. | Images over 5MB on Pi 3B+ |
| No file type filtering before random.choice | Selecting .DS_Store, thumbs.db, or other junk files | Filter by supported extensions before selection | Any folder accessed via macOS/Windows |

---

## Security Mistakes

Domain-specific security issues for a headless Pi appliance.

| Mistake | Risk | Prevention |
|---------|------|------------|
| `yaml.load()` instead of `yaml.safe_load()` | Arbitrary code execution via malicious config file | Always use `yaml.safe_load()` |
| Running as root without necessity | Any bug becomes a root-level compromise | Acceptable for v0.2 (USB access), but use udev rules to drop to non-root in future |
| Config file world-writable | Any local user can change GPIO pins, source folder | Set config file permissions to 644 (owner read-write, others read-only) |
| Source folder traversal | Config points source_folder to `/etc` or `/` and the system tries to "print" arbitrary files | Validate that source_folder exists, is a directory, and optionally restrict to allowed paths |
| No validation of GPIO pin numbers | Invalid pin number could damage hardware or cause kernel errors | Validate pin number against known valid BCM pins for Pi 3B+ (2-27) |

---

## UX Pitfalls

Common user experience mistakes for a headless button-triggered printer.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No feedback after button press | User presses repeatedly, wastes paper or gets confused | Log each trigger; in future milestone, add LED feedback. For now, ensure cooldown prevents waste. |
| Silent failure when source folder is empty | Button press does nothing, user thinks device is broken | Log clearly: "No printable files found in /path/to/folder" |
| Config syntax error crashes service | Device stops working, user cannot diagnose without SSH | Validate config on startup, fall back to defaults if config is invalid, log the specific error |
| Cooldown with no indication | User presses button during cooldown, nothing happens | Log cooldown rejection. Future: LED blink pattern to indicate "busy" or "cooldown active". |
| Switch mode confusion | User flips switch expecting print, nothing happens because wrong transition is configured | Default to `both` for switch transitions; document the three modes clearly in example config |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **GPIO listener running:** Often missing `signal.pause()` -- verify: service stays running for 10+ minutes without restart
- [ ] **Button debounce working:** Often undertested -- verify: press button 10x rapidly, exactly 1 print job executes (or 2 if presses span cooldown boundary)
- [ ] **Switch mode working:** Often missing initial state read -- verify: flip switch to ON position, start service, verify it detects the already-ON state (or not, depending on design)
- [ ] **YAML config loading:** Often using `yaml.load()` -- verify: grep for `yaml.load` (should find zero hits, only `yaml.safe_load`)
- [ ] **Config validation:** Often missing -- verify: set `gpio_pin: 99` and confirm clear error message, not a crash
- [ ] **Empty folder handling:** Often crashes -- verify: empty the source folder, press button, confirm graceful handling with log message
- [ ] **systemd service on reboot:** Often missing `WantedBy=` or `enable` -- verify: reboot Pi, service starts automatically, button triggers print
- [ ] **Correct Python environment in systemd:** Often missing venv/path -- verify: `journalctl -u service` shows no import errors after fresh reboot
- [ ] **USB printer accessible from service:** Often blocked by usblp -- verify: service can print without manual `modprobe -r usblp` after reboot
- [ ] **Logging visible in journalctl:** Often using print() -- verify: `journalctl -u service` shows structured log messages with timestamps
- [ ] **Clean shutdown:** Often missing signal handler -- verify: `systemctl stop service` exits cleanly within 5 seconds, no zombie processes
- [ ] **YAML boolean trap:** Often unquoted -- verify: `mode: on_only` in config is read as string "on_only", not boolean True

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Script exits immediately (no signal.pause) | LOW | Add `from signal import pause` and `pause()` at end of main loop |
| Wrong GPIO library (RPi.GPIO) | MEDIUM | Rewrite GPIO code using gpiozero Button class; API is different but simpler |
| usblp kernel driver conflict | LOW | `echo "blacklist usblp" > /etc/modprobe.d/blacklist-usblp.conf` and reboot |
| Multiple prints from bounce | LOW | Add `bounce_time=0.3` to Button constructor, add cooldown timestamp check |
| yaml.load vulnerability | LOW | Find-and-replace `yaml.load` with `yaml.safe_load` |
| Empty folder IndexError | LOW | Add `if not files: log.warning(...); return` before `random.choice()` |
| systemd environment mismatch | LOW | Add `Environment=`, `WorkingDirectory=`, full path in `ExecStart=` to service file |
| Pin factory mismatch | LOW | Add `Environment=GPIOZERO_PIN_FACTORY=lgpio` to service file, install python3-lgpio |
| Config not validated | MEDIUM | Add validation function that checks all fields on startup; requires defining schema |
| Printer error crashes daemon | LOW | Wrap print call in try/except PrinterError, log and continue |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Script exits immediately | GPIO listener | Service stays running 10+ minutes: `systemctl status` shows active |
| Using RPi.GPIO instead of gpiozero | GPIO listener | No `import RPi.GPIO` in codebase; `import gpiozero` only |
| usblp kernel driver conflict | systemd / deployment | `lsmod | grep usblp` returns empty after reboot |
| Concurrent button presses | GPIO listener (cooldown) | 10 rapid presses = 1 print job; no USB errors in journal |
| yaml.load vulnerability | Configuration system | `grep -r "yaml.load" src/` returns zero results |
| Empty folder crash | Random file selection | Empty source folder + button press = log warning, no crash |
| systemd environment mismatch | systemd service | Fresh reboot, service starts, no import errors in journal |
| Pin factory mismatch | GPIO listener + systemd | `GPIOZERO_PIN_FACTORY` set in service file; works on clean boot |
| YAML boolean interpretation | Configuration system | Config value `on_only` survives round-trip as string, not bool |
| Printer error kills daemon | GPIO listener | Disconnect printer, press button, service continues running |
| No logging | All phases | `journalctl -u service -n 50` shows meaningful diagnostic output |

---

## Sources

**GPIO Library Selection:**
- [gpiozero 2.0.1 Documentation](https://gpiozero.readthedocs.io/)
- [gpiozero FAQ -- keeping scripts alive](https://gpiozero.readthedocs.io/en/stable/faq.html)
- [Migrating from RPi.GPIO to gpiozero](https://gpiozero.readthedocs.io/en/stable/migrating_from_rpigpio.html)
- [gpiozero vs RPi.GPIO -- Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=204466)
- [Newbie: gpio vs lgpio vs gpiozero -- Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=375971)
- [gpiozero + systemd Discussion #1153](https://github.com/gpiozero/gpiozero/discussions/1153)

**Button Debounce:**
- [GPIO debounce -- Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=137484)
- [raspberry-gpio-python Wiki / Inputs](https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/)
- [GPIO Zero performance with event detect -- Issue #227](https://github.com/RPi-Distro/python-gpiozero/issues/227)

**USB Printer / python-escpos:**
- [Errno 16 Resource busy -- pyusb Issue #76](https://github.com/pyusb/pyusb/issues/76)
- [Intermittent errno 16 resource busy -- Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=366058)
- [python-escpos Raspberry Pi documentation](https://python-escpos.readthedocs.io/en/v2.2.0/user/raspi.html)
- [USB Permissions Thermal Printer Error -- Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=363085)

**PyYAML Security:**
- [PyYAML yaml.load(input) Deprecation](https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation)
- [FullLoader still vulnerable to RCE -- PyYAML Issue #420](https://github.com/yaml/pyyaml/issues/420)
- [Testing vulnerable PyYAML versions -- Semgrep](https://semgrep.dev/blog/2022/testing-vulnerable-pyyaml-versions/)

**systemd Service Issues:**
- [Setting permissions for systemd service -- Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=355439)
- [Unable to write .service file for auto-boot -- Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=253291)
- [Why does systemd stop my service immediately](https://linuxvox.com/blog/why-is-systemd-stopping-service-immediately-after-it-is-started/)

**Pin Factory / OS Compatibility:**
- [Bookworm gpiozero and libgpiod -- Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=362804)
- [No module named lgpio -- gpiozero Issue #1120](https://github.com/gpiozero/gpiozero/issues/1120)
- [Pi 4 Bookworm GPIOZero not working -- Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=367867)

---

*Pitfalls research for: Adding GPIO triggers, YAML config, systemd service, and random file selection to Raspberry Pi 3B+ thermal printer system*

*Researched: 2026-03-19*

*Confidence Level Notes:*
- GPIO library choice (gpiozero over RPi.GPIO): HIGH confidence -- verified against official gpiozero docs and Raspberry Pi recommendations
- signal.pause() requirement: HIGH confidence -- documented in gpiozero FAQ, verified in systemd context
- usblp kernel driver conflict: HIGH confidence -- extensively documented across Pi Forums, python-escpos docs, and pyusb issues
- Button debounce patterns: HIGH confidence -- well-documented across multiple sources with specific timing values
- PyYAML safe_load: HIGH confidence -- multiple CVEs, official deprecation notice, widely verified
- random.choice empty list: HIGH confidence -- documented Python behavior, trivial to verify
- systemd environment issues: HIGH confidence -- extremely common, well-documented failure mode
- Pin factory behavior across OS versions: MEDIUM confidence -- verified for Bookworm/Bullseye but edge cases may exist with specific lgpio versions in virtual environments
