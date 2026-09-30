# Внешние зависимости
from typing import Optional, List
from datetime import date, timedelta
from enum import Enum
import sqlalchemy.orm as so
import sqlalchemy as sa
# Внутренние модули
from web_app.src.models.base import Base


# Enum класс статусов машин
class StatusMaintenance(Enum):
    ON = "ON"
    RESERVE = "RESERVE"
    RESERVE_LSO = "RESERVE_LSO"  # личный состав отсутствует
    RESERVE_LSB = "RESERVE_LSB"  # личный состав болен
    REPAIR = "REPAIR"
    TO1 = "TO1"
    TO2 = "TO2"
    VP = "VP"
    OFF = "OFF"


STATUS_MAINTENANCE_MAP = {
    "ON": "Включено",
    "RESERVE": "Резерв",
    "RESERVE_LSO": "Резерв (ЛСО)",
    "RESERVE_LSB": "Резерв (ЛСБ)",
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
    "резерв (лсб)": StatusMaintenance.RESERVE_LSB,
    "ремонт": StatusMaintenance.REPAIR,
    "то-1": StatusMaintenance.TO1,
    "то-2": StatusMaintenance.TO2,
    "вп": StatusMaintenance.VP,
    "выключена": StatusMaintenance.OFF
}

# Состояния (русские названия), в которых допустима передислокация: «Включено» и все виды «Резерва»
RELOCATABLE_STATUSES = frozenset({
    StatusMaintenance.ON,
    StatusMaintenance.RESERVE,
    StatusMaintenance.RESERVE_LSO,
    StatusMaintenance.RESERVE_LSB,
})


# Категория техники: участвует ли в боевом расчёте с личным составом
class MachineryKind(Enum):
    SPECIAL = "SPECIAL"  # специальная: АЦ, АЛ, АКП, АНР, АГ и т. п.
    OTHER = "OTHER"      # прочая: оперативные, хозяйственные, легковые, лодки, тракторы, автобусы


MACHINERY_KIND_MAP = {
    "SPECIAL": "Специальная",
    "OTHER": "Прочая",
}


# Пожарные машины
class Machinery(Base):
    __tablename__ = "machineries"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(
        sa.String(64),
        nullable=False
    )
    model: so.Mapped[Optional[str]] = so.mapped_column(
        sa.String(128),
        nullable=True
    )
    number: so.Mapped[Optional[str]] = so.mapped_column(
        sa.String(32),
        index=True,
        nullable=True
    )
    status: so.Mapped[StatusMaintenance] = so.mapped_column(
        sa.Enum(StatusMaintenance),
        index=True,
        nullable=False
    )

    # Категория: специальная / прочая (задаётся администратором при создании)
    kind: so.Mapped[MachineryKind] = so.mapped_column(
        sa.Enum(MachineryKind),
        index=True,
        nullable=False,
        default=MachineryKind.OTHER,
        server_default=MachineryKind.OTHER.value
    )
    # Краткое обозначение типа (АЦ, АЛ, АКП, АНР, АГ, АСА и т. п.) — выводится в строевую записку
    short_title: so.Mapped[Optional[str]] = so.mapped_column(
        sa.String(16),
        nullable=True
    )
    # Ход выезда автоцистерны (1, 2, 3...). Только у АЦ, уникален в пределах одной ПСЧ
    departure_order: so.Mapped[Optional[int]] = so.mapped_column(
        sa.Integer,
        nullable=True
    )

    supervisor: so.Mapped[str] = so.mapped_column(
        sa.String(128),
        nullable=False
    )
    current_personnel: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        nullable=False,
        default=0
    )
    gdzs: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        nullable=False,
        default=0
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

    # Передислокации (история сохраняется)
    relocations: so.Mapped[List["Relocation"]] = so.relationship(
        "Relocation",
        back_populates="machinery",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Ход выезда — положительное число и уникален в пределах ПСЧ
        sa.CheckConstraint(
            "departure_order IS NULL OR departure_order >= 1",
            name="ck_machinery_departure_order_positive"
        ),
        sa.Index(
            "uq_machinery_section_departure_order",
            "section_id", "departure_order",
            unique=True,
            postgresql_where=sa.text("departure_order IS NOT NULL")
        ),
    )

    # ------------------------------------------------------------------
    # ЕДИНОЕ правило «моя техника сегодня» (см. п. 3.2 ТЗ).
    # Реализовано только здесь и используется везде: список техники диспетчера,
    # форма подачи строевой записки, выгрузка.
    # ------------------------------------------------------------------
    @classmethod
    def effective_section_id(cls, on_date: date):
        """SQL-выражение: ПСЧ, за которой машина числится на дату.

        Принимающая ПСЧ, если на дату есть активная передислокация, иначе штатная.
        """
        active_target = (
            sa.select(Relocation.to_section_id)
            .where(
                Relocation.machinery_id == cls.id,
                Relocation.active_clause(on_date)
            )
            .limit(1)
            .correlate(cls)
            .scalar_subquery()
        )
        return sa.func.coalesce(active_target, cls.section_id)

    @classmethod
    def on_duty_clause(cls, section_id: int, on_date: date):
        """Условие: машина в списке «моя техника сегодня» для ПСЧ."""
        return cls.effective_section_id(on_date) == section_id

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
    date: so.Mapped[Optional[date]] = so.mapped_column(
        sa.Date,
        index=True,
        nullable=True
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
        return self.date.strftime("%d.%m.%Y") if self.date else self.note


# Передислокация техники между ПСЧ. Штатная принадлежность машины (Machinery.section_id) не меняется.
class Relocation(Base):
    __tablename__ = "relocations"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    machinery_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("machineries.id"),
        index=True,
        nullable=False
    )
    machinery: so.Mapped[Machinery] = so.relationship(
        "Machinery",
        back_populates="relocations"
    )

    # Отдающая ПСЧ (штатная принадлежность машины на момент оформления)
    from_section_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("sections.id"),
        index=True,
        nullable=False
    )
    from_section: so.Mapped["Section"] = so.relationship(
        "Section",
        foreign_keys=[from_section_id]
    )

    # Принимающая ПСЧ
    to_section_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("sections.id"),
        index=True,
        nullable=False
    )
    to_section: so.Mapped["Section"] = so.relationship(
        "Section",
        foreign_keys=[to_section_id]
    )

    # Дата начала (включительно)
    date_from: so.Mapped[date] = so.mapped_column(
        sa.Date,
        index=True,
        nullable=False
    )
    # Дата возврата (машина возвращается в эту дату, т. е. передислокация действует ДО неё).
    # Пусто — «до конца текущих суток» (действует только в date_from, закрывается в 00:00).
    date_to: so.Mapped[Optional[date]] = so.mapped_column(
        sa.Date,
        nullable=True
    )

    # Аудит
    created_by_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    closed_by_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    __table_args__ = (
        sa.CheckConstraint("from_section_id <> to_section_id", name="ck_relocation_sections_differ"),
        sa.CheckConstraint("date_to IS NULL OR date_to >= date_from", name="ck_relocation_dates"),
    )

    # Первый день, когда передислокация уже не действует
    @property
    def end_exclusive(self) -> date:
        return self.date_to if self.date_to is not None else self.date_from + timedelta(days=1)

    def is_active_on(self, on_date: date) -> bool:
        return self.date_from <= on_date < self.end_exclusive

    @classmethod
    def active_clause(cls, on_date: date):
        """SQL-условие «передислокация действует на дату» (единственное место, где оно описано)."""
        return sa.or_(
            sa.and_(cls.date_to.is_(None), cls.date_from == on_date),
            sa.and_(cls.date_to.isnot(None), cls.date_from <= on_date, on_date < cls.date_to)
        )

    def __repr__(self):
        return f"<Relocation(id={self.id}, machinery_id={self.machinery_id})>"
