# Внешние зависимости
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import cfg, connection
from web_app.src.models import Department


# Получаем пожарный участок по ID
@connection
async def sql_get_department_by_id(
    department_id: int,
    session: AsyncSession,
) -> Department:
    try:
        department_result = await session.execute(
            sa.select(Department)
            .where(Department.id == department_id)
            .options(
                so.selectinload(Department.sections)
            )
        )

        return department_result.scalar_one()

    except NoResultFound:
        cfg.logger.info(f"Department not found by department_id: {department_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get department by department_id: {department_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get department by department_id: {department_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")