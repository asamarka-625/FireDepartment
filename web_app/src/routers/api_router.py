# Внешние зависимости
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
# Внутренние модули
from web_app.src.dependencies import get_current_user_by_access_token, get_data_by_refresh_token, verify_csrf_token
from web_app.src.schemas import UserScheme, UpdateMachineryRequest
from web_app.src.crud import sql_get_department_by_id, sql_update_machinery


router = APIRouter(
    prefix="/api/v1",
    tags=["Authentication"]
)


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
    user_id_str = str(current_user.id)
    if not (user_id_str == token_data["user_id"] == csrf_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token user mismatch")

    department = await sql_get_department_by_id(department_id=current_user.department_id)
    section_ids = tuple(section.id for section in department.sections)

    if data_update.id not in section_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await sql_update_machinery(update=data_update)

    return {"status": "success"}