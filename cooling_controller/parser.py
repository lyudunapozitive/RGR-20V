"""
Модуль імпорту, нормалізації та валідації телеметрії датчиків дата-центру.
Освітній компонент: Програмування на Python. Базовий рівень.
Спеціальність: F7 «Комп'ютерна інженерія». Варіант 20.
"""

import re
from collections.abc import Iterable

from cooling_controller.exceptions import TelemetryValidationError
from cooling_controller.models import ServerRack

# Регулярний вираз для перевірки формату текстового кадру телеметрії
TELEMETRY_LINE_RE = re.compile(
    r"^\s*"
    r"RACK\s*=\s*(?P<unit_id>[A-Za-z0-9_-]+)\s*\|\s*"
    r"ZONE\s*=\s*(?P<zone_id>-?\d+)\s*\|\s*"
    r"TEMP\s*=\s*(?P<temp>[+-]?\d+(?:[.,]\d+)?)\s*(?:°?C)?\s*\|\s*"
    r"POWER\s*=\s*(?P<power>[+-]?\d+(?:[.,]\d+)?)\s*(?:kW)?\s*"
    r"(?:\|\s*SERVERS\s*=\s*(?P<servers>-?\d+)\s*)?"
    r"(?:\|\s*MAX_TEMP\s*=\s*(?P<max_temp>[+-]?\d+(?:[.,]\d+)?)\s*(?:°?C)?\s*)?"
    r"$",
    re.IGNORECASE,
)

# Шаблон нормалізованого ідентифікатора стійки (наприклад: RACK-A01, SRV-04B)
UNIT_ID_RE = re.compile(r"^[A-Z]{2,8}-[A-Z0-9]{2,8}$")


def _normalize_float(raw_num: str) -> float:
    """Нормалізує десятковий роздільник (кома -> крапка) та перетворює у float."""
    cleaned = raw_num.strip().replace(",", ".")
    return float(cleaned)


def parse_telemetry_line(raw_line: str, line_number: int | None = None) -> ServerRack:
    """
    Виконує валідацію та нормалізацію одного рядка телеметрії,
    повертаючи ініціалізований об'єкт ServerRack.
    """
    normalized_line = raw_line.strip()
    match = TELEMETRY_LINE_RE.match(normalized_line)
    if not match:
        prefix = f"Рядок {line_number}: " if line_number is not None else ""
        raise TelemetryValidationError(
            f"{prefix}некоректна структура кадру телеметрії",
            raw_value=normalized_line,
        )

    unit_id = match.group("unit_id").strip().upper()
    if not UNIT_ID_RE.match(unit_id):
        raise TelemetryValidationError(
            "Ідентифікатор стійки не відповідає шаблону [A-Z]{2,8}-[A-Z0-9]{2,8}",
            raw_value=unit_id,
        )

    zone_id = int(match.group("zone_id"))
    temperature = _normalize_float(match.group("temp"))
    power_kw = _normalize_float(match.group("power"))

    servers_raw = match.group("servers")
    server_count = int(servers_raw) if servers_raw is not None else 24

    max_temp_raw = match.group("max_temp")
    max_temp = _normalize_float(max_temp_raw) if max_temp_raw is not None else 38.0

    return ServerRack(
        unit_id=unit_id,
        temperature=temperature,
        power_kw=power_kw,
        max_temp=max_temp,
        server_count=server_count,
        zone_id=zone_id,
    )


def parse_telemetry_lines(lines: Iterable[str]) -> list[ServerRack]:
    """
    Пакетно обробляє потік рядків телеметрії (часова складність O(N)),
    пропускаючи порожні рядки та коментарі (#).
    """
    racks: list[ServerRack] = []
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rack = parse_telemetry_line(stripped, line_number=idx)
        racks.append(rack)
    return racks