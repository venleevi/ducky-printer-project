# Technology Stack — v0.2 Additions

**Project:** Ducky Thermal Printer POC
**Milestone:** v0.2 - User-Triggered Printing
**Researched:** 2026-03-13
**Platform:** Raspberry Pi 3B+ (ARM, Bookworm OS)
**Existing Stack:** Python 3.13.5, python-escpos 3.0+, pyusb 1.0+

## Executive Summary

**New capabilities:** GPIO button trigger, web interface, WiFi access point hosting
**Stack additions:** gpiozero (GPIO), Flask (web), NetworkManager (WiFi AP)
**Philosophy:** Lightweight, minimal dependencies, integrate with existing Python codebase
**Confidence:** HIGH (all libraries officially supported, Raspberry Pi 3B+ compatible, Python 3.13 compatible)

---

## New Stack Components

### GPIO Button Handling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **gpiozero** | 2.0.1 | GPIO input device abstraction | Official Raspberry Pi Foundation library, high-level API simplifies button event detection, built-in debounce support, replaces deprecated RPi.GPIO |
| **lgpio** (backend) | latest | Low-level GPIO access | Required backend for gpiozero on modern Raspberry Pi OS, kernel-level GPIO operations |

**Rationale:**
- gpiozero is the official 2026 recommendation from Raspberry Pi engineers ([gpiozero documentation](https://gpiozero.readthedocs.io/))
- RPi.GPIO is deprecated and doesn't work on Raspberry Pi 5; gpiozero ensures future compatibility ([Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=376663))
- Clean event-driven API: `button.when_pressed = callback` vs manual polling ([gpiozero recipes](https://gpiozero.readthedocs.io/en/stable/recipes.html))
- Built-in `bounce_time` parameter handles switch debouncing in software ([gpiozero API docs](https://gpiozero.readthedocs.io/en/stable/api_input.html))
- Python 3.9+ support confirmed; works with Python 3.13 ([gpiozero PyPI](https://pypi.org/project/gpiozero/))

**Integration with existing code:**
```python
from gpiozero import Button
from src.printer import print_file

def handle_button_press():
    print_file("/GEN26_BILLPRINTER/wish1.png")

button = Button(17, bounce_time=0.05)  # GPIO 17, 50ms debounce
button.when_pressed = handle_button_press
```

### Web Server

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Flask** | 3.1.3 | Lightweight web framework | Minimal, Python-native, official Python 3.9+ support, 2026-current release, micro-framework philosophy matches simple single-button UI |
| **Waitress** | latest | Production WSGI server | Pure Python (no compilation), Windows/Linux compatible, single-process multi-threaded (low memory footprint on Pi 3B+), officially documented Flask deployment method |

**Rationale:**
- Flask 3.1.3 released Feb 2026, actively maintained, Python 3.13 compatible ([Flask PyPI](https://pypi.org/project/Flask/))
- Micro-framework design: minimal boilerplate for single-page interface ([Flask documentation](https://flask.palletsprojects.com/))
- Waitress chosen over Gunicorn because it's pure Python (no C compilation), lower resource usage on constrained devices ([Flask deployment docs](https://flask.palletsprojects.com/en/stable/deploying/waitress/))
- Gunicorn doesn't support Windows (irrelevant here) but has higher memory overhead due to pre-fork worker model ([Gunicorn vs Waitress comparison](https://stackshare.io/stackups/gunicorn-vs-waitress))
- **CRITICAL:** Never use Flask development server (`app.run()`) in production — it's insecure, single-threaded, exposes debug info ([Flask deployment security](https://flask.palletsprojects.com/en/stable/deploying/))

**Integration with existing code:**
```python
from flask import Flask, render_template
from src.printer import print_file

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('button.html')

@app.route('/print', methods=['POST'])
def trigger_print():
    print_file("/GEN26_BILLPRINTER/wish1.png")
    return {"status": "success"}

# Production: waitress-serve --host=0.0.0.0 --port=8080 app:app
```

### WiFi Access Point

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **NetworkManager** (nmcli) | system | WiFi AP configuration | Native to Raspberry Pi OS Bookworm, replaces legacy hostapd/dnsmasq stack, single command AP setup, built-in DHCP/DNS |
| **WPA2-PSK** | - | WiFi security | Maximum compatibility with Android/iOS, WPA3 not supported on Pi 3B+, CCMP encryption standard |

**Rationale:**
- NetworkManager is default on Raspberry Pi OS Bookworm (2023+), replacing dhcpcd/wpa_supplicant ([Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=357998))
- Single `nmcli` command creates AP vs multi-service hostapd/dnsmasq configuration ([nmcli WiFi guide](https://www.jeffgeerling.com/blog/2023/nmcli-wifi-on-raspberry-pi-os-12-bookworm))
- Built-in IPv4 sharing mode (`ipv4.method shared`) provides DHCP automatically ([NetworkManager hotspot setup](https://waltsworkbench.com/securing-a-wifi-hotspot-with-wpa2-using-networkmanager-on-a-raspberry-pi-running-bookworm-aka-debian-12/))
- 2.4GHz band (bg) for maximum device compatibility; 5GHz (a) not universally supported on older phones ([RaspberryTips AP guide](https://raspberrytips.com/access-point-setup-raspberry-pi/))
- **IMPORTANT:** Must specify band explicitly (`802-11-wireless.band bg`) — "automatic" causes connection failures ([Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=357998))

**No additional Python packages required** — system configuration only.

**Setup command:**
```bash
sudo nmcli con add type wifi ifname wlan0 mode ap con-name ducky-ap \
  ssid "DuckyPrinter" \
  802-11-wireless.band bg \
  802-11-wireless.channel 6 \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "your-password-here" \
  ipv4.method shared \
  ipv4.address 192.168.4.1/24 \
  ipv6.method disabled \
  autoconnect true
```

---

## Installation

### System Dependencies (one-time)
```bash
# GPIO library (may be pre-installed on Raspberry Pi OS)
sudo apt-get update
sudo apt-get install -y python3-lgpio

# NetworkManager (pre-installed on Bookworm, verify)
which nmcli || sudo apt-get install -y network-manager
```

### Python Packages (add to requirements.txt)
```bash
# GPIO control library (official Raspberry Pi recommendation for 2026)
gpiozero==2.0.1

# Lightweight web framework for single-button interface
Flask==3.1.3

# Production WSGI server (pure Python, low memory footprint)
waitress>=3.0.2
```

### Full Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure WiFi AP (one-time, persists across reboots)
sudo nmcli con add type wifi ifname wlan0 mode ap con-name ducky-ap \
  ssid "DuckyPrinter" \
  802-11-wireless.band bg \
  802-11-wireless.channel 6 \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "ducky2026" \
  ipv4.method shared \
  ipv4.address 192.168.4.1/24 \
  ipv6.method disabled \
  autoconnect true

# Activate AP
sudo nmcli con up ducky-ap
```

---

## Anti-Patterns to Avoid

### ❌ Don't: Use Flask development server in production
**Why:** Single-threaded, insecure, exposes debug info, crashes under load
**Instead:** Use Waitress: `waitress-serve --host=0.0.0.0 --port=8080 app:app`

### ❌ Don't: Use RPi.GPIO library
**Why:** Deprecated, incompatible with Raspberry Pi 5, no future support
**Instead:** Use gpiozero with lgpio backend

### ❌ Don't: Omit band specification in NetworkManager AP
**Why:** "automatic" band causes connection failures on many devices
**Instead:** Explicitly set `802-11-wireless.band bg` for 2.4GHz

### ❌ Don't: Use WPA3 on Raspberry Pi 3B+
**Why:** Hardware doesn't support WPA3, causes devices to fail authentication
**Instead:** Use WPA2-PSK (`wifi-sec.key-mgmt wpa-psk`)

### ❌ Don't: Skip button debouncing
**Why:** Physical switches bounce, causing multiple trigger events
**Instead:** Set `bounce_time=0.05` (50ms typical for quality switches)

### ❌ Don't: Run Flask with debug=True in production
**Why:** Exposes interactive debugger with code execution capabilities
**Instead:** Remove `debug=True` or set `FLASK_ENV=production`

### ❌ Don't: Use legacy hostapd/dnsmasq on Bookworm
**Why:** NetworkManager conflicts, deprecated workflow, more complex
**Instead:** Use NetworkManager's native AP mode via nmcli

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| GPIO | gpiozero 2.0.1 | RPi.GPIO | Deprecated, doesn't work on Pi 5, lower-level API |
| GPIO | gpiozero 2.0.1 | pigpio | Requires daemon, more complex, overkill for simple button |
| Web Framework | Flask 3.1.3 | Django | Too heavy for single-page app, database overhead |
| Web Framework | Flask 3.1.3 | FastAPI | Async complexity unnecessary, larger dependencies |
| Web Framework | Flask 3.1.3 | http.server (stdlib) | No routing, manual request parsing, production-unsuitable |
| WSGI Server | Waitress | Gunicorn | Pre-fork model = higher memory, no Windows support |
| WSGI Server | Waitress | uWSGI | Requires compilation, complex config, heavy for Pi 3B+ |
| WiFi AP | NetworkManager | hostapd + dnsmasq | Multi-service complexity, conflicts with NetworkManager, deprecated workflow |
| WiFi Security | WPA2-PSK | WPA3 | Pi 3B+ hardware doesn't support WPA3 |
| WiFi Security | WPA2-PSK | Open (no password) | Security risk, no user expects open printer AP |

---

## Configuration Recommendations

### GPIO Button
- **Pin:** GPIO 17 (physical pin 11) — avoid special-purpose pins (I2C, SPI, UART)
- **Pull resistor:** Use internal pull-up (`pull_up=True`, default) with button grounding the pin
- **Debounce:** Start with 50ms (`bounce_time=0.05`), adjust if multiple triggers occur
- **Hold time:** Consider `hold_time=2.0` if long-press needed for confirmation

### Web Interface
- **Host:** `0.0.0.0` (all interfaces) — allows access via WiFi AP
- **Port:** `8080` (non-privileged) — avoids needing root for port 80
- **Workers:** Single process, 4 threads (Waitress default) — adequate for 1-5 concurrent users
- **Timeout:** 30s request timeout — printing completes in <5s typically

### WiFi Access Point
- **SSID:** `DuckyPrinter` — descriptive, unique
- **Password:** Minimum 8 characters, WPA2 requirement
- **Channel:** 1, 6, or 11 (non-overlapping 2.4GHz channels) — avoid interference
- **IP Range:** `192.168.4.1/24` — avoids common router ranges (192.168.0.x, 192.168.1.x)
- **Band:** `bg` (2.4GHz) — maximum compatibility vs `a` (5GHz, less compatible)

---

## Resource Footprint

| Component | Memory (MB) | CPU (idle) | Notes |
|-----------|-------------|------------|-------|
| gpiozero | <1 | <1% | Event-driven, sleeps between events |
| Flask + Waitress | ~30-50 | <5% | Single process, 4 threads |
| NetworkManager AP | ~10-20 | <2% | System service, already running |
| **Total NEW** | ~40-70 | <8% | Acceptable on Pi 3B+ (1GB RAM, quad-core) |

**Baseline:** python-escpos + USB overhead ~20-40MB
**v0.2 Total:** ~60-110MB (well within Pi 3B+ 1GB RAM)

---

## Testing Considerations

### GPIO Button Testing
- **Mock gpiozero in tests:** Use `pytest-mock` to mock `Button` class, avoid GPIO hardware dependency
- **Test debounce logic:** Simulate rapid button presses, verify single callback execution
- **Test button hold:** Mock `when_held` callback if implementing long-press

### Web Interface Testing
- **Flask test client:** Use `app.test_client()` for route testing without server startup
- **Mock printer calls:** Patch `print_file()` to avoid USB printer requirement in web tests
- **CORS not needed:** Single-origin (AP-hosted), no cross-origin requests

### Integration Testing
- **End-to-end:** Requires real hardware (GPIO, USB printer, WiFi AP)
- **Staging:** Test on spare Pi 3B+ before production deployment
- **Network isolation:** AP mode doesn't require internet, simplifies testing

---

## Security Notes

### WiFi Access Point
- **WPA2-PSK encryption:** Industry standard, supported by all modern devices
- **Hidden SSID not recommended:** Security through obscurity, breaks device compatibility
- **MAC filtering not implemented:** Low security value, high maintenance overhead
- **No internet sharing:** `ipv4.method shared` provides DHCP but no NAT/routing (by design)

### Web Interface
- **No authentication:** Single-button interface, AP password provides physical access control
- **No HTTPS:** Local network only, certificate management overhead unjustified
- **CSRF not needed:** POST endpoint has no session/cookies, no persistent state
- **Input validation:** Hardcoded file path (`wish1.png`), no user input to sanitize

### General
- **Principle of least privilege:** Web server runs as non-root user
- **No remote access:** WiFi AP is isolated, no internet connection
- **Physical security:** Raspberry Pi should be in secured location

---

## Version Compatibility

| Component | Min Python | Max Python | Raspberry Pi OS | Notes |
|-----------|------------|------------|-----------------|-------|
| gpiozero 2.0.1 | 3.9 | 3.13+ | Bookworm, Bullseye | Dropped Python 2.x in v2.0 |
| Flask 3.1.3 | 3.9 | 3.13+ | Any | Dropped Python 3.8 in v3.1.0 |
| Waitress 3.0.2 | 3.8 | 3.13+ | Any | Pure Python, platform-agnostic |
| NetworkManager | - | - | Bookworm+ | Default since Bookworm (2023) |

**Current project:** Python 3.13.5 ✅ All components compatible

---

## Migration Path (v0.1 → v0.2)

### No Breaking Changes
- Existing `src/printer.py`, `src/file_handler.py`, `src/print_job.py` **unchanged**
- python-escpos integration **untouched**
- CLI interface **preserved**

### Additive Changes
```
src/
├── printer.py          # Existing (no changes)
├── file_handler.py     # Existing (no changes)
├── print_job.py        # Existing (no changes)
├── triggers/           # NEW
│   ├── gpio_trigger.py    # Button handler
│   └── web_trigger.py     # Flask app
└── config.py           # NEW (enable/disable triggers)
```

### Configuration System
```python
# config.py
ENABLE_GPIO_BUTTON = True
ENABLE_WEB_INTERFACE = True
GPIO_PIN = 17
WEB_PORT = 8080
PRINT_FILE = "/GEN26_BILLPRINTER/wish1.png"
```

---

## Next Phase Considerations

### What's NOT Included (Deliberately)
- **Database:** No persistent state needed (stateless printing)
- **Async framework:** Printing is synchronous I/O, no benefit from async
- **ORM:** No database, no ORM needed
- **Template engine beyond Jinja2:** Flask includes Jinja2, adequate for single button HTML
- **CSS framework:** Single button doesn't justify Bootstrap/Tailwind overhead
- **JavaScript framework:** Vanilla JS `fetch()` adequate for single POST request
- **Logging framework:** Python `logging` stdlib sufficient
- **Monitoring/metrics:** Out of scope for v0.2 POC

### Future Extensibility
If v0.3+ requires:
- **File selection UI:** Flask + Jinja2 templates scale to multi-page forms
- **Print queue:** Add lightweight job queue (e.g., `rq` with Redis)
- **Remote management:** Add Flask-Login for authentication, HTTPS with Let's Encrypt
- **Analytics:** Add lightweight SQLite logging via `sqlite3` stdlib

---

## Sources

### Official Documentation
- [gpiozero 2.0.1 Documentation](https://gpiozero.readthedocs.io/en/stable/)
- [Flask 3.1.x Documentation](https://flask.palletsprojects.com/en/stable/)
- [Flask Deployment - Waitress](https://flask.palletsprojects.com/en/stable/deploying/waitress/)
- [Raspberry Pi Configuration](https://www.raspberrypi.com/documentation/computers/configuration.html)

### Library Information
- [gpiozero PyPI](https://pypi.org/project/gpiozero/)
- [Flask PyPI](https://pypi.org/project/Flask/)
- [Flask Changelog](https://flask.palletsprojects.com/en/stable/changes/)

### Tutorials & Guides
- [gpiozero Basic Recipes](https://gpiozero.readthedocs.io/en/stable/recipes.html)
- [gpiozero Button API](https://gpiozero.readthedocs.io/en/stable/api_input.html)
- [Migrating from RPi.GPIO to gpiozero](https://gpiozero.readthedocs.io/en/stable/migrating_from_rpigpio.html)
- [Build a Python Web Server with Flask](https://projects.raspberrypi.org/en/projects/python-web-server-with-flask)
- [Securing WiFi Hotspot with WPA2 on Bookworm](https://waltsworkbench.com/securing-a-wifi-hotspot-with-wpa2-using-networkmanager-on-a-raspberry-pi-running-bookworm-aka-debian-12/)
- [Turn Your Raspberry Pi into an Access Point (Bookworm Ready)](https://raspberrytips.com/access-point-setup-raspberry-pi/)
- [nmcli for WiFi on Raspberry Pi OS Bookworm](https://www.jeffgeerling.com/blog/2023/nmcli-wifi-on-raspberry-pi-os-12-bookworm)

### Community Resources
- [Raspberry Pi Forums - GPIO Libraries](https://forums.raspberrypi.com/viewtopic.php?t=376663)
- [Raspberry Pi Forums - NetworkManager Hotspot](https://forums.raspberrypi.com/viewtopic.php?t=357998)
- [gpiozero vs RPi.GPIO Discussion](https://forums.raspberrypi.com/viewtopic.php?t=204466)
- [Gunicorn vs Waitress Comparison](https://stackshare.io/stackups/gunicorn-vs-waitress)

### Technical Articles
- [Why GPIO Zero Is Better Than RPi.GPIO](https://www.makeuseof.com/tag/gpio-zero-raspberry-pi/)
- [Flask Deployment Security Considerations](https://flask.palletsprojects.com/en/stable/deploying/)
- [GPIO Programming on Raspberry Pi - Python Libraries](https://medium.com/geekculture/gpio-programming-on-the-raspberry-pi-python-libraries-e12af7e0a812)

---

## Confidence Assessment

| Area | Confidence | Rationale |
|------|------------|-----------|
| GPIO (gpiozero) | **HIGH** | Official Raspberry Pi documentation, active maintenance, 2026-current recommendation |
| Web (Flask) | **HIGH** | v3.1.3 released Feb 2026, official Python 3.13 support, widespread production use |
| WSGI (Waitress) | **HIGH** | Officially documented Flask deployment method, pure Python compatibility verified |
| WiFi AP (NetworkManager) | **MEDIUM-HIGH** | Default Bookworm method, some users report connection issues (band config resolves) |
| Python 3.13 compatibility | **HIGH** | All libraries explicitly support Python 3.9+, 3.13.5 verified on device |
| Raspberry Pi 3B+ compatibility | **HIGH** | All libraries widely used on Pi 3B+, no Pi 5-specific requirements |

**Overall Confidence:** HIGH — Stack validated with official sources, version compatibility confirmed, platform requirements met.

---

## Decision Summary

**For v0.2 milestone, add three focused libraries:**

1. **gpiozero 2.0.1** — GPIO button events (official 2026 recommendation)
2. **Flask 3.1.3** — Lightweight web framework (single-page interface)
3. **Waitress 3.0.2+** — Production WSGI server (low-resource footprint)

**NetworkManager (system-level)** — WiFi AP configuration (no Python packages)

**Total new dependencies:** 3 Python packages, ~40-70MB RAM footprint
**Integration:** Zero breaking changes to existing v0.1 code
**Philosophy:** Minimal, lightweight, official, well-documented, Raspberry Pi-optimized
