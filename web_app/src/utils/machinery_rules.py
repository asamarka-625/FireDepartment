# Внешние зависимости
from typing import Optional, Set
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


MOSCOW_TZ = ZoneInfo("Europe/Moscow")

# Краткое обозначение автоцистерны (кириллица)
AUTOTANKER = "АЦ"

# Смена караула / начало дежурных суток по Москве. Дежурные сутки идут с 09:00 текущего дня
# до 08:59 следующего (а не по астрономической полуночи): всё, что происходит до 09:00,
# относится к дежурным суткам, начавшимся накануне.
DUTY_DAY_START = time(9, 0)


# Текущие дежурные сутки (дата их начала) по Москве.
# До 09:00 — это ещё предыдущая календарная дата (дежурство, начатое накануне в 09:00).
def today_msk() -> date:
    now = datetime.now(MOSCOW_TZ)
    duty_date = now.date()
    if now.time() < DUTY_DAY_START:
        duty_date -= timedelta(days=1)
    return duty_date


# Краткое обозначение → нормализованный вид (верхний регистр, без пробелов)
def normalize_short_title(short_title: Optional[str]) -> str:
    return (short_title or "").strip().upper()


# Автоцистерна ли (только у АЦ бывает ход выезда)
def is_autotanker(short_title: Optional[str]) -> bool:
    return normalize_short_title(short_title) == AUTOTANKER


# Подпись техники в строевой записке.
# ЕДИНСТВЕННОЕ место склейки: у АЦ краткое обозначение + ход через дефис («АЦ-1»),
# у остальной техники — краткое обозначение как есть. Если обозначение не задано — полное название.
# Значение нигде не хранится: собирается в момент формирования отчёта.
def machinery_label(
    title: str,
    short_title: Optional[str],
    departure_order: Optional[int]
) -> str:
    short = (short_title or "").strip()
    if not short:
        return title

    if is_autotanker(short) and departure_order:
        return f"{short}-{departure_order}"

    return short


# Проверка хода выезда (п. 2.5). Возвращает текст ошибки или None.
# taken_orders — ходы других автоцистерн той же ПСЧ.
def validate_departure_order(
    short_title: Optional[str],
    departure_order: Optional[int],
    taken_orders: Set[int]
) -> Optional[str]:
    if departure_order is None:
        return None

    if not is_autotanker(short_title):
        return "Ход выезда задаётся только у автоцистерн (краткое обозначение «АЦ»)"

    if departure_order < 1:
        return "Ход выезда должен быть положительным числом (1, 2, 3...)"

    if departure_order in taken_orders:
        return f"В этой ПСЧ уже есть автоцистерна с ходом выезда {departure_order}"

    return None
