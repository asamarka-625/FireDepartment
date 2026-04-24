# Внешние зависимости
from sqladmin import ModelView
# Внутренние модули
from web_app.src.models import Machinery, STATUS_MAINTENANCE_MAP


# Админка для Machinery
class MachineryAdmin(ModelView, model=Machinery):
    column_list = [
        Machinery.id,
        Machinery.title,
        Machinery.model,
        Machinery.number,
        Machinery.status,
        Machinery.section
    ]

    column_labels = {
        Machinery.id: "Идентификатор",
        Machinery.title: "Название",
        Machinery.model: "Модель",
        Machinery.number: "Номер",
        Machinery.status: "Статус",
        Machinery.section: "Пожарное отделение",
        Machinery.maintenance: "Обслуживание",
        Machinery.created_at: "Создан",
        Machinery.updated_at: "Последние обновление"
    }

    column_formatters = {
        "status": lambda m, a: STATUS_MAINTENANCE_MAP[m.status.value]
    }

    column_formatters_detail = {
        "status": lambda m, a: STATUS_MAINTENANCE_MAP[m.status.value]
    }

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
        "section"
    ]

    column_details_list = [
        Machinery.id,
        Machinery.title,
        Machinery.model,
        Machinery.number,
        Machinery.status,
        Machinery.section,
        Machinery.maintenance,
        Machinery.created_at,
        Machinery.updated_at
    ]

    form_edit_rules = [
        "title",
        "model",
        "number",
        "status",
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