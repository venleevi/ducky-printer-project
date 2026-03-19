#!/usr/bin/env python3
"""Ducky Printer - GPIO-triggered thermal printing service.

Loads configuration, starts GPIO listener, and runs until interrupted.
"""

import logging
import signal
import sys
import time
from pathlib import Path

from src.config import load_config, start_config_watcher
from src.gpio_listener import start_gpio_listener

# Configure logging for systemd journal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# Global references for signal handler
gpio_observer = None
config_observer = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")

    if gpio_observer:
        logger.info("Stopping GPIO listener...")
        gpio_observer.close()

    if config_observer:
        logger.info("Stopping config watcher...")
        config_observer.stop()
        config_observer.join(timeout=2)

    logger.info("Shutdown complete")
    sys.exit(0)


def main():
    """Main service loop."""
    global gpio_observer, config_observer

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info("Starting Ducky Printer service...")

    # Load initial configuration
    config_path = Path("config.yaml")
    try:
        config = load_config(config_path)
        logger.info(f"Loaded config: GPIO pin {config.gpio_pin}, mode {config.trigger_mode}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Start GPIO listener
    try:
        gpio_observer = start_gpio_listener(config)
        logger.info("GPIO listener started")
    except Exception as e:
        logger.error(f"Failed to start GPIO listener: {e}")
        sys.exit(1)

    # Start config file watcher for hot-reload
    def reload_config():
        """Reload configuration and restart GPIO listener."""
        global gpio_observer

        try:
            logger.info("Config file changed, reloading...")
            new_config = load_config(config_path)

            # Stop old GPIO listener
            if gpio_observer:
                gpio_observer.close()

            # Start new GPIO listener with updated config
            gpio_observer = start_gpio_listener(new_config)
            logger.info(f"Config reloaded: GPIO pin {new_config.gpio_pin}, mode {new_config.trigger_mode}")
        except Exception as e:
            logger.error(f"Config reload failed: {e}")

    try:
        config_observer = start_config_watcher(config_path, reload_config)
        logger.info("Config watcher started")
    except Exception as e:
        logger.warning(f"Config watcher failed to start: {e}")

    # Run forever
    logger.info("Service running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
