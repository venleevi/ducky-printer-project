"""Tests for configuration schema validation.

Tests Pydantic dataclass validation for:
- GPIO pin number (2-27, excluding reserved pins)
- Trigger mode (press/switch)
- Cooldown duration (non-negative)
- Source folder (exists and is directory)
- Switch direction (both/on_only/off_only)
"""

import pytest
from pathlib import Path
from pydantic import ValidationError
from src.config.schema import PrinterConfig


def test_gpio_pin_default():
    """PrinterConfig() has gpio_pin=17."""
    config = PrinterConfig()
    assert config.gpio_pin == 17


def test_gpio_pin_valid_range():
    """gpio_pin=2 and gpio_pin=27 accepted."""
    config_low = PrinterConfig(gpio_pin=2)
    assert config_low.gpio_pin == 2

    config_high = PrinterConfig(gpio_pin=27)
    assert config_high.gpio_pin == 27


def test_gpio_pin_too_low():
    """gpio_pin=1 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PrinterConfig(gpio_pin=1)
    assert "gpio_pin" in str(exc_info.value)


def test_gpio_pin_too_high():
    """gpio_pin=28 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PrinterConfig(gpio_pin=28)
    assert "gpio_pin" in str(exc_info.value)


def test_gpio_pin_reserved():
    """gpio_pin=0, 1, 14, 15 raise ValidationError with 'reserved' message."""
    reserved_pins = [0, 1, 14, 15]
    for pin in reserved_pins:
        with pytest.raises(ValidationError) as exc_info:
            PrinterConfig(gpio_pin=pin)
        error_msg = str(exc_info.value)
        assert "reserved" in error_msg.lower(), f"Pin {pin} should mention 'reserved'"


def test_trigger_mode_default():
    """PrinterConfig() has trigger_mode='press'."""
    config = PrinterConfig()
    assert config.trigger_mode == "press"


def test_trigger_mode_valid():
    """'press' and 'switch' accepted."""
    config_press = PrinterConfig(trigger_mode="press")
    assert config_press.trigger_mode == "press"

    config_switch = PrinterConfig(trigger_mode="switch")
    assert config_switch.trigger_mode == "switch"


def test_trigger_mode_invalid():
    """'toggle' raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PrinterConfig(trigger_mode="toggle")
    assert "trigger_mode" in str(exc_info.value)


def test_cooldown_default():
    """PrinterConfig() has cooldown_seconds=2.0."""
    config = PrinterConfig()
    assert config.cooldown_seconds == 2.0


def test_cooldown_zero():
    """cooldown_seconds=0 accepted."""
    config = PrinterConfig(cooldown_seconds=0)
    assert config.cooldown_seconds == 0


def test_cooldown_negative():
    """cooldown_seconds=-1 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PrinterConfig(cooldown_seconds=-1)
    assert "cooldown_seconds" in str(exc_info.value)


def test_source_folder_valid(tmp_config_dir):
    """Existing directory path accepted."""
    config = PrinterConfig(source_folder=tmp_config_dir)
    assert config.source_folder == tmp_config_dir


def test_source_folder_nonexistent(tmp_path):
    """Nonexistent path raises ValidationError with 'does not exist'."""
    nonexistent = tmp_path / "nonexistent"
    with pytest.raises(ValidationError) as exc_info:
        PrinterConfig(source_folder=nonexistent)
    error_msg = str(exc_info.value)
    assert "does not exist" in error_msg.lower()


def test_source_folder_is_file(tmp_path):
    """Path to a file raises ValidationError with 'not a directory'."""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("test")

    with pytest.raises(ValidationError) as exc_info:
        PrinterConfig(source_folder=file_path)
    error_msg = str(exc_info.value)
    assert "not a directory" in error_msg.lower()


def test_source_folder_default():
    """PrinterConfig() has source_folder=Path('print_files').

    NOTE: Default value skips existence validation since the folder
    may not exist at test time. Existence is validated at config load time.
    """
    config = PrinterConfig()
    assert config.source_folder == Path("print_files")


def test_switch_direction_default():
    """PrinterConfig() has switch_direction='both'."""
    config = PrinterConfig()
    assert config.switch_direction == "both"


def test_switch_direction_valid():
    """'both', 'on_only', 'off_only' accepted."""
    config_both = PrinterConfig(switch_direction="both")
    assert config_both.switch_direction == "both"

    config_on = PrinterConfig(switch_direction="on_only")
    assert config_on.switch_direction == "on_only"

    config_off = PrinterConfig(switch_direction="off_only")
    assert config_off.switch_direction == "off_only"


def test_switch_direction_invalid():
    """'left' raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PrinterConfig(switch_direction="left")
    assert "switch_direction" in str(exc_info.value)


def test_all_defaults():
    """PrinterConfig() succeeds with all default values."""
    config = PrinterConfig()
    assert config.gpio_pin == 17
    assert config.trigger_mode == "press"
    assert config.cooldown_seconds == 2.0
    assert config.source_folder == Path("print_files")
    assert config.switch_direction == "both"
