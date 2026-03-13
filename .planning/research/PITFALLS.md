# Pitfalls Research

**Domain:** Adding GPIO button triggers and WiFi AP hosting to Raspberry Pi thermal printer projects
**Researched:** 2026-03-13
**Confidence:** MEDIUM-HIGH

GPIO/WiFi research based on official documentation and community experience. Integration patterns extrapolated from python-escpos and general USB device behavior.

---

## Critical Pitfalls

### Pitfall 1: GPIO Callbacks Execute Sequentially, Not Concurrently

**What goes wrong:**
Multiple rapid button presses queue up and execute one-by-one in a single thread. If a print job takes 5 seconds and the user presses the button 3 times quickly, all three jobs will eventually execute even though the user expected only one.

**Why it happens:**
RPi.GPIO runs all callbacks sequentially in a single thread. Developers assume each button press is independent, but callbacks cannot run concurrently—they're queued and processed in order.

**How to avoid:**
- Implement explicit debouncing: track last execution time and ignore events within cooldown period
- Use a flag to indicate "print in progress" and reject new requests while true
- OR use a proper job queue (e.g., Python `queue.Queue`) and single worker thread that respects state

**Warning signs:**
- Observing the printer execute the same job multiple times after rapid button presses
- Print jobs continuing long after expected based on visible button presses

**Phase to address:**
Phase 1 (GPIO Button Implementation) - Prevent this from day one, don't retrofit later.

---

### Pitfall 2: USB Printer Lacks Thread-Safe Access in python-escpos

**What goes wrong:**
Concurrent access to the printer from multiple triggers (button + web interface) causes USB timeout errors, "device busy" failures, or corrupted print output. The printer connection blocks indefinitely or raises `OSError` on close.

**Why it happens:**
python-escpos does not implement thread safety. Two threads attempting to print simultaneously both try to acquire the USB device, leading to libusb1 errors. The existing project uses per-job lifecycle (open-print-close), which works for single-threaded CLI but breaks with concurrent triggers.

**How to avoid:**
- Implement a `threading.Lock()` wrapper around ALL printer operations (open, print, close)
- Use context managers: `with printer_lock: ...`
- Maintain the existing per-job connection pattern (open → print → close) but serialize access across threads
- Consider a single print queue with one worker thread that owns the printer

**Warning signs:**
- `USBTimeoutError` exceptions in logs
- Print jobs that hang indefinitely
- `OSError` when calling `printer.close()`
- Garbled or incomplete print output

**Phase to address:**
Phase 1 (GPIO Button) OR Phase 2 (Web Interface) - Must be addressed before BOTH triggers are enabled simultaneously. If implementing sequentially, add locking infrastructure when adding the second trigger.

---

### Pitfall 3: NetworkManager vs dhcpcd Conflict Breaking WiFi AP

**What goes wrong:**
After configuring hostapd with dhcpcd following older tutorials, the access point fails to start on boot or the static IP doesn't appear. WiFi AP works initially but breaks after reboot or OS update.

**Why it happens:**
Raspberry Pi OS Bookworm (2023+) switched from dhcpcd to NetworkManager as default network manager. The two services conflict when both try to manage the same interface. Older tutorials (2018-2022) all use dhcpcd+hostapd patterns that no longer work.

**How to avoid:**
- Check `cat /etc/os-release` to determine Pi OS version (Bullseye = dhcpcd, Bookworm = NetworkManager)
- **For Bookworm:** Use NetworkManager-native AP configuration (`nmcli` commands), not dhcpcd
- **For Bullseye:** Disable NetworkManager if using dhcpcd approach
- After creating hostapd config, run `sudo systemctl unmask hostapd` and `sudo systemctl enable hostapd` (hostapd is masked by default)
- Verify WiFi country code is set via `raspi-config` (rfkill soft-blocks WiFi otherwise)

**Warning signs:**
- SSID not appearing in WiFi scan
- `hostapd` service fails to start: check `/var/log/syslog`
- Static IP not assigned to `wlan0`: check for service conflicts
- WiFi works until reboot, then stops

**Phase to address:**
Phase 3 (WiFi AP Configuration) - Research OS version and choose correct method BEFORE writing configuration files.

---

### Pitfall 4: Flask Development Server in Production

**What goes wrong:**
The system becomes unstable under even modest load. Web interface stops responding after a few hours, or crashes when multiple users connect. Flask emits warning: "WARNING: This is a development server. Do not use it in a production deployment."

**Why it happens:**
Developers test with `app.run()` and assume it's suitable for always-on operation. Flask's dev server is single-threaded and not designed for 24/7 operation. It may work for demos but becomes unreliable over time.

**How to avoid:**
- Use production WSGI server: Gunicorn with 1-2 workers for Pi 3B+ resource constraints
- Example: `gunicorn --workers 2 --bind 0.0.0.0:80 app:app`
- For very minimal deployments, Waitress is lighter than Gunicorn
- Document in README that Flask dev server is dev/test only

**Warning signs:**
- Flask warning message in logs about development server
- Web interface becomes unresponsive after hours/days
- Single request blocking all other clients
- Memory usage slowly increasing over time

**Phase to address:**
Phase 2 (Web Interface Implementation) - Use production server from the start. It's easier than retrofitting.

---

### Pitfall 5: Inadequate Power Supply Causing Intermittent USB Failures

**What goes wrong:**
USB printer works fine initially but becomes unreliable: timeouts, "device not found" errors, or complete disconnections. Under-voltage lightning bolt icon appears. Problems worsen when WiFi AP is active and multiple clients connect.

**Why it happens:**
Raspberry Pi 3B+ with WiFi AP + USB thermal printer + GPIO operations draws significant current. Cheap power supplies or thin Micro USB cables cause voltage drop below 4.65V. The USB/LAN chip is the first component to fail when voltage drops. WiFi transmission spikes worsen the problem.

**How to avoid:**
- Use official Raspberry Pi power supply (5V 2.5A minimum for 3B+)
- Use short, thick Micro USB cable (thin cables have significant resistance)
- Disable WiFi power management: `sudo iwconfig wlan0 power off` (in systemd service or rc.local)
- Monitor voltage: `vcgencmd get_throttled` - any non-zero value indicates power issues
- If using existing power infrastructure, consider powering via GPIO pins (5V + GND) with proper voltage regulation

**Warning signs:**
- Under-voltage warning (lightning bolt) on Pi
- `vcgencmd get_throttled` returns non-zero
- USB printer disconnects/reconnects in `dmesg`
- Printer works reliably when plugged directly into wall, fails when on power strip/hub
- Ping latency spikes to 1000+ms with packet loss

**Phase to address:**
Phase 0 (Hardware Verification) - Verify BEFORE implementing triggers. Power issues will cause intermittent failures that are hard to debug.

---

### Pitfall 6: GPIO Pull Resistor Misconfiguration for Buttons

**What goes wrong:**
Button press detection is unreliable: false triggers when no one touches the button, or button presses that don't register. GPIO pin "floats" and picks up electromagnetic interference from nearby wiring or the printer.

**Why it happens:**
Buttons without pull resistors leave GPIO pins in undefined state between HIGH and LOW. Internal pull resistors are weak (50kΩ) and easily overcome by even short wires or environmental noise. Developer assumes internal pull-up is sufficient without testing in production environment with printer EMI.

**How to avoid:**
- Enable internal pull resistor: `GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)` for active-low buttons
- For reliable operation, add external 1-10kΩ pull resistor (I2C pins use 1.6kΩ reference)
- Add 1kΩ series protection resistor between button and GPIO to prevent damage if pin accidentally set to OUTPUT
- Test with printer actively running to verify EMI doesn't cause false triggers
- Keep button wiring short and away from power lines

**Warning signs:**
- Random print jobs without button press (check logs/timestamps)
- Button press sometimes fails to trigger (timing-dependent)
- Button works reliably when printer is off, unreliable when printer is running
- Different behavior with long vs short wires to button

**Phase to address:**
Phase 1 (GPIO Button Implementation) - Configure correctly from the start; resistor values are hard to change after PCB/wiring is finalized.

---

### Pitfall 7: Inadequate Software Debouncing (bouncetime Too Low)

**What goes wrong:**
Single button press triggers multiple print jobs. Logs show callback executed 2-5 times for one physical press. RPi.GPIO's `bouncetime` parameter doesn't prevent all bounce-related issues.

**Why it happens:**
Mechanical buttons physically bounce for 5-40ms, creating multiple transitions. RPi.GPIO's bounce handling is "notoriously weak" - it doesn't always wait long enough before reading the pin state, sometimes reading during bounce period. Default/low bouncetime values (e.g., 50ms) are insufficient for many switches.

**How to avoid:**
- Use `bouncetime=300` minimum for RPi.GPIO callbacks (200-300ms recommended)
- Implement additional application-level debouncing: track timestamp of last execution and ignore events within cooldown period
- Consider hardware debouncing: 0.1µF capacitor across button creates ~0.5ms filter
- Alternative: use `gpiod` library which does kernel-level debouncing (more reliable than userspace)
- Log all button events initially to tune debounce values for your specific switch

**Warning signs:**
- Multiple rapid callback executions for single press (check timestamps in logs)
- Number of callbacks varies (sometimes 1, sometimes 2-3) for identical button press
- Problem worse with certain button types or worn buttons

**Phase to address:**
Phase 1 (GPIO Button Implementation) - Test thoroughly with production hardware before considering "done". Emulated buttons won't reveal bounce issues.

---

### Pitfall 8: Flask + GPIO Interrupt Interaction Issues

**What goes wrong:**
When Flask web server is running, GPIO callbacks become unreliable or stop working entirely. Alternatively, GPIO interrupts cause Flask to behave erratically (jittery servo PWM reported in forums).

**Why it happens:**
Flask (especially with eventlet/async modes) and RPi.GPIO compete for thread/event loop control. GPIO callbacks setting Event objects may not wake threads waiting on those events when Flask's event loop is active. The two libraries' threading models conflict.

**How to avoid:**
- Use separate processes (not threads) for GPIO and web server, communicating via Unix signals, files, or message queue
- OR disable GPIO interrupts entirely when web server runs: use polling (`GPIO.input()`) in a dedicated thread instead
- If using Flask-SocketIO, test thoroughly with GPIO callbacks - known conflicts with eventlet async_mode
- Consider microservice pattern: GPIO script writes to queue/file, web server reads queue/file, printer service consumes queue

**Warning signs:**
- GPIO callbacks work before starting Flask, stop working after
- GPIO Event objects set but `wait()` never returns
- Web server requests blocked during GPIO callback execution
- PWM signals become unstable when web server handles requests

**Phase to address:**
Phase 2 (Web Interface) - Architecture decision needed BEFORE implementation. Difficult to refactor from threading to multiprocessing later.

---

### Pitfall 9: systemd Service Lacks Permissions for GPIO/USB

**What goes wrong:**
Systemd service that runs as non-root user fails with "Permission denied" when accessing GPIO pins or USB printer. Service works when run manually as `pi` user but fails when systemd starts it.

**Why it happens:**
GPIO and USB devices require specific group memberships (`gpio`, `lp`, `dialout`). Systemd services may run before groups are properly initialized or with minimal environment. udev rules may not have executed yet when service starts.

**How to avoid:**
- Add service user to required groups: `sudo usermod -a -G gpio,lp,dialout,video pi`
- Create udev rule for USB printer: `/etc/udev/rules.d/99-printer.rules`
  ```
  SUBSYSTEM=="usb", ATTR{idVendor}=="xxxx", ATTR{idProduct}=="yyyy", MODE="0666", GROUP="lp"
  ```
- For GPIO: `/etc/udev/rules.d/99-gpio.rules`
  ```
  SUBSYSTEM=="gpio", ACTION=="add", PROGRAM="/bin/sh -c 'chown -R pi:pi /sys%p'"
  ```
- Reload udev: `sudo udevadm control --reload-rules && sudo udevadm trigger`
- In systemd service file, add: `User=pi` and `Group=pi`
- Verify groups with: `groups pi`

**Warning signs:**
- Service fails with "Permission denied" on GPIO or USB access
- Manual `python script.py` works, `sudo systemctl start service` fails
- Different behavior between `sudo systemctl start` and `systemctl --user start`

**Phase to address:**
Phase 4 (Systemd Service/Auto-start) - Create udev rules and verify permissions before writing service file.

---

### Pitfall 10: WiFi AP Client Limit Causing Web Interface Failures

**What goes wrong:**
Web interface works for 1-2 clients but subsequent clients cannot connect to WiFi, or connection succeeds but web requests time out. Pi WiFi AP becomes unresponsive under modest load.

**Why it happens:**
Raspberry Pi 3B+ WiFi chipset has limited resources. Reports show 20-30 concurrent users as practical maximum. Combining WiFi AP duties with CPU-intensive print operations and USB I/O creates resource contention. All I/O (disk, network, USB) shares single USB bus on Pi 3B+.

**How to avoid:**
- Document WiFi AP client limit (2-3 concurrent clients recommended for print workload)
- Configure hostapd `max_num_sta=5` to prevent overload
- Monitor system load: `top` or `htop` during testing
- Consider client limits acceptable for use case: if this is single-user with occasional guests, 2-3 clients is fine
- If higher capacity needed, use external WiFi AP and connect Pi via Ethernet

**Warning signs:**
- Web interface stops responding when 3+ clients connected
- `top` shows CPU consistently >80% with WiFi active
- WiFi clients connect but cannot get DHCP lease (dnsmasq overload)
- Ping latency to Pi increases dramatically with each additional client

**Phase to address:**
Phase 3 (WiFi AP Configuration) - Set realistic limits from the start. Load testing should verify limits.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using Flask development server | Works immediately, no extra dependencies | Service instability, crashes, poor performance | Development/testing only, never production |
| Skipping thread locks on printer access | Simpler code, faster to implement | Random USB errors, corrupted prints, hard-to-debug failures | Only if truly single-threaded (no GPIO + web simultaneously) |
| Internal pull resistors only (no external) | No extra hardware, cheaper BOM | Unreliable button detection, EMI sensitivity | Prototyping only, or if button physically adjacent to Pi |
| Single global try-except for all GPIO/USB | Catches all errors, prevents crashes | Hides root causes, makes debugging impossible | Never - use specific exception handling |
| Skipping power supply verification | Assume any 5V supply works | Intermittent failures impossible to debug | Never - power issues cause 50%+ of Pi problems |
| Using dhcpcd method on Bookworm | Following familiar old tutorials | WiFi AP doesn't work, hours wasted debugging | Never - check OS version first |
| Polling GPIO instead of interrupts | Simpler to understand, no threading issues | Wasted CPU, higher latency | If web server has threading conflicts OR if latency <500ms is acceptable |
| No print queue, direct execution on trigger | Fewer moving parts, less code | Cannot prevent duplicate jobs, no cancellation, no status | Single-user scenario with physical access (can power cycle) |

---

## Integration Gotchas

Common mistakes when integrating GPIO triggers with existing printer system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| GPIO → Printer | Calling printer code directly from GPIO callback | Queue job in callback, process in separate thread with lock |
| Web → Printer | Each request creates new printer instance | Use singleton pattern or connection pool with lock |
| Button + Web triggers | Both directly call print function | Both add to shared queue, single worker thread dequeues |
| Systemd service startup | Starting service before USB devices ready | Add `After=multi-user.target` and `udev` rules for printer |
| Error handling | Catch exceptions in trigger, ignore printer errors | Log all errors, expose status via web interface or LED |
| Configuration | Hardcoded GPIO pins and printer endpoints | Config file for pins, printer selection, enable/disable triggers |
| File reading | Re-reading file on every button press | Cache file list, refresh only when folder changes (inotify/watchdog) |
| Connection lifecycle | Keeping printer connection open indefinitely | Maintain per-job pattern (open→print→close) but add locking |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| No GPIO debouncing | Multiple prints per button press | Implement 300ms software debounce + track last execution | Immediately with real buttons |
| Synchronous web request handling | One request blocks all others | Use async/await or Gunicorn workers | 2+ concurrent web clients |
| Linear printer search on every job | Slow startup, USB enumeration delays | Cache printer once at startup, reconnect only on error | 3+ print jobs/minute |
| Loading large images in callback | Button press hangs, other callbacks blocked | Preload/cache images, or queue job and load in worker | Images >100KB |
| No WiFi power management control | Random disconnections under load | Disable power management: `iwconfig wlan0 power off` | 2+ active WiFi clients |
| All services on Raspberry Pi | Pi overloaded, everything slow | Offload AP to separate hardware if >5 clients needed | 3+ concurrent WiFi + print jobs |
| No request timeout on web interface | Clients hang forever on printer errors | Set request timeout (5-10s), return error status | First printer error |
| Using 2.4GHz WiFi with USB3 devices (Pi 4) | WiFi becomes unreliable with USB activity | Use 5GHz WiFi, ferrite beads on USB cables, or switch to USB2 ports | Immediately on Pi 4 with USB3 |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Open WiFi AP without authentication | Anyone in range can trigger prints, waste paper/ink | Use WPA2-PSK with strong password, or MAC address filtering |
| Flask debug mode in production | Remote code execution via debug console | Set `app.debug = False`, use Gunicorn |
| No rate limiting on web endpoint | Attacker triggers thousands of prints | Rate limit: max 1 print per 10 seconds per client IP |
| Default Raspberry Pi password (`raspberry`) | SSH access, full system compromise | Change password immediately: `passwd`, or disable password auth |
| Running service as root | USB/GPIO bugs become privilege escalation | Run as `pi` user with group permissions, never root |
| Exposing Flask/Gunicorn directly to internet | DoS attacks, vulnerability scanning | Only bind to local WiFi AP network, never 0.0.0.0 on public interface |
| No input validation on print files | Malicious file crashes printer or Pi | Validate file types, size limits, sanitize filenames |
| Hardcoded WiFi password in code | Password exposed in git repo, logs | Use environment variables or config file outside git |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No feedback after button press | User presses multiple times, wastes paper | LED blinks during print, or buzzer confirms job queued |
| Button works but printer out of paper | Silent failure, user doesn't know why nothing printed | Check printer status before job, LED indicates errors |
| Web interface doesn't show print status | User submits job and wonders if it worked | Show "Printing...", "Complete", or "Error" status |
| No way to cancel queued jobs | User presses button 5x by mistake, must waste 5 prints | Hold button 3s to cancel queue, or cancel button on web UI |
| Error messages only in logs | Non-technical users cannot diagnose problems | Show errors on web interface: "Printer offline", "Out of paper" |
| WiFi SSID is default ("raspberrypi") | Confusing in environment with multiple Pis | Set descriptive SSID: "DuckyPrinter" or device-specific |
| No indication of WiFi AP status | User doesn't know if they should connect to Pi or router | LED pattern: slow blink = AP mode, solid = connected |
| Button requires exact timing | Frustrating to use, accessibility issues | Accept any press >100ms, provide tactile/audio feedback |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **GPIO button working:** Often missing debouncing, duplicate request prevention - verify: press button 10x rapidly, should only print once
- [ ] **Web interface responsive:** Often missing production server (using Flask dev server) - verify: run for 24 hours, test with 3 concurrent clients
- [ ] **WiFi AP configured:** Often missing hostapd unmask, country code - verify: reboot and check SSID appears, client can connect
- [ ] **Printer communication working:** Often missing thread lock for concurrent access - verify: trigger print from button AND web simultaneously
- [ ] **Print job execution:** Often missing error handling for printer offline/out of paper - verify: disconnect printer and trigger job
- [ ] **Systemd service enabled:** Often missing udev rules, group permissions - verify: works after fresh reboot without manual intervention
- [ ] **Power supply adequate:** Often untested with all components active - verify: WiFi AP + active print job + button press doesn't cause under-voltage
- [ ] **Button wiring:** Often missing pull resistors or has weak internal-only - verify: printer running, press button 20x, count false/missed triggers
- [ ] **Configuration system:** Often hardcoded values in source - verify: can change GPIO pin number without editing code
- [ ] **Logging configured:** Often using print() instead of proper logging - verify: systemd journal contains useful diagnostic info

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Multiple prints from one button press | LOW | Add timestamp check: `if time.time() - last_print < 2.0: return` |
| Flask dev server crashes | LOW | Install Gunicorn: `pip install gunicorn`, update startup script |
| NetworkManager/dhcpcd conflict | MEDIUM | Identify OS version, disable conflicting service, reconfigure AP with correct method |
| USB timeout errors from concurrent access | MEDIUM | Add `threading.Lock()`, wrap all printer operations: `with printer_lock: ...` |
| GPIO permission denied in systemd | LOW | Add user to gpio group, create udev rule, reload and restart |
| Under-voltage causing USB failures | MEDIUM | Replace power supply (official Pi supply), check cable quality, monitor with `vcgencmd` |
| WiFi AP doesn't start on boot | LOW | `sudo systemctl unmask hostapd`, `sudo systemctl enable hostapd`, check `/var/log/syslog` |
| Button false triggers from EMI | MEDIUM | Add external pull resistor (1-10kΩ), shorten wiring, add capacitor for hardware debounce |
| Web interface blocks on long print jobs | MEDIUM | Refactor to async handlers or use Gunicorn workers, return response before job completes |
| Printer connection blocks indefinitely | HIGH | Requires architecture change: timeout wrappers, separate process for printer, or queue-based design |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Sequential GPIO callbacks causing duplicates | Phase 1: GPIO Button | Rapid press test: 10x button press = 1 print job |
| USB printer thread safety | Phase 1 or 2 (before both triggers active) | Concurrent trigger test: button + web simultaneous |
| NetworkManager/dhcpcd conflict | Phase 3: WiFi AP Config | Check OS version, SSID appears after reboot |
| Flask development server | Phase 2: Web Interface | Use Gunicorn from start, 24hr uptime test |
| Power supply inadequacy | Phase 0: Before any implementation | `vcgencmd get_throttled` = 0 during full load |
| GPIO pull resistor config | Phase 1: GPIO Button | Button works reliably with printer running |
| Inadequate debouncing | Phase 1: GPIO Button | Bounce test with oscilloscope or logged timestamps |
| Flask + GPIO interrupt conflict | Phase 2: Web Interface | GPIO callbacks work with Flask running |
| systemd permissions | Phase 4: Auto-start | Service starts successfully after fresh boot |
| WiFi AP client limits | Phase 3: WiFi AP Config | Load test with 5 concurrent clients |

---

## Sources

**GPIO and Button Handling:**
- [GPIO debounce - Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=137484)
- [raspberry-gpio-python / Wiki / Inputs](https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/)
- [Raspberry Pi GPIO Interrupts Tutorial](https://roboticsbackend.com/raspberry-pi-gpio-interrupts-tutorial/)
- [Avoiding False Hits with RPi.GPIO Edge Detection](https://forums.raspberrypi.com/viewtopic.php?t=134394)
- [Using PullUp and PullDown Resistors on the Raspberry Pi](https://grantwinney.com/raspberry-pi-using-pullup-and-pulldown-resistors/)
- [Troubleshooting Internal Pull-Up Resistors](https://forums.raspberrypi.com/viewtopic.php?t=291350)

**WiFi Access Point Configuration:**
- [Create wireless access point - Raspberry Pi Guide](https://raspberrypi-guide.github.io/networking/create-wireless-access-point)
- [Trouble with access point IP address](https://forums.raspberrypi.com/viewtopic.php?t=326916)
- [Network Manager vs DHCPCD functionality](https://forums.raspberrypi.com/viewtopic.php?t=370235)
- [How to create wifi AP with NetworkManager on Bookworm](https://forums.raspberrypi.com/viewtopic.php?t=357998)

**Raspberry Pi 3B+ Performance and Limitations:**
- [Raspberry Pi 3B+ iPerf WiFi Performance](https://netbeez.net/blog/raspberry-pi-3b-iperf-wifi-performance/)
- [Performance evaluation of Raspberry Pi 3B as a web server (PDF)](https://www.diva-portal.org/smash/get/diva2:1439759/FULLTEXT01.pdf)
- [Is there a practical upper limit to number of concurrent USB devices?](https://forums.raspberrypi.com/viewtopic.php?t=313051)

**Flask and Web Server:**
- [Flask GPIO input button web and physical](https://forums.raspberrypi.com/viewtopic.php?t=296292)
- [flask with eventlet async_mode do not react on GPIO callbacks - Issue #1434](https://github.com/miguelgrinberg/Flask-SocketIO/issues/1434)
- [The Flask Mega-Tutorial, Part XVII: Deployment on Linux](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvii-deployment-on-linux-even-on-the-raspberry-pi)

**USB and Printer Issues:**
- [python-escpos GitHub](https://github.com/python-escpos/python-escpos)
- [printer.close issue - Issue #417](https://github.com/python-escpos/python-escpos/issues/417)
- [Python Thread Safety: Using a Lock](https://realpython.com/python-thread-lock/)
- [USB Permissions Thermal Printer Error](https://forums.raspberrypi.com/viewtopic.php?t=363085)

**Power Supply Issues:**
- [Resolving Under Voltage Issue](https://forums.raspberrypi.com/viewtopic.php?t=261802)
- [Extremely unreliable USB (includes the onboard ethernet)](https://forums.raspberrypi.com/viewtopic.php?f=28&t=61084)
- [Raspberry Pi Troubleshooting: 15 Expert Fixes You Need in 2026](https://www.whypi.org/raspberry-pi-troubleshooting/)

**System Permissions:**
- [Setup Raspberry Pi Hardware Permissions](https://roboticsbackend.com/raspberry-pi-hardware-permissions/)
- [setting udev rules for the GPIO](https://forums.raspberrypi.com/viewtopic.php?t=9667)
- [Understanding the udev rules](https://forums.raspberrypi.com/viewtopic.php?t=279731)

**Security:**
- [17 Security Tips to Protect Your Raspberry Pi](https://raspberrytips.com/security-tips-raspberry-pi/)
- [Raspberry Pi Configuration - Security Documentation](https://www.raspberrypi.org/documentation/configuration/security.md)

**Hardware Integration:**
- [Thermal Printer Interfacing with Raspberry Pi](https://circuitdigest.com/microcontroller-projects/thermal-printer-interfacing-with-raspberry-pi-zero-to-print-text-images-and-bar-codes)
- [Thermal-Printer-Buttons GitHub](https://github.com/almostsurelyape/Thermal-Printer-Buttons)

---

*Pitfalls research for: Adding GPIO button triggers and WiFi AP hosting to Raspberry Pi thermal printer projects*

*Researched: 2026-03-13*

*Confidence Level Notes:*
- GPIO debouncing, WiFi AP configuration, power supply issues: HIGH confidence (well-documented, verified across multiple sources)
- python-escpos threading behavior: MEDIUM confidence (inferred from general USB device patterns and reported issues, library lacks explicit thread-safety documentation)
- Flask/GPIO conflicts: MEDIUM confidence (documented issues exist, but specific to eventlet mode and may vary by configuration)
- Integration patterns: MEDIUM confidence (extrapolated from existing project structure and general best practices)
