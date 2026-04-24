# Внешние зависимости
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
# Внутренние модули
from web_app.src.dependencies import (authenticate_user, create_refresh_token, create_access_token,
                                      create_csrf_token, get_connection_info, get_current_user_by_access_token,
                                      get_data_by_refresh_token, verify_csrf_token)
from web_app.src.core import cfg
from web_app.src.utils import redis_service
from web_app.src.schemas import UserScheme, TokensResponse


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


@router.post(
    "/login",
    response_model=TokensResponse,
    summary="Аутентификация пользователя"
)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection_info: Dict[str, str] = Depends(get_connection_info)
):
    user = await authenticate_user(form_data.username.lower(), form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    refresh_token = await create_refresh_token(
        user_id=str(user.id),
        user_agent=connection_info["user_agent"],
        ip=connection_info["ip"]
    )

    response.set_cookie(
        key="refresh_token",
        path="/",
        value=refresh_token,
        httponly=True,
        secure=False, # HTTP
        samesite="lax",
        max_age=cfg.REFRESH_TOKEN_EXPIRE_MINUTES * 60
    )

    return TokensResponse(
        csrf_token=create_csrf_token(user_id=str(user.id)),
        access_token=create_access_token(user_id=str(user.id)),
    )


@router.post(
    "/refresh",
    response_model=TokensResponse,
    summary="Обновление токена"
)
async def get_refresh_token(
    response: Response,
    token_data: Dict[str, str] = Depends(get_data_by_refresh_token),
    connection_info: Dict[str, str] = Depends(get_connection_info)
):
    refresh_token = await create_refresh_token(
        user_id=token_data["user_id"],
        user_agent=connection_info["user_agent"],
        ip=connection_info["ip"],
        last_token=token_data["jti"]
    )

    response.set_cookie(
        key="refresh_token",
        path="/",
        value=refresh_token,
        httponly=True,
        secure=False, # HTTP
        samesite="lax",
        max_age=cfg.REFRESH_TOKEN_EXPIRE_MINUTES * 60
    )

    return TokensResponse(
        csrf_token=create_csrf_token(user_id=token_data["user_id"]),
        access_token=create_access_token(user_id=token_data["user_id"])
    )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: UserScheme = Depends(get_current_user_by_access_token),
    token_data: Dict[str, str] = Depends(get_data_by_refresh_token),
    csrf_user_id: str = Depends(verify_csrf_token)
):
    user_id_str = str(current_user.id)
    if not (user_id_str == token_data["user_id"] == csrf_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token user mismatch")

    await redis_service.del_user_refresh_token(
        user_id=token_data["user_id"],
        refresh_uuid=token_data["jti"]
    )

    response.delete_cookie(key="refresh_token", path="/")

    return {"message": "Logout successful", "redirect": "/login"}