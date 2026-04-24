# Внешние зависимости
from typing import Annotated
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import Field
# Внутренние модули
from web_app.src.dependencies import get_current_user_by_refresh_token
from web_app.src.crud import sql_get_department_by_id, sql_get_machineries
from web_app.src.schemas import UserScheme


router = APIRouter()
templates = Jinja2Templates(directory="web_app/templates")


# Страница аутентификации
@router.get("/login", response_class=HTMLResponse)
async def auth_page(
    request: Request
):
    return templates.TemplateResponse(request=request, name="authentication.html")


# Главая страница
@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    current_user: UserScheme = Depends(get_current_user_by_refresh_token)
):
    department = await sql_get_department_by_id(department_id=current_user.department_id)
    context = {
        "title": "Главная страница",
        "department": department.title,
        "sections": department.sections
    }

    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)


# Страница сс сведеньем о технике
@router.get("/equipment/{section_id}", response_class=HTMLResponse)
async def equipment_page(
    request: Request,
    section_id: Annotated[int, Field(ge=1)],
    current_user: UserScheme = Depends(get_current_user_by_refresh_token)
):
    department = await sql_get_department_by_id(department_id=current_user.department_id)
    section_ids = tuple(section.id for section in department.sections)

    if section_id not in section_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    machineries = await sql_get_machineries(section_id=section_id)
    context = {
        "title": "Сведения о машинах",
        "department": department.title,
        "sections": department.sections,
        "machineries": machineries
    }

    return templates.TemplateResponse(request=request, name="equipment.html", context=context)