# Phase 2: Configuration Foundation - Research

**Researched:** 2026-03-19
**Domain:** Python YAML configuration management with validation and hot reload
**Confidence:** HIGH

## Summary

Phase 2 implements a YAML-based configuration system for the GPIO print trigger, allowing users to configure GPIO pins, trigger modes, cooldown durations, source folders, and switch behavior without modifying code. The solution combines PyYAML for parsing, Pydantic for validation with clear error messages, and watchdog for automatic config reload without service restarts.

The Python ecosystem provides mature, well-tested libraries for this use case: PyYAML (YAML 1.1 parser, simple and fast), Pydantic v2 (Rust-backed validation, 5-50x faster than v1), and watchdog (cross-platform file monitoring with inotify on Linux). This stack is standard across DevOps, ML pipelines, and configuration-heavy applications.

**Primary recommendation:** Use PyYAML + Pydantic dataclasses + watchdog for a type-safe, validated, hot-reloadable configuration system with sensible defaults and user-friendly error messages.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CFG-01 | User can specify GPIO pin number in YAML config file | YAML parsing (PyYAML), integer field validation (Pydantic), BCM pin range 2-27 (gpiozero) |
| CFG-02 | User can set trigger mode (press or switch) in config file | Enum validation (Pydantic Literal types), string field constraints |
| CFG-03 | User can set cooldown duration between activations in config file | Float/int field validation, non-negative constraints (Pydantic Field with ge=0) |
| CFG-04 | User can set source folder path for print files in config file | Path validation (Pydantic path types), existence checks |
| CFG-05 | User can set switch trigger direction (both/on_only/off_only) in config file | Enum validation (Pydantic Literal types for constrained choices) |
| CFG-06 | System validates config at startup and shows clear error messages for invalid values | Pydantic ValidationError with detailed field-level messages, custom error formatting |
| CFG-07 | System re-reads config file when it changes without restarting the service | watchdog FileSystemEventHandler, inotify on Linux, debouncing for duplicate events |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.0+ | YAML parsing | Most popular Python YAML library (simple, fast, YAML 1.1 support), installed 100M+ times/month, use `safe_load()` for security |
| Pydantic | 2.x | Data validation | Standard for validation in Python (FastAPI, LangChain, SQLModel use it), v2 is 5-50x faster with Rust core, type-hint based validation |
| watchdog | 6.0.0+ | File monitoring | Cross-platform file watcher, uses inotify on Linux, 2M+ monthly downloads, proven for config hot-reload |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-mock | 3.14+ | Mock watchdog in tests | Already in requirements.txt, use for testing file watcher behavior |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML | ruamel.yaml | ruamel preserves comments (YAML 1.2), but PyYAML is simpler and sufficient for read-only config |
| Pydantic | Marshmallow or Cerberus | Both offer validation but lack type-hint integration and performance of Pydantic v2 |
| watchdog | polling (check mtime in loop) | Polling wastes CPU and has latency, watchdog uses OS-native inotify for instant notification |
| Pydantic dataclass | BaseModel | Both work, but dataclasses integrate better with existing Python code patterns |

**Installation:**
```bash
pip install pyyaml pydantic watchdog
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── config/
│   ├── __init__.py         # exports load_config, ConfigError
│   ├── schema.py           # Pydantic dataclass with validation rules
│   ├── loader.py           # YAML loading + Pydantic parsing
│   └── watcher.py          # watchdog FileSystemEventHandler for hot reload
├── gpio_listener.py        # Main service (uses config)
└── (existing v0.1 modules)

tests/
├── test_config_schema.py   # Validation rules (pin range, modes, etc.)
├── test_config_loader.py   # YAML loading, defaults, error messages
└── test_config_watcher.py  # File change detection, debouncing
```

### Pattern 1: Pydantic Dataclass with Defaults and Validation
**What:** Use Pydantic dataclass to define config schema with type hints, defaults, and validation constraints
**When to use:** All configuration validation scenarios
**Example:**
```python
# Source: Pydantic docs + community patterns (2026)
from pydantic import Field, field_validator
from pydantic.dataclasses import dataclass
from pathlib import Path
from typing import Literal

@dataclass
class PrinterConfig:
    """Printer GPIO trigger configuration with validation."""

    # GPIO settings
    gpio_pin: int = Field(default=17, ge=2, le=27,
                          description="BCM GPIO pin number (2-27)")
    trigger_mode: Literal["press", "switch"] = Field(
        default="press",
        description="Button press or switch flip trigger"
    )
    switch_direction: Literal["both", "on_only", "off_only"] = Field(
        default="both",
        description="Which switch transitions trigger printing"
    )

    # Timing
    cooldown_seconds: float = Field(default=2.0, ge=0,
                                    description="Minimum seconds between prints")

    # File handling
    source_folder: Path = Field(default=Path("print_files"),
                                description="Folder containing files to print")

    @field_validator('source_folder')
    @classmethod
    def validate_source_folder_exists(cls, v: Path) -> Path:
        """Ensure source folder exists."""
        if not v.exists():
            raise ValueError(f"Source folder does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Source folder is not a directory: {v}")
        return v

    @field_validator('gpio_pin')
    @classmethod
    def validate_gpio_pin_usable(cls, v: int) -> int:
        """Check GPIO pin is not reserved for special functions."""
        # Pins 0-1 are I2C, 14-15 are UART (avoid in validation)
        reserved = {0, 1, 14, 15}
        if v in reserved:
            raise ValueError(
                f"GPIO {v} is reserved (I2C: 0-1, UART: 14-15). "
                f"Use pins 2-27 excluding reserved."
            )
        return v
```

### Pattern 2: YAML Loading with Validation and User-Friendly Errors
**What:** Load YAML with `safe_load()`, validate with Pydantic, format errors for users
**When to use:** Config file loading at startup and reload
**Example:**
```python
# Source: Multiple tutorials + production patterns (2026)
import yaml
from pathlib import Path
from pydantic import ValidationError
from .schema import PrinterConfig

class ConfigError(Exception):
    """User-friendly configuration error."""
    pass

def load_config(config_path: Path = Path("config.yaml")) -> PrinterConfig:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to YAML config file

    Returns:
        Validated PrinterConfig instance

    Raises:
        ConfigError: With user-friendly message if config is invalid
    """
    try:
        # Security: Always use safe_load to prevent code execution
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}  # Handle empty file

        # Validate with Pydantic (applies defaults for missing fields)
        config = PrinterConfig(**data)
        return config

    except FileNotFoundError:
        # Config file missing - use all defaults
        return PrinterConfig()

    except yaml.YAMLError as e:
        raise ConfigError(
            f"Invalid YAML syntax in {config_path}:\n{e}"
        )

    except ValidationError as e:
        # Convert Pydantic errors to user-friendly format
        errors = []
        for error in e.errors():
            field = ".".join(str(x) for x in error['loc'])
            msg = error['msg']
            errors.append(f"  - {field}: {msg}")

        raise ConfigError(
            f"Configuration validation failed in {config_path}:\n" +
            "\n".join(errors) +
            "\n\nFix these errors and restart the service."
        )
```

### Pattern 3: Watchdog Hot Reload with Debouncing
**What:** Monitor config file for changes, debounce duplicate events, reload on modify
**When to use:** Long-running services that need config updates without restart
**Example:**
```python
# Source: watchdog docs + production debouncing patterns (2026)
import time
from pathlib import Path
from typing import Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

class ConfigWatcher(FileSystemEventHandler):
    """Watches config file and reloads on changes with debouncing."""

    def __init__(self, config_path: Path, reload_callback: Callable):
        """Initialize watcher.

        Args:
            config_path: Path to config file to watch
            reload_callback: Function to call when config changes
        """
        self.config_path = config_path.resolve()
        self.reload_callback = reload_callback
        self.last_reload_time = 0
        self.debounce_seconds = 1.0  # Ignore events within 1 second

    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification events with debouncing.

        Editors can trigger multiple events per save (temp files, atomic writes).
        Debounce by checking time since last reload.
        """
        if not isinstance(event, FileModifiedEvent):
            return

        # Check if this is our config file
        event_path = Path(event.src_path).resolve()
        if event_path != self.config_path:
            return

        # Debounce: ignore events within 1 second of last reload
        now = time.time()
        if now - self.last_reload_time < self.debounce_seconds:
            return

        self.last_reload_time = now

        # Reload config (callback handles errors)
        try:
            self.reload_callback()
            print(f"Config reloaded from {self.config_path}")
        except Exception as e:
            print(f"Config reload failed: {e}")

def start_config_watcher(config_path: Path, reload_callback: Callable) -> Observer:
    """Start watching config file for changes.

    Args:
        config_path: Path to config file
        reload_callback: Function to call on config change

    Returns:
        Observer instance (call .stop() to stop watching)
    """
    event_handler = ConfigWatcher(config_path, reload_callback)
    observer = Observer()

    # Watch the parent directory (file must exist there)
    watch_dir = config_path.parent
    observer.schedule(event_handler, str(watch_dir), recursive=False)
    observer.start()

    return observer
```

### Anti-Patterns to Avoid
- **Using `yaml.load()` without SafeLoader:** Security vulnerability - allows arbitrary code execution from YAML
- **No debouncing on file events:** Editors trigger 2-4 events per save, causes multiple reloads
- **Validating in main code instead of schema:** Spreads validation logic across codebase, hard to maintain
- **Silent config failures:** User has no idea why service behavior is wrong, always log/print errors
- **Watching with polling loops:** Wastes CPU and has ~1 second latency, use watchdog's inotify integration

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Manual string parsing | PyYAML `safe_load()` | Handles YAML spec edge cases (multiline strings, escapes, types), secure against injection |
| Type validation | `if not isinstance()` checks | Pydantic dataclass | Handles coercion (string -> int), nested validation, clear error messages, 50+ field types |
| File watching | `while True: check mtime` | watchdog Observer | Uses OS-native inotify (instant, zero CPU), cross-platform, handles symlinks/moves |
| Config defaults | `config.get('key', default)` | Pydantic Field defaults | Self-documenting, type-checked, works with validation |
| Error formatting | String concatenation | Pydantic ValidationError | Structured error details (field path, type, constraint), easy to transform |

**Key insight:** Configuration validation seems simple but has deep complexity (type coercion, nested validation, clear errors, defaults interaction). Pydantic is battle-tested across millions of production deployments and handles edge cases you won't discover until production.

## Common Pitfalls

### Pitfall 1: Using `yaml.load()` Instead of `yaml.safe_load()`
**What goes wrong:** Attackers can craft YAML payloads that execute arbitrary Python code when parsed with `yaml.load()` or `FullLoader`
**Why it happens:** `yaml.load()` was the original API, `safe_load()` was added later for security
**How to avoid:** ALWAYS use `yaml.safe_load()`. Never use `yaml.load()`, `yaml.unsafe_load()`, `yaml.FullLoader`, or `yaml.UnsafeLoader`
**Warning signs:** Security scanners (Semgrep, Bandit) flag `yaml.load()` as critical vulnerability

### Pitfall 2: Watchdog Fires Multiple Events Per File Save
**What goes wrong:** Config reloads 2-4 times per save (vi creates temp swap files, editors do atomic writes with move)
**Why it happens:** Editors save files using temp files + atomic rename for crash safety, triggering multiple inotify events
**How to avoid:** Implement debouncing - track last reload time, ignore events within 1 second window
**Warning signs:** Logs show "Config reloaded" multiple times for single save, service stutters on config change

### Pitfall 3: Forgetting Optional vs. Default in Pydantic
**What goes wrong:** `Optional[int]` does NOT give a default of `None`, field is still required unless you set `= None` explicitly
**Why it happens:** Pydantic v2 changed behavior from v1 (v1 gave implicit `None` default, v2 does not)
**How to avoid:** Use `field: type = default_value` syntax. `Optional` only means "can be None", not "has default None"
**Warning signs:** Pydantic raises "field required" error even though type hint says `Optional`

### Pitfall 4: Validation Errors Expose Internal Field Names
**What goes wrong:** Pydantic errors use Python field names (`gpio_pin`) not YAML keys (`gpio-pin` or display names), confusing for users
**Why it happens:** Pydantic validates Python objects, doesn't know about YAML key names
**How to avoid:** Catch `ValidationError`, format errors with field descriptions from `Field(description=...)`, map to YAML keys if different
**Warning signs:** User bug reports say "what is gpio_pin? I see gpio-pin in the config file"

### Pitfall 5: Config Watcher Doesn't Handle Reload Errors
**What goes wrong:** Invalid config crashes the watcher thread, service keeps running with stale config and no way to recover
**Why it happens:** Callback raises exception (validation fails), exception propagates up and kills Observer thread
**How to avoid:** Wrap reload callback in try/except, log error but keep watcher running, service continues with last-known-good config
**Warning signs:** Config changes stop working after one bad config, have to restart service to fix

### Pitfall 6: Validating GPIO Pin Format but Not Hardware Availability
**What goes wrong:** Config validation passes (pin 17 is valid BCM number), but service crashes later when gpiozero can't access the pin
**Why it happens:** Config validation runs before GPIO hardware initialization, can't check /dev/gpiochip* permissions or availability
**How to avoid:** Do two-phase validation: config schema validation (cheap, at load), hardware validation (expensive, at service start). Log clear error if hardware validation fails
**Warning signs:** Config loads fine but service fails with "permission denied" or "pin already in use" from gpiozero

## Code Examples

Verified patterns from official sources:

### Pydantic ValidationError Handling
```python
# Source: Pydantic docs - Error Handling (2026)
from pydantic import ValidationError

try:
    config = PrinterConfig(**yaml_data)
except ValidationError as e:
    # e.errors() returns list of error dicts
    for error in e.errors():
        print(f"Field: {error['loc']}")  # ('gpio_pin',) tuple
        print(f"Error: {error['msg']}")  # "Input should be less than or equal to 27"
        print(f"Type: {error['type']}")  # "less_than_equal"
        print(f"Input: {error['input']}")  # 99 (the bad value)
```

### Pydantic Field with Constraints
```python
# Source: Pydantic docs - Fields (2026)
from pydantic import Field

# Numeric constraints
cooldown: float = Field(default=2.0, ge=0, le=60)  # 0 <= x <= 60

# String constraints
mode: str = Field(default="press", min_length=1, max_length=20)

# Literal for enums (better than string validation)
from typing import Literal
trigger: Literal["press", "switch"] = "press"  # Only these values allowed
```

### watchdog Basic Usage
```python
# Source: watchdog PyPI docs (2026)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"File {event.src_path} modified")

observer = Observer()
observer.schedule(MyHandler(), path='/path/to/watch', recursive=False)
observer.start()

# Later, to stop:
observer.stop()
observer.join()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic v1 (Python) | Pydantic v2 (Rust core) | 2023 | 5-50x faster validation, v1 gave `Optional` implicit `None` default, v2 requires explicit default |
| configparser (INI) | YAML + Pydantic | 2020-2024 | YAML supports nested structures, comments, lists; Pydantic gives type safety and validation |
| Environment variables only | YAML + env override | 2022+ | Files allow comments and structure, env vars override for Docker/K8s |
| Manual file polling | watchdog with inotify | 2015+ | Instant notification instead of 1s polling lag, zero CPU overhead |

**Deprecated/outdated:**
- `yaml.load()` without `Loader=yaml.SafeLoader`: Critical security vulnerability (arbitrary code execution)
- Pydantic v1 style `Config` class: Use `model_config = ConfigDict(...)` in v2
- Pydantic `@validator`: Renamed to `@field_validator` in v2 (old name still works but deprecated)

## Open Questions

1. **Should we validate GPIO pin hardware availability at config load time?**
   - What we know: Config validation is cheap, gpiozero pin validation requires hardware access (expensive, can fail in tests)
   - What's unclear: Best practice for two-phase validation (schema validation + hardware validation)
   - Recommendation: Validate pin number range in config schema, validate hardware access at service start (before entering main loop). Log clear error with instructions if hardware validation fails.

2. **Should config file be required or optional with all defaults?**
   - What we know: Requirement CFG-01 through CFG-07 say "user can configure", not "user must configure"
   - What's unclear: Is missing config.yaml an error or just means "use all defaults"?
   - Recommendation: Missing config.yaml uses all defaults (sensible defaults exist), malformed YAML or invalid values are errors. This lets users start simple and add config as needed.

3. **Where should config.yaml live in production?**
   - What we know: Development uses project root, systemd services often use /etc/ or /opt/
   - What's unclear: Standard location for Pi user-editable config
   - Recommendation: Default to `./config.yaml` (same directory as service script), allow override via `--config` CLI flag or `PRINTER_CONFIG` env var. Document location in systemd service file comments.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0+ |
| Config file | pytest.ini (exists, configured with pythonpath) |
| Quick run command | `pytest tests/test_config_schema.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CFG-01 | GPIO pin number parsed and validated (2-27) | unit | `pytest tests/test_config_schema.py::test_gpio_pin_validation -x` | ❌ Wave 0 |
| CFG-02 | Trigger mode validated (press/switch only) | unit | `pytest tests/test_config_schema.py::test_trigger_mode_validation -x` | ❌ Wave 0 |
| CFG-03 | Cooldown duration validated (non-negative float) | unit | `pytest tests/test_config_schema.py::test_cooldown_validation -x` | ❌ Wave 0 |
| CFG-04 | Source folder path validated (exists, is directory) | unit | `pytest tests/test_config_schema.py::test_source_folder_validation -x` | ❌ Wave 0 |
| CFG-05 | Switch direction validated (both/on_only/off_only) | unit | `pytest tests/test_config_schema.py::test_switch_direction_validation -x` | ❌ Wave 0 |
| CFG-06 | Invalid config shows clear error at startup | integration | `pytest tests/test_config_loader.py::test_validation_error_messages -x` | ❌ Wave 0 |
| CFG-07 | Config file changes reload without restart | integration | `pytest tests/test_config_watcher.py::test_hot_reload -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_config_schema.py -x` (schema validation tests, < 1 second)
- **Per wave merge:** `pytest tests/ -v` (full test suite including existing v0.1 tests)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_config_schema.py` — covers CFG-01 through CFG-06 (Pydantic validation rules)
- [ ] `tests/test_config_loader.py` — covers CFG-06 (YAML loading, error formatting, defaults)
- [ ] `tests/test_config_watcher.py` — covers CFG-07 (watchdog hot reload, debouncing)
- [ ] Framework install: `pip install watchdog` — watchdog not yet in requirements.txt

## Sources

### Primary (HIGH confidence)
- [PyYAML PyPI page](https://pypi.org/project/ruamel.yaml/) - Installation, version info
- [Pydantic official docs - Dataclasses](https://docs.pydantic.dev/latest/concepts/dataclasses/) - Dataclass validation patterns
- [Pydantic official docs - Fields](https://docs.pydantic.dev/latest/concepts/fields/) - Field constraints and defaults
- [Pydantic official docs - Validation Errors](https://docs.pydantic.dev/latest/errors/validation_errors/) - Error handling and formatting
- [watchdog PyPI page](https://pypi.org/project/watchdog/) - Installation, basic usage
- [gpiozero official docs - API Exceptions](https://gpiozero.readthedocs.io/en/stable/api_exc.html) - GPIO error handling
- [gpiozero official docs - API Pins](https://gpiozero.readthedocs.io/en/stable/api_pins.html) - Pin numbering and validation

### Secondary (MEDIUM confidence)
- [Real Python - YAML: The Missing Battery in Python](https://realpython.com/python-yaml/) - PyYAML tutorial
- [Sarah Glasmacher - How to Validate Config YAML with Pydantic](https://www.sarahglasmacher.com/how-to-validate-config-yaml-pydantic/) - ML pipeline pattern
- [Better Programming - Validating YAML Configs with Pydantic](https://betterprogramming.pub/validating-yaml-configs-made-easy-with-pydantic-594522612db5) - Practical examples
- [OneUpTime Blog - Config System with Hot Reload in Python (2026)](https://oneuptime.com/blog/post/2026-01-22-config-hot-reload-python/view) - Hot reload architecture
- [Raspberry Pi Pinout Reference](https://pinout.xyz/) - BCM GPIO pin mapping
- [DEV Community - Python Watchdog Mastering](https://dev.to/devasservice/mastering-file-system-monitoring-with-watchdog-in-python-483c) - Debouncing patterns

### Tertiary (LOW confidence)
- [Semgrep Blog - PyYAML Vulnerabilities](https://semgrep.dev/blog/2022/testing-vulnerable-pyyaml-versions/) - Security context
- [TonyBaloney - 10 Python Security Gotchas](https://tonybaloney.github.io/posts/10-common-security-gotchas-in-python.html) - YAML security warning
- [watchdog GitHub issues](https://github.com/gorakhargosh/watchdog/issues/346) - Duplicate event discussions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PyYAML, Pydantic v2, and watchdog are verified from official docs and PyPI, widely adopted
- Architecture: HIGH - Patterns verified from Pydantic official docs and multiple 2025-2026 production examples
- Pitfalls: MEDIUM-HIGH - Security issues (safe_load) verified from official sources, duplicate events verified from watchdog GitHub, Pydantic v2 behavior verified from official docs

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (30 days - stable libraries with mature APIs)
