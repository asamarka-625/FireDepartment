# Внешние зависимости
from typing import Optional
from datetime import datetime
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncAttrs


# Базовая модель
class Base(AsyncAttrs, so.DeclarativeBase):

    # Дата создания и обновления
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime,
        default=sa.func.now()
    )
    updated_at: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.DateTime,
        onupdate=sa.func.now(),
        nullable=True
    )

    def update_from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
