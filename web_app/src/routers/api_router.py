# Внешние зависимости
from typing import Dict, Annotated, List
import base64
from pydantic import Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
# Внутренние модули
from web_app.src.dependencies import (get_current_user_by_access_token, get_data_by_refresh_token, verify_csrf_token,
                                      get_accessible_section_ids, get_relocation_target_ids)
from web_app.src.schemas import (UserScheme, UpdateMachineryRequest, ReportScheme, CreateReportRequestScheme,
                                 CreateExportReportScheme, CreateRelocationRequest, UpdateRelocationRequest,
                                 CancelRelocationRequest)
from web_app.src.crud import (sql_get_machinery_access, sql_update_machinery, sql_create_report, sql_get_reports,
                              sql_get_all_reports, sql_get_miss_sections_title, sql_get_all_machineries,
                              sql_create_relocation, sql_update_relocation)
from web_app.src.utils import creator_reports


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


# Аутентифицированный пользователь с проверкой токенов (access + refresh + csrf)
async def authorized_user(
    current_user: UserScheme = Depends(get_current_user_by_access_token),
    token_data: Dict[str, str] = Depends(get_data_by_refresh_token),
    csrf_user_id: str = Depends(verify_csrf_token)
) -> UserScheme:
    await user_rights_validation(
        user=current_user,
        token_data=token_data,
        csrf_user_id=csrf_user_id
    )

    return current_user


# Проверка доступа пользователя к ПСЧ (учитывает уровень учётной записи: ПСО / ПСЧ / администратор)
async def check_section_access(user: UserScheme, section_id: int) -> None:
    section_ids = await get_accessible_section_ids(user)

    if section_ids is not None and section_id not in section_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post(
    "/machinery/update",
    response_class=JSONResponse,
    summary="Изменение информации о машине"
)
async def machinery_update(
    data_update: UpdateMachineryRequest,
    current_user: UserScheme = Depends(authorized_user)
):
    section_ids = await get_accessible_section_ids(current_user)

    access = await sql_get_machinery_access(
        machinery_id=data_update.id,
        section_ids=section_ids
    )
    if access is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Принимающая ПСЧ правит только сегодняшний расчёт; состояние и обслуживание — за штатной ПСЧ
    await sql_update_machinery(update=data_update, crew_only=(access == "receiver"))

    return {"status": "success"}


@router.post(
    "/relocations/create",
    response_class=JSONResponse,
    summary="Оформление передислокации машины"
)
async def create_relocation(
    data: CreateRelocationRequest,
    current_user: UserScheme = Depends(authorized_user)
):
    await sql_create_relocation(
        machinery_id=data.machinery_id,
        to_section_id=data.to_section_id,
        date_return=data.date_return,
        user_id=current_user.id,
        manage_section_ids=await get_accessible_section_ids(current_user),
        target_section_ids=await get_relocation_target_ids(current_user)
    )

    return {"status": "success"}


@router.post(
    "/relocations/update",
    response_class=JSONResponse,
    summary="Изменение даты возврата (дата не позже сегодняшней — отмена передислокации)"
)
async def update_relocation(
    data: UpdateRelocationRequest,
    current_user: UserScheme = Depends(authorized_user)
):
    await sql_update_relocation(
        machinery_id=data.machinery_id,
        date_return=data.date_return,
        user_id=current_user.id,
        manage_section_ids=await get_accessible_section_ids(current_user)
    )

    return {"status": "success"}


@router.post(
    "/relocations/cancel",
    response_class=JSONResponse,
    summary="Отмена передислокации машины"
)
async def cancel_relocation(
    data: CancelRelocationRequest,
    current_user: UserScheme = Depends(authorized_user)
):
    await sql_update_relocation(
        machinery_id=data.machinery_id,
        date_return=None,
        user_id=current_user.id,
        manage_section_ids=await get_accessible_section_ids(current_user),
        cancel=True
    )

    return {"status": "success"}


@router.post(
    "/reports/create",
    response_class=JSONResponse,
    summary="Создание строевой записки"
)
async def create_report(
    data: CreateReportRequestScheme,
    current_user: UserScheme = Depends(authorized_user)
):
    await check_section_access(current_user, data.section_id)

    await sql_create_report(
        section_id=data.section_id,
        leadership=data.leadership,
        total_personnel=data.total_personnel,
        personnel=data.personnel,
        current_personnel=data.current_personnel,
        operational_machinery=data.operational_machinery
    )

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
    current_user: UserScheme = Depends(authorized_user)
):
    await check_section_access(current_user, section_id)

    reports = await sql_get_reports(
        section_id=section_id,
        last_seen_id=last_seen_id,
        reports_per_page=reports_per_page
    )

    return reports


def _xlsx_response(buffer, missing: List[str]) -> JSONResponse:
    file_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")

    return JSONResponse({
        "file": file_b64,
        "missing": missing,
    })


@router.post(
    "/reports/export",
    response_class=StreamingResponse,
    summary="Получение таблицы всех строевых записок"
)
async def export_reports(
    data: CreateExportReportScheme,
    current_user: UserScheme = Depends(authorized_user)
):
    if not current_user.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    reports, section_ids = await sql_get_all_reports()
    miss_sections = await sql_get_miss_sections_title(
        section_ids=section_ids
    )

    # Лист «Техника» — только по ПСЧ, подавшим строевую записку (как и лист «Строевая записка»)
    machineries = await sql_get_all_machineries(section_ids=section_ids)

    buffer = creator_reports.run(
        reports=reports,
        machineries=machineries,
        creator=data.creator
    )

    return _xlsx_response(buffer, miss_sections)


@router.post(
    "/reports/export/{section_id}",
    response_class=StreamingResponse,
    summary="Выгрузка строевой записки одной ПСЧ"
)
async def export_section_report(
    section_id: Annotated[int, Field(ge=1)],
    data: CreateExportReportScheme,
    current_user: UserScheme = Depends(authorized_user)
):
    await check_section_access(current_user, section_id)

    reports, section_ids = await sql_get_all_reports(section_ids=(section_id,))
    if not reports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Строевая записка за сегодня не подана"
        )

    machineries = await sql_get_all_machineries(section_ids=section_ids)

    buffer = creator_reports.run(
        reports=reports,
        machineries=machineries,
        creator=data.creator
    )

    return _xlsx_response(buffer, [])
