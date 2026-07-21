import json
import time
from typing import Optional, Any

import redis.asyncio as aioredis

from app.core.config import settings


class CacheService:
    def __init__(self, redis_url: str):
        self._redis: Optional[aioredis.Redis] = None
        self._redis_url = redis_url

    async def init(self):
        self._redis = await aioredis.from_url(
            self._redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
            retry_on_timeout=True,
        )

    async def close(self):
        if self._redis:
            await self._redis.close()

    @property
    def client(self) -> aioredis.Redis:
        return self._redis

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        if not self._redis:
            return False
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self._redis.set(key, value, ex=ttl)

    async def get(self, key: str) -> Optional[Any]:
        if not self._redis:
            return None
        val = await self._redis.get(key)
        if val is None:
            return None
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return val

    async def delete(self, key: str) -> bool:
        if not self._redis:
            return False
        return await self._redis.delete(key) > 0

    async def exists(self, key: str) -> bool:
        if not self._redis:
            return False
        return await self._redis.exists(key) > 0

    async def increment(self, key: str, amount: int = 1) -> int:
        if not self._redis:
            return 0
        return await self._redis.incrby(key, amount)

    async def expire(self, key: str, ttl: int) -> bool:
        if not self._redis:
            return False
        return await self._redis.expire(key, ttl)

    async def blacklist_token(self, jti: str, expires_in: int) -> bool:
        return await self.set(f"blacklist:{jti}", "1", expires_in)

    async def is_token_blacklisted(self, jti: str) -> bool:
        return await self.exists(f"blacklist:{jti}")

    async def check_rate_limit(self, key: str, max_attempts: int, window: int) -> tuple[bool, int]:
        if not self._redis:
            return True, 0
        count = await self._redis.incr(key)
        if count == 1:
            await self._redis.expire(key, window)
        return count <= max_attempts, count


cache = CacheService(settings.REDIS_URL)