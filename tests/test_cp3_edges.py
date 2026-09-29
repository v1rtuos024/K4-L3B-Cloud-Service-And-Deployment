"""Các trường hợp đồng thời và request bị chặn trước khi gọi LLM."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi import HTTPException


def test_concurrent_requests_respect_quota(fake_redis):
    from app.rate_limiter import RateLimiter, WINDOW_SECONDS

    limiter = RateLimiter(fake_redis, limit_per_minute=3)
    barrier = Barrier(12)

    def request(_):
        barrier.wait(timeout=10)
        try:
            limiter.check("concurrent", now=1000.0)
            return True
        except HTTPException as error:
            assert error.status_code == 429
            assert error.headers["Retry-After"] == str(WINDOW_SECONDS)
            return False

    with ThreadPoolExecutor(max_workers=12) as pool:
        accepted = list(pool.map(request, range(12)))

    assert sum(accepted) == 3
    assert limiter.hit_count("concurrent", now=1000.0) == 3
    assert 0 < fake_redis.ttl(limiter._key("concurrent")) <= WINDOW_SECONDS
    limiter.check("concurrent", now=1060.0)
    assert limiter.hit_count("concurrent", now=1060.0) == 1


@pytest.mark.parametrize("status_code", [401, 429, 402])
def test_rejected_requests_do_not_call_llm(
    monkeypatch, client_factory, fake_redis, auth_headers, status_code
):
    from app import main
    from app.cost_guard import CostGuard
    from app.rate_limiter import RateLimiter

    def unexpected_llm(*args, **kwargs):
        pytest.fail("Request bị chặn không được gọi LLM")

    monkeypatch.setattr(main, "ask_llm", unexpected_llm)
    client = client_factory(rate_limit=1)
    user_id = auth_headers["X-User-Id"]
    if status_code == 429:
        RateLimiter(fake_redis, 1).check(user_id)
    elif status_code == 402:
        fake_redis.set(CostGuard._key(user_id), "999")

    response = client.post(
        "/ask",
        json={"question": "Xin chào"},
        headers={} if status_code == 401 else auth_headers,
    )
    assert response.status_code == status_code
    assert CostGuard(fake_redis, 10.0).spent(user_id) == (
        999.0 if status_code == 402 else 0.0
    )
    if status_code == 401:
        assert fake_redis.zcard(RateLimiter._key(user_id)) == 0


def test_monthly_cost_isolation_and_expiration(fake_redis):
    from app.cost_guard import CostGuard, KEY_TTL_SECONDS

    guard = CostGuard(fake_redis, 1.0)
    assert guard.record("u1", 0.9, month="2026-08") == pytest.approx(0.9)
    guard.check("u1", estimated_cost=0.1, month="2026-08")
    with pytest.raises(HTTPException) as error:
        guard.check("u1", estimated_cost=0.2, month="2026-08")
    assert error.value.status_code == 402
    assert guard.spent("u1", month="2026-09") == 0.0
    assert guard.record("u1", 0.25, month="2026-09") == pytest.approx(0.25)
    assert guard.spent("u1", month="2026-08") == pytest.approx(0.9)
    assert 0 < fake_redis.ttl(guard._key("u1", "2026-09")) <= KEY_TTL_SECONDS
