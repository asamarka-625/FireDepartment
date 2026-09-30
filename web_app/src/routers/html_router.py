# Внешние зависимости
from typing import Annotated, Dict, Any, Optional, List
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import Field
# Внутренние модули
from web_app.src.dependencies import (get_current_user_by_refresh_token, get_accessible_section_ids,
                                      get_relocation_target_ids)
from web_app.src.crud import (sql_get_sections, sql_get_department_by_id, sql_get_machineries,
                              sql_get_today_report_signature)
from web_app.src.models import MACHINERY_KIND_MAP
from web_app.src.schemas import UserScheme, MachineryScheme


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
        page_info["admin"] = False
        # ПСО-уровень видит все ПСЧ отряда, ПСЧ-уровень — только свою часть
        accessible_ids = await get_accessible_section_ids(user)
        sections = [section for section in department.sections if section.id in accessible_ids]

    else:
        page_info["admin"] = True
        sections = await sql_get_sections()

    if section_id is not None:
        section = next((section.title for section in sections if section.id == section_id), None)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        page_info["section"] = section

    page_info["sections"] = sections

    return page_info


# Баннер о рассинхроне сегодняшней записки с передислокацией (п. 3.5).
# Возвращает None, если записка не подана или актуальна; иначе текст уведомления.
def get_relocation_banner(
    report_signature,
    machineries: List[MachineryScheme]
) -> Optional[str]:
    if report_signature is None:
        return None

    submitted = {(machinery_id, direction) for machinery_id, direction in report_signature if direction}
    current = {(m.id, m.relocation.direction) for m in machineries if m.relocation}

    if submitted == current:
        return None

    if any(direction == "in" for _, direction in current - submitted):
        return "Поступила передислоцированная техника. Требуется обновить строевую записку"

    return "Изменилась передислокация техники. Требуется обновить строевую записку"


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

    # Список «моя техника сегодня» + машины, ушедшие в передислокацию (для отмены/возврата)
    all_machineries = await sql_get_machineries(section_id=section_id, include_relocated_out=True)
    machineries = [m for m in all_machineries if not (m.relocation and m.relocation.direction == "out")]
    relocated_out = [m for m in all_machineries if m.relocation and m.relocation.direction == "out"]

    # ПСЧ, в которые можно передислоцировать (по умолчанию — часть того же ПСО)
    target_ids = await get_relocation_target_ids(current_user)
    if target_ids is None:
        candidate_sections = await sql_get_sections()
    else:
        department = await sql_get_department_by_id(department_id=current_user.department_id)
        candidate_sections = [s for s in department.sections if s.id in target_ids]
    relocation_targets = [s for s in candidate_sections if s.id != section_id]

    report_signature = await sql_get_today_report_signature(section_id=section_id)

    context = {
        "title": "Сведения о машинах",
        "section_id": section_id,
        "machineries": machineries,
        "relocated_out": relocated_out,
        "relocation_targets": relocation_targets,
        "report_submitted_today": report_signature is not None,
        "relocation_banner": get_relocation_banner(report_signature, all_machineries),
        "kind_map": MACHINERY_KIND_MAP,
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