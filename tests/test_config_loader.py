"""Tests for configuration loader with YAML parsing and error formatting.

Tests YAML loading, validation, defaults, and user-friendly error messages.
"""

import pytest
from pathlib import Path
from src.config.loader import load_config, ConfigError
from src.config.schema import PrinterConfig


def test_load_valid_config(tmp_path):
    """load_config(path_to_valid_yaml) returns PrinterConfig with values from YAML."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
gpio_pin: 22
trigger_mode: switch
cooldown_seconds: 5.0
source_folder: /tmp
switch_direction: on_only
""")

    config = load_config(config_file)
    assert config.gpio_pin == 22
    assert config.trigger_mode == "switch"
    assert config.cooldown_seconds == 5.0
    assert config.source_folder == Path("/tmp")
    assert config.switch_direction == "on_only"


def test_load_missing_file_returns_defaults(tmp_path):
    """load_config(nonexistent_path) returns PrinterConfig() with all defaults."""
    nonexistent = tmp_path / "nonexistent.yaml"
    config = load_config(nonexistent)

    # Should get all defaults
    assert config.gpio_pin == 17
    assert config.trigger_mode == "press"
    assert config.cooldown_seconds == 2.0
    assert config.source_folder == Path("print_files")
    assert config.switch_direction == "both"


def test_load_empty_file_returns_defaults(tmp_path):
    """load_config(empty_yaml) returns PrinterConfig() with all defaults."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("")

    config = load_config(config_file)
    assert config.gpio_pin == 17
    assert config.trigger_mode == "press"


def test_load_partial_config(tmp_path):
    """YAML with only gpio_pin=22 returns config with gpio_pin=22 and all other defaults."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("gpio_pin: 22\n")

    config = load_config(config_file)
    assert config.gpio_pin == 22
    assert config.trigger_mode == "press"  # default
    assert config.cooldown_seconds == 2.0  # default


def test_load_invalid_yaml_syntax(tmp_path):
    """load_config(malformed_yaml) raises ConfigError with file path in message."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("gpio_pin: [invalid yaml syntax here")

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)

    error_msg = str(exc_info.value)
    assert str(config_file) in error_msg


def test_load_invalid_values(tmp_path):
    """load_config(yaml_with_gpio_pin=99) raises ConfigError with field-level error message."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("gpio_pin: 99\n")

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)

    error_msg = str(exc_info.value)
    assert "gpio_pin" in error_msg


def test_load_multiple_errors(tmp_path):
    """YAML with gpio_pin=99 AND cooldown=-1 raises ConfigError listing both errors."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
gpio_pin: 99
cooldown_seconds: -1
""")

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)

    error_msg = str(exc_info.value)
    assert "gpio_pin" in error_msg
    assert "cooldown_seconds" in error_msg


def test_config_error_includes_field_names(tmp_path):
    """ConfigError message contains the failing field name."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("trigger_mode: invalid_mode\n")

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)

    error_msg = str(exc_info.value)
    assert "trigger_mode" in error_msg


def test_config_error_is_human_readable(tmp_path):
    """ConfigError message does NOT contain Python tracebacks or Pydantic internals."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("gpio_pin: 99\n")

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)

    error_msg = str(exc_info.value)
    # Should NOT contain Pydantic internals
    assert "ValidationError" not in error_msg
    assert "pydantic" not in error_msg.lower()
    # Should be user-friendly
    assert "config" in error_msg.lower() or "validation" in error_msg.lower()


def test_load_validates_source_folder_exists(tmp_path):
    """YAML with source_folder pointing to nonexistent dir raises ConfigError."""
    config_file = tmp_path / "config.yaml"
    nonexistent_dir = tmp_path / "nonexistent_folder"
    config_file.write_text(f"source_folder: {nonexistent_dir}\n")

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)

    error_msg = str(exc_info.value)
    assert "source_folder" in error_msg or "does not exist" in error_msg.lower()
