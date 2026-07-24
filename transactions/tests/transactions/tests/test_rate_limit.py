import pytest
from django.conf import settings
import redis
from transactions.rate_limit import is_rate_limited


@pytest.fixture(autouse=True)
def clear_redis_test_keys():
    yield
    r = redis.from_url(settings.REDIS_URL)
    for key in r.keys("test_ratelimit:*"):
        r.delete(key)



def test_allows_requests_under_limit():
    key = "test_ratelimit:under"
    for _ in range(5):
        assert is_rate_limited(key, limit=10, window_seconds=5) is False


def test_blocks_requests_over_limit():
    key = "test_ratelimit:over"
    for _ in range(10):
        is_rate_limited(key, limit=10, window_seconds=5)
    assert is_rate_limited(key, limit=10, window_seconds=5) is True