"""
Пакет програмного емулятора контролера прецизійного охолодження дата-центру.
Освітній компонент: Програмування на Python. Базовий рівень.
Спеціальність: F7 «Комп'ютерна інженерія». Варіант 20.
"""

from cooling_controller.controller import ControlDecision, PrecisionCoolingController
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
from cooling_controller.parser import parse_telemetry_line, parse_telemetry_lines
from cooling_controller.storage import (
    load_state_json,
    load_telemetry_file,
    save_decisions_csv,
    save_state_json,
)

__version__ = "0.4.0"

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
    "ControlDecision",
    "PrecisionCoolingController",
    "parse_telemetry_line",
    "parse_telemetry_lines",
    "load_telemetry_file",
    "save_state_json",
    "load_state_json",
    "save_decisions_csv",
]