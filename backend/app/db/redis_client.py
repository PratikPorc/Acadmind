from typing import Any

import redis.asyncio as redis

_redis: redis.Redis | None = None


def init_redis(settings: Any) -> None:
    global _redis
    _redis = redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> redis.Redis:
    if _redis is None:
        raise RuntimeError("Redis client is not initialized")
    return _redis


async def check_redis_connection() -> tuple[bool, str]:
    try:
        client = get_redis()
        pong = await client.ping()
        return (True, "connected") if pong else (False, "no pong")
    except RuntimeError as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
