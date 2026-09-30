# Внешние зависимости
from typing import Optional, Sequence, Set
from datetime import date, timedelta
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import cfg, connection
from web_app.src.models import Machinery, Relocation, Section, RELOCATABLE_STATUSES
from web_app.src.crud.machinery import RELOCATION_STATUS_ERROR
from web_app.src.utils.machinery_rules import today_msk


# Оформляем передислокацию машины.
# manage_section_ids — ПСЧ, которыми управляет пользователь (None — все, администратор):
#   штатная ПСЧ машины должна входить в этот набор.
# target_section_ids — ПСЧ, в которые пользователь вправе передислоцировать (None — любые).
@connection
async def sql_create_relocation(
    machinery_id: int,
    to_section_id: int,
    date_return: Optional[date],
    user_id: int,
    manage_section_ids: Optional[Sequence[int]],
    target_section_ids: Optional[Set[int]],
    session: AsyncSession,
) -> None:
    try:
        today = today_msk()

        # Блокируем машину: две одновременные передислокации одной машины невозможны
        machinery_result = await session.execute(
            sa.select(Machinery)
            .where(Machinery.id == machinery_id)
            .with_for_update()
        )
        machinery = machinery_result.scalar_one_or_none()

        if machinery is None or (
            manage_section_ids is not None and machinery.section_id not in manage_section_ids
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Машина не найдена")

        if to_section_id == machinery.section_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Принимающая ПСЧ совпадает со штатной ПСЧ машины"
            )

        if target_section_ids is not None and to_section_id not in target_section_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Передислокация в выбранную ПСЧ недоступна"
            )

        target_exists = await session.execute(
            sa.select(Section.id).where(Section.id == to_section_id)
        )
        if target_exists.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Принимающая ПСЧ не найдена")

        # п. 3.4: только «Включено» и «Резерв» (все варианты)
        if machinery.status not in RELOCATABLE_STATUSES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=RELOCATION_STATUS_ERROR)

        if date_return is not None and date_return <= today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Дата возврата должна быть позже сегодняшней (или не указана — до конца суток)"
            )

        # п. 3.1: у одной машины — не более одной активной передислокации
        existing_result = await session.execute(
            sa.select(Relocation)
            .where(
                Relocation.machinery_id == machinery_id,
                sa.or_(Relocation.date_to.is_(None), Relocation.date_to > today)
            )
        )
        if any(r.end_exclusive > today for r in existing_result.scalars()):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="У машины уже есть активная передислокация"
            )

        session.add(Relocation(
            machinery_id=machinery_id,
            from_section_id=machinery.section_id,
            to_section_id=to_section_id,
            date_from=today,
            date_to=date_return,
            created_by_id=user_id
        ))

        await session.commit()

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error create relocation by machinery_id: {machinery_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error create relocation by machinery_id: {machinery_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Изменяем/отменяем активную передислокацию.
# date_return <= сегодня — отмена (машина возвращается сразу);
# date_return > сегодня — продление; пусто — «до конца текущих суток».
# Запись не удаляется — история сохраняется.
@connection
async def sql_update_relocation(
    machinery_id: int,
    date_return: Optional[date],
    user_id: int,
    manage_section_ids: Optional[Sequence[int]],
    session: AsyncSession,
    cancel: bool = False,
) -> None:
    try:
        today = today_msk()

        relocation_result = await session.execute(
            sa.select(Relocation)
            .where(
                Relocation.machinery_id == machinery_id,
                Relocation.active_clause(today)
            )
            .with_for_update()
        )
        relocation = relocation_result.scalar_one_or_none()

        if relocation is None or (
            manage_section_ids is not None and relocation.from_section_id not in manage_section_ids
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Активная передислокация не найдена")

        if cancel or (date_return is not None and date_return <= today):
            # Возврат уже сегодня: передислокация перестаёт действовать (date_to — первый день без неё)
            relocation.date_to = today
            relocation.closed_by_id = user_id

        elif date_return is not None:
            relocation.date_to = date_return

        else:
            # «До конца текущих суток»
            relocation.date_to = None if relocation.date_from == today else today + timedelta(days=1)

        await session.commit()

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error update relocation by machinery_id: {machinery_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error update relocation by machinery_id: {machinery_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")
