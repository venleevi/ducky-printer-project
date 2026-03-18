# Phase 2: Configuration Foundation - Research

**Researched:** 2026-03-13
**Domain:** Python YAML configuration management
**Confidence:** HIGH

## Summary

Phase 2 establishes a YAML-based configuration system to control trigger behavior (GPIO and web), target print file, and GPIO pin selection. The standard approach uses PyYAML 6.0.3 (Python 3.13 compatible) with `yaml.safe_load()` for secure parsing, combined with Python dataclasses for type validation and default values. This configuration-driven architecture eliminates hardcoded values and enables runtime customization without code changes.

The configuration file (`printer_config.yaml`) will be loaded at application startup by a dedicated `config.py` module. The module provides a dataclass-based schema with field validation, sensible defaults, and comprehensive error handling for missing files and invalid YAML syntax. Configuration is loaded once at startup and passed to trigger modules (GPIO listener, web server) as immutable objects, preventing runtime modification bugs.

**Primary recommendation:** Use PyYAML 6.0.3 with `yaml.safe_load()` for security, Python 3.13 dataclasses with `field()` defaults for schema validation, and PathLib for file path handling. Place default config at project root (`./printer_config.yaml`) with fallback search in user home directory (`~/.config/ducky-printer/`).

## Phase Requirements

<phase_requirements>
| ID | Description | Research Support |
|----|-------------|------------------|
| CFG-01 | System reads configuration from YAML file | PyYAML 6.0.3 safe_load pattern with FileNotFoundError handling |
| CFG-02 | Configuration specifies whether GPIO trigger is enabled | Boolean field with default value in dataclass schema |
| CFG-03 | Configuration specifies whether web trigger is enabled | Boolean field with default value in dataclass schema |
| CFG-04 | Configuration specifies target file path (wish1.png) | PathLib Path field with validation and default |
| CFG-05 | Configuration specifies GPIO pin number for button | Integer field with BCM pin range validation (0-27) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.0.3 | YAML parsing and serialization | De facto standard for Python YAML, Python 3.13 compatible (released Sep 2025), official wheels for all platforms |
| dataclasses | stdlib | Configuration schema with type validation | Python 3.7+ standard library, zero dependencies, native IDE support |
| pathlib | stdlib | File path handling | Python 3.4+ standard library, object-oriented path API, cross-platform |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.x (optional) | Advanced validation with custom validators | If complex validation logic needed (GPIO pin ranges, file existence checks) |
| platformdirs | 4.x (optional) | OS-aware config directory paths | If supporting multi-user installs with system-wide config |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML | TOML (tomllib in stdlib 3.11+) | TOML simpler but less human-readable for nested configs; no comments after inline tables |
| PyYAML | JSON | JSON more rigid (no comments), less user-friendly for manual editing |
| dataclasses | Pydantic BaseModel | Pydantic adds 5MB+ dependency, overkill for simple config schema |
| dataclasses | dict validation | Manual validation error-prone, no IDE autocomplete |

**Installation:**
```bash
pip install pyyaml>=6.0.3
```

Note: dataclasses and pathlib are standard library (no install needed).

## Architecture Patterns

### Recommended Project Structure
```
.
├── printer_config.yaml           # Default config file (project root)
├── src/
│   ├── config.py                 # Configuration module
│   └── ...                       # Other modules import config
└── tests/
    └── test_config.py            # Config loading and validation tests
```

### Pattern 1: Dataclass Configuration Schema
**What:** Define configuration as frozen dataclass with typed fields and defaults
**When to use:** All configuration schemas (immutable, type-safe, IDE-friendly)
**Example:**
```python
# Source: Python dataclasses official docs + 2026 best practices
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class PrinterConfig:
    """Printer configuration loaded from YAML file.

    Attributes:
        gpio_enabled: Enable GPIO button trigger
        web_enabled: Enable web interface trigger
        target_file: Path to image file for printing
        gpio_pin: BCM GPIO pin number for button (0-27)
    """
    gpio_enabled: bool = True
    web_enabled: bool = True
    target_file: Path = field(default_factory=lambda: Path("wish1.png"))
    gpio_pin: int = 17  # BCM pin 17 (physical pin 11)

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Convert string paths to Path objects (YAML loads as strings)
        if isinstance(self.target_file, str):
            object.__setattr__(self, 'target_file', Path(self.target_file))

        # Validate GPIO pin range (BCM 0-27 for Pi 3B+)
        if not 0 <= self.gpio_pin <= 27:
            raise ValueError(f"GPIO pin must be 0-27 (BCM), got {self.gpio_pin}")
```

### Pattern 2: Safe YAML Loading with Error Handling
**What:** Load YAML with comprehensive exception handling and user-friendly errors
**When to use:** All YAML file loading operations
**Example:**
```python
# Source: PyYAML docs + 2026 error handling best practices
import yaml
from pathlib import Path
from typing import Dict, Any

def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load YAML file with error handling.

    Args:
        file_path: Path to YAML file

    Returns:
        Dictionary of configuration values

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If YAML syntax is invalid
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if data is None:
            return {}  # Empty file returns None, convert to empty dict

        return data

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Configuration file not found: {file_path}\n"
            f"Create {file_path} with required settings."
        )
    except yaml.YAMLError as e:
        error_msg = f"Invalid YAML syntax in {file_path}"
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            error_msg += f"\nError at line {mark.line + 1}, column {mark.column + 1}"
        raise ValueError(error_msg) from e
```

### Pattern 3: Configuration Factory with Search Path
**What:** Load config from multiple search locations (project root → user home)
**When to use:** User-facing applications with flexible config locations
**Example:**
```python
# Source: Python configuration best practices 2026
from pathlib import Path
from typing import Optional

def load_config(custom_path: Optional[Path] = None) -> PrinterConfig:
    """Load printer configuration from YAML file.

    Search order:
    1. Custom path if provided
    2. ./printer_config.yaml (project root)
    3. ~/.config/ducky-printer/config.yaml (user home)

    Args:
        custom_path: Optional custom config file path

    Returns:
        PrinterConfig instance with validated settings

    Raises:
        FileNotFoundError: If no config file found in search paths
    """
    search_paths = []

    if custom_path:
        search_paths.append(custom_path)

    # Project root
    search_paths.append(Path("printer_config.yaml"))

    # User home directory
    home_config = Path.home() / ".config" / "ducky-printer" / "config.yaml"
    search_paths.append(home_config)

    for path in search_paths:
        if path.exists():
            data = load_yaml_file(path)
            return PrinterConfig(**data)

    raise FileNotFoundError(
        f"No configuration file found. Searched:\n" +
        "\n".join(f"  - {p}" for p in search_paths)
    )
```

### Anti-Patterns to Avoid
- **yaml.load() without Loader:** Never use deprecated `yaml.load()` without explicit safe Loader - enables arbitrary code execution (CVE-level vulnerability)
- **Mutable configuration objects:** Don't use regular classes without `frozen=True` - allows runtime modification causing race conditions in multi-threaded trigger system
- **Hardcoded defaults in code:** Don't scatter default values across modules - centralize in dataclass schema for single source of truth
- **No validation at load time:** Don't defer validation to usage time - fail fast at startup with clear error messages
- **String-based file paths:** Don't use `str` for paths - use `pathlib.Path` for OS-agnostic path operations

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom YAML parser | PyYAML 6.0.3 with yaml.safe_load() | YAML spec is complex (aliases, anchors, multi-line strings); PyYAML handles edge cases, security (arbitrary code execution in unsafe loaders) |
| Configuration validation | Manual dict key checking | dataclasses with __post_init__ | Type hints provide IDE autocomplete, frozen=True prevents mutation, __post_init__ centralizes validation logic |
| File path handling | String concatenation with os.path.join | pathlib.Path | Cross-platform path separators, automatic normalization, .exists()/.is_file() methods |
| Config file search | Manual if-file-exists chains | Search path list with Path.exists() | Declarative search order, easy to add new locations, clear error messages listing all searched paths |

**Key insight:** Configuration seems simple but has many edge cases - missing files, invalid YAML syntax (tabs vs spaces), type mismatches (string "17" vs int 17), platform-specific paths. Standard library modules handle these robustly with 15+ years of production hardening.

## Common Pitfalls

### Pitfall 1: yaml.load() Without Safe Loader
**What goes wrong:** Using `yaml.load()` or `yaml.FullLoader` enables arbitrary Python code execution if YAML contains malicious `!!python/object/apply` tags
**Why it happens:** Older PyYAML tutorials (pre-2018) use `yaml.load()` before security became default concern
**How to avoid:** Always use `yaml.safe_load()` - only constructs standard YAML types (strings, numbers, lists, dicts)
**Warning signs:** Security scanners flagging yaml.load, CVE warnings in dependency audits

### Pitfall 2: Forgetting YAML Returns None for Empty Files
**What goes wrong:** Empty YAML file returns `None`, causing `TypeError: 'NoneType' object is not iterable` when unpacking with `**data`
**Why it happens:** YAML spec defines empty document as null value
**How to avoid:** Check for None after `safe_load()` and convert to empty dict: `data = yaml.safe_load(f) or {}`
**Warning signs:** Crashes only with empty config files, works fine with content

### Pitfall 3: Tab Characters in YAML Files
**What goes wrong:** YAML treats tabs as syntax errors: `yaml.scanner.ScannerError: while scanning for the next token found character '\t'`
**Why it happens:** YAML spec forbids tabs for indentation (must use spaces), text editors default to tabs
**How to avoid:** Configure editor to use spaces for .yaml files, validate YAML in tests
**Warning signs:** Config works in some editors but fails at runtime, indentation looks correct visually

### Pitfall 4: Type Mismatches from YAML Strings
**What goes wrong:** YAML loads numbers as strings if quoted: `gpio_pin: "17"` becomes string, fails integer validation
**Why it happens:** YAML auto-detects types only for unquoted values, users quote "to be safe"
**How to avoid:** Use dataclass type hints to catch mismatches early, provide clear error messages in __post_init__
**Warning signs:** Validation errors about string vs int types, works with unquoted values

### Pitfall 5: Path Separator Hardcoding
**What goes wrong:** Hardcoded forward slashes in config: `target_file: data/images/wish1.png` fails on Windows
**Why it happens:** Developers test on Linux/Mac, YAML is plain text with manual path strings
**How to avoid:** Use pathlib.Path which handles platform differences, test on Windows VM
**Warning signs:** Works on Pi/Linux but fails in Windows development environment

### Pitfall 6: Missing Configuration File Not Caught Until Runtime
**What goes wrong:** Application starts successfully, crashes when trigger attempts to load config: "file not found"
**Why it happens:** Lazy loading of config on first use instead of eager validation at startup
**How to avoid:** Load and validate config in main() before starting services, fail fast with clear error
**Warning signs:** Service starts, appears healthy, then crashes on first button press

### Pitfall 7: GPIO Pin Physical vs BCM Number Confusion
**What goes wrong:** User configures `gpio_pin: 11` expecting physical pin 11, but gpiozero interprets as BCM GPIO 11 (physical pin 23)
**Why it happens:** Raspberry Pi has two numbering schemes - physical pin position (1-40) vs BCM GPIO number (0-27)
**How to avoid:** Document BCM numbering in config file comments, validate range 0-27 to catch physical pin numbers (>27)
**Warning signs:** Button doesn't work, user says "I connected to pin 11"

## Code Examples

Verified patterns from official sources:

### Complete Configuration Module
```python
# Source: PyYAML docs + Python dataclasses + 2026 best practices
"""Configuration management for thermal printer triggers.

This module loads and validates YAML configuration files for controlling
GPIO button and web interface trigger behavior.
"""

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class PrinterConfig:
    """Printer configuration schema.

    Attributes:
        gpio_enabled: Enable GPIO button trigger
        web_enabled: Enable web interface trigger
        target_file: Path to image/text file for printing
        gpio_pin: BCM GPIO pin number (0-27 for Pi 3B+)
    """
    gpio_enabled: bool = True
    web_enabled: bool = True
    target_file: Path = field(default_factory=lambda: Path("wish1.png"))
    gpio_pin: int = 17  # BCM 17 = Physical pin 11

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Convert string path to Path object (YAML deserializes as string)
        if isinstance(self.target_file, str):
            object.__setattr__(self, 'target_file', Path(self.target_file))

        # Validate GPIO pin range for Pi 3B+ (BCM 0-27)
        if not isinstance(self.gpio_pin, int):
            raise TypeError(f"gpio_pin must be integer, got {type(self.gpio_pin).__name__}")
        if not 0 <= self.gpio_pin <= 27:
            raise ValueError(
                f"gpio_pin must be 0-27 (BCM numbering), got {self.gpio_pin}\n"
                f"See https://pinout.xyz for BCM pin numbers"
            )


def load_config(config_path: Optional[Path] = None) -> PrinterConfig:
    """Load and validate printer configuration from YAML file.

    Args:
        config_path: Optional path to config file. If None, searches:
                     1. ./printer_config.yaml (project root)
                     2. ~/.config/ducky-printer/config.yaml

    Returns:
        Validated PrinterConfig instance

    Raises:
        FileNotFoundError: No config file found in search paths
        ValueError: Invalid YAML syntax or validation failure
    """
    search_paths = []

    if config_path:
        search_paths.append(config_path)
    else:
        # Default search paths
        search_paths.append(Path("printer_config.yaml"))
        search_paths.append(
            Path.home() / ".config" / "ducky-printer" / "config.yaml"
        )

    # Try each search path
    for path in search_paths:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}

                # Validate and construct config object
                return PrinterConfig(**data)

            except yaml.YAMLError as e:
                error_msg = f"Invalid YAML syntax in {path}"
                if hasattr(e, 'problem_mark'):
                    mark = e.problem_mark
                    error_msg += f" at line {mark.line + 1}, column {mark.column + 1}"
                raise ValueError(error_msg) from e

            except TypeError as e:
                raise ValueError(f"Invalid configuration in {path}: {e}") from e

    # No config file found
    raise FileNotFoundError(
        "Configuration file not found. Searched:\n" +
        "\n".join(f"  - {p}" for p in search_paths) +
        "\n\nCreate printer_config.yaml with settings:\n"
        "  gpio_enabled: true\n"
        "  web_enabled: true\n"
        "  target_file: wish1.png\n"
        "  gpio_pin: 17  # BCM numbering"
    )
```

### Example Configuration File
```yaml
# printer_config.yaml - Thermal printer trigger configuration
# Place in project root directory

# Enable/disable GPIO button trigger
# Set to false to disable physical button without code changes
gpio_enabled: true

# Enable/disable web interface trigger
# Set to false to run only GPIO trigger (headless operation)
web_enabled: true

# Target file path for printing
# Relative paths are relative to project root
# Absolute paths also supported: /home/pi/images/wish1.png
target_file: wish1.png

# GPIO pin number for button (BCM numbering, NOT physical pin number)
# BCM 17 = Physical pin 11 (see https://pinout.xyz)
# Valid range: 0-27 for Raspberry Pi 3B+
gpio_pin: 17
```

### Test Pattern: Configuration Loading
```python
# Source: pytest best practices 2026
"""Tests for configuration loading and validation."""

import pytest
import yaml
from pathlib import Path
from config import load_config, PrinterConfig

def test_load_valid_config(tmp_path):
    """Test loading valid YAML configuration."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text("""
gpio_enabled: true
web_enabled: false
target_file: test.png
gpio_pin: 23
""")

    config = load_config(config_file)
    assert config.gpio_enabled is True
    assert config.web_enabled is False
    assert config.target_file == Path("test.png")
    assert config.gpio_pin == 23


def test_load_config_with_defaults(tmp_path):
    """Test partial config uses defaults for missing fields."""
    config_file = tmp_path / "minimal_config.yaml"
    config_file.write_text("gpio_pin: 18\n")

    config = load_config(config_file)
    assert config.gpio_enabled is True  # default
    assert config.web_enabled is True   # default
    assert config.gpio_pin == 18        # overridden


def test_invalid_gpio_pin_range(tmp_path):
    """Test GPIO pin validation rejects out-of-range values."""
    config_file = tmp_path / "bad_config.yaml"
    config_file.write_text("gpio_pin: 50\n")  # BCM pins only go to 27

    with pytest.raises(ValueError, match="gpio_pin must be 0-27"):
        load_config(config_file)


def test_missing_config_file():
    """Test clear error when config file not found."""
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config(Path("/nonexistent/config.yaml"))


def test_invalid_yaml_syntax(tmp_path):
    """Test clear error for malformed YAML."""
    config_file = tmp_path / "bad_syntax.yaml"
    config_file.write_text("gpio_enabled: true\n  invalid_indent: value\n")

    with pytest.raises(ValueError, match="Invalid YAML syntax"):
        load_config(config_file)


def test_empty_config_file(tmp_path):
    """Test empty YAML file uses all defaults."""
    config_file = tmp_path / "empty.yaml"
    config_file.write_text("")

    config = load_config(config_file)
    assert config.gpio_enabled is True
    assert config.gpio_pin == 17  # default
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ConfigParser (.ini files) | YAML for structured config | ~2015 with PyYAML 3.x | YAML supports nested structures, lists, better readability |
| JSON config files | YAML with comments | ~2018 | User-editable configs need comments for documentation |
| yaml.load() | yaml.safe_load() | 2018 (PyYAML 5.1+) | Security: prevents arbitrary code execution |
| Manual dict validation | Dataclasses with type hints | 2020 (Python 3.7+) | IDE autocomplete, type checking, frozen immutability |
| Dict-based config | Pydantic BaseModel | 2021+ | Advanced validation, but adds dependencies |

**Deprecated/outdated:**
- **yaml.load() without Loader:** Security vulnerability, use yaml.safe_load()
- **ConfigParser for new projects:** Limited to flat key-value pairs, use YAML for nested configs
- **Global mutable config dict:** Thread-safety issues, use frozen dataclass instances
- **os.path module:** Deprecated in favor of pathlib (Python 3.4+)

## Validation Architecture

> Note: workflow.nyquist_validation is not explicitly disabled in config.json, so this section is included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0+ |
| Config file | pytest.ini (already exists) |
| Quick run command | `pytest tests/test_config.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CFG-01 | System reads YAML config file | unit | `pytest tests/test_config.py::test_load_valid_config -x` | ❌ Wave 0 |
| CFG-01 | Missing config file error handling | unit | `pytest tests/test_config.py::test_missing_config_file -x` | ❌ Wave 0 |
| CFG-01 | Invalid YAML syntax error handling | unit | `pytest tests/test_config.py::test_invalid_yaml_syntax -x` | ❌ Wave 0 |
| CFG-02 | GPIO enable/disable flag | unit | `pytest tests/test_config.py::test_gpio_enabled_flag -x` | ❌ Wave 0 |
| CFG-03 | Web enable/disable flag | unit | `pytest tests/test_config.py::test_web_enabled_flag -x` | ❌ Wave 0 |
| CFG-04 | Target file path specification | unit | `pytest tests/test_config.py::test_target_file_path -x` | ❌ Wave 0 |
| CFG-04 | Path string to Path object conversion | unit | `pytest tests/test_config.py::test_path_conversion -x` | ❌ Wave 0 |
| CFG-05 | GPIO pin number specification | unit | `pytest tests/test_config.py::test_gpio_pin_number -x` | ❌ Wave 0 |
| CFG-05 | GPIO pin range validation (0-27) | unit | `pytest tests/test_config.py::test_invalid_gpio_pin_range -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_config.py -x` (fast fail on config tests)
- **Per wave merge:** `pytest tests/ -v` (full suite including existing v0.1 tests)
- **Phase gate:** Full suite green + manual YAML file creation test before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_config.py` — covers all CFG-01 through CFG-05 requirements
  - test_load_valid_config
  - test_load_config_with_defaults
  - test_missing_config_file
  - test_invalid_yaml_syntax
  - test_empty_config_file
  - test_gpio_enabled_flag
  - test_web_enabled_flag
  - test_target_file_path
  - test_path_conversion
  - test_gpio_pin_number
  - test_invalid_gpio_pin_range
  - test_gpio_pin_type_validation
- [ ] `printer_config.yaml` (example) — reference config for documentation
- [ ] Framework already installed: pytest 9.0+ in requirements.txt ✓

## Sources

### Primary (HIGH confidence)
- [PyYAML 6.0.3 on PyPI](https://pypi.org/project/PyYAML/) - Version compatibility, Python 3.13 support
- [Python dataclasses Documentation](https://docs.python.org/3/library/dataclasses.html) - Official stdlib docs for schema patterns
- [Python pathlib Documentation](https://docs.python.org/3/library/pathlib.html) - Official stdlib docs for path handling
- [PyYAML safe_load Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation) - Official docs on secure YAML loading
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/) - Official BCM pin numbering reference

### Secondary (MEDIUM confidence)
- [Python YAML: How to Load, Read, and Write YAML](https://python.land/data-processing/python-yaml) - YAML loading patterns
- [Working with YAML Files in Python | Better Stack Community](https://betterstack.com/community/guides/scaling-python/yaml-files-in-python/) - Best practices 2026
- [PyYAML yaml.load(input) Deprecation](https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation) - Security advisory
- [Working with Python Configuration Files: Tutorial & Best Practices](https://configu.com/blog/working-with-python-configuration-files-tutorial-best-practices/) - Configuration patterns
- [Python Dataclasses: The Complete Guide for 2026](https://devtoolbox.dedyn.io/blog/python-dataclasses-guide) - Dataclass best practices
- [Pydantic Dataclasses Documentation](https://docs.pydantic.dev/latest/concepts/dataclasses/) - Advanced validation patterns
- [How to Configure pytest for Python Testing](https://oneuptime.com/blog/post/2026-01-24-configure-pytest-python-testing/view) - pytest configuration 2026
- [gpiozero 2.0.1 Documentation](https://gpiozero.readthedocs.io/en/stable/) - GPIO pin numbering (BCM)

### Tertiary (LOW confidence)
- WebSearch results on configuration file locations - Multiple sources, general consensus patterns
- WebSearch results on YAML error handling - Aggregated best practices from community tutorials

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PyYAML 6.0.3 is current stable with Python 3.13 wheels, dataclasses are stdlib
- Architecture: HIGH - Dataclass frozen pattern is well-established Python best practice, search path pattern is standard
- Pitfalls: HIGH - yaml.load security issue is well-documented CVE, other pitfalls verified in official docs and community forums
- Validation: HIGH - pytest infrastructure already exists, test patterns are standard unit testing

**Research date:** 2026-03-13
**Valid until:** ~2026-09-13 (6 months - stable technology, slow-moving domain)

**Key assumptions verified:**
- PyYAML 6.0.3 supports Python 3.13 (checked PyPI release dates)
- Raspberry Pi 3B+ uses BCM GPIO 0-27 (verified against pinout.xyz)
- yaml.safe_load() prevents code execution (verified security advisories)
- dataclasses available in Python 3.13 (stdlib since 3.7)

**Integration points validated:**
- Config module will be imported by GPIO listener (Phase 4) and web server (Phase 5)
- PrinterConfig.target_file will be passed to existing printer.print_file() from v0.1
- Existing test infrastructure (pytest.ini, conftest.py) supports new test_config.py
