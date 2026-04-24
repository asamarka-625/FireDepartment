# Внешние зависимости
from typing import Optional
from datetime import date
from enum import Enum
import sqlalchemy.orm as so
import sqlalchemy as sa
# Внутренние модули
from web_app.src.models.base import Base


# Enum класс статусов машин
class StatusMaintenance(Enum):
    ON = "ON"
    RESERVE = "RESERVE"
    RESERVE_LSO = "RESERVE_LSO"
    REPAIR = "REPAIR"
    TO1 = "TO1"
    TO2 = "TO2"
    VP = "VP"
    OFF = "OFF"


STATUS_MAINTENANCE_MAP = {
    "ON": "Включено",
    "RESERVE": "Резерв",
    "RESERVE_LSO": "Резерв (ЛСО)",
    "REPAIR": "Ремонт",
    "TO1": "ТО-1",
    "TO2": "ТО-2",
    "VP": "ВП",
    "OFF": "Выключена"
}

REVERSE_STATUS_MAINTENANCE_MAP = {
    "включено": StatusMaintenance.ON,
    "резерв": StatusMaintenance.RESERVE,
    "резерв (лсо)": StatusMaintenance.RESERVE_LSO,
    "ремонт": StatusMaintenance.REPAIR,
    "то-1": StatusMaintenance.TO1,
    "то-2": StatusMaintenance.TO2,
    "вп": StatusMaintenance.VP,
    "выключена": StatusMaintenance.OFF
}

# Пожарные машины
class Machinery(Base):
    __tablename__ = "machineries"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(
        sa.String(64),
        nullable=False
    )
    model: so.Mapped[str] = so.mapped_column(
        sa.String(128),
        nullable=True
    )
    number: so.Mapped[str] = so.mapped_column(
        sa.String(32),
        index=True,
        nullable=True
    )
    status: so.Mapped[StatusMaintenance] = so.mapped_column(
        sa.Enum(StatusMaintenance),
        index=True,
        nullable=False
    )

    # Связи с отделением
    section_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("sections.id"),
        index=True,
        nullable=False
    )
    section: so.Mapped["Section"] = so.relationship(
        "Section",
        back_populates="machineries"
    )

    # Связь с обслуживанием
    maintenance: so.Mapped[Optional["Maintenance"]] = so.relationship(
        "Maintenance",
        back_populates="machinery",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Machinery(id={self.id}, title={self.title})>"

    def __str__(self):
        return self.title


# Обслуживание машины
class Maintenance(Base):
    __tablename__ = "maintenance"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    note: so.Mapped[str] = so.mapped_column(
        sa.String(256),
        nullable=False
    )
    date: so.Mapped[date] = so.mapped_column(
        sa.Date,
        index=True,
        nullable=False
    )

    # Связь с машиной
    machinery_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("machineries.id"),
        unique=True,
        nullable=False
    )
    machinery: so.Mapped[Machinery] = so.relationship(
        "Machinery",
        back_populates="maintenance"
    )

    def __repr__(self):
        return f"<Maintenance(id={self.id}, machinery_id={self.machinery_id})>"

    def __str__(self):
        return self.date.strftime("%d.%m.%Y")