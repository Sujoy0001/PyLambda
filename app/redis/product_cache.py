import json
import uuid
import redis.asyncio as redis

from app.middlewares.logging import logger

PRODUCT_TTL = 300   # 5 minutes
LIST_TTL = 60       # lists change more often, so keep them short


def product_key(product_id: uuid.UUID) -> str:
    return f"product:{product_id}"


def list_key(skip: int, limit: int) -> str:
    return f"products:list:{skip}:{limit}"


async def get_cached(r: redis.Redis, key: str):
    try:
        raw = await r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        logger.warning(f"Redis GET failed: {key}")
        return None          # treat as a cache miss


async def set_cached(r: redis.Redis, key: str, value, ttl: int) -> None:
    try:
        await r.set(key, json.dumps(value), ex=ttl)
    except Exception:
        logger.warning(f"Redis SET failed: {key}")


async def invalidate_product(r: redis.Redis, product_id: uuid.UUID | None = None) -> None:
    """Call this whenever products change."""
    try:
        if product_id:
            await r.delete(product_key(product_id))
        async for key in r.scan_iter(match="products:list:*"):
            await r.delete(key)
    except Exception:
        logger.warning("Redis invalidate failed")