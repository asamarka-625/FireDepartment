from typing import Annotated, Literal, Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


# Схема обслуживания
class MaintenanceScheme(BaseModel):
    note: Annotated[str, Field(max_length=256, min_length=1)]
    date: date


# Схема обновления машины
class UpdateMachineryRequest(BaseModel):
    id: Annotated[int, Field(ge=1)]
    status: Optional[
        Literal["включено", "резерв", "резерв (лсо)","ремонт", "то-1", "то-2", "вп", "выключена"]
    ] = None
    maintenance: Optional[MaintenanceScheme] = None

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True
    )