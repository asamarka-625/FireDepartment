# Внешние зависимости
from typing import Optional, Tuple, Set
# Внутренние модули
from web_app.src.core import cfg
from web_app.src.crud import sql_get_department_by_id
from web_app.src.schemas import UserScheme


# Идентификаторы ПСЧ, с которыми пользователь вправе работать (просмотр, подача записки, управление техникой).
#   администратор (гарнизонный уровень) — все ПСЧ → None;
#   учётная запись уровня ПСО (section_id пуст) — все ПСЧ своего отряда;
#   учётная запись уровня ПСЧ (section_id указан) — только своя часть.
async def get_accessible_section_ids(user: UserScheme) -> Optional[Tuple[int, ...]]:
    if user.admin:
        return None

    department = await sql_get_department_by_id(department_id=user.department_id)
    department_section_ids = tuple(section.id for section in department.sections)

    if user.section_id is not None:
        return (user.section_id,) if user.section_id in department_section_ids else ()

    return department_section_ids


# ПСЧ, в которые пользователь вправе передислоцировать технику (None — в любые).
# По умолчанию — части того же ПСО; расширение до гарнизона включается RELOCATION_ALLOW_GARRISON.
async def get_relocation_target_ids(user: UserScheme) -> Optional[Set[int]]:
    if user.admin or cfg.RELOCATION_ALLOW_GARRISON:
        return None

    department = await sql_get_department_by_id(department_id=user.department_id)
    return {section.id for section in department.sections}
