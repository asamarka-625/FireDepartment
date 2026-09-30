"""report improvements: reserve LSB, machinery kind/short title/departure order, relocations, section-level users

Revision ID: 3b7d5a91c2e4
Revises: ecdc457e8bc9
Create Date: 2026-09-29 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b7d5a91c2e4'
down_revision: Union[str, Sequence[str], None] = 'ecdc457e8bc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 2.1. Новое состояние «Резерв (ЛСБ)». ALTER TYPE ... ADD VALUE нельзя выполнять внутри транзакции.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE statusmaintenance ADD VALUE IF NOT EXISTS 'RESERVE_LSB'")

    # 2.3-2.5. Категория, краткое обозначение, ход выезда
    machinery_kind = sa.Enum('SPECIAL', 'OTHER', name='machinerykind')
    machinery_kind.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'machineries',
        sa.Column('kind', machinery_kind, nullable=False, server_default='OTHER')
    )
    op.add_column('machineries', sa.Column('short_title', sa.String(length=16), nullable=True))
    op.add_column('machineries', sa.Column('departure_order', sa.Integer(), nullable=True))
    op.create_index('ix_machineries_kind', 'machineries', ['kind'])
    op.create_check_constraint(
        'ck_machinery_departure_order_positive', 'machineries',
        'departure_order IS NULL OR departure_order >= 1'
    )
    op.create_index(
        'uq_machinery_section_departure_order', 'machineries', ['section_id', 'departure_order'],
        unique=True, postgresql_where=sa.text('departure_order IS NOT NULL')
    )

    # Первичное заполнение по старому правилу (в названии две заглавные буквы подряд = спецтехника):
    # категория и краткое обозначение (АЦ, АЛ, АГ, АСО...). Ходы выезда АЦ задаются вручную в админке.
    op.execute("UPDATE machineries SET kind = 'SPECIAL' WHERE title ~ '[А-ЯЁA-Z]{2}'")
    op.execute(
        "UPDATE machineries SET short_title = substring(title from '^[А-ЯЁ]{2,4}') "
        "WHERE kind = 'SPECIAL' AND substring(title from '^[А-ЯЁ]{2,4}') IS NOT NULL"
    )

    # 2.2. Учётная запись уровня ПСЧ (section_id пуст — уровень ПСО)
    op.add_column('users', sa.Column('section_id', sa.Integer(), nullable=True))
    op.create_index('ix_users_section_id', 'users', ['section_id'])
    op.create_foreign_key('fk_users_section_id', 'users', 'sections', ['section_id'], ['id'])

    # 3. Передислокации
    # Таблицу могло уже создать приложение при старте (Base.metadata.create_all) — тогда пропускаем
    if not sa.inspect(op.get_bind()).has_table('relocations'):
        op.create_table(
            'relocations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('machinery_id', sa.Integer(), nullable=False),
            sa.Column('from_section_id', sa.Integer(), nullable=False),
            sa.Column('to_section_id', sa.Integer(), nullable=False),
            sa.Column('date_from', sa.Date(), nullable=False),
            sa.Column('date_to', sa.Date(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), nullable=True),
            sa.Column('closed_by_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.CheckConstraint('from_section_id <> to_section_id', name='ck_relocation_sections_differ'),
            sa.CheckConstraint('date_to IS NULL OR date_to >= date_from', name='ck_relocation_dates'),
            sa.ForeignKeyConstraint(['machinery_id'], ['machineries.id']),
            sa.ForeignKeyConstraint(['from_section_id'], ['sections.id']),
            sa.ForeignKeyConstraint(['to_section_id'], ['sections.id']),
            sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['closed_by_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_relocations_machinery_id', 'relocations', ['machinery_id'])
        op.create_index('ix_relocations_from_section_id', 'relocations', ['from_section_id'])
        op.create_index('ix_relocations_to_section_id', 'relocations', ['to_section_id'])
        op.create_index('ix_relocations_date_from', 'relocations', ['date_from'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('relocations')

    op.drop_constraint('fk_users_section_id', 'users', type_='foreignkey')
    op.drop_index('ix_users_section_id', table_name='users')
    op.drop_column('users', 'section_id')

    op.drop_index('uq_machinery_section_departure_order', table_name='machineries')
    op.drop_constraint('ck_machinery_departure_order_positive', 'machineries', type_='check')
    op.drop_index('ix_machineries_kind', table_name='machineries')
    op.drop_column('machineries', 'departure_order')
    op.drop_column('machineries', 'short_title')
    op.drop_column('machineries', 'kind')
    sa.Enum(name='machinerykind').drop(op.get_bind(), checkfirst=True)

    # Значение 'RESERVE_LSB' из enum PostgreSQL удалить нельзя без пересоздания типа;
    # переводим такие машины в «Резерв (ЛСО)» и пересоздаём тип.
    op.execute("UPDATE machineries SET status = 'RESERVE_LSO' WHERE status = 'RESERVE_LSB'")
    op.execute("ALTER TYPE statusmaintenance RENAME TO statusmaintenance_old")
    op.execute(
        "CREATE TYPE statusmaintenance AS ENUM "
        "('ON','RESERVE','RESERVE_LSO','REPAIR','TO1','TO2','VP','OFF')"
    )
    op.execute(
        "ALTER TABLE machineries ALTER COLUMN status TYPE statusmaintenance "
        "USING status::text::statusmaintenance"
    )
    op.execute("DROP TYPE statusmaintenance_old")
