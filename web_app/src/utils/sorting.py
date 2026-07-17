# Внешние зависимости
from typing import Callable, List, Any


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