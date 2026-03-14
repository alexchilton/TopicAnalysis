"""Redis client for caching and SSE broadcast."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Optional

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def cache_get(key: str) -> Optional[Any]:
    try:
        r = await get_redis()
        val = await r.get(f"cache:{key}")
        return json.loads(val) if val else None
    except Exception as exc:
        logger.warning("redis_cache_get_failed", key=key, error=str(exc))
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    try:
        r = await get_redis()
        await r.setex(f"cache:{key}", ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.warning("redis_cache_set_failed", key=key, error=str(exc))


async def publish_event(channel: str, data: dict) -> None:
    try:
        r = await get_redis()
        await r.publish(channel, json.dumps(data, default=str))
    except Exception as exc:
        logger.warning("redis_publish_failed", channel=channel, error=str(exc))


async def subscribe_events(channel: str) -> AsyncIterator[dict]:
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    yield json.loads(message["data"])
                except json.JSONDecodeError:
                    continue
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()


async def check_redis_health() -> bool:
    try:
        r = await get_redis()
        return await r.ping()
    except Exception:
        return False
