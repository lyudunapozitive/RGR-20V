#### 1. Файл `cooling_controller/exceptions.py`
"""
Модуль користувацьких виняткових ситуацій системи прецизійного охолодження.
Освітній компонент: Програмування на Python. Базовий рівень.
Спеціальність: F7 «Комп'ютерна інженерія». Варіант 20.
"""


class CoolingSystemError(Exception):
    """Базовий клас винятків для всіх підсистем контролера охолодження."""

    def __init__(self, message: str, error_code: str = "ERR_SYS") -> None:
        self.error_code = error_code
        super().__init__(f"[{error_code}] {message}")


class ConfigurationError(CoolingSystemError):
    """Виняток, що виникає при помилках конфігурації або роботи з файлами стану."""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="ERR_CFG")


class TelemetryValidationError(CoolingSystemError):
    """Виняток, що виникає при невалідному форматі або діапазоні вхідної телеметрії."""

    def __init__(self, message: str, raw_value: str | None = None) -> None:
        self.raw_value = raw_value
        details = f"{message} (отримано: '{raw_value}')" if raw_value is not None else message
        super().__init__(details, error_code="ERR_VAL")


class HardwareLimitError(CoolingSystemError):
    """Проміжний базовий виняток для аварійних апаратних обмежень підсистеми."""

    def __init__(
        self,
        message: str,
        measured_value: float,
        limit_value: float,
        error_code: str = "ERR_HW",
    ) -> None:
        self.measured_value = measured_value
        self.limit_value = limit_value
        super().__init__(message, error_code=error_code)


class ThermalOverloadError(HardwareLimitError):
    """Критичне перевищення допустимої температури у серверній стійці або зоні."""

    def __init__(self, unit_id: str, current_temp: float, max_temp: float) -> None:
        self.unit_id = unit_id
        msg = (
            f"Тепловий пробій вузла '{unit_id}': "
            f"зафіксовано {current_temp:.2f} °C при граничній межі {max_temp:.2f} °C."
        )
        super().__init__(
            message=msg,
            measured_value=current_temp,
            limit_value=max_temp,
            error_code="ERR_THERMAL",
        )


class AirflowLimitError(HardwareLimitError):
    """Порушення допустимих меж витрати повітря або обертів вентиляторів CRAC."""

    def __init__(self, unit_id: str, requested_airflow: float, max_airflow: float) -> None:
        self.unit_id = unit_id
        msg = (
            f"Недопустимий повітряний потік для '{unit_id}': "
            f"запитано {requested_airflow:.2f} м3/год (макс. межа: {max_airflow:.2f} м3/год)."
        )
        super().__init__(
            message=msg,
            measured_value=requested_airflow,
            limit_value=max_airflow,
            error_code="ERR_AIRFLOW",
        )