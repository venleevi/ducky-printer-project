"""Configuration module for printer GPIO trigger.

This module provides configuration schema, loading, and validation
for the Ducky Printer GPIO trigger system.
"""

from .schema import PrinterConfig
from .loader import load_config, ConfigError

__all__ = ["PrinterConfig", "load_config", "ConfigError"]
