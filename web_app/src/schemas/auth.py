# Внешние зависимости
from pydantic import BaseModel


# Схема ответа токенов
class TokensResponse(BaseModel):
    csrf_token: str
    access_token: str