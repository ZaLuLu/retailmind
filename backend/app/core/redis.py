# backend/app/core/redis.py
import json
import logging
from typing import Optional, Any
from .config import settings

logger = logging.getLogger(__name__)

class CacheClient:
    """
    Asynchronous caching client that connects to Redis if configured,
    and falls back to an in-memory dictionary-based cache otherwise.
    """

    def __init__(self):
        self.redis = None
        self._in_memory_db = {}
        self.is_redis_available = False

    async def initialize(self):
        if not settings.REDIS_URL:
            logger.info("REDIS_URL not configured. Using in-memory cache fallback.")
            return

        try:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            # Test connection
            await self.redis.ping()
            self.is_redis_available = True
            logger.info("Successfully connected to Redis cache!")
        except Exception as e:
            logger.warning(
                f"Failed to connect to Redis at {settings.REDIS_URL}. "
                f"Falling back to in-memory cache. Error: {e}"
            )
            self.redis = None
            self.is_redis_available = False

    async def get(self, key: str) -> Optional[str]:
        if self.is_redis_available and self.redis:
            try:
                return await self.redis.get(key)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}. Falling back to in-memory.")
        
        # In-memory lookup
        val = self._in_memory_db.get(key)
        if val is not None:
            import time
            expire_at = val.get("expire_at")
            if expire_at is not None and time.time() > expire_at:
                del self._in_memory_db[key]
                return None
            return val["data"]
        return None

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if self.is_redis_available and self.redis:
            try:
                await self.redis.set(key, value, ex=ex)
                return True
            except Exception as e:
                logger.warning(f"Redis set failed: {e}. Falling back to in-memory.")

        # In-memory storage
        import time
        expire_at = (time.time() + ex) if ex is not None else None
        self._in_memory_db[key] = {
            "data": value,
            "expire_at": expire_at
        }
        return True

    async def delete(self, key: str) -> bool:
        if self.is_redis_available and self.redis:
            try:
                await self.redis.delete(key)
                return True
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}. Falling back to in-memory.")
        
        if key in self._in_memory_db:
            del self._in_memory_db[key]
            return True
        return False

    async def invalidate_chart_bundle(self, user_id: Any):
        """Clears all cached chart bundles for a given user."""
        user_id_str = str(user_id)
        if self.is_redis_available and self.redis:
            try:
                # Find all keys matching the pattern and delete them
                pattern = f"chart_bundle:{user_id_str}:*"
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
                # Also delete the "all" key just in case
                await self.redis.delete(f"chart_bundle:{user_id_str}:all")
            except Exception as e:
                logger.warning(f"Failed to invalidate Redis cache: {e}")
        
        # Also clear from in-memory cache
        keys_to_del = [k for k in self._in_memory_db.keys() if k.startswith(f"chart_bundle:{user_id_str}:")]
        for k in keys_to_del:
            del self._in_memory_db[k]

    async def clear_all(self):
        """Clears all cached keys."""
        if self.is_redis_available and self.redis:
            try:
                await self.redis.flushdb()
                return True
            except Exception as e:
                logger.warning(f"Redis flushdb failed: {e}.")
        
        self._in_memory_db.clear()
        return True

cache = CacheClient()
