# Внешние зависимости
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin
# Внутренние модули
from web_app.src.core import cfg, setup_database, engine
from web_app.src.routers import router
from web_app.src.middlewares import AuthenticationMiddleware
from web_app.src.admin import (DepartmentAdmin, SectionAdmin, MachineryAdmin, MaintenanceAdmin,
                               ReportAdmin, UserAdmin, authentication_backend)
from web_app.src.utils import redis_service


async def startup():
    cfg.logger.info("Запускаем приложение...")

    cfg.logger.info("Инициализируем базу данных")
    await setup_database()

    cfg.logger.info("Инициализируем redis")
    await redis_service.init_redis()


async def shutdown():
    cfg.logger.info("Закрываем соединение с redis")
    await redis_service.close_redis()

    cfg.logger.info("Останавливаем приложение...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup логика
    await startup()
    yield
    # Shutdown логика
    await shutdown()


app = FastAPI(lifespan=lifespan, docs_url="/api/docs", root_path="/72tldh")

# Подключение маршрутов
app.include_router(router)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Authorization",
        "Content-Type",
        "Content-Language",
        "Origin",
        "Referer",
        "User-Agent",
        "X-CSRF-Token",
        "X-Requested-With",
    ],
    max_age=600
)

app.add_middleware(AuthenticationMiddleware, login_url="/72tldh/login")

# Админка
admin = Admin(app, engine, authentication_backend=authentication_backend)
admin.add_view(DepartmentAdmin)
admin.add_view(SectionAdmin)
admin.add_view(MachineryAdmin)
admin.add_view(MaintenanceAdmin)
admin.add_view(ReportAdmin)
admin.add_view(UserAdmin)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', port=8000, reload=False)