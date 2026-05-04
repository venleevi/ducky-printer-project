"""Configuration schema with Pydantic validation.

Defines the PrinterConfig dataclass with validation rules for:
- GPIO pin number (BCM 2-27, excluding reserved pins)
- Trigger mode (press or switch)
- Cooldown duration (non-negative)
- Source folder (path validation)
- Switch direction (both, on_only, or off_only)
"""

from pathlib import Path
from typing import Literal
from pydantic import Field, field_validator
from pydantic.dataclasses import dataclass


@dataclass
class PrinterConfig:
    """Printer GPIO trigger configuration with validation.

    All fields have sensible defaults. Missing config values will use these defaults.
    """

    gpio_pin: int = Field(
        default=17,
        ge=0,
        le=27,
        description="BCM GPIO pin number (2-27, excluding reserved pins 0,1,14,15)"
    )

    trigger_mode: Literal["press", "switch"] = Field(
        default="press",
        description="Button press (momentary) or switch flip (toggle) trigger"
    )

    cooldown_seconds: float = Field(
        default=2.0,
        ge=0,
        description="Minimum seconds between print activations (0 = no cooldown)"
    )

    source_folder: Path = Field(
        default=Path("print_files"),
        description="Folder containing files to print (.txt, .png, .jpg, .bmp)"
    )

    switch_direction: Literal["both", "on_only", "off_only"] = Field(
        default="both",
        description="Which switch transitions trigger printing (both/on_only/off_only)"
    )

    printer_interface: Literal["usb", "serial"] = Field(
        default="serial",
        description="Printer connection type: 'usb' (USB class 7) or 'serial' (virtual COM port e.g. /dev/ttyACM0)"
    )

    serial_port: str = Field(
        default="/dev/ttyACM0",
        description="Serial device path (only used when printer_interface is 'serial')"
    )

    serial_baudrate: int = Field(
        default=9600,
        gt=0,
        description="Serial baud rate (only used when printer_interface is 'serial')"
    )

    @field_validator('gpio_pin')
    @classmethod
    def validate_gpio_pin_not_reserved(cls, v: int) -> int:
        """Check GPIO pin is not reserved for special functions and is in valid range.

        Reserved pins:
        - 0, 1: I2C (SDA, SCL)
        - 14, 15: UART (TXD, RXD)

        Valid range: 2-27 (BCM numbering)

        Args:
            v: GPIO pin number

        Returns:
            int: Validated pin number

        Raises:
            ValueError: If pin is reserved or out of valid range
        """
        reserved = {0, 1, 14, 15}
        if v in reserved:
            raise ValueError(
                f"GPIO {v} is reserved (I2C: 0-1, UART: 14-15). "
                f"Use pins 2-27 excluding reserved pins."
            )
        if v < 2 or v > 27:
            raise ValueError(
                f"GPIO pin must be in range 2-27 (BCM numbering). Got {v}."
            )
        return v

    @field_validator('source_folder')
    @classmethod
    def validate_source_folder_exists(cls, v: Path) -> Path:
        """Ensure source folder exists and is a directory.

        NOTE: Skips validation for the default value Path("print_files")
        to allow schema instantiation in tests/CI where the folder doesn't exist.
        The loader validates folder existence after applying config values.

        Args:
            v: Source folder path

        Returns:
            Path: Validated path

        Raises:
            ValueError: If path doesn't exist or is not a directory
        """
        # Skip validation for default value (may not exist at test time)
        if v == Path("print_files"):
            return v

        if not v.exists():
            raise ValueError(f"Source folder does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Source folder is not a directory: {v}")
        return v
