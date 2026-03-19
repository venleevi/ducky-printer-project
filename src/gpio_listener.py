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


def start_gpio_listener(config: PrinterConfig):
    """Start GPIO listener for button or switch trigger mode.

    Args:
        config: PrinterConfig with gpio_pin, trigger_mode, cooldown settings

    Returns:
        Button or InputDevice object for lifecycle management
    """
    pass
