"""
Модуль емуляції 16-бітного апаратного регістра стану контролера охолодження.
Освітній компонент: Програмування на Python. Базовий рівень.
Спеціальність: F7 «Комп'ютерна інженерія». Варіант 20.
"""

from enum import IntEnum

from cooling_controller.exceptions import TelemetryValidationError


class CoolingMode(IntEnum):
    """
    Дискретні режими роботи контролера прецизійного охолодження (3 біти: 0..7).
    """

    IDLE = 0
    ECO = 1
    BALANCED = 2
    BOOST = 3
    EMERGENCY = 4


class HardwareTelemetryRegister:
    """
    Клас для бітового пакування, розпакування та модифікації 16-бітного регістра.
    """

    FAULT_SHIFT = 15
    FAULT_MASK = 0x1

    MODE_SHIFT = 12
    MODE_MASK = 0x7

    PWM_SHIFT = 4
    PWM_MASK = 0xFF

    ZONE_SHIFT = 0
    ZONE_MASK = 0xF

    @classmethod
    def pack(
        cls,
        fault: bool,
        op_mode: CoolingMode | int,
        pwm_code: int,
        zone_id: int,
    ) -> int:
        """
        Упаковує поля стану у 16-бітне беззнакове ціле слово.
        """
        mode_val = int(op_mode)
        if not (0 <= mode_val <= 7):
            raise TelemetryValidationError(
                "Код режиму OP_MODE має бути в межах 0..7",
                raw_value=str(mode_val),
            )
        if not (0 <= pwm_code <= 255):
            raise TelemetryValidationError(
                "Код ШІМ вентилятора має бути в межах 0..255",
                raw_value=str(pwm_code),
            )
        if not (0 <= zone_id <= 15):
            raise TelemetryValidationError(
                "Ідентифікатор зони ZONE_ID має бути в межах 0..15",
                raw_value=str(zone_id),
            )

        fault_bit = 1 if fault else 0
        register_word = (
            (fault_bit << cls.FAULT_SHIFT)
            | (mode_val << cls.MODE_SHIFT)
            | (pwm_code << cls.PWM_SHIFT)
            | (zone_id << cls.ZONE_SHIFT)
        )
        return register_word & 0xFFFF

    @classmethod
    def unpack(cls, register_word: int) -> dict[str, bool | int | str]:
        """
        Розпаковує 16-бітний регістр у словник апаратних параметрів.
        """
        if not (0 <= register_word <= 0xFFFF):
            raise TelemetryValidationError(
                "Значення 16-бітного регістра виходить за межі 0..65535",
                raw_value=str(register_word),
            )

        fault = bool((register_word >> cls.FAULT_SHIFT) & cls.FAULT_MASK)
        mode_code = (register_word >> cls.MODE_SHIFT) & cls.MODE_MASK
        pwm_code = (register_word >> cls.PWM_SHIFT) & cls.PWM_MASK
        zone_id = (register_word >> cls.ZONE_SHIFT) & cls.ZONE_MASK

        try:
            mode_name = CoolingMode(mode_code).name
        except ValueError:
            mode_name = f"UNKNOWN({mode_code})"

        return {
            "fault": fault,
            "mode_code": mode_code,
            "mode_name": mode_name,
            "pwm_code": pwm_code,
            "pwm_percent": round((pwm_code / 255.0) * 100.0, 1),
            "zone_id": zone_id,
        }

    @classmethod
    def set_fault(cls, register_word: int) -> int:
        """
        Встановлює біт аварії (біт 15) у 1.
        """
        return (register_word | (1 << cls.FAULT_SHIFT)) & 0xFFFF

    @classmethod
    def clear_fault(cls, register_word: int) -> int:
        """
        Скидає біт аварії (біт 15) у 0.
        """
        mask = ~(1 << cls.FAULT_SHIFT)
        return (register_word & mask) & 0xFFFF

    @classmethod
    def format_word(cls, register_word: int) -> str:
        """
        Повертає представлення регістра у HEX та BIN форматах.
        """
        return f"0x{register_word:04X} (0b{register_word:016b})"