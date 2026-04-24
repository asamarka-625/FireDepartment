from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict


# Схема пользователя
class UserScheme(BaseModel):
    id: Annotated[int, Field(ge=1)]
    email: Annotated[str, Field(strict=True, max_length=255)]
    department_id: Annotated[int, Field(ge=1)]

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        str_strip_whitespace=True
    )