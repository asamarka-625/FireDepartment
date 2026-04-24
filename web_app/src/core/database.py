# Внешние зависимости
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# Внутренние модули
from web_app.src.core.config import cfg
from web_app.src.models import Base


engine = create_async_engine(cfg.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Инициализируем таблицы
async def setup_database():
    cfg.logger.info("Инициализируем таблицы")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Декоратор подключения к базе данных
def connection(method):
    async def wrapper(*args, **kwargs):
        if kwargs.pop('no_decor', False):
            return await method(*args, **kwargs)

        async with AsyncSessionLocal() as session:
            try:
                return await method(*args, session=session, **kwargs)

            except Exception as e:
                await session.rollback()
                raise e

            finally:
                await session.close()

    return wrapper