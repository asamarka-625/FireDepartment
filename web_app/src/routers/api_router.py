# Внешние зависимости
from typing import Dict, Annotated, List
from pydantic import Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
# Внутренние модули
from web_app.src.dependencies import get_current_user_by_access_token, get_data_by_refresh_token, verify_csrf_token
from web_app.src.schemas import UserScheme, UpdateMachineryRequest, ReportScheme
from web_app.src.crud import (sql_get_department_by_id, sql_get_machinery_ids,
                              sql_update_machinery, sql_create_report, sql_get_reports)


router = APIRouter(
    prefix="/api/v1",
    tags=["Authentication"]
)


# Проверка прав пользователя
async def user_rights_validation(
    user: UserScheme,
    token_data: Dict[str, str],
    csrf_user_id: str
):
    user_id_str = str(user.id)
    if not (user_id_str == token_data["user_id"] == csrf_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token user mismatch")


@router.post(
    "/machinery/update",
    response_class=JSONResponse,
    summary="Изменение информации о машине"
)
async def machinery_update(
    data_update: UpdateMachineryRequest,
    current_user: UserScheme = Depends(get_current_user_by_access_token),
    token_data: Dict[str, str] = Depends(get_data_by_refresh_token),
    csrf_user_id: str = Depends(verify_csrf_token)
):
    await user_rights_validation(
        user=current_user,
        token_data=token_data,
        csrf_user_id=csrf_user_id
    )

    if not current_user.admin:
        department = await sql_get_department_by_id(department_id=current_user.department_id)
        section_ids = tuple(section.id for section in department.sections)
        machinery_ids = await sql_get_machinery_ids(section_ids=section_ids)

        if data_update.id not in machinery_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await sql_update_machinery(update=data_update)

    return {"status": "success"}


@router.post(
    "/reports/create/{section_id}",
    response_class=JSONResponse,
    summary="Создание строевой записки"
)
async def create_report(
    section_id: Annotated[int, Field(ge=1)],
    current_user: UserScheme = Depends(get_current_user_by_access_token),
    token_data: Dict[str, str] = Depends(get_data_by_refresh_token),
    csrf_user_id: str = Depends(verify_csrf_token)
):
    await user_rights_validation(
        user=current_user,
        token_data=token_data,
        csrf_user_id=csrf_user_id
    )

    if not current_user.admin:
        department = await sql_get_department_by_id(department_id=current_user.department_id)
        section_ids = tuple(section.id for section in department.sections)

        if section_id not in section_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await sql_create_report(section_id=section_id)

    return {"status": "success"}


@router.get(
    "/reports/{section_id}",
    response_model=List[ReportScheme],
    summary="Получение строевых записок"
)
async def get_reports(
    section_id: Annotated[int, Field(ge=1)],
    last_seen_id: Annotated[int, Field(ge=0)] = 0,
    reports_per_page: Annotated[int, Field(ge=10, le=50)] = 10,
    current_user: UserScheme = Depends(get_current_user_by_access_token),
    token_data: Dict[str, str] = Depends(get_data_by_refresh_token),
    csrf_user_id: str = Depends(verify_csrf_token)
):
    await user_rights_validation(
        user=current_user,
        token_data=token_data,
        csrf_user_id=csrf_user_id
    )

    if not current_user.admin:
        department = await sql_get_department_by_id(department_id=current_user.department_id)
        section_ids = tuple(section.id for section in department.sections)

        if section_id not in section_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    reports = await sql_get_reports(
        section_id=section_id,
        last_seen_id=last_seen_id,
        reports_per_page=reports_per_page
    )

    return reports