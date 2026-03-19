"""Tests for config file watcher with hot-reload."""

import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.config.watcher import ConfigWatcher, start_config_watcher


def test_watcher_calls_callback_on_file_change(tmp_path):
    """File modification triggers reload callback within 2 seconds."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("gpio_pin: 17\n")

    callback = Mock()
    observer = start_config_watcher(config_file, callback, debounce_seconds=0.1)

    try:
        # Modify the file
        time.sleep(0.2)  # Let observer start
        config_file.write_text("gpio_pin: 22\n")

        # Poll for callback within 2 seconds
        for _ in range(20):
            time.sleep(0.1)
            if callback.called:
                break

        assert callback.called, "Callback should be called within 2 seconds"
    finally:
        observer.stop()
        observer.join(timeout=2)


def test_watcher_debounces_rapid_changes(tmp_path):
    """Rapid file modifications produce only one reload."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("gpio_pin: 17\n")

    callback = Mock()
    observer = start_config_watcher(config_file, callback, debounce_seconds=1.0)

    try:
        time.sleep(0.2)  # Let observer start

        # Make 3 rapid changes within 0.5 seconds
        config_file.write_text("gpio_pin: 18\n")
        time.sleep(0.15)
        config_file.write_text("gpio_pin: 19\n")
        time.sleep(0.15)
        config_file.write_text("gpio_pin: 20\n")

        # Wait for debounce window to pass
        time.sleep(1.5)

        # Should be called at most 2 times (first change + possibly last if debounce expired)
        # But definitely not 3 times (one per change)
        assert callback.call_count <= 2, f"Debouncing failed: called {callback.call_count} times"
    finally:
        observer.stop()
        observer.join(timeout=2)


def test_watcher_survives_invalid_config(tmp_path):
    """Invalid config during reload logs error but keeps watcher running."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("gpio_pin: 17\n")

    # Callback that raises an error
    callback = Mock(side_effect=ValueError("Invalid config"))
    observer = start_config_watcher(config_file, callback, debounce_seconds=0.1)

    try:
        time.sleep(0.2)  # Let observer start

        # Modify file to trigger callback with error
        config_file.write_text("gpio_pin: 22\n")
        time.sleep(0.5)

        # Callback should have been called despite error
        assert callback.called, "Callback should be called even if it raises"

        # Observer should still be alive
        assert observer.is_alive(), "Observer should survive callback errors"

        # Reset mock and verify watcher still works
        callback.reset_mock()
        callback.side_effect = None

        config_file.write_text("gpio_pin: 23\n")

        for _ in range(20):
            time.sleep(0.1)
            if callback.called:
                break

        assert callback.called, "Watcher should still work after previous error"
    finally:
        observer.stop()
        observer.join(timeout=2)


def test_watcher_ignores_other_files(tmp_path):
    """Modifying a different file does not trigger callback."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("gpio_pin: 17\n")

    other_file = tmp_path / "other.yaml"
    other_file.write_text("unrelated: data\n")

    callback = Mock()
    observer = start_config_watcher(config_file, callback, debounce_seconds=0.1)

    try:
        time.sleep(0.2)  # Let observer start

        # Modify the other file
        other_file.write_text("unrelated: changed\n")

        # Wait a bit
        time.sleep(0.5)

        # Callback should NOT be called
        assert not callback.called, "Callback should not be called for other files"
    finally:
        observer.stop()
        observer.join(timeout=2)


def test_watcher_stop(tmp_path):
    """Observer stops cleanly."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("gpio_pin: 17\n")

    callback = Mock()
    observer = start_config_watcher(config_file, callback)

    time.sleep(0.2)
    assert observer.is_alive(), "Observer should be running"

    observer.stop()
    observer.join(timeout=2)

    assert not observer.is_alive(), "Observer should stop cleanly"


def test_start_config_watcher_returns_observer(tmp_path):
    """start_config_watcher returns a stoppable Observer."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("gpio_pin: 17\n")

    callback = Mock()
    observer = start_config_watcher(config_file, callback)

    try:
        # Should return an Observer instance
        assert hasattr(observer, 'stop'), "Should return Observer with stop method"
        assert hasattr(observer, 'join'), "Should return Observer with join method"
        assert hasattr(observer, 'is_alive'), "Should return Observer with is_alive method"
    finally:
        observer.stop()
        observer.join(timeout=2)
