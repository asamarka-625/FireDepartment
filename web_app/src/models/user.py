# Внешние зависимости
import sqlalchemy.orm as so
import sqlalchemy as sa
# Внутренние модули
from web_app.src.models.base import Base


# Пользователи
class User(Base):
    __tablename__ = "users"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(
        sa.String(64),
        unique=True,
        nullable=False
    )
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    admin: so.Mapped[bool] = so.mapped_column(
        sa.Boolean,
        default=False,
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
        back_populates="users"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

    def __str__(self):
        return self.email
