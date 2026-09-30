# Внешние зависимости
from sqladmin import ModelView
# Внутренние модули
from web_app.src.models import Relocation


# Админка для Relocation — только просмотр: история передислокаций сохраняется
class RelocationAdmin(ModelView, model=Relocation):
    column_list = [
        Relocation.id,
        Relocation.machinery,
        Relocation.from_section,
        Relocation.to_section,
        Relocation.date_from,
        Relocation.date_to
    ]

    column_labels = {
        Relocation.id: "Идентификатор",
        Relocation.machinery: "Машина",
        Relocation.from_section: "Отдающая ПСЧ",
        Relocation.to_section: "Принимающая ПСЧ",
        Relocation.date_from: "Дата начала",
        Relocation.date_to: "Дата возврата (пусто — до конца суток начала)",
        Relocation.created_by_id: "Оформил (ID пользователя)",
        Relocation.closed_by_id: "Закрыл досрочно (ID пользователя)",
        Relocation.created_at: "Создана",
        Relocation.updated_at: "Последнее обновление"
    }

    column_sortable_list = [Relocation.id, Relocation.date_from]
    column_default_sort = [(Relocation.id, True)]

    column_details_list = [
        Relocation.id,
        Relocation.machinery,
        Relocation.from_section,
        Relocation.to_section,
        Relocation.date_from,
        Relocation.date_to,
        Relocation.created_by_id,
        Relocation.closed_by_id,
        Relocation.created_at,
        Relocation.updated_at
    ]

    can_create = False
    can_edit = False
    can_delete = False  # историю не удаляем
    can_view_details = True
    can_export = True

    name = "Передислокация"
    name_plural = "Передислокации"
    icon = "fa-solid fa-truck-arrow-right"
    category = "Техника"
    category_icon = "fa-solid fa-list"

    page_size = 10
    page_size_options = [10, 25, 50, 100]
