"""
Головна точка входу CLI-емулятора контролера охолодження дата-центру.
Освітній компонент: Програмування на Python. Базовий рівень.
Спеціальність: F7 «Комп'ютерна інженерія». Варіант 20.
"""

import sys
import time

import cooling_controller
from cooling_controller import (
    CoolingSystemError,
    TelemetryValidationError,
    ThermalOverloadError,
)


def print_startup_banner() -> None:
    """
    Виводить службову інформацію про середовище та завантажений пакет.
    """
    separator = "=" * 80
    sub_separator = "-" * 80

    print(separator)
    print(f"{'ЕМУЛЯТОР КОНТРОЛЕРА ПРЕЦИЗІЙНОГО ОХОЛОДЖЕННЯ ДАТА-ЦЕНТРУ':^80}")
    print(separator)
    print(f"Версія пакета:          {cooling_controller.__version__}")
    print(f"Інтерпретатор Python:   {sys.version.split()[0]}")
    print(f"Публічний API (__all__): {', '.join(cooling_controller.__all__)}")
    print(sub_separator)


def verify_exceptions_smoke() -> None:
    """
    Перевіряє коректність генерації та перехоплення ієрархії винятків.
    """
    print(f"{'ПЕРЕВІРКА ІЄРАРХІЇ ВИНЯТКІВ (SMOKE TEST)':^80}")
    print("-" * 80)

    test_cases = [
        ThermalOverloadError(unit_id="RACK-A01", current_temp=47.5, max_temp=40.0),
        TelemetryValidationError("Некоректний формат кадру датчика", raw_value="TEMP=??"),
    ]

    for exc in test_cases:
        try:
            raise exc
        except CoolingSystemError as err:
            print(f"Перехоплено [{type(err).__name__}]: {err}")

    print("=" * 80)


def main() -> None:
    """
    Головна функція запуску програми.
    """
    t_start = time.perf_counter()
    print_startup_banner()
    verify_exceptions_smoke()
    t_elapsed = (time.perf_counter() - t_start) * 1000
    print(f"Час ініціалізації та перевірки: {t_elapsed:.4f} мс\n")


if __name__ == "__main__":
    main()