"""
Модуль персистентного збереження стану та звітів у форматах JSON і CSV.
Освітній компонент: Програмування на Python. Базовий рівень.
Спеціальність: F7 «Комп'ютерна інженерія». Варіант 20.
"""

import csv
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cooling_controller.controller import ControlDecision
from cooling_controller.exceptions import ConfigurationError
from cooling_controller.models import ServerRack
from cooling_controller.parser import parse_telemetry_lines


def load_telemetry_file(filepath: str | Path) -> list[ServerRack]:
    """Зчитує та валідує вхідний файл телеметрії через менеджер контексту with."""
    path = Path(filepath)
    if not path.is_file():
        raise ConfigurationError(f"Вхідний файл телеметрії не знайдено: '{path}'")

    try:
        with open(path, mode="r", encoding="utf-8") as file:
            return parse_telemetry_lines(file)
    except OSError as exc:
        raise ConfigurationError(f"Помилка читання файлу '{path}': {exc}") from exc


def save_state_json(
    filepath: str | Path,
    decisions: list[ControlDecision],
    racks: list[ServerRack],
) -> Path:
    """Зберігає повний знімок стану контролера та стійок у файл JSON (with)."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "zone_count": len(decisions),
        "rack_count": len(racks),
        "decisions": [asdict(item) for item in decisions],
        "racks": [rack.to_dict() for rack in racks],
    }

    try:
        with open(path, mode="w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise ConfigurationError(f"Не вдалося записати JSON-файл '{path}': {exc}") from exc

    return path


def load_state_json(filepath: str | Path) -> dict[str, Any]:
    """Завантажує збережений знімок стану контролера з JSON-файлу (with)."""
    path = Path(filepath)
    if not path.is_file():
        raise ConfigurationError(f"JSON-файл стану не знайдено: '{path}'")

    try:
        with open(path, mode="r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"Помилка декодування JSON '{path}': {exc}") from exc

    if not isinstance(data, dict) or "decisions" not in data:
        raise ConfigurationError(f"Некоректна структура JSON-знімка у '{path}'.")
    return data


def save_decisions_csv(
    filepath: str | Path,
    decisions: list[ControlDecision],
) -> Path:
    """Експортує журнал рішень контролера у таблицю CSV через менеджер контексту with."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "zone_id",
        "crac_id",
        "rack_count",
        "total_power_kw",
        "peak_rack_id",
        "peak_temp_c",
        "base_airflow_m3h",
        "adaptive_factor",
        "target_airflow_m3h",
        "fan_pwm_percent",
        "mode_name",
        "register_word",
        "register_hex",
        "fault_active",
    ]

    try:
        with open(path, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for decision in decisions:
                writer.writerow(asdict(decision))
    except OSError as exc:
        raise ConfigurationError(f"Не вдалося записати CSV-звіт '{path}': {exc}") from exc

    return path