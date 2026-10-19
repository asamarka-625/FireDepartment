"""relocation: status chosen by the receiving ПСЧ (received_status)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-15 16:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Статус передислоцированной машины в принимающей ПСЧ (п. 3.4).

    Значение выбирает диспетчер принявшей части («Включено» / «Резерв»).
    Тип статуса — существующий enum statusmaintenance (создавать не нужно).
    Операция идемпотентна: колонки могло не быть, либо её мог создать create_all.
    """
    op.execute(
        "ALTER TABLE relocations ADD COLUMN IF NOT EXISTS received_status statusmaintenance"
    )

    # Для действующих передислокаций — начальный статус берём из штатной карточки машины
    op.execute(
        "UPDATE relocations r "
        "SET received_status = m.status "
        "FROM machineries m "
        "WHERE r.machinery_id = m.id "
        "  AND r.received_status IS NULL "
        "  AND (r.date_to IS NULL OR r.date_to > CURRENT_DATE)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE relocations DROP COLUMN IF EXISTS received_status")
