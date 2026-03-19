"""Tests for GPIO listener with button/switch modes, debounce, and cooldown.

Tests cover GPIO-01, GPIO-02, GPIO-03, GPIO-04 requirements:
- Button press triggers print via handle_print_trigger
- Switch toggle triggers print based on configured direction
- Cooldown prevents rapid-press spam
- Hardware debounce prevents false triggers from electrical noise
- Error resilience (handle_print_trigger returning False)
"""

import pytest
import time
from unittest.mock import MagicMock, patch, call
from pathlib import Path
from src.config.schema import PrinterConfig
from src.gpio_listener import start_gpio_listener


# GPIO-01: Button press triggers print
def test_button_mode_triggers_print(mocker):
    """Test that button press in 'press' mode calls handle_print_trigger."""
    mock_button = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mock_button_class = mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(
        gpio_pin=17,
        trigger_mode="press",
        cooldown_seconds=0.0
    )

    listener = start_gpio_listener(config)

    # Verify Button created with correct parameters
    mock_button_class.assert_called_once_with(17, pull_up=True, bounce_time=0.01)

    # Simulate button press by calling the registered callback
    assert mock_button.when_pressed is not None
    callback = mock_button.when_pressed
    callback()

    # Verify handle_print_trigger was called with config
    mock_handle.assert_called_once_with(config)


def test_button_mode_passes_config_to_handler(mocker):
    """Test that button callback receives correct config with gpio_pin set."""
    mock_button = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(
        gpio_pin=22,
        trigger_mode="press",
        source_folder=Path("test_folder"),
        cooldown_seconds=0.0
    )

    listener = start_gpio_listener(config)
    callback = mock_button.when_pressed
    callback()

    # Verify config passed to handle_print_trigger
    called_config = mock_handle.call_args[0][0]
    assert called_config.gpio_pin == 22
    assert called_config.source_folder == Path("test_folder")


def test_button_mode_uses_hardware_debounce(mocker):
    """Test that Button is created with bounce_time parameter."""
    mock_button = MagicMock()
    mock_button_class = mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(gpio_pin=17, trigger_mode="press")
    listener = start_gpio_listener(config)

    # Verify bounce_time passed to constructor
    mock_button_class.assert_called_once_with(17, pull_up=True, bounce_time=0.01)


# GPIO-02: Switch toggle triggers print based on direction
def test_switch_mode_both_direction_triggers_on_both_edges(mocker):
    """Test that switch_direction='both' triggers on rising AND falling edges."""
    mock_switch = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.InputDevice', return_value=mock_switch)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(
        gpio_pin=17,
        trigger_mode="switch",
        switch_direction="both",
        cooldown_seconds=0.0
    )

    listener = start_gpio_listener(config)

    # Verify both callbacks are set
    assert mock_switch.when_activated is not None
    assert mock_switch.when_deactivated is not None

    # Simulate rising edge (activated)
    mock_switch.when_activated()
    mock_handle.assert_called_with(config)

    # Simulate falling edge (deactivated)
    mock_switch.when_deactivated()
    assert mock_handle.call_count == 2


def test_switch_mode_on_only_direction_triggers_on_rising_edge_only(mocker):
    """Test that switch_direction='on_only' triggers only on rising edge."""
    mock_switch = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.InputDevice', return_value=mock_switch)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(
        gpio_pin=17,
        trigger_mode="switch",
        switch_direction="on_only",
        cooldown_seconds=0.0
    )

    listener = start_gpio_listener(config)

    # Verify only activated callback is set
    assert mock_switch.when_activated is not None
    assert mock_switch.when_deactivated is None

    # Simulate rising edge
    mock_switch.when_activated()
    mock_handle.assert_called_once_with(config)


def test_switch_mode_off_only_direction_triggers_on_falling_edge_only(mocker):
    """Test that switch_direction='off_only' triggers only on falling edge."""
    mock_switch = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.InputDevice', return_value=mock_switch)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(
        gpio_pin=17,
        trigger_mode="switch",
        switch_direction="off_only",
        cooldown_seconds=0.0
    )

    listener = start_gpio_listener(config)

    # Verify only deactivated callback is set
    assert mock_switch.when_activated is None
    assert mock_switch.when_deactivated is not None

    # Simulate falling edge
    mock_switch.when_deactivated()
    mock_handle.assert_called_once_with(config)


def test_switch_mode_uses_hardware_debounce(mocker):
    """Test that InputDevice is created with bounce_time parameter."""
    mock_switch = MagicMock()
    mock_switch_class = mocker.patch('src.gpio_listener.InputDevice', return_value=mock_switch)
    mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(gpio_pin=17, trigger_mode="switch")
    listener = start_gpio_listener(config)

    # Verify bounce_time passed to constructor
    mock_switch_class.assert_called_once_with(17, pull_up=True, bounce_time=0.01)


# GPIO-03: Cooldown prevents rapid-press spam
def test_cooldown_first_press_triggers_immediately(mocker):
    """Test that first button press triggers print without delay."""
    mock_button = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(
        gpio_pin=17,
        trigger_mode="press",
        cooldown_seconds=2.0
    )

    listener = start_gpio_listener(config)
    callback = mock_button.when_pressed

    # First press should trigger immediately
    callback()
    mock_handle.assert_called_once()


def test_cooldown_second_press_within_window_does_not_trigger(mocker):
    """Test that second press within cooldown window does NOT trigger print."""
    mock_button = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.LGPIOFactory')
    mock_time = mocker.patch('src.gpio_listener.time')

    # Mock time progression: 0s -> 1s (within 2s cooldown)
    mock_time.time.side_effect = [0.0, 1.0]

    config = PrinterConfig(
        gpio_pin=17,
        trigger_mode="press",
        cooldown_seconds=2.0
    )

    listener = start_gpio_listener(config)
    callback = mock_button.when_pressed

    # First press
    callback()
    assert mock_handle.call_count == 1

    # Second press within cooldown (1s < 2s)
    callback()
    assert mock_handle.call_count == 1  # Should NOT call again


def test_cooldown_press_after_expiry_does_trigger(mocker):
    """Test that press after cooldown expires DOES trigger print."""
    mock_button = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.LGPIOFactory')
    mock_time = mocker.patch('src.gpio_listener.time')

    # Mock time progression: 0s -> 2.5s (after 2s cooldown)
    mock_time.time.side_effect = [0.0, 2.5]

    config = PrinterConfig(
        gpio_pin=17,
        trigger_mode="press",
        cooldown_seconds=2.0
    )

    listener = start_gpio_listener(config)
    callback = mock_button.when_pressed

    # First press
    callback()
    assert mock_handle.call_count == 1

    # Second press after cooldown (2.5s > 2s)
    callback()
    assert mock_handle.call_count == 2  # Should call again


def test_cooldown_tracks_last_trigger_time(mocker):
    """Test that cooldown is tracked per-activation using last_trigger_time."""
    mock_button = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.LGPIOFactory')
    mock_time = mocker.patch('src.gpio_listener.time')

    # Mock time progression: 0s -> 1s -> 3s
    mock_time.time.side_effect = [0.0, 1.0, 3.0]

    config = PrinterConfig(
        gpio_pin=17,
        trigger_mode="press",
        cooldown_seconds=2.0
    )

    listener = start_gpio_listener(config)
    callback = mock_button.when_pressed

    # First press at t=0
    callback()
    assert mock_handle.call_count == 1

    # Second press at t=1 (within cooldown)
    callback()
    assert mock_handle.call_count == 1

    # Third press at t=3 (after cooldown from first press)
    callback()
    assert mock_handle.call_count == 2


def test_cooldown_zero_allows_all_presses(mocker):
    """Test that cooldown_seconds=0 disables cooldown enforcement."""
    mock_button = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(
        gpio_pin=17,
        trigger_mode="press",
        cooldown_seconds=0.0
    )

    listener = start_gpio_listener(config)
    callback = mock_button.when_pressed

    # Multiple rapid presses should all trigger
    callback()
    callback()
    callback()

    assert mock_handle.call_count == 3


# GPIO-04: Hardware debounce parameters
def test_default_bounce_time_is_10ms(mocker):
    """Test that default bounce_time is 0.01s (10ms)."""
    mock_button = MagicMock()
    mock_button_class = mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(gpio_pin=17, trigger_mode="press")
    listener = start_gpio_listener(config)

    # Verify 10ms bounce_time
    call_kwargs = mock_button_class.call_args[1]
    assert call_kwargs['bounce_time'] == 0.01


# Error resilience (GPIO-05 satisfaction in Phase 04)
def test_handle_print_trigger_returning_false_does_not_crash(mocker):
    """Test that handle_print_trigger returning False does not crash listener."""
    mock_button = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=False)
    mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(gpio_pin=17, trigger_mode="press", cooldown_seconds=0.0)
    listener = start_gpio_listener(config)
    callback = mock_button.when_pressed

    # Should not raise exception
    callback()
    callback()

    # Both calls should go through (False return is not an error)
    assert mock_handle.call_count == 2


def test_exceptions_in_callback_are_caught_and_logged(mocker):
    """Test that exceptions in GPIO callback are caught and logged."""
    mock_button = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', side_effect=RuntimeError("Test error"))
    mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.LGPIOFactory')
    mock_logger = mocker.patch('src.gpio_listener.logger')

    config = PrinterConfig(gpio_pin=17, trigger_mode="press", cooldown_seconds=0.0)
    listener = start_gpio_listener(config)
    callback = mock_button.when_pressed

    # Should not raise exception
    callback()

    # Should log exception
    mock_logger.exception.assert_called_once()


# Lifecycle management
def test_start_gpio_listener_returns_button_object(mocker):
    """Test that start_gpio_listener() returns Button object for lifecycle control."""
    mock_button = MagicMock()
    mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(gpio_pin=17, trigger_mode="press")
    listener = start_gpio_listener(config)

    assert listener is mock_button


def test_start_gpio_listener_returns_input_device_for_switch(mocker):
    """Test that start_gpio_listener() returns InputDevice for switch mode."""
    mock_switch = MagicMock()
    mocker.patch('src.gpio_listener.InputDevice', return_value=mock_switch)
    mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(gpio_pin=17, trigger_mode="switch")
    listener = start_gpio_listener(config)

    assert listener is mock_switch


def test_stopping_listener_cleans_up_gpio(mocker):
    """Test that calling close() on returned object cleans up GPIO resources."""
    mock_button = MagicMock()
    mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(gpio_pin=17, trigger_mode="press")
    listener = start_gpio_listener(config)

    # Simulate cleanup
    listener.close()

    # Verify close was called
    mock_button.close.assert_called_once()


def test_lgpio_factory_set_for_pi_compatibility(mocker):
    """Test that LGPIOFactory is set for Raspberry Pi 3B+ compatibility."""
    mock_button = MagicMock()
    mock_factory = mocker.patch('src.gpio_listener.LGPIOFactory')
    mock_button_class = mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)

    config = PrinterConfig(gpio_pin=17, trigger_mode="press")

    # Access Button.pin_factory before calling start_gpio_listener
    original_factory = mock_button_class.pin_factory

    listener = start_gpio_listener(config)

    # Verify factory was set to LGPIOFactory instance
    assert mock_button_class.pin_factory == mock_factory.return_value


def test_config_passed_to_callback_is_loaded_config(mocker):
    """Test that callback receives the exact config passed to start_gpio_listener."""
    mock_button = MagicMock()
    mock_handle = mocker.patch('src.gpio_listener.handle_print_trigger', return_value=True)
    mocker.patch('src.gpio_listener.Button', return_value=mock_button)
    mocker.patch('src.gpio_listener.LGPIOFactory')

    config = PrinterConfig(
        gpio_pin=25,
        trigger_mode="press",
        cooldown_seconds=1.5,
        source_folder=Path("custom_folder")
    )

    listener = start_gpio_listener(config)
    callback = mock_button.when_pressed
    callback()

    # Verify exact config object passed
    called_config = mock_handle.call_args[0][0]
    assert called_config.gpio_pin == 25
    assert called_config.cooldown_seconds == 1.5
    assert called_config.source_folder == Path("custom_folder")
