# Внешние зависимости
from typing import Any
import sqlalchemy as sa
from sqladmin import ModelView
from starlette.requests import Request
# Внутренние модули
from web_app.src.models import Machinery, STATUS_MAINTENANCE_MAP, MACHINERY_KIND_MAP
from web_app.src.utils.machinery_rules import validate_departure_order, normalize_short_title


# Админка для Machinery
class MachineryAdmin(ModelView, model=Machinery):
    column_list = [
        Machinery.id,
        Machinery.title,
        Machinery.model,
        Machinery.number,
        Machinery.status,
        Machinery.kind,
        Machinery.short_title,
        Machinery.departure_order,
        Machinery.section
    ]

    column_labels = {
        Machinery.id: "Идентификатор",
        Machinery.title: "Название",
        Machinery.model: "Модель",
        Machinery.number: "Номер",
        Machinery.status: "Статус",
        Machinery.kind: "Категория)",
        Machinery.short_title: "Краткое обозначение",
        Machinery.departure_order: "Ход выезда",
        Machinery.relocations: "Передислокации",
        Machinery.supervisor: "Старший на машине",
        Machinery.current_personnel: "Количество личного состава",
        Machinery.gdzs: "ГДЗС",
        Machinery.section: "Пожарное отделение",
        Machinery.maintenance: "Обслуживание",
        Machinery.created_at: "Создан",
        Machinery.updated_at: "Последние обновление"
    }

    column_formatters = {
        "status": lambda m, a: STATUS_MAINTENANCE_MAP[m.status.value],
        "kind": lambda m, a: MACHINERY_KIND_MAP[m.kind.value]
    }

    column_formatters_detail = {
        "status": lambda m, a: STATUS_MAINTENANCE_MAP[m.status.value],
        "kind": lambda m, a: MACHINERY_KIND_MAP[m.kind.value]
    }

    # Валидация категории и хода выезда: у АЦ ход обязателен по смыслу, но уникален в пределах ПСЧ,
    # у остальной техники хода нет
    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        short_title = data.get("short_title", model.short_title if not is_created else None)
        departure_order = data.get("departure_order", model.departure_order if not is_created else None)

        if isinstance(short_title, str):
            short_title = normalize_short_title(short_title) or None
            data["short_title"] = short_title

        section = data.get("section")
        section_id = getattr(section, "id", section) if section is not None else getattr(model, "section_id", None)

        taken_orders = set()
        if departure_order is not None and section_id is not None:
            stmt = sa.select(Machinery.departure_order).where(
                Machinery.section_id == section_id,
                Machinery.departure_order.isnot(None)
            )
            if not is_created:
                stmt = stmt.where(Machinery.id != model.id)

            if self.is_async:
                async with self.session_maker(expire_on_commit=False) as session:
                    taken_orders = set((await session.execute(stmt)).scalars())
            else:
                with self.session_maker(expire_on_commit=False) as session:
                    taken_orders = set(session.execute(stmt).scalars())

        error = validate_departure_order(short_title, departure_order, taken_orders)
        if error:
            raise ValueError(error)

    column_searchable_list = [Machinery.id, Machinery.number]  # список столбцов, которые можно искать
    column_sortable_list = [
        Machinery.id,
        Machinery.status
    ]  # список столбцов, которые можно сортировать

    column_default_sort = [(Machinery.id, True)]

    form_create_rules = [
        "title",
        "model",
        "number",
        "status",
        "kind",
        "short_title",
        "departure_order",
        "supervisor",
        "current_personnel",
        "gdzs",
        "section"
    ]

    column_details_list = [
        Machinery.id,
        Machinery.title,
        Machinery.model,
        Machinery.number,
        Machinery.status,
        Machinery.kind,
        Machinery.short_title,
        Machinery.departure_order,
        Machinery.supervisor,
        Machinery.current_personnel,
        Machinery.gdzs,
        Machinery.section,
        Machinery.maintenance,
        Machinery.relocations,
        Machinery.created_at,
        Machinery.updated_at
    ]

    form_edit_rules = [
        "title",
        "model",
        "number",
        "status",
        "kind",
        "short_title",
        "departure_order",
        "supervisor",
        "current_personnel",
        "gdzs",
        "section"
    ]

    can_create = True  # право создавать
    can_edit = True  # право редактировать
    can_delete = True  # право удалять
    can_view_details = True  # право смотреть всю информацию
    can_export = True  # право экспортировать

    name = "Машина"  # название
    name_plural = "Машины"  # множественное название
    icon = "fa-solid fa-bus"  # иконка
    category = "Техника"  # категория
    category_icon = "fa-solid fa-list"  # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]