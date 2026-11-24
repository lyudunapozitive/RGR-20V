"""
Головна точка входу CLI-емулятора контролера охолодження дата-центру.
Освітній компонент: Програмування на Python. Базовий рівень.
Спеціальність: F7 «Комп'ютерна інженерія». Варіант 20.
"""

import argparse
import sys
import time

import cooling_controller
from cooling_controller import (
    ControlDecision,
    CoolingSystemError,
    CRACUnit,
    PrecisionCoolingController,
    ServerRack,
    load_state_json,
    load_telemetry_file,
    parse_telemetry_lines,
    save_decisions_csv,
    save_state_json,
)


def build_arg_parser() -> argparse.ArgumentParser:
    """Конфігурує парсер аргументів командного рядка (sys.argv)."""
    parser = argparse.ArgumentParser(
        prog="cooling-cli",
        description="Емулятор контролера прецизійного охолодження дата-центру (Варіант 20)",
    )
    parser.add_argument(
        "-i",
        "--input",
        default="data/telemetry_normal.txt",
        help="Шлях до файлу вхідної телеметрії (за замовчуванням: data/telemetry_normal.txt)",
    )
    parser.add_argument(
        "--json-out",
        default="output/cooling_state.json",
        help="Шлях для збереження JSON-знімка стану",
    )
    parser.add_argument(
        "--csv-out",
        default="output/cooling_report.csv",
        help="Шлях для експорту CSV-звіту рішень",
    )
    parser.add_argument(
        "--setpoint",
        type=float,
        default=28.0,
        help="Уставка температури стійок (°C), за замовчуванням 28.0",
    )
    parser.add_argument(
        "--fault",
        choices=["overheat", "airflow", "format"],
        default=None,
        help="Штучна ініціалізація аварійної ситуації (для перевірки перехоплення винятків)",
    )
    parser.add_argument(
        "--inspect-json",
        default=None,
        help="Шлях до раніше збереженого JSON-файлу для перегляду знімка",
    )
    return parser


def print_decisions_table(decisions: list[ControlDecision]) -> None:
    """Виводить форматований табличний звіт роботи контролера у консоль."""
    separator = "=" * 88
    sub_separator = "-" * 88
    print(separator)
    print(f"{'ЗВІТ КОНТРОЛЕРА ПРЕЦИЗІЙНОГО ОХОЛОДЖЕННЯ (v' + cooling_controller.__version__ + ')':^88}")
    print(separator)
    print(
        f"| {'Зона':<4} | {'CRAC':<8} | {'Стійок':<6} | {'P (кВт)':<8} | "
        f"{'T_пік':<6} | {'Потік (м3/г)':<12} | {'ШІМ':<6} | {'Режим':<9} | {'Регістр':<6} |"
    )
    print(sub_separator)

    for d in decisions:
        print(
            f"| {d.zone_id:<4} "
            f"| {d.crac_id:<8} "
            f"| {d.rack_count:<6} "
            f"| {d.total_power_kw:<8.2f} "
            f"| {d.peak_temp_c:<6.2f} "
            f"| {d.target_airflow_m3h:<12.2f} "
            f"| {d.fan_pwm_percent:<5.1f}% "
            f"| {d.mode_name:<9} "
            f"| 0x{d.register_word:04X} |"
        )
    print(separator)


def simulate_fault(fault_kind: str, controller: PrecisionCoolingController) -> None:
    """Штучно ініціює позаштатну ситуацію обраного типу."""
    print(f"[ТЕСТ АВАРІЇ] Ініціалізація позаштатної ситуації: '{fault_kind}'...")
    crac = CRACUnit("CRAC-TEST", supply_temp=18.5, max_airflow=12000.0, zone_id=9)

    if fault_kind == "format":
        parse_telemetry_lines(["RACK=BROKEN_ID | ZONE=1 | TEMP=INVALID"])
    elif fault_kind == "overheat":
        racks = parse_telemetry_lines(
            ["RACK=RACK-ERR1 | ZONE=9 | TEMP=46.5C | POWER=15.0kW | MAX_TEMP=38.0C"]
        )
        controller.regulate_zone(9, racks, crac, strict_limits=True)
    elif fault_kind == "airflow":
        racks = parse_telemetry_lines(
            ["RACK=RACK-ERR2 | ZONE=9 | TEMP=37.0C | POWER=42.0kW | MAX_TEMP=38.0C"]
        )
        controller.regulate_zone(9, racks, crac, strict_limits=True)


def run_inspect_json(json_path: str) -> None:
    """Читає та відображає зведення зі збереженого JSON-файлу."""
    data = load_state_json(json_path)
    print("=" * 88)
    print(f"{'ІНСПЕКЦІЯ ЗБЕРЕЖЕНОГО JSON-СТАНУ':^88}")
    print("=" * 88)
    print(f"Файл:             {json_path}")
    print(f"Час генерації:    {data.get('generated_at_utc')}")
    print(f"Кількість зон:    {data.get('zone_count')}")
    print(f"Кількість стійок: {data.get('rack_count')}")
    print("-" * 88)
    for item in data["decisions"]:
        print(
            f" -> Зона {item['zone_id']} ({item['crac_id']}): "
            f"Режим={item['mode_name']}, Потік={item['target_airflow_m3h']} м3/год, "
            f"Регістр={item['register_hex']}"
        )
    print("=" * 88)


def main(argv: list[str] | None = None) -> int:
    """Головна функція CLI-програми; приймає аргументи sys.argv[1:]."""
    t_start = time.perf_counter()
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        if args.inspect_json:
            run_inspect_json(args.inspect_json)
            return 0

        controller = PrecisionCoolingController(rack_setpoint_temp=args.setpoint)

        if args.fault:
            simulate_fault(args.fault, controller)
            return 0

        racks = load_telemetry_file(args.input)
        zones: dict[int, list[ServerRack]] = {}
        for rack in racks:
            zones.setdefault(rack.zone_id, []).append(rack)

        decisions: list[ControlDecision] = []
        for zone_id, zone_racks in sorted(zones.items()):
            crac = CRACUnit(f"CRAC-Z{zone_id}", supply_temp=18.0, zone_id=zone_id)
            decision = controller.regulate_zone(zone_id, zone_racks, crac, strict_limits=True)
            decisions.append(decision)

        print_decisions_table(decisions)
        json_path = save_state_json(args.json_out, decisions, racks)
        csv_path = save_decisions_csv(args.csv_out, decisions)
        print(f"Збережено JSON-стан : {json_path}")
        print(f"Збережено CSV-звіт  : {csv_path}")

    except CoolingSystemError as err:
        print("=" * 88)
        print(f"[АВАРІЙНЕ ПЕРЕРИВАННЯ] Перехоплено виняток {type(err).__name__}:")
        print(f"   {err}")
        print("=" * 88)
        return 1

    finally:
        t_elapsed = (time.perf_counter() - t_start) * 1000
        print(f"Час виконання CLI-циклу: {t_elapsed:.4f} мс\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))