# Внешние зависимости
from typing import List
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import cfg, connection
from web_app.src.models import Section


# Получаем все пожарные отделения
@connection
async def sql_get_sections(
    session: AsyncSession,
) -> List[Section]:
    try:
        sections_result = await session.execute(
            sa.select(Section)
            .order_by(Section.id)
        )

        return list(sections_result.scalars())

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get sections: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get sections: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")