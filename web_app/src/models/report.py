# Внешние зависимости
from typing import List, Dict
from datetime import date
import sqlalchemy.orm as so
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
# Внутренние модули
from web_app.src.models.base import Base


# Служебные записки
class Report(Base):
    __tablename__ = "reports"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    data: so.Mapped[List[Dict]] = so.mapped_column(JSONB, nullable=False)
    date: so.Mapped[date] = so.mapped_column(
        sa.Date,
        nullable=False,
        index=True,
    )

    # Связи с отделением
    section_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("sections.id"),
        index=True,
        nullable=False
    )
    section: so.Mapped["Section"] = so.relationship(
        "Section",
        back_populates="reports"
    )

    __table_args__ = (
        sa.UniqueConstraint("date", "section_id", name="uq_report_date_section"),
    )

    def __repr__(self):
        return f"<Report(id={self.id}, section_id={self.section_id})>"

    def __str__(self):
        return f"Report(id={self.id})"