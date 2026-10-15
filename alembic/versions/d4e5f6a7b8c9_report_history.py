"""report history: keep every строевая записка per day (drop unique date+section)

Revision ID: d4e5f6a7b8c9
Revises: 3b7d5a91c2e4
Create Date: 2026-10-15 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = '3b7d5a91c2e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """История строевых записок: за одни дежурные сутки у ПСЧ может быть несколько записок.

    Снимаем уникальность (date, section_id) — каждая подача теперь отдельная запись.
    «Актуальная» за сутки определяется по наибольшему id.
    """
    # UNIQUE-ограничение в PostgreSQL обслуживается одноимённым уникальным индексом.
    op.drop_constraint('uq_report_date_section', 'reports', type_='unique')

    # Индекс для выборки записок ПСЧ по дате (история + поиск актуальной за сутки)
    op.create_index('ix_report_section_date', 'reports', ['section_id', 'date'])


def downgrade() -> None:
    """Downgrade: возвращаем «одна записка на сутки».

    За сутки могли накопиться несколько записок — оставляем последнюю (наибольший id),
    иначе уникальное ограничение не создастся.
    """
    op.drop_index('ix_report_section_date', table_name='reports')

    op.execute(
        "DELETE FROM reports a USING reports b "
        "WHERE a.section_id = b.section_id AND a.date = b.date AND a.id < b.id"
    )

    op.create_unique_constraint('uq_report_date_section', 'reports', ['date', 'section_id'])
