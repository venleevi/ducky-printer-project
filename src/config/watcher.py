"""Configuration file watcher with debouncing for hot-reload.

Monitors the config YAML file for changes and triggers a reload callback.
Handles rapid saves (editor atomic writes) with debouncing, and survives
invalid config without crashing.
"""

import logging
import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class ConfigWatcher(FileSystemEventHandler):
    """Watches a config file for changes and triggers reload with debouncing.

    Handles FileModifiedEvent and FileCreatedEvent to cover both normal
    saves and atomic save patterns (write temp + rename).
    """

    def __init__(
        self,
        config_path: Path,
        reload_callback: Callable,
        debounce_seconds: float = 1.0,
    ):
        super().__init__()
        self.config_path = config_path.resolve()
        self.reload_callback = reload_callback
        self.debounce_seconds = debounce_seconds
        self._last_reload_time: float = 0

    def on_modified(self, event):
        self._handle_event(event)

    def on_created(self, event):
        self._handle_event(event)

    def _handle_event(self, event):
        if event.is_directory:
            return

        event_path = Path(event.src_path).resolve()
        if event_path != self.config_path:
            return

        now = time.time()
        if now - self._last_reload_time < self.debounce_seconds:
            return

        self._last_reload_time = now
        try:
            self.reload_callback()
        except Exception:
            logger.exception("Config reload failed — watcher continues running")


def start_config_watcher(
    config_path: Path,
    reload_callback: Callable,
    debounce_seconds: float = 1.0,
) -> Observer:
    """Start watching a config file for changes.

    Args:
        config_path: Path to the config YAML file.
        reload_callback: Called when the file changes (after debounce).
        debounce_seconds: Minimum interval between reloads.

    Returns:
        Observer that can be stopped with observer.stop(); observer.join().
    """
    handler = ConfigWatcher(config_path, reload_callback, debounce_seconds)
    observer = Observer()
    observer.schedule(handler, str(config_path.resolve().parent), recursive=False)
    observer.start()
    return observer
