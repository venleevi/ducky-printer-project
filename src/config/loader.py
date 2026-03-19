"""Configuration loader with YAML parsing and user-friendly error messages.

Loads configuration from YAML files, applies defaults for missing values,
and validates with clear, user-friendly error messages.
"""

import yaml
from pathlib import Path
from pydantic import ValidationError
from .schema import PrinterConfig


class ConfigError(Exception):
    """User-friendly configuration error.

    Raised when config file has invalid syntax or values.
    Messages are formatted for end users, not developers.
    """
    pass


def load_config(config_path: Path = Path("config.yaml")) -> PrinterConfig:
    """Load and validate configuration from YAML file.

    Missing config file returns all defaults.
    Empty config file returns all defaults.
    Partial config file merges provided values with defaults.

    Args:
        config_path: Path to YAML config file (default: config.yaml)

    Returns:
        PrinterConfig: Validated configuration with defaults applied

    Raises:
        ConfigError: If YAML syntax is invalid or values fail validation
    """
    try:
        # Missing file: use all defaults
        if not config_path.exists():
            return PrinterConfig()

        # Open and parse YAML
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}  # Handle empty file

        # Validate with Pydantic (applies defaults for missing fields)
        config = PrinterConfig(**data)

        # Additional validation: check source_folder exists (if not default)
        # This catches cases where the user provided a custom path
        if config.source_folder != Path("print_files"):
            if not config.source_folder.exists():
                raise ConfigError(
                    f"Configuration validation failed in {config_path}:\n"
                    f"  - source_folder: Directory does not exist: {config.source_folder}\n\n"
                    f"Create the directory or update your config file."
                )
            if not config.source_folder.is_dir():
                raise ConfigError(
                    f"Configuration validation failed in {config_path}:\n"
                    f"  - source_folder: Not a directory: {config.source_folder}\n\n"
                    f"Provide a directory path or update your config file."
                )

        return config

    except yaml.YAMLError as e:
        raise ConfigError(
            f"Invalid YAML syntax in {config_path}:\n{e}\n\n"
            f"Fix the YAML syntax and try again."
        )

    except ValidationError as e:
        # Convert Pydantic errors to user-friendly format
        errors = []
        for error in e.errors():
            field = ".".join(str(x) for x in error['loc'])
            msg = error['msg']
            errors.append(f"  - {field}: {msg}")

        raise ConfigError(
            f"Configuration validation failed in {config_path}:\n" +
            "\n".join(errors) +
            "\n\nFix these errors and restart the service."
        )
