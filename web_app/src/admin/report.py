# Внешние зависимости
from sqladmin import ModelView
# Внутренние модули
from web_app.src.models import Report


# Админка для Report
class ReportAdmin(ModelView, model=Report):
    column_list = [
        Report.id,
        Report.section,
        Report.date
    ]

    column_labels = {
        Report.id: "Идентификатор",
        Report.data: "Данные записки",
        Report.section: "Отделение",
        Report.date: "Дата",
        Report.created_at: "Создан",
        Report.updated_at: "Последние обновление"
    }

    column_searchable_list = [Report.id, Report.date]  # список столбцов, которые можно искать
    column_sortable_list = [
        Report.id,
        Report.date
    ]  # список столбцов, которые можно сортировать

    column_default_sort = [(Report.id, True)]

    column_details_list = [
        Report.id,
        Report.data,
        Report.section,
        Report.date,
        Report.created_at,
        Report.updated_at
    ]

    can_create = False  # право создавать
    can_edit = False  # право редактировать
    can_delete = True  # право удалять
    can_view_details = True  # право смотреть всю информацию
    can_export = True  # право экспортировать

    name = "Служебная записка"  # название
    name_plural = "Служебные записки"  # множественное название
    icon = "fa-solid fa-book"  # иконка
    category = "Записки"  # категория
    category_icon = "fa-solid fa-list"  # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]