# Внешние зависимости
from sqladmin import ModelView
# Внутренние модули
from web_app.src.models import Department


# Админка для Department
class DepartmentAdmin(ModelView, model=Department):
    column_list = [
        Department.id,
        Department.title
    ]

    column_labels = {
        Department.id: "Идентификатор",
        Department.title: "Название",
        Department.users: "Пользователи",
        Department.sections: "Отделения",
        Department.created_at: "Создан",
        Department.updated_at: "Последние обновление"
    }

    column_searchable_list = [Department.id]  # список столбцов, которые можно искать
    column_sortable_list = [
        Department.id
    ]  # список столбцов, которые можно сортировать

    column_default_sort = [(Department.id, True)]

    form_create_rules = [
        "title"
    ]

    column_details_list = [
        Department.id,
        Department.title,
        Department.users,
        Department.sections,
        Department.created_at,
        Department.updated_at
    ]

    form_edit_rules = [
        "title"
        "users",
        "sections"
    ]

    can_create = True  # право создавать
    can_edit = True  # право редактировать
    can_delete = True  # право удалять
    can_view_details = True  # право смотреть всю информацию
    can_export = True  # право экспортировать

    name = "Пожарный участок"  # название
    name_plural = "Пожарные участки"  # множественное название
    icon = "fa-solid fa-fire"  # иконка
    category = "Отделения"  # категория
    category_icon = "fa-solid fa-list"  # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]