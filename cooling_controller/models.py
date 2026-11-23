"""
Об'єктна модель компонентів системи прецизійного охолодження дата-центру.
Освітній компонент: Програмування на Python. Базовий рівень.
Спеціальність: F7 «Комп'ютерна інженерія». Варіант 20.
"""

import math

from cooling_controller.exceptions import (
    AirflowLimitError,
    TelemetryValidationError,
    ThermalOverloadError,
)
from cooling_controller.hardware_register import CoolingMode, HardwareTelemetryRegister


class ThermalNode:
    """
    Базовий клас апаратного вузла дата-центру з тепловими параметрами.
    """

    MIN_PHYSICAL_TEMP = -50.0
    MAX_PHYSICAL_TEMP = 150.0

    def __init__(
        self,
        unit_id: str,
        temperature: float,
        power_kw: float,
        max_temp: float = 40.0,
    ) -> None:
        self.unit_id = unit_id
        self.max_temp = max_temp
        self.temperature = temperature
        self.power_kw = power_kw

    @property
    def unit_id(self) -> str:
        """
        Унікальний ідентифікатор апаратного вузла.
        """
        return self.__unit_id

    @unit_id.setter
    def unit_id(self, value: str) -> None:
        cleaned = value.strip()
        if not cleaned:
            raise TelemetryValidationError("Ідентифікатор вузла не може бути порожнім", value)
        self.__unit_id = cleaned

    @property
    def temperature(self) -> float:
        """
        Поточна температура вузла (°C).
        """
        return self.__temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        temp_val = float(value)
        if not (self.MIN_PHYSICAL_TEMP <= temp_val <= self.MAX_PHYSICAL_TEMP):
            raise TelemetryValidationError(
                f"Температура поза фізичним діапазоном датчика "
                f"[{self.MIN_PHYSICAL_TEMP}; {self.MAX_PHYSICAL_TEMP}] °C",
                raw_value=str(value),
            )
        self.__temperature = temp_val

    @property
    def power_kw(self) -> float:
        """
        Теплове навантаження або споживана потужність (кВт).
        """
        return self.__power_kw

    @power_kw.setter
    def power_kw(self, value: float) -> None:
        pwr = float(value)
        if pwr < 0.0:
            raise TelemetryValidationError(
                "Потужність (кВт) не може бути від'ємною",
                raw_value=str(value),
            )
        self.__power_kw = pwr

    @property
    def max_temp(self) -> float:
        """
        Гранично допустима робоча температура вузла (°C).
        """
        return self.__max_temp

    @max_temp.setter
    def max_temp(self, value: float) -> None:
        limit = float(value)
        if not (0.0 < limit <= 100.0):
            raise TelemetryValidationError(
                "Гранична робоча температура має бути в межах (0; 100] °C",
                raw_value=str(value),
            )
        self.__max_temp = limit

    @property
    def is_overheated(self) -> bool:
        """
        Повертає True, якщо поточна температура перевищує допустиму межу.
        """
        return self.__temperature > self.__max_temp

    def check_thermal_safety(self) -> None:
        """
        Перевіряє теплову безпеку вузла та генерує виняток при перегріві.
        """
        if self.is_overheated:
            raise ThermalOverloadError(
                unit_id=self.__unit_id,
                current_temp=self.__temperature,
                max_temp=self.__max_temp,
            )

    def __str__(self) -> str:
        status = "ПЕРЕГРІВ" if self.is_overheated else "НОРМА"
        return (
            f"[{self.__unit_id}] T={self.__temperature:.2f}°C "
            f"(макс {self.__max_temp:.1f}°C), P={self.__power_kw:.2f} кВт [{status}]"
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(unit_id={self.__unit_id!r}, "
            f"temperature={self.__temperature:.2f}, "
            f"power_kw={self.__power_kw:.2f}, max_temp={self.__max_temp:.2f})"
        )

    def __eq__(self, other: object) -> bool:
        """
        Порівняння об'єктів з урахуванням точності IEEE 754 (math.isclose).
        """
        if not isinstance(other, ThermalNode):
            return NotImplemented
        return (
            type(self) is type(other)
            and self.__unit_id == other.__unit_id
            and math.isclose(self.__temperature, other.__temperature, rel_tol=1e-9, abs_tol=1e-12)
            and math.isclose(self.__power_kw, other.__power_kw, rel_tol=1e-9, abs_tol=1e-12)
        )

    def __lt__(self, other: object) -> bool:
        """
        Порівняння вузлів за пріоритетом теплового навантаження (температура, далі потужність).
        """
        if not isinstance(other, ThermalNode):
            return NotImplemented
        if not math.isclose(self.__temperature, other.__temperature, rel_tol=1e-9, abs_tol=1e-12):
            return self.__temperature < other.__temperature
        return self.__power_kw < other.__power_kw


class ServerRack(ThermalNode):
    """
    Похідний клас: серверна стійка дата-центру з обчислювальним навантаженням.
    """

    def __init__(
        self,
        unit_id: str,
        temperature: float,
        power_kw: float,
        max_temp: float = 38.0,
        server_count: int = 24,
        zone_id: int = 0,
    ) -> None:
        super().__init__(
            unit_id=unit_id,
            temperature=temperature,
            power_kw=power_kw,
            max_temp=max_temp,
        )
        self.server_count = server_count
        self.zone_id = zone_id

    @property
    def server_count(self) -> int:
        """
        Кількість серверних юнітів у стійці.
        """
        return self.__server_count

    @server_count.setter
    def server_count(self, value: int) -> None:
        if int(value) < 0:
            raise TelemetryValidationError(
                "Кількість серверів у стійці не може бути від'ємною",
                raw_value=str(value),
            )
        self.__server_count = int(value)

    @property
    def zone_id(self) -> int:
        """
        Ідентифікатор кліматичної зони (0..15).
        """
        return self.__zone_id

    @zone_id.setter
    def zone_id(self, value: int) -> None:
        if not (0 <= int(value) <= 15):
            raise TelemetryValidationError(
                "Ідентифікатор зони має бути в діапазоні 0..15",
                raw_value=str(value),
            )
        self.__zone_id = int(value)

    def __add__(self, other: object) -> "ServerRack":
        """
        Арифметичне об'єднання двох стійок в еквівалентний тепловий кластер.
        """
        if not isinstance(other, ServerRack):
            return NotImplemented

        total_power = self.power_kw + other.power_kw
        if total_power > 0.0:
            weighted_temp = (
                self.temperature * self.power_kw + other.temperature * other.power_kw
            ) / total_power
        else:
            weighted_temp = (self.temperature + other.temperature) / 2.0

        return ServerRack(
            unit_id=f"{self.unit_id}+{other.unit_id}",
            temperature=weighted_temp,
            power_kw=total_power,
            max_temp=min(self.max_temp, other.max_temp),
            server_count=self.server_count + other.server_count,
            zone_id=self.zone_id,
        )

    def to_dict(self) -> dict[str, str | float | int | bool]:
        """
        Серіалізує параметри серверної стійки у словник.
        """
        return {
            "unit_id": self.unit_id,
            "zone_id": self.zone_id,
            "temperature_c": round(self.temperature, 3),
            "max_temp_c": round(self.max_temp, 3),
            "power_kw": round(self.power_kw, 3),
            "server_count": self.server_count,
            "overheated": self.is_overheated,
        }


class CRACUnit(ThermalNode):
    """
    Похідний клас: прецизійний кондиціонер (CRAC) з адаптивним потоком повітря.
    """

    def __init__(
        self,
        unit_id: str,
        supply_temp: float = 18.5,
        power_kw: float = 4.2,
        max_temp: float = 35.0,
        min_airflow: float = 1500.0,
        max_airflow: float = 12000.0,
        current_airflow: float = 4000.0,
        zone_id: int = 0,
    ) -> None:
        super().__init__(
            unit_id=unit_id,
            temperature=supply_temp,
            power_kw=power_kw,
            max_temp=max_temp,
        )
        if min_airflow < 0.0 or max_airflow <= min_airflow:
            raise TelemetryValidationError(
                "Некоректні межі продуктивності CRAC (min_airflow < max_airflow)",
                raw_value=f"{min_airflow}..{max_airflow}",
            )
        self.__min_airflow = float(min_airflow)
        self.__max_airflow = float(max_airflow)
        self.__zone_id = int(zone_id)
        self.__op_mode = CoolingMode.BALANCED
        self.current_airflow = current_airflow

    @property
    def min_airflow(self) -> float:
        """
        Мінімально допустима витрата повітря (м3/год).
        """
        return self.__min_airflow

    @property
    def max_airflow(self) -> float:
        """
        Максимальна пропускна здатність вентиляторів (м3/год).
        """
        return self.__max_airflow

    @property
    def current_airflow(self) -> float:
        """
        Поточний об'ємний потік повітря (м3/год).
        """
        return self.__current_airflow

    @current_airflow.setter
    def current_airflow(self, value: float) -> None:
        flow = float(value)
        if flow < self.__min_airflow or flow > self.__max_airflow:
            raise AirflowLimitError(
                unit_id=self.unit_id,
                requested_airflow=flow,
                max_airflow=self.__max_airflow,
            )
        self.__current_airflow = flow

    @property
    def op_mode(self) -> CoolingMode:
        """
        Поточний дискретний режим роботи кондиціонера.
        """
        return self.__op_mode

    @op_mode.setter
    def op_mode(self, mode: CoolingMode) -> None:
        self.__op_mode = CoolingMode(mode)

    @property
    def fan_pwm_percent(self) -> float:
        """
        Відсоток завантаження вентиляторів (ШІМ, %).
        """
        span = self.__max_airflow - self.__min_airflow
        ratio = (self.__current_airflow - self.__min_airflow) / span
        # Мінімальний робочий ШІМ 20% при min_airflow, до 100% при max_airflow
        return round(20.0 + ratio * 80.0, 2)

    def build_status_register(self, fault: bool = False) -> int:
        """Формує 16-бітне апаратне слово стану для поточного стану CRAC."""
        pwm_code = min(255, max(0, round((self.fan_pwm_percent / 100.0) * 255)))
        return HardwareTelemetryRegister.pack(
            fault=fault or self.is_overheated,
            op_mode=self.__op_mode,
            pwm_code=pwm_code,
            zone_id=self.__zone_id,
        )

    def __str__(self) -> str:
        return (
            f"[{self.unit_id}] Режим={self.__op_mode.name}, "
            f"Потік={self.__current_airflow:.1f}/{self.__max_airflow:.0f} м3/год "
            f"(ШІМ={self.fan_pwm_percent:.1f}%), T_подачі={self.temperature:.1f}°C"
        )