# Внешние зависимости
from sqladmin import ModelView
# Внутренние модули
from web_app.src.models import Maintenance


# Админка для Maintenance
class MaintenanceAdmin(ModelView, model=Maintenance):
    column_list = [
        Maintenance.id,
        Maintenance.machinery,
        Maintenance.date
    ]

    column_labels = {
        Maintenance.id: "Идентификатор",
        Maintenance.machinery: "Машина",
        Maintenance.note: "Причина/Примечание",
        Maintenance.date: "Дата постановки",
        Maintenance.created_at: "Создан",
        Maintenance.updated_at: "Последние обновление"
    }

    column_searchable_list = [Maintenance.id]  # список столбцов, которые можно искать
    column_sortable_list = [
        Maintenance.id,
        Maintenance.date
    ]  # список столбцов, которые можно сортировать

    column_default_sort = [(Maintenance.id, True)]

    form_create_rules = [
        "machinery",
        "note",
        "date"
    ]

    column_details_list = [
        Maintenance.id,
        Maintenance.machinery,
        Maintenance.note,
        Maintenance.date,
        Maintenance.created_at,
        Maintenance.updated_at
    ]

    form_edit_rules = [
        "machinery",
        "note",
        "date"
    ]

    can_create = True  # право создавать
    can_edit = True  # право редактировать
    can_delete = True  # право удалять
    can_view_details = True  # право смотреть всю информацию
    can_export = True  # право экспортировать

    name = "Обслуживание"  # название
    name_plural = "Обслуживания"  # множественное название
    icon = "fa-solid fa-toolbox"  # иконка
    category = "Техника"  # категория
    category_icon = "fa-solid fa-list"  # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]