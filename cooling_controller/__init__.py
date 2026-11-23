"""
Пакет програмного емулятора контролера прецизійного охолодження дата-центру.
Освітній компонент: Програмування на Python. Базовий рівень.
Спеціальність: F7 «Комп'ютерна інженерія». Варіант 20.
"""

from cooling_controller.exceptions import (
    AirflowLimitError,
    ConfigurationError,
    CoolingSystemError,
    HardwareLimitError,
    TelemetryValidationError,
    ThermalOverloadError,
)
from cooling_controller.hardware_register import CoolingMode, HardwareTelemetryRegister
from cooling_controller.models import CRACUnit, ServerRack, ThermalNode

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "CoolingSystemError",
    "ConfigurationError",
    "TelemetryValidationError",
    "HardwareLimitError",
    "ThermalOverloadError",
    "AirflowLimitError",
    "CoolingMode",
    "HardwareTelemetryRegister",
    "ThermalNode",
    "ServerRack",
    "CRACUnit",
]