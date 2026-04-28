# Внешние зависимости
from typing import List
import sqlalchemy.orm as so
import sqlalchemy as sa
# Внутренние модули
from web_app.src.models.base import Base


# Пожарные части
class Department(Base):
    __tablename__ = "departments"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(
        sa.String(128),
        nullable=False
    )

    # Связи
    users: so.Mapped[List["User"]] = so.relationship(
        "User",
        back_populates="department",
        cascade="all, delete-orphan"
    )
    sections: so.Mapped[List["Section"]] = so.relationship(
        "Section",
        back_populates="department",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Department(id={self.id}, title={self.title})>"

    def __str__(self):
        return self.title


# Отделения пожарной части
class Section(Base):
    __tablename__ = "sections"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(
        sa.String(128),
        nullable=False
    )

    # Связи с участком
    department_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("departments.id"),
        index=True,
        nullable=False
    )
    department: so.Mapped["Department"] = so.relationship(
        "Department",
        back_populates="sections"
    )

    machineries: so.Mapped[List["Machinery"]] = so.relationship(
        "Machinery",
        back_populates="section",
        cascade="all, delete-orphan"
    )
    reports: so.Mapped[List["Report"]] = so.relationship(
        "Report",
        back_populates="section",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Section(id={self.id}, title={self.title})>"

    def __str__(self):
        return self.title
