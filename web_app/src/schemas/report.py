# Внешние зависимости
from typing import Annotated, List
from datetime import date
from pydantic import BaseModel, Field, ConfigDict
# Внутренние модули
from web_app.src.schemas.machinery import MachineryScheme


# Схема строевой записки
class ReportScheme(BaseModel):
    id: Annotated[int, Field(ge=1)]
    machinery: List[MachineryScheme]
    section: Annotated[str, Field(max_length=128)]
    date: date

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        str_strip_whitespace=True
    )