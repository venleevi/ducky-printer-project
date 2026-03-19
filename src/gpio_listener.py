"""GPIO button and switch listener with debounce and cooldown protection.

Implements GPIO-01, GPIO-02, GPIO-03, GPIO-04 requirements:
- Button press triggers print via handle_print_trigger
- Switch toggle triggers print based on configured direction
- Cooldown prevents rapid-press spam
- Hardware debounce prevents false triggers from electrical noise

This module provides the physical button integration that satisfies the core
value proposition: "user presses a physical button and a random file prints."
"""

import logging
import time
from gpiozero import Button, InputDevice
try:
    from gpiozero.pins.lgpio import LGPIOFactory
except ImportError:
    # lgpio not available (test environment or non-Pi system)
    # Tests will mock LGPIOFactory, real Pi will have system lgpio
    LGPIOFactory = None
from src.config.schema import PrinterConfig
from src.trigger_handler import handle_print_trigger

logger = logging.getLogger(__name__)

# Module-level variable to track last trigger time for cooldown enforcement
_last_trigger_time = None


def start_gpio_listener(config: PrinterConfig):
    """Start GPIO listener for button or switch trigger mode.

    Sets up GPIO hardware with debouncing and cooldown protection.
    Triggers print via handle_print_trigger when button pressed or switch flipped.

    Hardware configuration:
    - Uses LGPIOFactory for Raspberry Pi 3B+ compatibility (gpiozero issue #1090)
    - Hardware debounce: 10ms bounce_time (standard for mechanical buttons)
    - Pull-up resistor enabled (button/switch connects to ground)

    Requirements:
    - GPIO-01: Button press triggers print
    - GPIO-02: Switch toggle with direction configuration
    - GPIO-03: Cooldown prevents rapid-press spam
    - GPIO-04: Hardware debounce via bounce_time
    - GPIO-05: Error resilience (errors logged, never crash)

    Args:
        config: PrinterConfig with gpio_pin, trigger_mode, cooldown_seconds,
                switch_direction settings

    Returns:
        Button or InputDevice object for lifecycle management (caller should
        keep reference and call .close() to clean up GPIO resources)

    Example:
        >>> config = PrinterConfig(gpio_pin=17, trigger_mode="press")
        >>> listener = start_gpio_listener(config)
        >>> # Listener is now active, responding to GPIO events
        >>> listener.close()  # Clean up when done
    """
    global _last_trigger_time

    # Preserve cooldown state across config reloads (don't reset _last_trigger_time)
    # This ensures cooldown enforcement continues even after hot-reload

    # Set pin factory for Pi 3B+ compatibility
    if LGPIOFactory is not None:
        Button.pin_factory = LGPIOFactory()

    # Create callback with cooldown enforcement and error handling
    def gpio_callback():
        """Handle GPIO event with cooldown and error resilience."""
        global _last_trigger_time

        try:
            # Check cooldown
            current_time = time.time()
            if config.cooldown_seconds > 0 and _last_trigger_time is not None:
                elapsed = current_time - _last_trigger_time
                if elapsed < config.cooldown_seconds:
                    logger.info(
                        f"Button press ignored - cooldown active ({elapsed:.1f}s / {config.cooldown_seconds}s)"
                    )
                    return

            # Update trigger time before calling handler (prevents race conditions)
            _last_trigger_time = current_time

            # Trigger print
            logger.info("GPIO trigger activated")
            success = handle_print_trigger(config)

            if not success:
                logger.debug("Print trigger did not succeed (see above errors)")

        except Exception as e:
            # Catch all exceptions to prevent listener crash (GPIO-05)
            logger.exception(f"GPIO callback error: {e}")

    # Branch on trigger mode
    if config.trigger_mode == "press":
        # Button mode: momentary press
        button = Button(config.gpio_pin, pull_up=True, bounce_time=0.01)
        button.when_pressed = gpio_callback
        return button

    elif config.trigger_mode == "switch":
        # Switch mode: toggle with direction filtering
        switch = InputDevice(config.gpio_pin, pull_up=True, bounce_time=0.01)

        # Configure callbacks based on switch_direction
        if config.switch_direction in ("both", "on_only"):
            switch.when_activated = gpio_callback

        if config.switch_direction in ("both", "off_only"):
            switch.when_deactivated = gpio_callback

        return switch

    else:
        raise ValueError(f"Invalid trigger_mode: {config.trigger_mode}")
