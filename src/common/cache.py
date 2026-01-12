import redis.asyncio as redis
import json
import os

# Connect to the Redis Container (hostname: amrutam_redis)
REDIS_URL = os.getenv("REDIS_URL", "redis://amrutam_redis:6379/0")

class CacheService:
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        # CONFIG: How long (in seconds) to keep search results?
        # 60 seconds is a good balance: Data isn't too stale, but DB is protected.
        self.TTL = 60 

    async def get_cached_data(self, key: str):
        """Try to fetch data from RAM."""
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_cached_data(self, key: str, data: dict):
        """Save data to RAM with an expiration timer."""
        await self.redis.setex(key, self.TTL, json.dumps(data))

    async def invalidate_pattern(self, pattern: str):
        """Delete all keys matching a pattern (e.g., 'doctors:*')."""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

# Global Instance
cache = CacheService()