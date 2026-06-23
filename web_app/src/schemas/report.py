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
    total_personnel: Annotated[int, Field(ge=0)]
    personnel: Annotated[int, Field(ge=0)]
    current_personnel: Annotated[int, Field(ge=0)]
    leadership: Annotated[str, Field(max_length=512)]

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        str_strip_whitespace=True
    )


# Схема запроса на создание строевой записки
class CreateReportRequestScheme(BaseModel):
    section_id: Annotated[int, Field(ge=1)]
    total_personnel: Annotated[int, Field(ge=0)]
    personnel: Annotated[int, Field(ge=0)]
    current_personnel: Annotated[int, Field(ge=0)]
    leadership: Annotated[str, Field(max_length=512)]

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True
    )


# Схема запроса на создание экспорта строевых записок
class CreateExportReportScheme(BaseModel):
    creator: Annotated[str, Field(max_length=512)]

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True
    )