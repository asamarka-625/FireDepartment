# Внешние зависимости
from typing import Any, List
import logging
from pydantic import Field, PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict
# Внутренние модули
from web_app.src.core.logger import setup_logger


# Конфиг приложения
class Config(BaseSettings):
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")

    ADMIN_LOGIN: str = Field(alias="ADMIN_LOGIN")
    ADMIN_PASSWORD: str = Field(alias="ADMIN_PASSWORD")

    redis_url: str = Field(alias="REDIS_URL")
    USER_CACHE_SECONDS: int = Field(alias="USER_CACHE_SECONDS")

    # Security
    ALGORITHM: str = Field(alias="ALGORITHM")

    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(alias="REFRESH_TOKEN_EXPIRE_MINUTES")
    SECRET_REFRESH_KEY: str = Field(alias="SECRET_REFRESH_KEY")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    SECRET_ACCESS_KEY: str = Field(alias="SECRET_ACCESS_KEY")

    CSRF_TOKEN_EXPIRE_MINUTES: int = Field(alias="CSRF_TOKEN_EXPIRE_MINUTES")
    SECRET_CSRF_KEY: str = Field(alias="SECRET_CSRF_KEY")

    allowed_origins_env: str = Field(alias="ALLOWED_ORIGINS", default="*")

    LOG_LEVEL: str = Field(alias="LOG_LEVEL", default="INFO")
    LOG_DIR: str = Field(alias="LOG_DIR", default="logs")
    LOG_FILE: str = Field(alias="LOG_FILE", default="web_app")

    # Приватное поле для логгера, чтобы Pydantic его не проверял
    _logger: logging.Logger = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        # Настройка логгера
        logger = setup_logger(
            level=self.LOG_LEVEL,
            log_dir=self.LOG_DIR,
            log_file=self.LOG_FILE
        )

        # Используем object.__setattr__ для PrivateAttr
        object.__setattr__(self, "_logger", logger)

        self._logger.info("Configuration initialized via Pydantic")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        if self.allowed_origins_env == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins_env.split(",") if origin.strip()]

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@db:5432/{self.postgres_db}"

    def __str__(self) -> str:
        try:
            return f"Config(database_host={self.DATABASE_URL.split('@')[-1]})"
        except Exception:
            return "Config(database_host=unknown)"

    model_config = SettingsConfigDict(
        env_file=[".env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )


cfg = Config()