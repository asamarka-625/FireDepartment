# Внешние зависимости
from typing import List, Tuple
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import cfg, connection
from web_app.src.models import (Machinery, STATUS_MAINTENANCE_MAP, StatusMaintenance,
                                REVERSE_STATUS_MAINTENANCE_MAP, Maintenance)
from web_app.src.schemas import UpdateMachineryRequest, MachineryScheme


# Получаем список машин
@connection
async def sql_get_machineries(
    section_id: int,
    session: AsyncSession,
) -> List[MachineryScheme]:
    try:
        machineries_result = await session.execute(
            sa.select(Machinery)
            .where(Machinery.section_id == section_id)
            .options(
                so.joinedload(Machinery.maintenance)
            )
        )

        result = []
        for machinery in machineries_result.scalars():
            machinery.status = STATUS_MAINTENANCE_MAP[machinery.status.value]
            result.append(MachineryScheme.model_validate(machinery))

        return result

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get machineries by section_id: {section_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get machineries by section_id: {section_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем список ID машин
@connection
async def sql_get_machinery_ids(
    section_ids: Tuple[int],
    session: AsyncSession,
) -> Tuple[int, ...]:
    try:
        machinery_ids_result = await session.execute(
            sa.select(Machinery.id)
            .where(Machinery.section_id.in_(section_ids))
        )

        return tuple(machinery_ids_result.scalars())

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get machinery_ids by section_ids: {section_ids}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get machinery_ids by section_ids: {section_ids}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Обновляем информации о машине
@connection
async def sql_update_machinery(
    update: UpdateMachineryRequest,
    session: AsyncSession,
) -> None:
    try:
        machinery_result = await session.execute(
            sa.select(Machinery)
            .where(Machinery.id == update.id)
            .options(
                so.joinedload(Machinery.maintenance)
            )
        )
        machinery = machinery_result.scalar_one()

        if update.status is not None:
            machinery.status = REVERSE_STATUS_MAINTENANCE_MAP.get(update.status, StatusMaintenance.OFF)

        if update.maintenance is not None:
            if machinery.maintenance:
                await session.delete(machinery.maintenance)
                await session.flush()

            machinery.maintenance = Maintenance(
                note=update.maintenance.note,
                date=update.maintenance.date
            )

        await session.commit()

    except NoResultFound:
        cfg.logger.info(f"Machinery not found by machinery_id: {update.id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machinery not found")

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error update machinery by machinery_id: {update.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error update machinery by machinery_id: {update.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")