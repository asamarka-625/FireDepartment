# Внешние зависимости
from typing import Type, Any
from starlette.requests import Request
from sqladmin import ModelView
from sqladmin.forms import Form
from wtforms import PasswordField
from wtforms.validators import DataRequired
# Внутренние модули
from web_app.src.models import User
from web_app.src.utils import get_password_hash


# Админка для User
class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.email,
        User.department,
        User.section
    ]

    column_labels = {
        User.id: "Идентификатор",
        User.email: "Электронная почта",
        User.department: "Пожарно-спасательный отряд (ПСО)",
        User.section: "ПСЧ (заполнять для учётной записи уровня ПСЧ; пусто — уровень ПСО, все ПСЧ отряда)",
        User.admin: "Администратор",
        User.created_at: "Создан",
        User.updated_at: "Последние обновление",
        "password": "Пароль"
    }

    async def scaffold_form(self, form_type: str = None) -> Type[Form]:
        form_class = await super().scaffold_form(form_type)

        if "password" in form_type:
            form_class.password = PasswordField(
                label="Пароль",
                validators=[DataRequired()],
                description="Придумайте пароль"
            )

        return form_class

    async def on_model_change(self, data, model, is_created, request):
        # Учётная запись уровня ПСЧ: часть должна входить в отряд (ПСО) пользователя
        section = data.get("section")
        department = data.get("department")
        if section is not None and department is not None and section.department_id != department.id:
            raise ValueError("Выбранная ПСЧ не входит в выбранный отряд (ПСО)")

        # Хэширование пароля
        if "password" in data and data["password"]:
            data["password_hash"] = get_password_hash(data["password"])

        return await super().on_model_change(data, model, is_created, request)

    column_searchable_list = [User.id, User.email]  # список столбцов, которые можно искать
    column_sortable_list = [
        User.id
    ]  # список столбцов, которые можно сортировать

    column_default_sort = [(User.id, True)]

    form_create_rules = [
        "email",
        "password",
        "department",
        "section",
        "admin"
    ]

    column_details_list = [
        User.id,
        User.email,
        User.department,
        User.section,
        User.admin,
        User.created_at,
        User.updated_at
    ]

    form_edit_rules = [
        "email",
        "password",
        "department",
        "section",
        "admin"
    ]

    can_create = True  # право создавать
    can_edit = True  # право редактировать
    can_delete = True  # право удалять
    can_view_details = True  # право смотреть всю информацию
    can_export = True  # право экспортировать

    name = "Пользователь" # название
    name_plural = "Пользователи" # множественное название
    icon = "fa-solid fa-user" # иконка
    category = "Пользователи" # категория
    category_icon = "fa-solid fa-list" # иконка категории

    page_size = 10
    page_size_options = [10, 25, 50, 100]