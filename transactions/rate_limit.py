import redis
from django.conf import settings

redis_client = redis.from_url(settings.REDIS_URL)


def is_rate_limited(key: str, limit: int = 10, window_seconds: int = 1) -> bool:
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window_seconds)
    return current > limit