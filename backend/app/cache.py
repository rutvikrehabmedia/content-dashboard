from typing import Optional, Any
import json
from datetime import datetime
import aioredis
import logging
from .config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    _redis: Optional[aioredis.Redis] = None

    @classmethod
    async def init_redis(cls, redis_url: str = "redis://localhost"):
        try:
            cls._redis = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            cls._redis = None

    @classmethod
    async def close(cls):
        if cls._redis:
            await cls._redis.close()
            logger.info("Closed Redis connection")

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        if not cls._redis:
            return None
        try:
            data = await cls._redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    @classmethod
    async def set(
        cls, 
        key: str, 
        value: Any, 
        expire: int = 3600
    ) -> bool:
        if not cls._redis:
            return False
        try:
            value = json.dumps(value, default=str)
            await cls._redis.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    @classmethod
    async def delete(cls, key: str) -> bool:
        if not cls._redis:
            return False
        try:
            await cls._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

cache = RedisCache() 