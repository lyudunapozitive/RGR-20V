"""
Головна точка входу CLI-емулятора контролера охолодження дата-центру.
Освітній компонент: Програмування на Python. Базовий рівень.
Спеціальність: F7 «Комп'ютерна інженерія». Варіант 20.
"""

import time

import cooling_controller
from cooling_controller import (
    CoolingMode,
    CoolingSystemError,
    CRACUnit,
    HardwareTelemetryRegister,
    ServerRack,
)


def demonstrate_object_model() -> None:
    """Демонструє роботу ієрархії класів, @property, dunder-методів та регістра стану."""
    separator = "=" * 80
    sub_separator = "-" * 80

    print(separator)
    print(f"{'ДЕМОНСТРАЦІЯ ОБ`ЄКТНОЇ МОДЕЛІ (v' + cooling_controller.__version__ + ')':^80}")
    print(separator)

    rack_a = ServerRack("RACK-A01", temperature=31.4, power_kw=12.5, max_temp=38.0, server_count=28, zone_id=1)
    rack_b = ServerRack("RACK-B02", temperature=26.8, power_kw=8.0, max_temp=38.0, server_count=18, zone_id=1)
    rack_a_copy = ServerRack("RACK-A01", temperature=31.4000000001, power_kw=12.5, max_temp=38.0, server_count=28, zone_id=1)

    print("1. Рядкове відображення (__str__ та __repr__):")
    print(f"   __str__ : {rack_a}")
    print(f"   __repr__: {repr(rack_b)}")
    print(sub_separator)

    print("2. Компонентне порівняння (__eq__ через IEEE 754 isclose та __lt__):")
    print(f"   rack_a == rack_a_copy : {rack_a == rack_a_copy}")
    print(f"   rack_b < rack_a       : {rack_b < rack_a}")
    sorted_racks = sorted([rack_a, rack_b])
    print(f"   Сортування за нагрівом: {[r.unit_id for r in sorted_racks]}")
    print(sub_separator)

    print("3. Арифметична взаємодія об'єктів (__add__ — об'єднання кластера):")
    cluster = rack_a + rack_b
    print(f"   {rack_a.unit_id} + {rack_b.unit_id} => {cluster}")
    print(f"   Сумарно серверів: {cluster.server_count} шт.")
    print(sub_separator)

    print("4. Прецизійний кондиціонер CRAC та 16-бітний регістр стану:")
    crac = CRACUnit("CRAC-Z1", supply_temp=18.0, current_airflow=6800.0, zone_id=1)
    crac.op_mode = CoolingMode.BOOST
    reg_word = crac.build_status_register(fault=False)
    unpacked = HardwareTelemetryRegister.unpack(reg_word)
    print(f"   {crac}")
    print(f"   Апаратне слово регістра: {HardwareTelemetryRegister.format_word(reg_word)}")
    print(f"   Розпаковані поля       : {unpacked}")

    try:
        crac.current_airflow = 25000.0
    except CoolingSystemError as err:
        print(f"   Перехоплення аварії ШІМ: {err}")

    print(separator)


def main() -> None:
    """Головна функція запуску програми."""
    t_start = time.perf_counter()
    demonstrate_object_model()
    t_elapsed = (time.perf_counter() - t_start) * 1000
    print(f"Час виконання демонстрації моделі: {t_elapsed:.4f} мс\n")


if __name__ == "__main__":
    main()