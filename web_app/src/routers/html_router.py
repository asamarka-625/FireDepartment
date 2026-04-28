# Внешние зависимости
from typing import Annotated, Dict, Any, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import Field
# Внутренние модули
from web_app.src.dependencies import get_current_user_by_refresh_token
from web_app.src.crud import sql_get_sections, sql_get_department_by_id, sql_get_machineries
from web_app.src.schemas import UserScheme


router = APIRouter()
templates = Jinja2Templates(directory="web_app/templates")


# Получения информации для формирования страницы
async def get_info_page_by_user(
    user: UserScheme,
    section_id: Optional[int] = None
) -> Dict[str, Any]:
    page_info = {}

    department = await sql_get_department_by_id(department_id=user.department_id)
    page_info["department"] = department.title

    if not user.admin:
        sections = department.sections

    else:
        sections = await sql_get_sections()

    if section_id is not None:
        section = next((section.title for section in sections if section.id == section_id), None)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        page_info["section"] = section

    page_info["sections"] = sections

    return page_info


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
    page_info = await get_info_page_by_user(user=current_user)

    context = {
        "title": "Главная страница",
        **page_info
    }

    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)


# Страница со сведеньем о технике
@router.get("/equipment/{section_id}", response_class=HTMLResponse)
async def equipment_page(
    request: Request,
    section_id: Annotated[int, Field(ge=1)],
    current_user: UserScheme = Depends(get_current_user_by_refresh_token)
):
    page_info = await get_info_page_by_user(
        user=current_user,
        section_id=section_id
    )

    machineries = await sql_get_machineries(section_id=section_id)
    context = {
        "title": "Сведения о машинах",
        "section_id": section_id,
        "machineries": machineries,
        **page_info
    }

    return templates.TemplateResponse(request=request, name="equipment.html", context=context)


# Страница со строевыми записками
@router.get("/reports/{section_id}", response_class=HTMLResponse)
async def equipment_page(
    request: Request,
    section_id: Annotated[int, Field(ge=1)],
    current_user: UserScheme = Depends(get_current_user_by_refresh_token)
):
    page_info = await get_info_page_by_user(
        user=current_user,
        section_id=section_id
    )

    context = {
        "title": "Строевые записки",
        "section_id": section_id,
        **page_info
    }

    return templates.TemplateResponse(request=request, name="reports.html", context=context)