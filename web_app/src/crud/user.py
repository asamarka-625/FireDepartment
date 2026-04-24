# Внешние зависимости
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from fastapi import HTTPException, status
# Внутренние модули
from web_app.src.core import cfg, connection
from web_app.src.models import User


# Получаем пользователя по email
@connection
async def sql_get_user_by_email(
    email: str,
    session: AsyncSession,
    not_found_error: bool = True
) -> Optional[User]:
    try:
        user_result = await session.execute(
            sa.select(User)
            .where(User.email == email)
        )

        if not_found_error:
            user = user_result.scalar_one()

        else:
            user = user_result.scalar_one_or_none()

        return user

    except NoResultFound:
        cfg.logger.info(f"User not found by email: {email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get user by email: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get user by email: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")


# Получаем пользователя по id
@connection
async def sql_get_user_by_id(
    user_id: int,
    session: AsyncSession
) -> User:
    try:
        user_result = await session.execute(
            sa.select(User)
            .where(User.id == user_id)
        )

        return user_result.scalar_one()

    except NoResultFound:
        cfg.logger.info(f"User not found by id: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except SQLAlchemyError as e:
        cfg.logger.error(f"Database error get user by id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    except Exception as e:
        cfg.logger.error(f"Unexpected error get user by id: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected server error")