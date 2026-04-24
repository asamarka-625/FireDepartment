# Внешние зависимости
from typing import Optional, Dict
import json
from datetime import date
import redis.asyncio as redis
# Внутренние модули
from web_app.src.core import cfg


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


class RedisService:
    def __init__(self):
        self.redis_url = cfg.redis_url
        self.redis: Optional[redis.Redis] = None
        self.refresh_prefix = "refresh:"
        self.user_set_prefix = "user_tokens:"
        self.user_prefix = "user:"

    async def init_redis(self):
        """Инициализация подключения к Redis"""
        cfg.logger.info("Инициализируем соединение Redis")

        if not self.redis:
            self.redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

    async def close_redis(self):
        """Закрытие подключения к Redis"""
        cfg.logger.info("Закрываем соединение Redis")

        if self.redis:
            await self.redis.close()

    async def add_user_refresh_token(
        self,
        user_id: str,
        refresh_uuid: str,
        data: str
    ):
        """Добавление токена и индексация его в сете пользователя"""
        token_key = f"{self.refresh_prefix}{user_id}:{refresh_uuid}"
        set_key = f"{self.user_set_prefix}{user_id}"

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.set(
                name=token_key,
                value=data,
                ex=cfg.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            )
            pipe.sadd(set_key, refresh_uuid)
            # Устанавливаем TTL для всего сета (чуть больше токена, для очистки)
            pipe.expire(set_key, cfg.REFRESH_TOKEN_EXPIRE_MINUTES * 60 + 3600)
            await pipe.execute()

    async def update_user_refresh_token(
        self,
        user_id: str,
        refresh_uuid: str,
        data: str,
        last_token: str
    ):
        """Обновление токена и индексация его в сете пользователя"""
        old_token_key = f"{self.refresh_prefix}{user_id}:{last_token}"
        new_token_key = f"{self.refresh_prefix}{user_id}:{refresh_uuid}"
        set_key = f"{self.user_set_prefix}{user_id}"

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.expire(old_token_key, 30)
            pipe.set(
                name=new_token_key,
                value=data,
                ex=cfg.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            )
            pipe.sadd(set_key, refresh_uuid)
            # Устанавливаем TTL для всего сета (чуть больше токена, для очистки)
            pipe.expire(set_key, cfg.REFRESH_TOKEN_EXPIRE_MINUTES * 60 + 3600)
            await pipe.execute()

    async def del_user_refresh_token(self, user_id: str, refresh_uuid: str):
        """Удаление конкретного токена"""
        token_key = f"{self.refresh_prefix}{user_id}:{refresh_uuid}"
        set_key = f"{self.user_set_prefix}{user_id}"

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.delete(token_key)
            pipe.srem(set_key, refresh_uuid)
            await pipe.execute()

    async def del_other_user_refresh_tokens(self, user_id: str, current_refresh_uuid: str):
        """Удаляем все сессии пользователя, кроме текущей"""
        set_key = f"{self.user_set_prefix}{user_id}"

        # Получаем все UUID сессий пользователя
        all_uuids = await self.redis.smembers(set_key)

        async with self.redis.pipeline(transaction=True) as pipe:
            for r_uuid in all_uuids:
                if r_uuid != current_refresh_uuid:
                    # Удаляем данные токена
                    pipe.delete(f"{self.refresh_prefix}{user_id}:{r_uuid}")
                    # Удаляем UUID из сета
                    pipe.srem(set_key, r_uuid)
            await pipe.execute()

    async def is_refresh_token_valid(self, user_id: str, refresh_uuid: str) -> bool:
        """Проверка валидности (есть ли UUID в сете и существует ли сам токен)"""
        token_key = f"{self.refresh_prefix}{user_id}:{refresh_uuid}"
        exists = await self.redis.exists(token_key)

        if not exists:
            await self.redis.srem(f"{self.user_set_prefix}{user_id}", refresh_uuid)
            return False
        return True

    async def add_user_data(
        self,
        user_id: str,
        data: dict
    ) -> None:
        """Добавление данных о пользователе"""
        await self.redis.set(
            name=f"{self.user_prefix}{user_id}",
            value=json.dumps(data, cls=CustomJSONEncoder),
            ex=cfg.USER_CACHE_SECONDS
        )

    async def get_user_data(
        self,
        user_id: str
    ) -> Optional[Dict[str, str]]:
        """Получаем данные о пользователе"""
        data = await self.redis.get(f"{self.user_prefix}{user_id}")
        if data:
            return json.loads(data)

        return None

    async def get_info(self) -> dict:
        """Информация redis"""
        return {
            "memory_usage": await self.redis.info('memory')
        }