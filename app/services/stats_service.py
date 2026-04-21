import redis.asyncio as redis

from app.config import settings

client = redis.Redis.from_url(settings.REDIS_URL)


async def update_llm_usage(operation: str, tokens: int | None) -> None:
    if tokens is None:
        return
    key = f"{settings.STATS_PREFIX}:llm_usage"
    await client.hincrby(key, operation, tokens)  # type: ignore
