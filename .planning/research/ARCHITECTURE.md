# Architecture Research

**Domain:** GPIO and Web Trigger Integration for Thermal Printer
**Researched:** 2026-03-13
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      Trigger Layer (v0.2)                         │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐              ┌─────────────────────────┐   │
│  │  GPIO Listener   │              │  Flask Web Server       │   │
│  │  (gpiozero)      │              │  (HTTP interface)       │   │
│  └────────┬─────────┘              └───────────┬─────────────┘   │
│           │ when_pressed callback              │ POST /print     │
│           └────────────┬───────────────────────┘                 │
│                        ↓                                          │
├────────────────────────────────────────────────────────────────────┤
│                    Shared Trigger Handler                        │
│                    (trigger_print_job.py)                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  • Load config (which triggers enabled)                  │    │
│  │  • Call existing print_file() from printer.py            │    │
│  │  • Handle errors and return status                       │    │
│  └────────────────────────────┬─────────────────────────────┘    │
│                               ↓                                   │
├──────────────────────────────────────────────────────────────────┤
│              Existing Printer Layer (v0.1) - REUSE               │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  print_file()   │  │  print_image()   │  │  print_text()  │  │
│  │  (dispatcher)   │  │  (USB + PIL)     │  │  (USB ESC/POS) │  │
│  └────────┬────────┘  └─────────┬────────┘  └────────┬───────┘  │
│           │                     │                     │           │
│           └─────────────────────┴─────────────────────┘           │
│                               ↓                                   │
├──────────────────────────────────────────────────────────────────┤
│                    USB Printer Communication                      │
│                    (python-escpos library)                        │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  • find_printer() - class 7 USB detection                │    │
│  │  • Per-job lifecycle: open() → print → cut() → close()  │    │
│  │  • Endpoints: in_ep=0x81, out_ep=0x02                   │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘

                               ↓
                    Citizen CT-S310IIEBK
                      (USB Thermal Printer)
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **GPIO Listener** | Detect physical button press events | gpiozero Button with when_pressed callback |
| **Flask Web Server** | HTTP interface for web-based print triggers | Flask app with POST /print endpoint |
| **Shared Trigger Handler** | Unified print logic called by both triggers | Python module with single function |
| **Config Reader** | Load settings (enabled triggers, file path) | YAML/JSON config file reader |
| **Existing Printer Layer** | Print operations (text/image routing) | printer.py - NO CHANGES NEEDED |
| **USB Communication** | Hardware communication with thermal printer | python-escpos Usb class |

## Recommended Project Structure

```
src/
├── print_job.py           # [v0.1] CLI entry point (UNCHANGED)
├── printer.py             # [v0.1] USB printer communication (UNCHANGED)
├── file_handler.py        # [v0.1] File operations (UNCHANGED)
├── config.py              # [v0.2] NEW - Config file reader
├── trigger_handler.py     # [v0.2] NEW - Shared print trigger logic
├── gpio_listener.py       # [v0.2] NEW - GPIO button daemon
└── web_server.py          # [v0.2] NEW - Flask web interface

config/
└── printer_config.yaml    # [v0.2] NEW - Configuration file

systemd/
├── gpio-listener.service  # [v0.2] NEW - GPIO daemon service
└── web-server.service     # [v0.2] NEW - Flask web service

tests/
├── test_config.py         # [v0.2] NEW - Config tests
├── test_trigger_handler.py # [v0.2] NEW - Trigger tests
├── test_gpio_listener.py  # [v0.2] NEW - GPIO tests
└── test_web_server.py     # [v0.2] NEW - Web server tests
```

### Structure Rationale

- **Existing v0.1 files remain unchanged**: The printer layer is already well-architected with clear separation of concerns
- **New v0.2 files are additive**: Integration happens through function calls, not modifications
- **config.py**: Single source of truth for configuration (which triggers enabled, file path)
- **trigger_handler.py**: DRY principle - both GPIO and web call the same function
- **Separate daemons**: GPIO listener and web server run as independent systemd services
- **Systemd service files**: Standard Linux pattern for auto-start and supervision

## Architectural Patterns

### Pattern 1: Event-Driven Triggers with Shared Handler

**What:** Multiple event sources (GPIO button, HTTP request) converge on a single trigger handler function that calls existing printer code.

**When to use:** When multiple input mechanisms need to perform the same action. Prevents code duplication and ensures consistent behavior across triggers.

**Trade-offs:**
- **Pros**: DRY principle, single point of logic change, consistent error handling
- **Cons**: Adds one level of indirection (trigger → handler → printer)

**Example:**
```python
# src/trigger_handler.py
from src.printer import print_file
from src.config import load_config

def handle_print_trigger(source: str) -> dict:
    """
    Unified print handler called by GPIO and web triggers.

    Args:
        source: "gpio" or "web" for logging

    Returns:
        dict with keys: success (bool), message (str)
    """
    try:
        config = load_config()

        # Check if trigger source is enabled
        if not config['triggers'][source]['enabled']:
            return {"success": False, "message": f"{source} trigger disabled"}

        # Call existing printer code (NO CHANGES to printer.py)
        file_path = config['print_file']
        print_file(file_path, rotate=True, target_width_cm=8, target_height_cm=18)

        return {"success": True, "message": f"Printed {file_path}"}

    except Exception as e:
        return {"success": False, "message": str(e)}
```

### Pattern 2: Callback-Based GPIO Event Handling

**What:** gpiozero's Button class with when_pressed callback for non-blocking event detection. Requires signal.pause() to keep process alive.

**When to use:** When detecting physical button presses without blocking the main thread. Standard pattern for GPIO input on Raspberry Pi.

**Trade-offs:**
- **Pros**: Non-blocking, runs callback in separate thread, built-in debouncing
- **Cons**: Requires daemon process with signal.pause(), callback must be thread-safe

**Example:**
```python
# src/gpio_listener.py
from gpiozero import Button
from signal import pause
import logging
from src.trigger_handler import handle_print_trigger

# GPIO pin 17 (physical pin 11)
button = Button(17, pull_up=True, bounce_time=0.1)

def on_button_press():
    """Callback executed in separate thread when button pressed."""
    logging.info("Button pressed - triggering print")
    result = handle_print_trigger(source="gpio")

    if result['success']:
        logging.info(f"Print successful: {result['message']}")
    else:
        logging.error(f"Print failed: {result['message']}")

# Assign callback (reference, not call)
button.when_pressed = on_button_press

logging.info("GPIO listener started on pin 17")

# Keep process alive to detect events
pause()
```

### Pattern 3: Lightweight Flask Web Server

**What:** Flask app with single POST endpoint, run with threading or gevent for concurrent requests. No database needed.

**When to use:** Simple web interface for triggering actions. Overkill for complex CRUD apps, perfect for trigger-based systems.

**Trade-offs:**
- **Pros**: Minimal dependencies, easy to test, works on Raspberry Pi 3B+
- **Cons**: Not suitable for high-traffic (but not needed for single-printer system)

**Example:**
```python
# src/web_server.py
from flask import Flask, request, jsonify, render_template
from src.trigger_handler import handle_print_trigger

app = Flask(__name__)

@app.route('/')
def index():
    """Serve simple HTML page with print button."""
    return render_template('index.html')

@app.route('/print', methods=['POST'])
def trigger_print():
    """HTTP endpoint to trigger print job."""
    result = handle_print_trigger(source="web")
    return jsonify(result), 200 if result['success'] else 500

if __name__ == '__main__':
    # host='0.0.0.0' allows access from WiFi clients
    # threaded=True handles concurrent requests (adequate for low traffic)
    app.run(host='0.0.0.0', port=5000, threaded=True)
```

### Pattern 4: Per-Job Connection Lifecycle (v0.1 - KEEP)

**What:** Open USB connection, print, close connection for each print job. Already implemented in printer.py.

**When to use:** USB devices that can enter busy state after power cycles. Critical for thermal printers.

**Trade-offs:**
- **Pros**: Prevents device busy errors, clean state per job
- **Cons**: Slight overhead per job (negligible for on-demand printing)

**Why keep:** Already working perfectly in v0.1. New triggers just call existing functions.

## Data Flow

### GPIO Print Flow

```
Physical Button Press (GPIO 17)
    ↓
gpiozero Button detects event
    ↓
when_pressed callback (separate thread)
    ↓
handle_print_trigger(source="gpio")
    ↓
Load config → Check GPIO enabled → Get file path
    ↓
print_file(filename, rotate=True, target_width_cm=8, target_height_cm=18)
    ↓
find_printer() → open() → print_image() → cut() → close()
    ↓
USB ESC/POS commands to Citizen CT-S310IIEBK
    ↓
Thermal printer outputs receipt
```

### Web Print Flow

```
User clicks "Print" button in browser
    ↓
JavaScript sends POST /print
    ↓
Flask route handler receives request
    ↓
handle_print_trigger(source="web")
    ↓
Load config → Check web enabled → Get file path
    ↓
print_file(filename, rotate=True, target_width_cm=8, target_height_cm=18)
    ↓
find_printer() → open() → print_image() → cut() → close()
    ↓
USB ESC/POS commands to Citizen CT-S310IIEBK
    ↓
Thermal printer outputs receipt
    ↓
JSON response {"success": true, "message": "..."}
    ↓
Browser displays success/error message
```

### Configuration Loading Flow

```
System Start
    ↓
systemd starts gpio-listener.service and web-server.service
    ↓
Each service imports trigger_handler.py
    ↓
First trigger call loads config/printer_config.yaml
    ↓
Config cached in memory for subsequent calls
    ↓
Triggers check if their source is enabled before proceeding
```

### Key Data Flows

1. **Config-driven trigger enablement:** Both GPIO and web check config before executing. Allows disabling triggers without code changes.

2. **Shared printer access:** Both triggers call the same printer functions. USB connection lifecycle ensures thread-safety through per-job connections.

3. **Independent daemon processes:** GPIO listener and web server run as separate systemd services. If one crashes, the other continues working.

## Integration Points

### New Code → Existing Code Integration

| Integration Point | New Component | Existing Component | How They Connect |
|-------------------|---------------|-------------------|------------------|
| **Print trigger** | trigger_handler.py | printer.print_file() | Function call with hardcoded params |
| **File resolution** | trigger_handler.py | file_handler.resolve_filepath() | Optional: validate file exists before printing |
| **Error handling** | trigger_handler.py | PrinterError, FileError exceptions | Catch and convert to dict response |
| **CLI compatibility** | gpio_listener.py, web_server.py | print_job.py | No conflicts - different entry points |

### External Integration Points

| External System | Integration Pattern | Notes |
|-----------------|---------------------|-------|
| **USB Printer** | python-escpos Usb class | Already working in v0.1 - NO CHANGES |
| **GPIO Hardware** | gpiozero Button class | Pin 17 (physical pin 11), pull-up resistor |
| **WiFi Clients** | Flask HTTP server on 0.0.0.0:5000 | Requires WiFi AP configured (hostapd/dnsmasq) |
| **systemd** | Service unit files with ExecStart | Auto-start daemons on boot, restart on failure |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **GPIO ↔ Trigger Handler** | Direct function call | Same process, callback runs in gpiozero thread |
| **Web ↔ Trigger Handler** | Direct function call | Same process, runs in Flask request thread |
| **Trigger Handler ↔ Printer** | Direct function call | Imports from printer.py, calls print_file() |
| **GPIO Daemon ↔ Web Daemon** | No direct communication | Independent processes, coordinated via USB printer access |

## Threading and Concurrency

### gpiozero Threading Model

- **Button detection:** gpiozero starts internal thread monitoring GPIO pin state
- **Callback execution:** when_pressed callback runs in separate thread
- **Thread safety:** trigger_handler.py must be thread-safe (per-job USB connections provide this)
- **Process lifetime:** signal.pause() keeps main thread alive indefinitely

### Flask Threading Model

- **Request handling:** Flask with threaded=True spawns thread per request
- **Concurrency limit:** Threading mode adequate for low traffic (1-10 req/sec)
- **Alternative:** Could use gevent for higher concurrency, but unnecessary for single-user printer
- **Thread safety:** Same as GPIO - per-job USB connections provide thread safety

### USB Printer Thread Safety

- **Per-job connections:** Each print call opens new USB connection
- **No shared state:** printer.py has no global printer instance
- **Automatic serialization:** USB bus serializes concurrent access at kernel level
- **Implication:** Both triggers can call printer simultaneously without explicit locking

## Configuration Design

### Recommended Format: YAML

**Why YAML:**
- Human-readable for editing on Raspberry Pi
- Supports comments for documentation
- Standard for DevOps/system configuration
- Python PyYAML library widely available

**Example config/printer_config.yaml:**
```yaml
# Thermal Printer Trigger Configuration

# Which file to print (relative to print_files folder)
print_file: "wish1.png"

# Print options for image
print_options:
  rotate: true
  target_width_cm: 8.0
  target_height_cm: 18.0

# Enable/disable trigger sources
triggers:
  gpio:
    enabled: true
    pin: 17  # Physical pin 11
  web:
    enabled: true
    port: 5000
```

### Config Loading Pattern

```python
# src/config.py
import yaml
from pathlib import Path
from typing import Dict, Any

_config_cache: Dict[str, Any] = None

def load_config(config_path: str = "/home/admin/ducky-printer-project/config/printer_config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file with caching."""
    global _config_cache

    if _config_cache is None:
        with open(config_path, 'r') as f:
            _config_cache = yaml.safe_load(f)

    return _config_cache

def reload_config(config_path: str = "/home/admin/ducky-printer-project/config/printer_config.yaml") -> Dict[str, Any]:
    """Force reload configuration from disk."""
    global _config_cache
    _config_cache = None
    return load_config(config_path)
```

## systemd Service Integration

### GPIO Listener Service

**File:** /etc/systemd/system/gpio-listener.service
```ini
[Unit]
Description=Thermal Printer GPIO Button Listener
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/ducky-printer-project
ExecStart=/usr/bin/python3 /home/admin/ducky-printer-project/src/gpio_listener.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Web Server Service

**File:** /etc/systemd/system/web-server.service
```ini
[Unit]
Description=Thermal Printer Web Interface
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/ducky-printer-project
ExecStart=/usr/bin/python3 /home/admin/ducky-printer-project/src/web_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Service Management Commands

```bash
# Enable auto-start on boot
sudo systemctl enable gpio-listener.service
sudo systemctl enable web-server.service

# Start services
sudo systemctl start gpio-listener.service
sudo systemctl start web-server.service

# Check status
sudo systemctl status gpio-listener.service
sudo systemctl status web-server.service

# View logs
sudo journalctl -u gpio-listener.service -f
sudo journalctl -u web-server.service -f
```

## Build Order and Dependencies

### Dependency Graph

```
Phase 1: Foundation
├── config.py (no dependencies)
└── trigger_handler.py (depends: config.py, printer.py)

Phase 2: GPIO Trigger
└── gpio_listener.py (depends: trigger_handler.py, gpiozero)

Phase 3: Web Trigger
├── web_server.py (depends: trigger_handler.py, Flask)
└── templates/index.html (static HTML)

Phase 4: System Integration
├── systemd service files
└── WiFi AP configuration (hostapd/dnsmasq)
```

### Recommended Build Order

1. **Config system (lowest risk)**
   - Write config.py with load_config()
   - Create example printer_config.yaml
   - Write tests for config loading
   - **Why first:** No external dependencies, pure Python

2. **Shared trigger handler (integration layer)**
   - Write trigger_handler.py calling printer.print_file()
   - Hardcode wish1.png with rotation and dimensions
   - Write tests mocking printer.print_file()
   - **Why second:** Establishes integration point before building triggers

3. **GPIO trigger (hardware dependency)**
   - Write gpio_listener.py with gpiozero Button
   - Test with actual button hardware
   - Create systemd service file
   - **Why third:** Requires physical setup, easier to debug in isolation

4. **Web trigger (network dependency)**
   - Write web_server.py with Flask
   - Create simple HTML interface
   - Test from browser on local network
   - Create systemd service file
   - **Why fourth:** Can test without WiFi AP, just need network access

5. **WiFi AP setup (infrastructure)**
   - Configure hostapd for access point
   - Configure dnsmasq for DHCP
   - Test client connection and web access
   - **Why last:** Infrastructure change, affects network connectivity

### Testing Strategy at Each Stage

| Stage | Test Approach | Pass Criteria |
|-------|---------------|---------------|
| **Config** | Unit tests with sample YAML | Load config, access nested values |
| **Trigger Handler** | Unit tests with mocked printer.print_file() | Returns success dict, handles errors |
| **GPIO** | Manual test with physical button | Button press triggers print, logs visible |
| **Web** | HTTP requests with curl/browser | POST /print returns JSON, triggers print |
| **Integrated** | Both triggers print simultaneously | No USB conflicts, both succeed |
| **WiFi AP** | Connect client device, access web interface | Device connects, web interface loads |

## Anti-Patterns

### Anti-Pattern 1: Modifying Existing Printer Code

**What people do:** Add GPIO/web logic directly into printer.py or print_job.py

**Why it's wrong:**
- Breaks single responsibility principle (printer.py should only handle USB communication)
- Makes testing harder (can't test triggers without printer hardware)
- Creates merge conflicts if printer code evolves

**Do this instead:** Create separate trigger modules that call existing printer functions as a library

### Anti-Pattern 2: Shared USB Connection Instance

**What people do:** Open USB connection once at daemon start, reuse for all prints

**Why it's wrong:**
- USB devices can enter busy state after errors
- Power cycling printer while daemon running causes crashes
- v0.1 specifically uses per-job connections to avoid this

**Do this instead:** Keep existing per-job connection lifecycle, let each trigger call print_file() which handles connections

### Anti-Pattern 3: Complex Event Queue Between Triggers

**What people do:** Build producer-consumer queue with both triggers as producers

**Why it's wrong:**
- Over-engineering for single-user system
- Adds complexity without solving actual problem
- Per-job USB connections already provide thread safety

**Do this instead:** Let each trigger call printer directly, USB serialization handles concurrency

### Anti-Pattern 4: Flask with Gevent Before Measuring Performance

**What people do:** Use gevent or eventlet "for better performance"

**Why it's wrong:**
- Threading mode adequate for 1-10 prints/minute
- Gevent adds complexity and compatibility issues
- Premature optimization

**Do this instead:** Start with Flask's built-in threading (threaded=True), only optimize if latency problems appear

### Anti-Pattern 5: Blocking GPIO Callback

**What people do:** Add time.sleep() or blocking operations in when_pressed callback

**Why it's wrong:**
- Callback runs in gpiozero's internal thread
- Blocking prevents other GPIO events from being detected
- Can cause when_released to fire late

**Do this instead:** Keep callbacks quick - call trigger_handler (which is already fast) and return immediately

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **1 printer, 1-10 prints/hour** | Current architecture perfect - threading adequate, no queue needed |
| **1 printer, 100+ prints/hour** | Add Queue between triggers and printer to prevent USB contention, rate limiting |
| **Multiple printers** | Config specifies printer ID, find_printer() accepts vendor/product filter |

### Scaling Priorities

1. **First bottleneck:** USB printer speed (~10 sec per receipt)
   - **Symptom:** Triggers timeout waiting for printer
   - **Fix:** Add Queue with max depth, return "queued" status immediately

2. **Second bottleneck:** Flask threading limit (~10 concurrent requests)
   - **Symptom:** Web requests hang during concurrent access
   - **Fix:** Switch to gevent mode: app.run(host='0.0.0.0', port=5000, **async_mode='gevent'**)

**Reality check:** For single-user "print on demand" system, will never hit these limits. Keep it simple.

## WiFi Access Point Architecture

### Component Stack

```
WiFi Client Device (phone/laptop)
    ↓ (WiFi association)
hostapd (access point daemon)
    ↓ (DHCP request)
dnsmasq (DHCP server)
    ↓ (IP assigned: 192.168.4.x)
Client accesses http://192.168.4.1:5000
    ↓
Flask Web Server (web_server.py)
```

### Network Configuration

**Static IP for wlan0:**
```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```

**hostapd.conf:**
```
interface=wlan0
ssid=DuckyPrinter
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=printer123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
country_code=US
```

**dnsmasq.conf:**
```
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=local
address=/printer.local/192.168.4.1
```

### Access Pattern

1. Client connects to "DuckyPrinter" WiFi network
2. Receives IP in 192.168.4.x range from dnsmasq
3. Opens browser to http://192.168.4.1:5000
4. Clicks "Print" button
5. JavaScript sends POST to /print endpoint
6. Flask triggers print, returns JSON response

## Testing Architecture

### Unit Tests (Fast, No Hardware)

```python
# tests/test_trigger_handler.py
from unittest.mock import patch, MagicMock
from src.trigger_handler import handle_print_trigger

@patch('src.trigger_handler.load_config')
@patch('src.trigger_handler.print_file')
def test_handle_print_trigger_success(mock_print, mock_config):
    mock_config.return_value = {
        'triggers': {'gpio': {'enabled': True}},
        'print_file': 'wish1.png'
    }
    mock_print.return_value = 0

    result = handle_print_trigger(source='gpio')

    assert result['success'] == True
    mock_print.assert_called_once_with(
        'wish1.png',
        rotate=True,
        target_width_cm=8,
        target_height_cm=18
    )
```

### Integration Tests (Hardware Required)

```python
# tests/integration/test_gpio_integration.py
import time
from src.gpio_listener import button
from src.trigger_handler import handle_print_trigger

def test_button_press_triggers_print(monkeypatch):
    """Requires physical button on GPIO 17 and USB printer."""
    printed = []

    def mock_trigger(source):
        printed.append(source)
        return {"success": True, "message": "test"}

    monkeypatch.setattr('src.gpio_listener.handle_print_trigger', mock_trigger)

    print("Press button within 5 seconds...")
    time.sleep(5)

    assert 'gpio' in printed, "Button press not detected"
```

### Manual Test Plan

| Test | Steps | Expected Result |
|------|-------|-----------------|
| **Config load** | Run python -c "from src.config import load_config; print(load_config())" | Prints config dict, no errors |
| **GPIO trigger** | Wire button to GPIO 17, start gpio_listener.py, press button | Print job executes, logs show success |
| **Web trigger** | Start web_server.py, curl -X POST http://localhost:5000/print | Returns JSON, print job executes |
| **Concurrent triggers** | Press button while web request in flight | Both prints complete successfully |
| **WiFi AP** | Connect phone to DuckyPrinter WiFi, open http://192.168.4.1:5000 | Web interface loads, print button works |

## Sources

### Official Documentation
- [gpiozero Button API](https://gpiozero.readthedocs.io/en/stable/api_input.html)
- [gpiozero Basic Recipes](https://gpiozero.readthedocs.io/en/stable/recipes.html)
- [Flask with Gevent](https://flask.palletsprojects.com/en/stable/gevent/)
- [Python threading module](https://docs.python.org/3/library/threading.html)
- [Python queue module](https://docs.python.org/3/library/queue.html)

### Integration Patterns
- [Raspberry Pi systemd autorun](https://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/)
- [Python systemd tutorial](https://github.com/torfsen/python-systemd-tutorial)
- [Create wireless access point - Raspberry Pi Guide](https://raspberrypi-guide.github.io/networking/create-wireless-access-point)

### Configuration Best Practices
- [JSON vs YAML vs TOML in 2026](https://dev.to/jsontoall_tools/json-vs-yaml-vs-toml-which-configuration-format-should-you-use-in-2026-1hlb)
- [Configuration files in Python](https://martin-thoma.com/configuration-files-in-python/)

### Community Resources
- [Raspberry Pi GPIO button callbacks discussion](https://forums.raspberrypi.com/viewtopic.php?t=316608)
- [Flask threading vs gevent discussion](https://github.com/miguelgrinberg/Flask-SocketIO/discussions/1915)
- [gpiozero multiprocessing considerations](https://github.com/gpiozero/gpiozero/issues/759)

---
*Architecture research for: GPIO and Web Trigger Integration*
*Researched: 2026-03-13*
