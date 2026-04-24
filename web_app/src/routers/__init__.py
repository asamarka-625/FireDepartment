# Внешние зависимости
from fastapi import APIRouter
# Внутренние модули
from web_app.src.routers.auth_router import router as auth_router
from web_app.src.routers.html_router import router as html_router
from web_app.src.routers.api_router import router as api_router


router = APIRouter()
router.include_router(auth_router)
router.include_router(html_router)
router.include_router(api_router)