# Внешние зависимости
from typing import Callable, List, Any, Optional, Tuple
# Внутренние модули
from web_app.src.utils.machinery_rules import normalize_short_title, is_autotanker


# Есть ли в строке две подряд идущие заглавные буквы
def has_adjacent_uppercase(text: str) -> bool:
    if not text:
        return False
    for a, b in zip(text, text[1:]):
        if a.isupper() and b.isupper():
            return True
    return False


# Спецтехника (две заглавные подряд) — вверх, остальное — вниз. Стабильно.
def sort_special_first(items: List[Any], title_getter: Callable[[Any], str]) -> List[Any]:
    return sorted(
        items,
        key=lambda item: 0 if has_adjacent_uppercase(title_getter(item)) else 1
    )


# Специальная ли техника. Для старых записей (kind не заполнен) — прежнее правило по названию.
def is_special(kind: Optional[str], title: str) -> bool:
    if kind is None:
        return has_adjacent_uppercase(title)
    return str(kind).upper() == "SPECIAL"


# Ключ сортировки техники в выгрузке (п. 2.7):
# автоцистерны (по ходу 1, 2, 3...), затем автолестницы, затем прочая специальная техника.
# Основание — краткое обозначение и ход выезда.
def machinery_sort_key(
    title: str,
    short_title: Optional[str],
    departure_order: Optional[int]
) -> Tuple[int, int, str, str]:
    short = normalize_short_title(short_title)

    if is_autotanker(short):
        group = 0
    elif short == "АЛ":
        group = 1
    else:
        group = 2

    # АЦ без хода — после АЦ с ходом
    order = departure_order if departure_order else 10 ** 6

    return group, order, short, title or ""


# Сортировка списка техники (объекты со свойствами kind, title, short_title, departure_order, relocation):
# специальная — вверх; внутри — АЦ по ходу, АЛ, прочая специальная; ушедшие в передислокацию — в конец.
def sort_machinery(items: List[Any]) -> List[Any]:
    return sorted(
        items,
        key=lambda m: (
            0 if is_special(m.kind, m.title) else 1,
            1 if (m.relocation and m.relocation.direction == "out") else 0,
            machinery_sort_key(m.title, m.short_title, m.departure_order)
        )
    )
