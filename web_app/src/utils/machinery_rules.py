# Внешние зависимости
from typing import Optional, Set
from datetime import date, datetime
from zoneinfo import ZoneInfo


MOSCOW_TZ = ZoneInfo("Europe/Moscow")

# Краткое обозначение автоцистерны (кириллица)
AUTOTANKER = "АЦ"


# Текущая дата по Санкт-Петербургу (границы суток — 00:00 по Москве)
def today_msk() -> date:
    return datetime.now(MOSCOW_TZ).date()


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
