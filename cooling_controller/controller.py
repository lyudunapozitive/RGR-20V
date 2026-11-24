"""
Алгоритмічне ядро контролера адаптивного регулювання повітряного потоку.
Освітній компонент: Програмування на Python. Базовий рівень.
Спеціальність: F7 «Комп'ютерна інженерія». Варіант 20.
"""

from dataclasses import dataclass

from cooling_controller.exceptions import AirflowLimitError, ConfigurationError
from cooling_controller.hardware_register import CoolingMode, HardwareTelemetryRegister
from cooling_controller.models import CRACUnit, ServerRack


@dataclass(frozen=True)
class ControlDecision:
    """Результат одного циклу адаптивного регулювання для кліматичної зони."""

    zone_id: int
    crac_id: str
    rack_count: int
    total_power_kw: float
    peak_rack_id: str
    peak_temp_c: float
    base_airflow_m3h: float
    adaptive_factor: float
    target_airflow_m3h: float
    fan_pwm_percent: float
    mode_name: str
    register_word: int
    register_hex: str
    fault_active: bool


class PrecisionCoolingController:
    """
    Емулятор контролера прецизійного охолодження дата-центру
    з адаптивним пропорційно-інтегральним регулюванням повітряного потоку.
    """

    AIR_DENSITY_KG_M3 = 1.2
    AIR_SPECIFIC_HEAT_KJ_KG_C = 1.005
    MIN_DELTA_T = 4.0

    def __init__(
        self,
        target_return_temp: float = 27.0,
        rack_setpoint_temp: float = 28.0,
        kp_gain: float = 0.06,
        ki_gain: float = 0.015,
    ) -> None:
        self.target_return_temp = target_return_temp
        self.rack_setpoint_temp = rack_setpoint_temp
        self.kp_gain = kp_gain
        self.ki_gain = ki_gain
        self.__integral_errors: dict[int, float] = {}

    @property
    def target_return_temp(self) -> float:
        """Цільова температура зворотного повітря на вході CRAC (°C)."""
        return self.__target_return_temp

    @target_return_temp.setter
    def target_return_temp(self, value: float) -> None:
        val = float(value)
        if not (18.0 <= val <= 40.0):
            raise ConfigurationError("Цільова температура повернення має бути в межах [18; 40] °C.")
        self.__target_return_temp = val

    @property
    def rack_setpoint_temp(self) -> float:
        """Номінальна уставка температури серверних стійок (°C)."""
        return self.__rack_setpoint_temp

    @rack_setpoint_temp.setter
    def rack_setpoint_temp(self, value: float) -> None:
        val = float(value)
        if not (18.0 <= val <= 38.0):
            raise ConfigurationError("Уставка температури стійок має бути в межах [18; 38] °C.")
        self.__rack_setpoint_temp = val

    @property
    def kp_gain(self) -> float:
        """Пропорційний коефіцієнт адаптації потоку."""
        return self.__kp_gain

    @kp_gain.setter
    def kp_gain(self, value: float) -> None:
        val = float(value)
        if val < 0.0:
            raise ConfigurationError("Коефіцієнт Kp не може бути від'ємним.")
        self.__kp_gain = val

    @property
    def ki_gain(self) -> float:
        """Інтегральний коефіцієнт корекції накопиченої похибки."""
        return self.__ki_gain

    @ki_gain.setter
    def ki_gain(self, value: float) -> None:
        val = float(value)
        if val < 0.0:
            raise ConfigurationError("Коефіцієнт Ki не може бути від'ємним.")
        self.__ki_gain = val

    def calculate_base_airflow(self, total_power_kw: float, supply_temp_c: float) -> float:
        """
        Розраховує базовий об'ємний потік повітря (м3/год) за рівнянням теплового балансу.
        """
        delta_t = max(self.__target_return_temp - supply_temp_c, self.MIN_DELTA_T)
        heat_capacity_vol = self.AIR_DENSITY_KG_M3 * self.AIR_SPECIFIC_HEAT_KJ_KG_C
        return (3600.0 * total_power_kw) / (heat_capacity_vol * delta_t)

    @staticmethod
    def _select_mode(pwm_percent: float, fault: bool) -> CoolingMode:
        """Визначає дискретний режим роботи CRAC за завантаженням вентиляторів."""
        if fault or pwm_percent >= 95.0:
            return CoolingMode.EMERGENCY
        if pwm_percent <= 30.0:
            return CoolingMode.ECO
        if pwm_percent <= 65.0:
            return CoolingMode.BALANCED
        return CoolingMode.BOOST

    def regulate_zone(
        self,
        zone_id: int,
        racks: list[ServerRack],
        crac: CRACUnit,
        strict_limits: bool = True,
    ) -> ControlDecision:
        """
        Виконує один цикл адаптивного регулювання для заданої кліматичної зони.
        Складність алгоритму за часом: O(N), де N — кількість стійок у зоні.
        """
        if not racks:
            raise ConfigurationError(f"У зоні {zone_id} відсутні серверні стійки для моніторингу.")

        total_power = 0.0
        for rack in racks:
            if strict_limits:
                rack.check_thermal_safety()
            total_power += rack.power_kw

        # Використовуємо перевантажений __lt__ для визначення найгарячішої стійки
        peak_rack = max(racks)
        thermal_error = peak_rack.temperature - self.__rack_setpoint_temp

        prev_integral = self.__integral_errors.get(zone_id, 0.0)
        new_integral = max(-10.0, min(20.0, prev_integral + thermal_error))
        self.__integral_errors[zone_id] = new_integral

        if thermal_error >= 0.0:
            adaptive_factor = 1.0 + self.__kp_gain * thermal_error + self.__ki_gain * max(0.0, new_integral)
        else:
            adaptive_factor = max(0.75, 1.0 + (self.__kp_gain * 0.5) * thermal_error)

        base_airflow = self.calculate_base_airflow(total_power, crac.temperature)
        requested_airflow = base_airflow * adaptive_factor

        fault_active = any(rack.is_overheated for rack in racks)
        if strict_limits and requested_airflow > crac.max_airflow:
            raise AirflowLimitError(
                unit_id=crac.unit_id,
                requested_airflow=requested_airflow,
                max_airflow=crac.max_airflow,
            )

        clamped_airflow = max(crac.min_airflow, min(crac.max_airflow, requested_airflow))
        crac.current_airflow = clamped_airflow

        if requested_airflow > crac.max_airflow:
            fault_active = True

        crac.op_mode = self._select_mode(crac.fan_pwm_percent, fault_active)
        reg_word = crac.build_status_register(fault=fault_active)

        return ControlDecision(
            zone_id=zone_id,
            crac_id=crac.unit_id,
            rack_count=len(racks),
            total_power_kw=round(total_power, 3),
            peak_rack_id=peak_rack.unit_id,
            peak_temp_c=round(peak_rack.temperature, 2),
            base_airflow_m3h=round(base_airflow, 2),
            adaptive_factor=round(adaptive_factor, 4),
            target_airflow_m3h=round(crac.current_airflow, 2),
            fan_pwm_percent=crac.fan_pwm_percent,
            mode_name=crac.op_mode.name,
            register_word=reg_word,
            register_hex=HardwareTelemetryRegister.format_word(reg_word),
            fault_active=fault_active,
        )