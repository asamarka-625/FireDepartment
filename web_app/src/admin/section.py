# Внешние зависимости
from sqladmin import ModelView
# Внутренние модули
from web_app.src.models import Section


# Админка для Section
class SectionAdmin(ModelView, model=Section):
    column_list = [
        Section.id,
        Section.title,
        Section.department
    ]

    column_labels = {
        Section.id: "Идентификатор",
        Section.title: "Название",
        Section.department: "Пожарный участок",
        Section.machineries: "Техника",
        Section.reports: "Служебные записки",
        Section.created_at: "Создан",
        Section.updated_at: "Последние обновление"
    }

    column_searchable_list = [Section.id]  # список столбцов, которые можно искать
    column_sortable_list = [
        Section.id
    ]  # список столбцов, которые можно сортировать

    column_default_sort = [(Section.id, True)]

    form_create_rules = [
        "title",
        "department"
    ]

    column_details_list = [
        Section.id,
        Section.title,
        Section.department,
        Section.machineries,
        Section.reports,
        Section.created_at,
        Section.updated_at
    ]

    form_edit_rules = [
        "title",
        "department"
    ]

    can_create = True  # право создавать
    can_edit = True  # право редактировать
    can_delete = True  # право удалять
    can_view_details = True  # право смотреть всю информацию
    can_export = True  # право экспортировать

    name = "Пожарное отделение участка"  # название
    name_plural = "Пожарные отделения участков"  # множественное название
    icon = "fa-solid fa-fire"  # иконка
    category = "Отделения"  # категория
    category_icon = "fa-solid fa-list"  # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]