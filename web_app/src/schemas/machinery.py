# Внешние зависимости
from typing import Annotated, Literal, Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


# Схема обслуживания
class MaintenanceScheme(BaseModel):
    note: Annotated[str, Field(max_length=256, min_length=1)]
    date: date

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        str_strip_whitespace=True
    )

# Схема обновления машины
class UpdateMachineryRequest(BaseModel):
    id: Annotated[int, Field(ge=1)]
    status: Optional[
        Literal["включено", "резерв", "резерв (лсо)", "ремонт", "то-1", "то-2", "вп", "выключена"]
    ]
    operational: bool
    supervisor: Annotated[str, Field(max_length=128)]
    current_personnel: Annotated[int, Field(ge=0)]
    gdzs: Annotated[int, Field(ge=0)]
    maintenance: Optional[MaintenanceScheme]

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True
    )


# Схема машины
class MachineryScheme(BaseModel):
    id: Annotated[int, Field(ge=1)]
    title: Annotated[str, Field(max_length=64)]
    model: Annotated[str, Field(max_length=128)]
    number: Optional[Annotated[str, Field(max_length=32)]]
    status: Annotated[str, Field(max_length=64)]
    operational: bool
    supervisor: Annotated[str, Field(max_length=128)]
    current_personnel: Annotated[int, Field(ge=0)]
    gdzs: Annotated[int, Field(ge=0)]
    maintenance: Optional[MaintenanceScheme] = None

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        str_strip_whitespace=True
    )