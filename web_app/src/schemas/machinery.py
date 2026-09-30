# Внешние зависимости
from typing import Annotated, Literal, Optional
from datetime import date as date_type
from pydantic import BaseModel, Field, ConfigDict, computed_field
# Внутренние модули
from web_app.src.utils.machinery_rules import machinery_label


# Схема обслуживания
class MaintenanceScheme(BaseModel):
    note: Annotated[str, Field(max_length=256, min_length=1)]
    date: Optional[date_type] = None

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        str_strip_whitespace=True
    )


# Схема обновления машины
class UpdateMachineryRequest(BaseModel):
    id: Annotated[int, Field(ge=1)]
    status: Optional[
        Literal[
            "включено", "резерв", "резерв (лсо)", "резерв (лсб)",
            "ремонт", "то-1", "то-2", "вп", "выключена"
        ]
    ]
    supervisor: Annotated[str, Field(max_length=128)]
    current_personnel: Annotated[int, Field(ge=0)]
    gdzs: Annotated[int, Field(ge=0)]
    maintenance: Optional[MaintenanceScheme]
    # Ход выезда автоцистерны. Если поле не передано — не меняется; передано null — сбрасывается.
    departure_order: Optional[Annotated[int, Field(ge=1)]] = None

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True
    )


# Сведения о передислокации в разрезе конкретной ПСЧ
class RelocationInfoScheme(BaseModel):
    # out — машина передислоцирована ИЗ этой ПСЧ, in — машина принята В эту ПСЧ
    direction: Literal["in", "out"]
    partner_id: Annotated[int, Field(ge=1)]
    partner: Annotated[str, Field(max_length=128)]  # вторая ПСЧ (принимающая для out, отдающая для in)
    date_from: date_type
    date_to: Optional[date_type] = None

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True
    )


# Схема машины
class MachineryScheme(BaseModel):
    id: Annotated[int, Field(ge=1)]
    title: Annotated[str, Field(max_length=64)]
    model: Optional[Annotated[str, Field(max_length=128)]] = None
    number: Optional[Annotated[str, Field(max_length=32)]] = None
    status: Annotated[str, Field(max_length=64)]
    supervisor: Annotated[str, Field(max_length=128)]
    current_personnel: Annotated[int, Field(ge=0)]
    gdzs: Annotated[int, Field(ge=0)]
    maintenance: Optional[MaintenanceScheme] = None

    # SPECIAL / OTHER. None — старые записки, сформированные до появления признака
    kind: Optional[Literal["SPECIAL", "OTHER"]] = None
    short_title: Optional[Annotated[str, Field(max_length=16)]] = None
    departure_order: Optional[Annotated[int, Field(ge=1)]] = None

    # Штатная ПСЧ (владелец)
    section_id: Optional[int] = None
    section: Optional[str] = None

    relocation: Optional[RelocationInfoScheme] = None

    # Подпись для формы строевой записки («АЦ-1», «АЛ» ...). Не хранится — считается при выводе.
    @computed_field
    @property
    def label(self) -> str:
        return machinery_label(self.title, self.short_title, self.departure_order)

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        str_strip_whitespace=True
    )


# Запрос на оформление передислокации
class CreateRelocationRequest(BaseModel):
    machinery_id: Annotated[int, Field(ge=1)]
    to_section_id: Annotated[int, Field(ge=1)]
    # Дата возврата. Пусто — до конца текущих суток (закрывается в 00:00)
    date_return: Optional[date_type] = None

    model_config = ConfigDict(frozen=True)


# Запрос на изменение/отмену передислокации: дата возврата не позже сегодняшней = отмена
class UpdateRelocationRequest(BaseModel):
    machinery_id: Annotated[int, Field(ge=1)]
    date_return: Optional[date_type] = None

    model_config = ConfigDict(frozen=True)


class CancelRelocationRequest(BaseModel):
    machinery_id: Annotated[int, Field(ge=1)]

    model_config = ConfigDict(frozen=True)